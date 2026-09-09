#!/usr/bin/env python3
"""Validate the fleet bottleneck ledger and generate deterministic fragments.

The bottleneck ledger records operational judgements: what blocked a gate, on
which project, how it was classified, and what proof clears it. This script
keeps the cross-project matrix and per-project focus table synchronized with
the fleet declared in sources.yml.

Usage:
  python tools/bottlenecks.py
  python tools/bottlenecks.py --check
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required. Install: pip install -r requirements.txt")

from strict_yaml import load_unique_yaml


ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "bottlenecks.yml"
SOURCES = ROOT / "sources.yml"
OUTPUTS = {
    ROOT / "docs" / "generated" / "bottleneck-matrix.md": "matrix",
    ROOT / "docs" / "generated" / "project-bottleneck-focus.md": "focus",
}

ID_RE = re.compile(r"^BN-[A-Z0-9]+-[0-9]{3}$")
STATE_VALUES = ("active", "open", "risk", "cleared", "na")
APPLIES_TO_VALUES = ("re", "source", "both", "hybrid")
EVIDENCE_VALUES = ("SPEC", "SOURCE", "STATIC", "LIVE", "HEADSET", "AUTHOR", "INFERENCE")
STATE_MARK = {
    "active": "🟥 active",
    "open": "🟧 open",
    "risk": "🟨 risk",
    "cleared": "🟩 cleared",
    "na": "—",
}


class LedgerError(Exception):
    """Actionable bottleneck-ledger validation failure."""


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = load_unique_yaml(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LedgerError(f"missing {path.name}") from exc
    except yaml.YAMLError as exc:
        raise LedgerError(f"invalid YAML in {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise LedgerError(f"{path.name} must contain a mapping")
    return value


def md(value: Any) -> str:
    if value in (None, ""):
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def source_fleet() -> tuple[list[str], dict[str, str], dict[str, str]]:
    cfg = load_yaml(SOURCES)
    entries = cfg.get("fleet")
    if not isinstance(entries, list) or not entries:
        raise LedgerError("sources.yml fleet must be a non-empty list")
    ids: list[str] = []
    display: dict[str, str] = {}
    authority: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("id"):
            raise LedgerError("every sources.yml fleet entry needs an id")
        project_id = str(entry["id"])
        ids.append(project_id)
        display[project_id] = str(entry.get("display_name", project_id))
        if not entry.get("authority"):
            raise LedgerError(f"sources.yml fleet entry {project_id!r} needs authority")
        authority[project_id] = str(entry["authority"])
    return ids, display, authority


def validate(cfg: dict[str, Any], fleet_ids: list[str]) -> None:
    errors: list[str] = []
    if not fleet_ids:
        errors.append("no fleet projects to validate")
    fleet = set(fleet_ids)
    records = cfg.get("bottlenecks")
    if not isinstance(records, list) or not records:
        errors.append("bottlenecks must be a non-empty list")
        records = []

    seen: set[str] = set()
    required = ("id", "title", "applies_to", "gate", "blocks", "fast_test", "exit_proof", "route")
    for index, record in enumerate(records):
        label = f"bottlenecks[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} must be a mapping")
            continue
        for field in required:
            if not record.get(field):
                errors.append(f"{label} is missing {field!r}")
        bid = str(record.get("id", ""))
        if not ID_RE.fullmatch(bid):
            errors.append(f"{label}.id must match BN-DOMAIN-000, got {bid!r}")
        if bid in seen:
            errors.append(f"duplicate bottleneck id {bid!r}")
        seen.add(bid)
        if "mode" in record:
            errors.append(f"{label}.mode is deprecated: use applies_to")
        if record.get("applies_to") not in APPLIES_TO_VALUES:
            errors.append(f"{label}.applies_to must be one of {APPLIES_TO_VALUES}")
        projects = record.get("projects") or {}
        if not isinstance(projects, dict):
            errors.append(f"{label}.projects must be a mapping")
            continue
        for project_id, occurrence in projects.items():
            plabel = f"{label}.projects.{project_id}"
            if project_id not in fleet:
                errors.append(f"{plabel} is not present in sources.yml fleet")
            if not isinstance(occurrence, dict):
                errors.append(f"{plabel} must be a mapping")
                continue
            if occurrence.get("state") not in STATE_VALUES:
                errors.append(f"{plabel}.state must be one of {STATE_VALUES}")
            evidence = occurrence.get("evidence")
            if evidence is not None and evidence not in EVIDENCE_VALUES:
                errors.append(f"{plabel}.evidence must be one of {EVIDENCE_VALUES}")
            if occurrence.get("state") in ("active", "open", "cleared") and not evidence:
                errors.append(f"{plabel} needs evidence for state {occurrence.get('state')!r}")
            if not occurrence.get("note"):
                errors.append(f"{plabel} needs a concise note")

    focus = cfg.get("project_focus")
    if not isinstance(focus, list):
        errors.append("project_focus must be a list")
        focus = []
    focus_ids: list[str] = []
    for index, item in enumerate(focus):
        label = f"project_focus[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be a mapping")
            continue
        for field in ("project", "stage", "primary", "current_question", "next_proof", "source"):
            if not item.get(field):
                errors.append(f"{label} is missing {field!r}")
        project_id = str(item.get("project", ""))
        focus_ids.append(project_id)
        if project_id not in fleet:
            errors.append(f"{label}.project is not present in sources.yml fleet")
        primary = item.get("primary") or []
        if not isinstance(primary, list):
            errors.append(f"{label}.primary must be a list")
        else:
            for bid in primary:
                if bid not in seen:
                    errors.append(f"{label}.primary references unknown bottleneck {bid!r}")
    if len(focus_ids) != len(set(focus_ids)):
        errors.append("project_focus contains duplicate project ids")
    missing = [project_id for project_id in fleet_ids if project_id not in set(focus_ids)]
    extra = [project_id for project_id in focus_ids if project_id not in fleet]
    if missing:
        errors.append(f"project_focus is missing fleet projects: {', '.join(missing)}")
    if extra:
        errors.append(f"project_focus contains non-fleet projects: {', '.join(extra)}")

    if errors:
        raise LedgerError("\n".join(f"- {error}" for error in errors))


def occurrence_cell(record: dict[str, Any], project_id: str) -> str:
    occurrence = (record.get("projects") or {}).get(project_id)
    if not occurrence:
        return "—"
    return STATE_MARK[occurrence["state"]]


def generate_matrix(cfg: dict[str, Any], fleet_ids: list[str], display: dict[str, str]) -> str:
    lines = [
        "<!-- Generated by tools/bottlenecks.py from bottlenecks.yml. Do not edit. -->",
        "",
        "Legend: 🟥 **active critical path** · 🟧 **open, not current critical path** · "
        "🟨 **known risk not yet exercised** · 🟩 **cleared with evidence** · — **no recorded evidence / not applicable**.",
        "",
        "A green cell does not mean the subsystem is perfect. It means the named bottleneck no longer blocks the next gate.",
        "",
        "| Bottleneck | Applies to | Gate | " + " | ".join(display[item] for item in fleet_ids) + " |",
        "|---|---|---|" + "---|" * len(fleet_ids),
    ]
    for record in cfg["bottlenecks"]:
        cells = " | ".join(occurrence_cell(record, project_id) for project_id in fleet_ids)
        lines.append(
            f"| **{record['id']}** — {md(record['title'])} | `{md(record['applies_to'])}` | "
            f"{md(record['gate'])} | {cells} |"
        )

    lines.extend(["", "## Bottleneck definitions", ""])
    for record in cfg["bottlenecks"]:
        lines.extend([
            f"### {record['id']} — {record['title']}",
            "",
            f"**Applies to:** `{record['applies_to']}`  ",
            f"**Blocks:** {record['blocks']}  ",
            f"**Fast discriminator:** {record['fast_test']}  ",
            f"**Exit proof:** {record['exit_proof']}  ",
            f"**Route:** {record['route']}",
            "",
            "| Project | State | Evidence | Fleet note |",
            "|---|---|---|---|",
        ])
        projects = record.get("projects") or {}
        if projects:
            for project_id in fleet_ids:
                occurrence = projects.get(project_id)
                if not occurrence:
                    continue
                lines.append(
                    f"| **{md(display[project_id])}** | {STATE_MARK[occurrence['state']]} | "
                    f"`{md(occurrence.get('evidence'))}` | {md(occurrence['note'])} |"
                )
        else:
            lines.append("| — | — | — | No fleet occurrence recorded yet. |")
        lines.append("")
    return "\n".join(lines)


def generate_focus(
    cfg: dict[str, Any],
    display: dict[str, str],
    authority: dict[str, str],
) -> str:
    lines = [
        "<!-- Generated by tools/bottlenecks.py from bottlenecks.yml. Do not edit. -->",
        "",
        "This is a routing view, not a promise that every listed question is the project's only open work.",
        "",
        "| Project | Integration authority | Stage | Current limiting question | Bottleneck | Next proof | Evidence source |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in cfg["project_focus"]:
        links = ", ".join(f"`{bid}`" for bid in item["primary"])
        lines.append(
            f"| **{md(display[item['project']])}** | `{md(authority[item['project']])}` | {md(item['stage'])} | "
            f"{md(item['current_question'])} | {links} | {md(item['next_proof'])} | `{md(item['source'])}` |"
        )
    return "\n".join(lines + [""])


def render(
    cfg: dict[str, Any],
    fleet_ids: list[str],
    display: dict[str, str],
    authority: dict[str, str],
) -> dict[Path, str]:
    return {
        path: (
            generate_matrix(cfg, fleet_ids, display)
            if kind == "matrix"
            else generate_focus(cfg, display, authority)
        )
        for path, kind in OUTPUTS.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated fragments differ")
    args = parser.parse_args()
    try:
        fleet_ids, display, authority = source_fleet()
        cfg = load_yaml(LEDGER)
        validate(cfg, fleet_ids)
        outputs = render(cfg, fleet_ids, display, authority)
    except LedgerError as exc:
        print(f"bottleneck ledger validation failed:\n{exc}", file=sys.stderr)
        return 1

    stale: list[str] = []
    for path, content in outputs.items():
        expected = content.rstrip() + "\n"
        if args.check:
            actual = path.read_text(encoding="utf-8") if path.exists() else ""
            if actual != expected:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8", newline="\n")
            print(f"wrote {path.relative_to(ROOT)}")
    if stale:
        print("generated bottleneck files are stale; run python tools/bottlenecks.py", file=sys.stderr)
        for path in stale:
            print(f"- {path}", file=sys.stderr)
        return 1
    if args.check:
        print(f"bottleneck ledger OK: {len(cfg['bottlenecks'])} classes, {len(fleet_ids)} fleet projects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
