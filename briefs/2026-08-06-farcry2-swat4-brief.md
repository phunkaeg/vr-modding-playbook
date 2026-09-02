# Brief: FarCry2-VR and Swat4-VR — cross-project review

**Date:** 2026-08-06 · **Audience:** the agents working `D:\Dev Debug\FarCry2-vr\` and
`D:\Dev Debug\Swat4-VR\` · **Author:** cross-project review across the seven-mod fleet

Read this once, act on §4 and §5, then go back to your own `CURRENT_STATE.md`.

---

## 1. Where you sit in the fleet

| Mod | Engine | API | Bits | Stage |
| --- | --- | --- | --- | --- |
| **SS2VR** | Dark / KEX (1998) | D3D11 | 32 | Most advanced — stereo, hands, melee, parry, teleport, climbing |
| **SOMAVR** | HPL3 (2015) | **OpenGL 4.6** | 64 | Advanced — AFR stereo, native hands/interaction, comfort |
| **BioshockVR** | **Vengeance / UE2.5** (2007) | D3D11 | 32 | Advanced — private-eye stereo, native AimIK, HUD tee |
| *(bioshock-vr)* | *same engine, other author* | *D3D11* | *32* | *Released & playable — see playbook [13]* |
| **PreyVR** | CryEngine | D3D11 | 64 | Frame observer + live probe protocols |
| **DishonoredVR** | **UE3** | **D3D9** | 32 | Phase 0.7 — caller-gated camera probe |
| **FarCry2-VR** | **Dunia** | **D3D9 / D3D10** | 32 | P0→P1 — injection proven, rung 2 partly live |
| **Swat4-VR** | **Vengeance / UE2.5** (2005) | **D3D9** | 32 | Phase 0→1 — engine hooks live, nothing mutated |

Two structural facts follow from that table, and they are the whole point of this brief:

- **You are both on graphics APIs the playbook does not cover.** D3D9 and D3D10 have **no OpenXR
  graphics binding at all**. Three of the seven mods are now D3D9 (SWAT4, Dishonored, FarCry2's
  primary). You are the projects generating that knowledge, not consuming it.
- **SWAT 4 and BioShock are the same engine family.** This is under-exploited by an enormous margin.
  See §2.

---

## 2. THE HEADLINE: the Vengeance flow should run *backwards*

**Correction to my first draft of this brief.** I expected to find that Swat4-VR had under-exploited
its engine relationship to BioShock. The opposite is true, and it is worth stating plainly:
**Swat4-VR has already mined that relationship better than this brief was going to suggest.** Its
`ENGINE_NOTES_SWAT4.md` reads chapter 13 as *"near-target documentation rather than a distant
analogy,"* correctly applies chapter 13's own counter-rule (*"SWAT 4 is an earlier, simpler build —
several of BioShock's hardest problems may simply not exist here; test before porting"*), and has
already used it to get ahead of BioShock's single longest failure arc.

So the useful finding is the reverse one: **SWAT 4 is where the Vengeance engine is *readable*, and
the two BioShock projects are flying blind on things SWAT 4 can just look up.**

Concrete examples already in Swat4-VR's notes that BioshockVR needs:

- **`DrawOffset = 90 / FirstPersonFOV × Hands.PlayerViewOffset`** — the foreground-lens compensation
  relationship, *in readable UnrealScript*, with `ZoomAlpha` as the ADS blend term. BioShock spent
  **three sessions** reverse-engineering the equivalent, shipped a counter-model, and then discovered
  the counter-model *was* the defect. Here it is one line of source.
- **The viewmodel is a separate render pass with its own FOV** — verified in SWAT 4 by direct
  observation (the two FOV sliders move independently; the world FOV needs a level re-entry while the
  viewmodel FOV updates live). Knowing that shape *before* touching the viewmodel is exactly what
  BioShock lacked.
- **`FPFOV` is an `exec` function**, so the viewmodel FOV is drivable at runtime through
  `UViewport::Exec` with **no hook at all**.
- **The `DefaultFOV` 85° clamp**: `FOVBias = tan(min(FOV, DefaultFOV)/2)`, which silently capped
  everything — setting 120 appeared to do nothing. That is a Vengeance-family gotcha BioShock's FOV
  work would want to know about.
- **`BaseFOV` reaches `FPlayerSceneNode`'s constructor 1:1** — no bias, no scaling, no mapping,
  verified against the live constructor.

**Action for Swat4-VR:** you are already logging these well. Add one explicit step — when a finding
comes from *readable script* and has a blind-reversed counterpart in BioShock, tag it so it can be
harvested. A short `docs/VENGEANCE_SHARED_FINDINGS.md` (or a tag in `VR_FINDINGS_INDEX.md`) that
BioshockVR's agent can read directly would be worth more to the fleet than another RE session.

**Action for the BioshockVR agent (separate brief, but flagging it here):** read
`D:\Dev Debug\Swat4-VR\docs\ENGINE_NOTES_SWAT4.md` §"FOV map" and §"the weapon model is a separate
render pass" before any further foreground-FOV work.

### The seam table still stands

What follows is *not* news to Swat4-VR — it is a cross-reference table, kept because it is useful to
have the correspondences in one place, and because FarCry2's agent benefits from seeing how dense a
sibling-engine relationship can get.

| Swat4-VR found | BioShock projects already did this |
| --- | --- |
| `APlayerController::eventPlayerCalcView` | **Both** hook it. It is the universal per-frame application point — bone writes, actor writes, FOV writes, input driving. Fires *after* the engine's tick, so **you are last writer of the frame** — no placement hook needed |
| `FPlayerSceneNode(UViewport*, FRenderTarget*, AActor*, FVector, FRotator, float FOV)` | BioshockVR: this constructor **is** the native camera/FOV boundary. It takes *transient* position/rotator/world-FOV/foreground-FOV args, writes them, then builds the frustum. **Mutate only the transient args, never persistent memory** |
| `FCameraSceneNode`, `FMirrorSceneNode`, `FDrawPortalSceneNode`, `FShadowSceneNode` | Exactly the secondary-view provenance problem in playbook [09]. BioshockVR's "cyan Rapture shell" was a bounded secondary view whose scissor got expanded. **Preserve each source view's viewport and scissor** |
| `UGameEngine::Draw(UViewport*, ...)` fires **1× per rendered frame** | **This is bioshock-vr's BioShock 2 stereo seam, verbatim.** Their BS2 adapter hooks `UGameEngine::Draw` and *calls it twice* per frame for SequentialReentry |
| `UViewport::Exec(const wchar_t*, FOutputDevice&)` | bioshock-vr's highest-leverage single hook: the console `SET <class> <property> <value>` handler makes **any script property writable by name** — no offset, no bitmask, no reflection walking. It also writes the class *default*, so objects spawned after a level load inherit it |
| Export RVAs are incremental-link thunks; callers bypass them | bioshock-vr hit the identical trap on the script side: hooking all four aim `exec` thunks caught **ZERO** calls, because native C++ callers go straight to the implementation |

**Action:** before your next RE session, read these three, in this order:

1. `D:\Dev Debug\VR Modding\docs\13-teardown-bioshock-vr.md` — the full teardown.
2. `D:\Dev Debug\bioshock-vr\docs\bioshock1\ENGINE_NOTES.md` (152 KB) — MIT, and the single densest
   Vengeance-engine knowledge base in existence. Their §"derivation recipes" transfer wholesale.
3. `D:\Dev Debug\BioshockVR\docs\RE_FINDINGS.md` + `ADDRESS_REGISTRY.md` — our own.

**Licensing / hygiene:** `bioshock-vr` is MIT — techniques and code may be adapted **with an
attribution comment in the file**. Their own standing rule applies with extra force here:
**never copy a number between titles.** Same engine tree, different link, twelve years and two
studios apart. Derive fresh; use their work for *shapes, names and method*.

**And it flows back.** SWAT 4 ships **1,492 `.uc` UnrealScript source files** plus the full
SWAT: Elite Force source (`D:\Dev Debug\SWATEliteForce\`). That is the closest thing to BioShock's
engine source that exists publicly. Anything you learn about `FPlayerSceneNode` semantics, the
camera-effect chain, or the HUD from *readable script* is directly useful to BioshockVR — which has
been reversing the same shapes blind. **Log those findings in a form BioshockVR can consume.**

---

## 3. What you are already doing right (do not regress these)

Both projects are, honestly, better set up at this stage than the mature three were. Specifically:

- **Swat4-VR is, at its stage, the best-run project in the fleet.** Its `UNVERIFIED`-as-load-bearing
  convention, its R1–R8 battery with explicit `ANSWERED`/`PARTLY`/`OPEN` states, and its use of
  chapter 13 as near-target prior art are all things the other six should copy. Its FOV work in
  particular — finding the `DefaultFOV` clamp by A/B rather than by reading config, and refusing to
  resolve the question from config files at all because *"the values disagree with each other and with
  the sliders; the constructor hook is ground truth"* — is textbook playbook [06].
- **Both `CLAUDE.md` files are built against the playbook** and already encode: build self-ID,
  RVAs-are-evidence/signatures-are-authority, fail-closed, default-off + revert knob, config
  whitelist lockstep, config identity logging, generated version strings, pure math in a
  desk-testable module, one hypothesis per headset build, failed-experiment-reverted-not-flagged,
  strike-through-not-delete.
- **The doc spine is complete on both** (`CURRENT_STATE`, `FAILURE_REGISTRY`, `DECISION_LOG`,
  `ADDRESS_REGISTRY`, `HYPOTHESES`, de-risking battery, `VR_FINDINGS_INDEX`).
- **A de-risking battery exists on both, with named fallbacks** — exactly playbook [08]. SWAT4's
  R1–R8 table with `ANSWERED`/`PARTLY`/`OPEN` states is the best implementation of this in the fleet.
- **FarCry2 inherited hazards it had not yet hit** — the 32-bit OpenXR-MotionCompensation implicit
  layer that appears in BioshockVR's `0xC0000409` crash chain, plus the session-state gate and the
  internal-D3D re-entrancy guard. That is precisely what the playbook exists for.
- **Both record corrections with the lesson, not just the fix** (FarCry2's "corrections this session"
  blocks are exemplary — a falsified roll detector, a DPI-virtualised resolution reading, an
  offset-comparison error).
- **SWAT4's `UNVERIFIED` tag as a load-bearing convention** is a genuinely good idea the other five
  mods should copy.

No manufactured criticism follows. The gaps below are real and verified.

---

## 4. Gaps to close (verified, ranked by cost/benefit)

### 4.1 — No commits. **Fix today.**

Precisely (measured 2026-08-06):

| Project | Repo | Commits |
| --- | --- | --- |
| `FarCry2-vr` | **none at all** | — |
| `Swat4-VR` | `.git` exists | **0 — `HEAD` does not resolve** |
| `PreyVR` | `.git` exists | **0 — `HEAD` does not resolve** |
| SS2VR / SOMAVR / BioshockVR / DishonoredVR | yes | 63 / 73 / 55 / 4 |

So none of the three has a single checkpoint, whether or not `git init` was ever run.

This directly breaks rules you have already written down for yourselves:

- *"Strike through superseded work; do not delete it — a retired design is a banked fallback"* needs
  history to be meaningful.
- *"One hypothesis per headset build"* implies a checkpoint per build to revert to.
- Build attribution (which binary produced which result) is unfalsifiable without commits.
- Both of you are about to start mutating a live game process. **Checkpoint before risky work** is a
  playbook rule you currently cannot obey.

```bash
git init && git add -A && git commit -m "checkpoint: pre-mutation baseline"
```

Mind your existing `.gitignore` intent: no game-derived content, no `Ghidra/`, `RenderDoc/`,
`captures/`, `dumps/`, `logs/`, `out/`, `analysis/`, `re/`, `reference/`.

### 4.2 — No graphify graph, despite your own rules telling you to use one

Both `CLAUDE.md` files instruct the agent to run `graphify query "<topic>"` as the **first**
orientation pass, before `rg`. Neither project has a `graphify-out/`. SS2VR, SOMAVR, BioshockVR and
DishonoredVR all do.

Code-only graphing is **AST-only, free, no API key, and takes seconds**:

```bash
graphify . --update
```

Do it now; it pays back immediately at your corpus size (FarCry2: 20 docs / 333 KB / 32 source files;
SWAT4: 13 docs / 192 KB / 22 source files). Per FarCry2's own `CLAUDE.md`, do **not** graph
`reference/Far-Cry-1-Source-Full/` in a default run.

*(Note: graphing **docs** needs an LLM backend key and is a separate, deliberate run — see
`D:\Dev Debug\VR Modding\cross-engine-graph\README.md`. Code-only is the free daily driver.)*

### 4.3 — The closed flat harness is not standing up yet on either

SWAT4 has this as `R8 OPEN` and correctly identifies the consequence: *"R4's proof line is a frame
diff and is worthless without it."* FarCry2 has `scripts/` reserved for it.

**This is now the blocking dependency for your most important experiment** (§5.1). Build the three
pieces — command-file seam polled ~1 Hz, screenshot grabber, pixel differ — and **measure the
standing-still noise floor first**. For calibration: bioshock-vr's floor is 0.21–0.40 mean, with a
real change reading 2–8+. A number between those is not evidence.

SWAT4 already has `src/diag/command_file.cpp`. That is the hard part done.

### 4.4 — FarCry2: your "hooks installed correctly, never fire" bug has prior art

FarCry2's `CURRENT_STATE` reports: *"the `ID3D10Device` draw hooks are installed correctly and never
fire"*, with wrong-interface, failed-write and bad-mechanism already ruled out.

**Swat4-VR hit the identical shape three days earlier** (`F-0007`): the `IDirect3D9::CreateDevice`
hook installs at a verified-correct address and never fires while the game renders normally, and the
mechanism self-tests fine. Their hypothesis is that **the game holds a *wrapper* object** — in their
case the `AcLayers.dll` app-compat shim wrapping `IDirect3D9`.

Their resolution generalises and you should try it: **hook the implementation, not the interface.**
Resolve the real function addresses at runtime from a throwaway device and inline-hook those. It is
wrapper-proof by construction.

Two cross-checks worth running: does an app-compat shim (`AcLayers.dll`, `apphelp.dll`) appear in
FarCry2's module list? And does the wrapper hypothesis explain why `Present` *does* work while the
draw slots do not — i.e. is `Present` reached through a different object than the draws?

Conversely, **SWAT4 should take FarCry2's device-resolution primitive**:
`IID_ID3D10DeviceChild` → `GetDevice` off a live resource is a clean, repeatable way to reach the
*real* device object rather than the one you created. FarCry2's `ComScan` is SEH-guarded and already
proven.

### 4.5 — Instruments each of you has that the other does not

| Instrument | Who has it | Who needs it |
| --- | --- | --- |
| **In-process frame inspector** (RenderDoc replacement; FarCry2 censused 2.62 M draws / 380 draw families) | FarCry2 | **SWAT4** — and it is how you find a scene-draw seam, because the thing you need is a **callstack** |
| **Standalone game-less interop experiment with a headset-free flat gate** (`experiments/r1_interop` — reads pixels back and checks them, no game, no injection) | SWAT4 | **FarCry2** — and Dishonored, which has an equivalent "game-less probe" |
| **Read-only RE script kit** (`tools/pe_symbols.py` — imports/exports with `undname` demangling) | SWAT4 | FarCry2 (has `tools/` reserved, read-only by construction) |
| **Desk-test suite that catches real bugs** (25/25 tests; caught a missing 2π wrap worth ~200° of heading error, and an inverted pitch sign) | FarCry2 | **SWAT4** — you have `src/math/` and the rule; make sure the tests exist |

### 4.6 — Smaller items

- **SWAT4: no LAA (~2 GB).** FarCry2 measured 831 MB contiguous free above 2 GB *because it is
  patched*. You are not. Budget eye targets explicitly, and expect the 32-bit trap class in playbook
  [06] — RenderDoc will fail on you, and DXGI truncates VRAM (identify adapters by LUID, not name).
- **FarCry2: the affinity-mask launch precondition is a test-validity fact.** You already treat it
  that way. Make sure the injector applies it **at process creation** and that the banner records it,
  exactly like a build hash.
- **Both: record base + RVA together.** FarCry2 already learned this the hard way (`Dunia.dll` holds
  its preferred base while the other modules relocate). SWAT4 has multiple modules too.

---

## 5. The three things that matter most next

### 5.1 — SWAT4: run the pixel proof on `UGameEngine::Draw`. This is your architecture decision.

You have `UGameEngine::Draw` located, hookable, and firing exactly 1× per rendered frame alongside
1× `FLevelSceneNode::Render` and 1× `FPlayerSceneNode::Render`. **That is the same seam bioshock-vr
doubles for BioShock 2 stereo.**

The experiment is one line of the de-risking battery: **double the call, yaw the camera, diff the
frame.** Everything in playbook [09] "can you just call the scene draw twice?" applies.

Read their failure ladder before you run it — they burned three candidates first:

- Their **render-thread drain** was dead by construction, because the camera function ran only on the
  game thread. **Confirm which thread `PlayerCalcView` runs on before choosing a seam** (your R6 is
  `OPEN` and this is why it matters).
- Their **frame submit** hooked perfectly, 1:1 with presents, args matching the camera — and doubling
  it produced **zero extra presents**, because view data was baked at *build* time. **A hook that
  fires perfectly is not the same as a hook that is the seam. Prove pixels changed.**
- Only the **scene build root** worked.

And know the price of admission: their BioShock 1 deadlocked under doubling and needed the renderer
forced inline; their BioShock 2 — with a command-ring draw path and no kick-and-wait handshake —
needed **none of that machinery**. Their standing rule: *test whether the second game has the problem
before porting the cure.* Your R6 answers which case you are in.

If it works, you skip most of the per-draw stereo long tail (playbook [14]: the mono screen-space and
temporal hazard classes largely stop arising, because the engine renders each eye natively).

### 5.2 — FarCry2: unblock the draw hooks, then classify the frame

Your blocker chain is B3 (camera write site) and the non-firing draw hooks. Take §4.4's
wrapper/implementation-hooking approach first — it is the cheapest test with the best prior art.

Then, before designing any stereo path, run playbook [14] against your frame census: **count the
screen-space and temporal passes**. You already have the inspector and 380 draw families. That count
*is* your per-draw stereo effort estimate — and if it is large, it is the quantitative argument for
scene re-entry (your DR-6) instead. Specifically check for **TAA or any temporal accumulation**: a
2008 Dunia build may well predate TAA, which would make alternate-eye far more viable for you than
for a modern target.

### 5.3 — Both: the FOV question, before any culling work

Playbook [01], via HaloVR: **if the game exposes an FOV setting, raising it widens the engine's own
culling frustum** — the entire peripheral-culling problem solved from the options menu, no hook.
Halo's fix was literally "set FOV to 120." FarCry2 already has this as an open question; SWAT4 should
add it. It is a config-only experiment and costs nothing to run.

---

## 6. What you owe the playbook

You are both generating knowledge the playbook does not have. When these land, they should come back
as a chapter:

- **D3D9 / D3D10 → OpenXR interop.** There is no OpenXR D3D9 or D3D10 binding. SWAT4 has *already
  answered this* — plain D3D9 (with `D3DPOOL_MANAGED` intact) → **D3D9On12** →
  `UnwrapUnderlyingResource` → D3D12 → `XR_KHR_D3D12_enable`, validated in-headset with a live
  per-eye-distinct stereo pair. That is a genuinely new route and three mods in this fleet need it.
- **The app-compat wrapper trap** (`AcLayers.dll` interposing on `IDirect3D9`) as a hooking hazard
  class.
- **The symbol-bearing shipping binary.** `Engine.dll` exporting **7,682 named, decorated C++
  symbols** collapses the whole anchor ladder to `GetProcAddress`. That is playbook [11] rung 2
  hitting the jackpot on a *retail* build, and it deserves a worked example.
- **The incremental-link thunk trap**: exports resolve to thunks that internal callers bypass — a
  distinct failure from the script-thunk trap already documented.
- **Prologue-scan failure #4**: `FPlayerSceneNode` starts `mov eax,[esp+28]`, no `55 8B EC`. Add it
  to the three already in [11].
