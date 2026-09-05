#!/usr/bin/env python3
"""Validate sources.yml and generate deterministic coverage fragments.

The ledger owns judgements and source identity. The generator owns measurable
filesystem facts: existence, file counts, newest change and the current tree
fingerprint. A fingerprint mismatch is shown as review staleness; it does not
silently change the human judgement about what was reviewed.

Usage:
  python tools/coverage.py
  python tools/coverage.py --check
  python tools/coverage.py --print-revisions
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required. Install: pip install -r requirements.txt")

from strict_yaml import load_unique_yaml


ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "sources.yml"
MODS = Path("D:/Dev Debug/Other VR mods")
OUTPUTS = {
    ROOT / "docs" / "coverage.md": "coverage",
    ROOT / "docs" / "generated" / "fleet-table.md": "fleet",
    ROOT / "docs" / "generated" / "source-summary.md": "summary",
}
CODE_EXT = {
    ".cpp", ".c", ".h", ".hpp", ".cs", ".rs", ".py", ".java", ".lua",
    ".nut", ".ws", ".reds", ".hlsl", ".glsl", ".vert", ".frag",
}
DOC_EXT = {".md", ".txt", ".rst", ".adoc"}
SKIP_DIRS = {
    ".git", "node_modules", "obj", "bin", "packages", ".vs", "build",
    "target", "vendor", "vendor-local", "__pycache__",
    # Scratch and log directories. The fingerprint below includes st_mtime_ns,
    # so a directory a project rewrites while it works makes the ledger stale on
    # every run and `verify.py` unpassable for anyone whose sibling happens to be
    # building. Measured: ss2vr-work/tmp/executor-*.ps1 changed between two
    # consecutive coverage runs three seconds apart, while its git tree was
    # stable - so the failure had nothing to do with the change under test.
    "tmp", "temp", ".tmp", "logs", ".cache",
}
REVIEW_VALUES = ("full", "partial", "skimmed", "not_reviewed")
EVIDENCE_VALUES = ("SPEC", "SOURCE", "STATIC", "LIVE", "HEADSET", "AUTHOR", "INFERENCE")
STATUS_VALUES = (
    "active_mod", "shipped_mod", "research_target", "external_reference",
    "archived_reference",
)
AUTHORITY_VALUES = (
    "re-owned",
    "source-owned",
    "script-owned",
    "hybrid-re+script",
    "hybrid-re+source-oracle",
    "hybrid-re+sdk-oracle",
)
VEHICLE_VALUES = (
    "native-injector",
    "managed-plugin",
    "framework",
    "framework-companion",
    "source-port",
    "engine-recreation",
    "script-native-hybrid",
)
TIER_VALUES = ("pre-T1", "T0", "T1", "T2", "T3", "T4")
TIER_TARGET_VALUES = ("T0", "T1", "T2", "T3", "T4")
STEREO_RUNG_VALUES = ("unproven", "R1", "R2", "R3", "R4")
SOURCE_OWNED_VEHICLES = ("source-port", "engine-recreation")
STEREO_RUNG_LABEL = {
    "unproven": "unproven",
    "R1": "R1 · native re-entry",
    "R2": "R2 · per-draw replay",
    "R3": "R3 · alternate-eye",
    "R4": "R4 · reconstruction",
}
REVIEW_MARK = {
    "full": "🟩 full",
    "partial": "🟨 partial",
    "skimmed": "🟧 skimmed",
    "not_reviewed": "🟥 not reviewed",
}
STATUS_LABEL = {
    "active_mod": "active mod",
    "shipped_mod": "shipped mod",
    "research_target": "research target",
    "external_reference": "external reference",
    "archived_reference": "archived reference",
}


class LedgerError(Exception):
    """Actionable ledger validation failure."""


def md(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def stereo_rung(value: Any) -> str:
    """Render the controlled rung code without weakening its stored vocabulary."""
    return STEREO_RUNG_LABEL.get(str(value), str(value))


def external_maturity(value: Any, rung: bool = False) -> str:
    """Render an external source's tier or rung, keeping three states distinct.

    Absent means nobody has assessed it; `unknown` means somebody looked and
    could not say - usually a binary-only source. Collapsing those two would
    make the column look complete when most of it is simply unexamined.
    """
    if value is None:
        return "—"
    if value == "unknown":
        return "?"
    return stereo_rung(value) if rung else md(value)


def scan(path: Path) -> dict[str, Any] | None:
    """Measure a source without interpreting its content."""
    if not path.is_dir():
        return None
    docs = code = total = 0
    newest = 0.0
    signature = hashlib.sha256()
    for directory, dirs, files in os.walk(path):
        dirs[:] = sorted(name for name in dirs if name not in SKIP_DIRS)
        for filename in sorted(files):
            file_path = Path(directory) / filename
            try:
                stat = file_path.stat()
            except OSError:
                continue
            total += 1
            suffix = file_path.suffix.lower()
            docs += suffix in DOC_EXT
            code += suffix in CODE_EXT
            newest = max(newest, stat.st_mtime)
            rel = file_path.relative_to(path).as_posix()
            signature.update(rel.encode("utf-8", errors="surrogatepass"))
            signature.update(b"\0")
            signature.update(str(stat.st_size).encode("ascii"))
            signature.update(b"\0")
            signature.update(str(stat.st_mtime_ns).encode("ascii"))
            signature.update(b"\n")
    measured = {
        "docs": docs,
        "code": code,
        "total": total,
        "newest": newest,
        "fingerprint": signature.hexdigest()[:16],
    }
    measured["revision"] = current_revision(path, measured)
    return measured


def current_revision(path: Path, measured: dict[str, Any]) -> str:
    """Identify file state without depending on Git trust or availability.

    Git commits are useful provenance, but they do not identify uncommitted
    files and `safe.directory` policy varies by execution account. Freshness
    therefore always compares the same tree-fingerprint vocabulary.
    """
    return f"tree:{measured['fingerprint']}"


def parse_date(value: Any, label: str, errors: list[str]) -> None:
    if value in (None, "", "unknown"):
        return
    try:
        dt.date.fromisoformat(str(value))
    except ValueError:
        errors.append(f"{label} must be YYYY-MM-DD or 'unknown', got {value!r}")


def validate(cfg: dict[str, Any]) -> None:
    errors: list[str] = []
    if not isinstance(cfg, dict):
        raise LedgerError("sources.yml must contain a mapping")
    areas = cfg.get("areas")
    if not isinstance(areas, list) or not areas or not all(isinstance(x, str) for x in areas):
        errors.append("areas must be a non-empty list of strings")
        areas = []
    elif len(areas) != len(set(areas)):
        errors.append("areas contains duplicate names")
    known_areas = set(areas)
    parse_date(cfg.get("ledger_updated_at"), "ledger_updated_at", errors)
    seen_ids: dict[str, str] = {}
    required = (
        "id", "root", "status", "upstream_url", "license", "reviewed_at",
        "reviewed_revision",
    )
    for section in ("fleet", "external"):
        entries = cfg.get(section, [])
        if not isinstance(entries, list):
            errors.append(f"{section} must be a list")
            continue
        for index, source in enumerate(entries):
            label = f"{section}[{index}]"
            if not isinstance(source, dict):
                errors.append(f"{label} must be a mapping")
                continue
            for field in required:
                if field not in source:
                    errors.append(f"{label} is missing required field {field!r}")
            sid = str(source.get("id", ""))
            canonical = sid.casefold()
            if canonical in seen_ids:
                errors.append(f"duplicate source id {sid!r} (also in {seen_ids[canonical]})")
            else:
                seen_ids[canonical] = label
            if source.get("status") not in STATUS_VALUES:
                errors.append(f"{label}.status must be one of {STATUS_VALUES}")
            parse_date(source.get("reviewed_at"), f"{label}.reviewed_at", errors)
            reviewed_revision = str(source.get("reviewed_revision", ""))
            if reviewed_revision not in ("unknown", "") and not re.fullmatch(
                r"tree:[0-9a-f]{16}", reviewed_revision
            ):
                errors.append(
                    f"{label}.reviewed_revision must be 'unknown' or tree:<16 lowercase hex>"
                )
            reviewed_git_commit = source.get("reviewed_git_commit")
            if reviewed_git_commit not in (None, "", "unknown") and not re.fullmatch(
                r"[0-9a-f]{40}", str(reviewed_git_commit)
            ):
                errors.append(
                    f"{label}.reviewed_git_commit must be 'unknown' or 40 lowercase hex"
                )
            if "mode" in source:
                errors.append(
                    f"{label}.mode is deprecated: use fleet.authority or external.vehicle"
                )
            if section == "fleet":
                for field in ("game", "engine", "api", "arch", "authority", "tier", "stereo_rung"):
                    if field not in source:
                        errors.append(f"{label} is missing required field {field!r}")
                if source.get("authority") not in AUTHORITY_VALUES:
                    errors.append(f"{label}.authority must be one of {AUTHORITY_VALUES}")
                if source.get("tier") not in TIER_VALUES:
                    errors.append(f"{label}.tier must be one of {TIER_VALUES}")
                target = source.get("tier_target")
                if target is not None and target not in TIER_TARGET_VALUES:
                    errors.append(f"{label}.tier_target must be one of {TIER_TARGET_VALUES}")
                if source.get("stereo_rung") not in STEREO_RUNG_VALUES:
                    errors.append(f"{label}.stereo_rung must be one of {STEREO_RUNG_VALUES}")
            else:
                for field in ("engine", "vehicle"):
                    if field not in source:
                        errors.append(f"{label} is missing required field {field!r}")
                if source.get("vehicle") not in VEHICLE_VALUES:
                    errors.append(f"{label}.vehicle must be one of {VEHICLE_VALUES}")
                # Maturity is OPTIONAL for external sources and shares the fleet
                # vocabulary. 'unknown' is an explicit "we looked and cannot say";
                # an absent key means "not assessed". Those are different claims
                # and the table renders them differently.
                ext_tier = source.get("tier")
                if ext_tier is not None and ext_tier not in TIER_VALUES + ("unknown",):
                    errors.append(
                        f"{label}.tier must be one of {TIER_VALUES + ('unknown',)} or absent"
                    )
                ext_rung = source.get("stereo_rung")
                if ext_rung is not None and ext_rung not in STEREO_RUNG_VALUES + ("unknown",):
                    errors.append(
                        f"{label}.stereo_rung must be one of "
                        f"{STEREO_RUNG_VALUES + ('unknown',)} or absent"
                    )
                if "tier_target" in source:
                    errors.append(
                        f"{label}.tier_target is fleet-only: an external project's intent is not ours to record"
                    )
                source_review = (source.get("areas") or {}).get("source_integration", {}).get("review")
                if source_review == "full" and source.get("vehicle") not in SOURCE_OWNED_VEHICLES:
                    errors.append(
                        f"{label}.areas.source_integration cannot be full for vehicle "
                        f"{source.get('vehicle')!r}; full requires one of {SOURCE_OWNED_VEHICLES}"
                    )
                chapter = source.get("chapter")
                if chapter is not None:
                    try:
                        number = int(chapter)
                    except (TypeError, ValueError):
                        errors.append(f"{label}.chapter must be an integer")
                    else:
                        if not list((ROOT / "docs").glob(f"{number:02d}-*.md")):
                            errors.append(f"{label}.chapter points at missing chapter {number:02d}")
            source_areas = source.get("areas") or {}
            if not isinstance(source_areas, dict):
                errors.append(f"{label}.areas must be a mapping")
                continue
            for area, entry in source_areas.items():
                if area not in known_areas:
                    errors.append(f"{label}.areas contains unknown area {area!r}")
                if not isinstance(entry, dict):
                    errors.append(f"{label}.areas.{area} must be a mapping")
                    continue
                review = entry.get("review")
                if review not in REVIEW_VALUES:
                    errors.append(f"{label}.areas.{area}.review must be one of {REVIEW_VALUES}")
                evidence = entry.get("evidence")
                if evidence is not None and evidence not in EVIDENCE_VALUES:
                    errors.append(f"{label}.areas.{area}.evidence must be one of {EVIDENCE_VALUES}")
                if review != "not_reviewed" and evidence is None:
                    errors.append(f"{label}.areas.{area} needs an evidence grade")
    if errors:
        raise LedgerError("\n".join(f"- {error}" for error in errors))


def review_counts(source: dict[str, Any], areas: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    source_areas = source.get("areas") or {}
    for area in areas:
        entry = source_areas.get(area)
        counts["none" if entry is None else entry["review"]] += 1
    return counts


def completeness(source: dict[str, Any], areas: list[str]) -> str:
    c = review_counts(source, areas)
    return f"{c['full']}F / {c['partial']}P / {c['skimmed']}S / {c['not_reviewed']}NR / {c['none']}—"


def freshness(source: dict[str, Any], measured: dict[str, Any] | None) -> str:
    if measured is None:
        return "🟥 path missing"
    reviewed = str(source.get("reviewed_revision", "unknown"))
    if reviewed in ("", "unknown", "local-snapshot"):
        return "⚪ unpinned"
    if reviewed == measured["revision"]:
        return "🟩 current"
    return "🟥 source changed"


def latest_date(measured: dict[str, Any] | None) -> str:
    if not measured or not measured["newest"]:
        return "—"
    return dt.date.fromtimestamp(measured["newest"]).isoformat()


def measure_sources(cfg: dict[str, Any]) -> dict[str, dict[str, Any] | None]:
    return {
        source["id"]: scan(Path(source["root"]))
        for section in ("fleet", "external")
        for source in cfg.get(section, [])
    }


def reader_corpus_metrics() -> tuple[int, int]:
    """Report the reader-visible Markdown corpus so growth is visible in every check."""
    docs_root = ROOT / "docs"
    files = [
        path
        for path in docs_root.rglob("*.md")
        if "generated" not in path.relative_to(docs_root).parts
        # coverage.md is generated output that happens to live in docs/. Counting
        # it makes the metric self-referential: regen writes the file, which
        # changes the corpus, so --check then reports the fresh file as stale and
        # only a second regen converges.
        and path.name != "coverage.md"
    ]
    words = sum(
        len(path.read_text(encoding="utf-8", errors="replace").split())
        for path in files
    )
    return len(files), words


# Folders that group sources rather than being one. The scan descends into these
# and reports their CHILDREN, so a grouping folder cannot become a place where new
# arrivals go unnoticed - which is the only thing the zero-untracked rule buys.
GROUPING_DIRS = {"binary-only", "monsterdeadwood"}


def find_untracked(cfg: dict[str, Any]) -> list[str]:
    known = {Path(source["root"]).name.casefold() for source in cfg.get("external", [])}
    known.update(item["id"].casefold() for item in cfg.get("not_a_source", []))
    if not MODS.is_dir():
        return []

    def walk(root: Path, prefix: str = "") -> list[str]:
        found: list[str] = []
        for directory in root.iterdir():
            if not directory.is_dir():
                continue
            if directory.name.casefold() in GROUPING_DIRS:
                found.extend(walk(directory, f"{prefix}{directory.name}/"))
                continue
            if directory.name.casefold() not in known:
                found.append(f"{prefix}{directory.name}")
        return found

    return sorted(walk(MODS), key=str.casefold)


def generate_summary(cfg: dict[str, Any]) -> str:
    statuses = Counter(source["status"] for source in cfg.get("fleet", []))
    external = cfg.get("external", [])
    uncovered = [
        area
        for area in cfg["areas"]
        if not any(
            (source.get("areas") or {}).get(area, {}).get("review") == "full"
            and (area != "source_integration" or source.get("vehicle") in SOURCE_OWNED_VEHICLES)
            for source in external
        )
    ]
    names = ", ".join(f"`{area}`" for area in uncovered) if uncovered else "none"
    active = statuses["active_mod"]
    targets = statuses["research_target"]
    references = len(external)
    if uncovered:
        gap_line = (
            f"**{len(uncovered)} area{'s' if len(uncovered) != 1 else ''} currently "
            f"{'have' if len(uncovered) != 1 else 'has'} no external source reviewed in full:** {names}."
        )
    else:
        gap_line = "**Every tracked knowledge area now has at least one external source reviewed in full.**"
    return "\n".join([
        "<!-- Generated by tools/coverage.py from sources.yml. Do not edit. -->",
        "",
        (
            f"The coverage ledger currently tracks **{active} active first-hand "
            f"conversion{'s' if active != 1 else ''}**, **{targets} research "
            f"target{'s' if targets != 1 else ''}** and **{references} external "
            f"reference{'s' if references != 1 else ''}** across **{len(cfg['areas'])} knowledge areas**."
        ),
        "",
        (
            f"{gap_line} See the [coverage dashboard](coverage.md) for live detail."
        ),
        "",
    ])


def generate_fleet(cfg: dict[str, Any]) -> str:
    lines = [
        "<!-- Generated by tools/coverage.py from sources.yml. Do not edit. -->",
        "",
        "| Project | Status | Game | Engine | Integration authority | Graphics API | Bits | Tier achieved | Tier target | Stereo route | Docs |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for source in cfg.get("fleet", []):
        docs_path = str(Path(source["root"]) / "docs").replace("/", "\\") + "\\"
        lines.append(
            f"| **{md(source.get('display_name', source['id']))}** | {md(STATUS_LABEL[source['status']])} | {md(source['game'])} | "
            f"{md(source['engine'])} | {md(source['authority'])} | {md(source['api'])} | {md(source['arch'])} | "
            f"{md(source['tier'])} | {md(source.get('tier_target'))} | {md(stereo_rung(source['stereo_rung']))} | `{md(docs_path)}` |"
        )
    return "\n".join(lines + [""])


def area_rollup(lines: list[str], title: str, sources: list[dict[str, Any]], areas: list[str]) -> None:
    lines.extend([
        f"## {title}",
        "",
        "| Area | full | partial | skimmed | not reviewed | no entry |",
        "|---|--:|--:|--:|--:|--:|",
    ])
    for area in areas:
        counts = Counter()
        for source in sources:
            entry = (source.get("areas") or {}).get(area)
            counts["none" if entry is None else entry["review"]] += 1
        flag = " ⚠" if counts["full"] == 0 else ""
        lines.append(
            f"| `{area}`{flag} | {counts['full']} | {counts['partial']} | {counts['skimmed']} | "
            f"{counts['not_reviewed']} | {counts['none']} |"
        )
    lines.extend(["", "⚠ = **no source in this group has been reviewed in full for this area.**", ""])


def generate_coverage(
    cfg: dict[str, Any],
    measured: dict[str, dict[str, Any] | None],
    untracked: list[str],
) -> str:
    areas = cfg["areas"]
    external = cfg.get("external", [])
    fleet = cfg.get("fleet", [])
    lines: list[str] = [
        "# Coverage dashboard",
        "",
        (
            f"**Generated deterministically by `tools/coverage.py` from `sources.yml` "
            f"(ledger updated {cfg.get('ledger_updated_at', 'unknown')}) plus a filesystem scan. "
            "Do not edit by hand.**"
        ),
        "",
        (
            "This page makes both knowledge gaps and stale reviews visible. `Last change` and "
            "`current revision` are measured; review depth, evidence and `reviewed revision` "
            "are human/agent judgements."
        ),
        "",
        "| Grade | Meaning |",
        "|---|---|",
    ]
    meanings = {
        "SPEC": "normative API fact",
        "SOURCE": "read in the project's own source",
        "STATIC": "binary / static reverse engineering",
        "LIVE": "observed at runtime",
        "HEADSET": "accepted in a headset",
        "AUTHOR": "the author's claim only",
        "INFERENCE": "hypothesis, not established on this target",
    }
    for grade in EVIDENCE_VALUES:
        lines.append(f"| `{grade}` | {meanings[grade]} |")
    lines.extend([
        "",
        "Coverage mix uses `F / P / S / NR / —` = full / partial / skimmed / explicitly not reviewed / no entry.",
        "Fleet `authority` and external `vehicle` are different controlled axes. `tier` is achieved; `tier_target` is optional intent (fleet only).",
        "External `Tier` and `Rung` are **inferred from the review**, not measured by us — `[INFERENCE]` unless the source states it. `—` means not assessed; `?` means assessed as indeterminable, which is the honest answer for a binary-only source.",
        "A full `source_integration` review counts as source-owned coverage only for a `source-port` or `engine-recreation` vehicle.",
        "",
    ])

    gaps: list[tuple[str, str, str]] = []
    for source in external:
        source_areas = source.get("areas") or {}
        for area in areas:
            entry = source_areas.get(area)
            if (entry is None or entry.get("review") == "not_reviewed") and (entry or {}).get("note"):
                gaps.append((area, source["id"], entry["note"]))
    lines.extend([
        "## Named gaps — material identified but not yet harvested",
        "",
        "| Area | Source | What is sitting there |",
        "|---|---|---|",
    ])
    if gaps:
        for area, source_id, note in sorted(gaps):
            lines.append(f"| `{area}` | **{md(source_id)}** | {md(note)} |")
    else:
        lines.append("| — | — | No named gaps. |")
    lines.append("")

    area_rollup(lines, "External coverage by area", external, areas)
    area_rollup(lines, "Fleet harvest coverage by area", fleet, areas)

    lines.extend([
        "## External sources",
        "",
        "| Source | Status | Engine | Delivery vehicle | Tier | Rung | Ch | Files | Code | Docs | Last change | Freshness | Area completeness |",
        "|---|---|---|---|:--:|:--:|--:|--:|--:|--:|---|---|---|",
    ])
    for source in sorted(external, key=lambda item: item["id"].casefold()):
        info = measured[source["id"]]
        if info is None:
            lines.append(
                f"| **{md(source['id'])}** | {md(STATUS_LABEL[source['status']])} | {md(source.get('engine'))} | "
                f"{md(source.get('vehicle'))} | {external_maturity(source.get('tier'))} | "
                f"{external_maturity(source.get('stereo_rung'), rung=True)} | "
                f"{md(source.get('chapter'))} | — | — | — | — | "
                f"🟥 path missing | {completeness(source, areas)} |"
            )
        else:
            lines.append(
                f"| **{md(source['id'])}** | {md(STATUS_LABEL[source['status']])} | {md(source.get('engine'))} | "
                f"{md(source.get('vehicle'))} | {external_maturity(source.get('tier'))} | "
                f"{external_maturity(source.get('stereo_rung'), rung=True)} | "
                f"{md(source.get('chapter'))} | {info['total']} | {info['code']} | "
                f"{info['docs']} | {latest_date(info)} | {freshness(source, info)} | {completeness(source, areas)} |"
            )
    lines.extend([
        "",
        "## Review freshness",
        "",
        (
            "A red row means the source tree no longer matches the snapshot that was reviewed. "
            "Re-review the affected areas; do not merely copy the new fingerprint."
        ),
        "",
        "| Source | Reviewed at | Reviewed tree | Current tree | Reviewed Git commit | Result | Upstream | License |",
        "|---|---|---|---|---|---|---|---|",
    ])
    for section in ("fleet", "external"):
        for source in sorted(cfg.get(section, []), key=lambda item: item["id"].casefold()):
            info = measured[source["id"]]
            lines.append(
                f"| **{md(source['id'])}** | {md(source.get('reviewed_at'))} | "
                f"`{md(source.get('reviewed_revision'))}` | "
                f"`{md(info['revision'] if info else 'path missing')}` | "
                f"`{md(source.get('reviewed_git_commit'))}` | {freshness(source, info)} | "
                f"{md(source.get('upstream_url'))} | {md(source.get('license'))} |"
            )

    lines.extend(["", "## Untracked directories", ""])
    if untracked:
        lines.extend([
            "**Present under `Other VR mods/`, absent from the ledger. `--check` fails until classified.**",
            "",
        ])
        for name in untracked:
            info = scan(MODS / name) or {}
            lines.append(f"- `{md(name)}` — {info.get('total', '?')} files, {info.get('code', '?')} code files")
    else:
        lines.append("None. Every directory under `Other VR mods/` is tracked or explicitly classified as not-a-source.")
    lines.extend(["", "### Deliberately not sources", ""])
    for item in cfg.get("not_a_source", []):
        lines.append(f"- `{md(item['id'])}` — {md(item['reason'])}")

    lines.extend([
        "",
        "## Fleet projects",
        "",
        "| Project | Status | Engine | Integration authority | API | Arch | Tier achieved | Tier target | Stereo route | Files | Docs | Last change | Freshness | Area completeness |",
        "|---|---|---|---|---|---|---|---|---|--:|--:|---|---|---|",
    ])
    for source in fleet:
        info = measured[source["id"]]
        lines.append(
            f"| **{md(source['id'])}** | {md(STATUS_LABEL[source['status']])} | {md(source['engine'])} | "
            f"{md(source['authority'])} | {md(source['api'])} | {md(source['arch'])} | {md(source['tier'])} | "
            f"{md(source.get('tier_target'))} | {md(stereo_rung(source['stereo_rung']))} | "
            f"{info['total'] if info else '—'} | {info['docs'] if info else '—'} | {latest_date(info)} | "
            f"{freshness(source, info)} | {completeness(source, areas)} |"
        )

    lines.extend(["", "## Per-source area detail", ""])
    for section, sources in (("Fleet", fleet), ("External", external)):
        lines.extend([f"### {section}", ""])
        for source in sorted(sources, key=lambda item: item["id"].casefold()):
            lines.extend([
                f"#### {source['id']}",
                "",
                "| Area | Review | Evidence | Note |",
                "|---|---|---|---|",
            ])
            source_areas = source.get("areas") or {}
            for area in areas:
                entry = source_areas.get(area)
                if entry is None:
                    lines.append(f"| `{area}` | — no entry — | — | — |")
                else:
                    lines.append(
                        f"| `{area}` | {REVIEW_MARK[entry['review']]} | "
                        f"`{md(entry.get('evidence'))}` | {md(entry.get('note'))} |"
                    )
            lines.append("")
    return "\n".join(lines) + "\n"


def write_or_check(outputs: dict[Path, str], check: bool) -> list[str]:
    stale: list[str] = []
    for path, content in outputs.items():
        if check:
            existing = path.read_text(encoding="utf-8") if path.is_file() else None
            if existing != content:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    return stale


def load_ledger() -> dict[str, Any]:
    try:
        data = load_unique_yaml(LEDGER.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise LedgerError(str(error)) from error
    validate(data)
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated files are stale")
    parser.add_argument("--print-revisions", action="store_true", help="print source fingerprints")
    args = parser.parse_args()
    try:
        cfg = load_ledger()
    except LedgerError as error:
        print(f"sources.yml validation failed:\n{error}", file=sys.stderr)
        return 2
    measured = measure_sources(cfg)
    if args.print_revisions:
        for section in ("fleet", "external"):
            print(f"# {section}")
            for source in cfg.get(section, []):
                info = measured[source["id"]]
                print(f"{source['id']}: {info['revision'] if info else 'path-missing'}")
        return 0
    untracked = find_untracked(cfg)
    generated = {
        "coverage": generate_coverage(cfg, measured, untracked),
        "fleet": generate_fleet(cfg),
        "summary": generate_summary(cfg),
    }
    stale = write_or_check(
        {path: generated[kind] for path, kind in OUTPUTS.items()},
        args.check,
    )
    if args.check and (stale or untracked):
        if stale:
            print("Generated documentation is stale:", file=sys.stderr)
            for path in stale:
                print(f"- {path}", file=sys.stderr)
            print("Run: python tools/coverage.py", file=sys.stderr)
        if untracked:
            print("Untracked Other VR mods directories:", file=sys.stderr)
            for name in untracked:
                print(f"- {name}", file=sys.stderr)
        return 1
    action = "checked" if args.check else "wrote"
    document_count, word_count = reader_corpus_metrics()
    print(
        f"{action} {len(OUTPUTS)} generated files — {len(cfg.get('fleet', []))} fleet, "
        f"{len(cfg.get('external', []))} external, {len(untracked)} untracked; "
        f"reader corpus {document_count} docs / {word_count:,} words"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
