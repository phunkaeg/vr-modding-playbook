# UI & HUD

Flat UI is drawn in screen space; in VR it has to live somewhere in 3D. And the reticle/HUD
elements you want to suppress or relocate are owned by systems that don't expect a second
opinion.

## A screen-space HUD is CROPPED, not mis-scaled, when declared FOV exceeds headset FOV {#hud-cropped-not-scaled}

`[LIVE, and the fix is UNVERIFIED IN A HEADSET - flagged by the reporting project.]`

One project renders **115 degrees** while the headset shows about **94**, so roughly **16% is cut from
each side**. The reflex is to hunt for a UI scale factor. **There is not one** - nothing is the wrong
size, the edges are simply outside the visible frustum.

**And apply the fix at the tile-draw call every 2D primitive passes through, not at the layout or clip
rect.** Adjusting the layout moves elements inward *while leaving glyphs and icons at their original
pixel size*, which produces a differently-wrong result that is easy to mistake for progress.

Related: [the HUD is not one class](#ui-not-one-class) - a crop affects every family at once, which is
part of why it reads as a global scale problem.


## Get UI off the backbuffer and onto a layer

Submitting the full backbuffer as **both** the world projection and the UI gives you frozen,
wrong-depth, head-locked UI. Instead:

- **Tee/capture** the engine's 2D UI draws into a separate transparent texture, and present
  that as its own composition layer (OpenXR quad layer) or a world-anchored panel.
- Classify draws by their render target and draw shape: HUD quads are typically small indexed
  draws into the backbuffer-class RT; fullscreen post passes are non-indexed or 3-vertex
  triangles. Filter on that, not on guesses.
- Decouple **visibility** from **interactivity** — you usually want to *see* inventory/HUD
  before you can *click* it, and they're gated separately.
- Tee from the *confirmed* final UI draw family, never the composited backbuffer. (*BioshockVR:
  the HUD is tee'd into a fresh head-locked quad from the confirmed final-LDR `TriangleFan` UI
  family; a HUD failure must leave the world projection and desktop HUD intact.*) Fix HUD staleness
  with source freshness, not a bigger max-age window.
- **Look for the engine's own "render UI to a target" switch before intercepting individual draws.**
  Many engines already support redirecting UI to an offscreen target for their own reasons. (*UEVR
  redirects Unreal's UI with mid-hooks around the render-target creation call and forces it to a separate
  target via the engine's existing `Slate.DrawToVRRenderTarget` cvar, then hooks viewport presentation to
  place that target in world space.*) One switch beats classifying hundreds of draws — see
  [11](11-re-anchoring-and-discovery.md).

Know the layer types: an OpenXR **projection layer** describes world views with per-eye poses
and asymmetric FoVs; a **quad layer** is a compositor-placed surface. Submitting a flat game
image through a projection layer does not make it spatially correct, while a quad layer is an
excellent honest fallback for menus, debugging, and cinema-mode presentation.

**For full-screen flat menus specifically, mirror the desktop window onto a quad — and get input for
free.** Capturing and re-laying-out a menu means rebuilding its hit-testing in VR space; mirroring the
window means the pointer is *inside the mirrored image*, so the physical mouse works with no extra code
and the click path is identical to the desktop by construction. (*The external
[IL-2 1946 VR mod](15-teardown-il2-1946-vr.md) blacks out both eyes whenever a flat menu is active and
presents the window as a world-space overlay at the window's own aspect ratio, auto-showing and
auto-hiding on menu state. No laser pointer, no controller, no cursor injection.*) This also sidesteps
the SS2VR trap below, where cursor injection overrode the OS mouse and the physical input path was never
reached. Reach for the mirror before you build a pointer.

Do not stretch a 16:9 UI or game source across a tall eye texture. Preserve aspect and place it
deliberately. Crop-to-fill is useful as an A/B but changes angular scale and hides content.

**Capture-and-reproject is not universally the right answer — it's engine-dependent.** On some engines
the native HUD already renders acceptably into the stereo view, and capturing it costs GPU time while
delivering less. (*HaloVR tried capture/diff of the HUD panel, got only the objective text out of it for
real GPU cost, and formally accepted the **native HUD** as the rendering path instead — then solved
sizing/placement through tag data and an anchor-basis hook, above.*) Decide by measuring what the capture
actually yields, not by assuming the layer approach always wins.

## HUD element ownership — find who actually draws it

Before you can hide or move a HUD element, identify the system that owns it. Engines often have
a table of named overlay/HUD elements with on/off state and per-element rects. Suppressing the
wrong layer (e.g. redrawing your own lines into the same flat overlay the broken element lives
in) just repeats the failure. (*SS2VR: drawing VR brackets through the engine's 2D overlay API
reproduced the exact flat-HUD problem they were trying to escape.*)

**Never re-invoke an immediate-mode GUI's render path just to capture its output.** Immediate-mode
systems execute widget logic on *every* render call — layout, animation timers, dirty rects, focus — so
"render it a second time to grab a copy" re-runs the logic and desyncs all of it. (*SOMAVR's first
terminal-overlay implementation replayed the native GUI's draws to composite them into the VR HUD;
stateful draw counts doubled from 17 to 34–56 per frame, producing the fragmented, flashing panes the
users reported. The fix rendered the native GUI **exactly once** into a dedicated surface sized to its
real logical resolution, then blitted that single result into the HUD target.*) Intercept and blit the one
real pass; never trigger a second one. This is the UI-side form of the ownership rule above — the GUI owns
its own execution, and you are only allowed to copy its output.

## The HUD's layout may be data, not code

Before you hook a single draw call to move or resize the HUD, check whether its geometry is **authored
data** the engine reads every frame. If it is, you retune the HUD by writing a few floats instead of
intercepting the renderer — vastly cheaper and far less fragile.

- *HaloVR:* HUD layout size lives in the `chud_globals` tag's "curvature infos" blocks (one per skin) as
  two "global safe frame" floats that scale the whole layout toward screen centre. It was proven twice —
  the official editing kit re-laid the HUD out at a different value, and live pokes resized the HUD
  instantly in-headset. Nearby fields in the same authoritative struct turned out to own curvature/depth
  (`destination_offset_z`) and, via a separate anchor-basis hook, true vertical placement.
- **The catch: that data lives in a loaded read-write heap, not the module image**, so a module-relative
  RVA won't find it. Locate it by an immutable **data** signature instead — HaloVR keys on a 24-byte
  prefix (`[int32 1280][int32 720][55.0f][661.0f][58.0f][4.0f]` — virtual canvas, sensor origin/radius,
  blip radius) with the safe-frame pair at `+24/+28`, confirms exactly the expected number of blocks with
  bit-exact payloads, and **re-checks the prefix and payload plausibility on every write** so a stale or
  relocated slot is rejected rather than corrupted. See [11](11-re-anchoring-and-discovery.md).

## The reticle is often not where you think

A "crosshair" may be a classic HUD-table element — or the remaster's own modern UI draw that
has nothing to do with the legacy table. Suppressing the legacy slot then leaves the reticle on
screen and you conclude (wrongly) that suppression failed.

- Prove which it is: log the element's on/off state while the reticle is visible. If the
  element is *off* and the reticle is *still there*, it's a different draw.
- Find the real draw by signature in a frame capture (vertex count + texture size + target),
  then skip exactly that draw. (*SS2VR: the surviving centre reticle was a 6-index sprite quad
  with a 32×32 texture in the UI pass — not the legacy crosshair slot, which was already off.
  Skipping that specific draw killed it.*)

- *BioshockVR:* the reference/aim reticle is explicitly **not** the gameplay crosshair
  (`gameplayAimOwner=unchanged`), and the private-HDR headset source legitimately lacks the late-LDR
  desktop crosshair — so "the crosshair is missing from the eye image" was expected, not a suppression
  failure. Prove which draw you're looking at before concluding anything.
- *HaloVR:* the value passed to the HUD widget draw is a **runtime tag index**, not a stable element id.
  Hardcoding the observed indices meant one weapon lost its cursor while others kept theirs, and the
  toggle could hide an unrelated weapon HUD icon. The durable fix was to gate on the engine's own
  semantic classification (the widget-collection "crosshair" scripting class) rather than on any observed
  numeric id. **An index you observed at runtime is an observation, not an identifier.**

## A world-depth reticle comes from the engine's own picker, not from GL/DX depth

When you want a reticle that sits *on the thing you're pointing at*, don't reconstruct depth from the
graphics buffer or fire your own ray — the engine already runs an interaction pick every frame and
knows the hit distance. Read that, and place a small quad layer on the controller aim at that distance.

- *SOMAVR:* the native picker (`SOMA_GetClosestEntity`) returns `mpEntity` / `mpBody` / `mfDistance` at
  known offsets. The bridge validates finite distance against the native ray length, takes the *exact*
  app-space controller aim pose the native query used, converts `mfDistance` through the world scale,
  and submits a source-alpha `XrCompositionLayerQuad` at that point — no second ray test, no depth
  read from OpenGL. Invalid/no-hit clears the reticle so stale focus is never shown.
- Make it **semantic** when the engine exposes intent. SOMA's shipped script drives a 34-state
  crosshair enum (carry/pickup, push/pull/rotate/button, tool/info, traversal, social/consume,
  unavailable, …); the bridge signature-guards the native dispatch thunk, observes only that callback,
  and maps the state to a native icon plus a matching haptic pulse — while SOMA still owns range,
  line-of-sight, `CanInteract`, and the actual interaction. Load the engine's *own* enum→asset table
  rather than inventing icons, and keep a procedural fallback for when decode fails.

Identifying HUD draws is the prerequisite, and the reliable test is the projection matrix, not the
shader or the texture:

```cpp
/* A HUD/2D draw is ORTHOGRAPHIC: w does not vary with z, so there is no
   perspective divide. That is a property of the matrix and cannot be faked by
   a 3D draw, which makes it far more robust than shader- or texture-matching. */
bool IsOrthographic(const Mat4& proj) {
    return std::fabs(proj.m[11]) < 1e-6f &&           // no -z -> w term
           std::fabs(proj.m[15] - 1.0f) < 1e-6f;      // w is constant 1
}

/* Screen-space quad -> a world-space panel at a fixed distance. Preserve the
   authored aspect: deriving height from the backbuffer instead of from the
   ortho volume is what makes ported HUDs subtly stretched. */
Mat4 PanelTransform(const Mat4& ortho, float distanceM, float metresPerUnitX,
                    const Pose& panelAnchor)
{
    const float halfW = 1.0f / ortho.m[0];     // ortho: m[0] = 2/(r-l)
    const float halfH = 1.0f / ortho.m[5];     //        m[5] = 2/(t-b)

    const float w = 2.0f * halfW * metresPerUnitX;
    const float h = w * (halfH / halfW);       // aspect from the ORTHO VOLUME

    return Mat4FromPose(panelAnchor)
         * Mat4Translate({0, 0, -distanceM})
         * Mat4Scale({w, h, 1.0f});
}
```

**Derive height from `halfH/halfW`, not from the render target.** The two agree only when the game is
running at its authored aspect ratio, and a VR swapchain almost never is.

## Converging an aim ray without hitting the player's own body

When you replace a flat game's crosshair with a headset- or controller-derived ray, the ray starts at
the player's head or hand — **inside their own avatar's collision shapes**. The naive first result is a
reticle stuck permanently on Geralt's shoulder.

The naive *fix* is worse: globally disabling the character collision group so the ray passes through
bodies. That breaks the feature, because the sight ray must still converge on **other** characters
standing nearby — which is most of what a player aims at.

The correct shape is a short retry loop that skips only the player's own shapes:

```text
direction  = normalize(farTarget - rayOrigin)
traceStart = rayOrigin + direction * 0.20      // begin just in front of the eyes

repeat up to 4 times:
    trace(traceStart -> farTarget) against Static, Terrain, Character, Ragdoll, Destructible
    no hit                       -> return farTarget          (converge at infinity)
    hit entity is NOT the player -> return hitPosition        (the answer)
    hit entity IS the player     -> advance traceStart past that shape and trace again
```

(*Witcher 3 VR's `W3VR_FP_ResolveAimConvergence`, in REDengine script. Its comment states the rule
directly: "never globally disable Character collisions, because the sight ray must converge on nearby
actors too."*)

Three details worth keeping:

- **The 0.20 m start offset** handles the common case without any retries at all — most of the body is
  behind the eyes.
- **Bound the loop.** Four passes is enough for a humanoid's overlapping shapes, and a bounded loop
  cannot hang the render thread if something unexpected keeps reporting a hit.
- **"No hit" is a valid answer, not a failure.** Return the far target so the reticle converges at
  infinity rather than snapping to the last known position.

Do this in the engine's own trace system if you can reach it — you inherit its collision groups, its
material filtering and its notion of what is targetable, none of which you want to reimplement.

## Suppression must be gated by context

Anything you suppress during gameplay (reticle, centre frob, native brackets) must come *back*
in menus/inventory and when tracking is lost. Gate on a cursor/menu-mode flag and a tracking-
staleness fallback. A reticle that's correctly gone in combat but also gone in the inventory
screen is a regression.

## Find the engine's authoritative UI state instead of inferring it

Deciding "is a full-screen UI up right now?" from observable proxies is a trap, and the proxies fail in
ways that each look reasonable:

| Proxy | Why it fails |
|---|---|
| **Pixel coverage** | Slow-motion, fades and full-screen effects are equally full-coverage. A briefing scored `coverage_percent ≈ 99` and was thrown away as a game frame. |
| **Menu focus** | Only knows about pause menus. Briefings, loading and movies are invisible to it. |
| **"Is the gameplay system still updating?"** | The weapon manager keeps running during a briefing, so freshness heuristics classify it as gameplay. |

The engine almost certainly has an authoritative answer already. (*F.E.A.R. keeps
`CInterfaceMgr::m_eGameState` — `GS_PLAYING`, `GS_MENU`, `GS_MOVIE`, `GS_LOADINGLEVEL` and six more.
Everything except `GS_PLAYING` belongs on the flat screen.*) Go and find that enum. It is one field, and
it replaces a stack of heuristics that will each fail on a different content type.

**Triangulate the offset rather than trusting one hit.** Their evidence for `m_eGameState` being a dword
at `+0x08` was three independent sites, all reached through the same global pointer:

```text
0x000EF900   cmp dword ptr [ecx+8], 5 ; setne al ; ret     -> a test against GS_MENU
0x000F2510   returns true for values 1..2                  -> "is in the world"
0x000F1F20   mov eax,[ecx+8]; cmp eax,9; ja ...            -> jump table over exactly TEN states,
                                                              matching the SDK enum's ten values
```

The jump-table arm is the strongest: a table with exactly as many entries as the enum has values is very
hard to produce by coincidence.

**Record the dead ends too.** They note that the `GS_MOVIE`…`GS_UNDEFINED` name table and the
`InterfaceMgr::` strings are **unreferenced dead debug strings**, as are the `ScreenMgr.cpp` and
`InterfaceMgr.cpp` filename strings — *"do not try again."* A negative result written down is worth as
much as a positive one on a multi-session project ([11](11-re-anchoring-and-discovery.md)).

**Keep the heuristics as a fallback, not as the primary.** Their implementation probes module identity
and the access functions' byte patterns once; if anything mismatches it logs
`retail_game_state_layout_mismatch` and the old heuristic path stays active, with an escape-hatch flag to
force it. Replacing a heuristic with a precise signal should not make the mod *more* fragile on an
unrecognised build.

## Redirect a whole category of draws by rebinding the target once

A neat and very cheap way to separate UI from the world: **hook one instruction and rebind the render
target**. Everything drawn after it lands on your surface, with no per-draw classification at all.

(*BF2VR hooks the instruction immediately after the engine's UI render-command dispatch — their comment:
"This is the instruction after a call to an address that dispatches render commands across the game.
This specific call is for the UI." The whole handler is three lines.*)

```cpp
void D3DService::OnUIDraw() {
    if (!OpenXRService::xrRunning) return;
    ID3D11RenderTargetView* uiRTV = OpenXRService::xrRTVs.at(2).at(uiSwapchainImageIndex);
    if (uiRTV == nullptr) return;
    pContext->OMSetRenderTargets(1, &uiRTV, nullptr);   // everything after this goes to the UI layer
}
```

Note `xrRTVs.at(2)` — index 2, beyond the two eyes. **The UI has its own OpenXR swapchain and its own
composition layer**, which is what [§ Get UI off the backbuffer and onto a layer](#get-ui-off-the-backbuffer-and-onto-a-layer)
asks for, obtained without touching a single UI draw individually.

Two requirements that are easy to miss:

- **Clear the UI target every frame.** They clear it to transparent black in `Present`; without that,
  last frame's HUD persists under this frame's, because nothing else writes those pixels.
- **Find a dispatch boundary, not an arbitrary draw.** This works because the engine funnels UI
  rendering through one call site. If your target interleaves UI and world draws, rebinding once will
  capture the wrong things and you are back to classification ([14](14-render-pass-hazard-atlas.md)).

**Look for the dispatcher.** An engine that batches render commands by category almost always has one
call site per category, and hooking the instruction *after* the call gives you a clean seam that needs no
knowledge of what the category contains.

## Three ways to place a HUD in stereo, and they are all legitimate

There is no single right answer, and the projects here have shipped all three. Pick per element and
state which you used:

| Placement | What you do | Costs |
|---|---|---|
| **Same pixel in both eyes** | Draw the HUD at identical screen coordinates per eye | Sits at optical infinity. Markers land in the same place, which is what you want for anything that annotates the world |
| **Fixed pixel disparity** | Draw with a constant horizontal offset between eyes | Puts the HUD at one fixed apparent depth, cheaply, with no 3D work at all |
| **World-placed panel** | A real quad at a real distance | Correct at every distance; costs a proper 3D placement and can collide with geometry |

*(Cyberpunk 2077 VR pastes the engine's HUD composite **at the same pixel in both eyes** by default "so
markers land in the same place", with finite-distance placement retained behind a setting because
wide-FOV headsets want it. JKXR takes the middle route — a `cg_hudStereo` cvar, defaulting to `20`, that
applies a per-eye horizontal offset to replayed HUD commands.*)

**The middle option is underrated on a constrained target.** A single cvar of pixel disparity gives the
HUD a comfortable apparent depth without re-rendering anything in 3D, and exposing it as a number lets
users tune it to their own comfort — which is the honest answer, since apparent depth interacts with
IPD and headset FOV.

**What you must not do is mix them silently.** A reticle at infinity and an ammo counter at two metres
will fight each other for accommodation every time the player's attention moves between them.

## Placing panels in 3D

- **Wrist/controller-anchored** panels (inventory, ammo, a keypad) feel diagnostic and
  reachable; **head-locked** panels are for transient comfort only (they induce nausea if
  persistent).
- **Parameterise panel sharpness as pixels-per-metre, not as a texture size.** Coupling the two means
  every resize is also a sharpness change and every sharpness fix is also a memory decision, so the
  tuning never converges. (*IL-2 1946 VR exposes `texdens`, default 1024 px/m, explicitly "decoupling
  sharpness from panel size" — the parameterisation the rest of this playbook argued its way around.*)
- **Fade world-space panels by gaze angle.** A dense instrument overlay can stay permanently configured
  without cluttering peripheral vision: full opacity within a few degrees of the gaze ray, gone by ~30°,
  with an explicit always-visible opt-out. (*IL-2 1946 VR: `fade_min_angle=5`, `fade_angle=30`,
  `always_visible=1`.*)
- **Offset the gaze ray, don't ask the user to look down.** Panels usually sit below eye level; a global
  pitch offset on the pick ray (IL-2 uses `-10°`) beats forcing an uncomfortable head posture. It does
  *not* generalise to picking real world geometry — use the engine's own picker for that (below).
- **For anything spatially placed, ship the editor.** Guessing coordinates in a config file and
  relaunching is the most wasteful loop in VR modding. (*IL-2 1946 VR ships a self-contained three.js
  page that previews panels in a simulated cockpit, reproduces the gaze fade, writes the INI, and pairs
  with a hot-reload hotkey so the change applies without a restart — the mature form of SS2VR's
  "expose the metrics as live config keys".*)
- Reuse the engine's own rect data when it exists — the native HUD already knows where the
  ammo/inventory/keypad rectangles are; cropping the captured UI by those rects beats guessing
  pixel slices that break at different resolutions.
- Pointer interaction wants a depth-clipped beam and clear hand-ownership (which controller
  owns the cursor right now), with last-active priority.

## System-panel lifecycle and input rules

Shock2Quest’s frontend-menu campaign exposes the failure cases that a static
“put the menu on a quad” recipe misses `[SOURCE]`.

### Place once from a valid pose, gravity-align, then world-lock

A system panel should not be gaze-glued. On entry:

1. reject an invalid/zero head quaternion;
2. take position from the tracked head;
3. derive direction from yaw only;
4. construct an honest basis where local +Z faces the viewer and +X is viewer
   right;
5. apply any content Y-flip exactly once;
6. leave the panel world-locked.

If the user moves far away or turns more than roughly 60° for a sustained
period, a lazy recenter can ease over about 0.3 seconds rather than snapping.
Those values are source-specific defaults, not universal constants.

The zero quaternion deserves an explicit guard. Some math libraries rotate
with it as though no rotation occurred, yielding a convincing but fixed ray or
a panel at a default world direction.

### One pointer arbitration, all visuals and clicks

Compute one authoritative hit record and make hover, highlight, beam, hit dot
and activation consume it. Never rerun a “visual” raycast independently. A
useful negative test positions two nearby targets and asserts that exactly one
shared target ID is used by every consumer.

### Enter modal screens already pressed

If a death, scene transition or menu entry occurs while trigger is held, the
new surface must not interpret that held value as a rising edge. Initialize
edge history as already pressed and wait for release. Clear button state for an
untracked or no-longer-driven hand.

For every modal surface, write an edge-policy table before implementation:

| Transition | Decision |
|---|---|
| Opens while a button is held | Ignore until release |
| Head/controller pose invalid | No pointer/click |
| Session visible but unfocused | Render, neutralize input |
| Scene/game state changes | Release old input owner |
| System UI opens | Freeze simulation if desired, never frame submission |

### Keep diegetic and system ownership separate

Use world surfaces for inventory, keypads, terminals and objects that remain
part of live gameplay. Use the system panel stack for main menu, pause, load,
death and dialogs. A modal system surface should explicitly make hands
pointer-only; a diegetic surface should coexist with the game’s normal
interaction rules.

Desktop/flat VR harnesses can prove geometry, pointer arbitration and input
edges. They cannot prove tracked-pose validity, compositor lifecycle or
headset readability; retain a device acceptance pass.

## Virtual-coordinate gotcha

UI APIs frequently use a fixed virtual canvas (e.g. 960×540) regardless of actual resolution,
while your raw draw/aim canvas uses real pixels. Mixing them puts everything off by a
resolution-dependent factor, worst at ultrawide. Keep "UI virtual coords" and "raw pixel
coords" as explicitly separate spaces and convert deliberately.

## The HUD as world geometry, and the three ways to place one {#hud-as-world-geometry}

There are three places a VR HUD can live, and this playbook previously described only two. The third is
what a source-owned port reaches for, because it needs no compositor concept at all. `[SOURCE]`

| Where | How | Cost |
|---|---|---|
| **Compositor quad / overlay** | Runtime composites it | Renders at runtime resolution - best text legibility. Cannot be occluded by world geometry. |
| **Quad blitted into the eye textures** | You composite it yourself | Renders at *eye* resolution, not the runtime's. One project's own notes concede this as the price of using no `XrCompositionLayerQuad`. |
| **A real world entity** | The engine draws it like anything else | Occlusion is available, depth is real, no overlay path needed - and legibility is whatever your eye buffer gives you |

DOOM-3-BFG-VR takes the third route, and does it by **reusing a mechanism the engine already had**:

```cpp
// model to place hud in 3d space
hudEntity.hModel        = renderModelManager->FindModel( "/models/mapobjects/hud.lwo" );
hudEntity.customShader  = declManager->FindMaterial( "vr/hud" );
hudEntity.weaponDepthHack = vr_hudOcclusion.GetBool();
```

The HUD is a **map object with a custom material**. `weaponDepthHack` is idTech's existing trick for
drawing the viewmodel without world geometry poking through it - compressed depth range - and the VR HUD
simply borrows it. Toggling `vr_hudOcclusion` chooses which behaviour you want:

> `vr_hudOcclusion` - 0 = Objects occlude HUD, 1 = No occlusion

**That is the C4 tradeoff exposed as one boolean.** Look for the engine's viewmodel depth handling before
building an overlay path; if it exists, a world-entity HUD inherits occlusion control for free.

### Body-locked is the default, not head-locked or world-locked

Their placement set, with shipped defaults:

```text
vr_hudPosDis   = 32     distance from view, inches
vr_hudPosVer   =  7     vertical offset, inches
vr_hudPosHor   =  0     horizontal offset
vr_hudPosAngle = 30     view angle
vr_hudScale    = 1.0
vr_hudPosLock  =  1     0 = Face, 1 = Body
```

**`vr_hudPosLock` defaults to Body.** That is a third option distinct from both head-locked (nauseating)
and world-locked (you walk away from it): the HUD follows your torso and stays put as you look around.
For a HUD that must remain reachable while the head moves freely, body-lock is the answer, and
[HUD-002](pattern-catalog.md#hud-002)'s world-locked rule is the right one only for *placed* panels.

### Look-activate, with an automatic override for the case that matters

`vr_hudType` defaults to **2 = Look Activate**, paired with `vr_hudRevealAngle = 48`: the HUD is absent
until you pitch your head down 48 degrees to consult it. That is the middle ground between permanent
clutter and no information, and it is diegetic - you look at your gear.

The detail worth stealing is the escape hatch:

> `vr_hudLowHealth` = 20 - "0 = Disable, otherwise force hud if health below this value."

**The comfort feature yields automatically in the one situation where hiding information could cost the
player the game.** A conditional-visibility HUD needs a condition under which the condition stops
applying; without it, the first thing a player loses is the number they most needed.

Twelve independent element toggles sit behind that - health, ammo, pickups, tips, location, objective,
stamina, pills, comms, weapon icons, new items, flashlight - which is the same granularity lesson as the
[shipped settings vocabulary](08-project-process.md#shipped-settings-vocabulary), one level finer.

### The reticle projects onto the surface it hits

```text
vr_weaponSight          0 = Lasersight  1 = Red dot  2 = Circle dot  3 = Crosshair  4 = Beam + Dot
vr_weaponSightToSurface 1 = map sight to surface
```

`vr_weaponSightToSurface` is the one that matters: the sight is drawn **where the ray lands**, not
floating at a fixed distance. A reticle at a fixed depth is double-imaged whenever the thing you are
aiming at is at a different depth - the classic flat-HUD-in-stereo failure - and projecting it onto the
hit surface removes the problem rather than tuning it. Five sight styles ship because which one reads
best is genuinely per-player.

## A UI pointer crosses three coordinate spaces, and each one fails differently {#pointer-coordinate-spaces}

BFVR's menu-pointer contract enumerates the spaces a captured 2D UI actually passes through, and the list
is longer than most implementations assume: `[SOURCE]`

1. the game's **native menu canvas** - theirs is 800x600, identified from the orthographic projection's
   `m00 = 0.0025` and `m11 = 0.003333` (that is, `2/800` and `2/600`);
2. the **captured raster** the mod draws it into - 1920x1080;
3. the **padded OpenXR texture** the presenter aspect-fits it into - 1872x2016, with the carrier quad at
   `z = -1.5 m` and `1.6 m` wide, so the visible content is a centred `1.6 x 0.9 m` region and the
   remainder is transparent padding.

Deriving the native canvas from the ortho matrix is worth remembering on its own: `m00 = 2/width` and
`m11 = 2/height` for a standard orthographic projection, so the game tells you its UI resolution even
when nothing is named.

**Two failure signatures separate the two mistakes, and both are observable without a headset:**

| What you see | Cause |
|---|---|
| Pointer error **varies with position** on the panel - correct in the centre, wrong at the edges | Two of the three spaces have been conflated; a scale or padding term is missing |
| Pointer error **varies with movement history** - drifts as you move, never returns | Relative mouse/controller deltas are being mixed with an absolute panel point |

That second row is the more insidious, because it looks like a calibration problem and invites exactly
the wrong fix. BFVR's document is explicit that their input overlay contains no cursor-write route at
all, so any pointer visible in the build comes from outside it and **must not be "corrected" by layering
relative deltas onto it** - the same discipline as
[not fixing the visible model by retuning the invisible systems](02-viewmodels-and-hands.md).

An absolute panel intersection is the only pointer definition that is stable under both tests. See
[HUD-001](pattern-catalog.md#hud-001).

## A glyph fallback that renders a space deletes text silently {#silent-glyph-fallback}

Any mod that draws its own text - a settings page, a debug readout, an in-headset tuning menu - inherits
whatever the engine's font system does with a character it does not have. Singularity VR's did the worst
possible thing. `[SOURCE]`

Reported as *"there are no `*`s around restart"*. `GlyphIndex` returns **space** for anything unknown,
so `*RESTART*` drew as `" RESTART "` - and the consequence nobody had noticed:

> **the `>` / `<` on the page rows had been invisible since they were added.**

**A missing-glyph box or a question mark is a bug report; a space is a design decision.** Substituting
whitespace makes the omission look deliberate, so it survives every review by everyone who was not
looking for it - here, across every session since those rows shipped.

Two fixes, and they took both: **add the glyphs** rather than rewording around them, and **make the
fallback warn** so the next missing character announces itself instead of vanishing.

**Audit your own text the cheap way:** render the full set of characters your UI can emit - including
punctuation and any decoration you use as a marker - and read it once. Marker characters are the usual
casualties, because they are exactly the glyphs a game font shipped for dialogue never needed.

## "UI" is not one class, and the shader signature will not separate it {#ui-not-one-class}

A transform that is right for the HUD is catastrophic for the fullscreen overlays drawn through the same
path, and Psychonauts VR found no cheap way to tell them apart. Worth knowing before you design a UI
correction. `[SOURCE]`

They needed to shrink screen-space UI back to its native angular footprint when the FOV is scaled up.
Shader constants could not do it - the ten UI shaders are purely additive (`oPos = input + c50`), with
no register that scales position - so it went in as a **viewport shrink**, factor
`tan(fovyBase/2) / tan(fovyScaled/2)` (0.602 at FOV 1.5), with the depth constant compensated by
`1/shrink` so perceived depth stayed put. Sound reasoning, and:

> **Live result: correct for actual HUD elements, catastrophic for everything else.**

The game draws its **fullscreen overlays through the same UI shader signature** - pause and menu
backdrops, fades - and those must span the full widened frame. The shrink crushed them into the centre
~60% and left black borders. In the paused-game dump the pause art is shrunk with pure black around it
while *"the 'your game was automatically paused' dialog itself shrank correctly."* One transform, two
populations, opposite requirements.

**And neither obvious discriminator works:**

- **Shader identity does not separate them** - UI shader `#0` draws everything rectangular.
- **The constant is not a position.** `c50` looked like a per-element offset and is not: it is the
  classic **D3D9 half-pixel offset**, exactly `(-1/640, 1/480)` at 640x480, plus occasional one- or
  two-pixel nudges for drop shadows. **Element positions live in the vertex buffers**, so there is no
  cheap constant-based fullscreen-versus-element test.

**Recognise the half-pixel offset on sight.** A constant whose components are `+/-1/width` and
`+/-1/height` for the current backbuffer is a rasterisation correction, not data about the element - and
reading it as position sends you down a long wrong path.

So classify by **geometry**, not by shader: a draw whose vertices span the full viewport is an overlay;
one that occupies a small rectangle is an element. That is more work than a constant test, and it is the
work the problem actually requires.

## Diegetic in-world screens and handheld devices

An in-world screen — a computer terminal, a handheld device, an arcade minigame — is a great VR moment
(you hold it, you point at it) but it lives inside a different subsystem than the HUD.

- **These are usually a table-dispatched immediate-mode framework; add content by detouring one slot.**
  (*SS2VR's Game-Pig is one `int gGameCurrent` selecting parallel function-pointer tables — Init / Draw /
  Input / Term, 13 entries each. A new "cartridge" is one `VirtualProtect` on the `.rdata` table and one
  slot overwritten with your callback of the same ABI.*) Signature-guard the slot (skip if it isn't the
  known RVA — fail closed on a patched binary), SEH-wrap install and every callback, and make the enable
  flag a **live** toggle that chains to the *saved original* when off, so it's an instant no-restart
  escape hatch. Leave the in-world unlock/item bit alone so the screen stays authentically diegetic.
- **VR input to the panel is often free — but verify the *real* input path live.** The panel already
  consumes the game's abstract input, which your controller beam + cursor injection synthesize. But
  don't assume. (*SS2VR nearly shipped assuming point-and-click; the remaster had rebuilt the minigame's
  input as a gated mouse dispatch, and in VR the physical-mouse path is never reached because cursor
  injection overrides the OS mouse — so only the controller beam drives it.*) Ship a belt-and-suspenders
  fallback with a short debounce so a click arriving via two paths collapses to one action.
- **Ship a "smoke mode" for render-detour work you can't test outside a headset.** Because you're
  patching live engine tables, first render only a couple of static text lines to validate the riskiest
  unknowns — does the detour fire? does the one engine font/blit export you verified land where its
  origin says? — before trusting the full game loop. Expose grid/font-cell metrics as live config keys;
  those can't be predicted statically.
