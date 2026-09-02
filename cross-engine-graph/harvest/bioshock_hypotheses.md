# BioshockVR — HYPOTHESES harvest
Lines read: 1-1344

### Preserve the source view's viewport/scissor when replaying a draw list — never force full-target
**What happened:** Private-eye replay forced a full-target viewport/scissor on every replayed draw. A bounded secondary/portal-style view (source rect `0,0,1920,279` inside a `1920x1080` target) was therefore expanded to fill the whole private eye, producing a complete exterior "city" backdrop shell over the interior scene, plus a large frame-rate penalty. Nine builds (`0.3.108`-`0.3.114`) falsified PS-null skipping, screen-space-SRV demotion, clear-boundary/epoch tracking, and draw-order sub-banding before `0.3.115-viewrect` tried simply preserving the original non-full scissor — 256 preserved rows and the shell vanished completely.
**Why it generalises:** The wrong model was "a replayed draw is defined by its shader and resources"; the right model is "a draw's meaning includes its viewport/scissor rect — expanding it changes which logical view you're showing," turning a bounded secondary view into a full-frame one.
**Chapter:** 09-d3d11-openxr-injection.md
**Status:** SHARPENS "Preserve render-view provenance"

### Guard your own hooks against your own reentrancy before blaming a third-party OpenXR layer
**What happened:** A motion-compensation OpenXR implicit layer (`XR_APILAYER_NOVENDOR_motion_compensation_32.dll`) crashed the mod with `0xC0000409` reason 7 at `VirtualDesktop.LibOVRRT32_1.dll+0x1e98c`, but only after the mod's own D3D11 hooks were installed — other OpenXR titles stayed stable on the same runtime. The layer's internal D3D11/DXGI calls were re-entering the mod's own draw/HUD/shader-tracking hooks. `0.3.191` added a thread-local guard so every hook calls straight through to the original while guarded; the build then survived 1,440 focused frames with the layer loaded.
**Why it generalises:** The wrong model was "a crash inside a third-party layer's module is that layer's bug." The right model: your hooks fire for *any* caller, including layers making their own D3D11 calls during their own init/submit — reentrancy into your own classification/tracking code is the actual hazard, not the layer itself.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Hooking & native-call discipline"

### Force symmetric/centered FOV as an A/B to split "asymmetric-projection math bug" from "mono screen-space resource bug"
**What happened:** Persistent shadow/lighting/volumetric offsets could have come from a wrong asymmetric-eye projection reconstruction, or from a resource that is simply mono (one camera, sampled by two eyes). `Ctrl+F6` toggled both the render FOV and the submitted OpenXR projection to the same centered value as a single-variable control, without touching any other stereo state.
**Why it generalises:** This is a reusable diagnostic wedge for any stereo renderer: an artifact that only appears/changes under asymmetric FOV implicates your reconstruction constants; an artifact unchanged in centered mode implicates a mono/center-camera resource and rules out projection math, redirecting effort toward per-eye resource ownership instead of more matrix tuning.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Your control group must consume the variable under test"

### After injecting into a running process, query live bound state at draw time — don't rely only on intercepted create/bind calls
**What happened:** Early builds hooked `VSSetConstantBuffers`/`PSSetConstantBuffers` and looked for known cbuffer byte sizes, but recorded zero matching binds across a stable 69,042-Present run — despite the target geometry clearly rendering. `0.2.4-config-shaderprobe` switched to sampling the actually-bound constant buffer at `DrawIndexed` time and immediately recovered the expected sizes (576/832 bytes) on the exact viewmodel draws.
**Why it generalises:** The wrong model was "intercepting the mutator call sees all state." Resources created, mapped, or bound before your hook installs are invisible to call interception; only querying the *current* live state at the moment you care about it (draw time) is reliable after an attach-style injection.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Attach versus launch injection — and one-time construction seams"

### A community shader-fix mod for the same game is a ground-truth RE oracle, not just prior art
**What happened:** An old stereoscopic-3D shader-fix package (`Bioshock 1 Remastered 3D fix WIP1`) for the same title gave concrete constant offsets — `screenDataToCamera` at `c3`, `worldViewProj` at `c10-c13`, `localEyePos` at `c14` — derived from someone else's manual shader RE years earlier. Live RenderDoc/runtime probes in `0.3.22`-`0.3.25` confirmed those exact offsets on the live shaders (`worldViewProjCommon=c10-c13`, `worldViewProjShifted=c9-c12`), collapsing what had been ~20 builds of blind scanning into direct verification.
**Why it generalises:** For any older/modded PC title, search for legacy stereoscopic-3D (3D Vision/Helix/3Dmigoto), reshade, or fan-patch shader-fix repositories before scanning cbuffers blind — they encode already-solved constant layouts you can verify instead of discover.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "Tooling worth adopting"

### Shader-reflection byte size and the runtime's actual allocated buffer size are two different numbers
**What happened:** RenderDoc's offline shader reflection reported `$Globals` layouts of 560 and 752 bytes for representative world/viewmodel draws. The live runtime allocations for the same draws were 576 and 832 bytes — a strict filter keyed to the reflected sizes matched nothing for many builds (`world_candidate_sample=0` across `0.3.8` and later), until the classifier was changed to accept the live-observed sizes as the primary signal and reflected sizes as secondary corroboration only.
**Why it generalises:** Static reflection describes the shader's declared/compiled layout; the runtime buffer can differ by padding, allocator rounding, or per-variant shader compilation. Never gate a live classifier on an offline-reflected exact byte count — validate against `ID3D11Buffer::GetDesc()` (or equivalent) from the live process.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Tooling lies in specific, learnable ways — know them before you trust a reading"

### Before RE-ing an engine "limit," check your own leftover debug scaffolding
**What happened:** A hard yaw/pitch/roll stop at 45 degrees looked like an engine or camera-system constraint worth reverse-engineering. It was in fact the mod's own `EngineCameraOrientationMaxDegrees=45` proof-stage clamp, applied independently per axis before converting the HMD residual to engine rotator units — confirmed directly from the mod's own source, not from any engine behavior.
**Why it generalises:** Early proof-of-concept code often ships small guard clamps to keep an experiment safe; once the experiment graduates, those clamps are easy to forget and easy to misdiagnose as "the engine won't let me." Check your own instrumentation/safety code for hardcoded bounds before spending RE effort hunting an external cause.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Falsify your own hypothesis before shipping a fix"

### A signed offset that overshoots in both directions means the model is wrong, not the sign
**What happened:** A weapon grip-yaw correction was tuned as `+90000` milli-degrees, which left the model quarter-turned one way; `-90000` left it quarter-turned the other way. Neither sign was closer to correct — both were roughly equally wrong in opposite directions. The fix was not a sign flip but recognizing the value was being applied at the wrong point in the transform chain (before the tracked delta, as a mount correction, not as a tunable knob), and resetting it to `0` while the actual placement bug moved to a different layer.
**Why it generalises:** When bisecting a signed parameter and both extremes fail symmetrically, that is evidence against the whole model (wrong basis, wrong composition order, wrong space), not evidence that you need a finer-grained sign/magnitude search. Stop tuning and re-derive which transform the value should belong to.
**Chapter:** 02-viewmodels-and-hands.md
**Status:** SHARPENS "Euler/quaternion traps (the recurring math failures)"

### Confirming a call reaches a generic input dispatcher does not confirm it owns the write you need
**What happened:** A synthetic mouse-yaw impulse was confirmed (via Ghidra) to enter `UGamepadPlayerInput::CalculateInput` and the `PlayerInput` script dispatcher at a specific address. That looked like progress, but the dispatcher only does deadzone/response math — it never writes the controller's yaw field directly, so the "confirmed" call chain established reachability, not ownership. The rendered view snapped via a different route (`RequestHeadPoseSnapTurn`), while movement direction and the weapon mesh never turned.
**Why it generalises:** A generic dispatcher, event bus, or input-processing entry point is a relay, not necessarily the owner of the state you're chasing. Proving a call reaches "the input system" is a weaker claim than proving it reaches the specific field write; keep tracing past the first plausible-looking function.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "'Installed at a verified-correct address and never fires' = you hooked a wrapper"

### A capture tool's own resource exhaustion can masquerade as a target-process crash
**What happened:** RenderDoc reliably crashed only when capturing the equipped-weapon viewmodel state, at a fixed offset in `renderdoc.dll`. Static disassembly showed that offset was RenderDoc's own intentional fatal path after an allocation failure; live debugging under x32dbg confirmed the failed allocation was `0x200020` bytes while the paused 32-bit process's largest contiguous free virtual-address region was only `0x1D0000` — RenderDoc's second scratch allocation simply couldn't fit in a fragmented 32-bit address space.
**Why it generalises:** In a 32-bit target especially, a capture/debug tool crashing at a specific spot is not automatically a bug in the thing you're inspecting. Check whether the tool itself is the one running out of resources (address space, handles, memory) before attributing the failure to game code.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Tools that cannot see the process report it as absent"

### Re-poll runtime state immediately after any blocking wait in the session lifecycle
**What happened:** The OpenXR startup sequence polled `READY`, called `xrBeginSession`, then blocked on a `~2030ms` `xrWaitFrame` — and rendered/submitted without polling again first. State transitions the runtime generated during that wait (session becoming `VISIBLE`/`FOCUSED`, or being torn down by a third-party runtime) were invisible to the app's policy, and the external runtime failed before the next `Present` could see them. Re-polling immediately after `xrWaitFrame` and gating eye-image work on the refreshed state fixed it.
**Why it generalises:** Any blocking call in a session/runtime lifecycle (not just OpenXR) can hide state changes that occurred entirely inside the block. Treat "I checked state before I waited" as stale the instant the wait returns — always re-check immediately after, before acting.
**Chapter:** 09-d3d11-openxr-injection.md
**Status:** SHARPENS "The OpenXR frame loop is an ownership contract"

### A synthetic controller's connection state must be latched, not answered fresh on every poll
**What happened:** Returning "disconnected" on every neutral poll of a synthetic XInput slot (when no real activation had occurred yet) made the game repeatedly flap the controller's presence, rather than cleanly treating it as absent. Only 16 of many synthetic "success" polls landed, and all of them coincided with unrelated snap-turn pulses. Latching the synthetic slot to "present" only after the first deliberate activation, and holding that answer stable through tracking gaps, fixed the flapping.
**Why it generalises:** An engine's device-management layer expects a controller's presence to be a stable fact it can cache, not something that flickers between polls; answering "truthfully" per-poll from noisy synthetic state can be worse than a simple latch that changes state only on a deliberate edge.
**Chapter:** 03-input-and-locomotion.md
**Status:** SHARPENS "A synthetic controller's *presence* is a lane too (rung 3 gotcha)"
