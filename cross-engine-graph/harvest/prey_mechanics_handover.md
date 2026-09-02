# PreyVR — mechanics risk / handovers harvest

Files read: VR_MECHANICS_RISK.md (246 lines, full), HANDOVER-2026-08-03.md (200 lines, full),
HANDOVER-2026-08-07-HARDENING.md (140 lines, full), ARCHITECTURE.md (52 lines, full),
RUNTIME_BASELINE.md (66 lines, full), BUILD_BASELINE.md (32 lines, full)

### A per-item/status camera-rate modifier cannot be applied to a real head
**What happened:** Prey slows the camera's turn rate while the GLOO gun is equipped
(`GooGunCameraSpeedMultiplier`, `GooGunWalkSpeedMultiplier`). That is a valid flat-game trick — the
mouse-to-yaw mapping is just a multiplier — but a VR head's rotation is physically driven; there is no
gain knob on a neck. Any weapon/status system found to scale "camera speed" needs its effect
retargeted (e.g. to snap-turn cadence, weapon sway, or a UI cue) rather than ported as a camera
multiplier.
**Why it generalises:** Any engine with equippable items or status effects that modify player turn
rate hits this same wall — the multiplier assumption baked into a mouse/gamepad camera model silently
breaks the moment the camera is a real head.
**Chapter:** 03-input-and-locomotion.md
**Status:** NEW
**Evidence:** ASSERTED (symbol `GooGunCameraSpeedMultiplier` confirmed present; VR-breaking
consequence is reasoned, not runtime-traced)

### Engine-owned roll plus a non-fixed up-vector is the hardest VR mechanic combination there is
**What happened:** Prey's zero-G movement writes `RollSpeedZeroG` (camera roll the neck didn't
perform — worse for nausea than yaw, with no snap-turn-equivalent mitigation) and modifies
`zeroGUpAddition` (the up vector itself moves), which invalidates every convention that assumes a
fixed world up: comfort horizon, snap-turn axis, teleport arc, seated recentre. Three separate
zero-G camera-offset variables confirm the flat camera system already branches on this state, so any
pose-injection path must handle both branches, not one.
**Why it generalises:** "Does this mechanic write roll, and does it move the up-vector?" is a
two-question triage any engine's mechanic list can be run through before committing camera-ownership
architecture — the answer predicts comfort-mitigation cost independent of engine.
**Chapter:** 01-camera-and-tracking.md
**Status:** SHARPENS "Turning (snap & smooth) without nausea" / "Comfort is its own engineering surface"
**Evidence:** ASSERTED (symbols confirmed present in the binary; VR-difficulty judgment is
explicitly unvalidated against a running game)

### An engine camera-takeover system is a second writer to the transform your HMD pose owns — decide a per-sequence policy, not a global one
**What happened:** Prey's cinematics (`Actor:PlayerCinematicControl`, `CinematicVTOLUpdate`,
`cinematicFlags`) directly fight HMD pose injection for the same camera transform, and gate the
game's opening minutes rather than being skippable content. The existing `cinematicFlags` field
suggests per-sequence configuration data already exists, which argues for a policy *table* (position
follows cinematic / head owns rotation; substitute a fixed comfortable vantage; suppress entirely)
picked per sequence, rather than one global rule or case-by-case patching.
**Why it generalises:** Any engine with scripted/cutscene camera control needs the same three-way
policy decision, and "does a per-sequence flag/config already exist" is worth checking before
building a bespoke suppression system.
**Chapter:** 01-camera-and-tracking.md
**Status:** SHARPENS "Yield to the engine's authored cameras (cutscenes, ladders, conversations, seats)"
**Evidence:** ASSERTED (systems confirmed present via strings; policy choice is unvalidated design judgment)

### A mechanic that turns the player into an object breaks three VR invariants simultaneously — flag it even when optional
**What happened:** Prey's Mimic Matter power (`ArkPsiPowerMimicMorphInObject`,
`ArkPsiPowerMimicPhysicalizeObject`) collapses eye height to object scale (roomscale tracking becomes
meaningless), removes the body/hands the controllers would drive, and hands view-transform ownership
to the morph instead of locomotion — three separate VR-invariant breaks from one mechanic. It was
deprioritized only because the power branch is declinable, not because the risk is small; weaker
variants (`ArkPsiPowerSmokeForm`, `ArkPsiPowerShift`) share the same shape.
**Why it generalises:** "Scale change / body removal / view-ownership transfer" is a reusable
three-question test for triaging any transform-into-object, possession, or size-change mechanic in
any engine, and "optional content" is not the same risk category as "low severity."
**Chapter:** 01-camera-and-tracking.md
**Status:** NEW
**Evidence:** ASSERTED (symbols confirmed present; VR-breaking consequence is reasoned, not runtime-validated)

### A diegetically-framed HUD (helmet visor, cockpit readout) removes the comfort argument against head-locking it
**What happened:** Prey's HUD is narratively a helmet visor (`ArkPsychoscopeMod`,
`psychoscope3p_open/close`), which the analysis flags as "unusually friendly to VR" specifically
because the in-fiction justification for a head-locked layer defuses the usual complaint that
head-locked UI feels like it's glued to your face. The remaining work becomes ordinary screen-space
reprojection plus per-eye handling for the attached full-screen blur effect.
**Why it generalises:** When triaging a HUD for VR, check whether it already has (or could get) a
diegetic frame — a visor, cockpit glass, in-world device screen — before defaulting to a floating
head-locked panel or a full worldspace conversion; the fictional frame is free comfort cover.
**Chapter:** 04-ui-and-hud.md
**Status:** SHARPENS "Diegetic in-world screens and handheld devices"
**Evidence:** ASSERTED (system confirmed present; comfort claim is design reasoning)

### Procedural camera shake is neck-motion-that-isn't-yours, and it is measurable before you've built anything
**What happened:** A live readback probe (not a symbol guess) measured the flat camera's Z position
oscillating roughly 0.01 units around a baseline of 17.10 while walking — footstep shake, confirmed
live rather than inferred from strings. The engine exposes shake as named channels
(`cameraShake_footstepCameraShake`, `cameraShake_explosionCameraShake`), which matters because some
channels are gameplay feedback (explosion impact) rather than pure flourish, so the right fix is
per-channel suppression, not an all-or-nothing kill switch.
**Why it generalises:** Any engine with a procedural camera-shake system can be probed the same way —
read the camera's per-frame position while performing the triggering action — to get a real amplitude
number before deciding whether to suppress, dampen, or keep it, and shake systems worth keeping should
be audited for a channel/tag split before disabling wholesale.
**Chapter:** 01-camera-and-tracking.md
**Status:** NEW
**Evidence:** DEMONSTRATED (live-measured amplitude ~0.01 units around 17.10 baseline)

### Before building a mod-owned per-eye render path, audit the shipping engine for any existing "render a second scene in one frame" feature — it need not be labeled stereo
**What happened:** Prey ships a live cvar `e_ArkLookingGlass` (4 documented modes) that renders a
second scene through in-world "Looking Glass" windows — unrelated to stereo/VR, built for portal-like
in-world screens. Its existence is direct evidence the renderer already contains machinery for a
second scene-view within one frame, which — if it generalizes to being driven by a second camera —
could cut the cost of the mod's committed per-eye scene-reentry route. This does not contradict a
prior finding that no *stereo-labeled* control surface survives (checked separately, exhaustively);
portal/mirror/security-camera machinery is a different code path from a stripped stereo layer.
**Why it generalises:** Any engine with portals, security-camera feeds, mirrors, or split-screen
likely has an internal "invoke the scene renderer again this frame" seam that predates and is cheaper
than building one from scratch for VR — search for those features specifically, not just for
"stereo" or "VR" strings.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "If the engine has its own stereo path, use it"
**Evidence:** ASSERTED (the cvar and its 4 modes are confirmed live and observable; the reuse payoff
is an untested hypothesis — "was not started")

### Separate "a string/symbol exists" from "the assessment built on it" with two explicit claim tiers, not just VERIFIED/UNVERIFIED
**What happened:** The risk-ranking doc tags every line as either **Evidence** (a named string/cvar
is present in the binary — proves the system exists, not how it drives the camera at runtime) or
**Judgment** (the VR-difficulty call reasoned from that evidence plus general VR-comfort knowledge,
explicitly "not yet validated against a running game"). This is a second, orthogonal axis from
verified/unverified: it separates *what the evidence supports* from *what was concluded from it*,
which matters most in forward-looking risk/design documents where nothing has been runtime-traced yet.
**Why it generalises:** Any cross-engine team writing a mechanic-risk or design-triage doc before an
engine is fully instrumented needs this same two-tier tag, because a plain VERIFIED/UNVERIFIED split
doesn't distinguish "the string is real" from "my read of what it implies is real."
**Chapter:** 08-project-process.md
**Status:** SHARPENS "Mark every claim `VERIFIED` or `UNVERIFIED`, and say how"
**Evidence:** DEMONSTRATED (this labeling scheme is the actual structure of the source document)

### A struct-visualization tool's "+N" offset semantics can silently contradict its own documentation — diff every overlay read against a direct read before trusting it
**What happened:** ReGenny's `+N` in this build placed a field N bytes after the *previous field's
end*, not at absolute offset N as documented. A pre-existing struct definition had been silently wrong
since it was written — `swapchain` resolved to `+0xAE90` instead of the correct offset — and an overlay
read returned `(-1635.07, -7952.76, 6753.18)` where the ground truth (from direct address arithmetic)
was `(783.58, 1573.48, 17.10)`. It survived undetected because every prior finding came from x64dbg or
direct address math; nobody had read a value *through* the overlay before. Fixed and reverified 21/21
fields against direct reads.
**Why it generalises:** Every memory-struct-visualizer (ReGenny, Cheat Engine structure dissect, IDA
structs) has its own offset-arithmetic convention, and it can diverge from its documentation in a given
build/version without any error — the only defense is diffing an overlay-read value against a
known-address direct read before trusting the tool for anything else.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Tooling lies in specific, learnable ways — know them before you trust a reading"
**Evidence:** DEMONSTRATED (wrong vs. correct values captured above; 21/21 fields reverified)

### To tell a stereo eye-pair apart from a double-buffer in an unknown struct, capture the process standing perfectly still
**What happened:** A live probe found two candidate camera slots in the per-frame view block. The
decisive test was reading them while the player stood still: the two slots were byte-identical,
separation `0.00000`. A genuine left/right eye pair must differ by a constant lateral IPD offset at
all times, including at rest — identical slots at rest can only be MT/RT frame double-buffers, not
eyes. This closed the question outright rather than leaving it as a probability.
**Why it generalises:** This is a specific, reusable instance of differential-state capture: when a
candidate structure could be "two of the same logical thing" (eye pair, LOD pair, buffer pair), the
stand-still/no-input state is the cheapest state that forces the two hypotheses to predict different
observations — do this before assuming a two-slot structure is stereo just because it's paired.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "Differential state scanning: capture the same process in known states"
**Evidence:** DEMONSTRATED (separation 0.00000 measured live, stationary vs. moving states both sampled)

### When auditing a candidate camera struct for OpenXR fitness, check whether the frustum is stored as four independent edges, not a single symmetric FOV
**What happened:** The located per-frame render-view block (`renderer+0x4A08`, stride `0x328`) stores
frustum left/right/bottom/top as four independent values at `+0x270`, rather than a single symmetric
FOV+aspect pair. OpenXR requires asymmetric per-eye projection (`L != -R`), and because this struct
already carries each edge separately, asymmetric frusta are directly representable without
restructuring the camera — a real cost saving discovered by inspecting struct layout, not by writing
code.
**Why it generalises:** This is a concrete, checkable item for any engine's camera-ownership audit:
inspect whether the internal frustum representation is symmetric-FOV or four-edge before assuming a
camera struct needs modification to support OpenXR's asymmetric requirement — many engines already
store it the general way for other reasons (e.g. tilt-shift, portal rendering).
**Chapter:** 09-d3d11-openxr-injection.md
**Status:** SHARPENS "Projection companions must remain coherent"
**Evidence:** DEMONSTRATED (live-verified orthonormal rotation, position delta of 0.67244 units over
100 frames, and the four-edge frustum fields at the offsets given)

### Pin a verified-safe module permanently and keep its inactive hook trampoline allocated after disabling — trading reload testing for closing an unload race
**What happened:** After the exact engine gate, observer plan, and no-call OpenXR preflight all pass,
PreyVR's bootstrap worker acquires its own module reference and the module pins itself until process
exit, refusing `FreeLibrary`/hot-replace. Disabling the frame observer restores the original bytes but
deliberately *keeps* the (now-inactive) hook trampoline allocated, so a callback already in flight when
disable fires can still finish executing instead of jumping into freed memory. The enable export also
re-checks pin state, closing a brief "ready-but-not-yet-pinned" window that could otherwise let a hook
arm inside an unloadable module. Verified with 100/100 unsupported-host load/status/unload stress
passes and 11/11 CTest targets.
**Why it generalises:** Any injected module with a "disable the hook, maybe later unload" lifecycle
faces this exact race (in-flight callback vs. freed trampoline) regardless of engine or hook library —
pin-on-verified plus retain-trampoline-until-genuinely-safe is a reusable pattern, and the tradeoff
(no more hot-reload testing) should be stated explicitly, as it was here.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Module lifecycle: three Windows loader hazards that look like engine bugs"
**Evidence:** DEMONSTRATED (100/100 stress passes, 11/11 CTest, described lifecycle behavior shipped
in `0.3.0-lifecycle-hardening`)
