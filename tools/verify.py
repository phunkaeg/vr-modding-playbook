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


def run(label: str, argv: list[str]) -> tuple[str, bool | None, str]:
    """Run a command, capturing everything. Never pipes; exit code is authoritative."""
    try:
        proc = subprocess.run(
            argv, cwd=ROOT, capture_output=True, text=True, timeout=600
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return label, False, f"could not run: {exc}"
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode == 2 or (proc.returncode == 0 and not output.strip()):
        return label, None, output.strip() or "no check output"
    return label, proc.returncode == 0, output.strip()


def site_html_for(md_rel: str) -> Path:
    stem = md_rel[:-3]
    if stem.lower() in ("readme", "index"):
        return SITE / "index.html"
    return SITE / stem / "index.html"


def audit_anchors() -> tuple[str, bool | None, str]:
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
    if not files:
        return "internal anchors", None, "no documents to audit"

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
    if checked == 0:
        return "internal anchors", None, detail
    return "internal anchors", True, detail


ROOT_DOCS = ("AGENTS.md", "CLAUDE.md", "README.md")
FILE_LINK = re.compile(r"\]\((?!https?:|#)([A-Za-z0-9._/-]+?)(#[a-z0-9._-]+)?\)")


def audit_entry_points() -> tuple[str, bool | None, str]:
    """Root-level routing files are outside docs/, so nothing else checks their links.

    They are the files most certain to be read, and a dead path in one sends a
    reader nowhere with no error anywhere.
    """
    broken: list[str] = []
    checked = 0
    present = [n for n in ROOT_DOCS if (ROOT / n).exists()]
    if len(present) != len(ROOT_DOCS):
        return "entry-point links", None, "missing required root routing files: " + ", ".join(set(ROOT_DOCS) - set(present))

    for name in present:
        text = (ROOT / name).read_text(encoding="utf-8", errors="ignore")
        for target, _anchor in FILE_LINK.findall(text):
            checked += 1
            if not (ROOT / target).exists():
                broken.append(f"{name} -> {target}  [not found]")

    detail = f"{checked} links across {', '.join(present)}"
    if broken:
        return "entry-point links", False, detail + "\n  " + "\n  ".join(broken)
    if checked == 0:
        return "entry-point links", None, detail
    return "entry-point links", True, detail


def audit_project_instructions() -> tuple[str, bool | None, str]:
    """Each fleet project's instruction files must point at each other AND route.

    Claude Code auto-loads CLAUDE.md; Codex auto-loads AGENTS.md. Neither reads
    the other by default, so content in only one file is invisible to one tool.
    The two files are NOT required to match - they are allowed to carry
    different content - but each must tell its reader the other exists.

    This gap ran silently for a long time: four projects kept their hard rules
    in CLAUDE.md only, so Codex never saw them.

    Both hosts can read SKILL.md files. The pair must route to the playbook,
    relevant skills, and the contribution workflow. Tool names are navigation
    hints; availability is established by discovery in the active session.
    """
    label = "project instruction pairs"
    try:
        import yaml
        cfg = yaml.safe_load((ROOT / "sources.yml").read_text(encoding="utf-8"))
    except Exception as exc:
        return label, None, f"cannot read sources.yml: {exc}"

    if not isinstance(cfg, dict) or not cfg.get("fleet"):
        return label, None, "no fleet entries"

    problems: list[str] = []
    checked = 0
    for entry in cfg.get("fleet") or []:
        root = entry.get("root")
        if not root:
            problems.append("fleet entry has no root")
            continue
        proj = Path(root)
        if not proj.is_dir():
            problems.append(f"{entry.get('id')}: root unavailable: {root}; use --portable to omit this check")
            continue
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

        # Do not require a fixed MCP roster: desktop/terminal sessions differ.
        if not any(tool in low for tool in RE_TOOL_NAMES):
            problems.append(
                f"{name}: instruction pair names no concrete RE tool"
            )
        if "research-receipts.md" not in low:
            problems.append(f"{name}: no research-receipts.md contribution route")

    detail = f"{checked} project pairs"
    if problems:
        return label, False, detail + "\n  " + "\n  ".join(problems)
    if checked == 0:
        return label, None, detail
    return label, True, detail


def reference_maths() -> tuple[str, bool | None, str]:
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
        return (label, None, "reference/ not present")

    exe = ref / "build" / "vrref_tests.exe"
    if not exe.exists():
        return (label, None, "not built - run reference/build-and-test.bat")

    built = exe.stat().st_mtime
    sources = list((ref / "tests").rglob("*.cpp")) + list((ref / "include").rglob("*.h"))
    if not sources:
        return label, None, "no reference sources"
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
    if proc.returncode == 0 and not re.search(r"\b[1-9][0-9]* tests\b", summary):
        return label, None, "test executable reported no positive test count: " + out
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
        # Missing reference trees are NO_DATA, never a passing empty census.
        results.append(run("interaction coverage",
                           [py, "tools/interaction_coverage.py", "--check"]))
    results.extend([
        run("bottleneck ledger", [py, "tools/bottlenecks.py", "--check"]),
        run("retrieval ID integrity", [py, "tools/playbook_integrity.py", "--check"]),
        audit_entry_points(),
    ])
    if not args.portable:
        results.append(audit_project_instructions())
    results.append(reference_maths())

    results.append(integration_tests())
    if not args.quick:
        results.append(strict_site_build())
        results.append(audit_anchors())

    width = max(len(label) for label, _, _ in results)
    failed = [r for r in results if r[1] is False]
    unavailable = [r for r in results if r[1] is None]

    for label, ok, detail in results:
        note = ""
        if ok and detail:
            note = "  " + detail.splitlines()[-1][:70]
        status = "NO_DATA" if ok is None else "PASS" if ok else "FAIL"
        if ok is None:
            note = "  " + detail
        print(f"{status}  {label:<{width}}{note}")

    if args.quick:
        print("SKIP  strict site build / internal anchors (--quick)")
    if args.portable:
        print("SKIP  source coverage / interaction coverage / project pairs (--portable)")

    if failed:
        for label, _, detail in failed:
            print(f"\n----- {label} -----\n{detail or '(no output)'}")
        print(f"\n{len(failed)} of {len(results)} CHECKS FAILED")
        return 1

    if unavailable:
        print(f"\nINCOMPLETE: {len(unavailable)} required checks did not execute")
        return 2

    print(f"\nall {len(results)} checks passed")
    return 0


def strict_site_build() -> tuple[str, bool | None, str]:
    if not (ROOT / "mkdocs.yml").is_file() or not list(DOCS.glob("*.md")):
        return "strict site build", None, "missing configuration or document corpus"
    return run("strict site build", [sys.executable, "-m", "mkdocs", "build", "--strict"])


def integration_tests() -> tuple[str, bool | None, str]:
    label, ok, detail = run("integration regression tests",
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    if ok and not re.search(r"Ran [1-9][0-9]* tests?\b", detail):
        return label, None, "no positive test count: " + detail
    return label, ok, detail


if __name__ == "__main__":
    sys.exit(main())
