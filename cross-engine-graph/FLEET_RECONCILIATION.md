# Fleet reconciliation report

Generated 2026-09-18 by `tools/reconcile_fleet.py`.

Cross-project edges carry `relation: same_concept_as` with the concept name and a
one-line reason, and are graded `INFERENCE` - a model proposed them from labels alone.
**Every node is a lead with provenance, not evidence.** Go read the document it names.

## Totals

- projects reconciled: **10**
- nodes: **2,545** (all namespaced `project::id`), of which **44** are concept nodes
- intra-project links: **1,094**
- cross-project links: **299**
- concept→implementation links: **181**
- distinct concepts bridging 2+ projects: **44**

Concept nodes exist because graphify seeds a query by **lexical** match on labels.
A question in plain English ("stop geometry being culled") matches no engine symbol
and seeds on noise; a concept node carries the plain-English name and reason, so the
question lands on it and every project's implementation is one `instance_of` hop away.

## Per-project coverage

| Project | Nodes | Intra links | Cross-project edges | Reachable from |
|---|---:|---:|---:|---|
| **ss2vr** | 704 | 285 | 128 | bioshockvr, dishonoredvr, farcry2vr, mohvr, preyvr, sims4vr, sofvr, somavr, swat4vr |
| **bioshockvr** | 435 | 252 | 96 | dishonoredvr, farcry2vr, mohvr, preyvr, sims4vr, sofvr, somavr, ss2vr, swat4vr |
| **somavr** | 410 | 138 | 114 | bioshockvr, dishonoredvr, farcry2vr, mohvr, preyvr, sims4vr, sofvr, ss2vr, swat4vr |
| **preyvr** | 465 | 194 | 105 | bioshockvr, dishonoredvr, farcry2vr, mohvr, sims4vr, sofvr, somavr, ss2vr, swat4vr |
| **dishonoredvr** | 64 | 38 | 24 | bioshockvr, farcry2vr, preyvr, sims4vr, somavr, ss2vr |
| **farcry2vr** | 146 | 79 | 47 | bioshockvr, dishonoredvr, mohvr, preyvr, sims4vr, somavr, ss2vr, swat4vr |
| **swat4vr** | 111 | 39 | 35 | bioshockvr, farcry2vr, mohvr, preyvr, sims4vr, sofvr, somavr, ss2vr |
| **sims4vr** | 75 | 27 | 24 | bioshockvr, dishonoredvr, farcry2vr, preyvr, sofvr, somavr, ss2vr, swat4vr |
| **mohvr** | 39 | 17 | 18 | bioshockvr, farcry2vr, preyvr, somavr, ss2vr, swat4vr |
| **sofvr** | 52 | 25 | 7 | bioshockvr, preyvr, sims4vr, somavr, ss2vr, swat4vr |

## Project pairs

| Pair | Shared-concept edges |
|---|---:|
| somavr ↔ ss2vr | 34 |
| preyvr ↔ ss2vr | 28 |
| bioshockvr ↔ ss2vr | 28 |
| preyvr ↔ somavr | 27 |
| bioshockvr ↔ somavr | 26 |
| bioshockvr ↔ preyvr | 20 |
| farcry2vr ↔ ss2vr | 11 |
| farcry2vr ↔ preyvr | 11 |
| ss2vr ↔ swat4vr | 9 |
| farcry2vr ↔ somavr | 8 |
| bioshockvr ↔ farcry2vr | 7 |
| sims4vr ↔ ss2vr | 6 |
| bioshockvr ↔ swat4vr | 6 |
| somavr ↔ swat4vr | 6 |
| preyvr ↔ swat4vr | 6 |
| dishonoredvr ↔ ss2vr | 5 |
| dishonoredvr ↔ somavr | 5 |
| dishonoredvr ↔ preyvr | 5 |
| mohvr ↔ ss2vr | 5 |
| sims4vr ↔ somavr | 4 |
| preyvr ↔ sims4vr | 4 |
| dishonoredvr ↔ farcry2vr | 3 |
| dishonoredvr ↔ sims4vr | 3 |
| mohvr ↔ somavr | 3 |
| mohvr ↔ preyvr | 3 |
| bioshockvr ↔ mohvr | 3 |
| farcry2vr ↔ swat4vr | 3 |
| bioshockvr ↔ dishonoredvr | 3 |
| farcry2vr ↔ sims4vr | 2 |
| sofvr ↔ ss2vr | 2 |
| sims4vr ↔ swat4vr | 2 |
| farcry2vr ↔ mohvr | 2 |
| mohvr ↔ swat4vr | 2 |
| bioshockvr ↔ sims4vr | 2 |
| sofvr ↔ swat4vr | 1 |
| sims4vr ↔ sofvr | 1 |
| bioshockvr ↔ sofvr | 1 |
| sofvr ↔ somavr | 1 |
| preyvr ↔ sofvr | 1 |

## Concepts that bridge projects

| Concept | Projects |
|---|---|
| Camera and View Matrix Overrides | 7 — bioshockvr, dishonoredvr, farcry2vr, preyvr, sims4vr, somavr, ss2vr |
| OpenXR Runtime Simulation | 6 — dishonoredvr, farcry2vr, preyvr, sims4vr, somavr, ss2vr |
| VR Simulation and Testing Harness | 6 — bioshockvr, dishonoredvr, preyvr, sims4vr, somavr, ss2vr |
| Camera Ownership Hijack | 5 — dishonoredvr, farcry2vr, preyvr, somavr, ss2vr |
| Camera and View Ownership | 5 — bioshockvr, farcry2vr, preyvr, somavr, ss2vr |
| Frame Boundary and Present Hooking | 5 — bioshockvr, preyvr, sofvr, somavr, ss2vr |
| Frame Boundary and Present Hooks | 5 — bioshockvr, preyvr, somavr, ss2vr, swat4vr |
| Frustum and Projection Correction | 5 — bioshockvr, preyvr, somavr, ss2vr, swat4vr |
| HUD and UI Separation | 5 — bioshockvr, mohvr, preyvr, somavr, ss2vr |
| Input Mapping and Locomotion | 5 — bioshockvr, farcry2vr, preyvr, somavr, ss2vr |
| OpenXR Runtime Bridge | 5 — bioshockvr, dishonoredvr, preyvr, somavr, ss2vr |
| Stereo Rendering Strategy | 5 — bioshockvr, mohvr, somavr, ss2vr, swat4vr |
| Viewmodel Pose Control | 5 — bioshockvr, farcry2vr, preyvr, somavr, ss2vr |
| Weapon Aim Detachment | 5 — bioshockvr, farcry2vr, mohvr, preyvr, ss2vr |
| Weapon Viewmodel Detachment | 5 — bioshockvr, farcry2vr, preyvr, ss2vr, swat4vr |
| Failure and Bug Tracking | 4 — farcry2vr, mohvr, ss2vr, swat4vr |
| Frame Timing and Pacing | 4 — preyvr, somavr, ss2vr, swat4vr |
| Frustum Culling Adjustment | 4 — mohvr, preyvr, somavr, ss2vr |
| Frustum and Culling Management | 4 — preyvr, sims4vr, somavr, ss2vr |
| HUD Spatialization | 4 — bioshockvr, somavr, ss2vr, swat4vr |
| Haptic Feedback Integration | 4 — bioshockvr, preyvr, somavr, ss2vr |
| Input Emulation and Locomotion | 4 — bioshockvr, preyvr, somavr, ss2vr |
| Input Event Injection | 4 — bioshockvr, preyvr, somavr, ss2vr |
| Inverse Kinematics and Hand Rigging | 4 — bioshockvr, preyvr, somavr, ss2vr |
| Physical Interaction and Grabbing | 4 — farcry2vr, preyvr, somavr, ss2vr |
| Project Documentation and Knowledge Base | 4 — bioshockvr, preyvr, somavr, ss2vr |
| Stereo Rendering Re-entry | 4 — sims4vr, sofvr, ss2vr, swat4vr |
| Stereo Rendering Strategy: Alternate-Eye / Sequential | 4 — farcry2vr, preyvr, somavr, swat4vr |
| UI and HUD Virtualization | 4 — bioshockvr, preyvr, somavr, ss2vr |
| Viewmodel and Weapon Hand-off | 4 — bioshockvr, farcry2vr, preyvr, ss2vr |
| Address and Offset Registry | 3 — bioshockvr, preyvr, swat4vr |
| Comfort Vignette | 3 — preyvr, somavr, ss2vr |
| Comfort and Vignette Systems | 3 — bioshockvr, somavr, ss2vr |
| Culling and Frustum Visibility | 3 — bioshockvr, somavr, ss2vr |
| Depth Buffer Reprojection | 3 — bioshockvr, somavr, ss2vr |
| Interaction and Selection Rays | 3 — preyvr, somavr, ss2vr |
| Inverse Kinematics (IK) for Arms | 3 — bioshockvr, preyvr, somavr |
| Melee Swing Detection | 3 — bioshockvr, somavr, ss2vr |
| Physical Interaction Raycasting | 3 — preyvr, somavr, ss2vr |
| Pose Calibration | 3 — bioshockvr, somavr, ss2vr |
| Recenter and Calibration Logic | 3 — bioshockvr, somavr, ss2vr |
| World Scale Calibration | 3 — sims4vr, ss2vr, swat4vr |
| Haptic Feedback Bridge | 2 — bioshockvr, somavr |
| World Scale and Unit Conversion | 2 — bioshockvr, ss2vr |

## Rejections

| Reason | Count |
|---|---:|
| `group_kept` | 45 |
| `group_single_project` | 1 |
| `edge_kept` | 299 |
| `edge_same_project` | 0 |
| `edge_self_loop` | 0 |
| `edge_duplicate` | 0 |
| `member_invented` | 1 |

Labels the model returned that exist in no graph (1), rejected rather than linked:

- dishonoredvr: The D3D11 x87 precision trap, and the adapter assertion we w
