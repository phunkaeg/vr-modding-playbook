# Cross-Engine Overlap & Contradiction Map

This is the synthesis the rest of the playbook points at: a side-by-side of where the projects hit the
**same** wall (so you can expect it on the next engine) and where they genuinely **diverge** (so you
don't copy a solution that only fits one engine). Read [00](00-engine-profiles.md) first for the engine
shorthand.

The one-line thesis: **the problems are shared; a handful of the *solutions* are engine-specific.**
Knowing which half you're in saves the most time.

This page compares technical overlap and contradiction. For the operational
question “which shared wall currently blocks each in-house project, and what
proof clears it?”, use the generated [fleet bottleneck map](bottleneck-map.md).

## Part 1 — Overlaps: problems every engine forced

Every row here appeared independently on Dark/KEX (D3D11), Unreal 2.5 (D3D11), *and* HPL3 (OpenGL) —
with a fourth, externally-built project (Blam/Saber) corroborating much of it in the section that
follows. That independence is the evidence the lesson is engine-agnostic.

| Recurring problem | SS2VR (Dark/KEX) | BioshockVR (UE2.5) | SOMAVR (HPL3/GL) | Chapter |
| --- | --- | --- | --- | --- |
| **Which camera does this consumer use?** | weapon wobble = wrong camera; residual probe → native-same-tick | viewmodel post-multiplies a matrix already holding the HMD → double-applied head motion | authored/scripted cameras vs player camera; frustum hook returns native for every non-player camera | [01](01-camera-and-tracking.md) |
| **Projection is a contract, not a matrix** | reconstruction/clip companions per eye | 8 coupled constants (`worldViewProj`+`screenDataToCamera`+`screenToWorld`+…) | GLSL UBO reconstruction (`a_mtxInvViewProjection`) in deferred lighting | [09](09-d3d11-openxr-injection.md) |
| **Engine owns culling, not your frustum** | 3 mechanisms; drive KEX cull camera, not the RenderView | peripheral coverage needs engine camera/FOV/near/culling | `cViewport`/`cCamera` ownership so aux cameras can't inherit HMD pose | [01](01-camera-and-tracking.md) |
| **Mono screen-space buffers break per-eye** | (forward — mostly N/A) | dominant artifact class: mono `s_shadowMask` → black sides; needs per-eye producers | deferred shadow/reflection reconstruct from mono-centered projection | [09](09-d3d11-openxr-injection.md) |
| **Render-view provenance / secondary views** | reflection/portal/vista must not merge into one eye pair | "cyan Rapture shell" = bounded secondary view scissored to full-eye | reflection/terminal/water/shadow cameras must not consume F10 | [09](09-d3d11-openxr-injection.md) |
| **Drive the engine's own system** | KEX cull camera + Squirrel verbs | native `AimIKTargetTracker` + `GetPerfectFireStart` rotator | native analog mover, `SOMA_GetClosestEntity` picker, camera-add channels | [07](07-engine-integration-safety.md) |
| **One input path per control** | keyboard-WASD + virtual pad = "ubermensch speed" | synthetic slot presence steals KB/M; sum vs arbitrate | synthetic keys demoted to fallback once native mover confirmed | [03](03-input-and-locomotion.md) |
| **Comfort is a subsystem** | snap blackout; vignette 0.30 m/1 m contract; roomscale crouch double-drop | (in progress) | *reused SS2's exact vignette contract*; head-bob/shake/sway channel suppression | [01](01-camera-and-tracking.md) |
| **Yield to authored/scripted cameras** | scripted cameras, cutscenes | scene-node camera constructor owns view; mutate only transient args | 20 player states classified; compose HMD on the authored base, reseed histories | [01](01-camera-and-tracking.md) |
| **Puppeteer native locomotion, don't reimplement** | reuse `TeleportObject`; latch native climb + feed stick | native XInput mover | native analog mover at `playerRoot+0x110` | [03](03-input-and-locomotion.md) |
| **Build/config must self-identify** | config-key bug looked identical to a stale DLL | stale OneDrive INI invalidated tests → `config_identity` log | version banner + fresh log per session | [06](06-debugging-methodology.md), [07](07-engine-integration-safety.md) |
| **Measure, don't theorize** | multi-candidate residual probe ended a multi-day wobble hunt | ~15 falsified hypotheses before the scissor fix; extract `P_center` don't guess | F-key A/B probes redirect the shadow-owner search | [06](06-debugging-methodology.md) |
| **Tonemapping at the eye blit** | HDR→LDR/sRGB mismatch | HDR scene target copied into UNORM swapchain → washed out; prefer sRGB | GL format prefs `GL_SRGB8_ALPHA8` first | [09](09-d3d11-openxr-injection.md), [10](10-graphics-apis.md) |
| **Full-eye FOV, not a stretched image** | aspect-fit vs crop as diagnostics only | 16:9 cropped into 2688×2880 eye → "very zoomed in"; allocate at eye extent | private targets at runtime eye extent | [09](09-d3d11-openxr-injection.md) |
| **Three tracked points do not define a torso** | hand bases stay controller-owned; future arms need a separate shoulder frame | native AimIK supplies arm articulation but still needs a stable body-relative target | HMD position drives shoulder translation; native capsule yaw drives heading; bilateral wrists and downward-biased elbow IK remain separate lanes | [12](12-torso-calculations-and-ergonomics.md) |

The takeaway from Part 1: when you start the next engine, walk this column top to bottom as a checklist.
You already know these are coming.

### Independent corroboration: HaloVR

[HaloVR](https://github.com/pancreations/Halo-MCC-VR) is an external project — different author,
different engine (Blam/Saber, 64-bit D3D11), no contact with the three above. It hit the same walls
anyway, which is the strongest evidence in this document that these lessons are structural rather than
habits of one team.

| Spine item | How HaloVR independently hit it |
| --- | --- |
| Engine owns culling | Default FOV culls outside the flat frustum → scenery pops at headset edges. Fixed by forcing the game's own FOV to `120` — the cheap version of the same lesson |
| Suppress engine head motion at source | Bypasses `observer_apply_camera_effect` while head tracking is active, killing recoil/shake without touching locomotion — structurally identical to SOMA's camera-add channel zeroing |
| Keep gameplay aim engine-owned | Converts controller aim into Halo's *normal aim steering*, so projectiles, target logic, vehicles and turrets stay game-owned (BioShock's `GetPerfectFireStart` conclusion, reached separately) |
| Input via native gamepad path | OpenXR actions merged into XInput slot 0 — the same rung-3 answer BioShock landed on |
| Predicted pose, correct sample point | Filtering the pose in `Present` felt laggy at every setting; the fix was sampling the *next* predicted display pose |
| Hot paths stay deterministic | No file I/O, logging bursts, locks, COM or allocation in render/palette hooks |
| RVAs are evidence, signatures are authority | RE notes name the exact build and forbid treating any recorded RVA as a shipping address |
| Forbidden-boundary ledger | A "never hook this" list, including one function that crashed on level load even as a pass-through detour |
| Headset observation is the acceptance test | "Desktop output and logs are supporting evidence only" |

## Part 2 — Contradictions: where the right answer is engine-specific

These are the decisions where copying the wrong project's solution actively costs you. When a chapter
gives advice, check it against this list before assuming it's universal.

### Graphics API — the plumbing genuinely differs
D3D11 (SS2VR, BioshockVR) gives you a device/context, RTV/DSV, constant buffers, and `Present`. OpenGL
(SOMAVR) gives you a **global state machine**, FBOs, `glUniformMatrix4fv`, and `SwapBuffers` — no device
object to bind, broader and less forgiving state to save/restore, and a compatibility profile that can
defeat RenderDoc. Everything strategic transfers; the API calls don't. See [10](10-graphics-apis.md).

### Stereo rendering strategy — same-frame replay vs alternate-eye
This is a spectrum, not a binary. BioshockVR replays **private per-eye draws within one frame**. SOMAVR
uses **alternate-frame rendering** (left eye one frame, right the next) because HPL3's pipeline has heavy
per-frame side effects (temporal, deferred) that make same-frame dual rendering expensive and sometimes
non-repeatable. SS2VR sits between — private per-eye targets but **half-rate alternate-eye** fills.
Instrument per-eye CPU/GPU cost before assuming same-frame replay is affordable — the answer flipped
between engines. And note the consequence: **any alternate-eye scheme (SS2VR, SOMAVR) bakes a non-IPD
temporal disparity into every pair** that same-frame replay doesn't have, which then needs rotation-only
latching + timewarp to hide ([10](10-graphics-apis.md)).

The external [IL-2 1946 VR mod](15-teardown-il2-1946-vr.md) anchors the far end of that spectrum and
clarifies what actually drives the choice. Its scene graph is a **replayable managed layer**, so it
renders three full passes per frame (left eye, desktop mirror, right eye) from one pose sample and one
shared prepass — and consequently has *none* of the pair-coherence bug class. **AFR is a concession to
expensive or side-effectful re-entry, not a stereo strategy in its own right.** Price the replay first;
the coherence tax is only worth paying when the replay genuinely isn't affordable.

### Which *mode* of modding applies is not an engine property — it is a licensing one

The sharpest divide across the surveyed mods in [18](18-beyond-the-native-injector.md) is not
technical. It is **what the developer released**:

| Released | Mode available | Cost |
|---|---|---|
| Engine source | Source port — compile VR in | You now ship and support an engine |
| An SDK, but an incompatible CRT | SDK as *oracle*; ship a verified patch | Reading is free, shipping is not |
| A scripting layer | Script mod as a state channel to your native DLL | Two languages, one version contract |
| A mod API (Unreal/Unity) | Managed plugin, or UEVR + companion mod | Bounded by what the API exposes |
| Nothing | Native injector | The whole anchor ladder |

A 2005 game with released source is *easier* than a 2015 game without. Age predicts almost nothing;
**check what shipped alongside the binary before you estimate anything.**

### How *many* times the engine will render is engine-specific

The stereo strategies in this fleet are not preferences — they are what each engine permitted. The
deciding property is whether the renderer's **world-execute step is reachable as a vtable slot or
function pointer** rather than welded inline into the frame loop.

| Rung | Engine property required | Seen on |
|---|---|---|
| **1 · Native stereo** | Re-entrant world execute **and** an engine camera-rebuild callable with your pose | Dunia / Far Cry 2 ([17](17-teardown-fc2vr-native-stereo.md)) — vtable slots for `PrepareFrameGraph` and `WorldExec` |
| **2 · Per-draw replay** | A hookable draw stream and reachable per-draw matrices | UE2.5 / D3D11 (BioshockVR, private eye targets + pair latching) |
| **3 · AFR** | Only a frame boundary | The general fallback ([10](10-graphics-apis.md)) |
| **4 · Reconstruction** | Per-primitive geometry with depth, and no reachable camera at all | Virtua Cop 2 ([16](16-teardown-virtua-cop-2-vr.md)) |

Rungs 1 and 4 are the two ends: rung 1 needs the engine to cooperate *more* than injection does; rung 4
needs it to cooperate not at all. Age is not the predictor — Far Cry 2 (2008, D3D9) reached rung 1 while
several newer targets here sit on rung 2.

### Whether you own the camera at all is itself engine-specific

Most projects in this comparison take the camera over and make the engine render twice. **Virtua Cop 2 VR
does the opposite** — it never finds the camera, and instead un-projects the 2D draw stream back into 3D
and re-renders that ([16](16-teardown-virtua-cop-2-vr.md)).

These are not competing styles; they fail in **opposite** conditions. Injection needs a reachable view
matrix and an engine that tolerates a second pass. Reconstruction needs neither, but needs per-primitive
geometry with depth — and it inherits a hard ceiling, because everything outside the original frustum
was culled and never submitted.

| | Own the camera | Un-project the draw stream |
|---|---|---|
| Needs a reachable view matrix | **Yes** | No |
| Needs the engine to render twice | **Yes** | No |
| Needs per-primitive geometry + depth | No | **Yes** |
| Output | A real world | A diorama of the original shot |
| Right when | The camera is yours to move | The camera was **never** yours to move |

The decision procedure — four preconditions, each with a fast test — is
[in chapter 16](16-teardown-virtua-cop-2-vr.md#when-to-reach-for-this-and-when-not-to). Run it before
concluding that a pre-2000 target is simply not moddable: *no camera object* is a reason to change
technique, not a reason to stop.

### Forward vs deferred lighting — "own the camera and stop" is only true on forward
On a forward-ish renderer (SS2/KEX), correct per-eye projection gets you most of the way. On a
**deferred** renderer (BioShock, SOMA), correct camera *and* correct per-eye WVP still leave shadows,
volumetrics, reflections, and material lighting broken, because they reconstruct from a mono
center-camera buffer. On those engines, **per-eye screen-space producers are a second workstream larger
than the projection contract itself.** Don't budget a deferred engine like a forward one.

### Which input rung actually works differs per engine
SS2VR has a real, supported **Squirrel command/verb** surface, so most controls live at rung 2 with no
native calls. BioShock ignores `SendInput` mouse-turn entirely and only responds to its native
**XInput** bridge (rung 3). SOMA needed the **exact native analog owner** — a player-helper sub-object
at `playerRoot+0x110`, not the root — before movement worked (rung 4). The [input ladder](03-input-and-locomotion.md)
is universal; *where you land on it* is not.

### How you obtain `P_center` differs
BioShock must **extract** the center projection from live `screenDataToCamera` rows — a guessed 75° FoV
left the affine residual at ~96 and rejected everything. SOMA can read `FOV=70` straight from the config
and the `a_mtxModelViewProjection` uniform. Same goal, opposite method; the strict affine gate is what
tells you which situation you're in.

### Bitness changes the entire tooling-failure class
The **32-bit** targets — BioshockVR, DishonoredVR, FarCry2-VR, Swat4-VR — make address-space exhaustion
real: RenderDoc crashes on big captures, DXGI truncates VRAM (identify GPUs by LUID), and you cannot
stack 3DMigoto + RenderDoc + the mod. The **64-bit** ones — SS2VR, SOMAVR, PreyVR — simply do not have
that trap class. Don't debug a 64-bit target expecting 32-bit failure modes, or vice-versa.

> **Corrected 2026-08-25.** This paragraph previously listed SS2VR as 32-bit. It is **x64** — KEX is a
> 64-bit remaster. That was the third page carrying the same wrong fact, and the reason it survived is
> the subject of [the note in ch00](00-engine-profiles.md#why-this-page-now-defers): the roster was
> duplicated across three pages, and the copies nobody was looking at are the ones that drifted.

### Asset/package pipeline is per-engine and non-transferable
Dark packs Squirrel + models in `.kpf`; BioShock uses non-stock Unreal `.bsm`/`.blk` indexed by
`Catalog.bdc` with a bespoke FString sign convention (stock UModel fails); HPL uses `.hps` scripts and
native semantic tables. There is no shared asset tool — each needs its own, and "the importer errored"
is never proof the asset is unusable ([05](05-assets-and-materials.md)).

### Injection timing — attach is sometimes fatal, sometimes fine
All three iterate happily on attach-to-running. But BioShock's native AimIK is built at a **one-time
construction seam** that attach can never re-trigger, and even `--launch` was too late until a
**hook-ready handshake** armed the hook before construction. SOMA and SS2 haven't needed that ceremony.
Match the injection mode to whether you're hooking a *recurring* call or a *one-time* construction
([07](07-engine-integration-safety.md)).

### Where the viewmodel lives changes its fix
BioShock draws the wrench/arm **into the HDR scene target** (a scene-depth participant, before the LDR
HUD), which is why it interacts with the shadow-depth buffer at all. On an engine where the viewmodel is
a late 2D overlay, the reference-frame fix is different. Identify which kind you have before choosing the
fix ([02](02-viewmodels-and-hands.md)).

### One game or a collection?
SS2VR, BioshockVR and SOMAVR each target **one** game in **one** process. HaloVR targets **Halo 3 inside
MCC**, where a single shipping executable hosts Halo 1–4, ODST and Reach as separate engine DLLs — so it
needs a **title registry and per-title adapters**, and every signature is scoped to a title *and* a build.
If your target is a collection, remaster bundle, or anthology, budget that indirection from day one
rather than retrofitting it around a single-title design.

### Is anti-cheat in the picture?
The first three targets are single-player games with no anti-cheat, so on-disk patching and arbitrary
hooking are merely *unwise*. HaloVR's target ships **EAC**, which makes them disqualifying: it patches no
game files, runs solely through MCC's official anti-cheat-disabled mode, and documents that the mod must
not be used in matchmaking. That constraint rules out whole techniques (file patching, some injection
routes) before design starts, and it's a compliance question as much as a technical one.

### Is the HUD capturable, or better left native?
Chapter [04](04-ui-and-hud.md) recommends tee-ing UI into a layer, and that's right for SS2VR and
BioshockVR. HaloVR tried capture/diff, got only objective text for real GPU cost, and formally accepted
the **native HUD** as the rendering path — then solved sizing and placement through authored tag data and
an anchor-basis hook instead. Measure what a capture actually yields on *your* engine before committing
to the layer architecture.

## How to use this map on the next engine

1. Run **Part 1** as a checklist — assume every shared problem is waiting for you.
2. For each **Part 2** axis, classify the new engine early (API? forward/deferred? bitness? input
   surface? viewmodel location?). Those five classifications determine which project's playbook pages
   you can copy verbatim and which you must re-derive.
   Ask two cheap questions first, because a "yes" to either reshapes the whole project: **does the engine
   have a latent stereo/multi-view path you can drive** instead of replaying draws, and **does it have a
   reflection/schema system or a symbol-bearing sibling build** that hands you its own type layouts? See
   [11](11-re-anchoring-and-discovery.md).
3. Feed new findings back here. This map is the hand-authored version of what the cross-engine graphify
   graph (staged in `cross-engine-graph/`, one repo up from this site) would surface automatically; keep
   both in sync as the mods progress.
