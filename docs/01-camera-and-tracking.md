# Camera & Tracking

The root discipline of flat-to-VR conversion. A flatscreen game has one camera; VR needs a
head-tracked stereo pair. The engine wasn't built for that, so the moment you inject a second
camera you've created an ambiguity that every other system inherits.

## The multiple-cameras problem (the #1 source of "VR jank")

After you start overriding the view, several cameras exist at once and they do **not** agree:

- **The HMD/display camera** — what the headset actually renders with (you control this).
- **The engine's native camera** — what the game *thinks* the camera is; it chases the HMD
  with a frame or two of lag, or holds a stale value, depending on how you feed it.
- **Per-eye cameras** — the display camera shifted left/right by half the IPD each frame.
- **Previous-frame copies** — anything captured on the render thread is already one frame old
  by the time a game-thread consumer reads it.

Every engine subsystem — viewmodel placement, object picking, attached-object transforms, UI
projection, projectile origin — silently binds to *one* of these. **The central skill is
knowing which one, per subsystem, and making your math use the matching camera.** Most VR
artifacts are a camera/frame mismatch, not engine corruption.

- *SS2VR:* the weapon wobble survived five "fixes" because each guessed a camera. A probe that
  reconstructed the object's position under four candidate cameras (native-now, native-prev,
  display-now, display-prev) showed the engine uses **native-same-tick** to ~0.01 units — the
  remaining error was elsewhere entirely (see below). Stop guessing; let the engine tell you.

## Authoritative vs. follower rendering

Two architectures for getting the HMD pose on screen:

- **Follower:** let the engine own the camera and nudge it toward the HMD (mouse-delta
  injection, etc.). Low risk, but everything lags the head and you fight the engine's own
  smoothing/recoil/headbob forever.
- **Authoritative:** you own the final view matrix; the engine's camera becomes a downstream
  value you keep in sync. Lower latency and correct stereo, but now *you* are responsible for
  everything the engine used to do to that matrix (culling frustum, UI projection, picking
  rays), and divergence between "your" camera and "its" camera becomes a bug surface.

Treat authoritative mode as **diagnostic until every dependent path is proven** — culling,
recenter, turn, picking, viewmodel. It's the right destination but it exposes a long tail.

## Stereo projection is a camera contract, not one matrix write

Moving `worldViewProj` is only the visible tip of the camera. A shader or later pass may also
consume inverse projection, screen-to-world reconstruction, eye position, clip planes, depth
scale/bias, fog reconstruction, or screen transforms. If one side remains center-eye while the
geometry becomes per-eye, the result can be correct parallax with broken clipping, lighting,
fog, or specular terms.

- Extract the game's real center projection from live/captured constants or a confirmed camera
  object. Guessed FoV and near/far values can produce plausible but structurally wrong results.
- Build each eye projection from the runtime's asymmetric left/right/up/down FoV, not a single
  symmetric "VR FoV" number.
- Apply physical IPD as a view-space eye translation in engine world units. A constant
  clip-space or image-space shift moves near and far objects equally and remains a flat image.
- Treat all reconstruction/clip/depth companions as one per-eye update set.
- Keep a strict numerical validation gate. If removing the center projection from a candidate
  WVP does not leave an affine transform, do not apply the eye transform to that layout.

The engine camera must eventually own culling too. A private wider projection can only show
geometry the engine submitted; positional 6DoF and peripheral FoV expose stale culling quickly.

In code, the contract is that **one function owns the whole per-eye camera** and no other site writes
any part of it. The bug this prevents is the classic one: view from VR, projection from the engine, and
a FOV that silently disagrees.

```cpp
/* ONE writer for the whole set. If any caller can set view without projection,
   or projection without the cull frustum, you have the multiple-cameras bug --
   and it presents as jank, not as an error. */
struct EyeCamera {
    Mat4  view;          // world -> eye
    Mat4  proj;          // eye   -> clip
    Frustum cull;        // MUST be built from the UNION of both eyes
    float ipdMetres;
    uint32_t frameId;    // stamp: catches a consumer reading last frame's camera
};

void BuildEyeCamera(EyeCamera& out, const XrView& xr, const Pose& bodyPose,
                    float nearM, float farM, uint32_t frameId)
{
    const Mat4 headToWorld = Compose(bodyPose, PoseFromXr(xr.pose));
    out.view = Inverse(headToWorld);

    /* Asymmetric frustum, straight from the runtime's four tangents. Never
       synthesise this from a single "FOV" scalar -- HMD frusta are off-centre
       and a symmetric approximation shows up as eye strain, not as a visual bug. */
    out.proj = ProjectionFromTangents(std::tanf(xr.fov.angleLeft),
                                      std::tanf(xr.fov.angleRight),
                                      std::tanf(xr.fov.angleUp),
                                      std::tanf(xr.fov.angleDown),
                                      nearM, farM);
    out.ipdMetres = ...;
    out.frameId   = frameId;
    /* out.cull is filled by BuildCullFrustum below -- deliberately NOT here,
       because it is not a per-eye quantity. */
}
```

**The cull frustum is not a per-eye value and must not be derived from one eye.** Culling with the left
eye's frustum removes geometry the right eye can see — which is the "you cannot render your way out of
missing geometry" failure: by the time you notice, the vertices were never submitted.

```cpp
/* Widen to the union of both eyes, then add margin. The margin covers
   reprojection and the pose moving between cull time and render time. */
Frustum BuildCullFrustum(const XrView& l, const XrView& r, float marginDeg = 5.0f)
{
    const float m = marginDeg * 3.14159265f / 180.0f;
    return FrustumFromTangents(
        std::tanf(std::min(l.fov.angleLeft,  r.fov.angleLeft)  - m),
        std::tanf(std::max(l.fov.angleRight, r.fov.angleRight) + m),
        std::tanf(std::max(l.fov.angleUp,    r.fov.angleUp)    + m),
        std::tanf(std::min(l.fov.angleDown,  r.fov.angleDown)  - m));
}
```

## You cannot render your way out of missing geometry (cull-camera ownership)

This is the sharpest edge of "the engine owns culling," and it recurs on every engine: **the
visibility pass runs before your render-view rewrite, from the engine's camera, not yours.** Widening
your render frustum or moving your projection changes *how* submitted geometry is drawn — it cannot
make the engine submit geometry it already culled. The symptoms are objects popping out at the edge of
view and corridors that don't render when you peek or lean around a corner, precisely because in VR
your eye moves (head 6DoF + per-eye IPD) while the engine's cull camera stays on the body.

- *SS2VR:* three distinct mechanisms hide behind one "frustum" complaint, and conflating them stalled
  the fix for weeks. Edge pop-out is **2D screen-space portal clipping** against the fixed-point
  viewport (`PortalGetClipInfo`); peek/lean failure is **cell/portal visibility computed from the
  body-anchored cull camera** (`SceneTraversalBegin_SetCullCamera` is the sole writer); and the
  suspected "grazing-angle portal drop" was **not a defect** — the front-face test is exact geometry
  and is what terminates the visibility BFS. The rule that governs all of it: *drive KEX's cull
  camera/aim before visibility/picking; keep the RenderView override for stereo/projection, never for
  CPU culling.* (Disabling the front-face test doesn't widen the view — it floods a fixed 20480-entry
  clip pool that then hard-fails for the rest of the frame.)
- *SOMAVR:* the same principle, defensively — hooking `cViewport`/`cCamera` frustum ownership so that
  when the exact player camera is known, *every other* camera (reflection, terminal, water, shadow)
  returns its native frustum and cannot inherit the headset pose or consume a VR hotkey.
- *BioshockVR:* full peripheral coverage and positional 6DoF ultimately require engine camera, FOV,
  near-plane, and culling ownership; expanding the private projection alone never made the engine draw
  culled objects.

**Check for an FOV setting before you write a single hook.** If the game exposes a field-of-view option,
raising it widens the *engine's own* culling frustum — the entire problem above, solved from the options
menu. (*HaloVR: Halo 3's default FOV culls geometry outside the flat-screen frustum, so scenery pops in
and out at the edges of the headset view; the mod simply requires the user to set FOV to `120`, which
pushes culling past the headset's field of view. It is documented as the one setting that visibly breaks
the game if it's wrong.*) SS2VR had to drive KEX's cull camera precisely because Dark exposes no such
lever — but it costs nothing to look first.

The general move: find the engine's single cull-camera writer, drive *that* from the HMD (bounded,
fail-closed), and keep your render-view rewrite for projection/stereo only.

## Camera view is not aim ownership

Head tracking, body facing, controller aim, visible weapon pose, projectile direction, and UI
pointer rays may all need different authorities. Mouse-injecting HMD yaw/pitch is a useful
follower bridge, but it couples head and aim and cannot supply roll or independent positional
tracking. Keep that path explicitly temporary and prevent mouse/gamepad/native camera lanes
from driving the same rotation simultaneously.

## Latency, prediction, and smoothing

- Use the runtime's **predicted pose** for the photons you're about to show; use **raw/fresh**
  pose for input sampling. Mixing them (e.g. predicted pose for a marker that's composited
  against an already-submitted frame) double-applies motion.
- **Sample the pose for the frame you are about to render, not the one you just finished.** `Present`
  feels like the natural place to read the HMD, but it sits *after* the engine has already rasterized —
  anything you derive there is describing a frame that's gone. (*HaloVR filtered the current-display pose
  in `Present`: the crosshair smoothing and gun axes were correct, but head motion felt delayed and
  nauseating, and dialling the filter to 0% could not remove the stale-frame feel. The rule they landed
  on: sample the **next** predicted display pose, for the upcoming game render.*) A "smoothing feels
  laggy at every setting" complaint is usually this — wrong sample point, not wrong filter.
- Pose **smoothing** fights latency. A micro-deadzone on orientation/position kills visible
  jitter from sub-degree/sub-mm noise without adding lag; heavy damping just trades jitter for
  swim. Make both tunable and default them low.
- Beware **feedback loops**: any system that reads the camera and then moves the camera (body-
  yaw assist, pitch servos, baseline recapture) can run away. Gate them to idle, clamp the
  per-frame correction, and add a deadzone.

## Turning (snap & smooth) without nausea

- In authoritative mode, **rotate your cached display baseline by the body/capsule's observed
  yaw delta** — don't recapture the full view each tick (that bakes the live HMD offset in and
  re-applies it, producing snap/stacking).
- **Snap turn is not a mouse-turn accumulator write.** Treat it as a discrete baseline
  rotation; if you route it through the smooth-turn/mouse path you get gain and timing bugs.
- The turn's effect lands a frame or two after you request it. If you recapture state *before*
  it lands, you miss it and the view turns "one snap late." Either rotate-on-observed-landing,
  or measure the actual delta and apply that.
- **Comfort blackout:** a brief head-locked black quad during snap/recenter dramatically cuts
  vection nausea — cheap, high value.
- **Residual leak:** any HMD motion you *discard* during a snap/turn window (because you
  suppressed it) is real aim input that silently vanishes — it shows up as a tiny per-turn
  drift. Bank the discarded delta and repay it while idle (an "idle trim servo").

## Near-vertical head poses have no usable yaw — reject, don't invent

When the headset points nearly straight up or straight down, **yaw is mathematically ill-defined**: the
forward vector's horizontal projection collapses toward zero length, and its direction becomes dominated
by noise. Any yaw you extract there is a number, not a measurement.

This matters most at two moments that are easy to miss in testing: **startup and recenter**. A headset
sitting face-down on a desk, or on the user's forehead as they put it on, is exactly the degenerate case
— and a recenter that captures a fabricated yaw silently rotates the whole world.

(*CoD4 VR ships a "near-vertical pose guard" that **rejects unstable yaw instead of inventing one**, and
scopes startup and recenter to yaw-only.*)

```cpp
// Reject rather than normalise. A caller that gets `false` can hold the previous
// yaw, defer the recenter, or ask the user to look at the horizon -- all of which
// are better than a plausible wrong number.
bool TryExtractYaw(const Quat& q, float& yawOut) {
    const Vec3 fwd = Rotate(q, {0, 0, -1});     // OpenXR: -Z forward
    const float horizLenSq = fwd.x * fwd.x + fwd.z * fwd.z;
    if (horizLenSq < kMinHorizontalLenSq)       // ~cos(80 deg)^2 is a reasonable floor
        return false;                            // near-vertical: no usable yaw
    yawOut = std::atan2(fwd.x, -fwd.z);
    return true;
}
```

**Pick the fallback deliberately per caller.** Recenter should *defer* — better to leave the world where
it was and let the user retry than to snap it somewhere arbitrary. A continuously-updated body yaw
should *hold* its previous value. Neither should quietly substitute zero.

This is the same family as the quaternion and Euler traps in [A1](a1-rotation-and-frames.md): the
degenerate case does not announce itself with an error, it produces a confident wrong answer.

## Recenter & horizon

- **THE STORED REFERENCE IS YAW-ONLY; THE LIVE HEAD POSE STAYS FULL.** This is the rule above seen
  from the other side, and the asymmetry is the whole point. **Strip roll from both and head tilt stops
  working; strip it from neither and a crooked capture tilts the world forever** - because a reference
  holding the entire head orientation bakes in whatever tilt the headset had at the moment of capture,
  sitting on a desk or crooked on the player's head, as a permanent offset on every later frame. A
  yaw-only reference is gravity-aligned, so pitch and roll are always measured against level.
  See [CAM-012](pattern-catalog.md#cam-012). `[SOURCE]`

- **RECENTER IS YAW AND POSITION. IT NEVER TOUCHES PITCH OR ROLL.** World pitch and play-space
  pitch are both anchored to *gravity*, and they must stay aligned at all times. Yaw is the only
  free parameter, because yaw alone has no physical reference to disagree with. Import HMD
  pitch/roll into the baseline and the horizon tilts permanently: recentre while looking at your
  boots and "forward" now means downward, with no way back but another recenter.
  - The implementation is one line and there is no excuse for getting it wrong: **flatten the
    reference basis to yaw before using it.** Take the reference's forward, project it onto the
    horizontal plane, rebuild an upright basis with `up` set to exact gravity. Pitch and roll then
    pass through *exactly* rather than approximately — a rotation about the gravity axis cannot
    change a vector's height — so there is no residue for drift to accumulate from.
  - Enforce it in the **guarded entry point**, not by convention at each call site, so that no
    caller can obtain the full-axis behaviour by accident.
  - *(FC2VR shipped a full-axis recenter on 2026-08-25 — recentring the entire orientation basis —
    despite this rule already being on this page. It was caught in a headset within one session, by
    a player who could feel the horizon was wrong. **Being written down is not the same as being
    applied**: check the recenter's axes against this line before shipping one, every time.)*
- Recentering mid-turn or mid-pitch is the classic way to bake a bad baseline. Snapshot only
  what you mean to (usually yaw + position), explicitly.
- **A newly created reference space can report a valid-but-wrong first pose. "Valid" is not "settled."**
  A tracking API will happily flag orientation and position as tracked while the space is still
  stabilising, and if you latch your neutral pose on that sample you bake the error in permanently.
  (*SOMAVR calibrated against OpenXR frame `2857` at head `Y = -1.244683`; the very next frame settled
  near `Y = +0.543`. That spurious **1.79 m** jump put the camera through the roof, and it looked
  convincingly like a world-scale or projection bug.*) Require a **deterministic latch** before accepting
  a neutral pose — SOMAVR's is 8 consecutive distinct poses agreeing within `0.25 m` and `45°` — and make
  a large jump *reset* the latch rather than become a permanent offset. This applies to first startup and
  to every recenter, since a recenter creates the same discontinuity.
- **One recenter *event*, consumed by every lane — not one detector per lane.** Camera yaw/origin,
  eye-height/crouch and the tracked-viewmodel baseline are usually owned by different code, and if each
  watches for the gesture independently they latch on *different frames* and drift relative to each other.
  (*BioshockVR had exactly three such detectors; the fix was one trigger raising a single
  **monotonically-increasing** recenter token that all three lanes consume in the same frame.*) The defect
  is invisible per-system and surfaces only as cross-system incoherence — the hands sitting at a different
  zero from the camera — which is miserable to debug backwards from the symptom.

### One recenter event is a standing check, not a one-time fix

The rule above is easy to state and easy to satisfy once. **It comes back every time you add a lane.**

FarCry2-VR hit it three times in a single session: the orientation recenter itself; then **leaning**,
which rotated by the player's physical facing; then **controller aim**, written in play-space. Each time
they fixed the instance, and the next lane reintroduced it.

> **The defect is invisible *inside* any lane and exists only *between* them.** Every individual lane
> looks correct in isolation, which is why review does not catch it and why fixing it once does not
> hold.

(The leaning instance is BioshockVR's precedent exactly — their user recognised it from that mod.)

**So put it on the pre-ship checklist rather than in the fix log**: *list every consumer of the reference
space — view, body, hands, aim ray, lean, visible avatar, UI anchor — and confirm each one consumes the
same recenter generation.* Adding a lane means running the list again, not remembering a rule.

## Yield to the engine's authored cameras (cutscenes, ladders, conversations, seats)

Any narrative game hands its own camera authority to scripted sequences — cutscenes, scripted camera
pans, ladders, conversations, sit/use animations, death. In VR you must **detect the takeover and
compose HMD freedom on top of the authored base**, never fight it and never feed physical head motion
into the script's endpoint (the script often reads its own final camera to place the body on exit —
pollute it and the player teleports).

- **Detection needs more than one signal.** A structural check (camera switched to matrix mode, or the
  body stopped updating the camera) catches the strong takeovers but misses the sneaky ones. (*SOMAVR
  tracks three separate signals — structural (matrix mode / body-camera-update disabled),
  body-camera-detached (`characterBody+0x1b0` ≠ the normal player camera), and semantic (a known
  authored state owns pose even while the camera still looks Euler/body-attached). ZoomArea and
  Conversation look structurally normal but are authored — a single structural check would run headset
  pose straight into them.*)
- **Classify states by what they own, then pick a policy per class.** (*SOMAVR maps 20 shipped player
  states into: normal, physical-manipulation, diegetic-terminal, structural-authored-camera
  (Sit/InteractiveCameraAnimation write a null body camera + matrix mode), semantic-authored-camera
  (Conversation/Ladder/ZoomArea alter FOV/limits/bob while staying body-attached), and fail-closed
  (Null/CustomControls, which are map-defined and get no shared policy).*) The unknown/scripted states
  fail **closed** — observe camera attachment and animation identity before acting.
- **Compose, don't replace.** For a seated/animated base: keep the authored placement and timing as the
  body/base transform, add HMD orientation (and bounded roomscale) *after* it, and **reseed your stereo
  and temporal histories on both the entry and exit edges** so the eye caches don't carry a stale view
  across the transition. Keep neutralizing VR-hostile authored FOV changes and head-bob during these
  states (see below), but preserve progress, constraints, and hand animation.

Yielding is a state machine, and the transitions are where it goes wrong. Write it as one:

```cpp
enum CamOwner { OWNER_VR, OWNER_ENGINE, OWNER_BLENDING };

/* The rule: the ENGINE wins whenever it has an authored camera, and the handover
   is blended, never instant. A hard cut to an authored camera is a guaranteed
   comfort failure -- the user's head says one thing and the view says another. */
void UpdateOwnership(CamState& s, const EngineCamFlags& f, float dt)
{
    const bool engineWants = f.inCutscene || f.onLadder || f.inConversation
                          || f.inVehicleSeat || f.inScriptedSequence;

    switch (s.owner) {
    case OWNER_VR:
        if (engineWants) { s.owner = OWNER_BLENDING; s.blend = 0.f; s.target = OWNER_ENGINE; }
        break;
    case OWNER_ENGINE:
        if (!engineWants) { s.owner = OWNER_BLENDING; s.blend = 0.f; s.target = OWNER_VR; }
        break;
    case OWNER_BLENDING:
        s.blend += dt / kBlendSeconds;
        if (s.blend >= 1.f) { s.owner = s.target; s.blend = 1.f; }
        break;
    }

    /* Head ROTATION stays live even under engine ownership. Locking rotation to
       an authored camera is the single most reliable way to make someone sick;
       let them look around inside the shot they do not control. */
    s.allowHeadRotation = true;
    s.allowHeadTranslation = (s.owner == OWNER_VR);
}
```

Two properties are non-negotiable. **Blend, never cut** — `kBlendSeconds` around 0.2–0.3 is usually
enough. And **never take rotation away**; translation can be the engine's, but a head that turns and a
view that does not is nausea by construction.

## Triage the game's mechanics before you commit to a camera architecture

Most of this playbook is engineering. This section is **scoping** — and it is cheap, because you can do it
against a symbol dump and a decompiler before writing any code. Two projects arrived at it independently
by auditing their targets' ability lists for VR hostility.

A caveat first, because it matters: nearly everything below is `UNVERIFIED` in the sense
[08](08-project-process.md) means it. These are risk assessments derived from symbols confirmed present in
a binary, not behaviours traced in a running game. **The triage questions transfer; the verdicts on any
specific mechanic must be re-earned on your target.**

**The two-question test for any camera-touching mechanic:**

1. **Does it write roll?** Roll the neck didn't perform is worse for nausea than yaw, and unlike yaw it
   has no snap-turn equivalent to hide behind.
2. **Does it move the up-vector?** This is the expensive one, because a non-fixed up invalidates *every*
   convention built on a fixed world up at once — comfort horizon, snap-turn axis, teleport arc, seated
   recentre. (*PreyVR's zero-G movement does both: it writes `RollSpeedZeroG` and modifies
   `zeroGUpAddition`. Three separate zero-G camera-offset variables confirm the flat camera system already
   branches on that state — so any pose-injection path has to handle both branches, not one.*)

**The three-question test for transform-into-object mechanics** — possession, body-swap, size change,
vehicle entry:

1. Does eye height / scale change? (roomscale tracking becomes meaningless)
2. Are the body and hands the controllers drive removed?
3. Does view-transform ownership move somewhere else?

(*PreyVR's Mimic Matter breaks all three at once; DishonoredVR's possession re-parents the controller to
an entirely different pawn — a rat — for roughly a **1.5 m** vertical shift, changing eye height, movement
model, collision and animation source in one step.*) Note that PreyVR deprioritised its case only because
the power branch is **declinable** — *optional content is not the same risk category as low severity*, and
conflating the two is how a mechanic ships broken.

**The architectural consequence, worth acting on immediately:** bind your tracking origin to *whatever
actor is currently possessed*, configurable from day one. An origin hard-coded to the original player pawn
must be **rewritten** rather than reconfigured the moment control re-parents — and possession, vehicles
and body-swap are common enough that this is cheap insurance.

**Forced rotation outranks forced translation.** Camera-seizing animations — takedowns, fatalities,
knockdowns, hit reactions, mantling, scripted cinematics — both move *and* rotate along an authored path,
and the rotation is what hurts. Triage them per mechanism by asking **"is the animation the point?"**
rather than applying one blanket policy: keep the game's camera position and let HMD orientation add on
top within a clamp where the animation *is* the content (an assassination); disable outright where there
is no player value (knockdowns, strong-hit reactions — engines often ship a flag for exactly this);
vignette rather than remove for core traversal (mantling); orientation-only for scripted cinematics.

**A "teleport" may not be a cut.** An ability named for instant travel may be a *smoothed camera blend*
under the hood, added for flat-screen polish — which turns the one locomotion mode everybody trusts for
comfort into a nausea source. (*DishonoredVR found a node literally called `BlinkBlender` and flagged
"does the blend drive the camera or only the arm animation?" as the cheapest high-value live check before
shipping Blink as VR locomotion.*) A name is not a camera behaviour; look for the interpolation node.

**Some flat-game knobs have no VR translation at all.** (*Prey scales the camera's turn rate while a
particular weapon is equipped — `GooGunCameraSpeedMultiplier`. Perfectly sensible when yaw is a multiplier
on mouse delta; meaningless when the camera is a neck.*) When you find a system that scales "camera
speed," the effect has to be **retargeted** — to snap-turn cadence, weapon sway, a UI cue — not ported.

**Finally, measure the flourishes rather than arguing about them.** (*PreyVR probed its flat camera's Z
position while walking and measured footstep shake oscillating ~**0.01 units** around a 17.10 baseline —
live, not inferred from strings.*) That number tells you whether to suppress, dampen or keep it. And audit
for a **channel split** before killing a shake system wholesale: explosion shake is gameplay feedback,
footstep shake is flourish, and engines usually name them separately
(`cameraShake_footstepCameraShake`, `cameraShake_explosionCameraShake`).

## Comfort is its own engineering surface

Comfort features are not polish bolted on at the end — they're subsystems with the same ownership and
timing concerns as the camera itself, and they port across engines.

- **Snap/recenter blackout** — a brief head-locked black quad during discrete rotation cuts vection
  nausea for almost no cost (see Turning, above). SOMA extends the same idea to *authored* transitions:
  short compositor-black guards around scripted camera takeovers and state changes.
- **Peripheral vignette** — a VIEW-space alpha quad (transparent center, dark edges) whose radius
  tracks locomotion/turn magnitude, driven through a display-period attack/release envelope. Keep it a
  compositor layer independent of world, HUD, reticle, and projection transforms, on its own swapchain,
  and expire the motion samples on the same bounded age as input so it can't stick on. (*The same
  0.30 m distance / ~1 m square contract was authored on SS2VR and then reused verbatim on SOMAVR —
  a different engine and a different graphics API — which is the clearest proof comfort math is
  engine-independent.*)
- **Suppress engine head motion at its source, don't cancel it downstream.** Head-bob, weapon-sway,
  camera-shake, and view-roll are the engine writing motion into the camera you're now driving. Fight
  them where the engine *writes* them, by zeroing the specific channel, not by post-correcting the
  final view. (*SOMAVR: the shipped `SetCameraPosAdd(int type, vec3)` exposes named channels —
  Bob=1, Shake=2, Sway=9, plus Crouch/Climb/Lean/Crawl/Conversation to preserve — and a separate
  `SetCameraRoll`. The comfort hook calls the original setter with a zero vector for the selected
  channels, clearing stale goals while preserving the engine's channel lifecycle; it only suppresses
  while tracking is active and stops the instant tracking drops.*)
  *HaloVR reached the identical design independently on a different engine:* its
  `observer_apply_camera_effect` stage reads the already-computed observer position/forward/up, composes
  Halo's authored camera-effect transform, and writes those three fields back — so the VR hook **bypasses
  only that stage, and only while head tracking is active**, removing firing recoil and artificial screen
  shake without filtering locomotion or headset leaning. Two engines, two authors, one answer: intercept
  the stage that *writes* the artificial motion, and gate it on tracking being live.
  Preserve the semantically meaningful
  ones (crouch, climb, lean, scripted cameras) or you break traversal and cutscenes.

## Adding roomscale to a game that has none is a handoff problem {#roomscale-handoff}

The section below is about not double-counting height. This is the larger version of the same hazard, and
Condemned VR's plan is the most complete statement of it in the survey. `[SOURCE]`

**Camera-only translation is where every project starts and it is not roomscale.** Theirs computes the
HMD displacement from the recenter origin, clamps it to 0.25 m, adds it to each eye transform, renders,
and restores the original camera. So:

> A player can lean or take a small physical step, but the Retail player object, collision capsule,
> triggers, movement direction, body model, and gameplay position **do not move with that step**.

Rotation has the same gap: physical yaw changes what you see but is not a player-turn input. And the
constraint that shapes the whole design:

> **Roomscale must add a player-controller handoff without applying the same motion twice** to the final
> camera or to controller and weapon poses.

### Split the degrees of freedom by who owns them

| DOF | Owner |
|---|---|
| Horizontal HMD **yaw** | turns the **player** as well as the view |
| Horizontal HMD **translation** | moves the **player**, through the game's normal collision and movement path |
| HMD **pitch and roll** | **view only** - never tilt the player |
| Physical **height** | **view/stance only** - gravity, steps, ladders, lifts and floor contact stay game-owned |

### Eight principles, and the two that are easy to miss

Their list, condensed - all of it is load-bearing:

1. **The game owns movement.** Prefer its own movement commands. **Do not teleport** a camera, body model
   or guessed player object with `SetObjectPos`, `ForceCurrentObjectPos` or `SetRigidTransform`.
2. **Measure accepted motion** - collision, stairs, acceleration, special moves and scripts make
   *requested* and *actual* differ.
3. **Apply tracking once.** Motion the player consumed must be **subtracted** from eye, aim, controller,
   weapon, IK and interaction poses.
4. **Update once per simulation frame** - publish one command snapshot for the next update and **never
   integrate state once per eye.**
5. Yaw is separate from pitch and roll. 6. Vertical is not root translation. 7. **Fail closed** to neutral
   commands. 8. **Keep the old mode reversible** - every mutation gate independently switchable back to
   camera-only.

**Principle 4 is a stereo-specific trap**: the eye loop runs twice per frame, so anything that
*integrates* rather than *reads* inside it doubles silently. **Principle 1 is the one that buys
everything else** - routing through the game's own commands means collision, triggers, scripts and
network state stay authoritative for free, which no amount of capsule teleporting gets you.

### The state model: consumed versus residual

Roomscale needs **four** frames rather than one mutable recenter pose:

- **tracking anchor** - the HMD pose at gameplay entry or explicit recenter;
- **player anchor** - the verified player-root position and yaw at that same generation;
- **consumed** translation/yaw - physical motion the game has **demonstrably applied**;
- **residual** translation/yaw - physical motion **not yet accepted**.

```text
requested_xz = current_hmd_xz - tracking_anchor_xz
```

**That consumed/residual split is the whole mechanism.** Subtracting *consumed* from the view solves
double-application; keeping the remainder as *residual* means walking into a wall accumulates a
correction instead of desynchronising the body from the head.

### Collision has two layers, and the second one is the one people forget

Native movement gives you capsule collision, step handling, ledge behaviour, movement scripts and
trigger traversal. **It does not keep the residual head volume out of a nearby wall** - your head leans
through geometry your body never entered.

1. **Player layer** - the game's commands move the controller; accepted root displacement is measured
   *after* collision resolves.
2. **Head layer** - constrain the remaining camera residual against world geometry, with a safety margin
   and temporal hysteresis. **Where no safe sweep has been verified, clamp the residual conservatively
   and fade or vignette while the controller is stalled.**

Their stall spec is worth copying whole: detect requested motion with negligible accepted progress;
**stop continuously pressing the player into a wall**; retain a constrained residual **without
oscillation or tangential wall jitter**; retry only after the physical target or the collision situation
changes; and return smoothly when the HMD moves back toward the player.

### Two pieces of discipline worth as much as the design

**A hook verified for one callsite is not a verified API.** They have a working `IntersectSegment` target
used by the forensic camera, and refuse to build on it:

> Only that callsite and the query fields it modifies are authoritative. A new roomscale query requires a
> dedicated ABI, flags, result-layout, player-ignore-filter, and call-safety proof. **Do not turn the
> forensic hook's partial layout into an assumed general collision API.**

**And negative design evidence transfers where data does not.** Repository history holds a tested
engine-independent axis-follow solver whose own documentation records that body-follow was **disabled
after feedback, oscillation and body-lag problems**. They take the warning and explicitly refuse the
rest: *"That is negative design evidence only; no F.E.A.R.-specific address, layout, or tuning constant
is transferable to Condemned."* **A sibling project's failure is reusable; its numbers are not.**

See [CAM-011](pattern-catalog.md#cam-011).

## Roomscale stance: don't double-count height

When you physically crouch, HMD positional tracking *already* lowers the view. If you then trigger the
engine's crouch, the camera drops **again** — the double-drop. But you can't just skip the engine
crouch: it also shrinks the collision hull, updates AI, and enables fit-under-geometry, all keyed off
the engine's posture enum.

- **Let the engine do its full, correct crouch (driven by the posture enum — never skip it), then add
  the camera drop back in your VR pipeline so the net view movement is HMD-only.** Compensate only the
  *physically*-triggered crouch; a stick-crouch while standing physically upright *should* still lower
  the camera, because there's no physical motion to double against. (*SS2VR measured the engine crouch as
  four lockstep player floats moving ~0.62 m.*)
- **Compensate at the tracking-space head height, not the projection eye pose.** A correction applied to
  the OpenXR projection eye pose has no effect on where positional tracking places you — it only shifts
  the projection view (the same reason a raw `height_offset` does nothing). Apply it to the tracking-space
  origin both positional paths derive from. And the engine usually **animates** the eye-drop over ~0.3 s,
  so a fixed compensation steps instantly and pops — read the live engine eye field each frame and
  compensate by its *actual* animated delta. (*SS2VR: exactly this two-bug sequence — wrong space, then
  un-ramped step.*)

## Delay synthetic motion, late-latch head motion, never swap them {#delay-synthetic-latch-head}

Two projects in one survey did apparently opposite things, and separating them by *clock* produces a rule
stronger than either. `[SOURCE]`

One deliberately holds its camera **one frame behind**, because attached units apply their transforms on
the following frame - so matching that latency keeps synthetic motion coherent with the world. It
explicitly never touches the head rotation.

The other pushes the camera **one step forward at draw time**, regenerating every per-entity
model-view-projection in the render backend so the head pose is as late as the display deadline allows.

They are not in conflict:

> **Delay *synthetic* motion to match the engine's transform-application latency. Late-latch *head*
> motion to match the display deadline. Never apply either to the other.**

Apply the delay to head motion and you have added latency to the one channel a human detects instantly.
Apply the late-latch to synthetic motion and the camera separates from whatever the engine attached to
it - the vehicle, the ladder, the mounted weapon - by exactly one frame of its movement.

**These are two different clocks and the same camera.** Establishing which channel a given correction
belongs to is the whole decision; the implementations are easy once that is settled.

## Frame-timing bug classes (recognize these on sight)

These recur in every VR mod. When something "wobbles," "jitters," or "lags," check these
*before* touching math:

- **Stale-anchor subtraction:** you convert a world pose to camera-relative by subtracting a
  camera origin — but the world pose embedded *last frame's* origin while you subtracted
  *this frame's*. The difference rides on the result: invisible when still, oscillating at
  walking speed. Fix: subtract the *same* origin that was embedded. (*SS2VR walk-jitter.*)
- **One-frame consumer lag:** you write a transform this tick; the engine consumes it next
  tick against a newer camera. Cancels only if you predict or if the consumer's frame matches
  your source frame.
- **Two-thread pose skew (T1/T2):** input thread divides by pose at sample time, render thread
  multiplies by pose at draw time; if they're different samples, a *stationary* object orbits
  as the head moves. Reconstruct through one consistent sample.
- **Eye-alternation:** a value computed per-eye but consumed once will alternate by ±(half
  IPD) every frame — a fast shimmer that scales with IPD×world_scale. Anchor per-eye-invariant
  values at the eye *center*. (*SS2VR doubled-gun / cross-eye strain.*)
