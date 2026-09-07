# Project Process

A flat-to-VR conversion is a long, mostly-blind reverse-engineering grind with a slow test
loop (build → package → inject → put on headset → observe → take off headset). The process
scaffolding below is what kept SS2VR moving instead of going in circles. It generalizes to any
hardware-in-the-loop modding project.

## The documentation system that worked

A layered doc set, so each session starts with context instead of re-deriving it:

- **CURRENT_STATE** — a short, always-read dashboard: active baseline config, current build
  hashes, the last few sessions' results, and the immediate next tests. Kept short enough to
  load at the top of every session.
- **BUILD_HISTORY** — every build's hashes, what changed, and the handoff notes. The hash log
  is what lets you prove (later) which build produced which result.
- **FAILURE_REGISTRY** — "do not repeat." Every dead end, *why* it was a dead end, and the rule
  it produced. This is the highest-value doc; it stops you re-walking paths. (SS2VR's had 80+
  entries — most of this whole VR-modding guide is distilled from it.)
- **DECISION_LOG** — dated decisions with rationale, so reversals are deliberate not accidental.
- **CONVENTIONS** — single-source the math conventions (heading order, angle units, basis
  construction, field orders) with a parity table if you have sibling codebases. Conflated
  conventions were SS2VR's #1 recurring bug; one canonical doc kills the whole class.
- A **target/whitelist library** for data-driven gameplay (which objects are interactable,
  etc.) curated from in-game inspection, with a clear policy order.

The meta-point: write down the *non-obvious* — anything a future session (or a teammate, or an
AI assistant) couldn't re-derive from the code or git history. Don't document what the code
already says.

### One fact, one canonical owner

Navigation can be duplicated; technical truth cannot. Assign each new statement
to one layer before writing it:

| Layer | It may own | It should link instead of restating |
|---|---|---|
| Router | Entry question and destination | Gate rules and technical method |
| RE/source route | Access-specific discovery/ownership gates | Shared VR implementation |
| Shared spine | Gate order, artifact and exit test | Chapter algorithms and rule lists |
| Technical chapter | Full method, evidence, exceptions and cautions | Project-local addresses/hashes |
| Pattern/failure atlas | One atomic recipe/discriminator; patterns use `CAM-001`, failures use `FAIL-CAM-001` | Full explanation |
| Project receipt | Target/build-specific observation | Transferable rule |

If a factual sentence must be edited in two places, its ownership is already
wrong. Keep the fact in the canonical layer and make the other page ask the
question or link to it. Before adding a document, identify which existing owner
cannot hold the material; “this page is long” alone is not a new responsibility.
This is the growth control for the playbook: routing depth should buy narrower
reading, not force a reader through repeated summaries.

This exact layout is now running, near-identically, on all three projects (SS2VR, BioshockVR,
SOMAVR) — the same `CURRENT_STATE` / `BUILD_HISTORY` / `FAILURE_REGISTRY` / `DECISION_LOG` /
`CONVENTIONS` / `ADDRESS_REGISTRY` spine, plus per-feature RE docs. That convergence is itself the
argument for it: three engines, three teams-of-one, and the same doc set kept each one moving. Two
force-multipliers worth adopting deliberately:

- **A findings index.** Once the per-feature docs multiply (SS2VR has a `VR_FINDINGS_INDEX.md`), a
  one-line "which doc owns this topic" map is what stops the same finding being written in three
  places or lost entirely.
- **A knowledge graph over the corpus.** All three projects run graphify over their source and
  docs (`graphify-out/`), and treat `graphify query "<topic>"` as the first orientation pass before
  `rg`. For a *cross-project* view — "where did all three hit the projection-companion problem?" — a
  graph built over the combined doc set surfaces the overlaps and contradictions a per-repo grep
  can't. This playbook is the hand-authored version of that synthesis; the graph is how you keep
  finding what belongs in it.

## Test-validity discipline (the hardest-won lesson)

A test that can't prove *what it tested* is worse than no test — it produces confident wrong
conclusions. Bake validity in:

- Every test has a **machine-checkable precondition** (the build banner shows the right
  version; the config key wasn't rejected; the expected mode flag is set) **and** a
  **machine-checkable proof line** (the value changed; the action fired; the residual dropped).
- Check the precondition *before* asking the user to put the headset on. (SS2VR repeatedly
  burned headset sessions on builds that silently weren't running the change — every one was
  preventable by reading the first log line.)
- Distinguish "user reported X" from "log proves X." Both matter; conflating them hides bugs.

## Reduce the project's biggest bet to one falsifiable experiment, first

Before writing any stereo code, run a **de-risking battery**: for each project-level risk, the cheapest
experiment that could kill it, plus a **named fallback** if it does. This front-loads the answers that
determine whether the architecture is viable at all.

(*An independent BioShock mod's battery is a good model — a standalone 32-bit OpenXR hello-world under
both target runtimes, with the fallback "SteamVR-only ⇒ 64-bit companion compositor" declared **up
front**; a check that the exe is large-address-aware and using the expected renderer; a frame map; a
camera-hook wobble test; and — the whole stereo bet — **"call the scene-draw entry twice per frame with a
2° yaw delta."** That single experiment decided the project's primary architecture before a line of
stereo code existed. See [13](13-teardown-bioshock-vr.md).*)

It is fine to leave non-blocking items unretired; the point is that the items that could *invalidate the
plan* are answered while they are still cheap to answer.

## How VR is it? Declare a completeness tier and ship to it

"Is this a VR mod yet?" has no answer without a scale, and without one a project drifts: every missing
affordance feels like an outstanding task, so nothing is ever finished. **Pick a tier, say so publicly,
and build to it.**

The scale below is drawn from the surveyed external mods plus the first-hand fleet.

| Tier | What the player gets | Technically requires | Examples |
|---|---|---|---|
| **T0 · Flat in a headset** | A screen floating in space. No parallax; head look pans a virtual display, not the game camera | A blit to both eyes | vorpX cinema mode; sims4-vr's first VorpX-based release |
| **T1 · Stereo view** | Two eyes with real parallax, head rotation driving the **game's** camera. You are *in* the world. Input unchanged | Correct per-eye projection and a stereo pair ([09](09-d3d11-openxr-injection.md), [17](17-teardown-fc2vr-native-stereo.md)) | The intended floor for any mod here |
| **T2 · 6DoF + motion-mapped input** | Head translation moves the view; controllers drive the game, usually mapped onto the existing scheme. Aim may be decoupled from view | Pose pipeline, an input layer, aim redirection | **BF2VR**, **Virtua Cop 2 VR** |
| **T3 · VR-native interaction** | **Tracked hands exist as objects.** Physical weapon handling, world-space or layered UI, comfort options as first-class settings | Hands, IK, [02](02-viewmodels-and-hands.md) in full, [04](04-ui-and-hud.md) | **GTFO**, **RoR2VRMod**, **White Knuckle**, **Satisfactory+UEVR** |
| **T4 · Adapted for VR** | The game's own systems are **changed** to suit VR: per-content tuning, physical reload, holsters, body avatar, seat/scale calibration | Deep engine integration; per-weapon and per-context work | **FEAR VR**, **Cyberpunk VR**, **Halo-MCC-VR** |
| *T5 · Designed for VR* | *Content authored for VR from the start* | *Not reachable by modding a flat game* | *— (an engine recreation like `shock2quest` is the only mode that could aim here)* |

### The cut between T3 and T4 is the useful one

T3 **adds** VR affordances. T4 **changes the game** to suit them.

- T3: you have hands, and you can grab the weapon.
- T4: **thirteen weapons are individually tuned**, the magazine follows the path the weapon's own well defines, and the empty hand relaxes when a weapon is drawn.

That is where the work becomes unbounded, and it is exactly the boundary at which a scope needs to be
declared rather than discovered.

### Higher is not automatically better

**A rock-solid T1 beats a broken T3.** BF2VR stopping at T2 on a closed Frostbite title with anti-cheat
is a defensible engineering position, not a shortfall — and it says so in its own README rather than
implying more.

The failure mode is not aiming low; it is aiming *unstated*. A project with no declared tier reads as
permanently unfinished, to its author most of all.

### The tiers gate each other — build in order

T3 hand work sitting on a T1 that is subtly wrong produces bugs that look like hand bugs. A T4 comfort
decision can be invalidated by a
[per-eye alignment fault](09-d3d11-openxr-injection.md#the-two-eyes-dont-line-up-a-five-minute-differential-diagnosis)
nobody diagnosed. **Get each tier genuinely right before spending on the next**, and note that the
per-eye alignment diagnosis belongs at the bottom of the stack precisely because everything above
inherits it.

### This is one of three independent axes

The playbook now carries three scales, and **they are orthogonal** — knowing one tells you little about
the others:

| Axis | Question | Where |
|---|---|---|
| **Mode** | How do you build it? Injector, managed plugin, framework+companion, source port, engine recreation | [18](18-beyond-the-native-injector.md) |
| **Stereo rung** | How is the second eye produced? Native, per-draw replay, alternate-eye, reconstruction | [17](17-teardown-fc2vr-native-stereo.md) |
| **Completeness tier** | How much of the game becomes VR? T0–T4 | *this section* |

Worked examples of the independence:

- **BF2VR** — native injector, stereo rung 2–3 (per-draw replay + alternate-eye), completeness **T2**.
- **Cyberpunk VR** — native injector, rung 1 (a real second engine view), completeness **T4**.
- **Virtua Cop 2 VR** — native injector, **rung 4** (scene reconstruction, the bottom rung), completeness
  **T2** — and it is a *good* mod. A low stereo rung did not cap its completeness.
- **Satisfactory** — framework+companion, rung 1 (UEVR's), completeness **T3**.

**A source port can ship at T1 and an injector can reach T4.** Do not let a hard-won position on one
axis imply anything about the others.

### State it in the README

Every mod surveyed here that is pleasant to use tells the player what it is and is not, up front —
supported modes, unsupported content, known limitations. That is the same instinct as
[naming the near-miss states](#name-the-near-miss-states-that-look-like-success), applied to scope
rather than to bugs: **an honest limitations list is what lets a user trust the rest of the document.**

## Two gates per milestone: flat first, headset second

The headset is the expensive, scarce resource ([08 slow-loop ergonomics](#slow-loop-ergonomics) below), so
make it the *second* gate, never the first:

- **Flat gate** — numeric acceptance on a clean boot: counters, call rates, image diffs against a
  *measured noise floor* (one project's standing-still floor was 0.21–0.40 mean, with a real change
  reading 2–8+, so anything in between is not evidence).
- **Headset gate** — an explicit checklist, and the milestone ticks on the **user's** verdict.

**Add a third, backwards gate: every live probe emits a fixture that the headless suite replays forever
after.** A headset or live-game session is expensive and produces a one-off observation that can silently
regress the next week. Promoting its captured bytes into a permanent no-game test converts each expensive
session into standing regression coverage.

(*PreyVR's promotion rule states a live discovery is not implementation-ready until its deterministic parts
sit behind a pure API exercised with no game and no headset. All three of its live protocols were promoted
into named fixtures that reproduce the exact recorded values — a `0.127165`-unit displacement, an entity
handle changing `0xFDE0`→`0x1117` — with 11/11 passing headless. The doc also draws the boundary
explicitly: pose maths, signature validation, config parsing and log-schema checks belong headless;
renderer ownership, GPU identity and OpenXR timing need a live process.*)

Drawing that boundary in writing is most of the value — it stops "we need the headset for this" from
expanding to cover work that never did.

Write the "done when" clause in **user-observable terms**, not implementation terms. "You can physically
lean around a corner and nothing drifts", "look left while shooting right and impacts land where the
controller points", "a friend can install from the zip, press one button, and every binding works" — each
of those is testable by someone who has never seen the code, and none of them can be satisfied by a green
log.

Two habits that pair with it: record *what was actually verified and what was deferred, by whose call*,
inline with each tick; and **strike through superseded work rather than deleting it** — a retired design
that stays on file is a banked fallback, and the next session can see why it was retired instead of
rediscovering it.

## Assert the ARCHITECTURE in the source text, not only the behaviour {#source-contract-tests}

Witcher3-VR ships a class of test this playbook did not have: **CMake scripts that read the source file
and assert structural properties of it.** They sit beside ordinary unit tests and catch a different kind
of regression entirely. `[SOURCE]`

The clearest example enforces "the presentation-size slider is applied **only** at the final OpenXR
submit":

```cmake
string(REGEX MATCHALL "g_config\\.presentation_scale" slider_reads "${source}")
list(LENGTH slider_reads slider_read_count)
if(NOT slider_read_count EQUAL 4)
    message(FATAL_ERROR "Presentation Size must have exactly four reads
        (INI, Alt producer coupling, config log, final OpenXR); found ${slider_read_count}")
endif()
```

It then splits the file at the final hook and requires that **exactly three** of those four reads are
upstream of it.

**No unit test can express that.** "This value is consumed in exactly these places, and nowhere else" is
a property of the *code's shape*, and the regression it guards against - somebody adding a fifth,
reasonable-looking read - passes every behavioural test until the two consumers disagree.

The same file pins the frustum-declaration rule in the source itself, by requiring these fragments to be
present:

```
derive_symmetric_eye_subimage(
projection_views[eye].subImage.imageRect = final_presentation.image_rect;
projection_views[eye].fov               = final_presentation.represented_fov;
```

So "the submitted FOV is the one derived from the submitted rectangle" is not a convention anyone has to
remember - **decoupling them fails the build.**

**Where this earns its place.** Use it for invariants that are about *structure* rather than results:

| Invariant | Why a unit test cannot hold it |
|---|---|
| a value is read in exactly N places | the extra read behaves correctly in isolation |
| two fields are always assigned together | either one alone is a valid program |
| a hot path contains no allocation, logging or locking | the cost is not a wrong answer |
| a fix is still present | a refactor can quietly revert it |

That last one is why their fragments carry tagged markers like
`[FIX:FINAL-OPENXR-PRESENTATION-SIZE V1417 1/2]`: **the test names the fix it protects**, so a failure
tells you which decision was undone rather than that a string is missing.

**The obvious caveat, and it is real:** a text assertion breaks on an innocent rename, and it can only
see what it was told to look for. Keep them few, keep them aimed at decisions that were expensive to
reach, and make the failure message say *why the rule exists* - every one of theirs does.

See [TEST-012](pattern-catalog.md#test-012).

## A test can lock in the bug it was written to catch

The worst outcome of writing a test alongside a feature is not a missing test — it is a **passing test
that asserts the broken behaviour**, because then the defect is protected.

(*FarCry2-VR: `SwapEyes` was a **no-op for three headset sessions** while their own test asserted the
broken behaviour as correct. They noted it was "the second time that failure shape has bitten here."*)

It happens when the expected value is written by reading what the code currently produces, rather than
derived independently from what it *should* produce. That is an easy thing to do at 2am and almost
impossible to spot afterwards, because everything is green and self-consistent — the same failure as
[a self-consistent instrument](#a-self-consistent-instrument-can-be-consistently-wrong), one layer up.

Two defences, both cheap:

- **Derive the expected value from the requirement, not from a run.** For `SwapEyes`, "left and right
  differ after the call" is derivable without executing anything.
- **Prove the test can fail.** Invert the behaviour deliberately and confirm the test goes red. A test
  that has never been observed failing is an assertion about nothing — the same negative-control
  argument as everywhere else in this playbook.

When a bug turns out to have been shipped under a green test, **fix the test first and watch it fail**,
then fix the code. Otherwise you have no evidence the test now covers anything.

## A self-consistent instrument can be consistently wrong

The most dangerous test is one that validates your code against *itself*. If your ray, your laser, and
your test harness all derive from the same math, they will agree beautifully while all being wrong
together.

(*One project shipped a muzzle-direction feature whose flat gate proved only internal consistency; in the
headset the beam was visibly off "by a lot," because the bone axis it derived from was not the barrel.
The gate had never once compared the computed axis against the **rendered** barrel.*)

**At least one gate in every chain must anchor to ground truth you did not compute** — a rendered pixel, a
bullet hole in a wall, a physical measurement. Everything else is a consistency check, which is necessary
but never sufficient.

## Slow-loop ergonomics

Because the test loop is minutes long and ends in a headset, optimize for **information per
loop**:

- Bundle independent tests into one session (lighting + wobble + input in one headset trip).
- Prefer **live cvars** over rebuild-required changes for feel-tuning; an A/B you can flip
  in-headset is worth ten rebuilds.
- Build **default-off probes** alongside fixes so the next session can both *test the fix* and
  *measure the next unknown* in the same trip.
- When you hand back to the user, give a **short, numbered, command-level** test script and ask
  for specific artifacts (the log, the condump, three-word verdicts). Vague asks → vague data →
  wasted loops.
- **Automate the flat loop end to end.** The highest-leverage tooling is a closed loop that can answer
  "did this change the image?" with no human and no headset: a command channel into the running mod, a
  screenshot grabber, and a pixel-differ. A plain **text file the injected DLL polls once a second** is
  enough of a command channel — no console, no hotkeys, no IPC library, and scriptable from anything.
  Pair it with automated boot-to-gameplay and you can sweep dozens of pokes unattended. See
  [13](13-teardown-bioshock-vr.md) for a worked example.
- **Build a deterministic record/replay lane** if you can: capture the poses and inputs at one seam, then
  replay them so a refactor can be proven byte-identical rather than "looks the same." (*One project
  gets 712/712 bitwise-identical marks across a 7112-frame sweep.*) The trap to enumerate explicitly:
  **any global state that drifts between record and replay poisons the comparison** — pin or disable it.

## Your pixel-diff threshold is an experiment, not a constant

A flat harness answers "did this change the image?" by comparing two captures. That answer is worthless
until you know what the *unchanged* case scores — and measuring that is a real experiment with four ways
to get it wrong. Two projects hit all four independently.

**1. Prove your capture actually contains the 3D scene.** A capture API that returns the window's GDI
layer gives you the UI and nothing else — and it looks like a beautifully quiet signal. (*Swat4-VR's
`PrintWindow` captures were ~8 % non-black, completely static, and produced **eleven exactly-zero
diffs**. A 0.0000 floor is not a quiet scene, it is *no scene* — and it would have made every later diff
read as "changed."*) Sanity-check the non-black fraction and confirm the image moves when you move.
Capturing from **inside** the engine (Swat4-VR uses the game's own `Shot` console command) sidesteps the
whole class.

**2. The naive statistic is actively harmful on a bimodal sample.** Your measurement pairs are usually a
mixture of genuinely-quiet frames and frames where something moved. (*Swat4-VR's mean + 3σ over the mixed
population gave a threshold of **47.26** — which would have hidden every real change while looking
rigorous. Their real quiet floor is 0.25–0.58 and real changes read 13.6–15.8.*) Use median/MAD, report
the quiet population only, and **list the pairs you excluded** rather than silently dropping them.

**3. There may be no single floor for the target at all.** A game with fire, foliage, wind or adaptive
exposure has a floor that depends on what is on screen. (*FarCry2-VR measured **0.1285** in a still scene
and **6.79 mean / 8.85 max** in a busy one — high enough to swallow a real change. Their delay sweep was
non-monotonic (0 ms → 2.24, 700 ms → 12.98, 2000 ms → 5.10), which is the signature of periodic content:
fire flicker, cloud shadows, a ~30 s weapon idle.*) **Capture a control pair in the same scene
immediately before the treatment, and compare against that** — never against a number measured earlier,
elsewhere, or by another project. A floor is a property of a scene, not of a game.

**4. Report separation, not the floor.** The number that licenses a conclusion is the ratio. (*FarCry2-VR:
control 0.1285 vs treatment 23.5611 — **183×**, driven end-to-end through the command seam with no hotkey
and no window focus.*)

Two capture traps worth paying for once: **make the harness DPI-aware** (*a 1920×1080 window measures
1536×864 at 125 % scaling* — the same virtualisation trap as a scaled desktop resolution), and remember
captures are **not frame-synchronised**, so even a zero-delay pair differs by ~2.2 in a moving scene.

A useful cross-check: two of these projects landed in the same band (0.21–0.40 and 0.25–0.58 quiet, with
real change an order of magnitude up). Matching *bands* across targets is evidence the method transferred.
Matching *numbers* would be evidence you copied a constant you hadn't earned.

## Sweep every install location before ranking candidates {#sweep-install-locations}

A candidate survey is only as complete as the directories it looked in, and an unswept drive is
[a negative claim from a partial index](06-debugging-methodology.md#negative-claims-exhaustive) wearing
a shortlist's clothes. `[LIVE]`

One survey's open questions recorded *"non-Steam installs not checked"* as a known limitation. When the
second drive was finally swept, **two targets landed in the top four immediately** - and it also held a
game already being modded by this fleet. Storefront-diverse installs are the norm, not the exception:
GOG, Epic, standalone installers and old retail discs all land outside the default library.

**And DRM status is a ranking input, not a footnote.** A DRM-free install makes static analysis work at
all, which can be the difference between a tractable target and an intractable one - so record it beside
the engine, not in prose.

**One heuristic to calibrate before trusting it:** a "thin import table means packed or wrapped" rule
**assumes an executable**. A game *module* legitimately imports almost nothing, because it links against
the engine's exports rather than the OS - so the check fires on exactly the DLLs you most want to read.
Scope that heuristic to executables, or it produces confident false positives on every well-structured
engine.

## Hard-fail the preconditions; do not document them {#hard-fail-preconditions}

Two process failures, each of which cost a wasted headset trip, and each fixed by a check rather than a
sentence. `[LIVE]`

**Three separate "hangs" were the game simply not being the foreground window.** A helper script had
documented that since an earlier recorded failure; the launcher never called it. The playbook already
covers foreground handling - the addition is that **the precondition must be checked and hard-failed by
the launcher**, not written down. A documented precondition is one an operator can satisfy; it is not one
the run can rely on.

**Fail closed on a stale build.** One project's tools defaulted to `build/x86-release/Release` while the
CMake preset built `RelWithDebInfo`, so a headset trip tested a **day-old DLL**. The gate compares the
DLL's mtime against the newest source file and **exits non-zero rather than launching** - cheap, and it
converts a whole class of confusing headset results into a build error. See
[an artifact's identity includes whether it matches your source](#irreproducible-artifact).

**And instructions to a person wearing a headset must be executable while wearing it.** One engineer told
their operator *"if it stalls, don't alt-tab, just tell me"* - which cannot be complied with, because
telling them requires alt-tabbing. Same family as
[controls that must be reachable from inside](#headset-reachable-controls): an instruction the wearer
cannot follow without breaking the test is not an instruction.

## Verify a sibling's build identity from their own patch bytes {#sibling-build-identity}

Before trusting another project's address corpus, **find a documented patch site with expected bytes in
their source and read those bytes from your executable.** `[LIVE]`

DishonoredVR's matched exactly - `5E 8B E5 5D C3` followed by `CC` padding - and their *rejected*
candidate showed the same misleading prologue shape the sibling had described. **That single check turned
23,000 lines of another project's research log into a directly usable corpus with no rebasing.**

Cheap, decisive, and it should be **step one** whenever two projects share a target or a build - it is
the difference between inheriting a corpus and inheriting a hypothesis.



`[LIVE]`

**Two builds can share a PE timestamp and be different images.** FarCry2-VR's build profile identifies
`Dunia.dll` by **SHA-256 prefix and file size, never by timestamp**, because the Modernized Edition is
a different image carrying the same timestamp - the exact trap. Hash the **file on disk**, not the
loaded image: the image has relocations applied and its import table written, so a memory hash
depends on where Windows chose to load it, while the file hash reproduces what `sha256sum` gives the
user and what the address registry records. Unknown images are **refused by name** rather than
falling back to a default, and `Offset.*` config keys override any entry without a rebuild. The test
asserts the refusals as hard as the matches, because *a wrong-image build does not crash - it hooks
plausible addresses inside unrelated functions.* They ship their verified UPLAY/Steam set, the GOG set
so a user on that image is refused rather than mis-hooked, and Modernized with no offsets so it
resolves to a name and then fails completeness. `[LIVE]` FarCry2-VR rule 10.

## An instrument's controls must be reachable from inside the headset {#headset-reachable-controls}

One project bound a headset viewer's image cycling and quit to console keystrokes. **With an HMD on you
cannot see which window has focus, cannot click one, and on a shared machine focus changes under you.**
The session had to be killed from Task Manager.

**The real cost was not the annoyance.** The comparison the session existed to perform *did not happen* -
only the first image was ever shown, and the judgement that came back therefore applied to **a single
data point rather than the sweep**. They found out afterwards, from the log.

> **A focus-dependent control silently converts a measurement session into one sample.**

**Fix:** OpenXR **input actions** - an action set with suggested bindings for
`khr/simple_controller`, which every runtime must support, plus the vendor profile. Controller input is
delivered to the focused XR **session**, so desktop focus is irrelevant. A timed auto-advance covers the
no-controller case.

**In-headset A/B pays for itself immediately**, and a second project reached the same conclusion
independently: having the wearer remove the headset, describe the change, and wait for the next value is
a round trip *slower than the thing being measured*, and it **destroys the comparison** - by the time the
second value is applied the first is a memory. Two consecutive settings were reported indistinguishable,
almost certainly because of the gap rather than the settings. **The wearer asked for this**, which is
worth noting: it was not obvious from the outside.

**Export a press counter.** The wearer cannot read the current value, so *"the poll cannot see your
keys"* and *"the setting does nothing"* are otherwise indistinguishable.

**And do not bind headset-mod hotkeys to `Ctrl+Alt+Arrow`.** That is Intel's display-rotation shortcut
where the driver's hotkeys are enabled. Rotating the desktop under someone who is wearing a headset and
cannot see it happen is a genuinely bad outcome. `PageUp`/`PageDown` and `Home`/`End` are safe.

## Launch preconditions are part of test validity

Chapter [06](06-debugging-methodology.md) says every test needs a machine-checkable precondition. Some
preconditions are not in your build or your config at all — they are in **how the process was started**,
and if you miss one the run does not merely produce a wrong result, it produces *no valid result*.

(*FarCry2-VR's target cannot start at all on their machine without a restricted CPU affinity mask: a
32-logical-processor boundary bug in the game's hardware-detection DLL runs away and smashes the stack
during startup. Proven by A/B — six identical crashes without it, clean boot with it. And the mask must
be applied **at process creation**; setting it afterwards races the detection code.*)

Treat these the same as the build banner: **record the launch condition alongside the version string**,
and make the injector own it so it cannot be forgotten. Anything in this family qualifies — affinity
masks, compatibility flags, elevation, a required command-line switch, a working directory, a
disabled overlay. A run that violated one is not a failed test; it is a **void** test, and must be
labelled that way rather than entered as evidence.

## Mark every claim `VERIFIED` or `UNVERIFIED`, and say how

A convention worth stealing wholesale: in the engine-notes document, **every single claim carries a tag**
— `VERIFIED` with the method that verified it, or `UNVERIFIED` with what *would* verify it.

It sounds like bookkeeping; it is actually a guard against the most expensive documentation failure
there is, which is a plausible search result quietly ageing into an assumed fact. Research done before
the game was even installed reads exactly like measurement six weeks later unless the tag is there.

(*Swat4-VR states it as a rule: "`UNVERIFIED` is a load-bearing tag… do not silently promote a search
result to a fact."*)

Pair it with a de-risking battery that tracks explicit states — `ANSWERED` / `PARTLY` / `OPEN`, each with
the evidence and the named fallback. A battery table where most rows say `PARTLY` is telling you
something true about the project that a prose status update will hide.

## Build shared tooling at a standardised interface, never at the game {#observe-at-the-interface}

This fleet ran the experiment twice, with opposite results, and the discriminator is clean enough to
plan around. `[LIVE]`

**One substitute OpenXR runtime serves seven projects** spanning Unreal 2, UE3, Dunia, KEX, HPL3,
CryEngine and a proprietary engine, across two architectures and five graphics bindings. Four private
forks of it were deleted in favour of the shared one.

**Six game harnesses share almost no code and never will.** One drives Frida and a game's own Python
camera API; one drives a UE2 console bridge and greps the engine's log; one drives Squirrel through a
vtable call at a fixed RVA.

> **A tool that sits at a standardised interface generalises. A tool that sits at the game generalises
> never.**

That is not a failure of the harnesses. It is the correct outcome, and knowing which side of the line a
tool falls on *before* building it tells you whether to invest in one good copy or six cheap ones.

### The split that follows

When a tool is on the generalising side, the shape is always the same - and the fleet's runtime and its
frame recorder independently landed on it:

| Layer | Owner |
|---|---|
| the mechanism, the schema, the checks | **shared** - pure specification types, zero game knowledge |
| launch wrapper | **per project**, tens of lines - one game needs a CPU affinity mask at process creation, another must go through its own injector or you test a mod-less game, a third cannot be started through its store client at all |
| state stamping | **per project**, opt-in - and the shared tool must be useful *without* it, or it cannot be pointed at a mod you did not write |
| assertions and golden baselines | **per project** - this is content, not infrastructure |

**The per-project half is about a day.** Resist the pull to move any of it into the shared core: the
moment the shared tool knows a game's name, it stops being reusable and starts being a fork waiting to
happen.

### And version the contract from v1

Seven consumers means a breaking change breaks seven projects at once. Additive-only: new records and
new fields any time, existing names and meanings never. Reserve fields for what one project already
does even if the others do not yet - one fleet project submits depth composition layers, and the
runtime it was first tested against had no depth handling at all, so that path could be neither
observed nor failed. **Reserving the slot costs nothing; adding it later breaks everyone.**

## Running several mods at once: which way knowledge flows

If you maintain a portfolio of conversions, the highest-value work is often not *in* any one project but
*between* them. Two patterns make that real:

- **One shared playbook, per-project rules on top.** Each project keeps a short `CLAUDE.md` of its own
  hard edges that explicitly defers to the shared playbook for everything general. New projects then
  start with the whole fleet's scar tissue instead of re-earning it — the point is that a project can
  inherit a hazard *before it is capable of hitting it*.
- **Deliberate cross-project review at intervals.** Run an explicit pass asking "what has each project
  learned that another needs?" The same failure appearing on two engines within days is common, and
  neither project notices without someone looking across.

Make that review operational through the [fleet bottleneck map](bottleneck-map.md): record the earliest
uncleared gate, its fast discriminator and exit proof for every project. The cross-project index tells
you where prior working lives; the bottleneck ledger tells you which piece of it should be transferred
now. Update the project receipt first, then `bottlenecks.yml`, so a summarized fleet row never becomes
more authoritative than the evidence it cites.

When two targets share an engine lineage, be careful about **which direction the knowledge flows**. The
instinct is to feed from the more mature project to the newer one. The better rule is:

> Knowledge flows from the target where the engine is **readable** to the target where it is **blind** —
> which may be the opposite of the maturity order.

(*SWAT 4 and BioShock are the same Vengeance/UE2.5 lineage. The BioShock projects are years ahead in VR
terms, but SWAT 4 shipped **1,492 UnrealScript source files** and a full SDK — so the foreground-lens
compensation relationship that BioShock spent three sessions reverse-engineering, shipped a
counter-model for, and later discovered the counter-model *was* the defect, is one readable line of
script in SWAT 4. The newer project is the reference implementation for the older one.*)

The corollary for a project sitting on readable source: **tag findings that have a blind-reversed
counterpart elsewhere**, so they can actually be harvested. A finding nobody knows to look for is not
shared.

## When source cannot reproduce the shipped artifact, say so in the repo {#irreproducible-artifact}

The worst version of a build-identity problem is not a stale build - it is a **released binary the source
tree cannot produce at all**, and Halo-MCC-VR documents theirs rather than quietly living with it.
`[SOURCE]`

Their released DLL received **five extra PE sections after linking** that no compile of the recorded
source commit produces. The way it surfaced is the transferable part:

> The first two-hand candidate was compiled from the narrow source change but did not contain those
> sections. That explains why its **Halo 3 hand behavior was correct while previously accepted Halo 4
> behavior regressed.**

**A missing post-build layer presents as a regression in an unrelated feature**, which is close to
undiagnosable if nobody has written down that the layer exists.

Their recovery tool is a model for handling it without pretending it is fixed:

- it accepts **only** the exact released donor DLL and an explicitly verified base profile, both pinned
  by complete SHA-256 - and for one profile also by the raw `.text` hash plus every stock section's
  geometry, because the embedded source-commit string legitimately changes the whole-file hash;
- it verifies all 11 redirected call sites, all 8 internal remaps whose linker RVAs moved, the custom
  section geometry, and that **nothing else differs** from base and donor;
- **it refuses a different code hash rather than falling back** to the older remap table.

And the honest label, which is what keeps it from becoming permanent by accident:

> This is a **recovery bridge, not a replacement for source**. Do not rebuild a release from that commit
> alone and call it parity.

## Verify the baseline you are betting on

A banked baseline — "we can always revert to X" — is the thing that makes it safe to run a risky
experiment. It is also the thing nobody ever tests, because testing it means throwing away current work
to prove you could.

(*Swat4-VR's `.gitignore` carried a bare `game/` rule, written to keep game-derived content out of the
repo. Git matches such a pattern **at any depth**, so it also matched `src/game/` — the symbol resolver,
the host adapter, all five engine hooks. **None of it had ever been committed.** Every `git commit`
reported success, `git status` was clean, the build never broke because the working tree was always
intact, and six sessions of "committed and verified" were true about the files git could see. The
pre-mutation baseline cited in the decision log, in commit messages and in the project dashboard could
never have restored the code it was supposed to protect — and one ordinary `git clean -fdx` would have
deleted the only copy.*)

Three rules, all cheap:

- **Anchor ignore rules that name a common word.** `game/`, `test/`, `docs/`, `src/` mean *at any depth*
  unless written `/game/`. That fix was one character.
- **"I committed it" is not evidence it is in the repository.** The check is `git ls-files <path>`, not a
  successful commit. This is the same shape as [06](06-debugging-methodology.md)'s *presence is not proof
  of loading*, turned on your own tooling — and it is the version you are least likely to suspect.
- **A fallback that has never been exercised is a belief, not a fallback.** If a revert knob, a quarantine
  path or a banked commit is load-bearing in your decisions, prove it works *once*, deliberately, while
  nothing is on fire. Restore the baseline into a scratch directory and build it.

Worth noting how this was found: **by review, not by the person who wrote it.** The failure mode was
invisible from inside the workflow precisely because every signal it produced was green.

## Classify the executable before you inject into it {#loader-preflight}

A loader that attaches to whatever it finds will eventually attach to something it cannot support,
and the failure surfaces as a crash the user reports as *your* bug. F4SEVR's loader is a compact
reference for the alternative, and it is all static: **map the target read-only and read it before
launching anything.** `[SOURCE]`

**Classify the image by its PE sections.** A `UPX0` section means the executable is packed; a Steam
DRM section means it is wrapped. The classification has four outcomes - normal, Steam, packed,
unknown - and the packed case is **refused by name**: *"Packed versions of Fallout are not
supported."* A refusal that names the reason is a support ticket that never gets filed.

**Compare versions three ways, not two.** Most loaders check "is this the version I know" and emit
one message. F4SEVR distinguishes:

| Case | Message |
|---|---|
| runtime **older** than supported | you are out of date, update the game |
| runtime **newer** than supported | *"You are using a newer version than this version supports... please be patient while we update our code"* |
| right runtime, **wrong branch** | you have the beta build of the extender; here is the release one |

Each is actionable and each names a different fix. The middle case is the one usually missed, and it
is the one that happens to every user on the day the game updates - so it is worth writing before
that day. This is [refuse, don't guess](#hard-fail-preconditions) applied at the loader.

**Read the version from the version resource, not from a hash of the whole file.** A hash changes for
reasons that do not matter; the version resource is what the vendor increments deliberately. Keep the
hash for [build identity](#sibling-build-identity) and use the version for compatibility.

## Test-artifact config files silently outrank your code defaults {#test-artifact-config}

A config file written by a smoke test, or left behind by a previous session, will be read at startup and
**override the default you just changed in code** — so the new default appears not to work, and you debug
the code instead of deleting the file. (*One project hit this twice, sessions apart, the second time
nearly cancelling a newly-tuned default with a stale `0.0`.*)

The rule that resolves it: **code owns defaults; test-artifact configs are deleted at session end.** But
tag the exceptions loudly — a file that is genuinely *user* data (tuning, calibration) must never be
swept up by that cleanup. And per [07](07-engine-integration-safety.md), log the config's identity so you
can see which file actually won.

**Deleting at session end is not enough when the test and the player share one profile directory.**
MoH-VR's automated runs archived their own cvars into the *play* profile - `sensitivity 0`,
`in_nograb 1`, `com_maxfps 60` and the test window size - and the next headset session had **no mouse
turn at all**. The engine was doing exactly what it was told by a file a test had written hours
earlier.

The fix is separation, not hygiene: **give the harness its own profile root** (`runtime/home-<flavor>-test`)
so a test run cannot write into the profile a human plays from. Cleanup you have to remember is a
cleanup that eventually does not happen; a separate directory cannot be forgotten. `[HEADSET]`
MoH-VR 2026-09-04, DEC-016.

Note the shape of the symptom: **the failure surfaced as a broken input device**, three layers away
from the config system that caused it. When a setting is inexplicably wrong, find which file supplied
it before debugging the subsystem that read it.

### A ported tool keeps the source project's identity at its edges {#ported-tool-identity}

Porting a working tool from another project is the cheapest move in this playbook - the
[substitute runtime](09-d3d11-openxr-injection.md#substitute-runtime) exists precisely so nobody writes a
fifth one. But the port has a predictable seam, and SOMAVR's is a clean worked example. `[SOURCE]`

They ported BioShock-Trilogy-VR's `xrsim` simulator (MIT) into `tools/xrsim`. The **runtime** came across
properly: the runtime name, the manifest, the environment variable and six of the seven scripts were all
renamed to SOMA's. The **launcher** was not. It still carried:

- `-Game bs1|bs2|bsi` and process names `BioshockHD` / `Bioshock2HD` / `BioShockInfinite`;
- log paths under `%LOCALAPPDATA%\BioshockVR\`;
- a staleness check on `bioshockvr.dll`;
- a probe for a **BioShock Remastered options dialog** that SOMA does not have;
- and a call to `launch-game.ps1`, which exists only in the source repository.

**The pattern: the algorithm ports, the identity does not.** The parts that talk to the outside world -
executable names, install directories, log paths, DLL names, window classes - are where the old project
survives, because they are the parts that carry no logic to attract review.

**And the worst case is a borrowed contract with someone else's component.** The launcher waited for two
lines in the mod's log:

```
xr: instance created on runtime '...'
xr: session running
```

**The SOMA mod never writes either of them.** So the launcher could not have worked here even with every
path corrected - it would have timed out on every run, reporting that the mod never came up. A contract
with another component's *output* is invisible in a diff, compiles nothing, and is not exercised until
someone runs the thing.

**The fix is to assert against the tool's own output, not the host's.** The simulator writes its own
`state.json` carrying `pid`, `runtime`, `frame` and `sessionState`. Reading that proves the simulator is
loaded, needs nothing from the mod, and is *better* than the log grep it replaced: if the runtime
selection silently failed, the simulator never loads and never writes the file, so **its absence is the
wrong-runtime signal**.

**A porting checklist that would have caught all of it**, and it is short enough to run every time:

1. Grep the port for the **source project's name** and every game code it used.
2. Resolve every **path, filename and window class** against this project.
3. List every **string the port matches on** and confirm something here actually emits it.
4. Confirm every **script or binary it invokes** exists at the path it uses.
5. Delete anything **conditional on the source game's behaviour** rather than leaving it inert - dead
   code that silently never fires reads as working.

Item 3 is the one that is normally skipped, and it is the one that made this port non-functional rather
than merely mislabelled.

### Every feature behind a config key is a bisection axis {#config-bisection}

The practical payoff of putting each new lane behind its own key, and it is larger than it looks.
Singularity VR diagnosed a hole in the floor **without a single rebuild**: `[SOURCE]`

| Test | Result | Rules out |
|---|---|---|
| rename `d3d9.dll` away | floor fine | **it is us** |
| `AIM METHOD` -> `HEAD` | floor fine | isolates the **mesh path** |
| `OcclusionQueryMode=0` | no effect | culling |
| `D3D9ExMode=0` | no effect | the texture wrapper |
| `HideStrayArms=0` | no effect | the stray-mesh rule |

> **Bisected on ini keys alone - no rebuild until the cause was named.**

**The first row is the one people skip**, and it is the same discipline that
[cleared a modder of a 22-year-old DRM bug](07-engine-integration-safety.md#dead-drm-sabotage): prove it
is yours before spending anything on which part of yours it is. After that, each key removes a
hypothesis for the cost of a relaunch rather than a build.

This is the argument for the practice, not just a nice property of it: **a lane with no off switch
cannot be excluded**, so it stays a suspect in every future investigation on that project.

### A measurement nothing consumes is not knowledge the system has {#unconsumed-measurement}

Two independent projects in this survey lost work to the same shape, and it is worth naming. `[SOURCE]`

Singularity VR's weapon-swap lag was 270 frames - about 2.25 s at 120 fps, worse below it. The fix
needed to know when the weapon changed, and that signal had already been established: runs 235b and 235c
measured that **the object pointer is the weapon's identity and that it does not move**. Meanwhile the
code that ran every frame *"had been reading `Pawn.Weapon` every frame since run 227 and throwing away
everything but 'is it null'"*.

> **The signal was measured three runs before anything used it.**

Psychonauts VR's version: correct unthrottled counters sat in the build for **two sessions** while work
continued from the numbers the old sampled ones had produced. **Finding something and wiring it in are
separate acts, and only the second one changes behaviour.** When a session establishes a fact, close it
by naming what now consumes it - or record explicitly that nothing does yet.

One more from the same fix, worth adopting as a habit: they deliberately made the comparison
**weapon-agnostic** (a pointer compare rather than a per-weapon rule), because *"a fix that works for the
two weapons someone happened to test is this project's recurring failure."* Name your project's recurring
failure, and check each fix against it.

### There are three configurations, and usually only one of them is tested {#three-configurations}

The section above says code owns defaults. Singularity VR found the harder version of that: **the code
defaults had never been run.** `[SOURCE]`

> Every validated run in this project's history ran against the dev machine's `SingularityVR.ini`.
> Nothing had ever run on the **code defaults** - the configuration a new user actually gets.

A second install exposed it immediately: the gun swivelled about the wrong point, the debug readout was
drawn, and the D3D9Ex wrapper was off so the frame took the **~9.8 ms** CPU copy. They diffed all 48
keys mechanically against the source and promoted the working values to be the defaults.

**And the shipped example file is a third configuration nobody tests.** Theirs shipped `D3D9ExMode=0`
and `Debug=1` **uncommented**, so it overrode whatever the code said - a user following the documentation
got neither the tested config nor the code defaults. Keep the count straight:

1. the **code defaults** - what a user with no file gets;
2. the **dev machine's file** - what every one of your runs actually used;
3. the **shipped example** - what a user who follows your README gets.

**Test 1 and 3 deliberately, because 2 tests itself.** A fresh install on a machine that has never run
the mod is the only thing that exercises them.

### A duplicated key is read once, silently {#duplicate-ini-key}

`GetPrivateProfileInt` and friends return the **first** occurrence of a key and report nothing about the
rest, so a hand-edited file *"reads as if the change was made and the mod behaves as if it was not."*
It cost Singularity VR a run: `ScopeDrawCensus` appeared twice, the first was `0`, and a census believed
armed recorded nothing. `[SOURCE]` BioShock-Remastered-VR ships the same warning to its users - *"the
first copy of a key is the one that is read, so a copy pasted at the bottom is ignored"* - which makes
two independent projects bitten by it.

Write-back through `WritePrivateProfileString` edits in place and is unaffected, so this only bites
hand-edits. One line detects it:

```bash
awk -F= '/^[A-Za-z]/ {print $1}' SingularityVR.ini | sort | uniq -d
```

Anything printed is a key whose later copies are dead. **Better still, echo every resolved setting at
startup** - then the log settles it either way, and the question never needs asking.

### An invariant in a comment is not an invariant {#invariant-in-a-comment}

The same project reported "the rifle is still broken" at run 271. It was not a regression: a key had
been set in the ini **since run 231**, forty runs earlier, and that key's own comment stated the cost.
`[SOURCE]` The [duplicate-key check](#duplicate-ini-key) and a startup echo would both have surfaced it.

Underneath sat the real defect, and its diagnostic signature is beautiful:

```
scope quad matches: 0 while AIMING, 120 while NOT aiming     (172 times in one run)
```

**A perfect inversion is a gate that was never applied.** The matcher was a pure *shape* test - prim
type, prim count, duplicate draws, render-target identity - with **no aim gate**, so it fired on ordinary
post-process quads, and every false match gated four separate features.

The part worth carrying:

> **The fix was already written as a comment directly above the code that ignored it:** *"the real scope
> quad can only be drawn while you are AIMING. A match with the aim trigger released is a false positive
> with no other possible reading."* **The trigger was read, counted, and never used as the gate.**

**A stated invariant that nothing enforces is a comment, not a guarantee.** When you write one down,
either assert it or gate on it in the same change - and when a classifier misbehaves, read the comments
around it before re-deriving the rule they already contain.

**A nastier variant if your config lives in a cloud-synced folder: the file you edited may not be the file
on disk yet.** OneDrive, Dropbox and friends put a race between "I saved it" and "the bytes are actually
written," and injection reads whatever is there at that instant. (*BioshockVR loaded a far-plane value of
`10000000` from an INI that already read `65536000` on screen, attributed to sync lag. Nothing errors; a
stale value simply loads, and you are now testing a different build variant than you think.*) Log the
config's **mtime and a hash of its contents** alongside the resolved values, and keep active test configs
out of synced folders entirely.

Two related snags worth knowing: a command that **does not exist** typically echoes nothing and does
nothing, and its silence is easily misread as "the feature ran and had no effect" — so make a command
echo a **mandatory precondition** of any measurement. And file handles opened non-shareable (`fopen_s`)
will fight your own log tailer or the OS indexer; open shared.

For graphics/OpenXR work, keep a permanent milestone ladder: injected log → D3D observation →
XR solid eyes → flat game bridge → tracked pose → private eye targets → sustained source →
native stereo subset → complete world → camera/culling → screen-space/viewmodel/UI. Never let a
later visual regression erase which earlier transport/ownership stages were already proven.

Track performance as evidence, not only polish. Record original draws, private draws per eye,
copies, source age, and rejected view groups. A new effect that coincides with hundreds of
extra replayed draws is an ownership clue before it is an optimization task.

### Order-dependent bring-up belongs in a script, not in memory {#bringup-script}

PreyVR baked its VR startup into `Invoke-PreyVRStartup.ps1` after three order-dependent steps had each
cost a headset session: `xr.srgb` before `xr.start` (the swapchain format is fixed at creation, so
gamma asked for afterwards returns an error - see [first pixels](09-d3d11-openxr-injection.md#first-pixels-gamma)),
`view.recenter` before `view.apply`, and `xr.native` defaulting off. The script also added `-Headset`,
because the launcher had been pinning `XR_RUNTIME_JSON` to the substitute runtime **unconditionally**
- correct for unattended capture, and it would have taken the game away from a real headset.

MoH-VR's launcher grew `-Arm`, `-Counters` and `-Cvars` for the same reason, and found a PowerShell
trap on the way: **`powershell -File` flattens array arguments**, so `@('+set','vr_arms','1')` arrives
as bare tokens and the strays bind to the next positional parameter. The documented command failed
outright; `name=value,name=value` survives `-File` intact. `[LIVE]` both.

## Packaging & backup hygiene

- **Back up before you overwrite** — the live config, the installed package, the user's
  profile. Keep timestamped backups in a known folder. You will need to roll back.
- **Bump the package version on every build** and verify it landed (open the installed archive,
  check the version string and changed files). "I copied the file" is not "the right file is
  installed."
- Keep the **live user config in sync** with shipped features in the *same* session you ship
  them — a lever that exists in code but not in the user's config tests nothing.
- Commit checkpoints with **hashes and a real changelog** in the message, so a result months
  later can be traced to an exact binary.

### An uninstaller is the most dangerous code you will ship

It runs on someone else's machine, with no supervision, against a directory layout you did not create —
and its whole job is deletion. Treat it as the highest-risk component in the package, not an afterthought.

*HaloVR's alpha uninstaller inferred "this is my folder" from the presence of its own DLL and then used a
recursive delete. A tester had extracted the package into the game root rather than a subfolder, so
confirming the uninstall **deleted their entire game installation.*** The rules that came out of it are
worth adopting wholesale:

- **Never infer ownership from an adjacent file.** Require an exact expected leaf folder name *and*
  validate the parent is the expected install root.
- **Never recursively delete an install directory.** Delete only an explicit **allowlist** of files you
  know you shipped, and preserve anything you don't recognise.
- **Keep a fake-tree regression test in CI** that builds a decoy directory layout and asserts the
  uninstaller removes exactly the right files and nothing else.
- If in doubt, **don't ship an uninstaller at all** — "delete this one folder yourself" is a perfectly
  good instruction, and it is what that project moved to. Also warn users about *older* copies of a
  destructive script still sitting on disk from a previous release.

The same caution applies to any install/deploy script that writes into the game directory: prefer a
self-contained subfolder, patch no game files, and make every destructive step enumerable in advance.

## Shipping to other people is its own engineering surface

Every project here is measured on whether the mod works on the developer's machine. That is a different
problem from whether a stranger can install it, and the second problem has its own failure modes. CoD4
VR's issue tracker is mostly install-time engineering, and the rules generalise
([18](18-beyond-the-native-injector.md) has the full teardown):

- **Detection is a preflight, not a proof.** *"Registry/file detection is an offline preflight, not a
  synthetic VR session."* Their first scan correctly reports that headset and controller evidence is
  *missing*, and only a live diagnostics run imports the real backend/runtime/interaction-profile
  receipt. Two verification stages, clearly labelled — the same distinction as
  [06](06-debugging-methodology.md)'s "presence is not proof of loading".
- **Refuse to guess at an unrecognised layout.** *"Setup rejects that layout before writing and never
  guesses, downloads, or moves original assets… automatic normalization is intentionally disabled until
  a verified before/after map is available."* An installer that guesses wrong damages a stranger's game
  install, and you will never see the machine it happened on.
- **Back up, hash, restore.** Back up every pre-existing file you manage, SHA-256 verify it, and restore
  the originals on uninstall. FC2VR's equivalent: the game executable and engine DLL are never modified
  on disk at all, with a `RESTORE_GAME.bat` for the interrupted case.
- **Say what a heuristic does not prove.** *"GPU memory provides only a conservative
  Native/Performance starting point. It is not a performance benchmark."*
- **Some content will not be shippable, and naming it is the deliverable.** *"Death From Above is not
  playable in VR and must be skipped"* — an AC-130 mission whose whole premise is a top-down sensor
  view. Documenting the skip and the next playable mission is a better outcome than an unbounded fix
  attempt, and an honest limitations list is what lets users trust the rest.
- **Assume other mods are installed.** On a managed game, users run a mod manager and twenty plugins.
  Witcher 3 VR's honest framing is worth copying: reproduce bugs on a clean install before reporting,
  stated as *"a temporary development-scope limitation, not a restriction on using mods."*

### The user's copy is not your copy {#ship-for-build-variants}

Everything above assumes the stranger is running the binary you measured. Often they are not. The same
game sold on Steam, Epic, GOG or Uplay — or patched after you started — is a **different image**, and
every RVA, vtable slot and struct offset you hold was measured against exactly one of them.

The fleet has this measured rather than assumed. Seven Prey functions whose Steam *and* Epic addresses
are both known show **five distinct deltas spanning `0x1590`**: code was inserted and removed unevenly
between the two, so there is no offset that carries a hook table from one to the other. Two of the
seven pairs happen to share a delta, which is exactly how a false shortcut earns confidence before it
corrupts something. Far Cry 2 VR ships against Uplay/Steam and treats the GOG build as a separate
target: their verifier passes 7/7 on one map and **correctly fails 7/7** on the other.

So a shipped mod owes the user three things:

- **Identify the build before touching it.** Hash the target binary and match it against the builds you
  actually validated. The install path often names the storefront; that is a hint, not an identity.
- **Select a table, or refuse.** Per-build offset tables with an honest refusal is a mod that works on
  two stores. One hardcoded table is a mod that works on one and writes to arbitrary addresses on the
  other — and the crash will surface somewhere unrelated, on a machine you cannot see.
- **Gate each hook as well as the image.** A per-landmark exact-byte check at the RVA you intend to
  hook catches a variant that slipped past the hash, and fails closed rather than instrumenting a
  plausible-looking wrong address.

State the builds you support in the release notes, including the patch level, and say plainly that
others are refused rather than untested. "Unsupported" that fails cleanly is a feature; "unsupported"
that runs anyway is a bug report you will never be able to reproduce.

Mechanics and the negative control that validates them: [RE-010](pattern-catalog.md#re-010).
Symptoms: [FAIL-RE-027 and FAIL-RE-028](failure-atlas.md).

## Compatibility is a property of the *route*, not the headset

"Which headsets are supported" is the wrong axis. The unit that actually works or fails is
**headset + connection method + active OpenXR runtime**, and the same headset can land on both sides of
the line:

| Route | Outcome |
|---|---|
| Quest 2 → **Virtual Desktop** | Working |
| Quest 2 → **Air Link** | Working, *but requires the SteamVR Beta branch* |
| Quest 2 → **Steam Link** | **Not working** |
| Rift S → Meta Horizon Link (Meta as active runtime) | Working |
| Rift S → SteamVR (SteamVR as active runtime) | Working |

(*World War VR's tested-configuration table. One headset, three connection methods, three different
answers.*)

Two consequences. **Publish the matrix by route**, because "Quest 2: working" is false for one third of
the ways people connect a Quest 2. And **require the connection method and active runtime in every bug
report** — without them a rendering-failure report is unactionable, and you will spend the exchange
asking for them anyway.

This also explains a class of "it works on my machine" that has nothing to do with the code: the
developer and the reporter may both be on a Quest 3 and still be running entirely different stacks.

## Name the near-miss states that look like success

Users do not report things they assume are normal. If a partial failure *resembles* a working build,
say explicitly that it is a fault:

> **A headset showing a desktop window or two-eye mirror instead of immersive stereo is a fault.** Exit
> the game and include the launch target and exact sequence in a bug report.

A flat mirror in the headset looks like something is working — there is an image, it moves, it came from
the game. Without that sentence the user files nothing, or files "performance is bad."

Every project here has at least one of these. Duplicated-mono-inside-a-Projection-layer
([17](17-teardown-fc2vr-native-stereo.md)) is the same shape at a deeper level: it reads as "the stereo
feels subtly wrong" rather than "the stereo is broken." **Write the list of states that look like
success and are not**, and put it in the user-facing docs rather than only in the registry.

## Check the dependency's BINARY, not its version {#dependency-binary-not-version}

"Install the latest stable build that has the feature" is a reasonable instruction that can be exactly
wrong, and a version number will not tell you. `[SOURCE]`

Visceral RE2 depends on a framework whose **mainline has never contained the feature they needed**. It
exists only on a branch in a fork. They downloaded **seventeen nightly builds spanning five months** and
counted the relevant symbols in each DLL: **every one zero**, including the newest. The fork publishes no
releases, its newest commit is months older than the nightlies, and both its CI runs failed - so no newer
binary exists at all.

> Installing "the latest" would have silently **removed** the feature they were trying to guarantee.

**When a feature lives on a fork, "latest" and "has the feature" point in opposite directions.** Symbol
counting is a crude tool and it settled this in minutes - the same shape as
[entropy triage](11-re-anchoring-and-discovery.md#probe-point) for packing: ask the binary, not the
metadata. Pin the exact build, record why, and record that upgrading is a **regression**.

**And distinguish a missing front end from a missing implementation.** Their framework ships the
feature's *UI* while the implementation is a separate plugin by a different author - which is why user
reports split into *"the option is missing"* and *"the option does nothing"*. **Those are two different
missing files**, and a support matrix that does not separate them will chase the wrong one.

## A self-healing mod cannot be uninstalled {#self-healing-uninstall}

A mod manager removes the files **it** deployed. It knows nothing about files a *script* wrote afterwards
- settings, caches, restored payloads - and those survive the uninstall. `[SOURCE]`

Visceral's clean-slate pass met the sharper version of this: the manager's uninstall emptied the content
directory, and **the next launch put 97 files straight back**, because their own switcher's *startup
heal* saw a recorded route, judged the file set inconsistent, and helpfully restored it.

> A self-healing mod is a nice feature right up until you are trying to uninstall it.

**If you ship a repair or migration step, gate it on the mod still being installed** - and say in the
uninstall instructions what it writes at runtime. This is [PACK-002](pattern-catalog.md#pack-002) from
the other side: *"uninstall = delete the folder"* only holds if nothing you wrote can rebuild the folder.

**Verify a clean baseline yourself rather than trusting the button**, and delete the framework's own
generated state too - config, UI layout, logs, accessed-file lists - or the previous project's tuning
follows you into the next one.

## Third-party dependencies you cannot redistribute

Sooner or later a mod needs a component whose licence forbids shipping it. The pattern that works
without touching the game install:

1. **Tell the user exactly which artifact to obtain**, by exact filename and source.
2. **Have them leave it unextracted** in a known location — an archive is verifiable, a directory of
   loose files is not.
3. **Verify it, then install it into your own private profile**, never into the game folder.
4. **Say plainly what not to do** — *"do not extract the ZIP or copy files into the game folder"* — and
   note that after the first successful import the original is no longer needed.

(*World War VR does this for an optional bot package it cannot bundle.*) The verification step is the
point: an exact-named archive can be checked before anything is written, which keeps you inside the
"refuse rather than guess" rule above. Their honest gap is instructive too — the launcher does not yet
surface installation status, so the documented fallback is a checklist of the three things that go
wrong.

## Close *families*, not attempts — and mark them decisive

Recording a failed attempt is good. Recording that an entire **family** of approaches is closed, with
the evidence, is what stops a long project walking the same ground every few weeks.

The Cyberpunk 2077 port is the strongest example of this discipline in any repository read for this
playbook. After **35 sessions** failing to obtain a second engine view, they wrote one synthesis naming
the single root cause, then closed three families explicitly:

> Closed families (all **DECISIVE, do not retry**):
> **A** "replay/double" — node write AV, driver read AV, view no-op, producer tears the shared manager.
> **B** "hand-build 2nd view" — byte-clone collides on a global arena slot; registry insert needs the
> engine's own hash+insert; call-site patch tears the shared manager.
> **C** "RTT handle shortcuts" — every callable path *consumes* a handle, never allocates one.

Four properties make that worth copying:

- **The root cause is stated once, above the families.** *"The engine carries exactly one main view per
  frame at every accessible level, and per-frame state is non-idempotent and globally arena-slotted."*
  Each closed family is then a corollary rather than an isolated anecdote.
- **"Decisive, do not retry" is explicit.** A reader six weeks later — or a fresh session — needs
  permission to stop, not just a record that someone once tried.
- **Every family links to the specific evidence** that closed it, so the judgement can be re-opened if
  the premise changes, rather than being an unfalsifiable "we tried that."
- **The dead ends are named in the filenames**: `…-dead`, `…-not-viable`, `…-exhausted`,
  `…-no-drivable-api`, `…-negative`. You can see what is closed without opening anything.

### Record falsified premises, including your own plan's

The same document contains a plan being killed by its own probe, in place, without being deleted:

> **UPDATE (run #1 of the probe):** the "per-frame attach iterator to piggyback" premise is
> **FALSIFIED** — the attach function fired **0× across ~900 frames**. So the vector is not "piggyback a
> per-frame loop"; it is "catch the one-time attach…"

That is the ideal shape: the original reasoning stays visible, the measurement that killed it is
recorded with its number, and the revised plan follows from the same paragraph. Deleting the dead premise
would have destroyed the reason the new plan looks the way it does — and would invite someone to
re-propose the piggyback next month.

**A plan you falsified yourself is a finding.** Give it the same weight as one that succeeded.

## Online multiplayer: presentation-only does not mean anti-cheat-safe

[18](18-beyond-the-native-injector.md) records that a presentation-only mod stays compatible with vanilla
peers. **That is a statement about the protocol, not about permission.** A live-service title with
anti-cheat treats an injected DLL as an injected DLL regardless of what it does.

BF2VR's README states it as plainly as it should be stated:

> **Do not play online. You will likely be banned.** … You can use [Kyber](https://github.com/ArmchairDevelopers/Kyber)
> servers though.

Three things to copy:

- **Say it in the README, in a warning block, above the fold.** Not in an issues page, not on Discord.
- **Point at where play *is* legitimate** — community/private servers, offline modes, an arcade mode.
  Theirs directs users to Arcade matches and a community server project.
- **Keep the flat-screen game reachable.** An eject key and a clean uninstall matter more here than
  anywhere else, because the cost of an accidental online launch is somebody's account.

## State the interoperability basis

Worth doing once, properly, in the README. BF2VR cites the statutory basis for the work and quotes the
operative paragraph:

> BF2VR is protected by [17 U.S. Code § 1201](https://www.law.cornell.edu/uscode/text/17/1201), which
> allows reverse engineering of programs for the sole use of interoperability. BF2VR allows Battlefront
> II with various OpenXR runtimes through the OpenXR Specification.

That is the correct framing for every project in this playbook: **an independently created program made
to interoperate with an existing one**, shipping no game code or assets. Pair it with the standard
disclaimers already common here — no game files included, trademark acknowledgement, no affiliation —
and the position is stated rather than assumed.

*(Not legal advice, and jurisdiction-specific. The point is that the projects which state it have
thought about it, and stating it costs a paragraph.)*

## Antivirus is part of your release process

An unsigned DLL that injects into a game is, structurally, indistinguishable from malware. Scanners will
flag it, and if you have not planned for that, your users' first experience is a quarantine dialog.

Halo-MCC-VR's release checklist is the most complete treatment of this in any project read here, and
every item generalises:

- **Never promise that every scanner will accept a build.** *"Unsigned injection-based binaries may be
  warned on or quarantined by security software."* Say it in the README, before someone discovers it.
- **Scan the package yourself before publishing**, with whatever is available locally.
- **If a scanner flags it, publish the exact detection name and the affected hash. Do not dismiss a
  result without investigation.** A false positive you have named is a support answer; an unmentioned
  one is a trust problem.
- **Tell users to allowlist the specific release files — never to disable protection globally.** The
  difference matters and users will do whichever you imply.
- **Publish hashes and insist downloads come from the official release only.** An injector is exactly the
  kind of artifact people reupload.
- **Make installation incapable of damage.** Theirs has no installer and no uninstaller: manual copy into
  a dedicated folder, so *"a package cannot delete or alter game files."*

Their candidate pipeline is worth copying wholesale, because it keeps the tested bytes and the shipped
bytes identical:

```text
build from a clean accepted-source descendant
  -> package to a unique ignored directory (never write into the game, never reuse a dir)
  -> CANDIDATE-MANIFEST.json says UNTESTED_LOCAL_CANDIDATE + source commit + DLL/launcher hashes
  -> headset acceptance
  -> release manifest and ZIP built WITHOUT changing the tested binaries; record ZIP SHA-256
```

The `UNTESTED_LOCAL_CANDIDATE` marker is the good idea: a build carries its own unaccepted status until
something explicitly promotes it, so an untested DLL cannot quietly become the release. It pairs with a
status line their docs use throughout — *"desk-tested, headset-untested, unaccepted"* — and a rule that
a candidate **must not be installed or launched without explicit approval for its exact packaged DLL
hash.**

## "Vacuous" is a distinct category from "absent"

A missing test is easy to notice. **A test that passes for a reason unrelated to what it claims to check
reads as coverage** — and it is worse than no test, because it stops anyone writing the real one.

Two of Swat4-VR's, both written the same day, both green:

- **A rotator-wrap test using yaws that were exact multiples of a full turn.** Normalisation subsumed
  the mask entirely, so deleting the mask failed nothing. (The mask *is* load-bearing — for precision
  near `INT32_MAX`, and for loop bounds: without it a `while (rel < 0) rel += 360` runs tens of
  thousands of times inside a per-frame camera hook. Their own comment justified that loop as safe
  *"because the input range is small"* — true only because of the mask nothing was checking.)
- **A singular-matrix test using the *zero* matrix**, which a second `isUsable` guard caught first, so
  the determinant guard the test existed to cover was never exercised.

**A test written from the same mental model as the code inherits its blind spots. Only breaking the code
checks the model.** That is the argument for mutation testing, and it is the same shape as
[a test that locks in the bug](#a-test-can-lock-in-the-bug-it-was-written-to-catch) — there the
assertion was wrong, here it is irrelevant.

Add `VACUOUS` alongside `ABSENT` when auditing coverage. They are found differently: absent tests by
reading the list, vacuous ones only by deleting code and watching what stays green.

### And ask what a restore restores *to*

From the same project, learned expensively: their mutation runner restored source with `git checkout` —
which restores to **HEAD**. Mutation testing is by definition run on **uncommitted** code, so mid-run it
deleted the implementations it was testing.

Its own *"source restored byte-for-byte"* self-check caught it, which is the only reason this is a
footnote rather than a lost day. **Ask what a restore restores *to*, not merely whether it restores** —
and give any harness that mutates your tree a self-check that compares against a snapshot it took, not
against version control.

## What a finished VR port actually exposes {#shipped-settings-vocabulary}

The Dark Mod's VR fork is a mature source port, and its full `vr_*` cvar list is the most complete
inventory in this survey of what survives contact with users. Read it as a **completeness checklist** —
if your port has no answer for one of these, that is a scope decision worth making deliberately rather
than discovering in a bug report. `[SOURCE]`

| Group | Settings | What their existence tells you |
|---|---|---|
| **Comfort** | `comfortVignette`, `comfortVignetteRadius`, `comfortVignetteCorridor` | A vignette is not one setting; the *corridor* variant narrows only along the movement axis |
| **Turning / movement** | `inputSnapTurnInterval`, `inputWalkHeadRelative`, `decoupleMouseMovement`, `decoupledMouseYawAngle` | Walk direction relative to head vs body is a user choice, and decoupled aim needs its own yaw threshold |
| **Aim feedback** | `aimIndicator`, `aimIndicatorSize`, `aimIndicatorColorR/G/B/A`, `aimIndicatorRangedSize`, `aimIndicatorRangedMultiplier` | Ranged weapons need *different* indicator sizing from melee - one size does not serve both |
| **UI placement** | `uiOverlayDistance`, `uiOverlayHeight`, `uiOverlayVerticalOffset`, `uiOverlayAspect`, `uiResolution` | Five independent knobs, because no single default fits every height, seated/standing pose and panel |
| **UI legibility** | `disableUITransparency`, `disableZoomAnimations` | Transparent UI over stereo reads as depth-ambiguous; zoom animations are a comfort hazard |
| **Handedness** | `inputLefthanded`, `useMotionControllers` | Left-handed play is a first-class setting, not a mirror hack |
| **Performance** | `useFixedFoveatedRendering`, `foveatedInner/Mid/OuterRadius`, `foveatedReconstructionQuality`, `useHiddenAreaMesh`, `useLightScissors` | See [source-side foveation](19-d3d12-and-performance.md#source-side-foveation) |
| **Operations** | `force`, `mirror`, `useDebug` | Forcing VR on, the desktop mirror and a debug lane are all user-visible in a shipped build |

Two of these are worth singling out because they are *not* obvious until someone plays for an hour:
**`disableZoomAnimations`** (BioShock-Trilogy-VR independently removed its zoom entirely, calling an HMD
FOV zoom a comfort hazard) and **`disableUITransparency`**. Both are cases where a flat-game affordance
becomes actively unpleasant in stereo.

## What a VR mod must force OFF in the host game {#host-settings-policy}

Distinct from the settings a mod *exposes*, above: these are the host game's own settings a mod
**overrides on the user's behalf**. Luke Ross's REAL mods ship per-game override files, and because
those mods have very large user bases the list is a shipped, complained-about, revised answer rather
than a theory. `[STATIC]`

Cyberpunk 2077's `option.replace` forces this set:

| Forced off | Why it fights VR |
|---|---|
| `AimAssistance`, `AimAssistanceMelee`, `VehicleAimAssistance` | Aim assist pulls against a head- or controller-aimed ray; the player feels the game resisting them |
| `AdditiveCameraMovements`, `SwayEffect` | Authored camera motion the head did not cause - the [bob/sway family](01-camera-and-tracking.md) |
| `MotionBlur`, `DepthOfField`, `FilmGrain`, `ChromaticAberration`, `LensFlares` | Screen-space post effects authored for a flat frame; in stereo they are per-eye artefacts with no depth |

**The instructive part is what it keeps.** This is not "turn everything down":

- `Anisotropy: 16` and `TextureQuality: High` stay **high** - cheap, and they pay off precisely at the
  glancing angles a headset spends its time at.
- `ContactShadows: true` and `FacialTangentUpdates: true` stay **on**.
- Everything volumetric, cascaded-shadow, SSR and subsurface drops to Low or Off - the expensive
  screen-space families.

**The policy is: kill camera-motion and screen-space effects; keep what is cheap and helps at angle.**
A blanket low preset throws away the second group for nothing.

### Square render targets, corroborated across authors and engines

Their Horizon Zero Dawn override sets:

```ini
ResolutionX   = 2700
ResolutionY   = 2700
AspectRatio   = 1:1
FieldOfView   = 70      ; the minimum the game allows
UpscaleMethod = Off
```

A **1:1 aspect at 2700x2700**. That is the same conclusion the
[independent BioShock VR mod](13-teardown-bioshock-vr.md) reached from the other direction - it
instructs users to set a roughly square desktop resolution because the eye target is sized from the
backbuffer and headset panels are near-square, so a 16:9 buffer spends most of its width outside the
FOV.

**Two unconnected authors, different engines, different eras, same answer.** Treat a square host
resolution as the default starting point rather than an optimisation, and note that they also force
`UpscaleMethod = Off` - an upscaler that owns the final image conflicts with a mod that wants to resample
it ([PERF-005](pattern-catalog.md#perf-005)).

### One binary, per-game data overrides

The delivery shape is worth copying for any multi-title mod. A single mod binary reads
`RealRepo/<GAMECODE>/settings/...`, so Cyberpunk, Horizon Zero Dawn and both Mafia Definitive Editions
are data directories rather than code paths - compare ForerunnerVR's per-title *modules* and
BioShock-Trilogy-VR's per-title *adapters*, which solve the same problem in code.

Two details in that tree are techniques in themselves:

- **`MDE1/1st_person/tables.sds`** - a replacement game **data table** shipped to enable the title's own
  first-person mode, instead of hooking the camera to synthesise one. Where a game already contains the
  mode you want, shipping data that switches it on beats reverse-engineering the camera.
- **`RealRepo/dbghelp.dll`** - the proxy vector. Games load `dbghelp.dll` from their own directory, which
  makes it a common injection point; note it is exactly the family a
  [no-installation-modification rule](18-beyond-the-native-injector.md#engine-sanctioned-loading)
  forbids.

## A feasibility document is a table of closed families {#feasibility-rejection-table}

BFVR's ambient-occlusion study is the shape to copy when a desirable feature may not be affordable. It
does not argue for one approach - it **enumerates every candidate and records a verdict with a reason**,
so the question cannot be reopened casually: `[SOURCE]`

| Candidate | Verdict and reason |
|---|---|
| Extra stereo geometry depth pass | **Reject** - replays hundreds of draws again, and measured replay cost already correlates almost exactly with draw count |
| Generic ReShade/MXAO injection | **Reject** - observes a generic `Present` boundary rather than the mod's two owned eye targets, and adds another hook owner |
| Colour-only darkening / unsharp-mask "AO" | **Reject** - cannot distinguish geometry from texture contrast, and its halos are especially objectionable in stereo |
| One-eye AO copied to both eyes | **Reject** - disocclusions and silhouettes differ by eye, so the term would disagree binocularly |
| Temporal / checkerboard AO | **Defer** - no motion vectors, no TAA, currently submitting at half display refresh; would add shimmer and ghosting to a first prototype |

Three of those reasons generalise well beyond ambient occlusion:

- **Any screen-space effect computed for one eye and copied to both will disagree binocularly**, because
  disocclusions and silhouettes are exactly what differ between the eyes. That is the general form of the
  [mono screen-space producer](14-render-pass-hazard-atlas.md) family.
- **Replay cost tracks draw count**, so any proposal whose implementation is "replay the geometry again"
  should be priced before it is designed.
- **A generic injector that hooks `Present` cannot see your owned eye targets**, and a second hook owner
  in the process is a cost in itself.

Note the distinction between **Reject** and **Defer**: the deferred row names the specific missing
preconditions (motion vectors, TAA, full-rate submission), so it becomes actionable the moment those
exist rather than being relitigated from scratch. This is
[closing families](#close-families-not-attempts-and-mark-them-decisive) applied to a feature that was
never built.

## A refutation can itself be wrong

[Falsifying your own plan](#record-falsified-premises-including-your-own-plans) is good practice. It is
not immune to the failure it protects against.

From one project's commit log, in order:

```text
revert(level-load gate): REFUTED - the load bounces with zero hooks installed
fix(level-load gate):    the refutation misread the log - re-enable with corrected thresholds
```

The refutation was itself a misreading, and the feature was correct after all. The cost of that round
trip was a revert and a re-implementation.

**Hold a refutation to the same evidence standard as a claim.** "It still happens with our code
disabled" is a strong result *if* the disable was total and the log actually shows the same event — and
those are two separate things to check, not one. The same discipline that stops you shipping a wrong fix
stops you deleting a right one.

## Working with the unknown

- Treat the engine as a black box you probe, not a system you reason about from first
  principles. Its actual behavior beats your model of it every time (see doc 06).
- Keep a running list of **parked / avoid** paths — things that didn't work and shouldn't be
  retried without new evidence. Future-you will be tempted; the list saves you.
- Celebrate the gambles that pay off and **write down why** (SS2VR's "crash combo" turned out
  to be a data bug, not a structural one — re-enabling it after the data fix retired a whole
  banned category). Today's hard "no" can become tomorrow's "yes" once an upstream cause is
  fixed — revisit bans when their suspected cause changes.
