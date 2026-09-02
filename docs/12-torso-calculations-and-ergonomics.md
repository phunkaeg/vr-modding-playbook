# Torso Calculations & Ergonomics

Consumer VR gives unusually good six-degree-of-freedom measurements at three
places: the headset and two controllers or hands. It does **not** measure the
neck, chest, pelvis, shoulders, elbows, or the user's proportions. Visible arms
therefore turn tracking into a reconstruction problem: the endpoints are known,
but most of the body between them is inferred.

This is not a cosmetic detail. A bad inferred torso makes otherwise exact hand
tracking look wrong. Shoulders that inherit headset roll tilt with every head
cant. Shoulders that inherit headset yaw rotate whenever the user looks aside.
An unconstrained elbow can choose any point on a large solution circle, producing
lateral flare, sudden flips, or arm twist. The solver must explicitly decide who
owns each degree of freedom.

The practical target is not anatomical ground truth; three trackers cannot
provide that. It is a stable, plausible, low-latency pose that:

- keeps the tracked head and hands exact where interaction depends on them;
- infers latent torso and elbow motion without pretending it was measured;
- respects body proportions, reach, joint limits, and temporal continuity;
- follows locomotion and room-scale movement without following every head turn;
- stays cheap and deterministic enough for a render/update hot path;
- yields to a game's authored animation where the state requires it.

## Two sequencing rules the body model depends on {#body-model-sequencing}

Both refine rules stated elsewhere in this chapter, and both are about **when** a value is read rather
than which value it is. `[HEADSET]`

**Body yaw must be sampled BEFORE head rotation is folded into the camera rotator.** The chapter already
says head translation uses HMD position with **body** yaw - the tracking volume anchors to where the
player is *facing*, not *looking*, so a physical step forward is still forward in the room after a
90-degree head turn. The addition is ordering: once head rotation has been composed into the camera
rotator, the "body" yaw you read back is contaminated by it, and the error scales with how far the head
is turned - largest exactly when the rule matters most.

**Eye separation must follow head ROLL, not yaw alone.** Tilt your head and the **interocular axis tilts
with it**. This is distinct from the torso rule above it: HMD roll must *not* drive the shoulder bar, but
it *must* drive the eye baseline. Same input, two consumers, opposite answers.

> **A caution for engines with no roll channel:** UE2's camera has none at all, so the roll axis exists
> **only in the mod's code** and there is nothing in the engine to compare against. A missing channel
> cannot be validated against the engine's own behaviour - only against the wearer.



## Reaching the wrist target does not prove the arm is solved {#endpoint-is-not-the-mesh}

A numerically successful endpoint solve and a visually broken arm are entirely compatible, and the IK
maths is not where the fault is. `[SOURCE]`

SOMA exposes a **34-node chain per side**:

```text
Clavicle -> Shoulder -> Arm_1..5 -> Elbow_1..2 -> Arm_6..10 -> Wrist
          -> Thumb_1..3 and four finger chains
```

A prototype restored all 34 but **directly solved only three ownership points** - `Arm_1` as the
upper-arm hinge, `Arm_6` as the elbow, `Wrist` as the tracked endpoint. That is enough for the wrist to
reach the controller **while every intermediate weighted node stays in its authored pose**. The released
skin weights show the shirt weighted through the clavicle, shoulder, `Arm_1..7` and both elbow nodes, so
the visible result is **stretched, creased or twisted skin** over a solve that reports success.

> **Anatomical hinge ownership and skin deformation are different problems.** Solving the first does not
> touch the second, and no endpoint metric can see the difference.

### A rig-validation ladder

1. Enumerate the **live** hierarchy - names, parents, local transforms, segment lengths.
2. Compare it against released or source asset weights where they exist.
3. **Perturb one candidate node at a time and observe pixels**, not transform writes.
4. Determine whether the runtime consumes hierarchical locals, flat component-space matrices, or a later
   skinning palette.
5. Separate hinge ownership from distributed swing/twist and skin deformation.
6. **Only then** distribute the solved rotation across intermediate nodes, preserving authored rest bases
   and failing back to native animation when the chain does not match.

The transferable half of [FarCry2-VR's rig mapping](02-viewmodels-and-hands.md) is the **method** -
synthetic per-bone pose sweeps, and the finding that anatomical controls, twist bones, attachment
helpers, the camera bone and the *actually deforming* range are different concepts. **Its indices and
flat-array composition rules do not transfer.**

**And label the evidence honestly.** Their census records
`releasedAssetWeightsKnown=1 runtimeSkinWeightsObserved=0` so static asset evidence is never mislabelled
as live skinning ownership - and they corrected their own terminology in the same pass: a complete
**first-person arm and finger chain** is not a torso skeleton, and calling an inferred body-yaw shoulder
model a "full-body rig" overstates it.

## A plausible yaw error is often a FRAME error, not a tuning problem {#mixed-frame-yaw}

Shoulders that start nearly reversed, unwind slowly, tangle the arms, or look like a bad follow
threshold - while the HMD and the native body heading are each individually stable. `[LIVE]`

**Measured:** at body-follow activation a value named `camera.headWorldRotation` produced about
**0.19 degrees** of yaw while the game's native camera/body heading was about **115 degrees**. The lane
subtracted them directly and began with a **-114.73 degree** error.

The name was the trap. That value was the **recentered tracking-space yaw delta**, not an absolute world
heading; the native value was in the game's world/body frame. **Smoothing a 114-degree discrepancy only
makes the wrong answer move slowly**, which is why it presents as a filter or threshold problem.

Compose through the native frame before evaluating any policy:

```text
worldHeadYaw = wrap(nativeBodyYaw + relativeHeadYaw)
yawError     = wrap(worldHeadYaw - torsoAnchorYaw)
```

**The cheap discriminator, before touching a single constant:** log both operands, their **declared
coordinate spaces**, and the **first unfiltered residual**. *A near-zero tracking delta paired with a
large native heading is an immediate mixed-frame signature* - and it is visible in one row.

> **Names like `worldRotation`, `cameraRotation` or `absolutePose` are not evidence of a coordinate
> frame.** Establish the transform chain from behaviour or construction. **Filters cannot repair
> subtraction between unlike spaces.**

Same family as [the eye-height datum](#eye-height-datum) and
[post-deadzone units](03-input-and-locomotion.md#gated-mechanic): a number is meaningless without the
space it is expressed in, and the bug hides in the space rather than the value.


## Any animation that moves the head relative to the body lifts the body {#hmd-anchored-float}

A VR-only failure with no flat-mode equivalent, and it looks exactly like an animation bug for as long as
you treat it as one. `[SOURCE]`

Visceral RE2's braced weapon-ready pose left the character **floating about 10 cm off the ground**. The
investigation ran through animation swaps, motlist swaps, weapon-category spoofing, poisoning the
weapon-HOLD banks, and forcing two different bank types - **all confirmed dead**. The answer came from
the headset, in one move:

> Lowering the physical HMD made the feet touch the floor and the knees bend.

**The chain is general.** In VR the body is anchored to the headset. A braced, crouched or leaning
animation lowers the head *relative to the body*, so the engine lifts the **whole body** to keep the head
where the headset is - and the feet leave the floor. Nothing is wrong with the animation; the animation is
being asked to move the head while something else insists the head cannot move.

**The fix works with the engine rather than against it:** lower the **pelvis bone** by a fixed amount
while the pose is active, composing with the game's own leg IK, and the engine plants the feet and bends
the knees by itself. Visceral's tuned value is **0.175 m**, applied only while aiming, at a
pre-late-update hook.

**The discipline that makes it safe is knowing what the fix must not touch.** The drop is *skeleton only*
- pelvis and children. Hands, weapon and arms are VR-controller-pinned, so the muzzle and the point of
impact are unaffected, and they confirmed it rather than assuming: *"bullets true."*

**Two dead ends worth inheriting**, because both look promising from a code reading:

- **Bank poisoning applied correctly and still failed** - the resolved motion did change, but *"the legs
  are bound to the weapon-HOLD bank whenever the weapon is up"*, so the fallback animation floated too.
  **Wrong layer**, not wrong value.
- **You may not be able to leave the state at all.** Firing was gated behind the aim state, decided
  player-side and un-overridable: *"'ready to fire' and 'combat pose' are one bundle."* When a mechanic
  and a pose share one state, the pose is a constraint to work inside, not a thing to switch off.

See [CAM-013](pattern-catalog.md#cam-013).


## Evidence: this is an underconstrained problem

[Parger et al., *Human Upper-Body Inverse Kinematics for Increased Embodiment in
Consumer-Grade Virtual Reality*](https://markussteinberger.net/papers/HumanUpperBodyIK.pdf)
is the closest direct reference for this problem. Its chain runs from tracked
head through inferred neck, shoulders, and elbows to tracked hands. It reports
three findings that should shape a VR mod implementation:

1. Torso yaw derived directly from HMD yaw creates excessive shoulder movement
   when the user merely looks left or right. Their solver estimates yaw from the
   two head-to-hand directions and uses HMD yaw only to resolve ambiguous cases.
2. Neutral shoulders are fixed offsets from the neck. They only rotate toward a
   hand after the arm approaches a reach threshold, and that contribution is
   bounded.
3. Shoulder and hand positions determine elbow bend but not elbow direction.
   The elbow lies on a circle around the shoulder-to-wrist axis, so a swivel or
   pole policy is required to choose a plausible point.

The same paper assumes neck roll is zero, blends toward a stable elbow direction
near vertical and behind-the-shoulder singularities, and corrects elbow swivel
when wrist limits would otherwise be exceeded. Its user study found responsive
IK arms plausible and controllable; 67% of participants preferred IK for the
highest embodiment in its fast arm task. The paper is
[ACM DOI 10.1145/3281505.3281529](https://doi.org/10.1145/3281505.3281529).

This remains an ill-posed estimation task even with more sophisticated methods.
[AvatarPoser](https://arxiv.org/abs/2207.13784) describes reconstruction from one
headset and two hands as vastly underdetermined, separates global body motion
from local joint pose, and then uses IK to force the inferred arms back onto the
known hand positions. [Ponton et al.](https://arxiv.org/abs/2209.11478) likewise
predict body orientation from the headset and both controllers instead of
equating body heading with HMD heading. These learned systems are useful evidence
for the decomposition even when a lightweight injected mod should not ship a
neural pose estimator.

Biomechanics literature describes the human arm as a redundant seven-degree-of-
freedom chain. The elbow's **swivel angle** selects one solution from the
self-motion arc around the shoulder-to-wrist axis; it is not determined by the
hand endpoint alone. See the open-access
[upper-limb reconstruction study](https://pmc.ncbi.nlm.nih.gov/articles/PMC5819179/)
and the discussion of effort-minimizing swivel selection in
[Li et al.](https://pubmed.ncbi.nlm.nih.gov/35951574/). This supports a practical
downward-biased elbow pole, but not a single fixed elbow direction for every
pose.

## The ownership model

Treat the estimate as four nested frames, not one transform:

| Frame | Authoritative evidence | Must not inherit blindly |
| --- | --- | --- |
| Tracking/world | OpenXR stage/local space and calibrated world conversion | game-camera shake, bob, or authored offsets |
| Body/torso | native player capsule/avatar heading when available; otherwise bilateral hand/head inference | raw HMD pitch, roll, or immediate yaw |
| Head | tracked HMD position and orientation relative to the body | body-turn state duplicated into the HMD pose |
| Hand | tracked **grip** pose plus model-specific wrist calibration | pointer-ray pose or the opposite hand's calibration |

The distinction between grip and pointer poses is standardized platform advice:
[Microsoft's motion-controller documentation](https://learn.microsoft.com/en-us/windows/mixed-reality/design/motion-controllers)
defines grip pose around the palm and recommends it for hands and held objects,
while pointer pose is for aiming. Arm IK should terminate at calibrated wrist or
grip poses; interaction rays can use a separate pointer basis.

### Body-heading evidence ladder

A flat-game VR mod often has evidence a general VR application lacks: the game
already knows which way its player capsule or avatar is facing. Prefer sources in
this order:

1. **Native body/avatar/capsule yaw.** This is the best owner when locomotion,
   snap turn, smooth turn, or mouse turn already updates it.
2. **Bilateral hand inference.** When no body heading exists, estimate a planar
   forward direction from both head-to-hand vectors, hand velocities, and the
   previous torso heading. Two hands provide more evidence than either hand.
3. **HMD yaw with hysteresis and limits.** Use it only as a fallback, ambiguity
   resolver, or slow recentering influence. A head can turn roughly sideways
   while the chest remains forward.
4. **Last valid body heading.** During tracking loss or an ambiguous crossed-hand
   pose, continuity is better than an instant guess.

Never copy the full HMD quaternion into the torso:

- **HMD roll is head roll, not torso roll.** Default torso roll to zero. Add
  limited authored lean only from an explicit body/animation signal.
- **HMD yaw is not immediate body yaw.** Looking aside should not rotate the
  shoulders. Allow body yaw to follow only native turning or a sustained,
  thresholded inference from the whole tracked configuration.
- **HMD pitch is at most evidence.** Height loss plus downward HMD pitch can
  suggest crouch or chest bend, but direct pitch coupling makes the torso fold
  whenever the player looks down.

Filter the *latent* torso heading, not the rendered HMD pose. The head and hand
endpoints should remain on the freshest pose for the upcoming render; smoothing
them adds visible lag. Apply angular-rate limits, dead zones, hysteresis, and
confidence blending to the inferred torso state instead.

## Shoulder position

Let:

- `H` be tracked HMD world position;
- `U` be stable world up;
- `F` be normalized planar body forward;
- `R = normalize(cross(F, U))` be body right;
- `d` be calibrated head-to-shoulder vertical distance;
- `b` be calibrated rearward shoulder offset;
- `w` be shoulder width.

A useful neutral shoulder centre and left/right anchors are:

```text
C = H - U*d - F*b
S_left_0  = C - R*(w/2)
S_right_0 = C + R*(w/2)
```

This deliberately uses **HMD position** but **body yaw**. Room-scale leaning and
crouching move the shoulder centre with the user; HMD roll and head-only yaw do
not rotate the shoulder bar. A game's native hand root may already contain a
good calibrated neck/shoulder vector. In that case, capture and preserve it
instead of replacing it with generic anthropometric constants.

### Hands influence shoulders near reach, not all the time

Rigid shoulders look wrong at full extension, but shoulders that chase hands on
every frame swim around the chest. Apply hand influence only after a reach gate.
For each arm:

```text
reach = length(W - S0) / (upperArmLength + forearmLength)
t = smoothstep(reachStart, reachFull, reach)
S = S0 + t * clamp(reachCompensation(W, torsoFrame), compensationLimits)
```

`reachStart` should leave ordinary near-body gestures untouched. The
compensation can rotate or translate the clavicle slightly forward/upward toward
the hand, but must be bounded and side-specific. Parger et al. use a threshold at
half total arm length and clamp shoulder rotation to about 33 degrees; those are
published reference values, not universal constants for every avatar.

This gives the three tracked points distinct jobs:

- the head drives shoulder-centre translation;
- body evidence drives shoulder-bar heading;
- each hand adds only its own near-extension clavicle/shoulder compensation.

## Efficient two-bone arm IK

**First, check what "two bones" actually means on your rig.** Real character skeletons rarely give you a
clean shoulder→elbow→wrist chain: the intermediate joints are usually **twist-distribution bones**, not
anatomical hinges, and the mesh is weighted *through* them expecting smooth interpolation.

(*SOMAVR's live traversal found a continuous chain `Clavicle → Shoulder → Arm_1..5 → Elbow_1/2 →
Arm_6..10 → Wrist`. Diffing the released mesh source showed the shirt is weighted through `Arm_1..7` plus
both elbow nodes, while the hands mesh overlaps at `Elbow_2`/`Arm_6-7` and continues to `Arm_10`. A solver
that transforms only `Arm_1` and `Arm_6` — shoulder and forearm start — and leaves the numbered bones
between them untouched creases the mesh exactly where those two weighted regions overlap.*)

So: enumerate the chain on the live rig before solving, and decide explicitly how twist is redistributed
across the intermediate bones. The solve below gives you the endpoints; it does not absolve you of the
bones in between.

For a shoulder `S`, tracked wrist target `W`, upper-arm length `Lu`, and forearm
length `Lf`, a closed-form two-bone solve is constant time and allocation-free.
Let `D = W - S`, `d = length(D)`, and `A = D/d`. Clamp `d` to the reachable
interval before solving:

```text
dMin = abs(Lu - Lf) + epsilon
dMax = (Lu + Lf) * maxReachFraction
dSolved = clamp(d, dMin, dMax)
x = (Lu*Lu - Lf*Lf + dSolved*dSolved) / (2*dSolved)
h = sqrt(max(Lu*Lu - x*x, 0))
```

`x` is the distance from the shoulder to the centre of the elbow solution
circle, and `h` is its radius. A preferred pole vector `P` chooses a point on
that circle:

```text
Pplane = normalize(P - A*dot(P, A))
E = S + A*x + Pplane*h
```

The wrist remains at the exact tracked target unless it is beyond calibrated
reach. The model should never stretch bones to hide a bad shoulder estimate.

### Choosing a plausible elbow pole

“Elbows down” is a good neutral bias, not a complete solver. Build the preferred
pole in torso space from several bounded terms:

```text
P = downWeight     * (-U)
  + outwardWeight  * (left ? -R : R)
  + backwardWeight * (-F)
  + historyWeight  * previousElbowDirection
  + wristWeight    * wristLimitCorrection
```

Then project `P` off the shoulder-to-wrist axis. The weights should vary with the
hand's position in the torso frame:

- hands low or forward: favour down and slightly outward/back;
- hands across the chest: reduce outward bias so the elbow can tuck naturally;
- hands overhead: preserve continuity and allow outward bend rather than forcing
  world-down through an impossible pose;
- hands behind the shoulder: blend toward a stable fallback and impose joint
  limits;
- strong wrist rotation: adjust swivel gradually so forearm twist does not force
  an implausible wrist angle.

The previous solved elbow is valuable evidence. Near full extension, near full
fold, or when the wrist aligns with the shoulder's vertical axis, the solution
circle becomes numerically or perceptually unstable. Blend toward the previous
projected elbow direction, use a stable torso-space fallback if projection
degenerates, and cap swivel angular velocity. Never allow a one-frame sign change
to flip the elbow across the arm.

## Calibration

At minimum, calibrate or recover:

- world units per metre;
- eye/head to shoulder-centre vertical and rearward offsets;
- shoulder width;
- upper-arm and forearm lengths per avatar mesh;
- controller grip-to-wrist orientation and position per hand;
- avatar root scale and the engine's bone-axis conventions.

A standing T-pose can estimate shoulder width and arm lengths, but a reverse-
engineered mod can often do better initially: read the shipped skeleton's neutral
bone lengths and retain its native root-to-head offset. User-specific calibration
can then scale those proportions without changing topology.

Do not infer arm lengths from a currently animated or previously IK-mutated pose.
Restore/capture a known authored local pose first. Otherwise segment lengths can
accumulate solver error and the arms progressively stretch.

## Runtime contract

A practical injected implementation should remain small and predictable:

1. Sample one coherent predicted OpenXR head-and-hands snapshot for the upcoming
   render/update, with one frame identifier.
2. Convert all three poses once into the game's world space.
3. Resolve body yaw from the evidence ladder and update only latent torso state.
4. Compute neutral shoulders and bounded per-hand reach compensation.
5. Solve each arm independently with closed-form two-bone IK.
6. Apply wrist orientation from that hand's calibrated grip basis.
7. Distribute swing/twist through the engine's existing arm chain or feed its
   native IK targets; do not rigidly move already-skinned vertices.
8. Restore or yield ownership at authored-state boundaries.

Keep the hot path free of file I/O, allocations, unbounded logging, debugger
queries, and iterative searches. Two analytic arm solves are `O(1)`. Expensive
learning or optimization is optional evidence for a future system, not a
prerequisite for credible first-person arms.

## Diagnostics

Log bounded state transitions and periodic summaries, not every bone every
frame. Useful evidence includes:

```text
frame, poseFrame, bodyYawSource, bodyYaw, headYaw, yawDelta, confidence
headPosition, shoulderCenter, shoulderLeft, shoulderRight
handLeft, handRight, reachRatioLeft, reachRatioRight
elbowLeft, elbowRight, swivelLeft, swivelRight
reachClampedLeft, reachClampedRight, singularFallbackLeft, singularFallbackRight
upperLength, lowerLength, wristResidual, shoulderCompensation
```

Add counters for body-source changes, yaw threshold crossings, reach clamps,
elbow-pole fallbacks, per-frame swivel-rate clamps, stale pose rejection, and
authored-state suspension. A visual debug mode should draw the three tracked
points, torso basis, shoulder bar, arm segments, target wrists, and elbow poles.

## World scale is one constant with three users, and they must move together {#one-scale-three-users}

[Chapter 15](15-teardown-il2-1946-vr.md) says stereo separation and 6-DOF translation are both wrong if
the world unit is wrong. There is a **third** consumer, and forgetting it produces a specific and
confusing symptom. `[SOURCE]`

Singularity VR's scale is governed by one constant, `kMetresToUU = 52.5` - **UE3's documented 16 units
per foot exactly, not a tuned guess**, which is why it looked right before anyone thought to adjust it.
Three real-world quantities flow through it:

| Consumer | What it controls |
|---|---|
| the **stereo baseline** | how big the world looks |
| the **6-DOF translation** | how far you travel per step of real movement |
| the **hand position** the weapon rides | where your hands are, relative to both |

> Those three **must** move together. Scaling the IPD alone changes how big things look but not how far
> you walk, which reads as **the world resizing *as you move*** - the exact complaint a world-scale
> slider exists to fix.

**One conversion, three users, one knob.** A "world scale" control wired only to eye separation is not a
world-scale control; it is an IPD control with a misleading label, and it will be reported as the bug it
was meant to cure.

**Look for the engine's documented ratio before tuning one.** Sixteen units per foot, one unit per
centimetre, one unit per metre - engine families usually have an exact answer, and a derived constant
that matches a documented one is evidence you got it right rather than a number that happened to look
acceptable.

### And check what the hands are anchored to

Same run, reported in passing: *"when I recentred, the gun came closer to me."* The weapon was anchored
to the **engine's** eye rather than to the player's. **A hand-held object that moves on recentre is
attached to the wrong origin** - recentring changes the relationship between the two, so it is the
cheapest test there is for this class of bug, and it costs one button press.

## The engine's eye height is measured from the capsule centre, not the floor {#eye-height-datum}

A world-scale trap with a wrong conclusion waiting at the end of it, and the numbers are small enough to
look plausible. `[SOURCE]`

Singularity's `Engine.Pawn` exposes `BaseEyeHeight` (measured 70.0, stable) and `EyeHeight` (oscillating
67.4-71.4 with head bob and the crouch interpolation). The trap is the datum:

> **`BaseEyeHeight` is measured from the actor's `Location`, which is the CENTRE of the collision
> cylinder - not from the floor.** So 70 UU is not the player's eye height above ground; that is roughly
> `CollisionHeight + BaseEyeHeight`. Converting 70 UU straight to centimetres gives 133 cm and invites
> the wrong conclusion that the character is child-sized.

**133 cm is exactly the sort of wrong answer that survives review** - it is a number, it is in range for
*a* human, and it points you at a world-scale correction that will make everything else worse. **Log
`CollisionHeight` before converting anything**, and state the datum next to every height you record.

The general rule: **an engine height is meaningless without its datum**, and the three candidates -
floor, capsule centre, and the actor's own origin - differ by amounts large enough to reshape the whole
room. This is the same class as
unit ratios established from geometry rather than assumed, and it deserves
the same treatment: derive the datum from something you can measure in the world, not from the field's
name.

## Headset acceptance matrix

Test poses that separate the estimator's inputs instead of waving everything at
once:

| Test | Expected result |
| --- | --- |
| Roll HMD with hands still | head rolls; shoulder bar remains level |
| Look 60-90 degrees aside | head turns immediately; torso remains stable |
| Native snap/smooth turn | torso and shoulders follow the player heading |
| Lean left/right/forward | shoulder centre follows HMD translation at calibrated offset |
| Move one hand near chest | that wrist tracks exactly; shoulder barely moves |
| Extend one arm fully | matching clavicle/shoulder contributes smoothly and within limits |
| Cross hands | no left/right state leak; elbows tuck without flipping |
| Raise hands overhead | elbows remain continuous; no vertical-axis spin |
| Hand behind shoulder | bounded fallback, no 180/360-degree elbow jump |
| Full extension then retract | no locked elbow, stretch, or hysteresis chatter |
| Lose one controller briefly | unaffected arm remains stable; lost arm holds/yields safely |
| Enter authored interaction | explicit blend/yield policy; no ownership fight |

Record video from the headset view and, where possible, a third-person mirror.
Hands can look correct in first person while shoulders or elbows are clearly
wrong from outside. Acceptance is perceptual plus numerical: exact wrist
residual alone does not prove a plausible arm.

## SOMAVR adoption state

SOMAVR 0.82 implements the first two deterministic rungs of this model:

- tracked HMD world position drives the retained shoulder/root translation;
- SOMA's native horizontal camera forward supplies body/capsule yaw, so raw HMD
  pitch and roll do not own the torso;
- the first native hand-root relationship preserves the shipped rig's calibrated
  offset, with explicit vertical and rearward tuning;
- each tracked grip drives its matching wrist independently;
- a closed-form, reach-clamped two-bone solve uses the native elbow as its pole,
  biased downward before solving;
- the complete authored arm chain is restored before each solve so animation or
  previous IK cannot accumulate segment-length error;
- ordinary hand motion leaves the native shoulder anchor unchanged, while
  near-full extension may add a smoothed, side-specific clavicle contribution
  capped at 5 cm;
- elbow selection uses a torso-space down/out/back preference, with previous
  elbow direction stored in torso-local coordinates;
- vertical singularities increase continuity weight and a bounded per-frame
  swivel limit prevents abrupt elbow flips.

The next evidence and calibration rung is:

1. headset acceptance of shoulder stability, extension contribution, bilateral
   elbow behavior, and continuity through turns and difficult poses;
2. body-yaw confidence and source telemetry where native ownership is unclear;
3. per-avatar or user-scaled anthropometric calibration;
4. evidence-driven distribution of twist across the authored upper-arm and
   forearm chains.

These additions should remain behind independent rollback controls and be
accepted one dimension at a time. Correct tracking endpoints, natural-looking
joints, and authored game behavior are separate contracts.
