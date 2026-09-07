# Render-Pass Hazard Atlas

When you frame-capture an unknown engine you meet a list of passes, and the only question that matters
for VR is: **what does this pass read, and does that make it hostile to stereo?** This chapter is the
lookup table.

It is distilled from published frame teardowns of shipped AAA renderers — Adrian Courrèges' studies of
[GTA V](https://www.adriancourreges.com/blog/2015/11/02/gta-v-graphics-study/) and
[DOOM 2016](https://www.adriancourreges.com/blog/2016/09/09/doom-2016-graphics-study/), Alain Galvan's
[Control](https://alain.xyz/blog/frame-analysis-control) analysis, Emilio López's
[Rise of the Tomb Raider](http://www.elopezr.com/the-rendering-of-rise-of-the-tomb-raider/) breakdown,
[RDR2](https://imgeself.github.io/posts/2020-06-19-graphics-study-rdr2/), and Muhammad A. Moniem's
[RE Engine](https://mamoniem.com/behind-the-pretty-frames-resident-evil/) study, among others collected on
[Courrèges' index](https://www.adriancourreges.com/blog/). None of those games is a mod target here — the
value is the **taxonomy**, which transfers to any renderer you inject into.

The organising principle behind the whole chapter: **classify a pass by what it *samples*, never by its
name or its output.** Engines disagree wildly about structure (see "there is no canonical G-buffer"
below), but the hazard follows the input.

## Alternate-eye breaks VELOCITY-buffer effects, not temporal ones {#velocity-not-temporal}

Counterintuitive, measured in a headset, and it corrects a prediction this fleet made from sound
reasoning. `[HEADSET]`

**Motion blur is a hard blocker for alternate-eye rendering.** Under AER the camera jumps a full IPD
between consecutive frames, so the velocity buffer reads that as large apparent motion and smears
accordingly. **Near geometry carries the most parallax, so it smears worst** - which is why the artefact
is distance-dependent and reads as *soft or out of focus* rather than as blur. It is easily misdiagnosed
as depth of field, a wrong frustum, or a resolution problem.

Disabling motion blur is a **requirement** of alternate-eye rendering, not a quality preference.

**Temporal AA is fine, and that was the surprise.** PreyVR predicted TAA would fail for the same reason -
it accumulates across frames which are now different eyes - and warned about it on that reasoning. A
wearer cycled all four AA modes in the headset and **chose the temporal one**; with motion blur off it
does not soften near geometry.

> The reasoning was sound and the conclusion was wrong.

So the hazard is **velocity-buffer effects**, not *temporal* effects - the two are not equivalent here.
Anything that reconstructs apparent motion from consecutive frames is exposed; anything that merely
accumulates samples may not be. Test them separately rather than banning a category.


## The five hazard classes

| Class | What defines it | Stereo hazard | Treatment |
| --- | --- | --- | --- |
| **1. World-geometry** | Rasterizes scene geometry through a camera | **Low** — correct per eye *if* you drive the camera | Drive the camera; replay or re-enter per eye |
| **2. Screen-space reconstruction** | Samples depth/normals by screen UV and rebuilds world position | **Severe** — the dominant artifact class | Per-eye producers, or re-render the scene per eye |
| **3. Temporal / history** | Reads the *previous frame's* result | **Severe under alternate-eye** — "previous frame" is the other eye | Disable, or make history per-eye |
| **4. Sub-resolution + upsample** | Renders at ½/¼ res, upsamples using depth/stencil | **Moderate** — needs its own per-eye depth to upsample against | Per-eye buffers; keep stencil coherent per eye |
| **5. Optical / display post** | Simulates a *camera*: lens distortion, vignette, grain, chromatic aberration | **Wrong by definition in VR** | **Disable outright** |

## The atlas

Read this as: *if you see this pass in a capture, expect this.*

| Pass | Typically reads | Class | Notes |
| --- | --- | --- | --- |
| Depth pre-pass | geometry | 1 | Often also writes **velocity** — see the temporal trap below |
| G-buffer / material pass | geometry | 1 | 3–6 MRTs; RE Engine packs velocity+AO+SSS into one target |
| Shadow-map / cascade generation | geometry from light | 1 | Light-space, **not** view-space → usually eye-independent and shareable |
| Shadow *resolve* / shadow mask | shadow map + **camera depth** | 2 | The classic offender: a screen-space mask consumed by lighting |
| Deferred lighting / G-buffer combine | G-buffers + depth, reconstructs world pos | 2 | Where a mono-centred projection shows up as mis-lit geometry |
| Clustered/tiled light assignment | depth → cluster index | 2 | Forward+ still reconstructs from screen coords |
| SSAO / HBAO+ | linear depth (+normals), usually ½ res | 2 + 4 | GTA V, DOOM and RoTR all half-res with depth-aware blur |
| Screen-space reflections | depth, normals, **and often the previous frame's colour** | 2 + 3 | DOOM's SSR reads *previous-frame* colour + previous camera state |
| Hi-Z / depth pyramid | depth | 2 | Derived per-eye data (RE Engine builds 8 mips) |
| Volumetric fog / light shafts | shadow maps + depth, into a **froxel volume** | 2 (+3 if accumulated) | RoTR: 160×90×64 volume; frustum-shaped ⇒ inherently per-camera |
| Fog / atmosphere composite | depth + light-shaft buffer | 2 | Cheap to get wrong, very visible |
| Planar reflection / water | scene re-rendered from a mirrored camera | 1 | A **second view** — see render-view provenance in [09](09-d3d11-openxr-injection.md) |
| Environment cubemap / probes | scene, low res | 1 | Usually view-independent; safe to share between eyes |
| Subsurface scattering | combined buffer + depth + stencil mask | 2 | Stencil-gated; keep stencil per eye |
| Particles / decals | depth (soft-particle fade), often ½ res | 2 + 4 | RoTR renders particles half-res with stencil-aware upsample |
| Distortion / heat-haze map | depth, low res | 2 | Screen-space displacement |
| TAA | **previous frame** + velocity + depth | 3 | The single worst pass for alternate-eye |
| Temporal denoiser (SVGF etc.) | **frame history** + motion vectors | 3 | Control denoises RT effects this way — same hazard as TAA |
| Motion blur | velocity buffer, often ½ res | 3-adjacent | Velocity is frame-relative; see below |
| Auto-exposure / eye adaptation | HDR luminance, **adapts across frames** | 3 | Global scalar; see "exposure" below |
| Bloom | HDR, downsample pyramid to ⅛–1/16 | 4 | Mostly benign; duplicate per eye |
| Tonemap / colour grading | HDR + exposure + LUT | 4 | Benign, but must be consistent between eyes |
| FXAA / SMAA | final colour | 4 | Benign (non-temporal) |
| **Lens distortion / chromatic aberration** | final colour | **5** | **Disable** — the headset has its own optics |
| **Vignette / film grain** | final colour | **5** | **Disable** — reads as dirt on the lens, hurts comfort |
| Depth of field | depth + CoC, often ½ res | 5-ish | **Usually disable** — your eyes do the focusing |
| UI / HUD | own buffer | — | Separate lane entirely ([04](04-ui-and-hud.md)) |

## The temporal trap, in detail

This is the sharpest thing the AAA studies contribute, and it is not obvious.

Any pass in class 3 reads "the previous frame." Under **alternate-eye or paired rendering
([10](10-graphics-apis.md)), the previous frame is the *other eye*.** So:

- **TAA blends the left eye's history into the right eye's image.** The result is a permanent
  half-IPD ghost that no amount of TAA tuning removes, because the history is not stale — it is *wrong*.
- **SSR that samples the previous frame's colour** (DOOM does exactly this, along with the previous
  camera state) reflects the other eye's view.
- **Temporal denoisers** — Control's SVGF, and every ray-traced effect that depends on one — inherit the
  same defect. A modern RT renderer is *more* temporally dependent, not less.

**Motion vectors are the hidden multiplier.** Velocity buffers are computed from the difference between
this frame's and the previous frame's vertex positions (DOOM computes velocity in the depth pre-pass; RE
Engine and RDR2 store it *inside* the G-buffer). Under alternate-eye, that difference includes the **IPD
shift** — so every motion vector encodes your eye separation as if the whole world had lurched sideways.
Everything downstream that trusts velocity (TAA, motion blur, denoisers) then does the wrong thing
confidently.

**Auto-exposure is temporal *and* global.** GTA V drives adaptation from a 1×1 luminance texture evolving
frame to frame. Two hazards: adaptation can pump when consecutive frames are different eyes, and if the
two eyes ever adapt *independently* you get binocular rivalry — genuinely unpleasant. Lock exposure, or
force both eyes to share one value.

Also watch for **results deliberately deferred by a frame**: DOOM defers occlusion-query results to the
next frame to avoid a GPU stall. Under alternate-eye those results arrive in the other eye's frame.

**Decompile the history copy; don't infer it.** The fix is a per-eye history bank, and to build one you
need to know exactly what is copied, from where, to where, and how often. (*SOMAVR's post-post pass copies
exactly `0x40` bytes — one 4×4 previous-view matrix — from the active frustum at `+0x158` into a single
renderer-owned history object at `+0x80`, once per viewport call. Knowing that turned "temporal effects
look wrong in stereo" into a bounded change: split that one copy into left/right banks, seed on first
use, and reseed both on renderer replacement, recenter, or calibration change.*) Treat a pose gap of
several frames as a camera cut and reseed both banks, or the first frame after a hitch reintroduces the
artifact.

**But do not duplicate every extra buffer reflexively.** A multi-pass framebuffer *pair* is not
automatically a temporal history — most bloom/blur/SSR chains are ping-pong scratch that is fully
rewritten within the same frame, and duplicating those costs memory and can itself introduce eye-desync.
(*SOMAVR's first instinct was to duplicate ToneMapping's six bloom framebuffer/texture pairs alongside
the confirmed image-trail history; investigation showed the bright/blur passes fully rewrite all six
every frame — intra-frame scratch, not carried state — so duplication was correctly skipped.*) The test
that separates them is whether the resource is **read before it is written** within a frame. Prove it per
resource; there is no blanket rule.

**A history buffer is not the only thing that carries state across a frame boundary.** Post-effects
frequently keep one small mutable "this frame" packet — a phase counter, an adaptation value, a noise
seed — and advance it once per invocation. Render two eyes in one frame and it advances twice, so the
second eye silently gets a different phase.

(*SOMAVR hit this in two unrelated effects with an identical shape. Deferred SSAO advanced a global float
once per invocation and derived its temporal blur phase from it. Tone mapping advanced exposure,
white-cut, fade, colour grading and film-grain phase together in one packet. The fix was the same both
times: **capture the pre-update packet and the committed result before eye one, replay that same baseline
for eye two, then restore eye one's committed result** — so exactly one logical update persists per
frame.*)

The rule generalises past graphics: any per-frame mutable state touched by a pass you now run N times
needs either **one shared physical advance** or **one isolated copy per eye**. Neither happens by default,
and the symptom — a subtle per-eye difference in a noise or grain pattern — is easy to dismiss as
compression or imagination.

**A cheap way to classify per-eye vs shared without engine source:** hash each pass's bound
texture/framebuffer footprint and require *both* eyes to produce resources at the *same* nonzero pose
frame before calling a resource eye-distinct. Ordinary alternate-eye timing cannot satisfy that gate by
accident, so it separates genuine per-eye state from shared scratch by measurement rather than by
inspection.

**Triage rule:** find out early whether the target has TAA. A pre-TAA renderer (Rise of the Tomb Raider
ships FXAA/SSAA and *no* temporal AA) has almost no history to corrupt, and alternate-eye is far more
viable. A TAA-era engine (roughly 2016 onward) is much harder to alternate-eye, and pushes you toward
same-frame per-eye rendering or scene re-entry ([09](09-d3d11-openxr-injection.md),
[13](13-teardown-bioshock-vr.md)).

## A stereo-only artifact is infrastructure until proven content

The most expensive mistake in this chapter is reaching for the shader. When a defect appears in stereo and
never appeared flat, the odds strongly favour a **resource shared across eyes or frames** over authored
material logic that nobody complained about before.

(*SOMAVR proposed that a moving translucent-boundary artifact on windows and water was the authored
view-depth reflection fade — a plausible, correctly-named parameter in the shipped water shader. They
patched that exact program across 369 draws. The artifact was completely unchanged. **Falsified.** The
real cause was that world reflections sample a texture rendered from a mirrored frustum **shared across
alternate eyes** rather than regenerated per eye. An ownership bug, not shader maths.*)

The wrong mental model is *"a parameter with the right name is the cause."* Before touching shader logic,
answer one question: **is the suspect buffer per-eye or a singleton?**

There is a matching visual tell worth memorising. **Shading that moves with the eye instead of sticking to
the surface is a mono screen-space buffer being sampled per-eye.** (*BioshockVR's black-boulder artifact
was a shadow mask, generated once for the centre view, sampled with a UV derived from the now-per-eye
`worldViewProj` — so the black side tracked the eye shift.*) Geometry-shaped shading errors that swim as
you move your head are almost never a shading bug.

A related provenance trap: **fixing the primary colour pass does not move its downstream consumers.**
(*BioshockVR proved its private per-eye depth correctly held the controller-posed weapon while the game's
native centre depth still held the neutral desktop pose — and the shadow pass was sampling the stale
centre depth, producing a stationary cutout silhouette that read convincingly as a shader bug.*)
Post-process and lighting passes keep their own references to "the" depth or G-buffer; enumerate every
consumer, not just the producer you fixed.

## Scope the fix to the narrowest predicate that reproduces

Once you have found a genuine screen-space hazard, the temptation is to fix its whole class — every
indexed-primitive draw, every slot-2 sample, every draw of that buffer type. **This overshoots, and the
regression lands somewhere you weren't looking.**

(*BioshockVR did it twice. A blind full-slot-2 mono substitution regressed unrelated materials; the fix
that actually held required **both** `SlotMask=4` **and** `MinIndexCount=18000`, matching only the large
boulder draws. Separately, demoting an entire indexed-primitive draw family regressed boulder and chest
shading and worsened an unrelated hole artifact — reverted the same day. What held instead keyed on exact
shader-signature and resource-signature plus explicit index-count and slot-mask lists.*)

Coarse buckets — draw type, buffer size, route family — are shared by many shader and material
permutations, so a predicate keyed to the bucket mutates far more than the evidence supports. **Key
mutation predicates to the narrowest identity that reproduces in evidence**, and widen only when a new
case is actually proven. This is the same joint-key discipline chapter
[11](11-re-anchoring-and-discovery.md) requires before authorising any replay.

## There is no canonical G-buffer

"Find the G-buffer" is not a universal instruction, which is why this chapter classifies by *inputs*:

- **GTA V** — textbook deferred: 5 MRTs (diffuse, normal, specular, irradiance, depth-stencil).
- **DOOM 2016** — **clustered forward+**: lights binned into 3072 frustum clusters, and only *two thin*
  G-buffers (normal, specular). There is no fat material buffer to find. But SSAO, SSR and TAA are still
  screen-space, so **forward+ does not save you from class 2 or 3.**
- **Rise of the Tomb Raider** — a **tiled light pre-pass** that inverts the usual split: it stores
  *lighting* (three RGBA16F targets: diffuse, specular, ambient) rather than materials, and submits
  geometry twice.
- **RE Engine** — an unusually compact three-target G-buffer that packs **velocity, AO and an SSS mask**
  into a single RGBA16_SNORM.
- **Control** — largely replaces SSAO and SSR with **ray-traced GI and reflections**, then leans on a
  temporal denoiser. The screen-space hazard mostly moves from class 2 into class 3.

The lesson for injection: identify passes by *what they sample*, and expect the architecture to
contradict your assumptions.

## One global correction cannot serve draws with different projections {#depth-slice-residue}

bfbc2-vr measured something on Frostbite 1.5 that every engine with more than one projection per
frame will reproduce, and the numbers are large enough that it is worth checking for before you
start debugging tracking. `[SOURCE]`

A census of one outdoor frame: **670 of ~716 scene draws are drawn with a near plane of 7.48 m or
21.34 m; only 46 use 0.1 m.** Frostbite renders the view in **depth slices** for Z precision. The
view-projection constant the mod was correcting through carried only the 0.1 m projection.

Apply a global correction `VP-1 . r . VP` to a draw that has its own `P'`, and what actually reaches
the draw is `P' . P-1` sitting in front of `r`:

```
        [ 1  0  0      0    ]
        [ 0  1  0      0    ]
P'.P-1 =[ 0  0  1  (q'-q)/t ]
        [ 0  0  0    t'/t   ]
```

**Rotation about the eye passes through exactly. Every translation in `r` is multiplied by
`t'/t`** - which measured **75x** for the 7.48 m slice and **213x** for the 21.34 m slice. A 3.3 cm
eye offset became 2.5 m. A 10 cm lean moved the far world 7-21 m.

**That gives you a symptom you can read backwards.** "The world warps around me, but I can still
look around fine" is not a tracking bug and not an IPD bug - **rotation surviving while translation
explodes is the signature of a projection mismatch**, and the multiplier tells you which projection.
The bug had been present since stereo first lit up on that project.

The fix is per-draw: build the correction around **each draw's own recovered projection**,
`P_d-1 . C_view . P_d`. It is cheap, because distinct projections are few - about **four per frame**
- so cache by `P_d` and the cost is four inversions, not seven hundred. The global form is simply the
`P_d == P` special case, worth keeping as the fallback for writes whose projection cannot be
recovered. Their guard is worth copying too: the horizontal/vertical scale terms are snapped to the
world's when within 2%, so a non-rigid draw cannot leak into the field, while the depth terms are
always taken from the draw itself.

**Check for this whenever a frame contains more than one projection** - depth slices, a separate
viewmodel pass, a portal or mirror view, or a UI camera. The playbook's usual advice is that render
camera and cull camera are different things ([CAM-002](pattern-catalog.md#cam-002)); this is the
same lesson one level down, where *two draws in the same pass* do not share a projection either. See
[CAM-008](pattern-catalog.md#cam-008).

## Widening the projection does not widen the culling {#widen-vs-cull}

Same project, the wall the obvious approach hits. Told to render 2.6x/3.4x wider, the game produced
**gray void over most of the image**: the engine still culls against its own ~58x45 degree frustum,
so sky segments, terrain patches and trees beyond that cone are **never drawn**. `settings.ini
Fov=90` had no effect at all - the tangents were identical at 55 and 90. `[SOURCE]`

**A projection-matrix widen is not an FOV change; it is a request for geometry nobody submitted.**
To actually fill a headset field you have to make the engine itself render *and cull* wide, which
means finding its FOV value and holding it - the memory-patch track, not the matrix track. BioVRDev
reached the same conclusion on Unreal 2.5 ("the FOV reported to the runtime is kept in sync with what
the game actually renders"), and Crysis VR keeps the viewmodel's near FOV in step through
`EFQ_DrawNearFov`. Three projects, three engines, one rule.

The honest fallback while that track is open is what they shipped: **auto-widen off by default -
correct geometry in a theater window** beats a wide image with a void in it.

## A CPU visibility tracker that alternates per render is a stereo hazard {#cpu-visibility-history}

The hazard census looks for temporal effects in the *renderer*. This one is in the **culling**, it is
on the CPU, and it survives a per-call render-list clear — so a census that checks for TAA, SSR and
history buffers will report clean and still be wrong. `[SOURCE]`

SOMAVR found it in HPL2's released source while studying HPL3. `cRenderSettings` owns **one**
`cVisibleRCNodeTracker`, and its **two** node sets alternate on every call to
`CheckForVisibleObjectsAddToListAndRenderZ` via `SwitchAndClearVisibleNodeSet()`. With sequential eyes
sharing those settings:

- **eye zero reads the previous pair's eye-one set**;
- **eye one reads eye zero's current-pair set**.

That is asymmetric, cross-eye coherent-occlusion history *even though the render list itself is
cleared per call*. It presents exactly as the SS2VR symptom — geometry missing from one eye — and no
amount of frustum widening fixes it, because the frustum is not what is wrong.

**Two coupled histories, not one.** GPU occlusion-query results and this CPU tracker are separate
owners and either alone reproduces the symptom. The safe first native-stereo experiment must **bank
the tracker per eye, or disable coherent occlusion culling for both passes** — and the honest state
until then is *open, high risk*, which is how SOMAVR records it.

**Look for this shape rather than this symbol.** Any "visible set" that is double-buffered so this
frame can consult the last one is the same hazard under another name, and it is invisible to a
renderer-only census. Add it to [the catalogue of shared structures a second view must borrow](#the-catalogue-of-shared-engine-structures-a-second-view-must-borrow).

## Shadow cascades: one eye is the authority, the other reuses

Cascaded shadow maps are computed *from the view*, which makes them a per-eye quantity in the same way a
G-buffer is — except you almost never want two of them. Recomputing cascades per eye doubles a
significant cost and, worse, produces **subtly different shadow boundaries between the eyes**, which the
visual system reads as shimmer along every shadow edge.

The fix is an explicit authority rule, keyed by the stereo pair rather than by time:

```cpp
enum class AuthorityAction : uint8_t { Seed, Reuse, SameEye };

constexpr AuthorityAction decide_authority(
    bool slot_valid, uint64_t slot_pair, uint32_t slot_generation, uint32_t authority_eye,
    uint64_t incoming_pair, uint32_t incoming_generation, uint32_t incoming_eye)
{
    if (!slot_valid || slot_pair != incoming_pair || slot_generation != incoming_generation)
        return AuthorityAction::Seed;      // new pair: this eye computes and owns it
    return authority_eye == incoming_eye
        ? AuthorityAction::SameEye         // the owner again -- recompute is legitimate
        : AuthorityAction::Reuse;          // the other eye -- take the owner's cascades
}
```

(*Witcher 3 VR's `shadow_cascade_authority_policy.h`, applied at two call sites distinguished by return
address — see [11](11-re-anchoring-and-discovery.md).*)

Three details make it correct rather than merely cheaper. **The key is `(pair, generation)`, not a
timestamp** — a dropped or repeated frame must reseed rather than reuse stale cascades. **`SameEye` is a
distinct outcome from `Reuse`**, because the authority eye legitimately recomputing is not an error.
And the whole thing is a pure function with no engine types in it, so it is unit-testable away from the
game.

**The general rule:** any per-view resource that is *shared in effect but computed per view* — cascades,
reflection probes chosen by view, LOD selection, occlusion query results — needs an owner and a reuse
path, not two independent computations.

## The catalogue of shared engine structures a second view must borrow

[Shadow cascades](#shadow-cascades-one-eye-is-the-authority-the-other-reuses) are one instance of a
larger class, and the Cyberpunk 2077 port enumerated four of them together with the symptom each
produces when the second view rebuilds it from its own frustum instead of borrowing it:

| Shared structure | Symptom when rebuilt per view |
|---|---|
| **Sun cascade shadows** | Blinking shadows |
| **The shader clock** | Dead flags — time-driven effects stop or reset |
| **The foliage wind volume** | Jittering vegetation |
| **The reflection march** | A mirror-finish ceiling |

> All four are **lent from one view** now.

Four different visual bugs, one root cause, and **none of them looks like a stereo problem.** Blinking
shadows read as a shadow bug; jittering foliage reads as an animation bug; the mirror ceiling reads as a
material bug. That is what makes this class expensive — it scatters into four separate investigations
unless you know to ask *"is this per-view state that should be shared?"*

**The general test:** for any state the renderer derives from the view, ask whether it is *semantically*
per-view or merely *computed* per-view. A shadow cascade is computed from the view but should look
identical in both eyes. A wind volume and a shader clock are not view-dependent at all — they are frame
state that happens to be initialised during view setup.

**"Lent from one view" is the right implementation**, not "computed twice and hoped to match." Give the
structure an owner ([the authority pattern above](#shadow-cascades-one-eye-is-the-authority-the-other-reuses))
and have the second view take the owner's copy.

The same project's HUD decision belongs here as a deliberate counter-example: their engine HUD composite
is ported shader-for-shader to the second eye and pasted **at the same pixel in both eyes**, so markers
land in the same place — with finite-distance placement retained behind a setting because wide-FOV
headsets want it. **Same-pixel and world-placed are both legitimate; pick per element and say which.**

## Temporal upscalers need per-eye history, and a fail-closed fallback

TAAU, DLSS and DLAA all keep a **history buffer plus motion vectors**, and both are per-eye. Feeding one
eye's history to the other is the temporal trap in its most expensive form: it does not merely ghost, it
ghosts *differently in each eye*, which is far more uncomfortable than a symmetric artifact.

Modern engines make this tractable because the data already exists per view. (*Witcher 3 VR's TAAU path
"uses exact per-eye REDengine temporal-camera history and preserves the native combined camera, object,
skinning, foliage and cloth motion field" for both alternate-eye and strict-stereo modes.*)

**Note the shape of their optimisation, which is the transferable part:** the accepted path skips a
redundant legacy full-resolution motion-vector composition, *"while retaining that route as a
fail-closed fallback whenever exact eye/pair authority is unavailable."* The fast path is taken only
when the mod can prove it knows which eye and which pair it is in; otherwise it degrades to the slower
route that does not need to know. **An optimisation gated on an authority check, with the unoptimised
path kept alive, is how you make a temporal fast-path safe.**

Treat every upscaler as a separate compatibility mode to be validated on its own — that project's status
table lists no-AA, FXAA, TAAU, DLSS and DLAA as five independently "working" states, and ray tracing as
experimental on only two of them.

## Sub-resolution passes need per-eye company

Half- and quarter-resolution passes are everywhere (SSAO, bloom, particles, motion blur, volumetrics,
depth of field), and they are upsampled using **depth-aware filtering or stencil-marked discontinuities**
(Rise of the Tomb Raider does both). Two consequences:

- The upsample references a depth/stencil buffer. If you replay per eye, that buffer must be **the same
  eye's** or edges reconstruct against the wrong geometry.
- Sub-resolution buffers are cheap to duplicate, which makes them the *easy* half of per-eye producer
  work. Do them first when converting a pass to per-eye.

## Image-based and sky lighting is view-dependent, and it will not survive a second view

Add to the hazard classes: **any lighting term computed from the view** — screen-space reflections,
specular from an environment probe, sky/ambient lighting resolved in screen space, tiled light culling
keyed to the view frustum.

These do not merely look slightly wrong in the second eye. They are computed for *one* view and then
applied to a differently-projected image, so shiny surfaces reflect the wrong thing entirely.

(*BF2VR's fix history is the worked example. Reflections on shiny surfaces were broken; their first
attempt disabled `specularLightingEnable` **and** `csLightTileCsPathEnable` — two features — plus a magic
skybox constant (`skybox->mapping.y.z = 35; // Makes it not washed out`). The shipped fix replaced all
three with **one** setting: `skyLightingEnable = false`.*)

Two lessons, and the second is the more useful:

- **The engine's own settings booleans are the right lever.** They found `skyLightingEnable` at `+0x1E8`
  in a `WorldRenderSettings` class reached through a global pointer. That is the same idea as
  [18](18-beyond-the-native-injector.md)'s shader keywords: **before writing a draw classifier, look for
  the switch the developers already built.** A settings struct is easier to find and far safer to toggle
  than a per-draw predicate.
- **Narrow the fix until it is one predicate.** Two features plus a magic number became one boolean.
  [Scope the fix to the narrowest predicate that reproduces](#scope-the-fix-to-the-narrowest-predicate-that-reproduces)
  is easy to state and easy to skip when the broad version *works*; this is what doing it properly looks
  like.

## Discrete per-view choices cause rivalry, which is a different failure {#per-view-decisions}

The hazard classes above are about per-view *state*. There is a fourth thing a renderer does per view:
it makes **discrete choices** - which LOD to draw, whether to draw a billboard or a mesh, which
reflection probe to use, whether an occlusion query passed. Those fail differently, and worse.
`[SOURCE]`

Psychonauts VR's first head-tracked playtest found distant trees and bushes flickering and reading
**cross-eyed**. Two mechanisms, both from the eyes being given slightly different camera positions:

- **Orientation.** Each eye gets a billboard rotated to face *that* eye, so the two eyes see the card at
  different orientations. And the deeper problem: **a zero-thickness card at object depth has no correct
  stereo answer anyway.** Orienting it consistently for both eyes removes the disagreement but not the
  flatness - it is a picture of a tree at a single depth, and stereo will say so.
- **Selection.** Near the LOD switch distance **the two eyes can disagree** - one draws the sprite, the
  other the mesh, or the choice alternates frame to frame. The result is **binocular rivalry**: the
  visual system cannot fuse two different objects and alternates between them, which reads as flicker.

**Rivalry is not an artifact you can grade.** A wrong colour or a smeared edge is uncomfortable; two eyes
being shown different *objects* is unusable, and it does not average out with distance or resolution.

### Occlusion queries are the worked example, and they have a clean override

The sharpest instance of a per-view decision, because the mechanism is explicit and the fix is one
function. Singularity VR: the engine *"issues a `D3DQUERYTYPE_OCCLUSION` query per primitive, draws its
bounding box, reads the pixel count back, and **skips drawing that primitive on a later frame if it came
back zero**."* `[SOURCE]`

Under stereo that is a decision taken in one eye's view and applied to both - **and applied a frame
later**, so it survives whatever you did to the camera in between. Overriding `GetData` to report a
large count *"fixed every reported symptom at once"*, and the draw counters show the scale of what was
being lost: from about **1,000 draws per frame to a peak of 2,272-3,809**.

**The override is safe in the direction that matters.** Reporting "visible" *"can never wrongly delete
geometry, only fail to save work"* - so the failure mode is cost, not correctness. That asymmetry is
what makes it a reasonable first move, and their own note that it is nonetheless **brute force** is the
honest caveat: the proper fix is to give the query an owner and a reuse rule like any other per-view
decision.

**The fix is to make the decision once, for both eyes**, from a single reference view - the head centre,
or whichever eye you nominate. That is the [shared-value rule](#shipped-vr-hazards) applied to a choice
rather than to a scalar, and it costs nothing but consistency. Where the engine will not let you share
the decision, push the LOD switch distance out until both eyes are reliably on the same side of it.

Two related cases in this survey: IL-2's cloud and smoke billboards surfaced as
[stereo-only artifacts](15-teardown-il2-1946-vr.md), and Far Cry 2 hooks `SkyCommon` precisely because
it is camera-derived. **Enumerate every per-view decision the renderer makes, not only every per-view
buffer it writes.**

## When you rewrite the camera constant buffer, know which fields are history {#cbuffer-fields}

The chapter above says temporal passes read the previous frame. The practical corollary, from
SnowRunner-VR's hook, is that **the previous frame's matrix is sitting in the same constant buffer you
are about to rewrite** - and rewriting it is how you break every pass at once. `[SOURCE]`

Their comment, at the point of the write:

> **Leave `g_tmViewProjPrev` (`0xA0`) untouched** - overwriting it corrupts passes that read the
> previous-frame ViewProj (water/SSR/velocity) -> artifacts. **Move the world-space eye with it.**

Two rules fall out, and they pull in opposite directions:

- **Do not touch the history slot.** A `ViewProjPrev`, `PrevViewProj` or `LastFrameVP` is *data about
  the past*, not a second copy of the current camera. Rewriting it makes this frame's motion vectors
  read as zero - or worse, as the inter-eye offset - and the artifacts land in water, screen-space
  reflections and velocity-driven effects, which is exactly the set that is hardest to attribute.
- **Do touch the scalar eye position.** The same buffer usually carries the **world-space camera
  position** as its own field, read directly by passes that never multiply by the view matrix.
  Rewriting the matrices and leaving that behind gives you geometry in one place and lighting,
  fog or specular in another.

**Enumerate the buffer before writing any of it**: current matrices to rewrite, history to preserve,
and derived scalars to keep in step. A buffer dump with named offsets is worth the hour.

### A value you write can be interpolated after you write it

Same project, a second note worth pairing with
[the engine that would not hold a wide FOV](#forced-projection): *"the game lerps this eye downstream,
so the alternating +/-IPD/2 shakes"* - lean is slow enough to survive, but a per-eye offset that flips
sign every frame is exactly the input a smoothing filter destroys.

**Anything the engine smooths will smooth your alternation into a shake**, so an injection point is only
correct if it is *after* the last thing that filters the value. Their options are the general ones:
inject post-lerp, or disable the lerp.

## Force the projection in the matrix; demote the engine's FOV to culling {#forced-projection}

[The section above](#widen-vs-cull) leaves the FOV problem where bfbc2-vr left it: widening the
projection does not widen culling, so the real fix is engine-level, and the engine-level route was open.
Singularity VR closed it, and the answer is both halves at once. `[SOURCE]`

### First, stop lying to the compositor - and read the truth rather than asking for it

Their projection layer submitted the **headset's** FOV while the game rendered 65 degrees horizontal at
16:9. The consequence is worth stating precisely, because it explains why this class of bug survives so
long:

> Everything is stretched by one uniform factor, so head movement, world scale and object size are all
> wrong **together** - and nothing can be judged against anything else.

**A uniform error leaves no internal reference to notice it against.** That is why their 6-DOF scale
"could not be assessed by eye" and why bfbc2-vr's dead widen term
[invalidated weeks of in-headset judgement](06-debugging-methodology.md#dead-correction-term).

The fix for the first half is a technique worth stealing on its own: **read the frustum out of the
matrix instead of asking the engine what it is.** The x and y columns of a world-to-clip matrix are the
projection scales times unit world axes, so their lengths are the scales and `tan(halfFov)` is the
reciprocal.

> This needs no knowledge of whether UE3's `FOVAngle` is horizontal or vertical, or how it folds in
> aspect - **we never ask, we read what came out.** Same trick as the forward vector, third time it has
> paid off.

**Recover the value from the artifact, not from the engine's declared field.** A declared FOV has a
convention, an aspect policy and an interpolator between it and the pixels; the matrix has none of that
left in it.

### Ask the game to cover the headset - vertically

Truth alone gives you a small correct rectangle floating in black, so the game still has to render wide.
Write the FOV each frame - and write **every** copy the interpolator reads, or it drags the value back
(theirs needed `mCurrentPOV +0x0438`, `mDesiredPOV +0x0470` and `mCurrentFOV +0x0490`).

**Match the headset's vertical FOV, not its horizontal.** The game renders 16:9 while a per-eye view is
nearly square, so equal vertical FOV leaves the game's horizontal field comfortably wider than needed -
full coverage on both axes, with the surplus falling outside the eye. Matching horizontally leaves top
and bottom short, which is the visible half of the aspect mismatch.

**And this does not resurrect the culling problem**, because the request goes *through* the engine rather
than around it - the engine widens its own culling frustum to match.

### But the engine will not hold it, and asking more politely cannot fix that

Against a steady requested **127.9 degrees**, the matrix reported what the engine actually rendered:

```
125.3  127.2  125.1  123.8  128.7  124.4  126.1  125.4  124.0  124.0  ...  80.7
```

**The write works - this is not a clamp.** The camera update interpolates back toward its own default
every tick, with each step sized by frame duration, so the value drifts between your writes and one long
frame produced the `80.7` outlier. Both symptoms follow: a rendered FOV swinging 128 to 80 is a visible
zoom on the monitor, and submitting that narrower frustum leaves the vertical short - the black bars
flicking in and out top and bottom. *"The engine gets the last word before rendering."*

### The resolution: two owners, one number

**Set the frustum where nothing can argue - in the matrix, on its way to the GPU, on every upload.**
Rescaling the x and y columns is exactly a clip-space x/y scale, which is exactly an FOV change, and it
composes correctly after the positional offset.

The engine's own FOV then matters **only for CPU culling**, where being roughly right is fine. So ask it
for **15% more than you render with** and let it drift: the drift is harmless as long as it stays above
what you draw. Two owners, two jobs - the matrix owns what is rendered, the engine owns what is kept.

**Submit the forced constant to OpenXR too, not the observed value.** *"Following the observation was
the flicker: a submitted frustum that tracked the engine inherited every wobble. Forced and submitted
from one number, the two agree by construction."* See [CAM-010](pattern-catalog.md#cam-010).

Two notes from the same runs. Forcing runs every frame rather than only while 6-DOF is on, so a full
sliding scan cannot stay in the hot path - once the matrix is located, the hook checks only its window
(a bounds test plus one window test per covering call). And **CPU frustum culling turned out to be a
non-issue at stereo scale**, measured rather than feared.

### Measure in the game's frame, not through the headset

Their last discipline note on this work: the artifact they were judging lives in the backbuffer.
**Judging it through the HMD means judging it through the aspect mismatch and the lens distortion as
well - neither of which will exist in the finished mod.** Read the backbuffer directly when the thing
you are measuring is upstream of the optics.

## The hazards a shipped VR mode still got wrong {#shipped-vr-hazards}

Every other source in this chapter is a mod adding VR to a flat game. EDVR is different: it patches
*Elite Dangerous: Odyssey*, a game that **ships** VR. Its bug list is therefore the most useful
population in the survey - these are the hazards that survived a funded, official implementation, which
makes them the ones your mod is most likely to reproduce. `[SOURCE]`

**Per-eye auto-exposure is two eyes disagreeing about the world.** Elite meters scene brightness
separately per eye, so near a star or a floodlight one eye stops down and the other does not. Measured
on a held view of a star: about **1.5 stops apart** without the fix, **0.4** with it - and the residual
is correct, being the glow in the eye that can actually see the star. Generalise it: **any adaptive or
feedback process - exposure, eye adaptation, auto white balance, temporal accumulation of a scalar -
must be driven from one shared value across the eyes, not computed per eye.** It is not a
render-target problem, so it survives every check that looks at buffers. See
[STR-009](pattern-catalog.md#str-009).

**Culling narrower than rendering, the other way round.** [Widening the projection does not widen the
culling](#widen-vs-cull) was bfbc2-vr hitting this from the flat-to-VR side. Elite hits it natively:
over planets it **culls terrain against a narrower frustum than it renders**, so squares of ground at
the edge of view are never drawn - black tiles popping as you look around. EDVR's fix is the mirror
image of the usual one: **tell the game the headset shows a little more than it does, then hand the
compositor only the part you really see.** Cost measured at about **6% GPU** on a Quest 3. Render
frustum and cull frustum are separate in both directions, and the fix is to move whichever one is
smaller.

**A single wrong frame is worse than a missing one.** Once per supercruise transition Elite draws one
frame from the wrong viewpoint. On a monitor it is a blink; in a headset it is the world lurching.
EDVR's fix is to **spot that frame and not submit it**, so the compositor holds the previous frame.
**Not submitting is a legitimate correction** - reprojection makes a dropped frame cheap and a wrong
frame expensive. Keep it in the toolbox next to fixing the frame. See
[STR-010](pattern-catalog.md#str-010).

**Anything sampled in screen space becomes head-locked.** Elite's loading-screen ship hologram carries a
faint scan pattern synthesized from the model's depth and **sampled in screen space**. A monitor can
never show it moving; a headset always does, and it is nauseating if you focus on it. The same applies
to their star glare, which rides the head rather than staying with the star. **Screen-space sampling is
invisible on a monitor and load-bearing in a headset** - dither, noise, scanlines, glare, veiling,
lens-flare placement. Audit every effect whose input is a screen coordinate.

**A both-edges overlay stamped identically into both eyes lands on your nose.** Elite's RemLok helmet
draws its edge lines with no per-eye placement, so the lines that should sit at your temples end up in
the middle of view. Any 2D overlay authored for one screen needs **per-eye placement, not per-eye
copies**; EDVR clips each eye to the line on its own outward side.

Two process details worth stealing regardless of engine: each fix is **measured** (1.5 stops to 0.4;
6% GPU) rather than asserted, and each is **individually switchable back to stock**, so a user or a
maintainer can attribute a regression to exactly one change.

## What to disable outright

Some passes exist to simulate a *camera*, and a headset is not a camera. These are usually one config or
cvar away and improve both comfort and performance:

- **Lens distortion, chromatic aberration, vignette, film grain** — the HMD applies its own optics;
  these read as smeared dirt and fight the compositor's own distortion.
- **Motion blur** — already flagged in [09](09-d3d11-openxr-injection.md); it reads as stereo echo on any
  alternate-eye or reprojected pipeline.
- **Depth of field** — your eyes accommodate; a forced focal plane causes eye strain.
- **Fullscreen colour/lens flare effects keyed to screen centre** — the centre of a headset image is not
  where you are looking.

## The classifier, as code

The atlas is a lookup table; this is the predicate that uses it. The ordering matters — cheap
structural tests first, and the *live* pipeline query before anything that depends on shader identity:

```cpp
enum PassKind { PASS_SCENE, PASS_SHADOW, PASS_POST, PASS_UI, PASS_TEMPORAL, PASS_UNKNOWN };

PassKind ClassifyDraw(ID3D11DeviceContext* ctx, const DrawInfo& d)
{
    /* Query LIVE, at draw time. A cache built at shader-creation time reports
       "PS is null" for anything created before injection, and D3D11 RETAINS
       stage bindings across draws -- so a depth-only draw carries a stale PS
       it never samples. Both mis-classify. */
    Microsoft::WRL::ComPtr<ID3D11PixelShader> ps;
    ctx->PSGetShader(&ps, nullptr, nullptr);

    Microsoft::WRL::ComPtr<ID3D11DepthStencilView> dsv;
    Microsoft::WRL::ComPtr<ID3D11RenderTargetView> rtv[8];
    ctx->OMGetRenderTargets(8, &rtv[0], &dsv);

    const bool hasColor = rtv[0] != nullptr;
    const bool hasDepth = dsv    != nullptr;

    /* Shadow: depth-bound, no colour, and a square-ish non-backbuffer target. */
    if (hasDepth && !hasColor)                       return PASS_SHADOW;

    /* UI/HUD: orthographic projection is the reliable tell, not the shader.
       m[11]==0 && m[15]==1 means w is constant -- no perspective divide. */
    if (d.projValid && std::fabs(d.proj.m[11]) < 1e-6f
                    && std::fabs(d.proj.m[15] - 1.f) < 1e-6f)
                                                     return PASS_UI;

    /* Post/temporal: full-screen triangle or quad, depth test off, and it SAMPLES
       the previous frame. The last clause is what separates TAA/motion blur
       (per-eye history required) from a stateless tonemap (safe to share). */
    const bool fullscreen = (d.vertexCount == 3 || d.vertexCount == 4) && !d.depthEnabled;
    if (fullscreen && d.samplesPrevFrameTarget)      return PASS_TEMPORAL;
    if (fullscreen)                                  return PASS_POST;

    if (hasColor && hasDepth && d.vertexCount > 4)   return PASS_SCENE;
    return PASS_UNKNOWN;
}
```

**`PASS_UNKNOWN` must stay in the enum and must be handled explicitly.** Folding unknowns into
`PASS_SCENE` is how a temporal pass gets stereo-duplicated and produces the ghosting in
[The temporal trap](#the-temporal-trap-in-detail); folding them into `PASS_POST` silently drops geometry.
Log the unknowns with their draw index and go look at three of them in a capture — the class you are
missing is usually one predicate away.

**Order is load-bearing.** The orthographic test must precede the full-screen test, because a full-screen
UI quad satisfies both and the UI answer is the correct one.

## Using this atlas on a capture

1. Dump a frame ([06](06-debugging-methodology.md) — an in-process inspector beats a capture tool on a
   32-bit target).
2. For each pass, ask **what it samples**: geometry only? depth? the previous frame? a screen-space
   buffer? That answer alone assigns the hazard class.
3. Count how many class-2 and class-3 passes exist. That number *is* your per-draw stereo effort
   estimate — and if it is large, it is the argument for scene re-entry instead
   ([09](09-d3d11-openxr-injection.md)).
4. Kill class 5 immediately; it is free.
5. Do sub-resolution (class 4) producers early — they are the cheapest per-eye conversions.
