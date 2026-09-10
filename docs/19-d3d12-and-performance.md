# D3D12 & Performance — resource lifetimes, queues, and measured budgets

D3D12 makes ownership explicit, but an injected mod does not automatically own
the engine’s frame graph. This chapter separates what the API permits from what
a particular recorded frame can safely repeat, then establishes a performance
method that works on desktop and standalone headsets.

Evidence here comes from Cyberpunk VR’s D3D12 pass/replay investigations
`[SOURCE]` and Shock2Quest’s Quest 3 mission baseline `[HEADSET]`.

## A closed command list is not a pure function {#d3d12-replay-context}

D3D12 permits a closed command list to be submitted more than once. That
`[SPEC]` fact answers only whether the call is legal. It does not establish
that the *work encoded by the engine* is repeatable.

The execution contract includes:

- resource state at first use and after last use;
- transition, UAV and aliasing barriers;
- descriptor heaps and descriptors captured while recording;
- placed/transient resource lifetime;
- UAV appends, atomics, counters and indirect-argument writes;
- fences, queue waits and async-compute consumers;
- upload-heap data read at execution time;
- temporal and engine-side state assumed by the pass.

Treat command-list replay like calling an unknown engine function twice: begin
with an idempotence probe, bound the experiment, and record what the second
execution is allowed to overwrite.

## Start with a pass and queue census

Cyberpunk’s RT-off Nsight/engine-hook census found `[SOURCE]`:

- 72–80 view-dependent passes per scene frame;
- 35–40 distinct render-target IDs;
- four queues;
- roughly 133,000 `ExecuteCommandLists` calls per diagnostic snapshot, with
  about 94.7% on the present queue;
- only a minority of work plausibly shareable between eyes.

Those numbers changed the architecture decision. “Clone the scene target” was
not one target; it was a frame-graph routing problem across dozens of
intermediates and four queues. Likewise, sharing shadows offered an estimated
6–12% frame benefit based on command-list counts—not GPU time—so it could not
justify making a non-reentrant frame graph stereo-aware without a GPU trace.

Build the census before writing replay code:

| Field | Why it matters |
|---|---|
| Queue identity | A present-queue duplicate may feed an async consumer |
| Command-list ordinal/signature | Lets experiments bisect a stable class |
| List count and type | Distinguishes orchestration from scene batches |
| Transition/UAV/aliasing counts | Predicts state and lifetime hazards |
| ExecuteIndirect usage | Flags GPU-produced inputs, but absence is not safety |
| Render/depth target IDs | Estimates redirection/clone surface |
| Fence Signal/Wait topology | Exposes delayed failure paths |
| Named pass / marker | Makes findings transferable beyond ordinals |

Ordinals are excellent probes and poor shipping identities. Product code needs
a content signature, pass marker, call ancestry or resource relationship.

## Resource-state compensation is necessary, not sufficient

Naively resubmitting Cyberpunk scene batches produced variable GPU hangs.
Restoring each tracked subresource from the first execution’s ending state to
its starting state extended survival substantially `[LIVE]`:

1. hook command-list `Reset` to establish recording generation;
2. record transition barriers;
3. calculate net start/end state per resource/subresource;
4. emit a compensation list before duplication;
5. reject untracked, mixed-granularity and initially aliased lists.

This isolated a real defect family, but did not make the full scene replayable.
State equivalence does not restore UAV data, ownership of aliased memory or the
cross-queue schedule.

### Never trust process responsiveness as GPU health

The Cyberpunk process could remain “Responding” while the present queue stopped
advancing. The useful heartbeat was a monotonically advancing fence/log marker.

For a replay probe:

- place a fence marker after each original and duplicate batch;
- keep a watchdog on a thread independent of Present;
- map issued fence values to frame, queue, ordinal, original/duplicate and
  recorded hazards;
- declare health as completed-fence/log growth, not window responsiveness.

## Cross-queue dependencies make the failure delayed {#d3d12-cross-queue}

A duplicated batch without `ExecuteIndirect` still poisoned a later async
consumer. The observed signature was `[LIVE]`:

1. duplicate producer writes a UAV or shared transient input;
2. async compute consumes the unexpected state/data;
3. async queue never signals;
4. present queue blocks at a later `Wait`;
5. the watchdog reports an *original* batch as stuck.

The last visible command is therefore not necessarily the corrupting command.
Bisect duplicates and retain causal history across at least one frame.

“Skip every list containing `ExecuteIndirect`” is not a safety proof. A small
feeder may write arguments or data consumed indirectly without issuing the
indirect draw itself.

## Transient aliasing can make replay impossible {#d3d12-transient-aliasing}

Cyberpunk’s decisive split was between batches on dedicated resources and
scene batches using aliased frame-graph memory `[LIVE]`:

- non-transient prep/begin/end batches could repeat for long runs;
- every meaningful scene group crossed aliasing barriers;
- duplicate-after-original raced async readers;
- duplicate-before-original still failed;
- replay after Present caused immediate device removal because transient
  memory/descriptors no longer described the recorded resources.

This is not fixed by adding more transition barriers. An aliasing barrier says
the heap region has a *different resource owner*. Once ownership changes, the
old command list’s semantic environment no longer exists.

The remaining theoretical choices are expensive:

- clone the frame graph’s transient resources into dedicated memory and record
  work against them;
- make the engine record a true second view;
- inject stereo into the geometry/shader path so the one engine pass produces
  both eyes;
- synthesize the second eye by depth/geometry reprojection.

The Cyberpunk project subsequently proved shader-stage control by intercepting
graphics PSO creation, reflecting real scene vertex outputs, compiling a
matching pass-through geometry shader, and inserting it into over 1,500
G-buffer PSOs with safe fallback `[LIVE]`. That did not by itself solve the
screen-space, transparency, seam, TAA/DLSS and full-pass-coverage problems. It
proved a different ownership route after replay was falsified.

## Descriptors are part of recording-time ownership

Shader-visible CBV/SRV/UAV contents can be read during execution, but RTV/DSV
bindings are encoded into the command list. Rewriting a descriptor after
recording is not a general way to redirect a recorded scene into a new
right-eye target.

Before choosing “patch constants then replay into another target”, prove:

1. which descriptors/addresses are captured at recording;
2. which data is dereferenced at execution;
3. whether target redirection requires re-recording;
4. whether the engine exposes geometry and PSO state needed to re-record.

## A performance result needs three ledgers

### 1. Budget ledger

Declare:

- headset refresh rate and frame interval;
- application target and acceptable reprojection policy;
- eye resolution/render scale;
- runtime and graphics mode;
- thermal/power state where relevant.

At 90 Hz, the interval is 11.11 ms. That does not mean an 11.0 ms average is
safe; synchronization variance, compositor work and spikes consume margin.

### 2. Stage ledger

Separate:

- game update/simulation;
- shared scene preparation;
- left/right CPU submission;
- swapchain acquire/wait/release;
- GPU execution;
- post-eye/finish work;
- OpenXR submit;
- compositor app time;
- memory.

An “eye time” that includes swapchain waiting is not pure rendering. Name the
measurement boundary before attributing a bottleneck.

### 3. Freshness ledger

Report:

- mean and minimum delivered FPS;
- stale/reprojected frames;
- torn frames where exposed;
- application-skipped render frames;
- focus/session validity;
- a visual capture proving the intended scene rendered.

The compositor can present at refresh rate while reusing an older application
frame. Average presentation FPS alone can certify a bad result.

### A rolling percentile and a lifetime counter have different denominators {#timing-population}

PreyVR's September 9 production-counter harness feeds 2,000 slow intervals followed
by 512 fast ones. The report correctly returns a 512-sample clean window alongside
2,000 lifetime overruns. Combining them into a whole-run miss rate is incorrect.
A second control produces 500 threshold overruns with no compositor present.
`frameMissed` was an interval-budget counter, not observed dropped displays.
`[SOURCE; LIVE harness]`

Retain frame IDs, start/end epochs, total and retained counts, actual collection
durations, configured budget and runtime period. Pair CPU/GPU samples by frame;
a ratio or subtraction of separate medians is not a measured budget decomposition.
Saved GPU work may reappear as runtime waiting, so unchanged paced cadence does
not establish that lower resolution saved nothing. Conversely it does not prove
a GPU bottleneck. Preserve that uncertainty until the discriminating timing run.
Evidence: `PreyVR/docs/RE-PERFORMANCE-HANDOVER-AUDIT-2026-09-09.md` and
`evidence/performance-handover-audit-2026-09-09/verification.txt`.

## Halving cadence: where the stall appears names the cause {#xr-frame-pacing}

A VR app that drops from the panel rate to exactly half it — 120 → 60, or 90 → 45 — is usually assumed
to have crossed a render budget. **Measure before believing that**, because the runtime has its own
reasons to halve you, and they present identically on a frame-rate counter.

Halo-MCC-VR captured a 120→60 flip in detail and the aggregate story was wrong. `[LIVE]`

**The aggregate correlation looked convincing and was refuted at the edges.** Their render window rose
from ~5 ms in a light scene to 9–12 ms while low cadence was active — an obvious budget story. But the
exact transition rows say otherwise:

> A measured **8.90 ms frame ran at 119 fps** and a **9.14 ms frame ran at 60 fps.** Exact edge rows show
> no render-window threshold and no consistent step at the flip. **The aggregate correlation is not
> evidence of a render-budget threshold.**

**Capture the transition rows, not the averages.** Their 570 deduplicated period-edge rows all carried an
identical per-frame work signature — same view-transaction count, same palette requests, same cache
hits/stores, zero cache-full events — which ruled out per-frame work as the trigger without needing a
single hypothesis about which work it might have been.

### The decisive signature was *which API call* absorbed the delay

```text
xrWaitFrame   returned packet already ready         ~0.007 ms   (not the stall)
xrBeginFrame  0.024 ms -> 1.495 -> 7.978 -> ~8-12 ms            (the stall)
              during recovery: ~12 ms -> 2.61 -> back to 0.024
```

Cadence delay appeared **synchronously inside `xrBeginFrame`, after `xrWaitFrame(N)` had already
completed.** That is diagnostic, because the OpenXR specification says runtimes **must not** perform
frame synchronisation or throttling in `xrBeginFrame`. `[SPEC]` A runtime doing it anyway is a strong
signal that the *application's* frame loop has left it nowhere else to do it.

**The rule: instrument each XR call separately and watch where time moves.** "The frame took longer" is
not a finding; "Begin went from 0.024 ms to 8 ms while Wait stayed at 0.007 ms" is.

### The fix is an ordering invariant, not a budget cut

The correction keeps one `xrWaitFrame` owner and changes *when* the render thread is released:

1. A **dedicated worker is the only `xrWaitFrame` caller** — never the game's render thread.
2. It publishes one immutable `Wait(N)` packet and parks on that exact sequence.
3. The render thread claims and validates the packet — session epoch, and no other Wait in flight.
4. **Immediately before `Begin(N)`, it releases the exact N permit.**
5. The worker publishes the `N+1` dispatch marker, and `xrWaitFrame(N+1)` is its next instruction.

The point of the ordering is that **`Wait(N+1)` is already pending when `Begin(N)` runs**, so the runtime
throttles in `xrWaitFrame` — where it is permitted and where blocking is harmless — instead of inside
`Begin`. The spec explicitly allows a subsequent `xrWaitFrame` before the preceding frame is begun; it
must block until that Begin, and must unblock independently of End. `[SPEC]`

Releasing the worker only *after* `xrBeginFrame` — the intuitive ordering — leaves no Wait pending while
the runtime enters Begin, which is exactly the condition that produced the halving.

See [PERF-003](pattern-catalog.md#perf-003).

### Keep an explicit "already excluded" list

Their document carries a **do not reopen without contradictory measurement** section: DWM composition,
desktop-mirror fit, SteamVR Motion Smoothing (verified off), `resolution_scale`, the eye blit
(`CopyResource`, sample count 1), `xrEndFrame` (measured 0.35–1.66 ms), per-frame TRACE logging, and
first-person palette capacity. A specific proposed trigger — a four-entry palette overflow — is recorded
as **did not occur, closed for this bug**.

That list is what stops a long investigation re-walking its own ground, and it is the
[closed-families discipline](08-project-process.md) applied inside a single bug.

### Report app cadence and panel rate as different numbers

`predictedDisplayPeriod` is **the cadence at which the runtime is asking this app to submit**. It is not
necessarily the physical panel period. `[SPEC]` Their UI calls it *app cadence* and reports the queried
panel rate separately.

Conflating them makes a runtime decision look like a hardware fact, and it hides exactly the halving
described above — the panel is still at 120 while you are being asked for 60.

### A fix that provably ran and did not help is a finding

From the same project's resolution/FSR track: a mod-owned resolve/upscale/AA/sharpen pass was built, and
its log **proved the pass active at `3786x2730 → 4164x4244`** — while the user reported the headset
remained stuck at approximately 60 FPS. `[HEADSET]`

The log proved the code ran. It did not prove the code helped, and those are different claims. The
series was **rejected and removed from the runtime rather than left dormant** — which is the right
disposal, because dormant rejected code reads as an option to a later reader.

## What the Quest 3 baseline teaches

Shock2Quest measured all 23 missions on Quest 3 at 1680×1760 per eye and 90 Hz,
using fresh processes, a three-second focused warmup and five-second samples
`[HEADSET]`.

The important lesson is not the exact table; it is how cautiously it is read:

- all missions reached `FOCUSED` and emitted complete telemetry;
- mean presentation stayed near 90 Hz;
- 22 missions still reported 1–15 stale frames;
- the worst one-second interval was 88 FPS;
- stationary spawns appeared inside budget but did not represent combat,
  effects-heavy rooms or thermal settling;
- four captures showed environment/void despite valid session telemetry, so
  those rows were rejected for visual/render-cost comparison.

Numeric telemetry can be valid while the workload is wrong. A device image is
part of performance evidence.

## With source access, foveation is yours to implement — and there are two routes {#source-side-foveation}

The mobile section below treats foveation as vendor territory, because on standalone hardware it is. With
engine source that changes completely, and The Dark Mod's VR fork is the worked example: one
`VRFoveatedRendering` class carrying **two independent implementations**, selected by what the hardware
supports. `[SOURCE]`

```cpp
class VRFoveatedRendering {
    void PrepareVariableRateShading( int eye );     // route 1: hardware VRS
    void DisableVariableRateShading();
    void DrawRadialDensityMaskToDepth( int eye );   // route 2: radial density mask
    void ReconstructImageFromRdm( int eye );
private:
    idImage      *variableRateShadingImage[2];      // one VRS lookup image PER EYE
    idImage      *rdmReconstructionImage;
    FrameBuffer  *rdmReconstructionFbo;
    GLSLProgram  *radialDensityMaskShader;
    GLSLProgram  *rdmReconstructShader;
};
```

**Route 1 — variable rate shading.** A per-eye lookup image tells the hardware to shade coarser toward
the periphery. Cheap and high quality where the GPU supports it, and note the image is **per eye**: the
lens centre is not the render-target centre, and it differs left to right.

**Route 2 — radial density mask.** Punch a radial pattern into depth so peripheral pixels are never
shaded, then **reconstruct** the missing ones from their neighbours in a second pass. It needs no VRS
support at all, which is why it exists alongside route 1 — but it costs you a reconstruction pass and a
shader, and its quality is a tunable rather than a given.

Their exposed tuning is a three-zone radial profile plus a reconstruction quality knob:
`vr_foveatedInnerRadius`, `vr_foveatedMidRadius`, `vr_foveatedOuterRadius`,
`vr_foveatedReconstructionQuality`, behind `vr_useFixedFoveatedRendering`.

### Two more per-eye savings the same fork exposes

- **`vr_useHiddenAreaMesh`** — the runtime tells you which pixels of each eye buffer the lens will never
  show. Masking them in the depth pass is close to free and removes real fragment work at the corners.
  Ask your runtime for the hidden-area mesh before optimising anything more elaborate.
- **`vr_useLightScissors`** — per-light scissor rectangles, computed per eye. On a stencil-shadow engine
  this is an existing flat optimisation that simply has to become eye-aware rather than being invented.

**The general point: an engine's existing per-view optimisations usually need to be made per-eye, not
replaced.** Look through the flat renderer for anything already scissored, masked or culled per view
before writing new VR-specific machinery.

## Mobile levers are optional extensions — negotiate every one {#mobile-extension-negotiation}

On standalone hardware the performance levers are **not part of core OpenXR**. They arrive as optional
extensions, they differ per vendor, and a runtime that does not advertise one will not fail politely if
you call into it anyway.

JKXR's pattern is the one to copy, and it is fail-closed at three separate levels: `[SOURCE]`

```c
const char* const optionalExtensionNames[] = {
    XR_EXT_PERFORMANCE_SETTINGS_EXTENSION_NAME,      // CPU/GPU perf level + thermal events
    XR_KHR_ANDROID_THREAD_SETTINGS_EXTENSION_NAME,   // tell the scheduler which TIDs matter
    XR_FB_DISPLAY_REFRESH_RATE_EXTENSION_NAME,       // enumerate and request panel rates
    XR_FB_COLOR_SPACE_EXTENSION_NAME,
    XR_PICO_CONFIGS_EXT_EXTENSION_NAME };            // vendor config: foveation, display rate

static qboolean openXrExtPerformanceSettings = qfalse;   // one flag per extension,
static qboolean openXrExtAndroidThreadSettings = qfalse; // set ONLY if the runtime advertised it
...
if (openXrExtPerformanceSettings) {                                   // 1. advertised?
    PFN_xrPerfSettingsSetPerformanceLevelEXT fn = NULL;
    XrResult r = xrGetInstanceProcAddr(instance, "xrPerfSettings…EXT", (PFN_xrVoidFunction*)&fn);
    if (XR_SUCCEEDED(r) && fn != NULL) {                              // 2. resolved AND non-null
        OXR(fn(session, XR_PERF_SETTINGS_DOMAIN_CPU_EXT, XR_PERF_SETTINGS_LEVEL_BOOST_EXT));
        OXR(fn(session, XR_PERF_SETTINGS_DOMAIN_GPU_EXT, XR_PERF_SETTINGS_LEVEL_BOOST_EXT));
    }                                                                 // 3. every call OXR-checked
}
```

**Three levers worth knowing, none of them core:**

- **`xrPerfSettingsSetPerformanceLevelEXT`** sets CPU and GPU performance levels **as separate domains**.
  A CPU-bound port and a GPU-bound port want different answers, and the API lets you say so.
- **`xrSetAndroidApplicationThreadKHR`** tells the runtime which thread IDs are
  `APPLICATION_MAIN` and `RENDERER_MAIN`, so the OS scheduler can prioritise them. Without it the
  scheduler is guessing, and on a thermally constrained device that guess costs frames.
- **`xrEnumerateDisplayRefreshRatesFB` / request** — the panel rate is a *list you query*, not a constant.

### Vendor-gate the calls, not just the extension

JKXR guards the thread-settings call with an extra check on the HMD identity: `[SOURCE]`

```c
if (openXrExtAndroidThreadSettings && TBXR_StringContainsNoCase(app->OpenXRHMD, "meta")) { … }
```

The extension being advertised is not the same as it behaving usefully on that vendor's runtime.
**When you have been burned by one vendor's implementation, gate on the vendor, and say so in the
condition** — this is a two-term guard that documents itself.

Note also that **foveation is vendor territory**: on Pico it arrives through
`XR_PICO_CONFIGS_EXT` as enum-indexed config slots (`FOVEATION_LEVEL`, `SET_DISPLAY_RATE`,
`FOVEATION_SUBSAMPLED_ENABLED`), not through a portable API. Any "enable foveation" line in your code is
per-vendor until proven otherwise.

### Thermal state arrives as an event, not a query

`XR_TYPE_EVENT_DATA_PERF_SETTINGS_EXT` is delivered through the ordinary
[event poll](09-d3d11-openxr-injection.md), carrying `subDomain`, `fromLevel` and `toLevel`.

**That is the thermal-throttling notification channel**, and it is the difference between "the device got
slower after twenty minutes and we do not know why" and a logged transition with a direction. On a
standalone target, log every one of these with a timestamp — a session that degrades at minute 18 and a
session that degrades at minute 3 are different bugs.

See [PERF-004](pattern-catalog.md#perf-004).

## Presentation scale is an FOV change, not a resolution change {#presentation-scale}

A subtle and valuable distinction from Witcher 3 VR, whose presentation policy is a pure predicate with
a comment explaining why: `[SOURCE]`

> AER+TAAU owns a completed, full-resolution per-eye source before final OpenXR presentation.
> **Presentation Size must therefore never resize its swapchain; it only changes the angular FOV used
> for the final submission.**

Once an upscaler has produced a finished eye image, "present it smaller" must **not** mean "render fewer
pixels" — the pixels already exist. It means submitting the same image against a **narrower per-eye
FOV**, so the fixed image covers less angular area and gains apparent density.

**Get this backwards and you either resize a swapchain the upscaler owns, or you silently drop the
upscaler's output.** Their policy therefore has an explicit *fixed-resolution route* predicate that fires
exactly when the upscaler owns the source:

```cpp
constexpr bool fixed_resolution_route_active(const FixedResolutionRouteInput& in) noexcept {
    return in.mode3_aer && in.native_asymmetric && in.taau_backend;
}
```

**Every rendering mode is a separate compatibility state.** Their final-remap predicate takes seven
inputs — mode, projection type, backend, gameplay-vs-cinema, freelook, pipeline readiness and the scale
itself — with a comment naming a specific hazard it exists to prevent: *"AER+TAAU also takes this route
at scale 1 so it cannot fall through to the legacy cover crop."* A mode matrix is not decoration; each
cell is a route that can be entered wrongly.

### A stale resolve must not move submission authority

Their TAAU policy is four lines and the comment is the finding: `[SOURCE]`

> A stale resolve **does not contain the pixels named by its old producer tag**: it copies the already
> valid private eye history instead. It therefore **must not change submitted-pair authority in either
> direction.**

```cpp
constexpr AuthorityDecision decide_authority(uint64_t previous_pair, uint64_t incoming_pair,
                                             bool replayed_as_stale) {
    return replayed_as_stale ? AuthorityDecision{previous_pair, true}
                             : AuthorityDecision{incoming_pair, false};
}
```

**A buffer carries a tag naming what it was supposed to contain, and after a stale replay that tag is a
lie.** Trusting it moves pair authority to a frame whose pixels came from somewhere else — which is the
[pair-latching rule](pattern-catalog.md#str-002) defeated by a label rather than by a missing eye.

The generalisation: **when a resource can be reused or replayed, its identity tag and its contents can
disagree, and the tag is the one you were about to trust.**

## Decide between FFR, multiview, resolution and CPU work

### Fixed foveated rendering

Prioritize when fragment share, overdraw, texture stalls, bandwidth or GPU load
dominates. Confirm runtime extensions and foveation-capable swapchain creation,
then compare off/low/medium/high with peripheral visual evidence.

### Multiview

Prioritize when duplicated CPU submission, state changes or vertex work
dominates. It requires texture-array swapchains/framebuffers,
multiview-capable shaders and explicit separation of shared scene preparation
from eye-dependent hands/HUD.

### Resolution/material reduction

Prioritize with fragment/bandwidth evidence. It is not a first response to high
game-update or synchronization time.

### CPU/game update

Prioritize when update time is high while GPU/compositor time has margin.
Inspect scripts, physics, AI/pathfinding, visibility and allocation counts.

## The biggest number in a VR-bridge profile is usually a wait you cannot remove {#blocking-wait-floor}

Psychonauts VR spent three sessions attributing a ~2x framerate regression to its readback chain, then
measured it. The result reverses the whole plan, and the shape recurs on every runtime. `[SOURCE]`

| Span | Measured | Verdict |
|---|--:|---|
| `GetRenderTargetData` (both eyes) | **0.003-0.015 ms** | negligible |
| `LockRect` + `memcpy` + `UpdateSurface`, per eye | **0.35-0.45 ms** | negligible |
| **`IVRCompositor::WaitGetPoses`** | **25-27 ms, every call** | the entire cost |

Their previous session's stated hypothesis - *"`GetRenderTargetData` is the likely culprit"* - was wrong
by three orders of magnitude, and the planned optimisations behind it (a GPU-side shared surface,
every-other-frame readback) *"would be optimizing a cost that isn't there."* **Instrument the candidate
before you design the fix**, because a readback chain is exactly the sort of thing that *sounds*
expensive.

**And the real cost is not yours to remove.** An A/B that skipped `WaitGetPoses` entirely restored full
baseline framerate - and broke **every** `Submit` with `VRCompositorError_DoNotHaveFocus` (error 101).
It is called once per frame, exactly as the documented usage pattern requires. Measured independent of
window OS focus, of window visibility, and of call ordering: a fixed floor imposed by the compositor
process.

That is what `WaitGetPoses` is *for* - it blocks until the compositor's running-start point, so the
number you are staring at is mostly the frame interval itself. **A blocking sync will dominate any
per-span profile of a VR bridge, and it is not a bug.** Record it as a floor, subtract it, and profile
what is left. The two textbook architecture fixes they implemented in the same session both measured
**~zero effect on framerate**, and they published that as a negative result rather than quietly keeping
the refactor.

### Pace the game to the runtime's request, and tag frames with the request they answer

[fear-vr's `pose_fallback`](#blocking-wait-floor) is this problem caught on the consumer side: a stale
image handed the current pose, which the compositor then believes and stops correcting. Condemned VR
prevents it on the **producer** side, and the mechanism is small. `[SOURCE]`

Their classic-D3D9 path reads completed staging copies back to the CPU and uploads them to D3D9Ex, so:

> Letting the game render freely can put **old completed images ahead of the current OpenXR request**,
> producing visible double images during fast head or controller motion.

The fix is to make the runtime's request the game's frame clock, once native stereo has begun:

1. a completed stereo pair **records the OpenXR request ID it was rendered for**;
2. if the next world render sees **the same request ID**, wait - bounded at **20 ms** - for a newer one;
3. during that bounded wait, service completed staging work and release output slots;
4. **duplicate request IDs are never captured again**, and if an output slot is still occupied the new
   image is **discarded rather than queued for stale delivery**;
5. a request already visible to the game renders immediately, with no extra pacing wait.

**The identity tag is what makes the rest possible.** Once a frame knows which request it answers, "is
this stale?" stops being a timing heuristic and becomes an equality test. Everything else follows:
duplicate suppression, the bounded wait, and the decision to drop rather than enqueue - which is
[STR-010](pattern-catalog.md#str-010) applied to a queue rather than to a single frame.

**Two boundaries worth copying.** The wait is **bounded**, so a runtime that stops issuing requests
stalls the game for 20 ms rather than forever. And **startup menus stay free-running** until the first
native stereo pair - pacing is switched on when there is something to pace, not at process start, which
avoids a class of bring-up hang that has nothing to do with the steady state. See
[PERF-007](pattern-catalog.md#perf-007).

### The wait time tells you whether you are slow or being held back

[The section above](#blocking-wait-floor) says the runtime's frame wait will dominate any per-span
profile. That same number is also the diagnostic that separates the two reasons a VR app runs at half
refresh. `[SOURCE]`

Singularity VR shipped a reprojection warning that fired on a run with reprojection **off**, reporting
`1.91x` and `1.99x`. It tested frame time against the display period and nothing else:

> **60 fps against 120 Hz is 2.00x by definition.** It would flag any app honestly running at half the
> refresh.

The discriminator was already being collected, and it is the wait:

| `xrWaitFrame` / `WaitGetPoses` | Meaning |
|---|---|
| **large** - a big share of the frame is idle | the runtime is **holding you back**; you finish early and block |
| **near zero** - `0.1-0.9 ms` of a 16 ms frame | you are **genuinely busy**; you arrive late and the wait returns at once |

Theirs measured `0.1-0.9 ms` of a 16 ms frame: honestly slow, not reprojecting.

**An app that is merely slow never idles.** That one sentence turns the frame wait from a number you
subtract into a number you read - and it is the difference between "buy back GPU time" and "find out why
the runtime is pacing us", which are opposite investigations.

**Ratio-against-refresh is not a reprojection test.** Any warning built on frame time over display
period will fire on every honest half-rate app, and a warning that cries wolf gets muted - which is how
a real one goes unnoticed later.

## DLSS in VR is a registration problem, not an upscaling one {#dlss-in-vr}

[Chapter 14](14-render-pass-hazard-atlas.md#temporal-upscalers-need-per-eye-history-and-a-fail-closed-fallback)
records temporal upscalers as a hazard. This is the other half: **DLSS demonstrably works in VR** - five
shipping mods use it - and when it looks bad the cause is almost always the inputs you declare, not the
upscaler. theHunter VR's research sweep read the Programming Guide (v310.5.0) in full alongside four VR
mod ecosystems and one same-engine flat comparable. `[SOURCE]`

**Their verdict is the model for diagnosing this**, because it starts by finding a comparable that
works:

> Our DLSS is not failing because the engine lacks vegetation motion vectors - **Luma ships DLSS on this
> exact engine with zero foliage/skinned MVs and calls the result "fine (a bit smudged)"**.

If a comparable integration on the same engine, missing the same data, looks acceptable, then the
missing data is not your problem. Theirs turned out to be three registration faults:

| Fault | Why it matters |
|---|---|
| **Zero jitter reported while the frame is jittered ±0.25 px** | direct spec violation (guide 3.7.3 rule 3) - *"misreported jitter is worse than none"* |
| **Motion vectors contain that jitter**, neither cancelled nor declared | the `MVJittered` / `JitterCancellation` flag exists precisely for this |
| **No exposure supplied for an HDR input** | guide 3.9 lists *"ghosting of moving objects"* as symptom #1 of exactly that |

Plus two cheap ones: the **`DepthInverted` flag** (a reversed-Z engine with the wrong flag corrupts
DLSS's closest-depth MV dilation, so **moving edges** break), and the **render preset**.

**Jitter is a hard requirement, not a quality setting**: at least 16 phases and preferably 32, with
`phases = 8 x (target/render)^2`, which still leaves a **minimum of 8 phases for DLAA** at native
resolution.

### What the VR mods actually teach

- **Native stereo is the friendly mode.** UEVR - both eyes every frame - reports *"DLSS/FSR2 usually work
  completely fine with no ghosting"*, and names the culprit: **alternate-eye rendering is what fights
  temporal accumulators.** An AFR design needs same-eye residual reconstruction that a native-stereo one
  does not.
- **Keep both eyes on the same jitter phase each frame.** Skyrim Community Shaders found per-eye
  stochastic effects converging differently per eye produce **binocular shimmer** - the
  [shared-value rule](14-render-pass-hazard-atlas.md#shipped-vr-hazards) applied to a sequence rather
  than a scalar.
- **Clear the motion-vector texture after every evaluate.** PureDark copies an always-empty texture in,
  so a skipped pass feeds **zeros rather than stale vectors** - a fail-closed default for the one input
  whose staleness is invisible.
- **When one eye misbehaves, audit that eye's inputs.** MSFS's right-eye-only shimmer root-caused to a
  **broken right-eye velocity buffer**. An asymmetric artifact points at an asymmetric input, not at the
  upscaler.
- **Per-eye evaluation works either way**: PureDark uses sub-rects on a double-wide target, theHunter
  uses separate textures, and both are fine. The requirement is *separate history*, not a particular
  layout.
- **Anything that blurs the input must be off** - TAA, DoF, FXAA, motion blur, grain, chromatic
  aberration. Every VR DLSS config in the survey force-disables them.

**And presets are a real lever, not a placebo.** MSFS's high-contrast VR smear - the same symptom class -
was largely fixed by preset choice alone: community fix DLL 310.1 with **preset J**, official fix DLSS
4.5 **preset M ("Ghost Killer")**, trained in linear space for exactly that. DCS VR also forces J; Luke
Ross's R.E.A.L. standing config is 310.5.x with preset L or M, and the transformer model *"fixed"* their
ghosting **even under AER**.

**The honest ceiling**, from fholger, on why vrperfkit never shipped DLSS: *"needs deep engine
integration."* **Input hygiene is the work, and there is no generic shortcut** - which is why a
drop-in upscaler injector and a DLSS integration are different projects.

### Ship the flags as live toggles

OptiScaler's design is worth copying wholesale: **no auto-detection anywhere**, just per-flag manual
overrides. Its flag list doubles as the checklist of common integration bugs - `DepthInverted`,
`AutoExposure`, `HDR`, `JitterCancellation`, `DisplayResolution` (high-res MVs), `DisableReactiveMask`,
plus the preset hint before feature creation. Expose all of them live, and **any future misdiagnosis is
a toggle rather than a build** ([TEST-010](pattern-catalog.md#test-010) applied to a shipped feature).
Note also that its missing-exposure fallback is not a fake texture - it **flips to auto-exposure**, which
is a real behaviour rather than a plausible-looking input.

### Three driver calls that do not belong in the frame, and what they cost

[PERF-006](pattern-catalog.md#perf-006) says separate the compositor's floor from your own cost. fear-vr
did exactly that on a working bridge and found three per-frame calls that were pure waste, with
before-and-after numbers. `[SOURCE]`

Before: `copy_avg_us` **310-440** with spikes to **3772**, and the XR display rate collapsing to **72.8**
instead of 90 in some windows - *"the short stutters where the world visibly lagged."*

| Call | Why it was wrong | Fix |
|---|---|---|
| `OpenSharedResource`, **per eye per game frame** | *"a kernel call with a driver lock, not a pointer copy"* | there are exactly six slots (three per eye) - open each **once** and memoise by handle; if the producer rotates slots, the same slot carries a new handle and the comparison reopens by itself |
| `CreateRenderTargetView`, **per eye per XR image** | the swapchain image count is fixed once enumerated | create one view per image, and **release the views before the images** - a view holds a reference to the texture |
| `Flush`, **per eye** | only submission before `xrEndFrame` matters | once per frame |

After, over 102 windows and 30,600 frames: `copy_avg_us` **82-106**, `copy_max_us` **612**, and
`xr_fps` **never below 89.4**.

**And two hypotheses were recorded as wrong so nobody re-tests them**: making the logger asynchronous
moved long frames per window from `0.89` to `0.80` - inside the noise - and `Flush` itself measured
`272 us`. *"Only the per-section measurement decided it."*

### Decompose the frame budget so "my work" is actually your work

The instrumentation is the reusable part, and the definition is the whole trick:

> `frame_cpu_max_us` is the **own** work: everything between `xrBeginFrame` and `xrEndFrame`, **minus
> the waits the compositor determines** (`xrWaitSwapchainImage` and `xrEndFrame` itself).

Around it sit section peaks - `swap_wait_max_us`, `input_max_us`, `locate_max_us`, `flush_max_us`,
`endframe_max_us` - which *together cover the frame*, so nothing hides between them. `long_frames`
counts frames over **8 ms against an 11.1 ms budget**, which leaves headroom rather than measuring the
cliff.

**That decomposition is what makes an answer possible.** Of 19 windows containing a frame over 11.1 ms,
**all 19 were more than 90% `xrEndFrame`** - the compositor accepting the frame, not their code. Without
the split, all nineteen would have read as "our frame was slow".

### A stale image with a fresh pose defeats reprojection silently

Their `pose_fallback` counter exists for a specific and nasty failure:

> When no remembered render pose is found for an imported image, an old image gets the **current** pose
> forced onto it, **the compositor believes it is fresh and stops correcting** - and the world visibly
> lags.

Reprojection can only fix a frame whose pose it can trust. Mislabelling a stale frame as current does
not merely skip the correction, it *disables* it, so the failure is worse than dropping the frame would
have been ([STR-010](pattern-catalog.md#str-010) is the right move instead).

**And it had been invisible**: *"until now only the first hit was logged, so the failure was not logged
at all."* A first-occurrence-only log is how a recurring fault reads as a one-off - the same trap as
[a throttled counter](06-debugging-methodology.md#throttled-counter-ratio), one step further along.
Their run after the fix reports `pose_fallback` **0 throughout**, which is what makes the number
evidence rather than decoration.

### Run the control through your own test convention

The session's most expensive lesson is not about VR at all. Their test convention moved the game window
off-screen with `SetWindowPos` for silent unattended runs. That triggers **Windows DWM
occlusion-throttling, capping real `Present()` at ~30 fps regardless of anything the mod does** - so
every framerate comparison made under that convention was measuring DWM.

They caught it by running the **bridge-OFF baseline under the same convention** and finding it was also
~30 fps when it should have been ~60. **A harness confound is invisible until the control goes through
the harness too**, and "the baseline is fine, I only changed the thing under test" is exactly the
assumption that hides it.

### In a stereo mod, a counter at `Present` counts eyes

The second correction is a one-line mechanism with three sessions of consequences. Their per-`Present`
frame counter incremented **twice per displayed frame**, because the render entry point invokes the
hooked `Present()` once per eye - one suppressed for eye 1, one real for eye 2. Reported figures of
"119 fps baseline, 57-60 fps bridged" were about **2x inflated**; the true numbers were ~60 and ~28-30.

The part worth copying is what survived. **The relative finding - a ~2x regression - stayed valid,
because the artifact applied equally to both sides of the comparison.** Only the absolutes were wrong.
When you find a counting error, say explicitly which of your claims were ratios and which were levels;
a ratio is often still good. They also went back and annotated the three earlier notes rather than
leaving corrected numbers only in the newest one.

## The matched A/B protocol

1. Use release builds and record exact build identity.
2. Match runtime, refresh rate, eye resolution, mission, spawn, pose and
   settings.
3. Warm caches and thermals consistently.
4. Predeclare the metric expected to move.
5. Capture both numeric telemetry and device/render output.
6. Repeat noisy runs.
7. Report regressions and negative results.
8. Restore profiler/runtime state after testing.

A fast flat harness can validate logic and submission counts. It cannot prove
Quest GPU parity, compositor behavior, tracking lifecycle or thermal
performance.

## Two reprojections that cover each other's failure mode {#composed-reprojection}

SnowRunner-VR ships alternate-eye rendering with two smoothing options, and the interesting part is that
its second option is built on top of the first rather than beside it. `[SOURCE]`

- **Stale-eye warp** brings that eye's own last real render forward to now and fills every pixel the
  shift could not reach. Three escalating modes: headset rotation only; plus the game camera's rotation;
  plus a full 6-DoF reprojection by the camera's translation. **This is the default**, on the grounds
  that it has the fewest artefacts while still being smooth - a ladder, with the cheapest rung first.
- **DIBR shift** reprojects the eye that *was* rendered into the other one using the scene depth buffer,
  so both eyes carry this instant's content. Its known failure is the **disocclusion hole**: geometry the
  source eye never saw has no pixels to supply.

**The composition:** the disocclusion hole is filled from the stale-eye warp. Their description - *"it's
like a poor man's AFR"* - undersells it. Each technique's blind spot is the other's strength: DIBR has
this instant's content but no data behind occluders; the stale warp has data everywhere but from an
older instant. **When you have two approximations with disjoint failure modes, the second one is a
better hole-filler than any inpainting heuristic**, because it is real rendered content rather than
invented content.

### Camera motion as a stand-in for motion vectors

Their honest note on a constraint worth planning around: *"I could not find motion vectors, so I'm using
the game camera movement because most of the world is static, and then exclude dynamic elements that
could move with the camera (trucks and trailers)."*

**In a mostly-static world, camera motion is a serviceable proxy for per-pixel motion** - and the
substitution is only safe if you can *name and exclude* the things that move independently. The cost is
stated rather than hidden: excluded objects show the AER offset, so **the cockpit feels lower-framerate
than the world around it**. That asymmetry is the price of the approximation, and in a cockpit game it
lands on the thing the player looks at most - worth knowing before choosing this route.

## D3D12 replay go/no-go checklist

Do not build a stereo architecture on command-list replay until all are true:

- [ ] meaningful scene lists are identified by content, not ordinal;
- [ ] starting and ending resource states are known;
- [ ] UAV/indirect writes are classified for idempotence;
- [ ] aliasing/transient lifetimes remain valid for the second execution;
- [ ] cross-queue producers/consumers are included;
- [ ] target descriptors can be redirected or work can be re-recorded;
- [ ] camera/projection data is patchable at the time it is read;
- [ ] final color can be captured without replaying UI/present work;
- [ ] bounded soak and fence watchdog pass;
- [ ] measured cost fits the declared headset budget.

If aliasing lifetime or descriptor ownership fails, stop calling the problem a
barrier bug. Change the stereo route.
