# Input & Locomotion

Getting controller input into a game that only understands mouse + keyboard. There's a ladder
of techniques from crude to clean; know where each rung lands you and that **exactly one rung
drives any given control**.


## Measure gesture velocity in ROOM space, or walking becomes a gesture {#roomspace-velocity}

A hand-speed threshold read from world-space controller poses fires when the **player** moves, not
when the **hand** does. Walk forward briskly and every velocity-gated gesture in the mod is armed.

PLANCK names the fix in the setting itself: `yankRequiredHandSpeedRoomspace`. **The velocity that
means intent is the hand's velocity relative to the play space**, with the player's own locomotion -
stick movement, teleport, vehicle, animation-driven motion - removed first. `[SOURCE]`

This applies to every speed-gated interaction the fleet is likely to build:

- HIGGS separates a quick swipe that loots from a slow approach that grabs by hand speed;
- SS2VR's `manualReload` gates on a downward *displacement*, which has the same exposure over a long
  enough window;
- any throw, swing, yank, shove or melee-velocity check.

**Displacement thresholds have the same problem as velocity ones**, and are easier to get wrong
because the window hides it: a 0.45-unit downward pull is unambiguous over 200 ms and meaningless
over two seconds of walking downhill. Where a gesture is a displacement, either bound its duration or
measure it in room space too.

The cheap check: perform the gesture standing still, then walk while deliberately holding the hand
still relative to your body. The second must not fire.

## A stroke grammar multiplies one button into a menu you never open {#stroke-grammar}

VR controllers run out of buttons long before a mod runs out of actions, and the usual answers are a
radial menu (a modal interruption) or a chord (unlearnable). VRIK's answer is neither. `[SOURCE]`

**One gesture button, plus a stick or trackpad stroke, gives thirteen actions per hand:**

- the press alone;
- press **+ Up / Down / Left / Right / Forward / Back** - six single strokes;
- press **+ Up,Down / Down,Up / Left,Right / Right,Left / Forward,Back / Back,Forward** - six
  out-and-return strokes.

Twenty-six actions across two hands, with **no menu, no dwell and no visual**, because the strokes
are cardinal and the hand already knows where the stick is. The gesture button itself is rebindable
across nine physical inputs (thumbstick press, trigger, grip, X/A, Y/B, trackpad variants), so the
grammar survives a controller that lacks any one of them.

Three details that make it work:

- **Blocking the game's own binding.** A gesture button also means something to the game, so VRIK
  optionally suppresses that input for half a second when a gesture starts - and, per
  [HAND-013](pattern-catalog.md#hand-013), replays it if no gesture matched.
- **Degrading by controller capability.** Hands animate from capacitive touch sensors where they
  exist; where they do not (Oculus controllers have no grip touch), a compatibility mode synthesises
  the fist from a top button plus trigger. **The fidelity degrades, the feature does not disappear.**
- **Palm orientation as a trigger.** VRIK shows the compass on *"left palm points upward"* - checking
  your wrist. A diegetic, zero-button UI gesture, and the same idea works for any glanceable readout.

## The input ladder (crude → clean)

1. **Synthetic key presses.** Translate stick/buttons into `SendInput` keyboard events. Works
   anywhere, instantly. But it's digital (no analog speed), it leaks into anything listening
   for keys (the in-game console, chat, rebind screens), and it's obviously a hack.
2. **Native action/command dispatch.** Most engines expose console verbs or a command system
   (`+forward`, `+jump`, `+crouchhold`, `fire_weapon 1`). Driving *those* gives you the real
   in-game action with correct semantics — but held analog movement through digital verbs is
   still on/off, not proportional.
3. **Virtual gamepad.** Attach a virtual controller *inside the game process* (e.g. SDL's
   virtual-joystick API if the game ships SDL; ViGEm system-wide otherwise) and feed it the
   real analog axes. The engine sees genuine controller hardware → true analog speed, correct
   prompts, no key leakage. Best general-purpose answer **if the game reads gamepads at all.**
4. **Native axis-state calls.** Reverse the engine's analog movement-state setter and call it
   directly with the stick value on the game thread. Truest fidelity, most fragile, most RE
   work. Reserve for when 1–3 genuinely can't deliver.

Climb only as far as you need. Most projects live happily at rung 3 for movement and rung 2
for discrete actions (jump/crouch/fire/use).

- *SOMAVR (rung 4 done right, and the value of live tracing):* Frida tracing proved the native analog
  owner is a **player-helper sub-object at `playerRoot+0x110`, not the root pointer** — physical `W`
  calls the analog setter on that helper with analog type `1`, reaching `iCharacterBody::Move`. Once
  the *exact* owner and semantic path were confirmed, controller locomotion queues a controller-relative
  analog vector into that path; synthetic keys survive only as an authored-state/failure fallback. The
  same trace also found an earlier readiness check was reading the *wrong object* (`root+0xc8` instead
  of the helper's `+0xc8`) — a reminder that "close pointer, wrong object" fails silently.
- *BioshockVR (rung 3, XInput):* the working movement/turn route is the engine's native **XInput**
  bridge. `SendInput`-style synthetic mouse turn reported `status=sent` with accepted Win32 events and
  the player still didn't rotate — a clean demonstration that the higher rungs silently no-op when the
  engine isn't listening on that channel.

## What seven shipped mods actually did

The rest of this playbook is drawn from projects still in flight. This section is different: it is a
source survey of **six shipped, publicly played flat-to-VR mods plus one generic injector**, chosen
because their *defaults* encode what survived contact with real users rather than what someone reasoned
their way to.

Surveyed: **JKXR** (Jedi Outcast/Academy, idTech3-derived), **TheDarkModVR** (idTech4-derived),
**GTFO_VR_Plugin** and **RoR2VRMod** (both Unity, but different modding frameworks and different camera
perspectives), **BendyVR** (Unity), **CSVR** (GoldSrc — partial: its VR code lives in an engine submodule
not present in the checkout), and **UEVR AFW** (the generic Unreal injector).

### Every one of them fed the engine's own input funnel. None built a parallel one.

Seven for seven, in seven different ways — and this is the strongest single result in the survey:

| Mod | How synthetic input enters the game |
|---|---|
| JKXR | Reuses the engine's **disused `CL_JoystickMove()` slot**, adding VR stick output onto whatever the keyboard already wrote, then clamping once |
| TheDarkModVR | Injected **as if it were a gamepad** — same `axis[6]` array, same action list, same per-tick call site |
| GTFO | Harmony **postfix** on the game's own `InputMapper.DoGetAxis/DoGetButton*`, merging `+=` and `\|\|` |
| RoR2 | **Registers as a Rewired hardware controller** and pushes values through `SetAxisValueById` |
| BendyVR | Harmony **prefix** on the game's `PlayerInput.MoveX/MoveY/Attack/...` accessors |
| CSVR | Leaves `usercmd_t` and the whole prediction path **byte-for-byte stock**; only what feeds it changes |
| UEVR | **Emulates XInput** — hooks `XInputGetState` and writes resolved action state into `XINPUT_STATE`, so the game believes a real pad is connected |

The lesson is not any one mechanism. It is that **the shipped answer is always "find the channel the
engine already listens on"** — a disused joystick slot, a gamepad array, an input-abstraction method, a
device registry, a usercmd, an XInput report. The ladder at the top of this chapter ranks techniques by
fidelity; this survey says the *entry point* matters more than the rung.

JKXR is the most quietly clever case: discrete VR actions are routed through **`Cbuf_AddText`**, so every
button press becomes literally the same console string a keybind would produce (`"+attack"`). Every
downstream system — demo playback, server-side checks, other mods — needed zero changes to understand VR
input.

### Interaction: repoint the engine's existing ray

Same story, and it is worth stating as a rule because three mods found it independently:

- **GTFO** replaces `FPSCamera.UpdateCameraRay` and writes back into the game's *own*
  `CameraRayPos/Collider/Normal/Object/Dist` fields — so native interaction prompts, pickups and doors
  inherit controller aiming without knowing anything changed.
- **RoR2** assigns `body.aimOriginTransform = dominantHand.currentMuzzle.transform`, repointing the
  `CharacterBody` field all native targeting reads.
- **TheDarkModVR** redirects the existing frob raycast at a single branch point (`GetFrobPos`); its
  `Grabber` class needed **zero** VR-specific changes.
- **JKXR** doesn't raycast at all — it triggers the same `+use` the keyboard game used, because that
  game's interact was already proximity-and-facing based.

**UEVR is the instructive exception:** it ships *no* generic grab/interact system, by design, because that
knowledge cannot be inferred from an unknown title. If you are hand-writing a mod for one known game, this
is precisely the work only you can do — and precisely where copying a generic tool's architecture would
cost you.

### The defaults these mods shipped

| | JKXR | TheDarkModVR | GTFO | RoR2 | BendyVR | UEVR |
|---|---|---|---|---|---|---|
| Default turn | **snap 45°** | — | **snap 60°** | **snap 45°** | **snap 45°** | smooth |
| Turn re-trigger delay | — | — | 0.25 s | 0.33 s | — | — |
| Teleport locomotion | absent | absent | **absent** (0 hits) | **absent** (0 hits) | config exists, **dead** | stub, unused |
| Comfort vignette default | **off** | on (camera-delta driven) | **off** | **on** | — | **absent entirely** |
| IRL crouch default | off | — | **on** (115 cm) | — | — | — |
| Roomscale vs seated | runtime recenter | — | no seated option | **roomscale** default | — | roomscale off |

Three things fall out of that table:

1. **Snap turn is the shipped default nearly everywhere** — the exception being UEVR, which cannot know
   the game. If you are choosing one comfort default, this is the one the field converged on.
2. **Nobody shipped working teleport locomotion.** Two mods have zero occurrences of the word in their
   entire source; two more have a config entry or an action stub with **no implementation behind it**. For
   action-paced games, smooth locomotion plus snap turn is what actually shipped.
3. **The conservative pattern is: cheap proven comfort ON, experimental comfort OFF.** Snap turn on;
   vignette and IRL crouch off more often than on. TheDarkModVR goes furthest — its motion-controller
   input ships behind `vr_useMotionControllers` defaulting to **0**, labelled "wip" in its own help
   string. Even in a released VR mod, controller *input* was considered less production-ready than HMD
   *rendering*.

### A correction to this chapter's own advice on arbitration

Elsewhere this chapter recommends arbitrating physical pad against synthetic VR sticks with a **bounded
recency window** (~250 ms), drawn from BioshockVR. The survey does not support that as the default answer.

**Six of the seven shipped mods do no per-frame arbitration at all:**

- GTFO merges additively and never suppresses real input.
- JKXR adds VR onto keyboard output and clamps once — "arbitration by saturation."
- RoR2 registers as a device and lets Rewired's own last-active-controller semantics decide.
- TheDarkModVR overwrites the gamepad axes (last-writer-wins), on the assumption the two are mutually
  exclusive in practice.
- BendyVR **hard-zeroes** the mouse axes rather than arbitrating — elimination, not priority.
- CSVR's arbitration, whatever it is, happens in an engine layer that never touches prediction.

Only **UEVR** uses a time-windowed heuristic — and it needs one precisely because it cannot know the
title, the input scheme, or whether a real pad is even in use.

**The revised rule: a recency window is what you need when you cannot control or predict the competing
input source. A single-game mod usually can.** Prefer, in order: eliminate the competitor (BendyVR), enter
the engine's device layer and inherit its arbitration (RoR2), or merge additively where the semantics are
safe (GTFO, JKXR). Reach for a recency window when none of those apply — not first.

### Two warnings the survey produced for free

**A shipped default is not evidence a feature works.** Two mods independently ship a user-facing,
documented, defaulted config entry whose implementation is absent: RoR2's `AimStabiliserAmount` (default
0.5) has its entire consumer commented out, and BendyVR's `Teleport` setting has **zero call sites**. Both
shipped. A one-line CI check that every config key is read somewhere would catch this class outright, and
it matters doubly here — a config file is exactly the artifact someone later mines as evidence of "what
they chose."

*Swat4-VR built that check on reading this, and it immediately found **10 of its own 15 keys had no
consumer**. They were forward declarations for unreached milestones rather than bugs — which is the common
case, and why the fix is not deletion. Their rule is worth copying exactly: mark the key `UNIMPLEMENTED` in
the **struct** and `[NOT IMPLEMENTED]` in the **shipped template**, and have the checker demand **both** —
because marking only one is precisely what misleads whoever reads the other.* If you have a config
whitelist, this is a half-hour of work with a startling hit rate.

**Put your settings in the game's own options UI.** GTFO registers its BepInEx config into GTFO's native
settings system; RoR2 generates a settings page by reflecting over its config dictionary. Both decided a
text file was not good enough for a shipped mod, and both did it without much machinery.

## Locomotion: puppeteer the engine's native movement, don't reimplement it

VR locomotion (teleport, blink, physical climbing) is where the [drive-the-engine's-own-systems](07-engine-integration-safety.md)
rule pays off most, because the engine already knows how to move the player *correctly* — cell
relocation, gravity, AI awareness, mantle rules — and reimplementing that fights the engine forever.

- **Teleport: reuse the engine's atomic player-move primitive, and find it via the debug console.** Most
  engines expose one "relocate the object properly" call. (*SS2VR: `IGameTools::TeleportObject`, exposed
  to script as `Object.Teleport` and driven by the remaster's own debug `teleport` console command — so
  typing `teleport $10,0,0` validates the entire feature end-to-end before you write a line of code.*)
  The primitive typically does **no destination validation** (SS2's literally carries a `// TODO: figure
  out if this fits in the world`), so a cheap caller-side validator — floor ray down, two headroom rays
  for crouch/stand clearance, reject steep normals, arc clamped — is your job, plus an origin-`(0,0,0)`
  guard so a bad read can't warp the player into the void. For ladders, snap the landing to the far
  platform and let residual stick-walk into the ladder trigger native auto-climb for free.
- **Physical climbing: latch the native climb *state* and feed it stick input.** Native climb is usually
  a **constraint regime, not an animation** — while it's active, ordinary movement input already slides
  you along the constrained surface. (*SS2VR (`phclimb.cpp`): hand-over-hand = convert each frame's hand
  world-delta into virtual-stick input while the native climb is latched; no position writes, no physics
  fights, and native exit/mantle keep working.*) This "puppeteer the native state" pattern beats
  UEVR-style direct position drive, which fights gravity/capsule/fall-state and loses the free mantle.
  Mantling is often a first-class engine state you can drive too (SS2's `CheckMantle`: headroom +
  forward-clearance + standable-surface raycasts); locate these functions by their warning strings
  (`"BreakClimb: %s has no active physics models"`). Some capabilities are compiled out — SS2's wall
  climbing is dead code behind `if(FALSE) // don't climb on walls, spidey`.

## The double-driving trap (read this twice)

If two paths drive the same control, the symptoms **never** look like "two inputs." They look
like:

- Movement that's mysteriously too fast (two lanes summing). (*SS2VR: keyboard-WASD fallback +
  virtual gamepad both driving = "ubermensch speed" that wasn't all the cheat.*)
- Jitter or stutter (two lanes fighting at different rates).
- "Broken thresholds" or "deadzone doesn't work" (one lane ignores the gate the other respects).

**Rule:** when you enable a higher-fidelity lane, *actively suppress* the lower one for that
specific control. And gate per-control, not globally — see the next trap.

The trap, concretely. Both paths are individually correct, which is why it survives review:

```cpp
/* BROKEN: the engine still reads the physical stick while you also inject
   movement. Inputs ADD -- the player moves at double speed, or fights
   themselves when the two disagree. */
void TickMovement_Broken(const XrInput& in) {
    InjectMoveAxis(in.stick.x, in.stick.y);      // our lane
    /* ...and the game's own input poll is still live... */
}

/* FIXED: suppress at the SOURCE the engine reads, and prove the suppression
   with a counter rather than assuming it. */
struct MoveLane {
    bool     engineInputSuppressed = false;
    uint64_t injected = 0, engineLeaked = 0;
};

void TickMovement(MoveLane& lane, const XrInput& in) {
    if (!lane.engineInputSuppressed) {
        lane.engineInputSuppressed = SuppressNativeMoveAxis();   // zero it at the read site
        if (!lane.engineInputSuppressed) return;                 // do NOT inject alongside
    }
    InjectMoveAxis(in.stick.x, in.stick.y);
    ++lane.injected;

    /* The check that catches double-driving: read back what the engine
       actually got. Nonzero native axis while we are injecting == both lanes live. */
    if (ReadNativeMoveAxisMagnitude() > kEpsilon && Magnitude(in.stick) < kEpsilon)
        ++lane.engineLeaked;
}
```

`engineLeaked` is the whole point. Double-driving presents as *"movement feels too fast"* or *"the
character drifts"* — subjective symptoms that get tuned around instead of diagnosed. A counter turns it
into a number, and the number is zero or it is not.

**Movement and buttons need separate gates.** A single `g_vrInputActive` flag that suppresses both means
disabling locomotion also kills your action buttons, and re-enabling one silently re-enables the other.

## Turn the character through the engine's own heading channel

Physical body rotation — the character turning to follow the headset — has an obvious wrong
implementation (rotate the visible mesh) and a correct one.

> The character turns to follow the headset **through the engine's own heading channel**, so the mesh,
> the collision capsule, the aim and the movement direction all move with it. The view does not move and
> the hands stay on the controllers.

*(Cyberpunk 2077 VR's optional physical body rotation.)*

The list in that sentence is the reason. A character's facing is consumed by at least four systems, and
they must not disagree:

| Consumer | If it doesn't follow |
|---|---|
| Visible mesh | Body faces the wrong way — cosmetic, and the one you notice first |
| Collision capsule | You clip through geometry your body appears to be clear of |
| Aim / weapon origin | Shots come from the wrong side |
| Movement direction | Stick-forward is not where you are facing |

Writing the mesh rotation alone fixes only the first row and silently desynchronises the other three.
**Find the single value the engine treats as "which way is this character facing" and write that** — it
is usually one field on the movement or locomotion component, and everything else derives from it.

Two properties to preserve while doing it, both easy to break:

- **The view must not move.** The player's head is already where they are looking; rotating the view to
  match the body double-applies the rotation and is instantly nauseating.
- **The hands stay on the controllers.** They are tracked in a space that did not rotate — if they swing
  with the body, you have applied the turn in the wrong frame.

## Feed gestures into the engine's physics, and inherit everything attached to it

The strongest argument for puppeteering rather than reimplementing, stated by White Knuckle VR:

> All VR interactions work as inputs into the existing physics system, meaning that the player moves in
> exactly the same way as in vanilla. The only difference is that you are using your hands to climb and
> jump. **This also means that buffs and debuffs should all work right out of the box.**

That last sentence is the whole case. A reimplemented climbing or locomotion system needs every speed
buff, stamina drain, status effect, surface modifier and difficulty scalar re-implemented beside it —
and each one is a bug you will find months later, in a build you are trying to ship. Converting hand
motion into the *same inputs the engine already consumes* inherits all of it for nothing.

It also means your mod survives the game being patched in ways a reimplementation would not.

**The gesture mapping is worth recording, because the obvious one is wrong.** While gripping a
handhold, the hand becomes the joystick and **the body moves opposite the arm**:

```text
pull your hand DOWN        -> you climb UP
move your hand LEFT        -> you move RIGHT
pull your hand TOWARD you  -> you swing FORWARD
extend your hand AWAY      -> you move away from the handhold
```

That is the physically correct relationship — you are pulling *yourself* toward a fixed grip, not
steering a vehicle — and it is the mapping that stops registering as a control scheme and starts
registering as climbing. Every threshold is exposed in config, and every gesture has a button
equivalent, so the gesture layer is an addition rather than a requirement.

## Don't share a gate between movement and buttons

A tempting shortcut is "disable the keyboard fallback to stop double-driven movement." If
movement and buttons share that one flag, you also kill jump/crouch/use. (*SS2VR: exactly this
— the fix was splitting the gate so movement-key synthesis suppresses under an analog lane
while button emulation stays alive.*) Keep movement suppression and button suppression
independent.

## A release must go to whoever owned the press

The nastiest input bug in a modifier-based scheme: **the meaning of a button changes while it is held.**
The press is routed to action A; the user then presses grip, which remaps the trigger to action B; the
release now goes to B — and **A never stops**.

(*JKXR's comment states it exactly: "We need to record if we have started firing primary so that
releasing trigger will stop firing — if user has pushed grip in the meantime, then it wouldn't stop the
gun firing and it would get stuck."*)

The fix is ownership, latched at press time:

```cpp
struct LatchedAction {
    Action owner = Action::None;   // decided ONCE, at the press edge
    bool   held  = false;
};

void OnTriggerEdge(LatchedAction& t, bool down, const Modifiers& mods) {
    if (down && !t.held) {
        t.owner = ResolveAction(mods);   // modifiers consulted here and only here
        t.held  = true;
        Begin(t.owner);
    } else if (!down && t.held) {
        End(t.owner);                    // NOT ResolveAction(mods) -- that may have changed
        t.owner = Action::None;
        t.held  = false;
    }
}
```

**Never re-resolve a modifier combination on the release edge.** The rule generalises to every held
input in a VR mod — firing, sprinting, grabbing, climbing, alt-fire — and the symptom is always the
same shape: something gets stuck on, and it only reproduces when the user does two things at once, which
is why it survives testing.

Two related habits from the same file:

- **Freeze input mapping during engine-owned animations.** *"If we are in saber block debounce, don't
  update the saber angles."* An action the engine is currently playing out should not have its inputs
  re-interpreted mid-animation.
- **Compute every candidate and let the consumer choose.** *"Set controller angles — we need to
  calculate all those we might need (including adjustments) for the client to then take its pick."*
  Same shape as the multi-candidate residual probe in [06](06-debugging-methodology.md): cheap to
  produce all of them, expensive to guess wrong once.

## Stick-as-buttons (jump/crouch on the right stick)

Mapping right-stick up/down to jump/crouch is comfortable, but:

- **Don't share the deadzone** with anything else on that stick; give the vertical press its
  own threshold + a release threshold (hysteresis) so it doesn't chatter, and a dominance
  margin so diagonal motion doesn't trigger it.
- Dispatch the **real action** (rung 2), not a synthetic key, so it behaves like the player
  pressed the real button (hold-to-crouch, coyote-time jumps, whatever the game does).

## Mirror the input state once at the boundary, never per mapping

Left-handed support is where per-mapping conditionals breed. FEAR VR states the rule as an invariant:

> Left-handed bindings: **only the incoming controller state is mirrored, never an individual
> assignment.**

Swap the two hands' poses, buttons and axes once, at the point the input state enters your code. Every
downstream consumer — grip solving, weapon attachment, melee, flashlight mount, climbing — then keeps
saying "primary hand" and needs no knowledge of handedness at all.

The failure mode of the alternative is not subtle but it is slow: each `if (leftHanded)` added at a
call site is individually correct, and the bug appears only in the combination nobody tested — usually
two-handed grip plus left-handed plus a weapon that has its own authored grip side.

## Calibration is per-context, with inheritance — not one global number

A single global height or scale value is the right *starting* place and the wrong *finishing* place, as
soon as the game puts the player into more than one physical situation.

Halo-MCC-VR's vehicle work is the clearest worked example. Every seat ships a starting camera position,
and their README is blunt that this is **"a starting point, not a finished setting"** — because everyone's
height, play space and headset sit differently, so a seat that is right for the author is wrong for you.
The structure they landed on:

```text
in a seat   -> the sliders adjust THAT seat only
               (driver / passenger / gunner / turret each remember their own, per game)
on foot     -> the same sliders set the shared starting point that every
               unadjusted seat inherits, across all three games at once
               + a "Reset the universal trim" button, shown only once it has been moved
```

Three properties make this work, and each fixes a real annoyance:

- **The same control means different things by context**, so there is one slider to learn rather than
  forty. This is [the shared-gate rule](#dont-share-a-gate-between-movement-and-buttons) used
  deliberately: one control, contexts that are mutually exclusive by construction.
- **Unadjusted contexts inherit**, so a user who tunes one thing gets a sensible default everywhere else
  instead of forty untuned seats.
- **It saves itself on exit**, and the reset appears only when there is something to reset.

**Tell the user calibration is expected.** Framing per-seat tuning as *"normal, and a one-time job per
seat"* converts what reads as a bug report into a setup step — the same honesty that makes
[SS2VR's world-scale-by-feel](05-assets-and-materials.md) work, applied to ergonomics.

## Physical lean moves the viewpoint; the engine's own lean usually does not

Worth checking before you wire a lean: many engines implement lean as a **camera tilt with the viewpoint
still at the player position**. That reads as a head tilt in VR, not as leaning around a corner, and
players notice immediately that peeking does not actually let them see more.

(*FEAR VR replaced it: the head offset from tracking moves the actual viewpoint, limited at walls.
Retail's own lean only tilted the camera.*)

Three details from their implementation worth carrying:

- **Amplification is a user setting in percent.** At 200, a 10 cm physical head offset acts like 20 cm —
  so the player leans half as far to see the same amount. This is a comfort *and* an ergonomics control:
  real rooms have walls and chairs.
- **Wall collision scales only the horizontal axes.** The calibrated vertical movement stays independent
  and keeps a minimum clearance (25 cm) above the reported floor, so ducking never clips you through it.
- **The collision capsule stays at the locomotion origin.** Only the viewpoint and the visible body move.
  Feeding the leaned viewpoint back into the collision body creates a feedback loop — the same shape as
  the hand/weapon loop in [02](02-viewmodels-and-hands.md).

## One diagnostic switch per group of writes

When an injected mod crashes at one specific moment — a particular cutscene, a level transition — the
useful bisection is not "VR on/off" but **one switch per group of writes**, each disabling exactly one
thing you do to the game.

(*FEAR VR ships `-fearvr-no-inject`, `-fearvr-no-bindings`, `-fearvr-no-update`, `-fearvr-no-weapon`,
`-fearvr-no-interaction`, a stereo-off switch, and a combined `-fearvr-safe`. One flag leaves the
weapon/aim/fire hooks unset; another leaves the detour installed but never overwrites the target,
which separates "the detour itself is fatal" from "our value is fatal" — a distinction that is
otherwise very expensive to establish.*)

That last pairing is the valuable one and generalises past VR: **ship a switch that keeps the hook
installed but neuters its effect.** It splits a crash into "the interception" versus "the data", and
those have completely different fixes. See [06](06-debugging-methodology.md) on coarse switches.

## Control-bind strings are vocabulary, not an API

Finding `+jump` in the binary's command table proves the verb *exists*; it does **not** give
you a callable function pointer. The table may be built at runtime (no static string→handler
references to scrape). Don't treat a discovered bind string as a confirmed dispatch address —
confirm the actual callable path, or fall back to the console/command system which *is* the
supported entry point. (*SS2VR: the jump/crouch handler RVA hunt dead-ended for exactly this
reason; the console-verb path via the existing action bridge worked immediately.*)

## A synthetic controller's *presence* is a lane too (rung 3 gotcha)

If you attach a virtual gamepad (rung 3), its mere *connected/neutral* state is an input signal the
engine reacts to — separately from the axes you feed it. Get the presence model wrong and you cause
symptoms that look nothing like input bugs.

- *BioshockVR:* advertising a neutral synthetic XInput slot *before* VR activation **stole native
  keyboard/mouse ownership**; advertising it only while an action was non-neutral caused
  connect/disconnect **flapping** and a "controller disconnected" warning. The stable model: after the
  first VR activation, keep **one neutral slot connected for the whole process lifetime**, and release
  synthetic buttons/axes (not the connection) through tracking gaps.
- Arbitrate physical pad vs synthetic VR sticks with a **bounded priority window** (e.g. "physical
  input wins for 250 ms after it moves"). *(BioshockVR.)*

  **This is one valid answer, not the default one** — and the shipped-mod survey above is a direct
  correction to the stronger claim this playbook used to make here. It previously said *never* sum the two
  and *never* disable the engine's original input call. Both absolutes are contradicted by mods that
  shipped: GTFO and JKXR both **sum** (additive merge with a single clamp) and it works, because their
  summed sources are semantically compatible; BendyVR **hard-disables** the mouse axes and ships that way.

  What survives as a genuine rule is narrower: **exactly one lane may end up driving a given control** —
  reached by elimination, by device-layer arbitration, by additive saturation, *or* by a recency window.
  Summing is only the double-driving trap when the two sources can disagree about the same intent; where
  one is provably idle or the semantics saturate cleanly, it is the cheapest correct answer.

## OpenXR actions: keep physical transport and game semantics separate

FEAR VR provides the cleanest complete example in the surveyed sources
`[SOURCE]`:

```text
OpenXR actions in the x64 host
  -> versioned physical input snapshot
  -> shared-memory seqlock
  -> x86 D3D9 bridge
  -> game-client semantic mapping
  -> IClientShell update / Retail command funnel
```

Haptics travel in the opposite direction: an accepted game event creates a
versioned request, the bridge returns it to the host, and the host applies the
OpenXR output action.

The boundary matters. The host transports:

- physical stick/trackpad axes;
- trigger and grip values;
- physical buttons;
- aim/grip poses and validity;
- active-hand/profile state;
- prediction/sample timestamp.

The game client decides those values mean *move, turn, fire, use, reload,
pause,* or a context-sensitive gesture. A bad or unexpected interaction
profile therefore cannot silently invoke a game command without an explicit
semantic mapping.

### Create, suggest, attach, sync, then query what actually won

The durable OpenXR order is:

1. create one gameplay action set;
2. create per-hand/subaction paths and input/output actions;
3. suggest bindings for supported profiles;
4. attach the action set once to the session;
5. call `xrSyncActions` while focused;
6. read states only when `isActive` and pose validity permit;
7. after sync and on
   `XR_TYPE_EVENT_DATA_INTERACTION_PROFILE_CHANGED`, call
   `xrGetCurrentInteractionProfile` for each hand and log it.

Suggested bindings are proposals. Logging the active profile is what tells you
which native or emulated mapping the runtime selected. FEAR suggests Touch,
Index, Microsoft Motion, Vive, Simple Controller and—when advertised—the KHR
generic-controller profile `[SOURCE]`.

Profiles do not all have the same controls. Vive wands lack stick clicks and
use trackpads/digital grip; a complete scheme declares which actions remain on
keyboard or move to gestures instead of inventing nonexistent buttons.

### Neutral state is the only safe failure state

FEAR’s game client zeros all VR input when:

- the host is absent;
- the shared snapshot is older than 250 ms;
- OpenXR is not focused;
- a hand/pose is inactive or invalid.

That is [XR-002](pattern-catalog.md#xr-002).
Never preserve “last known good” movement, fire or grip values across an
ownership loss. Release them, clear edge history and require a fresh post-focus
press.

Use a seqlock or another coherent snapshot protocol when producer and consumer
have different bitness/processes. Version the structure and publish sequence
last so the reader never combines axes from one update with buttons/poses from
another.

### Axis math happens before semantic thresholds

For a two-dimensional locomotion stick:

1. calculate radius;
2. apply one radial deadzone;
3. rescale the surviving radius;
4. preserve angle;
5. clamp final magnitude to one;
6. optionally apply a documented forward-corridor shaping curve.

Do not apply independent X/Y deadzones: they pull small diagonals toward axes.
Do not let a full diagonal exceed unit magnitude.

Keep turn-axis shaping independent from vertical stick-as-button thresholds.
FEAR uses the right stick horizontally for turn while jump/crouch read the
unchanged vertical component at an 80% threshold `[SOURCE]`.

### Edges, gestures and timestamps belong to the consumer clock

Retail command systems frequently distinguish `OnCommandOn` from held state.
Send one rising edge for a medkit or menu activation, and ensure the press owner
receives the release.

For velocity gestures, do not assume `predictedDisplayTime` advances on every
consumer poll. FEAR’s client can poll faster than the host publishes; using the
repeated prediction timestamp caused every gesture sample to be discarded.
It measures consumer-side elapsed time with its own monotonic clock while
retaining the producer timestamp as provenance `[SOURCE]`.

### Mirror handedness once, then mirror physical output back

FEAR swaps both sticks, triggers, grips, buttons, hand masks and tracked poses
immediately after reading the physical snapshot. All downstream systems retain
fixed logical weapon/support roles. Only the haptic hand mask is swapped again
on the way back to the physical controllers `[SOURCE]`.

The decisive desk test is involution: mirroring twice must reproduce the exact
input state. See [INPUT-003](pattern-catalog.md#input-003).

## The game's threshold is in different units, and it may be sustained {#gated-mechanic}

[INPUT-004](pattern-catalog.md#input-004) says invert the conditioning the game applies on receipt. This
is the next layer up: even a correctly-conditioned value can fail, because the *mechanic* you are
driving is gated rather than proportional. Mirror's Edge VR's arm-swing locomotion is the worked case,
measured over **22,404 samples**. `[SOURCE]`

**The gate is on near-full deflection, and it is sustained.** `InputMaxSprintRaduisLimit = 0.7` gates
sprint on near-full deflection in *both* radius and forward height, and an **energy accumulator decays
over three seconds**. Arm swing naturally produces an envelope that dips at every reversal, so:

> An envelope that sags to 0.6 twice a second drops `SprintRequested` twice a second, and the
> accumulator never gets anywhere: **the player is capped at a jog permanently, however hard they
> swing.**

**A gated mechanic cares about the minimum of your signal, not its peak.** The hold window has to keep
deflection pinned *above the gate through every reversal* - not merely above zero, which is what the
naive envelope guarantees.

**And the obvious mapping is the wrong one.** A linear `deadband → full` map puts a moderate
jog-cadence swing at roughly `0.55`, under the gate, leaving sprint reachable only at the top of the
player's physical range - *"exhausting, and it inverts the game"* in a title where running is the normal
state. **Map to the mechanic's thresholds, not to the axis range.**

### Convert the units before comparing

The trap inside the trap, and it moved the target by 12%:

> The game's limits are in **post-deadzone units**; the raw value that reaches them is **0.784**, not
> `0.7`.

With a measured stick dead band of `0.280`, a limit written as `0.7` in the game's own config is `0.784`
in the raw units you are synthesizing. **A threshold read out of a config or a disassembly is expressed
in whatever space that code sees**, which is rarely the space of the value you are writing. Convert it,
and say which space every number is in when you record it - this is the
[eye-height datum problem](12-torso-calculations-and-ergonomics.md#eye-height-datum) in another
coordinate system.

## Aim mode is a shipped setting, not a design decision to get right once {#aim-mode-is-a-setting}

The fleet has treated decoupled aim as *the* correct answer. An earlier Quake 2 VR port shipped **nine
aim modes as a user cvar** and let the player choose. `[SOURCE]`

```c
VR_AIMMODE_DISABLE,
VR_AIMMODE_HEAD_MYAW,          VR_AIMMODE_HEAD_MYAW_MPITCH,
VR_AIMMODE_MOUSE_MYAW,         VR_AIMMODE_MOUSE_MYAW_MPITCH,
VR_AIMMODE_TF2_MODE2,          VR_AIMMODE_TF2_MODE3,   VR_AIMMODE_TF2_MODE4,
VR_AIMMODE_DECOUPLED
```

Read the axis structure rather than the names: the modes vary **which input owns yaw and which owns
pitch**, independently. Head-yaw with mouse-pitch is a different experience from head-yaw-and-pitch, and
both are different from fully decoupled - and **which one a given player tolerates is not predictable
from first principles.**

**Three of them are named after another shipping VR implementation's taxonomy** (`TF2_MODE2..4`),
which is the useful part: rather than inventing a scheme, they inherited one that had already been
tested on players at scale and shipped it alongside their own.

**This matters beyond that era.** It was written before hand controllers, so the question was "you have a
head tracker and a mouse" - but the same question returns for **seated play, gamepad play, accessibility,
and any target where the weapon is not motion-tracked.** A mod that hard-codes one aim relationship has
made a comfort decision on the player's behalf.

The same port ships HUD **bounce** modes on the same principle (`NONE / SES / LES`), which is
[an in-headset A/B](08-project-process.md#headset-reachable-controls) turned into a shipped preference.

## A controller lying on a desk is not reporting zero {#resting-controller}

Nine runs, five proposed mechanisms, all buried, and a shipped workaround built on a correlation nobody
could explain - because the fault was never in the code anyone was reading. `[SOURCE]`

> A Touch controller that has been **set down and left to rest** reports a **sustained partial trigger
> pull** - measured at left **0.34-0.43** and right **0.23-0.28**, held for seconds, with `isActive`
> **true** on all 120 frames of every sample.

That clears a `0.10` deadzone comfortably, reaches the game as `LT ~= 97` / `RT ~= 64`, and the game's
own controller layout maps those to **AIM** and **FIRE**. So the weapon fires and aims by itself, and:

> **Nothing was ever wrong with the engine, the pad, or the input code.**

It presented as **judder**, because firing costs frames:

| Trigger state | fps |
|---|--:|
| neither | **120** |
| right only (fire) | **98** |

**Three things to take from it.** A resting controller is a *live* device reporting plausible non-zero
analog values, not an absent one - so `isActive` tells you nothing about whether the player is touching
it. A deadzone chosen for a held controller is too small for a resting one. And when a performance or
comfort symptom correlates with something you cannot explain, **check whether the input you are reading
is lying before you look for a mechanism inside the engine** - Singularity VR's own summary is that the
mechanism *"was never inside the engine's input plumbing, which is why nothing found there ever held
up."*

Practical defences: raise the deadzone above the measured resting value on the hardware you support,
prefer the runtime's touch or proximity signal over the analog value where one exists, and log raw axis
values alongside the derived button states so a phantom press is visible in the trace rather than
inferred from its consequences.

## Synthesize at the OS layer or the engine's own call - forging the layer between fails {#input-synthesis-layer}

Psychonauts VR lost **four sessions** (notes 15 through 18) to synthetic input that was delivered
correctly and did nothing, and the resolution is worth having before you start. `[SOURCE]`

**What failed:** forging DirectInput buffer contents and `GetDeviceData` event records under a debugger,
mid-frame. The forged state *arrived* - it reached `SetKeyState` intact - and produced no visible effect
at all.

**What worked, on the first try, in one session:** plain `SendInput` with `KEYEVENTF_SCANCODE` (DIK-style
scan codes; arrows also need `KEYEVENTF_EXTENDEDKEY`), with the game window genuinely foregrounded.

> The engine's edge-detection and its input focus evidently key off **the real input stack and real
> window focus**. Real OS-level events through the real stack, with the game genuinely focused, exercise
> the entire path the way a physical key does.

**Injecting state below the layer that computes edges skips the edge computation.** A game that acts on
key *transitions* - which is most of them - sees a level you wrote and no transition, so nothing fires.
The same reasoning explains why conditioning happens on receipt: the pipeline you bypassed was
doing work you needed.

Two safety details from their implementation, both worth copying: **verify the foreground grab with
`GetForegroundWindow` before sending and abort if it failed**, so synthetic keys cannot land in
someone's editor - and keep hands off the physical keyboard for the send window.

**But the opposite failure is equally real, so treat the layer as an empirical question.** BioShock
ignores `SendInput` mouse-turn entirely and responds only to its native calls; Psychonauts ignores forged
device state and responds only to `SendInput`. **Test the cheapest layer first, confirm it moves
something visible, and do not assume the answer transfers between games.**

**A third witness, and the sharpest one, because the API lies to you.** FarCry2-VR measured every route
into Dunia while building its headless harness:

| Route | Result |
|---|---|
| `SendInput`, 32-bit `INPUT` layout from x64 | returns **0** - `sizeof(INPUT)` is **40** on x64, not 28 |
| `SendInput`, correct layout, window verified foreground | returns **1** - and **the game ignores it** |
| `PostMessage` `WM_KEYDOWN`/`WM_CHAR`/`WM_KEYUP` | **advances the splash**; no effect on menus |
| `PostMessage` mouse move and click on a menu row | no effect |

`Dunia.dll` imports `DirectInput8Create`, and **the menus read device state, not window messages**. Two
conclusions they wrote down:

> **`SendInput` returning 1 is not evidence it worked.** It means the OS accepted it, nothing more.

> The splash and the menus use **different input paths**. A harness that uses one mechanism for both
> works intermittently and **looks flaky rather than wrong**.

That second one is the expensive part: an input route that works for one screen and not another does not
present as "wrong route", it presents as an unreliable harness, and unreliable harnesses get retried
rather than diagnosed. **Prove the route on every screen class you intend to drive**, not on the first
one that responds.

Their attach is worth stealing too: `DInputHook` creates **its own throwaway keyboard device**, reads the
vtable pointer out of it, and patches that. A COM vtable belongs to the **class**, lives in `dinput8.dll`
and is shared process-wide, so the patch also covers a device the game created long before the mod
loaded - *"there is no timing relationship to win."*

Their verification is a small model of [quantifying the artifact](06-debugging-methodology.md#quantify-the-artifact):
an eye dump before and after, **mean pixel diff 38.7 against a same-screen animation-noise floor under
15** - a number, with its noise floor stated, rather than "the screen changed".

## When the view is clamped, find the other thing that drives the same camera {#clamped-view-second-mechanism}

Third-person and follow-camera games clamp free-look, which looks fatal for head tracking. Psychonauts
VR spent five attempts trying to lift the clamp and then asked a better question. `[SOURCE]`

### First, establish whether the axis is a rate or an offset

A one-minute test that decides the entire control design. **Hold the axis at its extreme and watch
whether the value keeps moving.** Theirs was held at maximum for **12 seconds** and the camera sat at
`-82.2` degrees the whole time, *byte-identical*:

> A rate input would have kept orbiting; this does not.

**The stick is an absolute clamped offset from the follow position, not a rotation rate.** That is why
over-driving it does nothing, and why the reachable range is a hard number - measured at roughly 100-150
degrees total depending on the axis combination, saturating at `axis <= 250` and `axis >= 750`.

### Then look for a second mechanism that drives the same consumer

**There are two rotations in most such games and only one of them is clamped:**

| Rotation | Mechanism | Range |
|---|---|---|
| **Free-look** | right-stick offset from the follow position | **~87 degrees, hard-clamped** |
| **Body facing** | the character turns; the camera follows | **unlimited, 360 degrees** |

Both drive the *same* camera, so **the engine's culling follows either one**. Measured on body facing:
a total excursion of **317.7 degrees**, cleanly through the +/-180 wrap, no saturation and no hard stop.

> Every previous attempt targeted the clamped one. The unclamped one was available the whole time.

The lesson generalises past cameras: **a bound you keep hitting may be a property of the mechanism you
chose rather than of the game.** Before engineering around a limit, enumerate the other inputs that
reach the same consumer.

### The catch: body facing is usually coupled to locomotion

The character turns to face the direction he is *moving*, so no movement means no turning. Their run
wedged under a wooden structure and stopped dead - `yaw 168.0` for seven consecutive steps, `0` units
moved. For VR that is not a detail:

- it rules out **turning in place**, the most natural VR motion of all;
- and the unrendered region returns **exactly when the player stops to look around**.

### The fix is to pulse, not hold - and it is worth about 8x

Games commonly turn a character *before* translating them, so short taps buy rotation cheaply. Measured,
same direction, same total key-down time:

| Input style | Rotation | Distance | **Rotation per 100 units** |
|---|--:|--:|--:|
| 8 x 90 ms taps | 7.7 deg | **13 units** | **60.2 deg** |
| 1 x 720 ms hold | 14.6 deg | 190 units | 7.7 deg |

**Pulsed input yields ~7.8x more rotation per unit of travel** - a 180-degree turn costs roughly **300
units of drift tapped against ~2,340 held**, which is a short shuffle rather than a walk across the
level.

**Feed head yaw in as a pulse-width-modulated stream of short taps, not a sustained hold.** Their note on
why this matters is the part to keep: *"that is a different control design from the obvious one, and the
obvious one would have produced a mod that drags the player across the level whenever they turn their
head."* See [INPUT-006](pattern-catalog.md#input-006).

### Layer the three, because none of them is sufficient alone

- **Free-look** for small, precise, instant offsets - about +/-43 degrees, and no locomotion cost;
- **pulsed body turn** for the large rotations free-look cannot reach;
- **FOV widen** underneath both, covering whatever neither catches.

One more field worth checking before you build any of it: the yaw values you can *see* may not be the
ones that drive anything. Theirs found *"the yaw scalars are derived copies, not drivers"* and a
`camyaw` write that *"does not work - overwritten, not mis-aimed"* - the same
[field-level authority](11-re-anchoring-and-discovery.md#field-level-authority) problem, so verify by
writing before designing around a value.

**And note how this result was reported.** A first measurement of the 317.7-degree excursion was
**withdrawn as contaminated**, re-run with position tracked, and only then confirmed - with the
locomotion limitation stated alongside it. Their own process note, *"this is the second over-claim on the
same question today"*, is the kind of thing that stops a third.

## Platform-state gotchas

- **The OS/launcher controller layer can swallow input.** Steam Input, in particular, can
  intercept a controller before the game sees it; if a real pad does nothing, check that
  before blaming your code.
- **Cloud-synced config can override you silently.** A stale setting synced from an old install
  can disable the very thing you're testing, and no console command overrides it because it's
  reloaded from the synced file. (*SS2VR: a cloud-synced `joystick_enable 0` in `user.bnd`
  killed analog sticks even on a fresh install — burned real time before it was found.*) When
  vanilla behavior is inexplicably broken, suspect synced/profile state, not your mod.
- **Verify the game even supports the input class** before building a bridge for it. Test a
  real device first — if a physical gamepad doesn't move the player, no virtual one will.
