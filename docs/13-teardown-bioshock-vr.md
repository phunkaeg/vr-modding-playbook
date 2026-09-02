# Teardown: an independent BioShock VR mod

A focused study of **[VR-Stereo-Hub/bioshock-trilogy-vr](https://github.com/VR-Stereo-Hub/bioshock-trilogy-vr)**
— a native OpenXR mod covering **BioShock Remastered**, **BioShock 2 Remastered** *and*
**BioShock Infinite**. It gets its own chapter for a reason no other external project does: it targets
the **same game and the same engine** as this playbook's BioshockVR project, from scratch, and arrived at
a **materially different architecture**. That makes it the closest thing to a controlled experiment we
have — same problem, different solution, both working.

It is also unusually well documented (an 11,800-line status log, per-game engine-notes knowledge bases,
and a dated decision log recording *rejected* alternatives), so the reasoning behind each choice
survives, not just the outcome.

!!! info "This chapter covers two eras of one codebase"

    It began as `mohamad-balouza/bioshock-vr` at **227 commits**, covering BioShock 1 and 2 Remastered on
    Unreal 2.5 Vengeance. The project has since been rehomed to the **VR-Stereo-Hub** organisation and
    extended to Infinite, reaching **640 commits** and **v0.8.2** with all three games shipping from one
    branch. Its build instructions still clone the old URL, which is how the lineage was confirmed.

    Everything below the [trilogy-era section](#the-trilogy-era) was established in the first era and
    still holds. That section records **what generalised to a second engine and what turned out to be
    target-specific** — which is the more valuable question, and one only a multi-engine codebase can
    answer.

Everything below is technique and measurement. No code was copied, and their own rules forbid committing
game-derived content — the same posture this playbook takes.

## The headline: re-render the scene per eye instead of patching draws

This is the finding that matters most, because it dissolves a problem the other projects fight for
months.

Their primary stereo mode is **SequentialReentry**: hook the engine's **scene-draw entry**, then each
frame set the left camera + FOV → call the original → copy the backbuffer → set the right camera → call
the original again → copy. The engine renders the whole world twice, natively.

The consequence is the point:

> The engine computes every view-dependent effect natively per eye, so the per-shader fix long tail
> mostly evaporates.

Compare with [09](09-d3d11-openxr-injection.md)'s **mono screen-space buffer** problem — the dominant
artifact class on deferred engines, where shadow masks, SSAO, volumetrics and reflections stay
center-eye while geometry goes per-eye. Under scene re-entry that class *does not arise*, because the
engine regenerates those buffers for each eye as part of its own frame. They explicitly rejected
3Dmigoto-style draw duplication with vertex-shader stereo displacement as the primary route, citing
exactly the long tail of per-shader fixes that this playbook documents from the other side.

The cost is honest and worth stating: you render the world twice (real GPU cost), and you must make a
re-entrant call into an engine that never expected one — which is where all their hard problems live
(below).

**The generalizable rule:** before committing to per-draw stereo surgery, ask whether the engine's
scene-draw entry can simply be *called twice*. It is often findable, and it converts an open-ended
shader-fixing project into a bounded re-entrancy project.

## The stereo ladder as a de-risking device

Their five rungs, every one shippable, each de-risking the next:

1. **MonoScreen** — game frame on a quad ("cinema screen"). Validates all OpenXR plumbing with *zero*
   engine knowledge.
2. **MonoTracked** — same image to both eyes of a projection layer, camera driven by HMD 6DOF, FOV
   forced to headset FOV. Already a large experience win; validates camera math, world scale, and
   prediction timing.
3. **AlternateEye** — camera alternates ±IPD/2 per game frame, each frame submitted to one eye, stale
   image held for the other. Judders, **not shippable** — but proves geometric stereo correctness in
   about a day before the expensive bet.
4. **SequentialReentry** — the primary bet (above).
5. **DepthReproject** — vorpX-Z3D-style synthesis of the second eye from colour + depth. Full
   framerate, edge artifacts, flat-ish. Ships only if re-entry hits an intractable wall.

This refines [09](09-d3d11-openxr-injection.md)'s proof ladder in one specific way: rung 3 exists purely
as a **cheap correctness oracle for the expensive rung 4**. Alternate-eye is a day of work that answers
"is my stereo geometry right?" before you spend weeks on re-entrancy. Judder is an acceptable price for
an answer that arrives that early.

## Finding the re-entry seam: three refutations before the right one

Getting from "call the scene draw twice" to *which function* took three failed candidates, and the
failures are more instructive than the success.

**Candidate 1 — the render-thread drain. Dead by construction.** Their renderer is two-threaded: the
game thread builds and submits, a dedicated render thread drains once per Present. But **the camera
function runs entirely on the game thread — zero calls inside the drain.** So re-entering on the render
side could never re-sample the camera, no matter how well it worked. Double-calling the drain faulted,
then wedged the pump's event protocol into a hang.

> Before choosing a re-entry point, find out **where the camera is actually consumed**. A seam that never
> sees the camera cannot produce a second eye.

**Candidate 2 — the frame "root". Caught zero calls.** A function that looked like the frame root turned
out to be a flush/join. Cheap to discover, and only because they checked call counts before building on
it ([06](06-debugging-methodology.md)).

**Candidate 3 — the frame submit. The most dangerous failure, because it looked perfect.** Hooking the
submit worked flawlessly: exactly one submit per present, a single call site, and arguments that matched
the camera. Double-calling it produced **thousands of doubled submits, zero faults, zero extra presents,
and the yawed camera never rendered.** The view data was baked into the command queue during the
game-thread *build*, not at submit time.

> **A hook that fires perfectly and telemeters perfectly is not the same as a hook that is the seam.**
> Prove the doubled call produces *pixels* — yaw the camera 30° and diff the frame — not merely that it
> executed.

**The winner — the scene *build* root**, where the camera function runs exactly once inside every call.
Doubling it renders a complete second engine-paced frame per game tick, measured as 225 builds/s → 450
presents/s, with a yaw-30° frame diff of 7.8 mean against a 0.33 noise floor.

Note the discovery detail: a naive `CC 55 8B EC` prologue scan found a **decoy SEH function** nearby and
missed the real target, whose prologue is an aligned-stack `push ebx`. They located the true boundary by
finding the `CC`-padding run between functions instead. *The standard prologue heuristic misses
frameless and aligned-stack functions* ([11](11-re-anchoring-and-discovery.md)).

## Making a single-threaded engine re-entrant

Scene re-entry needs the renderer inline on the game thread; a threaded render pump deadlocks under
doubling. Their deadlock was brutally consistent — **five runs, 16 s to 3.5 min, always the identical
signature**: the game thread in `WaitForSingleObject(INFINITE)` inside the build, versus the render
thread waiting inside the drain. Getting out of it took two attempts, and the difference between them is
the lesson.

**Attempt 1 — poke the engine's hardware-thread count to 1.** They found the flush point's full decision
chain: every veto selects the inline drain, and the *only* route to the threaded hand-off is a
thread-count numerator/divisor pair. Poking the numerator to 1 made the engine's own decision chain
select its own native inline branch. It worked — and then **crashed a loader thread on a save load**,
because the hardware-thread global has *load-path consumers* that have nothing to do with rendering.

**Attempt 2 (shipped) — hook the decision point and reproduce its branch locally.** MinHook the flush
point, reproduce the decoded inline branch inside the detour (copy args to the render manager, stamp the
mode, call the drain through its guarded target), SEH-guarded, falling through to the original when the
manager is null. **The shared global is left untouched, so loaders see the true core count.** The
load-crossing soak then passed on all four transitions — save load, quit-to-menu, new game, and a real
multi-map streaming descent.

> **The rule: poking a shared engine global to change render mode is a load-path landmine. Hooking the
> decision point and reproducing its branch locally is the same effect with none of the blast radius.**

That is a genuine refinement of "drive the engine's own decision" in
[07](07-engine-integration-safety.md): drive it *locally, in a detour*, not by mutating state the whole
process reads.

The rejected alternatives are as instructive:

| Rejected | Why |
| --- | --- |
| The `-onethread` launch arg | **Appeared to work for a whole session, then was falsified — the string is not in the exe at all.** See "the false positive" below |
| Poking a per-client "use render thread" bool | Heap object — must be re-found every boot |
| Poking a `GIsEditor`-class global | 500+ references; crashed the next load (recorded as a dead end) |
| Start-state gating (frame-id / ring-counter) for the deadlock | Ran at full rate and did **not** prevent the hang — falsified twice |
| Watchdog event re-kicks | Detection was reliable, but **kicking a desynced protocol crashes the drain**. Demoted to detect-only |

Two selection criteria worth stealing. When several globals could flip a behaviour, prefer the one with
the **fewest cross-references and the narrowest purpose** (theirs was a 10-reference, single-purpose
static; the 500-reference one crashed). And **detection and recovery are separate problems** — a
watchdog that reliably detects a deadlock has earned the right to *log*, not to act.

BioShock 2, on the same engine tree, **needed none of this** — see "don't port the workaround" below.

### The false positive that survived a whole session

Their `-onethread` launch argument looked like it worked, and the supporting evidence was a hexdump of
pump globals reading zero. It was wrong twice over: **the string is not in the executable**, so the arg
was never parsed — and the hexdump was a *menu-time artifact*, because the pump globals are zero before
the first world load **in every mode**.

> **Verify a mode flag after a world load, and in both states.** A measurement taken before the
> subsystem initializes reads the same as success.

This is the [precondition-vs-result](06-debugging-methodology.md) trap wearing a different hat: they
measured something real, at a moment when it could not distinguish the two hypotheses.

## A serial ticket makes pair coherence checkable rather than hoped-for {#pair-serial}

The section below establishes the rule - replay the base, never re-sample. BL1GOTYVR ships the
mechanism that *enforces* it, and it is small enough to copy wholesale. `[SOURCE]`

1. **Eye 0 snapshots everything**: the OpenXR head pose, **both** runtime eye positions and FOVs, and
   the unmodified game camera state.
2. **Eye 1 restores that same camera state and reuses the exact eye-0 snapshot** - it does not locate
   views again.
3. Each completed draw **publishes a `{pairSerial, eye}` ticket** to the capture path.
4. **Eye textures are submitted only when both captures carry the same serial.**
5. Submission uses **the exact `XrView` pair that was rendered with**, and the projection crop uses the
   same frozen FOV and render aspect as the camera.

**Step 4 is the one that turns a convention into a guarantee.** Without it, pair coherence is a property
you believe holds because of how the code is written; with it, a mismatched pair is *detected* and never
reaches the compositor. The cost is one integer per frame.

**And step 5 is the same rule three projects have now arrived at independently**: submit the views you
**rendered with**, not freshly located ones -
[fear-vr's `pose_fallback`](19-d3d12-and-performance.md#blocking-wait-floor) counts the consumer-side
failure, [Condemned VR's request tickets](19-d3d12-and-performance.md#blocking-wait-floor) prevent the
producer-side one, and this is the same idea applied to the eye pair. **An identity tag turns "is this
still current?" from a timing heuristic into an equality test.**

Their authority discipline is worth the last line: `RenderScene`, render-command multiview and
double-`Draw` hooks are all deliberately **not installed**, so camera pose and projection are applied at
**one authority only**. IPD comes from the runtime in headset mode, with the configured value kept
solely as a desktop-simulation fallback.

## Pair coherence: replay the base, never re-sample

Their pass 2 does **not** re-sample the head pose. Pass 1 caches the final un-eyed camera and applies
−IPD/2; pass 2 replays *that cached base* + IPD/2.

> A Present lands between the two passes, so re-sampling would skew the pair (vertical disparity).

This is the third independent arrival at the same rule ([10](10-graphics-apis.md)): SS2VR latches
rotation across an alternate-eye pair, the BioVRDev mod pair-locks its camera, and this project replays
a cached base. **Any two-pass or two-frame stereo scheme must derive both eyes from one camera sample.**

They also stamp the projection layer with the pose the image was actually rendered from — not the
newest pose available at submit.

### Eye attribution: an explicit tag ring, not inferred parity

Which eye does this Present belong to? Their answer is a single-producer/single-consumer **tag ring**:
the game thread pushes the eye sign at each nested engine submit; the Present tail pops one per Present.
It works because submits:presents are exactly 1:1 in gameplay (live-verified), a ring depth > 2
self-clears at mode boundaries, and **presents with no tag flow mono**, so the other stereo modes are
untouched.

Explicitly rejected: **inferring the eye from present parity** ("breaks on any dropped present") and a
cross-thread mutex handoff ("a lock in the present path").

That rejection is the fix for the failure mode in [10](10-graphics-apis.md) where SS2VR's self-toggling
eye phase desynced permanently after a single skipped fill. A counter that *infers* phase can silently
invert forever; an explicit tag attached at the source cannot.

## Pacing: poll, never wait on a racy engine event — and never wait unbounded

Two pacing lessons, both earned through hangs.

**Drain by polling, not by the engine's waiter.** Before pass 2 they poll the frame-id pair's completion
bits until the pipeline is empty (bounded 20 ms, skip on timeout), because the engine's own event wait
has a **live-proven lost-wakeup race** that hung the game twice. A poll cannot lose a wakeup. The
timeout doubles as the unfocused path: presents stop, and doubling degrades to mono instead of stalling.

**An unbounded `xrWaitFrame` is never worth "insurance".** Their field hang is worth reading in full
because the failure signature is so quiet:

> The user took the headset off, the session dropped FOCUSED → VISIBLE, and the game wedged solid
> (0.11 s CPU over 4 s, 1 running thread, `Not Responding`, kill required) with **no crash, no dump and
> no fault line** — the log simply stopped one line after `xr: pace keepalive while VISIBLE`.

Mechanism: their stall guard skipped the blocking wait while unfocused, *but* let one real paced frame
through every 5 s "as insurance" — and the keepalive timer started at 0, so the **first** unfocused
present called `xrWaitFrame`, which takes no timeout and, with the headset idle, never returned. On
BioShock 2 that call sits on the present thread, so it back-pressured the game thread through the render
command ring and froze everything.

The rules that came out of it:

- Once FOCUSED has been held, unfocused presents **always** skip the wait. Recovery never depended on
  the keepalive — event pumping runs every present above the guard, and returning to FOCUSED is a
  *session event*, not something an app earns by submitting frames.
- **Close any leaked open XR frame before waiting**, because waiting on a begun-but-never-ended frame is
  the other way a runtime blocks forever.
- Worst case without the keepalive is "stays unfocused" (visible, recoverable). Worst case with it was a
  wedged process. When an "insurance" mechanism's failure mode is worse than the thing it insures
  against, delete it.

This belongs next to the OpenXR layer-budget freeze in [07](07-engine-integration-safety.md): both are
**silent hangs with the flat game still alive**, and neither produces a crash dump to work from.

## Don't port a workaround before testing whether the second game needs it

Their BioShock 2 adapter is a natural experiment in porting to a sibling engine, and it produced an
explicit project rule:

> BS2 is NOT bound by BS1's methods. Much of BS1's machinery — the foreground/viewmodel FOV
> counter-modeling, weapon scaling compensation, aim-seam workarounds — exists because of BS1-specific
> limitations, not because it is the right design. Before porting any BS1 compensation machinery to BS2,
> first test whether BS2 needs it at all.

Applied to the single-threading machinery, the first answer was **no** — and later evidence refuted it.
BioShock 2 initially produced `presents/s == 2 × draws/s` on the threaded path, but the Draw tail's real
flush call had disappeared through a link thunk. Longer stereo runs exposed the second per-tick
flag-test-then-`Wait(INFINITE)` handshake losing a wakeup. The shipped cure is therefore a **BS2-local
structural 1t path**, re-derived with BS2's flush point, inline branch and guards; none of BS1's addresses
or globals were shared.

That correction strengthens the rule rather than weakening it: **test whether the defect exists before
porting the cure, but keep testing long enough to falsify a timing-sensitive success.** When the measured
stall finally appeared, the team reused the strategy and derived every implementation detail fresh.

Two more consequences worth copying: BioShock 2 has a **native FOV slider and native dual-wield**, so the
adapter uses those instead of BioShock 1's compensation code; and they **duplicated** discovery tooling
into the second adapter rather than sharing it, keeping per-game addresses strictly separate
("NEVER copy a number between games — same engine tree, different link; derive fresh").

## Architecture: a game-agnostic core behind a capability-based adapter

The seam that makes a second game cheap:

```cpp
struct IGameAdapter {
    virtual uint32_t capabilities() = 0;   // CAP_CAMERA_OVERRIDE | CAP_FOV_WRITE | CAP_CONSOLE_EXEC
                                           // | CAP_AIM_OVERRIDE | CAP_HANDS_ATTACH
                                           // | CAP_SCENE_REENTRY | CAP_HUD_CAPTURE
    virtual bool init(ProcessImage&) = 0;
    virtual void onCalcView(CameraOverride&) = 0;
    virtual bool renderSceneReentrant(const EyeRenderParams&) = 0;
    virtual GameState queryState() = 0;
    // ...
};
```

- **Capability flags mean a partial adapter still runs** — progressive enhancement. A new game can start
  with camera override only and grow.
- **No raw addresses outside `game/<title>/patterns.cpp`.** Every resolved address flows through a named
  symbol table, logged at startup, and mirrored in that game's engine notes *with its derivation method*.
- **The core speaks poses, metres and D3D11; adapters own all engine semantics** — including units
  (metres ↔ Unreal units, FRotator 65536/turn ↔ radians). Core never touches UObject or FName.
- Adapter dispatch is by **host exe name**, and host detection is *silent by contract* — it runs before
  the logger exists, so those functions must never log.
- Unknown host → runs flat with a log line; scan failure → publish the adapter anyway so the overlay can
  show the failure. Fail-soft, visibly.

This is the [lane separation](09-d3d11-openxr-injection.md) principle taken to its conclusion: the
boundary is drawn so that *engine knowledge* sits on one side and *VR plumbing* on the other.

## Build your own in-process frame inspector

RenderDoc is unreliable on 32-bit targets ([06](06-debugging-methodology.md)); their answer is to build
the specific capability they needed, in-process:

**`frame_inspector`** hooks the immediate context's draw and clear vtable slots. When armed it records
one full Present-to-Present frame — render targets and formats, viewports, constant-buffer sizes and
contents, SRV0, and **return-address callstacks mapped to module+RVA** — then writes a text dump and
disarms. Idle cost is *one atomic load per draw call*.

Two details make it better than a capture tool for this job:

- Its own description: *"In-tree replacement for a RenderDoc frame map: the callstack RVAs are exactly
  what the SequentialReentry scene-draw hook needs."* The thing you need to find the scene-draw entry is
  a **callstack**, and an in-process hook gives you one directly.
- It can record **N consecutive present windows**, because "a game-thread arm always opens on the same
  pair phase" — a one-shot dump can only ever show you one eye of a stereo pair.

**`value_scan`** is Cheat-Engine-style narrowing built into the mod, driven through the command-file
seam. One trap it documents is a genuine gotcha: an ini line like `HorizontalFOV=130` with no decimal
point is an **integer** property and is **invisible to a float scan** — hence separate `scan_f32` and
`scan_u32` sweeps.

Its discipline matters as much as its existence: *results are logged, never baked in — anything found
here graduates into `patterns.cpp` with a documented derivation before production use.*

## A closed-loop flat-screen test harness

The strongest answer in this playbook to the slow-headset-loop problem ([08](08-project-process.md)).
Their PowerShell harness lets an automated sweep decide *"did the render change?"* with **no headset and
no human**:

| Tool | What it does |
| --- | --- |
| `boot.ps1` | Launches the game via Steam into **gameplay on the newest save**, dismissing dialogs |
| `game-cmd.ps1` | Writes commands to a **`command.txt` seam the mod polls at 1 Hz**, retrying past the share-lock |
| `game-shot.ps1` | Captures the game window with `PrintWindow` + `PW_RENDERFULLCONTENT` (grabs D3D content on Win10/11) |
| `img-diff.ps1` | Pixel-diffs two PNGs so an automated A/B poke sweep can decide whether the render changed |
| `game-click.ps1` | Clicks at window-relative coordinates matching `game-shot` pixel positions |
| `check-laa.ps1` | Reports whether the exe has `LARGEADDRESSAWARE` (32-bit headroom — see [06](06-debugging-methodology.md)) |
| `decode-framedump.ps1` | Recovers projection tangents and pass clusters from a `frame_inspector` dump |

The **command-file seam** is the keystone and is trivially portable: a plain text file the injected DLL
polls once a second. No console, no hotkeys, no IPC library, and it is scriptable from anything. Combined
with screenshot + diff, it turns "does this poke change the image?" into a loop that runs unattended.

Their `package.ps1` exists for a related reason worth noting — releases used to be hand-assembled in a
session scratchpad, which is exactly the packaging-hygiene failure in [08](08-project-process.md).

## Engine-side writes beat render-side writes

Their single biggest design principle, and it explains most of their architecture:

> **Engine-side writes** (actor transforms, bone matrices) are read by the engine, so attachments and
> effects recompute from them and follow for free. **Render-side writes** (patching a world matrix in a
> constant buffer at draw time) are invisible to the engine, so anything drawn as a separate object — the
> plasmid hand FX above all — stays behind.

That is why they drive the viewmodel by writing **bone matrices** rather than patching render matrices:
the engine recomputes the weapon attachment and muzzle effects from the bones. Render-side patching is
reserved for things with no engine-side handle at all.

Three findings shaped that choice, each live-proven:

- **The renderer draws *attached* actors from the attach matrix and ignores their own transform.** Writing
  the weapon actor's location/rotation at full frame rate moved nothing on screen.
- **Both arms are one skinned mesh on one actor**, so a single actor transform can never decouple left
  from right — the same shared-root wall SOMA hit ([02](02-viewmodels-and-hands.md)).
- **The actor's pivot is the eye anchor**, with the gun about 1.2 m out, so any rotation swings the weapon
  on a long lever arm. "A slight pivot breaks everything."

Their bone-write protocol is worth copying wholesale: write from the camera detour (which runs *after* the
engine's tick, so you are last writer), **clear the skeleton's dirty flag** so a render-side
evaluate-if-dirty cannot rebuild your pose in the same frame, detect engine re-evaluation by comparing an
anchor bone against your last write, and on disable **set** the dirty flag so the engine restores itself.
And a hard-won constraint: **never scale anything in the wrist chain** — the attachment path
inverse-decomposes chain scale, so scaling the wrist to shrink a hand makes the attached weapon explode to
fill the screen.

## Write script properties by name through the console seam

The highest-leverage single hook they found: the engine's own console `SET <class> <property> <value>`
handler, reached through the client's `Exec` dispatcher.

> This makes **any script property writable by name — no offset, no bitmask, no reflection walking**. The
> engine resolves the property itself.

They use it to disable the flat crosshair (`set shockplayer breticledisabled true` → the HUD pushes a
"no reticle" type to the Flash movie every frame, and nothing fights the write). Because it writes the
class *default* as well as instances, objects spawned after a level load inherit it — which quietly solves
the "my setting doesn't survive a load" problem.

Caveats they record: it writes *all* instances of the class plus the default (fine for player singletons),
and not every console verb survives — `NextWeapon` through the same chain **faults**, because stock UE2
console weapon switching was never wired up in this build. As always, the verb existing is not the same as
the verb working ([03](03-input-and-locomotion.md)).

## Foreground FOV: the viewmodel is a separate scene with its own lens

Their longest failure arc, and a clean generalizable diagnosis. The viewmodel is rendered as a **separate
foreground scene with its own projection** — a fixed ~60° 4:3 spec regardless of the world FOV. A two-shot
discriminator proves it in seconds: park the hand, change the world FOV, and see whether the gun holds its
screen size while the world rescales.

The geometric consequence is that a world-fixed hand at view angle θ renders at `atan(k·tanθ)` with
`k ≈ 2.1` — invisible in flat play at θ≈0, but **10–20° of over-pan under head-look**, plus an oversized
gun and a FOV slider that doesn't rescale the hands.

They spent three sessions **counter-modelling** that transform — analytically solving where to put the
bones so the wrong lens lands them right — and it kept passing flat acceptance while the in-headset percept
refused to move, "every session surfac[ing] one more unmodeled term." The pivot that worked:

> **Patch the foreground pipeline's *inputs*, stop countering its outputs.**

The foreground FOV turned out to be a live field on the player controller, consumed every frame; writing
the world-equivalent value re-lenses the entire rig the same frame, with no model at all. The retired
counter-model was itself later found to be the cause of a ±90° laser-vs-gun drift — **three sessions of
compensation machinery had become the defect.** It now ships default-off.

Two constraints bound what remains: the foreground eye "dollies back" by a FOV-coupled amount, and at the
matched lens that offset **cannot be countered through bones**, because pulling the anchor toward the
camera puts it behind the world camera and **the engine culls actors by origin** — the whole rig blanks.
(That also sets a floor: a hand closer than ~23 cm to the face can blank the rig.)

## Screen classes share one fingerprint: no world pass at all

Loading screens, the hack minigame, and the main menu are all **the same thing** to the renderer: a run of
non-indexed UI draws with **zero `DrawIndexed`** — no world pass whatsoever. (Their hack minigame: 322 UI
draws, 0 indexed, *even though the scene build keeps running* — it just draws nothing.) One detector —
"UI draws present, no world-pass vote leader," with hysteresis — routes all three to the readable quad.

The in-headset lesson attached to it: **these screens must be head-locked, not world-locked.** Their first
hack-minigame attempt pinned it at the recenter facing and was wrong in the headset; riding the head-locked
view space like the pause panel was "amazing, works as intended."

Two second-order costs they document honestly: the menu also trips the screen-only state, so their deadlock
watchdog is inert there; and a **loading screen honestly satisfies a deadlock signature**, which is why the
watchdog had to learn to stand down (see below).

## Cutscenes: the claim, not the pixels, was broken

Both plausible hypotheses about their bathysphere cutscene were **disproven by measurement** — the camera
function keeps firing the whole ride, the view state never changes, and the renderer demonstrably consumes
their camera writes (world-pass camera position matched their heartbeat to the unit). Eye offsets were
reaching pixels; disparity existed.

The actual defect: **the scene renders its own ~104° FOV while the option and the submitted projection
layer both claim 130°.** A 26° claim-over-render mismatch warps the geometry (the "fisheye") and
mis-registers the two eyes enough to break fusion — with correct pixels underneath.

> Fix the **claim** to the **measured** value. Do not assume the projection you submit matches the
> projection the engine used, and instrument the difference ([09](09-d3d11-openxr-injection.md)).

Their cinematic classifier ended up as four independent detectors (strict view-state, publish staleness,
FOV mismatch, screen-only) with hysteresis — any of which routes the frame. And the engine's *own*
letterboxed cutscenes are a different class again: the bars are **unpainted clear**, not draws, so there is
nothing to classify — detection has to sample pixel columns, with a **full-black fade guard** so a fade to
black doesn't read as maximal letterbox.

## The trilogy era: what generalised, and what was BioShock 1 all along {#the-trilogy-era}

Adding **BioShock Infinite (UE3 build 6829)** to a codebase built for **Unreal 2.5 Vengeance** turned the
project into a natural experiment. Everything above had been proven on one engine generation; the second
generation says which parts were laws and which were local conditions. `[SOURCE]`

**The delivery vehicle survived unchanged.** Infinite imports `XINPUT1_3.dll` **by ordinal 2 and 3**, so
the existing proxy works verbatim across both engine generations, and BS1's IAT-hijack lane transfers
too. Note also that `d3d11`/`dxgi` are **not imported at all** — they are loaded dynamically, one more
instance of [import tables lying](reverse-engineered-route.md#re-01) about the active graphics API.

Infinite differs from its siblings where it matters for anchoring: **x86 with a fixed image base of
`0x00400000` and no ASLR**, unlike BS1 and BS2.

### The single-threading machinery was target-specific, not a law

This is the correction the second engine bought, and it revises the
[re-entrancy section](#making-a-single-threaded-engine-re-entrant) above.

BS1 and BS2 both ultimately needed structural single-thread rendering, but **each adapter owns its own
seam, constants and guards**. Infinite did not. Their standing instruction is therefore: **test threaded
first, port nothing from a sibling's single-threading kit until a measured stall demands it, and then
derive the target's cure fresh.**

Infinite's substrate was already threaded and ring-buffered, and doubling ran clean on it:

```text
draws/s = 90    second draws/s = 90    presents/s = 180    camera replays/s = 90
second call cost 80-170 us    zero faults    15-minute armed soak green
```

**A mitigation that was expensive on the first target is a hypothesis on the second**, not a
prerequisite. Carrying it forward untested would have cost sessions and hidden the fact that it was never
needed — the same discipline as
[not porting a workaround before testing whether the second game needs it](#dont-port-a-workaround-before-testing-whether-the-second-game-needs-it).

### Two rules from the BS2 freeze, both general

**The fix for a race is removing the wait, not narrowing it - and the proof is a counter, not a soak
duration.** They did not tune the handshake timing. They made the wait *structurally unreachable* and
then measured that its entry counter was zero by construction. A soak surviving ten minutes tells you the
race did not fire; a counter reading zero tells you it cannot. `[SOURCE]`

**A watchdog episode the game recovers from is a load, not a wedge - permanence is the verdict, the
watchdog is the cry.** Save loads and respawns legitimately stop presents for seconds, so a stall
watchdog fires on them. Rather than teach the core to distinguish loads - trading diagnostic stacks for
silence exactly where stacks are cheapest - every episode gets a recovery watch: **log growing means
load, counted and reported; silence means the freeze.** The lesson was bought by a kill-on-fail switch
killing a healthy game the moment the user finished loading a save into it.

### Finding the re-entry root on UE3, and the negative that came with it

The scene-build root is the **viewport draw** (`canvas -> client draw -> present kick`), derived live from
a call census, a stack scrape and vtable probes rather than from UE3 knowledge.

The recorded negative is as useful as the find: **doubling the client draw alone produced no second
present and a ring skew.** The seam is the viewport draw, not the client draw one level in — a
distinction invisible from a symbol name.

### Deny-by-default re-entry, gated on the caller's return address

Their second pass is armed against a **known gameplay caller's return RVA** — a call census identified
that site as the per-tick dispatcher, and any other caller is refused. It is combined with four more
gates: camera-silent for 400 ms, present-stall, teardown, and poison.

**The gate was observed refusing a foreign caller live**, which is the only evidence that matters for a
deny-by-default guard.

PreyVR supplied a sharper reason to reach for this than defence-in-depth. Their re-entry candidate,
`C3DEngine::RenderWorld`, is **virtual with zero direct call sites** — every call arrives through a
global interface pointer. A second pass they drive is therefore *indistinguishable from the engine's own
by signature alone*, and the caller is the only discriminator available. `[STATIC]`

**Generalise that as the selection rule: when the function you re-enter is dispatched virtually through a
global, gating on the caller is not the strongest option, it is the only sound one.** Gating re-entry on *who called you* rather than on *what state you think you are
in* is the strongest form available, because a load path that reaches the same function is exactly the
case that corrupts state. See [HOOK-002](pattern-catalog.md#hook-002).

### One prediction per game tick, or the pair shears

Their pair pacing rule is one `xrWaitFrame`, one locate and one prediction per game tick, with a named
failure mode:

> Submitting the two eyes of a pair with poses located **a compositor period apart** produces
> motion-dependent shear.

And the [replay-don't-re-sample rule](#pair-coherence-replay-the-base-never-re-sample) above was
re-confirmed on the second engine with the mechanism spelled out — **a Present lands between the two
passes**, so re-sampling the camera skews the pair into vertical disparity. Infinite uses an absolute
replay with a 100 ms staleness guard.

### A third title, a third FOV contract

BioShock 1's FOV option is a true horizontal. BioShock 2's is a 16:9-referenced horizontal. **Infinite's
rendered lens is vertical-referenced** (`tanV` between 0.4317 and 0.4933, `tanH = tanV x aspect`,
verified at two aspects), while its later live camera-degrees lever is horizontal at a **fixed 16:9
reference**: `tanV = tan(deg/2)/(16/9)`, then `tanH = tanV x actualAspect`. These are compatible
descriptions of the same lens at different ownership boundaries, not interchangeable field semantics.

Three titles, three ownership/encoding contracts, one publisher, two engine generations.
[CAM-004](pattern-catalog.md#cam-004) was written from the first two; the third makes the point
unarguable — **the FOV law, its owner and its reference aspect are per-title evidence, exactly like an
address.**

Their `claimRatioH` instrument (see [the substitute runtime](09-d3d11-openxr-injection.md#substitute-runtime),
which this project built) was re-baselined for Infinite at **0.5576** against a symmetric 54-degree
reference eye at slider minimum. The later live lever made the claim derive from the degrees value on
each dispatch through the fixed-16:9 law, leaving the decoded lens as an independent audit.

### Order the ladder by dependency, and pull stereo forward

Their Infinite roadmap was **restructured mid-project** to follow the order BS2 had proven: reach
in-headset-accepted stereo first, then do lens and resolution polish driven by what the headset actually
shows. The justification is stated as a cost already paid:

> On BS1 the resolution/FOV question could not be judged at all until stereo ran, and **two sessions were
> lost to mono screenshots that measured the wrong thing.**

Two rules worth taking whole:

- **Order milestones by engineering dependency, not by desirability.** User priorities appear as
  *acceptance criteria*, not as ordering.
- **Every milestone's "done when" is a measured downstream effect, never a confirmed write.**

When they renumbered the ladder they published a **renumbering map** so older session logs stay readable.
A ladder that is reordered without one silently invalidates its own history.

### Practical multi-game constraints

Two operational details that only appear once one codebase serves several games:

- **One game owns the headset at a time.** Running two of the three simultaneously is forbidden and
  enforced by a preflight script — building, installing, packaging and log-tailing are explicitly exempt,
  because those must keep working while a game runs.
- **All three ship from one branch**, with the old per-game branches marked historical and explicitly
  not to be used as a starting point. Per-game branches are a merge debt that grows with each title.

## A fourth implementation, and what synthesized stick input costs {#square-deadzone}

BioShock-Remastered-VR (BioVRDev) is the fourth independent VR implementation of a BioShock title in this
survey and the second on the Remastered build. It reaches the same engine by a different route - a
`dxgi.dll` proxy hooking `IDXGISwapChain::Present`, `APlayerController::eventPlayerCalcView` and the D3D11
draw path - and its most transferable findings are about **input**, which nothing else here covers in this
much depth. `[SOURCE]`

### A square deadzone distorts direction, not just magnitude

Any mod that redirects walking synthesizes a stick vector. If the game's deadzone is **per axis** rather
than radial, the engine shrinks each component independently, and a rotated vector comes out pointing
somewhere else:

> The game's movement deadzone is **square** -- per axis, 0.225, straight out of its own binding file.
> Rotating the stick to redirect walking moves magnitude between the two axes and the game then shrinks
> each one independently, which distorts the **DIRECTION** by up to ~11 degrees and collapses it to pure
> strafe once the forward lane falls under the threshold.

The signature is diagnostic: **saturation at exactly +-90 degrees** (the forward component has fallen
under the threshold and been zeroed), a residual that **inverts with direction**, and error that is
**worst near 90 and least near 0**. If you see those three together, look for a per-axis deadzone
downstream.

The inverse is exact. For a desired unit direction `u` and magnitude `m`, send:

```
send_i = sign(u_i) * ( |u_i| * m * (1 - d) + d )
```

after which the game recovers `u_i * m` - direction exact, magnitude exact. A zero component stays zero,
so a pure-forward push is untouched. Note the shape: **direction and magnitude are treated separately,
because only the direction is being corrupted** and the magnitude is what the player asked for.

**Invert the conditioning; do not edit the config that sets it.** Their reasoning against the apparently
simpler fix generalises: the binding lines carry several bindings each - `XENON_LTHUMB_XAXIS` also holds
`Axis xLean DeadZone=0.4` - the file has multiple binding sections, and **the game rewrites it at exit**.
String surgery there risks breaking the controls outright, for a value you can simply invert. See
[INPUT-004](pattern-catalog.md#input-004).

### The response curve near full deflection is a cliff, and it is why turning feels random

Measured, on the game's own turn rate:

| Stick axis | Turn rate |
|---|---|
| 0.98 | ~105 deg/s |
| 0.99 | ~140 deg/s |
| 1.00 | ~200 deg/s |

**The same push landing 2% differently doubled the speed.** Their fix is not to model the curve but to
stay off it - remap the axis into a range that excludes the cliff (`turnAxisMax = 0.95`), trading top
speed for repeatability. A tracked thumbstick reaches full deflection far more often and far less
deliberately than a gamepad thumb does, so a curve that was acceptable flat is not automatically
acceptable in VR. See [INPUT-005](pattern-catalog.md#input-005).

### The config write-back loop, which no amount of in-game setting escapes

> The game reads its config at startup and rewrites it on exit with whatever it **actually ran at**, which
> is why a fresh install starts fullscreen at your desktop resolution and can never correct itself.

**A value the game overwrites with reality at exit cannot be fixed from inside the game.** If VR needs a
resolution, FOV or window mode the game will not accept at runtime, the write has to happen **before the
process starts**. Theirs is a setup script that edits fourteen values across eleven settings through the
same Windows profile API the game itself uses, backs the file up first, and restores the backup if the
result looks wrong. See [CFG-003](pattern-catalog.md#cfg-003).

### Two smaller findings worth carrying

- **The thing you attached the weapon to is itself animated.** Their weapon drifted and "breathed" in the
  hand, and a calibrated crosshair was impossible, because the game animates the arm the gun hangs off.
  Freezing that idle animation while the weapon is held fixed it. Before debugging a pose you compute,
  check whether its parent is being animated underneath you.
- **Grip offsets did not scale with resolution or FOV, and the scaling law was ruled out** rather than
  assumed - which is why their known-issues list says re-tune rather than offering a formula. Record
  ruled-out laws; they stop the next person deriving one.

Their reticle deserves a line for how the proof was designed: **aim, crosshair and the actual shot all
derive from one value**, which turns calibration into an exact test - fire at a flat wall and adjust until
the dot sits on the bullet hole. A shared source makes the check exact instead of a judgement call.
Building the thing so its correctness is observable is cheaper than inventing a test for it afterwards.

## Assorted findings worth keeping

- **Square your backbuffer.** They instruct users to set a roughly **square** game resolution (e.g.
  2750×2850) rather than 16:9, because the eye render target is sized from the backbuffer and headset
  panels are near-square: at 3840×2160 on a Quest 2 only ~54% of the width is inside the FOV. A square
  buffer with *fewer total pixels* is sharper in the headset and faster. Their startup log prints the
  resulting `game hfov / aspect` so the user can see the waste.
- **Hook implementations, not script thunks.** The engine has a readable symbol table for name-based
  natives (a registration string → `.data` entry → implementation pointer), which resolves aim symbols
  with no hardcoded addresses. But hooking all four aim *script thunks* caught **zero** calls while
  shooting, because C++ callers go straight to the implementation. (See
  [06](06-debugging-methodology.md) on proving a hook ran, and [11](11-re-anchoring-and-discovery.md) on
  the engine's own symbol table as an anchor.)
- **Substitute early enough to keep the engine's own behaviour.** They substitute aim at
  `GetPerfectFireStart` rather than at the spread function, so the engine still applies its own
  `ApplyAimError` afterwards — a shotgun still spreads. Substitution is **value-driven** (each out-param
  the engine filled with a position gets the hand's origin; each direction gets the hand's direction;
  zeros are left alone) because the same function's out-param order differs between the two signatures.
- **Gate by the engine's own ownership check.** Their aim override compares the weapon's owning pawn /
  the ability's instigator against the player vtable — *the same check the engine makes itself* — so AI
  fire keeps its own aim.
- **One ray, one algebra.** Three different algebras for "where the gun points" (rotator adds in game
  space, yaw/pitch adds in a spherical decomposition, and a quaternion composed in the controller's local
  frame) agreed only at the pose the user tuned at: a sweep measured up to **28.21°** of ray-vs-barrel
  divergence at rolled poses *with identical trims*. All three now run one implementation, as pure
  functions shared by production and the test sweep, with the acceptance gate "sync-check ≈ 0 at every
  orientation." Euler adds after conversion are banned outright — "only correct at one orientation,
  live-proven *goes crazy*."
- **A degenerate basis hides in a cross product.** Their laser's old right-vector built from
  `direction × worldUp` degenerated near vertical and *silently dropped* the right/up offsets there; the
  fix builds right from the ray's yaw angle so it stays defined at any pitch.
- **Put the laser in the compositor, not the scene.** XR quad layers are per-eye correct for free, need
  no engine hook, and nothing the renderer can clip or depth-test away. The accepted cost is a real
  verification gap: quad layers are invisible to flat-screen testing.
- **Generate the version string.** A hand-edited `#define` shipped "0.1.0" across three releases, making
  an external crash report unattributable and costing a session to resolve by PE-timestamp forensics. It
  now comes from the build system, stamped with `git describe --tags --always --dirty`, and the startup
  log prints the DLL's own PE `TimeDateStamp` plus an environment line (OS build, cores, RAM, host LAA).
- **A minimal minidump is not enough.** `MiniDumpNormal` showed *that* a worker thread jumped into game
  heap but not what smashed the slot. They now capture indirectly-referenced memory, data segments,
  thread data and handles, plus integer registers, a symbolized return-address chain, and an explicit
  read/write/DEP-execute classification of the access violation — with a **re-entrancy guard, because a
  fault inside the dump writer used to recurse.** Dumps grew from ~150 KB to a few MB; accepted.
- **A loading screen satisfies a deadlock watchdog honestly.** Their re-entry watchdog (stereo on, game
  thread inside a hooked call, builds and presents frozen for 1.2 s) fired on the first level load and
  auto-disabled stereo, leaving the user in flat-per-eye VR. The watchdog now stands down while the
  screen-only path is active, records that *it* caused an auto-off, and re-arms only once the game thread
  is outside the detours for 500 ms — and a deliberate user "off" can never be resurrected by it.
- **Every new render lever ships default-off** until the acceptance ladder is re-run in the new regime
  and judged in the headset, because a new lever can silently invalidate an existing headset-approved
  calibration.
