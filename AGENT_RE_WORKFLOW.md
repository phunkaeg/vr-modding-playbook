# Agent RE workflow

Shared workflow for the native VR fleet. Read once when choosing an RE approach;
then load only the relevant project notes and tool skill. Project restrictions and
the user's current scope still apply. An instruction-file edit does not authorize
launching a game, attaching to another agent's process, or changing a shared runtime.

## Choose the next proof

- Begin with the requested objective and the project's current-state entry point.
  Check existing code, native seams, reports and tests before calling something missing.
  Historical milestone descriptions do not reset completed work.
- Identify integration authority: shipped binary, buildable engine fork, script API,
  or supported SDK. Prefer an existing native/script/source interface where it serves
  the goal; use binary RE where that authority is unavailable. Retail is an oracle,
  not the integration target, for source-owned ports such as MoH-VR.
- For architecture/ownership questions, query the available project graph first.
  For exact symbols, addresses and errors, use scoped `rg`; then read the sources
  the graph names. Check graph age. Failed/empty retrieval is not absence evidence.
- Before committing to a seam or repeating a failed approach, route through the
  playbook's `docs/bottleneck-map.md`, `failure-atlas.md` or
  `cross-project-index.md`. Read the relevant row and linked section, not whole chapters.
- State the hypothesis, a control, the variable, and the decision rule before an
  experiment. Keep one falsifiable question per probe; change hypotheses only when
  a discriminating observation warrants it.

## Discover the tool that can answer it

| Question | Start with | Verify before use |
| --- | --- | --- |
| Binary layout, callers, stores, ABI | Ghidra; scoped offline PE/disassembler scripts | Open program, module hash/base/architecture; `list_instances` and explicit program selection where supported |
| Runtime object identity or pointer chain | ReGenny / Cheat Engine (`cheatengine`) | `regenny_status` or `ping` + attached PID/module; read help/schema |
| Did this path run, with what arguments? | Frida / x32dbg / x64dbg | Process identity and current attachment; project-specific crash restrictions |
| Which draw or state produced these pixels? | RenderDoc / apitrace | Target API, capture provenance, replay compatibility, frame/draw scope |
| What was submitted to OpenXR? | xr-sim + xr-tape and the project's harness | Client bitness, process-scoped selection, fresh trace header, exercised checks |
| Bounded mechanical review | Optional `local-llm` or available helper | Permitted delegation, responsive endpoint, bounded task, independently checked output |

The session's tool list and discoverable schemas establish availability; a tool name
in this document does not. Preflight distinguishes availability from a live app and
from the correct target. A different terminal's MCP configuration cannot settle
what this session exposes. Read a SKILL.md directly if no skill invocation tool exists.

If a tool fails: keep the exact error, check target/context and documented group
loading, and use a supported CLI/API/offline route where it answers the same question.
For example, a documented local server endpoint can expose an operation the session
wrapper omitted. Inspect its schema; do not guess endpoints or bypass an access denial.
State the fallback and its limits. Stop repeating an unchanged failing call.

A closed app is not automatically a user task. Within existing authorization,
use the documented launcher/open/attach controls if appropriate. Ask only for the
specific action that actually needs the user or new authorization. Respect exclusive
runtime ownership and explicit launch restrictions. Continue independent static work.
A missing launcher script is a tooling gap to investigate, not proof that testing
is impossible. Do not replace another agent's game, capture, debugger, or XR session.

## Prove the contract

1. Record module hash/build, architecture, VA versus RVA and relevant source revision.
   A PDB/header/engine ancestor gives vocabulary; it does not establish this build's ABI.
2. Normalize receivers: whole object, embedded object, secondary interface and any
   adjustor thunk. Track byte offsets separately from typed-pointer indices.
3. Resolve virtual calls through constructor/accessor -> concrete table -> slot target.
   Classify PE sections and pointer encoding; an unwind record is not a vtable.
4. Use the decompiler for navigation. Settle ambiguous types/argument counts against
   call-site register/stack setup and the callee. Preserve x64 pointers as pointers
   or full-width integers; never truncate an address to 32 bits.
5. For a field's meaning, trace a producer and consumer, including initialization,
   non-initializing writers and aliases. A gate's name comes after its writes.
   Registration, preparation, execution and post-processing are different stages.
6. Read bounds, sentinels, early returns, special cases and overwrite order.
   Check which object/thread/frame/eye owns the value and how long it remains valid.
7. Use a positive control for zero/empty readings. Check pagination, caps, capture
   coverage and instrument validity before making a negative claim.
8. Preserve the smallest useful receipt: instruction window, decoder fixture,
   raw buffer slice, or deterministic probe. A byte check establishes landmarks;
   it does not execute the game or prove the proposed hook's runtime behavior.

## VR acceptance is downstream

- Distinguish camera-world from world-to-view, storage from multiplication order,
  radians from degrees, handedness, model/world/view spaces and units/metre.
  Check translated and rotated examples, not identity matrices alone.
- Keep eye pose, projection, culling, near/viewmodel, depth reconstruction and submitted
  FOV consistent. Test asymmetric tangents and nonzero head rotations. Compose eye
  orientation too; identity-eye assumptions do not cover canted views.
- Separate once-per-frame simulation from per-eye rendering. Preserve time, input,
  random state, animation and resource ownership when re-entering or replaying work.
- Drive native input/action consumers where possible. A press needs release; prove
  menu acceptance, movement, selected target or impact, not just event/hook counts.
- xr-sim/xr-tape prove the exercised submission contract. They do not by themselves
  prove that submitted textures contain the right scene, match the declared camera,
  or feel correct in a headset. State synthetic, in-process, GPU and headset evidence
  separately. Use a frame capture or downstream observation for the remaining claim.
- Run the smallest relevant existing tests and bounded probe. Preserve exit codes.
  Do not repeat a passed suite without a new change, failure or unresolved concern.
  A static-only task can close static contracts and hand back named runtime checks.

## Leave reusable evidence, not a second story

Use the project's evidence grades; the fleet vocabulary is SPEC, SOURCE, STATIC,
LIVE, HEADSET, AUTHOR and INFERENCE. Keep ambiguity explicit and date negative findings.
Two summaries of the same decompile are one source, not independent confirmation.

For each substantial finding record: question; target/build; producer/consumer;
discriminating evidence; result; limitations; replay command or receipt path.
Use [research receipts](docs/research-receipts.md) for a reusable finding or failed
approach: create and validate a project-owned receipt with `tools/research_receipt.py`,
then submit it for playbook review. Keep validity, fact verdict, baseline health,
evidence grade and observation environment separate. INVALID cannot confirm/refute;
static work does not need a fabricated runtime gate. Intake never clears bottlenecks.
For numerical layout uncertainty use the [camera-mapping recipe](docs/11-re-anchoring-and-discovery.md#numerical-camera-mapping)
and `tools/research_checks.py`; choose the cheapest discriminating test within scope.
Update the owning ledger; correct misleading Ghidra names/comments when project
annotation edits are within scope. Routers
link to the answer instead of duplicating it. Preserve retired experiments in
history/receipts, not as competing active instructions. Re-read shared files before
editing and preserve other agents' changes.

Worked examples: `D:/Dev Debug/PreyVR/docs/RE-INVESTIGATION-GUIDE.md` and
`RE-H021-STATIC-VERIFICATION-2026-09-07.md` in the same directory.
