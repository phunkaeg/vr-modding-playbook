# BioshockVR — FAILURE_REGISTRY harvest
Lines read: 1-1412

### Classify an unknown draw/resource by multiple independent signals, never by one weak identity like size or count
**What happened:** Allocation-size and index-count classification repeatedly produced false positives/negatives: reflected+runtime cbuffer sizes 576/832 bytes matched both the viewmodel lane and, later, unrelated world draws; the confirmed hand/forearm index count `26178` failed to recur in a later build that nonetheless had the right cbuffer sizes; the 36-index draw signature used for a shadow-mask producer recurred on many unrelated draws, forcing a redesign that required the full producer/consumer contract (target format, PS-null stencil stage, shadow-test SRV shape, exact consumer resource identity) before any replay was authorized.
**Why it generalises:** allocation sizes, index counts, and other cheap identity proxies are attractive because they're free to read, but padding/pooling/compiler layout make them ambiguous across engines; RE-based classification needs a joint key (shader identity + resource identity + pass position + content) before it can gate a mutation.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "Classify an unknown value by its magnitude, not its declared type"

### Treat each rung of a proof ladder as proving exactly one claim — don't let a lower rung's success imply the next one
**What happened:** BioshockVR ran a strict sequence — clone-bind (buffer-swap plumbing, dataMutation=0) → numeric proof (byte mutation on cloned buffer, 512 applied) → pose proof → wide-view proof → direct same-target draw replay (8192 applied) → private eye-target bind proof (128 applied, 0 failures) → eye-blit proof → private-HDR blit — with every rung's writeup explicitly stating success meant only "this mechanism works," not "stereo is done." One run showed lifetime clone-bind applied counters at 4096 while numeric/pose/wide-proof totals stalled at 5, proving the mechanisms diverge and must be checked independently.
**Why it generalises:** any cross-engine stereo/injection project accumulates many semi-working intermediate builds; treating "it ran without crashing" or "the counter moved" as endorsement of the final goal is the single most repeated failure mode in this registry.
**Chapter:** 09-d3d11-openxr-injection.md
**Status:** SHARPENS "The proof ladder" / "The stereo ladder as a de-risking device"

### Give bounded diagnostic logging independent lifetime counters, separate from the sampled event budget
**What happened:** A shared bounded log-line budget for clone-bind events was spent entirely on 23 "skipped: pose_not_ready" rows before OpenXR pose became ready, producing zero raw "status=applied" lines even though later frame-summary counters proved 109 applies had actually happened by frame 34.
**Why it generalises:** any hot-path instrumentation that rate-limits or samples per-event log lines can systematically hide the exact evidence you're looking for if skip and apply share one budget; cumulative counters must be tracked and surfaced independent of what got logged verbatim.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Measure, don't theorize: the readback probe"

### Static shader-reflection buffer sizes and live driver-allocated buffer sizes will legitimately differ — trust the runtime value for classification
**What happened:** RenderDoc reflection reported the equipped-wrench VS `$Globals` at 544 bytes and the hand/forearm buffer at 752 bytes, but live `ID3D11Buffer::GetDesc().ByteWidth` for the same draws returned 576 and 832 bytes. The registry explicitly forbids rejecting a live candidate merely because it is larger than the reflected layout.
**Why it generalises:** alignment padding and constant-buffer pooling mean reflection metadata (from any offline tool) and runtime allocation sizes are two different truths; use reflection for field layout/offsets, but classify live draws by what the driver actually bound.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Tooling lies in specific, learnable ways — know them before you trust a reading"

### A screen-space buffer sampled with per-eye-shifted UVs reads stale data unless it is regenerated per eye
**What happened:** RenderDoc showed a boulder draw sampling a mono, target-sized shadow mask (`s_shadowMask`, R8G8B8A8_UNORM, EID 3176) from PS slot 2 using `screenUV = screenTransform * worldViewProj * vertex`. Once native per-eye WVP went live, that UV shifted per eye while the mask stayed centered/mono, producing eye-dependent black sides; a neutral-white override on the mask was tried and made results worse, confirming the fix must be per-eye regeneration, not suppression.
**Why it generalises:** any deferred/composited technique that bakes a screen-space pass once per frame (shadow masks, SSAO, reflections, volumetrics) implicitly assumes one camera; stereo-izing the geometry pass without stereo-izing its screen-space dependencies creates this exact incoherence class in any engine.
**Chapter:** 14-render-pass-hazard-atlas.md
**Status:** SHARPENS "There is no canonical G-buffer" / "Sub-resolution passes need per-eye company"

### Never implement a comfort/pacing frame by dropping to zero OpenXR composition layers
**What happened:** Two independent crash dumps under a streaming OpenXR runtime reproduced the same fail-fast (`0xC0000409` reason 7 at `VirtualDesktop.LibOVRRT32_1.dll+0x1e98c`, execute-access violation at freed marker `0xDEDEDEDE`) specifically correlated with `XrFrameEndInfo.layerCount=0` comfort-blackout submissions. The fix was to keep the projection layer present every frame and clear its eye images to black instead of submitting zero layers.
**Why it generalises:** composition-layer count is part of the runtime's frame contract, not a free toggle; some runtimes (especially streaming/compositor-in-the-loop ones) exercise distinct code paths on layer-count transitions, so "submit nothing" is riskier than "submit black."
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Budget OpenXR composition layers — over-submitting freezes the whole HMD" (adds the symmetric under-submission failure mode)

### Log the fully-resolved config state at the top of every run — an implied enable can be silently defeated by an explicit default elsewhere
**What happened:** A feature (`CbufferWriteProbe`) was designed to be implicitly enabled whenever a dependent feature (`StereoWorldProbe`) was on, but an explicit `CbufferWriteProbe=0` sourced from the INI overrode the implied enable — twice, in two separately logged runs — silently discarding the evidence those builds existed to collect, until the config file was corrected to state the dependency explicitly.
**Why it generalises:** layered config systems (explicit key > implied dependency > code default) are common everywhere; a run that "looks" like it ran the intended experiment but silently didn't wastes an entire test cycle on any project. The fix is always to make the resolved value observable, not to reason about which layer should win.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Settings lie: read the value the consumer receives, not the one you wrote" / "Test-artifact config files silently outrank your code defaults"

### After attaching to an already-running process, query live pipeline state instead of trusting your own creation-time cache
**What happened:** BioshockVR's shader-identity cache is populated only from `Create*Shader` calls the DLL observed. Attach-to-running injection happens after the game has already created and bound shaders, so a cache miss was misread as "no live pixel shader," causing one build to misclassify every 36-index mask row as a stencil volume and making the real shadow producer unreachable. The fix was to query `VSGetShader`/`PSGetShader` directly from the live context.
**Why it generalises:** any hook-based tool that builds identity caches from creation-time interception has a blind spot for objects that existed before the hook was installed; attach-mode injection on any engine reintroduces this gap, so classification-critical reads should hit the live API, with the cache reserved for cheap correlation only.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Attach versus launch injection — and one-time construction seams"

### A completed LoadLibrary call is not proof your hook is installed before the game's next construction event
**What happened:** Remote `LoadLibraryW` returning success let the game resume and construct its hands/animation actor before the DLL's own asynchronous hook-install worker thread had finished attaching the recreation detour, so two full attach-to-running test sessions silently missed the seam they were built to catch. The fix was a cross-thread readiness handshake with explicit log ordering: `hook_ready_event status=connected`, then install-signaled, then first construction — verified in that order.
**Why it generalises:** DLL injection completing and your hooks actually being live are two different events on any platform; any project timing a hook against a one-time engine construction event needs an explicit ready signal and ordered log proof, not just "the module loaded."
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Attach versus launch injection — and one-time construction seams"

### Windows will not hot-swap a loaded DLL image — always start a fresh target process per build under test
**What happened:** With an older DLL already loaded and hooked into a running BioShock process, a normal Release rebuild silently failed to overwrite the on-disk `bioshockvr.dll` because the file was locked by the running image, leaving the tester unknowingly running stale `0.3.19` while believing they had tested `0.3.20`.
**Why it generalises:** this is a Windows loader mechanic, not an engine one, so it applies to any DLL-injection mod on any Windows game; a second inject of the same module only bumps the refcount, so build/test workflows must close the target process before rebuilding and verify the loaded version via a self-identifying log line before trusting a result.
**Chapter:** 07-engine-integration-safety.md
**Status:** NEW

### Audit for third-party OpenXR implicit API layers sitting inside your own call chain, and disable them per-process rather than globally
**What happened:** A 32-bit Motion Compensation implicit OpenXR API layer (`XR_APILAYER_NOVENDOR_motion_compensation_32.dll`) was silently present in the active OpenXR-to-D3D11 call chain and correlated with a reproducible runtime fail-fast. The fix was a process-local `OpenXRDisableMotionCompensationLayer=1`, explicitly not uninstalling the layer or editing the system-wide layer registry, since other software may depend on it.
**Why it generalises:** OpenXR/OpenVR runtimes support layered third-party interceptors (motion compensation, overlays, performance tools) that inject ahead of the app; any cross-engine VR project should enumerate and selectively disable layers per-process as a standard diagnostic step, distinct from disabling your own hooks.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Know which modules are DRM and exclude them early" (same discipline applied to XR runtime layers instead of anti-tamper)

### Don't assume a legacy haptics API's channel names map to physical hands — verify what each channel actually drives
**What happened:** XInput's two rumble motors are low-frequency and high-frequency channels, not left-hand/right-hand channels. BioshockVR's first haptics proof deliberately drove both OpenXR controllers from whichever motor was strongest rather than assuming motor-0 meant left hand.
**Why it generalises:** legacy input/haptics APIs often predate multi-controller VR and encode a different axis (frequency, motor index, port number) than the one a VR mapping cares about (hand); verify the API's actual semantic axis before wiring it to a per-hand abstraction, on any engine bridging gamepad-era haptics into VR.
**Chapter:** 02-viewmodels-and-hands.md
**Status:** SHARPENS "Haptics: hook where the contact actually happens"
