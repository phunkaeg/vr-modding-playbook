import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import research_receipt as receipt
import research_checks as checks


class Receipts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.artifact = self.root / "evidence.txt"
        self.artifact.write_text("Synthetic unit-test evidence; not an in-game finding.", encoding="utf-8")
        self.data = receipt.create("test-project", "test-run")
        self.data.update(target={"name": "fixture", "identity_kind": "sha256", "identity": "a" * 64},
            question="Does the fixture reject stale evidence?", claim="Fixture remains immutable",
            evidence_grade="STATIC", method="Offline fixture inspection", validity="VALID",
            fact_verdict="CONFIRM", limits="Synthetic fixture only", next_action="Review the fixture")
        self.data["baseline"] = {"verdict": "NA", "reason": "No runtime mutation"}
        self.data["gates"] = {g: {"status": "PASS" if g in {"identity", "instrument"} else "NA",
                                       "reason": "Inspected fixture; static-only task"} for g in receipt.GATES}
        self.data["artifacts"] = [{"path": "evidence.txt", "sha256": receipt.digest(self.artifact), "role": "raw test evidence"}]

    def test_confirm_refute_invalid_and_baseline_failure(self):
        for verdict in ("CONFIRM", "REFUTE", "AMBIGUOUS"):
            self.data["fact_verdict"] = verdict
            receipt.validate(self.data, self.root, set())
        self.data["validity"] = "INVALID"
        receipt.validate(self.data, self.root, set())
        self.data["fact_verdict"] = "CONFIRM"
        with self.assertRaises(receipt.Invalid):
            receipt.validate(self.data, self.root)
        self.data["validity"] = "VALID"
        self.data["baseline"] = {"verdict": "FAIL", "reason": "Cadence regressed"}
        receipt.validate(self.data, self.root)

    def test_stale_empty_missing_evidence_and_unknown_keys(self):
        original = copy.deepcopy(self.data)
        for bad in ({}, dict(original, artifacts=[]), dict(original, mode="oops")):
            with self.assertRaises(receipt.Invalid):
                receipt.validate(bad, self.root)
        self.artifact.write_text("changed")
        with self.assertRaises(receipt.Invalid):
            receipt.validate(original, self.root)
        self.artifact.write_text("")
        original["artifacts"][0]["sha256"] = receipt.digest(self.artifact)
        with self.assertRaises(receipt.Invalid):
            receipt.validate(original, self.root)

    def test_grade_and_runtime_gate_boundaries(self):
        self.data["evidence_grade"] = "LIVE"
        with self.assertRaises(receipt.Invalid):
            receipt.validate(self.data, self.root)
        self.data["environment"] = "in_game"
        with self.assertRaises(receipt.Invalid):
            receipt.validate(self.data, self.root)
        self.data["validity"] = "INVALID"
        self.data["fact_verdict"] = "AMBIGUOUS"
        receipt.validate(self.data, self.root)

    def test_route_and_escape_rejected(self):
        self.assertIn("FAIL-DX12-001", receipt.routes())
        self.data["routes"] = ["CAM-999"]
        with self.assertRaises(receipt.Invalid):
            receipt.validate(self.data, self.root, set())
        self.data["routes"] = []
        self.data["artifacts"][0]["path"] = "../outside.txt"
        with self.assertRaises(receipt.Invalid):
            receipt.validate(self.data, self.root)

    def test_submit_idempotent_conflict_and_no_ledger_write(self):
        path = self.root / "receipt.json"
        path.write_text(json.dumps(self.data))
        inbox = self.root / "inbox"
        with patch.object(receipt, "routes", return_value=set()):
            name, wrote = receipt.submit(path, self.data, self.root, inbox)
            self.assertTrue(wrote)
            self.assertFalse(receipt.submit(path, self.data, self.root, inbox)[1])
            self.data["claim"] = "Changed finding"
            path.write_text(json.dumps(self.data))
            with self.assertRaises(receipt.Invalid):
                receipt.submit(path, self.data, self.root, inbox)
        self.assertEqual(len(list((inbox / "pending").glob("*.json"))), 1)
        self.assertFalse((inbox / "sources.yml").exists())

    def test_duplicate_json_keys(self):
        path = self.root / "duplicate.json"
        path.write_text('{"validity":"INVALID","validity":"VALID"}')
        with self.assertRaises(receipt.Invalid):
            receipt.read(path)

    def test_review_requires_provenance_and_preserves_verdict(self):
        path = self.root / "receipt.json"
        path.write_text(json.dumps(self.data))
        inbox = self.root / "inbox"
        destination = self.root / "chapter.md"
        destination.write_text("Synthetic editorial destination")
        with patch.object(receipt, "routes", return_value=set()), patch.object(receipt, "INBOX", inbox), patch.object(receipt, "ROOT", self.root):
            name, _ = receipt.submit(path, self.data, self.root, inbox)
            argv = ["receipt", "review", name, "--decision", "accepted", "--reviewer", "unit-test", "--reason", "Synthetic review"]
            with patch.object(sys, "argv", argv):
                self.assertEqual(receipt.main(), 1)
            with patch.object(sys, "argv", argv + ["--reference", "chapter.md"]):
                self.assertEqual(receipt.main(), 0)
            self.assertEqual(receipt.read(inbox / "pending" / (name + ".json"))["receipt"], self.data)
            self.artifact.write_text("changed after intake")
            with patch.object(sys, "argv", argv + ["--reference", "chapter.md"]):
                self.assertEqual(receipt.main(), 1)

    def test_temporary_mutation_needs_restore_and_array_is_invalid(self):
        self.data["mutation"] = "temporary"
        with self.assertRaises(receipt.Invalid):
            receipt.validate(self.data, self.root)
        self.data["gates"]["restore"] = {"status": "PASS", "reason": "State restored; fixture proof"}
        receipt.validate(self.data, self.root)
        path = self.root / "array.json"
        path.write_text("[]")
        with patch.object(sys, "argv", ["receipt", "validate", str(path), "--project-root", str(self.root)]):
            self.assertEqual(receipt.main(), 1)


class OfflineChecks(unittest.TestCase):
    def pair(self):
        return [dict(sim_frame="1", eye=e, pose_epoch="1", raster_hash=e, submit_id="1") for e in ("L", "R")]

    def test_pair_clean_bad_and_empty(self):
        rows = self.pair()
        self.assertEqual(checks.pairs(rows)[0], 0)
        rows[1]["pose_epoch"] = "2"
        self.assertEqual(checks.pairs(rows)[0], 1)
        self.assertEqual(checks.pairs([])[0], 2)
        self.assertEqual(checks.pairs(self.pair()[:1])[0], 1)
        self.assertEqual(checks.pairs(self.pair() * 2)[0], 1)

    def samples(self):
        return [dict(input_index=str(i), output_index=str(o), delta_input=str(d),
                     delta_output=str(d * int(i == o))) for i in range(2) for o in range(2) for d in (-0.01, 0.01)]

    def test_jacobian_clean_dirty_and_unmeasured(self):
        rows = self.samples()
        code, result = checks.jacobian(rows, 2, 2, 1e-6, 0.01, 2)
        self.assertEqual(code, 0)
        self.assertEqual(result["rank"], 2)
        self.assertEqual(checks.jacobian([], 2, 2, 1e-6, 0.01)[0], 2)
        self.assertEqual(checks.jacobian(rows[:-1], 2, 2, 1e-6, 0.01)[0], 2)
        rows[0]["delta_output"] = "100"
        self.assertEqual(checks.jacobian(rows, 2, 2, 1e-6, 0.01)[0], 1)

    def test_jacobian_zero_is_measured_and_rank_is_not_semantics(self):
        rows = self.samples()
        for r in rows:
            r["delta_output"] = "0"
        self.assertEqual(checks.jacobian(rows, 2, 2, 1e-6, 0.01)[0], 0)
        self.assertEqual(checks.jacobian(rows, 2, 2, 1e-6, 0.01, 2)[0], 1)
        rows[0]["delta_output"] = "nan"
        self.assertNotEqual(checks.jacobian(rows, 2, 2, 1e-6, 0.01)[0], 0)

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "pairs.csv"
            header = "sim_frame,eye,pose_epoch,raster_hash,submit_id\n"
            for content, expected in ((header, 2), (header + "1,L,1,l,1\n", 1),
                                      (header + "1,L,1,l,1\n1,R,1,r,1\n", 0)):
                path.write_text(content)
                proc = subprocess.run([sys.executable, checks.__file__, "pairs", str(path)], capture_output=True)
                self.assertEqual(proc.returncode, expected, proc.stdout)


if __name__ == "__main__":
    unittest.main()
