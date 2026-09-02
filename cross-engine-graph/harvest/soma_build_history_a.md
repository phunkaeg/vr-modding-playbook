# SOMAVR — BUILD_HISTORY harvest (lines 1-1400)
Lines read: 1-1400

### Never let a value you wrote into engine-owned state be read back as fresh native input
**What happened:** The same feedback-loop bug recurred three times under different names. In 0.65.1 a cached "first transition frame" forced later entrance matrices onto a wrong distant arc and had to be reverted. In 0.68.2, native Notepad distance grew `0.4272 -> 1.4772` because each frame's current (already-modified) matrix was multiplied again. In 0.85.0 `Notepad_open` entered at distance `0.4586`, then the mod observed its own previously-submitted `0.8842` and `1.4697` outputs as if they were new native input and scaled them again. Each fix required latching one immutable source value per object/session instead of reusing the live, mod-modified transform as next frame's input.
**Why it generalises:** Any hook that both writes a transform/value and later reads "the current value" for the next update is at risk of closing a loop with itself — the fix is always to snapshot the pristine source once and derive from that snapshot, never from your own last output.
**Chapter:** 07-engine-integration-safety.md
**Status:** NEW
**API-specific:** none

### A shared, once-per-frame mutable state packet gets double-advanced by same-frame stereo unless you frame and restore it per eye
**What happened:** HPL3's deferred SSAO (`0x1403f2b50`/`0x1405...`) advanced a global float `0x14079575c` once per invocation and derived its temporal blur phase (uniform slot 7) from it; rendering both eyes in one frame silently gave eye two a different noise phase. Tone mapping's `0x140284fd0` (via `0x1402842d0`) likewise advanced exposure, white-cut, fade, color-grading, and film-grain phase (fields `+0x8c..+0x158`) once per call. The fix pattern was identical both times: capture the pre-update packet and committed result before eye one, replay the same baseline for eye two, then restore eye one's committed result so exactly one logical update persists per frame. The SSAO history itself was additionally duplicated per-eye on the GPU with `glCopyImageSubData`.
**Why it generalises:** Post-effects frequently keep one mutable "this frame" packet rather than being pure functions of input; rendering N views per frame turns any such effect into a hazard unless each eye either shares one physical advance or gets its own isolated copy.
**Chapter:** 14-render-pass-hazard-atlas.md
**Status:** SHARPENS "The temporal trap, in detail" / "There is no canonical G-buffer"
**API-specific:** OpenGL

### A single missing REX prefix silently shifts every RIP-relative offset your signature scan depends on
**What happened:** A byte-signature scan expected the raycast entry to start `57 48 83 ec 60`; the installed binary actually began `40 57 48 83 ec 60` — one extra REX prefix byte. That single byte shifted the RIP-relative displacement location from `+8/+12` to the correct `+9/+13`, breaking both the "outer" and "inner" hooks simultaneously in a way that looked like two unrelated failures. The fix split outer/inner diagnostics to report actual-vs-expected byte prefixes and RVA, and added a compile-time-tied doctor check that explicitly rejects the old missing-prefix signature.
**Why it generalises:** REX prefixes (40-4F) are optional/compiler-dependent in x86-64 encoding, so two builds of "the same" function can differ by exactly one leading byte while everything after it reads as plausible code — a signature scan must anchor on the true prefix, not assume a fixed instruction start.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "Prologue scans lie in four specific ways"
**API-specific:** 64-bit

### Validate a reverse-engineered struct field by numeric plausibility, not by its position in your guess
**What happened:** A native "closest entity" result struct was originally misread, treating a pointer's raw bits as a floating-point distance. Live evidence corrected the layout to distance at `+0x18`, physics body pointer at `+0x20`, and Lux entity pointer at `+0x28` — reticle depth, semantic focus, and selected-body identity all worked immediately once the actual fields were consumed instead of the guessed ones.
**Why it generalises:** A pointer reinterpreted as a float is either a huge/denormal/NaN-adjacent value or coincidentally "reasonable"-looking garbage; checking whether a candidate field's value is plausible for its assumed type (finite, in-range, non-pointer-shaped) catches struct-layout misreads before they get built on for months.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "Classify an unknown value by its magnitude, not its declared type"
**API-specific:** none

### Don't re-invoke a stateful immediate-mode GUI's render path a second time just to capture its output
**What happened:** An early terminal-overlay implementation replayed the native GUI's draw calls a second time to composite them into the VR HUD layer. Telemetry showed this doubled stateful draw counts from 17 to 34-56 per frame, producing the reported fragmented/flashing email panes — the GUI framework was re-executing its own widget/animation logic, not just re-emitting pixels. The eventual fix rendered the native GUI exactly once into a dedicated surface sized to its real logical resolution (`1024x577`, elsewhere `880x560`) and linearly blitted that single result into the final `1920x1080` HUD target.
**Why it generalises:** Immediate-mode GUI systems execute logic on every render call; "rendering it again to grab a copy" is never free and desyncs any per-call state (dirty rects, animation timers, widget focus) — always intercept/blit the one real pass instead of triggering a second one.
**Chapter:** 04-ui-and-hud.md
**Status:** SHARPENS "HUD element ownership — find who actually draws it"
**API-specific:** OpenGL

### A scissor rectangle left outside your capture viewport silently discards the whole draw
**What happened:** Broken terminal email tiles traced back to the native renderer issuing scissor rectangles that fell entirely outside the `1024x577` capture viewport being used for that frame. Since the scissor test is part of OpenGL's global state machine, those draws were being clipped to nothing without any GL error. The fix bypassed zero-intersection scissors only during terminal capture, on the owning render thread, and restored GL state immediately afterward — with bounded telemetry so the bypass count itself became debug evidence.
**Why it generalises:** Any global-state graphics API lets scissor/viewport state outlive the render-target switch that made it valid; when you retarget a pass into a differently-sized surface, a stale scissor from the previous target is a silent, zero-error way to lose draws.
**Chapter:** 10-graphics-apis.md
**Status:** NEW section
**API-specific:** OpenGL

### A hook installed before an object's identity is finalized can poison every later lookup
**What happened:** A `SetActive` hook called `ResolveIdentity` and cached the result before SOMA had assigned the entity's final name during construction. That provisional, non-hand identity got cached and was then reused by every subsequent `SetMatrix` call for that object, silently breaking full-scale hand takeover. The fix stopped `SetActive` from reading or caching identity at all — it can only suppress a deactivation once the exact pointer has already been discovered and seeded by a genuine, later `PlayerHands_*::SetMatrix` call.
**Why it generalises:** Constructors in engine object systems often run in stages (allocate -> partially configure -> assign final name/type -> first real use); a hook that fires early in that sequence and memoizes what it sees will cache the wrong answer forever unless it defers to a later, unambiguous signal.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Attach versus launch injection — and one-time construction seams"
**API-specific:** none

### When subsystem construction order is uncertain, derive and validate the pointer chain yourself instead of calling the engine's own accessor
**What happened:** Calling the engine's `cLux_GetGamePaused()` wrapper from a new eligibility check crashed at process uptime 10 seconds with a null read at `Soma_NoSteam+0xccc9e` (`movzx eax, byte ptr [rcx+0x2d4]`, `rcx=0`) — the `gameContext+0xc8` subsystem the wrapper unconditionally dereferenced simply didn't exist yet that early. The fix derived the same RIP-relative `gameContext` slot from the verified wrapper bytes, then had every caller separately validate `gameContext`, subsystem `+0xc8`, and the paused byte `+0x2d4` at each query, returning "unavailable" and failing closed when any link was missing — and reused that one guarded accessor for locomotion, menu, and hand retention alike instead of one hand-only patch.
**Why it generalises:** An engine's own internal accessor is written for its own call sites, which are guaranteed to run after the subsystem exists; a hook running from an unrelated timing context has no such guarantee and must validate the whole chain itself, not trust the wrapper's implicit assumptions.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Initialization timing"
**API-specific:** none

### Comparing prior-frame stereo pairs instead of same-frame pairs can overstate latency by 20x+
**What happened:** Naive frame-to-frame comparison of left/right eye timing averaged 57.76 ms, suggesting a serious stereo latency problem. Restricting comparison to only genuinely same-frame eye pairs — 194 valid pairs — gave a true average of 2.61 ms, a 4.36 ms p95, and a 12.29 ms maximum, with zero pose-frame gap. The 57.76 ms figure was just ordinary inter-frame scheduling variance, not a same-frame stall.
**Why it generalises:** Any timing instrument that diffs consecutive samples without first confirming they belong to the same logical unit of work (same frame, same pass) will report a number that is technically true and practically meaningless — the fix is always to tag and filter by same-frame identity before computing the statistic.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Your capture is phase-locked to your own stereo pair"
**API-specific:** none

### Bound your logging I/O by severity, or the instrumentation becomes the performance bug it was added to diagnose
**What happened:** Per-frame logging was itself causing measurable stutter. The fix flushed normal log rows in bounded batches while warnings and errors continued to flush immediately, preserving crash-relevant evidence without paying an I/O cost on the hot path every frame.
**Why it generalises:** Diagnostic instrumentation added to catch a rare bug is easy to leave running broadly; unconditional synchronous flushing turns routine telemetry into a frame-time regression, so logging policy needs its own severity-based cost tiering just like any other hot-path code.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Logging discipline (or your evidence destroys itself)"
**API-specific:** none
