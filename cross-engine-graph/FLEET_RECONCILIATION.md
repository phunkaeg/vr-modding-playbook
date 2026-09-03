# Fleet reconciliation report

Generated 2026-09-03 by `tools/reconcile_fleet.py`.

Cross-project edges carry `relation: same_concept_as` with the concept name and a
one-line reason, and are graded `INFERENCE` - a model proposed them from labels alone.
**Every node is a lead with provenance, not evidence.** Go read the document it names.

## Totals

- projects reconciled: **8**
- nodes: **2,032** (all namespaced `project::id`), of which **32** are concept nodes
- intra-project links: **880**
- cross-project links: **192**
- concept→implementation links: **124**
- distinct concepts bridging 2+ projects: **32**

Concept nodes exist because graphify seeds a query by **lexical** match on labels.
A question in plain English ("stop geometry being culled") matches no engine symbol
and seeds on noise; a concept node carries the plain-English name and reason, so the
question lands on it and every project's implementation is one `instance_of` hop away.

## Per-project coverage

| Project | Nodes | Intra links | Cross-project edges | Reachable from |
|---|---:|---:|---:|---|
| **ss2vr** | 659 | 225 | 76 | bioshockvr, dishonoredvr, farcry2vr, preyvr, sims4vr, somavr, swat4vr |
| **bioshockvr** | 435 | 247 | 71 | dishonoredvr, farcry2vr, preyvr, sims4vr, somavr, ss2vr, swat4vr |
| **somavr** | 369 | 130 | 72 | bioshockvr, dishonoredvr, farcry2vr, preyvr, sims4vr, ss2vr, swat4vr |
| **preyvr** | 169 | 92 | 45 | bioshockvr, dishonoredvr, farcry2vr, sims4vr, somavr, ss2vr, swat4vr |
| **dishonoredvr** | 64 | 38 | 26 | bioshockvr, farcry2vr, preyvr, sims4vr, somavr, ss2vr, swat4vr |
| **farcry2vr** | 142 | 78 | 41 | bioshockvr, dishonoredvr, preyvr, sims4vr, somavr, ss2vr, swat4vr |
| **swat4vr** | 107 | 39 | 36 | bioshockvr, dishonoredvr, farcry2vr, preyvr, sims4vr, somavr, ss2vr |
| **sims4vr** | 55 | 31 | 17 | bioshockvr, dishonoredvr, farcry2vr, preyvr, somavr, ss2vr, swat4vr |

## Project pairs

| Pair | Shared-concept edges |
|---|---:|
| bioshockvr ↔ ss2vr | 20 |
| somavr ↔ ss2vr | 19 |
| bioshockvr ↔ somavr | 18 |
| preyvr ↔ somavr | 11 |
| bioshockvr ↔ farcry2vr | 11 |
| preyvr ↔ ss2vr | 10 |
| farcry2vr ↔ somavr | 9 |
| ss2vr ↔ swat4vr | 9 |
| farcry2vr ↔ ss2vr | 9 |
| bioshockvr ↔ preyvr | 8 |
| somavr ↔ swat4vr | 8 |
| bioshockvr ↔ swat4vr | 7 |
| dishonoredvr ↔ preyvr | 6 |
| dishonoredvr ↔ ss2vr | 5 |
| dishonoredvr ↔ somavr | 5 |
| farcry2vr ↔ preyvr | 5 |
| bioshockvr ↔ dishonoredvr | 4 |
| sims4vr ↔ ss2vr | 4 |
| farcry2vr ↔ swat4vr | 4 |
| bioshockvr ↔ sims4vr | 3 |
| preyvr ↔ swat4vr | 3 |
| sims4vr ↔ swat4vr | 3 |
| sims4vr ↔ somavr | 2 |
| preyvr ↔ sims4vr | 2 |
| dishonoredvr ↔ swat4vr | 2 |
| dishonoredvr ↔ sims4vr | 2 |
| dishonoredvr ↔ farcry2vr | 2 |
| farcry2vr ↔ sims4vr | 1 |

## Concepts that bridge projects

| Concept | Projects |
|---|---|
| Camera and Viewpoint Ownership | 7 — bioshockvr, dishonoredvr, preyvr, sims4vr, somavr, ss2vr, swat4vr |
| Camera and View Ownership | 6 — bioshockvr, dishonoredvr, farcry2vr, preyvr, somavr, ss2vr |
| Frustum and Culling Adjustment | 6 — bioshockvr, dishonoredvr, farcry2vr, preyvr, somavr, ss2vr |
| Frame Capture and Trace Logging | 5 — bioshockvr, farcry2vr, sims4vr, ss2vr, swat4vr |
| HUD and UI Spatialization | 5 — bioshockvr, sims4vr, somavr, ss2vr, swat4vr |
| OpenXR Runtime Integration | 5 — bioshockvr, dishonoredvr, preyvr, somavr, ss2vr |
| Project Status Documentation | 5 — bioshockvr, farcry2vr, somavr, ss2vr, swat4vr |
| Weapon and Viewmodel Pose Handoff | 5 — bioshockvr, farcry2vr, preyvr, somavr, ss2vr |
| Frame Boundary Hooking | 4 — bioshockvr, dishonoredvr, preyvr, somavr |
| Graphics API Hooking | 4 — bioshockvr, farcry2vr, preyvr, somavr |
| Input Injection and Locomotion | 4 — bioshockvr, farcry2vr, somavr, ss2vr |
| Input and Locomotion Bridge | 4 — bioshockvr, farcry2vr, somavr, ss2vr |
| Interaction and Selection Rays | 4 — preyvr, somavr, ss2vr, swat4vr |
| UI and HUD Overlay Management | 4 — bioshockvr, somavr, ss2vr, swat4vr |
| VR Simulation/Testing Tool | 4 — dishonoredvr, preyvr, sims4vr, ss2vr |
| Viewmodel Pose and Hand Tracking | 4 — bioshockvr, farcry2vr, somavr, ss2vr |
| World Ray-Trace / Object Selection | 4 — preyvr, somavr, ss2vr, swat4vr |
| Address and Offset Registry | 3 — bioshockvr, farcry2vr, swat4vr |
| D3D9 to Modern API Interop | 3 — dishonoredvr, farcry2vr, swat4vr |
| Eye Height and Floor Calibration | 3 — bioshockvr, ss2vr, swat4vr |
| Physical Melee Interaction | 3 — bioshockvr, preyvr, ss2vr |
| Recentering and Calibration | 3 — bioshockvr, somavr, ss2vr |
| Stereo Rendering Strategy (Alternate Eye / AFR) | 3 — somavr, ss2vr, swat4vr |
| Stereo Rendering Strategy (Alternate Frame Rendering) | 3 — farcry2vr, preyvr, somavr |
| Stereo Rendering Strategy (Per-Draw Replay) | 3 — bioshockvr, farcry2vr, ss2vr |
| Comfort Vignette | 2 — somavr, ss2vr |
| Comfort and Vignette | 2 — bioshockvr, ss2vr |
| Depth Buffer Reprojection | 2 — bioshockvr, somavr |
| Haptic Feedback Bridge | 2 — bioshockvr, somavr |
| Physical Interaction and Grabbing | 2 — somavr, ss2vr |
| Snap Turning | 2 — bioshockvr, ss2vr |
| World and Unit Scaling | 2 — bioshockvr, ss2vr |

## Rejections

| Reason | Count |
|---|---:|
| `group_kept` | 33 |
| `group_single_project` | 1 |
| `edge_kept` | 192 |
| `edge_same_project` | 4 |
| `edge_self_loop` | 0 |
| `edge_duplicate` | 0 |
| `member_invented` | 2 |

Labels the model returned that exist in no graph (2), rejected rather than linked:

- somavr: 0.42.0 native-gameplay-haptics
- somavr: 0.51.0 comfort-vignette
