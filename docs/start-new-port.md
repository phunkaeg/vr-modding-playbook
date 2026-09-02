# Start or Unblock a VR Port

This is the playbook router. Use it when starting a target, when inheriting one,
or when an existing port has accumulated several plausible next steps and no
clear critical path.

The playbook has two primary implementation routes:

- **[RE-owned](reverse-engineered-route.md):** the shipping camera/render code
  is closed. Discover a stable integration seam in the retail binary.
- **[Source-owned](source-owned-route.md):** the code that owns the camera and
  world-render loop can be built, changed and legally shipped.

Both routes rejoin the **[shared VR spine](shared-vr-spine.md)**. Source access
removes discovery and anchoring work; it does not remove stereo, culling,
per-eye state, lifecycle, input, UI, performance or comfort work.

If something is already blocked, do not restart at gate zero. Open the
**[fleet bottleneck map](bottleneck-map.md)**, identify the earliest uncleared
gate, and run its fast discriminator.

## The route in one screen

```text
PORT-00  Define the intended conversion
PORT-01  Classify what can actually be built and shipped
PORT-02  Establish a reproducible stock baseline
                     |
          +----------+-----------+
          |                      |
      RE-owned               Source-owned
      RE-01..09              SRC-01..06
      discover, prove,       build, map, edit,
      anchor, fail closed    test, maintain fork
          |                      |
          +----------+-----------+
                     |
PORT-06  Pose and transform ownership
PORT-07  Stereo proof ladder
PORT-08  OpenXR lifecycle and image transport
PORT-09  Render-pass and per-eye state ownership
PORT-10  Input, locomotion and native gameplay actions
PORT-11  UI, hands, viewmodels and interaction
PORT-12  Performance, audio and haptics
PORT-13  Compatibility, packaging and release
```

The route is a dependency graph, not a schedule. A T3 interaction feature built
on an unproven T1 camera will manufacture “hand bugs” that are actually camera
or frame-ownership bugs.

## The evidence vocabulary

Tag important claims where they are made:

| Grade | Use it for |
|---|---|
| `[SPEC]` | Guaranteed by an API specification or platform documentation |
| `[SOURCE]` | Read directly in source code |
| `[STATIC]` | Established by static binary analysis |
| `[LIVE]` | Observed in a running target |
| `[HEADSET]` | Accepted visually or behaviorally in a headset |
| `[AUTHOR]` | Claimed by another author but not independently checked |
| `[INFERENCE]` | A transferable hypothesis still unproven on this target |

Evidence grade describes how a claim is known, not how confident the author
sounds. A matrix identified by shape is `[INFERENCE]`; the same matrix tracking
a controlled camera motion is `[LIVE]`.

## PORT-00 — define the intended conversion {#port-00}

Record:

- exact game build, distribution and executable;
- intended devices and runtime;
- seated, standing or roomscale design;
- [completeness target](08-project-process.md#how-vr-is-it-declare-a-completeness-tier-and-ship-to-it)
  T0–T4;
- initially acceptable [stereo rung](17-teardown-fc2vr-native-stereo.md);
- anti-cheat, multiplayer and offline constraints;
- mechanics that may be fundamentally incompatible with VR;
- explicit exclusions for the first milestone.

**Artifact:** `PORT_BRIEF.md`.

**Exit test:** a reviewer can distinguish “deliberately out of scope” from
“forgotten.” “Full VR” is not a testable requirement.

## PORT-01 — classify integration authority {#port-01}

Do not ask only “is source code available?” Ask:

> Can we build, modify and ship the exact code that owns the retail camera and
> world-render loop?

| What you have | Primary route | Important boundary |
|---|---|---|
| Buildable, redistributable engine/game source matching retail assets | **Source-owned** | You support an engine fork |
| Official SDK/source that cannot produce a compatible retail binary | **RE-owned, source as oracle** | Names/layouts are leads until verified in the shipping binary |
| Managed or script game layer over a closed native renderer | **Hybrid** | Use source-owned methods above the boundary and RE below it |
| Framework that already owns stereo/tracking | **Framework + companion** | Treat the framework as the renderer owner; solve game-specific adaptation |
| Closed retail binary | **RE-owned** | Discovery, anchoring, build guards and fail-closed behavior are shipping requirements |
| No usable engine, but readable data formats | **Recreation** | This is a new engine project, not an injected port |

Presence of a source archive is not the exit proof. FEAR’s SDK is an excellent
oracle even where its CRT boundary prevents shipping a rebuilt engine. IL-2’s
replaceable Java layer owns the frame loop but not the native shader pipeline.
SWAT 4’s SDK and exports illuminate a native-injector target. These are hybrid
authority maps, not exceptions to be hidden.

**Artifact:** an `AUTHORITY_MAP.md` naming each layer, whether it is readable,
buildable, modifiable and shippable, plus the chosen primary route.

**Exit test:** every planned mutation names the code layer that owns it and how
that mutation reaches users.

## PORT-02 — establish a reproducible stock baseline {#port-02}

Before adding VR:

1. Hash the exact executable and logic/render modules.
2. Record architecture, engine/generation and graphics API from the active
   process or a trace—not imports alone.
3. Capture menu, loading and representative gameplay behavior.
4. Record stock resolution, frame cadence, settings, save, launch arguments,
   runtime and overlays.
5. Make a clean control recipe that removes injectors, wrappers and replacement
   packages without damaging the installation.
6. Choose one deterministic test scene and one transition sequence.

For source-owned work, also build the untouched source and compare it with the
expected retail behavior. For RE-owned work, prove the intended plugin/DLL can
identify itself without yet mutating gameplay.

**Artifacts:** `TARGET_PROFILE.md`, hashes, `BASELINE_RECEIPT.md`, control
capture and one-command vanilla launch recipe.

**Exit test:** another developer or agent can reproduce the same stock scene
and prove whether a later run used the same target.

## PORT-03 — choose the active route {#port-03}

### RE-owned target

Continue with the **[Reverse-Engineered Route](reverse-engineered-route.md)**.
It ends when you have:

- a deterministic load path;
- the real gameplay frame boundary;
- confirmed camera, projection and culling ownership;
- a version-resilient integration seam;
- a reversible mutation proof;
- an evidence-selected stereo architecture.

### Source-owned target

Continue with the **[Source-Owned Route](source-owned-route.md)**. It ends when
you have:

- an untouched reproducible build;
- a render/simulation ownership map;
- an explicit per-frame/per-view boundary;
- a narrow VR integration interface;
- tests and an upstream/fork maintenance contract.

### Hybrid target

Run the source route for layers you can build and the RE route for every closed
shipping boundary. Never transfer an address, layout or ABI from reference
source to the retail binary without independent static or live confirmation.

## PORT-04 — establish frame ownership {#port-04}

This gate now lives inside both routes:

- [RE-04 — prove the active frame boundary](reverse-engineered-route.md#re-04)
- [SRC-02 — map frame and render ownership](source-owned-route.md#src-02)

**Exit test:** the selected callback’s thread, cadence, target identity and
menu/loading behavior are known. A callback that merely fires is not a frame
boundary proof.

## PORT-05 — establish camera and projection ownership {#port-05}

This gate also has route-specific methods:

- [RE-05/06 — discover and reconstruct ownership](reverse-engineered-route.md#re-05)
- [SRC-02/03 — trace owners and separate frame from view](source-owned-route.md#src-02)

**Exit test:** a controlled trace or write distinguishes player render camera,
cull camera, body/game pose, scripted cameras, viewmodels and secondary views.

## PORT-06 — separate pose and transform ownership {#port-06}

Continue at [Shared VR Spine · PORT-06](shared-vr-spine.md#port-06).

## PORT-07 — climb the stereo proof ladder {#port-07}

Continue at [Shared VR Spine · PORT-07](shared-vr-spine.md#port-07).

## PORT-08 — implement OpenXR ownership and transport {#port-08}

Continue at [Shared VR Spine · PORT-08](shared-vr-spine.md#port-08).

## PORT-09 — classify the render graph {#port-09}

Continue at [Shared VR Spine · PORT-09](shared-vr-spine.md#port-09).

## PORT-10 — integrate engine-owned input {#port-10}

Continue at [Shared VR Spine · PORT-10](shared-vr-spine.md#port-10).

## PORT-11 — establish UI, hands and interaction lanes {#port-11}

Continue at [Shared VR Spine · PORT-11](shared-vr-spine.md#port-11).

## PORT-12 — measure performance, audio and haptics {#port-12}

Continue at [Shared VR Spine · PORT-12](shared-vr-spine.md#port-12).

## PORT-13 — harden, package and declare completion {#port-13}

Continue at [Shared VR Spine · PORT-13](shared-vr-spine.md#port-13).

## If the project is already underway

Do not walk every gate from the beginning. Instead:

1. Open the [current fleet focus](bottleneck-map.md#current-in-house-project-focus).
2. Confirm the project’s row still matches its source `CURRENT_STATE`.
3. Find the earliest red/orange bottleneck in dependency order.
4. Run that bottleneck’s **fast discriminator**.
5. Record the outcome in the project and in `bottlenecks.yml`.
6. Continue only after the named exit proof passes or a fallback route is
   explicitly selected.

This prevents mature projects from being forced through irrelevant onboarding
and prevents young projects from hiding a missing camera or transport proof
under T3 feature work.

## Minimum paper trail

Copy the schemas from [Project Evidence Templates](project-evidence-templates.md)
rather than inventing incompatible tables in every project.

### Every route

```text
docs/
  PORT_BRIEF.md
  AUTHORITY_MAP.md
  TARGET_PROFILE.md
  CURRENT_STATE.md
  HYPOTHESES.md
  FAILURE_REGISTRY.md
  DECISION_LOG.md
  STEREO_ROUTE.md
  STEREO_LADDER.md
  RENDER_PASS_CENSUS.md
  RECOVERY_MATRIX.md
  INPUT_OWNERSHIP.md
  TEST_CHECKLISTS.md
```

### RE-owned additions

```text
  ADDRESS_REGISTRY.md
  CAMERA_FINDINGS.md
  OWNERSHIP_CENSUS.md
  TOOL_PREFLIGHT.md
```

### Source-owned additions

```text
  SOURCE_BASELINE.md
  RENDER_OWNERSHIP_MAP.md
  VR_INTEGRATION_DESIGN.md
  UPSTREAM_MAINTENANCE.md
```

A finding is not complete until its evidence, applicability boundary,
invalidation condition and failed alternatives are written down. Future humans
and agents cannot recover knowledge that lived only in one debugger session or
chat context.
