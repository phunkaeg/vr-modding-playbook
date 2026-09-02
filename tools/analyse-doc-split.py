import re, sys
from pathlib import Path

DOCS = Path(r'D:\Dev Debug\ss2vr-work\docs')
FILES = ['USER_TEST_LOG.md', 'BUILD_HISTORY.md', 'DECISION_LOG.md', 'FAILURE_REGISTRY.md']
DATE = re.compile(r'(20\d\d)-(\d\d)-\d\d')

for name in FILES:
    p = DOCS / name
    raw = p.read_bytes()
    text = raw.decode('utf-8', errors='replace')
    lines = text.splitlines()
    size = len(raw)

    for level in ('## ', '### '):
        heads = [(i, l) for i, l in enumerate(lines) if l.startswith(level)]
        if len(heads) >= 20:
            break

    dated = []
    for i, l in heads:
        m = DATE.search(l)
        if m:
            dated.append((i, '{}-{}'.format(m.group(1), m.group(2))))

    print('=== {}  {:.0f} KB, {} lines'.format(name, size / 1024, len(lines)))
    print('    split level: "{}"  headings: {}  with dates: {}'.format(
        level.strip(), len(heads), len(dated)))
    if not dated:
        print('    !! no dates in headings — cannot split chronologically')
        print()
        continue

    order = 'newest-first' if dated[0][1] >= dated[-1][1] else 'oldest-first'
    print('    first heading {}, last {}  => {}'.format(dated[0][1], dated[-1][1], order))

    months = {}
    for i, ym in dated:
        months.setdefault(ym, 0)
        months[ym] += 1
    print('    months: ' + ', '.join('{}({})'.format(k, months[k]) for k in sorted(months)))

    # where would we cut to keep the live file under ~180KB?
    target = 180 * 1024
    if size <= target:
        print('    -> already under 180KB, no split needed')
        print()
        continue
    cum = 0
    cut = None
    byte_at = [0] * (len(lines) + 1)
    acc = 0
    for i, l in enumerate(lines):
        byte_at[i] = acc
        acc += len(l.encode('utf-8')) + 1
    byte_at[len(lines)] = acc
    for i, ym in dated:
        if byte_at[i] > target:
            cut = (i, ym)
            break
    if cut:
        print('    -> keep lines 1-{} ({:.0f} KB, {} and newer), archive the rest ({:.0f} KB)'.format(
            cut[0], byte_at[cut[0]] / 1024, cut[1], (acc - byte_at[cut[0]]) / 1024))
    else:
        print('    -> no clean cut point found')
    print()
