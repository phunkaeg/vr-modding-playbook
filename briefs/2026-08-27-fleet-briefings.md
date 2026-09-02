# Fleet briefings — 2026-08-27

Findings from this date's harvest that are **project-specific**, i.e. would not be found by ordinary
routing through [AGENTS.md](../AGENTS.md). Everything here is already in the playbook; this page exists
so each project sees the part aimed at it.

No agent sessions were running when these landed, so nothing was pushed. **Read your project's section
before your next session**, and treat every claim as `INFERENCE` for your target until you confirm it —
these come from other people's engines.

---

## DishonoredVR — two items, one urgent

**1. The D3D9 x87 precision trap.** `[SOURCE]` — bo1-vr

A D3D9 device created **without `D3DCREATE_FPU_PRESERVE`** lets the runtime reprogram the x87 control
word to a **24-bit mantissa** for the whole thread. Every `double` in your pose maths then computes at
float precision. There is no error and no warning.

The symptoms are ones you would blame on your own maths: drift accumulating over a session, an
orthonormality check failing by a margin that looks like it should have passed, quaternion normalisation
that will not settle. **This applies to every D3D9-era injector**, which includes yours.

Cost to check: read the control word after device creation and assert it. See
[ch10 #d3d9-x87-precision](../docs/10-graphics-apis.md#d3d9-x87-precision).

**2. You are one of three projects that solved D3D9 → XR, by three different routes.**

| Route | Mechanism | Who |
|---|---|---|
| D3D9Ex shared texture → D3D11 | `CreateTexture(D3DUSAGE_RENDERTARGET, D3DFMT_A8R8G8B8, D3DPOOL_DEFAULT, &sharedHandle)` → `OpenSharedResource` | CallOfDuty4_VR |
| D3D9Ex → D3D11 via SurfaceQueue | queue marshals surfaces; format whitelist collapses sRGB; 16×16 staging `Lock` as a sync point | gmcl_openvr |
| `Direct3DCreate9On12` → D3D12 | unwrap the underlying resource | **you** |

Your negative control (plain `Direct3DCreate9` refusing shared resources, `0x8876086C`) is now recorded
in the playbook as the canonical one for this family.

**The assertion you may be missing:** CoD4's probe checks four things, and the fourth is that **the
running game's device is on the same adapter** as the runtime asked for. A bridge proven in isolation
says nothing about the game's GPU, and on switchable-graphics laptops it frequently differs. Your own
per-boot-LUID observation (`0001667A` vs `00016A92`, same card) is recorded alongside it — compare within
a session, never persist. See [XR-006](../docs/pattern-catalog.md#xr-006).

---

## FarCry2-VR — basis validation, and a scope rule

**1. `|det| ≈ 1` accepts a mirrored basis.** `[SOURCE]` — bo1-vr

You are writing basis and bone-cluster maths right now, so this is timely. A reflection composed with a
rotation still has determinant magnitude 1, and `|det|` is what most implementations actually test. A
mirrored basis inverts hands, sends aim the wrong way off-centre and reverses stereo — **while every
orthonormality assertion passes**.

Test handedness, not magnitude: `det == +1` **and** `cross(forward, left) == up`.

bo1-vr pairs those, links the same object file into an offline binary that must **reject four named
wrong composition orderings**, re-runs at DLL load, and degrades to position-only after 30 rejects. That
last part is the half worth copying: a check that detects the fault and proceeds anyway is a log line,
not a guard. [ch06 #mirrored-basis](../docs/06-debugging-methodology.md#mirrored-basis).

**2. Per-item data is not per-item code** — [ch02 #per-item-data-not-code](../docs/02-viewmodels-and-hands.md#per-item-data-not-code).

BFVR refuses bespoke per-weapon pose code; CallOfDuty4_VR ships 128 weapon profiles. Not a contradiction
— per-item *code* multiplies paths to maintain, per-item *data* in one bounded schema is a table. If you
end up with per-weapon offsets, bound every field (CoD4 caps at 12 inches and 90 degrees precisely so a
slider or bad config cannot produce a pose the renderer must survive).

---

## PreyVR — the frame contract, and your own finding generalised

**XR-005 — wait once, cache, submit after every camera.** In a survey of eleven mods, **five got this
wrong**. Since you have not yet built the submission path, you can start correct rather than debug into
it: wait once early, cache the poses, render every camera from that same cached pose, submit from an
end-of-frame hook after all cameras have rendered, hand off last. The legitimate deviation is re-polling
*inside the render backend* at draw time — that is late-latching, and it applies to head motion only.
[XR-005](../docs/pattern-catalog.md#xr-005), [CAM-007](../docs/pattern-catalog.md#cam-007).

**Your `CreateIKLimb` finding became a general pattern.** META-006 now says: enumerate what the engine
*already honours* — a stereo device interface, a view-supplier callback, a native-extension loader, a
named IK facility, a cvar — before designing a hook. Four projects converged on it. Your instance is
cited.

**Also relevant:** a projection rebuilt from four tangents discards the shear that canted displays fold
into the matrix. If you can reach the matrix, treat it as opaque and left-multiply a clip-space crop.
The superset-and-crop family cannot carry shear either — it is an escape hatch for engines exposing only
scalar FOV and aspect.

---

## SS2VR and BioshockVR — the graph over your docs, and what it can actually do

Your documentation is in `cross-engine-graph/corpus/`. It was re-extracted today and the honest result is
recorded in that repo's README.

**Use the reconciled graph, not the merged one.** `merge-graphs` is a union: it stacks the three
project graphs and creates no edge between them, so a query seeded in SS2VR's nodes can never reach
BioshockVR's. Asked *"which projects hit problems with the cull camera or culling?"* the merged graph
returned 22 nodes, all SS2VR.

`tools/reconcile_graphs.py` adds the missing step — it reads node labels and links concepts that recur
across projects under different names, which string matching cannot find (only 7 labels match exactly
across 1328 nodes, and 5 of those are filenames). The same query against
`graphify-out/reconciled-graph.json` now reaches **both** SS2VR and BioshockVR documents. Fifteen
concepts are linked, including frustum/culling, stereo strategy, depth submission, HUD layering,
viewmodel posing, interaction raycasting, haptics, recentre and roomscale.

**It is good for entity lookup with provenance.** That same query surfaced
`SceneTraversalBegin_SetCullCamera (0x45C150)`, `PortalGetClipInfo (0x4638D0)` and
`PlayerTurnTilt (0x5126E0)`, each attributed to the document that named it. Faster than grep when you
want "which of our docs mentions X and what symbols sit near it".

### How to actually use it

Your project's graph:

```
D:\Dev Debug\VR Modding\cross-engine-graph\per-project\<somavr|ss2vr|bioshockvr>\graphify-out\graph.json
```

Ask it a question — BFS over the graph, capped so the answer fits a context budget:

```
graphify query "where is the cull camera set" --graph <path-to-graph.json> --budget 900
```

Trace how two things connect, or explain one node and its neighbourhood:

```
graphify path "CameraObj" "SceneTraversalBegin_SetCullCamera" --graph <path>
graphify explain "PortalGetClipInfo" --graph <path>
```

Find what breaks if you change something — reverse traversal:

```
graphify affected "OpenXRRuntime" --graph <path> --depth 2
```

**Three things to know before you trust an answer:**

1. **It indexes your DOCS, not your code.** A symbol appears because a document named it, so absence
   from the graph means nobody wrote it down - not that it does not exist.
2. **It is a snapshot.** Built 2026-08-27 from the staged corpus, not from your live `docs/`. Anything
   written since is missing.
3. **Query results are leads with provenance, not evidence.** Every node carries the document that
   minted it; go read that document before acting. The graph tells you *where to look*, and the
   [evidence grading rules](../AGENTS.md) still apply to whatever you find there.

**Cross-project questions need the reconciled graph:**

```
graphify query "<question>" --graph "D:\Dev Debug\VR Modding\cross-engine-graph\graphify-out\reconciled-graph.json"
```

Cross-project edges carry `relation: same_concept_as` plus the concept name and a one-line reason, so you
can see *why* two projects were linked and reject the link if it is wrong. It is regenerated with
`graphify-key.bat <graphify-python> tools/reconcile_graphs.py` for about a cent.

**What it is still bad at:** synthesis. It tells you *where the same problem was solved elsewhere*; it
does not tell you what the answer was. Go and read the documents it names. See
[ch06 #graph-cross-source-limit](../docs/06-debugging-methodology.md#graph-cross-source-limit).

**BioshockVR specifically:** your active performance blocker — two eye renders plus a desktop world
render, with eliminating the third being the architectural lever — was **independently reached by KSA_XR
on Vulkan**, which runs three complete game frames per displayed frame and calls it knowingly
inefficient. Scrap-Mechanic-Native-VR avoids the third render by reusing the finished left eye through a
3-vertex fullscreen triangle. Same problem, two other engines, one worked answer.

---

## Swat4-VR and Sims4VR

**Both:** the stereo ladder is a runtime policy with independently shippable rungs, corroborated twice
more today — MELE-VR ships four modes as a single config number including a depth-reprojection fallback.
[STR-006](../docs/pattern-catalog.md#str-006).

**Sims4VR:** [ch08 #host-settings-policy](../docs/08-project-process.md#host-settings-policy) is new and
aimed at targets where you override the host game's own settings. The shipped answer from a very large
user base: force aim assist, additive camera movement, sway, motion blur, DoF, film grain, chromatic
aberration and lens flares **off** — but keep anisotropy and texture quality **high**, because they are
cheap and pay off at the glancing angles a headset actually looks at. A blanket low preset throws that
away for nothing.

Also: **square the render target.** Two unconnected authors on different engines reached it independently
— a 1:1 aspect, because a 16:9 buffer spends most of its width outside the FOV.
