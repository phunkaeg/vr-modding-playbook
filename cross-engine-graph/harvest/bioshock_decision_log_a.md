# BioshockVR — DECISION_LOG harvest (lines 1-1900)
Lines read: 1-1900

### Mark your own D3D/OpenXR calls so your global hooks don't re-enter themselves
**What happened:** BioShockVR installed global D3D11/DXGI `Present`/`ResizeBuffers` hooks, then its own OpenXR eye-blit/swapchain work called back into D3D11 through those same hooks, crashing immediately under a runtime where non-hooking OpenXR mods stayed stable. The fix wrapped all OpenXR init/submission/copy work in a thread-local "internal-D3D" scope; every device/context/swapchain detour reachable there calls the real original directly instead of going through the mod's own detour logic.
**Why it generalises:** any mod that both globally hooks a graphics API and makes its own calls into that API for compositor/bridge work will recursively re-enter its own hooks unless it explicitly tags its internal call stack — true for D3D9/10/11/12, OpenGL, and Vulkan layers alike. The fix is always a thread-local "this call originated from me" flag, not a runtime-specific workaround.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS Hooking & native-call discipline

### Compare crash-dump exception records byte-for-byte across builds before blaming the newest change
**What happened:** dump `68008` under the newest build failed at the same `0xC0000409` reason-7 fail-fast inside `LibOVRRT32_1.dll+0x1e98c` as dump `40412` from the prior build — "byte-for-byte equivalent at the exception contract." That equivalence was used to rule out the new build's foreground-matrix code before continuing to look elsewhere (a loaded third-party OpenXR layer turned out to be the real cause).
**Why it generalises:** the reflexive move after a new build crashes is to suspect the newest diff. Diffing the exception record (fault address, module+offset, exception code) against the most recent known-bad crash is a cheap, engine-agnostic falsification step: an identical record means the new code is very likely innocent, and the search should move to whatever else changed instead of re-reviewing the diff.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS Crash-dump workflow

### Before rebuilding over a negative test, prove the config you shipped was actually armed
**What happened:** a build's log looked like a negative result for a new stereo-proof gate, but the log's own `hook_config` echo showed `stereoWorldPoseProof=0`/`stereoWorldWideProof=0` — the INI keys had simply never been added to the runtime config file. The call was explicit: "treat as config-missed and rerun, not rebuild."
**Why it generalises:** an inconclusive test result has two very different explanations — the code path didn't work, or it never ran. Grepping the log's startup config echo for the flag you meant to flip is strictly cheaper than a rebuild-and-retest cycle, and conflating the two wastes an entire test cycle, which is expensive in any headset-in-the-loop workflow.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS Settings lie: read the value the consumer receives, not the one you wrote

### Bind a replacement resource to whatever slot the consumer actually uses, not the slot one capture happened to show
**What happened:** a per-eye shadow-mask replay bound its private mask only at PS slot 2 because that was the slot seen in one RenderDoc capture; real consumers used other slots too, so masks kept producing zero binds. The fix scanned PS slots 0-7 for whichever slot was currently bound to the tracked *source* resource and rebound there instead.
**Why it generalises:** a captured slot number is evidence about one material variant in one frame, not a contract. Any stereo/per-eye resource substitution (shadow masks, reflections, SSAO, any screen-space pass) must match by resource/view identity, because different draw calls and material permutations legitimately bind the same logical resource at different slots.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS Attribute by ownership before shader identity

### An authored mount/trim offset belongs inside the baseline pose, applied before the live tracked delta — not after it
**What happened:** a configurable grip-yaw offset (tested at +90000, then -90000 millidegrees) was first applied *after* the live controller delta and produced a persistent quarter-turn error even though live roll tracked correctly. Moving the offset to apply *before* the tracked delta, and bypassing the neutral-pose early-out for it, fixed it — because the offset is the authored mount basis the delta must rotate around, not an add-on to the result.
**Why it generalises:** composing "authored calibration offset" and "live tracked delta" in the wrong order silently changes the basis the delta rotates in. Any attach-to-tracked-controller system (weapon mounts, tool grips, attached props) needs one explicit rule for whether authored offsets are baseline or overlay — get it backwards and it looks like a sign error but isn't fixable by flipping signs.
**Chapter:** 02-viewmodels-and-hands.md
**Status:** SHARPENS Grip pose places the model; aim pose points the ray

### Use one monotonic recenter event to rebase every independently-owned lane, not one detector per lane
**What happened:** separate recenter detectors for camera yaw/origin, crouch/eye-height, and tracked-viewmodel baseline let those three lanes latch different origins in different frames after a gesture. The fix made one trigger (a hotkey plus a bounded dual-stick hold) the single source of one monotonic recenter request, consumed identically by all three lanes in the same frame.
**Why it generalises:** whenever several independently-owned systems each derive their own "zero point" from tracking data, letting each detect the trigger separately risks them latching on different frames and drifting relative to each other — invisible per-system, visible only as cross-system incoherence. A shared, monotonically-increasing event token every consumer keys off costs nothing extra to plumb.
**Chapter:** 01-camera-and-tracking.md
**Status:** SHARPENS Recenter & horizon

### Arbitrate physical vs. synthetic input at the one hook that sees both, not downstream
**What happened:** physical gamepad sticks and synthetic VR-driven stick input could both reach the game's real `XInputGetState` import in the same frame. Arbitration (temporary physical-stick priority, suppression of synthetic body-turn while physical is active, bounded release window) was implemented inside the existing `XInputGetState` hook itself — the only point that sees true physical state before synthetic merging.
**Why it generalises:** once a mod hooks an input API to inject synthetic controller state, that hook is the *only* place that can see physical and synthetic input simultaneously and un-merged. Any coexistence policy implemented downstream of that hook is working from already-merged data and cannot correctly arbitrate.
**Chapter:** 03-input-and-locomotion.md
**Status:** SHARPENS The double-driving trap (read this twice)

### Read the engine's own control-bind config to find the native alias before writing a state field yourself
**What happened:** instead of reverse-engineering a player/capsule "crouch" field, the team read the installed `User.ini` and found `XENON_LTHUMB_BUTTON=Duck`, confirming an existing `Duck` alias already wired to `DuckKeyPressed`/`DuckKeyReleased`. Physical crouch was implemented by OR-ing a held synthetic button press into the existing XInput hook, reaching the native stance/collision owner with zero new hooks or memory writes.
**Why it generalises:** an engine's own shipped config/bind files are a legitimate, low-risk discovery channel for which native action a desired behavior maps to. Checking it before reverse-engineering an internal field is cheaper and safer, and routes the behavior through every native side effect (collision, animation, network) a raw memory write would otherwise have to reimplement.
**Chapter:** 03-input-and-locomotion.md
**Status:** SHARPENS Control-bind strings are vocabulary, not an API

### Recognize a freed-memory exception marker and quarantine by config, not by patching the call site
**What happened:** enabling a per-eye shadow-mask feature reproduced a repeatable `0xC0000409` fail-fast with a nested access violation at the classic freed-memory marker `0xDEDEDEDE`, during D3D11 texture/swapchain destruction. The response was immediate config-gate-off, keeping only non-mutating diagnostic code, and blocking re-enable until the resource's device/context/teardown ownership was independently redesigned.
**Why it generalises:** `0xDEDEDEDE`-class markers mean a resource was freed while something still held a pointer to it — almost always a lifetime/ownership bug in how a render resource is created, torn down, or shared across threads/devices, and rarely fixable by tweaking the failing call site. Config-gate off first, then redesign ownership deliberately.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS When a feature crashes the runtime, quarantine it — don't paper over it

### A system-wide runtime API layer can be genuinely incompatible with your stack even after being cleared once as the crash cause
**What happened:** a third-party Motion Compensation OpenXR API layer was first falsified as *the* crash cause (a run without it still crashed identically), then later found to be genuinely incompatible once other bugs were fixed. The fix set the layer's own disable-environment variable scoped to only the target process before `xrCreateInstance`, never editing global OpenXR registry state or unloading the layer system-wide.
**Why it generalises:** OpenXR, Vulkan, and DX12 all support third-party layers injected system-wide by the runtime, and "not currently the root cause" is not "compatible forever" — a layer can become newly incompatible as your own code changes. Scope any needed exclusion to your own process via the layer's documented disable mechanism.
**Chapter:** 09-d3d11-openxr-injection.md
**Status:** SHARPENS Architecture and loader compatibility

### Make double-injection and hung remote threads fail closed, not silently ambiguous
**What happened:** the injector was changed to refuse injection if the target already contains the mod's DLL, to require the remote `LoadLibraryW` thread to signal within a 30-second bound (previously unchecked, letting a stall masquerade as success), and to verify the module is actually loaded afterward. On timeout it deliberately does not free memory the still-running thread might read.
**Why it generalises:** two DLL versions loaded into one process, or an injection that "succeeded" but actually hung, are unrecoverable-in-place states that silently corrupt every later test session's evidence. Refuse-if-already-loaded, bounded-wait-with-explicit-failure, and post-injection verification are the minimum guard set for any injection-based mod, because a false "it worked" costs a whole debugging session.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS Attach versus launch injection — and one-time construction seams

### Preflight architecture/version/hash before the injector touches the process — a self-ID log line is too late
**What happened:** with several same-named historical build artifacts lying around for a 32-bit injected DLL, the injector was extended to run an x86/version/hash check before `CreateProcessW`/`OpenProcess` injection, rather than relying on the DLL's own self-identifying first log line, which only reports after the wrong binary is already loaded and possibly corrupting the session.
**Why it generalises:** a self-identifying log line is necessary but not sufficient — by the time it prints, a wrong-architecture or stale build has already been loaded into a live process. The precondition check belongs at the earliest common chokepoint every injection path (attach and launch) passes through, before the process is touched at all.
**Chapter:** 08-project-process.md
**Status:** SHARPENS Launch preconditions are part of test validity
