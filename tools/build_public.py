#!/usr/bin/env python3
"""Build a shareable variant of the playbook with the internal status report removed.

WHAT THIS DOES AND DOES NOT DO
------------------------------
It does NOT hide that the in-house projects exist. Their names are cited on
almost every page - "FarCry2-VR measured...", "SS2VR spent headset sessions on
it" - and that attribution is the content. Removing it would gut the playbook.

What it removes is the STATUS REPORT on unreleased work, plus local paths:

  * docs/coverage.md              per-project review depth, tree revisions,
                                  source roots, `internal-unreleased` licences
  * generated/fleet-table.md      every fleet project's root, licence, tier, rung
  * generated/bottleneck-matrix.md      per-project blocked/cleared state
  * generated/project-bottleneck-focus.md   current limiting question, NEXT PROOF,
                                  and the CURRENT_STATE path each cites
  * local absolute paths in the hand-written pages

generated/source-summary.md is KEPT: it carries aggregate counts only, no names.

The build fails loudly if any banned string survives into the output. A
sanitiser that cannot prove it worked is worth nothing.

Usage:
  python tools/build_public.py            # build to site-public/
  python tools/build_public.py --serve    # build, then serve it on :8001
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = ROOT / "site-public"

# Pages dropped entirely (also removed from nav).
DROP_PAGES = {"coverage.md"}

# Snippet includes replaced with a short note.
DROP_INCLUDES = {
    "generated/fleet-table.md",
    "generated/bottleneck-matrix.md",
    "generated/project-bottleneck-focus.md",
}

NOTE = ("!!! note \"Omitted from the shared build\"\n\n"
        "    This section carries the in-house project status table, which is not\n"
        "    part of the shared copy. The method around it is unchanged.\n")

# Local-path rewrites applied to hand-written pages.
PATH_SUBS = [
    (re.compile(r"`D:\\Dev Debug\\mcp-updates\\([A-Za-z0-9_.-]+)`"), r"`<tools-repo>/\1`"),
    (re.compile(r"`D:\\Dev Debug\\Other VR mods\\`", re.I), "`<external-mods>/`"),
    (re.compile(r"`D:\\Dev Debug\\Other VR Mods\\`", re.I), "`<external-mods>/`"),
    (re.compile(r"`D:\\Dev Debug\\([A-Za-z0-9 _.-]+)\\`"), r"`<projects>/\1/`"),
    (re.compile(r"D:[\\/]Dev Debug"), "<workspace>"),
]

def _fleet_dirs() -> list[str]:
    """Fleet project directory names, read from the ledger so this stays current."""
    try:
        import yaml
        cfg = yaml.safe_load((ROOT / "sources.yml").read_text(encoding="utf-8"))
        names = set()
        for entry in cfg.get("fleet", []):
            root = str(entry.get("root", ""))
            if root:
                names.add(re.split(r"[\\/]", root.rstrip("/\\"))[-1])
            if entry.get("id"):
                names.add(str(entry["id"]))
        return sorted(n for n in names if n)
    except Exception:
        return []


FLEET_DIRS = _fleet_dirs()

# Relative internal doc paths, in either slash style:
#   `ss2vr-work\docs\FAILURE_REGISTRY.md`   `FarCry2-vr/docs/CURRENT_STATE.md`
# Matched case-insensitively because the same project is written several ways.
if FLEET_DIRS:
    _alt = "|".join(re.escape(n) for n in FLEET_DIRS)
    PATH_SUBS.append(
        (re.compile(r"(?:" + _alt + r")[\\/](docs[\\/][A-Za-z0-9_./\\-]*)", re.I),
         r"<project>/\1")
    )
PATH_SUBS.append(
    (re.compile(r"`cross-engine-graph\\([A-Za-z0-9_\\.*-]+)`"),
     r"`<workspace>/cross-engine-graph/\1`")
)

# Anything matching these in the built output is a failure.
BANNED = [
    ("local workspace path", re.compile(r"D:[\\/]Dev Debug", re.I)),
    ("user profile path", re.compile(r"C:[\\/]Users[\\/][A-Za-z0-9_.-]+", re.I)),
    ("unreleased licence marker", re.compile(r"internal-unreleased")),
    ("OneDrive path", re.compile(r"[A-Za-z]:[\\/][^\s\"<]*OneDrive")),
]

if FLEET_DIRS:
    BANNED.append((
        "internal project path",
        re.compile(r"(?:" + "|".join(re.escape(n) for n in FLEET_DIRS) + r")[\\/]docs[\\/]"),
    ))


def prepare(src_docs: Path, dst_docs: Path) -> list[str]:
    """Copy docs, dropping pages, neutering includes, rewriting paths."""
    actions: list[str] = []
    shutil.copytree(src_docs, dst_docs)

    for name in DROP_PAGES:
        target = dst_docs / name
        if target.exists():
            target.unlink()
            actions.append(f"dropped page {name}")

    for md in sorted(dst_docs.rglob("*.md")):
        text = original = md.read_text(encoding="utf-8")

        for inc in DROP_INCLUDES:
            pattern = re.compile(r'^--8<--\s+"' + re.escape(inc) + r'"\s*$', re.M)
            if pattern.search(text):
                text = pattern.sub(NOTE, text)
                actions.append(f"{md.relative_to(dst_docs)}: removed include {inc}")

        # Drop links to pages that no longer exist.
        for name in DROP_PAGES:
            stem = name[:-3]
            text = re.sub(r"\[([^\]]+)\]\(" + re.escape(name) + r"(#[a-z0-9-]*)?\)", r"\1", text)
            text = re.sub(r"\[([^\]]+)\]\(" + re.escape(stem) + r"(#[a-z0-9-]*)?\)", r"\1", text)

        for pattern, repl in PATH_SUBS:
            new = pattern.sub(repl, text)
            if new != text:
                actions.append(f"{md.relative_to(dst_docs)}: rewrote a local path")
                text = new

        if text != original:
            md.write_text(text, encoding="utf-8")
    return actions


def write_config(tmp: Path, docs_dir: Path) -> Path:
    """Derive a config from mkdocs.yml: new docs_dir, no dropped pages in nav."""
    cfg = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    cfg = cfg.replace("docs_dir: docs", f"docs_dir: {docs_dir.as_posix()}")
    # snippets' base_path is relative to the repo root, so it would otherwise pull
    # the ORIGINAL generated fragments straight past every sanitiser here.
    cfg = cfg.replace("base_path: docs", f"base_path: {docs_dir.as_posix()}")
    kept = []
    for line in cfg.splitlines():
        if any(re.search(r":\s*" + re.escape(p) + r"\s*$", line) for p in DROP_PAGES):
            continue
        kept.append(line)
    path = tmp / "mkdocs-public.yml"
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    return path


def audit(site: Path) -> list[str]:
    """Every banned pattern must be absent from the built output."""
    problems: list[str] = []
    for f in site.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in {".html", ".js", ".json", ".xml", ".txt"}:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for label, pattern in BANNED:
            hit = pattern.search(text)
            if hit:
                problems.append(f"{label}: {f.relative_to(site)} -> {hit.group(0)[:60]}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the shareable playbook variant.")
    ap.add_argument("--serve", action="store_true", help="serve the result on :8001 after building")
    args = ap.parse_args()

    if OUT.exists():
        try:
            shutil.rmtree(OUT)
        except OSError as exc:
            # Almost always a server still serving site-public/ and holding a handle.
            print(f"Could not clear {OUT.name}/: {exc}")
            print("\nSomething is still using it - usually a running serve-shared.bat")
            print("or host-shared.bat. Stop that window and run this again.")
            print("Nothing was rebuilt, so the previous output is untouched.")
            return 1

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        docs_copy = tmp / "docs"
        actions = prepare(DOCS, docs_copy)
        cfg = write_config(tmp, docs_copy)

        proc = subprocess.run(
            ["mkdocs", "build", "--strict", "-f", str(cfg), "-d", str(OUT)],
            cwd=ROOT, capture_output=True, text=True,
        )
        if proc.returncode != 0:
            print("BUILD FAILED\n")
            print((proc.stdout or "") + (proc.stderr or ""))
            return 1

    for a in actions:
        print(f"  {a}")

    problems = audit(OUT)
    pages = len(list(OUT.rglob("*.html")))
    print(f"\nbuilt {pages} pages -> {OUT}")

    if problems:
        print(f"\nSANITISE CHECK FAILED - {len(problems)} leak(s):")
        for p in problems[:20]:
            print("  -", p)
        print("\nThe output was NOT cleaned. Do not publish it.")
        return 1

    print("sanitise check passed - no workspace paths, user paths, "
          "unreleased markers or OneDrive paths in the output")

    if args.serve:
        print("\nserving at http://127.0.0.1:8001  (Ctrl+C to stop)")
        subprocess.run([sys.executable, "-m", "http.server", "8001",
                        "--bind", "127.0.0.1", "-d", str(OUT)], cwd=ROOT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
