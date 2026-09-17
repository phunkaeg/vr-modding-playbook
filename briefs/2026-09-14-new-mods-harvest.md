# September 14 external-mod harvest and fleet relevance

## Outcome

Three previously untracked checkouts were analysed: **MGS5VR, KHARVOX and
titanfall2vr**. Nine approach-level findings are now distilled into six technical
chapters, including corroboration of the existing crop/FOV rule. Six new failure
rows and symptom routes make the additions findable. `sources.yml` records the
scope of review and pins each donor; unreviewed areas remain explicit.

The highest immediate value is **MGS5VR's arm/twist separation for FarCry2-VR**,
**its crop and panel geometry for PreyVR**, and **the ownership/endurance checks
for projects progressing from image transport to repeated scene rendering**.
These are candidate methods, not evidence that any fleet defect has been fixed.

## Scope and provenance

| Local checkout under `D:/Dev Debug/Other VR Mods` | Reviewed commit | Character of the useful material |
|---|---|---|
| MGS5VR | `a51c4b9660f18addc71f06208fcd357d5ad58b15` | FOX/D3D11 native injector; source-backed capture transactions, optics, panels and authored arm corrections |
| KHARVOX | `e2e15d603ae7bfa45b05424b88207179e903670e` | DOOM 2016/Vulkan; alternate-eye caches, explicit replay contracts and bounded streaming writes |
| titanfall2vr | `8c50a7d491d9a275103cfc659430e4bc1b75a608` | Respawn Source-derived/D3D11, Northstar-hosted native plugin; useful failed re-entry experiments and viewport classification |

All three donor working trees were clean when inspected. `vrframework` was also a
recent arrival, but already covered by the September 10 comparison; it was not
counted or harvested again. This was a targeted implementation review, not a claim
to have audited every line of all three repositories.

Evidence is **SOURCE** for implementations read. Donor runtime anecdotes and
wearer compatibility remain **AUTHOR** unless independently supported. The new
52-check executable is **LIVE, standalone CPU harness only**: no game, graphics
driver, OpenXR session or headset was exercised. No donor tier/rung was inferred
from marketing/version labels. KHARVOX recommends AER and calls native stereo
experimental; Titanfall2VR explicitly disables its same-frame experiment.

The [evidence folder](evidence/2026-09-14-external-mods/README.md) contains the
test source, invocation and source fingerprints. Canonical chapter sections carry
pinned upstream file links; local source trees retain the full implementations.

## What changed in the playbook

| Finding | Previous coverage → additional value | Canonical destination |
|---|---|---|
| Deferred eye-copy execution | Completed draw/pair publication already covered → distinguish recording, command-list execution and GPU completion | [ch09: deferred execution](../docs/09-d3d11-openxr-injection.md#deferred-eye-execution), FAIL-STR-058 |
| Integer crop/FOV agreement | Already taught from Witcher3 → actual MGS5VR helper plus even/odd resolution and invalid-input tests | [ch09: subimage/FOV](../docs/09-d3d11-openxr-injection.md#subimage-fov-pair) |
| Wrong viewport provenance | Correct optics cannot repair the wrong pass association → tiny startup viewport example and explicit unknown-size limitation | [ch09: world rectangle](../docs/09-d3d11-openxr-injection.md#world-rect-provenance), FAIL-STR-059 |
| Hinge versus skin twist | Endpoint/deform-chain problem already known → authored-basis implementation separating pronation, plus length-preserving elbow clearance | [ch02: hinge/twist](../docs/02-viewmodels-and-hands.md#hinge-versus-twist); complements existing FAIL-HAND-013 |
| Binocular panel fitting | Spatial panels already covered → all corners in both posed frusta; move the panel without shrinking text | [ch04: binocular fit](../docs/04-ui-and-hud.md#binocular-panel-fit), FAIL-HUD-015 |
| Original replay inputs and typed retirement | Lifecycle/aliasing already covered → seed before the first destructive pass; CPU recording and GPU completion are separate gates | [ch10: replay inputs/retirement](../docs/10-graphics-apis.md#replay-input-retirement) |
| Pair state across workers and turns | Per-eye history already covered → entity/stage-plus-serial cache and per-cached-eye snap generation | [ch14: pair identity](../docs/14-render-pass-hazard-atlas.md#pair-cache-identity), FAIL-STR-061 |
| Bounded streaming append | Fixed-buffer overruns already known → preserve backlog while respecting destination capacity, with actual boundary tests | [ch14: streaming bound](../docs/14-render-pass-hazard-atlas.md#bounded-streaming-append), FAIL-RND-002 |
| Re-entry endurance | Side-effect gate already covered → short diagnostic bursts can all pass below a documented failure horizon | [ch17: endurance](../docs/17-teardown-fc2vr-native-stereo.md#reentry-endurance), FAIL-STR-060 |

## Relevance to the current fleet

This is a **September 14 documentation-based comparison**, not fresh runtime
validation. Project-owned current-state notes were read instead of relying on the
September 7 graph snapshot. Unless specified otherwise, the source for each row is
`<project>/docs/CURRENT_STATE.md` under `D:/Dev Debug`; the evidence manifest pins
those documents. The priorities below are inference from that state and donor
source, not a promotion of project milestones.

| Project | Current relevant position in its own notes | Best use / cheapest next proof |
|---|---|---|
| **FarCry2-VR — high** | September 10 default-off arm/twist candidate has offline checks, but right deform identity and rendered-arm acceptance remain open | Compare MGS5VR's authored hinge/twist division with the existing residual-palm-roll approach. Hold endpoint/grip/weapon fixed; first prove which target channels deform the sleeve. Then compare twist off/on at neutral, pronated and bent-elbow poses. Do not import FOX indices or weights, or replace the stereo route. |
| **PreyVR — high** | September 13 inventory controls show planar binocular disparity, not internal 6DoF UI. Launcher aspect/vertical coverage is also under active correction | Apply crop-to-ray identity tests only where subimages are used; separately measure rendered coverage. Use binocular panel fitting for spatial UI experiments. Test both corners/eyes, odd resolutions and menu transitions, then headset readability. These donors do not prove the proposed launcher resolution fixes the reported border. |
| **BioShockVR — high ownership relevance** | September 3 notes identify process-termination failure in shadow-mask teardown/CRT destruction, plus replay cost | Audit the actual destructor/explicit-unload owners before more rendering changes. KHARVOX supplies a useful typed-retirement checklist, not a fix for a C++/loader-lock deadlock. Prove stop, explicit unload and process exit independently; a deferred queue alone cannot make destructor work safe. Source state may be older than subsequent unrecorded work. |
| **Sims4VR — high for next stereo stage** | Native M1 transports game imagery on a quad and has owner-thread shutdown evidence; this is not scene stereo | Carry source-frame/eye/activation identity into M2, with recorded-versus-executed capture controls where D3D11 deferred work exists. Establish distinct raster and one simulation advance before sustained re-entry. No “quad works, therefore scene stereo works” promotion. |
| **SoF-VR — high for next proof** | M3 single-view displacement is documented; M4 is built, not run, and 32-bit XR remains a separate gate | Use Titanfall2VR's two-stage re-entry acceptance: small zero-separation double-draw control, then reuse/endurance/transition checks. Translate the ownership invariant to OpenGL; D3D11 hooks are not reusable code here. |
| **SWAT4-VR — medium/high validation value** | Current notes retain paired in-game simulator transport and bounded motion-weapon tests; physical calibration and the complete side-effect gate remain unfinished | Strengthen endurance and image/pose provenance controls without repeating the already-passed transport milestone. MGS5VR arm/panel methods are later calibration leads. D3D9/9On12 needs its own copy/queue semantics, not donor D3D11 assumptions. |
| **SS2VR — medium, incremental** | September 13 notes include weapon-inertia changes and further interaction/pose work; new branches still require their own acceptance | Review entity/weapon/activation reset identity and preservation of the raw gameplay ray while smoothing or correcting the visible model. Use original-input/per-eye lifetime checks for future history-dependent rendering work. Existing physical-grip/reload prior art remains more directly relevant than migrating to a donor framework. |
| **SOMAVR — medium, later ergonomics** | September 10 hands-bootstrap candidate and earlier manipulation changes still need relevant runtime/headset acceptance | First accept the existing native receiver/bootstrap. Then reuse fixed-length arm and binocular panel tests if those symptoms appear. HPL3/OpenGL does not gain a direct Vulkan implementation from KHARVOX. |
| **MoH-VR — medium, source-owned route** | Source-owned fork has flat-training controls; current VR feature candidate still needs stereo/controller acceptance, including doorway lean | Put pair identity, resource lifetime and panel geometry in engine-owned APIs/tests directly. No need to copy an injector's discovery or binary-hook scaffolding. Preserve the flat baseline while testing the VR candidate. |
| **DishonoredVR — conditional** | Current-state document mixes completed camera-stage language with older no-injection/session-pending language | Resolve the baseline from latest authoritative receipts before selecting a donor recipe. Viewport provenance and repeat-render guards are good prospective tests; this harvest does not claim a working stereo milestone or choose a new architecture from conflicting summaries. |

Prey sources are `docs/INVENTORY-STEREO-LIVE-2026-09-13.md` and
`docs/LAUNCHER-RESOLUTION-FIX-2026-09-13.md`. BioShock's entry point also points to
`docs/NEXT_CHAT_HANDOVER.md`; the teardown issue is stated in current state itself.

### Recommended order

1. **FarCry2 arm acceptance:** close the deform-channel/pixel gap before adding more
   corrective coefficients. The donor offers an implementation to compare, not a
   reason to discard the existing candidate.
2. **Prey optics/UI controls:** cheap geometry assertions alongside the current
   resolution and inventory experiments, followed by separate headset acceptance.
3. **BioShock teardown ownership:** check whether the documented failure is still
   current, then use its actual lifecycle as the repair target.
4. **Sims4, SoF and SWAT4 repeat-render acceptance:** add queue provenance and
   sustained-lifecycle checks as each project reaches the corresponding gate.

For shared bottleneck routing, these findings principally strengthen stereo
ownership/side effects, resource lifecycle, projection/coverage, hands and UI.
**No bottleneck was cleared** and no project's production code or milestone was
changed: donor knowledge is not the named exit proof on a fleet target.

## Deliberately not adopted

- No new framework migration, mechanical corpus merge or fleet-graph rebuild.
- No foreign offsets, bone indices, DOOM capacities or thumbstick/eye parity
  constants treated as portable facts.
- No recommendation to enable Titanfall2VR's disabled same-frame experiment or
  KHARVOX's experimental native replay as a shipping stereo solution.
- No automatic TAA disable, copied fatal-process policy, or “more wait time fixes
  the scheduler” conclusion.
- No claim that a GPU queue or engine lifetime was tested by the CPU harness.

## Validation

The donor-helper harness passes **52 assertions**, including positive cases and
negative controls. Repository validation results are recorded in the evidence
README after regeneration. Existing unrelated working-copy changes were preserved.
No game was launched, no fleet/donor repository was edited, and nothing was
committed or pushed.
