# Publication boundary

The public edition shares engineering methods, not private-project reconstruction
guides. Keep private implementation records outside the tracked release tree.

The useful public product is the reviewed method: symptoms, discriminating tests,
reusable recipes, evidence limits, reference maths, and attributed public prior art.
It is not the raw working memory of every contributing project.

## What stays local

Raw and merged documentation graphs, extraction caches, briefs, handoffs, private
project status, unreviewed receipts and private project case studies stay in
the internal corpus. Briefs can contain valuable evidence as well as coordination;
keep them locally and deliberately promote reviewed findings, not whole folders.

Removing a name alone is insufficient. Build numbers, distinctive symbols,
engine/game combinations, addresses, screenshots and timelines can identify the
same project. Do not replace attribution with a fictitious public source, or
upgrade a private observation to a publicly reproducible result.

An external mod for the same game is not automatically a private project. Preserve
its attribution when discussing its independently public work; remove statements
that connect it to private development.

## Local gate

Use the same explicit Python 3.12 interpreter as the normal verifier:

```powershell
python tools/publication_check.py
python tools/publication_check.py --index
```

The first checks tracked working files and non-ignored untracked candidates. The
second checks actual staged bytes. The private policy is stored in the ignored
`.publication-private/policy.json`; it must not be committed. Missing or malformed
policy blocks the check. Binary/undecodable candidates require further review.
After inspecting an image and its metadata, record its exact relative path and
SHA-256 in the private policy's `reviewed_binary_assets` map. That approves only
those bytes, not a file extension or folder; replacement images need fresh review.
Filename and private-path rules still apply to approved binary assets.

Even with no rule matches, the result is **REVIEW_REQUIRED** until an editor has
reviewed that exact candidate snapshot. The policy's `approved_snapshot` must
match its SHA-256 fingerprint. Staged-byte approval uses the separate
`approved_index_snapshot` field: Git's line-ending conversion can make those
bytes different without changing the text. A change invalidates approval. Never record approval
merely to silence a failing check. Matching known names is not an anonymity proof.

`tools/build_public.py` now requires this gate before building or serving. Its
legacy path/status filters are not a privacy boundary. Existing site exports may
still contain disclosures; do not serve them directly. A pre-existing server or
tunnel is not stopped by this change.

This is **not a Git pre-push hook**: a direct push can bypass it. Neither the regular
engineering verifier nor `.gitignore` establishes publication safety.

## Before each public release

1. Keep the complete internal corpus in private storage.
2. Prepare a public candidate containing reviewed documents and tools only.
   Exclude raw graphs, briefs, handoffs and private case studies. Export public
   source attribution without private-project rows or private transfer notes.
   The published fleet roster is deliberately not an exhaustive internal roster.
3. Review identifying context, citations, links, generated fragments, navigation,
   images and the built site's search index—not only visible page text.
4. Run engineering/link tests and the privacy audit on the actual release bytes.
5. Review the commits and refs being uploaded. Snapshot approval covers neither
   older commits nor commit messages, tags, releases or previously uploaded assets.

## Existing public history

A cleanup commit removes files from the latest tree, **not from history**.
The owner has accepted retaining existing public history. This cleanup targets
the current edition, not historical copies, and makes no guarantee against a
reader consulting older commits. No history rewrite, force-push or visibility
change is required by this publication policy. Copies already downloaded cannot
be recalled.

Stage reviewed changes deliberately and check the staged bytes before pushing.
The checker does not push, and passing it is not a promise that generic public
knowledge cannot help someone independently develop a similar mod.
