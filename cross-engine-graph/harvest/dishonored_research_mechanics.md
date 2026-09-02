# DishonoredVR — research / mechanics / workflow harvest

Files read: 00-project-baseline.md (30/30), 01-feasibility-plan.md (54/54), 02-live-runtime-probe-2026-07-31.md (68/68), 03-test-build-smoke-2026-07-31.md (35/35), 05-camera-caller-sampling-plan.md (46/46), 06-camera-callers-live-2026-07-31.md (67/67), 07-visual-camera-probe-0.3.md (56/56), 09-vr-mechanic-risk-2026-08-03.md (240/240), 00-evidence-workflow.md (27/27), 01-test-harness.md (144/144), 00-module-boundaries.md (15/15). Also read playbook_toc.md in full.

### A single query function is usually many logical callers — classify by return address before writing to it
**What happened:** The player-view hook fires 5–10x/frame. A fixed 64-slot, allocation-free sampler recorded caller return addresses: an idle sample found exactly 5 unique callers at 1,303 hits each (5 distinct per-frame consumers, not one loop); a focused-gameplay sample found 10 unique callers (the original 5 plus 5 new ones at ~18,055–18,102 hits each), proving the engine doubles view queries during active simulation. Only return RVA `0x002C48AE` (inside `FUN_006c4710`) fed the actual render/projection path; the rest fed tick/distance logic (writes to global `0x01448C4C`), per-object effects, script wrappers, and volume/relevance tests. The write was gated to that one return address only.
**Why it generalises:** Any engine funnels render, AI, physics, and UI needs through one shared accessor (GetViewPoint/GetCamera/etc). Overwriting its output blindly corrupts every consumer; return-address sampling is a cheap, engine-agnostic way to find which caller actually feeds the screen.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Dynamic tracing finds the exact owner that static RE only approximates"
**Axis:** none
**Evidence:** DEMONSTRATED

### Keep the hot path atomic-only; defer symbolization and logging to a separate thread on demand
**What happened:** The camera-caller sampler performs only atomic memory operations inside the hook itself — no allocation, no symbolization, no file I/O. Symbolization and log dumps happen later on the bootstrap thread, only when a command (`camera callers off`) explicitly requests them. Across a 22,417-call continuous sample there was zero overflow and no observable gameplay hitch.
**Why it generalises:** The failure mode (allocating or logging inside a hook called thousands of times per second) is universal across engines and APIs. Deferring heavy work to a separate thread, triggered by an explicit command rather than every hit, is a directly reusable pattern for any hot-path instrumentation.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Hooking & native-call discipline"
**Axis:** none
**Evidence:** DEMONSTRATED

### Never compile a runtime pointer into a build constant until it survives two independent clean launches
**What happened:** The evidence workflow requires: "Add a build-scoped RVA/signature only after validating it twice across clean game launches." All runtime pointers are treated as session-only evidence — e.g. the dynamic-RHI global at the fixed RVA `+0x103EC78` held `0x11BCA800` in one session and `0x11B4A800` in another; the containing global's *address* is stable, but its *value* is not.
**Why it generalises:** Distinguishing a stable static offset from a transient runtime value is required for any RE-based mod, independent of engine or graphics API, to avoid baking a session-specific pointer into shipped code.
**Chapter:** 08-project-process.md
**Status:** SHARPENS "Mark every claim `VERIFIED` or `UNVERIFIED`, and say how"
**Axis:** none
**Evidence:** DEMONSTRATED

### An interposer may wrap one COM interface in an object graph while a sibling interface stays native
**What happened:** In the same RHI object, `RHI+0x4` (`IDirect3D9`) resolved to a Steam Overlay proxy vtable belonging to `gameoverlayrenderer.dll`, while `RHI+0x824` (`IDirect3DDevice9`) resolved to a genuine heap-allocated vtable at `0x2384EB7C`. One interface was overlaid; its sibling, reachable from the exact same object, was not.
**Why it generalises:** Any third-party interposer (overlay, anti-cheat, capture tool) may proxy one interface in a COM/vtable graph without touching adjacent interfaces reachable from the same object. Never assume overlay wrapping of one API pointer implies every related interface is wrapped — check each pointer's vtable module independently before picking a hook layer.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Know which modules are DRM, and exclude them early" (generalises to non-DRM interposers)
**Axis:** D3D9
**Evidence:** DEMONSTRATED

### Hook the engine's own forwarding wrapper, not the raw interface vtable slot it calls through
**What happened:** `Dishonored.exe+0x5C0180` is the engine's own Present-forwarding wrapper, calling through the RHI's device field to vtable offset `0x44`. A breakpoint on the live device's `Present` (`d3d9.dll+0xE05D0` in-session) returned to `Dishonored.exe+0x5C01A4`, proving the wrapper runs every frame, ahead of the overlay-proxied D3D call.
**Why it generalises:** Hooking the engine's own forwarding call — a static, signature-verifiable RVA — survives device/vtable recreation (resets, overlay reinit) because the vtable slot it calls through can be swapped underneath it, while the wrapper's own address does not move.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Installed at a verified-correct address and never fires = you hooked a wrapper" (the mirror case: sometimes the wrapper is the right target)
**Axis:** D3D9
**Evidence:** DEMONSTRATED

### D3D9-to-D3D11 GPU sharing requires a D3D9Ex device; plain D3D9 cannot share at all
**What happened:** A negative control proved a plain (non-Ex) D3D9 device cannot share resources under any configuration. Only after upgrading to a D3D9Ex device could a shared render target be created and opened via `OpenSharedResource` on the matching DXGI adapter (mismatched adapter LUID is a hard failure). Steady-state transfer cost measured ~0.2 ms median on an idle GPU, with enqueue/barrier/completed phases distinguished separately.
**Why it generalises:** Any D3D9-era engine bridging to a modern (D3D11/OpenXR) swapchain needs the Ex device variant specifically for GPU-side sharing; CPU readback is a fallback of last resort for the real-time path, not an option. Adapter-LUID matching generalises to any cross-API shared-resource bridge.
**Chapter:** 10-graphics-apis.md
**Status:** SHARPENS "D3D9 and D3D10: there is no OpenXR binding at all"
**Axis:** D3D9
**Evidence:** DEMONSTRATED

### Before hooking an arbitrary call site, check whether the engine already ships a sanctioned composition/extension point
**What happened:** UE3 registers `UCameraModifierexecModifyCamera`, `execUpdateAlpha`, `execIsDisabled`, `ACameraexecApplyCameraModifiers`, and `execUpdateCamera` — a built-in camera-modifier stack with alpha blending that is the engine's designed way to alter the final POV. This is flagged as a candidate superior to the return-address-gated write already proven at `+0x2C48AE`, partly because it may absorb cinematic/possession transitions for free.
**Why it generalises:** Many engines expose a first-class camera-composition layer distinct from the raw view-query accessor. Checking for a designed extension point before committing to an ad hoc call-site hook composes better with the engine's own authority and transition logic.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "If the engine has its own stereo path, use it" (generalised beyond stereo to any sanctioned composition point)
**Axis:** UE3
**Evidence:** ASSERTED (nominated, not yet measured against the existing gate)

### Query the engine's own "input/camera ignored" flags to arbitrate camera authority, rather than inferring it
**What happened:** `ADishonoredPlayerControllerexecSetCinematicMode_Native`/`PreSetCinematicMode_Native`, `IsLookInputIgnored`, and `IsMoveInputIgnored` are all registered natives — the engine already signals when it has seized the camera (assassinations, fatalities, knockdowns, mantling, death, possession, keyholes, Matinee). The plan is an explicit camera-authority state machine keyed off these signals instead of an unconditional head-pose write.
**Why it generalises:** Most engines expose some cinematic/input-ignored flag surface for exactly this purpose; querying it directly is more robust than inferring camera ownership by diffing state.
**Chapter:** 01-camera-and-tracking.md
**Status:** SHARPENS "Yield to the engine's authored cameras (cutscenes, ladders, conversations, seats)"
**Axis:** UE3
**Evidence:** ASSERTED (natives confirmed compiled-in; arbiter not yet built)

### Make the VR tracking-origin anchor re-anchorable from day one — possession/body-swap will otherwise force a rewrite
**What happened:** `DisPossessionProxyPawn` and `AControllerexecPossess`/`execUnPossess` prove the controller can re-parent to an entirely different pawn (e.g. a rat), instantly changing eye height, movement model, collision, and animation source by roughly a 1.5 m vertical shift. The recommendation is to bind the tracking origin to "whatever pawn is currently possessed," configurable from the start, rather than hard-coding it to the original player pawn.
**Why it generalises:** Any game with possession, vehicle entry, or body-swap mechanics hits the same problem — an origin hard-coded to one actor must be rewritten, not reconfigured, once control reparents. Treat the origin binding as a swappable reference from the outset.
**Chapter:** 01-camera-and-tracking.md
**Status:** NEW
**Axis:** UE3
**Evidence:** ASSERTED (risk analysis; not yet implemented)

### Forced camera rotation is the worst comfort offender — worse than forced translation — and needs per-mechanism triage, not one blanket policy
**What happened:** Camera-seizing animations (assassination, fatality, knockdown, strong-hit-reaction, mantle, Matinee) both move and rotate the camera along an authored path, ranked as the single most urgent comfort item because it fights head-pose injection immediately. Mitigations differ per mechanism: keep game camera position and let HMD orientation add on top within a clamp for assassinations (where the animation is the point); disable outright via `PlayerDisableKnockdown`/`PlayerDisableStrongHitReaction` where there's no player value; comfort vignette (not removal) for mantling, which is core traversal; orientation-only for Matinee.
**Why it generalises:** The rotation-worse-than-translation severity ordering, and triaging each camera-seizing system by "is the animation the point" rather than one blanket policy, both transfer to any first-person game with canned kill-cams, takedowns, or scripted traversal.
**Chapter:** 01-camera-and-tracking.md
**Status:** SHARPENS "Comfort is its own engineering surface"
**Axis:** none
**Evidence:** ASSERTED

### A "teleport" ability may be a smoothed camera blend, not an instant cut — verify the blend target before trusting it as comfort locomotion
**What happened:** A node literally named `BlinkBlender` exists for Dishonored's Blink power, indicating the transition may be blended rather than an instant cut — which would make canonical "point-and-teleport" comfort locomotion into a nausea source instead. Whether the blend drives the camera or only the arm animation is flagged as the single cheapest, highest-value live check before shipping Blink as VR locomotion.
**Why it generalises:** Any flat-game teleport/dash ability inherited from non-VR development may be a smoothed camera interpolation under the hood for visual polish. A name suggesting instant travel is not proof of an instant camera cut; always check for a blend/interpolation node on the camera specifically.
**Chapter:** 01-camera-and-tracking.md
**Status:** SHARPENS "Turning (snap & smooth) without nausea" (extends instant-vs-smoothed from turning to teleport)
**Axis:** UE3
**Evidence:** ASSERTED (hypothesis flagged for live validation, not yet confirmed)

### Search for the engine's own debug/cheat toggles for VR-hostile subsystems before reverse-engineering a patch — but verify reachability separately from presence
**What happened:** `UDishonoredCheatManager` registers 259 exec natives in this build, including ready-made mitigations for nearly every comfort risk found: `PlayerDisableAssassinate`, `PlayerDisableKnockdown`, `PlayerDisableStrongHitReaction`, `PlayerDisableMeleeAssist`, `PlayerForceFastFinishers`, `PlayerArmsToggle`, `SetCameraBob_Native`, and `UpdateEyeHeight` (crouch/landing eye-height interpolation — camera translation the player didn't initiate). Two caveats: presence in the binary doesn't prove `UCheatManager` is instantiated in a shipping build (must be confirmed live), and reaching them must go through the validated controller at runtime, never by editing the game's ini files.
**Why it generalises:** Shipped games routinely retain debug/cheat toggles for exactly the subsystems that hurt VR comfort (camera bob, forced eye-height, canned camera moves); searching for them is cheaper than reversing a patch — but "compiled in" must still be verified "reachable at runtime" separately.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "The engine's own debug commands are a validation oracle"
**Axis:** UE3
**Evidence:** ASSERTED (existence demonstrated statically; reachability and use as mitigation unverified)
