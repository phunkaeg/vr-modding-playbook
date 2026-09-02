#!/usr/bin/env python3
"""Validate stable retrieval IDs and cross-catalog routes.

Pattern IDs keep their established form (for example CAM-001). Failure IDs
live in the explicit FAIL- namespace (for example FAIL-CAM-001), so the same
short domain/number can never identify two unrelated records.

Usage:
  python tools/playbook_integrity.py --check
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PATTERNS = ROOT / "docs" / "pattern-catalog.md"
FAILURES = ROOT / "docs" / "failure-atlas.md"

PATTERN_HEADING_RE = re.compile(
    r"^## (?P<id>[A-Z][A-Z0-9]*-[0-9]{3})\s+.+?\{#(?P<anchor>[a-z0-9-]+)\}\s*$"
)
FAILURE_ROW_RE = re.compile(
    r"^\| \*\*(?P<id>FAIL-[A-Z][A-Z0-9]*-[0-9]{3})\*\* \|"
)
UNQUALIFIED_FAILURE_RE = re.compile(
    r"^\| \*\*(?P<id>[A-Z][A-Z0-9]*-[0-9]{3})\*\* \|"
)
PATTERN_ROUTE_RE = re.compile(r"\]\(pattern-catalog\.md#(?P<anchor>[a-z0-9-]+)\)")
ANY_FAILURE_ID_RE = re.compile(r"\bFAIL-(?P<base>[A-Z][A-Z0-9]*-[0-9]{3})\b")
UNQUALIFIED_ID_RE = re.compile(
    r"(?<!FAIL-)(?<![A-Z0-9-])(?P<id>[A-Z][A-Z0-9]*-[0-9]{3})(?![A-Z0-9-])"
)


def duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    repeated: set[str] = set()
    for value in values:
        if value in seen:
            repeated.add(value)
        seen.add(value)
    return sorted(repeated)


def validate() -> tuple[list[str], int, int]:
    errors: list[str] = []
    pattern_text = PATTERNS.read_text(encoding="utf-8")
    failure_text = FAILURES.read_text(encoding="utf-8")

    pattern_records: list[tuple[str, str, int]] = []
    for line_number, line in enumerate(pattern_text.splitlines(), 1):
        match = PATTERN_HEADING_RE.match(line)
        if not match:
            continue
        pattern_id = match.group("id")
        anchor = match.group("anchor")
        pattern_records.append((pattern_id, anchor, line_number))
        expected_anchor = pattern_id.lower()
        if anchor != expected_anchor:
            errors.append(
                f"pattern-catalog.md:{line_number}: {pattern_id} must use anchor #{expected_anchor}, got #{anchor}"
            )

    if not pattern_records:
        errors.append("pattern-catalog.md contains no stable-ID headings")
    for pattern_id in duplicates([record[0] for record in pattern_records]):
        errors.append(f"pattern-catalog.md contains duplicate ID {pattern_id}")
    for anchor in duplicates([record[1] for record in pattern_records]):
        errors.append(f"pattern-catalog.md contains duplicate anchor #{anchor}")

    failure_records: list[tuple[str, int]] = []
    pattern_anchors = {record[1] for record in pattern_records}
    for line_number, line in enumerate(failure_text.splitlines(), 1):
        unqualified = UNQUALIFIED_FAILURE_RE.match(line)
        if unqualified:
            errors.append(
                f"failure-atlas.md:{line_number}: failure ID {unqualified.group('id')} must use the FAIL- namespace"
            )
            continue
        match = FAILURE_ROW_RE.match(line)
        if not match:
            continue
        failure_id = match.group("id")
        failure_records.append((failure_id, line_number))
        for route in PATTERN_ROUTE_RE.finditer(line):
            anchor = route.group("anchor")
            if anchor not in pattern_anchors:
                errors.append(
                    f"failure-atlas.md:{line_number}: {failure_id} routes to missing pattern anchor #{anchor}"
                )

    if not failure_records:
        errors.append("failure-atlas.md contains no FAIL- namespaced records")
    for failure_id in duplicates([record[0] for record in failure_records]):
        errors.append(f"failure-atlas.md contains duplicate ID {failure_id}")

    global_ids = [record[0] for record in pattern_records] + [record[0] for record in failure_records]
    for retrieval_id in duplicates(global_ids):
        errors.append(f"retrieval ID is not globally unique: {retrieval_id}")

    failure_bases = {record[0].removeprefix("FAIL-") for record in failure_records}
    failure_only = failure_bases - {record[0] for record in pattern_records}
    corpus = [ROOT / "sources.yml", *sorted((ROOT / "docs").glob("*.md"))]
    for path in corpus:
        if path in (PATTERNS, FAILURES):
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in ANY_FAILURE_ID_RE.finditer(line):
                if match.group("base") not in failure_bases:
                    errors.append(
                        f"{path.relative_to(ROOT)}:{line_number}: unknown failure ID FAIL-{match.group('base')}"
                    )
            for match in UNQUALIFIED_ID_RE.finditer(line):
                retrieval_id = match.group("id")
                if retrieval_id in failure_only:
                    errors.append(
                        f"{path.relative_to(ROOT)}:{line_number}: failure-only ID {retrieval_id} must be qualified as FAIL-{retrieval_id}"
                    )

    return errors, len(pattern_records), len(failure_records)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without writing (the only mode)")
    parser.parse_args()
    try:
        errors, pattern_count, failure_count = validate()
    except OSError as error:
        print(f"playbook integrity validation failed:\n{error}", file=sys.stderr)
        return 2
    if errors:
        print("playbook integrity validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        f"playbook integrity OK: {pattern_count} pattern IDs, "
        f"{failure_count} namespaced failure IDs"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
