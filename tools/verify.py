#!/usr/bin/env python3
"""Run every playbook check and report one line each.

WHY THIS EXISTS
---------------
The individual validators print a lot, so it is tempting to run them as
`python tools/coverage.py --check | tail -1`. A shell pipeline returns the exit
status of the LAST command, so that reports `tail`'s success and silently
discards the checker's failure. A real regression (stale generated docs) was
reported green for a whole session that way.

This script computes each verdict internally and prints roughly one line per
check, so there is never a reason to pipe it anywhere. It exits non-zero if any
check fails, and prints the failing check's output in full.

It also runs an anchor audit that nothing else does: mkdocs --strict validates
that a linked PAGE exists, not that a linked #fragment exists on it.

Usage:
  python tools/verify.py            # all checks
  python tools/verify.py --quick    # skip the site build and anchor audit
  python tools/verify.py --portable # skip checks requiring sibling fleet trees
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SITE = ROOT / "site"

# Naming any one of these inline proves AGENTS.md carries tooling a Codex session
# can act on. Deliberately a low bar - the canonical detail lives in the
# `re-mcp-toolkit` skill, and duplicating it here is how two copies drift.
# The entry-point documents. An agent arriving with a symptom needs one of these
# by name; "the playbook exists at <path>" is a location, not a route.
PLAYBOOK_DOORS = (
    "symptom-index.md",
    "failure-atlas.md",
    "cross-project-index.md",
    "pattern-catalog.md",
    "bottleneck-map.md",
)

RE_TOOL_NAMES = (
    "ghidra", "regenny", "renderdoc", "cheat engine", "cheatengine",
    "x64dbg", "x32dbg", "frida", "apitrace", "ilspy",
)

ANCHOR_LINK = re.compile(r"\]\(([A-Za-z0-9._/-]*\.md)?#([a-z0-9][a-z0-9._-]*)\)")


def run(label: str, argv: list[str]) -> tuple[str, bool, str]:
    """Run a command, capturing everything. Never pipes; exit code is authoritative."""
    try:
        proc = subprocess.run(
            argv, cwd=ROOT, capture_output=True, text=True, timeout=600
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return label, False, f"could not run: {exc}"
    output = (proc.stdout or "") + (proc.stderr or "")
    return label, proc.returncode == 0, output.strip()


def site_html_for(md_rel: str) -> Path:
    stem = md_rel[:-3]
    if stem.lower() in ("readme", "index"):
        return SITE / "index.html"
    return SITE / stem / "index.html"


def audit_anchors() -> tuple[str, bool, str]:
    """Every ]( ... #fragment ) in the docs must exist as an id= in the built page."""
    if not SITE.exists():
        return "internal anchors", False, "site/ not built - run the site build first"

    ids_cache: dict[Path, set[str]] = {}

    def ids_of(html: Path) -> set[str]:
        if html not in ids_cache:
            ids_cache[html] = (
                set(re.findall(r'id="([^"]+)"', html.read_text(encoding="utf-8", errors="ignore")))
                if html.exists() else set()
            )
        return ids_cache[html]

    broken: list[str] = []
    checked = 0
    files = [m for m in sorted(DOCS.rglob("*.md"))
             if not m.relative_to(DOCS).as_posix().startswith("generated/")]

    for md in files:
        rel = md.relative_to(DOCS).as_posix()
        for target, anchor in ANCHOR_LINK.findall(
            md.read_text(encoding="utf-8", errors="ignore")
        ):
            checked += 1
            tgt = (Path(rel).parent / target).as_posix().replace("./", "") if target else rel
            html = site_html_for(tgt)
            if not html.exists():
                broken.append(f"{rel} -> {tgt}#{anchor}  [page not built]")
            elif anchor not in ids_of(html):
                broken.append(f"{rel} -> {tgt}#{anchor}  [anchor missing]")

    detail = f"{checked} links across {len(files)} files"
    if broken:
        return "internal anchors", False, detail + "\n  " + "\n  ".join(broken)
    return "internal anchors", True, detail


ROOT_DOCS = ("AGENTS.md", "CLAUDE.md", "README.md")
FILE_LINK = re.compile(r"\]\((?!https?:|#)([A-Za-z0-9._/-]+?)(#[a-z0-9._-]+)?\)")


def audit_entry_points() -> tuple[str, bool, str]:
    """Root-level routing files are outside docs/, so nothing else checks their links.

    They are the files most certain to be read, and a dead path in one sends a
    reader nowhere with no error anywhere.
    """
    broken: list[str] = []
    checked = 0
    present = [n for n in ROOT_DOCS if (ROOT / n).exists()]
    if not present:
        return "entry-point links", True, "no root routing files"

    for name in present:
        text = (ROOT / name).read_text(encoding="utf-8", errors="ignore")
        for target, _anchor in FILE_LINK.findall(text):
            checked += 1
            if not (ROOT / target).exists():
                broken.append(f"{name} -> {target}  [not found]")

    detail = f"{checked} links across {', '.join(present)}"
    if broken:
        return "entry-point links", False, detail + "\n  " + "\n  ".join(broken)
    return "entry-point links", True, detail


def audit_project_instructions() -> tuple[str, bool, str]:
    """Each fleet project's instruction files must point at each other AND route.

    Claude Code auto-loads CLAUDE.md; Codex auto-loads AGENTS.md. Neither reads
    the other by default, so content in only one file is invisible to one tool.
    The two files are NOT required to match - they are allowed to carry
    different content - but each must tell its reader the other exists.

    This gap ran silently for a long time: four projects kept their hard rules
    in CLAUDE.md only, so Codex never saw them.

    Pointing at each other is necessary and not sufficient. An agent arriving
    cold also needs the playbook (so it routes instead of re-deriving) and the
    RE tooling. Skills are a CLAUDE mechanism - Codex cannot load one - so
    AGENTS.md must additionally name at least one concrete tool inline rather
    than delegating the whole subject to `re-mcp-toolkit`. Sims4VR did exactly
    that and this check passed anyway, which is why it now looks at content.
    """
    label = "project instruction pairs"
    try:
        import yaml
        cfg = yaml.safe_load((ROOT / "sources.yml").read_text(encoding="utf-8"))
    except Exception as exc:
        return label, True, f"skipped (cannot read sources.yml: {exc})"

    problems: list[str] = []
    checked = 0
    for entry in cfg.get("fleet") or []:
        root = entry.get("root")
        if not root:
            continue
        proj = Path(root)
        if not proj.is_dir():
            continue  # a fleet root that is not mounted is not this check's business
        name = entry.get("id", proj.name)
        agents, claude = proj / "AGENTS.md", proj / "CLAUDE.md"
        if not agents.exists() or not claude.exists():
            missing = "AGENTS.md" if not agents.exists() else "CLAUDE.md"
            problems.append(f"{name}: no {missing}")
            continue
        checked += 1
        a = agents.read_text(encoding="utf-8", errors="replace")
        c = claude.read_text(encoding="utf-8", errors="replace")
        if "CLAUDE.md" not in a:
            problems.append(f"{name}: AGENTS.md never mentions CLAUDE.md - Codex will not see it")
        if "AGENTS.md" not in c:
            problems.append(f"{name}: CLAUDE.md never mentions AGENTS.md - Claude will not see it")

        both = a + "\n" + c
        low = both.lower()

        # Naming the playbook is NOT enough, and this check used to accept it.
        # Six of eight projects passed on the string "VR Modding" appearing
        # inside a `graphify query --graph "D:\Dev Debug\VR Modding\..."`
        # command line - a tool incantation, not a routing instruction. The
        # check was green while the instruction did not exist, which is the
        # vacuous-test failure this playbook catalogues, in its own verifier.
        #
        # An agent arriving with a SYMPTOM needs a door to walk through, so
        # require at least one entry-point document by name, and require it
        # somewhere other than a graphify command line.
        routing = "\n".join(
            line for line in both.splitlines()
            if "graphify" not in line.lower() and "--graph" not in line.lower()
        ).lower()
        if not any(door in routing for door in PLAYBOOK_DOORS):
            problems.append(
                f"{name}: no playbook entry point named outside a graphify command - "
                f"an agent with a symptom has no door to walk through. Name one of: "
                + ", ".join(sorted(PLAYBOOK_DOORS))
            )
        for skill in ("re-mcp-toolkit", "vr-re-workflow"):
            if skill not in both:
                problems.append(f"{name}: neither file names the {skill!r} skill")

        # Codex has no skill mechanism and auto-loads AGENTS.md ONLY, so this one
        # deliberately does not fall back to CLAUDE.md. An earlier version did, and a
        # test that stripped every tool name from AGENTS.md still passed - CLAUDE.md
        # answered for it, which is precisely the reader that does not need the help.
        # Naming SOME tool is not enough either. Audited 2026-09-01: every project
        # named 8-9 of the 12 configured MCP servers, and the systematic gaps were
        # `local-llm` (missing from ALL EIGHT, despite having its own delegation
        # skill) and `cheatengine` (also all eight). A Codex session sees only
        # AGENTS.md, so a server absent from it does not exist as far as that
        # session is concerned.
        for server in ("local-llm", "cheatengine"):
            if server not in a.lower():
                problems.append(
                    f"{name}: AGENTS.md never names {server!r} - it is a configured "
                    f"MCP server, so omitting it hides a live tool from Codex"
                )

        if not any(tool in a.lower() for tool in RE_TOOL_NAMES):
            problems.append(
                f"{name}: AGENTS.md names no concrete RE tool - a Codex session "
                f"cannot load a skill, so pointing at one is not enough"
            )

    detail = f"{checked} project pairs"
    if problems:
        return label, False, detail + "\n  " + "\n  ".join(problems)
    return label, True, detail


def reference_maths() -> tuple[str, bool, str]:
    """Run the compiled appendix reference tests, and insist they are not stale.

    The maths in docs/a1..a5 was read-only for a long time: it referenced types that
    existed nowhere, so none of it had ever been compiled. Building it found three real
    defects - an epoch that never rebased, a residual computed in the wrong matrix
    convention, and a test file that was never added to the build.

    This deliberately does NOT invoke a compiler. Shelling out to a vcvars batch file
    from here hangs, and a check that hangs is worse than no check. Instead it runs the
    binary that build-and-test.bat produced and FAILS if any source is newer than it, so
    a change without a rebuild is a red line rather than a silent pass.
    """
    label = "reference maths"
    ref = ROOT / "reference"
    if not ref.is_dir():
        return (label, True, "skipped: reference/ not present")

    exe = ref / "build" / "vrref_tests.exe"
    if not exe.exists():
        return (label, True, "skipped: not built - run reference/build-and-test.bat")

    built = exe.stat().st_mtime
    sources = list((ref / "tests").rglob("*.cpp")) + list((ref / "include").rglob("*.h"))
    stale = sorted(f.relative_to(ROOT).as_posix() for f in sources if f.stat().st_mtime > built)
    if stale:
        listing = "\n".join(f"- {f}" for f in stale)
        return (label, False,
                "the test binary is older than these sources:\n" + listing +
                "\n\nRun: reference\\build-and-test.bat")

    try:
        proc = subprocess.run([str(exe)], cwd=ref, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return (label, False, f"could not run {exe.name}: {exc}")

    out = (proc.stdout or "") + (proc.stderr or "")
    summary = next((ln.strip() for ln in reversed(out.splitlines())
                    if "checks" in ln and "tests" in ln), "")
    return (label, proc.returncode == 0, out if proc.returncode else summary)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run every playbook check.")
    parser.add_argument("--quick", action="store_true",
                        help="skip the site build and anchor audit")
    parser.add_argument("--portable", action="store_true",
                        help="skip checks requiring sibling fleet source trees")
    args = parser.parse_args()

    py = sys.executable
    results = []
    if not args.portable:
        results.append(run("source coverage ledger", [py, "tools/coverage.py", "--check"]))
    results.extend([
        run("bottleneck ledger", [py, "tools/bottlenecks.py", "--check"]),
        run("retrieval ID integrity", [py, "tools/playbook_integrity.py", "--check"]),
        audit_entry_points(),
    ])
    if not args.portable:
        results.append(audit_project_instructions())
    results.append(reference_maths())

    if not args.quick:
        results.append(run("strict site build", ["mkdocs", "build", "--strict"]))
        results.append(audit_anchors())

    width = max(len(label) for label, _, _ in results)
    failed = [r for r in results if not r[1]]

    for label, ok, detail in results:
        note = ""
        if ok and detail:
            note = "  " + detail.splitlines()[-1][:70]
        print(f"{'PASS' if ok else 'FAIL'}  {label:<{width}}{note}")

    if failed:
        for label, _, detail in failed:
            print(f"\n----- {label} -----\n{detail or '(no output)'}")
        print(f"\n{len(failed)} of {len(results)} CHECKS FAILED")
        return 1

    print(f"\nall {len(results)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
