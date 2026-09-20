"""Offline positive controls using invented project identifiers only."""
import tempfile
import json
import hashlib
from pathlib import Path
import unittest

import publication_check as pub


def policy():
    return {'version': 1, 'approved_snapshot': None,
            'deny_paths': [r'^raw-notes/'],
            'content_rules': [{'id': 'private', 'pattern': r'violet[-_ ]*port'}]}


class PublicationTests(unittest.TestCase):
    def test_empty_is_not_pass(self):
        self.assertEqual(pub.inspect([], policy())['status'], 'NO_DATA')

    def test_no_matches_requires_review(self):
        self.assertEqual(pub.inspect([('a.md', b'generic recipe')], policy())['status'],
                         'REVIEW_REQUIRED')

    def test_approval_is_bound_to_content_and_name(self):
        files = [('a.md', b'generic recipe')]
        cfg = policy()
        cfg['approved_snapshot'] = pub.inspect(files, cfg)['snapshot']
        self.assertEqual(pub.inspect(files, cfg)['status'], 'PASS')
        for altered in ([('a.md', b'changed')], [('b.md', b'generic recipe')]):
            self.assertEqual(pub.inspect(altered, cfg)['status'], 'REVIEW_REQUIRED')

    def test_disclosure_overrides_approval(self):
        files = [('a.md', b'Violet-Port')]
        cfg = policy()
        cfg['approved_snapshot'] = pub.inspect(files, cfg)['snapshot']
        self.assertEqual(pub.inspect(files, cfg)['status'], 'BLOCKED')

    def test_encoded_json_html_filename_and_path(self):
        for name, body in [('a.json', br'"Violet\u002dPort"'),
                           ('a.html', b'Violet&#45;Port'),
                           ('Violet_Port.md', b'generic'),
                           ('raw-notes/clean.md', b'generic')]:
            self.assertEqual(pub.inspect([(name, body)], policy())['status'], 'BLOCKED')

    def test_binary_and_null_are_not_silently_skipped(self):
        for data in (b'\xff\xfe', b'abc\0def'):
            self.assertEqual(pub.inspect([('image.png', data)], policy())['status'], 'BLOCKED')

    def test_reviewed_asset_requires_exact_path_and_bytes(self):
        data = b'\x89PNG\x00synthetic-test-fixture'
        cfg = policy()
        cfg['reviewed_binary_assets'] = {'art.png': hashlib.sha256(data).hexdigest()}
        self.assertEqual(pub.inspect([('art.png', data)], cfg)['findings'], [])
        for files in ([('renamed.png', data)], [('art.png', data+b'changed')]):
            self.assertEqual(pub.inspect(files, cfg)['status'], 'BLOCKED')

    def test_asset_approval_cannot_bypass_private_filename_or_folder(self):
        data = b'\x89PNG\x00synthetic-test-fixture'
        for name in ('Violet-Port.png', 'raw-notes/art.png'):
            cfg = policy()
            cfg['reviewed_binary_assets'] = {name: hashlib.sha256(data).hexdigest()}
            self.assertEqual(pub.inspect([(name, data)], cfg)['status'], 'BLOCKED')

    def test_bad_asset_approval_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'policy.json'
            cfg = policy()
            cfg['reviewed_binary_assets'] = {'../art.png': 'a'*64}
            path.write_text(json.dumps(cfg))
            with self.assertRaises(ValueError):
                pub.load_policy(path)

    def test_policy_missing_malformed_or_empty_fails(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'policy.json'
            with self.assertRaises(FileNotFoundError):
                pub.load_policy(path)
            for content in ('{}', '{', '{"version":1,"deny_paths":[],"content_rules":[]}'):
                path.write_text(content)
                with self.assertRaises(ValueError):
                    pub.load_policy(path)

    def test_reports_do_not_echo_secret_text(self):
        report = pub.inspect([('a.md', b'Violet-Port unreleased details')], policy())
        self.assertNotIn('unreleased', str(report))
        self.assertNotIn('Violet-Port', str(report))

    def test_worktree_and_index_are_distinct(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pub.git(root, 'init', '-q')
            (root / 'a.md').write_text('Violet-Port')
            pub.git(root, 'add', 'a.md')
            (root / 'a.md').write_text('clean working copy')
            self.assertEqual(pub.inspect(pub.candidate_files(root, True), policy())['status'], 'BLOCKED')
            self.assertEqual(pub.inspect(pub.candidate_files(root), policy())['status'], 'REVIEW_REQUIRED')

    def test_missing_worktree_file_is_not_assumed_removed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pub.git(root, 'init', '-q')
            path = root / 'a.md'
            path.write_text('text')
            pub.git(root, 'add', 'a.md')
            path.unlink()
            with self.assertRaises(FileNotFoundError):
                list(pub.candidate_files(root))

    def test_working_approval_does_not_approve_index_implicitly(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pub.git(root, 'init', '-q')
            (root / 'a.md').write_text('generic')
            pub.git(root, 'add', 'a.md')
            cfg = policy()
            cfg['approved_snapshot'] = pub.inspect(pub.candidate_files(root, True), cfg)['snapshot']
            path = root / '.git' / 'publication.json'
            path.write_text(json.dumps(cfg))
            self.assertEqual(pub.check(root, path, index=True)['status'], 'REVIEW_REQUIRED')
            cfg['approved_index_snapshot'] = cfg['approved_snapshot']
            path.write_text(json.dumps(cfg))
            self.assertEqual(pub.check(root, path, index=True)['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
