# PreyVR — test protocol / headless method harvest

Files read: LIVE_MULTIVIEW_PROBE_PROTOCOL.md (103 lines), LIVE_A0B_WRENCH_PROTOCOL.md (72 lines),
LIVE_INTERACTION_A0_PROTOCOL.md (60 lines), HEADLESS_TESTING.md (45 lines), SMOKE_BUILD.md (55
lines), FRAME_OBSERVER_BOOTSTRAP.md (41 lines), TEST_PLAN.md (19 lines), GHIDRA_SYNC.md (26 lines).
All read to end-of-file.

### Write the decision rule, including its "ambiguous" branch, before running the experiment
**What happened:** The multi-view probe protocol states in advance the exact byte pattern that means "multi-view retained," the pattern that means "closes negative," and explicitly reserves a third outcome — "ambiguous — record what was seen and do not promote either way. An honest null is a result; a guessed layout is not." All three live protocols (multiview, wrench A0b, interaction A0) were run and their actual results were recorded against these pre-stated branches, including one refuted hypothesis (the command-ring candidate turned out to be `ID3D11Query` GPU timing objects, not view info).
**Why it generalises:** Any engine-RE team can pre-register a three-way decision rule (confirm / refute / inconclusive) before a probe, so the write-up cannot be quietly reshaped after seeing the data.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Falsify your own hypothesis before shipping a fix"
**Evidence:** DEMONSTRATED

### Perturb only stack-local, per-call scratch memory in a live experiment, never persistent state
**What happened:** Both the wrench and interaction protocols edit only the twelve direction bytes of a local ray copy sitting in the current call's stack frame ("this memory belongs to the current `GetHits` stack frame... the edit naturally disappears on return and does not require a persistent-state restoration write"). Camera, UI reticle, and the player's cached aim state are explicitly left untouched and verified unchanged.
**Why it generalises:** Choosing an experiment's write target by its lifetime, not just its semantics, eliminates an entire class of restoration bugs — nothing to undo means nothing to forget to undo, even after a crash.
**Chapter:** 07-engine-integration-safety.md
**Status:** NEW
**Evidence:** DEMONSTRATED (two independent protocols, both completed with confirmed effect)

### Bracket a single edited field with two one-shot stops, and read back the write before trusting it
**What happened:** Both wrench and interaction protocols arm exactly two hardware execute breakpoints per pass — one immediately after the engine copies its ray to the stack (edit point), one after the result is computed but before side effects begin (capture point) — and require reading the twelve written bytes back and aborting rather than resuming if they don't match what was written.
**Why it generalises:** A live-memory write is only proven to have taken effect once it is read back through the same path the consumer will use; assuming a `WriteProcessMemory` call succeeded is exactly the settings-lie failure mode in a different guise.
**Chapter:** 05-assets-and-materials.md
**Status:** SHARPENS "One-variable A/B, always"
**Evidence:** DEMONSTRATED

### Sequence live experiments as an explicit prerequisite ladder, not a grab-bag
**What happened:** The interaction protocol states "run it only after the wrench A0b protocol, unless the scene does not provide a safe static melee target," and `TEST_PLAN.md` shows A0a → A0b → I0 as ordered rows, each depending on the prior row's passed evidence. Each live protocol is the smallest possible next bounded runtime experiment building on the last confirmed rung.
**Why it generalises:** A de-risking ladder isn't just for render-path proofs (stereo/OpenXR); gameplay-logic and input proofs benefit from the same discipline of not attempting rung N+1 until rung N has a recorded pass.
**Chapter:** 09-d3d11-openxr-injection.md
**Status:** SHARPENS "The proof ladder"
**Evidence:** DEMONSTRATED

### Every runtime probe must emit a fixture that gets replayed in the fully headless suite afterward
**What happened:** `HEADLESS_TESTING.md`'s "promotion rule" states a live discovery isn't implementation-ready until its deterministic parts are extracted behind a pure API and exercised with no game and no headset. All three live protocols' captured bytes were promoted into named CTest fixtures (`wrench_query_fixture`, `interaction_query_fixture`, `aim_state_fixture`) that reproduce exact recorded values (e.g. the `0.127165`-unit displacement, the `0xFDE0`→`0x1117` entity change) without launching Prey. The doc draws an explicit boundary list of what belongs headless (pose math, signature validation, config parsing, log-schema checks) versus what needs a live process (renderer ownership, GPU identity, OpenXR timing).
**Why it generalises:** Turning every headset/game session into permanent regression coverage — rather than a one-off observation that can silently regress — is a reusable pipeline pattern independent of engine.
**Chapter:** 08-project-process.md
**Status:** SHARPENS "Two gates per milestone: flat first, headset second"
**Evidence:** DEMONSTRATED (11/11 fresh headless pass recorded 2026-08-07)

### Gate lifecycle promotion on an exact, all-or-nothing signature count — not "most landmarks matched"
**What happened:** The bootstrap DLL validates 22 exact renderer/player/interaction landmarks against mapped memory; only a full 22/22 match lets it plan the observer and pin the module. A headless test (`engine_map`) proves both a one-byte mutation and a truncated image fail closed, and `dll_load_fail_closed` proves the same DLL loaded with the target module absent returns unsupported, stays unpinned, and rejects observer activation.
**Why it generalises:** "N of N required, anything else fails closed" is a stronger and more testable contract than a fuzzy confidence threshold, and it composes cleanly with self-identifying builds (version/hash/landmark-count in every log line).
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Everything default-off, behind a knob"
**Evidence:** DEMONSTRATED

### Keep a disabled hook's trampoline allocated until process exit, not freed on disable
**What happened:** `FRAME_OBSERVER_BOOTSTRAP.md`: "Disabling restores the target entry bytes... The disabled hook entry and trampoline are retained until process exit so a callback that was already in flight cannot return through freed executable memory."
**Why it generalises:** A hook's teardown has to outlive its own in-flight callers; freeing trampoline memory the instant a toggle flips is a use-after-free waiting for a race, and the fix (retain until process exit) is cheap and engine-agnostic.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Hooking & native-call discipline"
**Evidence:** ASSERTED (stated design contract; the enable/disable cycle itself was proven, but the specific in-flight-callback race it guards against was not exercised)

### A full disassembler re-analysis pass can silently drop hand-made annotations — re-verify survival, don't assume persistence
**What happened:** `GHIDRA_SYNC.md` records that a 2026-08-01 full auto-analysis pass (86,434 functions, 557,719 symbols) reverted the prior day's `BeginRendererScene`/`EndRendererScene` renames and evidence-plate comments, while 24 other `Ark*`/weapon/camera annotations survived the same pass. The team re-applied the lost pair afterward and logged it as a named regression, not a surprise.
**Why it generalises:** Any RE workflow that periodically re-runs whole-binary auto-analysis needs an explicit post-pass diff/re-sync step; annotation survival is not guaranteed just because it "should be static."
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** NEW
**Evidence:** DEMONSTRATED

### Correlate the same target across two builds by exact bytes and live hits, not a linear RVA offset
**What happened:** To map a canonical EGS/Chairloader reference build's named functions onto the differently-built Steam binary, the project used "exact bytes, invariant control flow, and live hits... instead of a global RVA delta" to name matching player-resolver, camera, and reticle functions.
**Why it generalises:** Builds of the same engine rarely differ by a constant address offset once the linker/compiler changes; byte-identity plus control-flow plus a live confirmation is the robust substitute, reusable on any cross-build/cross-version RE task.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "Version robustness"
**Evidence:** DEMONSTRATED
