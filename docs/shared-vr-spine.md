# Shared VR Engineering Spine

Enter here after the selected route has established frame and camera ownership.
These gates apply whether the port edits source, injects a closed binary, uses a
managed layer, or combines them.

The route affects **how** you reach an owner. This spine defines what that owner
must do for correct VR.

## Scope and canonical ownership

This document owns only the **shared gate order, required decision/artifact and
exit proof**. It is not a second copy of the implementation chapters.

| Layer | Canonical responsibility |
|---|---|
| RE/source route | How authority is reached and proven for that access model |
| Shared spine | Which cross-route gate comes next, what receipt it produces, what clears it |
| Numbered technical chapter | Algorithms, implementation rules, evidence, exceptions and trip hazards |
| Pattern/failure index | Atomic recipe or symptom discriminator, linked back to its canonical chapter |

When a spine summary and a linked chapter disagree, the chapter is the
technical authority and the spine must be corrected. Do not “fix” the mismatch
by preserving both versions. A spine gate should ask questions and name proof;
new technical assertions belong in the linked chapter.

## The shared ownership contract

Every project should be able to name one owner for each row:

| Contract | Required owner |
|---|---|
| Simulation frame | Game update/tick identity |
| Render frame | One immutable frame/predicted-pose packet |
| Body/game pose | Locomotion and gameplay heading |
| Render pose | HMD-composed view used for pixels |
| Cull pose | Camera/frustum that decides visible geometry |
| Aim pose | Engine-native ray/weapon endpoint |
| Eye pair | Generation that proves left and right belong together |
| XR lifecycle | State machine allowed to call wait/begin/end/session actions |
| Input edges | Press owner that also owns release |
| Render resources | View/pair identity, not only size/format |

Most cross-engine bottlenecks are failures to establish one of these ownership
contracts. Track them in the [bottleneck map](bottleneck-map.md).

## PORT-06 — separate game, body, render and cull pose {#port-06}

Define the transform chain before adding positional tracking:

```text
OpenXR tracking-space pose
  -> reference-space / recenter transform
  -> body yaw and locomotion basis
  -> engine camera basis and unit conversion
  -> per-eye pose from OpenXR view
  -> render-view and cull-view consumers
```

Keep these concepts separate:

- **game pose:** simulation’s authoritative player/camera state;
- **body pose:** locomotion heading, capsule and torso basis;
- **render pose:** late HMD-composed view used to draw pixels;
- **cull pose:** view/frustum used for visibility and LOD;
- **aim pose:** controller or engine-native direction used by gameplay;
- **authored base:** cutscene/vehicle/ladder/script camera to which HMD may be
  composed conditionally.

### Immutable pose packet

Publish one packet per render frame:

```text
PosePacket
  simulationFrameId
  renderFrameId
  predictedDisplayTime
  trackingSampleId
  referenceSpaceGeneration
  recenterGeneration
  bodyPose
  headPose
  leftGripPose / rightGripPose
  leftAimPose / rightAimPose
  validity + staleness flags
```

Every camera, hand, ray, UI pointer, haptic decision and audio listener consumes
this packet or explicitly declares why it uses another generation. Do not let
each subsystem query “the latest pose” independently.

### Required desk tests

- quaternion normalization and zero-quaternion rejection;
- basis handedness and game-to-metre conversion;
- yaw-only recenter preserving pitch/roll;
- head yaw independent of body yaw;
- eye transform conjugation into engine space;
- identical recenter generation across camera, hands, rays and UI;
- stale/focus-loss snapshot becomes neutral or held according to policy.

Use [A1](a1-rotation-and-frames.md) and [A2](a2-pose-pipeline.md).

**Artifact:** transform diagram, `POSE_OWNERSHIP.md` and numeric tests.

**Exit test:** head movement can be changed independently of body/game heading
without double application, culling follows the declared policy, and every
consumer reports the same packet/recenter generation.

## PORT-07 — climb the stereo proof ladder {#port-07}

OpenXR submission is transport, not stereo. Prove these in order:

1. **Runtime transport:** session accepts two known-color eye images.
2. **Pose transport:** a controlled head movement changes submitted view poses.
3. **Private target:** one eye can render/copy without corrupting the host.
4. **Distinct resources:** left/right target identity and matrices differ.
5. **Coherent pair:** both views name one simulation, pose and pair generation.
6. **Geometric stereo:** near, mid and far world geometry have depth-dependent
   disparity and fuse.
7. **Asymmetric optics:** all four runtime FOV tangents reach the engine or an
   equivalent off-axis projection.
8. **Culling:** leaning reveals geometry rather than empty space at the edges.
9. **Projection companions:** reconstruction, eye position, depth, fog, shadows
   and temporal state agree per eye.
10. **Secondary views:** mirrors, portals, cubemaps, cutscenes and UI do not
    silently enter the main eye pair.

### Per-eye contract

For every submitted eye, log or make derivable:

```text
pairGeneration, eye
simulationFrameId, renderFrameId, trackingSampleId
viewPose, fourFovTangents
colorTargetId, depthTargetId
sourceViewOwner, cullOwner
projectionCompanionGeneration
temporalHistoryGeneration
copy/resolve source identity
```

“Latest left plus latest right” is not a pair. AFR must latch an explicit pair
policy and accept its temporal disparity; same-frame stereo must prove it did
not rerun once-per-frame work.

### Alignment discriminators

- Eye-swap must visibly reverse disparity; if it changes nothing, label and
  sign may have been swapped together.
- Constant pixel shift at all depths indicates a clip-space slide or duplicated
  mono render, not geometric stereo.
- Error growing with depth points toward view-translation sign/space or FOV
  tangent error.
- Correct geometry with wrong lighting/fog points toward mono projection
  companions or per-eye producer resources.

Run [A3](a3-stereo-projection.md) assertions before headset acceptance and use
the [five-minute alignment diagnosis](09-d3d11-openxr-injection.md#the-two-eyes-dont-line-up-a-five-minute-differential-diagnosis).

**Artifact:** `STEREO_LADDER.md` with evidence, receipt and rollback for each
rung.

**Exit test:** world geometry fuses at multiple depths, eye swap reverses the
error, pair generations agree, and mono screen-space classes are separately
identified rather than hidden in a “stereo works” claim.

## PORT-08 — implement OpenXR lifecycle and image transport {#port-08}

Treat OpenXR as an ownership state machine, not a bag of calls.

### Lifecycle requirements

- Poll events every frame.
- Request begin only after `READY`.
- Mark the session running only after `xrBeginSession` succeeds.
- Keep rendering/submitting in `VISIBLE`.
- Accept semantic input only in `FOCUSED`.
- Neutralize input and synthesize releases on focus/host loss.
- Request end on `STOPPING`; mutate local state only after successful result.
- Rebuild after `LOSS_PENDING` according to the recovery policy.
- Exit on `EXITING`.
- Keep the compositor alive through game pause/loading with a safe frame or
  explicit zero-layer policy; do not freeze the render thread.
- Keep exactly one owner for `xrWaitFrame`, `xrBeginFrame` and `xrEndFrame`.

Repeated state events must be idempotent. Desired state and accepted runtime
state are different fields.

### Prove transport separately from the game

1. Resolve runtime, system, view configuration and formats.
2. Match the runtime-required adapter/device.
3. Submit known colors to correctly sized eye swapchains.
4. Prove acquire/wait/release ordering.
5. Move one controlled game image into an owned compatible resource.
6. Submit that resource without claiming it is stereo.
7. Add depth only after color ownership is stable.

For D3D9/10/OpenGL interop, record API object ownership, shareability, adapter
identity, format, multisampling, synchronization, copy/resolve semantics and
device-loss behavior. A successful handle open does not prove the copied pixels
belong to the intended view.

### Recovery matrix

At minimum classify:

- runtime/session/instance loss;
- focus/visibility loss;
- game device/context reset;
- game render-target recreation;
- XR swapchain recreation;
- adapter mismatch;
- unsupported build/signature failure;
- tracking/controller loss;
- level/process transition.

For each: detector, owner, neutral behavior, resources destroyed/rebuilt,
whether flat gameplay continues, and proof receipt.

**Artifacts:** lifecycle transition tests, known-color receipt and
`RECOVERY_MATRIX.md`.

**Exit test:** failed begin/end calls cannot create false local state, focus
loss cannot leave movement/fire latched, and game/XR resource loss recovers or
fails flat and closed.

## PORT-09 — classify render passes and per-eye state {#port-09}

Before replaying or duplicating work, census the render graph. For each
important pass record:

- source view/camera provenance;
- color/depth target identity and lifetime;
- projection and reconstruction companions;
- temporal history and motion vectors;
- culling/LOD owner;
- resource state, descriptor and queue ownership;
- persistent side effects and idempotence;
- once, per-eye, per-pair, banked, disabled or fallback policy.

Use the [render-pass hazard atlas](14-render-pass-hazard-atlas.md).

### Ownership outranks appearance

Do not classify by shader hash, dimensions or format alone. Main view,
reflection, portal, shadow, inventory, security-camera and cutscene targets can
share all three. Prefer:

1. prepared-view/render-view identity;
2. target/depth resource identity across producer and consumer;
3. call-stack or engine phase;
4. camera/projection generation;
5. only then shader/material traits.

### Deferred and screen-space producers

Correct per-eye geometry does not make mono depth reconstruction, shadow mask,
SSAO, SSR, fog, volumetrics or lighting correct. Track the producer resource
through every consumer slot and duplicate/bank the producer by eye where the
engine cannot reconstruct from the final per-eye depth.

Projection is a bundle:

```text
P_eye
inverse/reconstruction matrices
screen-to-camera / screen-to-world constants
eye position and clip planes
depth linearization / z-buffer parameters
motion vectors and previous-view state
shadow/cluster/cascade frusta where view-dependent
```

### D3D12 warning

A closed command list may be legally resubmittable and still be semantically
unreplayable. Resource states, transient/aliased allocations, descriptor heaps,
UAV writes, cross-queue feeders and recording-time RTV/DSV ownership are part
of the captured execution context. See [D3D12 and performance](19-d3d12-and-performance.md).

### Viewmodels and culling

- Identify whether hands/weapons are world geometry, a foreground scene, a
  depth participant or a late overlay before selecting a fix.
- Drive the engine’s cull camera or provide a conservative union frustum;
  widening a render matrix cannot resurrect geometry the engine never emitted.
- Suppress bob/shake/sway at the authoritative channel where possible, while
  preserving authored camera motion according to state.

**Artifact:** `RENDER_PASS_CENSUS.md`, target/resource lineage and captured
control/result images.

**Exit test:** stereo architecture is justified by measured ownership and every
known view-dependent pass has an explicit policy.

## PORT-10 — integrate input through the engine’s semantic funnel {#port-10}

The canonical method, input ladder, edge rules, handedness policy and engine
integration examples live in [03 · Input & Locomotion](03-input-and-locomotion.md).
Grip-versus-aim/viewmodel contracts live in
[02 · Viewmodels & Hands](02-viewmodels-and-hands.md); semantic haptic return
lives in [20 · Audio & Haptics](20-audio-and-haptics.md).

`INPUT_OWNERSHIP.md` must answer this boundary without copying those chapters:

```text
physical OpenXR action
  -> versioned transport snapshot
  -> semantic VR action
  -> engine-owned command / axis / mover / aim / interaction
  -> accepted game event
  -> haptic request back to the physical controller
```

The receipt names the active physical profile, transport field, semantic owner,
native endpoint, press/release owner, loss/staleness neutral state, handedness
boundary, coexistence policy, accepted-event proof and haptic return for every
action family. Any algorithm or precedence ladder belongs in chapter 03.

**Artifact:** `INPUT_OWNERSHIP.md`, action map and headless tests for deadzones,
edges, context changes, focus/staleness and handedness.

**Exit test:** every action has one semantic owner and one release path;
disconnect/focus loss cannot preserve movement, fire or grab; gameplay results
come from native accepted endpoints.

## PORT-11 — establish UI, hands, viewmodels and interaction lanes {#port-11}

Inventory every progression-relevant surface and mechanic. For each decide:

- compositor quad, world geometry, viewmodel, wrist surface or flat fallback;
- world-, body-, wrist- or view-locked placement;
- authoritative pointer/picker and depth;
- modal input owner and edge policy;
- behavior during menu, loading, save/load, death, possession and cutscene;
- left/right-hand policy and seated/standing reach;
- declared completeness tier.

### Panel contract

- Place world/system panels from a valid tracked pose.
- Reject zero/invalid quaternions.
- Gravity-align where appropriate and world-lock after placement.
- Use one authoritative target for hover, beam, dot and click.
- Keep compositor submission alive while the game is paused.
- Provide an explicit recenter/reposition route.
- Preserve readable angular size and depth without forcing head-locked nausea.

### Hands and viewmodels

- Separate grip pose from aim pose.
- Compose one authored mount offset in a documented algebra/order.
- Prefer native skeleton/IK/attachment ownership to pre-skinned vertex hacks.
- Distinguish game animation, controller pose and additive recoil/inertia lanes.
- Define behavior under stale tracking, authored cameras and modal UI.
- Validate muzzle, projectile/trace, reticle and rendered barrel against one
  external ground truth.

### Interaction

Reuse the game’s picker/frob/use model when possible. Physical rays often hit
collision geometry that is not the semantic object the game can activate.
Inventory, keypad, corpse, container, door and special-panel cases need coverage
tests, not only a generic raycast.

**Artifacts:** `VR_UI_MATRIX.md`, mechanic coverage table, authoritative-pointer
tests, flat captures and headset checklist.

**Exit test:** the visual promise and accepted interaction agree; every required
surface is usable at the declared tier; entering a screen with a held trigger
cannot activate it accidentally.

## PORT-12 — measure performance, audio and haptics as VR systems {#port-12}

The canonical performance method—including fresh-frame accounting, XR wait
attribution, GPU/CPU/synchronization classification, matched A/B conditions and
mobile thermal evidence—lives in
[19 · D3D12 & Performance](19-d3d12-and-performance.md). Canonical listener,
emitter and semantic-haptic ownership lives in
[20 · Audio & Haptics](20-audio-and-haptics.md).

This gate asks only whether the project receipts name the runtime budget,
fresh-frame result, dominant measured cost and valid A/B; the listener/emitter
owners and unit transform; and the accepted game events, controller owner and
loss-stop behavior for haptics. Measurement recipes and optimization rules stay
in chapters 19 and 20.

**Artifacts:** `PERFORMANCE_BASELINE.md`, capture/telemetry receipt,
`AUDIO_OWNERSHIP.md` and `HAPTIC_EVENT_MAP.md`.

**Exit test:** the dominant cost is named and moved by a valid A/B; spatial audio
tracks the head and emitters; haptics reflect accepted semantic events.

## PORT-13 — harden, package and declare completion {#port-13}

Before release:

- known builds/signatures are guarded; unknown builds fail closed;
- every feature has a rollback or safe fallback;
- config defaults and parser consumers are schema-validated;
- install/update/uninstall targets are exact and recoverable;
- runtime, bitness, adapter and dependency checks refuse rather than guess;
- logs are bounded and self-identifying;
- clean boot, menu, loading, save/load, death, cutscene, focus loss, controller
  loss and device/runtime loss are in the matrix;
- supported stores/builds/renderers/runtimes are explicit;
- anti-cheat/multiplayer limitations are explicit;
- licenses and redistributability are recorded;
- unsupported content/levels have honest fallback or skip instructions;
- declared T-tier and stereo rung match the tested package.

### Evidence ladder for release claims

```text
desk/unit assertion
  -> flat live control/result
  -> device/capture ownership proof
  -> headset acceptance
  -> clean-machine install/update/uninstall
```

Not every claim needs every stage, but transport, stereo, comfort and user-facing
release behavior cannot terminate at a desktop log.

**Artifacts:** `RELEASE_CHECKLIST.md`, compatibility table, clean-install log,
uninstall test, recovery receipts and declared T-tier/stereo rung.

**Exit test:** a clean machine can prove what loaded, recover safely, identify
unsupported conditions and remove the mod without damaging the installation.

## Maintaining the spine

When a new project discovers a transferable failure:

1. Preserve the project-specific receipt and negative result locally.
2. Add or update the normalized family in the [failure atlas](failure-atlas.md),
   using its globally distinct `FAIL-…` namespace.
3. Add a reusable solve to the [pattern catalog](pattern-catalog.md) when one
   exists.
4. Update `bottlenecks.yml` if it blocked a gate or changed fleet priority.
5. Crosscheck the [cross-project index](cross-project-index.md) for siblings.
6. Update the shared gate only when the lesson changes the required method or
   exit proof.

This keeps long technical chapters, atomic patterns, symptoms and operational
bottlenecks distinct while allowing them to point at one another.
