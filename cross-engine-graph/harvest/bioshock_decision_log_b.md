# BioshockVR — DECISION_LOG harvest (lines 1800-end)
Lines read: 1800-3642

### Validate a reverse-engineered matrix with a numeric self-consistency residual, not a "looks plausible" bound
**What happened:** BioShockVR derived a per-draw camera projection `P_center` from live VS constants `screenDataToCamera` (`c3=[2.383507,0,-1.191754,0]`, `c4=[0,-1.340723,0.670361,0]`, implying ~100° h-FOV), validated by checking that `oldWVP * P_center^-1` is affine (near-identity last row/column). The early gate `StereoWorldProjectionAffineMaxMilli=250000` (residual limit 250.0) was loose enough to let a wrong guessed 75° FOV "pass" and produce large per-object displacement (`0.3.58`). Tightening to `1000` (limit 1.0) correctly rejected it (residual ~96.65) and the screen-data-derived projection then landed near zero.
**Why it generalises:** any engine where a projection/view matrix is reconstructed from disassembly or captured shader constants needs a tight numeric falsification test — a loose tolerance lets a wrong reconstruction silently pass and corrupt geometry instead of failing loudly.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "Validate a discovery by provenance, not by hope"

### Absence of runtime errors is not evidence a fix is working — check the activity counters
**What happened:** Build `0.3.78` added a PS-null mono-depth fallback; the user reported "zero shader errors," which read as success. The counters told the real story: `stereoWorldPsNullDepthOnlyMonoFallbackTotal=2134527` against `stereoWorldMatrixStereoProofAppliedTotal=1765` — the fallback had silently swallowed almost the entire native-stereo path rather than fixing the artifact.
**Why it generalises:** any pipeline with a guard/fallback branch can look clean by error count while the intended code path has been bypassed nearly completely; only per-branch application counters expose that.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Presence is not proof of loading"

### Check output-merger write masks before spending build cycles chasing a "suspect" draw
**What happened:** Builds `0.3.76` through `0.3.90` repeatedly targeted PS-null draws (`indexCount=36`, `vs0=320`, `ps0=64`) as the suspected source of red/blue clear-color holes, until artifact rows added `om=` state and showed `rt0WriteMask=0x0`, `depthWriteMask=0` — those draws wrote nothing to color or depth and physically could not be the visible artifact.
**Why it generalises:** every D3D/GL/Vulkan pipeline exposes per-target write masks; checking them is nearly free and immediately rules a draw in or out as visually responsible before mutating it.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Attribute by ownership before shader identity"

### Conjugate the eye transform through the real projection; don't slide clip-space pixels
**What happened:** `0.3.57` shifted clip space directly (`clip.x += eyeShift * clip.w`) — a constant NDC offset that cannot produce depth-varying parallax. `0.3.58` replaced it with `P_center^-1 * T_eye * P_center` applied to the cloned WVP, validated by the affine-residual gate above.
**Why it generalises:** confirms the existing rule on a second engine (UE2.5/D3D11) and adds the concrete remediation — the matrix form to use, and an empirical way (the residual gate) to confirm the row/column-vector and pre/post-multiply convention instead of guessing it.
**Chapter:** 09-d3d11-openxr-injection.md
**Status:** SHARPENS "Stereo math: translate in view space, not by sliding clip-space pixels"

### A screen-space resource fix must be scoped to the exact resource-and-draw-shape proven responsible, not the whole resource class
**What happened:** Black eye-dependent shading on rocks traced (via RenderDoc) to `s_shadowMask`, a texture sampled by screen position in PS slot 2 — generated once for the mono/center view, so per-eye geometry shifted the sample UV out of alignment. A blind full-slot-2 mono substitution (`0.3.67`) regressed unrelated materials; the fix that actually worked (`0.3.72`) required both `SlotMask=4` AND `MinIndexCount=18000`, matching only the large boulder draws.
**Why it generalises:** the render-pass-hazard pattern (mono buffer sampled by screen position, broken by per-eye geometry) recurs in any deferred/screen-space technique; the fix must key on the narrowest proven predicate, not the resource type alone.
**Chapter:** 14-render-pass-hazard-atlas.md
**Status:** SHARPENS "Sub-resolution passes need per-eye company"

### Key mutation predicates to exact shader/resource identity, not a coarse structural bucket
**What happened:** Demoting an entire draw "family" (`StereoWorldScreenSpaceSrvFallbackIndexedPrimitive=1`, all indexed-primitive draws) regressed boulder/chest shading and worsened poster-frame holes; it was reverted the same day. The fix that held (`0.3.99`-`0.3.101`) grouped by exact `shaderSignature=`/`resourceSignature=` and exact index-count + slot-mask lists instead.
**Why it generalises:** in any engine with many shader/material permutations sharing a coarse bucket (draw type, buffer size, route family), a fix keyed to the bucket overshoots; key mutation predicates to the narrowest identity that reproduces in evidence.
**Chapter:** 14-render-pass-hazard-atlas.md
**Status:** NEW

### Bounded diagnostic/proof budgets need an explicit exhaustion signal, or "budget hit" reads as "feature broken"
**What happened:** Multiple proof caps (`stereoWorldMatrixStereoProofAppliedTotal` plateauing at `4096`; an earlier shared budget for `stereo_world_mutation_clone_bind` consumed entirely by `reason="pose_not_ready"` skip rows) silently fell back to mono/solid output mid-run, which looked like a regression rather than "the test window ended." Each time cost a diagnostic cycle to distinguish cap-hit from real failure.
**Why it generalises:** any bounded instrumentation or proof budget in a live system needs a distinct "budget exhausted" telemetry state, or engineers will debug a healthy-but-capped system as if it were broken.
**Chapter:** 08-project-process.md
**Status:** SHARPENS "A self-consistent instrument can be consistently wrong"

### Before shipping a new build, read back the runtime's own config echo — don't assume the INI took
**What happened:** A `0.3.32` log showed the expected proof route inactive. Instead of building `0.3.33`, the team read the logged `hook_config` and found `stereoWorldPoseProof=0`/`stereoWorldWideProof=0` — the INI simply had not been updated. They fixed the INI and reran the same DLL. This pattern recurs more than once in the range.
**Why it generalises:** any injected/DLL-based mod risks conflating "feature doesn't work" with "feature was never armed"; always verify the runtime's own config dump before writing new code.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Config-system rigor"

### Wire one explicit trigger between independent diagnostic subsystems that must capture the same moment
**What happened:** A user hotkey (Ctrl+F10) armed the D3D-side artifact probe, but the separate OpenXR eye-texture BMP dumper had its own poll-based arm that frequently missed the same keypress (D3D saw 11 arms / 8448 rows; the OpenXR blit poll saw only 2 arms / 24 BMPs). The fix (`0.3.87`) made the D3D arm call the OpenXR arm directly (`ArmEyeBlitDebugDump`) instead of relying on two independent pollers to observe the same transient input.
**Why it generalises:** whenever two independently-polled diagnostic subsystems must capture the same instant, chain one explicit call between them — don't trust both loops to see the same short-lived signal.
**Chapter:** 06-debugging-methodology.md
**Status:** NEW

### Capture broadly at the moment of the defect; don't ask the user to relocate it after a rebuild
**What happened:** Early attribution asked the user to notice an artifact, then re-aim at it after a build to isolate the offending draw ("F11 solo") — too brittle, because per-frame camera/culling/object state doesn't reproduce identically between sessions. The working replacement (`0.3.97`) instead ranked candidates against the rows already captured inside the same Ctrl+F10 window, since those are the only rows guaranteed to reflect the exact state the user was looking at.
**Why it generalises:** in any live, camera-driven renderer, "capture broadly the moment the defect is seen, then mine offline" beats "ask the tester to relocate the defect later," because scene/culling state is not reproducible on demand.
**Chapter:** 06-debugging-methodology.md
**Status:** NEW

### Linearize hardware depth before deriving distance-based weights or disparity
**What happened:** An early screen-space disparity pass used `one_minus_raw` on the raw D3D24 depth buffer, which saturates non-linearly toward 1.0, spending almost all disparity range on near objects while mid/far geometry stayed flat. Switching to a linearized inverse-Z response (view-space distance, `1 - convergence/z`, with convergence=2500mm, near=100mm, far=1,000,000mm) gave near/mid/far ranges distinct, usable separation.
**Why it generalises:** any technique sampling a hardware depth buffer for screen-space work (SSAO, fog, reprojection, cheap parallax) must linearize first — raw D3D/GL depth is not linear in view-space distance, on any engine.
**Chapter:** 10-graphics-apis.md
**Status:** NEW
