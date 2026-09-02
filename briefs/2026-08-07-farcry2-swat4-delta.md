# Delta brief — FarCry2-VR & Swat4-VR

**Revised 2026-08-07 (third pass), after the registry harvest, the Prey/Dishonored harvest, and a source
survey of seven shipped VR mods were all mined into the playbook.**
Follow-up to [2026-08-06-farcry2-swat4-brief.md](2026-08-06-farcry2-swat4-brief.md), which both projects
actioned. This is a **delta**, not a re-brief: what you taught the playbook, what the playbook gained
since, and the handful of items that bear on what each of you is doing *right now*.

The playbook grew 41k → 56k words in the last day. **That is not a reading assignment.** The sections
below are the ones that touch your current work; the rest will keep.

> **New since the second pass:** the entire "Seven shipped mods" section below, plus a **correction to
> chapter 03's arbitration advice** that changed under you — if you read that chapter before today,
> re-read the arbitration part.

---

## First: you both did the work

FarCry2-VR went from no repository to six commits carrying rung 3b (XR session on a private D3D11 device,
live in-game), a closed flat loop with a measured 183× separation, rung 4 stereo smoke with stereo-math
desk tests, and a lifecycle/hook-verification hardening pass. Swat4-VR went from zero commits to a console
bridge, a derived world scale (1 UU = ½ inch, ≈78.74 UU/m), a measured noise floor, an img-diff loop moved
into C# (minutes → ~1 s per pair), and a review pass covering R6 union checks, fail-closed math and
swapchain balance.

## What you taught the playbook

Five things from your registries are now in the playbook proper, because they generalise past your targets:

- **[08] "Your pixel-diff threshold is an experiment, not a constant"** — a new section built almost
  entirely from your two harnesses. Swat4-VR's `PrintWindow` blindness (eleven exactly-zero diffs from a
  GDI-only capture) and its bimodal-statistics trap (mean+3σ → 47.26, which would have hidden every real
  change while looking rigorous); FarCry2-VR's finding that a target with fire, foliage and adaptive
  exposure has **no single floor** (0.13 quiet → 6.79/8.85 busy, with a non-monotonic delay sweep), plus
  the DPI-awareness trap.
- **[08] "Verify the baseline you are betting on"** — a new section, entirely from Swat4-VR's **F-0011**.
  A bare `game/` ignore rule matched `src/game/` at depth, so the symbol resolver, host adapter and all
  five engine hooks had *never been committed* — while `git commit` reported success, `git status` stayed
  clean, and the build never broke because the working tree was the only copy. The generalised rules are
  now playbook text: anchor ignore rules that name a common word, `git ls-files` is the check and a
  successful commit is not, and **a fallback that has never been exercised is a belief, not a fallback.**
  Note the meta-point the entry makes about itself — it was found *by review*, because every signal the
  failure produced was green.
- **[07] A correction you earned.** The playbook credited FarCry2-VR's non-firing draw hooks to the same
  `AcLayers` app-compat cause as Swat4-VR's `F-0007`. That was wrong. The shims *were* resident, but the
  real cause was `d3d10core` swapping its own dispatch table every frame — both vtable addresses **inside
  `d3d11.dll`**. Two cause classes for one symptom, and **reading the two addresses is now the first
  diagnostic**: a replaced pointer still landing inside the API's own module means the runtime is
  reorganising itself, not that something interposed.

---

## For both of you, right now

### [09] Each rung of a proof ladder proves exactly one claim

You are both climbing explicit ladders — FarCry2-VR's rung 3b/rung 4, Swat4-VR's R1–R8 battery — so this
is the one to internalise. BioshockVR ran clone-bind → numeric proof → pose proof → wide-view → replay →
private-eye bind → eye-blit, and one run showed lifetime clone-bind applied counters at **4096** while the
numeric, pose and wide-view proofs had stalled at **5**. The plumbing worked perfectly and carried nothing.
Their own registry calls treating "it ran without crashing" as endorsement of the goal **the single most
repeated failure mode in it**.

Give each rung its own counter and read them side by side. Divergence between adjacent rungs is the signal
the ladder has stopped climbing while still reporting success.

### [06] Absence of errors is not evidence

Directly downstream of the above. A guarded or optional path — a shader replace, a hook override, a
patched draw — can degrade silently to a no-op fallback and produce a clean log. BioshockVR shipped a
visibly-mono build with the user reporting "zero shader errors"; the counters read `Attempted=2137915`
against `Applied=1765`, because a broad fallback added that build was swallowing essentially every draw.

**Count applied *and* attempted for the specific mechanism under test, and read the ratio.** Two counters.
This is the difference between "working" and "silently bypassed", and no amount of clean logging
distinguishes them.

### [06] Coarse switches first — then stop toggling and read state

Before instrumenting individual draws, build a reversible switch for the *whole stage*; a negative result
kills an entire hypothesis class in one test. SOMAVR bypassed its full post-effect composite and ruled the
chain out in a single toggle.

The counterweight matters as much: **when a hypothesis survives several A/B toggles without dying, you are
testing behaviour and the question is about state.** BioshockVR spent three builds skipping and
mono-falling-back a suspect draw class with mixed results; direct output-merger telemetry then showed those
draws had `rt0WriteMask=0x0` and `depthWriteMask=0` — they wrote nothing at all. No further toggle could
have exonerated them.

### [07] Your global hooks will intercept your own calls

Both of you detour a graphics API *and* will make your own calls into one — FarCry2-VR through the Dunia
render-device vtable plus a private D3D11 device; Swat4-VR through D3D9 into 9On12/D3D12. Every call you
make runs through your own detour logic, lands in your own classification and telemetry, and can
recursively re-enter submission. BioshockVR spent **six build cycles** chasing what looked like a Virtual
Desktop runtime bug (`0xC0000409`) before finding its own eye-blit was the caller.

The fix is not runtime-specific: a **thread-local "this call is mine" scope**, with every detour reachable
from it calling the original directly.

### [07] Creation-time caches are blind to whatever existed before you attached

Any identity cache seeded from `Create*` interception has a hole exactly the size of everything that
existed at attach time — and a cache miss reads as a *negative result*, not as missing data. BioshockVR's
shader-identity cache reported every sampled draw as PS-null under attach-mode, which misclassified a whole
family of mask draws and left the real producer unreachable. **Anything classification-critical queries the
live API; the cache is for cheap correlation only.**

Related, and cheap to get wrong: independent capture stages that each poll a hotkey **will** disagree about
a short press. Arm the later stage from the earlier one.

### [08] Log your config's mtime and hash, not just its values

If a test config lives in a cloud-synced folder there is a race between saving it and the bytes landing on
disk. BioshockVR loaded a far-plane of `10000000` from an INI that already read `65536000` on screen. No
error; you are simply testing a different variant than you think.

---

## FarCry2-VR specifically

- **[09] + [11] The affine residual gate, for your rung-4 stereo maths.** You have desk tests already —
  this is the specific assertion to add. Conjugating the eye transform through the real projection
  (`P_center⁻¹ · T_eye · P_center`) is only trustworthy if you *validate* the reconstruction: assert
  `oldWVP · P_center⁻¹` comes out affine, **and set the tolerance tight enough that a wrong answer fails
  it.** BioshockVR's first gate allowed a residual of 250.0, which let a guessed 75° FOV pass and silently
  distort geometry; tightening to 1.0 rejected it at residual 96.65. A bound nothing can fail is
  decoration — pick the threshold by confirming a known-wrong input trips it. The same residual settles
  your row-vector/column-vector convention empirically instead of by guessing.
- **[14] You have 380 draw families and four identified weapon draws. When you start mutating, key on the
  narrowest identity that reproduces.** BioshockVR fixed a screen-space artifact with a predicate of
  `SlotMask=4` **and** `MinIndexCount=18000` — matching only the specific draws. Broadening the same
  mechanism to the whole indexed-primitive family regressed four unrelated things and was reverted the
  same day. Widening a working narrow fix is a **new experiment**, not a generalisation.
- **[11] Look for a stereoscopic-3D fix for Far Cry 2 before you scan blind.** Legacy 3D Vision / Helix /
  3Dmigoto packages encode already-solved constant layouts, and they solve a neighbouring problem to
  yours. An old 3D fix for BioShock named `screenDataToCamera` at `c3` and `worldViewProj` at `c10–c13`;
  live probes confirmed those exact offsets and collapsed ~20 builds of blind cbuffer scanning into
  verification. Your `reference/` corpus discipline (CLAUDE.md rule 7) already handles the "vocabulary,
  not truth" part correctly — this just adds a source worth checking.
- **[06] Two unrelated systems failing the same way is one bug upstream.** With ~3 class-2 passes (shadow
  resolve, fog/volumetrics, heat-haze), if two of them misbehave identically, check shared resource
  ownership before triaging either. SOMAVR's shadows and reflections shared a signature and a root cause.

## Swat4-VR specifically

- **[14] The most relevant new lesson for B1: a once-per-frame mutable packet gets double-advanced by
  same-frame stereo.** You are about to double the scene draw. Post-effects routinely keep a small mutable
  "this frame" packet — a phase counter, an adaptation value, a noise seed — advanced once per invocation.
  Call the draw twice and it advances twice, so eye two silently gets a different phase. SOMAVR hit this in
  deferred SSAO *and* tone mapping with the identical shape, and the fix was identical both times:
  **capture the pre-update packet and the committed result before eye one, replay that baseline for eye
  two, then restore eye one's committed result** so exactly one logical update persists per frame. This is
  distinct from the temporal-history problem and will not show up in a hazard-atlas class-3 count.
- **[14] And the triage rule that goes with it: a stereo-only artifact is infrastructure until proven
  content.** SOMAVR patched a correctly-named water-shader parameter across 369 draws to explain a
  stereo-only artifact. Zero effect. The cause was a reflection texture shared across eyes. Before touching
  shader logic, answer one question: is the suspect buffer per-eye or a singleton?
- **[13] R6 removes the deadlock machinery, not the re-entrancy question.** Single-threaded (227k calls,
  one thread) puts you in the BioShock-2 case — no forced-inline renderer, no thread-count poke, no drain
  watchdog. Read `SequentialReentry`'s re-entrancy section before doubling the draw anyway.
- **The Vengeance backward-flow has an artifact.** `cross-engine-graph/harvest/bioshock_*.md` holds 88
  lessons mined from BioshockVR's registries — the *same engine family* as your target — of which only the
  generalisable ones reached the playbook. The engine-specific residue is exactly what
  `VENGEANCE_SHARED_FINDINGS.md` is for. Your rule 14 still applies: never copy a number, derive it fresh.
- **[08] Your noise floor is well-measured; adopt the control-pair rule anyway.** SWAT 4 maps carry far
  less dynamic content than Far Cry 2, so your fixed 0.25–0.58 is probably sound — but a control pair
  costs one capture and upgrades "probably sound" to "measured here, just now."

---

---

## Seven shipped mods: what they all did about input

Everything else in this playbook comes from projects still in flight — including yours. This section is
different. It is a source survey of six **shipped, publicly played** flat-to-VR mods plus the generic
Unreal injector: **JKXR**, **TheDarkModVR**, **GTFO_VR_Plugin**, **RoR2VRMod**, **BendyVR**, **CSVR**, and
**UEVR AFW**. Their *defaults* encode what survived contact with real users.

**You are both pre-input right now** — FarCry2-VR is at rung 3b/4 on the render path, Swat4-VR is at B1.
That is the best possible time to receive this, because you can adopt the shipped pattern instead of
retrofitting onto something you already built.

### 1. All seven fed the engine's own input funnel. None built a parallel one.

| Mod | How synthetic input enters |
|---|---|
| JKXR | reuses the engine's **disused `CL_JoystickMove()` slot** |
| TheDarkModVR | injected **as if it were a gamepad** — same axis array, same call site |
| GTFO | Harmony **postfix** on the game's own `InputMapper.DoGetAxis/DoGetButton*` |
| RoR2 | **registers as a Rewired hardware controller** |
| BendyVR | Harmony **prefix** on `PlayerInput.MoveX/MoveY/...` |
| CSVR | leaves `usercmd_t` and prediction **byte-for-byte stock** |
| UEVR | **emulates XInput** — the game believes a real pad is connected |

Seven for seven. The shipped answer is always *find the channel the engine already listens on*. The
input ladder in chapter 03 ranks techniques by fidelity; this survey says the **entry point matters more
than the rung**.

**FarCry2-VR:** your export census found 404 named `FCE_*` exports, and nothing in your docs shows an
input/gamepad channel among them — but Far Cry 2 shipped with gamepad support, so a DirectInput or XInput
path exists somewhere in Dunia. **Run the census again specifically for it before you design rung 4.**
JKXR's entire input layer rides a slot the engine had stopped using; that is the cheapest possible
outcome and it costs one search to rule in or out.

**Swat4-VR:** your `CLAUDE.md` rule 16 — *"Prefer the script surface over a hook. If a behaviour can be
reached from `script/SwatVR/`, or from the console `Exec` seam, that beats a detour"* — **is exactly
JKXR's pattern**, which routes every discrete VR action through `Cbuf_AddText` so each button press
becomes literally the console string a keybind would produce. You arrived at it independently and you
already have the `Exec` seam bridged. That is the shipped answer; don't talk yourself out of it when the
hooking route looks more direct.

### 2. Interaction: repoint the engine's existing ray, don't build a picking system

Three mods found this independently. GTFO replaces the camera-ray function and writes back into the
game's *own* `CameraRayPos/Collider/Normal/Object` fields, so native interaction prompts, pickups and
doors inherit controller aiming without knowing anything changed. RoR2 assigns
`body.aimOriginTransform = hand.muzzle.transform`. TheDarkModVR redirects the frob raycast at a single
branch point — and its `Grabber` class needed **zero** VR-specific changes.

When either of you reaches interaction: find the engine's existing pick/use/frob ray and change **where it
starts**, rather than building a controller-ray picker alongside it.

### 3. Two defaults that save you work

- **Snap turn is the shipped default nearly everywhere** — 45°, 45°, 45°, 60°, with a re-trigger delay
  around 0.25–0.33 s. The sole exception is UEVR, which cannot know the game.
- **Nobody shipped working teleport locomotion.** GTFO and RoR2 have *zero occurrences of the word* in
  their entire source. BendyVR ships a documented `Teleport` config with **zero call sites**. UEVR has an
  unused stub. For action-paced games, smooth locomotion plus snap turn is what actually shipped —
  so **don't budget for teleport** unless a specific mechanic in your target demands it.

### 4. Chapter 03's arbitration advice changed under you

It previously said: arbitrate with a bounded recency window, **never** sum the two sources, **never**
disable the engine's original input call. Six of the seven shipped mods do no per-frame arbitration at
all — GTFO and JKXR **sum** (additive merge, single clamp) and it works; BendyVR **hard-disables** the
mouse axes and ships that way. Only UEVR uses a recency window, and it needs one because it cannot know
the title.

The rule that survives is narrower: **exactly one lane ends up driving a given control**, reached by
elimination, by entering the engine's device layer, by additive saturation, *or* by a recency window.
Prefer them roughly in that order; reach for the window when none of the others apply.

### 5. You are both hand-writing for one known game — so don't build generic machinery

UEVR is the control case, and its limits are the instructive part. It fully generalises the
controller→gamepad translation layer. It explicitly **cannot** generalise "which axis means what to this
game" — both its aim and movement modes ship defaulted to *let the game decide*. It ships **no** generic
grab/interact system by design, and its one attach-by-overlap tool is a human calibration aid, not a
runtime system.

Swat4-VR, this points at you hardest: you have **1,492 SDK `.uc` files plus SEF's 1,741**, and 7,682
exported symbols. You know the answers UEVR has to ask a user for. Hard-code the known paths; skip the
generic discovery machinery entirely.

### 6. A staging signal, and a cheap CI check

**TheDarkModVR ships motion-controller input behind a cvar defaulting to `0`, labelled "wip" in its own
help string** — in a released VR mod, controller *input* was judged less production-ready than HMD
*rendering*. Both of you are doing rendering first. That ordering is what shipped.

**Add a check that every config key is actually read somewhere.** Two mods independently ship a
user-facing, documented, defaulted config entry with no implementation behind it — RoR2's
`AimStabiliserAmount` has its consumer commented out; BendyVR's `Teleport` has zero call sites. Swat4-VR's
rule 11 already enforces struct/parser/template/whitelist lockstep; this adds the last link — *and is
consumed*. It matters more than it sounds, because a config file is exactly the artifact someone later
mines as evidence of what you chose.

---

## Two cautions, both sharper after this week

**A lot of the new material does not apply to either of you.** Two axes in particular:

- **64-bit.** REX-prefix signature drift, x64 crash-handler ABI divergence, 64-bit image bases,
  trampoline sizing on short vtable thunks — all from SOMAVR and PreyVR. **Both your targets are
  32-bit.** None of it is yours.
- **Engine-specific finds.** The UE3 rotator arithmetic and camera-modifier notes are DishonoredVR's;
  Swat4-VR is UE**2.5**, which is a different generation with a different camera surface — treat those as
  adjacent evidence, not as your answers. The CryEngine and OpenGL material is Prey's and SOMAVR's.

I am flagging this explicitly because the playbook grew 37% in a day, and the fastest way to waste a
session is to apply a correct lesson to the wrong architecture or the wrong engine generation.

**Do not import a constant you did not earn.** The floors, thresholds, residual limits and offsets in the
playbook are evidence that a *method* worked on a target, not values to reuse. Swat4-VR's F-0011 is the
current best illustration of the general form: the thing everyone had confidently cited for six sessions
was never checked by anyone. `UNVERIFIED` and `ASSERTED` are load-bearing tags — two of this week's
harvested "lessons" turned out to be plans that were never built, and both are tagged as such in the
playbook.
