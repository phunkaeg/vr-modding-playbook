# Fleet Bottleneck Map

This page answers a different question from the failure atlas or pattern
catalog:

> What missing fact or capability is currently preventing a valid next step,
> and where has the same critical-path blocker appeared before?

A **failure** starts from a symptom. A **pattern** is a reusable solution. A
**bottleneck** is the earliest uncleared dependency that makes downstream work
premature or its verdict invalid.

The authoritative data is `bottlenecks.yml`. The fleet roster is imported from
`sources.yml`; generation fails if an in-house project is omitted, duplicated
or misspelled.

## How to use it

### Starting a new project

1. Follow [Start or Unblock a VR Port](start-new-port.md).
2. For each bottleneck class, run the fast discriminator when its gate is
   reached.
3. Mark it `cleared`, `active`, `open`, `risk` or `na` with an evidence grade.
4. Do not start a downstream gate while an earlier red bottleneck invalidates
   its assumptions.

### Unblocking an existing project

1. Read the project-focus table below.
2. Verify the row against the project’s current-state source; generated routing
   can still become stale when the external project changes.
3. Choose the earliest active bottleneck in dependency order.
4. Run its **fast discriminator**, not the most interesting implementation idea.
5. Close it only with the named **exit proof** or select a documented fallback.

### Looking for commonality

Read the matrix horizontally. A class cleared on several engines is a strong
candidate for a reusable test or pattern. A class active on several projects is
portfolio-level work: improving the shared discriminator, harness or recipe can
unblock several ports at once.

## State semantics

| State | Meaning |
|---|---|
| 🟥 `active` | Current critical path; downstream verdicts depend on it |
| 🟧 `open` | Unresolved, but another bottleneck is currently earlier |
| 🟨 `risk` | Structurally plausible or expected, not yet exercised |
| 🟩 `cleared` | The class’s exit proof passed; not a claim that the subsystem is perfect |
| `na` / — | Demonstrated inapplicable, or no fleet evidence recorded |

Do not use percentages. “Camera 80% solved” cannot tell the next developer
whether render camera is proven but culling is open, or whether the entire claim
is still based on a static guess.

## Dependency order

```text
ACCESS
  -> BASELINE / LOAD
  -> OBSERVE FRAME
  -> CAMERA / PROJECTION / CULLING
  -> STEREO ARCHITECTURE
  -> SIDE-EFFECT SAFETY + XR TRANSPORT
  -> POSE + PER-EYE RENDER CORRECTNESS
  -> INPUT / UI / HANDS / INTERACTION
  -> PERFORMANCE
  -> PACKAGE / RELEASE
```

Some work can proceed in parallel, but a later result cannot clear an earlier
owner. For example, known-color headset pixels can prove XR transport while
camera discovery continues; they cannot prove geometric stereo.

## Cross-project bottleneck matrix

--8<-- "generated/bottleneck-matrix.md"

## Current in-house project focus

--8<-- "generated/project-bottleneck-focus.md"

## The bottleneck record contract

Every class in `bottlenecks.yml` has:

| Field | Purpose |
|---|---|
| `id` | Permanent `BN-DOMAIN-NNN` identifier |
| `title` | Missing fact or capability, not a proposed fix |
| `applies_to` | `re`, `source`, `both` or `hybrid`; this is bottleneck applicability, not integration authority or delivery vehicle |
| `gate` | Earliest playbook gate it blocks |
| `blocks` | Which downstream verdicts become invalid |
| `fast_test` | Cheapest experiment that classifies the bottleneck |
| `exit_proof` | Evidence required to mark it cleared |
| `route` | Full method or chapter |
| `projects` | Per-project state, evidence grade and concise note |

Project focus separately records the current limiting question and the **next
proof**, because several bottleneck classes can be open without all being the
next action. Its integration-authority column is imported from `sources.yml`;
`project_focus` must not duplicate that value.

## When to create a new bottleneck class

Create a new class only when all are true:

1. a missing fact/capability blocks a named gate;
2. it has a discriminator that can classify the condition;
3. it has an exit proof independent of confident prose;
4. it is transferable or plausibly transferable beyond one project;
5. it is not already a more specific symptom in the failure atlas.

If the issue is target-only, keep it in the project’s `CURRENT_STATE` or
`FAILURE_REGISTRY` and reference the nearest common class. If a class becomes
too broad to yield one discriminator, split it; never recycle an existing ID.

## Closure protocol

When a bottleneck is cleared:

1. Write the project receipt first—log, capture, trace, headset verdict or test.
2. State which premise was confirmed and which nearby alternatives were
   refuted.
3. Record the exit proof and evidence grade in `bottlenecks.yml`.
4. Update the project-focus row to the next earliest bottleneck.
5. Run `python tools/bottlenecks.py`.
6. Search other active/open fleet occurrences for an immediately transferable
   test or solution.

Do not mark a row green because implementation exists. Mark it green because
the named exit proof passed on the target whose row is changing.

## Agent operating protocol

For an AI using the playbook:

1. Read `start-new-port.md` and determine route.
2. Read this page’s project row if the target is in the fleet.
3. Read only the bottleneck definition and linked route needed for the current
   gate.
4. Read the project’s cited current-state/failure evidence.
5. State the hypothesis, control, test variable and decision rule before code.
6. Preserve ambiguous outcomes as ambiguous; do not promote them to refuted or
   confirmed.
7. Update both project evidence and fleet routing when the result changes the
   critical path.

This is designed to stop two common agent failures: solving an interesting
downstream problem while an earlier premise is unproven, and repeating an
experiment another project already paid for.

## Validation

Regenerate after intentional changes:

```powershell
python tools/bottlenecks.py
```

Validate without modifying generated files:

```powershell
python tools/bottlenecks.py --check
```

Generated fragments under `docs/generated/` must not be edited by hand.
