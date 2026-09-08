# KEX / Dark: native stereo through owned traversal products

**2026-09-08 · SS2VR phase 1.2.1 / H39.** This case study records the method
and its limits. Exact target contracts and runtime receipts remain in the linked
project documents. The shipping AFR build and this R1 investigation are separate
branches; the investigation does not upgrade the shipping mod's evidence grade.

## Target and evidence boundary

System Shock 2 Remastered / Anniversary Edition v1.3.4984.0 is an x64 KEX/D3D11
injector target with Dark gameplay/rendering ancestry. The inspected executable
SHA256 is `E7CB0E8D2E6E0D3AD4041002F2962ED9668E59253E12B8ADFB7535C9D8CD6499`.
Addresses below are RVAs, Ghidra image base `0x140000000`; live ASLR must be resolved.
The isolated branch is `codex/native-stereo-independent-targets` at
`D:/Dev Debug/ss2vr-native-stereo`. v3.93 source checkpoint: `0b9c159`.

`STATIC` means binary analysis; `LIVE` below means the injected game plus external
GPU/Frida observation under bounded tests. No native-stereo headset acceptance or
production GPU budget follows from those receipts. Dark source and sibling VR mods
were search leads, not proof of target layouts. No proprietary code is reproduced here.

| Gate | Evidence through v3.93 |
|---|---|
| Full native backend twice in one game frame | LIVE; separate owned targets and native extents |
| Own-eye traversal products | LIVE; world cell selection plus complete admitted MD/MM scene slices |
| Identical-camera controls | LIVE; sampled exact images and GPU camera controls |
| Displaced-eye doorway visibility | LIVE; both eyes recover independently verified missing surfaces |
| Current camera rather than an old view cache | LIVE; published basis, eye origins and actual GPU buffers agree |
| Sustained bounded use and recovery | LIVE; 600 centered frames, cancellation/failure/ordinary-frame controls |
| Arbitrary scenes, particles, sorted world lanes | Open; unsupported products remain rejected |
| Native OpenXR transport / HMD | See the current [bridge receipt](<D:/Dev Debug/ss2vr-native-stereo/docs/NATIVE_STEREO_OPENXR_BRIDGE.md>); transport and headset acceptance are separate gates |

## Find the full path before choosing a hook

`STATIC` + `LIVE`: the useful split is a frontend traversal at `0x45C470`, a full
native backend at `0x32C480`, setup at `0x32B920`, and per-eye scene upload at
`0x32BCA0`. The normal caller of the traversal returns to `0x27BD08`.
The traversal's confirmed Windows x64 ABI is `void(float* camera, float scalar)`:
RCX plus XMM1. Calling it as an integer-only signature is not equivalent.

Earlier repeated calls initially described as complete rendering were lighting /
visibility work. Trace a candidate through producers and consumers to real GPU
scene draws before calling it a world-render seam. Resolve receiver/subobject,
vtable callee, target bytes, thread and caller independently.

`0x32C480` was also named FlashRenderer in the shipping mod. Two independently
plausible RE names did not justify two detours. The existing wrapper now owns the
native experiment. Search installed hooks before merging new RE work.
The old native two-pass activation byte was a dead end as a persistent toggle:
settings refresh `0x279240` clears it. Scoped activation after refresh, before the
guarded backend load, works. Retain the native backend prologue and restoration.

`STATIC`: eye index 3 deliberately makes one per-draw matrix path a no-op; kind-3
draws force it. The bias cache compares the level, not the eye. A caller that jumps
straight to the scene upload can silently keep the previous eye's cached matrix.
Full backend re-entry is the proved route; a successful upload alone is weaker.

[Boundary investigation](<D:/Dev Debug/ss2vr-native-stereo/docs/NATIVE_STEREO_INVESTIGATION.md>) ·
[continuous backend proof](<D:/Dev Debug/ss2vr-native-stereo/docs/NATIVE_CONTINUOUS_STEREO.md>) ·
[shared-scene/bias correction](<D:/Dev Debug/ss2vr-work/docs/NATIVE_STEREO_SUBRENDERER_E89160.md>).

## Cull from each eye and own what the traversal produced

`STATIC`: this target does retain eight-plane 2D portal octagons, including all
four diagonals. Widening only left/right can pass horizontal edge witnesses while
still clipping corners. For a fixed camera origin, union is widening; the result
need only be a superset of the per-eye set, not equal to it.

That mathematical argument does **not** prove visibility from displaced eyes.
`LIVE`: a staggered doorway remains invisible to a center-origin traversal even at
100x root width while a displaced eye sees through. Center-projected portal windows
can be disjoint. Root expansion cannot make that chain overlap. The original
ENTRY-time HMD cull-camera correction solves a different ownership problem from
two displaced eye traversals. EXIT writes are too late to repair emitted clipping.
Preserve the camera's `cellId` cache field and byte-identical restoration; copying
only XYZ and inventing the rest can produce eye-in-wall black frames.

The admitted route runs the natural body traversal once as a control, then left
and right from their actual origins. It retains KEX's native recursion. Three
frontend traversals are a diagnostic convenience, **not** the final frame budget.

`LIVE`: a valid pair needs two distinct products:

* **World visible cells:** a separate buffer/descriptor at batch `+0x988/+0x994`,
  replaced by `0x336F90` and consumed by `0x336820`.
* **Model scene lists:** twelve 24-byte descriptors selecting 32-byte records,
  whose event IDs reference retained MD/MM event arenas.

The `+0x9EC` queue was cleanup, not the visible-cell buffer. An empty cleanup
observation never proved the world selection survived. Capture a positive visible
cell set and trace it into its actual consumer.

`STATIC`: `darkMDRenderer+8` points to a shared scene singleton `0xE89160`, not a
per-event transform store. `event[0x1F]` is a depth-bias level, not a transform
handle. Its consumer changes one view-matrix term using a power-of-two offset.
Comparing those numbers as handles proves nothing. This correction required both
the writer and the concrete consumer, not agreement between RE labels.

[Visibility counterexample](<D:/Dev Debug/ss2vr-native-stereo/docs/NATIVE_STEREO_VISIBILITY.md>) ·
[ownership contracts](<D:/Dev Debug/ss2vr-native-stereo/docs/NATIVE_SCENE_OWNERSHIP.md>) ·
[per-eye selection](<D:/Dev Debug/ss2vr-native-stereo/docs/NATIVE_STEREO_PRODUCT_SELECTION.md>).

## Separate scratch reset, retained arenas and borrowed descriptors

`LIVE`: preserve body, left and right event/instance/model data by append retention.
Do not rewind native arenas to manufacture the same event IDs. Select each eye by
borrowing DLL-owned descriptor/list/cell slices, then restore the final cumulative
native descriptors. Compare all active record bytes and referenced ranges.

v3.93 admits MD type0 in lanes0 and 2 and MM type1 in lane4. Selection uses actual
body/left/right count boundaries, not a presumed 1:1 record/event ratio. Duplicate
references, the same event in opaque and translucent categories, unequal eye
counts and empty eye slices are legal within the proved lane/range contract.
The 512 cumulative-event diagnostic cap is not an engine limit.

`LIVE`: three broad-scene centered pairs had MD counts 14/28/42, MM1/2/3,
10 opaque plus4 translucent MD records and 1 MM record per eye. Every selected eye
referenced its own arena interval. 3,240 raw blobs and 3,300 model-reference
observations survived both backend eyes unchanged. Multiple-MM and unequal-eye
cases have unit coverage, not their own live fixtures yet.

Scratch dispatch queues need a separate reset. `STATIC` + `LIVE`:

* Main queue `0x1321280`: 1,280 fixed 56-byte records, front/back cursors.
* Extra queue `0x1332A80`: 256 fixed 56-byte nodes, count `0x14DCCE4`.
* Eight signed-category bucket head/tail pairs at `0x13B1C40`; next pointer at+0x18.

Restore the native initialization contract, including the extra count and bucket
heads. Validate bounded links, alignment, uniqueness, cycle absence, tails and
complete reachability. Do not clear the separate outer cleanup queues. Positive
v3.93 controls observed front10/back1276/extra1. A one-front/one-back assumption
was a fixture restriction, not the engine's real queue contract.

Large snapshots belong in DLL-owned storage. They previously exceeded the game
thread's stack budget; adding a correct scene copy on that stack was not safe.
On cancellation after a traversal, select the preserved full body lists/cells for
ordinary rendering and restore the current cumulative descriptors afterwards.
Test cancellation at each mutation boundary, then prove ordinary draws resume.

Particles remain a separate admission problem. The v3.93 backend-only positive
control saw2 particle events,2 geometry records,380 vertices and 570 indices retained
through both backend eyes. It did **not** run extra particle traversals. Do not
promote that result to per-eye particle ownership. Sorted world/region-plane/cursor
products likewise remain excluded.

[Scene ranges, queue topology and receipts](<D:/Dev Debug/ss2vr-native-stereo/docs/NATIVE_STEREO_SCENE_RANGES.md>) ·
[bounded failure/recovery tests](<D:/Dev Debug/ss2vr-native-stereo/docs/NATIVE_STEREO_REMAINING_TESTS.md>).

## Use the current camera and verify every live consumer

`STATIC`: `0x32BBC0` publishes current XYZ at `0xE89450` and angles at `0xE8945C`;
`0x32B600` publishes the native basis. The basis at `0xE89468` is up/right/back,
so view rows are native basis rows1/0/2 with translation `-dot(row, origin)`.
`0x32B920` builds the GPU-facing view later. Reading `0xE89240` before that setup
can give the previous frame's camera even though the current cull input is fresh.

`LIVE`: the first separated-view experiment left shared `uViewOrigin` unchanged,
with 0.105 GU error at 0.210 GU separation. Derive each eye origin from its actual
rounded view translation and current rigid basis, set the shared XYZ only around
that eye's scene call, and restore after **each** eye plus at the outer boundary.
Validate GPU RenderView origin independently against `inverse(view).translation`.
A matrix delta alone misses this bug. Current-basis motion and 600 centered frames
passed after that correction.

Do not confuse world and viewmodel cameras. They both look like player views and
the last upload can win. Capture the actual world draw's projection and origin;
the native foreground path can change projection after world draws.

[Current-frame camera proof](<D:/Dev Debug/ss2vr-native-stereo/docs/NATIVE_STEREO_CENTERED_FRAMES.md>) ·
[displaced camera contract](<D:/Dev Debug/ss2vr-native-stereo/docs/NATIVE_STEREO_DISPLACED_CAMERA.md>).

## Actual render extent, FOV and OpenXR pair ownership

`LIVE`: 2560x1440 owned outputs with native dimensions/viewport/scissor agree while
the desktop remains1920x1080. A larger XR swapchain alone would not cause more game
pixels to be rendered. Reuse targets and restore native extent, native viewport,
D3D bindings and the mod's binding bookkeeping. Current proof retains16:9; it does
not establish arbitrary runtime-recommended aspect.

`STATIC`: FOV changes must update both RenderView and the separate approximately
304-byte ASSAO reconstruction constants. For off-axis projection, symmetric
`CameraTanHalfFOV` cannot encode the principal-point shift; derive `NDCToViewMul/Add`
from signed tangents. Changing only the projection previously caused a crash.
Leave unused tail matrices and depth terms alone unless the evidence calls for them.
Use runtime `recommendedImageRectWidth/Height` for the eventual render extent, then
derive its projection consistently. Angle averaging is not tangent averaging.

`SOURCE`: the shipping AFR runtime already locates a two-view array; it also has
several lifecycle helpers. Verify the active call graph instead of concluding that
one searched `xrLocateViews` line proves one locate per frame. Native ownership is:
wait/begin frame → locate both eyes once → traverse/render each from that sample →
copy both completed images → release → submit with one display time. On failure,
end with zero projection layers. Preserve AFR's stale-eye machinery for its fallback.

`SPEC`: submitted FOV may differ from the runtime recommendation when it honestly
describes the rendered image; the runtime maps it to the display. This permits a
bounded symmetric-projection transport test before off-axis fill. It does not
permit labelling symmetric pixels with asymmetric FOV metadata.
[Projection-view contract](https://registry.khronos.org/OpenXR/specs/1.1/man/html/XrCompositionLayerProjectionView.html).

`SPEC`: `XR_TIMEOUT_EXPIRED` is nonnegative; `XR_SUCCEEDED(waitResult)` does not
mean an acquired image is writable. Require the successful wait before copy/release;
do not submit a partial pair after acquire/wait/copy failure.
[Swapchain wait contract](https://registry.khronos.org/OpenXR/specs/1.1/man/html/xrWaitSwapchainImage.html).

### First transport result, v3.94

`LIVE`: two bounded runs each submitted 9 native pairs through xr-sim; the final
build's independent QPC trace places one two-eye locate before all body/left/right
traversals. Render/submit displayTime mismatches 0/9, submitted pose error 0.
Six sampled images per run are byte-identical between native outputs and released
XR swapchain contents. GPU origins and all four submitted FOV tangents agree.
Three ordinary recovery frames pass after each run. A final-build cancellation
after the right traversal submits zero projection layers, restores the full body
scene and passes three further ordinary frames. All owned games were closed.
The fixture is explicitly
stationary,64mm parallel-eye, symmetric native FOV,2560x1440; no HMD claim.

Keep raw checker verdicts: `never_submits_zero_layers` flags intentional empty
idle frames around the trial. The dedicated acceptance profile checks an exact
consecutive pair interval and all lifecycle/pose/pixel proofs; it does not waive
an empty frame inside the requested positive interval. No depth layer was submitted.
The [project report](<D:/Dev Debug/ss2vr-native-stereo/docs/NATIVE_STEREO_OPENXR_BRIDGE.md>)
owns final hashes, paths, cancellation evidence and the reproduction procedure.

## Cheapest discriminating proofs, in order

1. Observe the natural frame and prove candidate callee-to-GPU coverage.
2. Render a same-camera pair into owned targets; check zero disparity, camera and
   origin consumers, dimensions, restores and dispatch products.
3. Displace/reverse eye spacing, verify depth-dependent parallax and actual portal
   rays. A rendered cell count alone cannot prove doorway visibility.
4. Give each eye its actual traversal data; compare full retained prefixes and
   selected ranges, then identical-camera and displaced doorway GPU controls.
5. Connect a **bounded admitted fixture** to XR. Correlate xr-tape frame timing,
   poses/FOV/subimages with GPU cameras and actual copied image bytes.
6. Add moving-head/off-axis optics and bounded headset acceptance. Expand scene
   lanes independently, keeping unsupported-frame guards until each is proved.

`LIVE`: the doorway repair recovered8,104/8,104 left-eye and 44,216/44,216 right-eye
previously missing depth samples. Flashing lights made RGB differ; they did not
invalidate the stable depth witness. Preserve real geometry/control evidence rather
than treating a temporal color difference as an eye-lighting bug.

`LIVE`: the 600-frame sample's0.803ms versus0.333ms measured CPU backend work;
readback frames were excluded. It is **not** GPU time, production frame time or a
performance win. Sample GPU evidence first/middle/last; blocking readback every
frame distorts the behavior under test.

`INFERENCE` / process lesson: do not silently replace "first controlled XR test"
with "every gameplay scene supported." All four rendering gates above had passed
while particle/sorted-lane investigations kept delaying transport. State fixture
eligibility and connect the pair, then price headset frame budget and coverage.

Use process-scoped x64 xr-sim/xr-tape, exact executable/DLL hashes, a validated
PID/start-time receipt, and an independently verified watchdog. An "armed" file
is not proof the watchdog survived. Verify menu/load state before native commands;
verify measured pose changes rather than input acknowledgements. Close the owned
game after testing and retain a terminal shutdown receipt. No save writes are needed.

[Doorway depth repair](<D:/Dev Debug/ss2vr-native-stereo/docs/NATIVE_STEREO_VISIBILITY_REPAIR.md>) ·
[latest project state](<D:/Dev Debug/ss2vr-native-stereo/docs/CURRENT_STATE.md>).
