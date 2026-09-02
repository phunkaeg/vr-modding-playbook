# TheDarkModVR — input and interaction architecture

Source read:
- `renderer/vr/OpenXRInput.h` (105 lines), `OpenXRInput.cpp` (568 lines) — full read
- `renderer/vr/OpenXRBackend.h` (142 lines), `OpenXRBackend.cpp` (1310 lines) — cvar block, Init/InitBackend/DestroyBackend, RenderStereoView, UpdateFrameStatus/DrawComfortVignette, UpdateInput read in full; rest skimmed for VR-specific logic
- `renderer/vr/OpenXRSwapchain.h` (43 lines) — full read
- `renderer/vr/OpenXRSwapchainGL.cpp` (152 lines), `OpenXRSwapchainDX.cpp` (204 lines), `D3D11Helper.cpp` (137 lines) — full read
- `renderer/vr/VRFoveatedRendering.cpp` (206 lines) — cvar declarations and radius plumbing only (not central to the question)
- `framework/GamepadInput.h` (75 lines) — full read (shared action-change struct)
- `framework/UsercmdGen.cpp` — read around `Joystick()` (~1050-1180) and `JoystickMove()` (~695-745) for the injection/arbitration point
- `game/Player.cpp` — read `GetFrobPos` (~8495-8502), frob-trace block (~10770-10804), and grepped for `Lean`
- `game/Grabber.cpp` — grepped for `GetFrobPos` call sites (415, 632, 823)
- `assets/XrProfileBindings.default.cfg` (24 lines) — full read
- `assets/guis/mainmenu_vrsettings_controls.gui`, `mainmenu_vrsettings_general.gui` — full read

## 1. Input abstraction

Standard OpenXR actions/action sets, not raw polling and not a synthesized device. Two `XrActionSet`s are created: `"gameplay"` (`ingameActionSet`) and `"menu"` (`menuActionSet`) — `renderer/vr/OpenXRInput.cpp:206-229`. Each has a fixed enum of actions (`OpenXRInput::Action`, `renderer/vr/OpenXRInput.h:35-59`) covering movement axes, look axes, buttons (sprint/crouch/jump/frob/attack/parry/menu/inventory/use/drop) and two `XR_ACTION_TYPE_POSE_INPUT` actions (`XR_MOVE_DIR_HAND`, `XR_AIM`) plus menu-pointer poses per hand.

Bindings are data-driven via a bindings file, not hardcoded interaction-profile paths in C++. Two new console commands, `xr_profile <name> <interaction_profile_path>` and `xr_bind <profile> <action> <binding_path>` (`renderer/vr/OpenXRInput.cpp:88-119`), are registered and then a cfg file is executed: `XrProfileBindings.user.cfg` if present, else `XrProfileBindings.default.cfg` (`renderer/vr/OpenXRInput.cpp:121-122, 235-241`). The shipped default file (`assets/XrProfileBindings.default.cfg`) defines **only one interaction profile: `/interaction_profiles/valve/index_controller`** — no Touch, Vive, or WMR profile is registered by default. `xrSuggestInteractionProfileBindings` is then called per registered profile (`renderer/vr/OpenXRInput.cpp:244-279`).

Dominant-hand remapping is applied to binding *paths* before submission: `ApplyDominantHandToActionPath` rewrites `/user/hand/main/`→left or right and `/user/hand/off/`→the other, and has special-cased A/B↔X/Y swaps for the HP Reverb G2 and Oculus Touch profiles (`renderer/vr/OpenXRInput.cpp:293-311`) — even though only the Index profile is actually shipped, i.e. that remap logic anticipates other profiles a user/mission could add via a custom `XrProfileBindings.user.cfg`.

Controller state lands via `xrSyncActions` + `xrGetActionState{Boolean,Float,Vector2f,Pose}` per-action getters (`GetBool/GetFloat/GetVec2/GetPose`, `renderer/vr/OpenXRInput.cpp:534-568`), called once per frame from `OpenXRInput::UpdateInput` (`renderer/vr/OpenXRInput.cpp:324-419`). Pose actions resolve through per-action `XrSpace`s created in `CreateAction`/`CreateActionSpace` (`renderer/vr/OpenXRInput.cpp:176-204`) and located against a caller-supplied reference space (the seated space, see §2) with `xrLocateSpace`.

## 2. Injection point

`OpenXRInput::UpdateInput` is wrapped one level by `OpenXRBackend::UpdateInput` (`renderer/vr/OpenXRBackend.cpp:749-751`), which is called directly from the engine's existing gamepad-polling routine `idUsercmdGenLocal::Joystick()` in `framework/UsercmdGen.cpp:1093-1145`:

```
idGamepadInput::UpdateAxisState( joystickAxis );
idList<padActionChange_t> stateChanges = idGamepadInput::GetActionStateChange();
...
vrBackend->UpdateInput( joystickAxis, stateChanges, poseInput );   // UsercmdGen.cpp:1118
for ( auto change : stateChanges ) { ... }                        // same loop as gamepad changes
```

So there is no separate "VR input" tick — the VR backend is invoked as if it were an extra gamepad, sharing the same `int axis[6]` array (`AXIS_SIDE/AXIS_FORWARD/AXIS_YAW/AXIS_PITCH`, indices reused from the gamepad axis enum) and the same `idList<padActionChange_t>` (`framework/GamepadInput.h:48-52`) that the real gamepad code just populated. `OpenXRInput::UpdateInput` overwrites `axis[AXIS_SIDE/FORWARD/YAW/PITCH]` from the VR thumbstick/trackpad values (`renderer/vr/OpenXRInput.cpp:343-346`) and appends its own `padActionChange_t` entries (frob, jump, crouch, sprint, attack, parry, use/drop item, menu/inventory open) onto the *same* list the gamepad already wrote into (`renderer/vr/OpenXRInput.cpp:361-416`). Additionally, a `poseInput_t` struct (`movementAxis`, `frobHandPos`, `frobHandAxis`) is filled and copied into the per-tick `usercmd_t` (`cmd.movementAxis/cmd.frobAxis/cmd.frobPos`, `framework/UsercmdGen.cpp:836-838`), so controller pose data rides inside the regular usercmd structure that already carries `forwardmove`/`rightmove`/view angles into game logic.

## 3. Arbitration

There is no independent VR/non-VR arbitration layer — VR piggybacks the gamepad channel and is gated by a single cvar:

- `OpenXRInput::UpdateInput` early-returns immediately if `vr_useMotionControllers` is false (`renderer/vr/OpenXRInput.cpp:325-327`), so with the cvar off (its default — see §7) the VR backend call is a no-op and `Joystick()` behaves exactly as it did pre-VR.
- When enabled, VR values are written *after* the real gamepad values in the same call (`joystickAxis` is memset once at `UsercmdGen.cpp:1094`, filled by `idGamepadInput::UpdateAxisState` at `:1113`, then overwritten by the VR backend at `:1118`) — last writer wins, i.e. a physical gamepad and motion controllers are not summed, VR simply clobbers the axis values when active.
- Button/action state changes from gamepad and VR are concatenated into one `idList<padActionChange_t>` and processed uniformly afterward (`framework/UsercmdGen.cpp:1119-1142`), converting into `cmd.impulse`/button-state increments regardless of source.
- Keyboard and mouse are processed by wholly separate functions (`Keyboard()`, `Mouse()`) earlier in the same tick (`framework/UsercmdGen.cpp:1154-1170` calls `Mouse(); Keyboard(); Joystick();` in sequence) and write into the same `cmd`/`viewangles` state via the classic key-binding system, so keyboard/mouse, gamepad, and VR controller input are three independent producers that all mutate the same per-tick `usercmd_t` in sequence — the engine does not attempt to detect and suppress "stale" input sources.
- Turning is arbitrated by `vr_inputSnapTurnInterval`: if VR is active and the interval is >0, `JoystickMove()` (`framework/UsercmdGen.cpp:718-741`) takes a snap-turn branch instead of continuous yaw; if the interval is 0 or VR is off it falls through to the normal smooth-turn calculation used by gamepads (`:737`) — i.e. the same function serves gamepad-look and VR-look, branching on the cvar.
- Menu/GUI input takes a separate path entirely: `OpenXRInput::UpdateInput` detects an active GUI/console (`sessLocal.guiActive || console->Active() || ...ActiveGui()`) and diverts to `HandleMenuInput`, which synthesizes real mouse-move/mouse-button `sysEvent_t`s via `sys->GenerateMouseMoveEvent`/`GenerateMouseButtonEvent` and `Sys_QueEvent` (`renderer/vr/OpenXRInput.cpp:421-472`) — controller-pointer-to-GUI interaction is arbitrated by injecting synthetic mouse events into the normal event queue rather than a VR-specific UI path.

## 4. Interaction

Frobbing (TDM's core "use/examine" affordance covering doors, levers, lockpicking, item pickup, etc.) and the `Grabber` physical-manipulation system (used for handling ropes, moving bodies, physically operating levers/doors) are **not VR-specific systems** — VR only redirects the ray origin/orientation they already used.

- `idPlayer::GetFrobPos` (`game/Player.cpp:8495-8502`): if `vr_useMotionControllers` is on, origin/axis come from `usercmd.frobPos`/`usercmd.frobAxis` (the `XR_AIM` controller-pose action, bound by default to `/user/hand/main/input/aim/pose`, transformed into `poseInput.frobHandPos/frobHandAxis` in `renderer/vr/OpenXRInput.cpp:357-359`); otherwise it falls back to `GetViewPos` (camera/mouse-aim ray).
- `Grabber.cpp` calls `player->GetFrobPos(viewPoint, viewAxis)` at three call sites (`game/Grabber.cpp:415, 632, 823`) — the grab/manipulate raycast is the same call whether driven by mouse or by the controller aim pose.
- The frob trace itself (`game/Player.cpp:10786-10804`) does `start = eyePos + usercmd.frobPos * actualViewAngles.ToMat3()` and traces to `start + angles.ToForward() * maxFrobDistance` against `CONTENTS_SOLID|OPAQUE|BODY|CORPSE|RENDERMODEL|FROBABLE` — i.e. frob/lockpicking/door-handling are all driven by one controller-anchored raycast, not a physically-simulated hand or grab-collider.
- A separate `XR_ATTACK`/`XR_FROB`/`XR_USE_ITEM`/`XR_DROP_ITEM` action set of boolean buttons drives discrete interaction events (attack, frob-press, use selected item, drop item) alongside the continuous aim ray (`renderer/vr/OpenXRInput.h:44-51`, wired to `UB_FROB/UB_ATTACK/UB_INVENTORY_USE/UB_INVENTORY_DROP` in `renderer/vr/OpenXRInput.cpp:373-416`).
- Aiming assist: a 2D "aim indicator" is drawn at the frob-trace hit point, enlarged and range-extended for ranged weapons (bow) via `vr_aimIndicatorRangedMultiplier`/`vr_aimIndicatorRangedSize` (`game/Player.cpp:10776-10781`, `renderer/vr/OpenXRBackend.cpp:599-611`).
- Leaning: TDM's pre-existing keyboard lean system (`IMPULSE_LEAN_FORWARD/LEFT/RIGHT`, `physicsObj.ToggleLean(...)`, `game/Player.cpp:5751-5785`) has no VR-specific counterpart in `OpenXRInput::Action` — there is no `XR_LEAN` action. Whether/how physical head-lean (moving the HMD sideways) is reflected in the player's collision origin is **not determined** from `renderer/vr/` — `OpenXRBackend::AdjustRenderView` only adjusts the *rendered* stereo view/eye positions (`renderer/vr/OpenXRBackend.cpp:85-134`), and no code was found in the reviewed files that feeds HMD position back into the player's physics/collision origin (room-scale body translation).

## 5. Locomotion (shipped modes, default marked)

- **Smooth (thumbstick/trackpad) translation** — `AXIS_SIDE`/`AXIS_FORWARD` from `XR_SIDE`/`XR_FORWARD` (default binding: Index off-hand thumbstick X/Y) feed directly into `cmd.rightmove`/`cmd.forwardmove` (`framework/UsercmdGen.cpp:739-740`), exactly like a gamepad stick. **No teleport-locomotion code was found** anywhere in the reviewed source (`renderer/vr/`, `UsercmdGen.cpp`, `Player.cpp` frob/grab paths) — teleport is **not determined to exist** in this codebase.
- Movement direction reference frame is selectable: `vr_inputWalkHeadRelative` — "Head" (HMD-orientation-relative) vs **"Hand" (off-hand-controller-orientation-relative), DEFAULT = Hand** (cvar default `"0"`, `renderer/vr/OpenXRInput.cpp:26`; exposed as the "Movement mode" choice in `assets/guis/mainmenu_vrsettings_controls.gui:53-67`, values `"1;0"` = `Head;Hand`).
- Turning: **snap-turn is the default rotation mode** — `vr_inputSnapTurnInterval` default `"45"` degrees (`renderer/vr/OpenXRInput.cpp:27`). Setting it to 0 switches to continuous smooth turning driven by the same yaw-stick code path used for gamepads (`framework/UsercmdGen.cpp:730-738`). Menu exposes discrete steps `0;15;30;45;60;75;90` (`assets/guis/mainmenu_vrsettings_controls.gui:69-83`).
- Motion controllers as a whole are **off by default**: `vr_useMotionControllers` default `"0"`, described in its own cvar comment as "(wip)" (`renderer/vr/OpenXRInput.cpp:24`). With it off, VR locomotion/interaction code paths above are bypassed entirely and the player uses ordinary gamepad/keyboard+mouse locomotion while still seeing stereo HMD rendering.

## 6. Comfort (shipped options, defaults)

- **Comfort vignette** — `vr_comfortVignette`, default `"0"` (off) (`renderer/vr/OpenXRBackend.cpp:52`). When enabled, a circular vignette shader (`comfort_vignette.vert/frag.glsl`) is drawn over each eye (`renderer/vr/OpenXRBackend.cpp:650-661`) whenever `vignetteEnabled` is true. `vignetteEnabled` is driven by `UpdateFrameStatus`, which flags it true on any detected change in `frameData->cameraPosition`/`cameraAngles` and clears it 0.5s after the camera stops changing (`renderer/vr/OpenXRBackend.cpp:613-627`) — i.e. it triggers on any camera movement (not narrowly scoped to snap-turns/teleports specifically; the code comment on the cvar says "on artificial movement" but the trigger condition itself is any position/angle delta).
  - `vr_comfortVignetteRadius` default `"0.6"` (`renderer/vr/OpenXRBackend.cpp:53`).
  - `vr_comfortVignetteCorridor` (fade-band width) default `"0.1"` (`renderer/vr/OpenXRBackend.cpp:54`).
- **Zoom-animation disable** — `vr_disableZoomAnimations`, default `"0"` (animations shown), described as helping motion sickness from the spyglass zoom (`renderer/vr/OpenXRBackend.cpp:55`; GUI toggle at `assets/guis/mainmenu_vrsettings_general.gui:63-77`).
- **Mouse-decoupling for keyboard/mouse-in-VR play** — `vr_decoupleMouseMovement` default `"1"` (vertical mouse motion does not move the VR view) and `vr_decoupledMouseYawAngle` default `"15"` degrees (horizontal mouse motion inside this angle from HMD-forward is decoupled) (`renderer/vr/OpenXRBackend.cpp:35-36`). This is a comfort measure for the non-motion-controller default configuration (mouselook while wearing an HMD).
- Fixed foveated rendering (`vr_useFixedFoveatedRendering`, default `"0"`) is a performance option, not a comfort option, but is exposed in the same VR settings-general menu (`renderer/vr/VRFoveatedRendering.cpp:25`, `assets/guis/mainmenu_vrsettings_general.gui:79-93`).

## 7. Configurable vs hardcoded

**Configurable (cvar/menu/bindings-file driven):**
- Controller-to-action bindings: fully data-driven through `xr_profile`/`xr_bind` console commands and the `XrProfileBindings.default.cfg` / `XrProfileBindings.user.cfg` file pair (user file wins) — `renderer/vr/OpenXRInput.cpp:88-119, 235-241`.
- Dominant hand: `vr_inputLefthanded` cvar (declared this way, `renderer/vr/OpenXRInput.cpp:25`), exposed in the GUI as cvar `"vr_inputLeftHanded"` (`assets/guis/mainmenu_vrsettings_controls.gui:43-51`) — note the differing capitalization between the C++ declaration and the `.gui` reference; both name the same logical setting but this file set does not show whether the cvar lookup is case-normalized.
- All comfort/locomotion/aim settings enumerated in §5/§6 are `CVAR_ARCHIVE` (persisted) and have first-class entries in `mainmenu_vrsettings_controls.gui` and `mainmenu_vrsettings_general.gui`.
- Swapchain backend choice: `xr_preferD3D11` (default `"1"`), archived cvar (`renderer/vr/OpenXRBackend.cpp:33`) — not exposed in the reviewed GUI files, console/cfg only.

**Hardcoded:**
- The set of possible VR actions itself (`OpenXRInput::Action` enum) is fixed in C++ — `xr_bind` can only remap paths to these 18 predefined actions, it cannot create new ones (`renderer/vr/OpenXRInput.cpp:36-56` name table; `OpenXRInput.h:35-59`).
- The shipped default bindings cover exactly one interaction profile (Valve Index) — Touch/Vive/WMR users get no default bindings unless a `XrProfileBindings.user.cfg` supplies them (not found in the reviewed tree).
- The GUI overlay's screen-space geometry constants (position 640×480 cursor space in `HandleMenuInput`, `renderer/vr/OpenXRInput.cpp:439/442`) are hardcoded, not cvars.
- Frob/grab raycast content mask (`CONTENTS_SOLID|OPAQUE|BODY|CORPSE|RENDERMODEL|FROBABLE`, `game/Player.cpp:10796-10797`) is hardcoded.

## 8. Dual GL + D3D11 swapchain support — how and why

**How it's abstracted:** `OpenXRSwapchain` is a pure-virtual interface (`Init/Destroy/PrepareNextImage/ReleaseImage/CurrentFrameBuffer/CurrentImage/CurrentSwapchainSubImage`, `renderer/vr/OpenXRSwapchain.h:20-42`) with two concrete implementations, `OpenXRSwapchainGL` and `OpenXRSwapchainDX`. `OpenXRBackend` holds `OpenXRSwapchain*` pointers (`eyeSwapchains[2]`, `uiSwapchain`, `renderer/vr/OpenXRBackend.h:122-123`) and the rest of the renderer (`RenderStereoView`, `AcquireFboAndTexture`, `SubmitFrame`) only ever calls through this interface — it is agnostic to which backend is active.

- `OpenXRSwapchainGL` (`renderer/vr/OpenXRSwapchainGL.cpp`) creates a normal `XrSwapchain` with `XrSwapchainImageOpenGLKHR` images and wraps each directly in an engine `FrameBuffer`/`idImage` — the renderer draws straight into the OpenXR-owned GL texture, no copy.
- `OpenXRSwapchainDX` (`renderer/vr/OpenXRSwapchainDX.cpp`) creates the D3D11 swapchain (`XrSwapchainImageD3D11KHR`), but the engine renderer is GL-only, so it also creates one *separate* D3D11-independent GL texture (`qglGenTextures`) and registers it against the D3D11 texture via `WGL_NV_DX_interop2` (`qwglDXRegisterObjectNV`/`qwglDXLockObjectsNV`/`qwglDXUnlockObjectsNV`, `renderer/vr/OpenXRSwapchainDX.cpp:58-64, 157-160, 168`). The renderer draws into that GL-interop texture as normal; on `ReleaseImage()`, after unlocking the GL/DX interop, `D3D11Helper::RenderTextureFlipped` performs a D3D11 fullscreen-triangle draw that copies (and vertically flips) from the GL-rendered texture's `ID3D11ShaderResourceView` into the actual OpenXR swapchain's `ID3D11RenderTargetView` (`renderer/vr/D3D11Helper.cpp:72-97`, called from `OpenXRSwapchainDX.cpp:172`) — the flip exists because GL and D3D11 disagree on which way is "up" for render targets.
- `D3D11Helper` (`renderer/vr/D3D11Helper.cpp`) owns the D3D11 device/context (created against the exact `XrGraphicsRequirementsD3D11KHR::adapterLuid` OpenXR reports, `D3D11Helper.cpp:23-53`), the GL/DX interop device handle, and the flip vertex/pixel shaders (compiled HLSL blobs `VS_Flip`/`PS_Flip`, `D3D11Helper.cpp:99-105`) plus sampler/rasterizer state used only for that flip draw.
- Backend selection happens once in `OpenXRBackend::InitBackend` (`renderer/vr/OpenXRBackend.cpp:777-813`): on Windows, if `xr_preferD3D11` is true **and** the runtime advertises `XR_KHR_D3D11_enable`, it builds the D3D11 graphics binding, initializes `D3D11Helper`, and `new`s `OpenXRSwapchainDX` instances; otherwise it builds the native GL graphics binding (`Sys_CreateGraphicsBindingGL`, per-platform: WGL on Windows, GLX on Linux, `renderer/vr/OpenXRBackend.cpp:678-736`) and `new`s `OpenXRSwapchainGL` instances. On non-Windows platforms only the GL path exists (`OpenXRSwapchainDX.cpp` is entirely `#ifdef WIN32`).
- **Observed code quirk (not a comment claim, an actual code read):** in the `else` branch that builds the GL binding, `usingD3D11` is set to `true` (`renderer/vr/OpenXRBackend.cpp:797`) — the same flag that is `true` in the actual D3D11 branch (`:780`). Since `usingD3D11` gates whether `DestroyBackend()` calls `d3d11Helper.Shutdown()` (`renderer/vr/OpenXRBackend.cpp:870-874`), this looks like a copy/paste bug: on Windows with `xr_preferD3D11` forced off (or the extension unavailable) the GL path would still attempt to shut down an un-initialized `D3D11Helper` on session teardown. This is stated as an observation of what the code does, not a claim about whether it was ever hit at runtime (the default `xr_preferD3D11=1` means the D3D11 branch is what almost all Windows players exercise).

**Why a GL engine carries a D3D11 path at all:** stated directly in the cvar description, not inferred — `xr_preferD3D11`'s help text is *"Use D3D11 for OpenXR session to work around a performance issue with SteamVR's OpenXR implementation"* (`renderer/vr/OpenXRBackend.cpp:33`), and it defaults to `"1"` (D3D11 preferred). This is a runtime-specific performance workaround: SteamVR's OpenXR *GL* path was apparently slower/worse than its D3D11 path, so the engine keeps its GL renderer untouched and instead round-trips the final composited eye image through a D3D11 texture (via `WGL_NV_DX_interop2`) purely to hand OpenXR a D3D11 swapchain image. No comment ties this to a specific *runtime GL driver bug* (e.g., missing/broken GL support) — only to a general "performance issue" with SteamVR's OpenXR GL implementation.

## Defaults table

| Setting | cvar/name | Default | Source |
|---|---|---|---|
| Motion controllers enabled | `vr_useMotionControllers` | `0` (off, "wip") | `renderer/vr/OpenXRInput.cpp:24` |
| Dominant hand (left-handed) | `vr_inputLefthanded` | `0` (right-handed) | `renderer/vr/OpenXRInput.cpp:25` |
| Movement direction reference | `vr_inputWalkHeadRelative` | `0` (Hand-relative) | `renderer/vr/OpenXRInput.cpp:26` |
| Snap-turn interval | `vr_inputSnapTurnInterval` | `45` (degrees) | `renderer/vr/OpenXRInput.cpp:27` |
| Comfort vignette enabled | `vr_comfortVignette` | `0` (off) | `renderer/vr/OpenXRBackend.cpp:52` |
| Comfort vignette radius | `vr_comfortVignetteRadius` | `0.6` | `renderer/vr/OpenXRBackend.cpp:53` |
| Comfort vignette corridor | `vr_comfortVignetteCorridor` | `0.1` | `renderer/vr/OpenXRBackend.cpp:54` |
| Disable zoom animations | `vr_disableZoomAnimations` | `0` (animations on) | `renderer/vr/OpenXRBackend.cpp:55` |
| Decouple mouse from VR view | `vr_decoupleMouseMovement` | `1` (on) | `renderer/vr/OpenXRBackend.cpp:35` |
| Decoupled mouse yaw angle | `vr_decoupledMouseYawAngle` | `15` (degrees) | `renderer/vr/OpenXRBackend.cpp:36` |
| Prefer D3D11 swapchain over GL | `xr_preferD3D11` | `1` (D3D11 preferred) | `renderer/vr/OpenXRBackend.cpp:33` |
| Fixed foveated rendering | `vr_useFixedFoveatedRendering` | `0` (off) | `renderer/vr/VRFoveatedRendering.cpp:25` |
| Foveated inner/mid/outer radius | `vr_foveatedInnerRadius`/`MidRadius`/`OuterRadius` | `0.3` / `0.75` / `0.85` | `renderer/vr/VRFoveatedRendering.cpp:26-28` |
| Aim indicator shown | `vr_aimIndicator` | `1` (on) | `renderer/vr/OpenXRBackend.cpp:42` |
| Ranged aim indicator range multiplier | `vr_aimIndicatorRangedMultiplier` | `4` | `renderer/vr/OpenXRBackend.cpp:48` |
| UI overlay height / aspect / distance / vertical offset | `vr_uiOverlayHeight`/`Aspect`/`Distance`/`VerticalOffset` | `2` / `1.5` / `2.5` / `-0.5` | `renderer/vr/OpenXRBackend.cpp:38-41` |
| Hidden-area mesh optimization | `vr_useHiddenAreaMesh` | `1` (on) | `renderer/vr/OpenXRBackend.cpp:37` |

## Transferable lessons

- **Route synthetic VR input through the existing "extra input device" seam instead of building a parallel input pipeline.** TDM's VR controllers are injected as if they were a gamepad — same `axis[6]` array, same `padActionChange_t` list, same per-tick call site (`framework/UsercmdGen.cpp:1093-1145`). This meant no new arbitration code was needed for buttons/impulses; the cost is that VR simply overwrites gamepad axis values (last-writer-wins) rather than merging them, which is fine only because the two are assumed mutually exclusive in practice.
- **Bindings-as-data beats bindings-in-code for multi-headset support**, but only if you actually ship more than one profile. TDM built a genuinely flexible `xr_profile`/`xr_bind` cfg system (`renderer/vr/OpenXRInput.cpp:88-119`) capable of registering any OpenXR interaction profile, yet shipped bindings for exactly one controller (Valve Index, `assets/XrProfileBindings.default.cfg`). The mechanism scales; the content didn't — worth deciding explicitly whether a playbook mod needs to ship multiple profile files at launch, since a flexible mechanism doesn't populate itself.
- **Reuse existing "aim ray" plumbing for VR pointing/interaction rather than building a new hand-collider system.** `GetFrobPos` (`game/Player.cpp:8495-8502`) is a single branch point that redirects the *existing* mouse/frob raycast origin to the controller's `XR_AIM` pose; the `Grabber` class needed zero VR-specific changes because it always went through `GetFrobPos`. This is a cheap way to VR-enable "pointer" interactions in an engine that already has one.
- **Comfort features can be driven by a generic "did the camera move" signal rather than being wired into each individual locomotion function.** The comfort vignette triggers off any `cameraPosition`/`cameraAngles` delta with a 0.5s decay (`renderer/vr/OpenXRBackend.cpp:613-627`), not off "snap-turn fired" or "teleport fired" events specifically — simpler to implement, but coarser (it also fires for ordinary walking, per the code as read).
- **A GL engine can gain access to a friendlier/faster OpenXR runtime path by round-tripping through D3D11 via `WGL_NV_DX_interop2`,** without touching the GL renderer itself — render into a GL-interop texture as usual, then do one small D3D11 flip-blit into the real swapchain image (`renderer/vr/D3D11Helper.cpp:72-97`). This is a viable low-invasiveness pattern for "my renderer is GL but the runtime's GL path is bad" situations, at the cost of one extra device (D3D11) and one extra copy per eye per frame.
- **Gate experimental VR input behind a single master cvar defaulting off**, and let the game still run in stereo/HMD mode using ordinary gamepad/keyboard+mouse input underneath (`vr_useMotionControllers` default `0`, labeled "wip" in its own help string). This shipped-default choice is a real signal: even in a released VR mod, motion-controller *input* was considered less production-ready than HMD *rendering*, and the fallback path (mouse/gamepad + comfort mouse-decoupling cvars) was the one trusted as default.

## Not determined

- Whether physical head movement (leaning, room-scale translation) is fed back into the player's collision/physics origin, as opposed to only the rendered stereo eye positions — no such code path was found in `renderer/vr/OpenXRBackend.cpp` (`AdjustRenderView` only touches `view->vieworg`/`view->viewaxis` for rendering) within the files reviewed for this task.
- Whether the `.default.cfg`/`.user.cfg` pair is expected to be extended by the community/mission authors with additional interaction profiles (e.g. Touch, WMR) in practice, or whether Index was the only headset officially validated — the mechanism supports it (§1, §7) but no second profile file was found in the reviewed tree.
- Whether `vr_inputLefthanded` (C++ declaration) and `vr_inputLeftHanded` (GUI reference) resolve to the same cvar via case-insensitive lookup, or whether this is a latent naming bug — cvar-registration/lookup code was not reviewed.
- The consequence, if any, ever observed at runtime from the `usingD3D11 = true` assignment in the GL-fallback branch of `InitBackend` (`renderer/vr/OpenXRBackend.cpp:797`) — only the code path itself was verified, not its runtime behavior.
- Any lockpicking-specific mechanics beyond the generic frob/grab raycast (e.g., dedicated lockpick minigame input) — not investigated beyond `GetFrobPos`/`Grabber` call sites, which was as far as the assigned scope (`renderer/vr/` plus direct references out) reasonably extended.
