# Diablo II: Resurrected VR — source harvest

Reviewed **2026-10-07**, donor **0.141.0**, commit
[`4cb11b9ee35627bb58c3a13fb19b57b7b807aa44`](https://github.com/natpoh/diablo2-vr-port/tree/4cb11b9ee35627bb58c3a13fb19b57b7b807aa44).
This is **Resurrected**, not a VR conversion of the original sprite renderer.
The mod's source is available; the shipping game's source is not. Treat it as
RE-owned integration, not a source-owned engine port despite the repository name.

## What was actually established

**SOURCE:** inspected camera hooks, room activation, stereo scheduling, controller
mapping, HUD extraction and address resolution. No build, game launch, GPU capture
or headset test was performed. Donor comments about past experiments are **AUTHOR**
observations, not independently reproduced results.

The build produces a D2RLoader game plugin, a BodyWalk bridge and settings utility;
ReShade effects and FlatVR provide other parts of the presentation path. Public
headers describe the bridge, but this checkout is **not the complete BodyWalk/FlatVR
runtime implementation**. Do not infer OpenXR submission correctness from these headers.
The README specifies offline single-player, names game build 3.3.93787 / loader
1.3.1, and calls first-person a preview with unfinished weapon calibration.

The [MIT licence](https://github.com/natpoh/diablo2-vr-port/blob/4cb11b9ee35627bb58c3a13fb19b57b7b807aa44/LICENSE)
covers the mod's own code/shaders/pictures, **not** the separately licensed
BodyWalk/FlatVR products or the D2R VR name as a mark. Third-party licences remain separate.

## Read it for these mechanisms

The chapters below own the transferable method and failure tests; this table is
the donor's source map, not a second copy of those rules.

| Problem | Concrete donor seam | Owning method |
|---|---|---|
| Injected camera feeds back into native follow | `HandBackPoseForTick`, `SyncFrame`, `Apply`, lazy view/projection hooks; shadow-fit ray caller gets a local camera copy | [Camera loan and consumer exceptions](01-camera-and-tracking.md#camera-loan-consumers) |
| Isometric game becomes a walk-around miniature | `TopCamera`, `TableCamera`, `TrueScale`, `LiveScreen`; room anchor separate from avatar look-at | [Tabletop transform and physical screen calibration](01-camera-and-tracking.md#tabletop-screen-contract) |
| World ends behind a newly freed camera | `HookFindRooms` and `LoadAndAdd`: activate loaded neighbours, then bounded tiling | [Residency is not visibility](14-render-pass-hazard-atlas.md#activation-before-culling) |
| Effects disappear when the second draw gets zero time | `HookDrawGameScreen`, `PairWanted`, `right_dt_ms` | [Zero-delta render elision](17-teardown-fc2vr-native-stereo.md#zero-delta-render-elision) |
| Movement direction changes with the original overhead projection | `ViewStickToGame`, `TurnStick`, `ApplyActions` | [Projected input basis and menu ownership](03-input-and-locomotion.md#isometric-input-basis) |
| Extracting a minimap also removes labels | `OnScissor`, `OnBind`, `Publish` in `vr/hud.cpp` | [Extract the draw interval](04-ui-and-hud.md#hud-draw-interval) |
| Startup scan calls unavailable code permanently missing | `Resolve`, `Try`, `Search`, `Report` in `cleanroom/sigscan/` | [Coverage-aware resolution](11-re-anchoring-and-discovery.md#coverage-aware-resolver) |

Camera/room code is in
[`cleanroom/`](https://github.com/natpoh/diablo2-vr-port/tree/4cb11b9ee35627bb58c3a13fb19b57b7b807aa44/cleanroom);
scheduling and input in
[`vr/vrcam.cpp`](https://github.com/natpoh/diablo2-vr-port/blob/4cb11b9ee35627bb58c3a13fb19b57b7b807aa44/vr/vrcam.cpp);
HUD extraction in
[`vr/hud.cpp`](https://github.com/natpoh/diablo2-vr-port/blob/4cb11b9ee35627bb58c3a13fb19b57b7b807aa44/vr/hud.cpp).
Its replacement UI compositing equation is visible in
[`reshade/D2R_DepthFog.fx`](https://github.com/natpoh/diablo2-vr-port/blob/4cb11b9ee35627bb58c3a13fb19b57b7b807aa44/reshade/D2R_DepthFog.fx)
(`GamePieces` / `GameHud`).

## Limits worth keeping with the recipes

- **Stereo naming is not the scheduler.** The README describes alternating eyes,
  but the checked-in INI enables `pair_per_tick=1` and `right_dt_ms=0.01`.
  `PairWanted()` gates the paired path on resolved prerequisites, otherwise the
  code falls back to alternating eyes. Neither mode was measured here. The README
  asks users to disable DLSS/TAA; this is not a donor proof of per-eye temporal histories.
- **Freshness is not atomicity.** `D2RVR_Shared` has version/magic fields, a sample
  timestamp and a counter. The bridge writes fields then increments the counter;
  paired rendering copies the live block with `memcpy`. Those operations alone
  do not establish a coherent cross-process snapshot. Likewise, the camera's
  four-slot published ring assumes readers do not outlive slot reuse. Adopt the
  data contract, not an unproved concurrency guarantee; stress producer restart,
  a delayed reader, torn updates and timestamp wrap.
- **Weapon skeleton versus attachment owner.** `vr/skeletons.cpp::Hook` calls the
  native pose producer before `Arms`. Its disabled `HoldWeaponItem` path records
  unsuccessful attempts to stop weapon motion through the weapon skeleton;
  comments attribute it to body attachment bones instead. That history is AUTHOR;
  use it as a lead for [writer/consumer proof](11-re-anchoring-and-discovery.md#writer-census),
  not proof of any recipient's rig. Weapon calibration remains preview work.
- **Heuristics remain heuristics.** Broad render-target/scissor fingerprints,
  caller-range exceptions, a 0.5 m room-jump threshold and byte-equality restoration
  need recipient-specific evidence. A readable address or signature match does not
  prove its ABI or layout survived a game update.

## Transferring it to a source-owned target

For source-owned targets, implement these boundaries through explicit camera,
render-view, room-streaming and UI APIs. The donor's hooks and RVAs are examples
of reaching those boundaries in a closed engine, not required architecture.
