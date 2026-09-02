# Glossary — use these terms consistently

Ambiguous camera and timing language causes real implementation bugs. These
definitions are the playbook’s shared vocabulary.

## Architecture and evidence

**Active mod**  
A first-hand conversion currently being implemented. Distinct from a research
target, which has investigation but no established conversion path.

**Authority map**  
Per-code-layer record of what is readable, buildable, modifiable,
redistributable and compatible with the shipping game. It determines whether a
subsystem follows the source-owned, RE-owned or hybrid route.

**Bottleneck**  
The earliest missing fact or capability that prevents the next playbook gate
from producing a valid verdict. It is not synonymous with bug, backlog item or
most severe visible defect.

**Evidence grade**  
The provenance of a claim: specification, source, static RE, live observation,
headset acceptance, author claim or inference. It is not a confidence score.

**Exit proof**  
The evidence required to mark a gate or bottleneck cleared. Implementation or
confident prose is not an exit proof unless it satisfies the declared test.

**Fast discriminator**  
The cheapest controlled experiment that separates the important neighboring
causes or selects the next architectural route.

**Fail closed**  
Disable the dependent feature and preserve original game behavior when a guard
fails. The opposite is guessing or partially applying writes.

**Fleet**  
The in-house first-hand projects tracked in `sources.yml`, including explicit
status. External references are not fleet projects.

**Lane**  
An independently gated ownership path, such as world rendering, UI capture,
viewmodels, input or diagnostics. A lane should be able to fail without
silently corrupting unrelated lanes.

**RE-owned route**  
Workflow used when the shipping code owning a subsystem cannot be built and
shipped. Discovery, behavioral ownership, stable anchors, version guards and
fail-closed behavior are part of the production design.

**Source oracle**  
Readable source, SDK, sibling or recreation that supplies names and structural
priors but is not itself the shipping implementation. Its counterpart must be
verified in the exact retail binary.

**Source-owned route**  
Workflow used when the exact camera/render owner can be built, modified and
legally shipped. It replaces address discovery with source ownership mapping
and fork maintenance; shared VR correctness gates still apply.

**Hybrid route**  
A port whose authority boundary differs by subsystem—for example, editable
scripts/managed code over a closed native renderer, or SDK source used as an
oracle for a native injector.

**RVA**  
Relative virtual address: address relative to a module image base. More
portable than an absolute runtime address, but still build-specific unless
resolved by a signature or semantic anchor.

**Semantic anchor**  
A stable name, string reference, export, vtable relationship or behavior used
to rediscover a function/object across builds.

**Stereo rung**  
The mechanism used to obtain two views: native scene re-entry, per-draw replay,
alternate-eye rendering or reconstruction. It is independent of feature
completeness.

**T0–T4 completeness tier**  
The declared breadth of the VR adaptation, from flat-in-headset transport to a
fully adapted experience. A high stereo rung does not imply a high tier.

## Coordinate spaces and poses

**Aim pose**  
Controller pose intended for pointing. It is not necessarily aligned with the
physical grip or visible controller model.

**Body yaw**  
Horizontal orientation of the locomotion/player body. It usually persists
independently of momentary HMD yaw.

**Camera world transform**  
The camera’s position/orientation in world coordinates. Its inverse is
typically the view matrix.

**Cull camera / cull frustum**  
The camera/frustum the engine uses to decide visibility. It may be evaluated
earlier and differ from the final per-eye render camera.

**Engine camera**  
The game-owned camera before or after authored effects, depending on the
documented hook point. Always qualify which stage is meant.

**Game pose**  
The simulation-authoritative player/camera pose used by gameplay systems.

**Grip pose**  
Controller pose intended for attaching held objects. Use aim pose separately
for rays/muzzles unless the runtime profile proves they coincide.

**HMD pose**  
Tracked headset transform in a named OpenXR reference space at a named sample
time.

**Local / LOCAL_FLOOR / STAGE**  
OpenXR reference spaces. `LOCAL` has an application-origin convention;
`LOCAL_FLOOR` adds floor alignment when available; `STAGE` represents a
runtime-defined bounded stage. Do not treat them as interchangeable heights.

**Pose frame**  
The coordinate frame and timestamp/generation attached to a pose. A vector
without its pose frame is incomplete data.

**Recenter transform**  
Application-owned transform from tracking space into the chosen game/body
origin. One versioned event should update every consumer.

**Render pose**  
Pose used to build the submitted eye views. It may be sampled/predicted later
than the game pose, but the relationship must be explicit.

**Roomscale displacement**  
Physical HMD translation relative to the recenter/body origin. It is not
ordinary stick locomotion and should not automatically move the collision
capsule.

**Tracking pose**  
Raw runtime-reported pose before application recenter, body basis and engine
coordinate conversion.

**View matrix**  
World-to-view transform. Usually the inverse of camera world transform;
row/column convention and handedness must be established.

## Stereo and projection

**AFR / alternate-frame rendering**  
One eye produced per engine frame. It reduces re-entry requirements but creates
pair-coherence, latency and per-eye history problems.

**Asymmetric frustum**  
Projection with different left/right or top/bottom tangents. Required by most
headset optics; “same FOV with an eye translation” is insufficient.

**Canted display**  
An eye display whose optical plane is rotated relative to the other. Use the
runtime’s per-eye poses/projections rather than forcing parallel assumptions.

**Convergence**  
In legacy stereo-injection terminology, a depth/pivot parameter used with
separation. Do not implement headset stereo as camera toe-in.

**Disparity**  
Difference in an object’s image position between eyes. Correct perspective
stereo disparity varies with depth.

**Eye pair**  
Left and right images published under one declared simulation/pose/resource
generation policy.

**Eye swap**  
A diagnostic that exchanges left/right presentation without cancelling the
geometry offset. If nothing changes, the test itself may be broken.

**IPD**  
Interpupillary distance represented by the runtime’s two eye poses. Avoid a
second independent IPD setting unless deliberately calibrating game scale.

**Projection companion**  
Any value derived from or coupled to projection: inverse matrices, view-proj,
clip planes, eye position, depth reconstruction constants or temporal history.

**Projection matrix**  
View-to-clip transform. Its storage convention, depth range, handedness and
reverse-Z policy matter.

**Sequential stereo**  
Both eyes rendered during one host frame by invoking a world/scene path twice.

**Toe-in**  
Rotating eye cameras toward a convergence point. It introduces vertical
disparity and is wrong for normal headset rendering; use parallel eye poses
with asymmetric projections.

## Rendering and resources

**Aliasing barrier (D3D12)**  
Declares a change in which placed resource owns a shared heap region. It is not
equivalent to a transition barrier and makes command-list replay sensitive to
the exact frame-graph lifetime context.

**Command-list replay**  
Re-executing an already closed D3D12 command list. Legal API usage does not
imply semantic safety: resource states, descriptors, UAV effects, aliasing and
queue dependencies still apply.

**Frame boundary**  
The reliable transition at which a host frame is presented/submitted. It may
be `Present`, `SwapBuffers` or an engine callback.

**Frame graph**  
Engine scheduler that creates passes and transient resource lifetimes,
including barriers and cross-queue dependencies.

**Private eye target**  
Mod-owned color/depth resource carrying one eye before copying/submitting to an
OpenXR swapchain image.

**Provenance**  
The camera/view, frame, resource generation and pass ownership attached to a
render target. Size and format alone do not establish it.

**Screen-space pass**  
A pass operating on rendered buffers rather than world geometry—postprocess,
SSAO, SSR, TAA, HUD composition and similar work.

**Temporal history**  
Persistent per-frame state such as TAA/DLSS/motion history. Stereo usually
requires per-eye history or a deliberate mono policy.

**Transient resource**  
Short-lived frame-graph resource whose heap memory may be reused/aliased later
in the same frame.

**UAV side effect**  
Unordered-access write, append, atomic or counter mutation. Repeating it may
not be idempotent even when render-target transitions are restored.

## OpenXR lifecycle and input

**Action set**  
Named collection of OpenXR input/output actions attached to a session.

**Active interaction profile**  
Controller profile the runtime currently selected for a hand. Suggested
bindings are proposals; query/log the active profile after sync/profile-change.

**FOCUSED**  
OpenXR session state in which the application owns input. Rendering also occurs
in `VISIBLE`; input ownership is the key difference.

**Haptic request**  
Game-semantic feedback converted to an OpenXR output action, ideally triggered
after the game accepts an event rather than from a raw button edge.

**Input edge**  
Transition between released and pressed. Context entry while already held must
not manufacture a rising edge.

**Input owner**  
Lane/context that consumed a press and therefore owns its release.

**Session running**  
Local state established only after successful `xrBeginSession`, and cleared
after successful `xrEndSession` or terminal loss.

**Stale transport**  
Input snapshot older than the agreed freshness window. Treat it as neutral,
not as the last known physical state.

**VISIBLE**  
Session state where frames should continue, even if another system surface owns
input and the app is not focused.

## UI, audio and performance

**Diegetic UI**  
Interface represented as an object/surface in the game world and operated as
part of that world.

**Listener-relative audio**  
Sound intentionally fixed to the listener/head (UI, narration, some ambience)
rather than emitted from a world position.

**Pointer arbitration**  
Selection of one authoritative ray/hit result when multiple hands or input
methods could target UI.

**Stale frame**  
Compositor presents an older application frame. Display refresh can remain at
90 Hz while application freshness misses budget.

**World-locked panel**  
Panel placed in world/tracking space and left stationary until an explicit or
lazy recenter. It is not gaze-glued.
