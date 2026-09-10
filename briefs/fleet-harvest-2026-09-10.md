# Fleet research harvest — 2026-09-10

## Scope and evidence boundary

This is a selective harvest of the latest submitted findings, not a fresh acceptance
test of ten games or an exhaustive source review. Twenty intake packets from six
projects were validated against their original project-owned receipts and artifact
SHA-256 hashes. All twenty were intact at review. Key reports, raw probe output,
static contracts and capture summaries were inspected; not every artifact was read
end to end. No game was launched or instrumented for this harvest.

The Prey card correction received an additional independent check: all 112 recorded
crop hashes were recomputed from the saved images and matched. That supports the
saved-pixel claim, not human readability on a headset. Other runtime results below
are reviews of project receipts, not newly performed runtime experiments.

`LIVE` always retains its environment: harness, substitute-runtime in-game, and
headset are not interchangeable. Acceptance here means editorial acceptance of a
scoped lesson, **not** acceptance of a build or promotion of its evidence grade.
Earlier defects are historical counterexamples where a later candidate repairs them.
Baseline FAIL and REFUTE receipts remain visible; their fields were not rewritten.

The source ledger keeps earlier whole-tree review fingerprints deliberately: this
harvest does not certify all areas of a changed checkout as re-reviewed. New scoped
area notes, bottleneck corrections and the receipts below identify what was examined.
No achieved completeness tier or stereo rung was raised from harness/code evidence.

## Accepted receipt-to-recipe map

IDs below are the intake filename without `.json`; original receipts and raw evidence
remain in the named project. Local editorial decisions are under
`research-inbox/reviews/`. Intake and decisions are gitignored; this digest and the
canonical recipes are the portable audit record.

| Submission | Distilled finding / canonical destination | Limit retained |
|---|---|---|
| FarCry2-vr__20260910-arm-deform-01 | [Coherent arm pivots](../docs/02-viewmodels-and-hands.md#coherent-arm-pivots): solve the endpoint after accounting for pivot translation | LIVE harness; fresh-pivot scheduling and right-side weights are not accepted in-game |
| Medal-of-Honor-vr__20260909-frame-review-01 | [Input independent of rendering](../docs/09-d3d11-openxr-injection.md#input-independent-of-render): skipped render must not preserve stale actions | LIVE harness of reviewed candidate; subsequent repairs/features need their own engine regression |
| PreyVR__20260909-build-takeover-near-fov | [Override after the real latch](../docs/11-re-anchoring-and-discovery.md#override-after-latch) | STATIC ordering, not a new hardware result; physics environment receiver does not prove query ABI |
| PreyVR__20260909-equip-alignment-hud-scale | [Authored weapon basis](../docs/02-viewmodels-and-hands.md#authored-weapon-basis) and [native HUD ownership](../docs/04-ui-and-hud.md#single-native-hud-draw) | STATIC equip correction; sizing is not extraction, and a fixed callback delay cannot recover an authored basis |
| PreyVR__20260909-ik-crosstalk-anchor | [Aim-dependent hand anchor](../docs/02-viewmodels-and-hands.md#aim-dependent-hand-anchor) | STATIC/source feedback path; its runtime contribution is not isolated by that receipt |
| PreyVR__20260909-performance-instrument-audit | [Timing populations](../docs/19-d3d12-and-performance.md#timing-population) | LIVE harness; no compositor-miss or missing-raw-trace optimization claim |
| PreyVR__20260909-vee-weapon-collision-review | [Weapon query coverage](../docs/02-viewmodels-and-hands.md#weapon-query-coverage) | SOURCE camera-ray pullback is not a tracked-weapon volume or firing veto |
| PreyVR__20260909-weapon-basis-alignment | [Authored weapon basis](../docs/02-viewmodels-and-hands.md#authored-weapon-basis) | STATIC fixtures; later raw-slice evidence corrects the resolver's memory assumption |
| PreyVR__20260910-native-hud-layer | [Single native HUD draw](../docs/04-ui-and-hud.md#single-native-hud-draw) | LIVE in-game on private validation runtime; original baseline FAIL remains recorded, later card interpretation corrected separately |
| PreyVR__20260910-pose-slice-correction | [Slice owner and count](../docs/11-re-anchoring-and-discovery.md#slice-owner-count) | LIVE in-game REFUTE of prefixed allocation; true dynamic arrays elsewhere are unchanged |
| PreyVR__20260910-ui-card-pixel-correction | [Saved pixel correction](../docs/06-debugging-methodology.md#saved-pixel-correction) | LIVE in-game REFUTE; matched layout/eye/alpha groups, not arbitrary whole-image equality |
| PreyVR__20260910-ui-pointer-contract | [Native pointer receiver](../docs/04-ui-and-hud.md#native-pointer-receiver) | STATIC receiver, adjustor and mode contract; not live cursor/click acceptance |
| Sims4VR__20260909-review-geometry | [Geometry assertions](../docs/09-d3d11-openxr-injection.md#write-these-assertions-now-not-after-the-first-headset-session) | LIVE harness REFUTE of the checker; neutral symmetric fixtures remain useful when explicitly scoped |
| Sims4VR__20260910-native-m1 | [Completed-draw/owner-thread transaction](../docs/09-d3d11-openxr-injection.md#completed-draw-transaction) | LIVE in-game flat quad, not scene stereo; final/earlier DLLs and host/retail traces remain distinct |
| ss2vr-work__20260909-native-merge-review | [Shared native features](../docs/kex-dark-native-stereo.md#shared-native-features) | SOURCE branch review; an engineering spike is not a production merge recommendation |
| ss2vr-work__20260909-native-srgb-sim | [Shared native features](../docs/kex-dark-native-stereo.md#shared-native-features) | LIVE in-game v3.102 simulator receipt; correct transfer representation is not hardware colour acceptance |
| ss2vr-work__20260910-native-shared-features | [Shared native features](../docs/kex-dark-native-stereo.md#shared-native-features) | LIVE in-game v3.104/v3.105 bounded pairs and recovery; protected shipping baseline remains separate |
| Swat4-VR__20260909-openxr-frame-ownership-fixes | [Completed-draw transaction](../docs/09-d3d11-openxr-injection.md#completed-draw-transaction) | LIVE in-game 4ddb candidate; format harness, runtime trace and full side-effect acceptance are separate |
| Swat4-VR__20260909-openxr-release-review | [Completed-draw transaction](../docs/09-d3d11-openxr-injection.md#completed-draw-transaction) | LIVE harness historical counterexamples: failed acquire/wait, loss, disarm and partial retry |
| Swat4-VR__20260910-motion-weapons-01 | [Script-call consumer](../docs/03-input-and-locomotion.md#script-call-consumer) and [coherent pivots](../docs/02-viewmodels-and-hands.md#coherent-arm-pivots) | LIVE in-game d817 candidate: native shots/ammo and hand/head independence; no hardware/all-weapon acceptance |

## Fleet screening and superseding state

All ten fleet entries were screened using current project documentation and recent
history. No finding was invented to make coverage look even.

| Project | Additional current-state check |
|---|---|
| SS2VR | Native experimental v3.102–v3.105 receipts remain separate from the HEADSET-graded shipping route; shared input/UI must not introduce another frame owner. |
| BioShockVR | Current-state document dated September 3; no new intake packet in this batch. Existing render/performance bottlenecks retained; standing launch restrictions respected. |
| SOMAVR | September 9 interaction follow-through report and source/test result: manipulation position and velocity need the same gain; body-attached handles and bounded action ownership are distinct. Added [manipulation feedback](../docs/02-viewmodels-and-hands.md#manipulation-feedback). SOURCE/harness, not newly accepted headset feel. |
| PreyVR | Ten packets; later pose-slice and saved-card-pixel corrections supersede earlier interpretations. Private xr-sim fixes are version-local, not claims about every installed runtime. |
| DishonoredVR | No new intake packet; current-state prose contains older camera/launch-status tension. Do not resolve it by assertion or change acceptance grades without fresh receipts. |
| FarCry2-VR | A later twist candidate exists beyond the arm receipt. Its no-XR splash attempt produced no swapchain; it is not arm acceptance or proof of a crash. Active D3D9 versus D3D10 must be established per launch. |
| SWAT4-VR | 4ddb transport and d817 motion work are different candidates. The transport trace has 1315 distinct projections; three generic-checker failures require named contract explanations, not conversion to a universal pass. |
| Sims4VR | Native M1 on retail 1.127.41.1030 supersedes “no native mod/host.” Earlier DLL covers loaded-lot/resize cases; final f064c6 covers 405 retail quads and owner-thread shutdown. Old 1.126 camera findings need revalidation. |
| SoF-VR | September 9 current-state report advances reversible single-view M3. M4 is built but unrun. The verified zero-delta writeback check does not establish nonzero-shift safety; second-view and XR transport gates stay open. No new intake packet. |
| MoH-VR | September 10 `docs/reviews/FEATURES-20260910.md` supersedes “input not started”: repaired feature candidate reports 162 standalone checks. No new successful engine/headset acceptance in that report; stale old qconsole output is explicitly excluded. |

## What changed in the playbook

- Technical methods live in their owning chapters, not duplicated in a new summary chapter.
- Thirteen failure routes (`FAIL-HAND-048`–`051`, `FAIL-RE-034`, `FAIL-TEST-037`–`038`,
  `FAIL-XR-027`–`028`, `FAIL-INPUT-025`–`026`, `FAIL-PERF-021`, `FAIL-HUD-014`) plus
  twelve short symptom routes make the findings discoverable.
- Chapter 09's own world-axis stereo assertions and held-input refocus wording were
  corrected in place, rather than adding a warning that contradicted them elsewhere.
- Source coverage and fleet focus notes were updated without clearing broad bottlenecks
  or re-fingerprinting whole projects from a narrow receipt review.
- The fleet graph remains a September 7 discovery snapshot. It was not rebuilt or
  treated as evidence for September 9–10 work. A missing graph hit is not a missing solve.

Validation is performed using `python tools/verify.py` after regenerating the source
and bottleneck views. Publication is user-operated; this harvest does not itself push
to GitHub or publish the local external archive.

### Validation outcome

An initial full run passed all ten checks. After final routing/formatting edits,
two full reruns passed nine checks, including 28 reference tests / 95,559 assertions,
integration regression tests, retrieval integrity (144 patterns / 361 failures),
all ten project instruction pairs, strict site build and 844 internal links.
Rendered HTML was also checked: the new failure entries are real table cells.

The remaining source-coverage freshness check failed because the sibling Prey tree
changed between generation and checking (142,591 to 142,592 measured files and a
different tree fingerprint). This is an unresolved moving-snapshot warning, not a
passing final full check. No active research was interrupted and no freshness check
was disabled. Regenerate `tools/coverage.py` before committing; a stable full pass
requires the measured source trees to remain unchanged through `tools/verify.py`.
