# SOMAVR — OpenGL / cross-project notes harvest

Files read: `HPL_OPENGL_NOTES.md` (64 lines), `UEVR_LEARNINGS.md` (57 lines), `BIOSHOCK_VR_TRANSFER_AUDIT.md` (298 lines), `VR_COMPATIBILITY_RE.md` (550 lines) — all read in full, start to end.

### Decouple frame-boundary work from diagnostic sampling intervals
**What happened:** SOMAVR's F8 diagnostic trigger was originally sampled on a periodic summary interval, so it fired once per 120 rendered frames instead of every frame. Rebinding the OpenXR frame boundary to fire on every real `gdi32!SwapBuffers` (reached via `SDL_GL_SwapBuffers` from HPL3's `cLowLevelGraphicsSDL::SwapBuffers`) and using `FrameSummaryInterval` only for log throttling fixed it.
**Why it generalises:** Any engine that logs "every Nth frame" tempts you to wire real per-frame work to that same throttle; the work and the throttle must be decoupled or the work silently only runs at 1/N rate.
**Chapter:** 10-graphics-apis.md
**Status:** SHARPENS "Frame boundary: SwapBuffers, not Present"
**API-specific:** OpenGL
**Evidence:** DEMONSTRATED

### A single camera-ownership gate at the frustum-read entry point beats enumerating secondary cameras
**What happened:** Ghidra-confirmed `cViewport` ownership at `0x140298630` let SOMAVR compare every camera-frustum request against the known live player camera; any different camera (reflection, terminal, water, shadow) now returns its native frustum immediately instead of being able to inherit HMD pose or consume the F10 stereo hotkey.
**Why it generalises:** Engines with more than one camera object per frame are the norm; one ownership check at the frustum-read entry is cheaper and more robust than excluding every secondary camera by name or context.
**Chapter:** 01-camera-and-tracking.md
**Status:** SHARPENS "The multiple-cameras problem (the #1 source of 'VR jank')"
**API-specific:** none
**Evidence:** DEMONSTRATED

### Fix a mismatched camera value at its native owner, not by patching the shader constant block
**What happened:** Live UBO diffing found the per-eye horizontal projection center at uniform-block offset 96 alternating `-0.242513/+0.242513` across eyes. Fixing it via the native HPL camera packet (not a shader-byte patch) changed the captured values to `0/0` and removed the eye-disagreement defect.
**Why it generalises:** Uniform/constant-buffer diffing is a powerful attribution tool for finding which packet owns a mismatch, but the fix belongs at the packet's native owner — a downstream shader-constant patch will keep fighting the next frame's native write.
**Chapter:** 09-d3d11-openxr-injection.md
**Status:** SHARPENS "Preserve render-view provenance"
**API-specific:** OpenGL
**Evidence:** DEMONSTRATED

### A shared "previous frame" temporal cache must be decompiled and split per eye, not assumed safe
**What happened:** Decompiling `0x1401f1480` showed the engine's "previous-view" history is a fixed `0x40`-byte copy from active frustum view `+0x158` into a history object `+0x80`, once per viewport call. Splitting that copy into per-eye banks stopped AFR from alternating shared history every game frame; pose gaps over eight frames are treated as camera cuts that reseed both banks.
**Why it generalises:** Any renderer with a "previous frame" cache for temporal effects (SSAO, TAA, motion blur) has exactly this hazard under AFR/dual-render — a shared cache updated once per game frame silently mixes left/right data unless the exact copy is decompiled and proven, then split.
**Chapter:** 14-render-pass-hazard-atlas.md
**Status:** SHARPENS "The temporal trap, in detail"
**API-specific:** none
**Evidence:** DEMONSTRATED

### An untimed xrWaitFrame after a session was ever focused, then goes unfocused, can hang the whole Present thread
**What happened:** A sibling OpenXR mod (BioShock VR) found `xrWaitFrame` has no timeout; a low-cadence keepalive that kept calling it while the session was VISIBLE-but-not-FOCUSED wedged the Present thread with no crash dump. The fix latches "ever focused," then skips `xrWaitFrame`/`xrBeginFrame`/`xrEndFrame` while unfocused, polling events only, until focus returns.
**Why it generalises:** This is a pure OpenXR session-state hazard independent of graphics API or engine; any injected OpenXR mod that free-runs its wait/begin/end triad off the session state machine can hang identically the moment the user pulls the headset off mid-session.
**Chapter:** 09-d3d11-openxr-injection.md
**Status:** SHARPENS "The OpenXR frame loop is an ownership contract"
**API-specific:** none
**Evidence:** DEMONSTRATED (field-proven in BioShock VR; scoped as a planned fix in SOMAVR, not yet built there)

### Cap in-process crash-dump generation and dedupe by fault address
**What happened:** BioShock VR's crash handler comments record an earlier unbounded fault handler that produced 2,083 minidumps totaling 115 GB from one failure mode. Its repair adds reentrancy protection, repeated-address suppression, and a hard 3-dump cap per session.
**Why it generalises:** An in-process exception filter installed for diagnostics is itself a fault-recursion risk; a bounded cap plus dedupe-by-address is cheap insurance that must be designed in up front, not retrofitted after an incident fills a disk.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Crash-dump workflow"
**API-specific:** none
**Evidence:** DEMONSTRATED (in source project)

### Layer a semantic anchor (name/literal) with a structural anchor (validated call-return address)
**What happened:** With no public HPL3 symbols, SOMAVR anchored on shader uniform names (`a_mtxModelViewProjection`, `a_mtxTemporalProjection`, `a_mtxInvViewProjection`) plus literal config values (`FOV=70`, `NearClipPlane=0.03`, `FarClipPlane=1000`) plus a call-stack anchor: matching prologues for `cCamera::GetFrustum` and `cFrustum::SetupPerspectiveProj`, accepting only calls returning to one confirmed render-viewport RVA.
**Why it generalises:** Combining a semantic anchor that survives recompiles with a structural anchor that validates the call site is far more version-robust than one byte signature, and needs only some string, constant, or uniform name to exist on the target.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "The anchor ladder — prefer higher rungs"
**API-specific:** none
**Evidence:** DEMONSTRATED

### A single legacy fixed-function call observed in a capture is a reliable signal of an OpenGL compatibility profile
**What happened:** The RenderDoc-reported unsupported call `glTexEnvfv(GL_TEXTURE_ENV, GL_TEXTURE_ENV_COLOR, &vColor[0])` is present in HPL2 source, confirming the game runs an OpenGL compatibility profile (fixed-function remnants alongside GLSL), not a core-only renderer.
**Why it generalises:** On OpenGL targets, one legacy/fixed-function call flagged by a capture tool is a cheap, reliable signal of which profile you're dealing with, and should set your renderer-probe assumptions (e.g. `glMatrixMode`/`glLoadMatrixf` paths may still be live) before investing in a core-profile-only hook plan.
**Chapter:** 10-graphics-apis.md
**Status:** NEW (subsection: detecting the OpenGL profile in play)
**API-specific:** OpenGL
**Evidence:** DEMONSTRATED

### Identify GLSL matrices with the three-hook combination: name, current program, and upload
**What happened:** SOMAVR tracks projection/view/world matrices with no symbols by combining `glGetUniformLocation` (maps program+location to the uniform's name string), `glUseProgram` (tracks the current program), and `glUniformMatrix4fv` (captures value and upload cadence).
**Why it generalises:** On any GLSL renderer the uniform name string is available at bind time even when nothing else is symbolized; this is the minimum hook set to answer "which matrix, on which program, updated when" — and it is a strictly OpenGL pattern, since D3D constant buffers carry no name at the API boundary.
**Chapter:** 10-graphics-apis.md
**Status:** SHARPENS "Reading the projection: hook the uniform upload"
**API-specific:** OpenGL
**Evidence:** DEMONSTRATED

### Depth-layer submission requires real format negotiation and unit conversion, with a per-frame fallback
**What happened:** SOMAVR's `XR_KHR_composition_layer_depth` path only negotiates depth-stencil when the live default framebuffer reports stencil bits (avoiding incompatible GL depth blits), allocates one `GL_DEPTH_COMPONENT24` texture per eye, blits with `GL_NEAREST`, and converts HPL near/far from world units to meters for `minDepth=0`/`maxDepth=1`. Any negotiation, cache, copy, or projection failure falls back to the proven color-only path for that frame.
**Why it generalises:** Depth-layer submission is never "just enable the extension" — concrete format negotiation, filter choice, and unit conversion are engine-specific, and a per-frame fallback is what keeps a depth experiment from breaking the proven color path.
**Chapter:** 10-graphics-apis.md
**Status:** SHARPENS "Depth submission differs in the details, not the intent"
**API-specific:** OpenGL
**Evidence:** DEMONSTRATED

### Nested-safe, non-blocking GL_TIMESTAMP queries are the only way to get real per-stage GPU cost without stalling
**What happened:** `HPLCompatibilityProbe` issues nested-safe start/end `GL_TIMESTAMP` queries around viewport, world, callback, post, post-post, and GUI stages, never blocks for results, and attributes each to the correct AFR eye at stage completion.
**Why it generalises:** A naive query-per-stage implementation either deadlocks on nesting or forces synchronization that defeats the measurement's own purpose; "nested-safe" and "never block" are the actual engineering content behind reading GPU cost cheaply.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Read a per-frame GPU value without paying for it"
**API-specific:** OpenGL
**Evidence:** DEMONSTRATED

### 64-bit RE addresses cluster at the default 64-bit linker image base, not the 32-bit convention
**What happened:** Every address cited across SOMAVR's own RE docs sits in the `0x1400xxxxx` range (viewport owner `0x140298630`, shutdown hook `0x1403b16e0`, pick-ray wrapper `0x1400cd750`) — the default 64-bit linker image base — versus the `~0x00400000`-and-up range typical of the corpus's other, 32-bit targets.
**Why it generalises:** This is a trivial but real gotcha the first time a team's tooling (scripts, signature databases, address-diffing) assumes a 32-bit-shaped address; RVA/module-base bookkeeping must be checked for 64-bit width, not just correctness, before reusing 32-bit-project tooling on a 64-bit target.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "Record the module base alongside every RVA"
**API-specific:** 64-bit
**Evidence:** DEMONSTRATED

### A 32-bit crash handler cannot be ported to x64 as-is — Windows exception handling diverges at the ABI level
**What happened:** The BioShock transfer audit explicitly scopes SOMAVR's crash-handler port as needing to become "x64-aware," treating BioShock's 32-bit `crash.cpp` (frame-based SEH) as a design reference rather than portable code.
**Why it generalises:** 64-bit Windows uses table-based structured exception handling instead of x86's frame-based scheme, so any crash-capture or vectored-handler code inherited from a 32-bit sibling project needs a real x64 rewrite, not a recompile.
**Chapter:** 06-debugging-methodology.md
**Status:** NEW (subsection: x64 crash handling differs from x86)
**API-specific:** 64-bit
**Evidence:** ASSERTED (stated as the audit's plan; not yet built or proven in SOMAVR)

### Key calibration profiles by live engine identity, and reapply the active one after any bulk reload
**What happened:** BioShock VR's `aim.cpp` resolves the exact live equipped-object identity, swaps in a cached calibration profile on identity change, and reapplies the active profile after any bulk preset reload so a generic baseline load can't silently overwrite an exact calibration — leaving the hot path at one identity comparison per frame. SOMAVR has scoped this as `FEATURE.ENTITY_CALIBRATION_PROFILES` but it only resolves/caches/persists so far and does not yet affect gameplay.
**Why it generalises:** Any mod juggling several distinct held/attached objects needs exactly this pattern — key by live engine identity, not by cached pointer or last interaction event, or hot-swap and reload ordering will desync calibration from the object actually on screen.
**Chapter:** 12-torso-calculations-and-ergonomics.md
**Status:** NEW
**API-specific:** none
**Evidence:** ASSERTED (BioShock VR source pattern; not yet implemented or proven in SOMAVR)
