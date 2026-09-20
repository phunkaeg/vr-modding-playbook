"""Fail-closed publication audit. Policy and reports stay outside public Git.

This detects configured disclosures; it cannot establish anonymity by itself.
Editorial approval is bound to the exact candidate snapshot, not a boolean.
No files, index entries, remotes, or history are changed by this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_POLICY = ROOT / '.publication-private' / 'policy.json'


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(['git', '-C', str(root), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def load_policy(path: Path) -> dict:
    policy = json.loads(path.read_text(encoding='utf-8'))
    if policy.get('version') != 1:
        raise ValueError('Unsupported publication policy version')
    for field in ('deny_paths', 'content_rules'):
        if not isinstance(policy.get(field), list) or not policy[field]:
            raise ValueError(f'Policy requires a nonempty {field}')
    for item in policy['deny_paths']:
        if not isinstance(item, str) or not item:
            raise ValueError('Invalid deny path expression')
        re.compile(item)
    for rule in policy['content_rules']:
        if not rule.get('id') or not rule.get('pattern'):
            raise ValueError('Content rules need id and pattern')
        re.compile(rule['pattern'])
    for field in ('approved_snapshot', 'approved_index_snapshot'):
        approved = policy.get(field)
        if approved is not None and (not isinstance(approved, str) or
                                     not re.fullmatch(r'[a-f0-9]{64}', approved)):
            raise ValueError('Approval must be an exact SHA-256 snapshot, or null')
    return policy


def normalized(value: str) -> str:
    value = html.unescape(unicodedata.normalize('NFKC', value))
    # JSON search indexes can encode identifiers without literal characters.
    value = re.sub(r'\\u([0-9a-fA-F]{4})',
                   lambda m: chr(int(m.group(1), 16)), value)
    return value


def candidate_files(root: Path, index: bool = False):
    args = ['ls-files', '--cached']
    if not index:
        args += ['--others', '--exclude-standard']
    names = sorted(set(git(root, *args, '-z').decode('utf-8').split('\0')) - {''})
    for name in names:
        path = root / name
        if index:
            data = git(root, 'show', ':' + name)
        else:
            # Missing tracked files are not silently treated as a safe deletion.
            if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                raise ValueError(f'Linked file needs explicit review: {name}')
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError(f'File resolves outside candidate: {name}')
            data = path.read_bytes()
        yield name, data


def inspect(files, policy: dict) -> dict:
    path_rules = [re.compile(p, re.I) for p in policy['deny_paths']]
    content_rules = [(r['id'], re.compile(r['pattern'], re.I))
                     for r in policy['content_rules']]
    digest = hashlib.sha256()
    findings = []
    count = 0
    for name, data in sorted(files):
        count += 1
        # Length-prefix paths and hash bytes to avoid ambiguous concatenation.
        encoded = name.encode('utf-8')
        digest.update(len(encoded).to_bytes(8, 'big'))
        digest.update(encoded)
        digest.update(hashlib.sha256(data).digest())
        if any(rule.search(name.replace('\\', '/')) for rule in path_rules):
            findings.append({'file': name, 'rule': 'private-path'})
        try:
            body = data.decode('utf-8-sig')
        except UnicodeDecodeError:
            findings.append({'file': name, 'rule': 'unreviewed-binary-or-encoding'})
            continue
        if '\0' in body:
            findings.append({'file': name, 'rule': 'unreviewed-binary-or-encoding'})
            continue
        for rule_id, rule in content_rules:
            if rule.search(normalized(name)):
                findings.append({'file': name, 'rule': rule_id, 'location': 'filename'})
            for line_no, line in enumerate(body.splitlines(), 1):
                if rule.search(normalized(line)):
                    # No matching text: reports need paths/lines, not another leak copy.
                    findings.append({'file': name, 'line': line_no, 'rule': rule_id})
    snapshot = digest.hexdigest()
    approved = count > 0 and policy.get('approved_snapshot') == snapshot
    status = 'BLOCKED' if findings else ('PASS' if approved else 'REVIEW_REQUIRED')
    if not count:
        status = 'NO_DATA'
    return {'status': status, 'files': count, 'snapshot': snapshot,
            'editorial_approval_matches': approved, 'findings': findings}


def check(root: Path = ROOT, policy_path: Path = DEFAULT_POLICY,
          index: bool = False) -> dict:
    policy = load_policy(policy_path)
    if index:
        policy['approved_snapshot'] = policy.get('approved_index_snapshot')
    return inspect(candidate_files(root, index), policy)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', type=Path, default=DEFAULT_POLICY)
    parser.add_argument('--index', action='store_true', help='inspect staged bytes, not working files')
    parser.add_argument('--report', type=Path, help='write local JSON report, outside tracked files')
    args = parser.parse_args()
    try:
        result = check(policy_path=args.policy, index=args.index)
        if args.report:
            # Audit reports reveal filenames. Constrain this convenience to ignored local storage.
            report = args.report.resolve()
            private = (ROOT / '.publication-private').resolve()
            if not report.is_relative_to(private):
                raise ValueError('Reports must be inside .publication-private/')
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(f"{result['status']}: {result['files']} files; {len(result['findings'])} findings")
        for hit in result['findings'][:25]:
            print(f"  {hit['file']}:{hit.get('line', '-')} [{hit['rule']}]")
        print('Snapshot:', result['snapshot'])
        print('This is a candidate-tree check, not a Git-history or anonymity guarantee.')
        return 0 if result['status'] == 'PASS' else 1
    except (OSError, ValueError, KeyError, TypeError, re.error, subprocess.CalledProcessError) as exc:
        print(f'BLOCKED: publication audit could not complete: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
