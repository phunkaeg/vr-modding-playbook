# GTFO_VR_Plugin & RoR2VRMod — input and interaction architecture

*Assembled from two deep source-read passes. The dispatching agent stalled before writing its own
synthesis, so this file was written from the two sub-agent reports verbatim; all `file:line` citations are
theirs. Paths are relative to each mod's root under `D:\Dev Debug\Other VR Mods\`.*

Both are Unity games modded in C#, which makes them a matched pair — but they differ in modding framework
(Harmony vs MonoMod), input stack (SteamVR Input vs Unity XR/OpenXR), and camera perspective
(first-person shooter vs third-person action). Where they still converge, that convergence is strong
evidence a pattern is necessary rather than stylistic.

---

# GTFO_VR_Plugin

## 1. Input abstraction
**SteamVR Input action sets, end to end.** A shipped `actions.json` defines the `/actions/default` set with
named actions (`Shoot`, `Interact`, `Jump`, `Crouch`, `Sprint`, `Reload`, `Movement` (vector2),
`SnapTurn` (vector2), `AimOrShove`, `WeaponRadialMenu`, `ToggleFlashlight`, plus a `Haptic` vibration
output). **Per-controller default bindings ship alongside it** — Vive, Oculus Touch, Knuckles,
Holographic, Vive Cosmos. Lookup via `SteamVR_Input.GetBooleanAction` / `GetVector2Action` in
`Core\VR_Input\SteamVR_InputHandler.cs:194-211`.

## 2. Injection point — *additive Harmony postfixes into the game's own input abstraction*
This is the notable part. `Injections\Input\InjectInput.cs` postfixes GTFO's **own** input layer:

- `InputMapper.DoGetAxis` → `__result += SteamVR_InputHandler.GetAxis(action);` (`InjectInput.cs:16-23`)
- `InputMapper.DoGetButton` / `DoGetButtonDown` / `DoGetButtonUp` →
  `__result = __result || SteamVR_InputHandler.GetActionX(action) || ...` (`InjectInput.cs:25-50`)

Because these are **Postfixes, not Prefix-with-`return false`, the original method body still runs** and
still polls real keyboard/gamepad state. VR is merged *on top* (`+=` for axes, `||` for booleans). The mod
never replaces the game's input system — it augments it, keyed by the game's own `InputAction` enum.

One deliberate exception, with the reason in a code comment: `InjectSkipButton.cs:14-26` is a **Prefix
returning `false`** on `PUI_SkipText.UpdateSkipTimer`, because "Skip button uses a part of input mapper
which doesn't handle gamepad or vr input, so we inject our own bypass."

## 3. Arbitration
**No per-frame arbitration at all.** VR values are unconditionally merged whenever the handler is
initialised. Real input is never suppressed and never gated on a presence/recency check.

Arbitration is instead **config-level and coarse**: `configUseControllers` (default **true**,
`VRConfig.cs:156`, described as *"You can play with a gamepad and head aiming if you set this to false"*)
switches whole subsystems between controller-driven and head-driven behaviour — aim direction
(`Controllers.cs:289-343`), turn axis source (`Snapturn.cs:42-66`), interaction ray
(`InjectControllerAim.cs:73-108`), two-handed grip, melee, cursor handling.

A `Dummy_InputHandler` (`Core\VR_Input\Dummy_InputHandler.cs`) exists but is **not** a KBM fallback — it
synthesises timed button presses (`m_frameDuration = 5`, commented *"We do not have superhuman fingers,
keep button pressed for a bit"*) so the mod's own in-VR terminal keyboard can drive native terminal
navigation actions.

## 4. Interaction — *repoint the engine's ray, don't build a new one*
`InjectControllerAim.cs:70-109` Prefixes `FPSCamera.UpdateCameraRay` and **returns `false`**, fully
replacing it with a `Physics.Raycast` (50 m, `LayerManager.MASK_CAMERA_RAY`) from
`Controllers.GetAimFromPos()` along `Controllers.GetAimForward()` — muzzle-aligned when a weapon is held,
controller transform otherwise, HMD as last resort.

Critically, it writes the results back into **GTFO's own fields**: `CameraRayPos`, `CameraRayCollider`,
`CameraRayNormal`, `CameraRayObject`, `CameraRayDist`. Those are what the native interaction, pickup and
door logic already read every frame — so every downstream system inherits controller aiming without
knowing anything changed.

## 5. Locomotion
**Smooth only. A repo-wide grep for "teleport" returns zero matches.** Movement is GTFO's own native
locomotion, fed by the SteamVR thumbstick axis through the additive merge above.

## 6 & 7. Comfort, and configurable vs hardcoded
Everything is BepInEx config, and additionally injected into GTFO's **native** options UI
(`VRConfig.cs:160-169`) so users configure it in-game rather than in a text file.

## Defaults table — GTFO
| Setting | Config key | Default | Source |
|---|---|---|---|
| Use VR controllers | `configUseControllers` | **true** | VRConfig.cs:156 |
| Smooth turn | `configSmoothSnapTurn` | **false** → *snap is default* | VRConfig.cs:90 |
| Snap turn angle | `configSnapTurnAmount` | **60°** (range 0–180) | VRConfig.cs:91 |
| Smooth turn speed | `configSmoothTurnSpeed` | **90°/s** | VRConfig.cs:92 |
| Snap turn cooldown | `m_snapTurnDelay` | **0.25 s** (hardcoded) | Snapturn.cs:21 |
| Snap turn screen fade | `SnapTurnFade` | on (hardcoded) | Snapturn.cs:85-89 |
| IRL crouch | `configIRLCrouch` | **true** | VRConfig.cs:88 |
| Crouch height threshold | `configCrouchHeight` | **115 cm** (90–145) | VRConfig.cs:89 |
| Vignette while moving | `configUseVignetteWhenMoving` | **false** | VRConfig.cs:94 |
| Movement vignette intensity | `configMovementVignetteIntensity` | **1.0** (0.5–1.5) | VRConfig.cs:95 |
| Static vignette | `configPostVignette` | **false** | VRConfig.cs:141 |
| Floor height offset | `configFloorOffset` | **0 cm** (0–50) | VRConfig.cs:93 |
| Two-handed aiming | `configTwoHandedAiming` | **true** | VRConfig.cs:115 |
| Always two-handed | — | **false** | VRConfig.cs:116 |
| Weapon forward tilt | — | **12°** (−45–45) | VRConfig.cs:124-125 |
| Weapon haptics | — | **true**, strength **0.75** | VRConfig.cs:112-113 |
| Laser pointer | — | **true**, colour **RED** | VRConfig.cs:118-120 |
| Pose prediction (translation / rotation) | — | **true / false** | VRConfig.cs:85-86 |
| Hidden area mask | — | **true** | VRConfig.cs:137-139 |
| Render resolution multiplier | — | **1.0** (0.2–2.5) | VRConfig.cs:135 |
| Seated mode | — | **does not exist** | — |

---

# RoR2VRMod

## 1. Input abstraction
**Unity XR + OpenXR, bootstrapped in code at runtime** — not SteamVR. `VRMod.cs:62-104` constructs
`XRGeneralSettings`/`XRManagerSettings`, instantiates `OpenXRLoader`, sets `renderMode = MultiPass`, and
registers five interaction profiles (Oculus Touch, Index, Vive, WMR, KHR Simple) at `VRMod.cs:122-127`. A
BepInEx **preloader patcher** copies `UnityOpenXR.dll` / `openxr_loader.dll` and the subsystem manifest
into the game before its assemblies load (`VREnabler.cs:26-77`).

State lands in `UnityEngine.XR.InputDevices` (`BaseInput.cs:15-25`, `VectorInput.cs:21-27`,
`ButtonInput.cs:18-24`); poses via `TrackedPoseDriver` components.

*A complete SteamVR Input path exists but is entirely commented out (`Controllers.cs:339-409`) — the mod
migrated off it.*

## 2. Injection point — *register as a Rewired hardware controller*
No Harmony anywhere in the tree (MonoMod only). Instead of patching the input system, the mod **becomes a
device in it**: `RewiredAddons.cs:11-121` builds a `HardwareControllerMap_Game` with 33 named elements and
registers it via `ReInput.UserData.AddCustomController()`. Action maps bind those elements to RoR2's
existing Rewired action IDs (`RewiredAddons.cs:123-172`). Each frame,
`ReInput.InputSourceUpdateEvent += UpdateVRInputs` (`Controllers.cs:46`) pushes polled XR values in via
`CustomController.SetAxisValueById` / `SetButtonValueById`.

It even adds a **new** RoR2 input action ("RecenterHMD", id 150) and back-fills its bindings into existing
save profiles (`ActionAddons.cs:18,38-46`).

## 3. Arbitration
**None of the mod's own.** The VR controller is just another Rewired device, and Rewired's native
last-active-controller-wins semantics decide authority. The one explicit override: when motion controls
are on, mouse/stick *look* input is hard-zeroed (`CameraFixes.cs:535-537`) rather than arbitrated.

## 4. Interaction — *repoint the engine's aim origin*
Same pattern as GTFO, different field. On body spawn:

```
body.aimOriginTransform = dominantHand.currentHand.currentMuzzle.transform;   // MotionControls.cs:626
```

That is RoR2's **own** `CharacterBody` field, which all native attack/targeting code reads. The crosshair
raycast is likewise repointed to `GetHandByDominance(true).aimRay` (`CameraFixes.cs:811-829`), and dozens
of per-skill `GetAimRay` overrides substitute hand transforms (`MotionControlledAbilities.cs`).

**Engine aim-assist is deliberately disabled for the local player** (`MotionControlledAbilities.cs:842-862`)
and the aim-assist IL block is stripped from the look-input path (`CameraFixes.cs:553-558`).

**Third-person divergence:** `FirstPerson` (default **true**) converts the game to first person — camera
re-parented under an `XROrigin` at a collider-derived eye height, body hidden every frame. Head tracking is
applied **unconditionally, even in third person**, as a local offset on the vanilla orbit camera. Motion
controls only exist when `FirstPerson` is true; with it off, "VR controllers act as a simple gamepad."

Melee is driven by **physical swing speed thresholds**, per character (Merc 20, Loader 12, Acrid 10).

## 5. Locomotion
**Smooth only — again, zero "teleport" matches repo-wide.** Optional
`ControllerMovementDirection` (default **false**) switches the movement yaw reference from head to
off-hand controller.

## 6 & 7. Comfort and config
BepInEx config, surfaced through an in-game settings UI built by reflecting over the config dictionary
(`SettingsAddon.cs:170-339`).

## Defaults table — RoR2
| Setting | Config key | Default | Source |
|---|---|---|---|
| First person | `FirstPerson` | **true** | ModConfig.cs:82-87 |
| Use motion controls | `UseMotionControls` | **true** (only if FirstPerson) | ModConfig.cs:271-276, 301 |
| Snap turn | `SnapTurn` | **true** | ModConfig.cs:246-251 |
| Snap turn angle | `SnapTurnAngle` | **45°** | ModConfig.cs:252-257 |
| Snap turn hold delay | `SnapTurnHoldDelay` | **0.33 s** | ModConfig.cs:258-263 |
| Locked camera pitch | `LockedCameraPitch` | **true** (forced true when snap turn or motion controls on) | ModConfig.cs:265-270, 306 |
| Comfort vignette | `UseConfortVignette` | **true** | ModConfig.cs:88-93 |
| Seated mode | `SeatedMode` | **false** → roomscale default | ModConfig.cs:94-99 |
| Height multiplier | `HeightMultiplier` | **1.0** | ModConfig.cs:100-105 |
| Controller movement direction | `ControllerMovementDirection` | **false** (head-relative) | ModConfig.cs:283-288 |
| Left dominant hand | `LeftDominantHand` | **false** | ModConfig.cs:277-282 |
| Melee swing thresholds | Merc / Loader / Acrid | **20 / 12 / 10** | ModConfig.cs:137-154 |
| Two-handed grip snap angle | Bandit / Railgunner | **40° / 50°** | ModConfig.cs:131-136,155-160 |
| Scope zoom multiplier | `RailgunnerZoomMultiplier` | **3.0** | ModConfig.cs:161-166 |
| Aim stabiliser amount | `AimStabiliserAmount` | **0.5** — *consumer is commented out; dead config* | ModConfig.cs:289-294, HandController.cs:143-183 |
| Oculus mode (legacy raw joystick) | `OculusMode` | **false**, largely dead code | ModConfig.cs:76-81 |

---

# Direct comparison

| Dimension | GTFO_VR_Plugin | RoR2VRMod | Converged? |
|---|---|---|---|
| Input stack | SteamVR Input action sets | Unity XR / OpenXR | ✗ (RoR2 migrated *off* SteamVR) |
| Patch framework | Harmony | MonoMod only | ✗ |
| Injection strategy | Postfix the game's input abstraction, merge additively | Register as a Rewired hardware device | ✗ mechanism, ✓ principle (feed the game's own layer) |
| Real-vs-synthetic arbitration | none — additive merge | none — Rewired last-active-wins | **✓** |
| Aim/interaction | repoint `FPSCamera.CameraRay*` | repoint `CharacterBody.aimOriginTransform` | **✓✓ strongly** |
| Engine aim-assist | not addressed | explicitly disabled for local player | ✗ |
| Teleport locomotion | **absent** (0 grep hits) | **absent** (0 grep hits) | **✓** |
| Default turn | **snap**, 60° | **snap**, 45° | **✓** |
| Turn re-trigger delay | 0.25 s | 0.33 s | ✓ same order |
| Comfort vignette default | **off** | **on** | ✗ |
| Roomscale/standing default | standing (no seated option at all) | roomscale (`SeatedMode` false) | ✓ |
| Config surfaced in-game | yes, injected into native options UI | yes, generated settings page | **✓** |

---

## Transferable lessons

1. **Repoint the engine's own aim/ray field instead of building a parallel aim system.** *(Supported
   independently by BOTH mods.)* GTFO overwrites `FPSCamera.CameraRay*`; RoR2 assigns
   `CharacterBody.aimOriginTransform`. Every downstream native system — interaction prompts, pickups,
   doors, targeting — then inherits controller aiming for free, with no knowledge that anything changed.
   This is the single strongest convergence in the study.
2. **Neither shipped mod does per-frame real-vs-synthetic input arbitration.** GTFO merges additively and
   never suppresses real input; RoR2 relies on Rewired's last-active-device semantics. Both instead expose
   a **coarse mode switch** (`configUseControllers`, `UseMotionControls`) that reconfigures whole
   subsystems. Worth weighing against designs that build a bounded recency window.
3. **Additive postfix beats wholesale replacement.** GTFO's `+=` / `||` merge onto the game's *own* input
   abstraction means the flat game keeps working, gamepad play still functions, and the mod owns no
   input state machine. Reserve full override (`Prefix → return false`) for the specific paths that
   provably ignore the abstraction — GTFO does exactly that once, with the reason in a comment.
4. **Neither ships teleport locomotion.** Zero matches in either codebase. Both are smooth-only with snap
   turn as the comfort lever — evidence that for action-paced games, snap turn plus a vignette is the
   shipped compromise, not teleport.
5. **Snap turn is the shipped default in both** (60° and 45°), each with a re-trigger delay of the same
   order (0.25 s / 0.33 s), and GTFO additionally fades the screen to black across the turn.
6. **Register as a device where the engine has a device abstraction.** RoR2's `CustomController` route
   means Rewired handles binding, remapping, profiles and last-active arbitration for free — and the mod
   could even add a *new* named action that appears in the game's own binding UI. If your target has a
   device layer, entering it is cheaper than patching around it.
7. **Config belongs in the game's own settings UI.** Both mods inject their options into the native
   options menu rather than leaving users in a text file — GTFO registers into GTFO's settings system,
   RoR2 generates a page by reflecting over its config dictionary.
8. **Watch for dead config.** RoR2 ships `AimStabiliserAmount` (default 0.5) whose entire consumer is
   commented out — a user-facing setting that does nothing. A cheap CI check that every config key is read
   somewhere would have caught it.

## Not determined
**GTFO:** manifest-path wiring inside the precompiled `SteamVR_Standalone_IL2CPP.dll`; seated/standing
mode (appears simply absent).
**RoR2:** where OpenXR action-binding data lives (no JSON/asset found in the C# tree — likely a
Unity-serialised asset); whether `SnapTurn`'s "unavailable in third person" description matches a real
runtime gate (no such conditional found — possibly stale text); whether `AimStabiliserAmount` is dead in
the shipped build or stabilised elsewhere.
