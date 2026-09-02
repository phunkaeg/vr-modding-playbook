# Brief — SS2VR: harness, runtime-tooling and stereo findings not yet in the playbook

**From:** ss2vr-work (System Shock 2 Remastered, KEX, D3D11 + OpenXR, injected DLL)
**Date:** 2026-09-02
**Source sessions:** v3.64–v3.67, first live agent-harness run, xr-sim + xr-tape integration, and a
cross-read of SOMAVR's `NATIVE_STEREO_FEASIBILITY.md` / `CRASH_F10_DUAL_RENDER_2026-09-01.md` /
`XRSIM_INTEGRATION_ASSESSMENT.md`.

Ten findings, ordered by how much time they save someone who does not already know them. Each names a
suggested destination. **Items 7–10 originate wholly or partly with SOMAVR** and are included because a
second independent confirmation is exactly what promotes a project note to a playbook rule — attribution
is marked inline.

Confidence is stated per item. Where something is inference rather than measurement, it says so.

---

## 1. A BOM in an OpenXR manifest reports itself as `XR_ERROR_API_LAYER_NOT_PRESENT` (−36)

**Suggested destination:** `symptom-index.md` and `failure-atlas.md` — this is a wrong-error-code
mistranslation, the class that costs hours.

**Symptom.** `xrCreateInstance` returns **−36 (`XR_ERROR_API_LAYER_NOT_PRESENT`)** for a layer that is
present, correctly installed, and named correctly in `XR_ENABLE_API_LAYERS`. Or a runtime selected by
`XR_RUNTIME_JSON` is silently ignored.

**Cause.** The manifest JSON has a UTF-8 BOM. The OpenXR loader's parser fails at *"Line 1, Column 1"*
and reports the resulting absence as "layer not present". Windows PowerShell 5.1's
`Set-Content -Encoding UTF8` **writes a BOM**; pwsh 7 does not — so the same installer script works on
one machine and fails on another, which makes it look environmental.

**Fix.** `[System.IO.File]::WriteAllText($path, $json, [Text.UTF8Encoding]::new($false))`, or
`ConvertTo-Json` piped to that. Never `Set-Content -Encoding UTF8` for a manifest.

**Confidence: measured, three separate instances in one day** — our xr-sim runtime manifest, a
hand-written one, and xr-tape's `Install-XrTape.ps1` (reported upstream; its manifest is written with
`Set-Content -Encoding UTF8` and is BOM'd today). xr-sim's `install-runtime.ps1` already does it
correctly and is a good reference.

**Rule of thumb worth printing:** *"the loader ignored my layer/runtime" is a JSON-parse failure until
proven otherwise, and the first three bytes are the first place to look.*

---

## 2. A crash and a clean exit are indistinguishable from outside — read the ENGINE's log

**Suggested destination:** `06-debugging-methodology.md`.

**What happened.** Our game vanished ~6 s after launch, twice, with no crash dump. Configuration under
test was a simulated OpenXR runtime plus a recorder layer, so it read as *"the simulated runtime kills
the game"* and an afternoon went to the wrong tool.

`kexengine.log` — **the engine's own log, which this project had never read in months of work** — showed
the complete orderly shutdown sequence (job system → audio → renderer → filesystem → cvars → Steam →
SDL) and no fault of any kind. That is the normal quit path. The game had been *asked* to leave. One
line exonerated both tools and turned the search back on our own code, where the bug was.

**The general rule.** VR-mod authors instrument their own DLL and then read only that log. Every engine
writes its own, usually beside the saves or config (`kexengine.log`, `stdout.txt`, `consoleHistory.txt`
for KEX). When a process disappears, **the engine's log is the only thing that distinguishes "crashed"
from "was asked to quit"**, and no amount of mod-side instrumentation can supply it — a mod cannot log
its own absence.

**Two corollaries:**
- The **absence** of a crash dump is evidence, not missing evidence.
- A log file held open is a free liveness check (`tail` returning "device or resource busy" = alive).

**Confidence: measured.**

---

## 3. File-mailbox control channels re-execute the previous session's command

**Suggested destination:** `pattern-catalog.md` as a new entry (PACK/CFG family), referenced from
`07-engine-integration-safety.md`.

**Problem.** A driver and an injected DLL rendezvous through a command file. The DLL de-duplicates with
a last-sequence-number held **in memory**. That state resets on process start; the file persists on
disk. So a fresh launch reads the **previous session's** command file, finds a sequence number it has
never seen, and executes it.

Ours contained `quit`. The game closed itself ~6 s into every launch, which is finding 2's symptom.

**Recipe.** Stamp the bridge's start time when it initialises and refuse any command file older than
that, logging what was ignored. A file written before the bridge existed cannot have been addressed to
it. This needs no state file and cannot drift the way a persisted sequence number would.

**Trip hazard.** The severity depends on the payload. A stale *pose* is a confusing test; a stale
*console command* is an arbitrary action, and `quit` / `map` / `load` are all one keystroke away in any
automation transcript.

**Meta-finding, and the reason this brief exists.** xr-sim's own installer clears stale control files
**for exactly this reason**, and the SS2VR author ported that comment verbatim into our repo *the same
morning* — "a leftover command.txt would be re-applied the moment a session starts" — without asking
whether our own mailbox had the same hole. It did. **Reading a warning is not applying it**; a warning
about tool A's control file needs an explicit check of every other control file in the system.

**Confidence: measured, root cause confirmed, fix built (v3.67); the refusal path itself has not yet
been observed firing, so the fix is "built and plausible", not "verified".**

---

## 4. A self-test that only talks to itself cannot detect a contract disagreement

**Suggested destination:** `06-debugging-methodology.md`, next to the harness material.

Our agent harness passed every static check for six days while the **driver wrote commands to one
directory and the DLL polled another**. The driver assumed the log lived beside the saves; the DLL used
its compiled-in work root. Commands were written that nobody read; a folder was polled that nobody
wrote.

Every check passed because **every check inspected files the driver had created, in the driver's own
directory.** The self-test never made the other side state its path.

**The rule.** Where two components rendezvous at a path (or a port, or a key name), the rendezvous is a
**contract**, and a test that does not make *both sides declare it independently* is not testing the
contract at all. Our fix parses the DLL's own logged directory out of its startup line and FAILs on
mismatch.

**Note the shape recurs.** It is the same shape as an unknown-config-key warning: one side says a name
the other does not recognise, and nothing fails loudly.

**Confidence: measured.**

---

## 5. A console command that is safe at runtime can be fatal from the startup config

**Suggested destination:** `07-engine-integration-safety.md`.

Startup config files typically `exec` arbitrary console commands — not just `set`/`seta`. That is
exactly what makes them attractive for boot automation ("launch straight into a save").

**But the subsystems a command touches may not be constructed yet, and engines rarely null-check that
path.** KEX's `quickload` handler leaves its save-file handle NULL when the save subsystem does not yet
exist and virtual-calls it anyway:

```c
plVar2 = NULL;
if (saveSubsystem != NULL && lookup(saveSubsystem, quicksaveName, &out) == 0)
    plVar2 = out;                       // only assigned on success
(**(code **)(*plVar2 + 0x20))(plVar2);  // no null check -> access violation
```

Immediate crash, every launch. Safe from the console after boot; fatal at cfg-exec time.

**Guidance.** Drive boot automation *after* the game is up, through whatever command channel exists.
Reserve the startup config for commands that only touch already-initialised state (`bind`, `seta`,
`unbindall`). If a boot-command feature exists, have it **refuse** the known-unsafe verbs by name rather
than documenting the hazard — documentation did not prevent this one.

**Confidence: measured (live crash, dump, and the decompiled handler).**

---

## 6. Porting an OpenXR runtime or layer between x86 and x64 is not a rename

**Suggested destination:** `10-graphics-apis.md`, or wherever fleet tooling portability lives.

`XR_DEFINE_HANDLE` is **width-dependent**: on 64-bit it makes every handle an opaque *pointer* type; on
32-bit a plain `uint64_t`. Simulated runtimes typically pack type/index/generation into the handle bits,
so x86 code mixes handles and integers freely — and **does not compile at all** on x64.

The clean bridge keeps every call site unchanged:

```cpp
template <typename H> inline uint64_t handle_bits(H h) { return (uint64_t)(uintptr_t)h; }
inline uint64_t handle_bits(uint64_t v) { return v; }          // exact match beats the template
template <typename H> inline H from_bits(uint64_t v) { return (H)(uintptr_t)v; }
```

**Two adjacent SDK traps found the same day:**
- OpenXR **1.0.x SDKs predate `openxr/openxr_loader_negotiation.h`** (split out in 1.1). If your loader
  is 1.0.x, vendor just that header rather than moving the whole SDK — the negotiation ABI is frozen at
  `XR_LOADER_VERSION_1_0`, and the runtime must otherwise stay on the loader's header version.
- 1.1 spellings do not exist in 1.0.9: `XR_API_VERSION_1_0` → `XR_CURRENT_API_VERSION`.

**Confidence: measured** (done by hand before the standalone xr-sim matured and made it unnecessary —
which is itself the lesson: check whether a fleet tool already solved it before porting a copy).

---

## 7. Native stereo — a SECOND engine confirms the camera-as-parameter precondition

**Suggested destination:** the native-stereo material (`17-teardown-fc2vr-native-stereo.md`,
`18-beyond-the-native-injector.md`). **Origin: SOMAVR**, corroborated here.

SOMAVR's `NATIVE_STEREO_FEASIBILITY.md` draws the deciding structural distinction:

> Does the camera reach the renderer as a **parameter**, or as a mutated **global**?

- HPL3: `mpCurrentFrustum = apFrustum` at the top of every render call → parameter.
- **KEX: the same.** `Kex_RenderCamera_WorldRender` @ `0x45C470` takes the camera as a **stack-local
  parameter**, which is why our own static gate found no save/restore obligation.

Two unrelated engines, same test, same answer. The consequence SOMAVR draws is the transferable part:
FarCry2-VR's entire shipped defect family — exact post-rebuild camera restore, PRIMARY baseline freeze,
pose-space validators, last-pair hold — exists because that project *mutates shared camera state and
must then police every observer of it*. **Where the camera is an argument, that class is removed rather
than defended against.**

**So the honest case for native stereo is a maintenance case, not a rendering-quality case.** SOMAVR
paid for that defect family twice in one week (F-19, F-20); SS2VR paid for the same family in v3.61.

**Two framings the playbook should explicitly warn against**, both SOMAVR's, both endorsed here:

1. *"Native stereo is more VR."* **False.** It is pure **rung** movement (how the second eye is
   produced) and moves the **completeness tier** not at all — no hands, interaction, comfort or HUD work
   improves. A proposal resting on "more VR" deserves to lose to work that moves the tier.
2. *"It fixes the eye-lag."* **True but backwards as a pitch** — see item 8.

**Confidence: SOMAVR's precondition audit is theirs; the KEX corroboration is measured (Ghidra, and our
own `NATIVE_STEREO_GATE.md` verdict "the static gate does not block"). The frame budget for a second
world render remains unmeasured in BOTH projects — it is the single shared open unknown, and only a
headset can price it.**

---

## 8. The AFR pair slip is a property of the architecture, not a defect in it

**Suggested destination:** `a3-stereo-projection.md` or the stereo-rung material.

Alternate-frame stereo renders one eye per frame, so **the two eyes are always a frame apart**. That is
not a bug in an implementation of AFR; it is what AFR *is*. It presents in a headset as "one eye
lagging".

**The consequence that cost us real work:** a *timing* band-aid cannot fix an *architectural* property.
SS2VR shipped an `auto_resync_on_slip` that re-phased the cadence when it detected a slip. It hitched,
cured nothing, and is now disabled — it was attacking the wrong layer.

**What IS fixable at the AFR layer is the pose declaration, and it is a separate bug** (SOMAVR F-20,
independently learned by BioShock-VR and imported into SS2VR as v3.61 `stale_eye_submit`): a held or
stale eye must be submitted **with the pose its image was rendered at**, not the current pose. A
compositor reprojects by the difference between the declared pose and the display-time pose; declaring
the *current* pose for a stale image zeroes that difference, suppresses reprojection, and makes the
stale image stick to the head. Declaring the *rendered* pose lets timewarp do its job — the image goes
stale but stays world-locked.

Three projects have now hit that one independently, which probably makes it a rule rather than a note.

**Native/synchronised-sequential removes the slip by construction** — both eyes from one pose in one
frame, so there is no pair to slip. That is the accurate way to state the benefit.

**Confidence: measured (ours and SOMAVR's); the F-20 mechanism is measured in SOMAVR and imported in
SS2VR.**

---

## 9. The audio lane classification may already exist as DATA — check before classifying by RE

**Suggested destination:** `20-audio-and-haptics.md`.

Ch.20's four-lane model is validated by a 1999 engine that names the same lanes itself. Dark Engine's
`SchemaPlayParams` **Flags bit table** (`darkengine-main/src/sound/schprop.cpp:52`):

```c
"Retrigger", "Pan position", "Pan Range", "No Repeate", "No Cache", "Stream",
"Play Once", "No Combat", "Net Ambient", "Local Spatial",
"","","","","","",                       // 6 unused bits
"Noise", "Speech", "Ambient", "Music", "MetaUI",
```

| Dark flag | Ch.20 lane |
|---|---|
| `Noise` (+ object/vector-attached) | World spatial |
| `Speech` | Listener-relative — narration |
| `MetaUI` | Listener-relative — UI |
| `Ambient` / `Net Ambient` | Environment/ambience |
| `Music` | Music |

The 2D/3D split is also an **API** split (`psndapi.h:38-42`): `GenerateSoundObj(ObjID …)` and
`GenerateSoundVec(mxs_vector*, …)` are positional; bare `GenerateSound(sampleName, parms)` is not. And
`BOOL IsSoundListener(ObjID)` — **the listener is an object**, not a free transform, which matters
before assuming the lever is purely an audio-API call.

**Guidance to add:** before classifying a game's emitters by reverse engineering, **check whether the
engine's data already carries the classification**. For any remaster or port that reads the original
data files, those lane bits survive into shipped data — so the classification is a data read, not an RE
job. Ch.20's stated risk ("a listener-relative lane accidentally attenuated/panned as world audio")
becomes a named, testable prediction: steer the listener and `Speech`/`MetaUI`/`Music` must not change
level or panning.

**Confidence: the Dark source is measured; that a KEX-style remaster honours each bit identically is
INFERENCE until confirmed against the shipped binary.**

---

## 10. Two instrument-honesty rules, both learned the hard way this week

**Suggested destination:** `06-debugging-methodology.md`. **Origin: SOMAVR**, both endorsed here.

**(a) Know your instrument's flush semantics before inferring from its silence.** SOMAVR corrected the
claim that *"any crashing run produces no trace by construction"* — xr-tape flushes every 256 records,
and their crashed runs had written 2.4 MB. So an **empty** trace does not mean "crashed mid-session"; it
means "died before the first flush", which for an OpenXR recorder means *before instance creation* —
pointing away from the runtime entirely. That reframing is what sent us to the engine log in item 2.

**(b) A green probe is an ENVIRONMENT gate, not a regression gate.** A bare conformance client
(`xr_hello64`, `somavr_xrsim_smoke`) links **none of the mod's own code**. It proves a session can be
created on this machine and nothing whatsoever about the mod's submit path, layer budget or held-pair
logic. Reading it as coverage is the ch.06 trap of announcing an outcome from something adjacent to it.

SOMAVR's recommended alternative is worth codifying because it is cheaper *and* more durable: **lift the
decision logic into pure functions and unit-test it.** Layer-budget/eviction and hold decisions are pure
functions of their inputs; testing them needs no runtime, no headset, and keeps working when the harness
is broken. Reserve the simulated-runtime scenario for what genuinely needs a runtime — session-state
transitions, focus pacing, instance loss, per-eye capture.

---

## Provenance and how to verify

Everything above is written up in the SS2VR repo and can be checked:

| Finding | Where |
|---|---|
| 1, 3, 4, 5 | `ss2vr-work/docs/FAILURE_REGISTRY.md` (2026-08-31 and 2026-09-01 entries) |
| 2, 10b | `ss2vr-work/docs/AGENT_HARNESS.md` |
| 6 | `ss2vr-work/docs/BUILD_HISTORY.md` v3.66 |
| 7, 8 | `ss2vr-work/docs/NATIVE_STEREO_GATE.md` (cross-corroboration section) |
| 9 | `ss2vr-work/docs/AUDIO_OWNERSHIP.md` |
| 7, 8, 10 origins | `SOMAVR/docs/{NATIVE_STEREO_FEASIBILITY,REVIEW_HANDOVER_2026-08-07,XRSIM_INTEGRATION_ASSESSMENT,XRTAPE_FIRST_RUN}.md` |

**One correction to carry back into SS2VR's own record if the playbook disagrees with any of it:** item
3's fix is built but its refusal path has not been observed firing, and item 9 is inference about KEX.
Neither should be written up as settled.
