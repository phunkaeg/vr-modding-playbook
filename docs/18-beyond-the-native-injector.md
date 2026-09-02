# Beyond the native injector: managed engines, frameworks, and companion mods

The active first-hand fleet is dominated by one shape: a C++ DLL injected into a native engine, hooking
graphics APIs and reversing struct layouts. That is one mode of flat-to-VR modding. It is not the only
one, and picking the wrong mode for a target costs months. The operational routes are now split into the
[RE-owned workflow](reverse-engineered-route.md), [source-owned workflow](source-owned-route.md), and
[shared VR spine](shared-vr-spine.md); this chapter supplies the wider survey and tradeoffs.

This chapter surveys the other three, drawn from fourteen independent mods:

| Mode | You write | The engine gives you | Examples read here |
|---|---|---|---|
| **Native injector** | C++ DLL, hooks, RE'd offsets | Nothing | The applicable fleet projects, [13](13-teardown-bioshock-vr.md), [16](16-teardown-virtua-cop-2-vr.md), [17](17-teardown-fc2vr-native-stereo.md) |
| **Managed plugin** | C# against the game's own classes | A loader, reflection, real type names | GTFO, SPT-VR, RoR2, BendyVR, My Friendly Neighborhood, White Knuckle |
| **Framework + profile** | Config, and a companion mod in the game's own mod API | Stereo, tracking, input — all of it | Satisfactory (UEVR) |
| **Source port** | Engine modifications in released source | Everything, at the cost of shipping a whole engine | JKXR, CoD4 VR, CSVR |

**Decide this before anything else.** The question is not "how good am I at reverse engineering" — it is
*what did the developer already give away*, and the answer is usually discoverable in an afternoon.

> **This is one of three independent axes.** *Mode* (this chapter) is how you build it; the
> [stereo rung](17-teardown-fc2vr-native-stereo.md) is how the second eye is produced; the
> [completeness tier](08-project-process.md#how-vr-is-it-declare-a-completeness-tier-and-ship-to-it) is how much of the game becomes VR. Knowing one tells you little about
> the others — a source port can ship at T1, and an injector can reach T4.

---

## Mode 2 — Managed engines: the offsets are already named

If the game is Unity, the reverse-engineering problem largely evaporates. **Class names, method names and
field names are all present**, either as real metadata (Mono) or recoverable through a generated
interop layer (IL2CPP). You are not looking for `base+0x3C4`; you are calling `FPSCamera.RotationUpdate()`.

**The stack is standardised**, which is itself the finding — six mods here, six different games, and the
same three components:

```text
BepInEx            loader + plugin host   (note the build: Mono vs Unity.IL2CPP, x64 vs x86)
Harmony / HookGen  runtime method patching
SteamVR / OpenXR   the VR runtime, sometimes as a Unity package the mod ships itself
```

`BepInEx-Unity.IL2CPP-win-x64` and `BepInEx_win_x64_5.x` are *not* interchangeable, and every one of
these READMEs says so in bold because it is the most common install failure. **Identify the scripting
backend first** (a `GameAssembly.dll` beside the executable means IL2CPP; a `Managed/` folder full of
`.dll`s means Mono).

### The stereo seam is a callback, not a hook

The VR runtime package already renders both eyes. What you do is **mutate the game's own camera inside
its per-eye callbacks**:

```csharp
// GTFO VR. The plugin never touches D3D -- SteamVR's Unity integration
// already drives the eyes; the mod adjusts the game's camera per eye.
SteamVR_Render.preRenderBothEyesCallback += PreRenderUpdate;   // once per frame
SteamVR_Render.eyePreRenderCallback      += PrepareFrameForEye; // once per eye
```

That is structurally the same as [17](17-teardown-fc2vr-native-stereo.md)'s native stereo — *the world
renders twice, the camera moves between* — except somebody else already wrote the hard part. The work
that remains is the same work: which state is per-eye, which is per-frame, and what must not run twice.

### The engine's own render pipeline still fights you

Managed does not mean easy. GTFO's renderer is a custom deferred pipeline, and the stock hidden-area
mask does not survive it — so the mod disables it and rebuilds it at two specific pipeline stages:

```csharp
SteamVR_Render.SetRenderHiddenAreaMask(false);           // stock mask is wrong for this pipeline
m_occlusionMaterial = new Material(VRAssets.GetGTFOHiddenAreaMaskShader());
cam.AddCommandBuffer(CameraEvent.BeforeGBuffer,      gOverwrite); // fill depth, keep stencil clear
cam.AddCommandBuffer(CameraEvent.BeforeImageEffects, gOverwrite); // ensure masked area is black
```

Two insertion points, two different jobs, and the comments say why each is needed. **A managed engine
gives you names, not immunity** — the render-pass hazards in [14](14-render-pass-hazard-atlas.md) apply
identically.

Also present in the same file, and worth recognising as a class:

```csharp
Shader.DisableKeyword("FPS_RENDERING_ALLOWED");   // else weapons render only their sights
```

**Shader keywords are a global switch the game already ships.** Before writing a draw-classifier
([14](14-render-pass-hazard-atlas.md)), check whether the engine has a keyword or cvar that already
separates the class you care about.

### What managed modding buys, concretely

- **Named state.** `FocusStateManager.CurrentState == eFocusState.InElevator` is the authoritative
  UI/cutscene signal that [04](04-ui-and-hud.md) tells you to go hunting for in a native target. Here
  it is free.
- **The mod ecosystem is a compatibility surface.** RoR2VRMod ships SteamVR bindings for *other people's
  mods* (extra skill slots, push-to-talk, a buy menu). A managed game usually has a mod manager, and
  users will run twenty mods at once — plan for it rather than declaring it unsupported.
- **Uninstall is deleting one file.** Every one of these READMEs can say "remove the `.dll`". Native
  injectors need the backup-and-restore machinery in [§ Mode 4](#deployment-is-engineering-too).

## Mode 3 — Framework plus companion mod: let UEVR do the VR

For Unreal titles, **UEVR already solves stereo, tracking and input generically**. The interesting
pattern is what you build *next to* it.

Satisfactory's `satisfactory-uevr-enhancements` is not a VR mod — its README says so in bold. It is a
**game-side mod, written in the game's own modding API**, that adds VR-specific UI and interaction on
top of UEVR's stereo. The deliverable is three things:

```text
UEVR injector      (+ a game-specific patch, when the profile alone is not enough)
UEVR profile       per store build -- FactoryGameSteam-Win64-Shipping / FactoryGameEGS-...
companion mod      .uasset content + Lua, shipped through the game's normal mod manager
```

Two consequences worth internalising:

- **The profile is per *store build*, not per game.** Same problem as
  [17](17-teardown-fc2vr-native-stereo.md)'s GOG-vs-Uplay Dunia offsets, solved by shipping two
  profiles. Storefront divergence is a constant across every mode in this chapter.
- **A generic framework gets you to "it works in VR" fast, and stops at "it is good in VR."** Everything
  the companion mod adds — VR-appropriate UI scale, interaction ranges, icons — is the gap between those
  two sentences. If your target is Unreal, the honest plan is *UEVR first, then a companion mod for the
  parts UEVR cannot know about.*

If you find yourself writing a native injector for an Unreal game, be able to say why UEVR is
insufficient. That is a legitimate answer, but it should be an answer, not an oversight.

## What a companion plugin is actually for {#companion-plugin-scope}

The SystemReShock plugin is the clearest Mode 3 case study in the survey, and its shape answers the
question people actually have when choosing between a native mod and a UEVR profile: **what is left to
write once the framework is doing its job?** `[SOURCE]`

The answer is a ratio and a feature list. **UEVR is roughly 40,000 lines; this companion's own code is
about 2,900**, almost all of it in a single `dllmain.cpp`, plus a thin D3D11/D3D12 shim of ~300 lines
and a **generated UObject SDK** for reaching the game's classes by name.

And its entire shipped feature list is game semantics:

> 6DOF · working crosshair (guns, puzzles, vending machines) · emulated crosshair depth · minimalistic
> HUD · minimap and health bars attached to the right hand · hotbar item selector · hacker hardware
> toggler · emulated MFD laser pointer · refined controller mappings · two aiming modes for cyberspace

**Not one of those is stereo, tracking, projection or submission.** The framework owns all of it. So:

> **The framework gives you a VR camera. The companion gives you a VR game.**

Everything the framework cannot know is what remains — what a *vending machine* is, which crosshair
belongs to a puzzle rather than a gun, where a minimap should ride on the body, and what "cyberspace"
needs that the rest of the game does not. That is the honest scope of Mode 3, and it is also why the
companion needs a per-title UObject SDK: reaching game-specific classes by name is the whole job.

### Three operational facts from the same project

- **It is build-specific.** The profile does not work with the GOG or demo versions. A framework profile
  is scoped to a build exactly like an address is.
- **Antivirus is part of shipping.** Their README leads with a warning that Windows Defender removes the
  plugin DLL from the profile folder on import, and instructs users to add an exception *before*
  importing. See [08](08-project-process.md).
- **Profiles have a distribution ecosystem and it fragments.** Version 1.5.0 is available through one
  profile site while another still carries 1.4.0 - so "the latest profile" is not a single thing, and a
  bug report needs the profile version as well as the game build.

The project also records its lineage explicitly, crediting an earlier SystemShock UEVR plugin whose
fixes and ideas it borrows. **Mod lineage is worth stating for the same reason a source oracle is:** it
tells a later reader which findings were inherited rather than independently derived.

## UEVR: impersonate the engine's own stereo device {#uevr-fake-stereo}

The framework that most Unreal VR mods are built on is named after what it does. `FFakeStereoRendering`
is a **real Unreal class** — a stub stereo device that ships inside the engine — and UEVR's central move
is to locate its vtable and take it over: `[SOURCE]`

```
src/mods/vr/FFakeStereoRenderingHook.cpp   8,133 lines   <- the heart of it
src/mods/vr/IXRTrackingSystemHook.cpp      2,000 lines   <- the same trick for tracking
```

The engine then believes a stereo device is present and **drives its own stereo path** — view offsets,
per-eye projection, render targets — rather than having a foreign renderer bolted alongside it.

**This is the fourth independent instance in this survey of the same principle**, and at the largest
possible scale:

| Project | The seam the engine already had |
|---|---|
| **UEVR** | `FFakeStereoRendering` — a built-in stereo device interface waiting to be implemented |
| OpenMW-VR | `UpdateViewCallback` — the engine asks an abstract supplier for two views |
| Vostok-VR | GDExtension — a supported native-extension loader |
| PreyVR | `CreateIKLimb`, a nullable custom-view callback, `r_overrideDXGIAdapter` |

**Enumerate what the engine already honours before designing a hook.** The most widely deployed VR mod
framework in existence is, architecturally, an implementation of an interface the engine shipped with.
See [META-006](pattern-catalog.md#meta-006).

Note also the layered fallbacks: UEVR does not rely on one entry point but attempts the game-engine
tick, the slate render thread, and the `FSceneView` constructor, and creates its hooks
`StartDisabled` before arming them.

That is what UEVR *consumes*. For what it **exposes** to its own plugins - the C ABI, its versioning and
its callback surface - see [the next section](#framework-extension-surface). The two halves are worth
reading together: the same project both implements somebody else's interface and publishes one.

## What a framework must expose so companions can extend it {#framework-extension-surface}

The section above is UEVR's **engine-facing** half - how it persuades Unreal to drive its own stereo
path. This is its **plugin-facing** half: what it exposes so other people can build on it. Reading its
own headers shows that surface is designed rather than incidental. `[SOURCE]`

### A plain-C ABI, with the ergonomics kept separate

| File | Lines | Role |
|---|---|---|
| `include/uevr/API.h` | 648 | **The ABI.** Plain C: function-pointer tables, no C++ types across the boundary |
| `include/uevr/API.hpp` | 1,711 | C++ convenience wrapper over that table |
| `include/uevr/Plugin.hpp` | 170 | Optional base class so a plugin is a subclass and a global |

**The C header is why plugins survive framework updates** — no name mangling, no STL types, no layout
assumptions across a DLL boundary compiled by a different toolchain. The C++ header gives authors the
ergonomics without putting any of it in the contract.

It is versioned properly: `UEVR_PLUGIN_VERSION_MAJOR 2`, `MINOR 39`, `PATCH 0`, with a
`UEVR_PluginVersion*` handed to the plugin so it can refuse a framework it does not understand rather
than crashing inside it. Compare [NET-001](pattern-catalog.md#net-001) — same reasoning at a different
boundary.

A small licensing detail worth copying: **`Plugin.hpp` carries its own MIT licence, separate from the
rest of the codebase.** Plugin authors link the helper without inheriting the framework's terms. If you
want an ecosystem, the header people must compile against should be the most permissively licensed file
you own.

### The callbacks are pre/post pairs at the moments VR changes meaning

Twenty-four callbacks, and their shape is the transferable part - they bracket exactly the places where
VR alters engine semantics:

```text
on_pre_engine_tick                      on_post_engine_tick
on_pre_calculate_stereo_view_offset     on_early_calculate_stereo_view_offset
                                        on_post_calculate_stereo_view_offset
on_pre_viewport_client_draw             on_post_viewport_client_draw
on_pre_slate_draw_window_render_thread  on_post_slate_draw_window_render_thread
on_present   on_device_reset   on_controller_state(s)
on_xinput_get_state   on_xinput_set_state   on_custom_event   on_message
```

**Note the stereo view offset gets three hooks, not two.** One calculation, three distinct moments a
companion might need — before the framework computes the offset, early within it, and after. When a
single engine call is where the whole conversion happens, "before and after" is not enough resolution.

**`on_xinput_get_state` and `on_xinput_set_state` are in the list**, which is what lets a companion
rewrite pad input without touching the engine — the same seam the BioShock and Far Cry mods reach for,
here offered rather than hooked.

### It hands plugins the engine's own reflection

The API exposes `find_uobject`, `find_object`, `find_property`, `find_function`, `call_function`,
`get_class_default_object`, `get_console_manager` and `execute_command`. A companion mod therefore
**queries Unreal's metadata instead of reverse-engineering it** — which is the whole reason a
game-specific UEVR plugin is an afternoon rather than a project, and the same advantage
[Mode 2](#mode-2-managed-engines-the-offsets-are-already-named) gets from managed engines.

Aim is first class too (`get_aim_method`, `get_aim_pose`, `get_aim_transform`) rather than something each
plugin re-derives — the framework owning
[the grip/aim distinction](02-viewmodels-and-hands.md) once, for everyone.

**The design lesson generalises past Unreal:** if you are building anything others will extend, the
extension surface is *the set of pre/post pairs around moments where your layer changes the meaning of
what the host is doing*, plus whatever introspection stops extenders duplicating your reverse
engineering. See [META-008](pattern-catalog.md#meta-008).

## What a source-port VR layer actually costs, measured {#source-port-vr-layer}

Mode 4 below warns that a source port has *"the highest cost: you now ship and support an entire
engine."* That is true of the **maintenance** burden and misleading about the **integration** one. Two
independent Quake 2 VR ports were measured, and the VR layer is far smaller than the framing suggests.
`[SOURCE]`

**Team Beef's Quake2Quest** - active, OpenXR, 6DoF - keeps its VR code in **one directory** the engine
fork does not otherwise touch, and the entire VR-to-engine interface is **about thirteen globals**:

```c
extern vec3_t hmdPosition, hmdorientation, positionDeltaThisFrame;
extern vec3_t weaponangles,     weaponoffset;
extern vec3_t flashlightangles, flashlightoffset;
extern float  playerHeight, playerYaw;
extern int    ducked;          // DUCK_NOTDUCKED / DUCK_BUTTON / DUCK_CROUCHED
extern bool   player_moving, showingScreenLayer;
```

Counted across the engine tree: **23 files touched in total**, and the busiest values are read in very
few places - `hmdPosition` 11 references, `weaponangles` 11, `weaponoffset` 9.

> **`hmdorientation` is read in exactly one file, once.**

That number is the useful one. **Head orientation - the thing a VR port is fundamentally for - is a
single integration site** on an engine whose camera arrives as a parameter. The cost of a source port is
in shipping and supporting the engine, not in wiring VR into it.

### Four design decisions visible in that interface

- **Every tracked thing gets its own pose pair.** `weapon*`, `flashlight*` and the HMD are separate -
  there is no single "controller" concept that attachments hang off. Adding a tracked object is adding
  two vectors, not extending a class.
- **The roomscale delta is its own variable.** `positionDeltaThisFrame` sits beside absolute position, so
  the consumer decides which it wants - the
  [consumed-versus-residual split](01-camera-and-tracking.md#roomscale-handoff) in one field.
- **Crouch is tri-state, not boolean.** `DUCK_NOTDUCKED / DUCK_BUTTON / DUCK_CROUCHED` keeps *physically
  ducking* and *pressing crouch* distinguishable, because they need different handling on the way out
  even though the game has one crouch.
- **Per-weapon calibration is data, keyed by the engine's own index.** A cvar per weapon model -
  `vr_weapon_adjustment_%i`, six values for offset and rotation, with a sane default - so alignment is
  tuned without a rebuild, and the key is a number the engine already assigns.

## Mode 4 — Source ports: when the developer released the engine

Where the engine source shipped (id Tech, GoldSrc/Xash, IW/CoD4's community rebuild), the mod is a fork
of the engine with VR compiled in. JKXR (Jedi Outcast/Academy, ~780k lines of C++), CoD4 VR (~634k), and
the Xash3D-based Counter-Strike client are all this shape.

This has the highest ceiling — native stereo is trivial when you own the render loop — and the highest
cost: you now ship and support an entire engine. Note what CoD4 VR's docs spend their words on. Almost
none of it is rendering.

### Deployment is engineering too

The playbook has been light here, and CoD4 VR is the corrective. Its `KNOWN-ISSUES.md` is mostly
*install-time* engineering, and every item generalises:

- **A 64-bit OpenXR registration does not prove the 32-bit loader can start.** *"KisakCOD and COD4 are
  32-bit processes… Beta.14 reports both registry views independently and blocks an OpenXR-only launch
  when the 32-bit manifest is absent or missing on disk."* **Two independent projects hit this** — FEAR
  VR's whole two-process architecture (AD-001) exists because the `HKLM\SOFTWARE\WOW6432Node\Khronos\
  OpenXR\1` entry was missing on the dev machine. If your target is 32-bit, check for a 32-bit runtime
  manifest *before* designing anything.
- **Config detection is not proof of function.** *"Registry/file detection is an offline preflight, not a
  synthetic VR session. The first scan correctly warns that headset/controller proof is missing."* The
  user must wake the headset and run diagnostics to import a **live receipt**. This is
  [06](06-debugging-methodology.md)'s "presence is not proof of loading" applied to the installer.
- **Refuse rather than guess.** Their setup recognises the classic layout, and *"rejects [the
  Microsoft/Xbox] layout before writing and never guesses, downloads, or moves original assets…
  automatic normalization is intentionally disabled until a verified before/after map is available."*
- **Back up, hash, and restore.** *"backs up and SHA-256-verifies every pre-existing managed file,
  restores those originals on uninstall."* Same discipline as FC2VR never touching `Dunia.dll` on disk.
- **Be honest about what a heuristic proves.** *"GPU memory provides only a conservative
  Native/Performance starting point. It is not a performance benchmark."*
- **A whole level can be unshippable.** *"Death From Above is not playable in VR and must be skipped"* —
  the AC-130 mission, whose entire premise is a top-down sensor view. **Content-level incompatibility is
  a real category**, and documenting the skip is a better outcome than an unbounded fix attempt.

---

## Let the engine load your code: patch the command line, not the engine {#engine-sanctioned-loading}

Vostok-VR-Mod is the first Godot target in this survey, and its delivery is worth copying wherever an
engine has a documented native-extension mechanism. `[SOURCE]`

Godot loads native code through **GDExtension**, a supported, versioned interface. So rather than hook
the renderer, the mod ships `rtv_vr_mod.gdextension` as a resource and only needs to make the engine
*look* for it. Its bootstrap DLL hooks **`GetCommandLineW`** and returns a modified command line before
Godot starts, with the initialisation guarded by `std::call_once` against any future worker-thread
caller.

**The injection exists only to get the extension registered.** After that, the VR code runs as
engine-sanctioned native code with a documented API and lifecycle, not as a foreign hook fighting the
renderer for ownership.

Generalise the question: **does the target already have a supported way to load native code?**
GDExtension, a plugin folder, a `-mod` argument, a scripting host with an FFI, an addon manifest. If it
does, the smallest possible injection is the one that makes the engine's own loader find you - and
everything downstream inherits the engine's stability guarantees instead of your hook's.

Its taxonomy is genuinely awkward, and worth flagging rather than smoothing over: the delivery is
recorded as `native-injector` because an injector is present, but the payload is closer to a supported
plugin than to an injected hook. A future `vehicle` value may be needed for engine-sanctioned native
extensions.

### These routes are not interchangeable, and a project constraint can rule one out

DishonoredVR asked this section's question of UE3 and recorded the answer as a **closed negative**: there
is no GDExtension equivalent, and the 259 registered exec natives on the game's cheat manager are a
*script* surface, not a native-load surface — they cannot load a DLL. `[STATIC]` Worth having written
down so nobody reopens it.

But their more useful point is about the taxonomy itself. **This chapter presents engine-sanctioned
loading and proxy-DLL loading as neighbouring answers to one problem. For some projects they are not**,
because a proxy DLL modifies the game installation:

> This project's working rules forbid modifying the game installation, which is also why we declined
> FC2VR's `d3d9.dll` proxy. Same rule, different filename.

So a no-installation-modification constraint eliminates the entire proxy family — `xinput1_3.dll`,
`dxgi.dll`, `d3d9.dll` alike — and leaves manual injection, regardless of how convenient the proxy would
be. Compare [PACK-002](pattern-catalog.md#pack-002), which adopts the same constraint from the packaging
end and rules out the same vector.

**Establish that constraint before choosing a vehicle**, not after. It is a project policy rather than a
technical finding, and it silently invalidates otherwise-sound advice from any sibling project that does
not share it.

## When the engine already has XR, the mod is activation, not implementation {#engine-native-xr}

Vostok-VR-Mod's payload turns out to be far smaller than its delivery mechanism, and the reason is worth
generalising. Godot ships a first-class `XRInterface` with an OpenXR implementation behind it, so the
mod's XR layer is **196 lines** that activate and configure what is already there: `[SOURCE]`

```cpp
class XRInitializer : public godot::RefCounted {
    enum Result { RESULT_SUCCESS, RESULT_NO_INTERFACE,
                  RESULT_INIT_FAILED, RESULT_ALREADY_ACTIVE };
    Result activate_openxr();
    void   apply_settings(const godot::Dictionary& p_config);  // render_scale, refresh_rate, foveation
};
```

Compare the range this survey now covers for the same conceptual job:

| Target | What the mod supplies | Rough size |
|---|---|---|
| Godot (Vostok) | Activation + configuration of the engine's own XR interface | ~200 lines |
| Halo MCC (ForerunnerVR) | A whole runtime backend behind its own `IVR` seam | ~570 lines per backend |
| BioShock (trilogy VR) | A whole runtime backend **and** a substitute OpenXR runtime | ~5,300 lines for the substitute alone |

**Survey what the engine already provides before scoping the XR work at all.** A first-class XR
interface, a plugin loader, an existing stereo mode or a scriptable render pipeline each remove a layer
you would otherwise write — and the difference between the top and bottom rows here is more than an
order of magnitude for the same user-visible outcome.

Note also that `activate_openxr` returns a **four-value result** rather than a bool, separating "no
interface" from "init failed" from "already active." Three different operator actions, three different
return values.

### A VR layer bound to one backend quietly unsupports the others

Shipwright-VR's README opens by telling users the renderer **must** be D3D11 and that OpenGL will not
work. The reason is in the code: the VR layer is compiled `XR_USE_GRAPHICS_API_D3D11` and pulls its
device and context from the D3D11 backend through extern accessors, in a renderer (libultraship) that
supports several backends. `[SOURCE]`

That is a legitimate scope decision, not a defect. But **in a multi-backend renderer, binding the VR
layer to one backend silently makes every other backend unsupported**, and the user-facing symptom is
"VR does not work" with no explanation — which is why their README leads with it. If you take this
route, say so where the user will read it before they file the bug.

## When a family of ports shares a renderer, they share a VR seam {#family-seam}

Two source ports in this survey converged on the *same integration point* without coordinating, and the
reason generalises well beyond them.

**perfect_dark_VR** (a VR-only fork of the Perfect Dark decompilation) and **Shipwright-VR** (a fork of
Ship of Harkinian, the Ocarina of Time PC port) both implement stereo inside **Fast3D** — the shared
N64-microcode renderer that the whole family of N64 decomp ports is built on. Perfect Dark's projection
work lands in `port/fast3d/gfx_pc.cpp`, `gfx_rendering_api.h` and `gfx_opengl.cpp`; Shipwright's VR
layer lives in `libultraship/src/graphic/Fast3D/`. `[SOURCE]`

**The transferable point: when several ports descend from one renderer, the VR seam is a property of the
family, not of the game.** Before starting a source-owned port in a family like this, look for a sibling
that already cut the seam — you may be porting an integration rather than inventing one. Ask the same
question of any decompilation lineage, console-emulator-derived port, or engine with many forks.

The corollary is a warning that this playbook keeps re-learning: shared *lineage* still is not shared
*truth*. See [CAM-004](pattern-catalog.md#cam-004), where two titles in one engine tree expressed the
same FOV option under opposite conventions.

### A narrow VR boundary, written out

Shipwright's seam is worth reading as the concrete form of what
[SRC-04](source-owned-route.md#src-04) asks for: one `extern "C"` header, roughly forty functions, with
the game on one side and the VR layer on the other, and each function's comment naming which side owns
what. Four of its decisions are reusable:

- **The game pushes the anchor, the VR layer composes the view.** The game sets the player's head
  position in world space each frame; the VR layer produces `anchor + HMD offset/orientation`. Body
  ownership stays with the game, head ownership with VR.
- **A separate culling FOV is exported back into the engine.** `VR_GetCullingFovy` returns a vertical FOV
  wide enough to cover the binocular view, and the game feeds it into its own `View` so that **frustum
  culling, audio panning and projected-position/LOD** match what the player sees — while *rendering is
  unaffected*. This is [CAM-002](pattern-catalog.md#cam-002) with a detail worth adding: the cull frustum
  does not only decide visibility, it feeds every CPU-side system that asks "where is this on screen."
- **2D contexts get a world-locked panel with the last world frame frozen behind them**, still head
  tracked. See [HUD-003](pattern-catalog.md#hud-003).
- **Roomscale movement is a negotiation with the game's collision**, not a camera translation. See
  [CAM-005](pattern-catalog.md#cam-005).

The header also labels its own functions by delivery phase. An interface that records which increment
introduced each call is a maintenance artifact as much as a technical one.

## Factor the fork so the general half can go upstream {#upstream-factoring}

OpenMW-VR is the deepest source-owned VR conversion in this survey - a mature RPG engine with a full
OpenXR implementation - and its most useful lesson is structural rather than technical. `[STATIC]`

**Measured against the upstream merge-base, the VR branch changes 370 files: 154 added, 216 modified.**
New VR code concentrates in `components/vr` (31 files), `components/xr` (26) and `apps/openmw/mwvr` - but
**146 of the changed files sit in `apps/openmw`**, with more in `components/sceneutil`,
`components/myguiplatform` and `components/bsa`. So a source-owned conversion of a mature engine is
roughly **40 percent new code and 60 percent modification of existing engine files.** Take that as the
realistic shape of [SRC-04](source-owned-route.md#src-04)'s "narrow integration boundary": the VR modules
*are* containable, the engine touch surface is several times larger.

### The four layers, and which one escaped the fork

| Layer | Contents | Where it lives |
|---|---|---|
| `components/stereo` | `stereomanager`, `multiview`, `frustum`, stereo `types` | **Upstream OpenMW master** |
| `components/xr` | `instance`, `session`, `platform`, `extensions`, `interactionprofiles`, `typeconversion` | VR fork only |
| `components/vr` | tracking manager/source/transform, `layer`, `swapchain`, `viewer`, `frame` | VR fork only |
| `apps/openmw/mwvr` | animation, GUI, pointer, radial menu, virtual keyboard, realistic combat, input manager | VR fork only |

**`components/stereo` is in upstream master; `components/vr` and `components/xr` are not** - and the VR
fork's own maintainer is the majority author of the upstreamed layer, alongside upstream maintainers.

That is the concrete answer to [SRC-06](source-owned-route.md#src-06)'s fork-maintenance problem:
**stereo was factored as a VR-independent engine concept and upstreamed, so the permanently-diverging
fork shrank to what is genuinely VR-specific.** `components/vr/vr.hpp` includes
`components/stereo/types.hpp` and speaks in `Stereo::Pose` - stereo is the shared vocabulary, owned by
the engine, and VR is a *consumer* of it rather than its owner.

**Ask of every change you make to a source-owned port: is this VR, or is it something the engine was
missing that VR merely revealed?** Multiview, frustum handling, a stereo manager and off-axis projection
are all independently useful to a flat renderer. Anything in that category is a rebase you never have to
do again. See [SRC-002](pattern-catalog.md#src-002).

### The inversion that makes the split possible

Reading `components/stereo/stereomanager.hpp` shows *why* the general half could be upstreamed, and it is
one interface: `[SOURCE]`

```cpp
struct UpdateViewCallback
{
    //! Called during the update traversal of every frame to update stereo views.
    virtual void updateView(View& left, View& right) = 0;
};
```

**The engine owns stereo and asks for two views; the VR layer is merely one supplier of them.** The
stereo manager handles multiview framebuffers, the frustum manager, shader defines and near/far planes
without ever knowing an HMD exists - so it is genuinely useful to a flat renderer, which is precisely
what makes it acceptable upstream. Multiview itself is negotiated (`GL_OVR_Multiview` *if supported*),
the same fail-closed discipline as [PERF-004](pattern-catalog.md#perf-004).

**If you want [SRC-002](pattern-catalog.md#src-002) to work, this inversion is the mechanism.** A stereo
layer that *calls into* VR cannot be upstreamed; one that *is called* to fill two views can. Get the
direction of the dependency right and the fork boundary follows for free.

The header also ships a second implementation of that callback, and it is the reason to read the file:

```cpp
//! An UpdateViewCallback that supplies a fixed, custom view. Useful for debugging purposes,
//! such as emulating a given HMD's view.
struct CustomViewCallback : public UpdateViewCallback
```

That is a **headset substitute costing one class**, available because the interface already existed.

### Two details worth stealing

`VR::TrackingPose` carries **prediction status, pose and the display time it was predicted for** as one
struct - validity and staleness travelling with the value rather than alongside it, which is what
[PORT-06](shared-vr-spine.md#port-06)'s pose packet asks for.

And the game layer is unusually complete for a VR port: a **virtual keyboard**, a radial menu, a list-box
adaptation, a meta menu and motion-driven "realistic combat". Text entry in particular is a
[completeness-tier](08-project-process.md) item most conversions skip and then discover they needed.

## Mode 5 — Engine recreation: rebuild the engine, keep the data

There is one more mode, and it sits past the end of the table: **reimplement the engine from scratch and
read the original game's data files.**

`shock2quest` is a Dark-engine recreation in **Rust** (475 source files) targeting Quest, which loads
`sshock2.kpf` and the `mods/` folder from a retail System Shock 2 install. No engine source was ever
released; the author rebuilt the runtime and kept compatibility at the **asset-format** boundary rather
than the code boundary.

| | Source port ([Mode 4](#mode-4-source-ports-when-the-developer-released-the-engine)) | Engine recreation |
|---|---|---|
| Requires released engine source | **Yes** | No |
| Compatibility boundary | Code | **Data formats** |
| VR design freedom | Bounded by the original architecture | **Total** |
| Cost | Ship an engine you did not write | Ship an engine you *did* write |

**The payoff is design freedom that no other mode can offer.** Because nothing is inherited, the VR
affordances can be native rather than retrofitted — that project ships a floating inventory built for
VR, dual wielding, and hand-authored hitboxes, none of which are "the flat game plus stereo."

**The cost is everything else**, and the author is candid about it: *"currently in a pre-alpha state and
not really playable in any meaningful way."* Recreation trades a working game with wrong ergonomics for
correct ergonomics around a game that does not work yet. That is the right trade only when the target is
small, beloved and well-documented — which is exactly the profile of the titles people attempt it on.

**And there is a second, cheaper reason to care about one.** An active recreation is a
[rung-3 oracle](11-re-anchoring-and-discovery.md) for the *data* side of your target: file formats,
object systems, mission structure, resource naming. Where a released engine source tells you what the
code did in 1999, a maintained recreation tells you what the formats mean to someone who has parsed them
recently — and it is usually far more readable. Anyone working a Dark-engine target should read
`shock2quest` for that alone, whether or not they ever run it.

## Modern AAA native engines: two mods worth knowing

The native mode is not confined to 2000s titles. Two of the mods read here target current engines, and
both are informative about what changes at that scale.

### AnvilNext 2.0 (Assassin's Creed) — and a documented sibling port

`anvilengine2vr` supports Odyssey, Valhalla and Mirage from one codebase, DXGI-hooked, built on
REFramework. The interesting artifact is its **Origins porting guide**, which is the clearest statement
in this collection of how to move a mod within an engine family:

> Both games use the AnvilNext 2.0 engine, meaning: many byte signatures may match directly; SDK
> structures (Camera, CameraNode) are likely identical or very similar; hook points should be the same
> functions; **memory offsets within structures may differ slightly.**

That last clause is the trap. *Functions* port; *field offsets* drift. Verify every struct member even
when the signature matched first try.

**Three anchor techniques from that guide are new to this playbook:**

1. **SIMD density is a signal.** *"Camera/matrix functions use `__m128`, `_mm_*` intrinsics heavily."*
   On a modern 64-bit engine, searching for dense SSE/AVX blocks is a cheap way to narrow to matrix code
   before you have any string anchor. Add it to [11](11-re-anchoring-and-discovery.md)'s ladder as a
   *shape* heuristic rather than a byte one.
2. **Ship the decompiled pseudocode as the porting artifact.** The guide includes full IDA output for
   `CalculatePerspectiveProjectionMatrix`, `UpdateCameraMatricesAndFrustum` and `CameraNode::GetForward`,
   explicitly so a human can *visually* match a similar function in the sibling binary — *"the variable
   names and addresses will differ, but the structure and SIMD operations should be recognizable."*
   Given that automated cross-binary matching measured **46% rank-1** on the easiest possible case
   ([11](11-re-anchoring-and-discovery.md)), a readable pseudocode listing may be the higher-yield
   artifact. It is certainly the more durable one.
3. **Look for an override the engine already has.** In `UpdateCameraMatricesAndFrustum`:

   ```c
   v24 = *(Matrix4x4 **)(pCamera + 576);   // worldMatrixOverride
   if ( v24 )
     *pOutViewMatrix = *v24;               // <- the engine will take a view matrix from you
   ```

   **The engine ships a camera override pointer.** Set it and the engine's own code adopts your view
   matrix, before frustum construction. That is rung 1 of the anchor ladder in a form the ladder does not
   currently name: not a reflection system, but *an existing input the engine already honours*. Before
   hooking a matrix write, look for a nullable override pointer next to the camera — debug cameras,
   cinematics and photo modes all need one, so it is often there.

Their honest limitations are also instructive: *"dialogs are rendered in stereo but displayed in
letterbox"*, and *"water and some visual effects are not visible when looking in the opposite direction
to the character"* — screen-space effects tied to the original view, exactly
[14](14-render-pass-hazard-atlas.md)'s hazard classes at AAA scale.

### The Witcher 3 (REDengine, DX12) — where modern rendering bites

`witcher3-vr` is the most technically ambitious mod in this collection, and it is mostly a study in
**upscalers, temporal passes and headset optics**. Its findings have their own sections in
[09](09-d3d11-openxr-injection.md) and [14](14-render-pass-hazard-atlas.md); the architectural points
belong here:

**Hook sets are mode-scoped, and selected before launch.** From its README:

> This mod uses a launcher, mainly because every mode has its own hooks, and some of them must be on at
> startup. **Keeping all hooks enabled degrades performance**, so the launcher enables only the hooks
> required for the selected mode.

Six rendering modes (no-AA, FXAA, TAAU, DLSS, DLAA, plus AER+frame-generation variants), each a distinct
hook set. This is the opposite of the usual "install one DLL that does everything" model, and it is a
reasonable answer once hooks have measurable cost.

**A script-side mod can be a state exporter for the native mod.** Witcher 3 VR ships
`modWitcher3VRStateBridge`, a REDengine `.ws` script mod that *"supplies the instantaneous locomotion and
combat state used by the experimental First-Person view."* The native DLL cannot cheaply know whether
Geralt is in combat; the script layer knows trivially. **If the game has a scripting layer, it is a
legitimate IPC channel to your native mod**, and often a far better one than reversing the state you
need. Their scripts also fail closed: *"every older or missing DLL fails closed."*

**Minimal intervention inside the engine's own system.** The aiming bridge is explicit about it:

> REDengine keeps its native aiming state, crosshair, weapon animation and projectile code. During the
> real PlayerAiming state, this wrapper replaces **only** the free-camera look-at point with the latest
> complete cyclopean headset ray. Actor-target look-at remains untouched.

One value replaced, everything else stock. Same principle as [03](03-input-and-locomotion.md)'s
"puppeteer the engine's native movement, don't reimplement it", applied to aiming.

---

---

## Patterns that cut across all four modes

### Third-person games: default to first person, keep third as a supported mode

Several of these targets are third-person games, which the rest of this playbook barely addresses. The
pattern that emerges is consistent: **switch to first person by default, and keep third person as a
working, supported option** rather than an abandoned fallback.

RoR2VRMod defaults to first person and keeps third person configurable, with an honest limitation —
*"it still plays well but currently doesn't support motion controls."* Witcher 3 VR arrives from the
other direction: third person is the default, with an experimental first-person mode on `F11` plus
automatic handoffs *back* to third person during combat and aiming.

The honesty in RoR2's FAQ is worth copying verbatim as a documentation standard:

> Risk of Rain 2 was not intended to be played in VR. This means that getting motion sick is more
> likely, **especially with high mobility characters such as Loader or Mercenary.**

Naming *which* content is uncomfortable is far more useful than a general comfort warning, and it is the
same instinct as CoD4 VR naming the one unplayable mission.

### Scope support by game mode, not only by level

[Mode 4](#mode-4-source-ports-when-the-developer-released-the-engine) records CoD4 VR naming one
unplayable mission. The generalisation is broader: **a game's modes can differ enough that they are
effectively separate porting targets.**

(*World War VR ships with Zombies as "working / primary", local multiplayer and Campaign as
"experimental" — with campaign progression noted as failing around the second mission — and online
multiplayer as explicitly unsupported and not to be used on public servers.*)

That is four support tiers inside one game, and it is honest rather than evasive: a wave-defence mode in
fixed arenas, a scripted campaign with cinematic camera takeovers, and a networked competitive mode
impose completely different demands on a VR layer. Shipping the strongest one and labelling the rest
beats holding everything back until the weakest is fixed.

**The online-multiplayer exclusion is worth copying for a second reason**: a modified client on a public
server is an anti-cheat and fair-play problem regardless of intent. Presentation-only mods stay
compatible with *vanilla peers* (above), which is not the same as being appropriate on *public
servers*. Say which you mean.

### Presentation-only mods stay multiplayer-compatible

A constraint worth designing for from the start: **if your mod only changes what the local client
presents and how it feeds input, it does not need the other players to have it.**

RoR2VRMod: *"The mod is only required for VR players. You can play with vanilla players just fine too!"*
FEAR VR reached the same place for a different reason — item pickup by activation was already wired
client-to-server, so pointing the detector at the hand *"needs no server change."*

The rule that keeps this true: **drive the engine's existing systems with different inputs; never invent
a new mechanic that the server does not know about.** It is the same argument as the physics-input
philosophy below, with multiplayer as the payoff instead of buffs.

### Publish an extension API so other people's content gets VR support

RoR2VRMod ships **VRAPI**, a separate package that lets *other mod authors* add full VR support to their
custom characters — with a documented list of characters that have adopted it, and a graceful default
(aim with the dominant hand, generic pointer model) for those that have not.

On a game with an active modding scene this is the difference between supporting five characters and
supporting fifty. **The graceful default matters more than the API**: unadopted content must remain
playable, not broken.

### A game update can end a mod, and migration may beat repair

Worth planning for. BendyVR's README currently opens with:

> As of now the latest version on Steam doesn't appear to start at all with this mod. I'm investigating
> but looks to be a little more serious than just fixing a single function. I will continue and either
> patch this up or **make the move over to UUVR.**

That last clause is the strategic point: when a bespoke mod's maintenance cost rises far enough, porting
onto a generic framework can be the better answer than repairing the bespoke one. The same mod is also
hard-locked to game version 1.2.2 — version-locking is honest, but it is a debt that comes due on every
patch.

Version robustness ([11](11-re-anchoring-and-discovery.md)) is what buys you out of this, and the
decision to invest in it should be made early, not after the first break.

## The design philosophy that keeps showing up

White Knuckle VR states it best, and it is the cleanest articulation of a rule this playbook has been
circling for sixteen chapters:

> All VR interactions work as inputs into the existing physics system, meaning that the player moves in
> exactly the same way as in vanilla. The only difference is that you are using your hands to climb and
> jump. **This also means that buffs and debuffs should all work right out of the box.**

That last sentence is the payoff, and it is the argument. A reimplemented climbing system needs every
speed buff, every stamina debuff, every status effect re-implemented alongside it — and each one is a
future bug. Feeding hand motion into the *existing* physics system inherits all of it for free.

Their gesture mapping is worth recording too, because it is not the obvious one: while gripping a
handhold, **the hand is the joystick and the body moves opposite the arm** — pull your hand down to climb
up, move your hand left to go right. That is the physically correct mapping (you are pulling yourself,
not steering), and it is the one that stops feeling like a control scheme.

## Emulating XInput: two traps that both fail quietly {#xinput-emulation-traps}

[Proxying the DLL nobody else wants](#uncontended-proxy) usually means XInput, and synthesising an
`XINPUT_STATE` is the cheapest route to full playability in this whole survey. Two details decide
whether it works, and neither announces itself. `[SOURCE]`

**The executable may import XInput by ordinal.** Singularity's does:

> There is **no `XInputGetState` string in its import table**, so an **IAT patch keyed on the name would
> have found nothing to patch and reported success.**

That is the worst kind of failure - a patch that installs cleanly, logs success, and is not in the call
path. **Detour the function body inside `XINPUT1_3.dll` instead**, which catches the caller however it
resolved the address; `GetProcAddress` by name is still the right way to *find* the function, just not
to intercept it. Any name-keyed IAT approach needs a **positive** proof that the name was actually
present in the table, not merely that the patch returned success.

**`dwPacketNumber` must advance only on change.** Games use it to skip re-reading unchanged input:

| Behaviour | Consequence |
|---|---|
| increments **every call** | defeats the game's skip-unchanged optimisation |
| **never** increments | the game can ignore your state entirely |

> **Both fail quietly.**

**And the cost is nothing**, which is worth knowing before you weigh the approach: while emulating, the
real `XInputGetState` is never called, and **polling an absent device is the expensive case the game was
already paying every frame.** Measured after: 120.0 fps, mod work 1.08 ms, XR submit 1.31 ms, no
regression.

## On a UE1/UE2 target, assume the stock cheat-manager surface is present {#stock-cheat-commands}

A small, cheap thing to check before building any test tooling. XIII (2003) ships a native developer
console on **F2**, and its command list is not XIII-specific - it is the **stock Unreal
`GameInfo`/cheat-manager set, unchanged since UE1**: `[SOURCE]`

| Command | What it gives a VR mod |
|---|---|
| `Fly` | free flight, gravity off, **collision still respected** |
| `Ghost` | free flight with collision disabled - pass through geometry |
| `Walk` | cancels either, back to normal movement |
| **`PlayersOnly`** | **freezes NPCs and vehicles while the player still moves** |
| `God`, `HealMe <n>`, `MaxAmmo`, `KillPawns` | keep a test session alive without playing well |

**`Fly`/`Ghost` are a detached camera and `PlayersOnly` is a frozen world - the two levers every stereo
comparison wants** - available with no hooks, no injection and no reverse engineering. That makes this
the cheapest rung of the [control-plane ladder](06-debugging-methodology.md#http-control-plane) by a
wide margin, and it is available on the day you start.

**The transferable part is that the surface is the engine's, not the game's.** If your target is UE1 or
UE2, expect these to exist even when no wiki lists them and no menu mentions the console - and expect
other standard cheat-manager commands beyond the documented list. The same reasoning applies wherever an
engine family ships a debug surface: search for the *engine's* command set, not the game's.

## Proxy the DLL nobody else wants {#uncontended-proxy}

`dxgi.dll` and `d3d9.dll` are the obvious proxy names and the worst ones. ReShade, DXVK, Special K and
most injectors install under exactly those filenames, **only one file can own a name**, and the result
is that your mod and the user's existing tools are mutually exclusive - a known-issues entry in more
than one mod here.

Singularity's answer is to look at what else the game imports. It loads `XINPUT1_3.dll`, so the proxy
goes there instead: uncontended, and every graphics tool keeps working alongside. `[SOURCE]` The same
vehicle carries BioShock-Trilogy-VR across two engine generations, and GRAND's Alien Isolation mod uses
it too - three independent projects on one idea.

**It buys a second thing that is easy to miss.** The game already reads XInput, so motion controllers
can be composed into an `XINPUT_STATE` and handed over **with zero engine hooks** - full playability
arrives before any gameplay reverse engineering does. When you are choosing a proxy target, weigh what
the import gives you as an *interface*, not only as an injection point.

**Enumerate the imports before picking.** Anything the process loads early and nobody else fights over
will do; the graphics DLL is merely the one everybody thinks of first.

## Give concurrent sessions separate repositories with a one-way dependency {#repo-topology}

Not a rendering technique - a working structure, and the only one in this survey designed explicitly so
that **two sessions can run at the same time without colliding**. Six external-research repositories in
this batch share an identical layout, one per game. `[SOURCE]`

| Repository | What lives there |
|---|---|
| `<game>-vr-mod` | The mod itself. |
| `<game>-vr-dev-archive` | Full development history - snapshots, probes, dead ends, raw recon. |
| `<game>-vr-modding-notes` | Readable field notes and progress ledger. |
| `<game>-vr-staging` (private) | Unverified WIP builds, cross-machine handoff. |
| `<game>-vr-engine-research` | Distilled engine dossier plus a reusable RE playbook. |
| `<game>-vr-external-research` | Public-research leads. **Read-only input to the other five, never the other way around.** |

The load-bearing line is the last one:

> This repo exists so a dedicated research-only session can run **at the same time** as active
> reverse-engineering/coding work without any risk of the two colliding - research never writes to any of
> the other five repos, and the modding side just reads this one when it wants to check for new leads.

**A strict one-way dependency is what makes concurrency safe**, and it is cheaper than any locking
convention: there is no shared file to contend for, so "who is editing what" stops being a question. If
you run more than one agent session on a project, this is the structural version of the problem you are
otherwise solving with etiquette.

Two more details worth copying:

**The research index carries a status lifecycle, and one of the states is failure.** Entries move
🆕 new → 👀 reviewed → ✅ incorporated → ❌ **dead end**, and the dead-end state is explicitly *"kept for
the record so it isn't re-investigated from scratch."* Most note-taking systems record what worked. A
research corpus that does not record what was checked and abandoned will pay for the same lead twice.

**The consuming side updates the index, not the producing side.** Their rule: *"the modding side should
update this when it acts on a lead, so the index reflects reality without the research side needing to
poll."* That is [META-005](pattern-catalog.md#meta-005) - the knowing layer pushes - applied to a
workflow rather than to a frame.

## Unity's cheapest vehicle: turn on the VR path the engine already has {#unity-vr-flip}

Worth knowing before anyone writes a renderer hook for a Unity target. WeWereInVR (using Raicuparta's
patcher lineage) does not hook rendering at all. It opens the game's `globalgamemanagers` asset,
finds `BuildSettings.enabledVRDevices`, and writes one entry: `[SOURCE]`

```csharp
var enabledVRDevices = buildSettingsBase.Get("enabledVRDevices").Get("Array");
var vrDevicesList = new[] { StringField("OpenVR", stringTemplate) };
enabledVRDevices.SetChildrenList(vrDevicesList);
```

**Unity ships a complete stereo path in every build; that field decides whether it runs.** Flipping it
gives you stereo rendering, head tracking and the runtime handshake for free, with none of the
[hazards](14-render-pass-hazard-atlas.md) that come from making an engine render a second view it was
not designed to. It backs the original file up first, which is the whole of the uninstall story.

Everything after that is *gameplay*, not rendering - and it goes in a managed mod (BepInEx here) for
hands, poses, haptics, laser pointers and interaction. The split is clean: **an asset edit turns the
engine's VR on; a managed mod makes it playable.**

This is the same instinct as [META-006](pattern-catalog.md#meta-006) - implement or enable the engine's
own interface before hooking one - at its cheapest possible price point. **Check for it before anything
else on a Unity target**, and note the analogue on other engines: UEVR's target is Unreal's own stereo
device, and OpenMW-VR supplies a view callback. Where the engine has a VR path, the work is turning it
on and then fixing what the *game* assumes about a flat screen.

The limits are honest and worth stating: it needs the engine's built-in path to still exist in that
Unity version, it edits a file the game may overwrite on update - WeWereInVR's own README opens with
*"THE MOD DOES NOT WORK WITH THE NEWEST VERSION OF THE GAME"* - and it gives you no control over how the
game's UI, cameras and cutscenes behave, which is where the remaining work lives.

## Staged porting from a decompilation, and the oracle it gives you {#staged-decomp-port}

GoldenEye Omniport is in this survey as a **vehicle**, not as a VR implementation: its VR sections are
still `TBD` and there is no VR code in the tree yet. What it demonstrates is the route - and the test
infrastructure that route makes possible, which is the strongest in the batch. `[SOURCE]`

The layering is the point. From the [n64decomp/007](https://github.com/n64decomp/007) decompilation they
built **desktop first**, then Android on top of the desktop port, then VR on top of that. The desktop
port carries the renderer (Fast3D display lists interpreted on the CPU into OpenGL), the audio microcode
interpreter, input, and save handling. **Each layer is shippable and testable before the next one
starts**, so the VR layer inherits a port that is already known-good rather than debugging two unknowns
at once. If a decompilation exists for your target, this ordering is almost certainly cheaper than going
straight to VR - and it is the same argument as building a flat harness first
([13](13-teardown-bioshock-vr.md)), scaled up to a whole port.

**The oracle is the part to steal even if you never port a decomp.** Host-only changes inside the shared
`src/` are guarded with `#ifndef TARGET_N64`, and:

> the original N64 ROM build is untouched - **it still byte-matches the retail ROM**
> (`sha1: abe01e4aeb033b6c0836819f549c791b26cfde83`) after every change.

**A bit-exact reference build is the strongest regression test available to a port.** Any accidental
semantic change to shared code fails it immediately, with no test to have thought of in advance and no
judgement call about whether the difference matters. If your project has any build target whose output
should be byte-stable - the original binary, a reference dump, a golden capture - keep it in CI. See
[TEST-005](pattern-catalog.md#test-005).

Around it they run **struct-layout guards against the console ABI on every build**, a **483-check self
test** over the port layer, and **a scripted input regression that replays a full solo run of Dam with no
human present**, driven through `GE007_*` environment variables that also control windowing, timescale,
audio taps and diagnostics. That is the same conclusion four other projects in this survey reached from
different directions - [drive the game from outside so a person is not the test
harness](06-debugging-methodology.md#http-control-plane) - arrived at here through env-var input scripting,
which is the cheapest form of it and needs no server.

## A note on provenance

One mod in this collection ships this disclaimer:

> This project was developed entirely using AI code generation with Codex. None of the source code has
> been manually written or reviewed by a human. As a result, the code may contain bugs, security issues,
> performance problems, or other unintended behavior. Use this project at your own risk.

It is a complete, shipped, working 6DOF VR conversion with two-handed gripping, physical melee and a
config menu. Recorded here without judgement, for two reasons: **the disclosure is the responsible
pattern** and worth copying if you work the same way, and it is a data point on what this mode of work
now produces. Read such a codebase the way you would any other unfamiliar one — verify the claims
against the binary, not against the confidence of the comments.

---

**Related:** [11 · RE anchoring & discovery](11-re-anchoring-and-discovery.md) ·
[14 · Render-pass hazard atlas](14-render-pass-hazard-atlas.md) ·
[17 · Native stereo](17-teardown-fc2vr-native-stereo.md) ·
[08 · Project process](08-project-process.md) ·
[00 · Engine profiles](00-engine-profiles.md)
