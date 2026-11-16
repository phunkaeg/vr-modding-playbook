# Unreal Engine 4.27 — engine reference for VR work

UE 4.27 shipped in 2021, and essentially every current Unreal VR reference targets UE5 — including
Epic's own agent-facing skills plugin, which requires a `ToolsetRegistry` and a Model Context
Protocol plugin that do not exist in 4.27 at all. A 4.27 target therefore has almost no
agent-facing reference material, and a UE5 answer is frequently wrong *in a way that compiles*.

This page is the engine-version layer: what to do, **why you care**, and the symptom that sent
someone looking. The method lives in the chapters; this page routes to them.

Two sibling pages cover the other Unreal cases. If a framework already owns the stereo, go to the
[UEVR route](uevr-route.md) — a recipe that assumes you own the render path will mislead you there.
If you build and ship the project yourself, the workflow is the
[source-owned route](source-owned-route.md), and the gameplay-plugin prior art is the
[VR Expansion Plugin reference](unreal-vrexpansion-reference.md).

## What this is, and what it is not {#review-scope}

Every entry below cost at least one build cycle in a real 4.27 project. Nothing here is copied from
a tutorial and nothing is extrapolated from UE5 — that was the point of writing it down.

**Grades.** `[SOURCE]` read in the engine's own source. `[LIVE]` measured in a running 4.27 build.
`[HEADSET]` a headset session was the witness. `[STATIC]` read out of a shipped binary. `[AUTHOR]` a
working rule, stated as such. Where a simulated OpenXR runtime was the observer rather than a real
one, the grade says so — see
[running the headless instruments](09-d3d11-openxr-injection.md#headless-instrument-operation) for
what that does and does not establish.

**Contributors.** The public Unreal sources in the [coverage dashboard](coverage.md), plus a
source-owned VR project that is excluded from the published roster. Under the repository's
publication boundary, no project, game, build, address or timeline detail appears on this page; its
observations are attributed only to *an unpublished source-owned project*.

**Not covered.** UE5 of any minor. Chaos — the physics entries here are PhysX, which is what 4.27
uses by default. Blueprint nativization at scale. Console submission. Anything specific to a title.

## Go directly to the problem

| What you are seeing | Go to |
|---|---|
| A HUD re-runs its construction, re-binds delegates, or fails on a material instance when moved onto a world-space surface | [Hosting a live UI in world space](#ui-in-world-space) · [04](04-ui-and-hud.md#ui-in-world-space) |
| A hosted menu never appears, or stops responding, once the game pauses | [What stops ticking](#pause-and-ticking) · [04](04-ui-and-hud.md#ui-in-world-space) |
| The trigger reaches the UI but no action fires | [Hosting a live UI in world space](#ui-in-world-space), [Input](#input-and-haptics) |
| A hand or held object stops dead in contact and will not withdraw | [Sweeps and penetration](#transforms-and-physics) |
| A hidden body part is still visible in the headset although the check passes | [Skinning and bones](#skinning-and-bones) · [META-022](pattern-catalog.md#meta-022) |
| The game's own rumble is silent in VR | [Input, haptics and force feedback](#input-and-haptics) · [20](20-audio-and-haptics.md) |
| A VR key added to an existing action in config never fires | [Input, haptics and force feedback](#input-and-haptics) · [03](03-input-and-locomotion.md) |
| The eyes lose height after a crouch, but the posture test passes | [Deferred movement](#transforms-and-physics) · [12](12-torso-calculations-and-ergonomics.md) |
| A suite passes in the editor and fails in the packaged build | [Headless and packaged runs](#build-and-package) · [TEST-030](pattern-catalog.md#test-030) |
| A Blueprint export shows a function with no body, or a manager that never moves anything | [Inspecting Blueprints and assets](#blueprint-graphs) · [11](11-re-anchoring-and-discovery.md) |
| An editor script saved the asset and then the receipt disagreed with it | [Editor scripting](#editor-python) |
| A headless run exits 0 whatever happened | [Headless and packaged runs](#build-and-package) |
| A compile error says a function is missing and the obvious fix makes it worse | [Reflection and UHT](#uht-and-identity) |

---

## Reflection, UHT and class identity {#uht-and-identity}

### `BlueprintNativeEvent` on a class generates the function itself as a dispatching thunk

Declare `virtual bool Foo();` as a `BlueprintNativeEvent`, implement `Foo_Implementation()`, then
**call `Foo()` directly**. There is no `Execute_Foo()` for a class.

*Why you care:* the `Execute_` form exists only for **interfaces**, and reaching for it produces a
compile error that reads as though the function were missing entirely — so the "fix" is itself the
error. `[LIVE]`

### On an interface, UHT generates empty `_Implementation` defaults

Declare the interface function and let UHT emit the default body. Writing your own gives
`'X_Implementation': function already has a body`. `[LIVE]`

### Small reflection rules that each cost a build

- A **`const` pointer cannot be a `UPROPERTY`**. If the object outlives the holder — a game-instance
  subsystem, say — use a plain member and write down why.
- A **forward declaration cannot name an enumerator.** `enum class EHandPose : uint8;` is enough to
  declare a member, not to write `= EHandPose::Open`; include the header. The symptom is `C2027`
  plus `C2065` on a line that looks like a plain default initialiser.
- Declaring a variable inside a `case` label needs braces. Standard C++, but it surfaces constantly
  in stage machines.
- UHT's **`Circular dependency detected for filename …` is logged as an Error and is not fatal.**
  Worth fixing, not worth chasing mid-task, and never the cause of an unrelated failure. `[LIVE]`

### Blueprint generated classes carry a `_C` suffix; native ones do not

*Why you care:* **normalise in exactly one place.** One project stripped the suffix in the caller
*and* keyed the lookup table with it, so calls through one path silently missed while direct calls
succeeded — and because the policy table failed closed, the miss produced a plausible-looking
*decision* rather than an error. It sat in the log for a day underneath a suite reporting 11 passed,
0 failed. `[LIVE]`

A fail-closed default is correct and it is also camouflage: pair it with a count of lookups that
fell through, and assert that count is zero where it should be.

### Blueprint nativization is a project setting with three values

`BlueprintNativizationMethod` — Disabled / Inclusive / **Exclusive**. Exclusive takes an explicit
`NativizeBlueprintAssets` allowlist, so Blueprints can be collapsed to C++ selectively. Check which
one a delivered project uses before assuming a Blueprint exists as a graph at runtime. `[SOURCE]`

---

## Transforms, physics and constraints {#transforms-and-physics}

### `FTransform A * B` applies A **then** B

So `BodyOffset() * Target` puts the body at `Target.TransformPosition(Centre)`, and the inverse
composition recovers it. Getting this backwards produces an error that looks like drift, which sends
you to the wrong half of the system. See [A1](a1-rotation-and-frames.md). `[SOURCE]`

### `InverseTransformPosition` divides by scale

A world offset of 8 units taken into the local space of a component scaled `0.055` becomes a local
offset of about 150. Mathematically fine — `TransformPosition` undoes it — but it makes local
coordinates look absurd when printed, and it matters the moment you compare a local offset against a
distance in centimetres. `[LIVE]`

### Changing a component offset that a getter subtracts teleports the thing the getter reports

If `GetPose()` is `Offset.Inverse() * Body->GetComponentTransform()`, changing `Offset` alone moves
the *reported* pose by the delta, and any drive chasing that pose spends the next frames correcting a
displacement nobody asked for. Move the body by the same amount, then validate where it landed.
See [A2](a2-pose-pipeline.md). `[LIVE]`

### `GetClosestPointOnCollision` returns zero inside a supported body; negative means no valid query

Guard `Distance < 0.f` as an **unavailable or unsupported query**, not as penetration. The PhysX
implementation initialises the output point to the input and returns zero when that point is inside
a supported shape, so **zero counts as contact** while a negative value is not evidence of overlap at
all. Verified in `PhysicsInterfacePhysX.cpp`, `FPhysicsInterface_PhysX::GetSquaredDistanceToBody`.
`[SOURCE]`

*Why you care:* this is the general shape of a sentinel bug — the "no answer" value lives inside the
numeric range you are testing. The first version of this entry had it backwards, and a failed query
was read as an inside point for weeks.

### A sweep that starts penetrating reports `bStartPenetrating`, and its `Normal` is the depenetration direction

*Why you care:* the obvious handling — refuse the move, return the current position — is
**direction-blind**. It refuses withdrawal exactly as it refuses deeper penetration, and the body
freezes in contact.

Split the requested motion against the normal: keep everything that does not go deeper, add a
**bounded** push along the normal, and budget that push **per call and not per pass**, or a four-pass
loop moves four times what the name of the setting promises. A pass that reports zero penetration
depth with an outward request must still make progress, or it repeats the identical sweep until the
loop ends.

> Symptom: a headset session measured the hand moving **under 0.1 mm across eight seconds** of
> controller movement. `[HEADSET]`

### An animated surface can move onto a slow sweep's start

A sphere swept from its last sample to its current position finds a surface it moves into — unless
the surface moves instead. Pushed slowly, around 16 cm/s, into a breathing chest, a strike volume
sometimes made no clean arrival at all: a sweep from a position that touched nothing when sampled
reported the chest as `bStartPenetrating` at the next sample. Sweeps of a few millimetres per frame
missed arrivals too.

A rule that simply ignores sweeps which start inside a surface then judges nothing. Sweep a slow
volume only once it has moved about a centimetre, and **count a sweep that starts inside a surface as
an arrival when the previous sample touched nothing.** `[LIVE]`

### Joint limit setters share state, and angular limits default to soft

`SetLinearXLimit`, `SetLinearYLimit` and `SetLinearZLimit` all write the **same linear limit radius**.
Setting Y and Z to Locked with a size of zero *after* configuring X as Limited also removes X's
travel. Pass the intended radius to all three calls, even the locked axes.

`ProfileInstance.TwistLimit.bSoftConstraint` **defaults to true in 4.27**, so an authored limit of 45°
can reach 63° under a grip drive. For a hard mechanical stop, disable the soft limit explicitly before
constructing the joint, then measure the resulting motion rather than trusting the authored number.
`[LIVE]`

Both of those are worth keeping as named negative controls: a mechanism suite that can restore each
mistake on demand is the only thing that keeps the limits honest later.

### Physics bodies do not do what the verb implies

- **Teleporting a physics body does not stop it.** `SetWorldLocation(…, ETeleportType::TeleportPhysics)`
  moves a simulating body and leaves its velocity intact, so it carries on from wherever you put it.
  A fixture that places an object, waits a beat and then offers a grip can find the object already out
  of reach — and how far it gets depends on frame pacing. **Zero linear and angular velocity whenever
  a fixture teleports a simulating body, and re-assert the placement on each retry.** `[LIVE]`
- **Changing a held body's collision in the grip's first frame launches it.**
  `SetCollisionResponseToChannel` on a simulating body updates its physics filtering at once; done in
  the same frame the grip takes hold, it threw a held object about **1.4 m** out of the hand in one
  frame and broke the grip at 136 cm of separation. The same change half a second into the hold is
  harmless. Change a held body's responses only after the hold has settled. `[LIVE]`
- **`SetBoxExtent` on a simulating body rebuilds physics state.** Gate it on a tolerance or it runs
  every frame; growing a shape while it is inside geometry needs a validity check and a rollback path.
- **`UPhysicsHandleComponent::GrabComponentAtLocationWithRotation` grabs away from the centre of
  mass**, which is exactly what gives you a lever arm. `bInterpolateTarget` smooths the target and
  hides the lag you may be trying to observe.

### Spawning and possession

- **`ESpawnActorCollisionHandlingMethod::AlwaysSpawn` will bury a capsule in the floor.** A player
  start sits *on* the floor, so spawning a capsule at that exact point puts half of it below; the
  character then climbs out over the following second, and that motion is indistinguishable from a
  scripted move if you measure distance without splitting horizontal from vertical.
  `AdjustIfPossibleButAlwaysSpawn` is usually what you meant. `[LIVE]`
- **A map that auto-possesses its own pawn beats `DefaultPawnClass`.** The game mode's default pawn
  loses to a pawn placed in the level with auto-possess set; take the player deliberately if a test
  must run in any map. Symptom: a test reporting "found no pawn" in a map that visibly had one.
- **`TObjectIterator` walks CDOs and other worlds.** Filter on the world and on a valid owner, or you
  will find the class default object and act on it.

### Deferred capsule movement can silently defeat child transform compensation {#deferred-movement}

`CharacterMovement::PerformMovement` batches capsule movement inside an `FScopedMovementUpdate`. An
attached tracking origin can retain a **stale world transform** inside that scope. Both the world and
the relative setters ultimately move using a world-space delta, so if the pose you request happens to
equal the stale cache, the engine can **early-out without updating the relative offset** — and the
next propagation then moves the eyes with the capsule.

Compose the logical pre-resize pose from the relative transform and the *current* parent, then call
`UpdateComponentToWorld()` on the origin after resizing and before restoring its pose. That preserves
whatever movement already happened inside the scope.

> Symptom: **43 cm of height lost per crouch** in a normal-tick fixture, while a suite that called the
> same posture code directly passed. The scope is the difference, so a direct-call test cannot see it.
> `[LIVE]` See [12](12-torso-calculations-and-ergonomics.md).

---

## Skinning, bones and a manually posed body {#skinning-and-bones}

### A poseable mesh ignores bone visibility, so `HideBoneByName` does nothing

`USkinnedMeshComponent::HideBoneByName` records a flag in `BoneVisibilityStates`, and
`IsBoneHiddenByName` reads that flag straight back. What actually collapses a hidden bone on screen is
the **animation path**, which zeroes the bone's scale while evaluating. `UPoseableMeshComponent` fills
its own component-space transforms and never consults the visibility states at all — so on a poseable
mesh the call sets a flag, the getter agrees with it, and the bone renders exactly as before.

This shipped: a VR body's head was hidden, a check asserted `IsBoneHiddenByName("Head")` and passed,
and the wearer could see the inside of the head **twice running**. The hands had the same non-fix and
were only invisible because the hand meshes drew over them.

Collapse the bone yourself with
`SetBoneScaleByName(Bone, FVector::ZeroVector, EBoneSpaces::ComponentSpace)`; children inherit it
through the transform accumulation. 4.27 exposes only world and component space here —
`EBoneSpaces::LocalSpace` is commented out in the enum. `[SOURCE]` `[HEADSET]`

**The wider rule is [META-022](pattern-catalog.md#meta-022): asserting a flag is not asserting a
result.** The check that replaced this one skins the mesh and counts vertices in front of the player's
eye, which moved from 1261 to 0.

### A manually posed body must publish its bone transforms

`ComputeSkinnedPositions` reads the component's **published** component-space transforms. A poseable
mesh's setters edit local transforms and mark them dirty; its normal component tick publishes them. If
that tick is disabled, the host must call `RefreshBoneTransforms()` after posing — in the live path as
well as headless. The renderer does not repair the missing tick.

Two traps around it. `ComputeSkinnedPositions` is declared on both `USkeletalMeshComponent` and
`USkinnedMeshComponent`, and a poseable mesh needs the latter. And if the *check* calls refresh
itself, it masks the omission in production: **publication belongs to the presenter, not to the
check.** `[SOURCE]` `[LIVE]`

### Poseable CPU skinning does not apply the renderer's hidden-bone policy

`UPoseableMeshComponent::FillComponentSpaceTransforms` and
`USkinnedMeshComponent::CacheRefToLocalMatrices` use the pose transforms without visibility flags,
while the GPU path in `SkeletalRender.cpp::UpdateRefToLocalMatricesInner` replaces a hidden bone's
matrix with its parent's zero-scaled matrix. **A positive CPU scale therefore does not prove the
rendered skin is uncollapsed.** Keep bone visibility and transforms consistent; when retaining a wrist
bone after cropping duplicate hands, `UnHideBoneByName` it explicitly.

> Symptom: a CPU wrist-skin check passed while the rendered cuffs still retracted from the hands.
> Captured-pose rendering exposed the mismatch. `[SOURCE]` `[LIVE]`

---

## Hosting a live UI in world space {#ui-in-world-space}

Moving a running `UserWidget` out of the viewport and onto a `UWidgetComponent` is the standard way to
get a flat HUD into VR, and it breaks **three independent things at once** — ownership, ticking and
focus. The method and the acceptance test are in
[04 · UI & HUD](04-ui-and-hud.md#ui-in-world-space); the 4.27 mechanics are here.

### Re-hosting a live `UserWidget` must retain its Slate owner

Hold `Widget->TakeWidget()` in a shared pointer *while* you remove it from the viewport and hand it to
`UWidgetComponent::SetWidget`. The UObject surviving does **not** preserve its Slate tree: the viewport
may own the final `SObjectWidget` reference and `UWidget` keeps only weak references, so dropping that
last owner replays `Construct` during the rehost.

A re-run `Construct` on a HUD that was already initialised repeats initialisation, binds its delegates
a second time, and can try to create a material instance whose parent is already a material instance.
Keeping the Slate tree alive avoids the rebuild and retains the original initialised material.
`[SOURCE]` `[LIVE]`

### `UWidgetComponent::SetWindowVisibility` is not a safe constructor setter in 4.27

It ensures Automatic tick mode, a live widget and a registered visibility callback, so calling it from
a derived constructor produces three handled ensures even when rendering later succeeds. The
constructor already defaults to `SelfHitTestInvisible`; a passive HUD should leave that default
intact. **Check engine source before using a runtime setter on a class default object** — a green
check summary did not catch these. `[SOURCE]`

### A widget hosted in a widget component cannot hold key focus

Flat, the HUD is in the viewport, and keys it does not handle go on to the game. Hosted by a
world-space widget component, the HUD lives in that component's **own window**, and after
`SetInputModeGameAndUI` with that HUD as the focus widget, `GetUserFocusedWidget(0)` was **null** — the
trigger reached Slate but never reached player input.

While a hosted menu is open, put focus back on the game viewport whenever it is outside it
(`FSlateApplication::SetAllUserFocusToGameViewport`). `[LIVE]`

### A widget component does not tick while the game is paused

`UWidgetComponent` leaves `bTickEvenWhenPaused` off. A HUD hosted in one, with manual redraw, stops
**both drawing and ticking its widgets** while the game is paused — so a pause menu, which is exactly
the thing that pauses the game, never appeared on the hosted HUD, and its list never finished opening,
so it ignored Back. Flat, Slate ticks the viewport's widgets whatever the pause.

Set `bTickEvenWhenPaused` on the component that hosts a UI the player must use while paused. `[LIVE]`

---

## Pause: what stops ticking, and what does not {#pause-and-ticking}

`UWorld::Tick` runs actor ticks only when the world is not paused (`bDoingActorTicks`), and
`FWorldDelegates::OnWorldPreActorTick` and `OnWorldPostActorTick` are broadcast **inside that part**.
So per-frame upkeep hung off either delegate stops dead at the pause menu, and an observer reading a
state file sees only the last sample from before the pause.

`OnWorldTickStart` is broadcast on **every** world tick, paused or not. Run per-frame upkeep and pose
sampling from there if the hands must still point while the game is paused. Components that set
`bTickEvenWhenPaused` still tick. `[SOURCE]` `[LIVE]`

*Why you care:* in VR, "paused" is not a still frame — the wearer's head keeps moving, and anything
that stops sampling becomes a comfort problem rather than a cosmetic one. Pause is a per-view
lifecycle event; see [01](01-camera-and-tracking.md) and
[XR-003](pattern-catalog.md#xr-003) for the compositor side of the same rule.

---

## Input, haptics and force feedback {#input-and-haptics}

### OpenXR controllers never receive gamepad force feedback in 4.27

`APlayerController` writes its force-feedback channel values every frame, and the Windows platform
layer forwards them only to input devices that report `IsGamepadAttached()`. The OpenXR input device
does not override it, so it never receives them: `ClientPlayForceFeedback` drives an attached gamepad
and nothing else.

Two consequences, and the second is the useful one:

1. **A game's own weapon rumble is silent in VR.** Nothing is wrong with the call; the channel has no
   listener.
2. **Controller haptics arrive only through `SetHapticsByValue` and `PlayHapticEffect`**, which reach
   OpenXR's haptic device directly — so a VR haptic layer is the *sole* writer of the controllers and
   does not compete with the force-feedback stream. One arbiter, no interleaving to design around.

`[SOURCE]` See [20 · Audio & haptics](20-audio-and-haptics.md).

### A game can put its own action mappings back at run time

A VR key added to an existing action in `DefaultInput.ini` fired nothing. At play time both the player
input and the input settings listed only the original keys, so the game restores its own bindings
before play begins — and where it does that was in neither the exported Blueprints nor the C++.

The OpenXR plugin reads the mappings **before** that happens, which is what makes this so hard to see:
the plugin still suggests the binding, a simulator still drives it, and Slate still receives the key.
No action is listening. **A driven-binding count in a simulator log proves only the OpenXR half.**

Put VR keys on actions the game leaves alone, under your own prefix, and call the game's own handler
from C++. `[LIVE]` See [03 · Input & locomotion](03-input-and-locomotion.md).

### `-GameModeOverride` is editor and PIE only

For a `-game` run, put it in the map URL: `?game=/Script/Module.MyGameMode`. `[LIVE]`

### A synthetic press has a duration, and a second press inside it is not a press

A simulated button press typically holds for a fixed interval — 150 ms in the simulator used here. A
probe that pressed the same button again as soon as the first press had opened a window sent its second
press *while the first was still held*: the button never went up, the game saw no new press, and the
action it meant did not happen in two of four runs. **Wait out each whole press and release before the
next.** `[LIVE in simulator]`

---

## Editor scripting through the Python binding {#editor-python}

The 4.27 Python binding is a thin wrapper over the reflection system, and most of its traps come from
that: you are frequently holding a pointer into an asset while believing you hold a value.

### A struct read from an asset **is** the asset

`asset.get_editor_property('profile')` returns a wrapper that points into the asset's own memory.
Moving that struct's points into another frame moved the staged asset's own data too, and a later read
compared the moved struct with itself moved twice. Copy the struct into the struct that will own it
first, then edit the copy read back from there — or construct a fresh one. Never use an existing
asset's struct as a scratch value for another. `[LIVE]`

The same aliasing crosses assets: reading one item's profile and editing the wrapper disabled a flag on
the *source* item while authoring a new one. The repaired importer re-checks the donor's flag after
assigning the independent copy.

### Editor properties are not always Python attributes

Use `get_editor_property` for `UPROPERTY(EditAnywhere)` fields that are not Blueprint-visible. The
wrapper can accept `set_editor_property('mode', value)` and still have no `.mode` attribute, so an
importer can save its asset correctly and then fail generating its own receipt. `[LIVE]`

### `==` on engine structs does not compare values

`unreal.Vector` compares by value; a general struct does not. A profile read from an asset and the same
profile read back after assignment compared **unequal** with `==` although every field matched. Compare
natively — follow a dotted property path and use the property's own `Identical`.

And make that comparison fail somewhere: a receipt that only checks "these two are equal" passes
vacuously if the comparison is broken. Check that two **deliberately different** values compare
unequal in the same receipt. `[LIVE]`

### Construct rotations and transforms with named fields and an explicit scale

- `unreal.Rotator(-90, 0, 0)` produced **roll**, not the intended pitch. Use
  `unreal.Rotator(pitch=-90., yaw=0., roll=0.)`, and copy existing rotations by named fields too.
  Zero rotations conceal the mismatch entirely, so keep a nonzero numerical axis check before saving
  any attachment or grip transform.
- `unreal.Transform(location=offset)` authored `Scale3D` as `(0,0,0)` in one delivered editor. **Set
  scale explicitly for every authored transform**, and reject collapsed required axes in the runtime
  validator — `FTransform::IsValid()` only establishes a finite, valid rotation, so it passes a
  collapsed frame. `[LIVE]`
- Rerouting an identity quaternion through Python produced `-0.0` where the native text had `0.0`. All
  native rotation comparisons stayed equal, but a changed-field gate built on exported text rejected it
  as a real change. **Keep the native verdict and the textual difference as two results**, rather than
  discarding either.

### Arrays of structs need explicit write-back

After editing a local copy from `for index, part in enumerate(parts)`, assign `parts[index] = part`
before saving the array. Omitting it leaves the asset unchanged **despite a successful save log**.
`[LIVE]`

### Material graph connections fail silently

`connect_material_expressions` returns a bool — check it. For a vector parameter's aggregate output use
the empty/default output name, not `RGB`; the latter failed for a colour parameter while the same name
worked for a texture sample. The graph still compiled, leaving both variants untinted, and only an
offscreen render exposed it. `[LIVE]`

### The Python commandlet reports success when the script fails

`UE4Editor-Cmd -run=pythonscript` returns **0 even when the script raises** — the error is only in the
log, as `LogPython: Error: Traceback`. Treat a run as passed only when the log has no Python error
**and** the script's own receipt file was written. `[LIVE]`

### Struct wrappers left alive at module scope can crash the editor on shutdown

A commandlet script saved its asset and then the editor died in `Py_FinalizeEx` — an access violation
in the garbage collector's `handle_weakrefs` — exiting 3. The script still held, at module level,
wrappers of structs read from *inside* another struct, whose addresses lay in that struct's memory.
Moving the work into a function, so the wrappers are released while the editor is still running, plus
`gc.collect()` at the end, exited 0. `[LIVE]`

---

## Building, packaging and headless runs {#build-and-package}

### New translation units can be absent from a cached UBT source list

Finish writing new `.cpp` files **before** gathering a build. When one is added while an earlier build
is in flight, a later cached makefile may still omit it — and a declared function then links as
unresolved although its definition is on disk. A one-off `-NoUBTMakefiles` build forces source
discovery without deleting build trees. `[LIVE]`

### `.uplugin` `SupportedTargetPlatforms` is an allowlist

Omitting a platform **excludes** the plugin there, silently. The OpenXR descriptor lists `Win32`
first; omitting it produced a persistent "project file is out of date" toast and no other symptom at
all. `[LIVE]`

### `RequestExitWithStatus(false, code)` does not set the exit code in a headless run

The graceful path posts `WM_QUIT` carrying the status, and nothing consumes that in a
`-nullrhi -unattended` run, so the process exits 0 whatever happened. Pass `Force = true` when
`FApp::IsUnattended()` — the engine flushes the log before terminating, so nothing is lost.

*Why you care:* a CI gate that always returns success is worse than no gate. `[SOURCE]` `[LIVE]`

### Clearing an environment variable is not the same as removing it

`RunUAT.bat` finds `AutomationTool.exe` by searching the current directory, so with
`NoDefaultCurrentDirectoryInExePath=1` set — as some hardened shells do — packaging fails with exit
**9009** and `'AutomationTool.exe' is not recognized`, while the tool runs fine directly.

Setting that variable to an empty string left the key present and **still produced 9009**. Remove the
key from the process environment and read back that it is gone before launching UAT. Keep the change
local to the packaging shell. `[LIVE]`

### Never run two editor instances at once

They share `Saved/Logs/<Project>.log`. The second corrupts the first one's results, and the failure
mode is a run that reports no summary and exits 0 — which reads as a dead test rather than a clobbered
log. `[LIVE]`

### An outside process reading a volatile file can stall the game thread

UE's `IFileManager::Move` replacement may delete the destination first. An ordinary file open does not
grant `FILE_SHARE_DELETE`, so a concurrent reader can make UE retry that deletion for **half a second
on the game thread**. Open volatile JSON with read/write/delete sharing, and retain the last real
sample only within a bounded freshness interval.

Then two reading rules that follow from it: do not treat a brief missing path as tracking loss, and do
not count repeated reads of the same sequence number as new evidence. `[LIVE]`

This is the concrete case of [the instrument sharing the
fault](06-debugging-methodology.md#instrument-shares-the-fault) — the observer was on the critical
path it was measuring.

### Replacing a file another process holds open can be refused outright

Handing a tool its input by writing a temporary file and renaming it over the real one is refused with
`WinError 5` while the reader has that file open; the rename succeeds a few milliseconds later. Retry
briefly, and **classify a refused rename as a tooling failure — neither a pass nor a fail.** `[LIVE]`

### `Select-Object -First` stops reading a native command, not the command

`& UE4Editor-Cmd.exe … | Select-String … | Select-Object -First 12` returns as soon as it has twelve
lines **while the editor keeps running**. A `finally` block straight after it therefore ran while the
editor was still open, and its removal of a staged package silently did nothing. Capture the whole
output first (`$log = & … 2>&1`), then filter, so cleanup runs after the editor has exited. `[LIVE]`

This is a sibling of the rule in [the validator
section](06-debugging-methodology.md): a shell pipeline changes both the exit status *and* the
lifetime of the producer, and neither is visible in the text you get back.

### `pwsh -File` passes a comma list as one string

`pwsh -File Verify.ps1 -Only a,b` gives `-Only` the single string `a,b`, so nothing matched and the
runner reported an **empty selection as passed**. Call the script in-process with an array instead.
Array splatting has the same trap — `@('-ProofItem', $path)` arrives as positional values, so splat a
hashtable.

The durable half of this is the guard, not the syntax: **a selector that matches nothing must fail.**
`[LIVE]`

### Run the suites against the packaged artifact, not only the editor

Frame pacing differs between an editor `-game` run and a cooked build, and any fixture whose setup is
timing-dependent can pass in one and fail in the other with **nothing about the rule under test having
changed**. One probe passed 29/29 in the editor and failed packaged, with the object 46 cm from the
hand by the time the grip was offered. See [TEST-030](pattern-catalog.md#test-030). `[LIVE]`

### The Launcher's "Convert Project" dialog

If the Epic Launcher offers to convert a project that is already the right version, check
`LauncherInstalled.dat` for a `UE_4.27` entry. Without one, the editor identifies itself by a registry
GUID and treats every project as foreign. Restarting the Launcher rewrites it. `[AUTHOR]`

---

## Inspecting Blueprints and assets {#blueprint-graphs}

Static Blueprint export is the Unreal equivalent of a disassembly pass, and it has the same hazard: a
tool that walks the documented containers can return a complete-looking **empty** answer. Every entry
here produced a confident wrong conclusion first.

### Collapsed graphs are not in `FunctionGraphs` or `UbergraphPages`

A `K2Node_Composite` — a "collapsed graph" — keeps its nodes in `UEdGraph::SubGraphs` of the graph that
contains it. An exporter walking only `Blueprint->FunctionGraphs` and `UbergraphPages` reports the
composite as one node with In and Out pins and nothing inside.

One movement manager kept its whole drive path — the movement input call, the actor basis, the relative
location write and the impulse — inside a composite, so the first export read as **"the manager never
moves the pawn."** Recurse into subgraphs and name them `<Parent>/<Subgraph>`. `[LIVE]`

### An implemented interface function's graph is somewhere else again

`UBlueprint::FunctionGraphs` and `UbergraphPages` do not hold an implemented interface function: its
graph is in `ImplementedInterfaces[i].Graphs`. An export reading only the first two showed a real
function as a signature with no graph, which looks exactly like an empty function. Macro graphs are a
third list.

*Why you care:* **an export made before you fixed this cannot show that a function is empty** — so
re-run it rather than reinterpreting the old output. This is
[META-016](pattern-catalog.md#meta-016) applied to a container of containers. `[LIVE]`

### A Blueprint function call returns through its **named** output pin

`UK2Node_CallFunction::GetReturnValuePin()` finds `ReturnValue`, which native functions use. A
Blueprint function returns through its named out parameter instead, so a tool that wraps a call's
result must look the pin up by name — and should **refuse rather than guess** when it cannot find it.
`[LIVE]`

### Compiling a parent Blueprint and its children in a row logs a REINST ensure

`FKismetEditorUtilities::CompileBlueprint` on a base class and then on its children logged a handled
ensure — "a REINST class was parented to another REINST class" — while the compile itself succeeded.
What to check afterwards is the result, not the log: search the saved `.uasset` bytes for `REINST_` and
`TRASHCLASS` before trusting it. `[LIVE]`

### The stock PNG render-target exporter writes allocation padding

4.27's `ImageUtils.cpp::ExportRenderTarget2DAsPNG` serialises `PNGData.GetAllocatedSize()` rather than
its element count. One capture was a valid 1,445,164-byte PNG followed by 179,283 zero bytes; a later
one had nonzero bytes in the padding. **A strict image validator is right to reject both.**

Preserve the engine's colour conversion and trim the exported file at its bounded, parsed `IEND`
chunk; keep full CRC and deflate validation in the verifier. No engine installation needs modifying.
`[SOURCE]` `[LIVE]`

### A shipped binary's `__FILE__` strings name the producer's build machine

A path that appears in hundreds of `__FILE__` strings inside a shipped game binary is the **build
machine of whoever compiled it**, not a location on yours. Treating one as local sends you looking for
an engine installation that was never there. See
[11 · RE anchoring & discovery](11-re-anchoring-and-discovery.md). `[STATIC]`

---

## The meta-gotcha {#meta-gotcha}

Most of the entries above were found by **a test passing when it should not have**, or by a headset
session contradicting a green suite. The engine rarely tells you that you are wrong; it tells you that
you are done.

Before believing a check, restore its bug on purpose and watch it fail — and where you can, keep that
restoration reachable as a named fault flag, so the negative control re-runs forever instead of
existing once in a commit message. See
[06 · Debugging methodology](06-debugging-methodology.md) and
[META-022](pattern-catalog.md#meta-022).

## Deliberately still open

This is a working reference, not a survey of the engine. Not covered, and not claimed: Chaos physics,
UE5 of any minor, nativization beyond the setting's three values, Niagara, the render-dependency graph,
level streaming under VR pacing, Android or standalone packaging, multiplayer, and the engine's own
automation framework. The entries here are what a VR project actually tripped over, in the order it
tripped.
