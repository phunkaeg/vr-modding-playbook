# BioshockVR — BUILD_HISTORY harvest (lines 1-1100)
Lines read: 1-1100

### Global function-level hooks intercept your own mod's internal calls, not just the game's
**What happened:** 0.3.191 found that BioShockVR's own OpenXR eye blit and runtime D3D work called the same globally detoured D3D11/DXGI methods as BioShock's game rendering. Internal calls fell into draw classification, HUD capture, shadow probes, and tracked cbuffer state, and could recursively re-enter `Present` submission — the actual cause of the Virtual Desktop fail-fast crashes (`0xC0000409` reason 7) chased across 0.3.177-0.3.190. Fixed with a thread-local ownership guard: while the mod is doing its own D3D work, guarded hooks call the original methods directly instead of routing through the mod's own classification/telemetry pipeline.
**Why it generalises:** Any injected mod that globally detours the graphics API and also issues its own D3D/GL calls (compositing, probing, copying) will self-intercept unless it explicitly marks "this call is mine, not the game's." Six build cycles were spent chasing a phantom Virtual Desktop bug before this was found.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS Hooking & native-call discipline

### A suspended-launch injection needs an explicit readiness handshake, not a hope that hooks beat the game to it
**What happened:** 0.3.171 showed native `AHands` sampled at log line 37 while the hook-install thread was still running at line 175 — the game's own object lifecycle raced ahead of hook installation. 0.3.172 fixed this by having the injector create a per-process event, inject into the suspended game, block until `InstallD3D11Hooks()` signals completion, and only then resume the primary thread; a timeout or readiness failure now terminates the still-suspended process instead of silently running unhooked.
**Why it generalises:** Suspended-launch injection removes the "attach after the fact" blind spot, but only if you also gate thread resume on hook-install completion — otherwise you've traded one race for a narrower one.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS Attach versus launch injection — and one-time construction seams

### Attach-mode diagnostics that passively capture creation events will misreport already-bound state as absent
**What happened:** 0.3.175's shadow classifier reported every sampled draw as PS-null because it only recorded shader identity at `CreateVertexShader`/`CreateShader` time; when injection attached after the game had already created and bound those shaders, the classifier had nothing captured. The fix forced live `VSGetShader`/`PSGetShader` queries at classification time instead of relying on the historical creation log, which immediately revealed the shadow-test pass and its `screenToShadowBuffer` c17-c20 contract.
**Why it generalises:** Any live-state tracker seeded only by creation-time hooks is blind to everything that existed before the hook attached. When attach timing is uncertain, query current state directly instead of trusting an event history that may predate you.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS Attach versus launch injection — and one-time construction seams

### A downstream effect can sample the wrong eye's (or the wrong camera's) cached resource even when the visible geometry is correct
**What happened:** 0.3.175 proved the private per-eye depth buffer correctly held the controller-posed wrench, while BioShock's native center `1920x1080` depth still held the neutral desktop-pose wrench at a different location — and the shadow/mask pass sampled the stale center depth, producing a stationary cutout silhouette that looked like a shader bug. The real defect was resource *provenance*, not shading.
**Why it generalises:** Post-process and lighting passes often keep their own reference to "the" depth or G-buffer. Per-eye stereo work that fixes the primary color pass can leave a secondary consumer still bound to the old mono/center resource, and the result looks like a geometry or shader glitch instead of a wiring bug.
**Chapter:** 14-render-pass-hazard-atlas.md
**Status:** SHARPENS Sub-resolution passes need per-eye company / There is no canonical G-buffer

### An authored mount correction must be composed on the correct side of the tracked-delta chain, or it silently does nothing visible
**What happened:** 0.3.182 loaded a +90-degree grip-yaw offset correctly (confirmed in logs) but the user still saw the authored neutral pose from the wrong side, because the offset was applied additively after the user's live controller roll rather than as part of the reference frame. 0.3.183 fixed it by composing the correction as `currentController * authoredMount` — a real basis change applied before the tracked delta — not appended after it.
**Why it generalises:** "Loaded correctly" and "visually correct" are different claims when a fixed offset and a live tracked rotation are combined; multiplication order determines whether the correction is a basis change or a no-op residual.
**Chapter:** 02-viewmodels-and-hands.md
**Status:** SHARPENS One trim, one algebra, one ray

### A pre-skinned draw's VS shader signature tells you whether posing it is even possible before you try
**What happened:** RenderDoc on `BS4_wrench.rdc` (0.3.162) showed the hand/forearm draw's material VS consumes only `POSITION/TANGENT/BINORMAL/NORMAL/TEXCOORD0` and exposes no bone-palette cbuffer or SRV — the mesh arrives at that shader already GPU-deformed. This proved independent controller-driven posing of the hand mesh via WVP/matrix tricks was structurally impossible; the fix requires an engine animation/skeletal seam instead.
**Why it generalises:** Before spending cycles on a transform-level fix for a visibly-wrong attached mesh, inspect the consuming shader's input signature. If bone data isn't present at that stage, no downstream matrix trick can fix per-bone posing — the ownership boundary is upstream, in animation.
**Chapter:** 02-viewmodels-and-hands.md
**Status:** SHARPENS Drive the engine's own skeleton; don't override the skinned vertices

### Bracket an unknown sign/axis convention with symmetric opposite-extreme tests, not one guess
**What happened:** `WeaponViewmodelGripYawOffsetMilliDegrees` was tested at `+90000` then `-90000` (0.3.182→0.3.185) specifically to swing the neutral pose to opposite quarter-turn offsets and localize the authored basis error, rather than iterating single-value guesses. The same technique (test `+90000`, learn, test `-90000`) also resolved a separate horizontal-axis quarter-turn bug at the camera-recenter layer.
**Why it generalises:** For any unknown sign/axis convention (rotation direction, position delta sign, up-vector handedness), a single test only tells you "wrong"; two symmetric extremes tell you the actual mapping and cut debugging time roughly in half.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS Falsify your own hypothesis before shipping a fix

### An isolation gate that also suppresses the fallback path can turn a partial success into an apparent total failure
**What happened:** 0.3.59 added `StereoWorldMatrixStereoOnly=1` to cleanly isolate the native-matrix stereo proof. 0.3.60's log showed why the headset then displayed only solid proof colors: strict isolation also blocked the existing mono-fallback accumulation for every non-qualifying draw (`stereoWorldMatrixStereoProofAppliedTotal=0`, all 49,112 attempts fell back, and fallback itself was skipped because matrix-only was active), starving the private source entirely. The actual per-draw math was untested by this run.
**Why it generalises:** An A/B toggle meant to isolate one code path can accidentally also disable the safety net that would otherwise show a degraded-but-visible result. Check whether "isolate the variable" and "keep everything else observable" are actually the same switch before trusting a null result.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS Your control group must consume the variable under test

### Recentering math needs subtract-then-rotate-by-inverse-baseline-yaw, and axis mapping must be verified empirically, not assumed
**What happened:** An early recenter implementation used a fixed heading offset and left horizontal axes exactly quarter-turned (forward→right, right→backward, etc., confirmed live in 0.3.124). It was replaced (0.3.125) with a proper basis: subtract the baseline stage position, then rotate the horizontal delta by the inverse of the baseline HMD yaw, so recenter-time facing defines local forward/right. A related bug in the same lane (0.3.123) was that the engine's own decoded scene-node position turned out to be the negative of true world position — silently inverting every delta until it was found and the subtraction sign was corrected.
**Why it generalises:** Both the axis-swap and the sign-inversion were invisible in code review and only surfaced as "forward now goes sideways" in the headset; recenter/basis math needs a live directional test, not a math review, and the engine's own coordinate convention cannot be assumed symmetric with intuition.
**Chapter:** 01-camera-and-tracking.md
**Status:** SHARPENS Recenter & horizon

### Arbitrate between physical and synthetic input by recency, with a bounded hold window, not by static priority
**What happened:** 0.3.140 found that a naive merge of real XInput state with synthetic OpenXR-derived state let either source silently override the other. The fix: a recently-active physical stick temporarily owns locomotion, a recently-active physical stick suppresses synthetic VR turn, with `ControllerPhysicalStickPriorityMs` defaulting to 250ms — after which control reverts to whichever source is live. Buttons remain OR'd and triggers max'd, so the arbitration is scoped to the axes that can double-drive.
**Why it generalises:** When a virtual/synthetic controller and a real one both feed the same downstream consumer, a static "synthetic always wins" or "physical always wins" rule breaks whichever source the user is actually using. A short recency window resolves the ambiguity without needing to know the game's input priority rules.
**Chapter:** 03-input-and-locomotion.md
**Status:** SHARPENS The double-driving trap (read this twice)

### Zeroing an animation's blend weight is not the same as freezing it at a good pose
**What happened:** 0.3.165 suppressed the idle-animation weight to stop unwanted idle motion, but 0.3.166's live test showed this exposed BioShock's raw straight-finger bind pose, because every fresh idle handle still restarted at authored time `0.0000` with rate/weight `1.0`, producing one-frame forward-pose flashes. The fix called the native `SkeletonInstance` position/rate setters (not just weight) to seek the current channel-0 handle to a specific authored time (`HandsIdlePoseTimeMilli`) and hold rate at zero.
**Why it generalises:** An animation system's blend weight, playback rate, and playback position are three separate levers; suppressing only one leaves the others free to reset to a default (often the bind pose) on the next state transition. "Freeze at pose X" requires owning all three.
**Chapter:** 02-viewmodels-and-hands.md
**Status:** SHARPENS Don't fix the visible model by retuning the invisible systems

### In a per-draw stereo replay hot path, reuse dynamic constant buffers instead of allocating new ones every draw
**What happened:** 0.3.131 replaced a pattern of creating two fresh default-usage D3D11 buffers per applied stereo draw with per-context/per-eye/byte-width cached dynamic buffers updated via `D3D11_MAP_WRITE_DISCARD`. The old clone-per-draw path was kept only as an automatic fallback, toggleable with `StereoWorldReusableMatrixBuffers=0`.
**Why it generalises:** Any inject-and-replay stereo technique that clones a shader constant buffer per eye per draw multiplies driver-side resource churn by draw count; caching one reusable buffer per (context, eye, size) key and using discard-mapping is a standard fix that applies regardless of the specific engine or API.
**Chapter:** 09-d3d11-openxr-injection.md
**Status:** SHARPENS Performance accounting
