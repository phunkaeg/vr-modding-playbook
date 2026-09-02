# BioshockVR — USER_TEST_LOG harvest (lines 2500-end)
Lines read: 2500-5015

### Absence of errors is not proof a mutation path is actually running — check the applied/attempted ratio
**What happened:** `0.3.78-psnullmonodepth` produced a visually mono HMD image and the user reported "zero shader errors," which read as a healthy but unsolved path. The log showed the real cause: a newly added broad mono-depth fallback had swallowed nearly all native stereo mutation — `stereoWorldMatrixStereoProofAttemptTotal=2137915` against `AppliedTotal=1765`. Clean logs and a live OpenXR submit loop meant "nothing crashed," not "the feature under test executed." The fix was narrowing the fallback predicate so it stopped matching almost every draw.
**Why it generalises:** Any engine with a guarded/optional mutation path (a shader replace, a hook override, a patched draw) can silently degrade to a no-op fallback that produces a clean-looking log. The only trustworthy signal is a counted applied-vs-attempted ratio for the specific mechanism under test, not the overall absence of exceptions.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Presence is not proof of loading"

### A gate added to isolate one variable can also disable the fallback baseline the scene depends on to render at all
**What happened:** Twice, adding a strict isolation gate to test one hypothesis produced an apparently catastrophic regression that was actually a side effect of the gate itself. In `0.3.59-nativevs-isolate`, `StereoWorldMatrixStereoOnly=1` suppressed the already-proven mono private-eye fallback on every draw the strict matrix path rejected, so the HMD showed only solid proof colors (`stereoWorldMatrixStereoProofAppliedTotal=0`, `FallbackTotal=49112`, `affineLastColumnResidual=96.65`) even though the private-HDR pipeline itself was untouched. In `0.3.76-psnulldepthskip`, an over-broad skip predicate similarly starved `stereoWorldFullPassMonoAccumulationAppliedTotal` to `0`. Both looked like the isolated variable had failed; both were the isolation mechanism itself cutting the power, not the hypothesis.
**Why it generalises:** Any "isolate variable X" flag that works by suppressing everything else is itself a second experimental variable. Verify the fallback/baseline path is still alive before reading a blank or degraded result as a verdict on X.
**Chapter:** 06-debugging-methodology.md
**Status:** NEW

### Named/helper readouts of GPU constant data can omit the value you need — go to the raw bytes at a known offset
**What happened:** RenderDoc's named-cbuffer helper did not surface the projection constants needed to build a native per-eye matrix. Reading the raw `$Globals` VS cbuffer bytes directly (event 440, `ResourceId::1529`, 560 bytes) found `screenDataToCamera` at `c3=[2.383507,0,-1.191754,0]`, `c4=[0,-1.340723,0.670361,0]`, which derived HFOV≈100.0°, VFOV≈67.7°, near≈10, far≈65536 units. Applying that derived `P_center` collapsed an affine-fit residual from ~98 to `0.000015`.
**Why it generalises:** This is a second, independently-derived confirmation (with real numbers) of the project's own hard rule not to trust cbuffer values from a convenience helper — any GPU-inspection tool's "friendly" struct view can silently miss or mis-map fields that raw byte offsets reveal.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Tooling lies in specific, learnable ways — know them before you trust a reading"

### When a hypothesis survives several A/B toggles without dying, stop toggling and read the actual pipeline state
**What happened:** The team spent multiple builds (`0.3.76` through `0.3.78`) treating "PS-null depth-only draws" as the cause of red/blue clear-color holes, alternately skipping and mono-falling-back those draws with mixed, hard-to-interpret results. `0.3.89-depthpairdump` finally added direct output-merger telemetry and found the suspect draws had `rt0WriteMask=0x0` and `depthWriteMask=0` — they wrote nothing at all, making them a red herring. The real cause was upstream, in mono-fallback color passes tested against per-eye matrix depth.
**Why it generalises:** A hypothesis that keeps surviving toggle-based A/Bs is a sign you're testing behavior, not state. Reading the concrete pipeline/resource state (bind flags, write masks, resource IDs) directly settles ambiguity that another round of enable/disable cannot.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Measure, don't theorize: the readback probe"

### Widening a fix from the exact confirmed instances to a whole resource-shape class trades a narrow win for a broad, unpredictable regression
**What happened:** A slot-2 screen-space-SRV mono fallback, narrowed by exact index count (`SlotMask=4`, `MinIndexCount=18000`), reliably fixed the large black-sided boulders without collateral damage. Later, broadening the same mechanism to a whole route family (`StereoWorldScreenSpaceSrvFallbackIndexedPrimitive=1`) regressed stone elements, the boulder shading, an open chest, and a previously-fixed poster frame — reverting it restored the healthier baseline. The team then re-narrowed to exact per-draw index-count selectors (`ExactIndex0..7`) instead of a family-wide switch.
**Why it generalises:** In any per-draw or per-resource classification system, matching by "this exact identified instance" is far safer than matching by "everything shaped like it." Broadening a predicate should be an explicit, separately-tested step, not an assumed generalization of a working fix.
**Chapter:** 05-assets-and-materials.md
**Status:** SHARPENS "Pick the right control group"

### Depth-based per-eye reprojection must linearize the depth buffer before computing disparity, or the effect concentrates entirely in the near field
**What happened:** An early depth-weighted OpenXR eye-blit reprojection (`0.3.52`/`0.3.54`) used raw, non-linear D3D depth values directly, leaving mid/far objects flat while near objects absorbed almost all the parallax. `0.3.55-linearizedepth` added `linear_inverse_z` conversion to view-space distance with an explicit convergence plane (`near=100mm`, `far=1,000,000mm`, `convergence=2500mm`), which was needed before mid/far geometry showed coherent depth.
**Why it generalises:** This is a generic property of any hardware depth buffer (reverse-Z or standard), on any engine/API: raw depth is heavily non-linear near the camera, so any per-pixel effect keyed directly off depth (disparity, fog, DoF) needs linearization to view-space distance first, or the effect silently biases toward whatever is closest to the lens.
**Chapter:** 09-d3d11-openxr-injection.md
**Status:** NEW

### A create-time hook installed after attach misses every resource already constructed, and a short user keypress can fall between two capture stages' polling windows
**What happened:** Shader-identity hooks (`PSSetShader`/`CreatePixelShader`) installed via attach-mode injection reported `unknown` bytecode hashes for shaders created before the DLL attached, so identity-based classification stayed incomplete for the whole run. Separately, a bounded diagnostic scout "missed the non-null PS because its inspection gate was closed after late injection" during a live-attach RE session (`0.3.174`→`0.3.175` forced a live re-query to fix it). A related but distinct case: short Ctrl+F10 presses were caught by the D3D draw-stream artifact probe but missed by the OpenXR blit-stage BMP dumper in the same frame window, because the two stages polled the hotkey independently (`0.3.87-dumpsync` mirrored the arms to fix it).
**Why it generalises:** Both failures share one root cause — a hook or poll that only sees events after its own installation/arm point silently under-reports pre-existing state. Any injected/attached instrumentation needs either a construction-seam audit (what existed before attach) or synchronized arm points across independent capture stages.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Attach versus launch injection — and one-time construction seams"
