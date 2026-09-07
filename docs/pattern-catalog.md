# Pattern Catalog — atomic, reusable VR-mod solutions

Chapters explain systems. This catalog is for retrieval: search a stable ID,
copy the smallest applicable recipe, then follow the linked chapter for the
full reasoning. IDs are permanent. Retired patterns keep their ID and receive a
status note; IDs are never recycled.

These unprefixed IDs are the pattern namespace. Failure records use distinct
global IDs such as `FAIL-CAM-001`; an unqualified `CAM-001` always means the
pattern on this page.

Every pattern uses the same fields:

- **Problem** — the observable engineering problem;
- **Use when** — applicability boundary;
- **Recipe** — minimum safe implementation;
- **Proof** — evidence that distinguishes success from a near miss;
- **Trip hazard** — the failure most likely to masquerade as success.

## META-001 — Self-identifying build {#meta-001}

**Problem:** a correct change appears ineffective because different bytes ran.

**Use when:** every injected DLL, proxy, plugin, script package and helper.

**Recipe:** first log line contains version, build time, loaded absolute path,
PID, target hash and enabled feature lanes. Make the UI or flat harness expose
the same identity.

**Proof:** one log line distinguishes installed, loaded and executed.

**Trip hazard:** checking that a file exists does not prove loader precedence.
See [06](06-debugging-methodology.md).

## META-002 — Evidence-tagged finding {#meta-002}

**Problem:** a plausible hypothesis becomes an inherited “fact”.

**Use when:** documenting offsets, APIs, matrices, behavior and prior art.

**Recipe:** attach `[SPEC]`, `[SOURCE]`, `[STATIC]`, `[LIVE]`,
`[HEADSET]`, `[AUTHOR]` or `[INFERENCE]` at the claim; record the
experiment and invalidation condition.

**Proof:** another developer can reproduce or deliberately downgrade the claim.

**Trip hazard:** evidence grade is not confidence or priority.

## META-003 — Integration authority map {#meta-003}

**Problem:** possession of SDK/source/scripts is mistaken for authority to edit
and ship the retail camera/render path.

**Use when:** selecting source-owned, RE-owned or hybrid architecture.

**Recipe:** for each code layer record readable, buildable, modifiable,
redistributable and retail-compatible separately; route every planned mutation
through the layer that actually ships it.

**Proof:** `AUTHORITY_MAP.md` explains how each change reaches the user and
which closed boundary still requires binary verification.

**Trip hazard:** source can be an excellent semantic oracle while remaining an
invalid delivery route. See [PORT-01](start-new-port.md#port-01).

## META-004 — Earliest-bottleneck routing {#meta-004}

**Problem:** several plausible tasks are open and downstream feature work hides
an earlier unproven premise.

**Use when:** starting a session, inheriting a project or choosing work across a
fleet.

**Recipe:** identify the earliest uncleared gate, name its fast discriminator
and exit proof, run that experiment, then update the project and fleet
bottleneck ledgers before choosing the next task.

**Proof:** the chosen work either clears the gate or selects a documented
fallback; it does not merely add implementation behind an unresolved owner.

**Trip hazard:** severity and novelty are not dependency order. See the
[bottleneck map](bottleneck-map.md).

## META-005 — Self-expiring cross-layer publish {#meta-005}

**Problem:** an inner layer needs a fact only an outer layer knows (is the world loaded, is the melee
weapon equipped, is VR gameplay actually up), and a direct query is impossible or unsafe - wrong thread,
wrong lifetime, or it inverts the dependency.

**Use when:** any core/adapter, engine/mod or render/game split where state must cross a boundary that
calls in only one direction.

**Recipe:** the knowing layer **pushes** a timestamped value into a slot; the consuming layer reads the
slot and treats anything older than a fixed budget (BioShock-Trilogy-VR uses 500 ms) as absent. Choose
the representation so that **the expired state is the safe one**, so a publisher that stops - world
unload, feature disabled, thread died - disarms the dependent feature rather than freezing it on its
last value.

**Proof:** stop the publisher deliberately and confirm the feature disarms within the budget rather than
latching.

**Trip hazard:** a staleness budget whose expired value is the *active* one inverts the whole benefit;
and every new cross-layer fact should reuse this shape rather than inventing a private one.

## META-006 — Implement the engine's own interface before hooking one {#meta-006}

**Problem:** the VR layer is designed as a foreign renderer bolted alongside the engine, fighting it for
ownership of views, projection and render targets.

**Use when:** starting any port, and again whenever a hook turns out to be load-bearing and fragile.

**Recipe:** enumerate what the engine **already honours** before designing anything - a stereo device
interface, a view-supplier callback, a native-extension loader, a named IK facility, a console variable.
Implementing one of those puts the engine in charge of its own stereo path and inherits its lifecycle
guarantees. Four independent projects in this survey converged on it: UEVR implements Unreal's built-in
`FFakeStereoRendering` device; OpenMW-VR supplies an `UpdateViewCallback`; Vostok-VR registers a
GDExtension; PreyVR found `CreateIKLimb` and a nullable custom-view callback.

**Proof:** the engine computes per-eye views itself, and the feature survives an engine-version change
that would have moved a hook.

**Trip hazard:** the interface may exist as a stub with no obvious symbol - UEVR's target is a *fake*
stereo device shipped for the null case. Search for the concept, not for a promising function name.

**Its mirror image is [META-008](#meta-008)**, which is the same question asked from the other side: if
you are the framework, what interface should *you* publish? UEVR does both.

## META-007 — A clean early result is not evidence until the breaking mechanism is exercised {#meta-007}

**Problem:** an early test passes, the optimistic conclusion is recorded, and it survives review because
nothing has yet stressed the specific thing that would break it.

**Use when:** any "we tried it and it was fine" result, especially one that lets you skip expensive work.

**Recipe:** when a result permits the cheaper path, name the mechanism that would invalidate it and state
whether that mechanism has actually been exercised. Record the claim as *unstressed* until it has.
BioShock-Trilogy-VR's BS2 adapter tested clean on a threaded substrate and was recorded as needing no
single-threading machinery; the verdict was **refuted** later when a Draw-tail flush handshake turned up
that nobody had been looking for, and a `wait2/s` counter showed the infinite wait was entered on *every*
doubled frame. Two of three titles ultimately needed the machinery.

**Proof:** the mechanism has been exercised and counted, not merely survived - a counter reading zero by
construction beats a soak that did not happen to trigger.

**Trip hazard:** **refutations land disproportionately on the optimistic item**, because nobody
stress-tests good news. A finding that saves you work has a lower evidential bar in practice than one
that costs you work, and that asymmetry is invisible unless you name it. Weight an unstressed optimistic
claim accordingly before it becomes load-bearing in a document people read first.

## META-008 — Design the extension surface, do not leak it {#meta-008}

**Problem:** other people need to extend your mod or framework, and they end up hooking your internals -
so every refactor breaks them and you cannot change anything.

**Use when:** any framework, injector or tool intended to host game-specific companions.

**Recipe:** expose a **plain-C ABI** (function-pointer table, no C++ types, no STL across the boundary)
and keep the ergonomic C++ wrapper on the consumer side, so the contract survives a different toolchain.
Version it semantically and hand the version to the plugin so it can refuse an incompatible host. Make
the callbacks **pre/post pairs around the moments your layer changes the meaning of what the host does** -
UEVR brackets engine tick, stereo view offset, viewport draw, slate draw, present and device reset, and
gives the stereo view offset *three* hooks because one call is where the whole conversion happens.
Expose whatever introspection stops extenders repeating your reverse engineering: UEVR hands plugins
Unreal's own reflection (`find_uobject`, `find_property`, `call_function`, the console manager).

**Proof:** a companion built against version N still loads on version N+1, or refuses cleanly.

**Related:** [META-006](#meta-006) is this pattern inverted - what to look for when you are the one
extending somebody else's engine rather than publishing a surface of your own.

**Trip hazard:** licence the header people must compile against as permissively as you can - UEVR's
`Plugin.hpp` carries its own MIT licence separate from the codebase, so plugin authors do not inherit
the framework's terms. An ecosystem you legally discourage is not an ecosystem.

## META-009 — Name the rival cause before reporting a measurement {#meta-009}

**Problem:** a measurement is correct and is attributed to the nearest plausible cause, producing a
confident and specific conclusion that is wrong.

**Use when:** any timing, count, rate or pass/fail you are about to state as a property of something -
especially one that confirms what you already suspected.

**Recipe:** before reporting, answer four questions. Does the instrument measure the property or a
**proxy** for it? Does absence of a signal mean absence of the thing, or absence of **measurement**? What
**else** was running - a timing under contention measures the contention. Is the **population** what you
assume, or does it include things you do not own? Where you cannot answer one, say so in the report
rather than rounding it off.

**Proof:** measure the same quantity a second way, or under a different load, and get the same answer.
One measurement is a number; two agreeing measurements are a property.

**Trip hazard:** this survives review, because reviewers check the number and the number is right. The
practical tell is that **the fix does not work** - a change that should have moved the measurement leaves
it unmoved. At that point suspect the attribution, not the fix. Four instances in one day in this fleet,
each individually rigorous.

## META-010 — Promote a claim, not a branch {#meta-010}

**Problem:** one successful experiment silently promotes every assumption, note and adjacent change on
its branch to "proven".

**Use when:** experiments are prepared on child branches, evidence arrives asynchronously, or several
projects share donor code and research notes.

**Recipe:** give the experiment a claim ID and keep **evidence class** separate from **promotion scope**.
Pin the baseline revision, the one intended intervention, required artifacts, decision rule and
invalidation condition before the run. Afterward, promote only the named claim supported by those
artifacts; leave adjacent candidates cold. Reopening a closed claim requires a written new premise or
new evidence, not a renamed experiment.

**Proof:** the promotion record names the exact baseline and artifacts, and a validator rejects an
unreviewed artifact or a promotion whose claim ID/scope does not match the experiment.

**Trip hazard:** merging a branch, building successfully, or receiving a green summary is not blanket
validation of everything that travelled with it.

**Three scars in this fleet, each a different way the scope crept:**

- **Swat4-VR withdrew three separate stereo measurements** (F-0014, F-0015, F-0020), **one of them with
  a passing control.** The runs happened; what was promoted was a conclusion the artifacts did not carry.
  *Pin the decision rule before the run, or a passing control becomes evidence for whatever you hoped.*
- **A shipped Dishonored VR mod's patch series contains `revert to proven M3.1`** after two successive
  refinements lost to the thing they replaced - and the last commit in its 52-patch series is **also** a
  revert. **Reverting to a named proven state is only possible if the proven state was named**; that
  project could roll back precisely because each candidate carried an identity.
- **DishonoredVR quoted a sibling by name as prior art and never opened its tree** - for five days,
  while writing an architecture argument from first principles that the sibling had already falsified by
  experiment. **A citation promoted to a finding is this pattern at the corpus level**
  ([FAIL-META-005](failure-atlas.md)), and *"a good citation feels like an answer, which
  is precisely why it stops the search."*

The common shape: **the unit that gets promoted is larger than the unit that was tested.** A branch, a
session, a build, a cited project - each carries adjacent material that inherits a verdict it never
earned.

## HOOK-001 — Resolve from a throwaway object, hook the real object {#hook-001}

**Problem:** hard-coded COM vtable addresses drift across OS/runtime versions.

**Use when:** D3D/DXGI device, context, swapchain or queue interception.

**Recipe:** create a disposable API object, read the interface slot address,
release it, then install the hook against the corresponding method on the
game-owned object.

**Proof:** log interface pointer, slot, resolved address and first real call.

**Trip hazard:** the throwaway object supplies code addresses, not the device or
context that OpenXR must bind. See [09](09-d3d11-openxr-injection.md).

## HOOK-002 — Fail-closed feature lane {#hook-002}

**Problem:** a stale signature or partial initialization corrupts the game.

**Use when:** every native hook or direct write.

**Recipe:** validate module/hash, signature, decoded target, object invariants
and downstream resources. Disable only the dependent feature lane on failure;
leave the original call untouched.

**Proof:** deliberately break each guard and confirm normal flat behavior.

**Trip hazard:** “best effort” writes turn compatibility failures into random
crashes. See [A4](a4-hook-safety.md).

## HOOK-003 — Defeat a devirtualised call before trusting a vtable hook {#hook-003}

**Problem:** a vtable hook is installed at the correct address and never executes, because the compiler
proved the object's type and inlined the virtual's body behind a vtable-pointer comparison.

**Use when:** a vtable hook is verifiably installed but its counter stays at zero, and the usual causes
(wrong object, wrong slot, thunk, `/OPT:ICF`) are excluded.

**Recipe:** look for comparisons against the class's vtable address near call sites of the virtual. The
shape is `if (obj->vtable == &Known::vtable) <inlined body> else call obj->vtable[n]`. Patch the
comparison so the indirect path is always taken. UEVR ships exactly this patch for Unreal's
`FFakeStereoRendering`.

**Proof:** the hook's entry counter moves from zero after patching, with no other change.

**Trip hazard:** everything about this failure looks healthy - correct address, successful install, an
honest "hook installed" log line - so it is only reachable by counting entries rather than installs.
UEVR's own note says they have seen it in one game; grade it INFERENCE until observed on yours.

## HOOK-004 — Detect a lost hook by its silence {#hook-004}

**Problem:** the object you hooked is recreated - device reset, resolution change, alt-tab, an overlay
injecting itself - and your hook simply stops being called. There is no error to catch.

**Use when:** any hook on a swapchain, device, context or other object with a lifetime you do not own.

**Recipe:** run two detectors. Compare the **identity** of the current object against the one you hooked,
and time the **silence** - if the callback has not fired for a wall-clock threshold (Crysis VR uses one
second) assume the hook is gone. On either signal, remove and reinstall every hook on that object, and
log that you did. Cache the new object.

**Proof:** force a device reset or a resolution change and confirm the mod recovers without a restart.

**Trip hazard:** silence is the *only* signal a dead hook gives you, so a mod without this detector
presents as "VR stopped working" with a clean log. Reinstall the whole set, not just the one you noticed
- they were installed against the same object.

## HOOK-005 — In a multi-title container, ownership is a fresh unique heartbeat {#hook-005}

**Problem:** the game is a launcher-container holding several titles, more than one game module is
resident at once, and "which title is running" cannot be answered from the loaded-module list.

**Use when:** any collection, remaster bundle or multi-game container - and any mod that must survive
the user switching titles without restarting the host.

**Recipe:** treat **module presence as availability only**. A title owns the runtime when its currently
installed, non-teardown generation publishes **the one unique fresh heartbeat**; zero or multiple
qualifying titles means **no owner and no capabilities**. Tag every publication with a *title
generation* (changes on load/unload/reload/rebase) **and** a *module-set epoch* (changes when any member
of the set changes), and reject a heartbeat that is not strictly newer than both. Give a departing title
a short teardown-only pending window that exposes nothing. Mask every capability that needs the armed
camera transaction until it is armed, keeping plain controller input and mode reporting separate so the
frontend still works when nobody owns anything.

**Proof:** one continuous session that enters each title, switches among them, and loads two consecutive
levels inside each - with each old core retiring and each new core re-earning its own gate. Enumerate
**all combinations** of active/installed/running in unit tests so one title cannot invert the rule for
the others.

**Trip hazard:** "no owner" is a **correct** answer that consumers must not over-read - a call site that
treats it as "suppress everything" breaks title-independent input in the frontend. And do not rearm a
gate on the same poll that samples it: a 50 ms worker erasing its own accumulated evidence means the
gate can never open.

## HOOK-006 — Hook the path that must run for a frame to exist {#hook-006}

**Problem:** the engine offers a sanctioned, well-named place to adjust the view - and it is gated by
game state, so it stops being dispatched during cutscenes, scripted sequences or menus. The mod then
works in gameplay and dies exactly where the player cannot act.

**Use when:** choosing between two hook sites, and whenever head-look "works except in cutscenes".

**Recipe:** prefer the **render** path over the script or tick path. *If a frame is drawn, the render
path ran.* A project that drove head-look through a script-level view hook shipped **"cutscene cameras
are fixed (no head-look)"** as an unfixable known issue and made its first mission unplayable; hooking
the render-side view builder instead gave head-look inside cutscenes.

**Proof:** a heartbeat counter on the candidate hook, sampled during a cutscene. Zero dispatches there
is the whole answer, and it costs one run. **Two mods on the same game settled this by comparison:** the
script-path mod shipped "cutscene cameras are fixed" and **cannot express roll at all**; the render-path
mod drove all six axes, held through cutscenes twice, and survived a checkpoint that re-created the
PlayerController ([the worked comparison](17-teardown-fc2vr-native-stereo.md#dishonored-hook-site-ab)).

**Trip hazard:** the render path usually has more consumers, so it needs
[return-address gating](#cam-014). That is a smaller problem than a hook that is never called. It also
has a **named cost**: with the view offset, the first-person mesh anchors to the *unmodified* view and
sits at the wrong angle, so budget for decoupling it per draw.

## STR-008 — Borrow the engine's own off switch for the second eye {#str-008}

**Problem:** a second world pass re-runs once-per-frame work - particles, simulation, temporal updates -
and hooking each subsystem to suppress it is a lot of surface for a small gain.

**Use when:** the engine exposes debug or console variables that disable a subsystem's update.

**Recipe:** before writing a hook, look for a variable the engine already honours. Crysis VR suppresses
particle updates on the second eye with the existing `e_particles_debug` cvar rather than touching the
particle system, clearing `VF_CHEAT` first so the value is settable. **Restore the original value after
the eye** - an asymmetric suppression leaves the subsystem off for the next frame's first eye.

**Proof:** the counter for that subsystem's per-frame work reads the same with stereo on as with it off.

**Trip hazard:** a debug variable may do more than its name suggests, so verify what it actually
suppressed rather than trusting the label; and clearing a cheat flag is a blunt instrument - do it for the
narrowest possible window.

## PERF-006 — Separate the compositor's floor from your own cost {#perf-006}

**Problem:** a per-span profile of the VR bridge is dominated by one enormous number, and it is the
runtime's blocking wait rather than anything you wrote - so the optimisation effort goes to the wrong
place, or to a cost that does not exist.

**Use when:** any framerate regression measured after adding a VR bridge.

**Recipe:** time every span with `QueryPerformanceCounter`, including the real `Present` call itself and
including a **bridge-off** configuration in the same build. Expect the runtime's frame wait
(`WaitGetPoses`, `xrWaitFrame`) to dominate: Psychonauts VR measured **25-27 ms** there against
**0.003-0.015 ms** for the `GetRenderTargetData` it had blamed for three sessions. Record the wait as a
floor, subtract it, and rank what is left.

**Proof:** an A/B that skips the wait. If framerate returns *and* submission starts failing - theirs
returned `VRCompositorError_DoNotHaveFocus` on every `Submit` - the wait is required and the number is
not a defect.

**Trip hazard:** a readback chain sounds expensive and usually is not; measure before designing around
it. And **run the bridge-off control through the identical test convention** - an off-screen window
triggers DWM occlusion throttling that caps `Present` at ~30 fps and silently invalidates every
comparison.

## PERF-007 — Tag each frame with the request it answers {#perf-007}

**Problem:** the game renders freely while the runtime asks for frames on its own cadence, so a
completed image can arrive **older than the request it is delivered against** - which reads as double
images or judder during fast motion, and defeats reprojection because the pose looks current.

**Use when:** any transport with a queue or a staging step between the game's render and the runtime's
submit - readback paths and cross-process bridges especially.

**Recipe:** record the runtime's **request ID** on each completed frame. Then: if the next render still
sees the same ID, wait a **bounded** interval for a newer one while servicing completed work; never
capture the same ID twice; and if the output slot is occupied, **discard the new image rather than
queue it** for stale delivery. Leave startup and menus free-running and switch pacing on at the first
real stereo pair.

**Proof:** a counter of discarded duplicates and of bounded waits, plus the absence of the double-image
symptom under deliberate fast head motion - the condition that exposes it.

**Trip hazard:** an unbounded wait turns a runtime that stops requesting into a hang, so cap it
(Condemned VR uses 20 ms). And pacing from process start rather than from the first stereo pair creates
bring-up stalls unrelated to the steady state.

## RE-001 — GPU value to owning CPU structure {#re-001}

**Problem:** the scene camera is hidden in an unknown binary.

**Use when:** a graphics capture exposes a projection/view candidate.

**Recipe:** identify exact matrix values in RenderDoc/apitrace, search them in
live memory, break/hook the writer, locate it in static analysis, reconstruct
the containing object and validate under controlled motion.

**Proof:** translation, rotation and FOV perturbations affect the expected scene
draw and preserve matrix invariants.

**Trip hazard:** per-frame change also describes bones, lights and shadows.
See [11](11-re-anchoring-and-discovery.md).

## RE-002 — Stable address ledger {#re-002}

**Problem:** a working offset cannot survive a restart, patch or handoff.

**Use when:** any binary-derived RVA, pointer chain, vtable slot or signature.

**Recipe:** record module, RVA, build hash, signature, surrounding instruction,
access path, evidence, consumers and invalidation rule in
`ADDRESS_REGISTRY.md`.

**Proof:** a fresh process resolves the same semantic object without a debugger.

**Trip hazard:** absolute virtual addresses are observations, not shipping
anchors.

## RE-003 — Camera consumer census {#re-003}

**Problem:** a correct per-eye camera write corrupts aim, culling, UI, audio or
another observer that reads the same shared camera.

**Use when:** the proposed camera seam mutates a global, singleton, player-owned
or otherwise shared object.

**Recipe:** enumerate readers during the mutation window; record phase,
persistence and allowed per-eye behavior; prefer a later copy-by-value render
seam when the shared-reader set cannot be bounded.

**Proof:** before/after assertions show persistent gameplay owners unchanged
while the intended render view changes.

**Trip hazard:** proving the setter is side-effect-free says nothing about who
reads the value before it is restored. See [RE-06](reverse-engineered-route.md#re-06).

## RE-004 — Writer census plus external-effect proof {#re-004}

**Problem:** a getter census exposes only a few tiny arrays, or thousands of
successful writes produce no visible result.

**Use when:** discovering mutable engine populations such as skeleton/bone,
particle, transform or light records in a closed binary.

**Recipe:** derive array layout from a consumer; hardware-watch one live record
to find its writer; briefly collect writer record addresses; group contiguous
runs by the proven stride; reacquire them in-process; apply one large reversible
poke to one candidate at a time.

**Proof:** an independent render/game effect moves—preferably pixels plus a
shadow—while the zero-delta and off controls do not. Sporadic one-frame motion
means the engine is overwriting a correct target; move to the last-writer seam.

**Trip hazard:** the writer can be a 100k-calls/s path. Keep the common path to
an armed read/return and the armed path bounded; do grouping and logging cold.
See [11](11-re-anchoring-and-discovery.md#writer-census).

## RE-005 — Chained one-shot hardware breakpoints {#re-005}

**Problem:** you need to observe several points in a startup sequence, and the CPU gives you four debug
registers that every other tool in the process is also entitled to use.

**Use when:** proving frame-boundary, device-creation or call-ownership facts early in a process, before
any permanent instrumentation exists.

**Recipe:** arm the sequence as **one-shot** breakpoints that disable themselves on first hit, freeing
their slot for the next stage; copy only entry values in the handler. When you run out of slots, reuse
freed ones and **report partial results** rather than presenting an incomplete census as complete. Before
arming on a thread you do not own, save its debug-register context and restore it afterwards, and **skip
any thread that already has one set**. On x86/x64 execution breakpoints, set `EFLAGS.RF` before
continuing from the trapped instruction; clearing `DR6` alone leaves the instruction eligible to trap
again. Bound the whole diagnostic in time.

**Proof:** the same run reports which targets were hit and which were never reached - the second list is
the point.

**Trip hazard:** silently clobbering another tool's breakpoints, resuming without `RF` into a
same-instruction retrigger loop, and probes on hot null-return paths - BFVR removed one such probe
permanently after it froze a map-load session, and documented the absence where the probe would have
been.

## RE-007 — Discriminate on a second physical quantity {#re-007}

**Problem:** a memory scan for a matrix, pose or projection returns many candidates, and tightening the
threshold on the single test you have removes real hits before it removes false ones.

**Use when:** any scan whose discriminator can be satisfied accidentally - and especially where the
probe point makes the test degenerate.

**Recipe:** add a test that keys on a **different** physical quantity. Singularity's `clip.w`
cancellation test went vacuous at the origin (`clip.w` collapses to `r[3].w` under both storage
conventions, admitting any matrix with a near-zero `w` constant, 18 candidates). Their second test used
the fact that the xyz of the `w` term **is the camera's forward axis**, checked against the rotator the
game already exposes: `dotFwd >= 0.99`. Prefer a second test that also **resolves an ambiguity** you
would otherwise have to settle separately - theirs settled ROW versus COL storage on identical bytes.

**Proof:** the same bytes score decisively under one convention and not the other
(`dotFwd=+1.0000` vs `+0.0023`), and the candidate count collapses to one.

**Trip hazard:** check whether your probe point makes the first test carry information at all - a
cancellation argument at the origin proves nothing. And if world-position probes find nothing, suspect
**translated-world space**: many engines pre-subtract the view origin on the CPU for float precision, so
the only probe that matches is `(0,0,0)`, which is precisely where the cancellation test degenerates.

## RE-008 — A version field that passes is not an ABI that matches {#re-008}

**Problem:** a module contract carries an explicit version number, the host checks it, the check
passes - and the struct behind it is not the one your headers describe.

**Use when:** proxying or re-implementing any module contract on a licensed or forked engine
(`GetRefAPI`, `GetGameAPI`, `CreateInterface`, any exported factory).

**Recipe:** treat the version field as a *name*, and measure the **size** separately. The `rep movsd`
counts at the call boundary give it to you directly: the count is the struct size in dwords. Compare
that against the reference header before trusting a single offset.

Soldier of Fortune, measured against id's Quake 2 `API_VERSION 3`:

| Struct | id Quake 2, API 3 | Raven SoF 1.07f | How measured |
|---|---|---|---|
| `refexport_t` | 22 dwords | **55 dwords** (220 B) | `mov ecx,0x37; rep movsd` into the hidden return pointer |
| `refimport_t` | 16 dwords | **27 dwords** (108 B) | `mov ecx,0x1b; rep movsd` from the by-value arg |
| `refdef_t` | 26 dwords (104 B) | **33 dwords** (132 B) | `mov ecx,0x21; rep movsd` from `fd` into `r_newrefdef` |

The host still runs `re.api_version != API_VERSION` and still passes. **The version gate is intact
and it is not a drift gate.**

**Recipe, part two:** forward what you have not identified. Treat both tables as opaque `uint32_t[]`,
copy the import table byte-for-byte, and replace only the export slots you have named with evidence.
An unidentified slot forwarded unchanged is free; an unidentified slot *assumed* is a crash.

**Proof:** the live export table reproduces the static prediction slot for slot, and a pure
passthrough build (zero slots wrapped) is visually and numerically identical to stock. Confirm a
struct layout by **residual against a known formula** rather than by eye - SoF's `refdef_t` was
settled by a `fov_y` residual of 0.0000 against `CalcFov`, with `fov_x` exactly the install's `fov`
cvar, which also fixed the prefix shift at +1. `[LIVE]` SoF-VR, `1973e88`.

## RE-009 — Data write watchpoints: name the producer, not the consumer {#re-009}

**Problem:** you need to know *what writes* an address. The address is computed at runtime, so a
static search does not converge, and the writer is not a function entry, so there is nothing to hook
in the ordinary way. [RE-005](#re-005) covers the *execution* side of the same hardware; this is the
data side, and its failure modes are different and quieter.

**Use when:** [chapter 11's writer census](11-re-anchoring-and-discovery.md#writer-census) step 2 -
"put a hardware write watchpoint on one known live record" - or any time a value you can read is
being recomputed underneath you and you need the code that owns it. Especially when the only site
you hold turns out to be **downstream of consumption**, where writes land and do nothing.

**Recipe:** four `SPEC` facts do most of the work, and three of them fail silently if you get them
wrong.

1. **`LEN` is not in numeric order.** `00` is one byte, `01` is two, **`11` is four and `10` is
   eight**. Transposing the last two watches the wrong width and reports confidently. (Intel SDM
   Vol. 3B, DR7 layout.) `[SPEC]`
2. **A data breakpoint must be aligned to its own length or it does not fire.** A 4-byte watch on an
   unaligned address is not an error anywhere - it simply never triggers, and the run reports "nothing
   writes this". Refuse an unaligned request rather than arming it. `[SPEC]`
3. **Inside a vectored/structured handler, your `DR6` and `DR7` edits are dropped unless the resumed
   context asks for debug registers.** `CONTEXT_DEBUG_REGISTERS` is not part of the context a handler
   is normally handed, and `ContextFlags` is what selects which parts are restored. This one is
   nastier than it looks: `EFLAGS.RF` **is** in the default context, so
   [FAIL-RE-022](failure-atlas.md)'s fix appears to work while the paired `DR6` clear
   silently does not - and `DR6` is sticky, so every later trap is attributed to a slot that did not
   fire. `[SPEC]` for the `ContextFlags` rule; `[INFERENCE]` for the consequence, which is reasoned
   from it rather than observed.
4. **A write breakpoint is a trap, not a fault.** It reports *after* the store retires, so the
   captured instruction pointer is the instruction **following** the writer. Publish which convention
   you are reporting, so the offset is not applied twice or not at all.

Then: bound the capture, and **account for thread coverage**. Debug registers are per-thread, so a
producer on a thread you never armed is invisible. Report armed and missed thread counts alongside the
result; without them an empty result cannot be read as evidence of absence. Re-arm after the target
spawns its workers.

**Proof:** distinct writer addresses, reduced to module-relative offsets and folded by frequency - one
writer means a producer, several usually means a shared helper, in which case the return addresses
name the real owner. The armed/missed thread counts and a foreign-trap counter travel with the result:
foreign traps mean something else owns the registers, which in practice means a debugger is attached
and the numbers are not yours.

**Trip hazard:** every silent failure above returns a plausible value instead of an error, which is
the [FAIL-RE-010](failure-atlas.md) family - a measurement that cannot show the thing it
claims to test. Extract the bit encoding somewhere it can be unit-tested; it is small, total, and has
no runtime dependency, so there is no reason for it to live only in code that has to be running to be
checked. Also inherit [RE-005](#re-005)'s etiquette in full - four slots, shared, saved and restored.

**Status:** the mechanics here are `SPEC`, and the technique has a `LIVE` precedent in Far Cry 2's
bone-writer census. The PreyVR instrument that prompted this entry (hunting the hand-IK producer) is
**built and unit-tested but has not yet been fired at a running target**, so nothing here is graded
`LIVE` on that project.


## SRC-001 — Prepared frame, per-view render {#src-001}

**Problem:** source-owned stereo calls a legacy frame function twice and
advances simulation, audio, particles, queries or temporal state twice.

**Use when:** the source tree exposes a scene/frame loop but does not already
separate simulation preparation from view rendering.

**Recipe:** prepare one immutable frame/pose packet, derive a prepared view for
each eye, and keep once-per-frame state outside the per-view render call; assert
the classification with a zero-delta repeat control.

**Proof:** two view outputs differ under a camera delta while simulation and
other once-per-frame generations remain unchanged.

**Trip hazard:** named source functions are not automatically scoped by
ownership. See [SRC-03](source-owned-route.md#src-03).

## SRC-002 — Upstream the VR-independent half {#src-002}

**Problem:** a source-owned VR fork diverges from upstream forever, and every rebase costs more than the
last.

**Use when:** any source port, engine fork or decompilation-derived VR conversion with a live upstream.

**Recipe:** for each change ask whether it is *VR*, or something the engine was missing that VR merely
revealed. Multiview, off-axis projection, frustum handling, a stereo manager, render-target abstraction
and pose types are usually the latter. Factor those as VR-independent engine concepts, land them
upstream, and let the VR layer *consume* them. OpenMW-VR upstreamed `components/stereo` while keeping
`components/vr` and `components/xr` on the fork, so the permanently-diverging surface is only what is
genuinely VR-specific.

**Proof:** the general layer builds and is useful with VR compiled out entirely.

**Trip hazard:** upstreaming requires the general layer to be genuinely general - a "stereo" component
that assumes an HMD, two eyes or a runtime is a VR component with a misleading name, and will be
rejected or will rot.

## CAM-001 — Split head pose from body yaw {#cam-001}

**Problem:** head turning also rotates locomotion/body, or yaw is applied twice.

**Use when:** the engine owns a player heading and VR adds an independent view.

**Recipe:** maintain explicit tracking, recenter, body and engine-camera
transforms; apply HMD yaw to render pose and controller locomotion to the chosen
body/head basis exactly once.

**Proof:** rotate head while stationary, then turn body while holding head
orientation; log each term in the chain.

**Trip hazard:** reading a post-HMD camera and applying HMD again. See
[01](01-camera-and-tracking.md) and [A1](a1-rotation-and-frames.md).

## CAM-002 — Separate render frustum from cull frustum {#cam-002}

**Problem:** head translation reveals holes or geometry pops at eye edges.

**Use when:** engine visibility was computed before the per-eye camera rewrite.

**Recipe:** preserve correct asymmetric eye projection for rendering while
driving the engine’s authoritative cull camera/FOV conservatively enough to
cover both eyes and roomscale motion.

**Proof:** peek around occluders and inspect missing geometry, not just clipping.

**Trip hazard:** widening the render projection cannot resurrect objects the
CPU never submitted.

## CAM-003 — One recenter event, all lanes {#cam-003}

**Problem:** world, hands, UI and interaction rays drift into different origins.

**Use when:** more than one subsystem consumes tracking space.

**Recipe:** publish one versioned recenter transform/event. Every pose lane
consumes the same version and invalidates its local calibration together.

**Proof:** recenter while a panel, weapon ray and world landmark are visible.

**Trip hazard:** each subsystem sampling its own “current HMD origin”.

## CAM-004 — The FOV law is per-title, including its formula {#cam-004}

**Problem:** two titles on the same engine express the same FOV setting under **opposite conventions**,
so a derivation carried across is silently wrong even though every symbol matches.

**Use when:** any multi-title adapter, engine family, or port that inherits a sibling's camera work.

**Recipe:** each title publishes its own FOV law; shared core code holds none. BioShock 1's option is a
true horizontal FOV, BioShock 2's is a 16:9-referenced horizontal
(`tanV = tan(opt/2)*9/16`, aspect-invariant, then `tanH = tanV * bbW/bbH`) - same engine tree, opposite
conventions. Write a lens match as a **live FOV-degrees equality derived from the option read this
frame**, never a cached value or a measured tangent: BioShock 2 animates its own FOV from 73 to 96
degrees during play, so anything cached is wrong there regardless. Infinite adds an ownership-boundary
trap: its rendered projection is vertical-referenced, but the live camera field is degrees-horizontal at
a fixed 16:9 anchor (`tanV = tan(deg/2)/(16/9)`). Record the field owner, formula and reference aspect
together; naming an FOV “horizontal” or “vertical” without that tuple is incomplete.

**Proof:** change the in-game FOV option and the aspect ratio independently and confirm the submitted
projection tracks both.

**Trip hazard:** this was that project's third never-copy instance after ini keys and a constant-buffer
offset - and the first where the copied thing would have been a **formula rather than a number**. A
derivation is target-specific evidence exactly like an address is.

## CAM-005 — Roomscale as a negotiation with game collision {#cam-005}

**Problem:** physical walking moves the headset, but moving the camera does not move the player's body -
so the player walks through walls, or the body teleports to catch up.

**Use when:** any port offering real 6DOF room movement rather than stick locomotion only.

**Recipe:** make it a three-step contract per frame rather than a camera translation. The VR layer
publishes the **desired** horizontal move; the game **collision-sweeps** it exactly as it would any other
motion; the game then reports the **achieved** displacement back, and the anchor becomes
`bodyHead - roomscaleOrigin`. Provide an explicit re-zero for recenter, scene change and enable. Bound
how far the camera may sit from the body horizontally, and spend that slack only on physical lean -
never on controller-driven camera motion, which must stay inside the body's collision.

**Proof:** walk physically into a wall and confirm the view stops with the body rather than passing
through it, and that releasing returns without a jump.

**Trip hazard:** letting desired displacement become achieved displacement without the sweep. The game
owns collision; the VR layer only ever proposes.

## CAM-007 — Delay synthetic motion, late-latch head motion {#cam-007}

**Problem:** one camera carries two kinds of movement with opposite latency requirements, and a single
correction applied to both makes one of them worse.

**Use when:** the engine attaches things to the camera (vehicles, ladders, mounts, scripted rigs) *and*
the head drives it.

**Recipe:** separate the two channels by clock. **Delay synthetic motion** by whatever latency the engine
takes to apply attached transforms - one project holds its camera a frame behind for exactly this reason.
**Late-latch head motion** as close to the display deadline as the renderer allows, regenerating
per-entity matrices in the backend if needed. Never apply either correction to the other channel.

**Proof:** attached-object separation is stable during vehicle or mount motion, and head-motion latency is
unchanged by that fix.

**Trip hazard:** delaying head motion adds latency to the one channel a human detects instantly;
late-latching synthetic motion separates the camera from whatever the engine attached to it by one frame
of its movement.

## STR-001 — Private per-eye targets {#str-001}

**Problem:** the game backbuffer cannot safely serve as both engine target and
OpenXR swapchain image.

**Use when:** injected native rendering.

**Recipe:** allocate private color/depth resources per eye, preserve engine
state, render/copy into the private lane, then copy/resolve to acquired OpenXR
images under explicit ownership.

**Proof:** known colors, dimensions, formats and eye labels arrive correctly.

**Trip hazard:** matching format/size does not prove two views share camera
provenance.

## STR-002 — Pair-latched publication {#str-002}

**Problem:** AFR or asynchronous eye production submits mismatched simulation
or pose samples.

**Use when:** eyes are not rendered sequentially in one engine frame.

**Recipe:** make pixels, optional depth, pair ID, simulation frame, per-eye render poses, rendered FOV,
display time, contract identity and source-resource generation one immutable publication unit. The
producer owns both eye resources while it copies both images and publishes the metadata/ticket, issues
the release barrier, then releases ownership; the consumer acquires both resources before reading the
ticket and metadata. A last-good fallback carries the metadata that rendered those pixels. Before the
first complete packet, return **WAIT / no submit**, not a permanent session fault.

**Proof:** delayed-publication fault injection cannot produce old pixels with new pose/FOV, one fresh eye
with one stale eye, or a mixed resource generation; logs show pair IDs never regress or mix contracts.
The check that catches the cached-pair form is **submitted per-eye display time equals the display time
that eye's pixels were rendered at** — which is only answerable if the producer kept it, which is the
same discipline this recipe already asks for.

**Trip hazard:** “latest left + latest right” is not a pair, and a fresh ticket does not make stale
pixels fresh. See
[09](09-d3d11-openxr-injection.md#the-unit-of-publication-is-the-pair-not-the-eye).

**Audit this at ring-construction time, not when you see shear.** If a mod reaches alternate-eye
*before* the view is head-driven, this defect is **latent and unfalsifiable by testing** — not by luck
of timing but structurally. A newer pose describes the same picture, so nothing shears, every check
passes, in headset too, and the fault activates later when an unrelated milestone lands. PreyVR was
carrying exactly this defect with 20/20 green: `Publish(int eye)` stored the eye and nothing else, and
submission labelled two images captured on *different frames* with one pose and one FOV read at
submission time. It was found by reading the ring, one milestone before head tracking would have made
it visible. Ask of any eye-identity ring: **does an entry carry the eye only, or the whole contract?**
Carrying eye identity is necessary and not sufficient. (`LIVE`, PreyVR `838cc1a`; the mechanism is
`AUTHOR`-grade from MonsterDeadWood C2VR and not independently replayed.)

## STR-003 — Projection companion bundle {#str-003}

**Problem:** geometry moves correctly but lighting, depth, fog or reconstruction
is wrong in one eye.

**Use when:** changing view/projection in deferred or post-processed renderers.

**Recipe:** treat projection, inverse projection, view-projection, eye position,
clip planes, depth scale and temporal history as one versioned per-eye bundle.

**Proof:** reconstruct a known point through every companion path and inspect
screen-space passes.

**Trip hazard:** patching only the visually obvious 4×4 matrix.

## STR-004 — Pass provenance guard {#str-004}

**Problem:** reflections, portals, probes or videos contaminate main-eye
resources.

**Use when:** a hook observes multiple camera/render-target owners.

**Recipe:** classify by render target, depth, camera/view identity, call ancestry, frame phase and a
semantic image/resource generation. Where one resource is reused serially for LEFT then RIGHT, pointer
identity is deliberately ignored. For replay correspondence, prefer draw ordinal plus
primitive/geometry/VS/PS signature over "last texture seen for this shader"; a shader may consume many
unrelated resources.

**Proof:** capture each special pass and confirm it retains its own targets; instrument a known
same-pointer/different-eye reuse and a known same-shader/different-texture case and confirm neither is
misclassified.

**Trip hazard:** resolution, format, COM pointer and shader ID are all weak identity signals unless tied
to a semantic epoch and pass role.

## STR-005 — Native scene re-entry before draw replay {#str-005}

**Problem:** per-draw duplication is fragile or semantically incomplete.

**Use when:** the engine already repeats world rendering for cubemaps, portals,
mirrors or prepared views.

**Recipe:** locate a side-effect-bounded scene invocation, prove it is naturally
re-entrant, enumerate saved/restored state, then drive it once per eye.

**Proof:** engine simulation advances once while world rendering advances twice.

**Trip hazard:** an existing repeat render may be a reduced pass set—proof of
re-entry, not necessarily the production vehicle.

## STR-006 — Stereo rungs as a runtime policy, not a one-time choice {#str-006}

**Problem:** the stereo architecture is picked once, early, on the least evidence you will ever have -
and if the chosen rung hits a wall there is nothing to ship.

**Use when:** starting any stereo implementation whose highest viable rung is not yet proven.

**Recipe:** put the rungs behind one interface and make **every rung shippable on its own**.
BioShock-Trilogy-VR runs five implementations of a single `IStereoPolicy`: mono-on-a-quad (validates all
OpenXR plumbing with zero engine knowledge), mono-tracked (validates camera math, world scale and
prediction timing), alternate-eye (judders, not shippable, but proves geometric stereo in about a day),
sequential re-entry (the primary bet), and depth-reprojection (the fallback if re-entry hits an
intractable wall). Each rung de-risks the next, and the fallback is selectable at runtime rather than
being a rewrite.

**Proof:** switch policies at runtime and confirm each still submits a valid frame.

**Trip hazard:** the ladder only pays if the lower rungs stay working - a rung that rots once the
primary lands is not a fallback, it is dead code that reads like an option.

**Corroboration:** MELE-VR ships the same shape to end users as a single config number -
`2=Stereo 1=AER 3=DIBR 0=Mono` - switchable from an in-game menu. Two independent projects arrived at a
runtime-selectable mode ladder that includes a **depth-reprojection fallback** at the bottom, which is
good evidence the ladder is the shipping shape and not just a development scaffold.

## STR-007 — Symmetric base projection plus per-eye centre terms {#str-007}

**Problem:** the runtime hands you an asymmetric per-eye frustum, and the engine has exactly one
projection with no way to express an off-axis one.

**Use when:** any engine whose projection is a single symmetric FOV/aspect pair - most older engines and
most console-derived renderers.

**Recipe:** convert all four `XrFovf` angles to tangent extents, average the half-width and half-height
across both eyes to get a symmetric base FOV and aspect the engine can hold, and keep the per-eye
**centre** terms separate, applying them downstream in the vertex shader against `w`. Take the centre
terms from the runtime's own projection matrices rather than deriving them. Hold nothing
headset-specific: FOV, lens centre, IPD and aspect all come from the runtime each session.

**Proof:** the same build should hold across standalone and several PCVR runtimes with no per-headset
constants; edge stretch during physical head rotation is the failure it removes.

**Trip hazard:** the vertical centre term must be applied to 3D world geometry only. Screen-space menus,
HUD, crosshairs and blur geometry are authored in clip space, so a global application slides the whole
interface - roughly 19 percent of clip space on a Quest 3, enough to clip panels off the top.

## XR-001 — Result-driven session transition {#xr-001}

**Problem:** local lifecycle state says “running” after `xrBeginSession`
failed.

**Use when:** every OpenXR host.

**Recipe:** state events request Begin/End; mutate `sessionRunning` only after
the corresponding API call succeeds. Guard one pending transition.

**Proof:** inject begin/end failures and repeated READY/STOPPING events.

**Trip hazard:** making the desired state true before the runtime accepts it.

## XR-002 — Focus-loss input neutralization {#xr-002}

**Problem:** the player keeps walking/firing while a system overlay owns input.

**Use when:** session is visible but not focused, pose invalid, host absent or
transport stale.

**Recipe:** publish a zeroed state plus releases, clear edge history, and require
a fresh post-focus press.

**Proof:** hold movement, lose focus, release physically, regain focus.

**Trip hazard:** freezing the last action state preserves the dangerous value.

## XR-003 — Keep-submitting fallback {#xr-003}

**Problem:** loading/pause stalls the render loop and destabilizes the
compositor or Android lifecycle.

**Use when:** engine rendering can disappear while the XR session remains live.

**Recipe:** keep the XR frame loop alive with last-safe content, a neutral quad
or empty legal submission; decouple simulation pause from frame submission.

**Proof:** long loading, pause and device-wake tests show continued frame IDs.

**Trip hazard:** “pause” implemented by stopping the render thread.

## XR-004 — Symmetric subsystem toggle {#xr-004}

**Problem:** a command or config key starts a subsystem but cannot stop it, so once an OpenXR session
exists nothing in the control surface can end it - and a non-`FOCUSED` session paces the game at the
runtime's not-visible cadence (roughly 10 Hz), which a user reads as a hang.

**Use when:** any runtime toggle that creates a session, thread, hook or swapchain.

**Recipe:** for every command that starts something, implement and test the stop that returns the
process to its pre-start state, and treat the pair as one feature. Audit existing toggles by asking what
each one actually tears down, not what its name implies.

**Proof:** start and stop the subsystem repeatedly and confirm frame cadence, thread count and resource
count all return to baseline.

**Trip hazard:** a stop that clears the *visible* effect (a camera mode) while leaving the *pacing*
owner (the session) alive looks like it worked.

## XR-005 — Wait once, cache, submit after every camera {#xr-005}

**Problem:** pose query, render and submit are spread across a frame in whatever order the engine's
callbacks happen to fire, producing mixed-age poses, a frame of latency, or a first-frame hang.

**Use when:** any host where more than one camera renders, or where submission is not obviously the last
thing in the frame.

**Recipe:** wait **once**, early; cache the poses; render every camera from that same cached pose; submit
from an end-of-frame hook after all cameras have rendered; hand off to the compositor last. Re-polling
inside the render backend at draw time is the one legitimate deviation - that is late-latching, and it
belongs to head motion only ([CAM-007](#cam-007)).

**Proof:** log the tracking sample id every camera actually rendered with; they must be identical within a
frame. Separately, confirm the pose you *submit* is the pose you *rendered from*.

**Trip hazard:** moving submit earlier because it measures faster drags the wait with it and buys a full
frame of latency that no profile will show you. In a survey of eleven mods, five had one of these
defects; the most common was rendering from a polled tracking pose while submitting a different render
pose - individually plausible numbers that only disagree when compared.

## XR-006 — Prove the graphics bridge with a non-invasive probe {#xr-006}

**Problem:** the game's graphics API has no XR binding, so a bridge to another API is mandatory - and
building it into the renderer before proving it works turns one unknown into an entangled several.

**Use when:** D3D9, D3D10, legacy OpenGL, or any target where the runtime demands a device you do not
have.

**Recipe:** write a one-time probe that creates a **temporary** device and never replaces the game's
renderer, then asserts, in order: the bridging API is available at all; an adapter **matches the
runtime-requested adapter LUID**; a resource created on one side can be opened and read on the other;
and the **game's own device is on that same adapter**. Record a negative control - the non-`Ex` D3D9
device refusing shared resources with `0x8876086C` is the canonical one. Only then wire it into the
renderer.

**Proof:** the probe passes with the game running and its renderer untouched. If it cannot pass
standalone, no amount of integration work will make it pass integrated.

**Trip hazard:** omitting the fourth assertion. A bridge that works in isolation says nothing about
whether the *game's* device is on the same GPU, and on switchable-graphics laptops it frequently is not.
Also note adapter LUIDs are **per-boot handles** - compare them within a session, never persist one.

## XR-007 — Record the submitted frame at the loader boundary {#xr-007}

**Problem:** the mod is the one part of the pipeline nobody can watch. A frame capture sees what the
game drew and a substitute runtime sees what the mod asked for, but what the mod *submitted* - the two
poses, the two projections, the layer set, the frame's identity - is visible only to a person in a
headset.

**Use when:** any OpenXR mod, at any tier. It needs no integration, so there is no point at which it is
too early.

**Recipe:** write an **OpenXR API layer** that forwards every call unchanged and records
`xrWaitFrame`, `xrBeginFrame`, `xrLocateViews` and `xrEndFrame` to a versioned, line-oriented trace.
Select it per process via `XR_API_LAYER_PATH` and `XR_ENABLE_API_LAYERS`, never the registry. Link no
graphics API - identify the binding by walking `xrCreateSession`'s `next` chain - so one binary covers
every renderer. Store FOV as **four independent angles** and floats at nine significant digits, or the
comparisons below become questions about your trace format.

**Proof:** the two checks that exist only here - submitted FOV against located FOV, and submitted pose
against located pose. Both compare what the runtime was told against what it said, from outside both.

**Trip hazard:** the layer sees only applications that go through the **Khronos loader**; a probe that
hand-loads a runtime DLL is permanently invisible to it. The loader silently skips a layer of the wrong
bitness or in an elevated process, so **require a new trace with a header record** before believing any
run - a run that recorded nothing looks exactly like a run that recorded everything. And OpenXR handles
are pointers on x64 and `uint64_t` on x86: bit-copy them, do not cast.

## XR-008 — Negotiate the OpenXR API version; never assert it {#xr-008}

**Problem:** `XR_CURRENT_API_VERSION` is whatever your SDK is. A runtime that implements an older
version refuses the instance outright, and the loader reports only that a chained call failed.

**Use when:** every OpenXR client, from the first probe onward. It costs nothing before you have a
headset and a session after you do.

**Recipe:** attempt **newest-first and fall back** on `XR_ERROR_API_VERSION_UNSUPPORTED`, logging each
attempt and its result. Do not hardcode `XR_API_VERSION_1_0` - that works on the runtime in front of you
and is wrong for the next one. Ship a **static table for the negative `XrResult` values**, because
`xrResultToString` needs a live instance and therefore cannot name an instance-creation failure.

**Proof:** the same unmodified binary creating an instance against two runtimes that disagree - one
accepting 1.1, one refusing it - with the attempt sequence in the log.

**Trip hazard:** a substitute runtime that accepts a version production refuses will pass this silently
for a whole session ([the permissive-substitute problem](09-d3d11-openxr-injection.md#permissive-substitute)).
Before blaming an implicit API layer, read `XR_LOADER_DEBUG=all`: **`Completed loader terminator` printed
before the failure means the runtime refused**, and the loader and layers are exonerated in one line.

## INPUT-001 — Physical transport, semantic mapping {#input-001}

**Problem:** controller profiles directly trigger game behavior and become
unsafe or game-specific.

**Use when:** OpenXR host and game hook/plugin are separate layers.

**Recipe:** transport physical axes/buttons/poses in a versioned neutral struct;
map them to semantic VR actions at the game boundary; then drive the engine’s
normal command/axis funnel.

**Proof:** an unexpected profile cannot generate motion without an explicit
mapping.

**Trip hazard:** semantic command IDs embedded in the runtime/profile layer.

## INPUT-002 — Press-owner release {#input-002}

**Problem:** a button remains latched when context changes mid-press.

**Use when:** menus, gameplay, weapons, hands or mods compete for an input.

**Recipe:** the lane that consumed the rising edge owns the release. On context
loss, synthesize release and clear ownership.

**Proof:** switch context while holding every modal/action button.

**Trip hazard:** routing release according to the *new* context.

## INPUT-003 — Mirror handedness once {#input-003}

**Problem:** per-feature left-handed branches drift and haptics reach the wrong
controller.

**Use when:** a complete physical input snapshot exists.

**Recipe:** swap hands once immediately after transport, keep downstream logical
weapon/support roles fixed, and mirror only physical-output masks on the return
path.

**Proof:** applying the mirror twice returns the identical state.

**Trip hazard:** independently swapping input, pose, model and haptic code.

## HUD-001 — One authoritative pointer {#hud-001}

**Problem:** beam/dot highlights one control while click activates another.

**Use when:** ray-driven VR panels or world UI.

**Recipe:** compute one pointer hit record; hover, highlight, beam, dot and click
all consume it.

**Proof:** a negative test presents two nearby targets and asserts one shared ID.

**Trip hazard:** recomputing a visual ray “for convenience”.

## HUD-002 — World-locked gravity-aligned system panel {#hud-002}

**Problem:** system UI rolls with the head, face-glues, or appears at world
origin after tracking loss.

**Use when:** menus, pause, game over and dialogs.

**Recipe:** on entry, validate pose, place from head position with yaw-only
basis, world-lock it, and lazily ease a recenter after sustained large
deviation.

**Proof:** enter while tilted, walk around it, lose/recover tracking.

**Trip hazard:** accepting a zero quaternion as a valid orientation.

## HUD-003 — Flat context as a panel over a frozen, tracked world {#hud-003}

**Problem:** file select, pause and other authored 2D screens have no world to render, but blanking the
world or stopping submission breaks tracking and comfort.

**Use when:** any game with full-screen 2D contexts that are not overlays on live gameplay.

**Recipe:** render the 2D frame onto a **world-locked panel** placed in front of the player, and keep the
**last world frame frozen but still head-tracked** behind it, so the player can look around a still scene
instead of sitting in a void. Have the game assert the flat-context flag **every frame**, so that a
publisher which stops falls back to the world rather than latching the panel on - the same discipline as
[META-005](#meta-005).

**Proof:** enter and leave the context while moving your head; tracking must never pause, and the panel
must not follow your gaze once placed.

**Trip hazard:** a head-locked panel instead of a world-locked one, which reintroduces the discomfort the
frozen-world trick exists to avoid.

## HUD-004 — Composite an existing 2D pass into a transparent layer {#hud-004}

**Problem:** an engine's 2D pass is written for an opaque backbuffer. Captured
into an RGBA layer image its alpha is coverage-times-coverage, so translucent UI
becomes too transparent and edges read as too bright.

**Use when:** routing an engine's own 2D/HUD pass into a quad or overlay layer
instead of rebuilding the UI in VR space.

**Recipe:** clear the layer image to fully transparent each frame; while it is
bound, blend with SEPARATE functions - colour keeps the engine's own factors,
alpha accumulates coverage (`ONE`, `ONE_MINUS_SRC_ALPHA`). Submit the layer
premultiplied and composite the desktop mirror the same way. Keep a kill switch
that sends 2D back to the window.

**Proof:** the alpha histogram of the layer image, not a screenshot: fully
transparent where nothing drew, saturated under opaque elements, a partial band
at edges and translucent panels. Squared alpha shows up as a missing saturated
population.

**Trip hazard:** one blend function for both channels squares the alpha of
translucent UI. It reads as "the HUD is too faint" and invites a brightness fix
that hides the real fault. See [04](04-ui-and-hud.md#hud-as-world-geometry).

## INPUT-004 — Invert the game's input conditioning instead of editing it {#input-004}

**Problem:** you synthesize a stick vector - to redirect walking, to snap-turn, to drive a scripted move -
and the game applies its own deadzone and curve on receipt, so what it acts on is not what you sent.

**Use when:** any mod that writes analog input rather than reading it.

**Recipe:** find the conditioning (usually a value in the game's own binding or profile file) and apply
its algebraic inverse on the way out. For a **per-axis (square) deadzone** `d`, a desired unit direction
`u` and magnitude `m`, send `sign(u_i) * (|u_i| * m * (1 - d) + d)` per axis; the game then recovers
`u_i * m` exactly. Correct **direction and magnitude separately** - usually only the direction is being
corrupted.

**Proof:** read back what the engine actually received - the axis fields it builds movement from - and
compare its angle against the angle you sent. Equality on both sides of the boundary, not plausibility on
yours.

**Trip hazard:** editing the config that sets the deadzone looks simpler and usually is not - binding
lines carry several bindings each, and a game that rewrites its config at exit will undo you
([CFG-003](#cfg-003)). And a **per-axis** deadzone corrupts direction while a **radial** one does not, so
establish which you are facing before deriving anything: the signature of a square one is saturation at
exactly +-90 degrees, error worst near 90, and a residual that inverts with direction.

## INPUT-005 — Remap around a response cliff rather than modelling it {#input-005}

**Problem:** a game action driven by an analog axis is wildly inconsistent at the top of the range,
because the engine's response curve is nearly vertical there.

**Use when:** any axis a tracked controller can push to full deflection - turning above all.

**Recipe:** measure the response at a few points near the top before assuming it is smooth. BioShock
Remastered's turn rate reads ~105 deg/s at 0.98, ~140 at 0.99 and ~200 at 1.00, so a 2% difference in push
doubled the speed. Remap your output into a range that **excludes** the cliff - cap the axis at ~0.95 -
and accept the lower ceiling in exchange for repeatability.

**Proof:** the same deliberate push produces the same result twice, measured, not judged.

**Trip hazard:** a curve that was fine on a gamepad is not automatically fine in VR, because a tracked
thumbstick hits the rail far more often and far less deliberately than a thumb does. And modelling the
cliff to preserve top speed reintroduces the sensitivity you were removing - staying off it is the fix.

## INPUT-006 — Pulse the input when rotation is coupled to locomotion {#input-006}

**Problem:** you drive the character's body facing to rotate the view past a free-look clamp, and the
engine only turns the character while it is *moving* - so the player is dragged across the level every
time they turn their head, and cannot turn in place at all.

**Use when:** any game where the actor turns to face its movement direction, which is most
third-person and follow-camera designs.

**Recipe:** send the input as **short pulses rather than a sustained hold**. Engines commonly apply
rotation before translation each tick, so a tap buys most of a step's turn for a fraction of its
distance. Psychonauts VR measured `8 x 90 ms` taps against one `720 ms` hold at equal total key-down
time: **60.2 vs 7.7 degrees of rotation per 100 units travelled, about 7.8x**. Tune the duty cycle
against measured degrees-per-unit, not by feel.

**Proof:** rotation and distance logged together, expressed as degrees per unit of travel - the ratio
is the number, not either figure alone.

**Trip hazard:** blocked movement means no rotation at all (theirs wedged on scenery and held
`yaw 168.0` across seven steps), so the lane needs a fallback when travel is zero. And check first
whether the axis is a **rate or an absolute clamped offset** - hold it at maximum and see whether the
value keeps moving; an offset saturates and over-driving it achieves nothing.

## INPUT-007 — Pick the input transport from the import table, then own the device state {#input-007}

**Problem:** synthetic input is chosen by what is easiest to write rather than by what the game reads,
and `SendInput` has three faults no care fixes: it needs the foreground window, pointer acceleration
distorts injected relative motion so counts-per-radian is not even constant, and a stray moment types
into whatever the player is actually doing.

**Use when:** before writing any input synthesis. The decision is static and costs minutes.

**Recipe:** read the game's imports, and weigh the **absences** as heavily as the presences:

| Import | Consequence |
|---|---|
| `DirectInput8Create` present | DirectInput is a path worth hooking |
| `GetRawInputData` / `RegisterRawInputDevices` **absent** | no raw input competing for the same events |
| `GetCursorPos` / `GetKeyboardState` / `GetAsyncKeyState` **absent** | the game does not poll the OS directly |

Then wrap the device rather than the OS queue: exact counts, no acceleration, and structurally incapable
of leaking keystrokes into another application. Two rules make whole bug classes impossible - **OR held
keys in, never write zero** (so a release cannot clobber a key the player is physically holding, and a
dead module leaves the keyboard untouched), and make mouse counts **additive and consumed exactly once**
(`fetch_add` on publish, `exchange(0)` on drain) so total injected equals total requested whatever the
two cadences are. Levels travel by seqlock and are idempotent; impulses are exactly-once.

**Proof:** poll counters per device class, and a physical effect - one injected key held for two seconds
moved the recovered camera 1.4 world units, with exactly two events emitted.

**Trip hazard:** **a `DirectInput8Create` import proves DirectInput is initialised, not that it feeds
gameplay** - some titles of that era create a keyboard device for text entry only. And
**focus-independence is a property of the cooperative level, not of the transport**: a game acquiring at
FOREGROUND (mouse `0x6` exclusive|foreground, keyboard `0x16`) stops reading input the moment it loses
focus, whatever you inject through. Close the side doors or the wrap is decorative -
`DllGetClassObject` reaches DirectInput through `CoCreateInstance` without `DirectInput8Create`, and
`QueryInterface` must never hand back the raw device. Load the real DLL from `GetSystemDirectoryA()`
and refuse any copy in the game folder, which would be yourself.

## INPUT-008 — Ship aim mode as a setting, with the axes split {#input-008}

**Problem:** which input owns yaw and which owns pitch is treated as one design decision, so the mod
hard-codes a single aim relationship - and makes a comfort call on the player's behalf that cannot be
predicted from first principles.

**Use when:** any target where the weapon is not motion-tracked, and any target that should support
seated, gamepad or accessibility play - which is most of them.

**Recipe:** expose aim mode as a **user setting**, and vary **yaw ownership and pitch ownership
independently** rather than offering one "decoupled" toggle. A shipped Quake 2 port offers nine,
including head-yaw with mouse-pitch, head-yaw-and-pitch, mouse-only, fully decoupled and disabled.
**Inherit a taxonomy that has already been tested at scale** where one exists - three of its modes are
named after another shipping VR title's scheme.

**Proof:** a wearer cycling the modes in the headset and choosing, rather than an argument about which
is correct. Ship HUD smoothing on the same principle.

**Trip hazard:** do not collapse the axes into one switch. Head-yaw-with-mouse-pitch is a distinct
experience from head-yaw-and-pitch, and a single "decoupled aim" boolean cannot express it. And a mode
list is not a substitute for a sane default - pick one, and let the setting exist for the players it does
not suit.

## INPUT-009 — Multiply a button with a stroke grammar instead of a menu {#input-009}

**Problem:** the mod needs more actions than the controller has buttons, and the alternatives are a
radial menu that interrupts play or a chord nobody remembers.

**Use when:** any VR mod that has run out of inputs - which is most of them by the second milestone.

**Recipe:** take **one** rebindable gesture button and read a **stroke** alongside it: the press
alone, six cardinal directions, and six out-and-return pairs gives thirteen actions per hand and
twenty-six across two, with no menu, no dwell and no visual. Cardinal strokes are learnable because
the hand already knows where the stick is.

Make the gesture button itself selectable from every plausible physical input, so the grammar
survives a controller missing any one of them.

**Proof:** a wearer performs each stroke without looking, and the game's own binding for that button
still works when no gesture matched.

**Trip hazard:** the gesture button usually means something to the game as well. **Suppress that
input while a gesture is in progress, and replay it if no gesture matched** - a press that silently
does nothing is the worst outcome of the three. Degrade by controller capability rather than
disabling: where capacitive touch is absent, synthesise the hand pose from a button and trigger
instead of dropping hand animation. `[SOURCE]` VRIK.

## INPUT-010 — Gate gestures on room-space motion, not world-space {#input-010}

**Problem:** a speed or displacement threshold reads the controller's world pose, so the player's own
locomotion satisfies it and gestures fire while walking.

**Use when:** any interaction gated on how fast or how far a hand moved - throw, swing, yank, shove,
loot-versus-grab, or a pull-and-slam reload.

**Recipe:** prefer, in this order:

1. **A difference between two points that both move with the player** - hand to hand, hand to HMD,
   hand to a body joint, hand to a point on a held weapon. Locomotion, turning and the play-space
   origin all cancel for free, and no correction code exists to get wrong.
2. **Room-space motion** - the hand relative to the play space, with stick movement, teleport,
   vehicle and animation-driven displacement removed. PLANCK names this axis in the setting itself,
   `yankRequiredHandSpeedRoomspace`.
3. **World-space motion**, only when the other end of the measurement genuinely is the world.

SS2VR's `manualReload` is the reference for (1): its whole gesture is `rightHand.z - leftHand.z` and
the horizontal distance between the two hands, so the player can walk, run and turn through the
entire gesture without touching it.

**Proof:** perform the gesture standing still and it fires; then walk while holding the hand still
relative to the body, and it must not.

**Trip hazard:** **displacement thresholds have the same exposure and hide it better** - a pull that
is unambiguous over 200 ms is meaningless over two seconds of walking downhill, so a world-space
displacement gesture needs either a bounded duration or one of the formulations above. `[SOURCE]`
PLANCK; SS2VR; the same axis underlies HIGGS's loot-versus-grab speed split.

## CFG-003 — Write the config before the process starts {#cfg-003}

**Problem:** a setting VR needs cannot be made to stick, because the game rewrites its config at exit with
whatever it actually ran at - so a wrong value can never correct itself from inside the game.

**Use when:** resolution, FOV, window mode, or any startup-read setting the game also writes back.

**Recipe:** set it from outside, before launch, using the same API the game uses to read it (for an INI,
the Windows profile functions rather than a rewrite of the file). Back the file up first and restore
automatically if the result fails a sanity check. Re-run whenever the mod's own copy of those values
changes.

**Proof:** launch, exit, and re-read the file - the value survives a full round trip including the game's
write-back.

**Trip hazard:** rewriting the whole file loses formatting, comments and any key you did not know about;
and if the mod and the game disagree about the value, the game's exit write wins, so the two have to be
kept in step deliberately.

## CAM-008 — Correct each draw around its own projection {#cam-008}

**Problem:** a camera correction applied in one projection's space is wrong for every draw that uses
a different projection, and the error grows with the near-plane ratio rather than staying small.

**Use when:** the frame contains more than one projection - depth slices, a separate viewmodel pass,
portals, mirrors, a UI camera - which is most engines newer than about 2005.

**Recipe:** recover each draw's own projection `P_d` and build the correction as
`P_d-1 . C_view . P_d`. Distinct projections are few (bfbc2-vr measured ~4 per frame against ~716
draws), so cache by `P_d` and the cost is negligible. Keep the global form as the fallback for writes
whose projection cannot be recovered, and snap the scale terms to the world's when they are within a
few percent so a non-rigid draw cannot leak into the field.

**Proof:** a unit test on the residue matrix, and in-headset a 10 cm lean that moves the far world
10 cm rather than metres.

**Trip hazard:** the residue `P'.P-1` passes **rotation** through untouched and multiplies
**translation** by `t'/t`. So the bug presents as "the world warps around me but I can still look
around", which reads like a tracking or IPD problem and is not one. Frostbite's slices measured 75x
and 213x.

## CAM-009 — Widen the engine's FOV, not your projection {#cam-009}

**Problem:** the headset's field is wider than the game's, and widening the projection matrix
produces void at the edges instead of more world.

**Use when:** any port whose target renders a narrower field than the headset - which is nearly all
of them.

**Recipe:** locate the value the **engine** uses for its own field and hold it at the headset's, so
the engine renders *and culls* wide. A projection-matrix widen asks for geometry that was never
submitted, because culling ran against the engine's own frustum. Keep the projection and the value
you report to the runtime in step, and remember the viewmodel usually has a second FOV of its own.

**Proof:** the extra cone contains world, not void, and objects at the edge do not pop in as you
turn.

**Trip hazard:** a config-file FOV key may do nothing - bfbc2-vr measured identical tangents at
`Fov=55` and `Fov=90`. Until the engine-level route works, **auto-widen off** and correct geometry in
a theater window beats a wide image with a hole in it.

## CAM-010 — Force the render frustum in the matrix; leave the engine's FOV for culling {#cam-010}

**Problem:** the engine accepts a wide FOV and will not hold it - its camera update interpolates back
toward the default between your writes - so the rendered field pulses and the submitted frustum
inherits every wobble.

**Use when:** the engine-level FOV route works but the value drifts, which is the usual outcome once
[CAM-009](#cam-009) succeeds.

**Recipe:** split the two jobs. **Render**: rescale the x and y columns of the world-to-clip matrix on
its way to the GPU, every upload - that is exactly a clip-space x/y scale, exactly an FOV change, and it
composes after the positional offset. **Cull**: keep writing the engine's own FOV, asking for ~15% more
than you render, so its drift stays harmless as long as it remains above what you draw. Submit the
**forced constant** to the runtime, never the observed value.

**Proof:** log the FOV recovered from the matrix over many frames and confirm it is flat where the
engine's own value is not. Recover it *from the matrix* - column lengths are the projection scales,
`tan(halfFov)` is the reciprocal - rather than reading the engine's field, which has a convention and an
interpolator between it and the pixels.

**Trip hazard:** write every copy the interpolator reads, or it drags the value back. Match the
headset's **vertical** FOV - a 16:9 game against a near-square per-eye view already has horizontal
surplus, and matching horizontally leaves top and bottom short. And a frustum submitted to the
compositor that *tracks* the engine will flicker; forced-and-submitted from one number agrees by
construction.

## CAM-011 — Hand roomscale to the game's own movement, and track what it accepted {#cam-011}

**Problem:** the camera follows physical movement but the player object does not, so collision,
triggers, scripts and the body model stay where they were - and naively feeding the same motion to both
applies it twice.

**Use when:** promoting camera-only lean into real roomscale on a game with no roomscale of its own.

**Recipe:** route physical translation and **horizontal yaw only** through the game's **own movement
commands** so its collision and scripts stay authoritative - never `SetObjectPos` or an equivalent
teleport. Keep four frames: tracking anchor, player anchor, **consumed** motion the game demonstrably
applied, and **residual** motion it has not. **Subtract consumed from every downstream pose** - eyes,
aim, controllers, weapon, IK, interaction. Publish one command snapshot per simulation frame, never
per eye. Keep pitch, roll and height as view-only.

**Proof:** requested versus accepted displacement logged separately, and a walk into a wall that
accumulates bounded residual without the body desynchronising from the head.

**Trip hazard:** native movement does **not** protect the head - constrain the residual head volume
separately, with hysteresis, and fade or vignette while the controller is stalled rather than pressing
the player into geometry. Integrating anywhere inside the per-eye loop doubles the motion. And a
collision helper verified for one callsite is not a general query API - it needs its own ABI and
call-safety proof before you reuse it.

## CAM-012 — Never decompose head orientation into scalars {#cam-012}

**Problem:** the horizon tilts. Three separate defects produce it, and they share one cause: a 3-DOF
orientation reduced to Euler scalars somewhere on the path from tracking to the eye matrix.

**Use when:** any mod composing a head pose with a body/game camera.

**Recipe:** carry the orientation as a **quaternion or a 3x3 basis end to end**, and strip roll only
where a consumer genuinely wants gravity alignment - a HUD panel anchor, a snap-turn accumulator that
reasons about a scalar heading. Store the recenter reference from **yaw alone**; keep the live pose
**full**. Ride the eye baseline on the *head's* right axis, not the body camera's, so a tilted head
tilts the stereo separation.

**Proof:** the symptom itself discriminates. **Tilt only when you tilt your head** is missing roll;
**tilt while merely turning and looking around** is a composition that injects roll; **a constant tilt
even looking straight ahead** is a reference that stored pitch and roll. Measure it: composing pitch
about the body camera's right and then yaw about world up put the camera's right axis **11 degrees off
horizontal** at yaw 0.6 rad / pitch -0.35 rad.

**Trip hazard:** **a forward vector cannot carry roll**, so any helper deriving yaw and pitch from the
head's forward direction discards it silently and no amount of downstream care recovers it. Positional
lean has the same failure: map the delta through the *reference's* frame, not the raw tracking axes,
or leaning sideways slides the player partly forwards at any heading but one.

## CAM-013 — Drop the pelvis, not the camera, when a pose lifts the body {#cam-013}

**Problem:** the player model floats off the ground in a crouched, braced or weapon-ready pose. It reads
as an animation defect and survives every animation-layer fix.

**Use when:** any mod that anchors the player body to the HMD - which is every 6DoF mod - on a game whose
animations move the head relative to the body.

**Recipe:** recognise the chain first. The body is pinned to the headset, the animation lowers the head
relative to the body, so the engine **raises the body** to keep the head at the headset and the feet
leave the floor. Then work with the engine: lower the **pelvis bone** by a fixed offset while the pose is
active, at a pre-late-update hook so it composes with the game's own leg IK, and let that IK plant the
feet and bend the knees.

**Proof:** physically lower the headset. If the feet come down and the knees bend, the float is a height
effect and not an animation problem - a one-move test that no desk instrument can run.

**Trip hazard:** move the **skeleton only**, and confirm what you did not move. Hands, weapon and arms
are controller-pinned, so a pelvis drop must leave the muzzle and the point of impact untouched - check
that shots still land where they did rather than assuming. And before reaching for the animation system
at all, note that poisoning or swapping banks can apply *correctly* and still fail, because the legs stay
bound to the weapon-hold bank whenever the weapon is up: that is the wrong layer, not the wrong value.

## CAM-014 — The render camera may be produced, not stored {#cam-014}

**Problem:** the view is fetched fresh each frame and its matrices built as locals, so **no field
anywhere steers the renderer**. Searching the camera object for one fails in the worst way - like a
wrong offset rather than a wrong premise - and can absorb a project's largest effort block.

**Use when:** any engine where writing the obvious camera fields "does nothing", and especially UE3.

**Recipe:** stop hunting for storage and **hook the producer**, rewriting its out-parameters. Then
**gate by return address**, because the producer typically serves many consumers per frame - audio
listener, AI, weapons - and only one is the render camera. Treat visible `Location`/`Rotation`/`FOV`
blocks as **caches**: per-frame outputs, not inputs.

**Proof:** count calls against presents. One target measured **6,516 view calls to 666 presents in
5 s**, with the gate applying 34,073 and rejecting 284,597.

**Trip hazard:** ungated, your offset moves the audio listener and the AI with the camera. Gating is
also a feature - every non-render consumer keeps the engine's own values, which **buys aim/view
decoupling for free**.

## CAM-015 — Proxy a published module contract instead of injecting {#cam-015}

**Problem:** the usual choices are a native injector into a closed binary, or forking a whole engine.
An engine that splits its renderer into a **separate DLL behind a documented C contract** offers a third
route that is cheaper and safer than either.

**Use when:** the target exports a single well-known entry point for a subsystem - `GetRefAPI`,
`GetGameAPI` and their relatives in the id Tech family - and a reference implementation of that contract
is available to read.

**Recipe:** rename the original module and ship a shim under its name that loads it, forwards the entry
point, and wraps **only** the one function you need. For stereo on a Quake 2 derivative that is
`RenderFrame`, called twice with two `refdef_t` values. **Check the contract's `API_VERSION` first** -
interface drift is the only real gate, and it is a static question.

**Proof:** dump the module's exports. A single symbol matching the published contract is the whole
finding: the licensee forked the engine and did not restructure it.

**Trip hazard:** not every game in a modular family ships the modules. Medal of Honor: Allied Assault is
id Tech 3 with the renderer **inside the executable** and only an allocator shim beside it, so there is
nothing to proxy and the route is a source port instead. The export table settles which case you are in
before any other work. And a shim is **reversible by renaming a file**, which is worth preserving - do
not let it grow into a fork by accident.

## CAM-016 — A cross product tells you both of its operands are directions {#cam-016}

**Problem:** a camera-block offset is labelled "position" from context or from a plausible-looking
triple of floats, and the stereo displacement is then applied to a direction vector - where a
following `normalize` quietly undoes most of it.

**Use when:** naming fields in a decompiled camera or view structure, before writing to any of them.

**Recipe:** read the arithmetic, not the layout. `normalize(cross(a, b))` proves **both `a` and `b`
are directions**, because a cross product of a point with anything is meaningless. A field that is
read on every path and never written is a *derived* basis vector, not the thing you steer. The
position is the field the basis block is *copied from*, and it is the one nothing else recomputes.

**Proof:** displace the candidate and sample the whole chain, each link separately - the write
landed, the rebuild consumed it, and it reached the block the GPU's view is built from. Three
nested claims, each falsifiable on its own; a zero-displacement control must move nothing.

**Trip hazard:** a wrong write here is nearly silent. FarCry2-VR displaced one component of a unit
forward vector for **1,264 runs**: a few thousandths of a radian, largely cancelled by the
`normalize` on the next line. The view never moved, and the missing-publish theory that followed was
**a second explanation stacked on a first fault that was never the cause**. When a fix does nothing,
re-derive the premise before you extend the model. `[LIVE]` FarCry2-VR, `d07fbac`/`5a981f9`.

## CAM-017 — Diagnose a frame mismatch by its signature before touching a sign {#cam-017}

**Problem:** a controller-driven rotation or placement is *almost* right, and the temptation is to flip
signs until the wearer's report matches - which fits the report and fails off-axis.

**Use when:** any transform composed from a tracked pose and applied to a bone, a weapon or a camera,
the moment a wearer says a component is inverted or something swings when they turn.

**Recipe:** read the signature first; each names a different missing conversion.

| Wearer reports | Signature of | Fix |
|---|---|---|
| yaw right, **pitch and roll inverted** | the rotation composed in world while the position was in the body basis | conjugate the rotation by the *same* body yaw the position lane uses |
| placement **swings to the other side when they turn around** | a fixed offset written into a world-oriented column | rotate the offset through the body basis, or use a world-space delta which needs none |
| a per-eye offset that **does not change with distance** | a per-eye camera reference leaking into a model-space transform | anchor the conversion at the origin ([FAIL-HAND-037](failure-atlas.md)) |
| an arm that **barely moves with the hand** | an unconjugated target, which reads as a distant one | print the shoulder-to-target distance; conjugate |

The first row's mechanism is the one to remember: conjugating a rotation by a yaw preserves its own Z
term and rotates the other two, so the missing conjugation shows as correct yaw with wrong pitch and
roll, and at 180 degrees both invert cleanly - which also looks like a handedness flip.

**Proof:** the confirming run must vary the body yaw *materially* - PreyVR's moved from 80 to 143
degrees and stayed correct - and the tests must assert the signature **and** that both lanes agree for
an arbitrary axis, which no pair of sign flips satisfies. Where two conjugations are candidates,
measure them head to head (MoH-VR: 71/133 degrees residual against 0).

**Trip hazard:** when a transform is *transported* rather than rebuilt, preserve what the engine was
carrying. FarCry2-VR rotates its camera's live basis vectors rather than constructing a fresh unit
basis, because nothing guarantees they are unit length and a rebuild would silently change a
magnitude - a second variable in a one-variable experiment. `[HEADSET]` PreyVR, MoH-VR; `[STATIC]`
FarCry2-VR.

## CAM-018 — Derive world scale from shipped content, not from a sibling {#cam-018}

**Problem:** world scale is taken from the engine's tooling, a sibling project on the same engine, or
a measurement made before the projection was verified — and every consumer of that constant inherits
the error.

**Use when:** before IPD, arm length, holster placement or locomotion speed is tuned against it.

**Recipe:** measure **authored content whose real dimensions are known** — a door, a corridor width,
a character's height — from the game's own files. Then check it in a headset against a real object.

Rank the evidence honestly:

| Source | Weight |
|---|---|
| shipped content with known real dimensions | **strongest** |
| a headset check on your own target | strong |
| a sibling project's headset-confirmed value on the same engine tree | **a prior, not a fact** |
| the engine's own editor/physics tooling | weak — often a default nobody set |
| anything measured before the projection was verified | **discard it** |

**Proof:** the derived value survives a headset check, and the numbers it disagrees with are recorded
with it rather than deleted — that record is what stops someone re-adopting the sibling's number.

**Trip hazard:** the fleet's measured spread on one engine tree is 50 / 65 / 78.74 units per metre —
tooling, sibling, derived — and the derived one won. **Content authors pick a unit convention per
title and the engine does not enforce one.** A frustum error also contaminates a scale reading
invisibly, so any value measured before the projection was proven has to go, however plausible.
`[HEADSET]` Swat4-VR, against BioshockVR on the same UE2.5 tree.

## STR-009 — Drive per-eye adaptive state from one shared value {#str-009}

**Problem:** an adaptive process runs independently per eye, so the two eyes disagree about the world
and the disagreement is not visible in any buffer comparison.

**Use when:** auto-exposure, eye adaptation, auto white balance, adaptive sharpening, any temporal
accumulation of a scalar, and any effect with feedback from the previous frame.

**Recipe:** compute the adapted value **once** - from one eye, or from a shared metering of the scene -
and apply it to both. Elite Dangerous meters brightness per eye and reads about **1.5 stops apart** near
a star; sharing the value brings it to **0.4**, and that residual is correct because it is the glow in
the eye that can actually see the star.

**Proof:** hold a view containing a bright source and measure the two eye images, in stops. Do not judge
it by eye - the visual system works hard to fuse exactly this.

**Trip hazard:** it is not a render-target bug, so it survives every check that inspects buffers,
formats or matrices. And **residual difference is not automatically wrong** - genuine per-eye occlusion
of a light source should differ. Decide what the correct residual is before treating any of it as error.

## STR-010 — Drop a bad frame instead of submitting it {#str-010}

**Problem:** one frame per event is rendered from the wrong viewpoint - a transition, a teleport, a
level load, a camera cut - and in a headset that reads as the world lurching.

**Use when:** you can detect the condition but cannot cheaply fix the frame.

**Recipe:** detect it and **do not submit**. The compositor holds the previous frame and reprojects it,
which costs one frame of staleness against a full viewpoint jump. EDVR does exactly this for Elite's
supercruise transitions.

**Proof:** the event is smooth in the headset, and a counter says how often you dropped - a suppression
that fires constantly is masking a different bug.

**Trip hazard:** on a monitor the bad frame is an unnoticeable blink, so this class of bug is invisible
in flat testing and unfixed in flat builds. And a drop must stay rare and bounded: never let the
detector run open-ended, or a mispredicted condition freezes the view.

## STR-011 — Declare the world camera's frustum, and only the world camera's {#str-011}

**Problem:** the frame contains more than one projection — the world, a near/viewmodel pass with its own
deliberately different field, sometimes a UI or scope camera — but OpenXR takes **one** `XrFovf` per eye.
Declare the wrong one, or a value blended from both, and the runtime reprojects the whole image against a
frustum that describes none of it.

**Use when:** any injected mod at the point of submission. This is the sibling of
[CAM-004](#cam-004), which is about reading a *title's own* FOV convention; this one is about what you
**declare to the runtime**, which is a different question with a different failure.

**Recipe:** enumerate every projection the frame builds before you declare anything. Declare the
**world** camera's frustum, expressed in tangent space rather than degrees. Leave the near pass alone —
its field is a deliberate art decision (BioShock renders its foreground at a fixed ~60° 4:3 *regardless*
of the world FOV; Far Cry 2 instead keeps them in step through `EFQ_DrawNearFov`), so it needs its own
handling rather than a shared number. See
[02 · the weapon's own FoV](02-viewmodels-and-hands.md),
[13 · BioShock's foreground projection](13-teardown-bioshock-vr.md) and
[17 · FC2VR's DrawNearFov](17-teardown-fc2vr-native-stereo.md).

**Confirmed on a third engine tree 2026-09-05.** Prey (CryEngine) shows the same split: with the world frustum correctly declared and stereo fusing, the weapon model still reads at a visibly different field. Three unrelated trees now - UE2.5 twice, Dunia, CryEngine - so treat the split as the default expectation rather than a per-engine quirk, and check it as soon as stereo fuses.

**Look for a cvar before you build a hook.** The split is usually described as something to
reverse-engineer, and on CryEngine it is simply exposed. Prey ships the whole near-render family as
console variables -- `r_DrawNearFoV` ("Sets the FoV for drawing of near objects"), `r_NoDrawNear`,
`r_DrawNearZRange` and `r_DrawNearFarPlane` -- so correcting the viewmodel projection costs one
command and no code. Found by string search in the shipped DLL with no game running, after a wearer
reported the weapon looking like it was rendered at a different field; setting it to the world's own
measured vertical FOV made the weapon and the world agree, with the world visibly unchanged. That
last part is the proof the cvar reaches the pass you think it does: **one pass changes and the other
does not.** `[HEADSET]` PreyVR 2026-09-05.

Two things travel with it. The near pass owns **everything drawn close** -- both arms and the body,
not just the weapon -- so its camera is the wrong lever for independent per-hand control, however
tempting it looks once you find it; that is a bone-level problem and moving the near camera produces
the whole-torso-swings-with-the-gun look. And the shipped value is tuned for a flat screen, so a VR
build should set this at startup rather than treat it as a debug toggle: the default is wrong for VR
by construction.

**Assert declared-against-rendered IN-PROCESS, because nothing outside can.** There are three
frustums in play and an OpenXR API layer can only see two of them - the one the runtime located and the
one you declared. The projection the engine actually rendered with never crosses the OpenXR boundary,
so `xr-tape`'s `submitted_fov_matches_located` cannot see it, and for an injector that check *failing*
is its correct state anyway. A mod that can rewrite the projection on any path therefore owes itself an
in-process comparison, in **tangent** space, made at the point the declaration is bound to the pixels it
describes. PreyVR shipped a synthetic 50 degree half-angle render under a 60 degree declaration with the
trace looking exactly as it should throughout; the assert is a few lines and would have caught it on the
first frame. `[LIVE]` PreyVR 2026-09-05, `FAIL-STR-048`.

**Proof:** two shots. Park the hand, change the world FOV, and see whether the viewmodel holds its size —
if it does, the near pass has its own projection and must not inherit your declaration. Then the depth
discriminator: a frustum mismatch offsets **every** object by the same angle regardless of depth, while
parallax scales with `1/distance` ([Question 1](09-d3d11-openxr-injection.md#q-distance)).

**Trip hazard:** the canonical OpenXR sample — including
[the one in chapter 09](09-d3d11-openxr-injection.md) — renders with the FOV the runtime handed back and
submits that same value. For an application that owns its renderer this is correct. For an injector whose
host engine builds its own projection it declares an image you did not render, and the result is
wall-eyed divergence that no amount of IPD tuning will fix.

## STR-012 — Carry the eye identity with the frame; never wait for it {#str-012}

**Problem:** under alternate-eye rendering, identifying which eye is on screen by setting a lock and
waiting N frames for the game thread's edit to reach the render thread makes a full cycle cost `2N`
frames. At N=4 and 90 fps each eye refreshes at about **11 Hz** - a slideshow.

**Use when:** any alternate-eye implementation, as the second thing you build after the
correct-but-slow version.

**Recipe:** a game/render thread split **delays work but does not reorder it** - the camera built for
frame N renders before the camera built for frame N+1. So push the eye you just built onto a small
lock-free ring on the game thread and pop one per finished frame on the render thread. Identity is
exact, every rendered frame updates an eye, and a pair completes every **2** frames. One project
measured **~11 Hz to ~45 Hz**.

**Proof:** pushes minus pops is the pipeline depth and must sit at a small constant - **drift means the
1:1 correspondence has broken and eye identity is no longer trustworthy**. Export lag plus starved and
dropped counts: **lag 0-1 across 30,833 frames, 0 dropped**.

**Trip hazard:** the failure mode is swapped eyes, which is miserable to diagnose in a headset.
**Verify off-headset first** - with nothing consuming the queue, lag equals the publish count, so
comparing lag growth against rendered-frame growth tests whether the camera hook fires more than once
per frame (**1.0019 publishes per rendered frame over 514 frames**).

## STR-013 — On a per-view culling engine, two-view outranks alternate-eye {#str-013}

**Problem:** the stereo rungs are ranked by implementation cost, so alternate-eye looks like the
cheap way to get a second eye and a same-frame two-view family looks like the tidy one.

**Use when:** the engine culls per view rather than once per frame - check before choosing a rung.

**Recipe:** read the visibility code first. UE3's `PerformViewFrustumCulling` walks the octree with a
**per-view bit**, tests each node against *that view's own* frustum, and culls a node away only when
it is outside **every** view; each view also gets its own `PrimitiveVisibilityMap`. A two-view family
therefore gets correct visibility for both eyes **for free**, and the union-frustum hazard does not
apply to it at all.

**Proof:** find the per-view bit and the "outside every view" condition in the culling walk; confirm
each view owns its own visibility map. A `MaxViews == 2` special case for a shipped stereo mode
(UE3 has one, `WITH_REALD`) is corroboration that the engine was built to do this.

**Trip hazard:** the hazard **inverts**. Alternate-eye culls from **one** eye per frame, so it is the
rung that inherits the union-frustum problem, not the one that avoids it. **Two-view is the safer
rung, not merely the tidier one** - which reverses the usual ranking, and is worth knowing before
building the cheaper thing twice. `[SOURCE]` DishonoredVR, `f4fb409`.

## TEST-005 — Keep a bit-exact reference build {#test-005}

**Problem:** a port shares code with an original target, and an accidental semantic change to that shared
code is caught only by whichever test somebody thought to write.

**Use when:** decompilation ports, source ports, any project with a build target whose output should be
byte-stable - and by extension any golden capture or reference dump.

**Recipe:** keep the original target buildable, guard every host-only change (`#ifndef TARGET_N64` in
GoldenEye Omniport), and assert the hash in CI. GoldenEye Omniport's N64 build still matches the retail
ROM (`sha1: abe01e4a...`) after every change to the port layer.

**Proof:** the hash. There is no judgement call and no test to have anticipated.

**Trip hazard:** it only covers what the reference target compiles, so host-only code needs its own
tests; and the moment the reference build is allowed to fail "temporarily" the oracle is gone, because
nobody can tell an intended difference from an accidental one afterwards.

## TEST-006 — Make the instrument fail on demand before trusting it {#test-006}

**Problem:** a checker reports clean, and a checker that has never seen the fault is indistinguishable
from a checker that is broken. Both print the same line.

**Use when:** any runtime guard, probe or census whose *negative* result you intend to act on.

**Recipe:** induce the fault in-process, confirm the instrument sees it, restore, and confirm the
restore. If any step fails, **fail loudly rather than reporting clean** - DishonoredVR's FPU probe sets
`_PC_24`, reads it back, restores and re-reads, and exits 1 if that round trip does not hold. On the test
side, assert that the *broken* case passes the weaker check as well as failing the stronger one, so the
suite records why the weaker check was insufficient.

**Proof:** the self-test fails when you deliberately break the detector, not only when you break the
subject.

**Trip hazard:** a check that detects the fault and proceeds anyway is a log line, not a guard - decide
the response before shipping the check. And an all-zero census is not a clean bill of health; it is an
untested one.

## TEST-007 — Assert the margin, not the verdict {#test-007}

**Problem:** a numeric gate passes, but nothing records how close it came, so the limit can be widened
later without any test noticing.

**Use when:** every residual, tolerance, threshold and timing budget.

**Recipe:** build a separation table - the correct case, the *tightest wrong case you can construct*,
and the rest - and assert the ratio between them. PreyVR's correct case scores `0.000000000`, its
tightest wrong case `0.004000008` at 40x the limit, everything else 600x-7500x above. Then a later
loosening breaks a test instead of passing review.

**Proof:** widen the limit deliberately and confirm the suite goes red.

**Trip hazard:** a test that recomputes the expected value with the same formula on the same inputs
reproduces to **exactly zero** and tells you nothing about the live path, where the engine does its own
float ops. Until that floor is measured, **log the residual as a number rather than a verdict**.

## HAND-007 — One optical axis while scoped {#hand-007}

**Problem:** the game magnifies the world while a reticle sits at zero disparity, so the two eyes are
asked to fuse a crosshair at optical infinity against a target at `D/M`. The reticle doubles, and the
player cannot tell where it is - which makes the shot unplaceable however accurate the ballistics are.

**Use when:** any weapon optic, binocular, spotting scope or magnified overlay in a mod.

**Recipe:** while the optic is up, **render both eyes from one camera** - the one the game fires from -
and leave the per-eye crop alone. Put it behind a default-off switch so the unscoped build is unchanged.
Do not render the scope to one eye and do not blank the other.

**Proof:** compute `M · IPD / D` across the ranges the game is actually played at and compare against
Panum's fusional limit, roughly **6-10 arcmin** for fine foveal detail. theHunter measured `M ≈ 2.75x`
and disparities of 30 / 12 / 6 / 4 arcmin at 20 / 50 / 100 / 150 m - unfusable at every one.

**Trip hazard:** a monocular disc inside a fused field is a **rivalry generator**, alternating at
0.5-2 Hz, not a substitute for a closed eye. Blanking the other eye costs binocular summation, lets the
covered eye drift to its phoria so the pair must re-fuse on every scope-down, and an LCD's black is grey
with mura. And note that a pure-translation eye offset puts the bullet a **fixed** lateral distance from
a one-eye-centred reticle at *every* range - so the error does not look like a scaling bug and will not
be found by testing at distance.

## HAND-008 — Dock the reload to the weapon, not to the hand {#hand-008}

**Problem:** the magazine's insertion path starts at the controller, so it cuts through the weapon
mesh whenever the hand is angled to the chamber, and drifts further wrong while the player walks.

**Use when:** building any hand-driven insert - magazine, shell, speedloader, battery, cartridge.

**Recipe:** define the dock as **a named joint on the weapon skeleton plus a local offset**, per
weapon, and start the insertion there. The hand's job is to *trigger* the insert and to be within a
distance threshold, not to supply the geometry. Where the weapon exposes two points on the axis you
need, derive the axis from those instead of reconstructing a bone's local frame: the hand's travel
projected onto that vector is the true along-axis distance, because rotation preserves length.

**Proof:** the insert looks identical standing still, walking, and with the hand deliberately
rotated. If it only looks right standing still, the path is still hand-derived somewhere.

**Trip hazard:** the threshold is not one global number. RE4VR keeps an insert distance **per weapon
category** with an optional **per-weapon override**, so tuning an SMG does not move every SMG.
Top-loading weapons take the magazine from above and their offsets are legitimately positive where
every other weapon's are negative - annotate that in the data, or someone will "fix" it.
`[SOURCE]` Talemann RE4VR 2.0; cyberpunk-vr-port.

## HAND-009 — A weapon taxonomy you did not predict, carried as data {#hand-009}

**Problem:** physical reload is written for "the pistol", then a break-action, a top-loader or a
rotary-cycle weapon arrives and the mechanism has nowhere to put the difference.

**Use when:** the second weapon is about to be added - not the tenth.

**Recipe:** one mechanism, one data file per weapon, and a **list of weapons that is itself data**.
Adding a weapon must never mean editing the reload module. Expect the table to need columns for at
least: whether the moving part slides, pivots or rotates; whether the weapon has a magazine, a
chamber or a cylinder; whether the engine closes the slide itself; whether a cycle is required after
a shot, and separately after a tactical insert; and how the carried round exists at all - a static
sub-mesh part, a spawned entity, or a mesh clone.

**Proof:** add a weapon with no change to the shared module, and confirm a weapon of a different
class still behaves.

**Trip hazard:** identify a rig by **more than its bone count**. Cyberpunk keyed rig signatures on
(rig, bone count) and a new pistol with eleven bones silently un-registered the four pistols that
shared that count - the signature now carries named bones at their indices. This is
[two-part signature](11-re-anchoring-and-discovery.md#two-part-signature) in a different domain.
And a genuinely different shape deserves its own file rather than another branch: their revolver was
lifted out of a 3,400-line module because "a revolver is not it".
`[SOURCE]` cyberpunk-vr-port; Talemann RE4VR 2.0.

## HAND-010 — Correct a spawned entity by its own last step, never by root velocity {#hand-010}

**Problem:** a held object that is a real world entity - a magazine, a grenade, a detached part -
lags the hand at walking speed and shakes against it on rough ground.

**Use when:** anything the mod places with a world transform has to appear held by a tracked hand.

**Recipe:** first, notice that **model-space work does not have this problem**: the base and every
slot come from the same game state in the same call, so the player's travel cancels. Only things
placed in world space against the game's transform, while the hand is drawn from the rendered
frame, are a frame behind. **A frame apart is speed.** Correct only those.

Lead the placement by **the last observed step of the point being placed**, lightly smoothed, and
predict the next step as that one. Take no `dt` - a step is already per-frame, so a long frame
carries itself. Reject an implausible step (a teleport, a fast travel, a re-grab) rather than
following it.

**Proof:** the object holds position against the hand standing still, at a run, and over steps and
kerbs. Rough ground is the test that matters; flat ground is where every wrong method also works.

**Trip hazard:** do **not** lead by the player root's velocity. The root is not the anchor - over a
step the controller lifts the capsule while the camera and skeleton ease after it, so hand and root
briefly travel in different directions - and a filter over it has its own lag, which is right only
while speed is steady. Do not take a second-order term either: it buys a little on a ramp and doubles
the noise, and that noise is exactly what reads as shaking. Measure your own staleness rather than
assuming it, by reading the same quantity at two points in the frame; and beware a transform whose
error cancels in a round trip - it will hand you that error as a constant if you use it one way.
`[SOURCE]` cyberpunk-vr-port.

## HAND-011 — Census the arsenal before building the reload {#hand-011}

**Problem:** a reload mechanism is designed against the weapon in hand, and the arsenal disagrees -
some weapons recharge, some have no reload verb, some feed from the top, some must be racked only
when empty, and one is a wrench.

**Use when:** before the first line of reload code, and before promising a treatment to anyone.

**Recipe:** write `docs/WEAPON_CENSUS.md` with a row for **every** weapon, in three tables that must
be filled in order - what the flat game does, then the reload topology, then the VR treatment. See
[the schema](02-viewmodels-and-hands.md#weapon-census). The load-bearing column is **implementation**:
whether the engine merely plays an animation and changes a number (`counter`), actually models
magazine state (`stateful`), regenerates the resource (`recharge`), draws each shot from inventory
(`consume`), or has no reload at all (`none`). Key every row on the **engine's own identifier**.

**Proof:** the count of censused weapons equals the count of weapons in the game, and the treatment
column contains no value that Table A does not support. A `full` treatment on a `counter` weapon is
a promise to invent state the engine does not have; say so in the row rather than discovering it in
a headset.

**Trip hazard:** a weapon that needs nothing still needs a row, or "no work required" and "nobody
looked" become the same blank. Record how the enumeration was obtained and what it may have missed -
a census with no stated lower bound reads as complete. And fill Table C last: a treatment chosen
before the topology is known is how a magazine animation gets built for a weapon with no magazine.
`[LIVE]` SS2VR's `manualReload` is the `gesture-native` tier working today, gated by a substring
model filter to a single weapon family - which is exactly what a census exists to widen.

## HAND-012 — Choose how an object is held before you tune how it feels {#hand-012}

**Problem:** an object in the player's hand jitters, lags, clips through geometry or refuses to
collide - and the tuning that would fix it depends on a choice nobody made explicitly.

**Use when:** anything is held: a magazine, a grenade, a torch, a detached part, a thrown item.

**Recipe:** pick one of three routes deliberately.

- **Kinematic, local** - animate the object's existing joint in its parent's frame. Perfectly stable,
  needs no correction, and **cannot collide with the world**. Right for a magazine sliding into a
  well.
- **Kinematic, world** - place a spawned entity by world transform each frame. Collides if you make
  it, and is **a frame behind the drawn hand**; correct it per [HAND-010](#hand-010).
- **Dynamic, motor-driven** - keep the body dynamic and drive it toward the hand with a 6-DOF spring.
  Collides naturally, and **does not care that its target is a frame old** because it is chasing
  rather than being placed.

**Proof:** hold the object still, walk, run, and push it into a wall. Each route fails a different
one of those, so the failure identifies the route rather than the tuning.

**Trip hazard:** the dynamic route needs two things that are easy to omit. **Ramp the grip**: tau
from ~0.1 at onset to ~0.65 steady over ~0.3 s, or the object snaps into the hand. **Clamp the
motor**: soft 6-DOF limits on stretch and twist, or a spring chasing a fast hand through geometry
finds a configuration it cannot leave. And never keyframe a body while its motor constraint is
active - pick one authority. `[SOURCE]` HIGGS / Heisenberg; contrast RE4VR and cyberpunk-vr-port.

## HAND-013 — A holster is a pose, a hand, and an accept-list {#hand-013}

**Problem:** holsters are added as body-relative offsets, and then every question after the first -
which hand reaches this one, what fits in it, how does the player find it - has nowhere to live.

**Use when:** putting anything on the player's body: weapons, magazines, tools, quick items.

**Recipe:** make each slot a data row with **a pose** (position and rotation), **a hand assignment**
(both / left only / right only) and **an accept-list** of item classes. VRIK's fourteen anatomical
slots - hips, thighs, calves, upper arms, forearms, shoulders, stomach, chest - are a good starting
enumeration, and its default hand assignment is **cross-body**: left hip is right-hand-only. Copy
that; a same-side default is wrong for the way people actually draw.

Give the zone a **discoverability channel and gate it by context**: a hover indicator shown while
weapons are sheathed and hidden in combat, and haptics on hover with an *only when empty* state, so
the feedback is about the affordance rather than the contents.

**Proof:** a wearer finds each slot without being told where it is, and the wrong hand cannot reach a
cross-body slot.

**Trip hazard:** **hysteresis is mandatory** - entry and exit distances must differ, and three mods
on three engines independently chose to separate them. **Calibrate the pose in the headset**, never
on a desk; both stacks ship an in-headset placement mode for exactly this, and the rotation ends up
stored as raw matrix floats precisely because no one hand-edits it. And **give back input you
intercepted but did not use**, or a grip that lands near a holster and activates nothing will simply
be eaten. `[SOURCE]` VRIK; Heisenberg; FRIK.

## HAND-014 — Give the hand a frame, and let speed and distance pick the interaction {#hand-014}

**Problem:** grab logic is written against the controller's position, so "is the palm facing it",
"is it in front of the hand" and "where does a held thing sit" have no defined answer, and every
interaction ends up sharing one distance threshold.

**Use when:** before the first grab, pull, press or holster check.

**Recipe:** define the hand's **frame** first - a palm vector, a pointing vector and a palm position
offset, per controller model. Then separate the interactions along the axes you now have:

- **distance**, in tiers: a near cast for a direct grab, a far cast for a pull, and a wider forgiving
  radius for the marginal case;
- **direction**, as a cone - a required half-angle or dot product, so an object behind the hand is
  never selected;
- **speed** - a quick swipe and a slow approach are different intents, and a leeway time covers the
  boundary between them.

**Proof:** each interaction can be triggered deliberately and none of them fires for the others.

**Trip hazard:** grabbing from clutter must **briefly damp and speed-clamp nearby dynamic bodies**, or
reaching into a pile launches the pile. And check the engine's physics stepping before promising any
of this - HIGGS ships fixes for Havok step count, minimum physics frame rate and simulation-island
size, which says a mature grab layer is downstream of a sane physics loop rather than independent of
it. `[SOURCE]` HIGGS; Heisenberg.

## HAND-015 — Blend into physics, clamp it, and decide what happens when it loses {#hand-015}

**Problem:** a body or object handed to physics pops on the transition, explodes when the solver
cannot converge, or vibrates in geometry forever.

**Use when:** anything driven by a physics constraint rather than by animation - a held object, a
ragdoll, a dragged actor, a detached part.

**Recipe:** three rules, in order.

- **Blend, never swap**, and find *all* the transitions: entering physics, leaving it, getting up,
  and recomputing the object's world-from-model transform each have their own blend time. Constraint
  parameters are **per phase** too - a driven body and a body standing up want different tau and
  force limits.
- **Clamp the solver's output** - maximum linear and angular velocity per bone or body, plus inertia
  bounds - so one bad frame cannot become a launch.
- **Decide in advance what to do when physics cannot win.** Two answers both worth having: **warp
  back** when a body drifts further than any recovery will close, disabling it briefly; and **phase
  through with an alpha fade** when two bodies intersect too deeply to resolve, with a larger
  threshold in combat than out of it.

**Proof:** force each failure - drive an object into a wall, into another body, and to the far side
of the level - and confirm each degrades the way you chose rather than the way the solver chooses.

**Trip hazard:** physics is a **distance-gated LOD**, so give the enable band hysteresis and spread
activation cost across frames. And every physical event needs a **cooldown**, because contact is
continuous: hits, shoves, bumps and their consequences all fire at frame rate otherwise, and a thing
you just released needs an ignore window so it cannot immediately hit you. `[SOURCE]` PLANCK; HIGGS.

## HAND-001 — Grip pose and aim pose are different contracts {#hand-001}

**Problem:** a visible controller/hand aligns, but weapon ray or muzzle does not.

**Use when:** OpenXR controllers drive weapons or tools.

**Recipe:** use grip pose for held-object attachment and aim pose for pointing;
compose one authored mount trim in a documented order.

**Proof:** compare physical controller, visible grip and projectile ray over
roll/pitch/yaw.

**Trip hazard:** mixing grip position with aim rotation.

## HAND-002 — Repoint the interaction-origin accessor {#hand-002}

**Problem:** hand-origin interaction looks like a rewrite of every grab, use, pick and ray in the game.

**Use when:** any target - managed or native - that has spectator, vehicle, cutscene or security-camera
views, because those features required the same indirection you now want.

**Recipe:** find the accessor the game already routes interaction through (RepoXR's was
`PlayerLocalCamera.GetOverrideTransform`) and repoint its call sites at a hand-derived transform. In
managed targets a Harmony transpiler does this without touching behaviour; in native ones it is usually a
single function hook. Apply the same treatment to the picker's ray check so grab rays leave the hand.

**Proof:** an interaction the mod never explicitly handled now originates from the hand.

**Trip hazard:** some call sites legitimately want the camera - UI pointers, screen-space effects,
authored cameras. Repoint by call site, not by blanket replacement, and keep the enumerated exceptions
visible.

## HAND-003 — Drive haptics from a channel the game already modulates {#hand-003}

**Problem:** haptics authored as a parallel state machine drift out of sync with the mechanic they are
meant to express, and need maintaining separately.

**Use when:** any continuous mechanic - grabbing, drilling, charging, engine load - that the game already
expresses continuously through some other channel.

**Recipe:** find the existing modulated signal and evaluate a curve over it. RepoXR keys grab haptics on
**the pitch of the game's own grab loop sound**, adds a second term from the beam overcharge value, and
suppresses output entirely while a scripted hold is forcing the grab. Audio is the usual candidate;
animation blend weights and material parameters also work.

**Proof:** the haptic follows the mechanic through states the mod never explicitly handled.

**Trip hazard:** suppress haptics for state the player did not cause - a forced or scripted interaction
should not buzz as though it were theirs.

## HAND-004 — Motion gesture as a testable decision core {#hand-004}

**Problem:** a physical motion must become a game input, and the detector ends up somewhere that cannot
be tested without a headset — so every threshold costs a headset session.

**Use when:** swing, shove, throw, reload flick, two-handed brace, or any other motion-driven action.

**Recipe:** sample poses through your own input funnel (not the runtime's velocity, which no replay tool
can drive) and smooth over a **window** — GTFO uses 50 ms — tracking **both positional and angular**
velocity, because a flick and a thrust differ in which one moves. Put threshold, hysteresis, cooldown and
pulse in the layer that runs **with and without a headset**; put "is this input legitimate right now" in
the game adapter, published per frame with a staleness budget that fails closed; emit the synthetic input
through the same merge as every other producer. Ship a `sim` command that drives the real decision core
**with a repetition count**, so cooldowns are exercisable flat.

**Proof:** every threshold, gate, latch and cooldown verified without a headset; only tuning constants
require one. Report one verdict per gesture, not per sample.

**Trip hazard:** hysteresis and cooldown are not redundant — without a re-arm latch one motion crosses
the threshold twice on the way up and down; the cooldown separately bounds a shake. And gate on the
equipped item's **identity**, never on "that motion looked like melee": a synthetic input means whatever
the game currently binds it to, so the wrong context turns a swing into a gunshot.

## HAND-005 — Substitute the pole, let the engine solve the arm {#hand-005}

**Problem:** VR arms need an elbow, and a hand-written two-bone solver has to fight the engine's own
skeleton, its bone lengths, its rest pose and its singularities.

**Use when:** the target has any authored two-bone IK - first-person body, weapon rig, look-at system.

**Recipe:** **enumerate the engine's own named IK facilities and cvars first** — a factory entry point,
a registered pose modifier, a limb definition or a console variable is an override the engine already
honours, and needs no hook at all. PreyVR found `CreateIKLimb` plus `IKLIMB_LEFTHAND`/`IKLIMB_RIGHTHAND`
in CryEngine 3 this way, their third independent instance of an engine-honoured override after a nullable
custom-view callback and `r_overrideDXGIAdapter`.

Only when no such facility exists, fall back to hooking: find the engine's two-bone solver and replace
**only its pole/hint argument**; let it keep writing the bone rotations. Compute elbow intent as a pure function of hand and shoulder in
the **stable shoulder/body frame**: a position-responsive anatomical bend for ordinary poses, blended
continuously toward a **fixed singularity-safe direction** as the hand approaches vertical or passes
behind the shoulder, then rate-limited by slerp (BFVR uses 12 degrees per XR sample). Return flags saying
which branch produced the answer, and return *nothing* on any non-finite or degenerate input so the
engine keeps its native pole.

**Proof:** sweep the hand through vertical and behind-shoulder poses; the elbow settles rather than
flipping, and the flags show the fallback engaging progressively rather than snapping on.

**Trip hazard:** branching at the singularity instead of blending into it - a hard threshold puts a
visible flip exactly where the maths was already weakest. And rate-limit on the sphere: per-component
clamping bends the direction as well as slowing it.

**Construction:** if you are computing the pole yourself rather than substituting one, build it with a
cross product - see [HAND-006](#hand-006), which removes a whole singularity that a projected fixed
direction cannot.

**Generation scope:** solver vocabulary does not survive engine generations even within one lineage. Far
Cry 1's `CCryModEffIKSolver` (with the `goal_normal` trap) is entirely absent from CryEngine 3, which
uses a serialised `CPoseModifierSetup` stack instead. Expect the names to fail and the structure to hold.

## HAND-006 — Build the pole by cross product, not by projecting a fixed direction {#hand-006}

**Problem:** an elbow pole built by projecting a chosen fixed direction onto the plane perpendicular to
the arm is degenerate in **two** places - along that direction and against it - so every choice of
direction buys one singularity and sells you another.

**Use when:** any two-bone limb whose bend plane you must choose (arms especially; the same holds for
knees and any hint-driven IK).

**Recipe:** construct the pole perpendicular by construction - `pole = cross(armAxis, sideAxis)` - rather
than projecting something into perpendicularity. There is no antipode and no residue to normalise. The
single remaining degeneracy sits where the arm points along the side axis (straight out sideways), which
you can place in a pose the game never holds. Keep a continuous blend for that one case; the cross
product subsumes the fade rather than removing it. Use the pole's own length as the proximity measure -
it *is* the sine of the angle between pole and arm axis, already computed.

**Proof:** sweep the hand through the rest pose and through the antipode of whatever fixed direction you
were previously using, and measure elbow displacement. FarCry2-VR measured rest-pose sweep 95 mm to
1.8 mm and the old antipode 236 mm to 1.1 mm on a 0.30/0.28 m arm.

**Trip hazard:** a magnitude threshold guarding the degenerate case marks where a bad region *ends*, not
where a good one starts - just above it you are normalising a near-zero vector and amplifying noise.
And do **not** sign-mirror the left arm here: at the singularity the arm lies along the side axis, so a
mirrored component lies along the arm and the perpendicular projection removes it exactly. That
parameter is inert, and a test asserting the two arms mirror will pass while certifying nothing.

## RE-006 — A write that survives and does nothing eliminates a field {#re-006}

**Problem:** you write to a candidate field, the value reads back intact at end of frame, and the picture
does not change - and you conclude the hook is not landing.

**Use when:** hunting the real camera, projection or view field in a struct that carries several
plausible matrices.

**Recipe:** treat it as a **positive** result. A write that survives the whole frame proves your hook
lands and proves that field is a **derived output nothing reads**. Cross it off and move on. Psychonauts
VR eliminated three matrices this way (`+0x20`, `+0x50`, `+0x90`) before finding the input at `+0x150`.

**Proof:** probe at several points in the frame (before each eye, after both) and confirm the value
survives. If it does, the field is not the source.

**Trip hazard:** the natural reading is "wrong timing", and chasing that costs sessions - it is **wrong
field, not wrong timing**. And make sure your dump samples on the correct side of your own write: a probe
that reads before the write shows the engine's value in every run and looks like a clean negative.

**The symptom has a second cause, and it points the opposite way.** If the engine caches a transform and
recomposes it only on invalidation, the field may be the genuine input while nothing marks the cache
dirty - Singularity VR wrote `SkeletalMeshComponent.Translation` +50 UU and measured `+0.0` movement,
because UE3 does not recompose `LocalToWorld` without a reattach. **Before crossing a field off, ask
whether the engine has a transform-caching concept for that object type**; if it does, hunt the dirty
flag rather than the field. See [11](11-re-anchoring-and-discovery.md#silent-write-two-causes).

## TEST-008 — Make the artifact a number before you argue about it {#test-008}

**Problem:** a visual defect is described in words, so it cannot be trended, compared across builds, or
settled - and the investigation runs on screenshots and opinion.

**Use when:** any "there is a black area / it looks warped / it feels wrong" bug older than two sessions.

**Recipe:** pick a scalar the defect moves - share of near-black pixels, mean inter-eye luminance
difference, count of pixels differing by more than N - and sweep it against the variable you suspect.
Psychonauts VR's void closed in one session once it became a yaw sweep of near-black percentage.

**Proof:** three properties together, not one - the trend is **monotone**, the effect is **reversible**
(back to the starting value), and the reading is **bit-stable** across repeats.

**Trip hazard:** explain outliers rather than dropping them (theirs was a chase-cam pointing into
terrain). And if the metric comes from a debug facility you did not write, get a **positive control**
first - four toggles showing no effect meant the display system was broken, not that four things were
absent.

## TEST-009 — Prove re-entrancy in a debugger before you build for it {#test-009}

**Problem:** native stereo depends on whether the per-frame entry you intend to drive can be called
twice, and finding out by building the hook costs weeks if the answer is no.

**Use when:** before committing to a second world pass on any target - and instead of auditing the
dispatcher's nested call tree by hand.

**Recipe:** break at the entry's prologue **before `push ebp`**, so `esp` still holds the return address
`ra` pushed by the real `call`. Snapshot every GPR and `EFLAGS` - for a function with no stack args that
set *is* the arguments. Run the real call to completion via a single-shot breakpoint at `ra`. Then push
`ra`, restore the snapshot, set `EIP` to the entry, and run the synthetic call the same way. Let the
game continue on the **second** call's state, which is what a dual-render hook produces.

**Proof:** both calls land at `ra` with `esp` balanced and matching return values, across a sustained
window - and per-frame cadence measured **before and after** the window is statistically
indistinguishable. Psychonauts VR: 15/15 on every check, `0.2029-0.2054 s` both baselines.

**Trip hazard:** an after-baseline is not optional - without it you cannot distinguish "safe" from
"broke something that has not surfaced yet". And expect the synthetic call to look slower than the real
one; in a debugger-driven test most of what you are timing is debugger IPC, so explain the anomaly
rather than reporting it as double work.

**This proves re-entrancy, not identity.** Psychonauts VR ran the test against a function it believed
was the outermost render dispatcher and reclassified it six sessions later, from a full decompile, as
**the camera's own update tick** - not a renderer at all. The safety result held; the label did not.
Confirm separately what the function *is* before building an architecture on what it does.

## TEST-010 — Answer many hypotheses per round trip {#test-010}

**Problem:** each attempt costs a launch, a load and often a headset, so a single-variable guess per
session burns days on a question a matrix would settle in one.

**Use when:** any failing API call with several plausible causes - device creation, swapchain setup,
session creation, format negotiation.

**Recipe:** build the sweep **inside the hook**. Create a private, hidden throwaway target (Manhunt VR
used an invisible window), try N candidate parameter sets against the real API directly, release each
immediately, and log every outcome - without touching the game's real object or the forwarded call.
**Vary several fields at once**: a matrix names the sufficient condition as well as the necessary one,
where a list only rejects candidates.

**Proof:** one run produces a table where a single field separates every success from every failure
regardless of the others - theirs: `INTERVAL_IMMEDIATE` failed under every combination,
`INTERVAL_DEFAULT` succeeded with nothing else changed.

**Trip hazard:** take the scaffolding out once it has answered - a sweep is an instrument, not a
feature. Keep fixes that turned out not to be the blocker if they were correct on their own terms. And
do not trust a validation helper to narrow the search: `CheckDeviceType` reported success on the exact
configuration `CreateDevice` rejected, because it never inspected the offending field.

## TEST-011 — Declare the exact set each falsification fault must flip {#test-011}

**Problem:** a falsification matrix that only asserts *"something failed"* passes while a check is
measuring the wrong quantity, because a fault that trips three checks looks the same as one that trips
the right one.

**Use when:** any suite of checks over a recorded artifact - a trace, a capture, a census.

**Recipe:** for each injected fault, declare the **exact set** of checks it must flip, and fail the
case on any difference in either direction. Where two families of check should be independent, inject
the fault in the form that isolates them - a rig defect applied to *both* the source data and the
derived data, rather than only to the derived data.

**Proof:** every fault flips its declared set and nothing else, and the suite **reports by name any
check no fault reaches**.

**Trip hazard:** the tempting fix when a fault flips something extra is to loosen the surprised check.
That is backwards - the extra flip usually means one of the two is measuring the wrong thing. It found
a head frame derived from one eye instead of both, which made a toe-in defect report itself as vertical
disparity.

## TEST-012 — Assert structural invariants against the source text {#test-012}

**Problem:** some rules are properties of the code's shape rather than of its output - "this value is
consumed in exactly these places", "these two fields are always assigned together", "this hot path
allocates nothing". A behavioural test cannot fail on any of them, because the violating program is still
a correct-looking program.

**Use when:** a decision was expensive to reach and is cheap to undo by accident - especially a coupling
between two assignments, or a single point of application for a setting.

**Recipe:** add a build-time script that reads the source file and asserts the structure: count the
occurrences of a symbol and require an exact number, split the file at a known hook and require the
distribution either side of it, and require the presence of the specific fragments that implement the
decision. Tag those fragments with a marker naming the fix, so a failure says which decision was undone.
Make every failure message state **why the rule exists**.

**Proof:** delete or duplicate the guarded line and watch the build fail with that message.

**Trip hazard:** these break on an innocent rename and see only what they were told to look for, so keep
them few and aimed. They are a complement to unit tests, never a replacement - and a structural assertion
that nobody can read is worse than none, because the next person deletes it.

## TEST-013 — Expose a live kill mask over your draw classes {#test-013}

**Problem:** a visual artefact is diagnosed by rebuilding with a hypothesis, launching, looking, and
repeating - so the observation and the change are separated by a compile, a launch and a memory of what
the last one looked like.

**Use when:** you already classify draws per frame. That makes this a rung-2 affordance and not before -
the classifier is the precondition.

**Recipe:** expose a **runtime-writable kill mask over the draw classes** you already distinguish -
world, UI, shadow, additive, user-pointer, quarter-res - plus a switch per feature. Diagnose an artefact
by switching classes off **while looking at it**. Pair it with an **on-demand per-draw verdict dump**:
the mask says which class, the dump says which draw and why it was classified that way. Make the mask
reachable from inside the headset, alongside separation and convergence.

**Proof:** one run in which an artefact is attributed to a class, and the same run confirming it returns
when the class is re-enabled.

**Trip hazard:** a mask that only *hides* draws answers "which class" and not "why that class", so ship
the verdict dump with it. And a class list that grows into a per-shader-id list is brittle across builds
- [recognise a family by its constants](17-teardown-fc2vr-native-stereo.md#dishonored-splice).

## TEST-014 — Make the substitute asymmetric wherever the headset is {#test-014}

**Problem:** a substitute runtime or synthetic fixture is given tidy, symmetric numbers, so a whole
class of pairing and sign defects is unfalsifiable in every test that does not involve a headset.

**Use when:** building any off-headset fixture that stands in for runtime geometry - a substitute
runtime, a synthetic trace, a projection unit test.

**Recipe:** copy the **real** runtime's asymmetry into the fixture. A Quest 3 through VDXR is
vertically asymmetric (up ~44 degrees, down ~-55) and horizontally asymmetric per eye. A fixture
using +/-55 up and down is not a weaker test, it is a **blind** one: with equal tangents, swapping
which tangent feeds which vertical clip plane changes nothing at all.

**Proof:** deliberately transpose a tangent pair in the fixture and require the test to fail. If it
passes, the fixture is symmetric somewhere it should not be.

**Trip hazard:** two independent instances in one week. MoH-VR's vertical cull planes were paired
with the opposite tangents; every desk test and the desktop mirror looked correct, and the headset
showed an 11-degree wedge of missing ground when looking up ([FAIL-CAM-025](failure-atlas.md)).
Separately, `xr-tape`'s own falsification matrix had a vertically symmetric nominal FOV - the
substitute's shape, not VDXR's - and was recalibrated to real geometry for exactly this reason.
**The fixture inherits the simplification of whatever it was modelled on**, and that simplification
is invisible until real optics arrive. `[HEADSET]` MoH-VR 2026-09-04; `[LIVE]` xr-tape.

## TEST-015 — Check the metric's premise before reporting its verdict {#test-015}

**Problem:** an instrument computes a real number from real data, and the number answers a question
the target does not pose - so it reports a confident **error** every run, and the error is believed.

**Use when:** any audit that separates one thing from another by a measured gap: world vs viewmodel,
foreground vs background, UI vs scene.

**Recipe:** state the metric's precondition as an assertion the instrument evaluates **first**, and
read the underlying comparison rather than a flag another stage set - so no report ordering can make
it lie. If the precondition fails, report *"premise not satisfied"*, never a verdict.

**Proof:** run the instrument against a target you know violates the premise and require it to
abstain rather than to disagree.

**Trip hazard:** SWAT 4's FOV audit split world from viewmodel **by geometry volume**, which needs
two projection lanes to exist. Two headless runs found later projections **bit-identical to the first
on 11,057 comparisons, different on zero** - one lane. The split was a lane against itself, 48/52
rather than the orders-of-magnitude gap the metric assumes, and it had been firing a false error
every run. **Keep the instrument, gate it** - it had caught a real bug once.

The companion failure is a metric that is simply the wrong question. The same session's viewmodel
probe asked which of two lanes is rigid on an engine that has one, and correctly refused to give a
verdict; the detach built on its premise **could not have worked**, and only the gate around it
turned that into a headless run instead of a headset trip and a wrong fix. **Build the gate rather
than trusting the premise.** `[LIVE]` Swat4-VR, `7505207`.

## TEST-016 — A self-test that only talks to itself proves only that it is consistent {#test-016}

**Problem:** every static check passes, and the two halves of the system have never exchanged a
byte - because each half inspected artifacts it created itself.

**Use when:** any two-process bridge - driver and injected DLL, launcher and mod, host and probe -
where both sides agree on a *convention* rather than on a *rendezvous*.

**Recipe:** make the test assert the **shared** object, from the side that did not write it. The
driver must read what the DLL wrote; the DLL must acknowledge what the driver sent. A check that
"the file exists and parses" is satisfied by a file the checker just created, in a directory the
other side has never heard of.

**Proof:** run one side with the other deliberately absent and require the check to fail.

**Trip hazard:** SS2VR's agent bridge had the driver and the DLL using **different agent
directories**, so no command could ever arrive - and every static check passed, because each side
inspected its own files. **A self-test that only talks to itself cannot detect a disagreement about
the address.**

The same bridge carried a second one worth naming: a **stale command file re-executed on every
launch**, because the sequence counter resets when the DLL loads and the file does not. The stale
command was `quit`, which is why the game "mysteriously exited under xr-sim" - a fault whose symptom
names the wrong subsystem entirely. Refuse any command older than the bridge's own start.
`[LIVE]` ss2vr-work, `04518f0`.

## TEST-017 — Give a harness a fault taxonomy, not a kill switch {#test-017}

**Problem:** a control plane, bridge or injected harness treats every fault the same way, so it
either retires itself on a condition that would have cleared, or retries one that never will.

**Use when:** any long-lived in-process harness - agent bridge, control plane, automation hook.

**Recipe:** classify first, then choose permanence.

- **transient** (a subsystem not initialised yet): retry, and **rate-limit it** - without a limit,
  "not ready" is a hot loop competing with the initialisation it waits on.
- **structural** (signature mismatch, executor fault, wrong build): **latch off for this process.**
  It will not become true later, and retrying hides it.
- **absent** (no packet yet): return WAIT and do nothing - neither retry nor latch
  ([FAIL-XR-023](failure-atlas.md)).

Then keep a **read-only subset alive during the unsafe window**. Answering status while refusing to
write is a better shape than being absent until ready, and it is what lets a caller tell "not yet"
apart from "gone".

**Proof:** force each class and confirm the response differs - a transient fault recovers on its own,
a structural one stays off and says why, and the read-only path answers throughout.

**Trip hazard:** **a caught exception is not a handled one.** SS2VR caught a null-pointer call from a
`set` issued before the engine's config table existed - and the catch disabled automation for the
entire session. The crash was prevented and the session was still lost. Ask what the recovery policy
*costs*, because a guard that quietly retires a subsystem is indistinguishable from that subsystem
never having worked. And do not let the control plane depend on a diagnostic being enabled: theirs
polled only while frametime logging and the flight recorder were on. `[AUTHOR]` SS2VR v3.71/v3.72.

**A second instance, one week later, from SOMAVR - and it is the *expected-transient* case.** A 125 ms
first-eye transition into a Read object correctly rejected the cached pair base, and continuous
same-frame stereo classified that expected abort as an eye-sequence fault and **disabled itself
permanently**. The replay owner now stays armed after `expected_pair_abort_retry_next_frame`; genuine
unexplained eye/pose mismatches still invalidate caches and fail closed. Same release: one transient
`thread_open` race while installing a single optics patch **rolled back the entire comfort bridge**,
restoring head bob, terminal takeover and depth-of-field blur at once. Fixed by giving each lane its
own failure domain - an optional optics failure can no longer remove an already-installed camera
suppression - and by reporting **requested versus installed** per lane at startup and in the
summary. *A failure domain the size of the whole feature turns one flaky call into a full regression.*
`[LIVE]` SOMAVR 0.95.6.

## TEST-018 — Symbolise the crash before the user has to {#test-018}

**Problem:** an injected mod faults inside the game's code, so every crash report is a column of
addresses, and the first hour of every investigation is spent turning them into names.

**Use when:** the mod is about to reach anyone who cannot attach a debugger - which is the first
external tester, not the first release.

**Recipe:** install a crash handler that resolves the stack **at fault time**. Where symbols for the
target exist, ship them and read them at runtime - Buffout 4 NG carries the game's own PDBs beside
`msdia140.dll`, Microsoft's Debug Interface Access library, for exactly this. Where they do not,
**symbolise your own module anyway**: the question is usually *"was it us"*, and a named frame in
your DLL answers it in seconds.

Add two things while you are there: a **symbol cache** directory so the work is not repeated, and a
**wait-for-debugger-on-crash** switch - not at startup, at the fault, which turns an unreproducible
field crash into a live session.

**Proof:** force a fault in your own code and confirm the report names the function; force one in
game code and confirm the report says so rather than blaming yours.

**Trip hazard:** a report that names only *your* frames will be read as *"the mod crashed"* even when
your frame is three levels below the real cause, so record the full stack and mark which frames are
yours rather than filtering to them. `[SOURCE]` Buffout 4 NG.

## TEST-019 — Give every instrument a NO case, and compare at the effect's own scale {#test-019}

**Problem:** an instrument reports a confident verdict from data that cannot support it - a
whole-frame statistic that cannot see a local change, a comparison that ignores one of its outcomes,
or a check whose expected value came from the code under test.

**Use when:** any pass/fail readout that a build decision or a headset trip will rest on.

**Recipe:** three questions, before trusting the number.

- **Can it say no?** Force the case the instrument exists to catch and require it to report it. A
  verdict with two buckets and a third it may ignore is where the wrong yes comes from; require the
  alternatives to *disagree with each other*, and require *neither* to lose before it speaks.
- **Does the expected value share a producer with the measured one?** If the check builds its own
  target from the same code, a wrong input scores a perfect solver. The witness must come from
  somewhere the code under test cannot reach - see [external witness](06-debugging-methodology.md#external-witness).
- **Is the metric at the scale of the effect?** A highlight moving one row is a few hundred pixels in a
  million; a whole-frame mean is identical to two decimal places. For small local effects compare the
  image, and against scene animation compare **connected clusters and judge the largest**, reporting
  the rest as animation. Luminance answers "is the screen black" and nothing finer.

**Proof:** the instrument has flipped to NO on a deliberately broken input at least once, on record.

**Trip hazard:** a low reading is not automatically noise. PreyVR read 186 applications per 4 s as
nothing happening when 511 was healthy - the number was the finding (the target was not drawn) and it
was reported as an absence. *When an instrument reports a number, ask what it is blind to before
asking what it says.* `[LIVE]` `[HEADSET]` PreyVR, Swat4-VR, MoH-VR, one week.

## TEST-020 — Arm and value are separate keys, and the report names what was patched {#test-020}

**Problem:** an experiment installs perfectly and measures nothing, and reads as a failed experiment
rather than as a wrong renderer, wrong build, wrong value or wrong path.

**Use when:** any hook, patch or override that can be armed.

**Recipe:**

- **Separate arming from value**, so the armed path can run at **zero delta**. The armed zero-delta run
  proves the plumbing is inert independently of the value; without it, anything measured in the
  treatment run is unattributable. Make zero an *explicit early-out*, not arithmetic - `0 * right` is
  only harmless while `right` is finite, and a NaN attitude would otherwise poison the origin.
- **Refuse to arm on the wrong precondition, by name.** FarCry2-VR's D3D9 lane refuses under D3D10.1,
  because the D3D9 world render is never called there and arming would install and measure nothing -
  a mistake that project had already published twice.
- **Print the address actually patched**, not a literal, so a wrong profile cannot read as the right
  one; and carry the profile name on the status line so `install=0` is never mistaken for a statement
  about the engine.
- **Assert the invariant the seam rests on.** SoF-VR's wrapper mutates a *copy* of the caller's
  struct; it asserts the caller's is byte-identical afterwards and logs an alarm if not, rather than
  assuming the premise its whole route depends on.
- **Report what the target wrote back.** The same wrapper records which dwords the renderer writes
  into the struct it was handed - free evidence for the next milestone, because a private per-eye
  copy changes where those writes land.

**Proof:** an armed zero-delta run is bit-identical to unarmed; a wrong-renderer or wrong-build launch
is refused with the reason; the log names the address, the profile and the delta on every arm.

**Trip hazard:** a *silently successful* command is the same failure one layer up. MoH-VR's
`cheats 1` looked correct on the command line and did nothing in the headset: every `EV_CHEAT`
command checks `thereisnomonkey` first and, when it is 0, resets `cheats` and refuses. And a numeric
reader that parses base 10 rejects `0x40` as trailing garbage - correct for a pixel count, fatal for
an offset, because the override silently falls back to the table while the user believes it took.
Base 0 is not the fix: it reads a leading-zero literal as octal and returns a *different, plausible*
address. Require the `0x` prefix and refuse everything else. `[LIVE]` FarCry2-VR; `[STATIC]` SoF-VR M3;
`[HEADSET]` MoH-VR.

## TEST-021 — Pre-register the owner for every outcome, then run once {#test-021}

**Problem:** a live run returns a result and the argument about what it means starts *afterwards* -
which is when the interpretation is chosen to fit, and when a run that could have been decisive comes
back ambiguous.

**Use when:** a defect admits more than one owner and a headset session is the only way to
distinguish them.

**Recipe:** before the run, write the **table**: every outcome the witness can produce, and for each
one the owner it implicates and the next action. The run is then decisive by construction, because no
result is unassigned. SOMAVR's arm witness is the reference shape. The left-eye arm lags the right eye
under locomotion, and endpoint IK tuning cannot say why, so the witness snapshots the shared arm root
and both clavicle-to-wrist chains before and after each viewport render, plus the final deform
palette, and the table reads:

| Witness says | Owner | Next |
|---|---|---|
| coherent node inputs, **different** final palettes | HPL's render-time bone update | that function |
| coherent palettes, eye disagreement still visible | sub-mesh CPU skinning or VBO consumption | one rung later |
| **different** node inputs between passes | CPU animation / bridge last-writer | existing diagnosis |
| eye/pose mismatch | an AFR transaction fault, not the arm solver | pair policy |
| palettes unavailable | retained mesh identity incomplete at that boundary | identity/lifetime work, not IK |

**Proof:** every row of the table names a different next action, and the witness is bounded and
read-only - theirs samples the first eight eligible pairs and every thirtieth after, and never writes
a matrix.

**Trip hazard:** a table with two rows that lead to the same action is one row, and a witness whose
outcomes overlap needs a better boundary, not a longer run. This is
[observation boundary](06-debugging-methodology.md#observation-boundary) taken to its conclusion, and
it was built explicitly on the FarCry2-VR lesson that
[correct endpoints do not prove correct deformation](12-torso-calculations-and-ergonomics.md#endpoint-is-not-the-mesh).
`[STATIC]` SOMAVR 0.95.8 - built and desk-verified, not yet run.

## TEST-022 — Pin the instrument's identity as hard as the target's {#test-022}

**Problem:** a result is attributed to the mod when the variable was the tool — a substitute runtime,
a checker, a harness — and nothing in the record says which build of it ran.

**Use when:** any result that a substitute runtime, simulator or external checker produced.

**Recipe:** record the **commit or version of every instrument** beside the build identity of the
thing under test, in the result itself. SOMAVR's entry names `xr-sim 9155410` and `xr-tape 52d3fac`
next to its own version, which is what turned *"the menu edge does not fire"* into *"the shared
runtime regressed and our vendored copy did not."*

Then treat the substitute's verdicts as bounded in **both** directions:

- it can be **more permissive** than production — accepting an API version the real runtime refuses;
- it can be **broken where production is fine** — reporting `changedSinceLastSync` as always false so
  no edge ever fires.

**Proof:** a green run names the instrument versions that produced it. When two builds of one
instrument disagree on the same client, that disagreement is the finding.

**Trip hazard:** *"substitute green is not a pass."* A substitute exists to make a class of question
cheap, not to be the gate — anything it certifies still needs one real-runtime confirmation before it
is called done. And when you vendor a shared tool, the fork is now a second instrument: SOMAVR's
vendored xr-sim passing while the shared one failed was only legible because both were named.
`[LIVE]` SOMAVR; `[SOURCE]` SoF-VR.

## PERF-001 — Frame budget ledger {#perf-001}

**Problem:** average FPS looks correct while the compositor reuses stale frames.

**Use when:** every desktop and mobile VR performance claim.

**Recipe:** record refresh budget, minimum FPS, stale/torn/reprojected frames,
update, scene, each eye, synchronization, submission, compositor and memory
under matched conditions.

**Proof:** the measured workload is preserved in a device/capture image.

**Trip hazard:** presentation rate is not fresh application-frame rate.

## PERF-002 — Optimize from bottleneck evidence {#perf-002}

**Problem:** FFR, multiview or resolution changes are chosen by intuition.

**Use when:** performance misses budget or needs headroom.

**Recipe:** classify CPU update, submission, vertex, fragment, texture,
bandwidth and synchronization cost; run one matched A/B tied to the dominant
metric.

**Proof:** metric moves as preregistered without invalidating visual workload.

**Trip hazard:** desktop timing cannot prove mobile GPU behavior.

## PERF-003 — Wait-ahead frame-loop ordering {#perf-003}

**Problem:** the app runs at exactly half the panel rate, and the delay appears inside `xrBeginFrame`
rather than in `xrWaitFrame` or the render window.

**Use when:** any OpenXR host whose `xrWaitFrame` runs on a dedicated worker, especially when the game's
own render thread must own `xrBeginFrame`.

**Recipe:** one worker is the sole `xrWaitFrame` caller and publishes an immutable `Wait(N)` packet; the
render thread validates it (session epoch, no other Wait in flight), **releases the N permit immediately
before `Begin(N)`**, and the worker's next instruction is `xrWaitFrame(N+1)`. Throttling then lands in
Wait, where the spec permits it.

**Proof:** log per-call durations for Wait, Begin and End separately across a cadence transition; Begin
stays flat while Wait absorbs the change.

**Trip hazard:** releasing the worker *after* `xrBeginFrame` — the intuitive order — leaves no Wait
pending while the runtime enters Begin.

## PERF-004 — Negotiated optional-extension lever {#perf-004}

**Problem:** a performance lever (perf level, thread hints, refresh rate, foveation) is an optional or
vendor extension, and calling it unconditionally fails on runtimes that do not implement it.

**Use when:** any standalone/Android target, and any desktop runtime feature outside core OpenXR.

**Recipe:** keep one boolean per optional extension set only when the runtime advertises it; resolve the
function pointer with `xrGetInstanceProcAddr` and require both success **and** a non-null pointer; check
every call result. Add a vendor term to the guard where one runtime is known to misbehave. Log the
`PERF_SETTINGS` event stream with timestamps so thermal transitions have a direction.

**Proof:** run on a runtime lacking the extension and confirm the lane disables rather than errors.

**Trip hazard:** treating "advertised" as "works"; foveation in particular is per-vendor.

## PERF-005 — Presentation scale changes FOV, not resolution {#perf-005}

**Problem:** presenting a finished eye image "smaller" is implemented as a swapchain resize, resizing a
surface an upscaler owns or discarding its output.

**Use when:** any route where an upscaler (TAAU/DLSS/FSR) produces a completed per-eye source before
submission.

**Recipe:** hold the swapchain fixed and narrow the per-eye FOV used at submission, so the same pixels
cover less angular area. Gate the fixed-resolution route on an explicit predicate naming the modes that
own their source.

**Proof:** confirm swapchain dimensions are unchanged across the full scale range, and that image
sharpness rises as scale falls.

**Trip hazard:** a mode that falls through to a legacy crop path at exactly scale 1.

## TEST-001 — Substitute runtime as a test instrument {#test-001}

**Problem:** the work cannot be checked without a headset, or no real runtime fits the target at all -
32-bit games in particular, where almost nothing ships a 32-bit OpenXR runtime.

**Use when:** the headset round-trip dominates iteration cost, or an agent must verify VR work it cannot
physically observe.

**Recipe:** count your actual OpenXR surface first - a mod typically uses a small closed subset (39 entry
points, one extension and one interaction profile in BioShock-Trilogy-VR's case), which is what makes
writing one tractable. Select it per process with `XR_RUNTIME_JSON`, which the loader checks before the
registry, so the machine default is untouched and the mod binaries stay byte-identical. Make it
**composite**, not merely accept frames: resampling each eye through the tagged pose/FOV difference turns
a claimed-FOV mismatch into a visible magnification and a single measured ratio. Give every wait a finite
timeout, and keep compositing off except on capture frames.

**Proof:** assert the runtime's *name* out of the application's own log; an API layer cannot substitute
here, because with no headset the real runtime returns `XR_ERROR_FORM_FACTOR_UNAVAILABLE` and there is no
session to intercept.

**Trip hazard:** an elevated shell makes the loader ignore `XR_RUNTIME_JSON`, and a bad manifest path or
wrong-bitness DLL makes it skip the manifest - **both fall back to the real runtime silently**, so every
later measurement is against the wrong runtime. Trust is asymmetric: a bug that reproduces in the
substitute is real, one that does not may still exist on the real runtime. State in writing what the
instrument will never model.

**Blind spot:** a substitute that force-grants focus cannot exercise session-state negotiation at all -
session begin, focus transitions, keepalive submission and re-attach are structurally unreachable in it
and in flat soaks alike. Prove those on a real runtime.

**Cheaper forms first.** Four projects in this survey built a substitute, and the price was set by
whether a seam already existed: an `UpdateViewCallback` implementation supplying fixed views (OpenMW-VR),
a build configuration swapping the VR backend (ForerunnerVR), or a full runtime (BioShock-Trilogy-VR).
Only the last proves protocol. **Put the VR backend behind an interface early and the instrument becomes
nearly free.**

## TEST-002 — An instrument must not report success when it failed to measure {#test-002}

**Problem:** a sampled diagnostic reports the *absence* of a bad thing, and absence is also what it
reports when it simply did not look in the right place.

**Use when:** any counter, watch or sampler whose coverage is partial - constant-buffer scans, draw-call
classifiers, pass censuses, periodic pollers.

**Recipe:** state the instrument's coverage in its own output header, and make the acceptance criterion
something that sees everything (a frame dump) while the cheap sampler stays a hint. Where coverage cannot
be made sound, say what the number is worth rather than making it look sound. Record failed attempts at
better coverage in the code so the next reader does not retry them.

**Proof:** compute what fraction of the population the instrument actually observes, and check that a
negative reading is distinguishable from a missed reading.

**Trip hazard:** the failure is one-directional - a sampling gap can only ever fake the *good* news, so
it never triggers an investigation. BioShock-Trilogy-VR's lens watch saw about 12 of 400-600 constant
buffers and produced six consecutive false positives before the header was fixed.

## TEST-003 — Expose the running game over a local control plane {#test-003}

**Problem:** every VR regression check needs a human in a headset, so nothing is automated and nothing
runs twice the same way.

**Use when:** you own enough of the target to add a debug server - a source port, an engine recreation,
or an injected mod with a free thread. Complements
[TEST-001](#test-001): a substitute runtime fakes the *runtime*, this exposes the *game*.

**Recipe:** run a small HTTP server in the process exposing step, screenshot, input injection, entity
queries and **a detachable debug camera**. Put a typed SDK over it so a regression is an ordinary test
file. Gate the camera behind a developer option, because a placement that the next step silently undoes
reads as a broken API.

**Proof:** a test launches the game, drives input, steps, screenshots and asserts - with no headset and
no human.

**Trip hazard:** a debug camera is a **second view**, so every per-view hazard applies to it. Culling may
still follow the *player*, so a camera in another room sees geometry culled for someone standing
elsewhere. Detaching may repurpose the locomotion sticks to fly the camera, so re-attach before driving.
And if the runtime composes a tracked head onto the camera pose, the placement divides out the head *as
it was at request time* - aim the head first, and re-place if you re-aim.

## TEST-004 — Audit where agent tokens actually go {#test-004}

**Problem:** agent cost is optimised by guesswork, so effort goes to whatever *feels* expensive rather
than what is.

**Use when:** agent sessions are a running cost on the project.

**Recipe:** join `tool_use` to `tool_result` across session transcripts, estimate tokens per result, and
rank commands by total. Let the ranking pick the fixes. shock2quest's 30-day audit found the cost was in
**reading habits, not tooling**: re-paging files already read that session, whole-file reads, wide greps
and full diffs - with repeat reads of the same path alone at ~6% of all tool-result tokens.

**Proof:** the top of the ranking is something nobody predicted. If it confirms what you assumed, check
the instrument before believing it.

**Trip hazard:** the resulting rules only stick if they are in the agent instructions file, not a chat
message. Theirs are four lines in `AGENTS.md`: outline before paging a file over ~800 lines; never re-read
what is in context; `git diff --stat` before any diff; narrow the grep before adding `-A/-B/-C`.

## AUDIO-001 — Two-ear tracked listener {#audio-001}

**Problem:** positional sound stays attached to body origin or rotates
incorrectly with the HMD.

**Use when:** the audio engine exposes listener/ear positions.

**Recipe:** derive left/right ears from the same tracked head pose and world
scale as rendering; update them continuously along with moving emitters.

**Proof:** translate and rotate around a stationary emitter while logging both
ears and emitter identity.

**Trip hazard:** applying game-to-metre scaling to the source but not the ears.

## AUDIO-002 — Separate spatial and listener-relative lanes {#audio-002}

**Problem:** UI/music is spatialized or world sounds become head-locked.

**Use when:** porting a flat audio system into VR.

**Recipe:** explicitly classify world positional emitters, listener-relative UI
and voice, ambience beds and music; preserve channel/preemption semantics.

**Proof:** menu/UI remains centered while the head turns; world sources do not.

**Trip hazard:** playing everything through a midpoint spatial sink and treating
its gain as neutral.

## NET-001 — Mod side-channel over the game's own transport {#net-001}

**Problem:** a VR mod in a multiplayer game needs to send data vanilla clients know nothing about - hand
poses, head pose, held-item state - without breaking players who do not have the mod.

**Use when:** any VR conversion of a game with networked multiplayer that you do not control.

**Recipe:** ride the game's existing transport rather than opening a socket. RepoXR tunnels its frames
through Photon's own serialization, tagged with a **magic constant** (`0x5245504F5852`, "REPOXR") and an
explicit **`PROTOCOL_VERSION`**, and resolves RPC targets through type/method hashcode maps rather than
names. Unmodded clients see traffic they ignore; modded clients of a different protocol version can be
detected and refused rather than silently misparsed.

**Proof:** join a session mixing modded and vanilla clients, and a session mixing two protocol versions;
neither may desync or crash the other.

**Trip hazard:** omitting the version field. A magic number alone tells you the peer has *a* version of
the mod, which is exactly the case where a wire-format change corrupts state.

## PACK-002 — The mod is one directory {#pack-002}

**Problem:** uninstalling leaves proxy DLLs, patched executables and scattered files behind, and nobody -
including you - can state what a clean machine looks like.

**Use when:** any release intended for users rather than for the developer's own machine.

**Recipe:** adopt BFVR's constraint verbatim and test it: **no release component may replace the game
executable, install a proxy DLL in the game root, modify game data, or require files in more than one
game folder.** Everything ships inside a single parent directory beside the executable; the mod's own
launcher locates the game relative to itself and loads its client module from within that directory.
Uninstall is deleting the folder.

**Proof:** install, run, delete the directory, and confirm a byte-identical vanilla game with no
leftover registry, proxy or config state.

**Trip hazard:** this rules out the proxy-DLL injection vector that several mods in this survey use
(`xinput1_3.dll`, `XINPUT1_3.dll`), so it is a constraint to adopt *before* choosing the vehicle, not
after.

## PACK-003 — Skip teardown when the process is terminating {#pack-003}

**Problem:** the game closes but the process lingers, or the runtime reports it still running - your
`DLL_PROCESS_DETACH` teardown is blocking on threads that no longer exist.

**Use when:** every injected DLL, and especially a VR mod, which holds runtime IPC threads, a
compositor session, GPU resources and its own workers.

**Recipe:** branch on `lpvReserved`. Non-`NULL` means **the process is terminating** and every other
thread is already dead - return immediately and let the OS reclaim everything. `NULL` means a dynamic
`FreeLibrary`, which is the only case where a real teardown is correct or possible. Handle the runtime's
quit event separately (`VREvent_Quit` or the OpenXR session-state equivalent) so you stop submitting
into a runtime that has gone away.

**Proof:** exit the game normally and confirm the process disappears from the task list; then exit the
VR runtime while the game is running and confirm the mod disarms rather than hanging.

**Trip hazard:** it may not reproduce on your machine - it depends on which threads happen to be alive
at exit - so treat the contract as the authority rather than a clean test. And `(void)lpvReserved;`
discards the one parameter that distinguishes the two cases; if you see that line, you have this bug.

## PACK-004 — Classify the target executable before injecting {#pack-004}

**Problem:** the loader attaches to whatever it is pointed at, and an unsupported executable becomes
a crash the user reports as the mod's fault.

**Use when:** any installer, loader or injector that attaches to a game the user supplies.

**Recipe:** map the executable **read-only** and inspect it before launching anything.

- **Classify by PE section.** A `UPX0` section means packed; a Steam DRM section means wrapped. Four
  outcomes - normal, wrapped, packed, unknown - and **refuse the ones you cannot support by name**.
- **Compare versions three ways.** Older than supported, *newer* than supported, and right version
  but wrong build branch are three different user actions and deserve three different messages. The
  newer-than-supported case is the one that happens to everyone the day the game updates.
- **Take the version from the version resource**, and keep any file hash for build identity rather
  than for compatibility - a hash changes for reasons that do not matter.

**Proof:** point the loader at a packed build, an older build and a newer build, and confirm each is
refused with its own message rather than attaching and failing later.

**Trip hazard:** a refusal is only useful if it names the fix. *"Unsupported executable"* sends the
user to a forum; *"packed versions are not supported"* and *"you are using a newer version than this
build supports"* do not. `[SOURCE]` F4SEVR loader.

## CFG-001 — One owner per setting, or write both together {#cfg-001}

**Problem:** the mod and the game each hold a copy of the same setting - resolution is the usual one -
and a change on either side silently reverts the other.

**Use when:** any mod whose behaviour depends on a value the game also persists.

**Recipe:** prefer a single owner. Where that is impossible, make one component write **both files
together** and keep them in sync by construction. MELE-VR's installer writes its own per-mode resolution
and the game's `GamerSettings.ini` in one step, because the mod re-asserts its remembered per-mode
resolution on every VR-mode switch - so a disagreement would quietly undo the quality tier the user
picked, at a moment they would attribute to the mode change.

**Proof:** change the setting on each side independently and confirm the other follows or refuses, never
silently reverts.

**Trip hazard:** the failure surfaces one action later than its cause, so users report it against the
wrong feature.

## CFG-002 — Ship a short config with tuned defaults, expand on first save {#cfg-002}

**Problem:** a config file exposing every knob is unreadable and invites damage; one exposing too few
leaves power users stuck.

**Use when:** any user-facing release with more than a handful of settings.

**Recipe:** ship a **deliberately short** file containing only what a user might reasonably change, with
every other setting carrying a tuned default baked into the binary. Rewrite the file with the full list
the first time the user saves from the in-game menu. Tune in-headset, not in a text editor. Pair it with
an explicit per-feature **kill-switch block** - GRAND's `[Debug]` section carries one disable flag for
each risky subsystem, including a compatibility mode that reverts to the parent mod's behaviour.

**Proof:** a fresh install runs correctly with the shipped file untouched, and every risky subsystem can
be disabled without editing code.

**Trip hazard:** binding profile hotkeys onto keys the game already uses. MELE-VR chose F1-F4
deliberately because 1-4 are Mass Effect's weapon keys and "a profile swap mid-combat is not what you
want" - check the *game's* bindings, not just your own.

## CAM-006 — Re-trigger initialisation through a benign engine event {#cam-006}

**Problem:** a state transition leaves the VR camera broken - typically exiting a vehicle, a cutscene or
a possession - and the re-initialisation you need is inside code you cannot reach or modify.

**Use when:** working *alongside* another mod, or against a closed path where the init exists but is not
callable.

**Recipe:** find a legitimate engine event that already triggers the re-initialisation and fire it
deliberately, then restore everything that event disturbed. GTA-VRV-Patcher restores head tracking after
a first-person vehicle exit by setting the player's ped model **to the same model it already was**, which
re-runs the underlying VR mod's init. It captures the full appearance before entry - 12 component and 8
prop variations - and restores it after the falling animation completes, so the round trip is invisible.
Apply the same handler to every transition in the family: they also cover death and arrest.

**Proof:** tracking recovers with no freeze, and appearance, velocity and in-progress animations survive
the round trip.

**Trip hazard:** the restore list is the whole cost, and it is easy to under-enumerate. Anything the
event resets that you do not save is silently lost.

## PACK-001 — Refuse, do not guess {#pack-001}

**Problem:** installer/runtime silently chooses an incompatible runtime, bitness
or game build.

**Use when:** release packaging and startup.

**Recipe:** detect exact architecture, runtime registration, adapter, game hash
and conflicting proxies. Produce actionable failure text and make no writes
when confidence is insufficient.

**Proof:** every unsupported configuration fails before modifying the install.

**Trip hazard:** “helpful” fallback selection creates an unreproducible hybrid.

## RE-010 — One game, several binaries: storefront and patch variants {#re-010}

**Problem:** the same game, bought from a different shop or patched a week later, is a *different
binary*. Every RVA, every vtable slot and every struct offset the project holds was measured against
one image, and nothing in the code says so. The mod then either crashes on a user's install or, worse,
runs and writes to the wrong place.

**Use when:** promoting any address to a hook table, importing an address map from another modder or
from a reference build (an SDK, a leaked PDB, a sibling storefront), or planning what ships.

**Recipe:**

1. **Never translate an address by arithmetic.** There is no global delta between builds, and the
   fleet has the measurement: seven Prey functions whose Steam **and** Epic addresses are both known
   show **five distinct deltas spanning `0x1590`** — code was inserted and removed unevenly, so one
   offset does not carry. Two of those seven pairs happen to share a delta, which is exactly how a
   bogus shortcut comes to look convincing. Translate each function by **its own byte signature**,
   confirmed on both images. `[LIVE]` PreyVR, `BUILD_BASELINE.md`.
2. **Do not put a `[RIP+disp32]` operand in a signature.** The displacement encodes the *distance* to
   a global, which moves whenever anything between the instruction and its target changes size. Such
   a signature is exact for one build and worthless for translation. An audit of 22 promoted Prey
   signatures found three carrying one. `[LIVE]` PreyVR.
3. **Gate on the whole image, then on each landmark.** Hash the target file to identify the build,
   and separately match exact bytes at each RVA you intend to hook, so a variant that slips past the
   hash still cannot be instrumented at a plausible-looking wrong address. **Fail closed**: an
   unrecognised build must disable hooks, not guess.
4. **Verify a relationship, not a number, wherever one exists.** A vtable slot should *contain*
   `imageBase + target`; a call site should be `0xE8` with `imageBase + rva + 5 + rel32` equal to the
   target. These survive being checked against the wrong build by failing, which a bare address
   comparison does not.
5. **Ship variant detection, not a variant assumption.** The shipped mod resolves which build it is
   on and selects that build's table, or refuses. A per-build table with an honest refusal is a mod
   that works on two stores; a single hardcoded table is a mod that works on one and corrupts the
   other.

**Proof:** run a *foreign* build's address map against your binary and require it to **fail**. Far
Cry 2 VR does exactly this: their verifier passes 7/7 on the Uplay/Steam map and **correctly fails
7/7** on the GOG map — wrong vtable values, and call sites that are not even `0xE8`. That negative
control is what makes the passing run mean something; without it the check may be accepting anything
handed to it. `[LIVE]` FarCry2-vr, `verify_dunia_port_map.py`.

**Trip hazard:** a reference build is an oracle, never a target. Chairloader's headers gave Prey
14,622 Epic RVAs — enormously useful as *names and leads*, and unusable as addresses. The failure is
seductive because copying one across often works by luck, and the resulting corruption appears
somewhere unrelated. Related: [FAIL-RE-027](failure-atlas.md).
