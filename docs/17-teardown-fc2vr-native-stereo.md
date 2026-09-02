# Native stereo: two engines, two routes to rendering the world twice

Two independent mods that reached the top rung of the stereo ladder, on two engines, from opposite
starting positions:

- **[FEAR VR](https://github.com/DR-89/fear-vr)** (LithTech Jupiter EX, D3D9, 32-bit) — **open source**,
  with an official SDK available. Read from source and its German-language design docs
  (`STEREO-RESEARCH.md`, `ARCHITECTURE.md`, `COORDINATE-SYSTEM.md`, `BUILD-GAMECLIENT.md`,
  `RETAIL-ACTIVATION.md`).
- **FC2VR v1.0.1R4** (Dunia / Far Cry 2, D3D9, 32-bit) — **binaries only**, no SDK, no source. Read from
  the distributed test build's own documentation: `PATCH_AUDIT.txt`, `DUNIA_PORT_MAP.txt`,
  `STATIC_VALIDATION.txt` and the `R2`/`R3`/`R4` causal-evidence files.

They are worth reading together because they converged on the same architecture and the same failure
modes from very different information. FEAR VR shows what the reasoning looks like when you can read the
engine's source; FC2VR shows the same destination reached with nothing but a disassembler and
discipline. The FC2VR bridge exports are prefixed `FearVr_`, so the transport layer is very likely
shared between them — which is itself the architectural lesson in
[§ The three layers](#the-three-layers).

**Why this earns a chapter.** Every stereo strategy elsewhere in this playbook works *downstream* of the
engine's camera: patch the matrices per draw, replay the draw stream, or alternate eyes across frames.
Both of these do something else. They call **the engine's own world-render a second time per frame**,
with the camera moved to the other eye, and capture what comes out. The engine renders the scene twice
because it genuinely believes it is rendering two views — so culling, LOD, sky and fog are correct per
eye for free, which is exactly what downstream approaches cannot buy at any price.

That is the top rung of the stereo ladder, and these are the playbook's first worked examples of it —
both achieved on 2005–2008 D3D9 titles with no OpenXR binding of their own. Age is not the barrier.

> **What this chapter is based on.** For FEAR VR: source and its design docs. For FC2VR: shipped
> binaries and the author's own documentation — **not** source; its architecture, patch sites, RVAs and
> causal chain are quoted from those files, and inference is labelled as such.

---

## The repeat-render search gains a fourth engine, and a stronger result {#repeat-render-fourth}

The chapter says looking for a repeat world-render the engine already performs *"should be your first
move."* A fourth project applied it and it answered their largest open risk **from one capture, with no
code written**. `[LIVE]`

**The Sims 4 renders mirror reflections as a full scene render from a second, independently positioned
camera, in stock gameplay.** Add to the table:

| Engine | The engine's own repeat render | How found |
|---|---|---|
| **Sims 4** | **a bathroom mirror** | **deliberately staged capture** |

**"Stage the scene on purpose" belongs in the how-found column.** A mirror is a two-minute setup in any
game that has one, and it is the cheapest rung-1 evidence available - the other three engines found
theirs while chasing something else.

**And the chapter's own caveat did not hold here, which is the better news.** It warns that repeat
renders *"often use a reduced pass set; treat it as proof, not automatically the vehicle."* For this
target it is **not reduced**: comparing the *same mesh* in the main view and in the reflection reports
**only the event id as different** - same shaders, same blend, depth, stencil and rasterizer state, same
render targets, same bound resources.

> The reflection is **the identical code path with a different camera constant.**

That changes the shape of the mod: there is no separate reflection path to reconstruct.

**And the seam is a single constant-buffer write:**

| Event | What |
|---|---|
| 8317 | last draw of the main view |
| **8335** | **one CPU write to the 160-byte camera constant buffer** |
| 8355-11268 | the whole reflection pass, ~250 draws, all reading that write |

To render its world from somewhere else, this engine writes **one constant buffer**. That is the smallest
possible form of the smallest-safe-hook principle.

## Re-entering the frame renderer twice per frame is temporally CLEAN on UE2.5 {#ue25-double-draw-timing}

The standing worry about double-draw stereo is that the two eyes see two different moments. On UE2.5 that
is now **measured rather than assumed**. `[LIVE]`

Taken from the engine's own camera arguments *before* the mod's code touches them: **0 divergences across
5,949 frames** - position, rotation and FOV all exactly zero between the two passes.

Scope the result to UE2.5, but the **measurement is portable and cheap**: log the engine's camera
arguments at the top of each pass and difference them. If the engine rebuilds its camera between passes
you will see it immediately; if it does not, you have retired a risk that otherwise sits open for the
life of the project.

## Rule out object-level mirroring from what the format can EXPRESS {#instance-format-expressiveness}

Finding a second camera-ish transform is not the same as finding a second **camera**. A mirrored
*object* - a reflected copy drawn with the same camera - also produces different clip coordinates, and
**both hypotheses predict "props that appear in no other pass."** `[SOURCE]`

The usual discriminator is the sign of the reflected transform's determinant. On one target that was
unreadable, because the per-instance record is not a plain 4x4. **The better move is to ask what the
per-instance stream can express at all.** Disassembling the vertex shader showed the instance data is:

- `v2.xyz` - translation
- `v3.x`, `v3.z` - **yaw as `(cos, sin)`**
- uniform scale from a constant buffer

applied as a literal 2D rotation:

```
mul r0.xz, v3.xxzx, l(1.0, 0.0, -1.0, 0.0)   ; ( cos, -sin)
dp2 r1.x, r1.xwxx, r0.xzxx                    ; x' = x*cos - z*sin
dp2 r1.z, r1.wxww, v3.xzxx                    ; z' = x*sin + z*cos
```

A `(cos, sin)` yaw with a positive uniform scale is a **proper rigid transform by construction -
determinant +1**. There is no slot for a reflection, a mirror flag, or a third basis vector, so **a
mirrored object is not representable in this format.** The mirroring cannot be in the object, and the
only remaining place is the camera.

> **Ask what a parameterisation is *capable of* before trying to measure it.** A compressed instance
> format - position + quaternion, position + yaw, position + euler - usually cannot express a reflection
> at all, which settles the question **structurally, and costs one disassembly.**



## A shipped rung-2 splice, read from its own commit history {#dishonored-splice}

`Dishonored-VR` (GingasVRFO) is a `d3d9.dll` proxy over a **forked DXVK** that reached full stereo,
6DoF with lean, roomscale through the game's own collision, motion controls on Arkane's animation rig,
per-eye shadows and sunshafts - on **UE3/D3D9**. It is discontinued and its author explicitly invites a
pickup. Its **52 numbered fork-patches are a complete rung-2 development history**, and the sequence is
worth more than any single patch. `[SOURCE]`

**Status, 2026-09-02:** the in-house DishonoredVR project has **already mined this** and moved past it -
it has stereo work under way on the render path and has avoided the blockers recorded below. Read this
section for the *method* and the negative results, not as an outstanding task.

### The real payload is the research log, not the patches - and mind the licence

**`dllmain.cpp` is about 23,000 lines of in-game research log**, and a sibling project that mined it
calls it *"the richest source of measured UE3/Dishonored runtime facts we have found anywhere."* Their
verdict is the one to carry:

> **Its negative results are worth more than its code.**

**Licence boundary, checked rather than assumed.** The repository `LICENSE` is **DXVK's zlib**, which
cleanly covers `fork-patches/` and says **nothing** about their own `dllmain.cpp`. The workable position
is the one that project took: **use documented facts - addresses, offsets, outcomes, things that did not
work - and none of their source.** That is the same
[layout-knowledge-not-source-text rule](00-engine-profiles.md#local-engine-sources) that governs an
engine tree, applied to a sibling mod.

### The natural experiment this repository completes {#dishonored-hook-site-ab}

Their head-look is driven through **script-level `ProcessViewRotation`** - precisely the hook site
[HOOK-006](pattern-catalog.md#hook-006) exists to warn against. The in-house DishonoredVR project took
the **render** path instead, hooking `eventGetPlayerViewPoint` gated to the render caller, and the two
outcomes on **the same game** are the cleanest comparison in this corpus: `[LIVE]`

| | script path (`ProcessViewRotation`) | render path (`eventGetPlayerViewPoint`, gated) |
|---|---|---|
| head-look in gameplay | yes | yes |
| **head-look in cutscenes** | **no** - shipped as a known issue, "cameras are fixed" | **yes** - measured twice |
| **roll** | **cannot express it at all** (mouse-delta), recorded as absent by design | **yes** - 27 degrees |
| across a checkpoint that re-creates the PlayerController | - | kept applying |

The cutscene result was confirmed in a dialogue cinematic with **letterbox and subtitles unchanged and
the NPC swinging out of frame**, and again with a **27-degree roll composited onto a moving, scripted
camera panning along its own path**. A 22-degree yaw was verified by frame capture *and* by the person at
the screen.

**This is not a prediction any more.** Two mods, one game, two hook sites, opposite results - which is
about as controlled as evidence gets in this domain, and it is why
[hook the path that must run for a frame to exist](11-re-anchoring-and-discovery.md#hook-the-render-path)
is stated as a rule rather than a preference.

**And the render path has a named cost.** With the view offset, the first-person weapon and arms sit at
the wrong angle, because **the FP mesh anchors to the unmodified view** - the sibling names it
*"decoupling the FP mesh from the head (per-draw `LocalToWorld`)"*. **Any project taking this route will
hit it**, so budget for it rather than discovering it.

### The order is the lesson

| Phase | What |
|---|---|
| **M2** | frame-map instrumentation - *before any stereo at all* |
| M3 | stereo splice v1, per-eye draw replay |
| M3.2 -> M3.3 | world-quad splice by a **`c6` identity test**, then **depth-test state replaces that heuristic** |
| **M3.4** | **revert to proven M3.1** |
| M3.5 | **measured gates** replace the remaining heuristics |
| M3.6 - M3.8 | export live projection scales; live-writable separation and convergence; **on-demand per-draw splice verdict dump** |
| M4.3 - M4.9 | render-target twinning |
| M5.1 | frame-sequential, one whole eye per frame |
| M5.3 - M5.8 | light shafts, then modulated shadow projection, per eye |
| M6.7 | **live draw-class kill mask - "the artifact bisector"** |
| M7.0 - M8.4 | per-eye pixel-shader `ViewProjectionMatrix` shear, gated to additive draws |

Two things stand out. **Instrumentation is interleaved, not front-loaded** - a frame map at M2, a
per-draw verdict dump at M3.8, a full pixel-shader census at M5.5, a shadow-splice census at M6.2. And
**a heuristic that loses to a measurement is reverted, in public**: M3.3 replaced the `c6` test with
depth-test state, M3.4 went back to the proven behaviour, and M3.5 replaced the guesswork with measured
gates. The last commit in the series is also a revert.

### The `UP` path is a second draw path, and it carries world-space effects

`DrawPrimitiveUP` / `DrawIndexedPrimitiveUP` take vertices from a **user pointer**, bypassing vertex
buffers entirely. A splice built around bound vertex buffers **misses them completely and silently** -
and they are not decoration: this project's M3.10 is titled *"splice world-space UP effects - the fire
fix."*

**Enumerate both paths before believing a draw census**, and log verdicts for the UP path separately
(M3.9 exists only because the first verdict log ignored it).

### Twin the targets, and twin the right things

The M4 series is a complete recipe for per-eye render targets in a D3D9 injector, and each step is a
correction of the previous one:

- allocate a **right-eye twin for every full-size render target**;
- twin **textures, not surfaces**;
- **twin the depth buffers too**;
- **mirror `Clear` into both** colour and depth twins;
- restrict twinning to **viewport-derived targets** rather than everything;
- render **each eye at full size** into its twin.

### Recognise a FAMILY by its constants, not a shader id

Shadow work needed *"recognize the shadow projection **family** by constant"* and *"shadow-**only**
variants"*, with **per-shader stereo metadata stored on the shader object** rather than in a side table.
A per-id list is brittle across builds and grows without bound; a constant-signature test is stable and
self-describing.

**And their id map hit a silent cap** - M7.2 raises it from 2048 to 8192 because *"the cap silently"*
truncated. Same shape as
[a census supporting a negative claim](06-debugging-methodology.md#negative-claims-exhaustive): a
container that fills quietly turns a complete answer into a partial one with no error.

**One more, cheap:** clip a spliced region with the **scissor**, not the viewport (M5.4). A viewport
change moves the projection; a scissor only restricts what is written.

## Alternate-eye: carry the eye identity with the frame, never wait for it {#carry-eye-identity}

A technique that took one project's per-eye refresh from **~11 Hz to ~45 Hz** - slideshow to usable.
`[LIVE]`

**The naive version, and a reasonable first implementation:** identify which eye is on screen by *asking
and waiting* - set an eye lock, hold it N frames so the game thread's camera edit can reach the render
thread, then take the image. Correct and unambiguous. **But the wait is the entire cost**: a full
left-right cycle takes `2N` frames, so at N=4 and 90 fps each eye refreshes at about **11 Hz**.

**The insight: a game/render thread split *delays* work but does not *reorder* it.** The camera built for
frame N is rendered before the camera built for frame N+1. So the eye never needs to be waited for -
only **carried**. The game thread pushes the eye it just built onto a small lock-free ring; the render
thread pops one per finished frame. Identity is exact, every rendered frame updates an eye, and a pair
completes every **2** frames.

**Make the ordering assumption measurable.** Pushes minus pops is the pipeline depth in frames and should
sit at a small constant; **drift means the 1:1 correspondence has broken and eye identity is no longer
trustworthy.** Export that lag plus starved and dropped counts. Measured live: **lag 0-1 across 30,833
frames, 0 dropped.**

**Verify it off-headset first**, because the failure mode is swapped eyes and that is miserable to
diagnose while wearing one. With nothing consuming the queue, lag equals the publish count, so comparing
lag growth against rendered-frame growth directly tests whether the camera hook fires more than once per
frame: **1.0019 publishes per rendered frame over 514 frames.**

See [STR-012](pattern-catalog.md#str-012).

## CryEngine traverses once and submits twice - so doubling the traversal is the wrong seam {#cryengine-single-traversal}

Read from Crytek's own source and corroborated by three failed attempts. `[SOURCE]`

`CD3DStereoRenderer::RenderScene` **traverses the scene once and submits twice.** That identifies a whole
class of attempt as being at the wrong seam: calling the render path twice per frame is *not* what the
engine does, and PreyVR's attempts to do it failed consistently -

| Attempt | Result |
|---|---|
| second pass, secondary-pass flag **off** | the engine leaks and dies within **13-19 frames** |
| flag **on** | the pass survives but costs only **~7% of a frame** - it is hollow |
| flag on **plus a real per-eye camera** | crash |

**A second pass that is cheap is not a second pass.** The 7% figure is the diagnostic: a genuine world
render costs what the first one costs, so a cheap "second render" is doing almost nothing and the seam is
wrong.


## The three layers

| Layer | File | Scope | Rebuilt per… |
|---|---|---|---|
| **Outer** | `d3d9_gog.dll` / `d3d9_uplay.dll` | Engine-specific. Knows Dunia's renderer vtable, camera functions, sky path. Exports `Direct3DCreate9`. | **Game build** |
| **Bridge** | `d3d9_fc2vr.dll` | Game-agnostic transport. Exports `FearVr_BeginEye`, `FearVr_CaptureEye`, `FearVr_GetRenderRequest`, `FearVr_SetStereoEnabled`, `FearVr_SetRenderScalePercent`. Shared-memory eye slots. | **Never** (reused across games) |
| **Host** | `fc2vr-host.exe` + `openxr_loader.dll` | 64-bit OpenXR process. Reads eye slots, submits composition layers. | **Never** |

The seam that matters: **only the outer knows the game.** Two of the three layers are the same code the
author had already written for a different title. When Ubisoft Connect and Steam turned out to need
different Dunia offsets than GOG, the fix was a second *outer* — 66 KB — against an unchanged 1 MB
bridge and unchanged host.

That is the reusable architectural claim, and it is worth taking seriously before starting a fourth
project in this fleet: **the engine-specific surface of a VR mod is much smaller than it looks, if you
draw the line in the right place.** Everything about OpenXR, pose handling, shared memory, layer
submission and comfort modes is game-independent.

## What "native stereo" actually means here

The outer hooks Dunia at these seams (GOG RVAs; the Uplay/Steam column is in
[§ Porting across store builds](#porting-across-store-builds-a-method-worth-copying)):

```text
Renderer vtable      00DBD7BC
  Prepare slot       00DBD7D0  ->  PrepareFrameGraph   00339420
  WorldExec slot     00DBD7D4  ->  WorldExec           00334730
CameraCopy           00359D30   (called from 3 sites: 0035AA52, 0035AAFB, 0035AD9E)
ViewBuilder          0036B080   (called from      0035A6A2)
CameraRebuild        003FE960   (direct callers: see the caution below)
SkyCommon            0036C190   (called from      0033AA79)
```

The per-frame shape, as the event stream names it:

```text
CAMERA_C45                <- stock primary camera for this frame
NATIVE_VIEW_BEGIN flags=1 <- claim the engine's camera, set it to the LEFT eye pose
  (engine's own CameraRebuild + ViewBuilder run for that pose)
NATIVE_VIEW_END   flags=1
LEFT_GEOMETRY             <- capture
XR_LEFT
NATIVE_VIEW_BEGIN flags=0 <- same again for RIGHT
...
XR_PAIR                   <- both eyes present and coherent: publish
```

**Why this beats patching matrices.** The second view is built by `CameraRebuild` and `ViewBuilder` —
the engine's own functions — so everything derived from the camera follows automatically: frustum
culling, LOD selection, sky (`SkyCommon` is hooked precisely because it is camera-derived), fog, and
whatever else Dunia hangs off the view. A hand-written matrix injected downstream gets the geometry
right and silently leaves all of that on the first eye's values.

The cost is that you are **borrowing a live engine's camera mid-frame and must give it back exactly**.
Every hard problem below comes from that one fact.

### …and that cost is not universal. Check how the camera reaches the renderer first {#camera-delivery}

SS2VR made the correction that reframes this whole chapter: **rung 1 is a spectrum, not a yes/no.** What
decides where a target sits is not only *can you call the world render twice*, but **how the camera gets
in**:

| Camera reaches the renderer as… | What you must do | Which bugs below apply |
|---|---|---|
| **A global you overwrite** (FEAR, Far Cry 2) | Borrow it, restore it exactly, and freeze everything that observes it | **All of them** — R1 restore, R2 contamination, R4 validator |
| **A parameter / by-value argument** (KEX, CryEngine) | Build a second camera and pass it | **None of that family** — there is no shared state to corrupt |
| **A parameter across a documented module boundary** (id Tech 2 / Quake 2) | Build a second `refdef_t` and call `RenderFrame` twice | **None of that family**, and the contract is GPL - see [the id Tech family](00-engine-profiles.md#id-tech-family) |

*(SS2VR: KEX's camera is a parameter, not a global — `Kex_RenderFrame` builds it on its own stack and
passes it by pointer. PreyVR: `CreateGeneralPassRenderingInfo(const CCamera&, …)` takes an arbitrary
camera, and `CRenderView::SetCamera` copies **by value**.)*

**Every one of FC2VR's four shipped revisions exists only because they mutate shared state.** Where the
camera is already a parameter, that entire bug family is designed out rather than defended against —
and the snapshot/restore machinery this chapter describes is work you do not have to do.

PreyVR's version of the check is the practical one: **`CRenderView::SetCamera` copies by value, so no
downstream reader can observe your transient camera at all.** That is visible from the function prologue
in one look. **Do it before prescribing yourself a restore-and-freeze architecture.**

**And this axis is not specific to rung 1 — it applies to whatever rung you are already on.** SOMAVR
made the point against their own shipping code: HPL2's `iRenderer::Render(afFrameTime, cFrustum* apFrustum, …)`
takes the frustum as a **parameter**, assigning `mpCurrentFrustum` from the argument at the top of every
render call — the good column. But *their own AFR path* mutates the live frustum in place via
`ApplyStereoEye(frustum, …)`, which puts the mod itself in the bad column:

> That is why this project has `RestoreBaseView`, base-matrix latching and `pairRotationValid` — and it
> is why F-19 and F-20 happened this week. A transient fault clearing persistent stereo mode, and a held
> pair carrying the wrong pose: both are the FC2VR family, hit independently, same root cause of
> borrowing shared state.

**So the argument for climbing to rung 1 is not only per-eye correctness — it can be that rung 1 retires
a defect class you are already paying for.** If your alternate-eye or replay path mutates a camera or
frustum that the engine hands around as a parameter, you have *introduced* the shared-state problem that
the engine did not have. Check which column your own code is in before you check the engine's.

One tidy consequence, from the same project: an engine-honoured override pointer
([11](11-re-anchoring-and-discovery.md)) and a by-value parameter are the same idea at different
addresses — *you hunt for an override when the camera is a global you would otherwise fight; where it is
already a parameter, passing a different one **is** the override.*

---

## FEAR VR: the definition, and how to find the hook

FC2VR shows *that* it works. FEAR VR writes down *what the thing actually is*, and its definition is the
one to carry to a new engine.

### Render the world twice; render everything else exactly once {#side-effect-gate}

The frame flow, from `STEREO-RESEARCH.md` §2:

```text
1. Read the current XR render request, immediately before rendering
2. Save the original camera pose and FOV
3. Apply the LEFT eye pose relative to the calibrated origin
4. Render ONLY the 3D world for left, and capture it through the bridge
5. Apply the RIGHT eye pose
6. Render ONLY the 3D world for right, and capture
7. Restore the camera
8. Render HUD and menus EXACTLY ONCE
9. Present EXACTLY ONCE
```

Steps 8 and 9 are the ones people get wrong. **Native stereo is not "run the frame twice."** It is
"run the *world render* twice and everything else once" — and the gap between those two sentences is
the entire engineering problem.

Which gives the acceptance gate, and it is a gate about **side effects, not pixels** (§3):

> Prove from source **and** runtime test that the second `RenderCamera` call executes **no** simulation,
> AI, sound events, particle ageing, or input a second time.

That is the correct definition of done, and it is not something you can eyeball in a headset. A build
that looks perfect while double-ageing particles and double-firing sound events is not native stereo —
it is a game running at half speed with a stereo-shaped bug. Write the gate as a side-effect assertion
before you write the hook.

**That list is incomplete.** Everything in it is a double-*tick* hazard — something advancing twice.
There is a second, quieter class:

> **Resource starvation of the second eye.** State sized or scoped for one world pass is exhausted, or
> collides with itself, partway through the second.

It does not present as anything doubling. It presents as **geometry quietly missing in one eye** — which
reads like a culling bug and sends you looking in entirely the wrong place.

### And a third class: what gets overwritten between write and read

SOMAVR's main agent found a case that **both** of the above miss, and it is a genuinely separate hazard.

HPL performs partial `glCopyTexSubImage2D` rectangles immediately before refractive translucent draws —
copying scene colour into **shared texture storage** that the translucent shader then samples, alongside
scene depth, with camera and inverse-camera matrices arriving through a UBO. (Matches released HPL2's
per-object refraction copy; D3D targets have it identically via a `CopyResource` or
`ResolveSubresource` into a scene-colour SRV.)

> **"What advances twice" misses it — nothing advances. "What runs out" misses it — nothing is
> exhausted. It fails only because eye B's copy overwrites the storage eye A's translucent draws are
> about to read.**

**The rule:** a valid native-stereo transaction must **render, copy and consume any per-object scratch
sequentially per eye.** Duplicating the opaque world pass alone is not sufficient. Any engine doing
grab-pass, refraction or distortion against a shared scene-colour copy has this.

So the gate is **three** questions, not two:

1. **What advances twice?** — simulation, AI, audio, particle ageing, input.
2. **What runs out?** — arenas, pools, and cross-frame state keyed by an identity two eyes now share.
3. **What gets overwritten between write and read?** — grab-pass scratch, refraction copies, any
   shared buffer written then sampled within a pass.

**Their occlusion-query finding is now concrete too**, and it sharpens (2). The vanilla apitrace baseline
shows HPL polling query IDs `1..4` and **immediately reusing the same IDs** for new work — 14,828
begin/end pairs across the trace. So the hazard is not "queries span frames" in the abstract: it is a
**tiny pooled ID set with immediate reuse**, which means a second world render can *collide on an ID
while the first render's result is still outstanding*. Their 0.92 instrumentation tags begin/end/result
traffic by first/replay eye and reports same-frame ID reuse, target conflicts, unmatched ends and
bounded-state overflow — observation only, altering neither results nor ownership.

> **A correction they volunteered.** They had earlier written that an arena audit "came back mostly
> clean" because the deferred light batch buffer starves both eyes equally. The batch-buffer claim
> holds; the generalisation did not. The refraction copy is the counterexample — a shared fixed resource
> where the second eye genuinely damages the first. Do not carry "mostly clean" forward from an audit
> that only looked for exhaustion.

**A worked example of getting this wrong, in both directions.** SS2VR originally flagged a per-frame
clip-node arena (`ClipAlloc`) as a potential blocker for KEX, and this chapter recorded it. On
investigation **they withdrew it**: the flag they had read as a per-frame latch has two xrefs, both
inside the allocator, and nothing ever clears it — it is a **process-lifetime one-shot**, i.e. lazy
init on first call. The pool is balanced by paired alloc/free, so peak usage is **per-pass, not
cumulative**, and two sequential eye passes are fine.

Their own registry entry was wrong, and the correction is recorded here because the *shape* of the
mistake is instructive: **a one-shot init flag and a per-frame reset latch look identical at the call
site.** Distinguish them by asking who clears the flag — if nobody does, it is initialisation.

**The category survives the retraction**, because a second project found it productive as a *search
prompt* rather than as a specific bug. SOMAVR audited HPL3 for it and cleared the obvious candidates —
the render list clears per call; the 100-light deferred batch buffer is per-pass scratch, so an
over-budget scene starves *both* eyes equally, which is a pre-existing cap and not a stereo asymmetry.
What the audit did surface was **occlusion queries, which span frames and are keyed by source pointer**.
That is the real shape of "what runs out": not an arena that fills, but **cross-frame state keyed by an
identity that two eye passes now share**. It is now the highest-value thing they plan to instrument, and
a failure there would present exactly as the symptom above.

### Rung 2 at the command-buffer level — and validate before you replay

Between "call the world render again" (rung 1) and "patch each draw" sits a middle route worth naming:
**capture the renderer's own command buffer for the frame, then replay it for the second eye.**

JKXR added exactly this to OpenJK's GLES backend in 2026. The shape:

```c
typedef union {
    void *align;
    byte  cmds[MAX_RENDER_COMMANDS + sizeof(int) + sizeof(void *)];
} vrStereoReplayBuffer_t;

static vrStereoReplayBuffer_t vrStereoReplayCommands;   /* the captured list  */
static vrStereoReplayBuffer_t vrStereoReplayScratch;    /* replay workspace   */
static int      vrStereoReplayCommandBytes;
static qboolean vrStereoReplayActive;
static qboolean vrStereoReplayLoggedInvalid;            /* log once, not per frame */
```

This is cheaper than rung 1 — one scene traversal, one command list, two submissions — and unlike
per-draw patching it cannot miss a draw, because the list *is* the frame.

**The part worth copying is that they walk the buffer and validate it before replaying it.** Their
inspector steps every command, advancing by each command's own size, and tallies what it found:

```c
typedef struct {
    int drawSurfs;
    int stretchPics;
    int swaps;
    int flushes;
    int unknownCommand;      /* <- the one that matters */
} vrStereoReplayStats_t;

static qboolean R_VR_InspectStereoReplayCommands(const byte *cmds, vrStereoReplayStats_t *stats);
```

**An `unknownCommand` means the walk desynchronised**, and a desynchronised walk means the replay would
execute garbage — you are stepping a byte stream by structure sizes, so one unrecognised opcode
mis-advances the pointer and everything after it is misinterpreted. Refuse the replay rather than
running it; `vrStereoReplayLoggedInvalid` ensures that decision is reported once rather than every frame.

Three properties to carry to any command-list replay:

- **Validate by traversal, not by length.** The buffer being the expected size proves nothing about
  whether you can parse it.
- **Count the command types, and log the census.** It is a free per-frame description of what the frame
  actually contains, and it doubles as the draw-classification data
  [14](14-render-pass-hazard-atlas.md) asks for.
- **A new engine command must fail closed.** A game patch that adds one command type would otherwise turn
  a silent parse desync into arbitrary GPU work.

### Look for a repeat world-render the engine already performs

**The cheapest possible answer to "is the world render re-entrant" is that the engine is probably
already doing it.** Cubemap and reflection probes, portal and mirror views, security monitors, shadow
views from a second camera, render-to-texture — all of these re-enter the world render within one frame,
in shipping code, on the developer's own terms.

Find that path and you get two things at once: **proof of re-entrancy that needs no experiment**, and
**a reference implementation of exactly what must be saved and restored around a repeat pass.**

(*SS2VR, investigating something else entirely, found `Kex_RenderCubemapSixFaces` calling
`Kex_RenderWorldFromCamera_Probe` **six times with six camera orientations**, reaching the same core
world-render as the main view. KEX therefore re-enters its world render **six-plus times per frame in
stock gameplay** — the central question was never speculative.*)

The reference-implementation half is the more valuable of the two. Read what the engine changes *around*
its own repeat passes:

> Around its six passes the engine resets the touched-cell list and sets two flags, clearing them after.
> Both flags are read **only** by portal-expansion code. So for a repeat pass the engine changes
> **portal expansion behaviour and nothing else** — no simulation suppression, no audio gate, no
> particle freeze.

That is a **strong negative result on the "what advances twice" half of the gate**, obtained statically,
for free, and with the engine authors' own answer rather than your inference. If the developers only had
to suppress one subsystem to render the world again, your second eye probably only needs the same.

**This is now a three-engine pattern, and it should be your first move.** KEX, UE2.5 and UE3 have all
been shown to re-enter their world render in stock gameplay, and in each case the developers answered
the question before the modder asked it:

| Engine | The engine's own repeat render | How it was found |
|---|---|---|
| **KEX** | `Kex_RenderCubemapSixFaces` → `Kex_RenderWorldFromCamera_Probe` ×6 | Found while chasing something unrelated |
| **UE2.5** | `SwatGamePlayerController.RenderTexture` → `PlayerCalcView` → `DrawPortal` — the flashbang retina effect | Script-side search |
| **UE3** | The whole `USceneCapture*` family — see below | Class-name search in the shipped build |

**UE3's is the most enumerable**, because the engine names its capture family explicitly. DishonoredVR
found the complete set in the recorded build:

```text
USceneCaptureCubeMapComponent      <- six faces, six orientations: the exact KEX shape
USceneCaptureReflectComponent
USceneCapturePortalComponent
USceneCapture2DComponent
USceneCapture2DHitMaskComponent
USceneCaptureComponent             <- shared base
ASceneCaptureActor / ASceneCapture2DActor  + their render targets
```

**Prove it is live, not vestigial engine code.** Class presence alone proves the engine *supports* the
feature, not that this game *uses* it. Two cheap discriminators, both used there:

- **A configuration key is strong evidence.** `SceneCaptureStreamingMultiplier` appears as a config key
  at four addresses — *nobody ships a streaming-budget knob for a feature the game never uses.*
- **Script-settable capture parameters mean per-capture runtime use**, not a compiled-in demo:
  `USceneCapture2DComponentexecSetView`, `execSetCaptureParameters`,
  `USceneCapturePortalComponentexecSetCaptureParameters` are all registered natives.
- And the game has the fiction to match — Dishonored ships mirrors and security-monitor displays.

**Search terms that have worked:** `probe`, `cubemap`, `reflect`, `portal`, `mirror`, `RenderToTexture`,
`SceneCapture`, `SecondaryView`, `RenderTexture`, plus any config key containing `Capture`. The answer
arrives before you write a line of hook code.

**And it retires work, not just answers a question.** DishonoredVR had been preparing a transitive walk
of **59 callees** under `FUN_006c59a0`. That function has only two references, so the capture path
cannot route through it — capture must reach a *lower, shared* scene-render entry, which is the thing
actually worth doubling. The 59-callee walk was abandoned in favour of a cheaper target.

> **Keep the halves separate.** That the classes exist and are live is **demonstrated**. That the
> engine's save/restore around its capture pass is a usable model for what a second eye must suppress is
> **argued** — DishonoredVR flagged this explicitly, not having read that implementation yet. The KEX
> and UE2.5 results support the argument; they do not establish it on UE3.

**Second engine family, same answer.** Swat4-VR found UE2.5 doing it too, in ordinary shipping play:
`SwatGamePlayerController.RenderTexture` calls `PlayerCalcView(...)` then `DrawPortal(...)` — **the
flashbang retina effect**. Query the camera, re-render the world from it, same frame, triggered by a
gameplay event.

And the reference implementation read straight from the predicate bodies:

| predicate | primary `FLevelSceneNode` | `ScriptedPortal` | `DrawPortal` |
|---|---|---|---|
| `ShouldUseFrameBufferFX` | `return 1` | **`return 0`** | **`return 0`** |
| `ShouldRenderViewportActor` | `return 0` | field | inherits |
| `ShouldRenderMirrors` | `return 1` | field | inherits |
| `ShouldRenderPlayer` | field | field | `return 1` |

**FrameBufferFX is the one thing both secondary paths force off** — and, exactly as in KEX, **nothing
suppresses simulation, gates audio, or freezes particles.** Two unrelated engine families, and in both
the developers' own recipe for re-rendering the world is *which things get drawn*, not *what stops
advancing*. That is a strong prior for any new target, and it is a prior about the **first** gate
question specifically.

#### Proof is not a vehicle: the engine's repeat render is usually a *reduced* one

An important caveat, and it comes from the project that pushed this furthest.

The Cyberpunk 2077 port established that REDengine 4 **does** natively schedule a second full-scene view
into its view fan-out, persistently, during gameplay: the apartment mirror is a `worldMirrorNode` planar
reflection, with render stages `renderstage_planar_reflection` and
`renderstage_depthprepass_mirror_opaque_notxaa`. That is decisive proof that the fan-out supports
per-view pass configuration and that a second full view is architecturally allowed.

**And it is unusable as an eye.** Their own verdict — *"proof not vehicle"*:

> Its pass set is **REDUCED** (opaque-only, no TXAA, no transparents) and it is **mirrors-area gated**
> (quest-toggled, not open-world). Using it as an eye would give unequal-quality eyes.

That generalises into the shape you should expect on any engine:

| Existing second-view producer | Quality | Reachability |
|---|---|---|
| Reflection / mirror / portal view | **Reduced** pass set, often gated | Easy to trigger |
| Render-to-texture camera, security monitor | **Full** quality | Walled behind engine-side registration |

*"No free full-quality gameplay vehicle."* So use the existing repeat render for what it is genuinely
worth — **re-entrancy proof and a reference implementation of what to save and restore** — and expect to
do separate work to obtain a full-quality second view.

#### A fifth route: get the engine to register a second view for you

Where the world render cannot be called twice and the draw stream cannot be replayed, there is one more
option: **make the engine create a second view through its own registration path.**

Cyberpunk's shipped answer is exactly that — the second eye is *"an actual engine view — a
render-to-texture camera on the player entity that runs the frame graph for its own eye, from its own
position, with its own projection,"* falling back to mono automatically whenever that view has nothing
fresh to give (menus, loading).

Their synthesis of **35 failed sessions** explains why the cheaper routes did not work, and it is the
most useful paragraph in the repository:

> REDengine carries exactly **ONE main view per frame at every accessible level**, and per-frame state is
> **non-idempotent and globally arena-slotted**, so a second main view can only be created by the
> engine's own registration path.

They closed three families and marked each **decisive, do not retry**: replay/double (write and read
access violations, view no-ops, producer tearing the shared manager); hand-building a second view
(byte-cloning collides on a global arena slot; registry insertion needs the engine's own hash-and-insert);
and RTT handle shortcuts (every callable path *consumes* a handle, none allocates one).

**The transferable test is the arena-slot question.** Before attempting any hand-built second view, ask
whether per-frame render state is **globally slotted** — indexed by a single implicit "current view"
rather than carried per view. If it is, cloning a view structure gives you two objects pointing at one
slot, and the failure is a crash or a torn manager rather than a wrong image.

#### Both eyes from one sim tick is the real goal — not GPU savings

Worth knowing before you spend months on genuine simultaneity. Their pass census measured it:

- Two full views cost **≈188–200% GPU** (per-eye share ~88% after sharing view-independent passes).
- True-simultaneous rendering saves only **~6–12% GPU** versus rendering the eyes sequentially.

So the argument for simultaneity is **not** performance. It is that both eyes come from **one simulation
tick** — which is what removes alternate-eye ghosting. Their documented fallback ("Synchronized
Sequential") freezes simulation and time between the two eye frames and submits them as a synced pair:
identical sim state in both eyes, no engine wall to fight, at the cost of a pair rate of half the frame
rate. **That is a different thing from AFR and should not be lumped in with it.**

If a project rejects alternate-eye rendering for ghosting, sync-sequential may deliver the actual
requirement far more cheaply than genuine simultaneity does.

### The smallest safe hook is a *source-reading* problem

FEAR VR located its hook by reading the official Public Tools 1.08 client source, and cites line numbers:

```text
GameClientShell.cpp:4071-4104   PreRender, special-effect, shatter, ClientFX and streaming updates
GameClientShell.cpp:4124-4134   calls CPlayerCamera::Render(), then dynamic FX, then interface
PlayerCamera.cpp:417-419        clears the render target, calls ILTRenderer::RenderCamera(m_hCamera) once
iltrenderer.h:353-355           that one-arg call is an alias for RenderCamera(hCamera, NULL)
```

The conclusion is the transferable part:

> The smallest safe hook lies **below all client updates and above the pure engine world render.** Only
> that engine call is repeated per eye; `CGameClientShell::RenderCamera`, the PlayerCamera pre/post
> logic, simulation, input, audio and interface all still run once per frame.

**Generalises to: find the narrowest call that renders the world and does nothing else.** Hook one level
too high and you duplicate client updates — simulation, FX ageing, streaming. Hook one level too low and
you are below the camera the engine uses, patching matrices again (rung 2). The right seam is usually a
single engine-level `RenderCamera` / `RenderScene` / `WorldExec` call with the camera as its only
meaningful input. FC2VR's `WorldExec` vtable slot is the same seam found without source.

### Vtable *declaration* order is not vtable *slot* order

A trap worth carrying, and a good piece of RE. The overload declaration order in the header did not
match the retail VC7.1 vtable. A read-only runtime probe found:

```text
slot 17:  8B 54 24 04    mov edx,[esp+4]
          8B 01          mov eax,[ecx]
          6A 00          push 0            ; techniqueOverride = nullptr
          52             push edx          ; camera
          FF 50 4C       call [eax+0x4c]   ; -> slot 19
          C2 04 00       ret 4
```

`0x4C / 4 = 19`. **Retail slot 17 is the one-argument alias, and it forwards to the real two-argument
implementation in slot 19.** This is the thunk trap from
[11](11-re-anchoring-and-discovery.md) wearing a vtable's clothes: the slot you resolve by name is a
forwarding stub, not the body.

Two things about how they handled it are worth copying outright:

- **The loader verifies the 15-byte forwarding stub before patching**, and if the EXE differs the
  vtable is left completely untouched. Fail-closed, exactly as
  [11](11-re-anchoring-and-discovery.md) argues.
- The byte pattern and the slot index are cross-checked **at compile time**:

  ```cpp
  static_assert(0x4C / sizeof(void*) == kRenderCameraWithOverrideSlot,
                "Retail RenderCamera forwarding slot changed.");
  ```

  The magic number in the byte array and the constant used elsewhere can no longer drift apart silently.

### The official SDK is ground truth — but the rebuild may be unshippable

This is the sharpest correction in the whole study, and it is a rung-3 caveat with teeth.

FEAR ships **official Public Tools 1.08 source**. The project builds it successfully as PE32/x86 with
VS2022 and the v141 toolset — `GameClient.dll` 1.08.282.0. And then **refuses to ship it**:

> The original `GameClient.dll` imports `MSVCP71.dll`/`MSVCR71.dll` (Visual C++ 7.1); the v141 build
> imports `MSVCP140.dll`/`VCRUNTIME140.dll` and the UCRT. F.E.A.R. exchanges C++/CRT objects across the
> module boundary. Source compatibility is not enough.

An isolated live test with only the rebuilt `GameClient.dll` reproducibly killed the game with
`0xC0000005` inside `MSVCR71.dll`. Their deploy script now refuses the v141 build with a deliberate
**ABI safety abort** *before copying any file*.

So the SDK is used as an **oracle, not an artifact**: it gives exact call sites, semantics, struct
layouts and enum orders, and every one of those is then confirmed against — and patched into — the
retail binary. That is [11](11-re-anchoring-and-discovery.md)'s rung 3 stated precisely: *the ancestor
gives vocabulary, only the shipping binary is truth*. What this case adds is that **even the ancestor
compiled from official source can be untruth**, if the CRT ABI moved underneath it.

**Check before you plan a rebuild-based mod:** what CRT does the shipping module import, and do you have
that toolchain? For anything built before roughly 2010 the honest answer is usually no, and the mod has
to be a patch rather than a rebuild.

### Do not jump to a command replayer

Their fallback ladder (§4) is worth quoting because it names the temptation and forbids it:

> Do not blindly build a complete D3D9 command replayer. Check in this order, and document the exact
> cause here: **1.** official render-target / camera APIs from the SDK; **2.** a small,
> **version-checked** hook around the engine camera render call; **3.** depth + image reprojection
> **only** as a clearly-labelled compatibility mode.
>
> D3D9 depth hacks like `INTZ`/`RESZ` are vendor-dependent and must not be the sole basis of the main
> path.

### One runtime finding worth stealing

From the M4 gate: **the first image lagged the render request by two OpenXR frames.** Associating the
pose that was *actually rendered* with the image — rather than the pose current at submit time — is what
lets the compositor do correct timewarp. The user's rating went from acceptable to *"significantly
better"* on that change alone.

If your stereo is geometrically correct and still feels wrong in motion, check what pose you are
attaching to the submitted frame before you touch anything else.

## FC2VR: four failures, and what each one generalises to

The author shipped a numbered revision per root cause with a causal-evidence file for each. This is the
most valuable part of the package, and all four generalise well beyond Far Cry 2.

### R1 — The transaction must be restorable, and must fail visibly

Retained in every later build: *"exact post-`CameraRebuild` A/B/P restore"* and *"visible fail-back on
aborted LEFT/RIGHT"* — a backbuffer restore when an eye transaction aborts partway.

**Generalises to:** if you borrow engine state, treat the borrow as a transaction with an explicit
rollback, and make the abort path *visible* rather than silent. A half-restored camera is worse than no
stereo, because the flat game is now broken too. This is
[07](07-engine-integration-safety.md)'s write-target-lifetime rule applied to a per-frame borrow.

### R2 — The engine keeps observing while you hold its camera

The best-documented failure in the package, and the least obvious.

While the LEFT eye was being built, Dunia's primary observer *kept running*, because the flag that
gates it (`g_worldActive`) was still true. The transient camera position emitted during LEFT's
`CameraRebuild`/`ViewBuilder` therefore overwrote the stored primary camera. RIGHT then compared the
correctly-restored stock camera against that contaminated reference — and rejected it.

The proof is bit-exact, not statistical:

```text
seq=623742  CAMERA_C45        0x451CB247 0x4494681C 0x41B2AC54   (2507.14, 1187.25,  22.33)  <- stock
seq=623753  NATIVE_VIEW_BEGIN flags=1                                                        <- LEFT starts
seq=623770  CAMERA_C45        0x454D288F 0x4493E586 0x442D57EE   (3282.53, 1183.17, 693.37)  <- transient
seq=623801  NATIVE_VIEW_END   flags=1
seq=623811  NATIVE_VIEW_BEGIN flags=0   expected-primary = 0x454D288F 0x4493E586 0x442D57EE
seq=623812  XR_SKIP           flags=5

RIGHT expected-primary == transient LEFT c45 @623770 : EXACT BIT MATCH
RIGHT expected-primary != stock  PRIMARY  c45 @623742 : MISMATCH
```

Fix: **freeze primary camera and projection provenance across the whole duplicated-eye transaction.**

**Generalises to:** *your intermediate state will be latched by systems you did not know were watching.*
Anything that samples "the current camera" — observers, audio listeners, occlusion queries, LOD
managers, streaming — keeps running while you are halfway through building a second view. Identify what
samples the state you are borrowing and freeze it for the duration, or it will record your scratch value
as truth.

Note also *how* it was proven. Comparing floats would have produced "close enough, probably fine."
**Logging raw bit patterns turned a plausible theory into an identity proof** — see
[06](06-debugging-methodology.md) on measuring rather than theorising.

### R3 — One flag serving two meanings will flap

`FEARVR_BF_STEREO_ACTIVE` was used as both:

- **A.** persistent render-mode ownership — "we are a stereo mod right now", and
- **B.** per-event state — "the Present that just went through was stereo".

The host reads that bit every XR frame to choose its composition layer:

```text
set    ->  XrCompositionLayerProjection   (true VR)
clear  ->  XrCompositionLayerQuad         (flat rectangle in space)
```

After a valid stereo pair the bit was set. Any subsequent ordinary mono Present cleared it — while the
native stereo stream was still perfectly alive. Symptom: **blinking between true VR projection and a flat
theatre screen.**

The fix is eight bytes, and its narrowness is the point:

```text
RVA 0x00008B48   F0 81 60 60 7F FF FF FF    lock and dword ptr [eax+0x60], 0xFFFFFF7F
             ->  90 90 90 90 90 90 90 90
```

Every *explicit* transition was deliberately left intact — stereo HUD flat frame,
`SetStereoEnabled(false)`, `SetComfortModeEnabled(true)`, `SetMenuActive(true)`, the F8 and F10 paths,
and shutdown cleanup. Only the *generic* clear was suppressed. The author calls it *"the smallest causal
A/B patch"* and adds no timeout or hysteresis.

**Generalises to:** **a boolean that answers both "what mode are we in" and "what just happened" will
oscillate.** Separate persistent ownership from per-event state. When you find yourself adding a timeout
or hysteresis to stop something flickering, check first whether you have conflated these two — the
hysteresis is usually a patch over the real bug. Related: [07](07-engine-integration-safety.md) on gates
that guard more than they should.

### R4a — Publish the pair, never half of one

R3 fixed the flapping but exposed something subtler and worse. Measured over one run:

```text
XR_REQUEST=298   XR_PAIR=215   XR_SKIP=84
all retained skip reason = LEFT_NATIVE_VIEW_BEGIN_FAILED
MonoQuadAnchored=2 only, despite 84 eye rejects
```

A failed eye could still be followed by a generic mono Present. Because R3 correctly kept
`STEREO_ACTIVE` latched, that mono frame was written into **both** eye slots while the host stayed in
Projection mode. The result is not an obvious flat rectangle — it is *duplicated mono presented as
stereo*, which reads as "the stereo is subtly wrong" rather than "the stereo broke".

Fix: if a transfer is mono **and** stereo is active, release the already-claimed slot through the normal
release path and publish nothing. **The last complete coherent L+R pair stays live until the next
complete pair arrives.**

**Generalises to:** *the unit of publication is the pair, not the eye.* A reader must never be able to
observe one eye from frame N and the other from frame N+1, nor the same image in both slots. This is
exactly the atomic-publication argument behind the seqlock in
[07](07-engine-integration-safety.md) — and note the failure mode it prevents is *not* a crash or a
visible tear, but a silently degraded image that looks like a tuning problem.

Note the diagnostic that exposed it: **84 eye rejects but only 2 mono-quad anchors.** Two counters that
should have moved together didn't. Neither number is alarming alone.

### R4b — Validate in the space the quantity means something

The original guard compared all sixteen raw View-matrix coefficients against a flat `0.010` threshold.

That is wrong for a reason worth internalising: **a View matrix mixes rotation and translation, and its
translation terms are the rotation multiplied by the world position.** At Far Cry 2's map coordinates —
the R2 log shows the player at `(2507, 1187, 22)` — a rotation rounding error around `1e-6` becomes a
View-coefficient delta above `0.01`. The threshold therefore tightened and loosened depending on where
the player stood and which way they faced, producing rejects *"near one world direction and again about
180 degrees opposite."*

The fix inverts the rebuilt matrix back into a physical pose and validates the two quantities
separately, in their own units:

```text
old:  reject if max_abs(gotView - desiredView) >= 0.010

new:  got = inverse(rebuiltView)
      eRot = max abs delta of the 3x3 rotation      reject if >= 0.0025
      ePos = max abs delta of camera XYZ            reject if >= 0.010
      (raw eV retained as telemetry only)
```

**Generalises to:** **validate in the space where your tolerance has a fixed physical meaning, not in
whatever space the value happens to be stored.** "0.01 of a View coefficient" is not a unit of anything —
its meaning changes with world position. "0.01 metres of camera position" and "0.0025 of a rotation
component" are real tolerances that hold everywhere on the map.

This is the second time this family of error has appeared in the playbook. FarCry2-VR separately proved
that a bare affine residual check **cannot detect a wrong FOV** ([09](09-d3d11-openxr-injection.md),
[11](11-re-anchoring-and-discovery.md)). Same root cause: a matrix residual is not a measurement of
anything a human cares about. **Decompose first, then check each component against a tolerance that
means something.**

Keeping the old metric as telemetry rather than deleting it is also right — you lose nothing, and the
old number is what lets you recognise the failure again next time.

---

## Porting across store builds: a method worth copying

GOG, Steam and Ubisoft Connect ship different `Dunia.dll` builds. The package handles this by
**identifying the build by SHA256** and carrying a verified offset table per build.

Steam and Ubisoft turned out to be the same port — proven, not assumed:

> Identical `.text`/`.rdata`/`.data`/`CONST`/`.rsrc`/`.reloc` section hashes, and the same CodeView path
> `d:\dev\fc2relaunch\fcx-branches\fc2-pc-uplay\bin\Dunia.pdb`.

That is a good trick on its own: **the embedded PDB path is a build identity string**, and it collapsed
two apparent targets into one.

The port table is then *statically verified* rather than trusted. `Inspect-Dunia.ps1` re-derives every
anchor from the file:

- **vtable slots** — read the `u32` at the slot RVA, compare to `imageBase + expected`
- **call sites** — decode `E8 rel32` at the call RVA (`target = imageBase + rva + 5 + rel32`), compare
- Then a set of semantic cross-checks: all three `CameraCopy` call tails match the GOG instruction
  sequences; `CameraRebuild` reads the same camera fields (`+0x3B8`, `+0x3C4`, `+0x1F0`) the working
  kernel uses; and the *set of direct callers* maps across builds.

This is a concrete implementation of [11](11-re-anchoring-and-discovery.md)'s anchor-resolver harness —
every anchor carries a validator, the validator is independent of how the anchor was found, and the
whole set is checked before anything runs.

**The field-access check is the strongest link, and FarCry2-VR improved it when they reproduced this
on their own binary.** The published claim is that `CameraRebuild` reads `+0x3B8`, `+0x3C4` and `+0x1F0`.
Verified — each appears exactly twice — but the surrounding structure is far more specific:

```text
+0x3B8  +0x3BC  +0x3C0    consecutive float3   (position-like)
+0x3C4  +0x3C8  +0x3CC    consecutive float3   (direction-like)
```

**Two adjacent float3 blocks is a fingerprint; three isolated offsets is a coincidence waiting to
happen.** And the check *survives a rebuild* — every address moves, the struct layout does not — which
is exactly the patched-binary case that motivated the port map in the first place.

> **Do not use the caller count as the validator.** It is reported three incompatible ways for this same
> function: the port map says **12**, the package's own `STATIC_VALIDATION.txt` says **14**, and Ghidra
> on FarCry2-VR's binary says **10**. Ghidra may exclude thunked or indirect edges; their tooling may
> count call *sites* rather than distinct callers. An earlier version of this chapter passed the 12
> along as settled — it is not. A caller count is a useful *smell*, never an assertion.

One related habit, from FarCry2-VR correcting themselves in the same pass: they had recorded their
independently-named `FC2VR_BuildProjection` as sitting "adjacent" to `CameraRebuild` and called that
mutual corroboration. It was not — the real relationship is better, because `FC2VR_BuildProjection` is a
**direct caller** of it. **Meeting on the same call edge is corroboration; two addresses being near each
other is just proximity.**

---

## The validation discipline is the transferable part

`STATIC_VALIDATION.txt` reports **99/99 checks**, and the categories are worth stealing wholesale:

| Category | Examples |
|---|---|
| **Reproducibility** | Deterministic fresh rebuild reproduces the shipped SHA256, per outer |
| **Identity** | SHA256 of every shipped binary; PE machine type and magic (`PE32 x86`) |
| **Interface** | Each outer imports `FearVr_BeginEye`/`CaptureEye`/`GetRenderRequest`/…, exports `Direct3DCreate9` |
| **Patch precision** | Bridge diff touches **only** the planned byte ranges; each patch's actual bytes and resolved jump target asserted at its RVA |
| **Regression** | R3's NOP still present; R1 fail-back retained; R2 freeze retained; render scale still 100% |
| **Negative** | No `OculusMirror` invocation, no `vrmonitor` invocation, no 2× render scale, no AA/sharpening override |
| **Hygiene** | Shipped `.bat`/`.ps1` files: no UTF-8 BOM, CRLF only, braces and parens balanced |

Three things stand out.

**The negative checks.** *"No 2X render scale, XR target override, sharpening or AA override is
present."* Asserting the absence of things you did not intend to ship is how a debug experiment stops
leaking into a release. Most projects only test that intended things are present.

**The patch-precision checks.** Asserting that a binary diff touches *only* planned ranges — listed
explicitly as byte spans — converts "I think I only changed what I meant to" into a test.

**The honesty about scope.** The file ends:

> Far Cry 2 / Windows / OpenXR cannot be executed in this Linux validation container.
> Compiler/package/static invariants above are verified; the headset visual verdict remains the
> authoritative runtime test.

99/99 green, and the author still states plainly that none of it proves the thing works. That is the
right relationship between a test suite and reality, and it belongs in
[08](08-project-process.md) alongside the milestone definitions.

**One safety property worth copying verbatim:** `FarCry2.exe` and `Dunia.dll` are never modified on
disk. The proxy is installed at launch and the previous state restored at exit, with a
`RESTORE_GAME.bat` for the interrupted case.

---

## What a rung-1 refusal looks like, and what to do next {#rung1-refusal}

The gate above is only useful if a failure is as legible as a pass. BL1GOTYVR's is the clearest recorded
refusal in this survey. `[SOURCE]`

> Calling `GameViewportClient::Draw` twice in one frame **is unsafe in this build**. It corrupts the UE3
> heap and eventually terminates with `0xC0000374`. The hook must call the original function **exactly
> once**.

`0xC0000374` is `STATUS_HEAP_CORRUPTION`, and "eventually" is the dangerous word: the second call
returns, the frame completes, and the process dies later somewhere unrelated. **A re-entrancy failure
does not have to fail at the call site** - which is exactly why
[the debugger protocol](06-debugging-methodology.md#double-call-in-debugger) insists on a cadence
baseline *after* the double-call window, not only during it.

**They took the answer and moved down the ladder** rather than trying to make rung 1 work: the shipped
path is [rung 3](#the-ladder-and-what-each-rung-costs), geometric alternate-eye, with the camera saved
and restored around a **single** `Draw`:

1. select the render eye from the same frame counter Present capture uses;
2. save `CalcViewLocation`, `CalcViewRotation` and `CachedFOVAngle`;
3. apply the head pose and the per-eye IPD offset;
4. call `Draw` **once**;
5. restore the original camera values;
6. capture that frame into the matching eye texture during Present.

Validated in a headset with geometric parallax and head tracking, over a stability run exceeding
**5,700 frames** without errors. **A rung you can hold for 5,700 frames beats a rung that corrupts the
heap**, and recording *why* you are on rung 3 stops the next session re-litigating it.

One capture-path hazard from the same project, because it produces a silent wrong answer rather than a
crash: their path **temporarily unbinds the render target before copying it** and restores the bindings
before `Present`, because *"copying while it remained bound could silently preserve an old loading
frame."*

## The seam is below the client updates and above the engine's world render {#second-pass-seam}

The gate at the top of this chapter asks whether the world render can be invoked twice. fear-vr's
`STEREO-RESEARCH.md` is the clearest worked answer in the survey, and the rule it arrives at is
engine-independent. `[SOURCE]`

They read four sites in the official client source before touching anything:

| Site | What it does |
|---|---|
| `GameClientShell.cpp:4071-4104` | PreRender, special-effect, shatter, ClientFX and streaming updates - **all before the camera render** |
| `GameClientShell.cpp:4124-4134` | calls `CPlayerCamera::Render()`, *then* dynamic FX and interface |
| `PlayerCamera.cpp:417-419` | clears the render target and calls `ILTRenderer::RenderCamera(m_hCamera)` **exactly once** |
| `iltrenderer.h:353-355` | that one-argument call is an alias for `RenderCamera(hCamera, NULL)` |

> **The smallest safe hook lies *below* all client updates and *above* the pure engine world render.**

Only that engine call is repeated per eye. The client shell's own render function, the camera's pre- and
post-logic, simulation, input, audio and the interface all still run **once per frame**. That sentence
is the whole design, and it is worth writing down for your own target before writing code: **name the
lowest call that draws the world and nothing else.**

Their frame order, which matches the [four preconditions for rung 1](#the-four-preconditions-for-rung-1) exactly:

1. read the current XR render request immediately before rendering;
2. save the original camera pose and FOV;
3. apply the left eye pose relative to the calibrated origin;
4. render **only** the 3D world for the left eye, and capture it;
5. apply the right eye pose;
6. render **only** the 3D world for the right eye, and capture it;
7. restore the camera;
8. render HUD and menus **exactly once**;
9. present **exactly once**.

**And the gate is a side-effect gate, proven two ways.** Theirs required source *and* runtime evidence
that the second `RenderCamera` executes no simulation, AI, sound events, particle ageing or input a
second time.

### If it cannot be called twice, escalate in this order

Their fallback ladder opens with an instruction rather than an option, and it is the right one:

> **Do not blindly build a complete D3D9 command replayer.**

1. **Official render-target and camera APIs from the SDK**, if one exists.
2. **A small, version-checked hook** around the engine camera render call.
3. **Depth plus image reprojection, only as a clearly marked compatibility mode.**

With a caveat that decides the third rung's viability: **D3D9 depth hacks such as `INTZ` and `RESZ` are
vendor-dependent and must not be the sole basis of the main path.** A technique that works on one
vendor's driver is a compatibility mode, not an architecture.

The checklist they worked through is reusable on any D3D9 target: `OnRender` or the central client
render path, `RenderCamera`, `Start3D` / `End3D` / `FlipScreen`, the player camera and `SetCameraFOV`,
HUD and interface rendering, and camera shake, head-bob and the cutscene comfort path - plus a standing
requirement that input and weapon-direction calculation stay at once per game frame.

## A worked CryEngine second pass, and what it costs {#cryengine-second-pass}

Crysis VR (fholger) renders the world twice per frame on **CryEngine 2**, and its loop answers questions
this playbook has only been able to state abstractly. It matters most to CryEngine-lineage targets, where
the second-pass question is often the whole project. `[SOURCE]`

```cpp
gVR->AwaitFrame();                       // ONE wait for the frame
RenderSingleEye(0, renderFunc, pSystem);
pSystem->RenderBegin();                  // <-- see below
RenderSingleEye(1, renderFunc, pSystem);
```

**`RenderBegin()` between the eyes is not optional**, and their comment names the symptom:

> need to call RenderBegin to reset state, otherwise we get **messed up object culling** and other issues

That is the general shape of [the side-effect gate](#side-effect-gate): a second pass
inherits state the first pass left behind, and culling is the first thing to break. If your engine has a
frame-begin entry point, calling it between passes may be the whole fix.

### Borrow the engine's own debug switch to suppress once-per-frame work

The most transferable trick here is how they stop the particle system doing its update twice:

```cpp
if (particlesDebug && eye == 1) {
    // disables updating of the particles system, to avoid doing extra work for the second eye
    particlesDebug->SetFlags(particlesDebug->GetFlags() & (~VF_CHEAT));
    particlesDebug->Set((int)(origParticlesDebug | AlphaBit('z')));
}
...
if (particlesDebug && eye == 1) particlesDebug->Set(origParticlesDebug);   // restored
```

**The engine already had an off switch for that subsystem — a debug console variable — so they used it
rather than hooking the subsystem.** Before writing a hook to stop something running twice, check whether
the engine ships a variable that already stops it. Note also the `VF_CHEAT` clear: a cheat-protected cvar
can be made settable by clearing the flag, which is worth knowing and worth using sparingly.

And note the restore. A suppression that is not symmetric leaves the subsystem off for the *next* frame's
first eye.

### The rest of the per-eye body, which is the borrow/restore contract in miniature

```cpp
CCamera eyeCam = m_originalViewCamera;   // by VALUE
gVR->ModifyViewCamera(eye, eyeCam);
gEnv->pRenderer->EF_Query(EFQ_DrawNearFov, (INT_PTR)&fov);   // viewmodel FOV follows the eye FOV
pSystem->SetViewCamera(eyeCam);
m_viewCamOverridden = true;
    ... renderFunc(pSystem) ...
pSystem->SetViewCamera(m_originalViewCamera);                 // restored
m_viewCamOverridden = false;
gVR->CaptureEye(eye);
```

Three details worth copying: the camera is taken **by value** so the original is never mutated; an
`m_viewCamOverridden` latch lets everything else in the frame know the view is not the player's; and
`EFQ_DrawNearFov` keeps the **viewmodel** FOV in step with the eye FOV, which is the
[projection-companion](09-d3d11-openxr-injection.md) rule applied to the near plane.

They also refuse to render the world while a menu is up, "as it shows a rotating game world that is
disorienting" — a comfort decision, not a technical one, and the sort that only shows up after someone
wears it.

## Detect a lost hook by its silence, and reinstall {#hook-loss-detection}

Crysis VR treats its `Present` hook as something that **will** be lost, and watches for it: `[SOURCE]`

```cpp
if (currentSwapChain != gVR->GetSwapChain() || milliSecsSinceLastPresentCall > 1000) {
    CryLogAlways("May have lost our Present hook, recreating!");
    hooks::RemoveHook(&IDXGISwapChain_Present);
    ...
    hooks::InstallVirtualFunctionHook("IDXGISwapChain::Present",       currentSwapChain,  8, ...);
    hooks::InstallVirtualFunctionHook("IDXGISwapChain::ResizeBuffers", currentSwapChain, 13, ...);
    hooks::InstallVirtualFunctionHook("IDXGISwapChain::ResizeTarget",  currentSwapChain, 14, ...);
}
```

Two independent detectors, and the second is the interesting one: **the swapchain identity changed**, or
**the callback has been silent for a second**. A hook that stops being called produces no error — it just
stops — so silence is the only signal available, and a wall-clock threshold turns it into one.

**Any hook whose target can be recreated needs this**: device reset, resolution change, alt-tab,
overlay injection and driver recovery all swap the object out from under you. See
[HOOK-004](pattern-catalog.md#hook-004).

## The path to native stereo for your engine

Native stereo is the top of the ladder, and it is not always reachable. Assess before committing.

> **Do not read this ladder as a measure of quality.** It answers *how the second eye is produced*, and
> nothing else. Virtua Cop 2 VR sits on the bottom rung and is a good mod; the
> [completeness tier](08-project-process.md#how-vr-is-it-declare-a-completeness-tier-and-ship-to-it) is the axis that tracks how much of the game actually becomes VR.

### The ladder, and what each rung costs

| Rung | Approach | Parallax | Camera-derived systems | Cost |
|---|---|---|---|---|
| **1** | **Native stereo** — engine renders the scene twice from two real camera poses | Real | **Correct automatically** — culling, LOD, sky, fog | Highest. Needs a re-entrant world render and a transactional camera borrow |
| **2** | Per-draw replay / sequential re-entry — resubmit the draw stream with a per-eye matrix | Real | Wrong unless each is patched individually | High |
| **3** | AFR / alternate-eye — one eye per frame | Real, but temporally offset | Correct per eye, stale by one frame | Moderate; halves effective framerate, temporal artifacts |
| **4** | Reprojection from a mono image | **None** — synthesised | N/A | Low, and it does not look like VR |

### The four preconditions for rung 1

Test all four before committing. Precondition 2 is the one that decides it.

| # | Precondition | The test | Fails when |
|---|---|---|---|
| 1 | **A re-entrant world render** you can invoke more than once per frame | Find the renderer's frame-graph / world-execute entry — in Dunia these were **vtable slots**, which is the easy case. Call it twice with the same camera and confirm you get two identical frames and no corruption. | Scene submission is welded to `Present`, or one-shot state (command lists, transient allocators) is consumed on first use. |
| 2 | **The engine's own camera-build function**, callable with a pose you supply | Locate the `CameraRebuild` / `ViewBuilder` equivalent and its direct callers. Confirm it derives the view from stored camera fields you can write. | The view matrix is assembled inline at the call site and never round-trips through a function. Then you are on rung 2 — you can still patch matrices, but the sky and culling will not follow. |
| 3 | **A capture point per eye** before the engine reuses the target | The existing `Present`/backbuffer hook usually suffices. | Nothing — this is rarely the blocker. |
| 4 | **Everything you touch is restorable**, and you can enumerate what observes it | Log the camera fields across a frame and find every writer and reader. R2 is what happens when you miss one. | You can't enumerate the observers. Do the work anyway — this failure is silent. |

### The build order that the R1→R4 chain implies

The revision history is effectively a recipe, and the ordering is not arbitrary — each stage exposes the
next one's bug.

1. **Get one eye rendering natively, with exact restore.** Not stereo yet. Prove the engine survives a
   borrowed-camera transaction and that an abort restores cleanly and *visibly* (R1).
2. **Freeze everything that observes the camera** for the duration of the transaction — before adding
   the second eye, because R2's contamination only appears once two eyes compare against a shared
   baseline.
3. **Add the second eye and publish pairs atomically.** Never publish a single eye or a mono frame into
   stereo slots (R4a).
4. **Separate mode ownership from per-event state** in whatever flag the host reads to choose its
   composition layer (R3).
5. **Validate the rebuilt pose in pose space**, with separate rotation and position tolerances (R4b).
6. **Instrument all of it with a sequenced forensic ring** logging raw bit patterns, and pair counters
   that should move together so you notice when they don't.

### Where this fleet stands

Three projects have now answered this from their own binaries rather than from my guess. The
**camera-delivery** column is the one that matters, per the spectrum above:

| Project | Engine | Camera reaches renderer as | Status |
|---|---|---|---|
| **PreyVR** | CryEngine, x64 | **Parameter** — `CreateGeneralPassRenderingInfo(const CCamera&,…)` @ `0x1E5B30`, 3 direct callers; `CRenderView::SetCamera` copies by value | **Preconditions met, viability not established** (H-009). `C3DEngine::RenderWorld` @ `0x21F520` has *zero* direct xrefs — all virtual dispatch, `IProcess` index 3, vtable `+0x18`. Nothing called yet; pooled `CRenderView` contention and cost unknown |
| **SS2VR** | Dark/KEX, x64 | **Parameter** — `Kex_RenderFrame` builds it on its own stack, passes by pointer to `0x45C470` | **Best case in the fleet.** The borrow-and-restore bug family does not apply |
| **DishonoredVR** | UE3 / D3D9, x86 | *unresolved* | **Re-entrancy: strong static evidence.** The full `USceneCapture*` family ships and is live (config key at 4 addresses, script-settable capture params, in-fiction mirrors). The 59-callee walk under `FUN_006c59a0` was retired — only 2 refs, so capture routes lower. Camera delivery still open |
| **Swat4-VR** | UE2.5 / D3D9, x86 | **Parameter** — `FPlayerSceneNode` ctor takes `FVector`, `FRotator`, `float FOV`; Location matched the D3D9 view matrix to 4 dp | **Re-entrancy PROVEN in shipping play** — `SwatGamePlayerController.RenderTexture` → `PlayerCalcView` → `DrawPortal` (the flashbang retina effect). Hazard classes 2 and 3 measured **absent** |
| **BioshockVR** | UE2.5 / D3D11, x86 | *unresolved* | On rung 2 with private eye targets and pair latching. The native-function table is the obvious probe |
| **SOMAVR** | HPL3 / OpenGL, x64 | *unresolved* | HPL2 ancestor source makes the question answerable offline |

**One CryEngine-specific trap from PreyVR, which generalises:** the *recursive* `RenderWorld` variant is
**inlined and has no address**, which is why they had previously written the route off. The *general*
one is a real function. **On a heavily-templated C++ engine, the obvious-sounding entry point is often
the inlined one** — check the neighbours before concluding a seam does not exist.

**The two cheap first questions**, both answerable in an afternoon with
[11](11-re-anchoring-and-discovery.md)'s anchor ladder:

1. Is the world-execute step reachable as a **vtable slot or function pointer** rather than inline code?
2. Does the camera arrive as a **parameter** or as a **global you must overwrite**?

The first decides whether rung 1 is possible. **The second decides how much of this chapter you have to
implement** — and it is the question I originally left out.

---

**Related:** [09 · D3D11 & OpenXR injection](09-d3d11-openxr-injection.md) ·
[07 · Engine integration & safety](07-engine-integration-safety.md) ·
[16 · Teardown: Virtua Cop 2 VR](16-teardown-virtua-cop-2-vr.md) ·
[11 · RE anchoring & discovery](11-re-anchoring-and-discovery.md) ·
[A3 · Stereo projection & validation](a3-stereo-projection.md)
