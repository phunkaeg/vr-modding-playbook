# External-mod harvest evidence — 2026-09-14

This folder supports [the harvest report](../../2026-09-14-new-mods-harvest.md).
The donor implementations remain in their original checkouts. `manifest.json`
records Git identities and hashes of selected files read or compiled, plus the
fleet state documents used for the relevance comparison. It is not an exhaustive
dependency manifest or a binary/runtime receipt.

## Reproduce the standalone test

From the playbook root in PowerShell:

```powershell
cmd.exe /d /c briefs\evidence\2026-09-14-external-mods\run-checks.cmd
```

Requires the three pinned donor checkouts under `D:\Dev Debug\Other VR Mods`
and Visual Studio 2022 Community C++ tools. The script compiles the **actual**
MGS5VR `core.cpp`/`stereo.cpp`, KHARVOX header helpers and Titanfall2VR rectangle
helper. It writes build artifacts only below `reference/build/`, not to donors.
Compare the manifest before interpreting a run against changed donor code.

Observed tool output (MSVC, 2026-09-14; process exit **0**):

```text
policy_checks.cpp
core.cpp
stereo.cpp
Generating Code...
PASS: 52 checks; real donor helpers, standalone CPU only; no game/GPU/headset proof.
```

Scope: crop ray identity/containment and invalid inputs; bounded append and source
preservation; deferred-free queue ordering, duplicate/capacity refusal; viewport
plausibility including its permissive unknown-target branch. No `assert` compiled
out by release flags: the harness uses explicit failing exit checks.

Not tested: engine integration, skin deformation, panel fitting/readability,
worker scheduling, native patch stubs, GPU completion, command-list execution,
OpenXR lifecycle, sustained re-entry or headset acceptance. The typed Vulkan
retirement wrapper is source-reviewed; only the underlying generic queue is
instantiated by this harness.

## Repository validation

Executed on 2026-09-14 using
`C:\Users\meise\AppData\Local\Programs\Python\Python312\python.exe -B`:

- `tools/coverage.py`: exit 0; regenerated three files, 10 fleet projects,
  111 external sources, **0 untracked** folders.
- `tools/verify.py --portable`: exit 0; all seven portable checks passed.
- `tools/verify.py`: exit 0; **all ten checks passed**, including source and
  interaction coverage, bottlenecks, retrieval IDs, entry-point links, ten project
  instruction pairs, reference maths, integration regressions, strict site build
  and internal anchors.
- Retrieval check: 148 pattern IDs and 373 namespaced failure IDs; six failure
  rows added by this harvest. Existing pattern recipes were extended, not copied
  into a second namespace.
- Reference maths: 28 tests, 95,559 checks passed.
- Pinned donor citation audit: 16 linked implementation paths exist at the
  recorded local donor commits; zero missing/wrong-commit targets. This is a local
  source-path check, not an HTTP availability test.
- `git diff --check`: exit 0. Git emitted its existing LF-to-CRLF notices; those
  were warnings, not validation failures.

The final verifier summary was `all 10 checks passed`. No check was omitted in
that run. The source-ledger freshness scan does not turn a partial review into a
complete audit, and its source fingerprints are separate from game-target proof.
