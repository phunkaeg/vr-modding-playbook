---
name: vr-research-receipts
description: Record substantial VR research findings or failed approaches, validate project-owned evidence, and submit candidates to the fleet playbook for review. Also supports offline camera-mapping and same-frame metadata checks. Use for research closeout or contribution work, not every routine edit or build.
---

# VR research receipts

On this machine the canonical workflow is
`D:/Dev Debug/VR Modding/docs/research-receipts.md`. Read it when recording or reviewing
a substantial finding. Tools live in `D:/Dev Debug/VR Modding/tools/`.
If these files are unavailable, preserve the project receipt and report that fleet
submission is unavailable; do not invent a replacement ledger or claim it was submitted.

## Record and contribute

- Retain raw evidence in the owning project. Record target/build identity, one question,
  method/tool version, controls, claim, limits and next action. Use the existing project
  structure and runtime permissions. A static task does not require a game launch.
- Keep run validity, factual verdict, baseline health, observation environment and
  evidence grade separate. INVALID cannot confirm/refute. A synthetic harness result
  is not in-game proof. A confirmed fact with a failed baseline does not approve a build.
- Use `research_receipt.py init`, fill the draft from inspected evidence, `stamp` artifact
  hashes, then `validate` and `submit`. See the workflow for exact CLI arguments.
  Hashes identify evidence; re-stamping a changed file does not validate its claims.
- Submission queues a candidate. It does not allocate IDs, promote evidence, clear a
  bottleneck or rebuild graphs. Duplicate identical submissions are harmless; revisions
  use a new run ID and cite the previous record.

## Review

Use `research_receipt.py list`; inspect the raw evidence and current target state.
Prefer an existing pattern/failure/bottleneck over a duplicate. Scope negative findings
and record when reopening is justified. Update the owning chapter or ledger, regenerate
outputs if needed, run `tools/verify.py`, then record a review decision with the edited
file and truthful reviewer identity. Acceptance is an editorial action, not a proof engine.

## Optional offline tools

For unknown matrix correspondence, read the `numerical-camera-mapping` section of
`docs/11-re-anchoring-and-discovery.md`. `research_checks.py jacobian` needs explicit
dimensions, positive and negative perturbations, measured derivative tolerances and
all components including zeros. Rank is not camera semantics; prove a held-out prediction.

`research_checks.py pairs` checks same-frame metadata and different raster hashes;
it cannot prove stereo geometry or serve as an AFR acceptance gate. Checkers return
0 for measured clean data, 1 for failure and 2 for no usable/incomplete data. Never
turn a skip or empty denominator into PASS. Use the existing clean/broken/empty tests.
