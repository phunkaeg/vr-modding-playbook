# VR Expansion Plugin — source-owned solutions, bounded RE transfers

This is a **reference map**, not another integration framework to install into a closed game.
VR Expansion Plugin (VRE), by Joshua Statzer / mordentral, is an Unreal gameplay plugin. It is distinct
from **UEVR**, the injector. Use VRE directly only where you can build and ship the appropriate UE
project/plugin code. For UEVR companions and other RE-owned mods, borrow contracts and discriminating
tests, then prove the target's own implementation boundary.

## What was actually inspected {#review-scope}

Review date: **2026-09-28**. Method: clean-checkout identity checks, targeted symbol searches, and reading
function bodies plus their relevant callers. The 4.27 branch was already local; the UE5 reference was
fetched from the public upstream into ignored local storage. No builds, game runs, performance
measurements, multiplayer sessions or headset tests were performed. All implementation observations
below are **SOURCE**; transfer to another engine remains **INFERENCE** until tested there.

| Snapshot | Immutable identity | Boundary |
|---|---|---|
| `4.27-Locked` | [`4e52c69393271f3abce11d22c5265aa14373cb6e`](https://github.com/mordentral/VRExpansionPlugin/tree/4e52c69393271f3abce11d22c5265aa14373cb6e) | Basis of the detailed implementation harvest; engine compatibility still needs a local build |
| UE5 `Master` | [`c19f6e27440bc599c3b132cb38c2ffec3996008b`](https://github.com/mordentral/VRExpansionPlugin/tree/c19f6e27440bc599c3b132cb38c2ffec3996008b) | Targeted comparison only; plugin descriptor `VersionName` is `5.8`, not proof of compatibility with every UE5 minor |

The ledger tracks these as two **versioned snapshots of one upstream**, not two independent solutions.
Both carry the upstream MIT license; retain its notice when reusing covered code. This harvest adds
original explanations and links, not a source mirror. Some source files also carry engine-origin
notices: check those and applicable engine terms before copying them outside an Unreal project.

## Go directly to the problem

| Problem / design decision | Owning method | Source seam inspected |
|---|---|---|
| Recoil, support hand and collision compete for the final pose | [Ordered grip transform pipeline](02-viewmodels-and-hands.md#grip-transform-pipeline) | `GetGripWorldTransform`, `TickGrip`, `UGS_Default` |
| Palm offsets work one-handed but break two-handed aim | [Shared interaction pivots](02-viewmodels-and-hands.md#grip-transform-pipeline) | `GripActor`, `GripComponent`, `CalculateSecondaryLocation` |
| Held object jitters during contact or a support grip | [Conditional late update](02-viewmodels-and-hands.md#grip-design-space) | `ProcessGripArrayLateUpdatePrimitives` in both snapshots |
| Physics grip feels wrong despite a correct visual pose | [COM versus constraint anchor](02-viewmodels-and-hands.md#grip-design-space) | `SetUpPhysicsHandle` in both snapshots |
| Holstered object jumps back one frame later | [Physics-to-socket handoff](02-viewmodels-and-hands.md#physics-to-socket) | `Socket_Implementation` in both snapshots |
| Snap turn translates the wearer; teleport misses its marker | [Occupied VR pivot](03-input-and-locomotion.md#vr-turn-pivot) | `AddActorWorldRotationVR`, `SetActorLocationAndRotationVR` |
| Physical steps are doubled or leave residual velocity | [Room-scale movement accounting](03-input-and-locomotion.md#roomscale-movement-accounting) | 4.27 movement helpers and their movement call sites |
| A turn/teleport works locally, then network correction undoes it | [VR actions in saved moves](03-input-and-locomotion.md#vr-move-actions) | action construction; both `CanCombineWith` implementations and UE5 `CanCombine` |
| Teleport stretches a held prop or drags a world-fixed control | [Per-grip discontinuity policy](03-input-and-locomotion.md#vr-move-actions) | 4.27 `TeleportMoveGrip_Impl`, post-teleport `TickGrip` |
| Stereo panel ghosts, survives teardown or fails in flat mode | [Widget resource lifecycle](04-ui-and-hud.md#stereo-widget-lifecycle) | 4.27 `UVRStereoWidgetComponent` |
| AI/navigation still treat the player as standing at the old root | [VR-aware location consumers](07-engine-integration-safety.md#vr-location-consumers) | 4.27 nav-agent location; sight-target selection in both snapshots |

## What changed from the previous harvest

The earlier enum survey exposed useful choices, but names were not sufficient evidence for their
implementation. This pass corrects three overgeneralizations in the owning chapters:

- Candidate detection and grip response are separate; VRE leaves candidate selection to the caller.
- Collision-based late-update suppression has explicit exceptions and additional authority/script gates.
- A constraint at the controller and a changed physical centre of mass are different operations.

The UE5 comparison also prevents false API equivalence: its rotation helpers add pivot-selection
parameters, saved-move capsule-height representation differs, and the physics setup has a
geometry-collection COM fallback. Preserve the invariant, not a copied struct layout or signature.

## Use it in a port

**Source-owned Unreal:** select the exact engine-compatible branch, establish an unchanged build,
then exercise the relevant component in a minimal scene. The upstream
[installation guide](https://github.com/mordentral/VRExpansionPlugin#how-do-i-install-it) and
[example project](https://github.com/mordentral/VRExpPluginExample) are setup leads, not additional
implementation evidence harvested here.

**UEVR companion:** keep UEVR's stereo/pose ownership. Use the game's reflected APIs and existing
interaction/movement owners to implement a selected contract. Having VRE source does not make its
classes present in that game's cooked binary. Follow the [UEVR route](uevr-route.md).

**Other RE-owned engines:** choose one failing behavior from the table, read the method and its proof,
then map the producer, consumer, timing and ownership onto your target. Do not import an entire UE
physics/network stack to solve one handoff bug. The tests in these chapters are proposed acceptance
tests, not evidence that any fleet project already passes them.

## Deliberately still open

This is a partial harvest, not a review of the whole plugin. Weapon-specific grip scripts, detailed
melee contact/damage behavior, hand-socket pose retargeting, throw velocity sampling implementations,
OpenXR extension lifecycle, render-target-manager internals, and end-to-end multiplayer validation
remain candidates for separate focused reviews. The plugin is not evidence for an injected game's
native stereo re-entry seam, renderer ABI, or headset performance.
