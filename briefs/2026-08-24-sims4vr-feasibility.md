# Brief: Sims 4 VR — feasibility, go/no-go, and the deciding experiment

**Date:** 2026-08-24 · **Audience:** whoever picks up `D:\Dev Debug\Sims4VR\` ·
**Author:** cross-project review, written before the game was installed

**Target:** The Sims 4 (current retail, D3D11) · **Goal:** a **god-view** VR mod done *properly* —
real per-eye stereo, not alternate-eye reprojection.

> **Status of this document.** Everything in §1–§3 is derived from the **surviving source of the
> original mod** plus the playbook. **The game was not installed when this was written**, so every
> binary-side claim is inference and is labelled as such. §4 is the experiment that converts it into a
> decision. Do §4 before believing §1.

---

## 1. Verdict — conditional GO

**The condition is precondition 1 from [ch17](../docs/17-teardown-fc2vr-native-stereo.md): does the
engine render its world more than once per frame?**

Everything else about this target is favourable — unusually so. If the answer to that one question is
no, "properly" is off the table for a closed engine with no SDK, and the only remaining routes are the
ones already rejected.

| Outcome of §4 | Verdict |
|---|---|
| A second **full-quality** scene render exists | **GO.** Best-anchored, least-scoped target in the fleet |
| A second render exists but is **reduced** | **GO, harder.** Cyberpunk's position — *proof, not vehicle*. You need your own full-quality view |
| No second render | **NO-GO on "properly."** |

## 2. Why this target is unusually good

### 2.1 The anchoring problem is already solved — by construction

This is the finding that changes the estimate, and it is the opposite of every other project here.

The original mod does **not** hardcode a camera address. It reads the authoritative camera position from
Sims 4's own Python API, then **scans memory for a struct containing that value**:

```python
import camera                       # Sims 4 ships this module
...
x_pos = ctypes.c_float.from_address(structpos + 96)
y_pos = ctypes.c_float.from_address(structpos + 100)
z_pos = ctypes.c_float.from_address(structpos + 104)
# ...compare against camera._camera_position, keep matches...
vrdll.set_struct_location(structpos)
```

**That re-derives itself at runtime on any build.** No signatures, no RVAs, no per-patch re-reversing —
the thing that consumes most of the effort in every other fleet project. A patch moves the struct and the
scan finds it again.

The only version-dependent assumption left is the **internal layout** (`+96/+100/+104` for x/y/z), and
even that is verifiable at runtime against the API value. See §4.1.

> **Do not inherit its ambiguity handling.** The original logs *"Too many matching structs, picking the
> last one"* and takes the final candidate. That is
> [ch11](../docs/11-re-anchoring-and-discovery.md)'s `SCAN_AMBIGUOUS` treated as a tie to break rather
> than as a finding. Report the count, require uniqueness, and fail closed.

### 2.2 The camera is officially script-reachable

EA ships a `camera` Python module and supports script mods. The original uses:

```python
camera._camera_position          camera._target_position
camera.focus_on_object_from_position(target, position)
services.object_manager()        helpers.injector    sims4.commands
```

An official, documented control surface for the exact quantity a VR mod needs is not something any other
project in this fleet has.

### 2.3 D3D11 makes the presentation layer *simpler* than the original

The original targeted D3D9 and therefore carried a Vireio-derived bridge — a **separate D3D11 device**,
surface sharing, `IDirect3DTexture9` juggling — purely to get pixels to the compositor.

**On a D3D11 game that entire layer deletes.** Hook `IDXGISwapChain::Present`, take the backbuffer
texture, hand it to an OpenXR swapchain. The fleet has written this repeatedly.

### 2.4 God-view removes most of the playbook

No hands, weapons, viewmodels, arm IK, melee, physical reload, locomotion. Chapters
[02](../docs/02-viewmodels-and-hands.md), [03](../docs/03-input-and-locomotion.md) and most of
[12](../docs/12-torso-calculations-and-ergonomics.md) simply do not apply. The remaining surface is
stereo, projection, comfort and UI — which is where the real work should go anyway.

### 2.5 The process is instrumentable from inside — ~~RenderDoc works~~

> **REVISED 2026-08-25.** I wrote "RenderDoc works, this target sits in the good row." **It did not
> attach** — the binary is wrapped by EA's activation layer (§4.1). That is the capture-viability table
> in [06](../docs/06-debugging-methodology.md) being right again: *frame capture worked out of the box on
> a minority of the fleet's targets, and failed a different way each time.* I should not have assumed
> D3D11 implied a working capture path.

What is true, and is better: **the process is instrumentable from the inside.** Frida attaches, and the
game hosts a live Python 3.7 interpreter you can drive through it. That gives you both halves — the
camera (via the game's own `camera` module) and the renderer (via D3D11 vtable hooks) — without a capture
tool and without touching a game file. §4.3a turns that into the step-4 answer.

## 3. What is against it

- **The hard part has no prior art.** The original never had real stereo. Its FOV calculation is
  commented out, `game_camera_scale = 1.1298482051491667` is a hand-tuned magic number standing in for a
  projection, and its "stereo" was *set the game to 2× headset refresh and hope alternate `Present`s land
  on alternate eyes* — unsynchronised alternate-eye with no pair latching, i.e. exactly the R3/R4 failure
  class in [ch17](../docs/17-teardown-fc2vr-native-stereo.md). **You are writing the first stereo
  renderer for this game, not porting one.**
- **Closed EA engine.** No source, no SDK, live-service, patched frequently. The value scan protects your
  *address*; it does not protect your *hooks*.
- **Perf budget.** The camera struct scan runs from a Python script mod inside the game. Whatever §4
  concludes, the per-frame cost of the discovery path needs measuring, not assuming.
- **Unknown: what a second scene render costs.** A life sim is CPU-heavy and its GPU headroom is
  untested. Cyberpunk measured two full views at ~188–200% GPU; assume similar until measured.

## 4. The deciding experiment

**Run steps 1–3 first — they are cheap and they de-risk step 4's setup. Step 4 is the go/no-go.**

### 4.1 Confirm the anchoring still works · ~45 min

> **CORRECTED 2026-08-25 by the Sims4VR agent, from the installed game.** Two checks below were wrong
> as written. Both corrections are recorded here rather than silently edited, because *why* they were
> wrong is the useful part.

| Check | How | Pass |
|---|---|---|
| Architecture | `dumpbin /headers TS4_x64.exe` | `8664 machine (x64)` |
| Graphics API | ~~`dumpbin /imports`~~ → **the live process module list** | `d3d11.dll` + `dxgi.dll` loaded |
| `camera` module intact | **Static:** extract `camera.pyc` from `Data\Simulation\Gameplay\simulation.zip` and read its string table. **Live:** Frida → `PyRun_SimpleString` | `_camera_position`, `_target_position`, `focus_on_object_from_position` present |

**Why the import check fails.** `TS4_x64.exe`'s import table has **one entry** — `Core/Activation64.dll`,
EA's activation layer — plus a non-standard `.ooa` section. Every graphics symbol is resolved by name at
runtime; `D3D11CreateDevice`, `D3D11CreateDeviceAndSwapChain` and `CreateDXGIFactory1` sit in the data
section as `GetProcAddress` arguments. **A one-entry import table and a non-standard section mean the
binary is wrapped/protected**, which matters far beyond this check — it is the likely reason a
frame-capture injector will struggle to attach (see §4.3a).

**Why the console check is not needed.** The game ships a live **Python 3.7** interpreter
(`python37_x64.dll`, `Py_IsInitialized()` returns 1). Frida can drive it directly through
`PyGILState_Ensure` → `PyRun_SimpleString` → `PyGILState_Release`, with **no script mod installed, no
in-game console, and no game file touched** — a cleaner satisfaction of hard rule 1 than the original
mod's approach. Resolve those exports **by name every run**; the addresses are session-scoped.

**Also revised:** `TS4_DX9_x64.exe` ships alongside, same version. The 2024 D3D9→D3D11 move did **not**
remove the D3D9 path; it remains as a shipped fallback binary. Whether it is a full renderer or a stub is
unverified — but if it is real, it is a second, possibly easier target.


| Struct layout intact | Run the original's discovery path | A struct is found whose `+96/+100/+104` track the API value |
| **Uniqueness** | Log the candidate **count**, do not pop the last | **Record the number.** If >1, that is a finding to resolve, not a tie to break |

If the layout has moved, re-derive it the same way: the API value is ground truth, so scan for the triple
and read back the offset. Record it in `ADDRESS_REGISTRY.md` as a *layout*, never as an address.

### 4.2 Establish the flat baseline capture · ~30 min

Take a RenderDoc capture of **ordinary gameplay, live mode, camera stationary, nothing else on screen** —
no build mode, no CAS, no thumbnails visible. This is your control, and every later capture is read
against it.

Record: total draw count, the draw-index range of the main scene pass, its render-target dimensions and
format, and roughly where the UI begins.

### 4.3 Step 4 — does the world render more than once per frame? · 1–2 hrs

**Sims 4 is an unusually promising candidate**, because a life sim generates second views constantly.
Capture each of these situations and compare against §4.2:

| Situation | Why it might be a second scene render |
|---|---|
| **Create-a-Sim** | The Sim preview is a live 3D render of a posed character |
| **Household / Sim thumbnails** | Portrait generation renders a character to a texture |
| **Build mode wall/floor preview panes** | Live material previews |
| **Mirrors** | If Sims 4 has planar reflections at all |
| **Camera transition / lot loading** | Some engines pre-render the destination |

**What you are looking for, concretely:**

```text
main scene pass    -> renders to a target at (or near) backbuffer resolution
                      large draw count, full pass set (opaque, transparent, post)

a SECOND scene pass -> a DIFFERENT render target, usually SMALL and square-ish
                       (thumbnails: 128-512 px; CAS preview: a panel-sized target)
                       reached through the SAME shaders / vertex formats as the main pass
```

**The discriminator between "a second scene render" and "a UI blit":**

- **A second scene render binds a depth buffer and draws indexed geometry** with the same vertex layouts
  as the main pass.
- **A UI blit is a handful of full-screen or quad draws** with no depth and a different shader family.

Use `list_actions` / `find_draws` to enumerate, `get_draw_call_state` on the suspect range, and
`get_pipeline_state` to confirm depth binding. `diff_draw_calls` between a main-pass draw and a suspect
one will show whether they share the pipeline.

**Record the answer either way.** A clean negative retires the whole approach and is worth as much as a
positive — see [ch08](../docs/08-project-process.md) on closing families.

### 4.3a If the capture tool will not attach — answer step 4 without it

A wrapped binary is exactly the case the playbook's
[capture-viability table](../docs/06-debugging-methodology.md) warns about: **frame capture worked out of
the box on a minority of the fleet's targets.** Do not treat a failed injector as a blocker — *a dead
capture path is a finding*, and here it has a cheap alternative.

**You already have Frida inside the process.** That is enough to answer step 4 directly, because the
question is a *counting* question, not a pixel question:

```text
hook ID3D11DeviceContext::OMSetRenderTargets   -> record (RTV ptr, width, height, format, has-depth)
hook ID3D11DeviceContext::DrawIndexed(Instanced) -> increment the count for the CURRENT RT
hook IDXGISwapChain::Present                    -> flush one frame's tally, reset
```

Per frame you then have: **how many distinct render targets received indexed geometry with a depth buffer
bound.** One = the world renders once. Two or more = precondition 1 is answered, and the second RT's
dimensions tell you immediately whether it is a thumbnail-sized pass or a full one.

Resolve the vtable slots from the live `ID3D11DeviceContext` — get the device from
`D3D11CreateDeviceAndSwapChain`'s output, or find the swapchain from the window. This is the
[bespoke-inspector route](../docs/06-debugging-methodology.md) FarCry2-VR took when RenderDoc was not
viable in a 32-bit address space, and it produced their best instrument.

**It is also strictly better than a capture for this specific question** — a capture is one frame, and
you want to watch the tally change as you enter CAS, open build mode, or a thumbnail regenerates.

### 4.4 Step 5 — is the second render full-quality? · ~1 hr

Only if §4.3 is positive. In the **same capture**, compare the two passes' pass sets:

- Does the second one run transparents, or opaque only?
- Does it run post-processing, or write straight to its target?
- Is anti-aliasing present?
- Is its resolution a policy choice (a thumbnail size) or derived from a target you could change?

**Cyberpunk's caveat applies directly:** their apartment mirror *proved* the engine schedules a second
full-scene view, and was unusable as an eye because its pass set was reduced and it was area-gated —
*proof, not vehicle*. A thumbnail pass is very likely the same shape.

**So a reduced second render still answers precondition 1** (the engine's world render is re-entrant) —
it just means you must find or create a full-quality second view rather than borrowing this one.

## 5. If it is a GO — the build order

Follow [ch17](../docs/17-teardown-fc2vr-native-stereo.md)'s ordering; each stage exposes the next one's
bug.

1. **Presentation first, mono.** DXGI `Present` hook → OpenXR swapchain, whole backbuffer to both eyes.
   Proves the pipe with zero stereo risk.
2. **Head tracking, still mono.** Drive `camera._camera_position` / orientation from the HMD pose. This
   is where god-view scale is decided — see §6.
3. **The alignment assertions from
   [ch09](../docs/09-d3d11-openxr-injection.md#the-two-eyes-dont-line-up-a-five-minute-differential-diagnosis)
   before any stereo build.** Four projects lost headset sessions to this; write the desk tests first.
4. **One eye rendering natively**, with exact camera restore and a *visible* fail-back.
5. **Freeze whatever observes the camera** — then add the second eye and **publish pairs atomically**.
6. **Pose-space validation**, sequenced ring logging **raw bit patterns**, counter pairs.

## 5a. Declare the completeness tier before building

Use the [completeness ladder](../docs/08-project-process.md#how-vr-is-it-declare-a-completeness-tier-and-ship-to-it) and put the answer in `CURRENT_STATE.md`, so the project
has a definition of done rather than an open-ended list of missing affordances.

**Recommended target: T2, with T3 as a stretch.**

- **T1** (stereo view, head rotation drives the camera) is the floor and is non-negotiable — it is what
  the whole go/no-go is about.
- **T2** (6DoF, controllers driving the game) is the natural target. A god-view observer wants to *lean
  in and look around the lot*, which is head translation — the single most valuable VR affordance for
  this genre.
- **T3** (tracked hands as objects) is where it gets interesting for a dollhouse: reaching in to place
  an object, or pointing at a Sim to select. **But it is a stretch, not a commitment**, because it needs
  interaction plumbing this target has not been surveyed for.
- **T4 is explicitly out of scope.** Adapting Sims 4's own systems for VR is a different project.

**Why declaring it matters more here than usual.** God-view removes hands, weapons, IK, melee and
locomotion from scope — which means the usual signals that a VR mod is "incomplete" are absent by design
rather than by omission. Without a declared tier, a finished T2 god-view mod will read as unfinished
against a checklist that was never relevant to it.

## 6. The one design question god-view raises

Nothing in the playbook answers this, because no fleet project is god-view.

**What is the player?** Two coherent answers, and they are different mods:

- **Dollhouse observer** — the lot is a physical model on a table in front of you. World scale is small
  (a Sim is ~10 cm), stereo separation is enormous relative to the scene, and comfort is excellent
  because you are stationary and the world is beneath you.
- **Giant / first-person-adjacent** — you are at true scale looking down. Closer to the flat game's
  framing, worse for comfort, and much more dependent on the engine's own camera limits.

**Decide this before step 2 of §5**, because it sets world scale, IPD scaling and near-plane, and those
propagate into everything after. The dollhouse reading is the one that plays to VR's strengths and is
the recommended default; the original mod attempted neither and simply put the flat camera in the
headset.

## 7. Assets you already have

| Thing | Where |
|---|---|
| Full original source + 43 commits of history | `D:\Dev Debug\Other VR mods\sims4-vr\` |
| The author's own camera-scale constants and FOV notes | `.../docs/explore-files/main.py` |
| A prior analysis of the camera interface | `.../docs/explore-analysis/camera-interface-explained.md` |
| Vireio-derived D3D9 interop (reference only — deletes on D3D11) | `.../docs/explore-files/OpenVR-DirectMode.cpp.txt` |

**Note:** the upstream repo (`convexvr/sims4-vr`) is **deleted**. The copy in
`Other VR mods\sims4-vr\` appears to be the only surviving public copy, carried as a clone-and-push with
full history. Mirror it before relying on it.

---

**Related:** [17 · Native stereo](../docs/17-teardown-fc2vr-native-stereo.md) ·
[09 · D3D11 & OpenXR injection](../docs/09-d3d11-openxr-injection.md) ·
[11 · RE anchoring](../docs/11-re-anchoring-and-discovery.md) ·
[18 · Beyond the native injector](../docs/18-beyond-the-native-injector.md) ·
[Cross-project index](../docs/cross-project-index.md)
