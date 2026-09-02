# VR Modding Playbook — architecture handoff for Claude

The playbook at `D:\Dev Debug\VR Modding` has been restructured for practical
use by a human developer or AI agent. Please treat the files named here as the
current architecture and do not collapse them back into one generic injected-
DLL workflow.

## Outcome

The playbook now has:

1. an **RE-owned route** as the primary, deepest workflow;
2. a **source-owned route** for projects that can build and ship the code owning
   the camera/render loop;
3. a **shared VR engineering spine** that owns cross-route gates, artifacts and
   exit proofs while deferring technical method to canonical chapters;
4. a generated, fleet-wide **common bottleneck system** covering every in-house
   project tracked in `sources.yml`;
5. stable links from symptoms, patterns, failures, cross-project working and
   project-process guidance into the new routes;
6. copy-ready evidence templates so projects do not invent incompatible
   authority, address, camera, experiment and render-pass schemas.

The key architectural principle is:

> With source, camera integration is a code-ownership problem. Without source,
> it is a discovery, behavioral-proof and anchoring problem. Once ownership is
> established, most VR engineering converges.

## Start here

`docs\start-new-port.md`

This is now a router for new, inherited and blocked projects. It preserves the
stable `PORT-00` through `PORT-13` entry anchors while sending route-specific
work to the correct workflow.

Its primary access question is not “does source exist?” It is:

> Can we build, modify and legally ship the exact code that owns the retail
> camera and world-render loop?

It requires an `AUTHORITY_MAP.md` that classifies each code layer as readable,
buildable, modifiable, redistributable and retail-compatible.

## RE-owned route — primary focus

`docs\reverse-engineered-route.md`

Ordered gates `RE-01` through `RE-09` cover:

- exact target/module/API/bitness fingerprinting;
- GUI/tool preflight and API-appropriate capture routing;
- deterministic loading and control sessions;
- active gameplay frame-boundary proof;
- GPU-first and CPU-first camera/projection discovery;
- matrix candidate scoring and behavioral confirmation;
- camera-consumer census, lifetime/copy/restore ownership;
- shipping anchors, signatures, pointer chains and fail-closed guards;
- first reversible mutation with zero-delta control;
- evidence-based selection of native re-entry, per-draw, AFR or reconstruction;
- the three-capture scene-reentry side-effect gate.

Important technical additions include:

- a raw-bytes-to-owner camera discovery loop;
- explicit rigid/projection validation cautions;
- an ownership-census record format;
- an `ADDRESS_REGISTRY.md` shipping schema;
- a distinction between existing repeat-render **proof** and a usable repeat-
  render **vehicle**;
- once-per-simulation, once-per-frame, once-per-eye and snapshot/restore
  assertions.

`docs\11-re-anchoring-and-discovery.md` remains the deep RE reference. The new
route is the ordered operational workflow that points into it.

## Source-owned route

`docs\source-owned-route.md`

Ordered gates `SRC-01` through `SRC-06` cover:

- untouched reproducible build and retail/asset equivalence;
- source call-graph/type/instrumentation ownership mapping;
- simulation/frame/view separation;
- immutable prepared-frame plus per-view rendering;
- a narrow runtime/engine VR integration boundary;
- source-native tests, sanitizers, profiler markers and render assertions;
- upstream, license, asset and compatibility maintenance for an engine fork;
- explicit hybrid handoff back into the RE route for every closed shipping
  layer.

An SDK, open ancestor, sibling engine, decompilation or recreation can be a
**source oracle** without being the shipping implementation. Never transfer an
address/layout/ABI to retail without independent static or live confirmation.

## Shared VR engineering spine

`docs\shared-vr-spine.md`

This owns the gate contract for `PORT-06` through `PORT-13`: order, decision
questions, required artifact and exit proof. The numbered chapters own the
algorithms, detailed rules, evidence and exceptions.

- immutable pose packet and transform ownership;
- stereo proof ladder and per-eye evidence packet;
- OpenXR lifecycle, known-color transport and recovery matrix;
- render-pass census, projection companions, culling, deferred/screen-space
  state and D3D12 replay context;
- physical input → semantic action → native game endpoint → haptic return;
- UI, panel, hand, viewmodel, aim and interaction contracts;
- fresh-frame performance, audio listener/emitter ownership and semantic
  haptics;
- compatibility, package, clean install/uninstall and declared completion.

Do not duplicate technical rules in route documents or the spine. Route pages
establish access/ownership; the spine asks what must be proven next; linked
chapters establish the canonical method. If a spine summary and chapter ever
disagree, the chapter is authoritative and the spine must be corrected.

## Copy-ready project evidence

`docs\project-evidence-templates.md`

This provides project-local templates for `PORT_BRIEF`, `AUTHORITY_MAP`,
`TARGET_PROFILE`, `TOOL_PREFLIGHT`, `ADDRESS_REGISTRY`, `CAMERA_FINDINGS`,
`OWNERSHIP_CENSUS`, experiment preregistration, `STEREO_ROUTE`,
`MUTABLE_ARRAY_CENSUS`, `RENDER_PASS_CENSUS`, `INPUT_OWNERSHIP`, bottleneck
occurrence updates and human/AI session handoff. Prefer these schemas over
creating a new incompatible format in each project.

## Mutable-array discovery addition

The FarCry2-VR project produced a live, project-backed method now harvested into
the playbook:

- `docs\11-re-anchoring-and-discovery.md#writer-census` is canonical;
- `RE-004` is the atomic writer-census plus external-effect pattern;
- `RE-003`, `RE-004` and `HAND-002` are the routed failure families;
- `MUTABLE_ARRAY_CENSUS.md` is the copy-ready receipt.

The decisive observation is that a getter census is a consumer-demand trace,
not an instance inventory. In Far Cry 2, 92,298 getter calls exposed only three
`(entity,bone)` pairs on 2/6/9-bone attachment rigs. Hooking the animator writer
for three seconds exposed contiguous 106/101/101-bone arrays. A deliberately
large poke on a 101-bone rig moved a body 0.5 m and moved its shadow; that is the
render-path proof. Its 4–5 surviving frames per second out of 60 diagnosed a
last-writer race, not a bad address.

Keep the limitations: this writer ran about 97,000 times per second and needs a
bounded allocation-free observer; the full rigs did not move the first-person
arms, so the viewmodel remains a separate path; live heap bases are receipts,
not shipping anchors. Canonical target evidence is in
`D:\Dev Debug\FarCry2-vr\docs\RE_FINDINGS.md` and
`src\dll\engine\DuniaBoneProbe.cpp`.

## Common bottleneck system

Authoritative data:

`bottlenecks.yml`

Generator/validator:

`tools\bottlenecks.py`

Human/agent page:

`docs\bottleneck-map.md`

Generated files—never edit manually:

- `docs\generated\bottleneck-matrix.md`
- `docs\generated\project-bottleneck-focus.md`

The generator imports the fleet roster from `sources.yml` and fails if any
in-house project is missing from the current-focus table.

States mean:

- `active`: current critical path;
- `open`: unresolved but not the earliest/current blocker;
- `risk`: plausible and not yet exercised;
- `cleared`: the named exit proof passed;
- `na`: demonstrated inapplicable.

A green cell does **not** mean a subsystem is perfect. It means the named
bottleneck no longer blocks the next gate.

The bottleneck classes currently cover:

- access/integration authority;
- active bytes and session identity;
- renderer/frame ownership;
- camera/projection/culling/consumer ownership;
- stereo route selection;
- repeated-pass side effects;
- graphics-to-OpenXR transport;
- per-eye render state;
- pose/frame/pair coherence;
- native input/aim/interaction;
- UI/hands/viewmodels/adaptation;
- fresh-frame performance;
- packaging/version/recovery.

Each class carries a permanent ID, controlled `applies_to` route applicability, blocked gate, fast
discriminator, exit proof, full route and per-project evidence notes.

Project-focus rows do not duplicate integration authority. The bottleneck
generator imports `authority` from `sources.yml`, so the two ledgers cannot
quietly disagree.

## In-house coverage

The generated system includes:

- SS2VR;
- BioShockVR;
- SOMAVR;
- PreyVR;
- DishonoredVR;
- FarCry2-VR;
- SWAT4-VR;
- Sims4VR as the tracked research target.

Do not manually copy their current priorities here. Read the generated project-
focus table and verify it against the cited project `CURRENT_STATE` or hypothesis
source before acting.

## Source coverage ledger

`sources.yml` remains authoritative for fleet/external identity, review depth,
evidence and freshness. A schema defect was corrected before propagation:

- fleet uses controlled `authority` values for PORT-01 shipping/integration
  ownership;
- external references use controlled `vehicle` values for delivery/build form;
- achieved `tier` is controlled separately from optional `tier_target`;
- `stereo_rung` is controlled as `unproven`, `R1`, `R2`, `R3` or `R4`;
- deprecated `mode` now fails validation instead of rendering two incompatible
  vocabularies under one column.

Generated tables therefore show **Integration authority** for fleet entries and
**Delivery vehicle** for external references. Sims4VR is recorded as achieved
`pre-T1`, target `T2`; aspiration no longer occupies the achieved-tier field.
Every coverage generation/check also reports the reader-visible document and
word count, making corpus growth visible without adding a third ledger.

Generator/validator:

`tools\coverage.py`

Generated files—never edit manually:

- `docs\coverage.md`
- `docs\generated\fleet-table.md`
- `docs\generated\source-summary.md`

## Related retrieval layers

Keep their responsibilities distinct:

- `bottleneck-map.md`: what dependency blocks progress and what proof clears it;
- `failure-atlas.md`: symptom → discriminator → likely cause;
- `pattern-catalog.md`: small reusable implementation/engineering recipe;
- `cross-project-index.md`: who has raw working and where it lives;
- `cross-engine-map.md`: technical overlap versus genuine engine-specific
  contradiction;
- long chapters: full reasoning and implementation context.

New stable patterns include:

- `META-003` integration authority map;
- `META-004` earliest-bottleneck routing;
- `RE-003` camera consumer census;
- `RE-004` writer census plus external-effect proof;
- `SRC-001` prepared frame / per-view render.

New failure families include access-route mismatch, false camera ownership and
unstable raw-address/transient-instance anchoring, consumer-getter inventory
bias, writable-but-not-rendered arrays and last-writer animation races.

## Rules for continuing the system

1. Preserve the RE/source/shared separation.
2. Keep existing stable IDs and anchors; add rather than recycle.
3. Update project evidence before updating its summarized bottleneck state.
4. Do not mark a bottleneck cleared because code exists—require its exit proof.
5. Preserve ambiguous outcomes as ambiguous.
6. Treat source/SDK names as oracles until matched to the shipping bytes when
   the deliverable is an injector.
7. Keep project addresses and hashes in project docs; keep transferable
   bottleneck/failure/pattern classes in the playbook.
8. Use `sources.yml` for fleet identity/counts and review freshness.
9. Never hand-edit generated fragments.
10. Run both ledgers and strict MkDocs validation after changes.
11. Enforce one-fact/one-owner: routers route, workflows establish authority,
    the spine owns artifacts/exits, chapters own technical method, and project
    receipts own target-specific facts.

## Validation

Regenerate after intentional source-ledger or bottleneck changes:

```powershell
python tools\coverage.py
python tools\bottlenecks.py
```

Check generated state and internal links:

```powershell
python tools\coverage.py --check
python tools\bottlenecks.py --check
mkdocs build --strict
```

Or run:

```text
docs-check.bat
```

`docs-check.bat` now validates both structured ledgers before the strict site
build.

## Recommended way to continue

When working on any fleet project:

1. open `docs\bottleneck-map.md`;
2. verify the project-focus row against its cited source;
3. select the earliest active bottleneck;
4. read only the linked route/gate plus relevant technical chapter;
5. preregister control, variable, metric and decision rule;
6. run the cheapest discriminator;
7. update the project receipt, bottleneck ledger and transferable pattern or
   failure record;
8. regenerate and validate.

This architecture is intended to make the playbook useful as an operating
system for real VR-mod work, not merely an encyclopedia of techniques.
