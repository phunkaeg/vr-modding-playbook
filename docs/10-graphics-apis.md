# Graphics APIs — The Same Spine on D3D11, OpenGL, and Older D3D

Chapter [09](09-d3d11-openxr-injection.md) is written in D3D11 terms because two of the three projects
(SS2VR, BioshockVR) are D3D11. SOMAVR is **OpenGL** (HPL3, GL 4.6). Everything strategic in chapter 09
still holds — the proof ladder, private per-eye targets, source-freshness tracking, projection
companions, render-view provenance, lane separation. What changes is the *plumbing*: how you find the
frame boundary, own render targets and state, read the projection, and submit to OpenXR. This chapter
is the translation layer. Read [09](09-d3d11-openxr-injection.md) for the concepts; read this for the
OpenGL dialect.

## The concept map

| Concept | D3D11 (SS2VR, BioshockVR) | OpenGL (SOMAVR / HPL3) |
| --- | --- | --- |
| Frame boundary hook | `IDXGISwapChain::Present` | **`gdi32!SwapBuffers`** (reached via `SDL_GL_SwapBuffers`) |
| Device/context handle | `ID3D11Device` + `ID3D11DeviceContext` | **none** — a thread-current `HGLRC` context and a global state machine |
| Render target | RTV/DSV bound with `OMSetRenderTargets` | **FBO** (`glBindFramebuffer`) with color/depth attachments |
| Projection delivery | constant buffer (`VSSetConstantBuffers`) | **`glUniformMatrix4fv`** (GLSL) *or* `glLoadMatrixf` (fixed-function) |
| Reading the projection | dump the cbuffer bytes | hook `glUniformMatrix4fv` + `glGetUniformLocation` + `glUseProgram` |
| State to save/restore | RTs, DSS, blend, VP, scissor, shaders, CBs, SRVs, samplers | bound FBO, program, matrix stacks, enables, texture units — the whole global machine |
| OpenXR graphics binding | `XR_KHR_D3D11_enable`, bind the game's `ID3D11Device` | `XR_KHR_opengl_enable`, bind the game's `HDC`/`HGLRC` |
| Swapchain image | `ID3D11Texture2D` | GL texture id enumerated from the runtime |
| Eye copy | `CopyResource` / fullscreen blit | `glBlitFramebuffer` between FBOs |
| Preferred swapchain format | `..._SRGB` | `GL_SRGB8_ALPHA8`, then `GL_RGBA8`, then `GL_RGBA16F` |

## Frame boundary: SwapBuffers, not Present

There is no `Present` in an OpenGL game. The stable first frame-boundary hook is
`gdi32!SwapBuffers`, which is what `SDL_GL_SwapBuffers` (and thus HPL's
`cLowLevelGraphicsSDL::SwapBuffers`) eventually calls on Windows. Anchor all XR work to that real
boundary; do **not** couple it to your diagnostic/logging cadence. (*SOMAVR: an early build sampled its
F8 trigger once per 120 rendered frames because XR work was tied to the log interval instead of the
swap; moving the OpenXR boundary onto every real `SwapBuffers` and letting `FrameSummaryInterval`
control only logging fixed it.*)

**A GL engine can borrow D3D11's OpenXR path without touching its renderer.** If the runtime's OpenGL
support is slow or unreliable — a real and common situation — you do not have to port the renderer.
Render into a GL texture as usual, share it via `WGL_NV_DX_interop2`, and do one small D3D11 flip-blit
into the actual XR swapchain image. (*TheDarkModVR ships exactly this: `OpenXRSwapchainGL.cpp` alongside
`OpenXRSwapchainDX.cpp` and a `D3D11Helper`, with a cvar comment naming the SteamVR OpenXR GL performance
problem as the reason.*) The cost is one extra device and one extra copy per eye per frame; the benefit is
that the entire renderer stays untouched. Worth pricing before committing to a GL-native XR path.

**Do not wire real per-frame work to a diagnostic throttle.** Engines that log "every Nth frame" invite
you to hang the frame boundary off the same interval — and then the work runs at 1/N rate while looking
correct. (*SOMAVR's XR frame trigger was sampled on a periodic summary interval and fired once per 120
rendered frames; rebinding it to fire on every real `SwapBuffers` and leaving the summary interval for log
throttling alone fixed it.*) Keep the boundary and the throttle as separate concepts.

## There is no device to bind — bind the context

D3D11's OpenXR session takes the game's `ID3D11Device`. OpenGL has no such object; the session is
created against the thread-current **`HDC`/`HGLRC`**. Two consequences:

- Record the exact `HDC`/`HGLRC` you created the session with. If the graphics binding changes (window
  recreate, context loss), that is your signal to run full runtime recovery — re-enumerate view
  configs and rebuild spaces, swapchains, and caches. (*SOMAVR does exactly this, transactionally,
  every 300 frames plus on binding change.*)
- All GL work is implicitly on the current context and current thread. You do not pass a context
  around; you must *be on the right thread with the right context current* when you touch GL. This is
  the OpenGL form of chapter 07's "do native calls on the right thread."
- **The context you see at init is probably not the one the game renders with.** Engines routinely create
  a throwaway context during startup and swap to the real one before the main loop, so code that binds
  resources to "the current context" at load time silently targets a dead context. (*SOMAVR's early
  OpenXR session probe succeeded on SOMA's startup context `hglrc=0x10000`; per-frame rendering actually
  ran on `hglrc=0x30000`, created later.*) **Bind at the first real frame, not at load** — and treat a
  changed `HDC`/`HGLRC` as full recovery, while changed recommended dimensions or sample limits get a
  transactional resource rebuild. This failure mode has no D3D equivalent: D3D hands you an explicit
  device object, so there is nothing to be implicitly current *on*.

## Own state in a global machine, not on a context object

D3D11 lets you save and restore a bounded list of bindings on the context. OpenGL is a **global state
machine**: the bound FBO, current program, matrix mode and stacks, every `glEnable`, active texture
unit, and viewport are all process-global and sticky. A private-eye replay or blit that leaves any of
them changed corrupts the game's next draw. Save/restore is broader and less forgiving than the D3D11
list in chapter 07 — treat FBO binding, program, viewport/scissor, and the enable bits as the minimum,
and prefer a scoped guard that captures and restores them around every private operation.

**The specific trap this creates: a stale scissor silently deletes draws, with no error.** Viewport and
scissor outlive the render-target switch that made them valid, so when you retarget a pass into a
differently-sized surface, a scissor left over from the previous target can fall entirely outside your new
one — and every draw is clipped to nothing. (*SOMAVR's broken terminal tiles traced to exactly this: the
native renderer issued scissor rectangles outside the `1024×577` capture viewport in use that frame.
The first fix bypassed only **zero-intersection** scissors, only during capture, on the owning render
thread, restoring GL state immediately afterwards — with bounded telemetry so the bypass count is itself
evidence.*) When a retargeted pass produces nothing and GL reports success, check the scissor before you
check anything else.

### CORRECTION: translate the scissor, do not disable it {#translate-dont-disable-scissor}

**Bypassing every zero-intersection scissor recovers pixels while destroying authored clipping** — list
panes, email regions and dirty rectangles become tiles or flashes. The clips are not garbage; they are in
**the wrong coordinate space**. `[LIVE]`

The engine authors GUI clips against **its own cached render-target viewport**, and a mod that binds a
private FBO *directly through GL, behind the engine's state cache*, leaves GL on the new framebuffer
while the engine keeps emitting clips in the **source** framebuffer's coordinates. SOMAVR's capture
target was `0,0,1024,577` while HPL emitted fully offscreen clips like `(20,886,230,116)` and
`(24,1797,446,224)` — and subtracting a source-viewport origin near `(256,768)` maps an offscreen clip at
`(532,886)` back to a valid `(276,118)`. **A translation, not noise.**

The order that preserves authored clipping:

1. save the original scissor **and the engine/source viewport** before rebinding the private target;
2. if the original scissor already intersects the capture viewport, **leave it alone**;
3. otherwise translate its origin into capture coordinates —
   `captureX = sourceScissorX - sourceViewportX + captureViewportX` (and likewise for Y);
4. apply the remapped clip **only if it now intersects** the target;
5. restore the exact original scissor immediately after the draw;
6. disable the scissor **only as a logged fallback**, for a clip that cannot be mapped.

**Cheap discriminator, before any of that:** give the overlay a **known opaque background**. If the
background stays stable while only the content flashes, the composition layer never disappeared —
so investigate the source render and capture path, not OpenXR alpha, layer ordering or the layer budget.

**Scope caution, stated by the reporting project:** the evidence proves a **translation**, not a general
scale transform. If source and target extents differ, measure the engine's coordinate convention before
adding scaling or axis inversion.

Private per-eye targets are **FBOs** with their own color and depth attachments, the direct analogue
of chapter 09's private RTV/DSV pair. The same rules apply unchanged: independent depth per eye, clear
once per eye view (not per draw), and keep the game's default framebuffer path intact until the private
path is proven.

## Reading the projection: hook the uniform upload

You cannot "dump the cbuffer" in OpenGL. HPL3 delivers matrices as **shader uniforms**, so the
projection probe is a hook set:

- `glUseProgram` to track the current program,
- `glGetUniformLocation` to map `(program, location)` → uniform *name*,
- `glUniformMatrix4fv` to catch the actual matrix uploads and their cadence.

Then anchor semantically, not by raw offset: HPL3's projection-like uniform is named
`a_mtxModelViewProjection` (companions `a_mtxInvViewProjection`, `a_mtxTemporalProjection`), and the
camera config values `FOV=70`, `NearClipPlane=0.03`, `FarClipPlane=1000` are stable string/number
anchors. (*SOMAVR confirmed the main scene projection is uniform-driven, not fixed-function:
`fixedProjection={valid=0}` while `uniformProjectionName="a_mtxModelViewProjection"` showed
`fovYDeg=70.0` — proving where to look before any hook mutated anything.*)

**That hook set is necessary but not sufficient: uniform *buffers* bypass it entirely.** Passes that
source their matrices from a bound UBO range never call `glUniform*`, so a `glUniformMatrix4fv` hook
reports nothing for them and you conclude — wrongly — that those passes don't use a projection.
(*SOMAVR's deferred shadow programs `942`/`944` and the reflection/water program `989` all drew their
view/projection and SSR parameters from bound uniform-buffer ranges; the plain uniform hook silently
missed every one until UBO binding and contents were captured per program **and per eye**.*) Budget for a
second interception path — capture buffer bindings and their contents — or your matrix census will
quietly cover only some of the frame. The same warning applies to D3D constant buffers; the difference is
that in OpenGL the single-uniform path looks complete enough to fool you.

A related payoff: once you can read the uniform block, **fix a mismatched value at its native owner, not
in the block.** (*SOMAVR found the per-eye horizontal projection centre at uniform-block offset `96`
alternating `-0.242513`/`+0.242513` across eyes; correcting it in the native camera packet drove the
captured values to `0/0`, whereas patching the shader constant would have fought the engine's own write
every frame.*) Uniform/constant diffing is an excellent **attribution** tool and a poor **fix** site.

Do not assume a modern core-only renderer. HPL uses a **compatibility profile**: fixed-function paths
(`glLoadMatrixf` after `glMatrixMode(GL_PROJECTION)`, `glTexEnvfv`) coexist with GLSL. That
compatibility call (`glTexEnvfv`) is also why **RenderDoc may refuse or destabilize the capture** —
plan a capture-independent inspection route (chapter 06) from the start on an OpenGL compatibility
engine.

The hook itself, since "hook the uniform upload" is doing a lot of work in that sentence. In GL there is
no device object to intercept — you replace the exported entry points and filter by the uniform's
*location*, which you resolve once per program:

```c
/* GL has no per-draw constant buffer to inspect: the matrix arrives through
   glUniformMatrix4fv, identified only by a location int. Resolve name -> location
   once per program, then filter every upload against it. */
static PFNGLUNIFORMMATRIX4FVPROC real_glUniformMatrix4fv;

typedef struct { GLuint prog; GLint loc_mvp; GLint loc_proj; } prog_slots;
static prog_slots g_slots[256];
static int        g_nslots;

static prog_slots *slots_for(GLuint prog)
{
    for (int i = 0; i < g_nslots; ++i)
        if (g_slots[i].prog == prog) return &g_slots[i];
    if (g_nslots == 256) return NULL;

    prog_slots *s = &g_slots[g_nslots++];
    s->prog     = prog;
    /* HPL3's names; yours come from the shader source or a GL capture. */
    s->loc_mvp  = glGetUniformLocation(prog, "a_mtxModelViewProjection");
    s->loc_proj = glGetUniformLocation(prog, "a_mtxProjection");
    return s;
}

void APIENTRY hk_glUniformMatrix4fv(GLint location, GLsizei count,
                                    GLboolean transpose, const GLfloat *value)
{
    GLint prog = 0;
    glGetIntegerv(GL_CURRENT_PROGRAM, &prog);
    prog_slots *s = slots_for((GLuint)prog);

    if (s && count == 1 && (location == s->loc_mvp || location == s->loc_proj)) {
        mat4 m;
        memcpy(&m, value, sizeof(m));
        if (transpose) m = transpose4(m);      /* GL callers pass either; normalise */

        if (g_stereo_active) {
            m = apply_eye(m, g_current_eye, location == s->loc_proj);
            real_glUniformMatrix4fv(location, 1, GL_FALSE, (const GLfloat *)&m);
            return;
        }
        record_flat_matrix(location == s->loc_proj ? MTX_PROJ : MTX_MVP, &m);
    }
    real_glUniformMatrix4fv(location, count, transpose, value);
}
```

Three GL-specific hazards are visible in those twenty lines:

- **`transpose` is a per-call argument, not a convention.** The same engine can pass `GL_TRUE` from one
  call site and `GL_FALSE` from another. Normalise on entry or your maths is silently transposed.
- **A uniform location is only meaningful for one program.** Caching `loc_mvp` globally and applying it
  to a different shader edits an unrelated uniform — a bug that looks like corrupted geometry.
- **`glGetIntegerv(GL_CURRENT_PROGRAM)` inside a hot hook is a real cost.** Cache it against the
  `glUseProgram` hook once the probe is proven; do not optimise before you have the matrix.

## Projection companions are an OpenGL problem too

Chapter 09's "changing WVP alone breaks reconstruction" is not a D3D11 quirk — it is a rendering fact
that reappears in GLSL. HPL3's **deferred lighting reconstructs view-space position from screen
coordinates**, reading inverse-projection/view and screen-reconstruction values from GL uniform
blocks. So stereo geometry can be perfectly per-eye while lighting/shadows stay wrong because they
reconstruct from a mono-centred projection. (*SOMAVR: with correct per-eye WVP, an asymmetric
projection-*center* offset — UBO offset 96 reading `-0.242513 / +0.242513` for the two eyes — moved the
reconstructed world position under pitch and produced a sharp diagonal ceiling/shadow boundary;
centering horizontal projection to `0 / 0` removed the eye disagreement, and a residual vertical center
offset of `-0.193187` remained the next suspect.*) This is the exact "mono screen-space buffer" and
"projection companion" failure from chapter 09, in OpenGL, via UBOs instead of cbuffers.

## AFR: a legitimate first stereo path when re-entry is expensive

D3D11 projects here replayed private per-eye draws in one frame. SOMA's HPL3 render pipeline has heavy
per-frame side effects (temporal effects, deferred passes, timestamped stages) that make same-frame
dual rendering expensive and, in places, non-repeatable. **Alternate-frame rendering** — render the
left eye one frame, the right the next, and hold/transfer each eye image — was the pragmatic first
stereo experiment. It keeps the ownership split (HPL bridge builds the eye view, the XR runtime records
the exact pose/FOV, the GL bridge retains and transfers the eye image) and can fall back to the proven
mono path without recreating OpenXR resources. Budget it honestly: instrument per-eye CPU and
non-blocking GPU timestamp queries to prove whether same-frame dual render is even affordable before
committing to it. (*SOMAVR uses `GL_TIMESTAMP` query rings, never blocking for results, attributed to
the active AFR eye.*)

AFR is not SOMA-specific — **SS2VR renders half-rate alternate-eye too**, so the coherence rules below
apply to any scheme where the two eyes of a pair are rendered at different sim times (not just OpenGL).

**The counter-case is worth knowing before you commit.** The external
[IL-2 1946 VR mod](15-teardown-il2-1946-vr.md) is also OpenGL, also on a legacy engine — and takes the
opposite route: three full scene passes per frame (left eye FBO, desktop mirror, right eye FBO) driven
from **one** HMD pose sample and one shared prepass. It can, because its render orchestration lives in a
managed layer that replays cleanly and has no temporal state to corrupt. The result is that **every rule
in this section simply does not apply to it** — no inter-eye yaw, no eye-phase desync, no blackout
masking bad pairs. So: measure the cost of replaying the scene *before* accepting AFR. AFR buys you
frame time and charges you a permanent coherence tax; when replay is cheap, that is a bad trade.

## AFR stereo coherence: the disparity you bake in, and how to hide it

If the left and right eyes are rendered on different frames, and the sim/game-camera advances between
them, every stereo pair carries a **non-IPD disparity**: a world yaw plus one frame of animation. It
reads as strain/ghosting *while moving* and is invisible at rest — which is exactly why it survives
casual testing. Measure it before theorizing (a per-pair audit), and treat these as the working rules:

- **Quantify it.** (*SS2VR: inter-eye world yaw was ~`0.025°` standing — the numerical noise floor — but
  `0.77°` mean / `44.98°` worst while moving, and inter-eye camera *translation* reached ~`6 cm` moving,
  rivaling the `6.4 cm` IPD itself. A pair that disagrees by more than an IPD is not a stereo pair.*)
- **Use one XR frame — one `xrWaitFrame`, one `xrLocateViews`, one predicted display time — per
  *pair*, not per present.** If each eye of a pair runs its own `xrWaitFrame`, the two images get
  *different* predicted display times while both were rendered from *one* head sample. The compositor
  then reprojects them by different amounts, producing motion-dependent shear, and your effective tick
  halves. (*An independent BioShock mod's first headset stereo test passed but "eyes feel weird on head
  movement"; holding one XR frame open across the left present and completing it on the right fixed it —
  user verdict "a looot better… comfortable now." See [13](13-teardown-bioshock-vr.md).*)
- **Latch the game-camera *rotation* across the pair, never the position.** Replaying eye0's view
  rotation on the eye1 frame collapses inter-eye yaw to the noise floor (`0.77°`→`0.003°`) and makes the
  pair *uniformly* stale — which is precisely what compositor timewarp corrects. Latching *position*
  instead would render a camera-relative viewmodel displaced by the full ~6 cm baseline at ~40 cm from
  the face, worse than the error you fixed. (This is why UEVR's plain-AFR latch is rotation-only by
  deliberate choice.)
- **Close the eye-phase toggle against a real fill.** Self-toggling `currentEye` every "should-render"
  frame without checking whether an eye was *actually* filled means a single skipped fill (null scene
  texture, swapchain not ready) desyncs the pair **permanently** — it does not self-heal; only a view
  reset cures it. Gate the toggle on `eyeFilledThisFrame`, and instrument *which* bail condition fired
  rather than assuming the toggle was root cause.
- **The comfort blackout is also masking broken pairs, not just vection.** A snap turn straddling a pair
  produces ~`44–45°` inter-eye yaw (one eye pre-snap, one post); a recenter straddling a pair spikes the
  rendered view while the input camera barely moved. The snap/recenter blackouts (chapter
  [01](01-camera-and-tracking.md)) hide these transient bad pairs — turning them off exposes them.
- **Know when depth submission helps.** `XR_KHR_composition_layer_depth` feeds only *positional*
  timewarp (parallax, near geometry, head translation); rotational reprojection is depth-free by
  geometry, so half-rate stale pairs already get correct rotational correction without it. At 90 Hz the
  uncorrected translation is ~11 mm ⇒ ~`1.5°` worst-case on a 40 cm viewmodel, near-zero at room scale.
  If you do build depth, the reversed-Z convention is the trap (wrong near/far produces no error, just
  subtle world wobble), and ordered immediate-context copies + ordered submit suffice — no GPU
  fences/queries needed (UEVR's D3D11 path uses none).
- **Audit every temporal pass before choosing alternate-eye at all.** Under alternate-eye the "previous
  frame" is *the other eye*, so TAA, temporal denoisers, previous-frame-sampling SSR, auto-exposure
  adaptation, and anything driven by motion vectors will blend the eyes together — and motion vectors
  themselves come out encoding the IPD shift as world motion. A pre-TAA engine has almost nothing to
  corrupt; a TAA-era engine may rule the whole approach out. See the
  [render-pass hazard atlas](14-render-pass-hazard-atlas.md).
- **A residual flicker on a near viewmodel held still at an angle is usually this pair-slip, not a bug in
  whatever feature you're testing.** (*SS2VR chased it as a hand-collision bug until parking the hand
  far from any wall still flickered, orientation-dependent. It's invisible to RenderDoc because it's a
  compositor-level inter-frame artifact.*)

The D3D11 equivalent is a different problem: the matrix is already in a constant buffer, so you are
looking for *which* buffer and *where in it* — and the read-back path has a known trap.

```cpp
/* The cbuffer is GPU-resident and usually not CPU-readable. You cannot Map() it.
   Stage a copy, then read the staging resource. */
bool ReadConstantBuffer(ID3D11DeviceContext* ctx, ID3D11Device* dev,
                        ID3D11Buffer* src, std::vector<uint8_t>& out)
{
    D3D11_BUFFER_DESC bd{};
    src->GetDesc(&bd);

    /* Classify by the LIVE byte width, never by the reflected size: BioshockVR
       measured reflection saying 544/752/560 where GetDesc said 576/832/1088. */
    D3D11_BUFFER_DESC sd = bd;
    sd.Usage          = D3D11_USAGE_STAGING;
    sd.BindFlags      = 0;
    sd.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
    sd.MiscFlags      = 0;

    Microsoft::WRL::ComPtr<ID3D11Buffer> staging;
    if (FAILED(dev->CreateBuffer(&sd, nullptr, &staging))) return false;

    ctx->CopyResource(staging.Get(), src);

    D3D11_MAPPED_SUBRESOURCE map{};
    if (FAILED(ctx->Map(staging.Get(), 0, D3D11_MAP_READ, 0, &map))) return false;
    out.assign((uint8_t*)map.pData, (uint8_t*)map.pData + bd.ByteWidth);
    ctx->Unmap(staging.Get(), 0);
    return true;
}

/* Find a 4x4 at an unknown offset: slide a window and test for matrix-ness.
   Far more reliable than trusting a reflection offset you did not verify. */
std::vector<size_t> FindMatrixCandidates(const std::vector<uint8_t>& buf)
{
    std::vector<size_t> hits;
    for (size_t off = 0; off + 64 <= buf.size(); off += 4) {   // 4-byte stride: it
        float m[16];                                           // is NOT always 16-aligned
        memcpy(m, buf.data() + off, 64);

        bool sane = true;
        for (float v : m)
            if (!std::isfinite(v) || std::fabs(v) > 1e7f) { sane = false; break; }
        if (!sane) continue;

        /* A projection matrix has a hard tell: w comes from -z, so m[11] is +/-1
           and m[15] is 0. A view/world matrix has the affine row 0,0,0,1. */
        bool proj   = std::fabs(std::fabs(m[11]) - 1.f) < 1e-3f && std::fabs(m[15]) < 1e-6f;
        bool affine = std::fabs(m[15] - 1.f) < 1e-6f &&
                      std::fabs(m[3]) < 1e-6f && std::fabs(m[7]) < 1e-6f &&
                      std::fabs(m[11]) < 1e-6f;
        if (proj || affine) hits.push_back(off);
    }
    return hits;
}
```

**Do not stop at the first candidate.** FarCry2-VR's camera hunt rejected two decoys — a shadow view and
a viewmodel matrix — that were structurally perfect matrices, and separated them from the real scene
camera on FOV mismatch. Structure tells you it *is* a matrix; only behaviour over time tells you *whose*.
Cross-check every candidate against [11](11-re-anchoring-and-discovery.md)'s constancy test: a matrix
whose `distinct_values` is 1 across the frame is not a camera, whatever its shape.

## Three routes from D3D9 to an XR runtime, and how to choose {#d3d9-xr-interop-routes}

D3D9 has no OpenXR graphics binding, so every D3D9 project must bridge to an API that does. Three
projects in this survey solved it three different ways, which is the useful part - the choice is real,
not a matter of taste. `[SOURCE]`

| Route | Mechanism | Taken by |
|---|---|---|
| **D3D9Ex shared texture -> D3D11** | `IDirect3D9Ex` creates a shared render-target texture; `ID3D11Device::OpenSharedResource` opens the handle | CallOfDuty4_VR |
| **D3D9Ex -> D3D11 via a SurfaceQueue** | A queue object marshals surfaces between the two devices | gmcl_openvr |
| **`Direct3DCreate9On12` -> D3D12** | The 9On12 layer wraps D3D9 calls onto a D3D12 device; unwrap the underlying resource | DishonoredVR |

**The shared-texture route in concrete terms**, from CallOfDuty4_VR's probe:

```cpp
direct3D9Ex->GetAdapterLUID(...)                    // must match the OpenXR-requested adapter
CreateTexture(..., D3DUSAGE_RENDERTARGET,
                   D3DFMT_A8R8G8B8,
                   D3DPOOL_DEFAULT, &sharedHandle)  // shared handle out-param
openXrD3D11Device->OpenSharedResource(sharedHandle, ...)
```

Note the requirements that are not optional: **`D3D9Ex`, not plain D3D9** (plain `Direct3DCreate9`
refuses shared resources outright - DishonoredVR recorded the exact failure, `0x8876086C`),
`D3DPOOL_DEFAULT`, `D3DUSAGE_RENDERTARGET`, and an adapter LUID that matches the one the runtime asked
for.

### Prove it before you build on it, without touching the game's renderer

The shape worth copying is their probe's contract - a **one-time, non-invasive proof** that creates a
temporary device and does not replace the game's renderer, asserting four things in order:

1. `Direct3DCreate9Ex` is available at all;
2. a D3D9Ex adapter **matches the OpenXR-requested DXGI adapter LUID**;
3. a D3D9Ex render-target texture can be opened and read by D3D11;
4. the **currently running game device appears to use the same adapter**.

Step 4 is the one that is easy to omit and expensive to discover later: the bridge working in isolation
says nothing about whether the *game's* device is on the same GPU. On a laptop with switchable graphics
it frequently is not.

**Adapter LUIDs are per-boot handles**, not stable identifiers - DishonoredVR observed the same card
reporting `0001667A` on one boot and `00016A92` on another. Compare them within a session; never persist
one.

Two more constraints, from the SurfaceQueue variant: a **format whitelist that collapses sRGB**, and a
16x16 staging-texture `Lock` used purely as a synchronisation point. If your bridged image is correct but
one frame stale, look there before suspecting your pose pipeline.

### Who creates the 9On12 device: the game does, and you adopt it {#who-owns-9on12}

The intuitive order is inverted, and getting it wrong is a day. `[LIVE]`

**You do not create a D3D12 device and hand it in.** You pass `D3D9ON12_ARGS` with `Enable9On12 = TRUE`
and nothing else, let the **game** create its device, then **adopt** the D3D12 device out of it via
`GetD3D12Device`.

**Match adapters by LUID, never by index or name** - DXGI enumerated **four entries for one physical
GPU** on the machine where this was measured, so index and name are both ambiguous and the LUID is not.

### Any D3D9 device YOU create must copy the game's behaviour flags {#fpu-preserve-contagion}

UE3's D3D9 RHI builds `BehaviorFlags` with **`D3DCREATE_FPU_PRESERVE` unconditionally**, plus vertex
processing, `D3DCREATE_DISABLE_DRIVER_MANAGEMENT`, and `MULTITHREADED` only under Games-for-Windows-Live.
Three consequences for any UE3 D3D9 target, and the second is a live hazard on the 9On12 route:
`[SOURCE]`

1. The game's render thread is **not** running at 24-bit x87 mantissa.
2. **A device the mod creates without `D3DCREATE_FPU_PRESERVE` reprograms x87 precision *process-wide*,
   underneath the running game** - silently corrupting its arithmetic. This is the
   [FPU-precision hazard](06-debugging-methodology.md#self-proving-instrument) arriving through your own
   device creation rather than the game's.
3. The game always passes `D3DADAPTER_DEFAULT`, so **there is no in-game lever** to make its device agree
   with the runtime's chosen adapter.

### Device loss: three faults behind "VR didn't survive alt-tab" {#device-loss-three-faults}

`[LIVE]`

- **`CreateRenderTarget` and `CreateDepthStencilSurface` are ALWAYS `D3DPOOL_DEFAULT`.** There is no pool
  argument, which makes it easy to miss - you never typed the thing you now have to release.
- **In exclusive fullscreen an engine may never call `Reset` at all**, so a carefully built
  release-before-Reset path is never reached.
- **The expensive one: never latch device-lost state from a function the engine can stop calling.** One
  project latched from `TestCooperativeLevel`, the engine stopped calling it, the flag never cleared, and
  the redirect stayed off permanently. **Poll from `Present`** - the one call a running game cannot stop
  making.

## D3D9 silently degrades your floating-point precision {#d3d9-x87-precision}

A trap that applies to **every D3D9-era injector** and produces no error at all. `[SOURCE]`

Creating a D3D9 device without `D3DCREATE_FPU_PRESERVE` lets the runtime reprogram the x87 control word
to **24-bit mantissa** - single precision - for the whole thread. Every `double` in your pose maths from
that point on quietly computes at float precision.

Nothing warns you. The symptoms are the ones you would blame on your own maths: drift that accumulates
over a session, a basis that fails an orthonormality check by a margin that looks like it should have
passed, quaternion normalisation that will not settle.

**Check for it explicitly rather than trusting a tolerance.** The control word is readable, and a pose
pipeline that asserts its own precision at init costs nothing. This matters most to projects on
[D3D9 targets](#d3d9-and-d3d10-there-is-no-openxr-binding-at-all), where the transport work is already
hard enough without an invisible precision floor underneath it.

## D3D9 and D3D10: there is no OpenXR binding at all

This is the hardest API case, and it is common — anything from roughly 2004–2010 is likely D3D9, with
D3D10 as an occasional selectable path. **OpenXR defines graphics bindings for D3D11, D3D12, OpenGL,
OpenGL ES and Vulkan. It defines none for D3D9 or D3D10.** You cannot create a session on the game's
device, so the zero-copy "bind the game's device" model in this chapter simply does not apply. You need
a **bridge to an API OpenXR does speak**, and that choice is a project-shaping decision — de-risk it
before designing anything downstream.

Three routes, in rough order of preference:

**1. Shared surface to D3D11 (the cheap case — but check two things first).** If the game is D3D10 or
D3D9**Ex**, its render targets can often be shared to a D3D11 device through a DXGI shared handle, and the
OpenXR session lives on the D3D11 side. (*FarCry2-VR's target runs D3D10 and reached "the cheap DXGI
shared-surface case."*)

For **plain** D3D9 this route is not merely harder — it is closed until you change the device, and two
independent projects have now mapped the constraint precisely:

- **A plain (non-`Ex`) D3D9 device cannot create a shared resource at all.** (*DishonoredVR proved it by
  negative control: the `Direct3DCreate9` device — the call the game itself makes — refused a
  `D3DUSAGE_RENDERTARGET | D3DPOOL_DEFAULT` shared-handle `CreateTexture` with `0x8876086C`
  `D3DERR_INVALIDCALL`. Only a `Direct3DCreate9Ex` device produced a shared `D3DFMT_A8R8G8B8` target that
  `ID3D11Device::OpenSharedResource` then opened — verified with two distinct fill colours so a stale or
  zeroed mapping couldn't fake the result.*) So this route requires hooking device creation and
  **upgrading the game to `Ex`**.
- **But `D3D9Ex` forbids `D3DPOOL_MANAGED` outright**, and changes device-lost/reset semantics. If the
  game allocates from the managed pool — as older titles routinely do — upgrading its device breaks it.

Put those together with the other known blocker and you get a decision you can make **statically, before
building anything**:

| Game's device | Uses `D3DPOOL_MANAGED`? | Route |
|---|---|---|
| D3D10, or already D3D9`Ex` | — | **Route 1.** Share directly. |
| Plain D3D9 | No | **Route 1**, after upgrading device creation to `Ex`. |
| Plain D3D9 | **Yes** | **Route 2.** Ex is closed to you; managed resources cannot be shared *and* `Ex` won't allocate them. |

*That bottom row is exactly where Swat4-VR landed: `D3DPOOL_MANAGED` for ordinary textures falsified route
1 for them, and they took the 9On12 path below. DishonoredVR then landed there too — its UE3 `D3D9Drv`
allocates ordinary textures, cube textures and static vertex/index buffers from the managed pool, which
killed its own earlier spike's recommendation to upgrade the device to `Ex`.* **Do that audit statically
first; it is a text search over the target build, and it decides your architecture.**

Three hard-won details from that audit, because this is where the route goes wrong:

- **Reading the pool out of a decompiled call is argument-index-sensitive — cross-check it.** DishonoredVR
  confirmed its result twice against values that could only be right by construction: the index-buffer
  format decompiled to `0x65`/`0x66` (exactly `D3DFMT_INDEX16`/`INDEX32`), and the texture usage flags
  were built from the *same two bits* that select the pool. (It also got lucky in a way worth knowing: that
  build's assertion macros embed the **original source expression**, so `GetD3DTexturePool(Flags)` is named
  in the binary rather than inferred from a bare immediate.)
- **Remapping `MANAGED` to `DEFAULT` is not a rescue, and the reason is structural.** The managed pool's
  entire purpose is that the runtime restores content after device loss — so an engine that uses it has no
  restore logic for those resources **by construction**. Remapping means writing device-loss restore for
  all art and static geometry: exactly the code that was never written.
- **Use `Direct3DCreate9On12`, never `Direct3DCreate9On12Ex`.** Both exist and the `Ex` name looks like the
  more capable choice; it is precisely the wrong one, because **an `Ex` device forbids `MANAGED` whatever
  backs it.** 9On12 (non-`Ex`) implements the managed pool over D3D12, so the game's allocations keep
  working while the resources become reachable as D3D12 — which is the whole point. On a 32-bit target,
  check `SysWOW64\d3d9.dll` exports `Direct3DCreate9On12` and that `d3d9on12.dll` is present.

Note what does **not** change when you discover you are on the bottom row: the hook site. You were always
going to intercept `Direct3DCreate9`; only the replacement call differs. And one gate moves to the top of
your list — **confirm the runtime advertises `XR_KHR_D3D12_enable`**, which needs no headset, because a
D3D11-only runtime forces a further D3D12→D3D11 shared-resource hop.

Two more measured facts about route 1 on a D3D9 origin, both worth budgeting for:

- **D3D9Ex shared surfaces have no keyed mutex.** The only producer/consumer barrier available is an
  `IDirect3DQuery9` event query — which blocks until **all** outstanding GPU work completes, not just your
  copy. (*Measured at 0.164–0.189 ms median, up to 0.78 ms p95 — dominating the total, and staying flat
  when surface area more than doubled from 1920×1080 to 2064×2096. The cost is the wait, not the blit.*)
  And those numbers came off an **idle** GPU; inside a real game the same query drains a full rendered
  frame. Treat idle-GPU screening figures as a floor, never as a budget.
- **The format may cross with no conversion at all — but verify rather than assuming either way.**
  (*`D3DFMT_A8R8G8B8` opened on the D3D11 side as `DXGI_FORMAT_B8G8R8A8_UNORM`, which the OpenXR runtime
  already accepted for its swapchain. No negotiation layer was needed anywhere in the
  D3D9→D3D11→OpenXR chain.*) Probing the actual mapping before designing a conversion path can delete a
  whole subsystem from your plan.

**2. `D3D9On12` → D3D12 → `XR_KHR_D3D12_enable` (the proven route for plain D3D9).** Run the game's D3D9
on Microsoft's D3D9-on-D3D12 mapping layer, call `UnwrapUnderlyingResource` to obtain the D3D12
resource behind a D3D9 surface, and create the OpenXR session on that D3D12 device.
(*Swat4-VR validated exactly this in-headset — a live, per-eye-distinct stereo pair — after route 1 was
falsified. Its falsifier is worth knowing: the game uses **`D3DPOOL_MANAGED`** for ordinary textures,
and managed resources cannot be shared, which kills device-substitution approaches. Check pool usage
early; a conditional breakpoint on the creation call answers it in minutes.*)

**3. A 64-bit companion compositor (the fallback of last resort).** A separate process owns the OpenXR
session and receives eye textures via shared handles and poses via shared memory. Keep this designed but
unbuilt unless the in-process routes fail — it doubles your process count and your failure modes.

Two more D3D9-era facts that shape the work: these targets are almost always **32-bit**, so the entire
32-bit trap class applies (RenderDoc failing on address-space exhaustion, DXGI truncating VRAM — see
[06](06-debugging-methodology.md)); and they frequently predate TAA, which per
[14](14-render-pass-hazard-atlas.md) makes alternate-eye far more viable than on a modern target.

**Prove the bridge outside the game first.** Build a standalone experiment with **no game and no
injection** — create the device, make the surface, push it through the bridge, submit to OpenXR — and
give it a **headset-free flat gate that reads the pixels back and verifies them**. That way the whole
interop question is answered before you touch the target, and a failure is unambiguous rather than
tangled up with injection. (*Swat4-VR's `r1_interop` does this, with `--probes-only` for the
no-headset path; it is why their route decision took days rather than weeks.*)

The decision that actually matters on those paths is which interop route you take, and it is worth
writing the test rather than reasoning about it:

```text
D3D9  --IDirect3DDevice9Ex::GetSharedHandle-->  shared surface  --> D3D11 OpenXR swapchain
D3D9  (plain, non-Ex)                        -->  no shared handle: CPU round-trip or 9On12
D3D10 --IDXGIResource::GetSharedHandle----->  D3D11 OpenDevice   --> XR swapchain
GL    --WGL_NV_DX_interop2----------------->  D3D11 texture      --> XR swapchain
```

The GL row is worth pricing even when a native GL XR path exists: *TheDarkModVR renders into a GL
texture, shares it via `WGL_NV_DX_interop2`, and does one small D3D11 flip-blit into the real XR
swapchain — GL renderer untouched — because SteamVR's OpenXR GL path is slow.* One blit can beat a
supported path.

## Vulkan: the submit lifecycle is atomic, and partial skips destroy the device {#vulkan-submit-lifecycle}

KSA-XR is the first Vulkan target in this survey - an OpenXR mod for a pre-alpha game on the BRUTAL
framework, a thin C# layer over Vulkan, GLFW and ImGui, with **no high-level engine abstraction to hook**.
Its collaboration rules read like a list of scars, and two of them are the important ones. `[SOURCE]`

> Do not suppress a renderer acquire or submit operation independently. **Acquire, command recording,
> queue submission, semaphore/fence transitions, and presentation form one lifecycle.** Partial skips
> have previously caused `NotReady`, freezes, and `VK_ERROR_DEVICE_LOST`.

This is the same shape as the [D3D12 warning](19-d3d12-and-performance.md) - a recorded command list can
be legally resubmittable and still semantically unreplayable - but Vulkan makes it sharper, because the
**synchronisation primitives are yours to keep balanced.** In D3D11 you can often skip a draw and get
away with it. In Vulkan, skipping one stage of the frame leaves a semaphore unsignalled or a fence never
waited on, and the failure arrives later and looks like a driver bug.

**The rule to carry into any explicit-API target: the unit you may skip is the whole frame, not a stage
of it.** If you want a frame not to present, do not suppress the present - drive the whole lifecycle and
discard the result.

Their second rule is about how you earn the right to try:

> Do not propose an eye `Viewport` or direct `RenderViewport` call without first proving all required
> framebuffer, render pass, command-buffer, and image-lifetime assumptions. Previous direct calls failed
> inside `BeginRenderPass` with invalid Vulkan state.

### Three full frames per displayed frame is a real starting architecture {#vulkan-three-frame-proof}

Their proof of concept renders **one desktop frame and two XR eye frames by running three complete game
frames**, copying each eye out of the main viewport's offscreen colour image into an OpenXR swapchain
image. They call it knowingly inefficient, and it produces correct stereo.

That is worth recording because **BioshockVR reached the identical architecture independently**, and
eliminating the third (desktop) world render is its current named performance blocker. Two projects, two
engines, two graphics APIs, same first-working shape and the same next problem: *the desktop mirror is a
third full render until you make it a copy.*

Scrap Mechanic supplies the worked D3D11 version of that next step. After the eye is finished, its mirror
path binds the left-eye SRV and desktop backbuffer RTV, updates one aspect-crop constant, sets no vertex
buffer and issues `Draw(3, 0)`. The log's acceptance line is explicit: `left eye ... aspect-cropped into
PC backbuffer ... without a third full scene render`. `[SOURCE]`

Note also what having no engine abstraction costs. With Vulkan and no renderer to speak of, the seam is
whatever the game's own frame function is - which is why their guidance is "prefer small, well-targeted
patches and explicit operations over broad attempts to replace the game's renderer."

## One register carries several matrices - validate content, not just location {#validate-every-upload}

Filtering uploads by uniform location or constant register proves **where** a value arrived. It proves
nothing about **what** it is, and Mirror's Edge VR found the difference the expensive way. `[SOURCE]`

> The derived FOV alternates between the scene view-projection and something at **160 x 160 degrees** on
> consecutive uploads to the same register - a shadow or light transform. Injecting into it corrupts
> that pass, and does so **invisibly**: the symptom appears somewhere else entirely.

**A shadow or light pass reuses the same constant slot as the scene camera**, because from the engine's
point of view it is the same shader input. Write your stereo offset into it and you have moved a light
frustum; nothing about the failure points back at the register you touched.

Their rule is the one to carry:

> **The register says where to look. It is never permission to modify.**

**Gate every upload with the same test that found the matrix in the first place.** Theirs is the
`clip.w` cancellation from [A3](a3-stereo-projection.md): a world-to-clip matrix maps the camera position
to `clip.w` near zero, and nothing else arriving in that register does. The cost argument matters,
because it is what makes per-upload validation practical rather than theoretical: **four multiply-adds
against a camera position cached once per frame**, where `c0` is written thousands of times a frame and
a memory read per call would be absurd.

**And the ratio is why a one-shot validation would have missed it**: **220,000 accepted against 91
rejected**. The foreign matrix is *rare*. A validation run at startup, or a spot check during
development, sees the scene matrix every time and concludes the register is safe - which is
[an unstressed optimistic claim](pattern-catalog.md#meta-007) in its purest form. Only a gate on every
write catches something that happens once in two thousand uploads.

## Forcing windowed mode on a D3D8/9 game takes three overrides {#force-windowed}

A VR mod usually wants the game windowed - for capture, for overlays, for not owning the display. On a
2003-era title that is not one flag. Manhunt VR's chain, after ten attempts: `[SOURCE]`

| Field | Game's value | Override | Why |
|---|---|---|---|
| `Windowed` | `FALSE` | `TRUE` | the obvious one |
| `SwapEffect` | `D3DSWAPEFFECT_FLIP` | `D3DSWAPEFFECT_DISCARD` | **`FLIP` cannot be used for windowed swap chains** - documented, and a real restriction |
| `FullScreen_PresentationInterval` | `IMMEDIATE` (`0x80000000`) | `DEFAULT` | **this driver rejects `IMMEDIATE` for a windowed device** - the actual root cause |

`DISCARD` is the standard windowed choice and needed no other field changes - their `BackBufferCount`
was already 1 with no multisampling to conflict with.

**The third one is the trap**, because the field's name says *fullscreen*: a fullscreen presentation
interval that is perfectly legal at full screen is rejected once you flip `Windowed` to `TRUE`, and the
error is a bare `D3DERR_INVALIDCALL` naming nothing. Expect to
[sweep the parameter space](06-debugging-methodology.md#in-hook-sweep) rather than reason your way to it.

## Depth submission differs in the details, not the intent

OpenXR depth composition (`XR_KHR_composition_layer_depth`) works on both APIs, but the OpenGL path has
its own traps: negotiate a depth vs depth-stencil format against what the live default framebuffer
actually reports (prefer depth-stencil when the framebuffer has stencil bits, to avoid incompatible GL
depth blits), blit source depth with `GL_NEAREST`, and convert HPL near/far from world units to metres
for `minDepth`/`maxDepth`. Any negotiation/copy/projection failure must fall back to the proven
color-only path for that frame. (*SOMAVR proved standard-OpenGL near/far → normalized depth `0/1`
against both Ghidra and HPL2 source before trusting it.*)
