# Engine Integration & Safety

You're injecting code into a process you don't own and calling functions the developers never
exposed. The difference between a mod that's *debuggable* and one that *random-crashes the
user* is discipline at the integration boundary.

## Hooking & native-call discipline

- **Validate before you call.** Before calling a discovered native function, check its prologue
  bytes against the signature you reversed. If it doesn't match (patch, different build,
  ASLR confusion), **fail closed** — disable the lane, log it, never call. (*SS2VR's native
  axis/fire lanes signature-check the handler prologue and disable themselves on mismatch.*)
- **Guard every raw memory read/write with SEH** (or the platform equivalent) and treat
  non-finite / null as "unavailable," not "zero." A fail-open default that returns 0 can drive
  the game with bogus input; fail *closed*.
- **Do native calls on the right thread.** Engine functions usually assume the game/main thread.
  Calling them from the render thread or a worker is a race and an eventual crash. Queue the
  call to the thread the engine expects.
- **Don't mix SEH with C++ objects that have destructors** in the same frame — the unwinding
  models conflict. Keep the guarded region a plain C scope. (*SS2VR registry entry.*) In practice this
  means the guarded helper is **POD-only**: it takes raw pointers and scalars, returns a status code, and
  does nothing else. Logging, config mutation, `std::string` and any STL container live *outside* the
  `__try`. This isn't a style preference — MSVC rejects `__try` in a function that requires C++ object
  unwinding outright (C2712), so the discipline is enforced at compile time, and the tempting fix
  (wrapping a larger, more useful function) is the one that won't build.
- **Your global hooks will intercept your own calls.** If you detour a graphics API *and* make your own
  calls into it — compositing, blitting, probing, copying — every one of those runs through your own
  detour logic, lands in your own classification and telemetry, and can recursively re-enter submission.
  (*BioshockVR spent **six build cycles** chasing what looked like a Virtual Desktop runtime bug —
  `0xC0000409` fail-fast — before finding that its own OpenXR eye-blit was calling the same globally
  detoured D3D11/DXGI methods as the game.*) The fix is not runtime-specific and not a workaround: wrap
  all of your own API work in a **thread-local "this call is mine" scope**, and have every detour reachable
  from it call the original directly. This applies identically to D3D9/10/11/12, OpenGL and Vulkan layers.
- **On x64, not every callsite has room for a standard trampoline.** A 5-byte relative `jmp` needs 5 bytes
  of prologue to displace, and short virtual thunks do not have them. (*SOMAVR's `AddImpulse` wrapper was
  a 9-byte thunk — `mov rax,[rcx]; jmp [rax+0x130]` — requiring a guarded INT3-plus-absolute-jump applied
  only for a one-shot window instead of a permanent detour.*) Check the available prologue length before
  designing the hook, not after it corrupts the next function.
- **Wide positional argument lists transpose silently.** A function taking many same-typed args (a
  19-pointer `EndFrame`, two adjacent quad args) lets you swap two of them with no compile error and a
  subtle runtime bug. Convert to a named-field struct once an arg list gets wide. (*SS2VR.*)
- **Patching one decision branch can be safer than hooking** — when the engine already contains the
  behaviour you want and merely chooses the other path. Do it with full ceremony: require a **unique**
  signature, **verify the exact original bytes** at the patch offset before writing, write under
  temporary writable protection, flush the instruction cache, and on any mismatch log and leave stock
  behaviour completely untouched. (*HaloVR frees the shotgun's left support hand by flipping one
  conditional so the engine selects its own existing no-weapon-IK path — verifying the two original
  bytes are exactly `74 05` before writing `EB 18`. A synthetic replacement built from scratch had
  failed to move the same hand, because native weapon IK was the overriding consumer.*) Verify AOB
  **uniqueness** before hooking or patching anything; zero matches and multiple matches are both
  "disable the lane and log," never "take the first hit."

## Module lifecycle: three Windows loader hazards that look like engine bugs

These are loader mechanics, not engine behaviour, so they apply to any injected mod on any Windows game —
and all three present as something else.

- **Windows will not hot-swap a loaded DLL image.** While your module is loaded in the running game, the
  file on disk is locked; a rebuild *silently fails to overwrite it*, and the next test runs the old
  binary. (*BioshockVR: a tester spent a session on `0.3.19` while believing they were on `0.3.20`.*)
  Re-injecting the same module only bumps its refcount — it does not reload it. **Close the target
  before rebuilding**, and confirm the version from the self-ID banner ([06](06-debugging-methodology.md))
  before trusting any result.
- **Preload companion DLLs from your own module's directory.** Windows' default search order includes the
  *host executable's* folder, not your injected module's — so a dependency you ship beside your DLL is not
  on the path when a delay-load import first fires. (*SOMAVR: `somavr.dll` injected from
  `build-openxr\Release` could not find `openxr_loader.dll` sitting right next to it; the first delayed
  `xr*` call died with `0xc06d007e` in `KERNELBASE.dll` — the classic delay-load module-not-found.*) Resolve
  your own module's directory at load and `LoadLibrary` the companion explicitly, before any call that
  could trigger the delay-load.
- **Exit an injected worker thread on last-thread-in-process, not on a stop handshake.** Teardown is a
  race: the host is exiting, and the code that would signal your thread to stop may already be gone. A
  thread waiting for a signal that can never arrive keeps a dead process alive. (*SOMAVR found an orphaned
  worker running in a process with no window and exactly one thread; switching the exit condition to
  "return when I am the final thread" removed the orphan without needing the handshake to fire at all.*)
  Checking your own thread's cardinality is race-free; coordinating a clean stop during process death is
  not.

## Choose an experiment's write target by its lifetime, not just its semantics

When you need to perturb the running game to prove something, the safest write is one that **cannot
persist**. Editing a per-call scratch copy on the current stack frame means the edit disappears on return
— nothing to restore, and therefore nothing to forget to restore, even if you crash mid-experiment.

(*PreyVR's live interaction protocols edit only the twelve direction bytes of a **local ray copy inside the
current call's stack frame**: "the edit naturally disappears on return and does not require a
persistent-state restoration write." Camera, UI reticle and the player's cached aim state are explicitly
left untouched and verified unchanged afterwards. Both protocols completed with a confirmed effect. On
provenance — that convention was already house style in the project before the lane that applied it; it is
recorded here as a practice worth adopting, not as one project's invention.*)

This eliminates a whole class of restoration bugs rather than managing it. Before designing a
save-mutate-restore dance around persistent state, ask whether a transient copy of the same value passes
through a function you can already hook — writing there is strictly safer and usually just as conclusive.

## A boolean gate around several atomics is not a safe handoff

Passing a multi-field update — a pose, six offsets, a command packet — from your hook to a consumer on
another thread without a full mutex is standard practice and usually wrong on the first attempt. The
common shape is: clear an enable flag, write the fields, set the flag. A reader that arrives mid-write
sees a **torn mix of two generations**, each field individually valid.

The fix is a **sequence counter** the reader checks before and after its read, retrying if it changed —
the seqlock pattern. (*DishonoredVR's original camera handoff was `exchange(false)` → write six atomics →
re-enable. The replacement added a generation counter and was validated by an adversarial stress test:
**200,000 alternating writes** against concurrent snapshots, with zero mixed-generation reads in both
Debug and Release.*)

Note how that was verified. Code review cannot find this class of bug and cannot prove its absence —
only a concurrent stress test can, and it costs an afternoon.

The failure is worth seeing as code, because the broken version looks obviously fine:

```cpp
/* BROKEN. Each field is atomic; the SET as a whole is not. A reader that passes
   the gate can still observe pose from frame N and matrix from frame N+1. */
std::atomic<bool> g_ready{false};
std::atomic<Pose> g_pose;
std::atomic<Mat4> g_view;

void Producer(const Pose& p, const Mat4& v) {
    g_pose.store(p); g_view.store(v);       // <-- reader can land HERE
    g_ready.store(true, std::memory_order_release);
}

/* FIXED: a seqlock. One odd/even counter publishes the whole set atomically.
   Three independent projects in this playbook converged on this shape. */
struct Shared {
    std::atomic<uint32_t> seq{0};
    Pose pose;                              // plain members, not atomics
    Mat4 view;
};

void Publish(Shared& s, const Pose& p, const Mat4& v) {
    uint32_t q = s.seq.load(std::memory_order_relaxed);
    s.seq.store(q + 1, std::memory_order_relaxed);       // odd == writing
    std::atomic_thread_fence(std::memory_order_release);
    s.pose = p;
    s.view = v;
    std::atomic_thread_fence(std::memory_order_release);
    s.seq.store(q + 2, std::memory_order_release);       // even == complete
}

bool TryRead(const Shared& s, Pose& p, Mat4& v) {
    for (int spin = 0; spin < 8; ++spin) {
        uint32_t a = s.seq.load(std::memory_order_acquire);
        if (a & 1) continue;                             // writer mid-update
        std::atomic_thread_fence(std::memory_order_acquire);
        p = s.pose; v = s.view;
        std::atomic_thread_fence(std::memory_order_acquire);
        if (s.seq.load(std::memory_order_relaxed) == a) return true;   // nothing moved
    }
    return false;    /* Say so. Reusing last frame's pose is a decision the CALLER
                        must make -- silently doing it here is how a stale pose
                        becomes an unexplained one-frame judder. */
}
```

The `return false` is the part that gets dropped. A reader that always succeeds by falling back to the
previous value hides tearing *and* turns a diagnosable contention problem into an intermittent visual
artifact. Count the failures ([06](06-debugging-methodology.md)'s `offered`/`acted` pair) — a nonzero
retry rate is information, and a rate that climbs with frame time tells you where to look.

## A flag that answers two questions will oscillate

Give one boolean two jobs — **"what mode are we in"** (persistent ownership) and **"what just happened"**
(per-event state) — and it will flap, because every event of the second kind overwrites the answer to the
first.

(*FC2VR used one bit, `FEARVR_BF_STEREO_ACTIVE`, for both. Its host read that bit every XR frame to pick
`XrCompositionLayerProjection` when set and `XrCompositionLayerQuad` when clear. After a valid stereo
pair the bit was set — then any ordinary mono `Present` cleared it, while native stereo was still running.
The user saw the view **blinking between true VR and a flat theatre rectangle**. The fix was to suppress
only the *generic* clear (eight bytes NOPed), leaving every explicit transition — menu, comfort mode,
`SetStereoEnabled(false)`, shutdown — able to clear it as before. See
[17](17-teardown-fc2vr-native-stereo.md).*)

**The diagnostic tell: you are about to add a timeout or hysteresis to stop something flickering.** Stop
and check whether two meanings are sharing one variable first. Hysteresis over a conflated flag hides the
bug and leaves the flicker rate as a tuning parameter forever. Splitting them removes it.

Give the persistent one a name that reads as ownership (`g_stereoModeOwned`) and the transient one a name
that reads as an event (`lastPresentWasStereo`), and the conflation becomes hard to reintroduce.

## An XR frame lifecycle spread across two hooks needs an explicit state machine

The OpenXR frame contract ([09](09-d3d11-openxr-injection.md)) is a strict sequence — wait, begin,
render each eye, end. When your hooks sit in *different* engine functions, no single site can see the
whole sequence, and the naive implementation is a handful of booleans that drift out of agreement.

BF2VR's commit history records the fix in its title: **"Changed the XR render states to an enum rather
than a bunch of bools."**

```cpp
enum DrawStage { WAITED, DRAWING_L, DRAWN_L, DRAWING_R, DRAWN_R, COMPLETE };
static inline DrawStage drawStage = COMPLETE;
```

The lifecycle is then driven from two different hooks, each advancing the same single variable:

```text
Draw hook     COMPLETE           -> WaitBeginFrame()  -> WAITED
              WAITED / DRAWN_L   -> BeforeDraw()      -> DRAWING_L / DRAWING_R
Present hook  DRAWING_L/R        -> AfterDraw()       -> DRAWN_L / DRAWN_R
              DRAWN_R            -> EndFrame()        -> COMPLETE
```

**One variable with named states beats N booleans**, for the same reason
[a flag answering two questions oscillates](#a-flag-that-answers-two-questions-will-oscillate): with
booleans, the *illegal* combinations are representable and eventually occur. `DRAWING_L && DRAWN_R` is a
state a bool pair can hold and an enum cannot.

It also makes the abort path expressible. **Every early return in either hook must leave the stage
consistent** — and with an enum you can see at a glance which returns skip a transition, which is
exactly the audit that finds an unpaired `xrBeginFrame`.

## Borrowing engine state is a transaction — including the abort path

If you take over a live engine's camera, matrix stack, or render target mid-frame, you have opened a
transaction. Two things have to be true before it is safe:

- **Exact restore on the success path.** Not "close enough" — the engine will compare what you gave back
  against what it remembers.
- **An explicit, *visible* rollback on the abort path.** (*FC2VR ships a backbuffer restore for an
  aborted eye transaction and calls it "visible fail-back": a frame that is obviously wrong beats a frame
  that is subtly wrong, because only one of them gets reported.*) A half-restored camera is worse than no
  VR at all, because now the flat game is broken too and the cause is invisible.

**And the part everyone misses: the engine keeps observing while you hold its state.** Anything that
samples "the current camera" — observers, audio listeners, occlusion queries, LOD and streaming managers
— is still running mid-transaction, and will happily latch your scratch value as the real one.
[17](17-teardown-fc2vr-native-stereo.md) documents this costing a project a whole revision: the transient
camera written while building the left eye overwrote the stored *primary* camera, and the right eye was
then rejected for disagreeing with it.

### The dual: enumerate the readers for safety, find the *writer* for leverage

The rule above is about **not breaking things**. There is a second question about the same value, asked
for the opposite reason, and PreyVR's dependency analysis makes the asymmetry explicit:

> **Readers are usually many and individually tolerant. The writer is often exactly one function — and
> it is where a hook changes behaviour for every consumer at once.**

Their detached-aim lane is the worked example:

```text
R-011  UpdateCachedReticleViewPosAndDir     <- the SOLE WRITER, once per frame from OnPreRender
   |
   +-> cached ray at ArkPlayer +0x17D4 / +0x17E0
         |
         +-> R-013  GetReticleViewPositionAndDir   <- the sole reader, 14 incoming edges
                +-- CArkWeapon::GetReticleInfoForFiring
                +-- CArkWeapon::GetReticlePosition
                +-- ArkWrenchComponent::GetHits
                +-- ArkPlayerTargetSelector::UpdateCandidates
```

**That asymmetry is why detached aim was tractable at all**: steer the one cached value and firearms,
melee and interaction all follow, without touching any of them.

So ask both questions of any value you intend to take over:

| Question | Why | What you get |
|---|---|---|
| **What reads it?** | Safety — they will observe your transient state | The freeze list ([above](#borrowing-engine-state-is-a-transaction-including-the-abort-path)) |
| **What writes it?** | Leverage — one hook, every consumer | The seam worth hooking |

### Check articulation points, not degree

The method generalises, and it corrected an intuition that was confidently wrong.

> R-013 has **14 incoming edges**. R-011 has far fewer. **But R-011 is an articulation point and R-013
> is not.** Remove R-013 and the graph barely notices — four consumers, several paths. Remove R-011 and
> the whole lane detaches, because it is the only thing that writes the value.

**The busiest node and the load-bearing node are frequently not the same one**, and degree is the one
that catches your eye. Build the read/write graph for the value you want to borrow and look for the
*cut vertex* — the node whose removal disconnects the lane — rather than the node with the most edges.

Two caveats they raised about their own result, both worth carrying:

- **Centrality partly measures how much you documented each entry**, not just how important it is. That
  is attention bias, the same family as the attribution caveat elsewhere in this playbook — a graph
  built from your own notes inherits your own emphasis.
- **"Is a cut vertex" is common.** Their graph had **121** articulation points. R-011 is interesting
  because of *what* detaches when you remove it, not because anything does. Rank by the size and
  relevance of the severed component, not by the property itself.

Before you borrow a field, **enumerate what reads it** and freeze those for the duration of the
transaction. This failure is silent and it does not look like a state bug — it looks like your second
eye is computing the wrong answer.

## Never read your own output back as fresh input

Any hook that both **writes** a value and later **reads** "the current value" to compute the next update
can close a loop with itself. The tell is a quantity that grows or drifts monotonically across frames
while every individual step looks correct.

(*SOMAVR hit this three times under three different names before naming the pattern. Native object
distance grew `0.4272 → 1.4772` because each frame multiplied the already-modified matrix again; later,
an object entered at `0.4586` and the mod observed its own previously-submitted `0.8842` and `1.4697`
outputs as if they were new native input and scaled them again.*)

**The fix is always the same shape: latch one immutable source value per object/session, and derive every
frame from that snapshot — never from your own last output.** Chapter
[01](01-camera-and-tracking.md) notes the camera-specific case (a system that reads the camera and then
moves it); this is the general form, and it applies to any transform, offset or scalar you both produce
and consume.

## Enable a hook set atomically, not one at a time {#atomic-hook-enable}

A small, concrete injection hazard with an intermittent symptom, which is the worst kind. `[SOURCE]`

> MinHook activation is **queued for all six hooks and applied atomically** with `MH_ApplyQueued`.
> Enabling hooks individually caused an **intermittent execute access violation** while the render
> thread was active.

**Enabling hooks one at a time races whatever is already running.** Between the first `MH_EnableHook`
and the last, the process is in a state you never designed: some detours live, some not, and a render
thread mid-frame can walk into the seam. It is intermittent because it depends on where that thread
happens to be, which is why it survives testing and appears on someone else's machine.

**Queue the whole set and apply it in one operation.** MinHook's `MH_QueueEnableHook` /
`MH_ApplyQueued` exist for this; other libraries have equivalents, and where none exists, suspend the
other threads for the duration. The same reasoning applies to *disabling* a set.

## Some engine defects get worse *because* you added VR {#vr-amplified-defect}

Condemned VR found a frame-rate defect in LithTech Jupiter EX that a VR mod amplifies by
construction, and the shape is worth watching for on any engine. `[SOURCE]`

> Condemned `1.0.314.0` contains the same **redundant HID/joystick initialization** pattern that causes
> F.E.A.R.'s **device-count-dependent frame-rate loss**.

**Device-count-dependent** is the whole point. A VR mod attaches controllers, so it walks into the worst
case of a defect that was merely latent for a keyboard-and-mouse player - and the symptom arrives
looking like the mod's own cost. This is the third Jupiter EX project in this survey
([fear-vr](17-teardown-fc2vr-native-stereo.md), FEAR2VR, Condemned VR), which makes it an engine
property rather than a game one: **check it on any Jupiter EX target before profiling your own code.**

**Ask the amplification question generally.** Before attributing a regression to your mod, ask whether
it added *quantity* to something the engine handles badly - input devices, render targets, swapchains,
threads, cameras. An `O(n)` cost the base game never exercised is not your bug, but it is now your
problem.

### The patch discipline is the reusable half

Their correction is *"deliberately narrower than loading EchoPatch"* - a targeted runtime patch rather
than a general community binary patch - and every step is a guard:

- require the **verified executable identity**: SHA-256
  `45A1404F213EDBDEAD16168B6E005B245B93105F7345AAF4FB83ECB6A7C5AE02` and PE timestamp `0x43FCFF00`;
- verify **all 76 live bytes** at RVAs `0x82670`, `0x826F6`, `0x82780`;
- NOP all three ranges **only when every identity and byte check passes**;
- otherwise **leave the running image unchanged and fail the guarded launch**;
- **never modify `Condemned.exe` on disk**;
- apply it **before the late D3D hooks**;
- log `hid_fps_fix_applied` on success, and keep a `-NoHidFpsFix` switch for A/B rollback.

Three of those are easy to skip and each is load-bearing. **Patch memory, never the file** - an on-disk
edit outlives your session, breaks verification, and turns a reversible experiment into a support
burden. **Fail the launch rather than continuing unpatched** - a mod that silently skips its own fix
produces a performance mystery on someone else's machine. And **keep the rollback switch**, because a
patch with no off position cannot be A/B tested, which means its benefit is asserted rather than
measured ([TEST-010](pattern-catalog.md#test-010)).

## The other half of the DllMain contract: do nothing on process termination {#dllmain-detach}

The playbook already says keep initialisation off the loader lock. **The detach side has its own rule,
it is the one that produces zombie processes, and one parameter tells you which case you are in.**
`[SOURCE]`

Psychonauts VR's mod hung on exit and left the process alive. The root cause is a documented-contract
violation, not an environment quirk - *"note it did NOT reproduce on the dev machine"*:

> `lpvReserved != NULL` at `DLL_PROCESS_DETACH` means the process is terminating and **every other
> thread** (vrclient's IPC threads, D3D driver workers) **is ALREADY dead** - the blocking teardown then
> **waits on corpses under loader lock**.

```cpp
BOOL WINAPI DllMain(HINSTANCE h, DWORD reason, LPVOID lpvReserved) {
    if (reason == DLL_PROCESS_DETACH) {
        if (lpvReserved != nullptr) return TRUE;   // process exiting: the OS reclaims everything
        FullTeardown();                            // dynamic FreeLibrary only
    }
    ...
}
```

**Skip all teardown on process termination.** Per the documented contract the OS reclaims the address
space, the handles and the threads; there is nothing your teardown can usefully do and several things it
can hang on. Run the real teardown only for a dynamic `FreeLibrary` unload.

Their note on how it got there is the part worth quoting, because it is easy to write:

> The old `DllMain` literally had `(void)lpvReserved;` - **discarding the one parameter that
> distinguishes the two cases.**

A VR mod is unusually exposed to this: it holds runtime IPC threads, a compositor session, GPU
resources and its own worker threads, so it has more to wait on at exit than most DLLs do. And the
symptom - the game window closes but the process lingers, or SteamVR reports it still running - looks
like a runtime bug rather than yours. See [PACK-003](pattern-catalog.md#pack-003).

Related, from the same session: **handle the runtime's own quit event.** Theirs added `VREvent_Quit`
handling and verified it end to end by exiting SteamVR while the game ran - otherwise the mod keeps
submitting into a runtime that has gone away.

## A stripped copy protection can leave the game permanently sabotaging itself {#dead-drm-sabotage}

The DRM section below is about DRM that is *present*. This is the opposite and much stranger case, and
if you mod games of a certain age you will be blamed for it. `[SOURCE]`

Manhunt (2003) on Steam is a known-buggy release - gates that never open, crashes when swapping items,
memory leaks - and the community framing has always been "leftover SecuROM checks that misfire". A
2026-08 investigation read the actual code and found the framing too gentle:

> It isn't misfiring at all - it is working exactly as designed. The game is **deliberately sabotaging
> itself**, on legitimately purchased copies, because a dead copy-protection can no longer answer a
> question it asks.

**The mechanism, and why it is permanent.** SecuROM had replaced certain imports with its own stubs that
returned magic values. When the protection was stripped for re-release, those call sites were repointed
at the **real** Windows APIs. One of sixteen sites, named "Drop Item Timer":

```asm
004C7891: mov  edx, 0xDD31             ; magic arguments SecuROM's stub expected
004C7896: mov  ecx, 0xC121
004C789B: mov  ebx, 0xFA0C
004C78A0: call [0x0081B380]            ; once a SecuROM stub - now the real GetVersion
004C78A6: cmp  eax, 1                  ; the stub used to return 1
004C78A9: je   0x004C78B5              ; got 1? fine, carry on
004C78AB: mov  dword [0x0073731C], 0xFE   ; didn't? SABOTAGE
```

**When the check fails the game does not error, warn or refuse to run.** It writes a poison value into
its own state and carries on, so the damage surfaces later as something that looks like an ordinary bug.
The real `GetVersion` returns a Windows version number and will never return `1`, so that sabotage fires
on every copy, every launch, forever. The other sites differ in kind, which is why the symptoms are so
varied:

| Site | What the stub used to do | What the real API does | Symptom |
|---|---|---|---|
| Drop Item Timer | return `1` | returns a version number | poison value written into game state |
| Broken Doors | **write to a global** (`0x007387A0`) | `GetCurrentThread` writes nothing | the global keeps stale data - the stuck-gate bug |
| `GetLastError` @ `0x0045A30C` | set `0x3E5` (`ERROR_IO_PENDING`) | never sets it | the function returns failure |

Sixteen tripwires, each with its own expected answer, all permanently unanswerable.

**Three things to take from this.**

**Rule yourself out properly, and more than one way.** They had a proxy DLL, D3D hooks, an input hook and
a memory patch in that process. Before blaming the game they disabled the proxy entirely and got a plain
vanilla run: *same faulting address `0x004C9AAD`, same trigger, `d3d8.dll` renamed away, no log written,
our code demonstrably not in the process.* Three-way confirmation - and their own note on why they
bothered is the part worth keeping: *"we'd already been wrong three times that day."*

**Dump the unpacked image once, then work offline.** The executable is packed at rest and a debugger
cannot attach, so reading its real code meant dumping the fully unpacked image from memory. After that
the entire investigation ran with **no further launches** - sixteen sites located and decoded statically.
When a target resists live inspection, one good dump converts the whole problem into offline work.

**A stale-DRM symptom looks exactly like a mod bug.** Crashes on item swap, doors that never open, state
that is subtly wrong - these are precisely what a bad hook produces. On any pre-2010 re-release, check
whether the game misbehaves *without you* before spending a week on your own code.

## Know which modules are DRM, and exclude them early

A protected release carries modules that are **not engine code** and must never become RE targets.
Identify them in your first module census and write them down, because they explain otherwise-baffling
behaviour: DRM layers carry **anti-debug**, which is a standing hypothesis whenever attaching a debugger
kills the process.

- Judge by exports, not by name or size. (*FarCry2-VR's `FC2.dll` is 410 KB with 1,696 functions —
  and exactly **one export**, `drm_pagui_doit`, the SecuROM activation GUI entry point. Large and
  function-dense, entirely irrelevant.*)
- Note that a repack or a patched install may not load them at all — worth confirming at runtime rather
  than assuming. (*The same project later found `FC2.dll=absent` during a successful injection: the DRM
  it had budgeted for was never in the process.*)

## Debuggers have an attach *window*, not just an attach *mode*

Chapter [06](06-debugging-methodology.md) covers what tools lie about; this is when they kill things.
Attaching a debugger during a game's **startup** can take down both the game and the debugger — startup
paths run hardware detection, DRM checks and anti-debug, and are the most fragile moment in the process's
life.

Prefer to **attach after the main menu**, or launch from your own suspended-create launcher. Note that a
debugger's own "open executable" path will not reproduce whatever launch conditions your game needs —
affinity masks, environment, working directory — so if your target has a launch precondition
([08](08-project-process.md)), the debugger's launch path will violate it. (*FarCry2-VR: `File > Open` of
the exe hits the startup crash the affinity mask exists to prevent.*)

## Hardware/debugger gotchas

- Hardware breakpoints can be consumed or cleared by the game's own anti-debug or input
  threads; don't trust them to stay set. (*SS2VR: x64dbg hardware breakpoints entry.*)
- Some engines re-assert state every frame (overlay flags, draw flags, camera values). A
  one-shot write gets overwritten; you may need to re-apply every frame or hook the writer.

## Everything default-off, behind a knob

- New behavior ships **disabled by default** and gated by a config key. You enable it
  deliberately for a test. This keeps the baseline always-playable and makes A/B trivial.
- **Every change has a revert knob** — a single config value or console command that restores
  the prior behavior live, ideally without a restart. (*SS2VR convention: `..._frame=camera`
  to undo hand-frame offsets, `conv_cam 0`, `family_filter 0`, etc. — each fix was A/B-able
  in-headset in seconds.*)
- Prefer **live console cvars** over restart-required config for anything you'll tune by feel
  (offsets, signs, thresholds). The headset round-trip is expensive; live tuning is worth the
  plumbing.

**A diagnostic knob must never gate shipped behaviour.** When a probe births a fix, the fix moves out of
the probe's code path — otherwise the diagnostic is quietly load-bearing and can never be switched off.
(*SS2VR shipped a viewmodel-depth fix that only armed **inside** the probe branch, so the probe stayed
enabled in the live config long after its question was answered — while issuing ~840 log writes/s from
the render thread. Both the perf cost and the inability to turn it off traced to the same mistake.*) When
a probe graduates, split it: the fix takes its own gate, the probe keeps its own, and you verify the fix
still works with the probe off.

**Stage a new bridge log-only until the far end proves live.** Anything with two halves — a script/native
bridge, an IPC channel, a companion process — starts default-off or log-only and refuses to activate
until it has seen a *fresh heartbeat* from the other side. (*SS2VR applies this across reload/holster
physics, viewmodel probes and the FlatAim Squirrel bridge; the DLL will not publish config traffic to a
script bridge that hasn't announced itself, precisely because the earlier version happily published to
nothing and left high-rate traffic running with no consumer — which then coincided with a save-load
crash.*) A bridge publishing into the void is not inert: it costs frametime and it fabricates the
appearance of a working link.

**But don't let a knob become a graveyard.** There's a real tension here worth naming: a config gate is
the right home for a *shipping* feature you want A/B-able, and the wrong home for a *failed experiment*.
HaloVR takes the stricter line — "one hypothesis per headset build; a failed experiment is reverted, not
hidden behind a config flag" — and it's a good corrective. Dormant switches, dead probes and abandoned
fallback paths accumulate into exactly the ownership confusion that chapter
[09](09-d3d11-openxr-injection.md) warns about, and they make the next bisection harder. Ship knobs for
things that work; delete the things that didn't. (*HaloVR also learned the matching lesson the hard way:
a broad "cleanup" build that touched many paths at once launched fine and then hit a fatal error at the
first level transition — clean **one independently verified path per headset build**.*)

## Config-system rigor

- If your config has a **validation/whitelist layer**, adding a key means editing *every* stage
  in lockstep (struct field, parser, template, **and** the whitelist). Miss one and the key is
  silently rejected — and that rejection often looks *identical* to running a stale build.
  (*SS2VR lost a day to exactly this; it became hard rule #1 in the project's CLAUDE.md.*)
- After adding a key, **confirm from logs** that the running build accepts it (no "unknown key"
  warning) before asking anyone to test it. An unverifiable test precondition wastes a whole
  session.
- **Log the config's identity, not just its values.** A cloud-synced or redirected config file can
  silently override you, and the symptom looks identical to a stale build. (*SS2VR: a cloud-synced
  `joystick_enable 0` disabled analog sticks on a fresh install. BioshockVR: a stale OneDrive-redirected
  INI invalidated tests until a mandatory `config_identity` log line — path, mtime, key hash — made the
  wrong file obvious.*) Emit which file you actually read and when it was last written.
- **An `AUTO`/sentinel value must be resolved by *every* consumer, not just the setter.** (*SS2VR:
  `cursor_injection_width=0` meant "auto → live backbuffer"; the setter resolved it but the getter
  clamped against the raw `0`, zeroing every injected pixel — the inventory pointer went dead and looked
  like an unrelated feature had broken it.*) If a value has a sentinel resolved to a live dimension,
  resolve it at every read site or store the resolved value once.

## Initialization timing

- **Don't initialize the VR runtime too early.** Starting OpenXR before the engine's graphics
  device/swapchain is ready races device creation and crashes or hangs. Wait for a stable
  signal (first present, device registered), and prefer explicit/manual start during bring-up.
  (*SS2VR registry: auto-starting OpenXR too early.*)
- Assume your hooks can be invoked before your own state is ready; null-check your own
  singletons on every hook entry.

## D3D11 state and resource ownership

- Capture and restore every state category a private replay/blit touches: render targets,
  depth-stencil state, blend state, viewports, scissors, shaders, constant buffers, SRVs, and
  samplers. Use scoped guards so early returns restore state automatically.
- Respect COM ownership. Every `Get*` call that returns an interface usually adds a reference;
  balance it. A long session finds leaks that a two-minute proof does not.
- Do not bind a texture simultaneously as an RTV/DSV and SRV in conflicting roles. Explicitly
  unbind hazards before copies or fullscreen sampling.
- Keep left/right private depth independent and clear once per eye view. Per-draw clears erase
  occlusion; one shared depth target cross-contaminates eyes.
- Preserve the original game draw during early private-eye work. Suppression should target only
  the private replay until the replacement path is proven complete.

For an **OpenGL** target the same discipline applies to a different, broader surface — a global state
machine and FBOs rather than a context's bound list. See [10](10-graphics-apis.md) for what to
save/restore and why it's less forgiving.

## When a feature crashes the runtime, quarantine it — don't paper over it

A feature whose resource lifetime is tangled with the OpenXR/compositor's own resources can hard-crash
the runtime, and the temptation is to wrap it in exception handling, force-release, or global locks.
That hides a real ownership bug behind a fragile guard. The correct response is to **quarantine the
feature behind its config knob (default-off) and redesign the ownership**, keeping observation-only
diagnostics alive in the meantime.

- *BioshockVR:* per-eye shadow-mask mutation produced repeated fail-fast crashes (`0xC0000409`) with an
  execute-AV on freed-poison `0xDEDEDEDE` during D3D11 texture / `ovr_DestroyTextureSwapChain`
  teardown, under Virtual Desktop's runtime. The fix was to force `StereoWorldPerEyeShadowMask=0` and
  isolate per-eye resource lifetime from swapchain teardown — not to swallow the exception. A revert
  knob (chapter above) is what makes this a one-line containment instead of a lost build.

## The hardening layer an old engine eventually needs {#engine-hardening}

Once a mod ships to people who are not you, a third category of work appears beside features and
bugs: **the engine's own defects, which are now yours to route around.** Buffout 4 NG is the mature
form of that layer and its 39-line config is a good statement of the shape. `[SOURCE]`

### A defect registry where every entry names its cause and is individually switchable

Twenty-two named fixes, each one line, each saying what it fixes:

```toml
UnalignedLoad = true    # Fixes a crash related to SIMD intrinsics with an aligned move on unaligned memory
SafeExit      = true    # Fixes crashes related to exiting the game caused erroneously by F4SE plugin hooks
CellInit      = true    # Fixes a crash where a form does not get converted to a form pointer on unloaded cells
InteriorNavCut = true   # ...persists throughout all interior cells. https://simsettlements.com/...
```

Two things make this more than a changelog. **Each fix is a toggle**, so it is a bisection axis in
the sense of [config bisection](08-project-process.md#config-bisection) - a user with a crash can be
asked to flip one. And **each carries its cause in one sentence**, sometimes with a link to the
community report, so the registry doubles as the engine's failure atlas. Our own
[failure atlas](failure-atlas.md) is the same instrument pointed at the fleet rather than at one
engine.

`SafeExit` deserves its own note: **it fixes crashes caused by plugin hooks like ours**, at shutdown.
A framework mature enough to route around its own extensions is a good model for a fleet whose mods
all inject.

### A warnings tier: say it before it crashes

The category most mods lack.

```toml
[Warnings]
CreateTexture2D   = true  # Warns when a call to CreateTexture2D fails
ImageSpaceAdapter = true  # Warns on bad IMAD definitions which will corrupt your memory and crash your game
```

**A warning fires where the bad data is introduced; the crash happens later somewhere unrelated.**
That distance is the whole cost of diagnosing it. Any place your mod tolerates a failed call or
accepts data it knows is malformed is a candidate - the warning costs a branch and saves the session
where someone bisects a crash that had nothing to do with where it landed.

### Old engines ship allocators that the OS now beats

Five of its patches replace a bespoke allocator with the operating system's: the global memory
manager, the Scaleform allocator, the small-block allocator, the Havok memory system and the texture
streamer's local heap. A sixth, `MemoryManagerDebug`, **traces allocations to attribute faults to
modules** - which is the "whose bug is this" question again.

These were reasonable engineering in 2008 and are now slower and more fragile than the default
allocator, and several fleet targets are that vintage. It is not free - it changes allocation
behaviour under you - but on an engine that is crashing in its own heap it is the shorter path.
`MaxStdIO = 2048` is the same shape at a smaller scale: the CRT's 512-handle default is a limit the
engine was never designed to reach, and modding reaches it.

## Classify a fault before deciding how long it lasts {#fault-permanence}

A mod's fault policy is usually one policy: something went wrong, so stop. That is wrong in both
directions at once - it retires the mod on a fault that would have cleared by itself, and it keeps
retrying one that never will.

**There are at least three classes, and they want different answers.** `[AUTHOR]` SS2VR's harness,
v3.71:

| Class | Example | Right response |
|---|---|---|
| **transient** | a subsystem is not initialised *yet* | retry, **rate-limited** - theirs is at most once per second |
| **structural** | a signature did not match; the executor faulted | **latch off permanently for this process** - it will not become true later |
| **absent** | the first packet has not arrived | return WAIT and submit nothing, per [FAIL-XR-023](failure-atlas.md) - neither retry storm nor latch |

A rate limit is what makes the transient case safe to retry at all: without one, "not ready yet"
becomes a hot loop that competes with the very initialisation it is waiting for.

### The catch that cost the session

The sharper half of the same work. `[AUTHOR]` SS2VR sent a `set` command before the Dark Engine's
configuration table had initialised, which called through a **null function pointer**. The exception
*was* caught - and the catch **disabled automation for the whole session**. The crash was prevented
and the session was still lost.

**A caught exception is not a handled one.** Ask what the recovery policy costs, because that cost is
paid every time the guard fires, and a guard that quietly retires a subsystem is indistinguishable
from the subsystem never having worked. The fix was not a better catch: **wait for verified
initialisation, then execute once** - and keep a read-only subset alive during the unsafe window, so
the harness can still answer `@status` while it is not yet safe to write. *Available-for-reading
during startup, refusing to write* is a better shape than *entirely absent until ready*.

### A control plane must not depend on a diagnostic being switched on

The same release fixed agent polling that **only worked when frametime logging and the flight
recorder were enabled**. A control plane whose liveness rides on a diagnostic flag is a control plane
that disappears exactly when someone turns the noise off - and the failure looks like the bridge
being broken, not like a coupling.

Two flags that can each be on or off make **four** configurations, and the fleet keeps finding that
only one or two get tested. Theirs were verified across all four. See
[three configurations](08-project-process.md#three-configurations) for the same shape at the
project level.

## "Installed at a verified-correct address and never fires" = you hooked a wrapper

A specific, repeating failure with a specific cause. Your hook installs cleanly, at an address you have
independently verified, on an interface the game demonstrably uses — and it **never fires**, while the
game renders perfectly. The mechanism self-tests fine in isolation.

The usual cause is that **the object the game holds is not the object you hooked.** Something has
interposed a wrapper between the game and the API:

- **Windows' own app-compat shims.** `AcLayers.dll` / `apphelp.dll` wrap COM interfaces for older
  titles as a compatibility fix. This is invisible unless you look for it, and it is *more* likely
  exactly where you are working — old games are what shims exist for.
- Third-party overlays, ReShade/3D-fix layers, or another mod already resident.
- The game's own abstraction layer holding a proxy object.
- **Overlay, capture and anti-cheat software wrapping the same creation entry points you need.** Steam
  Overlay, Discord, ReShade and friends hook exactly `Direct3DCreate9`, `IDXGIFactory::CreateSwapChain`
  and their relatives — the same functions a VR mod must reach. (*DishonoredVR found the Steam Overlay
  already proxying `IDirect3D9` in its target process, which matters doubly there because the plan
  requires **replacing** the device with an `Ex` one: a hook that appears installed at a verified address
  may be calling another party's wrapper rather than the driver, and "upgrade the device" then means
  something different from what you intended.*) An interposer can also wrap **one** interface in an object
  graph while a sibling interface stays native — so proving one pointer is clean says nothing about the
  next.
- **The runtime rewriting its own dispatch table, with no wrapper involved at all.** (*FarCry2-VR's
  vtable entries moved `0x63aa1790` → `0x63aa16e0` — **both addresses inside `d3d11.dll`** — because
  `d3d10core` swaps its dispatch table every frame. An interposed wrapper would have pointed *out* of the
  runtime module.*) Same symptom, different mechanism, and it changes the fix: re-resolving once is not
  enough if the table is rewritten per frame.

**Read the two addresses before you conclude which cause you have.** If the replaced pointer still lands
*inside the API's own module*, you are looking at the runtime reorganising itself, not at an
interposition — and hunting for a shim will waste the session.

**The fix generalises: hook the *implementation*, not the interface.** Resolve the real function
addresses at runtime — typically by creating a throwaway device of your own and dumping its vtable, or
by resolving from a live resource back to its owning device — and inline-hook those addresses. A wrapper
can interpose on an interface pointer; it cannot easily interpose on the implementation everyone
eventually calls. This is wrapper-proof by construction.

Diagnostics that separate this from the alternatives, cheaply:

- **Is a shim actually loaded?** Check the live module list for `AcLayers.dll` / `apphelp.dll`.
- **Does something on the same object work?** If `Present` fires but the draw calls do not, ask whether
  they are reached through *different objects*, not different mechanisms.
- **Does the implementation get hit at all?** A debugger breakpoint on the API's own exported
  implementation answers this directly. (*Swat4-VR confirmed the game reached `d3d9.dll`'s
  `CreateTexture` implementation 3,300 times while their interface-level hook sat silent.*)

(*Recorded on Swat4-VR as `F-0007`. FarCry2-VR hit the identical **symptom** on D3D10 days later and
initially assumed the same cause — the app-compat shims were in fact resident in their process too — but
on checking the addresses found a different mechanism entirely, as above. Two projects, two APIs, one
symptom, **two** cause classes: which is exactly why the address check is the first diagnostic, not the
shim check. FarCry2-VR's eventual fix was to hook the engine's own render-device vtable instead —
115 M draws intercepted.*)

## Budget OpenXR composition layers — over-submitting freezes the whole HMD

`xrEndFrame` accepts a bounded number of composition layers — the spec only guarantees **16**. Every
always/often-on layer you add (world projection, HUD quad, reticle, vignette, debug overlays) counts
against it, and blowing the cap is not a soft failure. (*SS2VR: a parry overlay growing 5→7 layers
pushed the total past 16 with combat HUD/beams present; `xrEndFrame` returned `-24`
`XR_ERROR_LAYER_LIMIT_EXCEEDED` **every frame**, freezing the HMD while the flat game kept running — not
a crash, so easy to misread.*) Hard-cap the submitted count, push **most-important-first** so the cap
drops debug layers rather than projection/HUD, and size the layer array with headroom (a too-small array
is a stack overflow, not a clamp).

**The floor is a hazard too: never submit *zero* layers.** The obvious way to implement a comfort
blackout or a paced frame is to submit nothing — and layer count is part of the runtime's frame contract,
not a free toggle. (*BioshockVR reproduced the same fail-fast in two independent crash dumps under a
streaming runtime — an execute-access violation on a freed marker `0xDEDEDEDE` — correlated specifically
with `layerCount=0` submissions. Streaming and compositor-in-the-loop runtimes exercise distinct code
paths on layer-count transitions.*) **Keep the projection layer present every frame and clear its eye
images to black.** "Submit black" is safe; "submit nothing" is a different code path in someone else's
runtime.

**And enumerate the API layers sitting in front of you.** OpenXR supports third-party *implicit* layers —
motion compensation, overlays, performance tools — that insert themselves into your call chain without
appearing anywhere in your project. (*BioshockVR traced a reproducible fail-fast to a 32-bit motion-
compensation implicit layer silently present in the OpenXR-to-D3D11 chain.*) Treat this as the same
discipline as the DRM-module census above: enumerate the active layers as a standard diagnostic, and
disable a suspect one **per-process** — never by uninstalling it or editing the system-wide layer
registry, because other software on the machine may depend on it.

**Log every layer you find; blocklist only the one you've proven.** A guard that excludes one named DLL
fixes today's incident and leaves the next one looking identical. (*BioshockVR's containment build
fail-closes on `motion_compensation_32` specifically — so an updated install under a new name, an overlay
tool, or a performance layer reproduces the same `0xC0000409` signature with nothing in the log to
distinguish it.*) At startup, walk the registry's implicit-layer manifests **and** the loaded module list,
and print everything present. Exclusion is a policy decision that needs evidence; **visibility is free**,
and one log line turns the next mystery fail-fast into a glance.

## Don't over-reject "implausible" values — they may be a valid branch

Fail-closed on non-finite/null is right; rejecting merely *surprising* values is not. A constant that
looks wrong for one code path can be exactly correct for another. (*BioshockVR: a light `invradius` of
`-2.78524` is valid for the directional-light `w=0` branch; a non-negative guard that was correct for
the point-light `w=1` branch silently disabled the wrench's lighting.*) Gate on the branch/semantics,
not on a blanket plausibility range.

## Attach versus launch injection — and one-time construction seams

Attach-to-running is fast but misses device, swapchain, shader, and resource creation that
happened before injection. A launch-suspended path gives early coverage: create suspended,
inject, then resume. Keep both modes because some capture/runtime combinations behave better
with one than the other, and log which path was used.

The sharper version of this, on engines with rich object models: some native systems are constructed
**exactly once**, at a seam that attach-to-running can never retroactively exercise. If you need to
hook that construction, you need to be installed *before it runs* — and a plain suspended launch may
still be too late.

- *BioshockVR:* the native `AimIKTargetTracker` is created only inside
  `AActor::RecreateActorAnimationMembers` during natural `AHands` construction. Attach-to-running kept
  the already-built hands and a null tracker through 1200+ callbacks; equip transitions and ordinary
  play never re-run the seam. And `--launch` alone wasn't enough either: the remote `LoadLibraryW`
  completed *before* the DLL's async hook-install worker finished, so the hook wasn't armed when the
  seam fired. The fix is a **hook-ready handshake** — the launcher waits for the DLL to signal
  "hooks installed" before letting the game proceed to first construction. "The wrapper is null" is a
  *waiting* state; never manufacture a pass by allocating the object or forcing recreation yourself.

**The corollary is quieter and catches more people: every cache you build from creation-time hooks is
blind to whatever existed before you attached — and a cache miss reads as a negative result.** This is
the same root cause as the seam problem, but it produces a wrong *classification* rather than a missing
object, so it doesn't announce itself.

(*BioshockVR seeds shader identity only from `Create*Shader` interception. Under attach-mode the game had
already created and bound its shaders, so the classifier reported **every** sampled draw as PS-null —
which made it misclassify a whole family of mask draws as stencil volumes and left the real shadow
producer unreachable. Forcing live `VSGetShader`/`PSGetShader` queries at classification time immediately
exposed the shadow-test pass and its constant contract.*)

**Rule: anything classification-critical queries the live API; the cache is for cheap correlation only.**
Chapter [06](06-debugging-methodology.md) states the general form — a cache lookup lies where a live query
wouldn't — and attach-mode injection is what makes it near-certain rather than occasional. Two more
practical notes: independent capture stages that each poll a hotkey **will** disagree about a short
press, so arm the later stage explicitly from the earlier one rather than letting both poll; and if you
support both injection modes, log which one ran, because half these symptoms are mode-specific.

**Make injection itself fail closed.** A false "it worked" costs a whole session of downstream evidence,
and two states in particular are unrecoverable in place: two versions of your DLL in one process, and an
injection that hung rather than completed. The minimum guard set is *refuse if the module is already
loaded*, *bound the remote thread's wait with an explicit failure* (a stall otherwise masquerades as
success), and *verify the module is actually present afterwards*. On timeout, deliberately **do not** free
memory the still-running remote thread might still read.

Finally, **preflight architecture, version and hash before the injector touches the process at all.** The
self-ID banner ([06](06-debugging-methodology.md)) is necessary but it prints *after* a wrong-architecture
or stale binary is already inside a live process. Put the precondition check at the earliest chokepoint
both injection paths share.

## When several titles share one process: presence is not ownership

Some launchers keep **more than one game module resident at the same time**. Halo's Master Chief
Collection does exactly this — Halo 3, ODST and Reach DLLs can all be loaded while you sit in the
frontend — and it breaks the assumption every injector makes, that "the module is present" means "that
game is running."

Their resolution rule is the transferable part:

> Module presence now means only **available**. A title is the runtime owner only when its currently
> installed, non-teardown lifecycle generation publishes the **one unique fresh camera heartbeat**. Zero
> or multiple qualifying titles expose **no owner** and no runtime capabilities.

Three properties worth copying:

- **Ownership is proven by a live signal**, not by presence — the same argument as
  [06](06-debugging-methodology.md)'s "presence is not proof of loading", raised from "is my hook
  installed" to "which game am I even in".
- **The heartbeat is tagged with a lifecycle generation**, so a stale signal from a title that has since
  torn down cannot win.
- **Ambiguity resolves to *no owner*, not to a guess.** Two qualifying titles is a bug, and picking one
  would produce a mod driving the wrong game's camera.

### But "no owner" is not "suppress everything"

The failure that followed is the more instructive half. Their resolver correctly reported zero owner in a
multi-resident frontend state — and **the controller call site treated that as a reason to suppress
title-independent input**, so ordinary VR pad input died after Save & Quit.

> The failure did not invalidate generation-tagged ownership. The resolver correctly returned zero owner
> … the controller admission call site incorrectly treated that as a reason to suppress
> title-independent frontend input.

**Separate "which title owns the camera" from "may this capability run at all."** Menu navigation,
controller transport and overlay input are title-independent and must survive the no-owner state.
Capability gating and ownership resolution are two questions, and answering the second correctly does
not license answering the first the same way.

### Deferred and immediate D3D11 contexts have DIFFERENT vtables {#deferred-context-vtable}

A silent-failure family worth knowing before you write the hook, not after. `[LIVE]`

Measured on one target: immediate context `0x1f66e723010`, deferred `0x1f66ea97b60`. **Different
objects, different vtables.** So a probe that reads `ID3D11DeviceContext`'s vtable from a throwaway
device and hooks only the **immediate** context will install cleanly, report success, and **intercept
nothing** in a game that renders through deferred contexts - with no error anywhere. (Sims 4 is such a
game; it is why RenderDoc needs `--opt-capture-all-cmd-lists` there.)

Two traps in the same family:

- **Hook both.** Create a deferred context from the throwaway device and hook that vtable too.
- **The throwaway device must be `D3D_DRIVER_TYPE_HARDWARE`.** A WARP or reference device can be a
  different implementation with a **third** vtable, failing in exactly the same silent way.

**Both failures are silent, so a selftest that proves interception fires is mandatory** - hook something
harmless like `ClearRenderTargetView` against your own D3D11 client and require a **non-zero hit count**
before believing the install. This is
[an instrument that must prove it can see the fault](06-debugging-methodology.md#self-proving-instrument)
applied to the hook itself.

### Never log from a static initialiser {#no-log-in-static-init}

A one-line rule that cost a shipped project a patch of its own (`M4.5: never log from a static
initialiser`). `[SOURCE]`

A proxy DLL's statics run during `DllMain`-time loader work, **before** your logger's own statics are
guaranteed constructed and while the loader lock is held. Logging there is the classic static
initialisation-order failure wearing a diagnostic's clothes: it crashes on load, it crashes *before*
anything you would want to read, and the crash names your logger rather than the initialiser that called
it.

Initialise diagnostics from an explicit entry point that runs after load - a first-frame hook, or the
first intercepted call - and let statics be data only. This is the
[DllMain constraint](#dllmain-detach) from the other direction: not "what may I call at detach", but
"what has been constructed yet at attach".

### Module presence means AVAILABLE, never OWNER {#module-presence-is-not-ownership}

The section above is one consequence. This is the rule underneath it, and it is the whole architecture
of a mod living inside a multi-game container. `[SOURCE]`

Halo MCC keeps more than one game DLL **resident at once**, so "which title is running" cannot be
answered by asking which module is loaded:

> A title is the runtime owner only when its currently installed, non-teardown lifecycle generation
> publishes **the one unique fresh camera heartbeat.** Zero or multiple qualifying titles expose **no
> owner and no runtime capabilities.**

**Fail closed on ambiguity** - two candidates is not "pick one", it is "no owner". Four mechanisms make
that decidable:

- **Two independent boundaries, not one.** A *title generation* changes when that title loads, unloads,
  reloads, or is rebound at another base. A separate *epoch* changes whenever any mask or base member of
  the **complete module set** changes. A heartbeat is valid only if it is strictly newer than **both**.
  One counter cannot distinguish "this title reloaded" from "the set around it changed".
- **A bounded pending interval.** On the first transition to a multi-resident set, the already-hooked
  title gets **100 ms, teardown-only**, to publish a post-transition heartbeat. Pending exposes no armed
  state, no heartbeat, no mode and no capabilities; it never installs a hook and never survives multiple
  qualifying owners.
- **Capability masking.** An owner that is not *armed* may publish only what does not require the armed
  camera transaction. Stereo, aim, HUD, arm IK, room scale and haptics stay masked; ordinary controller
  input and mode reporting are **separate capabilities** precisely so a frontend keeps working when no
  title owns anything.
- **Freshness is per-title and asymmetric, and tightens under contention.** Halo 3 uses a strict
  `<500 ms` camera-fresh boundary; ODST keeps `<500 ms` debounce, falls back after `>750 ms`, and
  retains a previously-seen ready camera to `5000 ms`. **Multi-resident ownership clamps both to a strict
  `<100 ms`.**

Their test discipline is the part to copy: the core matrix enumerates **all eight combinations of
active / installed / running**, so a later title cannot silently invert the rule for everyone else.
See [HOOK-005](pattern-catalog.md#hook-005).

### A rearm that runs on the sampling poll erases the evidence it is waiting for

The bug that forced the rule above is worth its own note, because the shape is not specific to titles.
`[SOURCE]`

A level-load gate rearmed itself *whenever the core was uninstalled and the gate had not yet proven
`levelRunning`* - and the worker polled every **50 ms**. So the active title's accumulated frozen and
ticking samples "were erased immediately after each sample". The gate could never open: not on first
entry, not after another title, not after a same-title teardown.

**A condition that resets state must never be evaluated on the same tick that gathers it.** Separate the
two questions explicitly - *is this thing active?* decides whether to accumulate; *has it finished?*
decides whether to rearm - and write the lifecycle as one decision function rather than as a reset
scattered through a poll.

## Don't trust "same path = loaded"

Replacing a script/asset at the path the engine *used* to load doesn't guarantee yours is the
one loaded — load order, package precedence, and save-embedded references can override you.
Prove your code is live with a **load banner** from the script/asset itself, not by assuming.
(*SS2VR/FlatAim: multiple entries on "assumed loaded but wasn't" — mod table order, KPF
presence, save-embedded order.*) The script's own "I loaded, version X" print is the only
proof.

## Execution readiness includes the called subsystem {#subsystem-readiness}

**Symptom:** a verified native console executor calls address zero during startup, yet the same
command works later. The engine object/vtable, renderer or XR session can exist before the subsystem
used by the command. Neither a valid executor address nor a native status reply proves that dependency.

**Cheap discriminant:** capture the null call's return address, follow it to the indirect callback
load, and observe that callback/storage read-only during a clean startup. Compare the identical command
before and after initialization. Gate on the confirmed dependency, behind instruction signatures and
guarded reads. Defer without consuming the command's sequence; distinguish pending from completed
acknowledgments. Do not replace the native call contract or add a fixed startup sleep without evidence.

**SS2VR v3.72, 2026-09-05 (phase 5.6.1):** `ReadConfigFile` was valid while Dark's config hash table
was still zero. Early `set` reached hash lookup `0x8E0890`, loaded `[table+0x18]`, and called null;
return site `0x8E08BA`, table RVA `0x127A150`. It reproduced with XR disabled. A read-only readiness
gate fixed the reproducer in XR-off and xr-sim-on startups, with exact config-value readback and once-only
dispatch. This does not establish readiness for unrelated commands such as save loading.
Evidence: `D:/Dev Debug/ss2vr-work/docs/AGENT_EXECUTOR_RE.md` and `docs/AGENT_HARNESS.md`.

Instrumentation caveat: Frida's exception observer localized the call, but that instrumented early run
exited before the application's normal SEH completion. Validate containment/fixes again without observer
detours. The installed Frida MCP's `execute_in_session` unloads scripts after each short invocation;
use an explicitly retained SDK script for asynchronous observation, and isolated Python mode for helpers.

