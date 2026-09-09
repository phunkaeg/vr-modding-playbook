#!/usr/bin/env python3
"""Offline receipt checks: 0 clean measured data, 1 failed check, 2 no usable data.

These check recorded invariants; they do not establish camera ownership or stereo geometry.
"""
import argparse
import csv
import json
import math
import sys
from collections import defaultdict


def read_csv(path, fields):
    with open(path, encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not fields <= set(reader.fieldnames):
            raise ValueError("missing columns: " + ", ".join(sorted(fields)))
        rows = list(reader)
    if not rows:
        raise ValueError("zero data rows")
    return rows


def pairs(rows):
    """Strict recorded same-simulation-frame pairing, not an AFR acceptance test."""
    frames = defaultdict(list)
    malformed = 0
    for row in rows:
        if any(not str(row.get(k, "") or "").strip() for k in
               ("sim_frame", "eye", "pose_epoch", "raster_hash", "submit_id")) or row.get("eye") not in {"L", "R"}:
            malformed += 1
            continue
        frames[row["sim_frame"]].append(row)
    bad, good, incomplete = 0, 0, 0
    for group in frames.values():
        if len(group) != 2 or {r["eye"] for r in group} != {"L", "R"}:
            incomplete += 1
            bad += 1
            continue
        a, b = group
        ok = (a["pose_epoch"] == b["pose_epoch"] and a["submit_id"] == b["submit_id"]
              and a["raster_hash"] != b["raster_hash"])
        good += int(ok)
        bad += int(not ok)
    summary = {"rows": len(rows), "frames": len(frames), "pairs_pass": good,
               "frames_fail": bad, "incomplete_or_duplicate": incomplete, "malformed_rows": malformed,
               "scope": "same-frame metadata and distinct raster hashes only; no geometry/headset proof"}
    code = 2 if not frames else 1 if bad or malformed else 0
    return code, summary


def jacobian(rows, inputs, outputs, atol, rtol, expected_rank=None):
    import numpy as np
    if inputs < 1 or outputs < 1 or inputs * outputs > 1000000:
        raise ValueError("dimensions must be positive and bounded")
    if not all(math.isfinite(t) and t >= 0 for t in (atol, rtol)):
        raise ValueError("tolerances must be finite and non-negative")
    if expected_rank is not None and not 0 <= expected_rank <= min(inputs, outputs):
        raise ValueError("expected rank exceeds matrix dimensions")
    samples = defaultdict(list)
    malformed = 0
    for row in rows:
        try:
            i, o = int(row["input_index"]), int(row["output_index"])
            di, do = float(row["delta_input"]), float(row["delta_output"])
            slope = do / di
            if not (0 <= i < inputs and 0 <= o < outputs and all(map(math.isfinite, (di, do, slope)))):
                raise ValueError("invalid scalar")
            samples[o, i].append((di, slope))
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            malformed += 1
    missing = [(o, i) for o in range(outputs) for i in range(inputs)
               if not (any(d > 0 for d, _ in samples[o, i]) and any(d < 0 for d, _ in samples[o, i]))]
    result = {"rows": len(rows), "expected_cells": inputs * outputs,
              "cells_with_both_signs": inputs * outputs - len(missing),
              "missing_cells": missing, "malformed_rows": malformed,
              "scope": "local numerical sensitivity; rank alone does not prove field semantics"}
    if missing or malformed:
        return (2 if missing else 1), result
    J = np.empty((outputs, inputs))
    unstable = []
    for (o, i), values in samples.items():
        slopes = np.array([s for _, s in values])
        mean = float(np.mean(slopes))
        J[o, i] = mean
        if float(np.max(np.abs(slopes - mean))) > atol + rtol * abs(mean):
            unstable.append([o, i])
    rank = int(np.linalg.matrix_rank(J, tol=atol))
    condition = float(np.linalg.cond(J))
    result.update(matrix=J.tolist(), rank=rank, rank_absolute_tolerance=atol,
                  condition=condition if math.isfinite(condition) else "infinite",
                  unstable_cells=unstable, expected_rank=expected_rank)
    return (1 if unstable or (expected_rank is not None and rank != expected_rank) else 0), result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("pairs")
    p.add_argument("csv")
    j = sub.add_parser("jacobian")
    j.add_argument("csv")
    j.add_argument("--inputs", type=int, required=True)
    j.add_argument("--outputs", type=int, required=True)
    j.add_argument("--atol", type=float, required=True, help="absolute derivative noise tolerance; also rank threshold")
    j.add_argument("--rtol", type=float, default=0.05)
    j.add_argument("--expected-rank", type=int)
    args = ap.parse_args()
    try:
        if args.command == "pairs":
            rows = read_csv(args.csv, {"sim_frame", "eye", "pose_epoch", "raster_hash", "submit_id"})
            code, result = pairs(rows)
        else:
            rows = read_csv(args.csv, {"input_index", "output_index", "delta_input", "delta_output"})
            code, result = jacobian(rows, args.inputs, args.outputs, args.atol, args.rtol, args.expected_rank)
        result["status"] = {0: "PASS", 1: "FAIL", 2: "NO_DATA"}[code]
        print(json.dumps(result, indent=2, allow_nan=False))
        return code
    except (OSError, ValueError, ImportError) as exc:
        print(json.dumps({"status": "NO_DATA", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
