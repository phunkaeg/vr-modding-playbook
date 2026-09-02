# UEVR AFW — generic input binding architecture

Source read: `D:\Dev Debug\UEVR-UEVR_AFW_v1.0-beta.5\` (~196 source files, ~16k lines in the files below).
Primary files (line counts): `src/mods/VR.cpp` (3936), `src/mods/VR.hpp` (1370), `src/mods/UObjectHook.cpp` (4368),
`src/mods/PluginLoader.cpp` (2314), `src/mods/vr/runtimes/OpenXR.cpp` (1920) + `OpenXR.hpp`,
`src/mods/vr/runtimes/OpenVR.cpp` (308), `src/mods/vr/runtimes/VRRuntime.hpp` (197),
`src/mods/vr/Bindings.cpp` (829), `src/mods/vr/FFakeStereoRenderingHook.cpp` (~7000, spot-read around
the view-offset/aim logic), `src/hooks/XInputHook.cpp` (272), `src/hooks/DInputHook.cpp` (145),
`src/mods/LuaLoader.cpp` (359), `lua-api/lib/src/ScriptContext.cpp`, `include/uevr/API.hpp`,
`examples/example_plugin/Plugin.cpp`.

## 1. Input abstraction

Both OpenVR and OpenXR are supported, and both are driven from **one shared, hand-authored action
manifest** — not per-title data. `VR::actions_json` (`src/mods/vr/Bindings.cpp:3-154`) declares a single
action set `/actions/default` with ~25 canonical actions (`Trigger`, `Grip`, `Joystick`, `AButtonLeft`,
`Teleport`, `Squeeze`, `SkeletonLeftHand`, `Pose`/`GripPose`, `Haptic`, etc.) — this is literally the
SteamVR Input System action-manifest JSON format. Five more static JSON strings
(`binding_rift_json`, `bindings_oculus_touch_json`, `binding_vive`, `bindings_vive_controller`,
`bindings_knuckles`, `Bindings.cpp:156-830`) are the default per-controller-type binding files SteamVR
Input expects.

- **OpenVR path**: these strings are written to disk under the per-game persistent dir and loaded with
  the real SteamVR Input API — `VR::initialize_openvr_input()` writes `m_binding_files` to
  `module_directory`, then calls `vr::VRInput()->SetActionManifestPath(actions_path...)`
  (`src/mods/VR.cpp:567-585`), then resolves action-set/action handles via
  `GetActionSetHandle`/`GetActionHandle` (`VR.cpp:588-608`). Runtime reads happen via
  `GetDigitalActionData`/`GetAnalogActionData`/`GetPoseActionDataForNextFrame`
  (`VR.cpp:3716`, `VR.cpp:3735`, `runtimes/OpenVR.cpp:64-67`). This is the modern SteamVR
  action-based system, not the legacy `GetControllerState` polling API.
- **OpenXR path**: there is no static `.json` interaction-profile manifest file. Instead
  `OpenXR::initialize_actions()` (`src/mods/vr/runtimes/OpenXR.cpp:821-1178`) **parses the same
  `actions_json` string** at runtime, creates one `XrActionSet` (`OpenXR.cpp:843-850`), and for each
  action translates its OpenVR-style `type` (`boolean`/`pose`/`vector1`/`vector2`/`vibration`,
  `skeleton` is dropped — `OpenXR.cpp:926-957`, `937-938`) into the matching `XrActionType`, then
  auto-generates `xrSuggestInteractionProfileBindings` calls for a **hard-coded list of six supported
  interaction profiles** (`khr/simple_controller`, `oculus/touch_controller`, `oculus/go_controller`,
  `valve/index_controller`, `microsoft/motion_controller`, `htc/vive_controller` —
  `OpenXR.hpp:492-499`), using a hard-coded path→action lookup table `s_bindings_map`
  (`OpenXR.hpp:434-475`, e.g. `/user/hand/*/input/squeeze → "grip"`). There is no per-interaction-profile
  binding manifest file for the default case; it's generic C++ glue code. Actions are polled once per
  frame via `xrSyncActions`/`xrGetActionStatePose`/etc. in `OpenXR::update_input()`
  (`OpenXR.cpp:584-666`). `OpenXR::get_current_interaction_profile()` (`OpenXR.cpp:803-810`) reads back
  which physical controller/profile the XR runtime actually bound.

So: controller state lands in named, engine-agnostic actions (`"trigger"`, `"grip"`, `"joystick"`, …)
identical across both backends. There *is* a bindings manifest, but it is generic-controller-shaped
(rift/vive/touch/knuckles), not game-shaped — no game ever appears in this file.

## 2. Injection point (the crux — be specific)

**UEVR injects controller state as a fake XInput gamepad, by inline-hooking `XInputGetState` in
`xinput1_3.dll`/`xinput1_4.dll`.** `XInputHook::XInputHook()` (`src/hooks/XInputHook.cpp:14-209`) locates
both DLLs and installs `safetyhook::create_inline` hooks on `XInputGetState`/`XInputSetState` for both
versions (falling back to resolving a leading `JMP` if the direct hook fails —
`XInputHook.cpp:100-111`). The hook trampoline (`get_state_hook_1_4`/`get_state_hook_1_3`,
`XInputHook.cpp:211-257`) calls the real function first, then dispatches to every loaded `Mod`'s
`on_xinput_get_state`.

`VR::on_xinput_get_state()` (`src/mods/VR.cpp:1068-1436`, ~370 lines) is where actions become a gamepad
state: it reads the resolved OpenVR/OpenXR action values (`is_action_active`, `is_action_active_any_joystick`,
`get_joystick_axis` — used throughout `VR.cpp:1153-1741`) and sets the `XINPUT_STATE::Gamepad` bitfields —
e.g. right A-button action → `XINPUT_GAMEPAD_A` (`VR.cpp:1166-1167`), trigger action → `bLeftTrigger`/
`bRightTrigger = 255` (`VR.cpp:1199-1208`), joystick axes added into `sThumbLX/LY/RX/RY`
(`VR.cpp:1245-1255`). It also spoofs the Start/Back buttons for a long-press "pause/select" menu gesture
using `VRRuntime::handle_pause_select()` (`VRRuntime.hpp:125-146`, called `VR.cpp:1157`,
`do_pause_select` `VR.cpp:1110-1132`), and tracks the lowest polled `user_index` across frames
(`VR.cpp:1082-1099`) so it spoofs onto whichever XInput slot the game is actually reading, faking
`ERROR_SUCCESS` and a connected-controller status if none is physically present
(`VR.cpp:1101-1106,1134-1136`).

This is **not** reflection-based `APlayerController`/`UPlayerInput` manipulation, and **not** console
commands — `CVarManager`'s console-variable list (`src/mods/vr/CVarManager.hpp:222-241`) is entirely
rendering knobs (motion blur, DoF, AO, tonemapper), never input. `DInputHook` (`src/hooks/DInputHook.cpp`)
only hooks `IDirectInput8::EnumDevices` to suppress spurious controller-enumeration calls when no VR
controllers are active (`DInputHook.cpp:130-145`); it does not spoof DirectInput axis/button state.
XInput emulation is the sole synthetic-input channel, and it is entirely generic: it assumes only that
the target game (a) polls XInput for gamepad input and (b) already has gamepad bindings wired to its own
`UPlayerInput`/Enhanced Input config — UEVR never touches that binding itself. No occurrence of
`AddMovementInput`, `MoveForward`, or similar reflection-driven movement calls exists anywhere in `src/`
(checked via repo-wide search) — locomotion is 100% "the game thinks a real Xbox controller moved its
stick."

## 3. Arbitration

Real-gamepad-vs-synthetic is time-based, not a hard switch. `VR::is_using_controllers()`
(`src/mods/VR.hpp:379-382`) is true only if `m_controllers_allowed` is on, the HMD is active, at least one
VR controller is registered, and a VR controller was interacted with inside a **configurable inactivity
window** (`m_motion_controls_inactivity_timer`, default 30s, range 30–100s — `VR.hpp:1053`). If the user
has not touched the VR controllers recently, `on_xinput_get_state` returns early after calling
`update_imgui_state_from_xinput_state`/`gamepad_snapturn` (`VR.cpp:1138-1140`) and leaves the real
`XINPUT_STATE` from the physical pad completely untouched — a real gamepad works normally when VR
controllers are idle. Once VR controllers have been used within the last 5 seconds
(`is_using_controllers_within(5s)`, `VR.hpp:384-386`), the hook zeroes out the whole `Gamepad` struct
(`VR.cpp:1143-1151`) before OR-ing in VR-derived button/axis state — full override, VR wins. Between 5s
and the inactivity-timer window there's a middle zone where the report is still forced to
`ERROR_SUCCESS` (`VR.cpp:1134-1136`) but buttons aren't cleared, so a real pad's last-read state and any
VR-derived bits can coexist (VR bits are additive on the thumbsticks — `VR.cpp:1251-1255` adds the VR
axis onto whatever the physical stick already reported). There is also an explicit
`m_swap_controllers` left/right-input swap toggle (`VR.hpp:988`) but no separate "prefer gamepad" toggle
beyond the inactivity timer and `m_controllers_allowed`.

## 4. Interaction

There is **no built-in generic "point at / grab / use"** for gameplay purposes. Search of `src/` for
`AddMovementInput`, `grab`, `WidgetInteraction`, teleport-locomotion code, etc. turns up nothing beyond
the raw `Teleport` action *declared* in the binding manifest (`Bindings.cpp:100-103`, bound to a
thumbstick north-gesture on Knuckles, `Bindings.cpp:781-803`) — grepping all of `src/` for "teleport"
(case-insensitive) hits only `Bindings.cpp`; no C++ consumer exists. It is a stubbed action exposed only
for a plugin/Lua author to read via `is_action_active`, not a shipped feature.

What *is* generic is a **calibration-time "intuitive attachment" (grab-to-attach) tool** in
`UObjectHook` (`src/mods/UObjectHook.cpp:843-947`): a small overlap-detection actor is placed at each
hand (`m_overlap_detection_actor`/`_left`, updated `UObjectHook.cpp:833-851`), and while the A button is
held, any `UPrimitiveComponent` overlapping that sphere gets permanently attached to follow the
controller's motion with a saved offset (`get_or_add_motion_controller_state`, `state.adjusting = true`,
`UObjectHook.cpp:931-934`, offset math `UObjectHook.cpp:975-977`). This is a **developer/setup-time
calibration aid** (used to align a weapon mesh or hand model to the physical controller once, then
persisted — see §5), not a runtime interact/grab system driven by game logic; it never calls into any
game "pick up" or "use" function.

## 5. Per-game escape hatches

Everything is keyed off `Framework::get_persistent_dir()`, which returns
`%APPDATA%\UnrealVRMod\<game_exe_name>\` (derived from the running executable's stem —
`src/Framework.cpp:1113-1132`) — i.e. every mechanism below is automatically per-game because the
directory is named after the game's exe:

- **Per-controller binding overrides (OpenXR only)**: `OpenXR::initialize_actions()` looks for
  `<controller_profile>.json` first in the per-game persistent dir, then in a global
  `UEVR\Profiles\` dir, and if found it clears the generic `s_bindings_map`-derived bindings and rebuilds
  them from `bindings`/`vector2_associations` entries in that file (`OpenXR.cpp:1059-1136`). This is the
  literal "supply the interaction-profile knowledge UEVR can't infer" hook for OpenXR headsets/profiles
  UEVR's hard-coded table doesn't handle well.
- **UObjectHook attachment state**: every "intuitive attachment" (or manually path-picked UObject
  attachment) is serialized to `<persistent_dir>\uobjecthook\*.json`
  (`UObjectHook::get_persistent_dir()`, `UObjectHook.cpp:1289-1303`; load/save around
  `UObjectHook.cpp:1446-1513`, `2101-2105`) — a UObject-path-driven per-game config the user (or a
  packaged plugin) builds up once per title (e.g. "attach the right hand to this SkeletalMeshComponent
  path with this rotation/location offset").
- **Native C++ plugin API**: `PluginLoader::early_init()` loads every `.dll` from
  `<persistent_dir>\plugins\` and a global `..\UEVR\plugins\` (`src/mods/PluginLoader.cpp:1725-1758`).
  `include/uevr/API.hpp` exposes full UE reflection to those plugins — `find_uobject<T>(name)`
  (`API.hpp:168`), `UObject::call_function`/`process_event` (`API.hpp:324-330`, `580`),
  `UStruct::find_function` (`API.hpp:456-458`) — i.e. a plugin author can call arbitrary
  `UFunction`s (including `APlayerController`/`UPlayerInput`-derived ones) by name via reflection. The
  shipped `examples/example_plugin/Plugin.cpp:239-240` demonstrates calling
  `K2_GetComponentsByClass`/`GetComponentsByClass` this way, and reading UEVR's own mod settings via
  `API::VR::get_mod_value` (`Plugin.cpp:544`).
- **Lua plugin API**: `LuaLoader::reset_scripts()` autoloads every `.lua` from
  `<persistent_dir>\scripts\` and a global `..\UEVR\scripts\` (`src/mods/LuaLoader.cpp:292-297`).
  `ScriptContext.cpp` binds `vr.is_action_active`, `vr.get_joystick_axis`,
  `vr.get_left_controller_index`/`get_right_controller_index`, `vr.set_mod_value`/`get_mod_value`
  (`lua-api/lib/src/ScriptContext.cpp:454-484`), and lets a script register its own
  `on_xinput_get_state`/`on_xinput_set_state` callback that runs inside the same hook chain as UEVR's own
  gamepad synthesis (`ScriptContext.cpp:111-131`, dispatch `ScriptContext.cpp:1219-1242`) — a script can
  observe or further modify the exact same synthetic `XINPUT_STATE` before it reaches the game.
- **Per-game config values**: every tunable in `VR.hpp` (aim method, decoupled pitch, snap-turn, dpad
  shifting, deadzones, …) is persisted through `on_config_save`/`on_config_load` into the same per-game
  `config.txt` under the persistent dir, so defaults below are exactly that — global defaults a user or
  packaged profile overrides per title.

## 6. Defaults

The important qualitative finding: **`AimMethod` and `MovementOrientation` both default to `GAME`**
(`VR.hpp:1028-1029`, enum order `GAME, HEAD, RIGHT_CONTROLLER, LEFT_CONTROLLER, TWO_HANDED_RIGHT,
TWO_HANDED_LEFT` — `VR.hpp:941-948`), i.e. out of the box UEVR does not redirect aim or movement
orientation to any VR controller at all — it leaves the game's native camera-driven aim/movement
untouched until a user (or profile) explicitly opts a title into controller-based aiming. There is
**no vignette/comfort-mode setting anywhere in `src/`** — a repo-wide search for "vignette"/"comfort"
returns zero matches.

## Defaults table
| Setting | name | Default | Source |
|---|---|---|---|
| Aim method | `AimMethod` | `Game` (0 = unmodified game aim; options: Game/Head/Right/Left/Two-Handed) | `VR.hpp:1028`, names `VR.hpp:941-948` |
| Movement orientation | `MovementOrientation` | `Game` | `VR.hpp:1029` |
| Aim speed | `AimSpeed` | `15.0` (range 0.01–25) | `VR.hpp:1035` |
| Aim smoothing/interp | `AimInterp` | `true` | `VR.hpp:1034` |
| Use pawn control rotation | `AimUsePawnControlRotation` | `false` | `VR.hpp:1031` |
| Modify player control rotation | `AimModifyPlayerControlRotation` | `false` | `VR.hpp:1032` |
| Aim multiplayer support | `AimMPSupport` | `false` | `VR.hpp:1033` |
| Snap turn (vs smooth) | `SnapTurn` | `false` (smooth turn is the default) | `VR.hpp:1018` |
| Snap turn angle | `SnapturnTurnAngle` | `45°` (range 1–359) | `VR.hpp:1020` |
| Snap turn joystick deadzone | `SnapturnJoystickDeadzone` | `0.2` (range 0.01–0.99) | `VR.hpp:1019` |
| Roomscale movement | `RoomscaleMovement` | `false` | `VR.hpp:986` |
| Roomscale sweep | `RoomscaleMovementSweep` | `true` | `VR.hpp:987` |
| Decoupled pitch | `DecoupledPitch` | `false` | `VR.hpp:982` |
| Decoupled pitch UI auto-adjust | `DecoupledPitchUIAdjust` | `true` | `VR.hpp:983` |
| DPad shifting (thumbstick as dpad) | `DPadShifting` | `true`, method = Right Thumbrest + Left Joystick | `VR.hpp:1036-1037` |
| Motion-controls inactivity timeout (real pad fallback) | `MotionControlsInactivityTimer` | `30s` (range 30–100) | `VR.hpp:1053` |
| Left-handed / swap controllers | `SwapControllerInputs` | `false` | `VR.hpp:988` |
| VR joystick deadzone | `JoystickDeadzone` | `0.2` (range 0.01–0.9) | `VR.hpp:1054` |
| Controller pitch offset | `ControllerPitchOffset` | `0°` (range -90–90) | `VR.hpp:1025` |
| World scale | `WorldScale` | `1.0` (range 0.01–10) | `VR.hpp:1059` |
| Controllers allowed | `ControllersAllowed` | `true` | `VR.hpp:1222` |
| Comfort vignette | — | not present in source | n/a |

## Transferable lessons

- **The generic part is the controller→gamepad translation layer, not the game-binding layer.** UEVR
  fully generalizes "read a VR controller action and produce a plausible XInput report"
  (`VR.cpp:1068-1436`) across any UE title that already accepts gamepad input — that part genuinely
  needs no per-game knowledge and a hand-written mod targeting one game gains little by reinventing it.
- **What it cannot generalize is "which axis means what to this specific game."** `AimMethod` and
  `MovementOrientation` both ship defaulted to `GAME` (`VR.hpp:1028-1029`) — UEVR explicitly declines to
  guess whether a title's gamepad aim/movement scheme is compatible with VR-controller-driven aim; the
  UI itself warns "Some games may not work with this enabled" (`VR.cpp:3075`). A hand-written single-game
  mod that already knows the correct aim/movement wiring is doing exactly the work UEVR pushes onto the
  user/profile author.
- **Reflection is reserved for engine-guaranteed base classes, not game classes.** The one place UEVR
  itself calls UE reflection generically (`bUsePawnControlRotation` on `UCameraComponent`,
  `FFakeStereoRenderingHook.cpp:5015-5064`) works only because that property exists on the stock engine
  camera component in virtually every UE project. Anything game-specific (which mesh is the weapon, which
  component is "the hand") is explicitly punted to the UObjectHook attach-by-hand tool
  (`UObjectHook.cpp:843-947`) or to a plugin calling `find_uobject`/`call_function` by path
  (`API.hpp:168,324-330`) — i.e. genuinely game-specific knowledge has no generic substitute and must be
  supplied per title either by a human using the calibration UI or by a plugin author.
  This is a strong signal for projects hand-writing bindings for one known game: skip the
  attach-by-overlap dance and just hard-code the known component path/offset — the generic tool only
  pays for itself when the target is unknown.
- **There is no generic locomotion, teleport, or grab/interact system, by design.** The `Teleport` action
  exists only as an unused stub in the binding manifest (`Bindings.cpp:100-103`, `781-803`); the only
  built-in "grab" concept (`UObjectHook`'s overlap-attach) is a one-time calibration aid, not a runtime
  interaction system. A hand-written mod for one game is the *only* place where a real point/grab/use
  binding to the game's own interact system can exist; UEVR intentionally leaves this gap for plugins.
- **Arbitration between real and synthetic input is a soft, time-windowed heuristic, not a mode switch**
  (`VR.hpp:379-386`, `VR.cpp:1134-1151`) — a project hand-authoring one game's bindings can instead do a
  hard, deterministic switch (e.g. an explicit menu toggle) since it doesn't need to cover the "unknown
  title, unknown input scheme" case UEVR is solving for.
- **The bindings manifest generalizes over *controllers*, not *games*.** The action set/binding JSON
  (`Bindings.cpp`) and the OpenXR interaction-profile table (`OpenXR.hpp:434-499`) exist purely to
  normalize "which physical VR controller layout" into a fixed vocabulary of ~25 actions — this is the
  part that's genuinely reusable/portable to any engine, and is a good template for a hand-written mod
  that wants to support multiple VR headsets without also trying to support multiple games.
- **Comfort features (vignette, etc.) are absent entirely** — even the generic input layer doesn't
  attempt every "obviously VR" feature; a hand-written mod aiming for comfort options is not duplicating
  anything UEVR already solved.

## Not determined

- Whether/how the XInput-spoofing approach interacts with UE5's Enhanced Input system specifically
  (e.g. titles using Input Mapping Contexts rather than classic axis/action bindings) — not addressed
  anywhere in the read source; VR.cpp only ever talks about XInput and never touches
  `UEnhancedInputComponent`/`UInputMappingContext`.
- Whether OpenVR falls back to the legacy (non-Input-System) `IVRSystem::GetControllerState` API under
  any condition — no such call was found in the sections read, but `OpenVR.cpp` was read for
  input handles/poses specifically, not exhaustively for every function in the file, and the ~3900-line
  `VR.cpp` was not read line-by-line in full.
- Exact behavior/precedence when both a per-game OpenXR binding-override JSON *and* a Lua/plugin
  `on_xinput_get_state` callback are present simultaneously — order of hook chain execution across mods
  vs. scripts beyond what's shown in `XInputHook.cpp:211-225` (mods run in `Mods::get_mods()` order) was
  not traced further into script-vs-native-plugin ordering.
- Whether the `Squeeze`/force-sensor (Knuckles) analog grip value is exposed anywhere beyond being an
  input action (e.g. whether it drives anything analog in the XInput trigger emulation, vs. only the
  boolean `Grip` action used at `VR.cpp:1210-1219`) — not traced further.
