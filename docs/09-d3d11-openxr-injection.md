# D3D11 & OpenXR Injection Pipeline

This chapter covers the graphics spine of an OpenXR injection mod for an older D3D11 game.
It assumes the game has no native stereo renderer, no OpenXR integration, and probably no
clean engine API for a second camera.

The key principle is to prove the route in layers. Do not jump directly from "DLL injected"
to "rewrite every world draw twice." Each milestone should answer one question, preserve the
working desktop path, and leave behind a useful fallback.

This chapter is written in D3D11 terms (SS2VR and BioshockVR). If your target is **OpenGL** (as
SOMAVR/HPL3 is), everything strategic here still holds — read [10](10-graphics-apis.md) for the
API translation (SwapBuffers instead of Present, FBOs instead of RTVs, uniform-driven projection,
global-state ownership, AFR).

## Keep the architecture in explicit lanes

A mature mod should separate these responsibilities even if the first prototype starts in one
file:

- **Injection and lifecycle:** process launch/attach, module identity, shutdown, and hook
  installation.
- **OpenXR runtime:** instance, system, session, spaces, swapchains, frame timing, and pose.
- **D3D bridge:** device/context ownership, texture allocation, copies/blits, and state guards.
- **Render-view ownership:** which source camera, render target, depth target, and clear epoch a
  draw belongs to.
- **Stereo world rendering:** per-eye projection/view transforms and draw replay.
- **Screen-space passes:** shadows, SSAO, fog, reflections, volumetrics, and post-processing.
- **Presentation:** tonemapping, gamma, aspect/FoV mapping, and XR layer submission.
- **UI, viewmodel, and input:** separate consumers with separate coordinate spaces.
- **Diagnostics:** logs, dumps, hotkeys, counters, and reversible A/B controls.

This is more than code organization. Most hard bugs are ownership bugs: the right data was
used in the wrong lane, at the wrong time, or for the wrong camera.

**Split the pure math out of the hook lanes so you can unit-test it without launching the game.** Pose
composition, projection/FoV construction, IPD/eye math, deadzone and hysteresis curves, basis
reconstruction, and comfort envelopes are all deterministic functions — they belong in libraries with
no GL/D3D/OpenXR handles and no native pointers, tested on the desk. The headset loop is minutes long
(chapter [08](08-project-process.md)); every bug you can catch in a millisecond-long unit test is a
headset trip you didn't spend. Both deferred-heavy projects converged on this independently — *SOMAVR*
has a `render_math` test suite covering projection centering, hand-basis calibration, menu-aim
projection, stick scaling, and temporal-mutation ranges; *BioshockVR* has separate handedness,
player-calibration, and viewmodel-transform test targets. A hook callback should then just gather native
state, delegate to one owner, restore any temporary state, and return.

## The proof ladder

Build in this order and do not promote a stage until its proof is machine-checkable:

1. **Injected DLL:** self-identifying log, clean detach, correct process architecture.
2. **D3D11/DXGI observation:** count `Present`, `Draw`, and `DrawIndexed`; no mutation.
3. **OpenXR bootstrap:** create instance/system/session against the game's real D3D11 device.
4. **Stereo smoke:** submit a different solid color to each eye. This proves eye routing, not
   game rendering.
5. **Flat game bridge:** copy or blit the live game image into both XR eyes.
6. **Pose probe:** log valid/tracked HMD orientation, position, asymmetric FoV, and IPD.
7. **Private eye targets:** allocate left/right color and depth targets; bind, draw, and restore
   state without affecting the desktop.
8. **Sustained private source:** keep both eyes fresh every frame and fall back explicitly when
   they are stale.
9. **Native stereo subset:** replay a small, known world lane with correct per-eye transforms.
10. **Complete world view:** preserve render-view ownership, depth coherence, and companion
    constants across the whole world pass.

**Each rung proves exactly one claim, and a lower rung's success never implies the next one.** This
sounds obvious and is the single most repeated failure in one project's entire registry — because
intermediate builds *run*, counters *move*, and nothing crashes. (*BioshockVR ran clone-bind → numeric
byte-mutation proof → pose proof → wide-view proof → same-target replay → private-eye-target bind →
eye-blit → private-HDR blit, with every write-up stating explicitly that success meant only "this
mechanism works." One run made the point: lifetime clone-bind applied counters read **4096** while the
numeric, pose and wide-view proofs had stalled at **5**. The plumbing was working perfectly and carrying
nothing.*) Give each rung its own counter, and read them side by side — divergence between adjacent rungs
is the signal that the ladder has quietly stopped climbing.
11. **Engine camera/culling:** drive the engine's view, projection, and frustum from HMD pose.
12. **Screen-space, viewmodel, and UI lanes:** make each stereo-correct or deliberately
    compositor-owned.

A flat bridge at step 5 is valuable plumbing, but it is not stereo. A depth-reprojected bridge
can be a useful fallback, but it is not full 6DoF native rendering.

**Before you commit to this ladder at all, check whether the engine already has a stereo/multi-view path
you can drive** — a split-screen mode, a cvar-gated second view, an `IStereoRendering`-style interface.
Driving the engine's own stereo pipeline is both more correct and faster than replaying every draw twice
(this is what UEVR does with Unreal's `-emulatestereo`/`FFakeStereoRendering`). None of SS2VR,
BioshockVR, or SOMAVR had a usable one — which is *why* all three replay draws — but the check is cheap
and the payoff is large. See [11](11-re-anchoring-and-discovery.md).

### The question before the ladder: can you just call the scene draw twice?

Even without a built-in stereo path, there is a route that skips most of this ladder: **hook the engine's
scene-draw entry and call it twice per frame**, once per eye, setting the camera and FOV before each call
and copying the result out after it. This is *scene re-entry*, and it changes what kind of project you
are running.

```text
per frame:  set LEFT camera + FOV  -> call original scene draw -> copy backbuffer -> left eye
            set RIGHT camera + FOV -> call original scene draw -> copy backbuffer -> right eye
```

The payoff is large enough to check for early: **the engine computes every view-dependent effect natively
per eye**, so the mono screen-space buffer problem below — shadow masks, SSAO, volumetrics, reflections,
the dominant artifact class on deferred engines — largely *does not arise*. The engine regenerates those
buffers per eye as part of its own frame. An independent BioShock mod took exactly this route on the same
engine BioshockVR fights per-draw, explicitly rejecting 3DMigoto-style draw duplication because of the
per-shader long tail ([13](13-teardown-bioshock-vr.md)).

The costs are real and land in a different place:

- You render the world **twice** — genuine GPU cost, not a trick.
- You must make an engine that never expected re-entrancy survive being called twice: temporal effects,
  occlusion queries, per-frame counters, and especially **threaded render pumps**, which can deadlock
  under doubling. Forcing the renderer inline (by driving the engine's *own* threading decision, not by
  reimplementing its branch) is the usual price of admission.
- Both passes must come from **one camera sample** — see pair coherence in [10](10-graphics-apis.md).

Finding the scene-draw entry is the enabling step, and it is a **callstack** question: capture the return
addresses on a known world draw and walk up. See the in-process frame inspector in
[06](06-debugging-methodology.md).

## Architecture and loader compatibility

- The injector, injected DLL, OpenXR loader, and target process must use the same architecture.
  A 32-bit game needs a 32-bit injector DLL and loader even on 64-bit Windows.
- Prefer a **launch-suspended** injector when early device/shader/resource creation matters:
  create the process suspended, inject, then resume. Attach-to-running is simpler and useful
  for iteration, but it misses all startup-time creation events.
- Never inject a second build over a process that already loaded the first one. Start a fresh
  process; unloaded hook state and static globals are otherwise unknowable.
- Log the actual loaded module path. Multiple Release/Debug/install copies are inevitable.
- **Device creation may not go through the plain SDK entry point.** Engines sometimes create the device via
  a vendor-extension path (NVAPI, AMD AGS and similar) and fall back to `D3D11CreateDevice` only otherwise.
  (*PreyVR's initializer selects between **two** vendor-extension creation functions on a runtime object
  flag, reaching plain `D3D11CreateDevice` only as the third branch — all three converging on the same
  adapter from one `EnumAdapters1` loop.*) A hook — or an adapter-agreement check for
  `XR_KHR_D3D11_enable` — that watches only the plain call will silently miss the path the game actually
  takes. Enumerate the creation sites before assuming there is one.

## Bind OpenXR to the game's real D3D11 device

For D3D11, the OpenXR session must be created with the same graphics device/adapter used for
the submitted textures.

- Wait until the game's D3D11 device and immediate context are stable. First `Present` is a
  practical bring-up signal.
- Request the D3D11 graphics binding extension and query the runtime's graphics requirements
  before session creation.
- Verify adapter compatibility rather than assuming the default adapter. Laptop hybrid-GPU
  systems make this especially important.
- Treat "headset unavailable" and "runtime unavailable" as retryable states during startup,
  not permanent global failure.
- Keep OpenXR initialization out of `DllMain`; loader-lock work should be tiny. Install hooks
  and initialize the runtime from a worker or a later render callback.

The minimum useful bootstrap log should expose runtime name, system availability, selected
adapter/device, session state, view count, swapchain formats/extents, and every failed OpenXR
result by symbolic name.

The binding itself, with the two failures that account for most "it initialises then dies" reports:

```cpp
/* Bind XR to the GAME's device -- never create your own. A second device cannot
   share resources with the game's, and the symptom is a black eye texture with
   no error anywhere. */
bool BindXrToGameDevice(ID3D11Device* gameDev, XrInstance inst, XrSystemId sys,
                        XrSession* outSession)
{
    /* 1. The runtime tells you which ADAPTER it requires. If the game is on a
          different GPU (laptop hybrid graphics, or a headset on the iGPU), you
          must fail loudly here -- sharing across adapters silently produces
          nothing. Match by LUID: names and VRAM sizes are not unique. */
    auto xrGetD3D11GraphicsRequirementsKHR = ...;   // via xrGetInstanceProcAddr
    XrGraphicsRequirementsD3D11KHR req{XR_TYPE_GRAPHICS_REQUIREMENTS_D3D11_KHR};
    if (XR_FAILED(xrGetD3D11GraphicsRequirementsKHR(inst, sys, &req))) return false;

    Microsoft::WRL::ComPtr<IDXGIDevice> dxgiDev;
    Microsoft::WRL::ComPtr<IDXGIAdapter> adapter;
    gameDev->QueryInterface(IID_PPV_ARGS(&dxgiDev));
    dxgiDev->GetAdapter(&adapter);
    DXGI_ADAPTER_DESC ad{}; adapter->GetDesc(&ad);

    if (memcmp(&ad.AdapterLuid, &req.adapterLuid, sizeof(LUID)) != 0) {
        LogError("XR runtime requires a different adapter than the game is using. "
                 "Refusing to bind -- this would render nothing, silently.");
        return false;
    }

    /* 2. Feature level is a FLOOR, not an equality test. Rejecting a device that
          exceeds minFeatureLevel is a self-inflicted failure. */
    if (gameDev->GetFeatureLevel() < req.minFeatureLevel) return false;

    XrGraphicsBindingD3D11KHR bind{XR_TYPE_GRAPHICS_BINDING_D3D11_KHR};
    bind.device = gameDev;

    XrSessionCreateInfo sci{XR_TYPE_SESSION_CREATE_INFO};
    sci.next     = &bind;
    sci.systemId = sys;
    return XR_SUCCEEDED(xrCreateSession(inst, &sci, outSession));
}
```

## The OpenXR frame loop is an ownership contract

The normal frame sequence is:

1. `xrWaitFrame`
2. `xrBeginFrame`
3. locate views at the runtime's predicted display time
4. acquire and wait for each swapchain image
5. write the eye images
6. release the images
7. submit projection/quad layers with `xrEndFrame`

Rules that prevent subtle failures:

- Use the runtime's **predicted display time** for the pose used to render the submitted frame.
- Track the game frame that produced each eye image. Never submit an old stereo pair forever
  because both caches happen to be marked ready.
- Log source age and fallback reason. "Private source unavailable" and "OpenXR failed" are
  different problems.
- Acquire/wait/release every swapchain image correctly even on fallback frames.
- Do not assume the runtime's recommended eye extent matches the game's render size or aspect.

The contract in code. Every early-out has to keep the Begin/End pairing intact — an unpaired
`xrBeginFrame` is what produces the runtime hang that looks like a GPU fault:

```cpp
void RenderXrFrame(XrSession s)
{
    XrFrameState fs{XR_TYPE_FRAME_STATE};
    if (XR_FAILED(xrWaitFrame(s, nullptr, &fs))) return;          // no Begin yet: safe

    if (XR_FAILED(xrBeginFrame(s, nullptr))) return;

    /* From here on, EVERY path must reach xrEndFrame. Not "should" -- must. */
    std::vector<XrCompositionLayerBaseHeader*> layers;
    XrCompositionLayerProjection proj{XR_TYPE_COMPOSITION_LAYER_PROJECTION};
    XrCompositionLayerProjectionView views[2]{};

    if (fs.shouldRender) {
        if (LocateViews(s, fs.predictedDisplayTime, views) && RenderBothEyes(views)) {
            proj.viewCount = 2;
            proj.views     = views;
            proj.space     = g_appSpace;
            layers.push_back(reinterpret_cast<XrCompositionLayerBaseHeader*>(&proj));
        }
        /* Failure here submits ZERO layers -- which is legal, and is a visible
           blank frame. That is correct behaviour: a blank frame is recoverable,
           a skipped EndFrame is not. */
    }

    XrFrameEndInfo fei{XR_TYPE_FRAME_END_INFO};
    fei.displayTime          = fs.predictedDisplayTime;   // the WAITED time, not "now"
    fei.environmentBlendMode = XR_ENVIRONMENT_BLEND_MODE_OPAQUE;
    fei.layerCount           = (uint32_t)layers.size();
    fei.layers               = layers.data();
    xrEndFrame(s, &fei);
}
```

> **Injector authors: this sample writes the runtime's located FOV into the views it renders AND
> submits.** That is correct for an application that owns its renderer and will honour the FOV it was
> handed. **An injected mod usually does not** — the host engine builds its own projection, so what you
> render is the engine's frustum while what you declare is the runtime's. That mismatch is the most
> expensive stereo bug in this fleet: it presents as eyes pulling outward that will not converge, or as
> edges that stretch on head motion but not on stick turning.
>
> Declare the frustum you actually rendered, and see
> [Question 1](#q-distance) for the five-second discriminator,
> [STR-011](pattern-catalog.md#str-011) for which camera's frustum to declare, and
> [FAIL-STR-031](failure-atlas.md) for the symptom row.


Three rules fall out, and each one has cost someone a day:

- **`xrEndFrame` must be unconditional once `xrBeginFrame` succeeded.** Wrap the body in RAII or a
  `goto end` if that is what it takes; an early `return` on a render error hangs the compositor.
- **`fei.displayTime` must be the time `xrWaitFrame` predicted**, not a fresh timestamp. Using "now"
  produces judder that scales with frame time and is very easy to misattribute to tracking.
- **Respect `shouldRender == false`.** It means the headset is off the user's face or the session is
  idle; rendering anyway wastes a full frame of GPU on something nobody sees.

## The session state machine — poll events, or nothing works and you will not know why {#xr-session-state-machine}

The frame loop above assumes a running session. **Getting to one, staying in one, and surviving losing
one is a separate contract**, and it is the half most injector mods skip until something breaks in a
user's headset.

`xrWaitFrame`/`xrBeginFrame`/`xrEndFrame` are only legal while the session is running. You get there by
**polling `xrPollEvent` every frame** and reacting to `XrEventDataSessionStateChanged`. Miss the polling
and the runtime never advances you past `IDLE`; your frame loop then fails on every call and the logs
fill with errors that describe a symptom, not a cause.

FEAR VR's implementation is a pure state machine with **no OpenXR types in it**, which is why it has a
unit test:  `[SOURCE]`

```cpp
enum class XrLifecycleState : uint8_t {
    Unknown, Idle, Ready, Synchronized, Visible, Focused, Stopping, LossPending, Exiting };
enum class XrLifecycleAction : uint8_t {
    None, BeginSession, EndSession, RestartSession, ExitHost };

XrLifecycleTransition OnStateChanged(XrLifecycleState state) noexcept {
    const XrLifecycleState previous = state_;
    XrLifecycleAction action = XrLifecycleAction::None;

    switch (state) {
    case XrLifecycleState::Ready:                       // runtime says: you may begin
        if (!sessionRunning_ && pending_ == XrLifecycleAction::None) {
            pending_ = action = XrLifecycleAction::BeginSession;
        }
        break;
    case XrLifecycleState::Stopping:                    // runtime says: stop submitting
        if (sessionRunning_ && pending_ == XrLifecycleAction::None) {
            pending_ = action = XrLifecycleAction::EndSession;
        }
        break;
    case XrLifecycleState::LossPending:                 // the session is going away
        sessionRunning_ = false;
        pending_ = XrLifecycleAction::None;
        action = XrLifecycleAction::RestartSession;
        break;
    case XrLifecycleState::Exiting:                     // the user/runtime wants out
        sessionRunning_ = false;
        pending_ = XrLifecycleAction::None;
        action = XrLifecycleAction::ExitHost;
        break;
    default: break;                                     // Synchronized/Visible/Focused: keep going
    }
    state_ = state;
    return {previous, state_, action, sessionRunning_};
}

// Call this only after the requested OpenXR API call returns.
void OnActionCompleted(XrLifecycleAction action, bool succeeded) noexcept {
    if (pending_ != action) return;                      // stale/double completion
    if (succeeded) {
        if (action == XrLifecycleAction::BeginSession) sessionRunning_ = true;
        if (action == XrLifecycleAction::EndSession)   sessionRunning_ = false;
    }
    pending_ = XrLifecycleAction::None;                 // a retry needs a new event/policy
}
```

Four things about that shape are worth copying:

- **The running flag changes on API success, not on intent.** `READY` requests
  `xrBeginSession`; only a successful return marks the session running. The
  pending guard makes repeated events idempotent without lying after a failed
  begin/end call.
- **`LOSS_PENDING` means restart, not exit.** The session is being destroyed — often a runtime restart or
  a headset reconnect — and the correct response is to tear down and try again, not to quit.
- **`VISIBLE` and `FOCUSED` are not the same thing, and both keep rendering.** You are still submitting
  frames when unfocused; what changes is **input**, see below.
- **It is engine-free, so it is testable.** Their `test_xr_session_state` covers `LOSS_PENDING` and the
  re-`READY`/begin sequence **with no headset attached** — which is the only way that path ever gets
  exercised, since you cannot reliably provoke it by hand.

### Neutralize input on focus loss — do not freeze it {#input-independent-of-render}

`VISIBLE` without `FOCUSED` means the runtime has given input to something else — a system menu, a
dashboard, another app. **Actions stop updating, and their last values are still sitting in your
buffers.** If you keep consuming them the player walks into a wall while reading a system dialog.

**Neutralize, do not freeze:** zero the axes and release the buttons; after focus returns,
require neutral/release before allowing a held control to generate a new press. This is the
[latched-action rule](03-input-and-locomotion.md#a-release-must-go-to-whoever-owned-the-press) again —
focus loss is a release you never received.

Do not put invalidation behind `shouldRender`, a successful locate, or image acquisition.
OpenMoHAA fork `63c790a277bdf153159d7ff8e59bdeca036994a5` returned before input sync
when rendering was skipped; its getter accepted the old snapshot using coarse ACTIVE
state. The source-linked harness calls sync in the good control but retains seeded
input when `shouldRender=false`. `[SOURCE; LIVE harness]` Test hold/fire -> skip/focus
loss -> release delivered -> held reconnection suppressed -> neutral -> fresh press.
The receipt proves the old call ordering, not a real-game firing incident or a fixed
current fork. Evidence: `Medal-of-Honor-vr/docs/reviews/REVIEW-20260909.md`.

### Keep submitting during loading screens and menus

A common and avoidable failure: the mod stops calling `xrEndFrame` while the game is loading or a menu is
up, the compositor starves, and the user gets a frozen or black headset with no explanation.

**Submit something every frame the session is running.** FEAR VR's answer is a quad layer:  `[SOURCE]`

> When [stereo] is clear, the host renders the latest mono image into one eye swapchain and submits it as
> a **2.4 m × 1.8 m quad anchored 2 m in front of the view**. The anchor is **yaw-only** and remains
> world-locked until a panel recenter is requested. **This same path covers startup, loading screens,
> normal menus, comfort-mode cutscenes, and stereo failure.**

One fallback path serving five situations is the design worth taking. Note the **yaw-only anchor** —
inheriting HMD pitch and roll into a world-locked panel is the recenter trap from
[01](01-camera-and-tracking.md).

## The recovery matrix — write one, and make every row a decision

Everything that can be unplugged, restarted, resized or crashed will be, on somebody's machine. FEAR VR
ships a table of every such event with a named owner and response, and reproducing it here is more useful
than any prose:  `[SOURCE]`

| Event | Owner and response |
|---|---|
| **OpenXR focus/session change** | Host state machine begins/ends/restarts the session, and **neutralizes input when unfocused** |
| **Game starts after the host** | Bridge creates IPC; host opens it on a **250 ms retry loop** |
| **Host disappears** | Game-side heartbeat check disables transport, **recovers ring slots, and continues flat** |
| **Game disappears** | Host heartbeat disconnects; production launch uses `--exit-on-game-disconnect` |
| **D3D9 `Reset` / resolution change** | Bridge releases **all** default-pool, capture, compositor and shared resources, then lazily recreates them |
| **Shared handle changes** | Host's per-slot cache detects the new handle and **reopens only that source** |
| **Adapter mismatch** | Shared-texture transfer stays disabled; the mismatch is **logged**, not worked around |
| **Protocol mismatch** | IPC is rejected and a protocol-error flag is set |
| **Unsupported game build/layout** | **That specific hook is left untouched**; less invasive features continue |
| **Ring pressure** | The producer **drops frames**; neither process blocks the other's render loop |

**The column that matters is "owner".** Every row names *who* notices and *who* acts. A recovery path
with two owners deadlocks; one with none hangs.

Four patterns generalise beyond this project:

- **Either process may start first.** A retry loop on the consumer side costs four lines and removes an
  entire class of launch-order bug.
- **Heartbeats in both directions.** Each side must survive the other vanishing — and the survivor's job
  is to *degrade*, not to wait.
- **Device loss is a full resource cycle, not a patch.** On D3D9 `Reset`, D3D11/12 device removal, DXGI
  resize, or GL context replacement, release **everything** in the affected pool and lazily recreate.
  Selectively keeping resources across a device reset is how you get a use-after-free that reproduces
  only on somebody else's GPU.
- **Degrade at every boundary, and say so.** Adapter mismatch, protocol mismatch and unrecognised build
  each disable one capability and let the rest run. **Flat/mono fallback at every external boundary** is
  their stated rule, and it is why the failure mode is a worse experience rather than a crash.

### Test the paths you cannot provoke

Most of that table cannot be exercised by hand — you cannot reliably make a runtime emit
`LOSS_PENDING` on demand. FEAR VR's split is the answer: **the logic is engine-free and unit-tested**,
and the live tests cover what live tests can.

Their honesty about the remainder is the part to copy. `FOCUSED → VISIBLE → FOCUSED` was observed twice
across ~20,400 submitted frames with a clean shutdown; but when they pulled the Link cable, **SteamVR
kept the same OpenXR session alive** and never reported a loss. So a genuine runtime-reported
`LOSS_PENDING` **remains an open live test**, recorded as such rather than assumed covered.

**Write that distinction down for your own matrix**: which rows are unit-tested, which are live-tested,
and which are still theory.

### Observe completed draws; close the frame on its owner thread {#completed-draw-transaction}

SWAT4's September 9 controls found normal gameplay inside
`UWindowsClient::Tick -> Repaint -> Draw`. Blanket Repaint exclusion suppressed
1,712 normal draws. Removing it allowed double draws, but the early Present callback
still preceded the current Draw's world projection. Moving capture after each
completed Draw aligned image, eye tag and FOV. `[LIVE in-game simulator]`

Guard actual nesting/destruction rather than excluding a caller by its name. Carry
one located pose/time through both renders and copies; admit a layer only after the
whole pair succeeds. The preserved final trace contains 1,315 distinct-eye projection
pairs, 151 deliberate mono frames and nine empty frames. Its generic checker still
reports three policy mismatches, explicitly classified in the project report—not
silently converted to passes. Metadata separation is not distinct-raster proof.

Use fault controls for each transaction edge: failed acquire/wait, partial creation,
failed copy/end, disarm, loss and incomplete pair. SWAT4's old source-linked probe
failed five such expectations; new tests exercise the repaired path. Preserve GPU
fence/borrowed-resource ownership during recovery instead of reusing in-flight state.

Sims4's native M1 adds a different ownership test: remote Stop must queue teardown
to the bound render thread. A mutex around Present alone does not protect the game's
graphics work outside that callback. Its final retail regression records caller
thread 37596 and cleanup thread 86464, 405 quad submissions and normal exit.
This is game-image transport, **not scene stereo**; loaded-lot/resize controls belong
to an earlier DLL, and retail xr-tape was not active. `[LIVE in-game simulator]`

Evidence: `Swat4-VR/docs/reviews/openxr-2026-09-09/probe-output.txt`,
`reviews/openxr-fixes-2026-09-09/IMPLEMENTATION.md` under its docs, and
`Sims4VR/experiments/native_m1_20260910/REPORT.md`. No headset, full re-entry
side-effect or release acceptance is implied by these controls.

## Private per-eye color and depth targets

The safest first native-stereo route preserves the original game draw and adds an offscreen
copy:

```text
original draw -> original game target (unchanged)
replayed left draw -> private left color/depth
replayed right draw -> private right color/depth
private eye color -> OpenXR swapchain image
```

Important details:

- Color needs the bind flags required for both rendering and later sampling/copying.
- Depth should be shared by all draws for one eye and cleared once at the start of that eye's
  view, not once per draw.
- Left and right targets need independent depth. Sharing one depth buffer between eyes creates
  eye-dependent holes and impossible occlusion.
- Restore render targets, depth-stencil state, blend state, viewports, scissors, shaders,
  constant buffers, and SRVs after replay. Use scoped/RAII guards; open-coded save/restore
  eventually misses a return path.
- Keep the original desktop path intact until the private path is stable. A broken HMD should
  not also destroy the only visible debugging surface.

Use loud per-eye clear colors during bring-up because uncovered pixels become obvious. Once
coverage debugging is complete, switch the normal clear to black or a mono background copy so
disocclusion gaps are not mistaken for material corruption.

## Stereo math: translate in view space, not by sliding clip-space pixels

A constant horizontal image shift gives two displaced flat images. It cannot create correct
depth-varying parallax.

For a precombined world-view-projection matrix, a useful native-stereo construction is a
projection-conjugated eye transform. In row-vector notation:

```text
M_eye  = inverse(P_center) * T_eye * P_eye
WVPeye = WVPcenter * M_eye
```

Column-vector engines use the reversed multiplication order. Determine the convention from
captured matrices and validate it numerically; do not transpose until it "looks less wrong."

*Confirmed on a second engine (UE2.5/D3D11): BioshockVR first shipped the naive form —
`clip.x += eyeShift * clip.w`, a constant NDC offset that by construction cannot produce depth-varying
parallax — then replaced it with the conjugated form above.*

**Validate the replacement with a numeric residual, and read
[11](11-re-anchoring-and-discovery.md)'s treatment of it before you build one.** The short version, because
it has bitten two projects: a bare "is `oldWVP · P_center⁻¹` affine?" check **cannot detect a wrong FOV at
all** — FOV and aspect never enter the term that check reads, and FarCry2-VR measured a guessed 75° FOV
scoring identically to the correct projection. Add an **orthonormality/basis-scale term**, build a table of
deliberately wrong inputs, confirm your metric separates them, and derive the threshold from your own gap.
A residual limit is a property of a metric, not of a problem — importing another project's number is how
FarCry2-VR briefly ended up with a gate looser than no gate at all.

The same residual, once it works, also settles the row-vector/column-vector convention empirically instead
of by assumption.

- `T_eye` is the left/right view-space translation derived from physical IPD and game world
  scale.
- `P_center` is the game's actual center projection, extracted from live/captured constants or
  a confirmed camera structure.
- `P_eye` is built from the runtime's **asymmetric** left/right/up/down FoV angles.
- Validate that removing `P_center` from candidate WVP matrices leaves an affine transform.
  A loose residual gate can turn a bad projection guess into meter-scale object displacement.

Never assume near/far values are meters. Projection matrices use engine units, and older games
commonly use large world-unit ranges.

### Extract `P_center`; don't guess it — and let the affine gate prove it

The single most productive move in the whole stereo-math effort is refusing to guess the center
projection. A guessed FoV produces a `P_center` that *looks* plausible and fails silently.

- *BioshockVR (the canonical numbers):* a guessed `75°` `P_center` left the affine residual at ~`96.65`
  (limit `1.0`) — every candidate rejected, HMD showed only the solid fallback. Extracting `P_center`
  **per draw from the VS `screenDataToCamera` rows** (`c3-c5`) plus the WVP-derived depth relation
  (`clipZ = a·clipW + b`) dropped the residual from ~`98` to near zero. The real projection was hFOV
  `≈100°`, vFOV `≈67.7°` at 16:9, near `≈10` units (`0.1538 m`), far `≈65536` units. An early
  `near=0.1/far=1000` **meters** guess was both the wrong values and the wrong units.
- Keep the affine gate **strict**. The same project ran with a permissive limit of `250.0` for a while
  and it passed bad matrices without complaint; tightening to `1.0` is what surfaced the bad guess.
  *If most rows reject, your `P_center` is wrong — extract it, don't loosen the gate.*
- Eye separation is a **world-space** translation via OpenXR IPD scaled by the engine's units/metre
  (BioShock `≈65`), **not** a clip-space offset. The runtime's raw asymmetric-FoV x-offset (e.g.
  `±0.242`) is *not* your stereo separation; at IPD `~0.0665 m` the expected clip shift is `0.01–0.03`.

### Constant offsets are per-shader-family, not fixed

The register/offset where a semantic (WVP, reconstruction, eye pos) lives varies by shader family, and
the family is best keyed by the **live constant-buffer byte size**, not by the reflected size. A single
"the WVP is at c10" assumption will mis-key half the draws.

- *BioshockVR:* the same `worldViewProj` semantic appeared at `c10-c13` (576-byte layer/model family),
  shifted to `c9-c12` (material-batch family), and at `c40-c43` in an 832-byte large-light-array
  family; PS reconstruction (`screenToWorld`/`worldEyePos`) lived in a separate 1088-byte lane. The
  practical method was: profile the top clean families, name a candidate window per family, gate it
  (bounded/no-bad counts), and only then mutate — WVP **and** its reconstruction companions together.
  Prior-art shader dumps (3DMigoto/3D-Vision fixes) are excellent for enumerating these layout families
  before you touch anything live.

## The crudest possible per-draw replay: call the original draw twice

Worth documenting because it is the smallest thing that works, and it is instructive about what it
costs. BF2VR replays **every** `Draw` call into the XR eye target by simply calling the original twice:

```cpp
void D3DService::DrawDetour(ID3D11DeviceContext* ctx, UINT vtxCount, UINT startVtx) {
    ...
    ID3D11RenderTargetView* xrRTV = OpenXRService::xrRTVs.at(eye).at(imageIndex);

    drawHook.call<void>(ctx, vtxCount, startVtx);          // 1: the game's own target
    ctx->OMSetRenderTargets(1, &xrRTV, nullptr);           // rebind to the eye swapchain
    drawHook.call<void>(ctx, vtxCount, startVtx);          // 2: the same draw, again
}
```

No draw classification, no per-draw matrices, no pass census — every draw goes to both. It gets an image
into a headset in very little code.

**Note the `nullptr` where the depth-stencil view belongs.** The replayed copy has **no depth buffer**,
so the second image is composed in submission order rather than depth order. On a scene with any
overlapping geometry that is painter's-algorithm rendering, and it is a plausible contributor to the
same project's reflection and transparency troubles. If you take this route, bind a depth target for the
replay too, or accept the artifact knowingly.

**And it doubles the draw count**, which is the reason this is a starting point rather than a
destination. It is [rung 2](17-teardown-fc2vr-native-stereo.md) at its least selective.

## Resolve vtable slots from a throwaway device, then hook the game's real one

A small, reusable trick for any D3D11 target. You need the *vtable layout* of `IDXGISwapChain` and
`ID3D11DeviceContext` to place hooks — but you do not need the game's objects to get it:

```cpp
// A dummy device + swapchain exists ONLY to give you well-known vtable pointers.
D3D11CreateDeviceAndSwapChain(nullptr, D3D_DRIVER_TYPE_HARDWARE, ..., &desc, &pSwapChain, ...);

// The objects you actually hook and use come from the game's own renderer.
pDevice  = DXRenderer::getDevice();
pContext = DXRenderer::getContext();
if (!isValidPtr(pDevice)) { /* fail closed */ }
```

The dummy needs a valid `HWND`, which is also a convenient engine tell —
`FindWindowA("Frostbite", "STAR WARS Battlefront II")` identifies both the engine and the title from the
window class alone.

**Validate the pointers you get back from the game** (`isValidPtr`) before using them. A renderer global
read too early in startup returns garbage rather than null, which is the
[attach-window problem](07-engine-integration-safety.md) in a different costume.

## The unit of publication is the pair, not the eye

A reader must never be able to observe the left eye from frame N beside the right eye from frame N+1 —
and, less obviously, must never observe **the same image in both slots**. Both are *partial updates*, and
the fix for both is that a pair is published atomically or not at all.

The second case is the dangerous one, because it does not look broken. (*FC2VR: after a failed eye, an
ordinary mono `Present` wrote the same image into both eye slots while the host was still in Projection
mode. The result is duplicated mono presented as stereo — which reads to a tester as "the stereo feels
subtly wrong", not "the stereo is broken". Their fix: if a transfer is mono while stereo is active,
release the claimed slot and publish nothing, holding the last complete coherent pair until the next
complete pair arrives. See [17](17-teardown-fc2vr-native-stereo.md).*)

**Hold the last good pair rather than publishing a bad one.** A repeated-but-coherent frame costs one
frame of latency; an incoherent pair costs the illusion.

Note how it was caught, because the symptom alone would not have found it: **84 eye rejects against only
2 mono-quad anchors.** Two counters that should have moved together did not, and neither number looks
alarming on its own — see [06](06-debugging-methodology.md) on counters that must be read as a pair.

## Validate the pose, not the matrix

When you check that a view you injected came back the way you intended, **do not threshold the raw matrix
coefficients.** A view matrix mixes rotation and translation, and its translation terms are the rotation
multiplied by the world position — so a fixed tolerance on its coefficients silently tightens as the
player walks away from the origin.

(*FC2VR's original guard compared all 16 raw View coefficients against a flat `0.010`. At Far Cry 2's map
coordinates — around `(2507, 1187, 22)` — a rotation rounding error near `1e-6` exceeds that threshold,
so valid eyes were rejected in a **yaw-dependent** pattern: near one world direction, and again about 180°
opposite. Replacing it with `eRot >= 0.0025 || ePos >= 0.010` on the **decomposed** pose fixed it.*)

```text
weak:    reject if max_abs(gotView - desiredView) >= tol        <- tol means nothing; scales with position

strong:  got  = inverse(rebuiltView)
         eRot = max abs delta of the 3x3 rotation   >= 0.0025   <- a real tolerance
         ePos = max abs delta of camera XYZ         >= 0.010    <- metres, meaningful everywhere
```

**Decompose, then check each component against a tolerance that has physical meaning.** Keep the old
matrix residual as *telemetry* — it costs nothing and it is what lets you recognise the failure again —
but do not let it own acceptance.

This is the second time this family has bitten a project here. FarCry2-VR separately proved that a bare
affine residual check **cannot detect a wrong FOV** ([11](11-re-anchoring-and-discovery.md)). Same root
cause: a matrix residual is not a measurement of anything anyone cares about.

## Projection companions must remain coherent

Changing only WVP is often enough to move geometry and enough to break everything else.
Shaders may also consume:

- inverse projection or `screenToWorld`
- camera/world eye position
- screen-to-camera reconstruction
- depth scale/bias or linearization constants
- clip planes
- screen transforms used to sample full-screen masks

Treat these as one camera contract. Use shader disassembly/reflection to identify exactly which
companions a layout consumes, then update the per-eye set coherently. A fix that changes WVP
but not a clip plane can make geometry disappear in one eye; a fix that moves geometry but not
screen reconstruction can make lighting, fog, or specular terms swim.

## Preserve render-view provenance

"HDR target with depth" is not a sufficient definition of the main world view. Older engines
may render several perspective views in one game frame:

- main camera
- mirrors or planar reflections
- water refraction
- portals or security cameras
- environment captures
- sky/vista subviews

If the injector replays all of them into one private eye color/depth pair, unrelated depth
spaces are merged. Typical symptoms are a camera-following city/sky shell, distant geometry
leaking through walls, black silhouettes, direction-dependent pop-in, and a sudden GPU cost
increase when the secondary view becomes active.

Track source ownership using, in increasing detail:

1. original color-resource + depth-resource identity
2. RTV/DSV view and subresource identity
3. viewport/scissor and projection signature
4. clear epochs within a reused target pair
5. engine camera/view object or call-site identity

Rank/census these groups and add a live isolation mode that skips only private replay. If one
group shows the room and another shows the reflection/vista, the diagnosis is complete. Draw
ordinal is useful for a quick probe but is not a stable ownership key; visibility changes the
order.

**Preserve the source draw's viewport and scissor — they are part of its provenance.** A secondary
engine view often renders into the *full* target but with a *bounded* scissor; if your private-replay
helper expands that to full-eye, you promote a small overlay into a camera-following shell.

- *BioshockVR:* the "cyan Rapture city shell" bleeding into the HMD was exactly this — a bounded
  secondary view (full `1920×1080` viewport, scissor `0,0,1920,279`) that the replay forced to
  full-target scissor. It survived ~15 falsified hypotheses (compact companion, remap, ordinal,
  target-pair, clear-epoch…) before `StereoWorldPreserveSourceViewRect=1` removed it completely.
  Separately, an `800×600` shadow-mask RTV rasterized through a viewport *scaled* to the `2688×2880`
  eye target produced a pure-geometry error unrelated to any constant. Carry the source rect through;
  don't synthesize a new one.

## Mono screen-space buffers are a separate stereo problem

World geometry can be perfectly stereo while materials remain eye-dependent because they
sample a mono screen-space buffer using per-eye screen coordinates. Common offenders:

- shadow masks
- SSAO
- volumetric fog/light shafts
- screen-space reflections
- decals and depth-aware particles
- deferred reconstruction buffers

Neutralizing the resource is a diagnostic, not a final fix: it can remove the artifact by
removing the effect. Durable options are:

- render the generator pass separately for each eye
- replay the whole dependent pass per eye
- patch the sampling/reconstruction coherently where the effect permits it
- deliberately render the material mono and accept flatness as a temporary fallback

This is why "make every WVP stereo" is not a complete stereo renderer.

For a pass-by-pass reference — what each common effect samples, which hazard class it falls into, and
what to do about it — see the [render-pass hazard atlas](14-render-pass-hazard-atlas.md). Counting the
screen-space and temporal passes in a capture *is* your per-draw stereo effort estimate.

On a **deferred / screen-space-heavy** engine this is not a minor cleanup pass — it is often the
*dominant* remaining artifact class, and a larger workstream than the projection contract itself.
Correct camera and correct per-eye WVP can still leave shadows, volumetrics, reflections, decals, and
material lighting broken because every one of them reconstructs from a **mono, center-camera depth
buffer**.

- *BioshockVR:* once world geometry went per-eye, a boulder's shader sampled a mono `s_shadowMask` by
  screen UV — correct UV per eye, but the sampled buffer was still center-eye — producing
  eye-dependent black sides and stretched shadow cutouts. Every cheap fix failed: a neutral-white mask
  override applied 117,714× and made boulders *darker*; broad SRV demotion over-caught architecture and
  punched red/blue holes. The durable answer is **per-eye generation of the producer buffers** (or
  UEVR-style synchronized-sequential rendering), not neutralizing the consumer. And note
  `XR_KHR_composition_layer_depth` does **not** create a second mask buffer — depth submission and
  producer ownership are different problems.
- **Counterintuitive symptom to memorize:** a *stale mono occluder* in a shadow/attenuation test reads
  as a **bright, sharpened, unshadowed cutout**, not a dark shadow. (*BioshockVR: the tracked wrench
  moved in the private-eye depth, but the native center depth still held the wrench at its neutral 2D
  pose; the multiplicative light-attenuation pass sampled the center depth, so the stale wrench appeared
  as a moving bright gobo.*) "Bright hole that follows the wrong pose" ⇒ a mono producer sampling stale
  center-camera depth.
- Mutating a per-eye producer can also crash the runtime through resource-lifetime coupling — quarantine
  behind a knob rather than papering over (see [07](07-engine-integration-safety.md)).

## FoV, aspect, and full-eye presentation

Stretching a 16:9 game image across a tall eye texture creates wrong angular scale and often a
vertically stretched view. Cropping it to fill removes borders but throws away peripheral
geometry and feels zoomed.

- Use aspect-fit/crop/stretch only as explicit diagnostic modes.
- The destination projection layer already carries each eye's asymmetric runtime FoV; the
  content rendered into that texture must correspond to that FoV.
- **Check how the engine stores its frustum before assuming you must rebuild the projection pipeline.**
  OpenXR needs asymmetric per-eye projection (`L != -R`), which a single FOV-plus-aspect pair cannot
  express — but many engines already keep the general form for unrelated reasons (portals, tilt-shift,
  off-centre views). (*PreyVR's per-frame render-view block stores frustum left/right/bottom/top as **four
  independent floats**, internally consistent with the block's own aspect field. Asymmetric per-eye frusta
  are therefore directly representable with no camera restructuring at all — a substantial cost saving
  found by reading a struct layout, before writing any code.*) It is a five-minute check with a large
  branch behind it.
- Prefer private eye targets at the runtime eye extent with a real per-eye projection.
- Expanding the private projection does not make the engine render objects it culled under the
  old camera. Full peripheral coverage and positional 6DoF eventually require engine camera,
  FoV, near plane, and culling ownership.
- Keep a compositor quad-layer mode as a comfortable, known-flat fallback. It is useful for UI
  and debugging even when it is not the end product.

## When the engine keeps clobbering your matrices, keep a reference instance it populates correctly

A recurring, exhausting failure: you write the correct per-eye projection, and the game overwrites it —
from a resolution change, a cutscene, an FOV effect, a post-process setup, a dozen sites you have not
found yet. Hunting every writer is a losing race.

There is a cheaper move. **Keep a second, non-rendering instance of the thing that the engine's own VR
path populates correctly, and copy from it at the last moment before use.**

```csharp
// Risk of Rain 2 VR: the game overrides the headset's projection matrices.
// Rather than chase every writer, keep a reference camera the XR system fills in.
_referenceCamera = refObject.AddComponent<Camera>();
_referenceCamera.CopyFrom(_mainCamera);
_referenceCamera.cullingMask = 0;                      // renders nothing
_referenceCamera.clearFlags  = CameraClearFlags.Nothing;
_referenceCamera.enabled     = false;                  // costs nothing

var pose = refObject.AddComponent<TrackedPoseDriver>(); // but the XR system still
pose.SetPoseSource(DeviceType.GenericXRDevice, TrackedPose.Head);  // gives it correct
pose.updateType = UpdateType.UpdateAndBeforeRender;                // stereo matrices

void OnPreCull()   { ApplyCorrectProjectionMatrices(); }   // copy reference -> main
void OnPreRender() { ApplyCorrectProjectionMatrices(); }   // again, after any late writer
```

The idea is not Unity-specific. Any time an engine computes a value correctly in one context and
clobbers it in another, **a parallel instance that the engine keeps correct is a source of truth you did
not have to reverse-engineer**. You stop needing to know who the writers are; you only need a point
after all of them.

**Apply at more than one point.** Copying at both `OnPreCull` and `OnPreRender` is not redundancy — it
covers writers that run between the two. Find the last hook before consumption and apply there, then add
an earlier one for anything that reads the value before that.

## "The two eyes don't line up" — a five-minute differential diagnosis

**Every project in this fleet has hit this, and none of them recognised it the first time.** The first
stereo image reaches the headset and the two eyes will not fuse: it looks as though there is a camera per
eye and they are aimed slightly wrong relative to each other. SS2VR, SOMAVR, BioshockVR and FarCry2-VR
all spent headset sessions on it, and the expensive part was never the fix — it was the round trip of
*put the headset on, look, take it off, describe it, guess, rebuild.*

The whole space is separated by **two questions**, and both are answerable in one headset session
without taking it off.

### Question 1 — does the misalignment change with distance? {#q-distance}

This is the single most valuable discriminator, and it comes from FarCry2-VR:

> A frustum mismatch offsets **every** object by the same angle **regardless of depth**; parallax scales
> with **1/distance**. Comparing a near object against the horizon separates them in five seconds.

- **Constant with depth** → you are declaring a **projection** to the runtime that does not match what
  you rendered. Nothing to do with IPD.
- **Scales with 1/distance** → it is a **parallax/IPD/eye-offset** problem: magnitude, sign, or units.
- **Present at infinity but not near** → eye offset applied to something that should be direction-only.

### Question 2 — which axis, and does it vary across the image? {#q-axis}

- **Horizontal only, uniform** → convergence or FOV. Fusable but uncomfortable; the common case.
- **Vertical at all** → always a bug. Human vision cannot fuse vertical disparity, so this is the one
  that produces immediate discomfort rather than "wrong depth."
- **Vertical, growing toward the edges (keystone)** → **toe-in**. You are *rotating* the eye cameras
  inward toward a convergence point instead of *translating* them apart. See below.
- **Whole image doubled and diverging outward** → eyes swapped, or the offset sign inverted.

### Question 3 — does it happen when you turn with the stick, or only when you move your head? {#q-stick-vs-head}

This one is free, needs no tooling, and comes from perfect_dark_VR. Their world had a light fisheye-like
stretch at the edges of the lenses that was **most visible when the player physically looked around, and
much weaker when turning with the controller while facing forward.** `[SOURCE]`

That asymmetry is diagnostic. Stick turning rotates the view *inside* a fixed relationship between the
projection you rendered and the projection you declared; **physical head rotation is what exercises the
runtime's lens correction against your submitted `XrFovf`.**

- **Only, or mostly, on physical motion** → the projection you rendered does not match the one you
  declared. The runtime's correction makes the mismatch visible as stretch or swim toward the edges.
- **Equally on stick turning** → the fault is in view/camera maths, not in the frustum declaration.

Note this is the *same underlying fault* that BioShock-Trilogy-VR chased for three sessions before
building [a compositing instrument](#substitute-runtime) to measure it as `claimRatioH`. Two independent
projects, two different cheap discriminators, one bug class: **submitted frustum ≠ rendered frustum.**

### Four ways a per-eye projection goes wrong at once

When perfect_dark_VR audited theirs, it was not one mistake but four, and every one of them is worth
checking by name: `[SOURCE]`

1. **Aspect effectively collapsed to `1.0`** instead of using the optical frustum's aspect.
2. **Vertical FOV derived from angular span** rather than tangent space — which is only equivalent for a
   *symmetric* frustum, and per-eye runtime frusta are not symmetric.
3. **Horizontal frustum-centre used, vertical frustum-centre discarded.**
4. **The tangent half-FOV helper returned eye 0's values for both eyes** — a silent single-eye read
   wearing a per-eye signature, and a close relative of the no-op swap flag below.

### The table

| What you see | Depth-dependent? | Likely cause | Confirm without a headset |
|---|---|---|---|
| Edge stretch/swim on **physical head rotation**, much weaker on stick turning | **No** | **Submitted frustum ≠ rendered frustum**, made visible by runtime lens correction | Compare submitted `XrFovf` tangents against the rendered projection |
| Interface shifts vertically and clips after a projection fix | **No** | Per-eye **vertical centre applied to screen-space UI** as well as world geometry | Assert the vertical asymmetry term is applied only in the 3D-world branch |
| Everything offset by the same angle, both eyes wrong in **opposite** directions | **No** | **Submitted FOV ≠ rendered FOV.** The compositor maps every world point to the wrong angle. | Assert submitted tangents equal the tangents you rendered |
| As above, and the error is a plausible-looking few degrees | **No** | **FOV halved in degrees instead of tangent space** | `atan(tan(fov/2))` round-trip test |
| Doubled, diverging outward, cannot fuse; depth inverted where it does | n/a | **Eyes swapped**, or eye-offset sign inverted | Assert `left.x < right.x` in view space across a run |
| Changing the swap flag does nothing at all | n/a | **The flag is a no-op** — it flips the label then derives the offset from the flipped label | Assert the *offset each eye receives* flips, not the label |
| Vertical offset, uniform | **No** | Per-eye projection-centre or viewport error | Assert both eyes' vertical tangents and viewport Y are identical |
| Vertical offset, growing toward edges | **No** | **Toe-in instead of parallel offset** | Assert both eye rotations equal the head rotation |
| Separation far too large, eyes ache, cannot fuse near objects | **Yes** | IPD in wrong units, or world-scale applied twice | Log metres → engine units once, at one site |
| Looks flat, no depth, but not misaligned | **Yes** | Eye offset ~0 — dropped, or scaled to nothing | Assert per-eye offset is non-zero and ≈ IPD × world scale |
| Some objects stereo, others flat or doubled | **Yes** | Per-draw stereo with unclassified passes | [14](14-render-pass-hazard-atlas.md) |

### When the engine can only accept one symmetric projection {#symmetric-base-decomposition}

Many engines have exactly one projection and no way to express an off-axis frustum. That does not force
you down to a symmetric approximation. perfect_dark_VR **decomposes** the runtime's asymmetric frustum
into a symmetric base the engine can hold plus per-eye centre terms applied downstream: `[SOURCE]`

```text
tanLeft  = tan(angleLeft)     tanRight = tan(angleRight)
tanUp    = tan(angleUp)       tanDown  = tan(angleDown)

tanHalfWidth  = (tanRight - tanLeft) / 2
tanHalfHeight = (tanUp    - tanDown) / 2

verticalFov = 2 * atan(average tanHalfHeight across both eyes)   -- the engine's base projection
aspect      = average tanHalfWidth / average tanHalfHeight
```

The **asymmetric centre terms stay per-eye**, read from the OpenXR column-major projection matrices
(`matrix[8]` horizontal centre, `matrix[9]` vertical centre) and applied in the vertex shader:

```glsl
mvPos.x -= eyeOffset.x + (eyeOffset.y * mvPos.w);   // eye/IPD translation + horizontal centre
mvPos.y -= eyeOffset.w * mvPos.w;                   // vertical centre
```

**The vertical term must never reach screen-space UI.** Menus and HUD are authored in clip space, not as
world geometry, so a global vertical correction slides the entire interface. On the Quest 3 they
diagnosed with, OpenXR reported a vertical centre of about **-0.193** — applying it everywhere moved the
interface up by roughly **19 percent of clip space**, which is exactly the clipping they observed. Guard
it inside the world branch and leave menus, HUD, crosshairs and blur geometry on their existing path.

Their values come **dynamically from OpenXR** with no headset-specific FOV, lens centre, IPD or aspect
hard-coded anywhere — which is why the same correction holds across Quest 2, Quest 3, Meta's PCVR
runtime, Virtual Desktop and SteamVR. See [STR-007](pattern-catalog.md#str-007).

### Superset-and-crop is an escape hatch, and it is lossy on canted displays

A second family exists for engines that cannot express an off-axis frustum: render a **symmetric superset**
covering both eyes' extents, then crop per eye with texture bounds at submission. Four projects in one
survey used it, and one of them objected to the whole approach for a reason none of the others saw.
`[SOURCE]`

The objection: **reducing the runtime's projection matrix to four tangents discards the shear term** that
canted-display headsets fold into it. Rebuild a frustum from tangents alone and the world keystones as
the head turns.

The important consequence, which none of the four sources states: **the superset-crop family cannot carry
a shear term either**, because it hands the engine a scalar FOV and aspect. So the objection applies to
the entire family, not only to tangent-rebuilding.

| Situation | Do this |
|---|---|
| You can reach the projection matrix | Treat it as **opaque** and left-multiply a clip-space crop. Shear survives. |
| The engine exposes only scalar FOV + aspect | Superset-and-crop is the correct escape hatch - and is **known-lossy** on canted headsets |
| You control the vertex shader | [Symmetric base plus per-eye centre terms](#symmetric-base-decomposition) |

Two of the four had defects that *hide* the symptom, which is why the family looks safer than it is: one
collapsed its frustum to the left eye only through a four-argument `max()` that compiles as **warning
C4002, not an error** (a missing `NOMINMAX`), and another called `GetProjectionMatrix` once and reused it
for both eyes. **A single-eye frustom bug and a correct symmetric superset look identical in one eye.**

### A VR shader prelude can overflow buffers sized for the flat game

Their title screen rendered and then the game took a `SIGSEGV` entering one particular menu. The cause
was not VR maths at all: the OpenGL backend builds shader variants in **fixed local character buffers
using append functions with no bounds checking**, the vertex buffer was 4 KiB, and the **VR prelude
alone is about 3.2 KiB.** Simple shaders fit; a more complex menu variant overflowed and corrupted the
native stack. `[SOURCE]`

Raising the buffers to 16 KiB fixed it, and their write-up is careful to say that this **prevents the
corruption without making the appends safe** — the unchecked builder is still there.

Generalise it: **anything you prepend to every generated shader is a size increase applied to code paths
sized for the flat game**, and the failure appears on whichever variant was already closest to the
limit — which is rarely the one you are testing.

### The two that actually bit this fleet

**FOV declared in degrees instead of tangent space.** This is the one that looks *entirely plausible* and
therefore survives review.

```cpp
// WRONG -- halving an angle is not halving a frustum.
float halfFovDeg = fullFovDeg * 0.5f;               // 91.3085 -> 45.654 ... coincidentally close

// The trap: when the game's horizontal FOV is split or letterboxed, the correct
// vertical FOV must be derived through TANGENTS, not degrees.
float wrongVert = fullVertDeg * scale;              // FarCry2: 57.0 degrees -- plausible, and wrong
float rightVert = 2.0f * atanf(tanf(fullVertRad * 0.5f) * scale) * kRad2Deg;   // 47.636
```

*(FarCry2-VR: the degrees-space answer was wrong by **9.4°**, and it looked fine on paper.
`tests/test_submitted_fov.cpp` now asserts the naive answer is rejected.)*

**A swap flag that cancels itself out.** FarCry2-VR's `SwapEyes` flipped the eye *label* and then derived
the offset *from the flipped label* — so the swap cancelled exactly, and **both settings produced
`LEFT = −half IPD`, `RIGHT = +half IPD`.** The question "is `SwapEyes=1` correct?" was unanswerable as
asked, because the flag did nothing.

Two lessons. **A swap must negate the offset, not the labelling** — "is the right vector inverted?" is
what you are actually asking. And their desk test **asserted the broken behaviour as correct**: it
checked "swapped frame 0 is the RIGHT eye and shifts right", which is true of a no-op and proves nothing.
Compare what each *eye* receives across a run and assert the sign flips.

### Toe-in is wrong; parallel offset with asymmetric frusta is right

Worth stating because it is the intuitive-but-incorrect construction. Real eyes converge, so it feels
right to rotate each eye camera inward onto a convergence point. **Do not.** Toe-in introduces
**keystone distortion** — the two images are trapezoids rotated relative to each other — which produces
vertical disparity that grows toward the edges and cannot be fused anywhere.

```cpp
// WRONG: toe-in. Vertical disparity at the edges, unfixable downstream.
leftRot  = headRot * RotY(+convergenceAngle);
rightRot = headRot * RotY(-convergenceAngle);

// RIGHT: translate only; both eyes keep the runtime's own orientation, and
// convergence comes from the ASYMMETRIC frustum the runtime already gave you.
leftPose  = { headPos + headRot * (-halfIpd * kRight), xrView[0].pose.orientation };
rightPose = { headPos + headRot * (+halfIpd * kRight), xrView[1].pose.orientation };
```

Take both position **and** orientation from `xrLocateViews` per eye and the runtime handles convergence,
cant and lens geometry for you — see the canted-display section below.

### Write these assertions now, not after the first headset session

These are desk tests, but their reference frame is part of the assertion.
Compare rendered and submitted values after conversion into the **same named space**:

```cpp
// 1. What you submit is what you rendered -- in tangent space.
ASSERT_NEAR(tanf(submittedFovLeft),  renderedTanLeft,  1e-4f);
ASSERT_NEAR(tanf(submittedFovRight), renderedTanRight, 1e-4f);
ASSERT_NEAR(tanf(submittedFovUp),    renderedTanUp,    1e-4f);
ASSERT_NEAR(tanf(submittedFovDown),  renderedTanDown,  1e-4f);

// 2. Each rendered position equals its own runtime pose after basis/scale/origin conversion.
ASSERT_VEC_NEAR(renderedLeft.position,  convertedXrView[0].position, tolerance);
ASSERT_VEC_NEAR(renderedRight.position, convertedXrView[1].position, tolerance);

// 3. Only a DECLARED symmetric, uncanted head-local fixture has equal y/z.
// Compare full baseline vectors for arbitrary views; do not hardcode world-axis ordering.
ASSERT_VEC_NEAR(renderedRight.position - renderedLeft.position,
                convertedXrView[1].position - convertedXrView[0].position, tolerance);

// 4. No toe-in: both eye rotations match what the runtime reported.
ASSERT_QUAT_EQ(leftRot,  convertedXrView[0].orientation); // modulo q == -q
ASSERT_QUAT_EQ(rightRot, convertedXrView[1].orientation);

// 5. The swap flag flips the OFFSET, not the label. Run it over several frames.
ASSERT_SIGN_FLIPPED(offsetDeliveredToEye(LEFT, swap=0), offsetDeliveredToEye(LEFT, swap=1));
```

The last offset diagnostic belongs to a declared symmetric test rig; it is not a
general transformation of canted runtime views. Add positive controls at translated
and rotated head poses and with runtime-provided cant. Sims4's old probe passed its
neutral selftest yet rejected a valid 63 mm pair at 30-degree yaw, rejected eye
ordering at 120 degrees, and rejected legitimate outward cant. `[LIVE harness]`
Test the validator with valid non-identity geometry before using it to reject a mod.
Evidence: `Sims4VR/experiments/review_20260909/geometry_results.txt`.

### When you do put the headset on, report a magnitude

This is the part that collapses the round trip, and it is FarCry2-VR's own conclusion:

> The user's first description — *"convergence isn't working, the opposite of cross-eyed"* — pointed at
> eye assignment, and `SwapEyes` did not help **because eye assignment was never wrong.** What made it
> solvable was the second description, which carried a **magnitude**: a mid-distance leaf about **half a
> screen apart**, ≈45° of angular error, where a 64 mm IPD accounts for a few pixels. That ruled out
> parallax immediately.

**A qualitative description cannot distinguish the rows of the table above; a magnitude can.** Half a
screen is not an IPD problem — it is an order of magnitude too large — and knowing that in the first
sentence skips every parallax hypothesis.

So the observation protocol, done once, in the headset:

1. **Find a near object and something at the horizon in the same view.** Close one eye, then the other.
2. **Does the offset change between them?** Near-only or distance-scaled → parallax. Both the same →
   projection.
3. **Which axis?** Any vertical component at all is a bug — say so first.
4. **If vertical: is it worse at the edges than the centre?** → toe-in.
5. **Estimate the magnitude in screen fractions** — "a tenth of the screen", "half the screen" — not
   "slightly off".
6. **Does closing one eye look correct on its own?** If a single eye is already wrong, this is not a
   stereo problem at all and the table does not apply.

Six observations, one session, no need to take the headset off between them. That is usually enough to
name the row before anyone touches the code.

## Canted displays: use each eye pose directly instead of forcing parallel projection

Some headsets (Pimax, and others with angled panels) mount their displays **canted** — rotated inward
rather than parallel. The common workaround is the runtime's "parallel projection" option, which
reprojects into a shared parallel frustum and costs a substantial amount of performance and FOV.

It is avoidable. **`xrLocateViews` already returns a full pose per eye — orientation as well as
position.** If you consume both, canted displays need no special case at all; the cant is simply the
relative orientation between the two eye poses.

(*Witcher 3 VR: "Native canted-display support — uses each OpenXR eye pose directly; no parallel-
projection workaround required," validated on a Pimax 5K with Parallel Projection disabled.*)

The mistake that forces the workaround is treating the eyes as *positions* with a shared orientation —
building both views from the head orientation plus `±ipd/2`. That is correct only for parallel panels.
Carry the per-eye orientation through your pose pipeline and the problem disappears:

```cpp
struct EyeGeometry {
    XrQuaternionf cyclopean_orientation;      // for anything that needs one head direction
    XrVector3f    cyclopean_position;
    XrQuaternionf eye_orientations[2];        // absolute, per eye
    XrQuaternionf relative_orientations[2];   // relative to cyclopean -- this is the cant
    XrVector3f    relative_positions[2];
    float baseline_m;                         // measured IPD, not assumed
    float cant_degrees;                       // derived, useful for diagnostics
};
```

**Derive HUD convergence from that geometry rather than hardcoding it.** The same project computes
headset-aware HUD convergence automatically from the eye geometry, which is what makes one HUD setting
work on both parallel and canted hardware.

### Off-axis lenses: size the frustum to *cover* the panel, not to match its span

A detail beyond the canted case, and it produces a very recognisable artifact. On headsets whose lenses
sit off-axis relative to the panel (Quest 3 and family), a frustum built to *match* the runtime's
reported span leaves **a black band down the outer edge** of each eye.

The fix is to size the frustum to **cover** the panel rather than match it — take the union of what the
optics can present rather than the nominal span, accepting that some rendered pixels fall outside the
visible area. (*Cyberpunk 2077 VR does exactly this, and names the black outer band as the symptom.*)

Note the trade: covering wastes a little fill rate at the edges; matching wastes nothing and shows the
user a black stripe. Prefer coverage, and expose it if you must, but do not default to the version that
looks broken.

## When the engine only accepts a symmetric FOV: use its optical-centre offset

An HMD frustum is asymmetric. Many engines expose only a symmetric vertical FOV plus an aspect ratio,
which looks like a dead end — and the usual fallback is a conservative symmetric FOV that throws away
coverage.

Check for a **projection-centre / optical-centre offset** first. Engines carry one for lens shift,
picture-in-picture, ultrawide letterboxing and cinematic framing, and *a centre offset plus a symmetric
FOV is an asymmetric frustum.*

(*REDengine represents a perspective view as symmetric vertical FOV + aspect + a **pixel-space
projection-centre offset**, and Witcher 3 VR drives asymmetry through that field rather than replacing
the projection matrix.*)

```text
vertical_fov_degrees, aspect          <- what the engine exposes
center_ndc_x / center_ndc_y           <- the conventional NDC displacement
optical_center_offset_px_x / _y       <- the same thing in pixels
horizontal_tangent_span, vertical_... <- what OpenXR actually gave you
```

Watch the **sign convention** — theirs needed a dedicated experiment to establish that the engine's
native offset fields use the same NDC sign as the optical centre. Determine it with a deliberate
one-axis test rather than by inspection.

## What checking the 32-bit registration looks like when it ships {#thirty-two-bit-preflight}

The 32-bit registration problem below is one this playbook has stated as a rule. CallOfDuty4_VR ships the
enforcement, and its wording is worth copying into any installer you write: `[SOURCE]`

> KisakCOD and COD4 are 32-bit processes. **A valid 64-bit OpenXR registration does not prove that the
> 32-bit loader can start.** Beta.14 reports both registry views independently and **blocks an
> OpenXR-only launch** when the 32-bit manifest is absent or missing on disk.

Three things that turns into, all of which generalise:

- **Report both registry views independently.** Not "OpenXR: OK" but one line per view, because the
  question the user needs answered is which one is missing.
- **Block, do not warn.** An OpenXR-only launch with no 32-bit manifest cannot work, so it is refused
  rather than attempted — [PACK-001](pattern-catalog.md#pack-001) applied at the runtime layer.
- **A fallback is labelled as one.** Their automatic backend may continue through an experimental x86
  OpenVR path when no usable 32-bit OpenXR runtime exists, and the report marks that a **Warning** — it
  "does not present OpenVR as equivalent to the primary VDXR path." A silent fallback to a lesser path is
  how users end up reporting the wrong bug.

### An installer that knows its own evidence grade

The same document does something this playbook argues for constantly, and I have not seen another mod
ship it — **it tells the user what its own check is worth:**

> Registry/file detection is an **offline preflight, not a synthetic VR session.** The first scan
> correctly warns that headset/controller proof is missing. Connect and wake the headset, run
> *Save & Launch Diagnostics*, then rescan to import the live backend/runtime/system/interaction-profile
> receipt.

And on its resolution advice: *"GPU memory provides only a conservative Native/Performance starting
point. **It is not a performance benchmark.**"*

That is the [evidence taxonomy](00-engine-profiles.md) shipped to end users: a `STATIC` check states that
it is static, and names the action that upgrades it to `LIVE`. Compare
[TEST-002](pattern-catalog.md#test-002) — an instrument that will not say what it failed to measure is
the same defect one layer down.

Two more from the same file worth stealing outright: setup **rejects an unrecognised install layout
before writing anything**, and "never guesses, downloads, or moves original COD4 assets"; and automatic
layout normalisation is **deliberately disabled until a verified before/after map exists** — a *Defer*
with a named precondition rather than a silent omission.

## The frame contract: wait once, cache, submit after every camera {#pose-timing-contract}

A survey of eleven independent VR mods found **five doing this wrong, one right, and one right by a
different route.** That ratio is the finding: the ordering is easy to get subtly wrong and the symptom is
latency or a hang rather than an error. `[SOURCE]`

The contract, from the one that reasoned it through explicitly:

```text
wait ONCE early in the frame  ->  cache the poses
   every camera renders from the SAME cached pose
      submit from an end-of-frame hook, after all cameras have rendered
         hand off to the compositor last
```

Each deviation has a named cost, and each was observed in this batch:

| Deviation | What it buys you |
|---|---|
| Letting each camera query "the latest pose" | **Mixed-age poses** - callback ordering between cameras is undefined, so the eyes can disagree |
| Waiting at the end of the *second* eye | A full frame of pose latency |
| Moving submit earlier "because it measured faster" | The wait moves with it - one project did this, gained "a little faster", and paid a full frame of latency the commit message never mentions |
| Submitting a texture the render thread still owns | **First-frame hang** - the compositor and the app wait on each other |
| Rendering from a *polled* tracking pose instead of the render pose you hand the compositor | Silent divergence between what you drew and what you declared |

That last one is worth dwelling on: one project's author documented it against themselves, named the
one-line fix, and had not applied it. **Rendering from a different pose than you submit is invisible
until someone compares the two numbers**, because both are individually plausible.

One project resolves it differently and legitimately: it re-polls **inside the render backend**, at draw
time - which is [late-latching](01-camera-and-tracking.md#delay-synthetic-latch-head), not a violation of
the contract above.

## Take both eye poses from the runtime; a scalar IPD cannot carry canting {#eye-offset-source}

Four positions in one batch, and they form a defect ladder: `[SOURCE]`

| Approach | Consequence |
|---|---|
| Both position **and rotation** from the runtime's eye-to-head transform | Correct. Carries canting. |
| One scalar taken from the transform's translation, applied symmetrically | Works on symmetric headsets; **silently drops eye canting** |
| Reconstructing the second eye from the first | Observed to produce **1.5x separation and a shifted cyclopean centre** - the captured first-eye transform was never used |
| No eye offset at all | Mono rendered to both eyes while appearing to be stereo |

**Never hardcode an IPD and never derive one eye from the other.** The runtime already has both poses and
they are not necessarily mirror images: canted displays fold rotation into the eye transform, and a
scalar has nowhere to put it. See [FAIL-STR-013](failure-atlas.md).

## Build a substitute runtime when no real one fits {#substitute-runtime}

The section below explains why 32-bit targets struggle to find a runtime at all. BioShock-Trilogy-VR
hit that wall from the other side and **wrote its own OpenXR runtime as a test instrument**, so agents
could verify VR work with no headset attached. `[SOURCE]`

**Why this was tractable, and the number that makes it a decision rather than a fantasy:** their entire
OpenXR surface was **39 entry points, one extension (`XR_KHR_D3D11_enable`) and one interaction
profile**. Count your own surface before dismissing the idea - a mod uses a small, closed subset of a
large API.

**An API layer cannot substitute for this.** A layer needs a working runtime *underneath* it, and with
no headset present the real runtime returns `XR_ERROR_FORM_FACTOR_UNAVAILABLE` - so there is no session
to intercept. If you need to run headless, you need a runtime, not a layer. `[SOURCE]`

### ...but a layer is exactly the right shape for OBSERVING one {#submitted-frame-recorder}

The sentence above is about *substituting*. Observation is the other job, and the layer wins it
outright. This fleet built `xr-tape` to do it. `[LIVE]`

There are three things between a game and a headset, and the mod in the middle is the one nobody could
watch:

```
   game draw stream  ──►  the mod  ──►  OpenXR runtime  ──►  headset
   ▲                      ▲               ▲
   a frame capture     THE GAP          a substitute runtime
```

A capture tool sees what the *game* drew. A substitute runtime answers what the *mod* asked. Neither
records **what the mod submitted**, which is the actual product - and which was only ever observable by
a person wearing a headset and remembering what they saw.

**Two checks exist only at this boundary**, because they compare what the runtime was *told* against
what the runtime *said*, from outside both:

- **submitted FOV against located FOV** - the declared projection must be the one that was rendered
  ([FAIL-STR-009](failure-atlas.md));
- **submitted pose against located pose** - *"log the value that reaches the submitted matrix, not the
  one computed"* ([FAIL-XR-011](failure-atlas.md)).

No in-process test can perform either on itself. A mod that lies to itself still cannot lie to the
wire.

**A layer needs no integration.** It works on every mod in a fleet on the day it is built, and on mods
you did not write - which is what makes a third-party integration readable as *measured behaviour*
rather than only as source. Link no graphics API and one binary covers every binding; identify the
graphics binding by walking the `next` chain of `xrCreateSession` and matching struct types by value.

### Two traps, both measured

**A layer sees only applications that use the Khronos loader.** A probe that `LoadLibrary`s a runtime
DLL and calls `xrNegotiateLoaderRuntimeInterface` itself never creates a loader instance, so **there is
nothing to insert a layer into**. That is a deliberate design in several fleet probes - it isolates
runtime defects from manifest and loader defects - and it puts them permanently out of reach. Detect it
rather than debug it: the string `xrNegotiateLoaderRuntimeInterface` in the client binary, or the
absence of `openxr_loader.dll` beside it.

**OpenXR handles are pointers in a 64-bit process and `uint64_t` in a 32-bit one.** So
`reinterpret_cast<uintptr_t>(handle)` compiles on x64 and **fails outright on x86** - which is half the
fleet. Copy the bits instead:

```cpp
template <typename Handle>
uint64_t HandleId(Handle handle) {          // handles are identity tokens, never interpreted
    static_assert(sizeof(Handle) <= sizeof(uint64_t), "unexpected OpenXR handle size");
    uint64_t id = 0;
    memcpy(&id, &handle, sizeof(handle));
    return id;
}
```

**Build both architectures from the first commit.** This was caught only because the x86 build was
attempted at all; a tool developed on x64 and shipped is a tool that serves the half of the catalogue
that did not need it most.

### Reading a stereo failure: which half is wrong

Two families of check, and the combination is the diagnosis:

| Result | Means |
|---|---|
| a **geometry** check fails alone | the runtime reported a bad rig and the mod passed it through faithfully - look at the runtime |
| geometry **and** submitted-vs-located fail | the mod mangled a good rig - look at the mod |

That distinction is only sharp if the falsification suite keeps it sharp: inject each geometry fault on
**both** the located and the submitted views. A fault applied only to the submitted side trips both
families at once, and the distinction goes untested. See [XR-007](pattern-catalog.md#xr-007).


**Four independent projects in this survey built one**, at four different price points. That is the
strongest signal in the batch that the headset round-trip is a first-class engineering problem rather
than an inconvenience:

| Project | Form | Cost | What it proves |
|---|---|---|---|
| BioShock-Trilogy-VR | A real 32-bit OpenXR runtime, selected per process via `XR_RUNTIME_JSON` | Highest | Protocol, geometry and composited content |
| ForerunnerVR | A **`Debug Emu` build configuration** swapping the VR backend for an emulated one drawing to a separate window | Low | Rendering and interaction, not protocol |
| OpenMW-VR | A **`CustomViewCallback`** supplying a fixed pair of views through the stereo interface that already existed | One class | Stereo geometry against a known HMD's view |
| perfect_dark_VR | Projection diagnostics logged from the runtime's own values | Lowest | Numbers, not pixels |

**The cost is set by whether an interface already exists**, and ForerunnerVR gives the measured version.
Its `IVR.h` is **112 lines**; the emulated backend behind it is **544 lines against the real OpenVR
backend's 570.** So a substitute of this kind is *not* free — it is roughly the size of the real thing —
but it needs no runtime, no loader and no protocol knowledge, and it was tractable only because the seam
predated it.

Their interface is worth copying wholesale:

```cpp
// Generic interface for interacting with a VR runtime, should be
// implemented for each vendor (OpenVR, OpenXR, etc) supported
class IVR {
    virtual bool EarlyInit() = 0;                       // near startup
    virtual bool Init(ID3D11Device*, ID3D11DeviceContext*) = 0;   // once D3D exists
    virtual void Shutdown() = 0;
    virtual void Update(float DeltaTime) = 0;
    virtual void SubmitEye(EVR_Eye, ID3D11Texture2D*,
                           const VR_Bounds& = {0,0,1,1}) = 0;      // sub-rect!
    virtual void EndFrame() = 0;
};
```

Two details that make it general. **Init is split in two** — an early phase near startup and a late
phase once the graphics device exists — which is the real lifecycle of an injected mod rather than a
convenient fiction. And **`SubmitEye` takes a bounds sub-rect defaulting to the whole target**, so a
single side-by-side render target and two separate per-eye targets travel through the same call.

**Write the seam first and the instrument becomes possible.** Note the comment says it was designed for
several vendors from the start — which is exactly why an emulated one slotted in later without a
redesign.

Reach for a full substitute runtime only when you also need to prove protocol, or - as with 32-bit
targets - when no real runtime fits at all.

### Select it per process, never machine-wide

The loader checks `XR_RUNTIME_JSON` **before** the registry. Setting that variable for one launched
process leaves the machine's `ActiveRuntime` untouched, so the real runtime and the substitute coexist
with no switching step and a normal launch is unaffected. Their mod binaries were **byte-identical**
between the two modes - the substitute links nothing from the mod.

The cost is honest and worth stating: the game cannot be started **through Steam** in this mode, because
Steam launches the process itself and the variable would have to be machine-wide.

### The two silent-failure traps, and why a printed warning is not enough

Both of these make the loader **fall back to the real runtime silently**, so every subsequent
measurement is taken against the wrong runtime while the transcript claims otherwise:

- an **elevated shell** makes the loader ignore `XR_RUNTIME_JSON` (it reads it through a secure-env
  path);
- a **bad manifest path or a 64-bit DLL** makes it skip the manifest.

Their guard asserts the runtime **name** out of the mod's own log and throws on anything unexpected, and
the installer checks the DLL's PE machine type is `0x014C`. The rule they drew is the transferable one:

> **A check that only prints is not a check.**

### The compositor is the payload

A substitute that merely accepts frames proves protocol. One that **composites** proves geometry, because
the layer's tagged pose and tagged FOV both differ from the eye's, so compositing per eye resamples
through that difference - which makes a **claimed-FOV mismatch visible as magnification** instead of
something to be inferred. They expose it as a single number, `derived.claimRatioH`.

That matters because an earlier **1.84x FOV under-claim took three sessions to pin down** by inference.
Add this to the [alignment differential diagnosis](#the-two-eyes-dont-line-up-a-five-minute-differential-diagnosis):
a compositing instrument turns that whole class into one measured ratio.

It also **retires a documented limitation**. Quad layers - aim laser, aim dot, HUD panel - exist only in
the compositor and never appear in a window screenshot, so "is the laser on screen" had been
un-checkable outside a headset. A compositing substitute counts them, and the question becomes an
assertion.

## The runtime may refuse your API version, and the loader will not say so {#api-version-negotiation}

**Two projects in this fleet hit this independently, and the second did not know the first had.** It
costs a session each time, and the fix is one line once you know which line. `[LIVE]`

`XR_CURRENT_API_VERSION` expands to whatever your SDK is. Build against OpenXR-SDK **1.1.x** and you are
asking every runtime for a 1.1 instance:

```
attempt api_version=1.1.60  result=XR_ERROR_API_VERSION_UNSUPPORTED
attempt api_version=1.0.60  result=ok
runtime name="VirtualDesktopXR" version=1.0.10
```

**VirtualDesktopXR 1.0.10 implements OpenXR 1.0 and refuses a 1.1 instance outright.** What reaches the
console is far less helpful than that:

```
Error [OpenXR-Loader] : LoaderInstance::CreateInstance chained CreateInstance call failed
FAIL: xrCreateInstance: XrResult(-4)
```

### Negotiate; do not hardcode the answer

The tempting fix is to change one constant to `XR_API_VERSION_1_0` and move on. **Do not.** Try
newest-first and fall back:

> The same unmodified binary works against both runtimes, and only because it tries newest-first and
> falls back rather than hardcoding a version. Had the probe been "fixed" by hardcoding 1.0 - the
> smaller change, and the tempting one - it would have worked on this machine's headset and been wrong
> the moment it met a 1.1 runtime.

A substitute runtime in this fleet **accepts** 1.1 where VirtualDesktopXR rejects it. That is the shape
that makes a version fallback worth writing: **a one-runtime reaction is indistinguishable from a
workaround until a second runtime disagrees in the other direction.**

### `xrResultToString` cannot name the failure that matters most

It requires a live `XrInstance`. So **the one failure worth naming - the one that stops an instance
existing - is precisely the one it cannot name**, and a probe prints `XrResult(-4)` for a whole session.
Any probe that names results through `xrResultToString` has this hole at instance creation. A static
switch over the common negative results is about twenty lines and closes it permanently.

### Read the loader log before you suspect a layer

`XR_LOADER_DEBUG=all` settles the whole family in one line:

```
LoadRuntime succeeded ... virtualdesktop-openxr-32.json
LoadApiLayers succeeded loading layer XR_APILAYER_NOVENDOR_motion_compensation
Entering loader terminator
Completed loader terminator          <- reached the runtime and returned
LoaderInstance::CreateInstance chained CreateInstance call failed
```

**`Completed loader terminator` appearing BEFORE the failure means the runtime itself refused**, which
rules out the loader and every API layer at once. Without it the obvious suspect is the implicit layer -
and it is a good suspect, since
[a third-party implicit layer really did cause a fail-fast elsewhere in this fleet](07-engine-integration-safety.md) -
so a project can spend a round trip disabling something that was never involved. See
[XR-008](pattern-catalog.md#xr-008).

## Running the headless instruments: xr-sim and xr-tape {#headless-instrument-operation}

The two sections above say *why* a substitute runtime and an observing layer exist. This is how to run
them day to day, and - the load-bearing half - how to read their results without being lied to. Three
instruments sit at three different boundaries, and confusing them is the common mistake:

```
   game draw stream  ──►  the mod  ──►  OpenXR runtime  ──►  headset
   ▲                      ▲               ▲
   apitrace            xr-tape          xr-sim
   (what it drew)   (what it submitted) (a runtime, no headset)
```

**Select the runtime per process; never machine-wide.** Generate a runtime manifest for the *target's*
architecture and set `XR_RUNTIME_JSON` only in the process that launches the game - a launcher that
detects x86 vs x64 from the PE header and restores its own environment immediately after is the safe
shape, because it leaves the machine's real headset runtime and every other application untouched.
`XR_RUNTIME_JSON` is a secure-loader variable, so do not launch from an elevated shell; a hardened
environment may ignore it and you will debug a phantom. `[SOURCE]`

**Drive it through its state channel, and wait for the acknowledgement.** A substitute runtime worth
using exposes a command/state/ack triple: the driver writes commands (head and hand poses, buttons,
sticks, triggers, validity bits), the runtime publishes rig/session/frame/layer/error state, and an ack
sequence tells you a batch was applied - committed atomically at the next `xrWaitFrame`, so a batch is one
frame's worth of input. Advance to a named frame and read `state.json` rather than sleeping. Scenarios
script this; keep the mod-specific command lines in an external script the scenario calls, so an inherited
scenario runs against a different mod unchanged.

**xr-tape needs no integration; that is the point.** It is an OpenXR API layer, links no graphics API
(one binary covers every binding), and reads the wire rather than the mod's own variables - so it works on
every mod in the fleet the day it is built, including mods you did not write, and a mod that lies to
itself cannot lie to the trace. Install it for the target's architecture, run the game under it with a
check pass, and check the trace against the runtime you expect. It carries the two checks no in-process
test can perform on itself - submitted-vs-located FOV ([FAIL-STR-009](failure-atlas.md)) and
submitted-vs-located pose ([FAIL-XR-011](failure-atlas.md)) - plus eye order, distinct sub-images, shared
display time, and validity bits, each naming the atlas row it implements so a red line leads to the
write-up.

Three reading rules keep a green run honest, and each is a lesson this fleet has paid for:

- **`SKIP` is not `PASS`.** A check that could not measure its property must say so, be counted, and be
  promotable to a failure (`--require`). An earlier tool skipped a check when its field was missing, so a
  main-menu run matched no pattern, nothing objected, and absence of evidence was read as evidence of
  validity. This is [META-013](pattern-catalog.md#meta-013) at the wire.
- **A green contract is not headset acceptance.** A full session can pass under the substitute and the
  same binary fail on the first *real* runtime - [FAIL-XR-022](failure-atlas.md). *xr-sim green is not a
  pass*; it clears the contract, not the experience.
- **The layer reads the wire, not the pixels.** `submitted_fov_matches_located` compares what the runtime
  was told against what it reported, not what the game's draws actually used - correlate with an
  [apitrace](11-re-anchoring-and-discovery.md#re-tool-surface) capture or renderer evidence, with explicit
  frame correlation, before calling the rendered projection correct.

**Prove the instrument can fail before you trust its clean verdict.** Both tools ship a self-test that
feeds every check a known-bad trace and requires each to fail - because a check never observed failing is
decoration, and this fleet has shipped a green suite over a no-op more than once. Run it after any change
to the checks. This is [#self-proving-instrument](06-debugging-methodology.md#self-proving-instrument)
made routine. And remember the two traps from [above](#submitted-frame-recorder): a layer sees only
loader-visible applications, and OpenXR handle widths differ between x86 and x64.

## Once a session exists, the runtime owns the frame pacing {#runtime-owns-pacing}

An engine frame cap and `xrWaitFrame` are two schedulers competing for the same frame. The runtime
already blocks in `xrWaitFrame` until the compositor wants the next frame; an engine cap on top of
that either fights it or silently caps the headset below its display rate.

**Set the engine's cap to unlimited once an OpenXR session exists, and only then.** MoH-VR's
`VR_Init` sets `com_maxfps 0` when the session is up, while the substitute-runtime path keeps its
pinned cap - because a substitute is not pacing anything and an unpinned loop there just burns CPU
and makes runs non-comparable. `[LIVE]` MoH-VR 2026-09-04.

The same reasoning applies to any engine-side limiter you find: vsync, a sleep in the main loop, a
"max foreground FPS" setting. In a VR session they are all downstream of the compositor, and the one
that should win is the one holding the swapchain.

## Three clocks, and borrow the engine's: reading the frame timeline for alternate-eye {#three-frame-clocks}

[#pose-timing-contract](#pose-timing-contract) fixes the *order* - wait once, cache, submit after every
camera. Alternate-eye adds a question the order does not answer: **which frame is this, and therefore
which eye?** Two shipped ports on two engines converged on the same answer, and it is engine-agnostic.
`[SOURCE]` starfield2vr and anvilengine2vr, read via vrframework's guide 07 and `spi/FrameTimeline.hpp`;
receipts resolved against the raw upstream files 2026-09-10.

**Keep three clocks, not one.** A flat game has one meaningful frame count. A staged pipeline has three,
each advancing on its own thread's beat:

| Clock | Advances when | What it decides |
|---|---|---|
| **engine** | the main loop ticks the world | which eye this frame is; when to sample the HMD pose |
| **render** | the render thread starts recording draws | whose commands are being built - view injection, history |
| **presenter** | the frame is handed to the swapchain | the cadence the headset actually sees; drift detection |

They are not equal at any instant - the engine runs one or two ahead of what is being presented, and
that pipelining is good. The mod's job is to know which one just ticked.

**Borrow the engine's frame index; count your own only when it has none.** Creation Engine 2 hands its
frame number to every NVIDIA Reflex marker (`oldFrameIndex`); the port copies it into all three clocks
and never invents one. Anvil's per-frame functions carry no index, so that port increments its own engine
counter and derives the other two from it. One line absorbs the difference - `frame ? frame : (count + 1)`
- and the rule behind it is what keeps alternate-eye honest: **the engine's own number is the authority
whenever it exists.**

**Look for instrumentation the engine already calls every frame.** An integrated latency or telemetry
SDK - Reflex, Streamline, PIX markers, a profiler's frame boundary - is emitted from the engine's own
threads at the engine's own pacing and carries its frame index. That is the timeline signal, already
wired through the whole pipeline. starfield2vr hooks one function, `setReflexMarkerInternal`, and decodes
marker IDs: **6/0/1** (first to arrive wins, guarded) is the engine edge - sample the pose, begin
rendering, advance the overlay; **2** sets the render clock; **4** sets the presenter clock
(`CreationEngineRendererModule.cpp:319-353`). This playbook had no mention of any of these SDKs before
this section; check for them before hooking the game loop.

**Hook the internal marker function, not the high-level callback.** The same port first tried
`worldTick` and the Streamline-level `sl::ReflexMarker` callback. That path "sometimes give 2 ticks" per
frame and was abandoned - `CreationEngineGameLoop.cpp` survives upstream with all 145 lines commented
out, which is the useful fossil. A cadence source that is not 1:1 with frames cannot carry parity, and
[STR-012](pattern-catalog.md#str-012)'s off-headset test - publishes per rendered frame - is exactly what
catches it.

**Size the synchronisation machinery to how untrustworthy the signal is.** Anvil's two structural hooks
are called once per frame, in order, so that port trusts them: no warm-up, no drift check, no recovery,
about fifty lines. Starfield's marker stream is asynchronous and multi-threaded, so that port polices it:
a warm-up gate (`frames_since_reset > 100` - transients at startup and after loads are normal), a check
for a render/present marker arriving while the port believed it was inside a clean left-then-right pair,
and one recovery - **skip the next present** (`CreationEngineRendererModule.cpp:364-373`). Dropping a
frame is the only correction that re-phases alternate-eye without showing a wrong eye; it is
[STR-010](pattern-catalog.md#str-010)'s mechanism for a different reason, and it inherits STR-010's rule
that a drop must stay rare, bounded and counted.

**Parity is a contract three consumers share.** Even engine frame = left, odd = right - decide once. View
injection, the eye the runtime is told about, and the per-eye history bank in
[14](14-render-pass-hazard-atlas.md#per-eye-history-bank) must all read the *same* counter, or the history
fix is silently keyed to the wrong eye. The history fix is only correct *because* the parity is.

**Verify with a counter readout, not your eyes.** Log all three clocks every frame. They should advance in
lockstep, one apart, with stable parity. A counter that jumps by two, or a parity that flips without a
logged skip, is the bug - visible in a log long before a wearer feels it, and the same proof shape as
STR-012's push-minus-pop depth. See [STR-014](pattern-catalog.md#str-014).

## What UE3 gives you for stereo, and the one thing it cannot express {#ue3-stereo-shape}

Read from a UE3 licensee source tree and directly reusable by every UE3 target. `[SOURCE]`

**UE3 already renders more than one view per frame.** `SceneRendering.cpp` iterates
`ViewFamily->Views` and `BeginRenderingViewFamily` is called **once**, drawing all of them - and
`CalcSceneView` **appends its own view to the family before returning**. So the second eye is obtained by
calling the function you already hook, **twice**. Each view must carry a **distinct `ViewState`**; stock
UE3's RealD path allocates a second one, and a `NULL` state on the second view is explicitly tolerated,
costing only temporal effects on that eye - **the cheap first rung.** `[INFERENCE - read from source, not
yet run by any project.]`

**It also ships a stereo hook and a data-only override:**

- **`CalcSceneViewOffs(..., FMatrix* Offset, ...)`** exists under `WITH_REALD`, and its entire eye offset
  is **one post-multiply on the finished view matrix**, applied *after* the world-to-view swizzle - i.e. a
  **view-space** transform, where the basis is X-right, Y-up, Z-forward, so an IPD offset is a
  translation on view X. Even compiled out, it tells you **where** an eye offset belongs and **in which
  space**.
- **`bOverrideView`** - `CalcSceneView` opens with
  `if (bOverrideView) { ViewLocation = OverrideLocation; ViewRotation = OverrideRotation; }`, and in at
  least one shipped build those are **globals**. **Three data writes drive the render view with no code
  patching at all** - worth checking for on any UE3 target. Two costs: it forces
  `fFOV = Actor->DefaultFOV`, bypassing the zoom curve (**which is simultaneously an FOV lever**), and
  leaves `bCameraCut` FALSE, so temporal effects are never told the view jumped.

**And the one thing it cannot do: UE3 has no off-centre projection helper anywhere in `UnMath.h`.**
`FPerspectiveMatrix` is symmetric by construction, and **adjusting FOV cannot produce an asymmetric
frustum**. OpenXR hands you four independent per-eye angles, so the per-eye projection **must be
hand-built** and written over `FSceneView::ProjectionMatrix`.

**A free identification signature:** `CalcSceneView` passes `GNearClippingPlane` as **both** `MinZ` and
`MaxZ`, taking the `MinZ == MaxZ` branch - `m22 = 0.999`, `m23 = 1`, `m33 = 0`, an **infinite far
plane**. That shape in a live capture identifies a UE3 projection without symbols.

## A substitute that is SIMPLER than production is a subtler trap {#simpler-substitute}

The section below is about a substitute enforcing *less*. This is the complementary failure and it is
harder to see: **the substitute is a simplification, so code that depends on the simplification is
correct on the substitute and silently wrong on real hardware.** `[HEADSET]`

Measured by Sims4VR, same client, same day - and independently by PreyVR:

| | substitute | VirtualDesktopXR / Quest 3 |
|---|---|---|
| eye texture | 2064x2208 | **2688x2880** |
| left-eye fov | `l -54 r 44` **`u 55 d -55`** | `l -54 r 40` **`u 44 d -55`** |
| horizontal asymmetry | 10.0 deg | 14.0 deg |
| **vertical asymmetry** | **0 deg (symmetric)** | **11 deg** |
| IPD | 63.0 mm | 64.7 mm |

**The substitute's frustum is vertically symmetric; the real one is not.** Any code assuming the optical
axis sits at the centre of the eye texture passes every desk test. On a 2880-tall image the centre is
1440 and the true axis is at **1161** - a **279-pixel vertical error**, which presents as eye strain
rather than as an obvious fault.

**Rule:** enumerate what the *real* runtime reports and pin your selftest cases to those measured
numbers, keeping the symmetric case only as a control. A test fixture built from a substitute's
defaults inherits every simplification the substitute made.

## A substitute that is MORE permissive than production is a weaker gate {#permissive-substitute}

The version fault above passed a full simulated session because **the simulator did not enforce a
constraint the real runtime does**. That generalises past OpenXR: `[LIVE]`

> A test instrument that is more permissive than production silently converts "passed the gate" into
> "passed a weaker gate", and the failure surfaces only when someone has a headset on - the most
> expensive place to find it.

The section below says trust in a substitute is asymmetric. This is the sharper operational form of it:
**enumerate what your substitute does not enforce, and write that list down in the substitute's own
docs.** A project that reads a green run as evidence about real runtimes is not being careless if
nothing ever told it the gate was narrower - and inferring the limitation yourself, correctly, in your
own tree, does not help the next project.

### Fidelity is a model, and trust in it is asymmetric

One runtime's observed behaviour is not the specification. They found that one runtime would not
re-grant `FOCUSED` to an app submitting nothing - and rather than baking that in as truth, they modelled
**both** policies behind a switch with the default stated rather than assumed. The standing rule:

> **A bug that reproduces in the substitute is real. One that does not may still exist on the real
> runtime.**

Two disciplines keep the instrument from becoming the bug:

- **No wait is ever unbounded** - every wait takes a finite timeout, no lock is held across one, and
  step mode grants a frame after 30 s of starvation. An agent that walks away mid-step leaves a slow
  game, never a hung one.
- **Compositing is off except on capture frames.** A test instrument that costs frame time becomes the
  pacing bug it was built to find.

**State what it will never model.** Theirs excludes lens distortion, chromatic aberration,
timewarp/reprojection, real display cadence and the wireless encode path. It proves **geometry, content
and protocol**; comfort, judder and world scale remain a headset verdict. An instrument with a written
boundary is trustworthy inside it - see [TEST-001](pattern-catalog.md#test-001).

!!! danger "The blind spot they found the hard way: session-state negotiation"

    **A substitute that force-grants focus makes every session-state negotiation bug invisible to it.**
    Theirs does exactly that, and the first real headset attach after it was built found **two such bugs
    in one evening**: `[SOURCE]`

    - **bring-up** - a never-focused session must pump frames in order to *reach* focused;
    - **re-attach** - the real runtime never re-promotes a session submitting empty keepalives, so it
      parks at `VISIBLE` / `shouldRender=0` forever.

    Both were **structurally unreachable** in the simulator *and* in flat soaks, because no runtime means
    no session at all. So sharpen the standing asymmetry: a bug that reproduces in the substitute is
    real, one that does not may still exist on the real runtime - **and an entire class of them cannot
    reproduce there by construction.** Anything touching session begin, focus transitions, keepalive
    submission or re-attach must be proven on a real runtime.

### A camera-constant remap is a no-op on anything already in clip space {#clip-space-immune}

The structural limit of every stereo correction that works by rewriting shader constants, and it
presents as a single element that will not duplicate no matter what you do to it. `[SOURCE]`

Singularity VR's sniper scope survived four wrong fixes. The overlay is `DrawPrimitive`, triangle strip,
2 primitives - **a fullscreen quad from a bound vertex buffer, already in clip space.** Their
`StereoPair` path duplicates a draw and scissors each copy to a half, then remaps the camera registers:

> This quad **reads no camera register**, so the remap is a **no-op** on it. Both copies landed at
> identical full-frame coordinates and each was clipped to its own half: **one circle across the seam.**

And the control that proves it: *"it also explains why the HUD was always fine - `HudStereoPair`
transforms `c5`-`c8`, which the HUD shader **does** read."*

**Ask what the shader reads before designing a correction for it.** A constant-based stereo path can
only move geometry whose position depends on the constants you are moving. Anything authored in clip
space - fullscreen quads, post-process passes, overlays, scope and letterbox art - is immune by
construction, and duplicating it without transforming it produces two identical copies, each cropped,
rather than a stereo pair.

**And there may be more than one view-projection to remap.** The same project found *"a second
view-projection at `vs c13` [that] is never remapped"*, with the symptom landing on shadows - geometry
rendering correctly while its *shadow* was mis-projected and split across the seam. **A remap that
covers the register you found first leaves every other one untouched**, and the passes that read the
second register are usually the derived ones (shadows, reflections, decals), which is why the symptom
arrives detached from the geometry it belongs to.

The general test is cheap: **for each element that will not respond, dump the constants its shader
actually reads.** An element that reads none of the registers you are remapping needs a different
mechanism entirely - a vertex-level transform, a per-copy viewport, or its own dedicated path.

### A redirect must cover every bind, not the first one {#redirect-every-bind}

A black eye on *some screens only* is a binding problem, not a maths problem, and the distinction saves
a session. `[SOURCE]`

Psychonauts VR carried a "black left eye" bug for twelve sessions, hypothesised as frustum or parallax.
Live tracing found something simpler and stranger: **on that screen the engine re-binds the real
backbuffer in the middle of the eye pass** and draws the whole scene there, leaving eye 1's surface at
its cleared black. The fix was three redirects rather than one.

**An engine may re-bind its own render target at any point in a frame** - for a fullscreen effect, a
screen-space pass, or a special-case screen like a title or loading sequence. If your redirect only
covers the bind you found first, every other bind escapes it.

The diagnostic is the pattern of failure, and it is worth reading correctly:

| Symptom | Points at |
|---|---|
| One eye black **on specific screens** | a **bind** your redirect does not cover |
| One eye black **everywhere** | the surface, the submit, or the copy |
| One eye **wrong but drawn** | the camera or projection maths |

Their old hypothesis was in the second and third columns for twelve sessions. **Which screens fail is
data**; a bug that respects screen boundaries is following a code path, not an equation.

### Do not derive a buffer index from a success counter {#index-deadlock}

A closed circular dependency that presents as total silence, found by reading rather than guessing.
`[SOURCE]`

Psychonauts VR's `Submit` had **never been called once in a 1763-frame session.** The double-buffer
index selecting which readback slot to write was computed as `hop1Count % 2` - but `hop1Count` only
increments when the readback fully succeeds, and that success requires the *other* slot to have been
written by a prior call, which can only happen once `hop1Count` is odd:

```
bCur = hop1Count % 2          -> stuck at 0 forever
  because slot[1] is never written
  because the promotion branch never runs
  because pendingB[bPrev] is never TRUE
  because hop1Count never leaves 0
```

**An index derived from a success counter cannot bootstrap**: the state that would let you succeed is
selected by having already succeeded. Drive the index from a **free-running** frame counter and keep
readiness in a separate variable - they are different questions and one must not gate the other.

**And confirm silence two ways.** Their verdict was reached *"two independent ways, not inferred from
silence alone"* - a code-level reading of the dependency plus counters proving the branch never
executed. A feature that never fires produces exactly the same logs as a feature that fires and does
nothing.

### Swapchain images come back TYPELESS, so name the view format {#typeless-swapchain}

A bring-up failure with a misleading shape: you asked for a format, the runtime gave you a different
number, and your first `CreateRenderTargetView` fails. `[SOURCE]`

```
[xr] swapchain texture: 1024x1024 DXGI format=90 bind=0x000000A8  (requested 91)
```

`90` is `DXGI_FORMAT_B8G8R8A8_TYPELESS`; `91` is what was requested. **The runtime allocates typeless
deliberately**, so the same image can be viewed as either sRGB or UNORM - which is what lets the
compositor and the application disagree about gamma without a copy.

**The consequence is one line of code.** `CreateRenderTargetView(tex, nullptr, &rtv)` **fails**: a null
description means *"use the resource's own format"*, and a typeless format cannot be a view format. The
view description must **name the format explicitly**.

Two things follow. **Do not treat the returned format as a rejection of your request** - it is not the
runtime declining `91`, it is the runtime giving you something that can *become* `91`. And **the format
you name in the view is the gamma decision**, so make it deliberately rather than copying whichever
constant happened to compile - see the
[sRGB double-brightening trap](#d3d9ex-vs-classic) for what the wrong choice looks like.

### When tracking drops, decay toward neutral - never hold the last value {#decay-not-freeze}

A three-line bug with a permanent symptom, and the instinctive fix is the wrong one. `[SOURCE]`

Singularity VR ended a run with its 6-DOF offset frozen at `(29.8, -30.8, -27.7)` UU - about **0.9 m of
permanent displacement**, repeated identically frame after frame with no way back. The cause is a
mismatch most people never think about: **orientation and position do not fail together.** The IMU
carries rotation, so orientation kept working; position needs the cameras, and it dropped. Their update
skipped, and the last value persisted forever.

> **Skipping the update looked like the safe choice and was the worst one.**

The fix is to **decay the offset toward neutral whenever `XR_VIEW_STATE_POSITION_VALID_BIT` is clear**,
so the view drifts home over about a second and recovers by itself when tracking returns. That is
[META-005](pattern-catalog.md#meta-005)'s rule - choose the representation so the *expired* state is the
safe one - applied to a pose rather than to a published fact.

**Check the two validity bits separately.** A runtime reporting orientation-valid and position-invalid is
a normal state, not an error, and code that tests one bit for both will hold a stale translation while
the view keeps turning - which reads as the world having moved.

### Deriving a tangent from `m00` drops the axis multiplier {#axis-multiplier}

A correction to a formula that spread **between two projects without ever passing through this
playbook**, and which is wrong in exactly the configuration a stereo mod creates. `[SOURCE]`

The circulating derivation is `tanH = 1 / m[0][0]`. UE3's six-argument `FPerspectiveMatrix` actually
builds:

```text
m00 = MultFOVX / tan(HalfFOVX)
m11 = MultFOVY / tan(HalfFOVY)
```

so the general form is **`tanH = MultFOVX / m00`**. `CalcSceneView` sets `XAxisMultiplier = 1.0` **only**
when the viewport is wider than tall under `AspectRatio_MajorAxisFOV`; otherwise it is `SizeY/SizeX`.

**Why it went unnoticed is the whole lesson.** On an ordinary widescreen desktop the two agree exactly.
They diverge on a portrait or square viewport - **and on any per-eye viewport whose aspect is not the
window's**, which is the configuration a stereo mod exists to create. The formula was correct everywhere
it had been tested and wrong everywhere it was about to be used.

**Generalises past UE3:** any engine whose projection build carries an axis-multiplier or
aspect-correction term makes `tan = 1/m` a special case. Read the matrix builder before inverting it, and
[verify the result against a witness the engine never supplies](06-debugging-methodology.md#external-witness).

### Who owns the projection decides whether "declared == located" is right {#projection-authority}

[The declaration law](#submitted-frame-recorder) says declare what you rendered. The corollary is sharper
than it first looks, and three projects converged on it independently. `[HEADSET]`

| Your mod | Correct outcome of "submitted FOV == located FOV" |
|---|---|
| can force the engine's projection to the runtime's | **equal** - you rendered with it, so declaring it is true |
| **cannot** - an injector over the game's own frustum | **different** - and equality is the defect |

**An injected mod cannot change what the game renders**, so its pixels come from the game's frustum.
Declaring the runtime's preferred FOV over them is a statement about the image that is not true, and
**the runtime cannot detect it** - it reprojects to whatever is claimed, so the error surfaces as wrong
depth and wrong scale rather than as an error.

Measured: Prey renders **120 deg horizontal by 88.507 deg vertical, zero asymmetry**; a Quest 3 reports
`l -54.0, r +40.0, u +44.0, d -55.0`. Declaring honestly makes the right edge differ by **20 degrees**.

> **For an injected mod, that mismatch is the pass.**

State it in the imperative, because the instinct on seeing a red check is to make it green - and here
green means something overwrote the declaration with the runtime's numbers.

### If you submit a sub-rectangle, derive the FOV FROM the rectangle {#subimage-fov-pair}

The playbook's standing advice is to leave `imageRect` alone and keep the runtime's projection. When a
design genuinely needs to submit part of a larger image - a symmetric producer serving two eyes, a
presentation-size control - this is how to do it without breaking the
[frustum-declaration law](#submitted-frame-recorder). `[SOURCE]`

Witcher3-VR's route renders **one centred angular envelope** and submits an eye-specific part of it.
`XrRect2Di` is **integer pixels**, so the crop quantizes - and the FOV you *wanted* is not the FOV the
rectangle actually covers. Their rule:

> The represented FOV is **derived back from the quantized integer rectangle**, so OpenXR rays stay
> paired with the exact source pixels selected by `imageRect`.

The direction matters: rect first, FOV second. Declaring the pre-quantization FOV declares an image you
did not submit, by a sub-pixel amount that is still a lie about where the rays go.

**And round outward, deliberately:** *"tangent-space leading edges are floored and trailing edges are
ceiled so quantization never drops a requested ray at the boundary."* Rounding to nearest can shave a
requested ray off an edge; rounding outward can only include a pixel you did not need.

### Changing presentation size without destroying the asymmetry

[PERF-005](pattern-catalog.md#perf-005) establishes that presentation scale is an FOV change, not a
resolution change. The mechanism has to preserve the principal point:

- **Scale all four tangent extents around the eye's optical axis**, not the angles, and not around the
  image centre - that *"changes angular presentation size while preserving the asymmetric principal
  point"*. Assert the identity: **a scale of 1 must return the original `XrFovf` exactly.**
- **Or keep the FOV and shrink the image on a black canvas.** Their alternative letterboxes the completed
  eye image around its optical axis while *"the submitted FOV remains the established route FOV"*. Two
  legitimate designs - what is not legitimate is changing one and not the other.

**One inherited-constant trick worth stealing.** A legacy left-eye HUD shift measured in pixels on one
parallel-view headset was converted into an **inverse physical distance** for a cyclopean HUD plane,
which *"preserves the legacy shader's exact shift semantics while making the resulting plane portable
across eye geometry."* When you inherit a magic pixel offset, convert it into a property of the world -
a distance, an angle - and it survives a different IPD, a canted display and a different resolution.

**A sign trap in the same lane:** **pixel-space Y grows down while OpenXR NDC Y grows up.** A positive
optical-centre Y therefore becomes a positive *source* offset and moves the displayed element **upward**.

### Read the backbuffer format from the SURFACE, never from the creation parameters {#format-from-surface}

A one-line habit that has already cost one project in this survey a `D3DERR_INVALIDCALL`. `[SOURCE]`

`D3DPRESENT_PARAMETERS::BackBufferFormat` is a **request**, and in windowed mode it is explicitly
permitted to be `D3DFMT_UNKNOWN` - the runtime picks the desktop format. So the parameters you logged at
`CreateDevice` are not necessarily the format the surface has. Read it from the object instead:

```
GetBackBuffer -> GetDesc      <- authoritative
D3DPRESENT_PARAMETERS         <- what was asked for
```

Mirror's Edge VR measured `A8R8G8B8` this way over 6,832 frames including two resolution changes. The
Singularity project's `D3DERR_INVALIDCALL` came from a note recording **`X8R8G8B8` where the answer was
`A8R8G8B8`** - a shared-surface creation refused because the format in the notes was the requested one.

Two more properties worth logging in the same pass, because both change the architecture:

- **`MultiSampleType`.** None means **no resolve step before sharing**, which removes a whole stage.
- **`D3DPRESENTFLAG_LOCKABLE_BACKBUFFER`.** Unusual, and it means the backbuffer can be locked directly -
  possibly a cheaper frame grab than `GetRenderTargetData`. Measure it rather than assuming: a lockable
  backbuffer carries a known driver-side cost on some hardware.

**And a resource-pool census sizes a port before you start it.** `D3D9Ex` does not support
`D3DPOOL_MANAGED` at all, so the count of `MANAGED` allocations *is* the size of the translation problem:
Mirror's Edge measured 11,084 against Singularity's 10,454, close enough that Singularity's texture
wrapper should transfer at similar cost. Their `DEFAULT` counts differ by two orders of magnitude and
that is recorded as **unexplained rather than concluded**, because the sessions may not be comparable.

### Classic D3D9 cannot share a texture, and that decides your architecture {#d3d9ex-vs-classic}

[Chapter 10](10-graphics-apis.md) records that the D3D9Ex interop route *requires* D3D9Ex rather than
plain D3D9. fear-vr hit the wall from the other side and documented what happens, which turns a
requirement into a decision procedure. `[SOURCE]`

**F.E.A.R. creates a classic `IDirect3DDevice9`, and a shared texture created directly on that device
was rejected with `D3DERR_INVALIDCALL` on the tested system.** So the project carries two paths, and
keeps them visibly separate:

```text
D3D9Ex - the real path, no CPU readback
  Present -> StretchRect into three shared-texture slots per eye
          -> D3DQUERYTYPE_EVENT fence
          -> versioned Local\ IPC carrying frame-ID and generation
          -> OpenSharedResource + CopyResource (x64 D3D11 host)
          -> fullscreen shader into both OpenXR swapchains

classic D3D9 - the compatibility path, and it is debt
  game backbuffer -> StretchRect into a D3D9 render target
                  -> GetRenderTargetData into system memory
                  -> row copy into a D3D9Ex sysmem surface
                  -> UpdateSurface into a D3D9Ex shared texture
                  -> unchanged D3D11/OpenXR host path
```

**Check `Direct3DCreate9` versus `Direct3DCreate9Ex` before you design anything**, because the answer
decides whether you get a GPU path or a per-frame readback - and on a hybrid-GPU machine it also decides
how you resolve the adapter. fear-vr's order for that: `IDirect3D9Ex::GetAdapterLUID` first; failing
that an exact vendor/device/subsys/revision match against DXGI; failing that a monitor-to-DXGI match,
which is the only route left for a classic device.

**How they carry the compromise is the transferable part.** The fallback publishes a runtime diagnostic
flag (`FEARVR_BF_CPU_FALLBACK`), logs `path=cpu_d3d9ex`, and the document states plainly that it
*"contradicts the production invariant 'no per-frame CPU readback' and is a performance and comfort
problem that must be removed before a playable release."* **A named compromise with a runtime flag and a
stated invariant it violates is debt; the same code without those is just the design.**

One optimisation worth stealing whatever your transport: they moved HUD compositing **onto the game's
own device** as a pixel shader, so the bridge carries finished eye images and only one surface is read
per eye rather than compositing after the transfer.

### What a cross-process frame protocol needs {#bridge-protocol}

Their `protocol.h` is the most complete example in this survey, and every field earns its place.
`[SOURCE]`

- **Three slots per eye**, each `EMPTY` / `WRITING` / `READY` / `CONSUMING` - a real ring with a claim
  protocol, not a double buffer.
- **Separate host and game heartbeats**, so either side can tell which of them stopped.
- **Host and game adapter LUID**, checked *before* the import - the exact gap Swat4-VR flagged as
  unchecked in its own build.
- **A seqlock** for the current XR render request, and **64-bit shared handles with frame ID and
  generation**.
- **Every kernel object carries a random session ID**: `Local\FearVr.M2.<session>.Mapping`,
  `.FrameReady`, `.SlotConsumed`. **Two instances then cannot collide** - a fixed name means a second
  launch silently attaches to the first one's shared memory.
- **Magic, version, header size, slot size and slot count are all validated on connect**, and an
  incompatible protocol is refused. The header is **exactly 432 bytes in both x86 and x64**, which is the
  discipline that makes a cross-bitness struct safe at all.

Two host-side rules from the same document: **claim only matching `READY` slots from both eyes**, and
**copy into a private texture** so a D3D9 shared texture that has already been recycled cannot still be
read by a live OpenXR swapchain.

### Late attach: an IAT hook can be too late {#late-attach}

Worth knowing because the symptom is a hook that never fires and looks correct. F.E.A.R.'s GameClient
module is loaded through the official `-archcfg` layer, **which starts only after the engine has already
created its D3D9 device** - so an IAT hook on `Direct3DCreate9` has nothing left to intercept.
`[SOURCE]`

fear-vr's answer reuses the throwaway-device idea for a different purpose: **create a hidden helper
device deliberately, read the `Present` and `Reset` targets out of its vtable, and install detours on
those** - with MinHook pinned to a fixed version, and installed **outside `DllMain`**. They keep the
early proxy path as well, for test producers that do load first.

**Ask when your code runs relative to device creation before choosing a hooking strategy.** Anything
loaded by a game's own module system, a script extender, or a late plugin loader is likely to be after
it.

### D3D8 is a rung below that, and the answer is to leave the process entirely {#d3d8-route}

If D3D9 has no OpenXR binding, D3D8 has less than nothing: **no shared surfaces at all**, so there is no
GPU path out of the process even in principle. Silent Hill 3 VR's frame producer is therefore a
system-memory chain, and it is worth reading as the floor case. `[SOURCE]`

```
IDirect3DDevice8::GetBackBuffer      (vtable slot 16)
  -> IDirect3DDevice8::CopyRects     (slot 28)  into a SYSTEMMEM surface
    -> IDirect3DSurface8::LockRect   (slot 9)
      -> memcpy into a shared memory section
        -> SetEvent, picked up by sh3vr_host64.exe
```

Two practical notes on working at this vintage: **the modern SDK no longer ships `d3d8.h`**, so the
interfaces are reached by hardcoded vtable slot indices behind named constants - and that is the normal
answer, not a hack. And the numbers from
[the profiling session in ch19](19-d3d12-and-performance.md#blocking-wait-floor) say the readback is
cheaper than its reputation: measure before treating it as the bottleneck.

**The architectural statement in their source header is the transferable part**, and it is a better
argument for the out-of-process route than bitness alone:

> Nothing here touches OpenXR or D3D11: **the 32 bit game process stays clean** and every headset facing
> call happens in the 64 bit host.

**The 32-bit process holds no XR stack, no second graphics API and no runtime loader** - it copies bytes
into shared memory and signals an event. Everything that can crash, hang, hold a device or fight the
game's own allocator lives in a process you can restart. That is worth having even when bitness is not
forcing your hand.

Two lifetime details worth copying from it, because an orphaned helper is the obvious failure mode:
**the proxy starts the host itself** (no console window), and **passes the game PID so the host exits
with the game**. And the host refuses to run standalone - it *"must not be started without the proxy's
shared-frame producer."*

Their proxy name is `dinput8.dll`, which is the [uncontended-proxy](18-beyond-the-native-injector.md#uncontended-proxy)
choice again from a different angle - a fourth project avoiding the graphics DLL everything else fights
over.

### Submit from the thread that owns the immediate context, not a VR thread {#submit-thread-affinity}

A constraint that is easy to design straight past, because the tidy architecture is the wrong one.
`[SOURCE]`

OpenVR's documentation is explicit: **`IVRCompositor::Submit()` "should only be called from the same
thread you are rendering on"** - meaning whichever thread owns the D3D11 immediate context that issues
the final present, not an arbitrary worker. Getting it wrong does not produce a clean error. It produces
**intermittent corruption or crashes**, which is the expensive kind of wrong.

**The natural instinct is to decouple.** A dedicated "VR thread" that owns the session, the poses and
the submission looks like good separation, and it is exactly what the constraint forbids.

The good news is that the correct thread is one you have already found. **`Present` is an
immediate-context and swapchain operation** - a deferred context cannot call it - so a working `Present`
hook is *by construction* on the thread that owns the immediate context. **Do the submit inside the
present hook or immediately after it, on that thread.**

This matters most on engines that record on deferred contexts, where "the render thread" is ambiguous.
The Evil Within records draw commands on **six worker threads simultaneously** and replays those command
lists from a **seventh** into the immediate context; naming "the rendering thread" there without care
picks the wrong one of seven. The same architecture is why such engines need
[`--opt-capture-all-cmd-lists` to capture at all](06-debugging-methodology.md).

And on a native D3D11 target the submission itself is a non-event: `Submit()` takes
`TextureType_DirectX` with a live `ID3D11Texture2D*`, a first-class intended path, with none of the
readback or interop work a [D3D9 target](#no-d3d9-binding) needs. **Renderer generation, not engine
complexity, decides how hard the last step is.**

### There is no OpenXR graphics binding for D3D9 {#no-d3d9-binding}

A gate worth knowing on day one, because it decides whether a D3D9 target is a weekend or a month.
**OpenXR binds to D3D11, D3D12, OpenGL and Vulkan only.** A D3D9 game therefore cannot submit directly,
and the bridge is the make-or-break spike. `[SOURCE]`

It is worse than one conversion, because **shared-surface interop requires a D3D9Ex device** and a
2010-era game calls `Direct3DCreate9`, not `Direct3DCreate9Ex`. Singularity's three routes, in their
order of preference:

1. **Hook `Direct3DCreate9` and return a D3D9Ex-backed device.** Create a render target with a shared
   handle, open that handle as an `ID3D11Texture2D`, submit to an OpenXR swapchain on a D3D11 device.
   Note that `D3D11_RESOURCE_MISC_SHARED_KEYEDMUTEX` **has no D3D9 counterpart**, so synchronisation
   has to be arranged by hand.
2. **`GetRenderTargetData` to system memory, then upload to D3D11.** Slow, but it proves the pipe end to
   end - and [measurement says the readback is cheaper than it sounds](19-d3d12-and-performance.md#blocking-wait-floor).
3. **Translate D3D9 wholesale** with DXVK or dgVoodoo2, then treat the game as Vulkan or D3D11.

**Spike this before building anything around it.** Their own instruction - *"do not build scaffolding
around an unproven pipe"* - is the general rule for a make-or-break dependency, and the three scoping
steps they put ahead of writing the mod (bridge spike, 32-bit session check, decrypt and stand up
pattern scanning) are independent, each could change the plan, and none of them require the mod to
exist.

### Three answers to "my game is 32-bit and my runtime is not" {#bitness-routes}

Because this constraint decides architecture rather than a detail, here are the three routes this
survey contains, with the trade that picks between them. `[SOURCE]`

| Route | How | Cost | Take it when |
|---|---|---|---|
| **Use a 32-bit-capable API directly** | Link `openvr_api.dll` (32-bit build still shipped) and submit to SteamVR. bfbc2-vr does this. | Lowest. No extra process, no shim. | You are targeting SteamVR anyway and do not need OpenXR features. |
| **In-process shim** | Implement the OpenXR surface your mod imports, over OpenVR, in a DLL named `openxr_loader.dll`. BioShock-Remastered-VR does this. | One runtime implementation, ~the same surface a [substitute runtime](#substitute-runtime) needs. | Your mod is already written to OpenXR and you want it unchanged. The shim becomes an install-time swap. |
| **Out-of-process 64-bit helper** | A separate x64 process owns the OpenXR session; the 32-bit game shares its eye textures across. L4D2VR and its Black Mesa port do this. | A process boundary, a bridge protocol, and a lifetime to manage. | You need the **real** OpenXR runtime - its features, its extensions, its vendor support - not an emulation of it. |

The third is the one worth describing, because the mechanism is reusable well beyond bitness. In the
Black Mesa port the Win32 `d3d9.dll` still renders through DXVK in-process; `OpenXRHelper64.exe`
creates the OpenXR session (D3D11 and/or Vulkan), **imports the eye textures as `OPAQUE_WIN32_KMT`
shared handles over a shared-memory bridge**, and calls `xrEndFrame`. Textures cross the process
boundary by handle, so no pixels are copied.

Three details in that bridge are general to any cross-process mod:

- **The shared block is versioned and magic-tagged** (`L4D2VROpenXrBridgeState`, magic `0x5258344C`,
  version 12). Two independently-updated binaries will eventually disagree about the struct; a magic
  and a version turn that into a clean refusal instead of garbage geometry.
- **The helper is optional and the fallback is the desktop game.** If the helper is missing the build
  falls back to OpenVR *so the game still launches*. A mod that makes the game unlaunchable when one
  of its parts is absent is worse than a mod that quietly runs flat.
- **It is a separate deliverable to install and to debug.** It has its own `openxr_loader.dll` beside
  it, its own working directory, and its own failure modes - budget for that, because "did the helper
  start" becomes a question you will ask often.

### The same technique, built for a completely different reason {#substitute-runtime-bitness}

The four above wrote a runtime to remove the *headset* from the loop. BioShock-Remastered-VR (BioVRDev)
wrote one to remove a *bitness* limitation, and that second payoff is worth knowing before you decide the
technique is only a testing luxury. `[SOURCE]`

The problem is one a lot of flat-to-VR targets have: **SteamVR's own OpenXR runtime does not support
32-bit applications**, and a large share of the games worth porting are 32-bit. That locks Lighthouse
headsets - Index, Vive, Bigscreen Beyond, Varjo - out of any 32-bit OpenXR mod, no matter how correct the
mod is. OpenVR *does* still ship a 32-bit build. So they wrote a DLL that presents the OpenXR surface the
mod imports and implements it over OpenVR:

> This DLL replaces `openxr_loader.dll` next to `BioshockHD.exe`. It implements the exact OpenXR API
> surface `BioshockVR.dll` imports, backed by OpenVR (SteamVR), which -- unlike SteamVR's OpenXR runtime
> -- fully supports 32-bit applications.

**The mod itself did not change.** It still speaks OpenXR to a file called `openxr_loader.dll`; which
file that is becomes an install-time choice, and their setup script renames the chosen loader into place.
That is the architectural benefit of having written to a runtime boundary rather than to a vendor SDK:
the boundary is a swap point you did not have to plan for.

Two traps in the implementation, both of which cost real time:

- **The two calling conventions in `openvr_api.dll` are different.** The module-level entry points
  (`VR_InitInternal2`, `VR_GetGenericInterface`, ...) are `__cdecl`; only the methods reached through the
  returned FnTable are `__stdcall`. Declaring them uniformly *"imbalances the x86 stack on the first call
  -- it crashed the game on startup before this was fixed."* On x86 a convention mismatch is a crash, not
  a warning.
- **The two compositor models do not line up.** An OpenXR projection layer carries an arbitrary per-view
  FOV and pose; OpenVR's `Submit()` carries neither. So `xrEndFrame` cannot forward - it has to
  **re-composite**, drawing each layer as a textured quad into a per-eye target built from the real HMD
  frustum (`GetProjectionRaw`), then submitting those. Their note on why that is not a compromise is the
  useful part: a projection layer becomes *a quad at 50 m*, and at that distance **a planar homography is
  indistinguishable from ideal rotational reprojection**. Translating between two compositors is a
  geometry problem with a defensible answer, not a fudge.

Coordinates were the easy part: OpenXR and OpenVR share conventions (right-handed, +y up, -z forward), so
poses carried over with no axis surgery. `LOCAL` space was emulated by latching the first valid HMD pose
(yaw and position) as the origin.

### If you build one: the parts that are not obvious {#substitute-runtime-build}

BioShock-Trilogy-VR ships its simulator's source, so the shape is measurable rather than guessed:
**5,296 lines of C++ across 11 files**, plus a declarative scenario DSL. Their architecture note puts
the *core* surface at 39 entry points; the shipped implementation names about **65**, once
enumerations, action queries and the debug-utils extension are counted. Budget for the larger number.
`[SOURCE]`

**A runtime has exactly one export.** Everything else is reached through the function-pointer table you
hand back during negotiation — so `xrGetInstanceProcAddr` is your dispatcher, not an export. And the one
export has a trap that costs a day:

```
; XRAPI_CALL is __stdcall, so on Win32 a plain __declspec(dllexport) would
; publish it as _xrNegotiateLoaderRuntimeInterface@8 and the loader would
; report "failed to find negotiate function". A .def file pins the exact name.
```

The loader looks the symbol up **undecorated**. On 32-bit builds `__stdcall` decoration silently renames
it, the loader finds nothing, and the error message points at your runtime being absent rather than
misnamed.

**Negotiation validates in both directions.** Check the loader's struct type, version *and* size; check
your own request struct the same way; then confirm the loader's advertised interface and API windows
actually contain the versions you implement, and fail the whole negotiation if not:

```cpp
const uint32_t iface = XR_CURRENT_LOADER_RUNTIME_VERSION;
const XrVersion api  = XR_MAKE_VERSION(1, 0, 34);
if (loaderInfo->minInterfaceVersion > iface || loaderInfo->maxInterfaceVersion < iface ||
    loaderInfo->minApiVersion       > api   || loaderInfo->maxApiVersion       < api)
    return XR_ERROR_INITIALIZATION_FAILED;

runtimeRequest->runtimeInterfaceVersion = iface;
runtimeRequest->runtimeApiVersion       = api;
runtimeRequest->getInstanceProcAddr     = my_GetInstanceProcAddr;
```

Log the loader's advertised window on every negotiation. Their comment explains why: it makes a future
SDK bump **visible in one line instead of as a mysterious load failure.**

#### Assume nothing about which thread calls you

This is the constraint that shapes the whole implementation, and it is a property of real applications
rather than of the specification:

```text
xrWaitFrame   the app's dedicated pace thread - or its present thread, if pacing is off
xrBeginFrame  always the present thread, possibly long after its matching wait
xrEndFrame    the present thread, sometimes on the NEXT present,
              sometimes never, for a frame the app deliberately holds open
```

So **nothing may assume same-thread ordering, and no lock may be held across a block.** A runtime that
quietly assumes Wait/Begin/End arrive in order on one thread will work against a simple test app and
deadlock against a real mod.

#### One invariant above all others

> **No wait in the simulator is ever unbounded.**

That single rule is what makes an interactive step mode safe: an agent that walks away mid-step gates XR
submission only, and the game keeps running. It is also the rule that keeps your instrument from becoming
the hang it was built to diagnose — the same reasoning as
[a diagnostic on the present path getting a hard rate limit](06-debugging-methodology.md#instrument-honesty).

#### Waking and aborting are different things

Their sharpest recorded bug is one you would otherwise ship. An abort flag used to break an in-flight
wait was not scoped to the session that set it:

```text
xrWaitFrame returns SESSION_LOST -> the app tears the session down
  -> teardown sets the abort again -> the NEXT session dies at birth
  -> forever
```

**Scope an abort to one session and clear it at session creation**, and keep a plain wake (notify
everything, decide nothing) as a separate operation. A flag that means "stop waiting" and a flag that
means "the session is going away" look identical until one of them leaks.

#### Make scenarios data, not code

Their tests are `.xrs` scripts the simulator interprets, which keeps a new test to a few lines and lets
non-obvious assertions live next to the thing they assert:

```text
# stereo.xrs - stereo must produce two DIFFERENT eye images.
# Standing-still noise is ~0.4 mean; identical eyes read at the noise floor,
# real stereo reads well above it.
reset
@mod vrstereo on
@frames 60
@assert projectionViews eq 2
@shot stereo_on
```

Note the header carries the **noise floor** for the comparison it sets up, so a reader can tell a pass
from a coincidence — [A5](a5-flat-harness-stats.md)'s discipline applied to a headless VR test.

### Two more instances, one week, and they fail in opposite directions {#substitute-two-faults}

The substitute is not simply "weaker". It can be **more permissive** than production *and*
independently **broken** where production is fine, and the same week produced one of each. `[LIVE]`

**More permissive — SoF-VR.** Their probe asked for `XR_CURRENT_API_VERSION`. Virtual Desktop is a
**1.0** runtime and refuses a 1.1 instance; xr-sim accepted it and hid the fault for a session. Their
rule, adopted from the failure: **ask for 1.0, not `XR_CURRENT_API_VERSION`** — and, more usefully,
*"xr-sim green is not a pass."*

**Broken where production is not — SOMAVR.** The shared xr-sim assigns `XR_FALSE` to
`XrActionStateBoolean::changedSinceLastSync` **unconditionally**, so a menu edge never fires: the
control channel acknowledged `btn menu down/up` and the client still reported `menu-edge: no`. The
tell is that **SOMAVR's own vendored copy passed the identical 600-frame client** — two builds of the
same instrument disagreeing is the cheapest possible signal that the instrument, not the mod, is the
variable.

Both point the same way: **pin and record the substitute's identity the way you pin the target's.**
SOMAVR names the commit of both tools in its result (`xr-sim 9155410`, `xr-tape 52d3fac`), which is
what makes "our vendored copy passes and the shared one does not" a finding rather than a mystery.
See [TEST-022](pattern-catalog.md#test-022).

## Every toggle that starts a subsystem must be able to stop it {#symmetric-toggle}

Their `vrcam on` started VR; `vrcam off` only cleared the camera mode. Once an OpenXR session was
running, **nothing in the command surface could stop the game being paced by it** - and with the session
not `FOCUSED`, the runtime paces its not-visible cadence of roughly 10 Hz, which the game inherits and
which reads to a user as a hang. `[SOURCE]`

Audit every command, config key and hotkey that *starts* something for the symmetric stop. See
[XR-004](pattern-catalog.md#xr-004).

Their own correction on the neighbouring bug is worth copying as a habit: moving `xrWaitFrame` off the
present thread stopped an unbounded wait from wedging the game, and that held - but it **did not** stop
the frame handoff pacing the game thread to the runtime's cadence. They recorded it as *open* rather
than closed. **"Not blocked" is not "not harmed."**

## 32-bit targets: a 64-bit OpenXR registration proves nothing

If your game is 32-bit, the OpenXR loader needs a **32-bit runtime manifest**, registered under
`HKLM\SOFTWARE\WOW6432Node\Khronos\OpenXR\1`. A working 64-bit registration does not imply one
exists.

**Two independent projects were shaped by this.** FEAR VR's entire two-process architecture (a 64-bit
host talking to the 32-bit game over shared memory) exists because that key was absent on the
development machine — SteamVR supplied only `steamxr_win64.json`. CoD4 VR reports both registry views
independently and **blocks an OpenXR-only launch** when the 32-bit manifest is missing or its file is
absent on disk.

Check for it in your first hour on a 32-bit target. It decides whether you need the two-process split in
[17](17-teardown-fc2vr-native-stereo.md) or can bind OpenXR in-process.

Note also FEAR VR's honest addendum: Virtual Desktop *does* register a 32-bit runtime
(`virtualdesktop-openxr-32.json`), so the premise later stopped being universally true — and they kept
the two-process design anyway, because it is runtime-independent and keeps a modern OpenXR loader out of
an ABI-sensitive VC7.1 process. **A decision can outlive the reason that produced it; record both.**

## Present the render at a smaller angular size to trade FOV for density

A quality knob worth knowing, because it costs nothing on the CPU and is not obvious: present the
**same rendered resolution over a smaller angular area** of the headset view.

(*Witcher 3 VR calls it Presentation Size. `1.00` fills the usable view; lower values zoom the scene out
and raise visible pixel density, with black bands gradually appearing at the edges. Their guidance:
choose the lowest value whose borders are still invisible for your headset and face fit — `0.85` is a
good starting point on Quest 3, where the borders are practically invisible unless the headset sits very
close to the lenses.*)

It is the inverse of supersampling: instead of rendering more pixels for the same angle, show the same
pixels over less angle. For a seated or cinematic experience that is often the better trade, and unlike
render scale it does not move the GPU cost at all.

## Resolution, aspect, and display-mode compatibility

The feared "resolution port" mostly doesn't exist if you read sizes semantically — but two real coupling
classes will bite, and the display mode matters for VR pacing.

- **The two coupling classes.** (*SS2VR's whole audit found only these:*) a config pair storing a
  hardcoded **reference resolution** that feeds aim→screen projection, and **pixel calibration offsets**
  silently divided by the *live* size. Fix the first with a `0 = AUTO` sentinel meaning "live backbuffer
  size" (and resolve it at every read site — see [07](07-engine-integration-safety.md)); fix the second
  by storing the reference resolution *alongside* the offsets and applying them as a fixed UV fraction
  (`offset / reference`), which is bit-identical at the calibration resolution and keeps its meaning
  elsewhere.
- **A flat-aim model must know the game's aspect-scaling mode.** A `halfTanH = halfTanV × aspect`
  reconstruction assumes hor+ (fixed vertical FoV, horizontal widens). If the game letterboxes or goes
  ver- at ultrawide, horizontal aim compresses and you recalibrate one scale number. UI slices measured
  as static UV fractions on 16:9 break at a new aspect; pieces derived from the engine's *live* rect
  tables are immune.
- **Match refresh and prefer borderless.** Exclusive fullscreen paces to the *mode's* refresh, borderless
  to the desktop's — either must be 90 Hz for VR. With swapchains created once from the first scene
  texture (no `ResizeBuffers`/device-loss handling), exclusive-fullscreen alt-tab churns the swapchain
  and mid-session resolution changes are unsupported by design; use borderless and restart-on-change.
- **Scale the game's internal raster, never the XR swapchain.** The tempting way to add a performance
  slider is to shrink the OpenXR swapchain or the submitted `imageRect` — don't. Keep the projection
  full-sized and scale the *engine's* internal render resolution, then let the existing normalized eye
  blit expand the complete source eye into the full-size projection; that preserves the lens frame and
  aspect. (*HaloVR scales Halo's internal raster by preset and rounds to even dimensions, leaving the
  runtime-recommended stereo-array swapchain and `imageRect` untouched.*)
- **Resolve preset tiers identically in every consumer.** If the launcher, the config parser and the
  in-game menu each map a raw value to a preset, they must use the *same* boundaries or the UI will
  disagree with what actually rendered — the same failure shape as the AUTO-sentinel trap in
  [07](07-engine-integration-safety.md).
- **Third-party upscalers can be incompatible with your presentation.** (*HaloVR: enabling OpenXR
  Toolkit FSR produced tiled/overlapping stereo regions rather than an intact softer eye — consistent
  with an incompatibility around stereo-array presentation, not ordinary low-resolution blur.*) Ship
  your own internal-resolution control and treat external upscalers as outside the supported path.
- **Temporal post-processing reads as stereo echo.** Motion blur, TAA and similar accumulate across
  frames that, in VR, belong to *different eyes or different poses*. HaloVR disables motion blur by
  default for exactly this reason — a good default on any alternate-eye or reprojected pipeline
  ([10](10-graphics-apis.md)).

## Double-encoded gamma is what "first pixels" usually look like {#first-pixels-gamma}

The section below states the rule - do not apply gamma twice. This is what breaking it looks like the
first time a game's own pixels reach a headset, and how to settle it with a number instead of an
argument. **Two projects hit this at the same milestone.** `[LIVE]`

**The setup that causes it.** The game writes **already sRGB-encoded bytes** into an `_UNORM` surface -
that is simply what it would have presented. The XR swapchain's preferred format is `..._UNORM_SRGB`, so
the hardware encodes **on write**. Pass the bytes straight through and they are encoded a second time:
the classic milky, washed-out picture.

**The copy is legal, which is why this is easy to miss.** `R8G8B8A8_UNORM` and `R8G8B8A8_UNORM_SRGB`
share the `R8G8B8A8_TYPELESS` family, so `CopySubresourceRegion` between them succeeds and nothing warns.
[The format you name in the view is the gamma decision](#typeless-swapchain) - the copy has no opinion.

### Settle it with two hypotheses and one number

Do not judge this by eye, and do not argue about it. Clear to a known colour and read back the reported
luma; the two candidate encodings are far apart:

| Clear colour | If bytes are taken as written | If linear→sRGB encoded |
|---|--:|--:|
| `(0.85, 0.15, 0.15)` | **91.5** | **145.8** |

One project measured **146.0** and had its answer in a single frame. This is
[turn the visual bug into a number](06-debugging-methodology.md#quantify-the-artifact) applied to the
cheapest possible case: the hypotheses differ by 60%, so no precision is required.

### Two fixes, and the reason to prefer the explicit one

- **An `_SRGB` view** lets the hardware do the conversion once - correct, and free.
- **The exact piecewise sRGB→linear curve in the blit shader**, so the round trip is neutral. One
  project chose this deliberately because the view route needed a format they could not get on that
  path. It is more code and it is auditable.

**CONFIRMED on production hardware, 2026-09-02.** The substitute and VirtualDesktopXR on a Quest 3
**double-encode identically** - swapchain created as `format=28` (`R8G8B8A8_UNORM`) with
`colour_conversion=no`, the game presenting already-encoded bytes, the compositor encoding again.
Naming the `_SRGB` variant (`format=29`) fixed it and a wearer confirmed correct gamma immediately. So
this is a property of the *format choice*, not of one runtime. `[HEADSET]`

**The cheapest fix is a format-preference change, not a shader.** Enumerate
`xrEnumerateSwapchainFormats` and prefer an `_SRGB` variant: the copy remains a bit copy, and only the
tag saying how to interpret the bytes changes.

**A selection-order trap that guarantees the bug.** One project's chooser preferred an **exact match**
to the source format before considering the sRGB variant - a reasonable-looking rule, and precisely the
wrong answer when the source holds already-encoded bytes. Their sRGB branch existed and simply never
ran. **Rank the sRGB variant above the exact match** when the source is a presented backbuffer.

## Tonemapping and gamma

Older games often render into an HDR scene target and later composite/tonemap into an LDR
backbuffer. Copying HDR directly into an 8-bit XR swapchain produces incorrect brightness.

- Identify whether the private source is HDR scene-linear or final LDR.
- Define the mapping explicitly: exposure/tonemap in the blit shader, then use an sRGB target
  view when appropriate so hardware performs the linear-to-sRGB conversion once.
- Do not apply gamma both in the shader and through an sRGB RTV.
- Log source format, destination format, RTV interpretation, and exposure.

## Diagnostics that work inside a headset

RenderDoc is invaluable but may destabilize old games or conflict with an OpenXR runtime. Build
an inspection route that does not depend on a successful VR capture:

- hotkey-triggered final-eye color dumps
- private-eye color dumps
- private-eye depth visualization/dumps
- synchronized left/right filenames with frame, eye, and sequence
- short attribution windows around the same frame
- mono/stereo compare hotkey
- per-view/per-target isolation hotkeys

GPU readbacks stall. Keep dump bursts short and treat artifacts that appear only during a dump
as capture pressure until proven otherwise.

Log on transitions and periodic heartbeats, not every draw forever. Detailed per-draw logging
can turn a playable mod into a single-digit-framerate test and can itself change timing. Clear
or rotate the log at process start so one test produces one bounded evidence set.

## Performance accounting

A naive path may render the world three times: original desktop + private left + private right.
That cost is real even before OpenXR composition.

- Count source draws, private left/right draws, skipped draws, copies, and source age per frame.
- Correlate visual effects with draw-count jumps; a direction-dependent increase can reveal a
  secondary render view or reflection pass.
- Do classification before expensive cbuffer/SRV inspection and short-circuit rejected views
  early.
- Disable discovery probes once their question is answered.
- Optimize only after ownership is correct. A fast mixture of two camera views is still wrong.
- Treat “two eye renders plus a cheap desktop copy” as an architecture step, not a D3D11-specific
  hunch: KSA_XR independently reached the same first-working desktop-plus-two-eyes shape on Vulkan and
  also names the third complete frame as knowingly inefficient. Scrap Mechanic demonstrates the D3D11
  completion: bind the finished left-eye SRV and desktop backbuffer RTV, then `Draw(3, 0)` with an
  aspect-crop constant and no vertex buffer ([10](10-graphics-apis.md#vulkan-three-frame-proof)).
- Separate a **performance** win from a **coherence** win in your own head before you start. (*BioshockVR:
  hook + OpenXR overhead was `~0.85–1.63 ms`; the game plus the duplicated per-eye world replay was
  `~15–28 ms` — the real cost. Eliminating the redundant "third" desktop world render is worth doing,
  but it is expected to give **zero** visual-coherence improvement — it's purely a frame-time win.*)
  Don't let a perf refactor masquerade as a fix for an artifact.
- Phase timers built from `QueryPerformanceCounter` around submit/present are **CPU wall time**
  (they include driver and compositor pacing), not GPU cost. For real GPU stage cost use non-blocking
  timestamp queries; never present CPU submit time as GPU time.

## Common signatures and likely causes

| Symptom | First suspects |
| --- | --- |
| Different solid color in each eye | XR eye routing works; private source is missing/stale |
| Same flat image in both eyes | mono bridge, stereo transform not applied, or viewmodel/UI lane |
| Entire image offset/divergent | asymmetric FoV center ignored or eye sign/convention wrong |
| Near and far shift equally | clip-space/image shift, not a view-space eye translation |
| Geometry present in only one eye | depth mismatch, clip-plane companion, culling, or missing lane |
| Lighting black on opposite sides per eye | mono screen-space mask sampled with per-eye coordinates |
| City/sky/reflection shell follows camera | multiple render views merged or wrong vista/sky ownership |
| HMD freezes while desktop continues | stale eye cache or OpenXR submission/feed stopped |
| Bright/washed-out headset image | HDR/LDR or linear/sRGB conversion mismatch |
| Severe slowdown only in certain directions | reflection/portal/subview replay or massive overdraw |
| Capture hotkey causes temporary corruption | synchronous GPU readback pressure/state restoration |

## Definition of a real native-stereo milestone

Do not call the renderer "native stereo" merely because both eyes receive different images.
A useful milestone requires:

- distinct per-eye world geometry from one logical game frame
- physical IPD-scale view translation and asymmetric runtime projection
- coherent depth and projection companion constants
- one main render view per eye, with auxiliary views explicitly routed
- valid OpenXR pose/FoV submission with fresh source tracking
- original desktop path preserved or deliberately replaced
- no device removal/crash under sustained motion

Full 6DoF additionally requires engine camera/culling ownership so head translation reveals
new geometry instead of only moving already-rendered content.
