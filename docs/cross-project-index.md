# Cross-Project Index — who solved what, and where it's written down

**Use this before solving something from scratch.** The playbook chapters carry the *distilled* rule; this
page points at the *raw working* in whichever project actually did it, so you can read the full reasoning,
the numbers, and what they tried first.

If you are an agent on one of these projects: the other projects' `docs/` folders are readable. Nothing
here is secret, and several of these questions have already cost someone a week.

This index answers **who has useful working**. The generated
[fleet bottleneck map](bottleneck-map.md) answers **which missing capability is
currently on the critical path**, including a next proof for every in-house
project.

---

## The fleet at a glance

This table is generated from `sources.yml`. Status distinguishes active
conversions from research targets, so a prospect cannot silently inflate the
first-hand conversion count.

--8<-- "generated/fleet-table.md"

### External mods surveyed — what each one is good for

All under `D:\Dev Debug\Other VR mods\`, read-only. **Go to the source tree, not just the chapter** —
the chapters carry the distilled rule, these carry the working. Distilled in
[16](16-teardown-virtua-cop-2-vr.md), [17](17-teardown-fc2vr-native-stereo.md) and
[18](18-beyond-the-native-injector.md).

| Mod | Engine / mode | Read it for |
|---|---|---|
| **fear-vr** | LithTech, native injector | **Native stereo done from source.** The definition (world twice, everything else once), the side-effect gate, the smallest-safe-hook argument, the CRT ABI wall |
| **cyberpunk-vr-port** | REDengine 4 / D3D12 | 80+ RE docs. Second view via engine registration, the four shared structures, off-axis lens coverage, and the best negative-result discipline anywhere |
| **witcher3-vr** | REDengine 3 / D3D12 | Canted displays, optical-centre offset for asymmetric frusta, shadow-cascade authority, per-eye temporal history, script-mod-as-state-bridge |
| **shock2quest** | Dark engine **recreation** (Rust) | **A live oracle for Dark formats** — `dark/` crate: gamesys, params, sound_schema, speech_db, mesh/skeleton importers, hitboxes. Directly relevant to SS2VR |
| **Halo-MCC-VR** | Blam/Saber, 3 games in one mod | Multi-title runtime ownership, the success-and-failure-in-one-log method, antivirus/release checklist, per-context calibration |
| **anvilengine2vr** | AnvilNext 2.0 / DXGI | `worldMatrixOverride` — an override the engine already honours. Sibling-port guide with published pseudocode |
| **CallOfDuty4_VR** | IW source port | Deployment engineering: 32-bit OpenXR registration, preflight vs live receipt, refuse-don't-guess installers |
| **JKXR** | id Tech 3 source port | Command-buffer stereo replay **with validate-before-replay**; grip-to-button hysteresis; latched action ownership |
| **BF2VR** | Frostbite / D3D11, native | The `-Array` string-convention type enumeration; register mid-hooks; view-dependent lighting disabled via engine settings; anti-cheat and the interoperability framing |
| **MonsterDeadWood FC2VR** | Dunia / D3D9, native | Exact-build culling sphere/plane dataflow; observer-only association before culling mutation; hash-locked golden experiments |
| **MonsterDeadWood C2VR** | CryEngine 3 / D3D11, native | Atomic publication of pixels + depth + pose/FOV/contract; last-good pair retains original metadata; startup absence is WAIT, not permanent fault |
| **MonsterDeadWood BF3VR** | Frostbite 2 / D3D11, native | Same-Present native scheduler proof; pointer identity is not image identity; distinct eye images still need inverse-depth disparity proof |
| **MonsterDeadWood DiRT2VR** | EGO / D3D11, native | Submitted-buffer stereo oracle; consumer-draw → stack → recurring-RVA discovery; the `EFLAGS.RF` breakpoint-resume trap |
| **MonsterDeadWood TimeShiftVR** | Saber3D / D3D9, native | Structural execution versus visual acceptance; draw ordinal + geometry/shader signature beats last-texture-per-shader replay |
| **Rea-Virtua-Cop-2-VR** | 1997 fixed-function | Scene reconstruction from the draw stream — the bottom rung, and when it is the *only* door |
| **GTFO / SPT-VR / RoR2 / BendyVR / MyFriendlyNeighborhood / White_Knuckle_VR** | Unity, BepInEx | The managed-plugin mode: per-eye callbacks, hidden-area-mask rebuild, physics-input philosophy, third-person→VR |
| **satisfactory-uevr-enhancements** | UEVR + companion mod | What you build *next to* a generic framework |
| **WorldWarVR-Releases** | binaries only | Compatibility as a property of the **route**, not the headset |
| **sims4-vr** | Sims 4, script-mod + injected DLL | A god-view target; script-driven camera; **the only surviving copy** of a deleted repo |
| **thedarkmodvr**, **SystemReShock-UEVR-Plugin**, **UEVR** | — | `WGL_NV_DX_interop2` route; UEVR plugin shape; the framework itself |

**Also read-only:** the **IL-2 1946 VR mod** (managed Java game layer, no injection —
[15](15-teardown-il2-1946-vr.md); `D:\Dev Debug\IL2 1946 VR Mod\`), `bioshock-vr` (rival mod, same
game — [13](13-teardown-bioshock-vr.md)), and the shipped-mod source trees in
`D:\Dev Debug\Other VR Mods\` plus `thedarkmodvr` and `UEVR-UEVR_AFW_v1.0-beta.5`.

**Engine siblings — knowledge should flow between these:**
- **BioshockVR ↔ Swat4-VR** — both Vengeance/UE2.5. Swat4 has 7,682 exported symbols and 3,233 `.uc`
  source files; BioshockVR has none (its exe has **no export table at all**). Flow runs *from* Swat4.
  See `Swat4-VR\docs\VENGEANCE_SHARED_FINDINGS.md`.
- **DishonoredVR ↔ Swat4-VR** — both plain D3D9, and they solved the bridge question from opposite ends.
- **SOMAVR ↔ PreyVR** — the two 64-bit targets. x64-only traps (REX prefixes) apply to both and to nobody else.
- **MonsterDeadWood FC2VR ↔ FarCry2-VR** — same game, different retail bytes and graphics route. Flow the
  culling *method* across; never flow an RVA or ABI without proving it against the in-house executable.
  **Done right on 2026-09-05:** the vtable region between his GOG image and the UPLAY/Steam one shifts by an
  *exactly constant* `+0x88274` - both known slots agree - so his `DUNIA_VTABLE_RVA` predicts ours as a
  **value, not a window**. Read back from the shipping `Dunia.dll`, `+0x14` holds `PrepareFrameGraph` and
  `+0x18` `WorldExec` exactly as he documents, plus six D3D9 renderer slots we did not have. Prediction from
  his source, confirmed against our bytes, no run. Two things his contract does that ours did not:
  transport the camera basis by the relative rotation, and verify the rebuilt view against the desired eye
  view with a fail-open guard - which `pose_agreement.h` had been built for and never wired to. And a
  worry that cost two misdiagnoses evaporated: *his kernel calls `CameraRebuild` itself*, so whether the
  engine calls it under D3D9 never mattered.
- **SoF-VR ↔ Medal-of-Honor-vr** — the id lineage, solved from **opposite ends**, which is what makes the
  pair worth reading. SoF is id Tech 2 via Raven and is **RE-owned at the `ref_gl` module contract**: a
  proxy DLL beside the original, no byte of the game patched. MoHAA is id Tech 3 via FAKK2 and is
  **source-owned** through the OpenMoHAA fork. Both reach the same place — the world render is a callable
  unit taking the camera as a parameter — so the *stereo* reasoning flows freely between them while the
  *delivery* reasoning does not. SoF also proves the module-contract route survives a heavily forked
  engine, which is the question MoHAA never had to ask. See [RE-008](pattern-catalog.md#re-008).

---

## MonsterDeadWood transfer map

This is the practical hand-off into the in-house fleet. It lists the first place to apply each result;
it does **not** claim those project code changes have been made.

| New reusable result | Canonical home | First in-house use |
|---|---|---|
| Claim ID + baseline + artifacts + decision rule; promote only that claim | [META-010](pattern-catalog.md#meta-010), [06](06-debugging-methodology.md#claim-scoped-promotion) | Every project experiment and evidence ledger |
| Pixels, depth, pose, FOV and resource generation publish atomically | [STR-002](pattern-catalog.md#str-002) | **FarCry2-VR native pair**, then SS2VR/SOMAVR asynchronous pair audits |
| Semantic image epoch outranks COM pointer or shader identity | [STR-004](pattern-catalog.md#str-004) | FarCry2-VR capture seam; BioshockVR/DishonoredVR replay correspondence |
| Observer-only denominator before force-pass or duplication | [06](06-debugging-methodology.md#observer-before-intervention) | FarCry2-VR M3/culling probes; Swat4-VR side-effect controls |
| Submitted-buffer oracle plus inverse-depth disparity | [FAIL-STR-001](failure-atlas.md) | Objective stereo acceptance across the fleet |
| `EFLAGS.RF` on hardware execution-breakpoint resume | [RE-005](pattern-catalog.md#re-005) | Every x86 target using DR breakpoints |
| Exact execution is not visible success | [FAIL-TEST-016](failure-atlas.md) | Render-state/shadow repairs in all projects |

---

## Three axes, and why a project's position on one says nothing about the others

Before comparing projects, note which scale you are comparing on:

| Axis | Question | Where |
|---|---|---|
| **Mode** | Injector / managed plugin / framework+companion / source port / recreation | [18](18-beyond-the-native-injector.md) |
| **Stereo rung** | Native stereo / per-draw replay / alternate-eye / reconstruction | [17](17-teardown-fc2vr-native-stereo.md) |
| **Completeness tier** | T0 flat-in-headset → T4 adapted-for-VR | [08](08-project-process.md#how-vr-is-it-declare-a-completeness-tier-and-ship-to-it) |

The fleet is mostly one mode (native injector) and spread across the other two. **Rung and tier move
independently** — Virtua Cop 2 VR is on the lowest stereo rung and is a genuinely good mod, while a
project can reach rung 1 and still be at T1 for completeness.

## Native stereo — the live per-project answer

The rung-1 question ([17](17-teardown-fc2vr-native-stereo.md)) is **two questions**: can the world render
be invoked again, and **how does the camera reach the renderer**. Several projects have now answered from
their own binaries. **Check here before starting that investigation.**

| Project | Camera arrives as | World-render re-entrancy | State |
|---|---|---|---|
| **SS2VR** | **Parameter plus globals (STATIC)** — traversal0x45C470, native backend0x32C480 | **LIVE owned eye products through v3.93:** same-frame native pairs, independent2560x1440 targets, same-camera and displaced doorway controls,600 centered frames and bounded recovery | [KEX / Dark method and evidence limits](kex-dark-native-stereo.md). Each eye owns world cells and complete admitted MD/MM scene slices; deferred scratch queues are reset separately from retained arenas. Current published basis and shared shader origin both need correct ownership. Particle/sorted lanes and arbitrary optics remain open. Native XR has its own transport/HMD evidence boundary; see the linked current project receipt. |
| **PreyVR** | **Parameter** — `CreateGeneralPassRenderingInfo(const CCamera&,…)` @ `0x1E5B30`; `CRenderView::SetCamera` copies **by value** | `C3DEngine::RenderWorld` @ `0x21F520`, zero direct xrefs — all virtual dispatch, `IProcess` idx 3, vtable `+0x18` | **H-009: preconditions met, viability not established.** Nothing called yet |
| **FarCry2-VR** | **Global** — must borrow and restore | `WorldExec` @ `0x342360` — 37 pass dispatches, **no simulation** | M3 Q1 live: 3,521 prepare+execute replays, 1.915× draws, animator 1.0×. Camera delivery, zero-delta control and capture/publication remain open |
| **SOMAVR** | **Parameter** — `iRenderer::Render(…, cFrustum* apFrustum, …)`, `mpCurrentFrustum` assigned from the argument every call | unresolved | **But their own AFR path mutates the frustum in place** — F-19 and F-20 are that defect family, self-inflicted |
| **DishonoredVR** | unresolved | `+0x2C59A0` is a reachability lead only; needs 59 callees walked | **Not open.** Side-effect gate never run by anyone |
| **Swat4-VR** | unresolved | unresolved — 7,682 exported symbols make it fast to check | Open |
| **BioshockVR** | unresolved | unresolved — the 1,822-entry native table is the obvious probe | On rung 2 (private eye targets + pair latching) |
| **Medal-of-Honor-vr** | **Parameter** — `viewParms_t` is built per view and passed into `R_RenderView`; the VR layer sets four tangents on it | **PROVEN and shipping** — the engine's own portal/sky re-entry of `R_RenderView`, called twice from one prepared `tr.refdef` | Source-owned (OpenMoHAA fork). Counter proof: `renderScene` 63/s unchanged while `renderView` doubled to 126/s, disparity 0 at separation 0 and depth-dependent above it |
| **SoF-VR** | **Parameter** — `refdef_t*` passed to the `RenderFrame` export (slot 16); the renderer copies 33 dwords out of it into `r_newrefdef` on entry | **Structurally free** — `RenderFrame` is the whole world render and the proxy owns the call site, so "render twice" is calling the export twice | Layout confirmed live 2026-09-04: `fov_y` residual 0.0000 vs `CalcFov`, prefix shift +1. Nothing written yet; M3 is the first reversible mutation |
| **Sims4VR** | **Parameter** — a per-draw constant-buffer write (`cbuffer0`): the same object in the same frame receives two different view-projections, so the delivery is copy-by-value and the borrow/restore/freeze-observers family does not apply | **Structurally present, not independently controllable** — world geometry is traversed three times per frame (depth prepass, 2048x6144 shadow atlas, main view) with three matrices, but every second traversal found so far shares the main camera's basis | Rung 1 selected by evidence, rung 2 declared fallback; nothing exercised. Cost unmeasured, and the main path is 8x MSAA so a per-eye render inherits a resolve |

**The cheapest unanswered check for the last three:** find a repeat world-render the engine *already*
performs — cubemap/reflection probes, portals, mirrors, security monitors, render-to-texture. Verify
that it reaches actual GPU scene draws: SS2VR's earlier six-call interpretation was lighting visibility,
not complete rendering ([AE boundary receipts](<D:/Dev Debug/ss2vr-native-stereo/docs/NATIVE_STEREO_INVESTIGATION.md>)).
Even an existing GPU repeat render can be a **reduced** pass set — *proof, not vehicle*.

## Per-eye alignment — solved, do not re-derive

**Four projects hit "the two eyes don't line up" and none recognised it first time.** FarCry2-VR solved
it and wrote down the discriminator; it is now
[09](09-d3d11-openxr-injection.md#the-two-eyes-dont-line-up-a-five-minute-differential-diagnosis) with a
full table and desk assertions.

The two findings worth knowing before you touch anything:

- **FOV halved in degrees instead of tangent space.** FarCry2's degrees answer was wrong by **9.4°** and
  looked entirely plausible. `2*atan(tan(fov/2)*scale)`. `Swat4-VR/…`, `FarCry2-vr/docs/CURRENT_STATE.md`.
- **`SwapEyes` was a no-op** — it flipped the eye *label* and derived the offset *from the flipped label*,
  so both settings produced identical geometry, and the desk test asserted the broken behaviour as
  correct. `FarCry2-vr/docs/CURRENT_STATE.md`.

## Graphics API → OpenXR bridge

| Question | Answered by | Where |
|---|---|---|
| **D3D9 → OpenXR, route decision** | Both, from opposite ends — see [10](10-graphics-apis.md) for the decision table | below |
| Plain D3D9 *cannot* create shared resources (`D3DERR_INVALIDCALL`), only `Ex` can | DishonoredVR | `docs/research/08-d3d9-d3d11-interop-2026-08-01.md` |
| `D3D9Ex` forbids `D3DPOOL_MANAGED` — and this engine uses it, so `Ex` is closed | DishonoredVR | `docs/research/` + commit `f2a29e0` |
| Use `Direct3DCreate9On12`, **never** `...On12Ex` | DishonoredVR | same |
| 9On12 → D3D12 → `XR_KHR_D3D12_enable`, **validated in-headset** | Swat4-VR | `docs/DECISION_LOG.md` D-0012 |
| `D3DPOOL_MANAGED` falsifies the shared-surface route | Swat4-VR | `docs/` R1 battery |
| **D3D10 → OpenXR** via DXGI shared surface | FarCry2-VR | `docs/engine/D3D9_OPENXR_NOTES.md` |
| **OpenGL → OpenXR**, incl. depth-layer negotiation and unit conversion | SOMAVR | `docs/HPL_OPENGL_NOTES.md`, `BUILD_HISTORY.md` |
| **D3D11 → OpenXR**, the reference path | SS2VR, BioshockVR | see [09](09-d3d11-openxr-injection.md) |
| GL renderer borrowing D3D11's XR path (`WGL_NV_DX_interop2`) | *external: thedarkmodvr* | `renderer/vr/D3D11Helper.cpp` |

## Stereo architecture

| Question | Answered by | Where |
|---|---|---|
| Alternate-eye (AFR): coherence, pair latching, eye-lag root cause | SS2VR | `docs/UEVR_STEREO_LESSONS.md`, `VR_LATENCY_RECOVERY_PLAN.md` |
| Per-eye temporal history banks under AFR (the fix pattern) | SOMAVR | `docs/BUILD_HISTORY.md` (0.5.x) |
| Atomic pixels + depth + render pose/FOV/contract publication across keyed-mutex transport | *external: MonsterDeadWood C2VR* | `C2VR/research/POSEPAIR_PACKET_ATOMICITY_PACING_20260824.md`, donor `t1_proxy.cpp` |
| One resource reused serially for L/R: semantic phase and generation outrank pointer identity | *external: MonsterDeadWood BF3VR* | `BF3VR/docs/STATE.md` |
| Submitted-buffer oracle: mono / normal / swap / exaggerated phases | *external: MonsterDeadWood DiRT2VR* | `DiRT2VR/docs/XR_EYE_SNAPSHOT_ORACLE_v1.3.0.md` |
| **SequentialReentry** — call the scene-draw twice | *external: bioshock-vr* | [13](13-teardown-bioshock-vr.md) |
| Per-draw stereo replay, private eye targets, proof ladder | BioshockVR | `docs/BUILD_HISTORY.md`, `DECISION_LOG.md` |
| Desktop + two XR eye frames as three complete game frames, with each eye copied from the main offscreen colour image | *external: KSA_XR* | [10](10-graphics-apis.md#vulkan-three-frame-proof) |
| Replace the third desktop world render with a fullscreen-triangle copy of the finished left eye | *external: Scrap-Mechanic-Native-VR* | [10](10-graphics-apis.md#vulkan-three-frame-proof) |
| Four-edge frustum = free asymmetric projection | PreyVR | `docs/RESEARCH_LOG.md` |
| Pre-temporal renderer verdict (no TAA ⇒ alternate-eye cheap) | FarCry2-VR | `docs/engine/RENDER_PASS_HAZARDS.md` |
| **Same-frame three-pass** (two eyes + a first-class desktop mirror) on a replayable scene graph | *external: IL-2 1946 VR* | [15](15-teardown-il2-1946-vr.md) |
| Asymmetric render matrix + symmetric cull FOV — the two-frusta defect | *external: IL-2 1946 VR* | [15](15-teardown-il2-1946-vr.md) |
| **Reconstruct the scene from the 2D draw stream** — when there is no camera to hook | *external: Virtua Cop 2 VR* | [16](16-teardown-virtua-cop-2-vr.md) |
| Recover camera motion by cancellation (`M(t)·M(t-1)⁻¹`), with consensus voting | *external: Virtua Cop 2 VR* | [16](16-teardown-virtua-cop-2-vr.md) |
| 32/64 two-process split over seqlock shared memory — the "last resort" route, shipped | *external: Virtua Cop 2 VR* | [16](16-teardown-virtua-cop-2-vr.md) |

## Camera, tracking, comfort

| Question | Answered by | Where |
|---|---|---|
| Cull-camera ownership; the FOV lever | SS2VR; *Halo-MCC-VR* | `docs/CULLING_FRUSTUM.md` |
| Authored-camera yielding (20 player states, 3 detection signals) | SOMAVR | `docs/AUTHORED_STATES_AND_VISIBLE_HANDS_RE.md` |
| Reference-space first-pose settling latch | SOMAVR | `docs/BUILD_HISTORY.md` (0.5.10-poselatch) |
| Side-only binocular cull union: preserve depth planes, widen lateral planes | *external: MonsterDeadWood FC2VR* | `FC2VR/research/FRUSTUM_PLANE_CLASS_MAP_20260824.md` — method transfers; offsets do not |
| One recenter event across all lanes | BioshockVR | `docs/DECISION_LOG.md` |
| Unified tracking space as the root cause of *panel* drift (not view drift) | *external: IL-2 1946 VR* | [15](15-teardown-il2-1946-vr.md) |
| Roomscale crouch double-drop | SS2VR | `docs/ROOMSCALE_CROUCH_RESEARCH.md` |
| **Mechanic triage before building** (roll / up-vector / possession) | PreyVR, DishonoredVR | `PreyVR/docs/VR_MECHANICS_RISK.md`, `DishonoredVR/docs/research/09-vr-mechanic-risk-2026-08-03.md` |

## Input & interaction

| Question | Answered by | Where |
|---|---|---|
| **How shipped mods do it** (7 mods surveyed) | — | [03](03-input-and-locomotion.md), raw in `cross-engine-graph/harvest/ext_*.md` |
| Native analog mover at rung 4 (live-traced owner) | SOMAVR | `docs/BUILD_HISTORY.md` |
| XInput bridge as the working route | BioshockVR | `docs/BUILD_HISTORY.md` |
| Engine's own normalised axis/button funnel *above* XInput | FarCry2-VR | `docs/RE_FINDINGS.md` (DR-7) |
| Console `Exec` / `SET <class> <prop>` as a property-drive seam | Swat4-VR | `docs/ENGINE_NOTES_SWAT4.md` |
| Frob/pick: copy the engine's model, don't invent one | SS2VR | `docs/FROB_TARGET_LIBRARY.md`, `INTERACTION_SQUIRREL_REPORT.md` |
| Grab / throw / gravity-glove / holsters | SS2VR | `docs/SQUIRREL_WORLD_PHYSICS.md`, `VR_BODY_HOLSTERS.md` |
| Physical melee, parry, block | SS2VR | `docs/MELEE_DAMAGE_RE.md`, `MELEE_VR_SPEC.md` |

## Viewmodels, hands, weapons

| Question | Answered by | Where |
|---|---|---|
| Grip pose vs aim pose; one trim one algebra | BioshockVR | `docs/DECISION_LOG.md` |
| Native skeleton/IK vs pre-skinned verts | BioshockVR, SS2VR | `docs/` |
| Authored mount offset composition order | BioshockVR | `docs/BUILD_HISTORY.md` (0.3.18x) |
| Bone-chain twist distribution (skinning crease) | SOMAVR | `docs/FUTURE_SYSTEMS_RE.md` |
| Weapon mesh pipeline, vhots, LGMD | SS2VR | `docs/VR_WEAPON_MESH_PIPELINE.md`, `WEAPON_MODEL_SPEC.md` |

## Reverse engineering & tooling

| Question | Answered by | Where |
|---|---|---|
| Retail exported symbols (7,682) collapsing the anchor ladder | Swat4-VR | `docs/ADDRESS_REGISTRY.md` |
| **No** export table at all — when the rung is absent | BioshockVR | PE export directory RVA `0` |
| Shipped plaintext script layer as ground truth | SOMAVR (`.hps`), Swat4-VR (`.uc`) | `docs/` |
| **The game itself is the script layer** — `javap` over replaceable bytecode, no RE at all | *external: IL-2 1946 VR* | [15](15-teardown-il2-1946-vr.md) |
| **A shipped renderer plugin ABI** as the injection seam — no hooks at all | *external: Virtua Cop 2 VR* | [16](16-teardown-virtua-cop-2-vr.md) |
| Read the live projection every frame; invalidate derived caches when it changes | *external: Virtua Cop 2 VR* | [16](16-teardown-virtua-cop-2-vr.md) |
| x64 REX-prefix signature drift | SOMAVR, PreyVR | `SOMAVR/docs/BUILD_HISTORY.md`, `PreyVR/docs/ADDRESS_REGISTRY.md` |
| Ghidra annotation loss on re-analysis | PreyVR | `docs/GHIDRA_SYNC.md` |
| Frame inspector as a RenderDoc replacement | FarCry2-VR | `docs/RE_FINDINGS.md` |
| Live probing over static RE (four recipes failed) | SS2VR | `docs/FAILURE_REGISTRY.md` |
| Hardware execution breakpoint resumes only after `EFLAGS.RF`; `DR6` clear is insufficient | *external: MonsterDeadWood DiRT2VR* | `DiRT2VR/docs/results/REENTRY_CONTRACT_RF_FIX_20260827_031450_032351.md` |
| Start at a known GPU consumer, capture the first-consuming-draw stack, then rank recurring RVAs | *external: MonsterDeadWood DiRT2VR* | `DiRT2VR/docs/results/CB400_BIND_ISOLATOR_20260827_141903.md` |
| Promote registry/RTTI candidates only after direct graphics-API activity proves runtime ownership | *external: MonsterDeadWood TimeShiftVR* | `TimeShiftVR/docs/STATE.md` |

## Process, testing, harnesses

| Question | Answered by | Where |
|---|---|---|
| Flat harness + **measured** noise floor | FarCry2-VR, Swat4-VR | `FarCry2-vr/docs/runbooks/flat-harness.md`, `Swat4-VR/docs/` R8 |
| Control capture that can veto a verdict | Swat4-VR | `docs/DERISKING_BATTERY.md` |
| Headless fixtures replaying live discoveries | PreyVR | `docs/HEADLESS_TESTING.md` |
| Pre-registered decision rules (confirm/refute/ambiguous) | PreyVR | `docs/LIVE_*_PROTOCOL.md` |
| Claim-scoped branch promotion with baseline and artifact integrity gates | *external: all five MonsterDeadWood trees* | each project's `docs/BRANCH_PROMOTION_POLICY.md` + `tools/research_integrity.py` |
| Launch preconditions as test validity (affinity mask) | FarCry2-VR | `docs/DECISION_LOG.md` D-005 |
| Config-key consumer check (found 10/15 dead) | Swat4-VR | `tools/check_config_keys.py` |
| Verifying the baseline you're betting on | Swat4-VR | `docs/FAILURE_REGISTRY.md` F-0011 |
| A headset substitute **inside the mod** (synthetic eye views, no runtime) plus pixel proofs that fail | Medal-of-Honor-vr | `code/vr/vr_null.c`, `tests/capture/measure_disparity.py`, `measure_yaw.py`, `measure_bands.py` |
| Test runs given their own profile so archived cvars cannot reach the play session | Medal-of-Honor-vr | `docs/DECISION_LOG.md` DEC-016, `tools/run-test.ps1` |

---

## Failure registries — read these before repeating something

Every project keeps one. They are the highest lesson-density documents in the fleet, and they are the
first thing to search when something smells familiar.

- `ss2vr-work\docs\FAILURE_REGISTRY.md`
- `BioshockVR\docs\FAILURE_REGISTRY.md`
- `Swat4-VR\docs\FAILURE_REGISTRY.md`
- `FarCry2-vr\docs\FAILURE_REGISTRY.md`
- `PreyVR\docs\FAILURE_REGISTRY.md`
- `Medal-of-Honor-vr\docs\FAILURE_REGISTRY.md` (with `HYPOTHESES.md` carrying the discriminators)
- SOMAVR keeps its failures inline in `BUILD_HISTORY.md` and `HYPOTHESES.md`

Distilled lessons from all of them live in `cross-engine-graph\harvest\*.md` — roughly 200 lessons, of
which only the generalisable ones reached these chapters. If a chapter feels thin on your specific
problem, the raw harvest is worth a look before starting fresh.
