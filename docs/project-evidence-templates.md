# Project Evidence Templates

Copy these into a target project and remove fields that are genuinely
inapplicable. Do not remove an unanswered field merely because it is difficult;
mark it `OPEN`, name the next discriminator and preserve the uncertainty.

The templates intentionally separate observations, ownership and decisions.
One giant progress document becomes unsearchable and lets stale assumptions
survive beside newer evidence.

## `PORT_BRIEF.md`

```markdown
# Port brief

Target game/build/store:
Executable + hash:
Intended runtime/devices:
Seated / standing / roomscale:
Target completeness tier:
Initially acceptable stereo rung:
Single-player / multiplayer / anti-cheat position:
Required mechanics/content:
Explicit exclusions:
Clean vanilla launch recipe:
Deterministic test scene/save:
```

## `AUTHORITY_MAP.md`

Do this before selecting source versus RE.

```markdown
# Integration authority map

| Layer / subsystem | Artifact | Readable | Buildable | Modifiable | Shippable | Retail-compatible | Route | Evidence / caveat |
|---|---|---:|---:|---:|---:|---:|---|---|
| Frame/simulation loop | | | | | | | source / RE / hybrid | |
| Camera/view construction | | | | | | | | |
| Culling/visibility | | | | | | | | |
| Native renderer | | | | | | | | |
| Script/managed game layer | | | | | | | | |
| Input/action layer | | | | | | | | |
| UI/HUD | | | | | | | | |
| Assets/content | | | | | | | | |

Primary delivery route:
Closed boundaries requiring RE:
Source/SDK/oracle versions:
License/redistribution constraints:
Decision receipt:
```

## `TARGET_PROFILE.md`

```markdown
# Target profile

| Field | Value | Evidence | Invalidation |
|---|---|---|---|
| Game/store/build | | | |
| Main executable SHA-256 | | | |
| Logic module + hash | | | |
| Architecture | x86 / x64 | | |
| Engine/generation | | | |
| Active graphics API | | loaded modules / trace | renderer/settings change |
| Active runtime | | live runtime name | user runtime switch |
| Game adapter LUID | | live | GPU/settings change |
| Script/managed loader | | | package/load-order change |
| Anti-cheat mode | | | launch-mode change |

Known launch preconditions:
Known capture/debugger conflicts:
Vanilla control receipt:
```

## `TOOL_PREFLIGHT.md`

```markdown
# Tool preflight

| Tool | Intended question | Host live? | Correct target/program? | Bitness/API fit? | Known hazard | Fallback | Checked at |
|---|---|---:|---:|---:|---|---|---|
| Ghidra | | | | | | | |
| ReGenny | | | | | | | |
| Cheat Engine | | | | | | | |
| Frida | | | | | | | |
| x32dbg/x64dbg | | | | | | | |
| RenderDoc | | capture path | | | | | |
| apitrace | | | | wrapper | | | |

Named capture requested:
Conflicting overlays/proxies removed:
```

## `ADDRESS_REGISTRY.md`

One row can summarize; follow it with the complete derivation and proof packet.

```markdown
# Address registry

## Supported builds

| Build/store | Module | SHA-256 | Image base convention | State |
|---|---|---|---|---|

## Anchors

| ID | Semantic owner | Module + RVA | Derivation | Guard/invariant | Evidence | Call phase/consumers | Invalidation | Fallback |
|---|---|---|---|---|---|---|---|---|

### ADDR-___ — semantic name

Build/hash:
Observed runtime VA:
Module + RVA:
Signature/export/RTTI/pointer derivation:
Uniqueness result:
Decoded instruction/target:
Expected object invariants:
Static evidence receipt:
Live behavioral receipt:
Restart/level-transition validation:
Consumers and mutation window:
Failure behavior on mismatch:
Rejected alternatives:
```

Absolute runtime VAs belong only in the observation field. The shipping path
must derive and guard its target.

## `CAMERA_FINDINGS.md`

```markdown
# Camera findings

## Controlled movement script

Scene/save:
Frame range:
Motion A — translation:
Motion B — rotation:
Known FOV/near/far:

## Candidate

Candidate ID:
Capture event + shader slot/API call:
Raw 64 bytes / storage order:
Decoded matrix hypothesis:
Projection paired with:
Translation correlation:
Rotation/orthonormal residual:
FOV/near/far residual:
Call phase:
Owning object/function:
Main / shadow / reflection / UI / authored classification:
Controlled write + zero-delta control:
Evidence grade:
Invalidation conditions:
Rejected alternatives:

## Camera roles

| Role | Owner | Authored when | Consumers | Safe per-eye seam | Evidence |
|---|---|---|---|---|---|
| Game/body camera | | | | | |
| Player render camera | | | | | |
| Cull camera/frustum | | | | | |
| Viewmodel/foreground | | | | | |
| Scripted/cutscene | | | | | |
| Secondary views | | | | | |
```

## `OWNERSHIP_CENSUS.md`

```markdown
# Ownership census

Proposed mutation seam:
Mutation window begins/ends:
Object lifetime/copy semantics:
Restore behavior:

| Consumer | Address/source | Phase | Reads | Persistent write/cache? | Allowed per eye? | Before/after assertion | Evidence |
|---|---|---|---|---:|---:|---|---|

Known lower bound if enumeration is incomplete:
Why later/downstream seam is or is not available:
Unknown reader policy:
```

## `MUTABLE_ARRAY_CENSUS.md` {#mutable_array_censusmd}

Use for skeletons/bones, particles, transforms, lights or another mutable
instance family discovered through a writer.

```markdown
# Mutable array census

Target/build/module hash:
Array purpose hypothesis:
Known live instance and liveness proof:

## Layout

Backing-store path:
Base/count offsets:
Record stride:
Mutable field offset/type:
Static evidence:
Live-register/watchpoint evidence:

## Consumer trace (not an inventory)

Getter/accessor seam:
Sample duration and call count:
Distinct requested (owner, index) pairs:
What caller demand may exclude:

## Writer census

Writer RVA/signature/call context:
Sample duration and total calls:
Hot-path common/armed work:
Fixed capacity and truncation behavior:

| Run base (session-only) | Records | Stride | Candidate owner/kind | Liveness proof |
|---|---:|---:|---|---|

## External-effect proof

Off control:
Armed zero-delta control:
Large reversible treatment:
Address/lifetime/finite-value guards:
Writes / rejects:
Pixel, shadow or independent game effect:
Surviving frames / total frames:
Verdict: AUTHORITATIVE / WRITABLE-NOT-CONSUMED / OVERWRITTEN / STALE / AMBIGUOUS

## Shipping ownership

Reacquisition trigger and stable anchor:
Last-writer/evaluate-if-dirty policy:
Disable restoration:
Known paths not covered by this writer:
Tool schema/effective-parameter receipt:
```

## `EXPERIMENT.md`

Use one file per important architecture decision or append permanent IDs.

```markdown
# EXP-___ — one falsifiable question

## Premise

Claim being tested:
Why it blocks the next gate:
Evidence grade before test:

## Design

Stock control A:
Armed zero-delta control B:
Single-variable result C:
Metric/receipt:
Measured noise floor:
Confirm threshold:
Refute threshold:
Ambiguous conditions:
Test-validity canaries:
Rollback:

## Result

Build/config identity:
Target hash/runtime/device:
Observed A/B/C:
Verdict: CONFIRMED / REFUTED / AMBIGUOUS / INVALID
Evidence grade after test:
Artifacts:
Newly refuted alternatives:
Next gate/bottleneck:
```

Do not write the decision rule after seeing C.

## `STEREO_ROUTE.md`

```markdown
# Stereo route

Selected rung:
Completeness tier (independent axis):
Camera delivery: parameter / copied view / global borrow / per-draw / none
World execution seam:
Eye cadence: same-frame / AFR / reconstruction
Pair-generation policy:
Per-eye culling policy:
Measured CPU/GPU cost:
Desktop mirror policy:

## Higher rungs evaluated

| Rung | Fast test | Result | Evidence | Why rejected/deferred |
|---|---|---|---|---|

## Side-effect ledger

| Operation | Once simulation | Once frame | Per eye | Banked | Snapshot/restore | Assertion |
|---|---:|---:|---:|---:|---:|---|

## Fallback

Fallback rung:
Trigger/invalidation:
Visual/comfort limitation:
Rollback control:
```

## `RENDER_PASS_CENSUS.md`

```markdown
# Render-pass census

Capture/build/scene:

| Pass ID | Phase | View owner | Color/depth owner | Projection companions | History/motion | Persistent side effect | Queue/state/alias context | Policy | Evidence |
|---|---|---|---|---|---|---|---|---|---|

Policy values:
- once per frame
- once per pair
- per eye
- per-eye banked
- conservative/shared
- disable in VR
- flat fallback
- unknown (blocks PORT-09)

Secondary-view identity rules:
Producer → consumer resource lineage:
Unclassified passes and next discriminator:
```

## `INPUT_OWNERSHIP.md`

```markdown
# Input ownership

| Physical action | Semantic action | Press owner | Release owner | Native endpoint | Contexts | Neutralization | Haptic return | Evidence |
|---|---|---|---|---|---|---|---|---|

Active interaction profile logging:
Transport snapshot version/timestamp:
Stale threshold:
Radial deadzone/diagonal rule:
Handedness boundary:
Keyboard/gamepad coexistence:
Context-switch held-button behavior:
```

## Bottleneck occurrence update

The common class belongs in `bottlenecks.yml`; the full receipt stays in the
project.

```yaml
PROJECT_ID:
  state: active        # active | open | risk | cleared | na
  evidence: LIVE       # required for active/open/cleared
  note: "Concise target-specific reason; cite the project-focus source for detail."
```

To close it, record the receipt first, satisfy the class’s exit proof, change
the state, then advance the project-focus `primary` and `next_proof` fields.

## Session handoff for a human or AI

```markdown
# Session handoff

Target build/hash:
Build/config that actually ran:
Current route and gate:
Active bottleneck ID:
Question:
Control / variable / metric / decision rule:
What was observed:
Verdict and evidence grade:
Artifacts and exact paths:
Addresses/layouts added or invalidated:
Negative results preserved:
Rollback/default state:
Next cheapest proof:
User/headset action required, if any:
```

The handoff should allow the next person or agent to continue without relying
on chat history, terminal scrollback or an attached debugger.
