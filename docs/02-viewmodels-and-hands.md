# Viewmodels & Hands

Getting the weapon/tool/hand to sit correctly in VR is where the camera problem (doc 01)
meets reference-frame and Euler-math problems. This is usually the single largest time sink
in a flat-to-VR conversion.

## The viewmodel is probably drawn twice

Flat games commonly render the held weapon in a **separate pass with its own FoV** (a wide,
symmetric "weapon FoV" so the gun never clips and looks heroic), composited over the scene.
In VR that second pass is poison:

- It has no per-eye frustum, so stereo fuses it at the wrong depth → "hyperstereo," tiny gun,
  or eye strain.
- Any view shift unmasks the gap between the scene copy and the HUD copy → "double gun."

The fix is to make the weapon pass use the **same per-eye headset frustum as the world**, then
size the apparent gun with a scale knob — *not* with a stereo view-shift hack (that's a dead
symptom-fix that fights itself). Confirm with a frame capture that the held item is one draw
in the real frustum, not two. (*SS2VR: RenderDoc proved pistol + both hands each drew a
transparent "invis" pass plus opaque passes; the flat HUD copy was the stereo-breaker.*)

## Reference frame: place attached objects in the right space

When you position a held object relative to the camera, the base offset (the grip lever that
puts the gun ~half a unit in front of and beside the hand) must live in the **hand's frame**,
not the **camera's frame**.

- Camera-frame offset → the lever rotates with your head: turn the HMD and the gun swings,
  even though the controller is still. (*SS2VR: this was the actual "wobble" after the camera
  selection was already correct.*)
- Camera-frame offset also makes **controller roll pivot about a displaced axis** — the model
  orbits a point offset from the hand instead of rotating in place.
- Hand-frame offset rides the controller: the grip point stays planted; roll pivots in the
  hand. This is what you want.

General rule: express any rigid attachment in the frame of the thing it's attached to, then
convert once at the boundary into whatever space the engine consumes.

- *BioshockVR (the same lesson, harder):* the engine post-multiplies an already-authored model-view
  matrix that *already contains the HMD camera*, so applying another absolute controller matrix
  double-applies head motion and destroys the animation. Chasing it with yet another camera-relative
  delta or sign flip is the trap; the real fix is **downstream orientation ownership** —
  `controllerRelativeToHead · capturedAuthoredMount`, re-keyed whenever the reference space
  regenerates. When two projects on two engines both reach "another delta/sign flip won't fix this,"
  believe it: it's a reference-frame ownership problem, not a calibration one.
- *SOMAVR (know what the mesh actually is):* the visible hands were one **shipped bilateral skinned
  mesh** (`PlayerHands_0`), not two independent roots. Overriding the "dominant-hand root" put *both*
  quarter-scale hands on the right controller. Confirm the rig topology before you reparent anything;
  a single skinned root can't be split by moving it.

Concretely, "the right space" means composing in the order the engine composes, and the common bug is
one inversion in the wrong place:

```cpp
/* Controller (XR tracking space) -> the space the engine's attach point lives in.
   Get this order wrong and the hand orbits the player instead of tracking. */
Mat4 ControllerToAttachSpace(const Pose& ctrlXr,        // from xrLocateSpace
                             const Mat4& xrToWorld,     // playspace -> game world
                             const Mat4& attachParent,  // e.g. bone/socket -> world
                             const Mat4& authoredTrim)  // static per-model fixup
{
    const Mat4 ctrlWorld = xrToWorld * Mat4FromPose(ctrlXr);

    /* Inverse of the PARENT, not of the controller. This is the line that is
       wrong when the model tracks but is anchored to the wrong origin. */
    return Inverse(attachParent) * ctrlWorld * authoredTrim;
}
```

**`authoredTrim` goes on the right (applied first, in model space).** Putting it on the left applies it
in parent space, which looks correct while the hand is near the origin and diverges as you move — the
signature of a trim on the wrong side is an offset that grows with distance from the anchor.

## Drive the engine's own skeleton; don't override the skinned vertices

If the game has a real skeletal/IK system, the final world-space hand/arm draw is almost always
**already skinned** — the vertex stream is deformed, with no bone palette or blend weights left to
touch. A world-matrix override can rigidly translate/rotate the whole arm around the grip, but it can
never bend an elbow or anchor a shoulder. Skeletal work has to move *upstream* of skinning, into the
engine's own solver.

For a binary-only target, the discovery/proof route for that upstream array is
[11 · enumerate mutable instances from the writer](11-re-anchoring-and-discovery.md#writer-census).
It includes the writer census, large pixel poke, overwrite-race diagnosis and
hot-hook constraints; keep those RE mechanics canonical there.

- *BioshockVR:* the arm draw (`indexCount=26178`) consumes only already-deformed position/normal/UV —
  no `BLENDINDICES`/weights, no bone cbuffer. So the mod drives BioShock's **native
  `AimIKTargetTracker`** instead: it never allocates the tracker (manual construction crashes), it
  augments the exact `AHands` animation-capability bits (`4` → `4|8`) so the *engine* creates the
  tracker at its natural seam, then resolves the live bone indices (upper-arm/forearm/hand = 25/26/27)
  and feeds a head-relative controller target. **A missing solver is a "wait for the engine to build
  it" state, not permission to build one yourself.** (This is why the injection-timing handshake in
  [07](07-engine-integration-safety.md) matters — the creation seam only fires at construction.)

- *SOMAVR (OpenGL, correcting bones not verts):* the shipped hands are one skinned bilateral mesh with
  wrist bones `j_L_Wrist`/`j_R_Wrist` under parents `j_L_Arm_10`/`j_R_Arm_10`. Rather than override the
  shared root (which put *both* quarter-scale hands on one controller), the mod drives each wrist with a
  **position-only post-animation transform** on the engine's own node — `cNode3D+0x108` is the
  post-transform matrix, `+0xc5` the use-post flag — in a bounded per-frame sequence: save the authored
  post matrix and flag, set the candidate, apply, then *restore and verify* so the flag never persists
  between frames (or the next animation update re-applies a stale correction). Normalize only the root's
  scale; keep its authored position and rotation. Gate on Normal state, no authored camera, fresh
  two-hand tracking, and exact parent identity. Live reconstruction error was `~1.4e-6` world units.
- Two engine-specific hand notes that generalize: the game may **swap hand meshes to convey story state**
  (SOMA cycles human/diving/deepsea/mutilated to show suit/body condition) — preserve the swaps, don't
  pin one mesh. And held **tools may be engine entities parented to a hand bone** (`<name>_HudObject` on
  `R_Hand`) with the native handler owning draw/holster/animation — retain that system rather than
  building a parallel one.

Keep the fallback honest: before the native solver is active, a shared-pivot controller placement of
the whole arm is a reasonable stopgap — just don't apply controller translation twice (once via the
solver lane, once via the WVP lane). And read the *symptom* correctly: tiny hands floating at your face
are usually the engine's untouched close-up rig (SOMA's is uniform `0.25` scale, root `~0.075` units
from the camera), not a failed controller attachment.

Visible arms also require a deliberate torso estimate: the HMD and two hands do
not measure shoulders or elbows. Never copy HMD roll/yaw directly into the
shoulder bar, and never treat a two-bone elbow as uniquely solved by its tracked
wrist. The body-heading evidence ladder, calibrated shoulder equations,
reach-triggered clavicle contribution, elbow swivel policy, and acceptance poses
are specified in [12 · Torso Calculations & Ergonomics](12-torso-calculations-and-ergonomics.md).

## Hang the arms off the body, not off the head

A full-body avatar has one structural decision that determines whether it ever looks right: **what the
shoulder girdle is parented to.**

Parenting the shoulders to the HMD is the obvious implementation and it is wrong. Every head movement
then drags the shoulders — look down and your chest follows your chin, lean and your whole upper body
pivots about your eyes. The hands are tracked so they stay put, which means the arms visibly stretch and
rotate to compensate for a torso that should not have moved.

> Hands are with the controllers, **the shoulder girdle and elbows hang off the BODY rather than the
> head**, and the solve is clocked by the engine's own animation batch.

*(Cyberpunk 2077 VR's VRIK: body under the HMD, arm-length calibration, leg IK, real-life squat.)*

Three things in that sentence, all load-bearing:

- **Shoulders parented to the body.** The head rotates freely on top of a torso that follows more slowly
  and by different rules — which is [12](12-torso-calculations-and-ergonomics.md)'s decoupling applied to
  a visible skeleton rather than to a movement direction.
- **Arm-length calibration.** Avatar proportions are authored; the player's are not. Without a
  calibration step the elbow solution is being asked to reconcile two different bodies, and it will fail
  at the extremes of reach — where the [clamp reporting](#two-bone-arm-ik-the-whole-difficulty-is-the-elbow-and-it-is-a-singularity)
  above becomes important.
- **Clock the solve on the engine's own animation batch**, not on your own timer or on frame boundaries.
  An IK solve that runs at a different cadence from the animation it corrects produces a one-frame
  fight between them, which reads as jitter in the hands specifically.

**And suspend the whole thing during authored content.** Their VRIK *"suspends itself during cutscenes so
the avatar does not fight an authored scene"* — the same yield rule as
[01](01-camera-and-tracking.md)'s authored cameras, applied to the body. A scripted animation and a live
IK solve both believe they own the skeleton, and the IK will win in exactly the frames where it should
not.

## Redirect the shot inside the engine's own evaluator, scoped to the player

Decoupling bullets from the camera is the point of motion-controlled aiming, and there is a right place
to do it.

> The hit is redirected inside the engine's own `PhysicalRay` evaluator, **so shotgun spread stays spread
> and every other shooter in the world keeps firing from their own barrel.**

*(Cyberpunk 2077 VR's decoupled weapon aim.)*

Both clauses are the lesson:

- **Redirect inside the engine's evaluator**, not by replacing the shot. Spread patterns, penetration,
  ricochet, damage falloff and hit reactions are all downstream of that ray, and a hand-rolled trace
  inherits none of them. This is [03](03-input-and-locomotion.md)'s puppeteer rule applied to ballistics.
- **Scope the hook to the player.** The same evaluator runs for every NPC in the world. An unscoped hook
  makes every enemy fire from *your* muzzle — a spectacular bug, and the same failure FEAR VR avoided by
  scoping its object detector to `this == *g_pPlayerMgr + 0x3CC`
  ([§ Point the engine's own interaction at your hand](#point-the-engines-own-interaction-at-your-hand-by-borrowing-the-camera)).

Small companion detail worth copying: with a weapon drawn, their **empty hand relaxes into a resting
pose** rather than holding an open grasp at nothing. A hand with no job still needs a pose, and the
default one is usually wrong.

## Two-bone arm IK: the whole difficulty is the elbow, and it is a singularity

Placing the elbow is trivial trigonometry. Making it *stay put* is not, and the failure — the elbow
snapping through the arm as the hand crosses some invisible line — is the defining artifact of bad VR
arms.

The position itself is the law of cosines, with the target clamped into the reachable band rather than
allowed to fail:

```cpp
const float minimumReach = std::fabs(upperLength - lowerLength) + 0.01F;
const float maximumReach = upperLength + lowerLength - 0.01F;
const float solvedDistance = std::clamp(targetDistance, minimumReach, maximumReach);

// distance from shoulder to the elbow's projection on the shoulder->target line
const float along = (upperLength * upperLength - lowerLength * lowerLength +
                     solvedDistance * solvedDistance) / (2.0F * solvedDistance);
const float bendHeight = std::sqrt(std::max(0.0F, upperLength * upperLength - along * along));

elbow = shoulder + targetDirection * along + bendDirection * bendHeight;
```

**Report the clamp instead of hiding it.** Their solution carries a `targetClamped` flag — an
over-extended arm is a legitimate state (the player reached further than the avatar can) and the
consumer may want to lean the body or stretch the shoulder rather than pretend it didn't happen.

### The elbow flip, and the two fixes it needs

`bendDirection` comes from projecting a **pole vector** (a body-relative "elbows point outward, down and
slightly back" direction) onto the plane perpendicular to shoulder→target. That works everywhere except
where it doesn't:

> A pole defines a plane, but at the parallel singularity its projected sign reverses.

When the pole becomes parallel to the reach direction, its projection shrinks to nothing and then comes
back out **the other side** — and the elbow flips 180°. Two defences, and you need both:

```cpp
// 1. Hemisphere memory: never cross to the other side of the plane.
if (hasPrevious && Dot(bendDirection, previousProjected) < 0.0F)
    bendDirection = -bendDirection;

// 2. Spatial fade near the singular cone, so entering it is not a hard turn.
//    poleStrength is how much of the pole survived the projection (0 = fully parallel).
const float poleWeight = std::clamp((poleStrength - 0.05F) / 0.30F, 0.0F, 1.0F);
bendDirection = Normalize(previousProjected * (1.0F - poleWeight) +
                          bendDirection    * poleWeight);
```

Fix 1 alone stops the flip but leaves a hard turn as the target enters or leaves the cone. Fix 2 blends
back toward the *remembered* plane as the pole loses authority, so the elbow drifts rather than snaps.

**Note that this makes the solver stateful.** `previousBendDirection` is an input, which means it needs
the same treatment as any other filter: an explicit list of events that invalidate it (see the reset
enumeration above). A remembered elbow plane carried across a teleport or a cutscene is a wrong answer
held confidently.

### Have a deterministic answer for every degenerate case

The fallback chain descends through four levels, and the last one cannot fail:

```text
pole projects usefully        -> use it (with hemisphere memory + fade)
pole is degenerate, have prev -> keep the previous plane
neither, but a bind pose      -> project the animated upper-arm direction
completely straight bind pose -> a fixed reference axis, chosen by orientation:
                                 |targetDirection.y| < 0.9 ? (0,-1,0) : (1,0,0)
```

That last line is the one people skip, and it is why their solver never returns garbage: with a perfectly
straight bind pose and no history, *something* still has to define a plane, and a hard-coded axis chosen
by which one is least parallel is a defensible answer. **A deterministic wrong-ish elbow beats a NaN.**

### Keep the geometry engine-independent

Their solver uses its own three-float vector type explicitly so the maths can be unit-tested without
loading the game's model interfaces. The whole file is header-only and has a test file beside it. This
is the same argument as the appendices in this playbook: **the parts of a VR mod that are pure geometry
should be testable on a build server with no game, no headset and no engine.**

Their tuning struct is also sanitised on every use, with a fallback for non-finite values and a hard
range per field (`elbowOutward` 0.20–2.0, hand offsets ±0.20 m, angles ±180°). A live-tuning menu wired
straight to an IK solver is an excellent way to produce NaNs; clamp at the boundary.

## You may not have to solve the elbow at all — find the game's own two-bone solver {#hook-the-native-two-bone-solver}

Everything above assumes you are solving the arm. **BFVR does not.** BF1942 ships its own two-bone IK
solver, and its signature hands you the one input that decides the elbow: `[SOURCE]`

```cpp
void __fastcall MayaApplyIk2BoneSolver(
    const float* pole,          //  <-- the only argument the mod replaces
    const float* shoulder,
    const float* elbow,
    const float* wrist,
    const float* handTarget,
    void*        upperRotation, //  outputs, written by the game
    void*        forearmRotation);
```

They hook it and substitute **only `pole`**. The engine still does the projection, still writes the bone
rotations, still owns the skeleton. Their own summary of the boundary is worth copying:

> Elbow intent is computed in the stable shoulder/body frame once per accepted XR generation, with
> position response, singularity fallback, and bounded continuity; **Maya remains the sole two-bone
> projector.**

**This inverts the usual difficulty.** The law-of-cosines placement above is the easy half and the elbow
is the hard half — so if the engine already owns the placement, the entire job reduces to *deciding
where the elbow should point*, which is a pure function of hand and shoulder position.

**Look for this before writing a solver.** Any game with an authored first-person body, a weapon-holding
third-person rig, or a look-at/attachment system probably has a two-bone solve somewhere, and its pole
argument is the seam. It is also the [drive-the-native-skeleton](#drive-the-engines-own-skeleton-dont-override-the-skinned-vertices)
rule reaching one level further in.

### The pole function, and how it survives the singularity

BFVR's `ComputeArmPoleVector` is 204 lines, runtime-independent, has a test file beside it, and is the
most directly liftable elbow code in this survey. Its shape: `[SOURCE]`

**Work in the stable shoulder/body frame**, not the hand frame and not world space — BF1942's is
`+X right, +Y up, +Z forward`. Normalise `handTarget - shoulder`, and bail out entirely if that is
degenerate (length² below `1e-6`) rather than producing a direction from noise.

**Mirror with a sign, not a branch:** `side = leftArm ? -1 : +1`, applied to the X term.

**Make the ordinary case respond to hand position**, biased anatomically — the elbow stays *below* the
wrist and swings outward and back as the hand reaches forward:

```cpp
const float sameSide = handDirection[0] * side;
const float forward  = handDirection[2];
const float vertical = handDirection[1];

std::array<float,3> bendDirection = {
    side * (0.45F + 0.25F * Clamp01(forward) + 0.20F * Clamp01(-sameSide)),
    -0.70F - 0.15F * Clamp01(vertical),
    -0.40F - 0.35F * Clamp01(forward) };
```

**Blend into the singularity, never branch at it.** This is the part that matters, and it is why their
elbow does not snap. Two independent proximity measures are computed as *continuous* blends and the
stronger one wins:

```cpp
const std::array<float,3> singularityDirection = { side * 0.133F, -0.443F, -0.886F };

const float horizontalLength  = std::hypot(handDirection[0], handDirection[2]);
const float verticalBlend     = Clamp01((0.35F - horizontalLength) / 0.25F);  // hand near vertical
const float behindBlend       = Clamp01((-forward - 0.10F) / 0.50F);          // hand behind shoulder
const float singularityBlend  = std::fmax(verticalBlend, behindBlend);

if (singularityBlend > 0.0F)
    bendDirection = Blend(bendDirection, singularityDirection, singularityBlend);
```

Near vertical or behind the shoulder, hand position **cannot** determine an elbow — the solution circle
degenerates. So rather than deriving a direction from a quantity that has stopped carrying information,
they fade to a **fixed, anatomically plausible direction** (after Parger et al.'s singularity-safe
formulation). The user sees the elbow settle, not flip.

**Rate-limit the result on the sphere, not per component.** Maximum step is 12° per XR sample
(`0.20943951` rad), applied as a true slerp with a fallback to linear blend when the angle is too small
for the `sin` division to be stable:

```cpp
const float dot   = clamp(Dot(previous, current), -1.0F, 1.0F);
const float angle = std::acos(dot);
if (angle <= maximumStep) return current;

const float amount = maximumStep / angle;
const float sine   = std::sin(angle);
if (std::fabs(sine) > 1.0e-4F) {
    const float previousWeight = std::sin((1.0F - amount) * angle) / sine;
    const float currentWeight  = std::sin(amount * angle) / sine;
    // ... weighted sum, then renormalise
} else {
    stepped = Blend(previous, current, amount);   // angle too small to slerp safely
}
```

**Report why, not just what.** The result carries `usedPreviousPole`, `usedFallbackAxis` and
`rateLimited`, so a caller — or a bug report — can distinguish "the elbow is where the hand put it" from
"the elbow is where it was last frame" from "the elbow is in the singularity fallback." That is
[instrument honesty](06-debugging-methodology.md#instrument-honesty) applied inside a solver, and it is
the difference between debugging this in an afternoon and debugging it in a headset.

**Fail closed.** A `preserveNative` input makes the function return nothing at all, and the game keeps
its own pole — so any doubt, any non-finite input, any degenerate geometry hands the arm back to the
engine rather than guessing.

See [HAND-005](pattern-catalog.md#hand-005).

### Not every native solver takes a pole — check before planning the lift

*(What follows describes the **Far Cry 1 generation** of CryAnimation. See
[the CE3 correction](#the-cryengine-finding-is-generation-scoped-ce3-replaced-it-entirely) below
before applying any of it to a later CryEngine derivative.)*

The technique above depends on the engine's solver *accepting* an elbow hint. Some do not, and the
difference decides your whole approach.

**CryEngine's `CCryModEffIKSolver` derives the bend plane from the pose it is given**, not from an
external hint. Reading Far Cry 1's `CryAnimation` — which FarCry2-VR carries as a source oracle — the
two-bone solve is the familiar law of cosines, and then: `[SOURCE]`

```cpp
beta = (alen*alen + clen*clen - blen*blen) / (2*alen*clen);   // law of cosines
c /= clen;
n = a ^ c;  nlen = n.len();      // bend-plane normal from the CURRENT upper-arm
if (nlen < 1E-6) return;         // degenerate: bail, change nothing
n /= nlen;
```

Two consequences, and they invert the BFVR recipe:

- **There is no pole argument to substitute.** The bend plane is `a ^ c` — the *current* upper-arm
  direction crossed with the shoulder-to-goal direction. So the lever is **whatever sets the upper arm's
  orientation before the solve runs**: the solver inherits the plane from the pose handed to it. Aim
  there rather than looking for a hint parameter that does not exist.
- **Its `goal_normal` is not an elbow hint.** It is applied *after* the two-bone solve, as
  `n = c ^ goalNormal; beta = atan2(nlen, c*goalNormal)` — an end-effector twist correction that aligns
  the hand about the goal axis. Mistaking it for a pole would produce a wrist roll and no elbow change at
  all.

Note also what the degenerate branch does: `if (nlen < 1E-6) return;` — at the singularity it **leaves
the bones untouched**. That is safe, and it is not the same as BFVR's continuous fade: the elbow holds
its previous pose rather than settling toward an anatomical one, so the arm can sit visibly wrong while
never visibly snapping.

### A projected fixed direction has TWO singularities; a cross product has one

FarCry2-VR implemented the blend-not-branch rule above and found a better construction underneath it.
This supersedes the fixed-direction approach for the ordinary case, and their numbers are worth the
space. `[SOURCE]` *(flat-measured on a 0.30/0.28 m arm; this lane has not yet run in a headset.)*

**The defect: projecting a fixed direction onto the plane perpendicular to the arm is degenerate in two
places — along that direction and against it.** Every choice of fixed direction therefore buys one
singularity and sells you another somewhere else:

| Fixed direction | Where the second singularity lands | Measured cost |
|---|---|---|
| Pure down | **The hanging rest pose** — the commonest pose an arm holds | 95 mm elbow jump sweeping the hand through it |
| Down-and-back | Fixes the rest pose, moves the antipode onto **aiming up and forward** | Elbow rose **131 mm above the shoulder-hand line** at target (0, 0.15, 0.20) — a chicken wing in the one posture the lane exists to prevent |

**A cross product has no antipode.** Build the pole perpendicular by construction instead of projecting
something into perpendicularity:

```cpp
pole = cross(armAxis, sideAxis);   // perpendicular by construction; no residue to normalise
```

It degenerates only where the arm points **along the side axis** — straight out sideways — which is a
pose nobody holds a weapon in. One singularity instead of two, and you get to choose where it sits.

Their measurements after the change: rest-pose sweep **95 mm → 1.8 mm**, and the old antipode
**236 mm → 1.1 mm**. It is also anatomically correct everywhere they checked without any tuning:
forward → elbow down, hanging → back, up → forward, behind → up.

This **subsumes the blend rather than replacing it** — keep the continuous fade for the one remaining
degenerate case. See [HAND-006](pattern-catalog.md#hand-006).

#### The threshold hid a worse bug one step earlier

Their original guard was `if (poleLen < 1e-3) use_fallback()`. The flip argument above holds, but the
failure that actually dominated was upstream of the branch: **just above the threshold they were
normalising a near-zero vector**, so the elbow direction was amplified floating-point noise before the
branch was ever reached.

> The threshold did not protect that region. It only hid where it ended.

**Treat a magnitude threshold as marking the end of a bad region, not the start of a good one.** The
branch is the visible half of a two-part defect; the noise-amplification half is silent and larger.

#### Use the quantity you already have

They dropped the two geometric blend factors in favour of `poleLen` itself, because **`poleLen` *is* the
sine of the angle between the pole and the arm axis** — the same quantity, already computed, with no
extra constants to tune. Equivalent, cheaper, one fewer thing to get wrong.

#### Handedness does not carry to a cross-product solver

A correction to what this playbook previously said, and it cost them a test. "Sign-mirror the left arm"
is right for the ordinary-case bend in a **projection** solver. Applied to a cross-product fallback it is
**inert by construction**: at the singularity the arm lies along the side axis, so a mirrored x component
lies along the arm and the perpendicular projection removes it exactly.

They had a passing test asserting the two arms' fallback elbows were mirrored. **It was asserting an
invention** — parameter and test both deleted. Both arms swing about the same world axis, which is
correct: hanging arms both put the elbow behind, forward arms both put it below, no handedness anywhere.

**A test that passes against a parameter with no effect is worse than no test**, because it certifies a
property the code does not have. Compare [TEST-002](pattern-catalog.md#test-002).

### The CryEngine finding is generation-scoped — CE3 replaced it entirely

PreyVR tested the vocabulary above against `PreyDll.dll` and **it does not survive**: no `IKSolver`,
`SolveIK`, `m_additLen` or `ApplyToBone` anywhere, the only `SetGoal` hits unrelated (network
serialisation and a turret), and the Chairloader PDB headers carry **no `CryAnimation` directory at all**
with zero `IK` matches across 1,131 files. `[STATIC]`

**So the `goal_normal` trap is real for the Far Cry 1 generation and absent by CryEngine 3.** Do not
carry it forward to a CE3-derived target; there is no such function to mistake.

What CryEngine 3 has instead is a **data-driven pose-modifier stack** — `CPoseModifierSetup`, serialised,
with modifiers registered by name. The two-bone descendant is there under a different identity, and so is
something better:

```text
AnimationPoseModifier_Ik2Segments      <- the two-bone descendant
AnimationPoseModifier_LimbIk
AnimationPoseModifier_IKTorsoAim / _PoseAlignerChain / _ConstraintAim
AnimationPoseModifier_Recoil / _PoseBlenderAim / _PoseBlenderLook / _LookAtSimple
IKLIMB_LEFTHAND   IKLIMB_RIGHTHAND   CreateIKLimb   IKLimbs
LimbIK_Definition   IK_Definition   AimIK_Definition   LookIK_Definition
a_poseAlignerEnable / ForceLock / ForceNoIntersections / ...   (7 cvars)
```

`IKLIMB_LEFTHAND` / `IKLIMB_RIGHTHAND` alongside `CreateIKLimb` is a **named per-hand IK facility with a
factory entry point** — an override the engine already honours, reachable without hooking anything.

**The transferable lesson is about method, not CryEngine.** A lineage oracle gave the wrong *names* and
still found the right *thing*, because what transferred was the shape — a two-bone solve, a limb concept,
a definition format — not the symbols. Expect the vocabulary to fail and the structure to hold.

!!! warning "Grade this as a lead, not a fact, for any Dunia target"

    Far Cry 1's `CryAnimation` is a **source oracle** for the Dunia lineage, not Dunia itself — Dunia
    forked from CryEngine and Far Cry 2 shipped years later, with its own animation work in between.
    Treat the signature, the parameter meanings and even the presence of this solver as `INFERENCE`
    until they are confirmed against the shipping binary, exactly as
    [the source-owned route requires](source-owned-route.md#hybrid-handoff-rule). The useful part of the
    oracle is the **vocabulary and the shape** — `SetGoal`, `ApplyToBone`, `m_additLen`, a bend plane
    from `a ^ c` — which is what makes the descendant findable.


## Foreground lighting rides the same reference-frame contract

Posing a viewmodel by changing only its `worldViewProj` leaves its *lighting* inputs in the old
authored orientation, so the model moves but its shading doesn't follow. The eye position, light
vectors, and normal basis are companions of the pose, exactly like the projection companions in
[09](09-d3d11-openxr-injection.md).

- *BioshockVR:* correcting the pose required also fixing, in the cloned private-eye cbuffers, the
  wrench's `localEyePos`/`light_vector`/`invradius` and the arm's `localEyePos`/`localToWorld` — each
  keyed to the exact `indexCount`/buffer-size pair. Note the viewmodel here is drawn *into the HDR
  scene target* before the LDR HUD, so it's a scene-depth participant, not a late 2D overlay — which
  is also why it interacts with the shadow-depth buffer at all. Identify which kind you have; the fix
  differs.

## Don't fix the visible model by retuning the invisible systems

Projectile aim, hitscan direction, and the visible weapon model are **separate surfaces**.
They often share inputs but must be tuned independently:

- The world-space aim ray (projectile origin/direction) wants to be controller-authoritative
  and is usually already stable.
- The visible model is a rendering-frame problem.
- Retuning projectile aim to fix the model's look (or vice-versa) just couples two things that
  should stay decoupled and creates a whack-a-mole. (*SS2VR registry: multiple entries.*)

**A related half-measure: an animation's blend weight, playback rate and playback position are three
separate levers, and "freeze at pose X" needs all three.** Suppressing weight alone leaves the others free
to reset on the next state transition — usually to the bind pose. (*BioshockVR zeroed the idle-animation
weight to stop unwanted hand motion and instead exposed the raw straight-finger bind pose, because every
fresh idle handle still restarted at authored time `0.0` with rate and weight `1.0`, flashing the forward
pose for a frame. The fix used the native skeleton's position and rate setters to seek channel 0 to a
chosen authored time and hold the rate at zero.*) If the engine gives you a pose you want, own all three
levers or you have not actually taken it.

## Authored offset or live delta — composition order decides which

Every attach-to-tracked-controller system combines two rotations: a **fixed authored offset** (the grip
mount, the trim you calibrated) and a **live tracked delta**. Which side of the multiply the offset lands
on decides whether it is a *basis change* or a meaningless residual — and getting it wrong produces a
symptom that looks exactly like a sign error and cannot be fixed by flipping signs.

(*BioshockVR loaded a +90° grip-yaw offset correctly — confirmed in its own logs — and the user still saw
the wrong neutral pose, because the offset was applied additively **after** the live controller rotation.
The fix was to compose it as `currentController · authoredMount`: a real basis change applied **before**
the tracked delta.*)

**The diagnostic that identifies this class:** tune the parameter to both extremes. (*The same project
tried `+90000` and `-90000` millidegrees; the model sat quarter-turned one way, then quarter-turned the
other. Neither was closer.*) **If both extremes of a signed parameter fail symmetrically, the model is
wrong — not the sign.** Stop bisecting and go and re-derive which transform the value belongs to. A finer
sign-and-magnitude search on a wrong basis converges on nothing.

Decide once, explicitly, and write it down: **are authored offsets baseline or overlay?** Every attached
thing — weapon mounts, tool grips, held props — must answer it the same way.

## Euler/quaternion traps (the recurring math failures)

- **Two heading conventions, 90° apart.** Most engines have a "world heading" (for view-
  relative things you reconstruct yourself) and an "engine heading" (for native object facing /
  projectiles), and they swap the `atan2` argument order. Picking the wrong one puts things
  exactly 90° or 180° off. Single-source both as named helpers; never inline `atan2`.
- **Per-axis scalar calibration doesn't work for orientation.** Negating individual
  quaternion components, or band-aiding Heading/Pitch/Bank one axis at a time, cannot solve a
  pitch-invariant screen-local aim — the axes are coupled. Build a full basis (forward/right/up)
  and convert once.

  This is the single most expensive rule in this chapter to learn the hard way, and it does not
  announce itself: each individual correction *improves* the case in front of you, so the failure looks
  like slow progress rather than a wrong approach. (*SS2VR's flat-aim weapon-roll investigation runs to
  roughly twenty consecutive numbered attempts in its own registry — inverse-cos heading plus bank
  cancellation, bounded bank cancellation, screen-axis heading/bank decomposition, per-component
  quaternion negation, screen-up proxy roll signs, several rounds of Euler tuning — before the frame
  itself was fixed. BioshockVR reached the same conclusion independently by measuring it: a single
  trim that looks perfect at one orientation diverges by 28.21° at 180° of roll.*) If you have corrected
  the same rotation more than twice, stop correcting and go find the frame.
- **Bank/roll cancellation near vertical.** Inverse-cos heading + bank corrections blow up or
  cancel near ±90° pitch. Use a screen-up Gram-Schmidt basis, or compute bank from the
  controller's up vector projected off the forward axis, not from Euler decomposition.
- **A single wrong term in a quaternion-to-matrix conversion will pass visual review.** These typos are
  copy-paste-adjacent (the same variable reused one line down) and the resulting error is *proportional
  to angle* — identity looks perfect, and the skew only appears at the extremes where testers stop
  looking. (*SOMAVR shipped `2*y*y` where `2*x*y` was required in the XY cross-term, progressively
  shearing the view basis as the headset rotated; it entered during a math-extraction refactor, not as a
  logic error.*) Camera math is one of the few places in a mod that is **pure and therefore unit-testable**
  ([09](09-d3d11-openxr-injection.md)) — so test it: assert the generated basis stays unit-length and
  mutually orthogonal, and assert matrix rotation agrees with an independently implemented
  quaternion-vector rotation. "Looks right in the headset" cannot catch this class.
- **Fixed-width integer angles don't add like floats.** Unreal-family rotators are 16-bit integer angle
  units, not degrees, and per-axis `+=` is not rotation composition — it happens to look right for a
  single-axis test and breaks the moment a real headset contributes pitch, yaw and roll together.
  (*DishonoredVR's camera-offset code does `pitch += / yaw += / roll +=` against a UE3 rotator, correct
  only for its planned yaw-only test at `1024` units, and missing the `& 0xFFFF` wrap so the sum can leave
  the representable range entirely.*) Two separate bugs in one line: compose rotations properly **and**
  wrap explicitly. Chapter [11](11-re-anchoring-and-discovery.md) covers the reading half of this trap —
  the same integer rotators read as floats print as denormal zeros.
- **Know your `GetFacing` field order.** Engines lie about this. (*SS2VR's Squirrel
  `Camera.GetFacing()` returns `(bank, pitch, heading)`, not `(heading, pitch, bank)` — proven
  by live logs, and the source of a whole class of "diagonal" bugs.*) Verify with data, write
  it down, never assume.

The two traps named above, as the code that avoids them:

```cpp
/* TRAP 1: Euler round-tripping. Converting quat -> euler -> quat to apply a trim
   loses the gimbal-locked axis and flips sign near +/-90 degrees. If your trim is
   authored in degrees, convert it ONCE at load and compose as quaternions. */
struct Trim { Quat q; Vec3 t; };

Trim LoadTrim(const Vec3& eulerDeg, const Vec3& offset) {
    return { QuatFromEulerXYZ(eulerDeg * kDeg2Rad), offset };   // once, at load
}
Mat4 ApplyTrim(const Mat4& base, const Trim& tr) {
    return base * Mat4FromQuat(tr.q) * Mat4Translate(tr.t);      // never back to euler
}

/* TRAP 2: quaternion double-cover. q and -q are the SAME rotation, so a naive
   lerp/slerp between them takes the long way round -- a 350-degree spin where
   10 degrees was intended. Presents as a one-frame flick on fast wrist motion. */
Quat SlerpShortest(Quat a, Quat b, float t) {
    float d = Dot(a, b);
    if (d < 0.f) { b = -b; d = -d; }          // <-- the whole fix
    if (d > 0.9995f) return Normalize(Lerp(a, b, t));   // near-parallel: lerp is stabler
    float th = std::acosf(d);
    return (a * std::sinf((1 - t) * th) + b * std::sinf(t * th)) * (1.f / std::sinf(th));
}
```

The double-cover flick is worth recognising on sight: it is **always** a fast, single-frame, roughly
full rotation, and it correlates with angular speed rather than position. Nothing else in a VR hand
pipeline produces that signature.

## Hiding the original viewmodel

If you replace the weapon with your own proxy, hiding the engine's original is its own
problem. A "don't draw" flag is not guaranteed to work; engines re-assert it. Tiny-scaling the
original (reversibly, restoring on exit) is often more reliable than fighting a draw flag —
but test it, because some engines clamp or ignore scale too.

## Lighting an attached/spawned object

An object you spawn yourself may have **no lighting state** if it has no archetype (a blank
"create empty object" call). Engine lighting often attaches to the archetype/class, so a blank
carrier renders fullbright or black regardless of material. Clone a real, already-lit archetype
and override its model/mesh, rather than building a bare object. (*SS2VR: the bright-white hand
was partly this — though the deeper cause was a material-header bug, see doc 05.*)

## Held tools and physical manipulation: drive the native system, share one basis

- **A tool with both a visual and a gameplay effect must drive both from one tracked basis.** A
  flashlight, welder, or scanner usually has a rendered cone *and* a gameplay ray (what it illuminates
  for AI, what it hits). Point only the visual and the gameplay ray lags; point them from separate
  sources and they disagree. (*SOMAVR: the controller flashlight's rendered matrix and the
  low-frequency AI/gobo physics rays share one cached tracked basis, so controller yaw/pitch/roll moves
  gameplay aim without collapsing the engine's own random cone spread or altering ray length.*)
- **For grab-and-move physics, drive the engine's own manipulation solver, don't replace it.** (*SOMAVR:
  the grab bridge substitutes a controller-relative target into SOMA's native force/torque PID and uses
  a one-shot native impulse for throws, without retuning PID gains, object mass, collision, or joints —
  so held objects keep their authored weight and collision.*) This is the [drive-the-engine's-own-systems](07-engine-integration-safety.md)
  rule applied to hands: the engine's physics already knows how to move a grabbed object correctly.

## Per-item *data* is not per-item *code* {#per-item-data-not-code}

Two projects appear to contradict each other on weapon posing, and resolving it produces a better rule
than either. `[SOURCE]`

BFVR states flatly that it **will not carry bespoke pose code or calibration per item** - one generic
route, proven on a default weapon, validated on a contrasting one. CallOfDuty4_VR ships a profile system
sized for **128 weapon profiles and 32 gunstock profiles**.

They are not in conflict, because they are refusing different things:

> **Per-item code multiplies the paths you must maintain and test. Per-item data in a bounded, uniform
> schema is a table.**

CallOfDuty4_VR's profiles are exactly that - every entry is the same `Pose { offset[3], angles[3] }`
shape, fed to one code path. It is the same distinction as
[ForerunnerVR's per-title *modules* versus Luke Ross's per-game *data directories*](18-beyond-the-native-injector.md#family-seam):
one adds branches, the other adds rows.

**Bound the schema, because a live-tuning UI wired to a pose system is how NaNs happen:**

```cpp
constexpr std::size_t kMaximumWeaponProfiles   = 128u;
constexpr std::size_t kMaximumGunstockProfiles =  32u;
constexpr float       kMaximumOffsetInches     = 12.0f;
constexpr float       kMaximumAngleDegrees     = 90.0f;
```

Hard limits on count *and* on every field. An offset of 12 inches is already absurd for a held weapon;
the constant exists so that a slider, a corrupt config or a bad import cannot produce a pose the renderer
has to cope with.

**The gunstock profile is a category worth knowing about**: a separate `shouldered` pose, selected when
the player is using a physical stock accessory. The same weapon has a different correct offset depending
on hardware the game cannot see, which is an argument for the data table rather than against it.

**So: refuse per-item code, and expect per-item data.** If you find yourself writing a second code path
for a second weapon, that is BFVR's warning. If you find yourself with a table of offsets, that is
normal and it should be bounded.

## Motion gestures: three implementations, one recipe {#motion-gestures}

Turning physical motion into a game input is the mechanic most likely to be written twice. Three projects
in this survey built one independently, and their disagreements are as informative as their overlap.
`[SOURCE]`

### Measure over a window, and measure rotation too

GTFO_VR_Plugin's `VelocityTracker` keeps a **queue of pose history over a target duration** — 50 ms —
rather than differencing the last two frames, and it tracks two quantities per sample:

```csharp
positionalVelocity = ((position - prev.position) / deltaTime).magnitude;
angularVelocity    = Quaternion.Angle(prev.rotation, this.rotation) / deltaTime;  // degrees
```

**A single-frame delta is noise**, and a swing that accelerates through one frame boundary reads
differently from the same swing a frame later. The window smooths that away.

**Angular velocity is not a refinement, it is a second gesture axis.** A wrist flick is high angular and
low positional; a thrust is the reverse. A detector that only sees translation cannot tell them apart,
and will fire on one while ignoring the other.

### Difference your own pose funnel, not the runtime's velocity

BioShock-Trilogy-VR deliberately finite-differences the poses coming through its own input funnel rather
than reading `XrSpaceVelocity`, and states the trade openly: the runtime's velocity would be *marginally*
more accurate and **invisible to every replay tool they own**. Because the funnel is what their session
recorder injects onto, a replayed session drives the gesture exactly as it drives the ray, the viewmodel
and the laser.

**Accuracy you cannot replay is worth less than accuracy you can.** This is the same trade as
[building the control before asking for the test](06-debugging-methodology.md#build-the-control).

### Hysteresis *and* a cooldown, because they catch different things

One motion accelerates and decelerates through the threshold, so **without a re-arm latch a single
gesture fires twice**; a cooldown separately bounds a shake. Report **one verdict per gesture, not per
sample** — their first build logged 106 identical "blocked" lines for one simulated swing.

### Gate on identity, never on plausibility

A synthetic input means whatever the game currently binds it to. A swing composing the fire button is a
*shot* when a gun is in hand. So the gate is **"the equipped holdable's class name is X"** — an identity
the mod already maintains — and never a heuristic like "that motion looked like melee."

Every such gate fails **closed** and expires on a staleness budget, so a publisher that stops (world
unload, feature disabled) disarms the gesture rather than latching it open. See
[META-005](pattern-catalog.md#meta-005).

### Put the detector where it can be tested without a headset

Their layering rule is the one to copy, and the temptation it warns against is real:

| Piece | Layer | Why there |
|---|---|---|
| Pose sample, once per XR frame | XR layer | Only place with the frame's poses and predicted display time |
| Threshold / hysteresis / cooldown / pulse | **Core** | The only layer that runs **with and without a headset** |
| "Would this input be legitimate now" | Game adapter | Only the adapter knows what is equipped |
| The synthetic input itself | Input bridge | Gestures are one more producer over the same merge |

> The temptation is to put the detector where its data is born, in the XR layer. **Do not:** that file
> compiles only with the XR backend enabled and its per-frame entry point never runs without a headset,
> so a detector there cannot be tested at all until someone puts a headset on.

Ship a `sim` command that drives the **real decision core**, and give it a repetition count — one
synthetic gesture crosses a threshold once, so without repetitions a sub-second cooldown is untestable
flat. With it, every threshold, gate, latch and cooldown was verified before the feature reached a
headset, and **only the tuning constants needed a human.**

Expose those constants as commands, persisted preset keys and overlay sliders, and have the status
readout report the **peak measured value since the last call** — that is the number a user's "it didn't
trigger" turns into. See [HAND-004](pattern-catalog.md#hand-004).

## Physical reload: the anatomy, from two independent implementations {#physical-reload}

Physical reload - eject the magazine, take a fresh one off the body, insert it, rack the slide -
is the clearest [T4](08-project-process.md) feature there is, and until now the playbook had one
sentence about it. Two mods have now built it properly and documented it unusually well:
**Talemann's RE4VR 2.0** (RE Engine, REFramework, ~31,000 lines of Lua across seven reload files)
and **cyberpunk-vr-port** (REDengine 4, a C++ plugin plus a CET Lua module, thirteen pistols and a
revolver). They share no code, no engine and no framework. `[SOURCE]`

They converge on three decisions and disagree usefully about a fourth.

### 1. The insertion anchor belongs to the WEAPON, not to the hand

Both start here, and RE4VR states the failure it fixes:

> The magazine insert used to start at the **hand position**. If the hand is at an angle to the
> chamber, the straight line runs through the middle of the weapon mesh - and while walking the path
> is wrong as well. With a fixed point on the weapon skeleton the start is **always the same**,
> independent of hand, view direction and walking speed.

So the dock is a **named joint on the weapon plus a local offset**, per weapon:

```lua
M.dock_default = { joint = "_03", x = 0.0, y = -0.092, z = -0.061 }
M.docks = {
    [6000] = { joint = "_03", x = 0.0, y = -0.092, z = -0.061 },  -- Sentinel Nine
    [4002] = { joint = "_03", x = 0.0, y =  0.064, z =  0.051 },  -- Red9: TOP-LOADER, so Y and Z
    [6113] = { joint = "_03", x = 0.0, y =  0.064, z =  0.051 },  -- Samurai Edge, a Red9 clone
}
```

Note the second comment in the real file: the positive signs on the Red9 are flagged as **not a sign
error, explicitly confirmed** - because a top-loader takes its magazine from above. Data that looks
like a bug and is not should say so where the next reader will look.

Cyberpunk reaches the same place from the other end. Its rack axis is **the vector between two of
the weapon's own slots** rather than the bone's local frame:

> The barrel direction is the model-space vector between the front and back slide slots; the free
> hand's travel **projected onto it** is exactly the along-barrel rack distance, because a rotation
> preserves length - so the bone's own local frame never has to be reconstructed.

That is the cheaper of the two derivations and it generalises: **if the weapon exposes two points on
the axis you need, you never have to solve the bone's orientation at all.**

### 2. Per-weapon *data* over one shared mechanism

This playbook already has [per-item data is not per-item code](#per-item-data-not-code); both mods
are a large worked example, and Cyberpunk's index file states the rule as a design constraint:

> Adding a pistol should never mean editing `reload.lua`, the same reason the rig signatures moved
> out to `reload/rigs.lua`.

RE4VR keeps per-`WeaponID` tables and marks the intent inline - several are annotated *"(DATEN, nicht
Logik)"*, data not logic. What lives in that data is the surprising part, because **the weapon
taxonomy is much bigger than "pistol, shotgun, rifle"**. RE4VR carries separate per-weapon tables for:

- **top-loaders** with no magazine at all, loading into a chamber (Red9);
- **break actions** whose "slide" joint is a pitch lever, not a Z-slide;
- **rotary cycles** whose slide joint is a rotating switch (Striker, `joint_01`);
- weapons that need **no cycle after a shot**, and others that need none after a *tactical* insert;
- three different ways a carried shell can exist - a static **sub-mesh part**, a **spawned** entity,
  or a **mesh clone** - because the engine does not represent them the same way;
- weapons where **the engine closes the slide itself**, so the mod must not;
- weapons whose magazine joint hangs off **a different parent** than the rest.

None of that is deducible from the weapon's category. It is per-weapon measurement, and the only
sane place for it is a table.

### 3. Grab thresholds need hysteresis, and zones need a body anchor

RE4VR's magazine holster is a joint plus an offset plus a box, and two thresholds:

```json
{ "joint": "Spine_1", "off_x": 0.301, "off_y": -0.117, "off_z": 0.360,
  "zx": 0.18, "zy": 0.2, "zz": -0.2,
  "grab_trigger": 0.333, "grab_release": 0.363, "smooth": 0.8 }
```

`grab_release` is **above** `grab_trigger` on purpose: one threshold for both directions chatters at
the boundary. Anchoring to `Spine_1` rather than to the camera is what makes the holster stay put
when the player looks down - see [12](12-torso-calculations-and-ergonomics.md#body-model-sequencing).

### 4. Where they disagree: how the magazine gets into the hand

**RE4VR animates the existing magazine.** The mag joint is interpolated from its rest pose to an exit
vector in **local** space over a slide duration, and only then does it fall in **world** space - and
the fall is a *controlled* one, `fall_dist` over `fall_dur`, not free gravity, because "free
gravitation accelerates without limit, so the magazine flies away". The floor is read from the player
body's root so the magazine lands at the feet rather than at a fixed distance.

**Cyberpunk spawns an entity** - and paid for it with a frame. That analysis is the single most
transferable thing in either mod:

> Everything this module computes is MODEL space, and that space is self-consistent by construction:
> the base and every slot come out of the same game state in the same call, so the player's own
> travel cancels out of all of it. One thing leaves that space - a spawned entity. It is placed by
> `SetWorldTransform` against a transform the game state has, while the hand beside it is drawn from
> the pose of the frame being rendered. **The two are a frame apart, and a frame apart IS speed**:
> nothing standing still, a hand's width at a run. The weapon's own parts never had this - the rig
> write puts them in the pose that the same frame draws - **so only entities need correcting.**

Their first correction failed, and the reason is general: they led the placement by the **player
root's smoothed velocity**, which is wrong twice over.

- **The root is not the anchor.** Over a step or a kerb the character controller lifts the capsule
  while the camera and skeleton are eased up after it, so the hand and the root are briefly going
  different ways, and no amount of root velocity describes where the hand will be.
- **A filter has its own lag.** Smoothed over three frames the estimate is right only while the speed
  is steady - which is exactly the flat ground where the problem was already small, and never on the
  bumps, where velocity changes faster than the filter follows.

What worked: **lead by the last observed step of the very point being placed** - root motion, step
easing, arm swing and whatever else caused it - and predict the next step as that one. Two details
carry the idea:

- **No `dt` appears anywhere.** A step is already a per-frame quantity, so a long frame carries
  itself and a variable frame time cannot distort the answer.
- **The second-order term is deliberately not taken.** Predicting the *change* in the step "buys a
  little on a ramp and doubles the noise", and that noise is a difference of two anchors - which
  shows up as the magazine shaking against a hand that is not.

They also measure their own staleness rather than guessing it, by reading the same quantity at two
points in the frame - the engine's player position at the store site, and the script's own read - so
the difference between them "carries no systematic part at all and is time and nothing else".

And they name why the obvious route cannot do it: the composed view position sits about a metre below
the real camera, which put the gun 0.397 m from the hand holding it. **A round trip through that
transform is exact because both directions share the error; a one-way use of it is not.** That is
worth remembering well outside reload code.

### The insertion itself: a line, a depth, and poses along it

The magazine's path into the well is not a point-to-point animation and it is not a physics problem.
Cyberpunk models it as **a measured straight line with the hand pose keyed to depth along it**, and
the whole thing is per-weapon data:

```lua
wellAxis   = { 0.0002, -0.3285, -0.9445 },  -- unit, pointing OUT of the well
insertRun  = 0.115,                          -- m the magazine travels, from the animation
seatAt     = 0.70,                           -- catches at 70% in, and lets the hand go
poseStages = {
    { d = 0.115, pose = 'unity_mag_left_d115' },
    { d = 0.080, pose = 'unity_mag_left_d080' },
    { d = 0.050, pose = 'unity_mag_left_d050' },
    { d = 0.025, pose = 'unity_mag_left_d025' },
    { d = 0.000, pose = 'unity_mag_left_d000' },
},
```

Four things in that block are worth copying exactly:

- **The well is a line, and its straightness is measured rather than assumed.** They read the
  magazine bone's own travel out of the game's insertion animation - 115 mm to the seat - and
  checked it: *"every sample between 10 and 60 mm out lies within 1.6 deg of it."* A stated residual
  is what makes "it is a straight line" a finding instead of a convenience.
- **The pose is a function of depth, not a swap between two grips.** Their note on the recorded pose:
  *"The animation does not swap between two grips, it rolls through them: fingers around the
  magazine on the way in, palm on its base at the end."* Stages plus interpolation give you that
  roll for free, and one pose cannot.
- **The seat is short of the bottom.** `seatAt 0.70` catches the magazine at 70% and releases the
  hand; it had been 0.80, and 80% *"meant pushing the magazine visibly too far into the well."* The
  hand stops before the geometry does.
- **The magnet is asymmetric on purpose.** The catch stays narrow, the release is 2.2x wider, and
  the pull saturates sooner - because *"a weight that fades to nothing at the edge let a small
  sideways move start a slide out of the well - less pull, more drift, less pull again."* A symmetric
  attraction well has a runaway at its rim.

**And the recorded pose is a starting point, not an answer.** Theirs is captured from the game's own
reload and then *tuned in VR and baked back*, because **the animation's hand re-grips the magazine
mid-motion and a tracked hand cannot** - so several joints are curled harder than the take has them.
The tuning is **angle-scaled**, keeping the recorded direction of every joint and only moving further
along it, which is what stops a hand-tuned pose from drifting into something the animation never did.

### What to steal, in order

1. **Dock on the weapon, offset per weapon.** Cheapest fix, biggest visual payoff, and it removes the
   walking artefact for free.
2. **One mechanism, a table per weapon** - and expect the table to grow columns you did not predict.
3. **Hysteresis on every grab threshold**, and body-anchored holster zones.
4. **Keep the magazine in the same space as the hand** if you can. If it must become a world entity,
   correct it by its own last step, and never by root velocity.
5. **Measure travel from the weapon's own animation asset, not from one reload.** Cyberpunk reads the
   Lexington's slide travel as 52.6 mm from `empty_reload` while the recorded takes only reach 44.7 -
   "the asset supports 52.6 and the reload uses most of it".
6. **Say which numbers are measured and which are transferred.** Their Lexington config marks the
   wrist pose as transferred rather than measured, "because it is the one number here that no
   measurement of this weapon could give" - the fingers are exact, the wrist is borrowed, and the
   file says so.

**Two traps worth naming before you hit them.** A part that rides on the slide is often **not on a
fixed ratio** - the Lexington's `barrel_top` follows 1:1 to 29.5 mm and then stops while the slide
runs on to 52.6, so it carries a `cap`, and a ratio fitted to the deep end "would lag visibly through
the whole first inch". And a pose referenced by name but never loaded is a **silent** failure: it
stays nil and every guard that reads it simply never fires. That one caught two weapons in Cyberpunk
before the rule became "a new place to name a pose is a new line in the loader, in the same commit".

## Holsters and physical grab, from the two native-VR interaction stacks {#holsters-and-grab}

Skyrim VR and Fallout 4 VR shipped *as* VR, so their mod scenes never had to solve stereo - they went
straight to the interaction layer and stayed there for years. That makes them the best available
references for [rungs 2-4](#weapon-census) of the reload staircase, and the two stacks are
independent solutions to the same problems: **VRIK + HIGGS + PLANCK** on Skyrim, **FRIK + Heisenberg**
on Fallout 4. `[SOURCE]` (annotated configuration; the plugins themselves are binary, and FRIK's code
is upstream at `github.com/rollingrock/Fallout-4-VR-Body`).

### There are three ways to put an object in a hand, and they fail differently

This is the taxonomy the fleet was missing. All three are in use across the mods now surveyed:

| Route | How | Cost |
|---|---|---|
| **kinematic, local** | animate the object's existing joint in the weapon's own frame | cannot collide with the world; needs no correction at all |
| **kinematic, world** | place a spawned entity by world transform each frame | **a frame behind the drawn hand** - see [HAND-010](pattern-catalog.md#hand-010) |
| **dynamic, motor-driven** | keep the body DYNAMIC and drive it at the hand with a 6-DOF spring | collides naturally; needs tuning, and can run away |

RE4VR takes the first, cyberpunk-vr-port the second, and **HIGGS took the third** - Heisenberg's
config still names it *"HIGGS-style HeldBody grab (object stays DYNAMIC)"*, with a hard guard beside
it: *"never KEYFRAME the grabbed body while motor constraint is active."*

Two things make the dynamic route work, and both are counter-intuitive:

- **The grip firms up over time.** Angular tau ramps from `0.10` at grab onset to `0.65` steady state
  over `0.30 s`, linear likewise. A spring that starts at full strength snaps the object into the
  hand; one that starts soft is what makes a grab feel like a grab.
- **The spring is clamped, not trusted.** Soft 6-DOF limits cap drift at `40` game units of stretch
  and `90` degrees of twist, *"to prevent runaway stretch/twist"*. A motor chasing a fast hand
  through geometry will otherwise find a configuration it cannot leave.

Note what the dynamic route buys for free: **it does not care that its target is a frame old**,
because it is chasing rather than being placed. The frame-lag problem that cost cyberpunk-vr-port two
attempts is a property of kinematic world placement, not of held objects in general.

### The holster data model, as VRIK settled it

VRIK enumerates **fourteen anatomical slots** rather than arbitrary offsets:

> 1=Left Hip, 2=Right Hip, 3=Left Thigh, 4=Right Thigh, 5=Left Calf, 6=Right Calf,
> 7=Left Upper Arm, 8=Right Upper Arm, 9=Left Forearm, 10=Right Forearm,
> 11=Left Shoulder, 12=Right Shoulder, 13=Stomach, 14=Chest

and each slot carries, as data: **a pose** (`posX/Y/Z` plus `rotA..rotI`, a raw 3x3 matrix), **which
hand may reach it** (`0=both, 1=left only, 2=right only`), and **which item classes it accepts**
(small / medium / large / ranged / shield / torch).

**The hand assignment is cross-body by default, and that is the finding.** Slot 1 (Left Hip) is
right-hand-only; slot 2 (Right Hip) is left-hand-only. Anatomy, encoded per slot rather than assumed
by the mechanism - and it is the sort of thing a mod invents wrongly and never revisits.

The rotation is stored as nine raw floats because **nothing hand-edits it** - see the calibration
point below.

### Hysteresis on the grab threshold, now on three engines independently

The fleet has hit this from three directions and every one of them separated entry from exit:

| Mod | Enter | Leave |
|---|---|---|
| VRIK slots | `slotActivationDistance` | **x1.75** (`slotChangeDistanceMultiplier`) |
| RE4VR mag holster | grip `0.333` | grip `0.363` |
| SS2VR `manualReload` | grip `0.55` | grip `0.30` |

Three mods, three engines, three teams, same discipline. **Treat a single threshold on a grab as a
defect on sight.**

### An invisible zone needs a discoverability channel, and it should be conditional

A holster the player cannot see is a holster they cannot find. VRIK answers with both channels and
gates each one:

- **Hover spheres** with configurable scale, opacity and colour - shown **while sheathed**, hidden
  **in combat** by default. Visible when you are looking for them, gone when you are busy.
- **Haptics on hover**, per slot, with a three-state switch: disable / enable / **enable when
  empty**. Feedback about an *affordance* rather than about an object.

Heisenberg's activators do the same in distance instead of state: **a pointing radius of ~25 cm where
the hand pose changes, and an activation radius of ~8 cm where the action fires**. The hand tells you
what is about to happen before it happens.

### Calibrate anything spatial from inside the headset

Both stacks ship an in-headset placement mode, and it is the only honest way to answer "where should
this zone be" - a body-relative offset that reads well on a desk is wrong on a person.

> Heisenberg: *"hold A to enter. Controls: R-Trigger=set position, L-Stick=radius, B=save, A=exit."*
> Its activators have a second one: *"hold right thumbstick near activator to set activation point."*

That is also why VRIK stores nine raw rotation floats: the values are written by a UI and read by
code, and no one is expected to type them.

### Two smaller rules worth taking outright

**Give back input you intercepted but did not use.** VRIK's `repeatBlockedInputs` replays a grip or
trigger press that was captured by holster logic and then did not activate a holster. A mod that sits
on the input path owes the game every event it does not consume, and the bug it prevents - a
grip that does nothing because the mod ate it - is nearly impossible to diagnose from the game side.

**Retrieval can be context-aware instead of positional.** Heisenberg's `SmartGrab` reaches behind the
head and returns *the item you probably need*, chosen from game state: a stimpak below 50% health,
RadAway above 25% rads, and **ammo when the magazine is below 30%**. For a reload that is a real
alternative to a dedicated magazine holster - the same gesture, and the arsenal decides what arrives.
It also detects seated play from **HMD height** (`< 110` units) and extends grab range from 100 to
150 units, which is a better answer than asking the player to declare a mode.

## What a mature physical grab actually contains {#grab-depth}

HIGGS is the reference implementation of physical grabbing in a shipped VR title, and its 593-line
configuration is the most complete statement of the problem the fleet has found. Its Papyrus API is
the other half: the vocabulary it exposes is as instructive as the tuning. `[SOURCE]`

### The hand needs a frame, not a position

The first three settings are `PalmVector`, `PointingVector` and `PalmPosition`. **Grab logic is
undefined without a palm direction** - "is the object in front of the hand", "is the palm facing it",
"where does a held object sit" are all questions about a frame, and a controller pose alone does not
answer them. Define it once, per controller model, and everything downstream gets simpler.

### Two cast tiers and a cone, then speed picks the mode

- **Near cast** (`NearCastRadius` / `NearCastDistance`) for a direct grab, **far cast**
  (`FarCastRadius` / `FarCastDistance`) for a pull, plus `WidePullGrabRadius` for the forgiving case.
- **`CastDirectionRequiredHalfAngle`** gates selection by a cone, not by distance alone. Heisenberg
  reaches the same place with a required dot product.
- **Hand *speed* selects the interaction**: `lootSpeedThreshold` and `lootToGrabSpeedThreshold`
  separate a quick swipe (loot it) from a slow approach (grab it), with `lootToGrabLeewayTime`
  covering the boundary. Speed is an input channel, and almost nothing in the fleet uses it.

### Constraint stiffness is contextual, not one number

[HAND-012](pattern-catalog.md#hand-012) says ramp the grip. HIGGS goes further: the tau it uses
depends on **what is being held and what is happening to it**.

| Setting | When it applies |
|---|---|
| `grabConstraintAngularTauBodyStart` | the first moments of a grab |
| `grabConstraintAngularTauBody` | steady state |
| `grabConstraintCollidingAngularTau` | **while the held object is in contact with the world** |
| `grabConstraintAngularTauActor` | the held thing is an actor, not an object |

The colliding case is the one worth stealing outright: **soften the constraint while the object is
colliding**, and a held object stops fighting the world instead of tunnelling through it. There are
matching linear settings, plus `grabbedObjectMinInertia` and `grabbedObjectMaxInertiaRatio` to keep a
pathological inertia tensor from destabilising the solver, and explicit recovery velocities for how
fast a displaced object returns to where the hand wants it.

### Grabbing from a pile must not explode the pile

`GrabFreezeNearbyVelocityTime`, `NearbyGrabBodyRadius`, `NearbyGrabMaxLinearVelocity`,
`NearbyGrabMaxAngularVelocity` and matching damping: **when a grab starts, nearby dynamic bodies are
briefly damped and speed-clamped.** Without it, reaching into clutter launches the clutter, and the
player is holding what they wanted in a room that has just exploded.

### Mass propagates back to the player

`slowMovementWhenObjectIsHeld` with mass proportion, exponent, maximum reduction and a fade-out;
`jumpHeightMassProportion` and its siblings; haptic strength with a `GrabHapticMassExponent`.
**Holding something heavy slows you down and lowers your jump.** That is embodiment as a rule rather
than as animation, and nothing in the fleet currently does it.

Grabbing also makes noise the AI can hear (`UseLoudSoundGrab` / `Drop` / `Pull`), which is the same
idea pointed at stealth.

### Physical grab needed the engine's physics loop fixed first

`EnableHavokFix`, `minPhysicsFrameRate`, `maxNumPhysicsStepsPerUpdate`,
`MaxNumEntitiesPerSimulationIslandToCheck`, `EnableShadowUpdateFix`. **A mature physical-interaction
layer is downstream of physics stepping being sane**, and that is a prerequisite to check before
promising the feature, not a polish item afterwards.

### An interaction framework needs a public off switch

Its API exposes `DisableHand` / `EnableHand` / `IsDisabled` and, separately,
`DisableWeaponCollision` / `EnableWeaponCollision`. **Any system that owns the hands must let another
system take them**, per hand, and must expose whether it currently has them. Without that, two mods
fight and neither can detect it. `useVrikWeaponTransform` is the same courtesy in the other
direction: explicit interop with the body mod rather than a race.

### The event vocabulary is the design

HIGGS's Papyrus events are worth copying verbatim as a starting taxonomy:

`OnObjectPulled` · `OnObjectGrabbed` · `OnObjectDropped` · `OnObjectStashed` · `OnObjectConsumed` ·
`OnStartTwoHanding` · `OnStopTwoHanding`

**Pulled is not Grabbed** (summoned to the hand versus taken by it) and **Stashed is not Dropped**
(put away versus released). Two-handing is a first-class *state* with enter and exit events, not a
per-frame query. And `GetGrabbedNodeName` answers **which node of the object is held** - grabbing a
rifle by its barrel is not grabbing it by its grip, and a physical reload needs to know which.

### Body zones: anchored to the HMD, or to the skeleton?

HIGGS defines its shoulder and **mouth** zones as offsets from the **HMD**
(`RightShoulderHmdOffset`, `MouthHmdOffset`, each with a radius); RE4VR anchors its magazine holster
to `Spine_1` on the **skeleton**. Both ship, and the tradeoff is real: an HMD-anchored zone follows
the head and is always reachable in the same way, a skeleton-anchored zone stays put when the player
looks around and is more honest about where the body is. **Choose deliberately and write down which**,
because the failure looks identical either way - a zone that is hard to hit.

## Driving a body with physics: blend, clamp, and give up gracefully {#physics-bodies}

PLANCK drives NPC bodies with active ragdoll so the player can shove, grab, drag and yank them. Its
758-line configuration is the fleet's best statement of what that costs, and most of it generalises
to any physics-driven object. `[SOURCE]`

### Blend between animation and physics; never swap

Every transition in and out of physics control has its own blend time - `blendInWhenAddingToWorld`
and `blendInTime`, `addToWorldSnapTime`, `blendWhenGettingUp` and `getUpBlendInTime`, and separate
fade in/out for the computed world-from-model transform. **A hard swap between animation-driven and
physics-driven is visible every time**, and there are more transition points than the obvious one.

And the constraint parameters are **per phase, not per object**: `poweredTau`, `poweredMaxForce` and
`poweredDaming` while driven, a wholly separate `getUpTau` / `getUpMaxForce` set while standing up.

### Clamp everything, then guard for divergence anyway

`ragdollBoneMaxLinearVelocity` and `ragdollBoneMaxAngularVelocity` cap the solver's output, the same
discipline HIGGS applies to a held object. Beyond that:

- **`maxAllowedDistBeforeWarp`** with `doWarp`, `warpDisableActorTime` and
  `disableWarpWhenGettingUp` - when a body drifts further from where it should be than any recovery
  will fix, **warp it back and disable it briefly** rather than letting the solver keep trying.
- **`playerActorCollisionPhaseThrough*`** - when the player and a body intersect too deeply to
  resolve, **phase through with an alpha fade** instead of pushing. A separate, larger threshold
  applies in combat.

Both are the same idea: **decide in advance what to do when physics cannot win**, because it
sometimes cannot, and the alternative is a body that vibrates in a wall.

### Physics is a distance-gated feature

`activeRagdollStartDistance` / `activeRagdollEndDistance`, plus `minFramesBetweenActorAdds` to spread
the cost of activation. Active physics is an LOD like any other, and the enable band has hysteresis
for the same reason every other threshold in this chapter does.

### Every physical event needs a cooldown

Contact is continuous, so a physical interaction generates events at frame rate unless told not to.
PLANCK carries cooldowns for hits (three of them, including a fallback), shoves, shove *collisions*,
bumps and aggression, plus lingering ignore windows: `thrownObjectIgnoreHitTime` and
`droppedActorIgnoreCollisionTime` stop a thing you just released from immediately hitting you.

### Exclusion lists belong to subsystems, not to the mod

Its API exposes **three separate ignore lists** - `AddIgnoredActor`, `AddAggressionIgnoredActor`, and
`AddRagdollCollisionIgnoredActor`. An actor can be exempt from *aggression* while still being
physically collidable, or exempt from ragdoll collision while still reacting. **One global "ignore
this" would collapse three questions into one**, and the mod would then have no way to express the
common cases.

### Physical interaction needs a consequence model, not just a simulation

This is the part a rendering-focused mod will not expect. Grabbing an NPC in PLANCK **accumulates
aggression over time**, with three thresholds (`aggressionRequiredGrabTimeLow` / `High` / `Assault`),
dialogue at each, a cooldown, a maximum accumulation, and a relationship-rank gate. It **costs
stamina**, with a higher cost for hostiles and a sound on depletion. Holding a heavy actor **slows
the player**, scaled by race size and health.

And intent is inferred rather than assumed: **`aggressionRequiredHandWithinHmdConeHalfAngle`** means
an NPC only takes offence if your hand is within a cone of where you are looking. *Brushing past
someone while looking elsewhere is not an assault* - which is exactly the false positive a naive
implementation ships.

## The weapon census: fill this before you build a reload {#weapon-census}

[Physical reload](#physical-reload) is a mechanism, and a mechanism built against one weapon will be
rebuilt when the second arrives. **The arsenal is the input, and it has to be enumerated first** -
because most of the design decisions are not choices at all, they are consequences of what the flat
game already does.

The fleet already writes a [render pass census](14-render-pass-hazard-atlas.md) and an ownership
census. This is the same instrument pointed at weapons, and it goes in `docs/WEAPON_CENSUS.md`.

**Every weapon gets a row, including the ones that need nothing.** A wrench does not reload; a wrench
still gets a row saying so. Without it, "this weapon needs no work" and "nobody looked at this
weapon" are the same empty space - which is
[partial index silence](06-debugging-methodology.md#partial-index-silence) applied to an arsenal.

### Table A — what the flat game does (observed, before any VR decision)

| Weapon | Engine key | Class | Reload verb? | Implementation | Ammo model | Evidence |
|---|---|---|---|---|---|---|

- **Engine key** is the *engine's own* identifier - archetype id, `WeaponID`, model name, record hash -
  never a display name we invented. Every per-weapon table downstream joins on this, and a table
  keyed on anything else silently stops matching the day a name changes.
- **Class:** `firearm` · `melee` · `energy` · `thrown` · `tool` · `none`
- **Implementation** is the important column, and it is about what the *code* does, not what the
  animation shows:
  - `counter` - an animation plays and an ammo number changes. **No magazine state exists anywhere.**
  - `stateful` - the engine actually models magazine and/or chamber contents per weapon.
  - `recharge` - no reload verb at all; the resource returns over time, at a station, or on pickup.
  - `consume` - each shot draws straight from inventory; there is no magazine step to physicalise.
  - `none` - no reload concept.
- **Ammo model:** `per-weapon reserve` · `shared pool` · `inventory item` · `n/a`. This decides
  whether a partial magazine can be lost, which is a *gameplay* change and needs saying out loud.

### Table B — reload topology (only for rows whose implementation is `stateful` or `counter`)

| Weapon | Feed | Removable unit | Spent unit | Cycle after | Cycle kind | Dock joint | Evidence |
|---|---|---|---|---|---|---|---|

- **Feed:** `bottom` · `top` · `rear` · `side` · `break` · `cylinder` · `belt` · `tube` · `n/a`
- **Removable unit:** `magazine` · `clip` · `charger` · `shell` · `cell` · `battery` · `none`
- **Spent unit:** `object` (something exists that could be made to fall) · `abstract` (nothing
  exists; a dropped magazine must be spawned or faked) · `unknown`. RE4VR needs three different
  answers here across one arsenal - a static sub-mesh part, a spawned entity, and a mesh clone.
- **Cycle after:** `none` · `always` · `empty-only`. **Cycle kind:** `slide` · `bolt` · `pump` ·
  `lever` · `rotary` · `charging-handle` · `n/a`. These are two columns because *whether* you rack
  and *what racking is* vary independently, and `empty-only` is the one most often missed - a mod
  that always racks is wrong on every tactical reload.
- **Dock joint** is the named joint the insertion starts from, per [HAND-008](pattern-catalog.md#hand-008).
  Blank is a legitimate value meaning "not measured yet"; it is not the same as `n/a`.

### Table C — the VR decision (fillable only once A and B are filled)

| Weapon | Treatment | Why | Priority | Blocked on |
|---|---|---|---|---|

**Treatment:** `full` (take a unit off the body, insert, rack) · `simplified` (one gesture stands for
the sequence) · `gesture-native` (a gesture fires the engine's own reload verb) · `button` · `none`.

The order matters and is the whole point of the census. **A treatment is a consequence, not an
opinion** - a `counter` weapon cannot be given a `full` treatment without inventing state the engine
does not have, and a `recharge` weapon has nothing to physicalise at all. Filling Table C first is
how a project ends up building a magazine animation for a weapon that has no magazine.

### Two traps the fleet's first real census hit, on its first pass

SS2VR's census is the worked example, and both of its early corrections generalise. `[SOURCE]`

**An `eject` event is not necessarily a magazine.** The Anniversary Edition's animation table fires
an `eject` event, which reads like exactly the hook a physical reload wants. It is not: **every
`eject` fires inside a `shoot` animation and no `reload` animation contains one.** It is the spent
casing leaving on firing. Magazine removal is expressed purely as joint translation, with no event at
all. A feature that hooks `eject` expecting a magazine fires once per shot and never on a reload.
**Check which animation an event belongs to before believing its name.**

**Searching by the name a human uses will lose weapons.** The census's own rule is to key every row
on the engine's identifier, and the reason showed up immediately: SS2's Laser Sabre has the archetype
`Electro Shock`. Searching the gamesys for *rapier*, *sabre* or *laser melee* returns nothing, and the
tempting conclusion - that the weapon does not exist - is wrong. The display name lives in the
remaster's script layer, the archetype in the engine. **An empty search for a display name is
evidence about the name, not about the arsenal.**

**And a remaster's script layer can add what the original engine never had.** SS2's Dark gamesys gives
the roster, the ids and the ammo items; the AE's Squirrel adds weapon models *and animations* on top.
Reload topology - which joint moves, how far, whether anything cycles - lives entirely in that second
layer. **Either source alone under-describes the arsenal**, and the census needs a source column
saying which answered what.

The payoff is concrete. Read out of the AE table, SS2's arsenal is not one mechanism:

| Weapon | Magazine joint | Travel | Cycles during reload? |
|---|---|---|---|
| Pistol | `joint2` | X 0 → **−2.00** | no - the slide has a single key |
| Assault Rifle | **`joint3`** | X 0 → **+5.00** | **yes**, slide −0.25 |
| Stasis Field Generator | translator + **30 deg rotation** | short | rotary, not a slide |
| Shotgun | none - shell-by-shell | — | pump, and it is in `shoot` |
| Fusion Cannon | none moves | — | no part moves at all |
| Laser Pistol | — | — | **no reload animation exists** |

**The magazine joint index is not constant, and the travel is not even the same sign.** A mechanism
written against the Pistol and pointed at the Assault Rifle drives the wrong joint the wrong way.
That is [HAND-009](pattern-catalog.md#hand-009) arriving one week early, for free, because the table
was read before the code was written.

### The tier below full physical, and it is already shipped

**SS2VR's `manualReload` is the `gesture-native` treatment working today**, and it is worth reading
before building anything larger, because it needs **no per-weapon geometry at all**. A three-state
machine on the left hand, firing the engine's own console verbs:

| State | Entry condition | Action |
|---|---|---|
| 0 → 1 *armed* | grip held, left hand inside `attach_radius 0.42 gu` of the weapon base and `under 0.45 gu` below it | record `startDrop`, haptic pulse |
| 1 → 2 *pulled* | hand drops `pull_down 0.45 gu` below `startDrop` | fire `unload_gun` — **the eject** |
| 2 → fire | hand rises `push_up 0.30 gu` from the deepest point **and** returns within `return_slack 0.18 gu` of the start | fire `reload_gun` — **the insert and slam** |

Cancels on `timeout 1800 ms`, on the hand drifting past `detach_radius 0.95 gu`, on grip release, and
on a `cooldown 900 ms`. Grip uses hysteresis exactly as RE4VR's holster does - `0.55` to arm, `0.30`
to hold.

Three things in it generalise past SS2:

- **It measures the rise from the deepest point reached, not from where the gesture armed.** A
  gesture that must go down and come back needs a running extreme, or a shallow pull followed by a
  big rise reads as a complete motion.
- **The eject and the insert are separate engine verbs** (`unload_gun`, `reload_gun`), fired at
  separate moments, which is what lets the pull and the slam feel like two events rather than one.
- **It is gated to one weapon family by a substring model filter** (default `atek`). That gate is
  correct and it is also the ceiling: without a census there is nothing to widen it *to*, because
  nobody has written down which of SS2's weapons reload the same way.

So the census is not paperwork ahead of the fun part. **It is the thing that turns a working
one-weapon gesture into an arsenal.**

### The staircase from that gesture to a full physical reload

Each rung is shippable on its own, and each is only reachable once the census says which weapons it
applies to. Nothing here needs the rung above it to be designed yet.

| Rung | What the player does | What the mod must own | New per-weapon data |
|---|---|---|---|
| **1 · gesture-native** *(SS2VR today)* | pull down at the grip, push back up | a hand-space gesture and two engine verbs | which weapons the filter allows |
| **2 · eject becomes visible** | same gesture; the spent magazine falls | one spawned or animated object, released at the pull | the mag joint, and whether a spent unit exists at all |
| **3 · the magazine comes off the body** | left hand grabs at a holster, then inserts | a body-anchored holster zone with grab hysteresis, and a held object | holster offset; which ammo type the weapon takes |
| **4 · guided insertion** | the magazine is driven into the well by the hand | the well axis, depth-keyed poses, a seat point, an asymmetric magnet | `wellAxis`, `insertRun`, `seatAt`, pose stages |
| **5 · the cycle** | rack, pump, lever or crank as the weapon requires | the moving part driven along its own axis, with travel and a stop | cycle kind, travel, rest and lock positions |

**Rung 2 is the cheapest large win** and is worth taking before rung 3: it needs no holster, no
grab, and no new input - the gesture already exists, and the only question the census has to answer
is whether a spent magazine is an object that can be made to fall or an abstraction that has to be
spawned. RE4VR's answer for that fall is a **controlled** one, not gravity: an eased local slide out
of the chamber, then a fixed distance over a fixed duration, with the floor read from the player
body's root - because free gravity accelerates without limit and the magazine flies away.

**Rung 5 is where the census pays for itself twice**, because `cycle after` and `cycle kind` are
independent columns: a weapon that racks only when empty and a weapon whose "slide" is a rotary
switch are both ordinary entries in a table, and both are silent disasters in a mechanism that
assumed a slide and assumed always.

## A magnified optic has no exit pupil in VR, and the reticle stops being placeable {#scoped-optics}

The best-argued design document in this survey, and it opens a topic nothing else here covers: what
happens to stereo when the game magnifies the world behind a zero-disparity reticle. `[SOURCE]`

The owner's report is the whole problem in one sentence: *"each eye looks at the scope crosshair from a
different angle and if i shoot based on one of them i will miss my shot."*

### Why it is geometry and not a rendering defect

**A real telescopic sight has an exit pupil** - the optic projects target and reticle into a small cone
behind the eyepiece, and only one eye fits in it. Inside that cone the reticle and target are collinear
along **one** optical axis, aligned to the bore. *"Closing the other eye is not a technique - it is the
consequence of a physical constraint of glass. The shooter does not want one eye; the instrument only
has room for one."*

**In VR there is no exit pupil.** The magnified picture is a screen-space image on a virtual lens, and
both eyes see it from their own position an IPD apart. Two facts then collide:

- the **reticle, lens disc and mask sit at zero disparity** - identical pixels at an identical angle in
  both eyes;
- the **world does not**, and while scoped it is magnified. Their engine narrows the scene projection
  when aiming (measured `1.08 → 2.98` in reciprocal tangent) while the mod pins the submitted field to
  the base frustum, giving an angular magnification `M = 0.9254 / 0.3360 ≈ 2.75x` - **and world disparity
  is multiplied by exactly that M while the reticle's stays at 0.**

So the eyes must fuse a reticle at optical infinity against a target pulled to an apparent depth of
`D/M`. The disagreement is `M · IPD / D`:

| Target range | Reticle-to-target disparity |
|---|--:|
| 20 m | 30 arcmin |
| 50 m | 12 arcmin |
| 100 m | 6 arcmin |
| 150 m | 4 arcmin |

**Panum's fusional limit for fine foveal detail is roughly 6-10 arcmin.** At every range the game is
played at, the crosshair and the animal cannot both be single - one of them doubles.

**And the shot is un-placeable rather than mis-aimed.** Because the eye offset is a pure translation -
`m[12..14]`, with the camera basis rows untouched - a reticle centred using one eye alone puts the
bullet **32 mm laterally off, at any range and any magnification**, not growing with distance. That is
inside the vitals of every animal in the game, so *"the geometry says he should still be hitting. He
misses because he cannot tell where the crosshair is, so he places it somewhere it is not."*

> **The fix must remove the ambiguity, not correct an offset.**

That sentence generalises well past scopes: **when a user cannot tell where something is, precision is
not the problem you have.**

### Their decision, and why the obvious alternatives lose

**While the player is looking down an optic, render both eyes from one camera** - the game's own, the one
the bullet leaves from. Do not blank an eye, do not render the scope to one eye, do not touch the per-eye
crop. It ships behind `scope_mono = 0` by default, so the build is unchanged *"byte for byte"* until
switched on.

Two rejected candidates are worth keeping for their reasons:

- **Render the scope picture to one eye only** - rejected. *"A bright monocular disc inside a fused
  binocular field is a binocular-rivalry generator, not a closed eye - it alternates and drops out at
  0.5-2 Hz."* It also splits the glass and the mask across two code paths that differ *by eye*, and
  leaves the 2.75x-magnified doubling of the whole surround untouched. (Rivalry from monocular content
  is the same failure as [mismatched LOD between the eyes](14-render-pass-hazard-atlas.md#per-view-decisions),
  from the opposite direction.)
- **Blank or dim the non-shooting eye** - *"genuinely works and is cheap"* via
  `XR_EYE_VISIBILITY_LEFT/RIGHT` on a quad layer, and kept as an option, but it costs **binocular
  summation** (the view dims on every scope raise - bad in a dusk-hunting game), the covered eye
  **drifts to its phoria within seconds** so the eyes must re-fuse every time the scope comes down, and
  **an LCD's black is a dim grey field with mura, not an eyelid**. *"It imports the limitation of glass
  without importing any benefit."*

**Suspending stereo deliberately is a legitimate move**, and this is the clearest case for it: there is
no correct stereo answer for a magnified image behind a zero-disparity reticle, so the honest design is
one axis, chosen to be the one the bullet uses. See [HAND-007](pattern-catalog.md#hand-007).

## Write down what the mod does *not* own {#weapon-non-ownership}

BFVR's weapon-presentation design opens with a scope paragraph worth copying almost verbatim, because it
prevents an entire class of argument later: `[SOURCE]`

> A supported first-person weapon will visibly follow the right tracked hand's translation and
> orientation in 3D. It does **not** mean that BFVR manufactures a projectile, changes a hit ray, or
> moves a player in room scale. **BF1942 remains the sole owner of firing, recoil, reload, spread,
> projectile spawning, hit detection, and network state.**

Two consequences follow that are easy to lose once code exists.

**One generic route, no per-item pose code.** They target the shared on-foot infantry presentation
family, prove it with one default weapon, and validate it with a *contrasting ordinary* weapon -
explicitly refusing bespoke pose code or per-item calibration. A per-weapon offset table is a maintenance
burden that grows with the game's content and hides the fact that the generic route was never right.

**Enumerate the states that keep the flat presentation.** Theirs are named: vehicle, mounted weapon,
death, spectator, map/menu, scope, stale input, and lost tracking. Each keeps the original view model
**until its own generic policy is proven.** An enumerated fallback list is what stops "it works" from
quietly meaning "it works while walking forward on foot."

### Valid and tracked are different, and only pose-dependent features may fail

Their transport carries **separate pose-valid and pose-tracked flags**, and weapon motion requires the
head and grip components to be active, valid **and tracked**. The rule they draw from it is finer than
ordinary focus-loss neutralisation:

> A 6DOF presentation layer never silently uses an inferred or last-known pose as precise weapon
> tracking, **while ordinary controller buttons and sticks remain available.**

Degrade the *pose-dependent* feature without degrading the button-dependent ones. A controller whose
tracking is briefly lost can still fire, reload and open a menu; what it cannot do is claim to know where
the barrel is pointing. Compare [XR-002](pattern-catalog.md#xr-002), which neutralises everything - the
right behaviour on focus loss, and too blunt for a tracking dropout.

## Look for the accessor the flat game already routes interaction through {#interaction-origin-accessor}

RepoXR's entire hand-interaction conversion turns on one observation: the game already had a single
accessor for *where interaction originates*, `PlayerLocalCamera.GetOverrideTransform`. Converting to
hand-origin interaction is then a **redirect, not a rewrite** - a Harmony transpiler repoints every call
site to a hand-derived transform, and the same treatment applied to `PhysGrabber.RayCheck` makes grab
rays leave the hand instead of the camera. `[SOURCE]`

**Before writing a hand-interaction layer, search the target for its equivalent.** Any game with a
spectator mode, a security camera, a vehicle camera or a cutscene system probably has one, because those
features needed the same indirection. Finding it converts a sprawling job into a scoped one, and it lands
you on [PORT-10](shared-vr-spine.md#port-10)'s native endpoint by construction rather than by effort.

### Flat-tuned interaction rates usually need retuning, not just re-origining

The same patch halves a hard-coded push/pull rate of `0.2` and multiplies what remains by an analog input
axis - so a fixed rate becomes a slower, player-modulated one. Their comment is simply that it is "way
too fast in VR."

**Rates tuned against a mouse or stick are tuned against a different input.** Expect a pass over
interaction speeds, and prefer converting fixed rates into analog ones while you are there.

### Haptics can ride a channel the game already modulates

RepoXR drives grab haptics from an evaluated curve keyed on **the pitch of the game's own grab loop
sound**, with a second term from the beam's overcharge value, and suppresses the whole thing while a
scripted hold is forcing the grab. `[SOURCE]`

The game was already expressing grab state continuously through audio. Reusing that signal gives haptics
that track the mechanic exactly, for free, and cannot drift out of sync with it - **look for an existing
continuously-modulated channel before authoring a parallel haptic state machine.** See
[HAND-003](pattern-catalog.md#hand-003).

## Grip pose places the model; aim pose points the ray

OpenXR gives every hand **two** poses, and using the wrong one is a calibration bug you will chase for a
session. `/user/hand/*/input/grip/pose` has its forward axis along the controller **handle**;
`/user/hand/*/input/aim/pose` is the runtime's own *pointing* ray. On Touch controllers these are **tens
of degrees apart**.

- **Aim pose → anything that claims to point where shots go**: the fire ray, the laser, the reticle.
- **Grip pose → anything that is physically *in the hand***: the weapon/hand model, contact haptics,
  throw velocity.

(*An independent BioShock mod's first in-headset aim test read low for exactly this reason — the ray was
built from the grip pose. See [13](13-teardown-bioshock-vr.md).*) Note this cuts against the natural
instinct to use one pose for everything "so they can't disagree" — they *should* differ, because a gun
model sits in your fist while its barrel points where you aim.

## One trim, one algebra, one ray

If the ray, the laser, and the model each apply the "same" calibration trim through *different math*,
they agree only at the orientation you tuned at. This is the single most measurable version of the Euler
trap above:

- Rotator/Euler **adds in world space** commute with rotations about world-up — so they agree perfectly
  at identity and at any pure-**yaw** pose, which is exactly where hand-tuning happens. The error hides
  until you roll or pitch your wrist.
- (*Measured on a 21-pose sweep with identical trims through two chains: `0.00°` at identity and every
  pure-yaw pose, `4–12°` on pitch, and **`10.70° / 19.85° / 28.21°` at 45° / 90° / 180° roll**. After
  unifying both chains onto one quaternion compose in the controller's local frame: `≤0.03°` everywhere —
  the integer-rotator quantization floor.*)

Two rules follow. **Implement the pose→direction conversion once, as a pure function that production and
your test sweep both call** — then a sweep measures the shipping code, and the acceptance gate is
"divergence ≈ 0 at every orientation." And **sweep rolled poses**: an axis-aligned or yaw-only sweep
would have under-reported that defect to near zero.

## The pose you draw and the pose you steer with are different variables

The single most instructive bug in FEAR VR's two-handed grip, and it is a closed loop:

During a two-handed hold the left hand **visually** sticks to the weapon's authored fore-grip, so it
looks like a real grip rather than a hand floating near one. But the weapon is still **steered** by the
*real* controller pose. Their comment says why:

> If the control path used that same visual position, the hand would follow the weapon that follows the
> hand — and the weapon could no longer be aimed at all.

```cpp
// Visible placement: snapped to the weapon's own grip point.
LTVector EffectiveLeftHandPosition() {
    if (LeftHandOnWeapon())
        return g_weaponAim.gripTransform.m_vPos +
               g_weaponAim.fireTransform.m_rRot.RotateVector(g_twoHandedGrip.grabOffsetInWeapon);
    ...
}

// Control input: ALWAYS the raw tracked pose. Never EffectiveLeftHandPosition().
const FearVrPose& steer = state.handGripPose[FEARVR_HAND_LEFT];
```

**Keep two separate variables and never let the visual one reach the control path.** This is
[07](07-engine-integration-safety.md)'s "never read your own output back as fresh input" in its most
seductive form: the feedback version *looks* more correct — the hand is exactly on the grip — and the
failure is not a visual artifact but a control system that goes limp.

The same rule with a different consequence, one layer down: **an attached light or laser must take its
parent's frame, not its own last frame.** When the hand snaps to the weapon, a flashlight that keeps
following the *hand* rotation points wherever the hand happened to be aimed at the instant of the grab,
and the cone shines sideways. Once the hand is on the fore-grip, the light belongs on the weapon axis.

## Two-handed grip: gate it on geometry, not on the button

A grab button pressed in empty air must not steer the weapon. FEAR VR gates the two-handed hold on the
off-hand actually being *where a fore-grip is*, expressed in the firing hand's aim frame:

```cpp
constexpr float kTwoHandEngageSqueeze         = 0.65F;  // engage above
constexpr float kTwoHandReleaseSqueeze        = 0.45F;  // release below -- hysteresis
constexpr float kTwoHandMinForwardMeters      = 0.05F;  // a hand BEHIND the firing hand
constexpr float kTwoHandMaxForwardMeters      = 0.60F;  // is not a fore-grip; past 60 cm
constexpr float kTwoHandMaxLateralMeters      = 0.22F;  // no weapon has anything to hold
constexpr float kTwoHandMinSteerSeparationMeters = 0.12F;
```

Outside that volume the same button keeps its ordinary meaning (sprint). That is
[03](03-input-and-locomotion.md)'s "don't share a gate" rule applied **spatially** — one physical button,
two meanings, disambiguated by where the hand is rather than by a mode.

**`kTwoHandMinSteerSeparationMeters` is the one to copy blind.** Any direction derived from *two* tracked
points has a minimum baseline below which the direction is tracking noise, not intent. Below 12 cm of
hand separation they refuse to let the hand-line steer anything at all. Without that floor, hands held
close together produce a violently unstable aim axis.

### A hard limit in a tracked path reads as a wall — compress instead

Their first version capped the angle between the hand-line and the weapon axis at a single hard 50°.
Past it the weapon **stopped dead mid-motion**. The user report (28.07.2026) is worth quoting as a design
principle: nobody holding a rifle works to centimetre accuracy, and a wall in the middle of a natural
movement is worse than a slightly wrong result.

```cpp
constexpr float kTwoHandSoftSteerRadians = 0.96F;  // ~55 deg: 1:1 up to here
constexpr float kTwoHandMaxSteerRadians  = 1.57F;  // ~90 deg: approached, never reached
```

Up to `Soft` the weapon follows one-to-one; beyond it the excess is squashed asymptotically toward `Max`.
Poor holding still has less effect, but **nothing ever blocks, and there is no point at which the weapon
stops or springs back.**

Generalise it: **anywhere you clamp a continuously tracked quantity, an asymptotic soft limit beats a
hard one.** A hard clamp is felt as a collision with an invisible surface; a soft one is felt as
resistance, which is what the player expects from a physical object anyway.

### Solving the pivot

Once the rotation is solved, making the support hand the pivot is a translation — no scaling, and the
distance between the two grips is preserved:

```cpp
// Move a rigid two-grab object so its (already rotated) secondary attachment
// lands on the tracked secondary hand. Units arbitrary, as long as all three match.
predictedSecondary = primaryPosition + rotatedSecondaryOffset;
correction         = (secondaryPosition - predictedSecondary) * influence;   // influence in [0,1]
primaryPosition   += correction;
```

The `influence` term is what lets you blend the effect in and out instead of latching it, which matters
at the engage/release thresholds above.

## A smoothing filter needs an enumerated list of things that must reset it

Simulated weapon weight is a follow filter: the weapon lags the controller, with mass, positional and
rotational follow rates, and a catch-up term. The filter is the easy part. **The shippable part is
knowing every discontinuity that must reset it**, and FEAR VR enumerates them rather than hoping:

```cpp
enum class WeaponWeightResetReason : std::uint8_t {
    none, firstValidPose, enabledChanged, weaponChanged, owningHandChanged,
    trackingLost, trackingReacquired, referenceSpaceChanged,
    teleportedOrRecentered, sceneLoaded, objectRecreated,
    nonPositiveDeltaTime, excessiveDeltaTime, nonFiniteValue
};
```

Every one of those is a case where interpolating from the previous state produces a visible smear: a
weapon that slides across the room after a teleport, a swap that morphs one gun into another, a
tracking dropout that snaps back through the floor. **Write this list before you write the filter**, and
log which reason fired — a filter that resets for an unexpected reason is telling you something about
the engine.

The same discipline applies to any pose smoothing, weight, inertia, or comfort damping you add.

## Order the weapon pose pipeline explicitly, and write the order down

FEAR VR states its ordering as a constraint in the header, not as an accident of call sites:

```text
controller pose
  -> two-handed grip solve
  -> simulated weight (follow filter)
  -> recoil                          <- AFTER weight, deliberately
  -> world collision                 <- AFTER all pose generation
  -> commit weapon, muzzle, laser and shot transforms
```

Two of those placements are load-bearing:

- **Recoil is layered after the weight filter** *"so controller motion cannot immediately erase a shot
  impulse."* Put recoil before the filter and a moving hand smooths the kick away — the gun feels dead
  precisely when the player is firing and moving, which is most of the time.
- **Collision is last, after every pose generator and before anything is committed** — because it is the
  only stage that must be true about the *final* pose. Retract first and then apply weight, and the
  weapon drifts back into the wall.

Recoil itself is a critically damped spring per axis, with the weight profile acting as mass
(`impulse / mass`), so a heavy weapon kicks less and recovers slower from the same shot.

## World collision on a hand-held object: asymmetric, held, and hitch-aware

Three constants carry most of the feel, and none of them is symmetric:

```cpp
constexpr float kWeaponCollisionMarginUnits     = 8.0F;         // clearance kept in front of the surface
constexpr float kWeaponCollisionTightenSeconds  = 0.025F;       // retract FAST
constexpr float kWeaponCollisionReleaseSeconds  = 0.080F;       // release SLOW -- no visible pop
constexpr uint64_t kWeaponCollisionHoldNs       = 90'000'000;   // hold the deepest hit ~90 ms
constexpr uint64_t kWeaponCollisionMaxGapNs     = 200'000'000;  // gap > 200 ms: accept new state at once
```

- **Attack fast, release slow.** Pushing into a wall must respond immediately or the weapon visibly
  penetrates; coming away from it must ease, or every surface exit produces a pop.
- **`HoldNs` exists because a ray at a geometry edge alternates.** Hit / miss / hit / miss across a
  doorframe makes the weapon flicker in and out. Retaining the *deepest* obstruction for ~90 ms
  converts a strobing raycast into a stable retraction. Worth generalising: **any per-frame raycast
  against world geometry will chatter at edges, and the fix is a short hold of the worst case, not a
  smoothing filter over the distance.**
- **`MaxGapNs` distinguishes a hitch from motion.** After a pause, loading screen or alt-tab, the last
  sample is meaningless — accept the new state instantly rather than animating a 4-second-old value
  toward the present one. Any time-based filter that can be suspended needs this test.

## Identify unnamed mesh pieces by isolation — then check what else is in there

Retail `player.Model00p` exposes **four unnamed pieces**, so the one carrying the arms could only be
found by hiding them one at a time, stepped by a debug key.

The interesting part is the correction. Piece #1 did carry the arms — and it is `Body_Group`, which
holds **arms, torso and legs together**. Hiding it removed the arms *and* every visible kick animation.
The fix was to stop hiding pieces at all: keep all four visible, and punch only the forearm regions out
of the shared texture atlas with a locally generated alpha-test material.

**Two rules.** Bisection by isolation is the right way to identify unnamed pieces — but **a piece is a
grouping decided by the artist, not a semantic unit**, so confirm what *else* disappears before shipping
the hide. And when a piece turns out to be over-inclusive, the finer instrument is usually the material,
not the mesh.

## A one-frame fallback is worse than a short staleness window

The weapon manager supplies the shared vertical basis for eyes, hands and weapons every game frame.
On a brief render hitch that value goes missing — and falling back to the camera object's height for
*exactly one frame* and back again is highly visible, especially on the near body.

Their fix is a **500 ms freshness window** that bridges only timing gaps, with real state changes
explicitly invalidating the cached value. **Reuse the last good value briefly rather than substituting a
different source for one frame.** A momentary substitution reads as a glitch; a held value reads as
nothing at all.

## Remember *which object* you hijacked

If you overwrite an engine object's transform and restore it later, store the object handle alongside
the saved transform and verify it before writing back. A cutscene can swap the game camera underneath
you, and restoring a remembered transform into a foreign or already-destroyed object is a corruption bug
that will not look like one.

## Keep left and right hands as fully separate lanes

Two controllers means two of everything — pose, basis, grip gate, visible mesh. It is very easy to
let one hand's state leak into the other's, and the symptom (a hand following the wrong controller)
looks like a tracking bug, not a code bug. (*SS2VR: a grip-gate change stamped the **left**-hand mesh
with the **right**-hand basis when the left wasn't gripping, so the left hand followed the right
controller; the fix was reverting to a pose-only gate that never crosses hands.*) Give each hand its
own basis and gate, and never compute one from the other's "current" value.

## Haptics: hook where the contact actually happens

Good VR touch feedback comes from the engine's own physics/contact events, not from guessing. If the
engine has a physics contact callback, hook it read-only and translate a real collision into a
controller pulse.

- *SOMAVR:* the Newton physics update walks 0x60-byte contact records after each step and dispatches
  `cSurfaceData::OnImpact` / `OnSlide`. The haptics bridge hooks **only `OnImpact`**, always runs the
  game's own handler first, and only then emits a pulse — gated on grab state, a fresh position-tracked
  grip, finite native speed, contact within a configured radius, and a duplicate-callback cooldown,
  with amplitude a bounded linear map of the native normal speed. The original sound, particles,
  physics, and gamepad rumble are never changed.
- Watch the ownership caveat: the engine may hand your callback the *higher-priority material's* body,
  not the one you grabbed. Don't infer "which object" from that pointer — filter by grab state and
  spatial proximity instead, and log body/speed/distance/amplitude so live testing can measure false
  positives.
- Feedback can also be *semantic* rather than physical: SOMA maps its 34-state native crosshair enum
  (carry/push/tool/traversal/…) to distinct pulse shapes, so the controller communicates interaction
  intent. See [04](04-ui-and-hud.md).

## Physical hand/viewmodel collision with the world

Letting a camera-relative viewmodel push into walls looks wrong; clamping it naively looks worse. The
traps are all about *which component* you clamp and *hysteresis*:

- **A wall in front constrains only the forward component of the offset.** The VR hand is a
  camera-relative offset `(forward, left, up)`; scaling the *whole* offset to clamp at a wall slides the
  hand along the eye→hand ray and up toward your face. Clamp only the forward term; leave up/left at the
  true hand position. (*SS2VR v1→v2.*)
- **Clamp proactively with a standoff, and gate the contact state with hysteresis.** A reactive ray cast
  only *to* the hand lets it sink in and pop back across the depth plane (visibility flicker); cast the
  ray a hand-`radius` *past* the target so it stops before penetrating. Noisy raycast depth (±0.15
  between samples) will flip engage/disengage ~2 Hz and machine-gun the contact haptic unless you add
  release hysteresis and ease the applied depth toward a target with a grace window for dropped rays.
- **Long-barrel weapons: pull back by actual overshoot, never a proportional factor.** Using barrel
  length as a clamp radius *inverts* when the barrel is longer than the camera-to-wall distance (the gun
  yanks to your face). Raycast camera→muzzle along the barrel axis and pull the grip straight back by the
  fixed overshoot `(muzzleDist − hitDist)`. (*SS2VR AR15 clip-through-then-pop bug.*)
- **Reject the kinematic-physics-proxy shortcut.** Teleporting a physics body to the hand each frame is
  unstable, and a kinematic body *pushes* props without itself being *blocked*, so it doesn't even solve
  static wall pushback. Impulse-on-contact (dynamic) plus render-pose clamp (static) are the two
  controllable primitives.

## Throwing, knocking, and physical melee

- **Use windowed-peak hand velocity, not instantaneous.** A single smoothed velocity decays at the exact
  release frame, so thrown objects drop straight down. Hold the peak ~150 ms so a thrown object inherits
  the arm's flick; the same peak drives contact-knock feel (slow hand pushes, fast swing sends it
  flying). (*SS2VR `m_handVelPeak`.*)
- **Linear velocity only slides a prop; to *tip* it, set angular velocity ∝ (contactOffset × pushDir)**
  using the tool tip as the lever arm (hit low → topples, hit centre → slides), scaled by
  `refMass/mass` so heavy props don't over-rotate and tunnel. Scripted physics services are often
  linear-only, but writing a rotational-velocity *property* can inject spin the sim integrates with no
  native call.
- **Physical melee beats a timed button, and both projects reached for it.** Detect the swing from grip
  linear/angular velocity with a hysteretic classifier (high threshold + release threshold + cooldown),
  and synthesize the mechanic at the seam you already own. (*BioshockVR classifies a physical wrench
  swing from OpenXR grip velocity without yet injecting an attack. SS2VR synthesizes a parry at the
  enemy→player damage-apply seam — an interpose returns without calling the trampoline so damage is never
  applied, gated on melee range so gunfire can't be parried.*)
- **A single-frame contact test tunnels; sweep a short ring buffer.** Both your blade and the enemy
  weapon move, so a fast swing slips between contact-frame samples. Push each frame's blade segment into
  a small ring buffer and test the incoming attack against every sample in a ~150 ms window, keeping the
  minimum separation — because it only ever *lowers* separation it can only add blocks, never remove a
  legitimate one. (Poor-man's continuous collision, no swept volumes.)
- **AI reactions are usually request/poll, not interrupt — and a damage stim is the wrong lever.**
  Staggering an enemy via a damage stim just kills it on repeated hits; a queued "recoil" request waits
  behind the currently-running maneuver (AI maneuvers play to completion). A real mid-swing interrupt
  must go through the engine's own stun/motion-abort primitive. (*SS2VR: `FUN_1403a15b0` tears down the
  current maneuver, plays a named motion, auto-recovers, non-damaging.*)

## Point the engine's own interaction at your hand, by borrowing the camera

Most flat games run *use*, *activate* and *pick up* from the camera, not from the player body. That is
excellent news: the engine already has an interaction system with correct rules about occlusion, range,
valid targets and networking — and all you have to change is where it thinks the camera is.

(*In F.E.A.R.: `CTargetMgr::CheckForIntersect` fires the activation ray from the camera position and
rotation, and `CPlayerMgr` keeps an `ObjectDetector` FOV cone around the **camera object** for pickups.
Item pickup by activation was already wired to the server, so **no server change was needed** — the
detector just had to follow the hand instead of the head.*)

**The enabling property has to be verified, not assumed.** They checked that `CheckForIntersect` reads
the camera **only in its first two instructions** and works on copies thereafter. That is what makes the
following safe:

```text
wrapper around CheckForIntersect:
    save camera position + both rotation factors
    write the muzzle transform into them        <- second rotation factor -> identity,
    call the original                              so the product is exactly the weapon rotation
    write the saved values back, unchanged
```

If the function had re-read the camera mid-call, or cached a pointer to it, the same wrapper would be a
race. **Read the target function first and confirm when it samples the state you intend to swap** —
this is the same read-then-copy check that makes any borrow-and-restore safe
([07](07-engine-integration-safety.md)).

Four details worth copying:

- **Scope the wrapper to the one instance you mean.** Their `ObjectDetector::Update` hook acts only when
  `this == *g_pPlayerMgr + 0x3CC` — the player's own pickup detector. The same function runs for other
  characters, and a global hook would move everyone's.
- **Raise ranges through the engine's own console variables, not in code.** `ActivationDistance` and
  `PickupDistance` get pushed to about arm's length while stereo is active and restored afterwards — and
  **a larger existing value is never lowered**, so a user's own setting is not silently clobbered.
- **Use the same transform the player can see.** The activation ray is deliberately the muzzle transform
  that already produces the visible laser and the fire vectors, so *what you point at is what you
  activate*. Any separate interaction ray will disagree with the visible one eventually.
- **Guard it where camera hijacking is known to be unsafe** — theirs is disabled during cutscenes and the
  comfort panel, the same boundary the flashlight path respects, because hijacking the camera in scripted
  scenes had already caused a crash once.

And the whole feature fails closed: a startup probe checks the module timestamp, image size and the
first bytes of both target functions. On any mismatch the interaction hooks simply are not installed and
the game runs stock.

## Gesture detection: speed is not a gesture

The naive melee trigger is "hand moving fast". It fires on every retraction, every sweep to look at
something, and every jerk while reloading. FEAR VR requires **two conditions at once** — fast *and*
travelling along the hand's own forward axis:

```cpp
constexpr float kMeleeThrustSpeedMps      = 2.0F;   // forward component, not total speed
constexpr float kMeleeThrustMinAlignment  = 0.64F;  // cos(50 deg): roughly where the hand points
constexpr float kMeleeThrustRearmSpeedMps = 0.8F;   // re-arm only below this
constexpr uint64_t kMeleeThrustCooldownNs = 700'000'000;  // one strike per animation
constexpr uint64_t kMeleeThrustMaxSampleGapNs = 100'000'000;
```

Four properties, each earning its place:

- **Project the velocity onto the pose's own forward axis** and threshold *that*, not the magnitude.
  Direction is what separates a punch from a shrug.
- **Re-arm on a low-speed threshold, not a timer.** One long thrust must not register twice, and a
  velocity-based re-arm handles a slow push and a fast jab identically.
- **The cooldown is set by what the game does**, not by feel: retail plays a melee animation, and a
  faster follow-up produces no second strike anyway. Match the engine's own rate limit rather than
  inventing one.
- **Reject samples separated by more than ~100 ms.** After a loading screen or a frame spike the
  position difference is a teleport, not a thrust — and it will trigger every gesture you have.

### Use your own clock, not the runtime's predicted display time

This one cost them their first implementation, and it is not obvious:

> `nowNs` is the caller's clock, **not** the timestamp from the input state. That
> `predictedDisplayTimeNs` is a *predicted* display time, which can stay the same between two fetches or
> jump. Both make the velocity unusable — with an identical timestamp every sample is discarded.

**A predicted-display timestamp is a scheduling hint, not a measurement of when you sampled.** Any
derivative you compute — velocity, acceleration, angular rate — must be divided by real elapsed time from
a monotonic clock you control. This applies well beyond melee: the same mistake silently breaks throw
velocity, gesture locomotion, and any comfort damping that is framerate-compensated.

### Instrument gestures with two counters that separate the two failures

A gesture that never fires has two completely different causes, and one counter cannot tell them apart:

```cpp
float    peakForwardSpeed{0.0F};   // highest forward component seen since last read
uint32_t evaluatedSamples{0};      // how many samples actually produced a velocity
```

> If `evaluatedSamples` stays zero, it is failing on the time base or the poses. If only
> `peakForwardSpeed` is too small, the threshold is set too high.

That is the counter-pair discipline from [06](06-debugging-methodology.md) applied to input, and it turns
*"melee doesn't work"* — the least actionable bug report there is — into one of two specific answers.

## A gesture is a proposal; game state decides what it means

The same forward thrust is three different attacks in FEAR VR, and the gesture recogniser does not
decide which:

```text
thrust detected on the ground -> queue for 250 ms
    CMoveMgr reports airborne within the window  -> JUMP KICK
    window expires                               -> normal strike
thrust + physical crouch (0.25 m drop within 400 ms) -> SLIDE KICK (1 s cooldown)
grab button held on the free hand                    -> NO strike at all
```

Two ideas worth taking whole:

**Queue the gesture briefly and let the engine's own movement state classify it.** The player jumps *and*
thrusts as one intention, but the two inputs cannot arrive simultaneously. A 250 ms window means you
read the game's actual airborne flag rather than trying to detect a jump gesture yourself — the engine
already knows, and its answer is authoritative.

**Composed gestures need the same context gate as buttons.** The free hand's grab button uses the same
0.65 threshold as sprint, use, two-handed grip and ladder climbing — and while it is held, the free hand
**belongs to another action and cannot strike**. Without that, every ladder grab is also a punch. This is
[03](03-input-and-locomotion.md)'s shared-gate rule again: a physical input means different things in
different contexts, and the contexts must be mutually exclusive by construction.

Read the movement state from the engine where you can. Their melee fields come from retail's `CMoveMgr`,
with an explicit degraded path: *if that state is unavailable, the two basic strikes still work without
the delay.* **A composed gesture should degrade to its simple form, not disappear.**

## Reflex sights are collimated — place the reticle by angle, not on the glass

A red-dot or holographic sight in reality is **collimated**: the reticle is projected to optical
infinity along the sight's own axis, so it stays on the bore no matter where your eye sits behind it.
Modelling it as a sprite drawn on the sight glass gets this exactly wrong — the reticle slides across
the glass as you move your head, and the weapon appears to shoot wherever the dot has drifted to.

**Place the reticle by angle along the sight's optical axis**, not at a position on the lens surface.
(*Cyberpunk 2077 VR: "the reticle is placed by angle along the sight's own optical axis, so it stays on
the bore instead of sliding across the glass when you look at the sight from the side."*)

This matters far more in VR than flat, because in flat the eye is always on the sight axis by
construction. In VR the player will look at the sight from the side constantly — and a sight that
tracks correctly under off-axis viewing is one of the cheapest large wins in weapon handling.

## Latching onto a mesh you identified at runtime needs three states, not two {#identity-latch}

Picking "the gun and the arms" out of a per-frame draw list and holding onto them is a standing problem
for viewmodel work. Singularity VR's latch shipped twice with the same defect before the shape came out
right. `[SOURCE]`

**The failure: a retry keyed on getting nothing cannot detect getting the wrong thing.** Their retry
fired when the counts were *zero*. But the source is the **previous frame's** foreground list, replaced
wholesale each frame, and at the main menu it holds two entries that are not the gun and arms.

> The latch took them, returned true, and **the retry never fired again**. Toggling the method
> re-latched from gameplay, which is why it "worked the second time".

They had seen it before, and the earlier phrasing is the better one: *"the hide indices then pointed at
things that were not the gun. **The report that came back was accurate; the labels on it were
fiction.**"*

**The fix is to validate continuously against the only evidence that means anything - is the latched
mesh still being drawn?**

| State | Rule |
|---|---|
| Not latched | take the top two **once they have held 30 frames** |
| Latched **and seen** | leave it alone - a muzzle flash shifts the list while firing |
| Latched **and unseen for 240 frames** | drop it and re-take |
| **Empty list** | **neither a hit nor a miss** |

**That last row is the insight.** Cutscenes and menus have no first-person pass at all, so counting an
empty list as a miss would throw away a good latch and re-take it from menu geometry - *"the same bug
from the other side."* **Absence of evidence and evidence of absence need different handling**, and a
two-state latch has nowhere to put the difference.

The hold-down before latching and the long timeout before dropping are both doing real work: the first
stops a transient frame from being latched, the second stops a legitimate interruption from breaking a
correct latch. Neither is a magic number - they are the two directions the latch can be wrong in.

## Weapon scopes: a second camera on a panel, staged in three steps

A magnified scope in VR can't be the flat game's fullscreen zoom — that hijacks the whole view. It has to
become **a panel on the weapon showing a second camera**, which means a second render and a camera-origin
decision. HaloVR's staging is a good template because each stage answers one question and is separately
headset-confirmable:

1. **A fixed, obviously-fake panel.** Prove placement, size, orientation and the toggle work on every
   weapon before rendering anything real into it. (*HaloVR stage 1: a flat blue-green 4:3 panel, toggled
   on a stick click, independent of the game's native zoom — confirmed across all tested weapons.*)
2. **Put a real rendered view on the panel.** Prove the render path and orientation, still without
   worrying about whether the image is *correct*. (*Stage 2 showed a valid eye render, small and flat and
   correctly oriented — and immediately exposed the real problem: its perspective felt head-mounted.*)
3. **Fix the camera origin — it is the weapon, not the head.** A scope image rendered from the eye is
   subtly wrong in a way that's hard to name until you see stage 2. Use the **weapon/hand position as the
   camera origin and the actual bullet ray as the forward axis**, so the scope shows what the gun is
   pointing at.

Budget it honestly: this is a second scene render, and HaloVR's first stage-3 attempt was rejected in
headset for excessive cost as well as an over-aggressive absolute zoom. Keep the toggle independent of
the engine's native zoom so the two can't fight, and keep the main stereo view intact while the scope is
up.
