# Engine Profiles — the deep-comparison set

> **⚠ The authoritative fleet table is
> [cross-project-index.md](cross-project-index.md#the-fleet-at-a-glance)**, not this page. This chapter
> is a *deep four-way comparison* kept for its per-engine detail; it predates the fleet growing to
> additional first-hand projects and it does not list them all.
>
> **Corrected 2026-08-25.** This page previously opened "Four Games, One Playbook", described the
> playbook as distilled from four conversions, and stated **SS2VR as 32-bit — which is wrong; it is
> x64** (KEX is a 64-bit remaster; SS2VR's own analysis works at image base `0x140000000`). The error
> survived here for weeks because two pages carried the same fact independently. **One canonical
> table, everything else links to it** — see [the note on drift](#why-this-page-now-defers) below.

This chapter holds four flat-to-VR conversions side by side in detail. The value of that comparison is
the thesis of the whole document: **the engines are wildly different in age, API, and architecture, yet
the VR conversion hits the same patterns, the same roadblocks, and the same solutions.** Where a lesson
only holds on one engine, this doc says so; the rest is cross-engine by construction.

Three of these (SS2VR, BioshockVR, SOMAVR) are first-hand. The fourth,
[Halo MCC VR](https://github.com/pancreations/Halo-MCC-VR), is an external MIT-licensed project folded
in as independent corroboration — built by a different person on a different engine, and it still landed
on the same core lessons.

**The other four first-hand projects** — PreyVR, DishonoredVR, FarCry2-VR, Swat4-VR — are covered in
[cross-project-index.md](cross-project-index.md), [17](17-teardown-fc2vr-native-stereo.md) and their own
`docs/` trees.

## The four-way comparison

| | **SS2VR** (System Shock 2) | **BioshockVR** (BioShock) | **SOMAVR** (SOMA) | **HaloVR** (Halo 3 / MCC) |
| --- | --- | --- | --- | --- |
| Original engine | LGS **Dark Engine** (1998) | **Unreal Engine 2.5** fork "Vengeance" (2007) | Frictional **HPL3** (2015) | **Blam/Saber** lineage (2007) |
| Shipping binary | Nightdive **KEX** remaster | **BioShockHD.exe** remaster | **Soma_NoSteam.exe** | **`halo3.dll`** hosted by `MCC-Win64-Shipping.exe` |
| Graphics API | **D3D11** | **D3D11** | **OpenGL 4.6** (SDL2 + GLEW) | **D3D11** |
| Bitness | **64-bit** | 32-bit x86 | **64-bit** | **64-bit** |
| Scripting | **Squirrel** (`sq_scripts`, `.kpf` mods) | native **UObject/UnrealScript** (`AShockPlayer`, `AHands`, `AWeapon`) | **HPL script** `.hps` (`LuxPlayer`, `PlayerState_*.hps`) | **HaloScript + tag data** (H3EK editing kit) |
| World scale (to metres) | `world_scale=3.28` | `~65 units/m` | HPL world units, near `0.03` / far `1000` | — |
| Native camera FOV | (KEX projection) | H≈`100°` / V≈`67.7°` (from `screenDataToCamera`) | vertical `70°` | **user-set `120`** (required; default culls) |
| Frame boundary hook | `Present` | `Present` | **`gdi32!SwapBuffers`** (via `SDL_GL_SwapBuffers`) | `Present` (but pose sampled for the *next* predicted display) |
| Stereo approach | private per-eye D3D11 targets + RenderView, **half-rate alternate-eye** | private per-eye HDR/depth targets, cloned cbuffers, same-frame replay | **AFR** (alternate-frame) into GL swapchains | **engine's own prepared-view renderer** driven per eye, stereo-array swapchain |
| Prior art leaned on | old Dark/Shock source, `openDarkEngine` | 3DMigoto/3D-Vision fixes, UEVR, UnrealPort | **HPL2 source** (Amnesia), UEVR patterns | HaloCEVR, ReclaimerVR, **ManagedDonkey** + H3EK |

### Why this page now defers

This chapter carried a fleet roster *and* so did the cross-project index. When the fleet grew, one was
updated and the other was not — and the stale copy sat on the orientation page, where it is most likely
to be believed. An agent reading only this page would have taken SS2VR for a 32-bit target and reached
for `x32dbg`.

**The rule that follows: a fact belongs in exactly one place, and every other page links to it.**
Duplicating a table is duplicating a maintenance obligation, and the copy that drifts is always the one
nobody is looking at. Where you cannot avoid a second copy, say which one is authoritative — as the
banner at the top of this page now does.


## Engine source trees held locally, and what each may be used for {#local-engine-sources}

`D:\Dev Debug\source code\` holds engine source for **five of the eight in-house targets**. This is
recorded here because knowing a tree exists is the whole value - a project that does not know cannot
consult it, and three separate projects in this fleet have re-derived something a sibling already had.
`[STATIC]`

| Tree | Applies to | Why |
|---|---|---|
| `UnrealEngine3` (build **10897**) | **DishonoredVR** | UE3 32-bit D3D9 - the exact stack. `Development/Src/` carries `Core`, `Engine`, `D3D9Drv` and `GFxUI` (Scaleform, which is how UE3 games build their HUD). Its README indexes `GNames`, `GObjects` and `GMalloc` by file and line |
| **Four CryEngine trees** (below) | **PreyVR**, and **FarCry2-vr** | Prey 2017 is a CryEngine/Arkane fork; **Dunia is a heavily forked CryEngine**. Pick by generation - see the table under [Choosing a CryEngine tree](#choosing-a-cryengine-tree) |
| `AmnesiaTheDarkDescent`, `AmnesiaAMachineForPigs` (**HPL2**) | **SOMAVR** | HPL3's direct predecessor - same lineage, same authors, much of the structure survives |
| `DarkEngine`, `SystemShock2`, `SystemShock2GD`, `thief_2_service_release`, `openDarkEngine`, `darkengine-main` | **ss2vr-work** | Dark Engine, plus a clean-room reimplementation |
| `geo-11-0.6.56` | any | a stereo driver in the 3D-Vision lineage; general reference for per-eye shader fixes |

Swat4-VR (UE2.5) and BioshockVR (a UE2.5 derivative) inherit partial lineage from the UE3 tree, but the
generational gap is large - treat it as vocabulary, not layout.

### Choosing a CryEngine tree, and what actually transfers {#choosing-a-cryengine-tree}

There are **four**, spanning three engine generations, and the generation is the whole decision.
`[STATIC]`

| Tree | Generation | Closest to |
|---|---|---|
| `CryGame` | **CryEngine 3** Free SDK stock GameDLL | **PreyVR** - Prey 2017 is CryEngine 3/4-era |
| `CRYENGINE` (MergHQ) | 5.3, self-described as *"a fork from 2016"* | general reference |
| `CRYENGINE_Source` | 5.x, and the only one carrying a `LICENSE.md` | general reference |
| `-CRYENGINE-Community-Edition-` | **5.7**, community continuation | newest; furthest from every target |

**Nothing here is close to Dunia.** Far Cry 2's engine forked from **CryEngine 1** around 2006-08, so the
5.x trees are three generations away and `CryGame` is still two. Treat them as vocabulary and
architecture for FarCry2-vr, never as layout.

**The version gap is real, and it moves symbols rather than concepts.** `EFQ_DrawNearFov` - the query
[FC2VR uses to keep viewmodel FOV in step with eye FOV](17-teardown-fc2vr-native-stereo.md) - **does not
exist anywhere in the 5.x tree.** But the *mechanism* it queries very much does, as `m_drawNearFov` and
`DRAW_NEAREST_MIN` in `D3DRendPipeline.cpp`. So the calibration is: **search for the concept, not the
symbol.** A missing enum is not a missing feature, and a found symbol in the wrong generation is not a
promise about your binary.

**Two things that do transfer, both verified present:**

- **CryEngine has native asymmetric-frustum support.**
  `CCamera::SetAsymmetry(l, r, b, t)` in `CryCommon/CryMath/Cry_Camera.h`, backed by
  `m_asymL/R/B/T`. For a CryEngine target this is the engine's own answer to
  [the symmetric-FOV problem](09-d3d11-openxr-injection.md), already built.
  **And Crytek's own comment corroborates a hazard this fleet derived independently:**

  ```cpp
  f32 m_asymL, m_asymR, m_asymB, m_asymT; //!< Shift to create asymmetric frustum (not used for culling atm).
  ```

  *Not used for culling.* That is first-party confirmation that
  [widening the projection does not widen what the engine culls](09-d3d11-openxr-injection.md) - the
  exact trap behind edge-void reports.

- **CryEngine ships a stereo renderer.** `CryCommon/CryRenderer/IStereoRenderer.h`,
  `RenderDll/XRenderD3D9/D3DStereo.cpp`, and `GameSDK/GameDll/Stereo3D/StereoFramework.cpp`. Reading how
  Crytek did per-eye rendering inside this engine family is prior art for **both** CryEngine targets, and
  the approach survives the version gap even where the symbols do not.

### The CryEngine asymmetric-frustum contract, read from source {#cryengine-asymmetry-contract}

Worth its own section because **PreyVR reverse-engineered this formula and the source names the same
variables.** Their RE labelled Prey's asymmetry fields `fWL/fWR/fWB/fWT`; `DriverD3D.cpp` builds the
projection as: `[STATIC]`

```cpp
rcam.Frustum(wL + cam.GetAsymL(), wR + cam.GetAsymR(),
             wB + cam.GetAsymB(), wT + cam.GetAsymT(), Near, Far);
```

Same four letters, same role. Three things follow that a decompiler will not tell you:

- **The shifts are frustum-edge offsets in near-plane units, not angles.** They are *added to* the
  computed edges. Anything solving OpenXR `XrFovf` tangents into these fields must produce edge offsets,
  which is what makes a tangent-space inversion the right shape.
- **The near/viewmodel pass re-applies the asymmetry, rescaled.** The weapon pass runs with its own FOV
  and its own near plane, and rescales every shift by the ratio between them:

  ```cpp
  float fNearRatio = DRAW_NEAREST_MIN / Cam.GetNearPlane();
  Cam.SetAsymmetry(Cam.GetAsymL() * fNearRatio, Cam.GetAsymR() * fNearRatio,
                   Cam.GetAsymB() * fNearRatio, Cam.GetAsymT() * fNearRatio);
  Cam.SetFrustum(..., fFov /* = DEG2RAD(m_drawNearFov) */, DRAW_NEAREST_MIN, ...);
  ```

  This is [STR-011](pattern-catalog.md#str-011) - *the near pass has its own projection* - stated by the
  engine itself. **Inject asymmetry into the world camera without accounting for `fNearRatio` and the
  viewmodel's asymmetry will be wrong relative to the world**, by exactly that ratio.
- **"Not used for culling" does not mean unused elsewhere.** `ShadowUtils.cpp` derives a
  `vStereoShift` from `GetAsymL()` and `GetAsymB()`, so **shadows consume the asymmetry while culling
  ignores it.** A mod that widens or shifts the frustum should expect shadow behaviour to follow and
  culling not to - which is the asymmetric failure behind edge-void reports.

**And PreyVR hooks a function whose source is here.** `CD3D9Renderer::RT_EndFrame` is declared in
`RenderDll/Common/Renderer.h` and driven from `RenderThread.cpp`. Reading its surroundings answers what
the render thread has already done by the time the hook fires - which is a question about *this engine
family*, and survives the version gap far better than any offset does.

### Two rules, and the second is not optional

**A licensee's engine is not your engine.** Every one of these games ships a *forked* build. UE3 10897 is
not Dishonored's build; the CRYENGINE mirror is not Dunia. Source tells you **what a structure is for and
roughly how it is shaped** - it never tells you an offset. That is
[the same rule as a sibling's addresses](11-re-anchoring-and-discovery.md): **a derivation is
target-specific evidence exactly like an address is**, and it must still be confirmed against your own
binary. Used correctly a source tree is a *hypothesis generator*, and an extremely good one.

**The trees do not share a licence, and it decides what you may do with each.** Checked by inspection,
not assumed:

| Tree | Licence found | Consequence |
|---|---|---|
| Amnesia TDD / AMFP | **GPL v3** (`LICENSE` present) | officially open-sourced by Frictional. Free to read; **GPL terms apply if you copy code** |
| openDarkEngine | **GPL v2** (`COPYING`) | clean-room reimplementation; same copying caveat |
| CRYENGINE (MergHQ mirror) | no licence file at the mirror root | source-available upstream; read freely, check terms before copying |
| UnrealEngine3, DarkEngine, SystemShock2 | **none** | circulated trees, not licensed to this project |

For the last row the practical rule is simple and it costs nothing: **take the layout knowledge, never
the source text.** What a mod needs is *where `GNames` lives and what `FSceneView` contains* - facts
about the binary in front of you, which you then confirm against it. Pasting engine source into a shipped
mod is a different act with a different consequence, and it is never necessary to get the answer.

Record which tree a finding came from in your evidence notes, the same way you would record a sibling
project. See [state the interoperability basis](08-project-process.md).


## What each engine makes easy, and what it makes painful

**SS2VR (Dark/KEX, D3D11, 64-bit).** A portal/cell engine with a CPU visibility pass that runs
*before* any render-view rewrite. Culling is decided in 2D screen space against a fixed-point
viewport, from a cull camera anchored to the body. That architecture makes "peek around a corner"
the hardest problem on this engine (see [01](01-camera-and-tracking.md)) and means you drive KEX's
*culling inputs*, never the RenderView, to change what's visible. Squirrel gives you a real,
supported command/verb surface for input and gameplay actions, which is why SS2VR lives high on the
[input ladder](03-input-and-locomotion.md) without native calls for most controls. The old
open-source Dark lineage is gold for *vocabulary*, but only the KEX binary is authoritative.

**BioshockVR (UE2.5 "Vengeance", D3D11, 32-bit).** A UObject engine: real named native classes
(`AShockPlayer`, `AHands`, `AimIKTargetTracker`, `AWeapon::GetPerfectFireStart`) you can hook by
signature and *drive* rather than reimplement. That is a double edge — the richest native-integration
surface of the three (native arm IK, native fire-direction seam), but object *lifecycle* becomes the
blocker: the AimIK tracker only exists after natural `AHands` construction, invisible to
attach-to-running (see [07](07-engine-integration-safety.md)). Its shaders carry the most elaborate
projection contract of the three — `worldViewProj` is one of eight coupled constants, laid out
differently per shader family — which is why BioShock is the reference example for
[projection companions](09-d3d11-openxr-injection.md). Non-stock package serialization (`.blk`
resources indexed by `Catalog.bdc`, `ShaderTag` → `MaterialFactory_*`) makes its assets a project of
their own.

**SOMAVR (HPL3, OpenGL, 64-bit).** The odd one out on every axis: modern-ish, 64-bit, and **OpenGL**,
which breaks most of the D3D11 assumptions in chapters [07](07-engine-integration-safety.md) and
[09](09-d3d11-openxr-injection.md) — no device/context object, a global state machine, FBOs instead
of RTVs, matrices arriving through `glUniformMatrix4fv`, and a compatibility profile that can defeat
RenderDoc (see [10](10-graphics-apis.md)). Its saving grace is the **HPL2 open source** (Amnesia),
which seeds string and control-flow searches for the closed HPL3 binary. HPL3 also exposes the
cleanest *semantic* surfaces of the three — named camera-add channels (Bob/Shake/Sway), a native
interaction picker that already returns hit distance, a 34-state crosshair enum, and Newton contact
records — which is why SOMA drives most of the [comfort](01-camera-and-tracking.md),
[reticle](04-ui-and-hud.md), and haptics material. AFR was the pragmatic first stereo path because
re-entering HPL3's whole render pipeline twice per frame is expensive and side-effectful.

**HaloVR (Blam/Saber, D3D11, 64-bit).** The only target here that is a *collection*: MCC hosts Halo 1–4,
ODST and Reach as separate engine DLLs under one shipping executable, so the mod needs a **title
registry and per-title adapters** rather than a single engine binding — a structural problem none of the
other three have. It is also the only one with **anti-cheat** in the picture; it patches no game files
and runs solely through MCC's official EAC-disabled mode, which rules out on-disk patching as a
technique from the start. Two things make it unusually tractable: an official **editing kit (H3EK)** and
the open-source **ManagedDonkey** reimplementation give real names for tags and HUD structures, and much
of the HUD is **tag data rather than code**, so it can be retuned by locating and writing floats in a
loaded asset heap instead of hooking the renderer. Its hardest surfaces are the ones driven by that same
tag system: the crosshair is selected through runtime `chud_definition` tag indices that are *not* stable
element ids, and normal play short-circuits past the obvious hook site entirely.

## A different shape entirely: the managed mod layer (IL-2 1946)

Every engine above is a native binary you must reverse-engineer. The
[IL-2 1946 VR mod](15-teardown-il2-1946-vr.md) is the one target in this playbook where **the game's
own logic is a managed, moddable layer** — IL-2's camera, HUD, flight model and render orchestration
are Java bytecode, and the SAS/UP mod frameworks already load replacement classes by hash. It is worth
holding next to the table above because it isolates what our method is actually buying us.

| | **IL-2 1946 VR** (external) |
| --- | --- |
| Original engine | Maddox Games IL-2 engine (2001–2006), **Java game layer over a C++ renderer** |
| Shipping binary | `il2fb.exe` — **never touched**; mod is `il2vr.dll` + 63 replacement `.class` files |
| Graphics API | **OpenGL** (legacy / compatibility, fixed-function `glLoadMatrixf` projection) |
| Bitness | 32-bit |
| Scripting | n/a — the *game itself* is the script layer (`com.maddox.il2.*`) |
| VR runtime | **OpenVR** (`IVRSystem_022`, `IVRCompositor_027`, `IVROverlay_026`) — no OpenXR |
| Frame boundary hook | **none** — the frame loop (`Renders.doVRStereoPaint`) is edited directly |
| Stereo approach | **same-frame three-pass**: left eye FBO, desktop mirror, right eye FBO, one pose sample |
| UI | **100% compositor overlays** — ImGui into private FBOs, submitted as `IVROverlay` quads |

**What it makes easy:** the hook cannot miss, drift across builds, or fire on the wrong thread —
class replacement *is* the hook. Chapter [11](11-re-anchoring-and-discovery.md) barely applies. Finding
"the camera" is a `javap` away, and the render loop can simply be rewritten to run three times.

**What it makes painful, and the trade to internalise:** you are locked out of everything the native
side owns. This mod cannot touch IL-2's shader pipeline, so its answer to the modern shader path is to
*disable it* (`ForceShaders1x=1`) — that is the price of having no hook. And **version coupling is
total**: a replaced class is a fork of one exact baseline, so the author maintains two builds and has
abandoned four. A signature-guarded native hook would have spanned all of them.

> **Source-level modding trades version robustness for access.** When both are available — as here,
> where the mod already ships a native DLL — the right architecture is usually *both*: managed classes
> for game logic, a native hook for whatever the managed layer cannot reach.

## Engines surveyed from other people's mods

Beyond the projects here, a wider independent set of mods was read for
[18](18-beyond-the-native-injector.md). Their engines widen the picture considerably — and note that
**modding mode correlates with what the developer released, not with the engine's age or complexity**:

| Engine | Game(s) | API / arch | Mode | What it hands you |
|---|---|---|---|---|
| **LithTech Jupiter EX** | F.E.A.R. | D3D9, x86 | Native injector | Official SDK source — but the CRT ABI blocks shipping a rebuild ([11](11-re-anchoring-and-discovery.md)) |
| **Dunia** | Far Cry 2 | D3D9/D3D10, x86 | Native injector | A `WorldExec` vtable slot — enough for native stereo ([17](17-teardown-fc2vr-native-stereo.md)) |
| **AnvilNext 2.0** | AC Odyssey / Valhalla / Mirage | D3D11/12, x64 | Native (DXGI hook) | A `worldMatrixOverride` pointer the engine already honours |
| **REDengine 3** | The Witcher 3 (NG) | **D3D12**, x64 | Native + script bridge | A scripting layer usable as a state channel; a projection-centre offset field |
| **Unity (Mono / IL2CPP)** | GTFO, SPT, RoR2, Bendy, MFN, White Knuckle | varies | Managed plugin | Named classes and methods; per-eye render callbacks |
| **Unreal 4/5** | Satisfactory | D3D11/12 | UEVR + companion mod | Stereo, tracking and input, generically |
| **id Tech 3 / IW / GoldSrc** | Jedi Academy, CoD4, Counter-Strike | GL / D3D9 | Source port | The entire engine |
| **Frostbite** | Star Wars Battlefront II (2017) | D3D11 | Native (safetyhook) | A settings-class type system enumerable from a string-table naming convention |

The practical use of this table is the **mode** column. Before starting, establish which one your target
falls into — an afternoon's work, and it changes the discovery route even though both routes later rejoin
the shared VR spine:

1. Can the code owning the retail camera/render loop be **built and shipped**? →
   [source-owned route](source-owned-route.md). If it can only be read, use it as an oracle for the RE route.
2. Is it **Unreal**? → UEVR plus a companion mod, unless you can say why not.
3. Is it **Unity**? → managed plugin; check IL2CPP vs Mono first.
4. Otherwise → [RE-owned route](reverse-engineered-route.md), then work the deeper anchor ladder in
   [11](11-re-anchoring-and-discovery.md).

Record the answer as an [integration authority map](start-new-port.md#port-01), not a binary “source: yes/no.”

## The cross-engine spine (why one playbook covers all four)

Every one of these recurred on **at least three of the four** engines despite the differences above. If
you internalize nothing else, internalize that these are engine-independent:

1. **A VR mod creates a second camera, and every subsystem silently binds to one of several.** The
   "which camera / which frame" question is the root of most jank on Dark, Unreal, HPL and Blam alike
   ([01](01-camera-and-tracking.md)).
2. **Moving the projection matrix is a contract, not a matrix write.** These engines consume
   projection *companions* (reconstruction, eye position, depth scale, clip planes). BioShock makes
   this loudest; SOMA's deferred lighting proves it in OpenGL too
   ([09](09-d3d11-openxr-injection.md)).
3. **Culling/visibility is owned by the engine's camera, not your render frustum.** You cannot render
   your way out of missing geometry — you drive the engine's cull camera/FOV. Halo is the cheap case
   that proves the rule: it exposes an FOV *setting*, and raising it to `120` pushes culling past the
   headset's field of view with no hook at all ([01](01-camera-and-tracking.md)).
4. **Prefer driving the engine's own native systems over reimplementing them.** SS2 drives KEX's cull
   camera and Squirrel verbs; BioShock drives native AimIK and the fire-start seam; SOMA drives the
   native analog mover, picker, and camera-add channels; Halo drives the engine's own prepared-view
   renderer per eye and converts controller aim into Halo's *normal aim steering*, so projectiles,
   target logic, vehicles and turrets stay game-owned. Reimplementation is the fallback, not the
   default ([03](03-input-and-locomotion.md), [07](07-engine-integration-safety.md)).
5. **The graphics API changes the plumbing, not the play.** D3D11 vs OpenGL changes *how* you own
   targets, state, and submission — but the proof ladder, private-eye targets, source-freshness
   tracking, and lane separation are identical ([10](10-graphics-apis.md)).
6. **Comfort and game-feel are their own engineering surface.** Snap-turn blackout, peripheral
   vignette, head-bob/shake suppression, and contact haptics recur; SOMA even reused SS2VR's exact
   0.30 m / 1 m vignette contract on a different engine and API, and Halo independently arrived at the
   same "suppress the engine's authored camera-effect stage while head tracking is active" solution
   ([01](01-camera-and-tracking.md), [02](02-viewmodels-and-hands.md)).
7. **The method dominates the engine.** Build self-ID, readback/residual probes, one-variable A/Bs,
   fail-closed hooks, and test-validity discipline saved more time than any engine trick on every
   project ([06](06-debugging-methodology.md), [08](08-project-process.md)).
