# Record a finding and contribute it

Use this after a substantial experiment, static investigation, or reusable failure.
Routine edits and builds do not each need a receipt. Choose the cheapest discriminating
proof; this workflow does not require launching a game or exhausting static analysis.

The project owns the evidence. The playbook receives a **candidate for review**.
Submission never allocates a pattern ID, changes a grade, clears a bottleneck, or updates
the fleet graph. See [run validity](pattern-catalog.md#meta-012) and
[checker controls](pattern-catalog.md#meta-013).

## Record once, submit a pointer

Run from the playbook root with `requirements.txt` installed. On this machine the
working interpreter is `C:/Users/meise/AppData/Local/Programs/Python/Python312/python.exe`;
bare `python` may resolve to an unconfigured pyenv shim. Below, `python` means your
working interpreter. Choose an existing fleet ID and unique run ID.

```powershell
python tools/research_receipt.py init --project FarCry2-vr --run-id 20260909-camera-01 --out "D:/Dev Debug/FarCry2-vr/receipts/20260909-camera-01.json"
```

This creates an incomplete draft. Fill it from actual evidence. Artifact paths are
relative to the project root, not the receipt directory. Choose durable, nonempty logs,
captures or source excerpts; do not list a file another agent is appending. Exclude secrets.
Record the tool/version and reproduction command in `method`.

```powershell
python tools/research_receipt.py stamp "D:/Dev Debug/FarCry2-vr/receipts/20260909-camera-01.json" --project-root "D:/Dev Debug/FarCry2-vr"
python tools/research_receipt.py validate "D:/Dev Debug/FarCry2-vr/receipts/20260909-camera-01.json" --project-root "D:/Dev Debug/FarCry2-vr"
python tools/research_receipt.py submit "D:/Dev Debug/FarCry2-vr/receipts/20260909-camera-01.json"
```

`stamp` hashes artifacts you inspected; re-stamping changed evidence does not restore an
old finding's validity. Re-review it and use a new run ID when revising a submitted finding.
Identical submissions are idempotent; conflicts are rejected. `submit` resolves the owning
root from `sources.yml` and checks current pattern, failure and bottleneck IDs. Empty
`routes` is allowed when no route fits; propose a destination in `next_action`.

## Field contract

`tools/research_receipt.py` is the executable schema; `init` emits its full template.
Unknown fields and duplicate JSON keys are rejected.

| Field | Meaning |
|---|---|
| `target` | Name plus binary SHA-256, full source commit or identified document. Source-owned work identifies the actual fork/build. Unknown identity is allowed only for an invalid run. |
| `question`, `claim`, `method` | One question, answer, tool/version, controls and reproduction command. Intake never executes stored commands. |
| `environment` | `spec`, `source`, `static`, `harness`, `in_game`, `hardware`, `headset`, or `author`. A synthetic LIVE result stays distinct from the game running. |
| `evidence_grade` | Fleet grade compatible with the environment. An author's account stays AUTHOR until its underlying evidence is inspected. |
| `validity`, `gates` | VALID or INVALID. Identity, instrument, control, scene and restoration record PASS / FAIL / NOT_MEASURED / NA with reasons. VALID requires applicable gates to pass. |
| `mutation` | `none`, `temporary` or `persistent`. Temporary mutation needs restoration proof. Static/source work can mark inapplicable runtime gates NA with reasons. |
| `fact_verdict` | CONFIRM / REFUTE / AMBIGUOUS. INVALID requires AMBIGUOUS; broken instrumentation cannot refute a hypothesis. |
| `baseline` | Independent PASS / FAIL / NOT_MEASURED / NA plus reason and pointer to metrics. Confirmation can survive baseline failure; that does not approve the build. |
| `limits` | What was not established, applicability and invalidation conditions. Separate from evidence grade. |
| `artifacts` | Project-relative path, SHA-256 and role. Validation proves bytes exist and match, not that they support the claim. |
| `do_not_repeat` | Approach, reason and `reopen_when`. Failures are scoped to conditions, not universal prohibitions. |
| `next_action` | Next discriminator, proposed record update, or reason to stop. |

Valid static work may mark scene/control/restore NA where justified; identity and
instrument must pass. LIVE harness evidence must say `harness`, not `in_game`.
An invalid launch can retain an unknown identity and its failure log. Temporary mutation
with unproven restoration remains INVALID. Persistent source edits use normal version
control and baseline testing; they need not restore on every run.

## Review and close the contribution

```powershell
python tools/research_receipt.py list
```

This lists findings and scoped “do not repeat” entries across projects. It is a receipt
index, not a second authoritative failure registry. An empty queue means no submissions,
not completed research. Existing histories still need targeted retrieval.

1. Read raw evidence, target identity, controls and limits. Check whether newer project
   work supersedes this finding.
2. Search for existing patterns, failures and bottlenecks. Prefer extending a receipt
   or correcting a rule over duplicating it.
3. Update the authoritative chapter/ledger or route. A target observation is not automatically
   a transferable recipe. Clear a bottleneck only against its named exit proof.
4. Regenerate ledger outputs when needed and run `python tools/verify.py`. NO_DATA is
   incomplete. `--portable` / `--quick` explicitly name omitted checks.
5. Record the editorial decision, edited files, reviewer identity and rationale:

```powershell
python tools/research_receipt.py review FarCry2-vr__20260909-camera-01 --decision accepted --reviewer "agent/session-id" --reason "Raw evidence inspected; extended the existing camera method with its limits" --reference docs/11-re-anchoring-and-discovery.md
```

Use `rejected` for an unsuitable contribution and `deferred` when evidence is missing.
These are editorial decisions, not REFUTE verdicts. Reviews are immutable; revised or
newly ready findings use a new run/submission and cite the previous ID in `method`.
Review commands record your decision; they do not perform semantic review or prove the
referenced edit is correct. Keep reviewer identity truthful.

Packets live in `research-inbox/pending/`, decisions in `research-inbox/reviews/`.
Acceptance rechecks artifact and original-receipt hashes. If the project is unavailable,
defer review rather than waiving provenance.

## Offline checks and the first experiment

- Camera layout: [numerical mapping recipe](11-re-anchoring-and-discovery.md#numerical-camera-mapping).
- Same-frame pairs: `python tools/research_checks.py pairs pairs.csv`, columns
  `sim_frame,eye,pose_epoch,raster_hash,submit_id`. Missing/duplicate eyes fail. Empty
  or wholly unusable input returns NO_DATA. Distinct hashes do not prove geometry,
  disparity or headset comfort. This is not an AFR acceptance gate.
- Exits: 0 measured clean/operation complete, 1 failed invariant/invalid record,
  2 missing/incomplete input. Record validation success is not hypothesis confirmation.

A first exercise can be offline: distinguish a correct pair, a stale-pose pair and no
pairs using `tests/test_research_integration.py`, then adapt the format to an existing
authorized trace. Tests also exercise confirmed, refuted and invalid receipts, baseline
failure, changed evidence and repeated submissions. These are synthetic fixtures, not
fleet findings. A real-run pilot remains governed by the project's launch rules.

## Origin

Adapted with MonsterDeadWood's permission (user confirmation, 2026-09-09) from
`External/VR_ANALYZER_BIBLE_SOURCE_BRAIN_MERGED_20260907/01_BIBLE/SPLIT/`:
`01_CONTRACTS/POSTFLIGHT_TEMPLATE.md`, `04_PYTHON_TOOLBOX/`, and analyzer methods.
Integrated tools are new, hardened implementations; the archive is preserved.
No donor success, address or synthetic result was promoted to a fleet fact.
The source mirror and large synthetic corpora are not added to the fleet graph.
