# VR Modding Playbook — RE-first, source-ready, cross-engine

Distilled from the active first-hand flat-to-VR conversions tracked in the coverage ledger, on
deliberately dissimilar engines —
**SS2VR** (System Shock 2, Dark/KEX, D3D11), **BioshockVR** (BioShock, Unreal 2.5, D3D11),
**SOMAVR** (SOMA, HPL3, **OpenGL**), **PreyVR** (Prey, CryEngine-derived, D3D11, 64-bit),
**DishonoredVR** (Dishonored, **Unreal Engine 3**, **D3D9**), **FarCry2-VR** (Far Cry 2, Dunia,
**D3D10**) and **Swat4-VR** (SWAT 4, Unreal 2.5, **D3D9**) — spanning 1998 to 2017, four graphics APIs
and both bitnesses. Everything here earned its place by costing real time at least once. The engines
differ on every axis; the VR conversion keeps hitting the *same* patterns, roadblocks and solutions.
Lessons are tagged with the project that paid for them. The primary evidence base is reverse-engineered
native injection, but the playbook now separates that route from source-owned development and rejoins
both at the shared VR problems: pose, stereo, culling, lifecycle, render state, input, UI and release.

Folded in as independent corroboration, from authors who hit the same walls on engines we don't own:
[HaloVR](https://github.com/pancreations/Halo-MCC-VR), an independent
[BioShock VR mod](13-teardown-bioshock-vr.md) on the *same game* as one of ours, the
[IL-2 1946 VR mod](15-teardown-il2-1946-vr.md) — the one target whose game logic is a **managed,
moddable layer**, which makes it the control case for how much of this method is a tax on not having
source — Praydog's **UEVR**
write-ups, and a growing source survey of shipped mods whose defaults tell you what actually survived
contact with users.

--8<-- "generated/source-summary.md"

**Where to start depends on why you're here.** New or inherited target →
[Start or Unblock a VR Port](start-new-port.md). Project has several plausible next steps →
[fleet bottleneck map](bottleneck-map.md). Something visibly broken →
[symptom-index.md](symptom-index.md). Wondering if another project already solved it →
[cross-project-index.md](cross-project-index.md). Want working code rather than a rule →
[A1](a1-rotation-and-frames.md) / [A2](a2-pose-pipeline.md) / [A3](a3-stereo-projection.md) /
[A4](a4-hook-safety.md) / [A5](a5-flat-harness-stats.md).

> **First stereo image not fusing?** Every project here hit that, and none recognised it first time.
> Go straight to
> [the per-eye alignment diagnosis](09-d3d11-openxr-injection.md#the-two-eyes-dont-line-up-a-five-minute-differential-diagnosis)
> — it separates the whole problem space with two questions and lists the desk assertions that retire
> most of it without a headset.

## Reading order

**Stuck on something right now?** Don't read in order — go to
**[symptom-index.md](symptom-index.md)**, which maps *what you are seeing* to the chapter that covers it.
Wondering whether another project already solved your problem? **[cross-project-index.md](cross-project-index.md)**
says who solved what and where the raw working is.

| Doc | What it covers |
| --- | --- |
| [Start or Unblock a VR Port](start-new-port.md) | **Route selector** — classify source/RE authority, begin a target, or resume at the earliest uncleared gate |
| [RE-owned route](reverse-engineered-route.md) | **Primary workflow** — fingerprint, preflight, load, discover, reconstruct ownership, stabilize anchors and select stereo |
| [Source-owned route](source-owned-route.md) | Reproducible stock build, call-graph ownership, per-frame/per-view separation, VR boundary and fork maintenance |
| [Shared VR spine](shared-vr-spine.md) | The work both routes share — pose, stereo, lifecycle, rendering, input, adaptation, performance and release |
| [fleet bottleneck map](bottleneck-map.md) | Generated cross-project blocker matrix, current limiting question and next proof for every in-house project |
| [project evidence templates](project-evidence-templates.md) | Copy-ready schemas for authority, targets, tools, addresses, cameras, consumers, experiments, stereo, passes and session handoff |
| [symptom-index.md](symptom-index.md) | **Start here when something is wrong** — symptom → chapter |
| [pattern catalog](pattern-catalog.md) | Atomic solution cards with stable IDs for search, issues and agent retrieval |
| [failure atlas](failure-atlas.md) | Normalized symptom → discriminator → cause → route records, with globally distinct `FAIL-…` IDs |
| [a1](a1-rotation-and-frames.md) · [a2](a2-pose-pipeline.md) · [a3](a3-stereo-projection.md) · [a4](a4-hook-safety.md) · [a5](a5-flat-harness-stats.md) | **Reference code** — working implementations of the maths and patterns everyone gets wrong, each with the test that catches the error |
| [cross-project-index.md](cross-project-index.md) | **Who solved what** across the fleet and external sources, with paths |
| [coverage dashboard](coverage.md) | What has and has not been harvested, review freshness, source snapshots and untracked directories |
| [glossary](glossary.md) | Canonical meanings for camera, pose, stereo, lifecycle, render and evidence terms |
| [00-engine-profiles.md](00-engine-profiles.md) | The engines side by side, the cross-engine spine, and how to read the evidence tags |
| [01-camera-and-tracking.md](01-camera-and-tracking.md) | The multiple-cameras problem, authoritative rendering, cull-camera ownership, turn/recenter, comfort, frame-timing bug classes |
| [02-viewmodels-and-hands.md](02-viewmodels-and-hands.md) | Weapons/hands: double-draw, per-eye contamination, reference frames, native IK, pivots, Euler traps, haptics |
| [03-input-and-locomotion.md](03-input-and-locomotion.md) | The input ladder (keys → actions → virtual gamepad → native calls), double-driving, driving the native mover, stick-as-buttons |
| [04-ui-and-hud.md](04-ui-and-hud.md) | UI capture/quad layers, HUD element ownership, reticle suppression, semantic reticles, panel placement |
| [05-assets-and-materials.md](05-assets-and-materials.md) | Custom model/material pipelines, exporter header traps, engine package/material formats, one-variable asset A/Bs |
| [06-debugging-methodology.md](06-debugging-methodology.md) | The big one: build identity, probes over theories, RenderDoc/crash-dump workflows, log budgets |
| [07-engine-integration-safety.md](07-engine-integration-safety.md) | Hooking discipline: guards, signatures, fail-closed lanes, object lifecycle seams, revert knobs |
| [08-project-process.md](08-project-process.md) | The documentation system, test-validity discipline, packaging/backup hygiene |
| [09-d3d11-openxr-injection.md](09-d3d11-openxr-injection.md) | The graphics spine: staged OpenXR proofs, private eye targets, native stereo, render-view ownership, screen-space effects, FoV/gamma/performance |
| [10-graphics-apis.md](10-graphics-apis.md) | The same spine translated across APIs: D3D11 ↔ OpenGL, SwapBuffers, FBOs, uniform-driven projection, AFR |
| [11-re-anchoring-and-discovery.md](11-re-anchoring-and-discovery.md) | Locating things in an unknown binary: the anchor ladder, string refs, emulation/tainting, version robustness, tooling (ReGenny) |
| [12-torso-calculations-and-ergonomics.md](12-torso-calculations-and-ergonomics.md) | Three-point upper-body reconstruction: body-heading ownership, shoulder anchors, reach compensation, elbow swivel, efficient IK, diagnostics |
| [13-teardown-bioshock-vr.md](13-teardown-bioshock-vr.md) | An independent mod on the *same game*: scene re-entry vs per-draw stereo, pair coherence, pacing hangs, in-process frame inspector, automated flat-screen harness |
| [14-render-pass-hazard-atlas.md](14-render-pass-hazard-atlas.md) | Classify any pass you meet in a capture: the five stereo-hazard classes, the temporal/motion-vector trap, and what to disable outright |
| [15-teardown-il2-1946-vr.md](15-teardown-il2-1946-vr.md) | A mod whose target has a **managed, moddable game layer** — no injection, no RE. Same-frame three-pass stereo, 100% compositor-overlay UI, and what "no hook" costs you |
| [16-teardown-virtua-cop-2-vr.md](16-teardown-virtua-cop-2-vr.md) | A 1997 arcade rail shooter: **reconstructing the 3D scene from the 2D draw stream** instead of hooking a camera, recovering camera motion by cancellation, the 32/64 two-process split, and the light-gun aim round-trip |
| [17-teardown-fc2vr-native-stereo.md](17-teardown-fc2vr-native-stereo.md) | Native stereo in FEAR VR and FarCry2-VR: scene re-entry, side-effect gates, camera delivery and the four-rung ladder |
| [18-beyond-the-native-injector.md](18-beyond-the-native-injector.md) | Source ports, managed plugins, framework companions, recreations and how mode changes the solution surface |
| [19-d3d12-and-performance.md](19-d3d12-and-performance.md) | D3D12 replay hazards, frame-graph ownership, multi-queue failures and desktop/mobile VR performance evidence |
| [20-audio-and-haptics.md](20-audio-and-haptics.md) | Tracked listeners, moving emitters, audio lanes, channel ownership and semantic haptic feedback |
| [cross-engine-map.md](cross-engine-map.md) | Capstone: the overlap matrix across the engines, and the axes where they genuinely diverge |

## The nine lessons that outrank everything else

1. **Classify integration authority before choosing tools.** Full shippable source, an SDK oracle,
   a managed/script layer, a generic framework and a closed retail binary create different discovery
   and maintenance costs. The real question is which code owning the camera and render loop can be
   built and shipped.
2. **Identify which camera each engine consumer actually uses.** A VR mod creates a second
   camera; every subsystem (viewmodels, picking, attached objects, UI, projectiles) silently
   binds to one of the two. Most "VR jank" is a frame mismatch, not engine noise. *(Every project.)*
3. **Make builds self-identify, and make every component prove it loaded.** First log line =
   version + build time + loaded file path. Whole days die to "the fix didn't work" when the fix
   was never running — installed but not in the engine's load path, shadowed by an earlier package
   shipping the same file, or simply captured from a build that predates it. Being present on disk
   is not being loaded, and being loaded is not having run.
4. **Measure before theorizing.** A readback probe (write X, log where the engine actually
   put it) or a multi-candidate residual probe replaces a week of plausible-sounding theories
   with one condump.
5. **Exactly one input path drives any given control.** Double-driven movement reads as
   mysterious speed, jitter, or "broken thresholds" and never as what it is.
6. **Every change ships with a machine-checkable proof line and a revert knob.** A test whose
   validity can't be verified from logs alone will eventually test nothing, silently.
7. **Preserve render-view ownership.** Matching size/format does not mean two HDR draws belong
   to the same camera. Main, reflection, portal, capture, and vista views must not share one
   private stereo depth/color space.
8. **OpenXR submission is plumbing, not stereo.** A correct session, valid pose, and two eye
   textures prove transport. Native stereo still requires per-eye world rendering, coherent
   projection companions, depth, culling, and separate UI/viewmodel/screen-space lanes — and
   the engine's own camera must own culling before head translation reveals new geometry.
9. **Drive the engine's own systems before you reimplement them.** The engine already owns a
   cull camera, an analog mover, an IK solver, an interaction picker, a fire-direction seam.
   Hooking and *steering* those (fail-closed, signature-guarded) beats fighting them from
   outside — and it survives patches better than a raw RVA call. Reimplementation is the
   fallback, not the default. *(SS2VR drives KEX's cull camera + Squirrel verbs; BioshockVR
   drives native AimIK + the fire-start rotator; SOMAVR drives the native analog mover, picker,
   and camera-add channels.)*
