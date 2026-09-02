# Reverse-Engineered Route

Use this route when the retail code that owns the camera or renderer cannot be
built and shipped. It is the primary route for the in-house fleet.

The goal is not to “reverse the game.” The goal is to establish the smallest
set of **owned, validated and version-resilient seams** required by VR:

1. gameplay frame boundary;
2. render/view camera and projection;
3. culling ownership;
4. player/body and native gameplay aim;
5. a way to produce and deliver two views;
6. a safe connection to the engine’s own input, UI and interaction systems.

Do not proceed because an address looks plausible. Each gate has a behavioral
proof and a shipping-quality representation.

## Outputs of this route

| Artifact | What it must answer |
|---|---|
| `TARGET_PROFILE.md` | Which exact executable/modules/API/architecture are active? |
| `TOOL_PREFLIGHT.md` | Which tools were actually live, attached and suitable? |
| `LOAD_PROOF.log` | Which mod bytes and config executed in which process? |
| `ADDRESS_REGISTRY.md` | What stable anchors exist, for which builds, with which guards? |
| `CAMERA_FINDINGS.md` | Which values own render view, projection and culling? |
| `OWNERSHIP_CENSUS.md` | Who writes and reads the camera/frame state, and when? |
| `STEREO_ROUTE.md` | Which stereo rung is selected, why, and what invalidates it? |
| `FAILURE_REGISTRY.md` | Which plausible routes were disproven, under what premises? |

## RE-01 — fingerprint the shipping target {#re-01}

Record facts from the **active shipping build**, not only its directory:

| Question | Minimum evidence | Why it controls the route |
|---|---|---|
| Executable and logic modules | PE headers plus loaded modules | The EXE may be a launcher; Prey logic lives mainly in `PreyDll.dll` |
| Architecture | PE machine type | Selects injector, wrapper, debugger and address-space assumptions |
| Engine and generation | banners, symbols, middleware, scripts | Supplies names and structural priors, not facts |
| Active graphics API | loaded modules or trace | Import tables lie when render devices are loaded dynamically |
| Store/build identity | file hashes and version resources | Every address, signature and layout is scoped to it |
| Script/managed/SDK surface | loader behavior and file tree | May move some work to a readable layer |
| Anti-cheat and multiplayer | actual supported launch mode | Can rule out whole injection/patching techniques |

Static imports are leads. SWAT 4 statically imports legacy graphics entry points
but loads its real render device dynamically. Far Cry 2 can run a renderer that
does not match the launcher’s obvious import story.

### Check the fingerprint against recorded prior art

Once engine and API are *confirmed*, ask whether anyone has already done this
combination:

```powershell
python tools\prior_art.py "unreal 2.5" d3d9
```

It matches the fingerprint against every fleet and external source in
`sources.yml` and reports each one's integration authority or delivery vehicle,
achieved tier, stereo rung, which areas were harvested and where the working
lives. A match is a reading list, not a verdict; an `(API-only match)` shares no
engine lineage. An empty result is also informative: no chapter, tier or rung in
this playbook was earned on that fingerprint.

Run it after confirmation, never instead of it. The tool believes whatever you
typed, so a guessed API returns confident prior art for the wrong engine.

**Artifact:** `TARGET_PROFILE.md`, hashes and an empty version row in
`ADDRESS_REGISTRY.md`.

**Exit test:** architecture, active logic module and active graphics API are
confirmed, not guessed.

## RE-02 — route and preflight tools {#re-02}

A tool name in an agent’s tool list does not prove its host application is
running, attached or holding the correct program. Record the preflight result
before relying on its output.

| Need | Preferred route | Required preflight / constraint |
|---|---|---|
| Static functions, RVAs, xrefs and call graphs | Ghidra | Instance connected **and the correct program open** |
| Live struct reconstruction | ReGenny | Host running, target attached, help/SDK state checked |
| Values, AOBs and pointer chains | Cheat Engine | Bridge alive **and correct PID attached** |
| Low-disruption runtime hooks | Frida | Target process present; use when debugger attach destabilizes it |
| Native breakpoints | x32dbg/x64dbg | Match bitness; prove session state |
| D3D11/12, Vulkan, modern GL frame analysis | RenderDoc | A named `.rdc` capture already exists |
| D3D7/8/9 or legacy GL | apitrace | Correct wrapper bitness and actual API; remove conflicting proxies |
| Managed .NET assemblies | ILSpy | Correct assembly/backend; irrelevant to native binaries |

### Where these tools are wired up

This gate covers **preflight** — proving a tool is live and holding the right target. It deliberately
does **not** cover installing or configuring them, because that is machine state with a much shorter
shelf life than anything else in this playbook, and merging the two would make these pages wrong on an
update schedule.

In this environment the tools above are reached through MCP servers, and their setup lives in three
places:

| Where | What it holds |
|---|---|
| `D:\Dev Debug\mcp-updates\handover-claude-desktop-re-mcps.md` | **The step-by-step setup guide** — wiring an LLM host to Ghidra, Cheat Engine and a debugger so it reads disassembly, walks pointer chains and inspects frame captures directly. ~30 min for the first server, 2-3 hrs for the full bench, all free/OSS. Derived from the same seven mods as this playbook. Also published as the *RE MCP Bench Setup* artifact, which is the form to send someone else. |
| `D:\Dev Debug\mcp-updates\README.md` | Inventory, version/compatibility tracking, and the three host config paths. All servers are **shared installs**, so updating once fixes Claude Desktop, Claude Code and Codex together. Also keeps an *evaluated but not installed* list with reasons. |
| `re-mcp-toolkit` skill | Which MCP to reach for, its preflight, and per-tool caveats. Referenced by a stanza in each VR project's `AGENTS.md` and `CLAUDE.md`. |
| `vr-re-workflow` skill | The method: new-game onboarding, per-engine approach, and the recipe for locating view matrix, camera, FOV and player structs. |

Both skills are mirrored to `~/.claude/skills/` and `~/.codex/skills/`.

**Check the inventory before concluding a tool is unavailable.** Its rejected-tools list is a
[closed-families record](08-project-process.md) for tooling — windbg-mcp, for one, is recorded as
evaluated and refused with the reason attached, so the evaluation is not repaid every time someone
wishes for time-travel debugging.

If you are reading this playbook outside that environment, treat the table above as an example of the
*shape* worth keeping — an inventory with versions, a behavioural skill per toolchain, and a rejected
list with reasons — rather than as paths that will resolve.

### Capture-tool decision

| Active API | First choice | Important trap |
|---|---|---|
| D3D11/12, Vulkan | RenderDoc | The analysis bridge cannot create the capture for you |
| Modern core OpenGL | RenderDoc | Compatibility contexts may still defeat capture |
| D3D8/9, DirectDraw | apitrace | Wrapper bitness must match the target |
| D3D10/10.1 | apitrace `dxgi` route | There is no separate `d3d10` wrapper selector |
| Legacy/compatibility OpenGL | apitrace `gl` | Remove ReShade/ENB/other proxy wrappers first |

Request captures by use case: “gameplay frame with pause HUD visible” or
“reflection artifact frame,” never merely “take a capture.” A capture without
the state needed to answer the question is not evidence.

**Artifact:** `TOOL_PREFLIGHT.md` or a project `AGENTS.md` block containing
preflight, target-specific crashes and fallbacks.

**Exit test:** each planned tool is demonstrably live and suitable, or is
recorded unavailable with a named fallback.

## RE-03 — prove deterministic loading {#re-03}

The first production problem is proving which bytes executed.

1. Emit version, build time, DLL/plugin path and config path in the first line.
2. Emit PID, executable hash, architecture, graphics API and selected route.
3. Add one bounded harmless canary.
4. Test cold launch and attach-to-running separately.
5. Prove package/proxy precedence; “present on disk” is not “selected by the
   loader.”
6. Preserve the previous log and start a fresh one on every launch.
7. Maintain a vanilla control recipe with no mod, wrappers or capture layer.

Treat launch conditions as test validity. CPU affinity, compatibility flags,
administrator state, overlays, injection timing and the active OpenXR runtime
can all change the result before the code under test runs.

**Artifact:** `LOAD_PROOF.log`, vanilla control receipt and one-command
install/run recipe.

**Exit test:** the log alone proves the intended build/config ran in the
intended process. Absence of the identity line invalidates the entire session.

## RE-04 — prove the active frame boundary {#re-04}

Observe before redirecting or replaying.

Candidate boundaries include:

- DXGI `Present` or the engine call immediately above it;
- OpenGL `SwapBuffers` or the engine stage above it;
- D3D9 device `Present`/`EndScene` or the renderer plugin’s callback;
- an exported engine draw function;
- a world-execute/render-view virtual call;
- a shipped renderer plugin ABI.

For every candidate, log a bounded packet:

```text
frameCandidate=<name>
thread=<id> callIndex=<n> hostFrame=<n>
deviceOrContext=<identity>
color=<identity, dimensions, format>
depth=<identity, dimensions, format>
viewport=<x,y,w,h>
phase=<menu|loading|gameplay|video|secondary>
```

Run menu → loading → gameplay → pause → gameplay. Note device resets, context
changes, multiple swapchains and call-rate changes. A `Present` hook can be the
right XR host while still being the wrong place to obtain a second world view.

### Frame-boundary acceptance

- The callback fires at a known cadence in gameplay.
- Its absence or altered cadence in menus/loading is understood.
- The active render target belongs to the intended view.
- Thread and context/device ownership are stable or explicitly handed off.
- The control shows the probe itself did not alter cadence or state.

**Artifacts:** bounded frame log and matched control/candidate captures.

**Exit test:** the callback is identified by ownership, not merely reachability.

## RE-05 — discover camera and projection ownership {#re-05}

Prioritize these in order:

1. render view/camera transform;
2. projection/FOV and near/far;
3. culling camera/frustum;
4. player/body transform;
5. render invocation or prepared-view object;
6. native aim/interaction ray.

### GPU-first route

This is normally the shortest path from pixels to the code that owns them:

```text
world-space draw
  -> exact shader constant / fixed-function matrix
  -> exact float search in live memory
  -> instruction that writes or uploads it
  -> static function and owning object
  -> live struct reconstruction
  -> stable shipping anchor
```

Procedure:

1. Capture at least two gameplay frames with a controlled camera movement.
2. Find a world-space draw, not UI, a bone, a light or a shadow-only view.
3. Identify projection and rigid/view candidates in shader state.
4. Record exact raw bytes as well as decoded values.
5. Search those values in the running process.
6. Find what writes/accesses the surviving candidate.
7. Take the instruction into static analysis and reconstruct the owner live.

Do not select a matrix because it “changes every frame.” Bones, moving props,
lights, cascades and UI transforms do that. Pairing with the **known scene
projection/FOV** is a stronger discriminator.

### CPU-first route

Use this when capture is unavailable or named engine structure is unusually
rich:

1. Search symbols, exports, strings, RTTI, scripts, SDK/source or engine siblings
   for camera, view, projection, frustum and FOV vocabulary.
2. Follow callers to the graphics state upload or prepared-view construction.
3. Hook candidates read-only and correlate them with controlled motion.
4. For legacy APIs, trace `SetTransform`, uniform uploads or shader-constant
   calls and walk back to their producer.
5. Validate the object live; do not stop at a plausible decompilation.

For a mutable-array inventory such as bones, reverse the usual consumer-first
assumption: a getter is a demand trace, while the writer exposes the records
evaluated through that seam. Use [RE-004](pattern-catalog.md#re-004) and preserve
the result in `MUTABLE_ARRAY_CENSUS.md`; pixels, not write/readback, prove the
render consumer.

### Candidate scorecard

| Test | Expected camera behavior | Common false positive |
|---|---|---|
| Straight translation | Eye position changes linearly in the commanded direction | Bone/prop moves locally or only while animated |
| Rotation | 3×3 basis rotates while staying orthonormal | Projection scales but is not rigid |
| Projection pairing | FOV/near/far agree with the active scene projection | Shadow/portal camera has a different FOV |
| Call phase | Updates before the intended world draw | UI or post-effect matrix updates late |
| View provenance | Main player view has stable owner/context | Reflection, cubemap, security camera or cutscene |
| Controlled write | Tiny reversible perturbation moves only the predicted consumer | Global state contaminates aim/culling/secondary views |

For a rigid basis, test axis lengths near one, mutual dot products near zero and
determinant magnitude near one. For a conventional symmetric projection,
`2*atan(1/P11)` is a useful vertical-FOV hypothesis and `P11/P00` an aspect
hypothesis—but storage order, handedness, clip range, off-axis terms and engine
companions must be established before treating either as truth. Use
[A3’s residual tests](a3-stereo-projection.md), not a memorized matrix layout.

**Artifacts:** `CAMERA_FINDINGS.md`, raw values/bytes, capture event/slot,
function signature, struct sketch, evidence grades and invalidation conditions.

**Exit test:** controlled movement and a reversible perturbation distinguish
the player render camera from bones, shadows, reflections, UI and authored
views.

## RE-06 — reconstruct ownership, not just a struct {#re-06}

An address is not ownership. Before injecting HMD state, answer:

| Ownership question | Required answer |
|---|---|
| Lifetime | Singleton, level object, player object, frame-local, pooled, copied or aliased? |
| Writer | Who authors it, on which thread and at what phase? |
| Consumers | Culling, renderer, UI, aim, audio, viewmodel, particles, scripted cameras? |
| Copy semantics | Pointer, reference, by-value snapshot, double buffer or transient stack object? |
| Variants | Main, reflection, shadow, portal, cutscene, inventory, capture? |
| Invalidation | Device reset, level load, possession, cutscene, resolution change, patch? |
| Restore contract | Can it be borrowed/restored bit-exactly, or does writing trigger observers? |

### Consumer census

For a global or shared camera, enumerate readers around the proposed per-eye
window. This is where “camera correct, gameplay broken” originates. Prey’s
global view camera feeds dozens of consumers, including an aim-ray update during
render preparation; its later `CRenderView::SetCamera` copy-by-value seam is
safer because it changes the renderer without contaminating that global owner.

Record each consumer as:

```text
consumer=<name/address>
phase=<update|pre-render|world|post|ui|audio>
reads=<gameCam|renderCam|cullCam|projection|aimRay>
writesPersistent=<yes/no/unknown>
allowedPerEye=<yes/no/conditional>
evidence=<grade + receipt>
```

If full enumeration is impossible, state the lower bound and choose a seam
downstream of shared consumers where possible.

**Artifacts:** `OWNERSHIP_CENSUS.md` and a typed struct/layout in ReGenny or the
project’s equivalent.

**Exit test:** the proposed mutation window has explicit writer, reader,
lifetime and restore semantics.

## RE-07 — turn observations into shipping anchors {#re-07}

Absolute virtual addresses are observations. Shipping code needs a guarded
derivation scoped to known builds.

Each `ADDRESS_REGISTRY.md` row should include:

| Field | Requirement |
|---|---|
| Build identity | Executable/module hash and store/version |
| Semantic name | What behavior this anchor owns |
| Module + RVA | Rebased observation, never only a process VA |
| Derivation | Signature, export, RTTI/vtable, pointer chain or symbol oracle |
| Guard bytes/invariants | What must still be true before use |
| Evidence | STATIC/LIVE/HEADSET plus receipt |
| Consumers/call phase | Why the hook/write occurs at the intended moment |
| Invalidation | Patch, level, object lifetime, context or renderer change |
| Fallback | Disable feature, lower stereo rung or alternate anchor |

### Anchor preference

Prefer, in order:

1. exported or documented interface;
2. unique semantic signature resolved to module-relative code;
3. RTTI/vtable slot with object validation;
4. stable base pointer plus validated pointer chain;
5. raw RVA only for a deliberately supported exact hash.

Verify signatures for uniqueness and semantic placement, not only byte match.
Verify pointer chains across restarts, level loads and ownership transitions.
Unknown builds must fail closed: leave the flat game working, identify the
unsupported hash, and disable only the affected lane.

**Artifact:** populated `ADDRESS_REGISTRY.md` plus automated signature/guard
tests where possible.

**Exit test:** the feature cannot execute on a mismatched target or invalid
object, and a known-good build resolves the expected semantic site.

## RE-08 — make the first reversible mutation {#re-08}

The first write is an experiment, not an implementation.

Use a value that is:

- small enough not to corrupt the scene;
- large enough to distinguish from the measured noise floor;
- attributable to one variable;
- applied for a bounded interval;
- restored immediately and verified;
- protected by a runtime toggle and target guard.

Examples include a tiny yaw offset, FOV perturbation, color clear, viewport
shift or one-frame camera translation. Always capture:

1. stock control;
2. armed-with-zero-delta control;
3. armed-with-test-delta result;
4. restore/readback result.

The zero-delta control separates the intended change from hook/re-entry side
effects. A blank result can mean the isolation gate disabled the necessary
fallback, not that the candidate was irrelevant.

**Artifact:** `MUTATION_PROOF.md`, receipt/capture and rollback command.

**Exit test:** the predicted owner changes, unrelated invariants remain stable,
and restore returns to the matched baseline.

## RE-09 — select the stereo production route {#re-09}

Choose the highest viable rung by evidence, not ambition:

| Rung | Route | Required property | Main tax |
|---|---|---|---|
| 1 | Native scene re-entry | Callable/re-entrant world execute plus camera delivery | Per-frame side effects, render-view pools, cost |
| 2 | Per-draw replay/private eye targets | Reachable draw stream and matrices/resources | Culling and per-eye producer reconstruction |
| 3 | Alternate-eye rendering | Reliable frame boundary and pair policy | Temporal disparity, pair latching, half-rate freshness |
| 4 | Draw-stream reconstruction | Geometry/depth present even without a camera seam | Original-frustum ceiling and semantic reconstruction |

Before settling below rung 1, find an existing repeat render: mirror, portal,
cubemap, reflection probe, security monitor or render-to-texture. It is evidence
that the engine can re-enter rendering, but often uses a reduced pass set; treat
it as **proof, not automatically the vehicle**.

### The three-capture side-effect gate

Run:

| Capture | Re-entry | Camera delta | Purpose |
|---|---:|---:|---|
| A | no | 0 | Stock baseline |
| B | yes | 0 | Detect repetition side effects |
| C | yes | controlled eye/yaw delta | Prove camera/view influence |

Decision:

- `A→B` at the measured noise floor and `A→C` above the preregistered
  threshold: camera/re-entry proof passes.
- `A→B` above the threshold: result is **confounded**; classify simulation,
  particles, audio, allocators, queries, temporal histories and observers.
- both at the floor: the camera was baked before this seam, the path did not
  execute, or the metric cannot see the error class.

Also assert which work is allowed:

```text
once per simulation frame: input edges, AI, physics, audio events, gameplay timers
once per rendered frame: pose sample, XR wait/begin, pair generation
once per eye: view/projection, culling, eye targets, view-dependent lighting
snapshot/restore: only state proven bit-exact and observer-safe
```

**Artifact:** `STEREO_ROUTE.md`, cost measurements, side-effect ledger and
fallback rung.

**Exit test:** the selected route has a camera-delivery contract, a side-effect
policy, a measured cost and a lower-rung fallback.

## In-house routing examples

| Project | What the RE route contributed | Current architectural lesson |
|---|---|---|
| SS2VR | KEX/D3D11 ownership, cull camera, native systems and private-eye path | A stock cubemap repeat can prove a higher rung after a lower rung ships |
| BioShockVR | Scene-node camera, per-draw matrices/resources and screen-space owners | Correct geometry does not clear mono deferred producers |
| SOMAVR | GL uniform/frustum owners, native mover and authored-camera states | Source oracles help naming; retail OpenGL behavior still needs live proof |
| PreyVR | Global versus copy-by-value camera seams and callable RenderWorld primitives | Prefer the latest seam that avoids shared gameplay consumers |
| DishonoredVR | UE3/D3D9 anchors | Transport can be a harder blocker than camera mathematics |
| FarCry2-VR | Dunia pass graph, camera delivery and WorldExec | Static “no simulation” still needs a live side-effect gate |
| SWAT4-VR | SDK/exports plus live engine hooks and 9On12 | Readable siblings can collapse RE without changing the shipping mode |
| Sims4VR | Python camera oracle plus RenderDoc pass census | Existing repeat rendering is not proof of an independently controllable view |

The generated [bottleneck matrix](bottleneck-map.md) carries the current fleet
state. This table explains the reusable architecture, not the live priority.

## Route exit checklist

Proceed to the [Shared VR Spine](shared-vr-spine.md) when:

- [ ] target identity and deterministic loading are proven;
- [ ] the gameplay frame boundary is owned;
- [ ] render, cull, game/body and scripted camera roles are separated;
- [ ] a stable guarded derivation replaces every raw observation used at runtime;
- [ ] the first reversible mutation passes with a zero-delta control;
- [ ] stereo route, camera delivery, side effects, cost and fallback are recorded;
- [ ] unresolved risks are registered in the [bottleneck system](bottleneck-map.md).

Do not wait for perfect decompilation. Do require enough behavioral ownership
that the shared VR work is no longer built on an ambiguous address or frame.
