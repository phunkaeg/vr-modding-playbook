#!/usr/bin/env python3
"""Create, validate and submit project-owned research receipts. Never edits ledgers.

Exit codes: 0 completed/valid, 1 invalid/conflict, 2 no usable input.
All JSON input uses unique keys. Commands and artifact contents are never executed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "research-inbox"
GRADES = {"SPEC", "SOURCE", "STATIC", "LIVE", "HEADSET", "AUTHOR", "INFERENCE"}
ENVIRONMENTS = {
    "spec": {"SPEC"}, "source": {"SOURCE", "INFERENCE"},
    "static": {"STATIC", "INFERENCE"}, "harness": {"LIVE", "INFERENCE"},
    "in_game": {"LIVE", "INFERENCE"}, "hardware": {"LIVE", "INFERENCE"},
    "headset": {"HEADSET", "INFERENCE"}, "author": {"AUTHOR", "INFERENCE"},
}
GATES = ("identity", "instrument", "control", "scene", "restore")
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}\Z")
SHA = re.compile(r"[a-fA-F0-9]{64}\Z")


class Invalid(ValueError):
    pass


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=unique)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def text(value, label):
    if not isinstance(value, str) or not value.strip() or value.strip().upper() in {"TODO", "OPEN", "TBD"}:
        raise Invalid(f"{label}: supply meaningful text")


def keys(value, required, label, optional=()):
    if not isinstance(value, dict):
        raise Invalid(f"{label}: expected object")
    missing, extra = set(required) - value.keys(), value.keys() - set(required) - set(optional)
    if missing or extra:
        raise Invalid(f"{label}: missing={sorted(missing)}, unknown={sorted(extra)}")


def choose(value, allowed, label):
    if not isinstance(value, str) or value not in allowed:
        raise Invalid(f"{label}: expected one of {sorted(allowed)}")


def safe_path(root, relative):
    text(relative, "artifact path")
    p = (root / relative).resolve()
    if Path(relative).is_absolute() or not p.is_relative_to(root.resolve()):
        raise Invalid(f"path must stay inside its owning project: {relative}")
    if not p.is_file():
        raise Invalid(f"missing file: {p}")
    return p


def routes():
    from playbook_integrity import PATTERN_HEADING_RE, FAILURE_ROW_RE
    patterns = (ROOT / "docs/pattern-catalog.md").read_text(encoding="utf-8")
    failures = (ROOT / "docs/failure-atlas.md").read_text(encoding="utf-8")
    bottlenecks = (ROOT / "bottlenecks.yml").read_text(encoding="utf-8")
    return {m.group("id") for line in patterns.splitlines() if (m := PATTERN_HEADING_RE.match(line))} | {
        m.group("id") for line in failures.splitlines() if (m := FAILURE_ROW_RE.match(line))} | set(
        re.findall(r"^  - id: (BN-[A-Z][A-Z0-9]*-\d{3})", bottlenecks, re.M))


def fleet():
    # YAML is only needed for fleet operations, never for standalone validation.
    from strict_yaml import load_unique_yaml
    cfg = load_unique_yaml((ROOT / "sources.yml").read_text(encoding="utf-8"))
    return {p["id"]: Path(p["root"]).resolve() for p in cfg["fleet"]}


def validate(data, root, known_routes=None):
    keys(data, ("schema_version", "project", "run_id", "recorded_at", "target", "question",
        "claim", "evidence_grade", "environment", "method", "validity", "gates", "fact_verdict",
        "baseline", "limits", "artifacts", "routes", "do_not_repeat", "next_action", "mutation"), "receipt")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise Invalid("unsupported schema_version")
    for field in ("project", "run_id"):
        if not isinstance(data[field], str) or not SAFE_ID.fullmatch(data[field]):
            raise Invalid(f"unsafe {field}")
    for field in ("question", "claim", "method", "limits", "next_action"):
        text(data[field], field)
    try:
        date = datetime.fromisoformat(data["recorded_at"].replace("Z", "+00:00"))
        if date.tzinfo is None:
            raise ValueError("timezone missing")
    except (ValueError, TypeError, AttributeError) as exc:
        raise Invalid("recorded_at must be an ISO timestamp with timezone") from exc
    choose(data["evidence_grade"], GRADES, "evidence_grade")
    choose(data["environment"], ENVIRONMENTS, "environment")
    if data["evidence_grade"] not in ENVIRONMENTS[data["environment"]]:
        raise Invalid("evidence grade does not match environment")
    choose(data["validity"], {"VALID", "INVALID"}, "validity")
    choose(data["mutation"], {"none", "temporary", "persistent"}, "mutation")
    choose(data["fact_verdict"], {"CONFIRM", "REFUTE", "AMBIGUOUS"}, "fact_verdict")
    if data["validity"] == "INVALID" and data["fact_verdict"] != "AMBIGUOUS":
        raise Invalid("INVALID cannot confirm or refute a hypothesis")
    target = data["target"]
    keys(target, ("name", "identity_kind", "identity"), "target")
    text(target["name"], "target.name")
    choose(target["identity_kind"], {"sha256", "git_commit", "document", "unknown"}, "target.identity_kind")
    text(target["identity"], "target.identity")
    if target["identity_kind"] == "sha256" and not SHA.fullmatch(target["identity"]):
        raise Invalid("target SHA-256 must contain 64 hex digits")
    if target["identity_kind"] == "git_commit" and not re.fullmatch(r"[a-fA-F0-9]{40}|[a-fA-F0-9]{64}", target["identity"]):
        raise Invalid("record the full source commit, not an abbreviated revision")
    if data["validity"] == "VALID" and target["identity_kind"] == "unknown":
        raise Invalid("VALID requires a pinned target")
    if data["validity"] == "VALID" and data["environment"] in {"static", "in_game", "headset"} and target["identity_kind"] != "sha256":
        raise Invalid("binary/runtime/headset findings require the inspected or loaded binary hash")
    keys(data["gates"], GATES, "gates")
    for name, gate in data["gates"].items():
        keys(gate, ("status", "reason"), f"gates.{name}")
        choose(gate["status"], {"PASS", "FAIL", "NOT_MEASURED", "NA"}, name)
        text(gate["reason"], name + ".reason")
        if data["validity"] == "VALID" and gate["status"] in {"FAIL", "NOT_MEASURED"}:
            raise Invalid(f"VALID requires passed applicable gates: {name}")
    if data["validity"] == "VALID":
        required = {"identity", "instrument"}
        if data["environment"] in {"in_game", "headset"}:
            required |= {"scene", "control"}
        if data["mutation"] == "temporary":
            required.add("restore")
        if any(data["gates"][g]["status"] != "PASS" for g in required):
            raise Invalid("required validity gates cannot be NA")
    baseline = data["baseline"]
    keys(baseline, ("verdict", "reason"), "baseline")
    choose(baseline["verdict"], {"PASS", "FAIL", "NOT_MEASURED", "NA"}, "baseline.verdict")
    text(baseline["reason"], "baseline.reason")
    for name in ("artifacts", "routes", "do_not_repeat"):
        if not isinstance(data[name], list):
            raise Invalid(f"{name} must be a list")
    if not data["artifacts"]:
        raise Invalid("at least one evidence artifact is required, including for INVALID runs")
    seen = set()
    for artifact in data["artifacts"]:
        keys(artifact, ("path", "sha256", "role"), "artifact")
        text(artifact["role"], "artifact.role")
        if not isinstance(artifact["sha256"], str) or not SHA.fullmatch(artifact["sha256"]):
            raise Invalid("artifact SHA-256 missing or malformed; use stamp")
        p = safe_path(root, artifact["path"])
        if p in seen or p.stat().st_size == 0:
            raise Invalid(f"duplicate or empty artifact: {p}")
        seen.add(p)
        if digest(p) != artifact["sha256"].lower():
            raise Invalid(f"artifact changed: {p}")
    for route in data["routes"]:
        text(route, "route")
        if known_routes is not None and route not in known_routes:
            raise Invalid(f"unknown playbook route: {route}")
    for item in data["do_not_repeat"]:
        keys(item, ("approach", "reason", "reopen_when"), "do_not_repeat")
        for k, v in item.items():
            text(v, k)
    return data


def create(project, run_id):
    return {"schema_version": 1, "project": project, "run_id": run_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "target": {"name": "", "identity_kind": "unknown", "identity": ""},
        "question": "", "claim": "", "evidence_grade": "INFERENCE", "environment": "static",
        "method": "", "validity": "INVALID", "mutation": "none",
        "gates": {g: {"status": "NOT_MEASURED", "reason": ""} for g in GATES},
        "fact_verdict": "AMBIGUOUS", "baseline": {"verdict": "NOT_MEASURED", "reason": ""},
        "limits": "", "artifacts": [], "routes": [], "do_not_repeat": [], "next_action": ""}


def write_once(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
    except FileExistsError:
        if read(path) != value:
            raise Invalid(f"conflicting existing record: {path}; use a new run ID")
        return False
    return True


def submit(path, data, root, inbox=INBOX):
    # Includes source location and hash; raw artifacts remain in the owning project.
    validate(data, root, routes())
    receipt_hash = digest(path)
    if read(path) != data or digest(path) != receipt_hash:
        raise Invalid("receipt changed during submission; re-read and retry")
    name = data["project"] + "__" + data["run_id"]
    packet = {"receipt": data, "project_root": str(root.resolve()),
              "receipt_path": str(path.resolve()), "receipt_sha256": receipt_hash}
    wrote = write_once(inbox / "pending" / (name + ".json"), packet)
    return name, wrote


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--project", required=True)
    init.add_argument("--run-id", required=True)
    init.add_argument("--out", type=Path, required=True)
    for command in ("stamp", "validate", "submit"):
        p = sub.add_parser(command)
        p.add_argument("receipt", type=Path)
        if command != "submit":
            p.add_argument("--project-root", type=Path, required=True)
    sub.add_parser("list")
    review = sub.add_parser("review")
    review.add_argument("submission")
    review.add_argument("--decision", choices=("accepted", "rejected", "deferred"), required=True)
    review.add_argument("--reviewer", required=True)
    review.add_argument("--reason", required=True)
    review.add_argument("--reference", action="append", default=[], help="playbook-relative edited file; required for accepted")
    args = parser.parse_args()
    try:
        if args.command == "init":
            if args.project not in fleet() or not SAFE_ID.fullmatch(args.run_id):
                raise Invalid("unknown project or unsafe run ID")
            write_once(args.out, create(args.project, args.run_id))
            print(f"DRAFT (not evidence): {args.out}")
        elif args.command in {"stamp", "validate", "submit"}:
            data = read(args.receipt)
            if not isinstance(data, dict):
                raise Invalid("receipt must be a JSON object")
            root = fleet().get(data.get("project")) if args.command == "submit" else args.project_root.resolve()
            if root is None:
                raise Invalid("unknown fleet project")
            if not args.receipt.resolve().is_relative_to(root):
                raise Invalid("receipt must remain inside its owning project")
            if args.command == "stamp":
                for artifact in data["artifacts"]:
                    artifact["sha256"] = digest(safe_path(root, artifact["path"]))
                # Explicit stamp action changes hashes, never grades or verdicts.
                args.receipt.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                print("STAMPED: re-read artifacts before treating hashes as evidence")
            else:
                validate(data, root, routes())
                if args.command == "submit":
                    name, wrote = submit(args.receipt, data, root)
                    print(f"{'QUEUED' if wrote else 'ALREADY_QUEUED'} {name}; no canonical records changed")
                else:
                    print(f"VALID_RECEIPT: {len(data['artifacts'])} hashed artifacts; semantic review still required")
        elif args.command == "list":
            pending = sorted((INBOX / "pending").glob("*.json"))
            for path in pending:
                receipt = read(path)["receipt"]
                decision = INBOX / "reviews" / path.name
                state = read(decision)["decision"] if decision.exists() else "pending"
                print(f"{path.stem}: {state}; {receipt['validity']}/{receipt['fact_verdict']}; baseline={receipt['baseline']['verdict']}")
                for item in receipt["do_not_repeat"]:
                    print(f"  DO_NOT_REPEAT [{state}]: {item['approach']}; reopen: {item['reopen_when']}")
            print(f"INBOX: {len(pending)} submissions (zero is a queue state, not an evidence verdict)")
        else:
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,220}", args.submission):
                raise Invalid("unsafe submission ID")
            packet = read(INBOX / "pending" / (args.submission + ".json"))
            text(args.reviewer, "reviewer")
            text(args.reason, "review reason")
            refs = []
            if args.decision == "accepted":
                if not args.reference:
                    raise Invalid("accepted needs the owning playbook file updated after review")
                if digest(packet["receipt_path"]) != packet["receipt_sha256"]:
                    raise Invalid("original receipt changed after submission")
                validate(packet["receipt"], Path(packet["project_root"]), routes())
            for ref in args.reference:
                p = safe_path(ROOT, ref)
                refs.append({"path": ref, "sha256": digest(p)})
            write_once(INBOX / "reviews" / (args.submission + ".json"), {
                "decision": args.decision, "reviewer": args.reviewer, "reason": args.reason,
                "submission_sha256": digest(INBOX / "pending" / (args.submission + ".json")),
                "references": refs})
            print("REVIEW_RECORDED: decision records review, not automatic evidence promotion")
        return 0
    except FileNotFoundError as exc:
        print(f"NO_DATA: {exc}", file=sys.stderr)
        return 2
    except (Invalid, ValueError, TypeError, KeyError, OSError, ImportError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
