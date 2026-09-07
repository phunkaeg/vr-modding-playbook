# Fleet reconciliation report

Generated 2026-09-07 by `tools/reconcile_fleet.py`.

Cross-project edges carry `relation: same_concept_as` with the concept name and a
one-line reason, and are graded `INFERENCE` - a model proposed them from labels alone.
**Every node is a lead with provenance, not evidence.** Go read the document it names.

## Totals

- projects reconciled: **10**
- nodes: **2,239** (all namespaced `project::id`), of which **34** are concept nodes
- intra-project links: **940**
- cross-project links: **126**
- concept→implementation links: **111**
- distinct concepts bridging 2+ projects: **34**

Concept nodes exist because graphify seeds a query by **lexical** match on labels.
A question in plain English ("stop geometry being culled") matches no engine symbol
and seeds on noise; a concept node carries the plain-English name and reason, so the
question lands on it and every project's implementation is one `instance_of` hop away.

## Per-project coverage

| Project | Nodes | Intra links | Cross-project edges | Reachable from |
|---|---:|---:|---:|---|
| **ss2vr** | 659 | 225 | 53 | bioshockvr, dishonoredvr, farcry2vr, preyvr, sims4vr, somavr, swat4vr |
| **bioshockvr** | 435 | 247 | 38 | preyvr, sims4vr, somavr, ss2vr, swat4vr |
| **somavr** | 410 | 138 | 55 | bioshockvr, dishonoredvr, farcry2vr, preyvr, sims4vr, ss2vr, swat4vr |
| **preyvr** | 220 | 104 | 29 | bioshockvr, farcry2vr, sims4vr, somavr, ss2vr, swat4vr |
| **dishonoredvr** | 64 | 38 | 8 | farcry2vr, mohvr, sims4vr, sofvr, somavr, ss2vr, swat4vr |
| **farcry2vr** | 146 | 79 | 8 | dishonoredvr, preyvr, sims4vr, somavr, ss2vr, swat4vr |
| **swat4vr** | 111 | 39 | 22 | bioshockvr, dishonoredvr, farcry2vr, mohvr, preyvr, sims4vr, sofvr, somavr, ss2vr |
| **sims4vr** | 75 | 27 | 23 | bioshockvr, dishonoredvr, farcry2vr, mohvr, preyvr, sofvr, somavr, ss2vr, swat4vr |
| **mohvr** | 39 | 17 | 9 | dishonoredvr, sims4vr, sofvr, swat4vr |
| **sofvr** | 46 | 26 | 7 | dishonoredvr, mohvr, sims4vr, swat4vr |

## Project pairs

| Pair | Shared-concept edges |
|---|---:|
| somavr ↔ ss2vr | 26 |
| bioshockvr ↔ ss2vr | 15 |
| bioshockvr ↔ somavr | 13 |
| preyvr ↔ ss2vr | 7 |
| preyvr ↔ somavr | 7 |
| bioshockvr ↔ preyvr | 6 |
| sims4vr ↔ swat4vr | 5 |
| preyvr ↔ sims4vr | 4 |
| preyvr ↔ swat4vr | 4 |
| mohvr ↔ sims4vr | 3 |
| mohvr ↔ sofvr | 3 |
| somavr ↔ swat4vr | 3 |
| sims4vr ↔ somavr | 3 |
| dishonoredvr ↔ swat4vr | 2 |
| mohvr ↔ swat4vr | 2 |
| sims4vr ↔ sofvr | 2 |
| farcry2vr ↔ somavr | 2 |
| bioshockvr ↔ swat4vr | 2 |
| sims4vr ↔ ss2vr | 2 |
| bioshockvr ↔ sims4vr | 2 |
| farcry2vr ↔ swat4vr | 2 |
| dishonoredvr ↔ sims4vr | 1 |
| dishonoredvr ↔ mohvr | 1 |
| dishonoredvr ↔ sofvr | 1 |
| sofvr ↔ swat4vr | 1 |
| dishonoredvr ↔ ss2vr | 1 |
| farcry2vr ↔ ss2vr | 1 |
| dishonoredvr ↔ somavr | 1 |
| dishonoredvr ↔ farcry2vr | 1 |
| ss2vr ↔ swat4vr | 1 |
| farcry2vr ↔ preyvr | 1 |
| farcry2vr ↔ sims4vr | 1 |

## Concepts that bridge projects

| Concept | Projects |
|---|---|
| Stereo Rendering Progression Ladder | 5 — dishonoredvr, mohvr, sims4vr, sofvr, swat4vr |
| Address and Offset Registry | 4 — bioshockvr, preyvr, sims4vr, swat4vr |
| Asymmetric Frustum / Projection | 4 — preyvr, sims4vr, somavr, swat4vr |
| Camera Ownership and Takeover | 4 — preyvr, sims4vr, somavr, ss2vr |
| Engine: World Scale | 4 — bioshockvr, preyvr, sims4vr, ss2vr |
| Frustum and Culling Adjustment | 4 — bioshockvr, preyvr, somavr, ss2vr |
| Input and Locomotion Mapping | 4 — bioshockvr, preyvr, somavr, ss2vr |
| Native UI and HUD Overlay | 4 — bioshockvr, somavr, ss2vr, swat4vr |
| Runtime Simulation Environment | 4 — dishonoredvr, farcry2vr, somavr, ss2vr |
| Tooling: XR Simulation / Tape | 4 — farcry2vr, sims4vr, somavr, swat4vr |
| Viewmodel and Hand Pose Control | 4 — bioshockvr, preyvr, somavr, ss2vr |
| Comfort: Blackout / Vignette | 3 — bioshockvr, somavr, ss2vr |
| Depth Buffer Submission | 3 — bioshockvr, somavr, ss2vr |
| Failure and Bug Tracking | 3 — mohvr, sims4vr, sofvr |
| Inverse Kinematics for Arms | 3 — bioshockvr, preyvr, somavr |
| Pose: Recentering and Calibration | 3 — bioshockvr, somavr, ss2vr |
| Scene Re-entry Rendering | 3 — mohvr, sims4vr, swat4vr |
| Stereo Rendering Strategy: Alternate-Eye Rendering | 3 — farcry2vr, preyvr, swat4vr |
| UI: HUD Stereo Parallax / Curvature | 3 — bioshockvr, somavr, ss2vr |
| UI: Virtual Cursor / Ray Pointer | 3 — preyvr, somavr, ss2vr |
| Viewmodel Depth and Occlusion | 3 — bioshockvr, somavr, ss2vr |
| Architecture: Sequential Re-entry | 2 — preyvr, swat4vr |
| Bug: x87 Precision Trap | 2 — dishonoredvr, swat4vr |
| Comfort Vignette | 2 — somavr, ss2vr |
| Graphics: Render State Capture | 2 — somavr, ss2vr |
| Haptic Feedback Bridge | 2 — somavr, ss2vr |
| Input Injection: Mouse Emulation | 2 — bioshockvr, ss2vr |
| Input: Haptic Feedback Bridge | 2 — bioshockvr, somavr |
| Physical Interaction and Grabbing | 2 — somavr, ss2vr |
| Physics: VR Manipulation / Grabbing | 2 — somavr, ss2vr |
| Recenter and Calibration | 2 — bioshockvr, somavr |
| Snap Turn Implementation | 2 — bioshockvr, ss2vr |
| Stereo Rendering Strategy: Native Re-entry | 2 — mohvr, sofvr |
| Weapon: Two-Handed Handling | 2 — somavr, ss2vr |

## Rejections

| Reason | Count |
|---|---:|
| `group_kept` | 34 |
| `group_single_project` | 1 |
| `edge_kept` | 126 |
| `edge_same_project` | 10 |
| `edge_self_loop` | 0 |
| `edge_duplicate` | 0 |
| `member_invented` | 6 |

Labels the model returned that exist in no graph (6), rejected rather than linked:

- ss2vr: Known Symptom Classes
- somavr: 0.511-recenter
- somavr: stereo R3 alternate-eye
- ss2vr: stereo R2 per-draw replay
- bioshockvr: stereo R2 per-draw replay
- farcry2vr: stereo R2 per-draw replay
