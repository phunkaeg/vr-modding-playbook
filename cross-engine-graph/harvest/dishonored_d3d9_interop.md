# DishonoredVR — D3D9 / interop harvest
Files read: 08-d3d9-d3d11-interop-2026-08-01.md (160/160), 2026-08-03-interop-lane.md (221/221), 2026-08-07-probe-hardening.md (154/154), 04-openxr-preflight-2026-07-31.md (41/41)

### A GPU benchmark must wait for completion, not submission, before it is trusted
**What happened:** The interop probe's original `Total` timing stopped after `CopyResource` + `Flush` — CPU submission, not proven GPU work. The 2026-08-07 hardening pass added a `D3D11_QUERY_EVENT` after the copy and polled `GetData` until it reported complete, splitting the number into `completed` (0.224 ms median, 0.291–0.397 ms p95 across two runs) versus `enqueue` (0.196 ms p95). The two diverge, and only `completed` is real.
**Why it generalises:** Any cross-API or cross-thread GPU transport benchmark that ends its timer at a submission call (`Flush`, `Present`, command-buffer-submit) is measuring driver queuing, not execution. This applies identically in Vulkan (fences), D3D12 (fences), or OpenGL (sync objects) — the fix is always "insert a completion primitive, wait on it, then stop the clock."
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Measure, don't theorize: the readback probe" / "Read a per-frame GPU value without paying for it"
**Axis:** none
**Evidence:** DEMONSTRATED

### A plain (non-Ex) D3D9 device cannot create shared resources at all — proven by negative control
**What happened:** `Direct3DCreate9` — the call Dishonored itself makes — refused `CreateTexture` with `D3DUSAGE_RENDERTARGET | D3DPOOL_DEFAULT` shared-handle request with `0x8876086C` (`D3DERR_INVALIDCALL`). Only a `Direct3DCreate9Ex` device could create the shared `D3DFMT_A8R8G8B8` target that `ID3D11Device::OpenSharedResource` then opened successfully. D3D11 was verified to observe the D3D9 writes using two distinct fill colours, ruling out a stale/zeroed mapping.
**Why it generalises:** This is the second independent project (after the existing single-project D3D9 witness) confirming the same mechanism: any D3D9 title bridging to a modern API must have its device creation hooked and upgraded to the Ex variant before zero-copy sharing is possible — this is a hard API constraint with a recorded error code, not a convention.
**Chapter:** 10-graphics-apis.md
**Status:** SHARPENS "D3D9 and D3D10: there is no OpenXR binding at all"
**Axis:** D3D9
**Evidence:** DEMONSTRATED

### D3D9Ex shared surfaces have no keyed mutex, so the only barrier drains the entire GPU queue
**What happened:** D3D9Ex shared surfaces expose no keyed-mutex synchronization; the only available producer/consumer barrier is an `IDirect3DQuery9` event query, which blocks until *all* outstanding GPU work completes, not just the copy. Measured barrier cost (0.164–0.189 ms median, up to 0.78 ms p95) dominated the total and stayed flat when surface area more than doubled (1920x1080 to 2064x2096) — the cost is the wait, not the blit.
**Why it generalises:** Second D3D9 witness on a cross-API sharing mechanism most engineers assume behaves like a modern fence. Inside a real game the same event query must drain a full rendered frame, not an idle GPU — so idle-GPU screening numbers are a floor, and any team budgeting a D3D9-origin transport must plan for a whole-frame-drain stall, not a per-resource one.
**Chapter:** 10-graphics-apis.md
**Status:** SHARPENS "D3D9 and D3D10: there is no OpenXR binding at all"
**Axis:** D3D9
**Evidence:** DEMONSTRATED

### GPU adapter LUIDs are per-boot handles, not stable machine identifiers — never persist one
**What happened:** The same physical RTX 5070 Ti reported D3D9Ex adapter LUID `00000000-0001667A` on 2026-08-01 and `00000000-00016A92` on 2026-08-07 — a different value after a reboot/driver restart, same hardware. Passing a stale LUID into the adapter-match check produces a hard mismatch failure on a single-GPU machine that reads exactly like a real adapter problem.
**Why it generalises:** Any Windows graphics-interop or multi-API-device-matching code (D3D9/D3D11/D3D12/DXGI/OpenXR) that compares adapters by LUID must re-read both values within the same boot session — LUIDs must never be hardcoded, cached across runs, or copied out of a document into config.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "Record the module base alongside every RVA" (same class of ephemeral-value hazard, applied to a Windows OS handle rather than a process address)
**Axis:** D3D9
**Evidence:** DEMONSTRATED

### A shared-texture format may cross API boundaries with no conversion — verify, don't assume
**What happened:** All four candidate D3D9 formats were shareable; `D3DFMT_A8R8G8B8` opened on the D3D11 side as `DXGI_FORMAT_B8G8R8A8_UNORM`, which was already one of the formats the OpenXR runtime accepted for its swapchain. No format-negotiation layer was needed anywhere in the D3D9→D3D11→OpenXR chain.
**Why it generalises:** Teams often assume a format-conversion or copy-with-reinterpret step is required whenever a resource crosses an API boundary. This is a case where it wasn't — but the lesson is procedural: probe the actual format mapping and downstream acceptance before designing a conversion path, since a working shortcut here removes an entire subsystem.
**Chapter:** 10-graphics-apis.md
**Status:** SHARPENS "D3D9 and D3D10: there is no OpenXR binding at all" / "Depth submission differs in the details, not the intent"
**Axis:** D3D9
**Evidence:** DEMONSTRATED

### In UE3, the engine's own camera-modifier stack is the sanctioned VR injection point, not a raw camera-write hook
**What happened:** A `_ReturnAddress()`-gated hook that overwrites camera state unconditionally is well-evidenced but fights every authored camera seizure UE3 exposes as native functions: `SetCinematicMode_Native`, `PreSetCinematicMode_Native`, `IsLookInputIgnored`, `IsMoveInputIgnored`. `UCameraModifier::ModifyCamera` (plus `execUpdateAlpha`, `execIsDisabled`, `ACameraexecApplyCameraModifiers`) is UE3's built-in mechanism for altering the final POV with a blend alpha already wired in — flagged as the better candidate but not yet measured against the existing gate.
**Why it generalises:** Confirms the playbook's "yield to the engine's authored cameras" rule with a concrete UE3 mechanism and native-function names: engines expose a sanctioned camera-modification seam with built-in blending; a return-address hook is a diagnostic, not the shipping architecture.
**Chapter:** 01-camera-and-tracking.md
**Status:** SHARPENS "Yield to the engine's authored cameras"
**Axis:** UE3
**Evidence:** ASSERTED (identified as the better injection point; not yet implemented or measured against the existing gate)

### UE3 rotators are additive 16-bit integers — naive Euler addition breaks under combined HMD rotation
**What happened:** The camera-offset code does `pitch += / yaw += / roll +=` against the game's rotator, correct only for the planned yaw-only test (`1024` units) and missing an `& 0xFFFF` normalization, so `game_yaw + offset` can leave UE3's 16-bit rotator range. Combined pitch/yaw/roll from a real headset will not compose correctly under simple addition.
**Why it generalises:** A specific, concrete instance of the general "Euler/quaternion traps" class, with UE3's exact representation named: rotators are fixed-width integer angle units, not floats, and per-axis addition is not rotation composition — the fix path is proper rotation composition plus explicit range wrapping, not just switching representations.
**Chapter:** 02-viewmodels-and-hands.md
**Status:** SHARPENS "Euler/quaternion traps (the recurring math failures)"
**Axis:** UE3
**Evidence:** DEMONSTRATED (found by code review of `visual_camera.cpp:79`)

### A lock-free multi-field handoff needs a sequence counter, not just an enable/disable flag, to avoid torn reads
**What happened:** The original camera-offset handoff used `exchange(false)` → write six atomics → re-enable, which could expose a reader to a torn mix of two different command generations. The fix added a sequence counter that readers check and retry on, validated with a stress test of 200,000 alternating writes against concurrent snapshots with zero mixed-generation reads observed in Debug and Release.
**Why it generalises:** Any engine integration passing a multi-field pose/state update across a game-thread/render-thread (or hook/consumer) boundary without a full mutex needs the same seqlock-style pattern — a boolean gate around several independent atomics is not sufficient, and the fix is verifiable only by an adversarial concurrent stress test, not code review alone.
**Chapter:** 07-engine-integration-safety.md
**Status:** NEW
**Axis:** none
**Evidence:** DEMONSTRATED

### D3D9Ex forbids D3DPOOL_MANAGED outright — audit a legacy renderer before upgrading its device
**What happened:** D3D9Ex disallows `D3DPOOL_MANAGED` allocations entirely and changes device-lost/reset semantics. UE3's `D3D9Drv` has not yet been checked for managed-pool allocations or reset-path assumptions; this was flagged as "now the largest open risk in the rendering path" and the next required step is a static, offline search of the target build before any live device swap is attempted.
**Why it generalises:** Any mod upgrading a legacy D3D9 title's device to Ex-mode to enable resource sharing (a near-mandatory step per the negative-control finding above) inherits this exact constraint — it is a general D3D9-to-D3D9Ex migration hazard, not an engine quirk, and it is cheap to check statically before touching the live device.
**Chapter:** 07-engine-integration-safety.md
**Status:** NEW
**Axis:** D3D9
**Evidence:** ASSERTED (identified as the next required check; not yet performed)

### A shipping cross-API bridge needs a synchronized ring of shared surfaces, not one serialized buffer
**What happened:** The probe deliberately stays single-buffered; the completion query makes that configuration correct and measurable for screening, but the handover explicitly states a shipping bridge must use a ring of shared textures with per-slot completion tracking so D3D9, D3D11, and OpenXR work can overlap instead of serializing every frame.
**Why it generalises:** A general architecture lesson for any legacy-API-to-modern-API frame bridge: a single shared resource forces full serialization (producer must wait for consumer before reusing the surface), which caps throughput regardless of how cheap the copy itself is — the fix (N-buffered ring with per-slot fences/queries) is API-agnostic.
**Chapter:** 09-d3d11-openxr-injection.md
**Status:** NEW
**Axis:** D3D9
**Evidence:** ASSERTED (stated as the required shipping design; not yet implemented or measured)

### The Steam Overlay may already be proxying the exact interface your device-creation hook targets
**What happened:** A prior probe found the Steam Overlay proxying `IDirect3D9` in this process. The device-creation hook needed to upgrade Dishonored to D3D9Ex has to coexist with that pre-existing proxy layer; this interaction is explicitly listed as untested by the interop spike.
**Why it generalises:** Overlay/anti-cheat/capture software commonly wraps the exact low-level creation entry points (`Direct3DCreate9`, `DXGIFactory::CreateSwapChain`, etc.) that a VR mod also needs to hook — a hook that appears "installed at a verified address" can still be calling into another party's wrapper rather than the driver, which changes what upgrading the device actually does.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "'Installed at a verified-correct address and never fires' = you hooked a wrapper"
**Axis:** D3D9
**Evidence:** ASSERTED (proxy presence demonstrated in an earlier probe; the coexistence-with-upgrade-hook scenario itself is untested)
