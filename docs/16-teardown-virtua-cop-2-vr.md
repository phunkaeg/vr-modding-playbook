# Teardown: Virtua Cop 2 VR

A study of **[Rea-Virtua-Cop-2-VR](https://github.com/NeuralF/Rea-Virtua-Cop-2-VR)**, a native VR mod for
the **1997 PC port of Virtua Cop 2** — a Sega arcade rail shooter. Source read: `src/hgl_view.c` (3,837
lines, the 32-bit in-game DLL), `src/vc2vr.c` (2,134 lines, the 64-bit VR app) and `src/vc2_share.h` (the
IPC contract).

**Why it earns a chapter.** Every other project in this playbook takes the same fundamental approach:
find the engine's camera, take it over, make the engine render twice. This mod does something else
entirely — it **reconstructs the 3D scene from the 2D draw stream** and renders that. It never takes the
camera over at all. On a 1997 fixed-function renderer, where there is no camera object to find and no
shader to patch, that turns out to be the only door that opens.

It is also the playbook's first **rail shooter** and first **light-gun** target, and both change the
problem in ways worth naming.

---

## The seam: the game shipped a renderer plugin ABI

Virtua Cop 2 draws through a pluggable renderer DLL (`HGL_D3D.DLL`), selected from the game's own
graphics menu. The mod ships `HGL_VIEW.DLL`, which sits in front of it and appears in that menu as a new
device: **"Direct 3D + 3D view."**

No signature scanning, no prologue patching, no injector. The game's own extension point.

This is the top of chapter [11](11-re-anchoring-and-discovery.md)'s anchor ladder in an unusual form —
not a reflection system, but a **documented plugin boundary the developer already built**. Before
reaching for hooks on an older title, check for a renderer selector, a plugin folder, or a driver
abstraction. Games from the era when 3D hardware was not yet standardised very often have one, because
they had to support Glide, Direct3D and software rendering from one codebase.

Note the failure mode the README calls out, which is chapter [06](06-debugging-methodology.md)'s
presence-versus-working distinction exactly: *"The mod's hooks install as soon as the game scans its
renderer DLLs, but geometry only flows when Direct 3D + 3D view is the selected device."* Installed, and
producing nothing, is a state this architecture can sit in indefinitely.

## Un-project the draw stream, don't hook the camera

The engine submits textured quads in **screen space with a depth key**. The mod reverses the projection
to get world-space geometry back:

```c
static void unproject(float sx, float sy, DWORD w, float *ox, float *oy, float *oz)
{
    DWORD layer = w / LAYER;
    float z = (float)(w - layer * LAYER) / 8.0f;
    *ox =  (sx - g_cx) * z / g_fx;
    *oy = -(sy - g_cy) * z / g_fy;   /* screen y grows downwards, world y up */
    *oz = -z;                        /* OpenXR convention: forward is -Z */
}
```

Ordinary pinhole algebra. **The interesting part is where `fx`, `fy`, `cx`, `cy` come from.**

### Read the live projection every frame; never assume it

The mod reads all four values out of the game's own globals, **every frame**, because the engine changes
its FOV at runtime for authored zoom moments. The source comment is worth quoting in full, because it is
chapter [09](09-d3d11-openxr-injection.md)'s *extract `P_center`, don't guess* taken one step further:

> *"…the whole scene inflates and tears — which is exactly what the zoomed screenshots show. Read the
> four values the game is using right now instead of assuming them, and the unprojection is correct by
> construction at every zoom step, no calibration and no table of modes."*

**"Correct by construction, no calibration and no table of modes"** is the whole argument for live
extraction over a calibration table, in one line. A table of zoom modes would have needed a mode
detector, a per-mode calibration and a maintenance burden; reading the live value needs none of them.

Two guards ride with it, and both generalise:

- **Range-check before trusting.** `fx` must be in `(10, 200000)`, the principal point in `[1, 4096]`.
  *"Nonsense means the game has not set them up yet — keep what we have."* This is chapter
  [11](11-re-anchoring-and-discovery.md)'s classify-by-magnitude rule used as a **live** guard rather
  than a discovery technique.
- **Invalidate every derived cache when the projection changes.** The mod resets its whole world cache on
  an `fx` change, because *"the cache holds world points built with the old focal length, and they are
  simply wrong now — keeping them is how the zoom scenes get their torn geometry."* Any cache downstream
  of a projection inherits that projection's lifetime.

## The world cache: recovering camera motion without ever finding the camera

This is the cleverest thing in the codebase and it deserves to be widely known.

**The problem.** The engine only builds the geometry its own logic decides to build, so anything the
camera has passed is simply gone next frame. A 6DoF view that lets you look around corners needs the
scenery to persist — but persisting it requires knowing where the camera moved, and the mod never found
a camera.

**The insight.** Every quad arrives tagged with the model-view transform that produced it. For a *static*
object, that transform is `M(t) = Camera(t) · Object`. So the frame-to-frame delta is:

```
D(t) = M(t) · M(t-1)⁻¹ = Camera(t) · Object · Object⁻¹ · Camera(t-1)⁻¹
                       = Camera(t) · Camera(t-1)⁻¹
```

**The object's own placement cancels out.** You never need to know where the object is, or which matrix
is the camera, or whether the engine even has a camera concept. Chain the deltas and you have `A(t)`, the
camera's motion since the first frame; `A(t)⁻¹` maps view-space corners into a frame that stands still
while the camera moves. That frame is the cache.

Three pieces of engineering make it survive contact with a real game:

**1. Consensus, not a single measurement.** Many objects each yield a candidate delta. The mod scores
each candidate by how many *other* candidates agree with it (within 1.0 units of translation), weighted
by vertex count, and takes the winner:

> *"the answer several objects agree on is the camera; a lone object that happened to move on its own
> cannot outvote them"*

That is robust estimation in about fifteen lines, and it is what stops a moving car from being mistaken
for camera motion.

**2. Reject candidates that are not rigid motions.** Before accepting a pairing, column lengths must
match between frames within **0.5 %** (same object, not a rescaled one), and the resulting delta's column
lengths must be within **1 %** of unity (a rotation, not a scale). A candidate that fails is dropped
rather than averaged in.

**3. Re-orthonormalise the accumulator.** `xfOrtho(&g_camAcc)` runs after every chained multiply, because
hundreds of chained deltas accumulate floating-point drift into a matrix that is no longer a rotation.
This is appendix [A1](a1-rotation-and-frames.md)'s orthonormality property applied to a *running*
accumulator — assert it in tests, and **restore** it in accumulators.

### Static and dynamic separated by positional repeatability

The same cache solves a second problem for free:

> *"Quads that turn up at the same place several frames running are scenery and get kept; cars and people
> never repeat a position and are dropped, which is why they leave no trail."*

No object IDs, no engine knowledge, no per-game list of what is scenery. **Persistence-as-classifier** —
a general technique for any reconstruction approach where the engine will not tell you what is static.

## Two processes, because 32-bit and 64-bit cannot share one

Chapter [10](10-graphics-apis.md) lists "a 64-bit companion compositor" as the **fallback of last
resort** for legacy targets. This mod is a shipped, working instance of it, and worth reading before
anyone dismisses the route.

The split is forced: a 1997 32-bit game cannot host a 64-bit OpenXR runtime. So `HGL_VIEW.DLL`
(32-bit, in-process) reconstructs geometry and writes it to shared memory; `VC2VR.exe` (64-bit,
separate) renders it through OpenXR.

The header names a benefit that is easy to miss when treating this as a compromise:

> *"A crash on the VR side then cannot take the game down with it."*

**Process isolation cuts both ways.** Every other project in this playbook can crash its host game from a
VR bug. This one structurally cannot.

### The IPC contract is a model worth copying

`vc2_share.h` is 120 lines and does several things right:

- **Three independent seqlocks** — one for geometry, one for the window capture, one for the texture
  atlas — so a slow atlas upload never stalls the geometry path. Chapter
  [07](07-engine-integration-safety.md) and appendix [A2](a2-pose-pipeline.md) argue for the seqlock over
  a boolean gate; this is a **third independent project** arriving at it, and the stated reason is the
  right one: *"a stalled reader can never stall the game."*
- **The convention is normalised once, at the boundary.** *"Coordinates are already in OpenXR convention
  when they are written here: X right, Y up, Z backwards… Divide by `units_per_metre` to get metres."*
  The 64-bit side never learns the game's convention. Compare appendix
  [A1](a1-rotation-and-frames.md): state the convention once, at one place, and test it.
- **A version field both sides check**, with an explicit note that mixing versions misreads the mapping
  because sizes differ — not merely "is incompatible."
- **Staleness is a defined state, with a defined response.** *"The game side treats a stale `aim_seq` as
  'the VR app is gone' and releases everything it held down."* A dead VR process does not leave the
  trigger held. Design the death of your own component, not just its life.

## The aim round-trip: one hit point, two consumers

A light-gun game makes aiming *the* mechanic, so "the laser points here but the game registered there"
is not a polish issue — it is the whole product. The mod's answer generalises well beyond light guns.

The path, end to end:

1. Take the controller pose in VR space.
2. Transform into game space — undo the recenter yaw, scale by `units_per_metre`.
3. **Ray-cast against the reconstructed scene** (`rayVsScene`), falling back to `aimreach` metres when
   nothing is hit, so the laser always terminates somewhere.
4. Project that hit back through the game's **live** projection — *"the exact inverse of the DLL's
   `unproject()`: `sx = cx + x*fx/z`, `sy = cy - y*fy/z`, all four values live"* — clamp to the game's
   own 640×480 screen space, and write it to shared memory as the light-gun position.
5. Transform the **same** hit point back into VR space to draw the laser and its cross.

**Steps 4 and 5 consume one hit point.** The visual and the input are not computed separately and then
reconciled — they are two projections of a single result. That is why they cannot drift apart, at any
zoom level, which is precisely the failure the README claims not to have.

The floating menu screen is tried as a ray target *first*, and produces coordinates in the same 640×480
space — so clicking a menu and shooting an enemy are the same code path with a different intersection
test.

**The general rule: when a visual indicator and an engine input must agree, derive both from one
intermediate value.** Computing "where the laser draws" and "what the game is told" from separate maths
is how they end up disagreeing under a transform nobody tested.

## An authored FOV change is a gameplay signal, not just a camera value

The mod's best design decision, and its reasoning is the transferable part:

> *"In the flat game the zoom moments were authored: the engine walks its fov from 60 down to ~18 degrees
> exactly when a distant enemy is meant to fill the screen, and the player just keeps shooting. Here the
> reconstruction stays true-scale through that (correct for the world, useless for the fight), so follow
> the game instead: magnify by the same ratio the game is applying, capped by the zoom key. **The player
> aims, the scope comes to them.**"*

Unpack what happened. A faithful reconstruction is **technically correct and gameplay-wrong**: the world
stays true-scale, so the distant enemy the designer meant to fill your view stays distant. The authored
FOV narrowing was never really about the camera — it was the designer saying *this, now, matters*.

You cannot narrow a VR player's field of view. But you can honour the **intent** by magnifying at the
same ratio, capped for comfort. Chapter [01](01-camera-and-tracking.md) says to yield to authored
cameras; this adds a sharper reading: **work out what the authored camera change was *for*, then deliver
that intent by whatever means VR permits.** An authored FOV change, a forced look-at, a camera shake —
each carries a designer's intent that survives the transition even when the mechanism does not.

The zoom ratio is also learned rather than configured: *"the smallest `fx` the game has used is its
unzoomed baseline (about 554 at 60 degrees); anything above it is the game zooming its own camera."*
Track the running minimum and the baseline derives itself.

## Reuse the engine's own sort key rather than reconstructing depth

Under reconstruction, draw order is not obvious — you have geometry but not the engine's intent about
what occludes what. The mod does not attempt to rebuild that. It carries the engine's own depth key
through to the shader:

> *"the FULL 32-bit `w` (layer in the high bits) normalised to 0..1. The layer is part of the z-buffer in
> `HGL_D3D` (`sz = K/w`), which is how shadows sit on roads and sights float over all."*

The engine had already solved layering by packing a layer index into the high bits of `w`. Preserving
that — rather than deriving depth from reconstructed positions — inherits the original's sorting
decisions for free. Compare chapter [14](14-render-pass-hazard-atlas.md): where the engine has already
encoded an ordering decision, carry it rather than re-deriving it.

## The blind spot, honestly stated

Reconstruction only sees what goes through the geometry path. The README and header both say so plainly:

> *"menus, scores and cutscenes are drawn as 2D sprites that never pass through the quad slot — without
> this the headset shows an empty void everywhere outside actual gameplay."*

The fix is a **window capture on a floating screen** in the headset, published under its own seqlock. It
carries its own caveat, also documented: exclusive-fullscreen windows cannot be captured, so the game
must run windowed.

Two things to take from this. First, **an architecture's blind spot is a design input, not a defect to
hide** — the mod ships a second, cruder path for the content the main path structurally cannot see, and
says which is which. Second, this is the mirror image of chapter [04](04-ui-and-hud.md)'s usual problem:
most projects fight to get 2D UI *out* of the world; this one had to build a surface to put it *back*.

## When to reach for this — and when not to

Everything above is *what this mod did*. This section is the part you need on a new target: whether
draw-stream reconstruction is the right door, or a clever answer to a question you do not have.

**The rule in one line: un-project when the camera was never yours to move.**

That is the precise inverse of the standard approach. Finding the camera and injecting a second one
needs the engine to (a) build a view matrix you can reach and (b) tolerate rendering the scene twice.
Reconstruction needs neither — the engine never cooperates and never has to. It only has to keep
*submitting geometry*. So the two techniques fail in opposite conditions, and the cases where injection
has nothing to inject into are exactly the cases where reconstruction is easy.

### The four preconditions, with the test for each

Run all four before committing. Each has a cheap test that fails fast, and **precondition 2 is the one
that silently kills projects** — it is the difference between a 3D scene and a pile of sprites.

| # | Precondition | The test | Fails when |
|---|---|---|---|
| 1 | **An interceptable renderer boundary** | Is there a renderer selector in the graphics menu, a plugin folder, a swappable `*_D3D.DLL`/`*_GL.DLL`? Failing that, is the API wrappable — Glide, DDraw, D3D ≤ 8, fixed-function GL? | The renderer is statically linked and internal. You are back to hooking, which is fine — but then you may as well hook the camera. |
| 2 | **Per-primitive geometry with usable depth** | Log one frame of submissions. Count distinct primitives, and check each carries vertex positions plus *something* depth-like — a z, a w, or the engine's own sort key. | You get a few dozen screen-space textured rects with no z. That is a sprite engine and there is no 3D to recover. |
| 3 | **The projection is readable that frame** | Log the projection scale across a minute of real gameplay — including a zoom, a cutscene, and a scripted moment. Confirm it *changes*. | You hardcode a constant the engine actually varies. VC2 changes FOV at runtime; a hardcoded guess drifts, and the drift looks like tracking error. |
| 4 | **The scene fits the re-render budget** | Triangles per frame, from the capture in test 2. | A modern scene. You are re-rendering the whole recovered world twice per frame with none of the engine's culling. |

Test 2 deserves the extra minute. A frame log that shows *"142 quads, each with four positions and a
sort key"* means the technique works. A frame log that shows *"38 blits"* means it cannot, and no amount
of engineering changes that — the depth information was never submitted.

### The hard ceiling: you get what was submitted, and nothing else

**Everything outside the original flat frustum was culled and is simply not there.** This is not a
polish item that improves with effort; it is the shape of the technique.

- Turn your head past the original FOV and you are looking at empty space.
- Objects the flat game occluded may be missing entirely, because the engine never submitted them.
- The mod runs with backface culling **off** — its own comment says *"winding is unknown, so draw both
  sides"* — so moving off-axis shows you polygon interiors rather than a sealed world.

So the honest description of the output is **a diorama of the original shot**, not a world. Which is why
the rule is what it is: on a rail shooter you were never leaving the shot, so the ceiling costs nothing.
On a free-roaming game it is the entire problem.

### Where it fits, ranked

| Target class | Verdict | Why |
|---|---|---|
| **Light-gun / rail shooters** — Virtua Cop 1, House of the Dead 1–2 PC, Area 51, Time Crisis ports | **Best fit** | Identical shape to this teardown. Fixed camera, no locomotion, and VR *restores* the arcade cabinet ergonomics rather than approximating them. |
| **Arcade emulators** — Model 2/3, Naomi | **Best fit, easiest** | You own the renderer outright, the geometry is in a documented format, and there is no injection problem at all. Closer to writing a stereo consumer than a reconstruction. |
| **Glide/DDraw-era games via a wrapper** | **Good fit** | nGlide or dgVoodoo already sit exactly where `HGL_VIEW.DLL` sits. Preconditions 1 and 2 come for free. |
| **On-rails sequences inside a normal game** | **Narrow fit** | Useful as a *fallback* for the specific moments the engine takes the camera away and your injected stereo path breaks — not as the primary architecture. |
| **Fixed-camera survival horror** — RE 1–3, early Alone in the Dark | **Partial, and instructive** | The 3D characters reconstruct; the pre-rendered *backgrounds* fail precondition 2 outright. You would recover actors floating in a void. A good illustration of the precondition, not a candidate. |
| **Sprite/2.5D** — Diablo II, Build-engine titles | **No** | Fails precondition 2. Build is a portal renderer with real 3D data, so hook higher and take the camera. |
| **Any free-roaming game with a reachable camera** | **No** | The engine has a real camera you can own. Use it. Reconstruction would trade a real world for a diorama. |

### Do not conflate this with the two-process split

The IPC architecture in this mod — 32-bit game, 64-bit VR app, seqlock shared memory — is a **separate,
independently reusable idea**. It applies to any pre-x64 target regardless of whether you reconstruct or
inject, and it is now the fourth independent convergence on seqlock IPC in this playbook. Decide the two
questions separately: *how do I get a stereo scene* and *how do I get it into a 64-bit runtime* have
different answers and different preconditions.

## What this target teaches that the others cannot

| | |
|---|---|
| **Rail shooter** | The camera is 100 % authored — there is no locomotion to build, and no camera to own. Everything in chapter [03](03-input-and-locomotion.md) about locomotion is simply out of scope, and chapter [01](01-camera-and-tracking.md)'s "yield to authored cameras" becomes the *entire* camera design. |
| **Light gun** | Aiming is the whole product, so the aim round-trip gets engineering attention that a shooter with a crosshair would not justify. The one-hit-point-two-consumers rule came from that pressure. |
| **1997 fixed-function** | No shaders to patch, no camera object to find, no reflection. Reconstruction from the draw stream is not a clever alternative here — it is the only approach available. |
| **Renderer plugin ABI** | The developer shipped an extension point. Worth checking for on any pre-2005 title before assuming you must hook. |

---

## Practical notes worth stealing

- **`--window` mode** renders to a flat window instead of the headset, *"which is useful to tell a
  game-side problem from a VR-runtime problem."* A one-flag bisection between your two biggest
  subsystems — see chapter [06](06-debugging-methodology.md) on coarse switches.
- **The triangle count in the window title** is the fastest possible "is data flowing?" check. Zero
  triangles immediately means the geometry path, not the VR path.
- **Zoom toggle hysteresis**: latch at a 0.65 push, re-arm only below 0.30. The same separate
  engage/release thresholds JKXR uses for grip-to-button ([03](03-input-and-locomotion.md)) — one
  threshold gives you a flickering toggle.
- **The gun is whichever hand fired last**, with a fallback to the other hand if the aim space fails to
  locate. No handedness config, and it survives a tracking dropout.
- **`units_per_metre` is a user-facing config** with a plain-language heuristic: smaller if the world
  feels like a dollhouse, larger if gigantic. World scale is the one value a user can calibrate better by
  feel than you can by measurement.
- **Magnification amplifies head shake** — the README calls it *"physics, not a bug"* and exposes the
  zoom cap rather than adding smoothing. Worth remembering before building a stabiliser for a problem
  the user can dial out.

**Related:** [13 · Teardown: independent BioShock VR mod](13-teardown-bioshock-vr.md) ·
[15 · Teardown: IL-2 1946 VR](15-teardown-il2-1946-vr.md) ·
[09 · D3D11 & OpenXR injection](09-d3d11-openxr-injection.md) ·
[10 · Graphics APIs](10-graphics-apis.md) ·
[A2 · Motion controls & pose pipeline](a2-pose-pipeline.md)
