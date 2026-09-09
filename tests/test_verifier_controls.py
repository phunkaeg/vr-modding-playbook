"""Positive, damaged and absent-input controls for all nine original checks.

Fixtures are isolated. External processes are simulated where the control is
about verdict propagation, not the implementation of MSVC or MkDocs.
"""
import contextlib
import copy
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import verify
import coverage as source_coverage
import bottlenecks
import interaction_coverage
import playbook_integrity
import yaml


class VerifierControls(unittest.TestCase):
    def test_integration_suite_cannot_pass_with_zero_tests(self):
        for output, status in (("Ran 20 tests in 1s\nOK", True), ("Ran 0 tests in 0s\nOK", None)):
            with patch.object(verify, "run", return_value=("integration regression tests", True, output)):
                self.assertIs(verify.integration_tests()[1], status)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.docs = self.root / "docs"
        self.site = self.root / "site"
        self.docs.mkdir()
        self.site.mkdir()
        for name, value in (("ROOT", self.root), ("DOCS", self.docs), ("SITE", self.site)):
            p = patch.object(verify, name, value)
            p.start()
            self.addCleanup(p.stop)

    def write(self, path, content):
        dest = self.root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        return dest

    def test_source_ledger(self):
        cfg = source_coverage.load_unique_yaml(source_coverage.LEDGER.read_text(encoding="utf-8"))
        source_coverage.validate(cfg)
        broken = copy.deepcopy(cfg)
        broken["fleet"][0]["tier"] = "target T2"
        with self.assertRaises(source_coverage.LedgerError):
            source_coverage.validate(broken)
        empty = copy.deepcopy(cfg)
        empty.update(fleet=[], external=[])
        with self.assertRaises(source_coverage.LedgerError):
            source_coverage.validate(empty)

    def test_bottleneck_ledger(self):
        cfg = bottlenecks.load_yaml(bottlenecks.LEDGER)
        fleet_ids, _, _ = bottlenecks.source_fleet()
        bottlenecks.validate(cfg, fleet_ids)
        broken = copy.deepcopy(cfg)
        broken["bottlenecks"][0]["applies_to"] = "anything"
        with self.assertRaises(bottlenecks.LedgerError):
            bottlenecks.validate(broken, fleet_ids)
        with self.assertRaises(bottlenecks.LedgerError):
            bottlenecks.validate({"bottlenecks": [], "project_focus": []}, [])

    def test_retrieval_integrity(self):
        pat = self.write("docs/pattern-catalog.md", "## CAM-001 — A fixture {#cam-001}\n")
        fail = self.write("docs/failure-atlas.md", "| **FAIL-CAM-001** | fixture |\n")
        self.write("sources.yml", "fleet: []\n")
        with patch.multiple(playbook_integrity, ROOT=self.root, PATTERNS=pat, FAILURES=fail):
            self.assertFalse(playbook_integrity.validate()[0])
            pat.write_text(pat.read_text() * 2, encoding="utf-8")
            self.assertTrue(playbook_integrity.validate()[0])
            pat.write_text("")
            fail.write_text("")
            self.assertTrue(playbook_integrity.validate()[0])

    def test_entry_points(self):
        self.assertIsNone(verify.audit_entry_points()[1])
        for name in verify.ROOT_DOCS:
            self.write(name, "[route](docs/route.md)\n")
        self.assertFalse(verify.audit_entry_points()[1])
        self.write("docs/route.md", "fixture")
        self.assertTrue(verify.audit_entry_points()[1])
        for name in verify.ROOT_DOCS:
            self.write(name, "No links")
        self.assertIsNone(verify.audit_entry_points()[1])

    def test_anchors(self):
        self.assertIsNone(verify.audit_anchors()[1])
        self.write("docs/page.md", "[section](#exists)")
        self.write("site/page/index.html", '<h2 id="exists">Fixture</h2>')
        self.assertTrue(verify.audit_anchors()[1])
        self.write("docs/page.md", "[section](#missing)")
        self.assertFalse(verify.audit_anchors()[1])

    def test_project_pairs(self):
        self.write("sources.yml", "fleet: []")
        self.assertIsNone(verify.audit_project_instructions()[1])
        project = self.root / "project"
        self.write("project/AGENTS.md", "Read CLAUDE.md; failure-atlas.md; re-mcp-toolkit; vr-re-workflow; Ghidra; research-receipts.md")
        self.write("project/CLAUDE.md", "Read AGENTS.md")
        self.write("sources.yml", yaml.safe_dump({"fleet": [{"id": "fixture", "root": str(project)}]}))
        self.assertTrue(verify.audit_project_instructions()[1])
        self.write("project/CLAUDE.md", "missing paired route")
        self.assertFalse(verify.audit_project_instructions()[1])

    def test_reference_maths(self):
        self.assertIsNone(verify.reference_maths()[1])
        self.write("reference/tests/test.cpp", "fixture source")
        exe = self.write("reference/build/vrref_tests.exe", "not executed")
        os.utime(exe, (2000000000, 2000000000))
        with patch.object(verify.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "2 tests, 8 checks", "")):
            self.assertTrue(verify.reference_maths()[1])
        with patch.object(verify.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "assertion failed", "")):
            self.assertFalse(verify.reference_maths()[1])
        with patch.object(verify.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "0 tests, 0 checks", "")):
            self.assertIsNone(verify.reference_maths()[1])

    def test_strict_site(self):
        self.assertIsNone(verify.strict_site_build()[1])
        self.write("mkdocs.yml", "site_name: fixture")
        self.write("docs/index.md", "fixture")
        for exit_code, output, expected in ((0, "Documentation built", True), (1, "broken link", False), (0, "", None)):
            with patch.object(verify.subprocess, "run", return_value=subprocess.CompletedProcess([], exit_code, output, "")):
                self.assertIs(verify.strict_site_build()[1], expected)

    def test_interaction_coverage(self):
        out = self.root / "result.md"
        with patch.multiple(interaction_coverage, ROOT=self.root, MODS=self.root, OUT=out,
                            SOURCES=[("fixture", "input.ini", "fixture")]), patch.object(sys, "argv", ["tool", "--check"]), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(interaction_coverage.main(), 2)
            self.write("input.ini", "anything")
            with patch.object(interaction_coverage, "read_settings", return_value=[]):
                self.assertEqual(interaction_coverage.main(), 2)
            with patch.object(interaction_coverage, "read_settings", return_value=["Grip"]), patch.object(interaction_coverage, "build", return_value="rendered fixture"):
                self.assertEqual(interaction_coverage.main(), 1)
                out.write_text("rendered fixture")
                self.assertEqual(interaction_coverage.main(), 0)


if __name__ == "__main__":
    unittest.main()
