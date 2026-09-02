# Source-Owned Route

Use this route when the exact code that owns the camera and world-render loop
can be built, modified and legally shipped. It is intentionally shorter than
the RE route, but it is not a shortcut around VR architecture.

Source ownership changes the discovery method:

```text
RE-owned:      pixels -> values -> writer -> object -> guarded seam
Source-owned:  types/call graph -> owner -> instrumented seam -> tested change
```

Both still have to prove which camera, frame, pass and side effect they own.
Named code can be the wrong code path just as easily as a plausible RVA can be
the wrong function.

!!! note "Evidence depth"
    This route is structurally complete but has less first-hand source-port
    harvest than the RE route. The coverage ledger tracks `source_integration`
    separately; consult the [coverage dashboard](coverage.md) before treating a
    source-port rule as fleet-proven. CoD4 VR, JKXR and The Dark Mod VR remain
    the highest-value deeper source reviews.

## What counts as source-owned

The decisive test is not possession of source files. All of these are
different:

| Access | Classification | Route |
|---|---|---|
| Exact engine/game source builds and ships against retail assets | Source-owned | This page |
| SDK headers/source describe retail structures but cannot produce a compatible binary | Source oracle | RE route; verify every boundary in retail |
| Managed/script layer owns game logic but native renderer is closed | Hybrid | This page above boundary, RE below it |
| Decompiled source or generated interop | Readable RE | Treat names as evidence leads; shipping guard requirements remain |
| Generic framework owns stereo | Framework-owned renderer | Use source methods in the companion layer; shared spine still applies |

An `AUTHORITY_MAP.md` should name the boundary by subsystem. IL-2 can edit its
managed render orchestration but cannot repair native shader behavior. SWAT 4’s
SDK and scripts explain engine relationships while the shipping renderer still
requires native integration.

## Outputs of this route

| Artifact | What it must answer |
|---|---|
| `SOURCE_BASELINE.md` | Can the untouched source reproduce the intended target? |
| `RENDER_OWNERSHIP_MAP.md` | Which types/functions own frame, view, culling and passes? |
| `VR_INTEGRATION_DESIGN.md` | Where does VR enter without infecting simulation and unrelated views? |
| `PER_VIEW_LEDGER.md` | Which work is once-per-frame, per-view or snapshot/restored? |
| `UPSTREAM_MAINTENANCE.md` | How are patches, branches, assets, licenses and compatibility maintained? |

## SRC-01 — prove source and retail equivalence {#src-01}

Build the source **without VR changes** first.

Record:

- source revision, patches and submodules;
- compiler, SDK, toolchain and architecture;
- build configuration and feature defines;
- asset/data version and expected retail installation;
- renderer selected at runtime;
- save/network/demo compatibility where applicable;
- redistributability of binaries and third-party components;
- known behavioral differences from retail.

Use a deterministic stock scene and compare:

- frame structure and pass count;
- camera/FOV/near/far;
- input and simulation cadence;
- content loading and scripted sequences;
- screenshots or capture-level invariants;
- logs/assertions that prove the intended code path compiled and executed.

A successful compile is not parity. If source corresponds to a different patch,
platform or community reconstruction, make that compatibility boundary explicit.

**Artifact:** `SOURCE_BASELINE.md` plus build receipt and control capture.

**Exit test:** a clean machine can build the untouched baseline and reproduce
the declared test scene closely enough that later differences are attributable
to the VR change.

## SRC-02 — map frame, camera and render ownership {#src-02}

Use symbols, types and the call graph to identify:

1. simulation/update entry;
2. render-frame preparation;
3. player/body camera update;
4. prepared-view or scene-view construction;
5. culling/frustum construction;
6. world draw/scene traversal;
7. post-processing and UI;
8. presentation;
9. secondary views—mirrors, shadows, portals, inventory, capture cameras;
10. native aim, interaction and audio-listener consumers.

Then instrument the named path. Record thread, call count, view identity, target
identity and phase across menu → loading → gameplay → cutscene. Source makes
this instrumentation easier; it does not make it optional.

### Ownership map template

| Owner | Type/function | Lifetime | Called | Reads | Writes | Per-eye policy |
|---|---|---|---|---|---|---|
| Simulation |  |  | once/frame | input, time | world state | never repeat |
| Frame preparation |  |  | once/render frame | world + pose | immutable frame packet | once |
| Player view |  |  | per player/view | frame packet | prepared view | per view |
| Cull view |  |  | per view | prepared view | visibility | per view or conservative union |
| World execute |  |  | per view | visibility + view | color/depth | per eye |
| UI |  |  | once/frame or layer | semantic state | HUD target | declared separately |
| Present/XR |  |  | once/frame | completed eyes | compositor | once |

**Artifact:** `RENDER_OWNERSHIP_MAP.md` with call counts and source locations.

**Exit test:** the map explains every world view in the control capture and
distinguishes gameplay update from view rendering.

## SRC-03 — separate once-per-frame from once-per-view work {#src-03}

The most expensive source-port mistake is wrapping the existing “render frame”
function in a two-eye loop when that function also advances game state.

Classify each operation:

```text
once per simulation frame
  input edges, AI, physics, gameplay timers, animation advancement, audio events

once per rendered frame
  predicted pose sample, XR wait/begin, immutable frame packet, pair generation

once per view/eye
  view/projection, culling, LOD selection, scene draw, view-dependent lighting

once per output surface
  desktop mirror, HUD capture, spectator view, encode/capture

never repeated without explicit banking
  temporal history advance, occlusion/query ownership, transient allocators
```

Where legacy code mixes categories, refactor toward a prepared immutable packet:

```cpp
struct PreparedFrame {
    SimulationFrameId simulation;
    PosePacket pose;
    SceneSnapshot scene;
    TemporalGeneration temporal;
};

PreparedFrame prepareFrameOnce(...);
PreparedView  prepareView(const PreparedFrame&, const EyeView&);
void          renderView(const PreparedFrame&, const PreparedView&, Targets&);
```

This is an architectural shape, not a demand to copy these types. The invariant
is that the per-eye function cannot silently advance once-per-frame state.

### Source side-effect test

Run stock, repeated-zero-delta and repeated-view-delta captures just as the RE
route does. Add assertions for simulation tick, animation time, particles,
audio events, query generations, allocators and temporal history. Owning source
makes the assertion cheap; it does not invalidate the need for a control.

**Artifact:** `PER_VIEW_LEDGER.md` plus assertions/tests.

**Exit test:** a second view changes view-dependent output while all declared
once-per-frame counters remain unchanged.

## SRC-04 — introduce a narrow VR integration boundary {#src-04}

Avoid sprinkling runtime calls and `if (vr)` through engine code. Create a
small boundary that supplies:

- runtime lifecycle and capability state;
- immutable per-frame predicted pose packet;
- per-eye view/projection/FOV tangents;
- eye target acquisition and completion;
- input snapshot and haptic requests;
- compositor layers and mirror policy;
- neutral fallback when VR is unavailable.

The engine should consume game-facing types. Keep raw OpenXR structures inside
the runtime adapter unless the renderer truly needs them. This makes flat mode,
headless tests and alternate runtimes possible without emulating a live headset.

### Integration seam requirements

- Flat mode follows the original path and remains continuously testable.
- VR capability is established from successful API results, not requested state.
- View construction accepts asymmetric projections natively where possible.
- Culling consumes per-eye frusta or an explicit conservative union.
- Secondary views declare whether they inherit, ignore or override HMD pose.
- Input enters the engine’s semantic funnel rather than becoming a second game.
- The mirror is an output consumer, not a third simulation/world frame.

**Artifact:** `VR_INTEGRATION_DESIGN.md` with interfaces, ownership and failure
policy.

**Exit test:** disabling the VR adapter restores the stock route without
duplicated code paths or persistent state.

## SRC-05 — use source-native verification {#src-05}

Exploit the evidence source work makes available:

- unit tests for rotations, projections, deadzones and state machines;
- invariant assertions for orthonormal camera bases and valid quaternions;
- sanitizers for lifetime, bounds and race errors;
- profiler markers per update/frame/view/pass;
- render-graph validation and resource-state assertions;
- deterministic replay/fixtures for live pose and frame packets;
- capture tests for pass count, target identity and temporal generation;
- build-time schema validation for config/defaults.

At least one test in every chain must anchor to ground truth the changed code
did not compute: a rendered pixel/capture, engine-owned target ID, native action
result or headset acceptance.

**Artifact:** automated tests plus flat and headset acceptance receipts.

**Exit test:** a deliberately injected sign, eye-order, lifecycle, side-effect
or stale-pose error causes the intended test to fail.

## SRC-06 — maintain the engine fork {#src-06}

Source ports exchange binary anchoring risk for fork-maintenance risk.

Record:

- upstream/default branch and merge cadence;
- VR patch ownership by subsystem;
- generated versus hand-edited files;
- third-party licenses and redistribution requirements;
- retail assets that must never be packaged;
- save/demo/network protocol compatibility;
- supported platforms, architectures and graphics backends;
- config migrations and default generation;
- clean install/update/uninstall behavior;
- abandoned or unsupported engine branches.

Prefer narrow commits around stable ownership boundaries. A 600k-line source
port is not maintainable if VR state is entangled with every renderer subsystem.

**Artifact:** `UPSTREAM_MAINTENANCE.md`, compatibility table and release recipe.

**Exit test:** a new contributor can update the upstream baseline, identify VR
conflicts and build a clean package without redistributing protected assets.

## Source-specific trip hazards

| Hazard | Why it masquerades as success | Fast discriminator |
|---|---|---|
| Source builds, but not the retail path | Named code appears correct while users execute another backend/version | Log renderer/backend and source revision in the first line |
| Two calls to `RenderFrame` | Produces two images while simulation/particles/audio advance twice | Zero-delta repeat plus once-per-frame assertions |
| One camera object reused for both eyes | Looks stereo locally but contaminates UI/aim/culling observers | Prepared per-view copy and consumer census |
| Symmetric FOV API forced onto asymmetric headset optics | Central image looks plausible; edges/fusion fail | Preserve four OpenXR tangents and run A3 residual tests |
| Desktop mirror implemented as a third world draw | Functionally correct but destroys frame budget | Mirror a completed eye or spectator target |
| Global temporal history | One eye ghosts/flickers even with correct matrices | Bank history by view/pair generation |
| Framework callback treated as full ownership | Names exist, but native shader/resource owners remain closed | Authority map at every language/API boundary |
| Unbounded engine fork | VR works once but cannot absorb patches or package legally | Upstream and license gate before feature expansion |

## Hybrid handoff rule

When source is an oracle rather than the shipping implementation:

1. derive semantic names, layouts and likely call relationships from source;
2. record the source version and structural hypothesis as `[SOURCE]`;
3. locate the counterpart in the exact retail binary;
4. verify it statically and behaviorally;
5. ship only the guarded retail derivation;
6. preserve differences as first-class findings.

Knowledge flows from the readable sibling to the blind target, but authority
still comes from the bytes users execute.

## Route exit checklist

Proceed to the [Shared VR Spine](shared-vr-spine.md) when:

- [ ] the untouched source build and retail/asset boundary are reproducible;
- [ ] frame, camera, culling, world, UI and presentation owners are mapped;
- [ ] once-per-frame and once-per-view operations are separated and asserted;
- [ ] the VR adapter has a narrow flat-safe failure boundary;
- [ ] tests can detect sign, eye, side-effect and lifecycle regressions;
- [ ] fork, license, compatibility and package maintenance are documented;
- [ ] hybrid closed layers have entered the RE route rather than being assumed.
