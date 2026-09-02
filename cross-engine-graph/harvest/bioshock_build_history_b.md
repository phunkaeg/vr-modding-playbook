# BioshockVR — BUILD_HISTORY harvest (lines 1000-end)
Lines read: 1000-2096

### A "fix" that makes the symptom disappear by disabling the feature is not a fix
**What happened:** `0.3.76-psnulldepthskip` broadly skipped private-eye replay for any PS-null draw and starved the stereo source entirely (`source=solid` dominant, `stereoWorldFullPassMonoAccumulationAppliedTotal=0`). The narrower follow-up `0.3.78-psnullmonodepth` still over-caught: `stereoWorldPsNullDepthOnlyMonoFallbackTotal=2134527` against only `stereoWorldMatrixStereoProofAppliedTotal=1765`. The user reported "no shader errors" — because almost nothing was rendering stereo anymore, not because the artifact was solved.
**Why it generalises:** Any predicate-gated workaround (skip/demote/fallback) can "succeed" by suppressing the feature under test rather than fixing it. Always cross-check a visual-success report against the applied/attempted ratio for the mechanism you're testing, not just absence of errors.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Falsify your own hypothesis before shipping a fix"

### Mixing two projection bases in one frame produces phantom/mirrored geometry, not just misalignment
**What happened:** `0.3.105-frustumlock`: draws that got native per-eye XR-FOV projection and draws that fell back to mono under the old center-camera projection landed at different angular frames in the same private eye target — 278 `xr_fov` rows vs 194 `center_projection` rows in one sampled frame — producing "2D phantoms" left/right of real geometry. The fix was an all-or-nothing rule: mono-fallback draws are remapped into the same eye sub-frustum via viewport, never left in the old center frustum.
**Why it generalises:** Once any draws in a frame use a per-eye frustum, every draw sharing that render target must be re-expressed in that same frustum — full-stereo and fallback/mono paths cannot silently coexist on different projection bases without producing doubled/mirrored geometry.
**Chapter:** 09-d3d11-openxr-injection.md
**Status:** SHARPENS "Projection companions must remain coherent"

### A mono screen-space buffer sampled with per-eye UV shows as geometry-shaped shading errors, not just a flat pass
**What happened:** RenderDoc on `BS4_wrench.rdc` showed a black-boulder artifact was a PS slot-2 sample of `s_shadowMask` (target-sized `R8G8B8A8_UNORM`) using screen UV derived from the *per-eye* `worldViewProj`. The mask itself stayed mono/center-eye, so the black side tracked the eye shift (`0.3.67-shadowmaskab`). A blunt "replace with white SRV" A/B (still `0.3.67`) made boulders uniformly darker without fixing edges — confirming the mask, not lighting, was the culprit, before the real fix (per-family screen-space fallback) arrived.
**Why it generalises:** A shading defect that moves with the eye/camera, rather than staying fixed on the surface, is diagnostic of a screen-space buffer generated once (mono) but sampled per-eye — this signature is engine-agnostic (shadow masks, SSAO, SSR are all typical culprits).
**Chapter:** 09-d3d11-openxr-injection.md
**Status:** SHARPENS "Mono screen-space buffers are a separate stereo problem"

### A stereo/mono compare instrument must be quarantined from unrelated experimental knobs
**What happened:** `0.3.83-fallbackdepthab` introduced a mono-fallback depth-write experiment that regressed the scene (suitcases translucent, a boulder vanished). The existing Ctrl+F9 stereo/mono compare hotkey inherited that experimental depth override, so toggling to "mono" no longer gave a clean baseline. `0.3.84-compareguard` fixed it by adding `EffectiveMonoFallbackDepthMode()`, which forces mode `0` whenever mono-compare is active, regardless of the configured experiment.
**Why it generalises:** A comparison tool only proves anything if it isolates the one variable under test. Any in-headset A/B hotkey needs its own code path that suppresses every other live experiment, or it silently becomes an uncontrolled comparison.
**Chapter:** 08-project-process.md
**Status:** SHARPENS "A self-consistent instrument can be consistently wrong"

### When a heuristic predicate causes collateral regressions, add a discriminating field — don't widen or abandon it
**What happened:** The screen-space-SRV mono-fallback predicate went through five narrowing passes to stop regressing architecture while still catching the boulder/paper class: `0.3.71` any target-sized SRV in PS slots 0-7 → `0.3.72` restricted to slot mask `4` + `indexCount>=18000` → `0.3.92` bounded to a min/max index range → `0.3.98` per-route-family selectors (indexed-primitive alone still regressed broadly and was reverted) → `0.3.100`/`0.3.101` exact per-draw index-count allowlists (`1542,2508,5412,...`) plus a separate BSP-specific slot mask (`0x18`) and index list.
**Why it generalises:** Broad classifier-driven fallbacks in a render pipeline nearly always overfire on some other draw class. The fix is progressively more specific discriminating fields (resource slot, size range, draw family, exact identity) — not a binary broaden/abandon choice.
**Chapter:** 06-debugging-methodology.md
**Status:** NEW

### Pre-commit an INI-only revert condition so a regression never needs a rebuild
**What happened:** `0.3.98-srvfamily` documented its falsification/regression criteria in advance ("if broad regression, revert with `StereoWorldScreenSpaceSrvFallbackIndexedPrimitive=0`"). When the indexed-primitive selector did regress broadly (poster/frame, boulder/chest, tall stones, small rubble), the team reverted purely via the active INI and shipped no new DLL — the next entry says explicitly "No new DLL was built for this revert."
**Why it generalises:** Writing the rollback lever into the same config surface as the experiment (not just a git revert) turns a regression from a lost test cycle into a five-second recovery, and keeps the build/test loop from becoming the bottleneck on every risky change.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Everything default-off, behind a knob"

### Solid sentinel colors plus source-state counters triage "nothing arrived" vs "wrong thing arrived" instantly
**What happened:** `0.3.60-pcenterfitprobe`: the HMD showed only cyan/yellow proof colors. Instead of assuming an OpenXR failure, the counters (`source=solid`, `privateSourceReady=0`, `privateSourceCopies=0`) immediately proved this was private-eye-source starvation caused by an overly strict matrix-only gate, not a compositor or OpenXR bug — diagnosed without a debugger session.
**Why it generalises:** Pairing a fixed, unmistakable debug clear color with an explicit "what filled this target" counter (solid vs. real source) lets you distinguish a starved pipeline stage from a corrupted one at a glance, across any injected-rendering project.
**Chapter:** 09-d3d11-openxr-injection.md
**Status:** SHARPENS "Diagnostics that work inside a headset"

### Independent hotkey pollers on different pipeline stages desync — arm the second stage explicitly from the first
**What happened:** `0.3.86` showed the D3D-side artifact-probe hotkey armed 11 times and produced 8448 rows, while the OpenXR-side eye-BMP dumper (polling the same Ctrl+F10 independently, at a different point in the frame) armed only twice and wrote 24 BMPs — log evidence with no matching screenshot. `0.3.87-dumpsync` fixed it by adding `ArmEyeBlitDebugDump(frame, source)` so the D3D probe explicitly mirrors its arm into the OpenXR dumper instead of both polling the key separately.
**Why it generalises:** When instrumentation lives in two different hooked stages (e.g. draw submission vs. present/compositor), independently debouncing the same hotkey in each stage will drift out of sync under frame-time jitter. One stage should own the trigger and explicitly call into the other.
**Chapter:** 13-teardown-bioshock-vr.md
**Status:** SHARPENS "Build your own in-process frame inspector"

### When static RE dead-ends on obfuscated/packed data, a live scan of a known-changing value is the fast path
**What happened:** Camera RE hit a wall: `FCameraSceneNode`/`FPlayerSceneNode` RTTI descriptors were located (`0x11afb884`/`0x11afec2c`) but had no resolved xrefs, and no `FOV`/`HorizontalFOV` strings existed anywhere because UnrealScript stores them in packed property tables, not ASCII. The documented next step was abandoning static disassembly in favor of a live Cheat Engine float-scan anchored on the in-game FOV slider's visible value change.
**Why it generalises:** Engines that store metadata in packed/reflected tables (common in UObject-style reflection systems) can make string/xref search a dead end even with full RTTI. A live differential scan on a value you can change from the UI sidesteps the entire static problem.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "The engine's own debug commands are a validation oracle"

### An exhaustive candidate-window scan finds a data layout that moved from where you assumed it was
**What happened:** The compact 320-byte VS constant buffer's WVP matrix was assumed to live at `c0-c3`. Several builds (`0.3.66` through `0.3.85`) failed to matrix-stereo those rows on that assumption. `0.3.85-fallbackfitprobe` added `vs_compactMatrixCandidateScan=`, testing every 4-row window from `c0` through `c16` against the projection-fit affine residual; it found the real WVP at `c10-c13`. `0.3.86-compactc10apply` promoted only that confirmed offset and compact-lane fallbacks dropped immediately.
**Why it generalises:** When a fixed-offset assumption about a data layout keeps silently failing validation, don't keep re-testing the same offset with different logic — brute-force scan the plausible offset range against your existing correctness gate (here, the affine residual check) and let the data pick the winner.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "Signature-scan the data, not just the code"

### Dump every intermediate stage, paired, to localize which stage actually introduces a visual defect
**What happened:** `0.3.89-depthpairdump` added synchronized BMP dumps of the private-eye color buffer, the private-eye depth buffer, and the final post-blit OpenXR eye texture, all from the same hotkey press. Comparing them showed the poster/paper/curved-architecture holes were already present in the private-eye *color* dump — proving the final OpenXR blit stage was not the cause, redirecting investigation to mono-fallback color/depth pairing instead of another blit-stage theory.
**Why it generalises:** A visual defect visible only in the final composited output is ambiguous about which of N pipeline stages introduced it. Capturing every stage at the same instant turns "which stage is broken" from a guess into a direct comparison.
**Chapter:** 06-debugging-methodology.md
**Status:** NEW

### Gate synthetic input injection to frames where the target system is actually active, and give it an explicit reset
**What happened:** Head-aim tracking (`0.3.105-frustumlock`) injects relative mouse counts via `SendInput` to drive the engine's native camera, but only on frames with live world draws — and it ships with a dedicated `Ctrl+F7` recenter hotkey plus bounded `head_aim_recenter`/`head_aim_injection` log rows, because raw delta-tracking without a reset accumulates drift.
**Why it generalises:** A synthetic input stream competing with (or standing in for) real input needs its own presence gate — tied to when the driven system is actually live, not just "always on" — plus an explicit, logged way to zero its accumulated state, matching the pattern of treating a synthetic controller's presence as its own lane.
**Chapter:** 03-input-and-locomotion.md
**Status:** SHARPENS "A synthetic controller's presence is a lane too (rung 3 gotcha)"
