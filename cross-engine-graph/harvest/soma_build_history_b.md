# SOMAVR — BUILD_HISTORY harvest (lines 1300-end)
Lines read: 1300-2697

### A single wrong term in a quaternion-to-matrix conversion produces skew that only shows up under rotation, not as a crash
**What happened:** The XY cross-term used `2*y*y` where `2*x*y` was required, shearing the HPL view basis progressively as the headset rotated — a regression introduced during a math-extraction refactor (`0.5.9-rotationfix`), not a logic error. Fix added regression tests requiring the generated rotation basis to stay unit-length and mutually orthogonal, and requiring matrix rotation to agree with an independently implemented quaternion-vector rotation.
**Why it generalises:** Quaternion/matrix typos are copy-paste-adjacent (same variable reused) and pass casual visual review because error is proportional to angle — it looks fine near identity and only skews at extreme angles, exactly where testers stop looking. Any camera-math port needs an orthonormality/independent-cross-check test, not just "looks right" visual QA.
**Chapter:** 02-viewmodels-and-hands.md
**Status:** SHARPENS "Euler/quaternion traps (the recurring math failures)"
**API-specific:** none

### Alternate-frame-rendering silently corrupts temporal effects that keep one shared history buffer per renderer, not per eye
**What happened:** `HPL3_Renderer_RenderPostPostEffects` copies exactly `0x40` bytes (a 4x4 previous-view matrix) from the active frustum at `*(renderer+0x20)+0x158` into a single renderer-owned history object at `*(renderer+0x438)+0x80`. Under AFR, eye A's temporal reprojection reads eye B's previous-frame matrix, producing an image-trail/motion-blur artifact that looks like a stereo bug but is actually a history-ownership bug. Fix required a guarded per-eye left/right history bank, seeded on first identity use and reset on renderer replacement, recenter, or calibration change.
**Why it generalises:** Any engine forced into AFR (a common first stereo path for single-threaded renderers) will silently misfeed temporal effects (motion blur, TAA, SSR, film grain) unless every stateful post-effect resource is audited and duplicated per eye — invisible until you specifically look for eye-order mismatch.
**Chapter:** 14-render-pass-hazard-atlas.md
**Status:** SHARPENS "The temporal trap, in detail"
**API-specific:** none

### Don't trust the first valid pose from a freshly created XR reference space as your calibration anchor — wait for it to settle
**What happened:** F10 calibrated neutral pose against OpenXR frame `2857` at head `Y=-1.244683`; the very next frame settled near `Y=+0.543`, a spurious ~`1.79 m` jump that placed the camera through the roof (`0.5.10-poselatch`). Root cause was a one-frame startup reference-space discontinuity, not a world-scale or projection bug. Fix required both orientation and position tracked bits, plus a deterministic latch — 8 consecutive unique poses within `0.25 m` / `45 degrees` of each other — before accepting a neutral pose; a large jump resets the latch instead of becoming a permanent offset.
**Why it generalises:** Any tracking API's reference space can report a transiently wrong first sample while still stabilizing after creation/recenter; treating "valid" as "ready to use" is a recurring VR bootstrap bug independent of engine or graphics API.
**Chapter:** 01-camera-and-tracking.md
**Status:** SHARPENS "Recenter & horizon"
**API-specific:** none

### Classify a resource as per-eye vs shared by hashing its footprint at a matched pose frame across both eyes — don't guess from where it's declared
**What happened:** An automated probe hashed each post-effect's bound texture/framebuffer footprint and required *both* eyes to produce resources at the *same* nonzero pose frame before calling a resource "eye-distinct" (`0.37.0-post-resource-probe`); ordinary AFR timing cannot satisfy that gate by accident. This correctly separated true per-eye state from shared scratch resources without reading engine source.
**Why it generalises:** Distinguishing "this buffer needs duplicating per eye" from "this buffer is safely shared" is exactly the kind of judgment call that's easy to get wrong by inspection; a resource-identity fingerprint compared across a controlled two-eye sample is a reusable, engine-agnostic test.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Measure, don't theorize: the readback probe"
**API-specific:** none

### Not every multi-pass framebuffer pair is a temporal history — some are same-frame scratch that gets fully overwritten
**What happened:** Initial instinct was that ToneMapping's six bloom framebuffer/texture pairs needed the same per-eye duplication as the confirmed ImageTrail history. Investigation (`0.52.0` note) showed the bright/blur passes fully rewrite all six every frame — sequential intra-frame scratch, not carried state — so duplication was correctly skipped.
**Why it generalises:** Reflexively duplicating every "extra" framebuffer under stereo bloats memory and can itself introduce eye-desync bugs; the ping-pong-buffer-vs-temporal-accumulator distinction recurs in bloom/blur/SSR chains on any engine and needs the same per-resource proof, not a blanket rule.
**Chapter:** 14-render-pass-hazard-atlas.md
**Status:** SHARPENS "There is no canonical G-buffer"
**API-specific:** none

### Explicitly preload a companion DLL from your own module's directory before its first delay-load call — don't rely on the process's default search path
**What happened:** `somavr.dll` was injected from `build-openxr\Release`, but the first delayed `xr*` import searched from SOMA's process/search path and failed to find `openxr_loader.dll` sitting right beside the injecting DLL, crashing with a `KERNELBASE.dll` exception `0xc06d007e` (classic delay-load module-not-found, `0.2.2-xrloaderpath`). The fix explicitly loaded the companion DLL from the directory containing the already-loaded module before any API call that would trigger the delay-load.
**Why it generalises:** Any injected DLL that ships its own dependency (loader shim, runtime, codec) cannot assume Windows' default DLL search order includes the injecting module's own folder — that assumption only holds for the host executable's own directory, not an injected module's. This bites on first launch of any mod that ships side-by-side dependencies, regardless of engine.
**Chapter:** 07-engine-integration-safety.md
**Status:** NEW
**API-specific:** none

### Exit an injected worker thread when it detects it is the process's last remaining thread, not via an event-based stop/detach handshake
**What happened:** A crash-dump investigation (`0.5.4-renderdiag`) found an orphaned SOMAVR worker thread still running in a process with no window and exactly one thread — the prior stop-event/DLL-detach cycle could leave the worker alive after the host was effectively gone. Changing the exit condition to "return when this is the final thread in the process" eliminated the orphan without needing the handshake to fire correctly during teardown.
**Why it generalises:** DLL-injection teardown races (host exiting while a hook thread waits on a signal that never comes because the signaling code already unloaded) are a generic Windows injection hazard, not an HPL3 quirk; checking your own thread's cardinality is a simpler, race-free exit condition than coordinating a clean stop signal during process death.
**Chapter:** 07-engine-integration-safety.md
**Status:** NEW
**API-specific:** none

### Treat the graphics context as replaceable at any time — rebuild bound resources when it changes, don't assume the bootstrap context persists
**What happened:** An early OpenXR session probe succeeded on SOMA's startup context (`hglrc=0x10000`), but the game's real per-frame rendering used a different context (`hglrc=0x30000`) created later. The eventual fix (`0.33.0-depth-resources`) made a changed HDC/HGLRC trigger full runtime recovery, while changed recommended dimensions or sample limits trigger a transactional rebuild of frame resources, instead of assuming the context captured at init time stays valid.
**Why it generalises:** Engines that create a throwaway context during startup and swap to a real one before the main loop are common; injected graphics code that binds resources to "the current context" at load time rather than at first real frame will silently target a dead context. This is squarely a context-based-API problem (OpenGL/WGL), distinct from D3D's explicit device-object model — the playbook's D3D chapters have no equivalent because D3D doesn't have this failure mode.
**Chapter:** 10-graphics-apis.md
**Status:** SHARPENS "There is no device to bind — bind the context"
**API-specific:** OpenGL

### When engine internals expose no stable signature, hook the graphics API entry point itself — but remember not all shader data arrives through it
**What happened:** `avShadowMapOffsetMul` had no stable internal setter to hook, so signature-independent interception of raw `glUniform2f`/`glUniform2fv`, filtered to that one uniform name, let an F7 toggle isolate shadow jitter without touching engine code (`0.5.3-shadowjitter`). Separately, the deferred shadow programs (`942`/`944`) and the reflection/water program (`989`) sourced their view/projection and SSR parameters from bound uniform-buffer ranges, not direct uniform uploads — a plain `glUniform*` hook silently missed both passes until UBO binding/contents were captured per program and eye (`0.5.5-reconstruct`).
**Why it generalises:** The graphics API surface is stable across game versions even when engine internals aren't, making it a good hook point for isolating a single named value; but any engine using UBOs (or D3D constant buffers) needs a second interception path for buffer-sourced data, or matrix-capture work will quietly cover only some passes.
**Chapter:** 10-graphics-apis.md
**Status:** SHARPENS "Reading the projection: hook the uniform upload"
**API-specific:** OpenGL

### OpenGL's depth convention is not implicit — confirm and convert it explicitly before submitting compositor depth layers
**What happened:** Ghidra plus HPL2 source confirmed SOMA's OpenGL depth is finite/standard, with submitted `XrCompositionLayerDepthInfoKHR` min/max fixed at `0/1`, while HPL's near/far are derived by dividing by world-units-per-meter — a separate conversion from the engine's own near/far values (`0.33.0-depth-resources`).
**Why it generalises:** OpenGL's NDC z range (`-1..1`) and its window-depth mapping conventions differ from D3D's (`0..1`) and from what a given compositor API expects; this project is the corpus's only OpenGL data point, so nothing else in the playbook has verified this conversion in practice. Any future OpenGL target must independently re-derive and unit-test the near/far-to-submitted-depth-range mapping rather than copying D3D assumptions.
**Chapter:** 10-graphics-apis.md
**Status:** SHARPENS "Depth submission differs in the details, not the intent"
**API-specific:** OpenGL

### Implement layered config presets with a two-pass parse — pre-scan the preset key, apply its defaults, rewind, then parse normally
**What happened:** `[Comfort] Preset=custom|minimal|balanced|maximum` (`0.49.0-readiness-presets`) is resolved by scanning the file once for just the preset key, applying that preset's defaults, rewinding the parser, then doing a normal full parse. This guarantees an explicit setting anywhere in the file overrides its preset default, without requiring presets to be declared first or the parser to support forward references.
**Why it generalises:** "Preset plus override" is a near-universal config pattern (graphics tiers, comfort presets, difficulty presets); a naive single-pass approach forces either strict section order or complex merge logic, while the two-pass rewind technique is small and engine-agnostic.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Config-system rigor"
**API-specific:** none
