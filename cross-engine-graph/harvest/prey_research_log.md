# PreyVR — research log / registries harvest
Engine and API: CryEngine-derived (Arkane's modified CryEngine), Prey (2017), 64-bit `Prey.exe` / `PreyDll.dll`, renderer Direct3D 11 via DXGI. Confirmed by `D:\Dev Debug\PreyVR\CLAUDE.md` ("Prey 2017, CryEngine-derived, 64-bit -> use x64dbg", "Prey renders via Direct3D 11") and corroborated throughout `RESEARCH_LOG.md` (DXGI/D3D11 device creation, `EndRendererScene`/`BeginRendererScene`, `ArkPlayerCamera`, `CArkWeapon` — the `Ark*` prefix is Arkane's engine layer over CryEngine).
Files read: RESEARCH_LOG.md (all 191 lines, in four passes: 1-50, 51-100, 101-150, 151-191); ADDRESS_REGISTRY.md (all 36 lines); FAILURE_REGISTRY.md (all 26 lines); HYPOTHESES.md (all 14 lines); playbook_toc.md (all 211 lines, read first for dedup).

### Never attach a temporary/interactive hook to a frame-frequency function
**What happened:** A Frida `CModule` callback attached in-process to `IDXGISwapChain::Present` while the interactive execution thread waited. `Prey.exe` crashed with `0xC0000005` in an unknown/freed-code region (`StackHash_1030`). Root cause is inferred (callback/listener lifetime went invalid while the interactive session was blocked or torn down), not symbolized. F-001's rule: use an externally-owned persistent tracer or a non-breaking logging hardware breakpoint instead, never a temporary CModule/Promise-based hook, for anything called every frame.
**Why it generalises:** Any RE toolchain that pairs an interactive scripting session with a hot-path hook (any engine's Present/frame-boundary equivalent) risks the same lifetime race — the hook outlives or races the harness that installed it. The fix (externally-owned persistent tracer, non-breaking breakpoint) is toolchain-agnostic.
**Chapter:** 07-engine-integration-safety.md ("Hooking & native-call discipline")
**Status:** SHARPENS Hooking & native-call discipline
**Evidence:** DEMONSTRATED (crash reproduced, dump captured, recovery clean)

### Scope a live-write experiment to the most transient copy of the value, not the persistent field
**What happened:** To prove controller-owned aim could steer native melee/interaction without touching the camera, the project didn't write ArkPlayer's persistent cached ray. It found the exact stack offset where the callee (`ArkWrenchComponent::GetHits`, `ArkPlayerTargetSelector::UpdateCandidates`) copies the ray onto its own stack frame — twelve bytes at `[RSP+0x64..0x6F]` and `[RSP+0x5C..0x67]` respectively — and mutated only that copy. The write expired with the stack frame; persistent state, camera, UI reticle, heap, and code were never touched, yet the mutation still produced a measured downstream effect (contact point moved `0.127165` units; selected entity changed from `0xFDE0` to `0x1117`).
**Why it generalises:** Any live-injection proof needs a controlled variable. Targeting the ABI-boundary stack copy of a value — rather than the object field it was read from — gives you causal proof with a blast radius that self-heals on return, which is safer and easier to justify than a persistent-memory patch on any engine.
**Chapter:** 06-debugging-methodology.md ("Measure, don't theorize: the readback probe")
**Status:** SHARPENS Measure, don't theorize: the readback probe
**Evidence:** DEMONSTRATED (two independent passes: wrench A0b, interaction A0)

### An overlay tool's relative-offset semantics can silently invert your data — diff every field against ground-truth arithmetic
**What happened:** ReGenny's `.genny` field syntax `+N` is a delta from the *previous field's end*, not an absolute offset from the struct base — contrary to the tool's own example doc. A struct written with absolute-offset assumptions silently resolved `swapchain` to `+0xAE90` instead of the correct `+0xAE88`, and `swapchain_mirror` drifted to `+0x36C58`. A camera-position overlay read returned `(-1635.07, -7952.76, 6753.18)` where direct pointer arithmetic at the true offset returned `(783.58, 1573.48, 17.10)` — a plausible-looking but entirely wrong vector. The defect existed from the struct's creation and went unnoticed because every prior finding had come from x64dbg/CE/explicit address math, so no overlay read was ever diffed against ground truth.
**Why it generalises:** Any struct-overlay/pretty-printer tool (ReGenny, ReClass, Cheat Engine's structure dissector) can have surprising accumulation semantics. A wrong overlay is worse than no overlay because it looks plausible. The rule — never trust an overlay value until it's diffed field-by-field against a direct read at the same absolute address — applies to any RE toolchain with a symbolic struct layer.
**Chapter:** 06-debugging-methodology.md ("Tooling lies in specific, learnable ways")
**Status:** SHARPENS Tooling lies in specific, learnable ways
**Evidence:** DEMONSTRATED (21 of 21 fields re-verified after fix)

### Fingerprint an unknown COM/interface object by counting vtable entries, not by its position in the search
**What happened:** The leading candidate for the CryEngine `CRenderView` (a per-eye render-view structure) was a 2-entry ring at renderer `+0xAC30`. Live inspection showed both entries share one `d3d11.dll` vtable with exactly 11 contiguous entries — matching `ID3D11Query`'s shape, not `ID3D11DeviceContext`'s (~145 entries). This closed the candidate as GPU timing queries (recorded as R-027), redirecting the search to the real view block, later found by scanning for an orthonormal 3x3 rotation followed by a plausible world position.
**Why it generalises:** Without RTTI (common when a studio strips it, as Arkane did here), vtable entry count is a cheap, engine-agnostic discriminator between candidate COM/virtual-dispatch object types — a lightweight structural fingerprint usable before any deeper decompilation.
**Chapter:** 11-re-anchoring-and-discovery.md ("Classify an unknown value by its magnitude, not its declared type")
**Status:** SHARPENS Classify an unknown value by its magnitude, not its declared type
**Evidence:** DEMONSTRATED

### A stereo eye pair must differ by a constant lateral offset in every state; if two candidates are byte-identical while stationary, they are double-buffers
**What happened:** Two camera-shaped slots existed at renderer `+0x4A08` (stride `0x328`, indexed by `+0x499C`). While the player stood still, the two slots were byte-identical (separation `0.00000`) — but a real per-eye pair must retain a constant IPD offset even when stationary. That single test proved the slots were frame double-buffers, not a resident stereo pair, closing H-001's structural half. Live motion further confirmed liveness: position moved `0.67244` units over 100 frames with visible head-bob in Z.
**Why it generalises:** This is a cheap, engine-agnostic discriminator for any "is this a stereo/multi-view structure or just double-buffering" question: freeze the process and compare the candidates — a real eye pair never converges to identical values, a double-buffer always can.
**Chapter:** 11-re-anchoring-and-discovery.md ("Differential state scanning: capture the same process in known states")
**Status:** SHARPENS Differential state scanning
**Evidence:** DEMONSTRATED

### Don't trust string-table search alone to prove a negative — reconcile it against an exhaustive byte search
**What happened:** Proving "this engine build has no retained stereo path" required two independent passes. `search_strings` initially found only 4 `Stereo`-bearing literals (during a mid-analysis-pass state, later corrected), while raw byte-pattern search over the full 48MB image found the true total of 10 (`Stereo` x7, `stereo` x3). After Ghidra's analysis pass completed, `search_strings` returned exactly 8, which reconciled 1:1 with the byte-search total once two hits inside already-known Flow Graph node names were accounted for. Only after two independent methods agreed was the negative (H-001, no `r_Stereo*` cvars, no `IHmdDevice`, no CryVR plugin) treated as corroborated rather than resting on one method.
**Why it generalises:** Defined-string tables in any binary can be partial (mid-analysis, stripped, or never promoted from raw data), so a single search tool returning zero hits is not proof of absence on any engine. A second, structurally different search method reconciling to the same count is what makes a negative claim trustworthy.
**Chapter:** 11-re-anchoring-and-discovery.md ("Never rely on a single discovery method")
**Status:** SHARPENS Never rely on a single discovery method
**Evidence:** DEMONSTRATED

### A camera storing its frustum as four independent edges (not one FOV scalar) gives you free asymmetric per-eye projection
**What happened:** The live render-view block (renderer `+0x4A08+0x270`) stores frustum edges L/R/B/T as four independent floats rather than a single FOV+aspect pair, verified internally consistent (`R/T = 1.77778` matches the block's own aspect field). OpenXR requires per-eye asymmetric projection where `L != -R`; because this engine already represents the frustum as four edges, asymmetric per-eye frusta are directly representable without restructuring the camera at all.
**Why it generalises:** Whether a legacy engine's projection representation is symmetric-FOV-only or already edge-based determines how much projection-math work a VR port needs before it can even attempt correct per-eye rendering — worth checking on any target engine before assuming you must rebuild the projection pipeline.
**Chapter:** 09-d3d11-openxr-injection.md ("FoV, aspect, and full-eye presentation")
**Status:** SHARPENS FoV, aspect, and full-eye presentation
**Evidence:** DEMONSTRATED

### One native camera-independent aim ray, reused by unrelated gameplay systems, is worth finding before building a parallel aim simulation
**What happened:** `IArkPlayer::GetReticleViewPositionAndDir` (backed by `ArkPlayer::UpdateCachedReticleViewPosAndDir`, RVA `0x1585320`) turned out to be consumed independently by melee (`ArkWrenchComponent::GetHits`, RVA `0x13BD620`), firearm targeting (`CArkWeapon::GetReticleInfoForFiring`/`FindIronsightsTarget`), and world-interaction selection (`ArkPlayerTargetSelector::UpdateCandidates`, RVA `0x159A660`) — three unrelated gameplay systems sharing one camera-independent ray producer. This closed the exact feasibility gate (H-004) that blocked an earlier public VR prototype for this game, which reportedly could not decouple aim from the head camera.
**Why it generalises:** Corroborates, with a fourth engine's evidence, that engines commonly already separate "where the camera looks" from "what gameplay logic aims at" for controller/gamepad support — and that ray producer is usually reused across melee/ranged/interaction rather than reimplemented per system, so finding and steering it beats building a parallel aim simulation.
**Chapter:** 01-camera-and-tracking.md ("Camera view is not aim ownership")
**Status:** SHARPENS Camera view is not aim ownership
**Evidence:** DEMONSTRATED (live A0/A0b write-and-readback on both melee and interaction paths)

### A dynamically-loaded D3D11/DXGI dependency leaves no import-table trace — find it by its embedded loader-name string cluster instead
**What happened:** `PreyDll.dll` has no direct `D3D11CreateDevice` or DXGI entry in its import table. The dependency was found instead as a contiguous ASCII cluster in `.rdata` at `PreyDll.dll+0x1D93408`: `CreateDXGIFactory1`, `dxgi.dll`, `D3D11CreateDevice`, `d3d11.dll` — the literal names a runtime `LoadLibrary`/`GetProcAddress` loader would need. Once the analysis pass was complete, xrefs to `CreateDXGIFactory1` resolved to exactly two code locations, one of which (`FUN_180F50000`) decompiled as the real device/adapter/swapchain creator.
**Why it generalises:** Any engine that dynamically loads its graphics API (rather than linking it) will be invisible to import-table inspection; the embedded GetProcAddress-name string cluster and its xrefs are the correct discovery path on any such binary, D3D or otherwise.
**Chapter:** 11-re-anchoring-and-discovery.md ("Signature-scan the data, not just the code")
**Status:** SHARPENS Signature-scan the data, not just the code
**Evidence:** DEMONSTRATED

### Device creation may branch through vendor-extension paths before ever calling the plain SDK entry point
**What happened:** `InitializeD3D11DeviceAndSwapChain` (RVA `0xF50000`) creates the D3D11 device through one of two vendor-extension paths (`FUN_180F621A0`/`FUN_180F623B0`, selected by a runtime object flag at `[0x58]`) or, only otherwise, plain `D3D11CreateDevice` at feature level `0xB000`. All three paths converge on the same adapter selected by an `EnumAdapters1` loop.
**Why it generalises:** A hook or an `XR_KHR_D3D11_enable` adapter-agreement check that only watches the plain SDK device-creation call can miss vendor-extension creation paths (NVAPI/AMD AGS-style) that some engines take by default — worth checking for on any D3D11/D3D12 target before assuming a single creation call site.
**Chapter:** 09-d3d11-openxr-injection.md ("Architecture and loader compatibility")
**Status:** SHARPENS Architecture and loader compatibility
**Evidence:** DEMONSTRATED (static decompilation; not yet live-traced through a vendor-extension branch)

### Version the gate's identity in lockstep with what it verifies, not just its landmark count
**What happened:** A signature-gate artifact grew from 21 to 22 fail-closed landmarks but kept the same lifecycle version string as the prior 21-landmark live-proved build, "making it too easy to transfer evidence between different binaries." The project's own self-correction bumped the artifact to a distinct version (`0.3.0-lifecycle-hardening`) that logs its own SHA-256 and compiled landmark count and is explicitly marked live-validation-pending, rather than inheriting the older build's proved status.
**Why it generalises:** A landmark/signature count alone is not a safe version identity — two different landmark sets can produce the same count, or a version string can outlive the set it originally described, letting stale "verified" status leak onto unverified binaries. Any fail-closed gate on any engine needs its version bumped whenever its verification set changes, independent of the count.
**Chapter:** 06-debugging-methodology.md ("Make every build self-identify (do this on day one)")
**Status:** SHARPENS Make every build self-identify
**Evidence:** DEMONSTRATED (self-correction recorded in the log)

### Keep one compiled source of truth for a growing signature/landmark list — duplicated copies drift
**What happened:** The project had maintained a duplicate PowerShell list of the same 22 fail-closed signatures used by the compiled C++ engine map. It was removed; both the build manifest and the build doctor now obtain their landmark count from the single compiled `engine::ValidateLandmarks` map instead of a parallel script-side copy.
**Why it generalises:** As an RE project's landmark/signature registry grows (here to 22+ entries across renderer, camera, weapon, and interaction subsystems), any second hand-maintained copy of that list — in a build script, a doc, or a test — will eventually drift from the source of truth silently. This is a general project-hygiene lesson independent of engine.
**Chapter:** 08-project-process.md ("Test-artifact config files silently outrank your code defaults")
**Status:** SHARPENS Test-artifact config files silently outrank your code defaults
**Evidence:** DEMONSTRATED
