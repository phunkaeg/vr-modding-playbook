# A4 · Hook Safety — reference code

!!! note "This code is compiled and tested"
    Every function below also lives in the repository's `reference/` directory as real,
    building C++ — `reference/include/vrref/` for the code, `reference/tests/` for the
    tests — and `tools/verify.py` runs them. Until it was compiled this was pseudocode,
    and compiling it found three genuine defects. Read the appendix for the reasoning;
    take the version something has actually executed from `reference/`.

    **Partial by design.** Signature scanning, trampoline disassembly, guarded reads and
    the file/PNG plumbing need a target process and are not covered; the *decision logic*
    they wrap is. `reference/README.md` states the boundary exactly.

Chapter [07](07-engine-integration-safety.md) is the discipline. This is the scaffolding: the guards that
turn a wrong address into a **loud no-op** instead of a wild write, and the instrumentation that tells you
whether a hook is working rather than merely present.

The theme throughout: **fail closed, and say why.** A guard that refuses silently costs you the same
session as no guard at all.

---

## A4.1 Resolve by signature, fail closed, and report the bytes

`signature_mismatch` as a log line is nearly useless — you cannot tell a patched binary from a typo in
your pattern. SOMAVR lost time to exactly this twice, both times a single missing `REX` prefix
([11](11-re-anchoring-and-discovery.md)).

```cpp
struct SigResult {
    uint8_t* addr   = nullptr;
    size_t   hits   = 0;              // 0 and >1 are BOTH failures
    std::string diagnostic;           // filled on failure -- this is the point
};

// `pattern` bytes with `mask`: 'x' = must match, '?' = wildcard.
SigResult ResolveUnique(uint8_t* base, size_t size,
                        const uint8_t* pattern, const char* mask, const char* name) {
    SigResult r;
    const size_t len = strlen(mask);
    uint8_t* first = nullptr;

    for (size_t i = 0; i + len <= size; ++i) {
        bool ok = true;
        for (size_t j = 0; j < len && ok; ++j)
            if (mask[j] == 'x' && base[i + j] != pattern[j]) ok = false;
        if (ok) { if (!first) first = base + i; if (++r.hits > 1) break; }
    }

    if (r.hits == 1) { r.addr = first; return r; }

    // Failure path: say what you expected, what is actually there, and where.
    char buf[512];
    if (r.hits == 0) {
        // Dump the bytes at the address you THOUGHT it was, if you have a prior RVA.
        snprintf(buf, sizeof buf,
                 "%s: 0 matches. Pattern len=%zu. Check for an x64 REX prefix (40-4F) at the head, "
                 "or a rebuilt binary.", name, len);
    } else {
        snprintf(buf, sizeof buf,
                 "%s: %zu matches -- pattern is not unique. Widen it; do NOT take the first hit.",
                 name, r.hits);
    }
    r.diagnostic = buf;
    return r;                          // addr stays null: the lane disables itself
}
```

Two rules encoded above, both from chapter 07:

- **Zero matches and multiple matches are both "disable the lane and log."** Taking the first hit of an
  ambiguous pattern is how you end up hooking a decoy.
- **A strict guard converts a one-byte mistake into a refusal.** SOMAVR's shutdown hook simply never
  installed rather than patching the wrong address — recoverable, diagnosable, and not a memory-corruption
  hunt.

## A4.2 Check you have room before you design the hook

A 5-byte relative `jmp` needs five bytes of prologue to displace. Short virtual thunks do not have them —
SOMAVR's `AddImpulse` wrapper was a **9-byte** thunk (`mov rax,[rcx]; jmp [rax+0x130]`).

```cpp
// Sum instruction lengths until you have at least `needed` bytes, without splitting an instruction.
// Uses whatever length-disassembler you already ship (hde, zydis, ...).
bool HasTrampolineRoom(const uint8_t* fn, size_t needed, size_t* stolenOut) {
    size_t stolen = 0;
    while (stolen < needed) {
        const size_t len = InstructionLength(fn + stolen);
        if (len == 0) return false;                    // undecodable: refuse
        if (IsRelativeBranch(fn + stolen)) return false; // relocating these is its own project
        stolen += len;
    }
    *stolenOut = stolen;
    return true;
}
```

If this returns false, you need a different strategy (guarded INT3-plus-absolute-jump for a one-shot
window, or hook the caller instead) — not a bigger hammer. Checking *before* you write is the difference
between a design decision and corrupting the next function.

## A4.3 The POD-only SEH wrapper

Chapter 07: MSVC **rejects** `__try` in a function requiring C++ object unwinding (error **C2712**). This
is enforced at compile time, and the tempting fix — wrapping a larger, more useful function — is the one
that will not build.

```cpp
// The guarded helper is POD-only: raw pointers and scalars in, a status code out, nothing else.
// No logging, no std::string, no containers, no destructors -- anywhere in this function.
enum class ReadStatus : int { Ok = 0, Faulted = 1, NullPtr = 2, NotFinite = 3 };

ReadStatus SehReadFloat3(const void* src, float out[3]) noexcept {
    if (!src) return ReadStatus::NullPtr;
    __try {
        const float* p = static_cast<const float*>(src);
        out[0] = p[0]; out[1] = p[1]; out[2] = p[2];
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return ReadStatus::Faulted;
    }
    // Finiteness is a separate check: "unavailable" must never be delivered as zero.
    for (int i = 0; i < 3; ++i)
        if (!std::isfinite(out[i])) return ReadStatus::NotFinite;
    return ReadStatus::Ok;
}

// The caller is ordinary C++ and does the logging, formatting and policy.
std::optional<Vec3> ReadPositionSafe(const void* src) {
    float v[3]{};
    const ReadStatus s = SehReadFloat3(src, v);
    if (s != ReadStatus::Ok) { LogOnce("position read failed: %d", (int)s); return std::nullopt; }
    return Vec3{ v[0], v[1], v[2] };
}
```

**`std::optional` rather than a sentinel** is the fail-closed half: a fail-open default of `0` drives the
game with bogus input, which is worse than not driving it at all.

## A4.4 Thread-local reentrancy guard — "this call is mine"

BioshockVR spent **six build cycles** chasing what looked like a runtime bug before finding its own
OpenXR eye-blit was calling the same globally detoured D3D11 methods as the game.

```cpp
// One flag per thread. Set it around ALL of your own API work.
inline thread_local int g_internalDepth = 0;

struct InternalCallScope {
    InternalCallScope()  { ++g_internalDepth; }
    ~InternalCallScope() { --g_internalDepth; }
};
inline bool CallIsOurs() { return g_internalDepth > 0; }

// Every detour reachable from your own code checks it FIRST and calls the original directly.
HRESULT STDMETHODCALLTYPE Hook_Present(IDXGISwapChain* sc, UINT si, UINT f) {
    if (CallIsOurs()) return g_originalPresent(sc, si, f);   // no classification, no telemetry
    /* ... the real hook body: this call came from the game ... */
    return g_originalPresent(sc, si, f);
}

void SubmitEyeImages() {
    InternalCallScope guard;      // everything below is ours, at any depth
    BlitToSwapchain();            // even if this re-enters Present, the guard holds
    xrEndFrame(...);
}
```

**It must be a counter, not a bool** — your own code nests, and a bool gets cleared by the inner scope
while the outer one is still running. Reentrancy applies identically to D3D9/10/11/12, OpenGL and Vulkan
layers.

## A4.5 Prove the hook ran before debugging its logic

Chapter 06: *"Called 0 times" and "called but wrong" are completely different investigations, and telling
them apart costs one log line.*

```cpp
struct HookStats {
    std::atomic<uint64_t> entered{0};     // the hook body ran
    std::atomic<uint64_t> attempted{0};   // we tried to do the thing
    std::atomic<uint64_t> applied{0};     // the thing actually happened
    std::atomic<uint64_t> skipped{0};     // and why -- keep a per-reason array in real code
};

// Emit ALL of these in the frame summary, every time. `applied/attempted` is the ratio that
// distinguishes "working" from "silently bypassed" (chapter 06).
void LogHookSummary(const char* name, const HookStats& s) {
    LogWarn("%s entered=%llu attempted=%llu applied=%llu skipped=%llu",
            name, s.entered.load(), s.attempted.load(), s.applied.load(), s.skipped.load());
}
```

**Counters must not share the log budget** ([06](06-debugging-methodology.md)) — BioshockVR had 23
`pose_not_ready` skip lines consume a shared budget, producing **zero** `applied` lines while counters
proved 109 applies had happened.

## A4.6 A guard's evidence is trigger opportunities, not uptime

The newest addition to chapter 06, from BioshockVR's motion-comp saga: **a quiet run does not prove a
guard works if the thing it guards against never fired.** Their crash appeared at frame 1 in one dump and
frame 35 in another, driven by focus changes and sleep/wake.

```cpp
// Count the OPPORTUNITIES, not the minutes. Without these, "the guard works" and
// "the trigger never happened" produce identical logs.
struct TriggerCensus {
    std::atomic<uint32_t> focusEvents{0};
    std::atomic<uint32_t> referenceSpaceChanges{0};
    std::atomic<uint32_t> sessionStateTransitions{0};
    std::atomic<uint32_t> deviceLostEvents{0};
};

void LogSurvivalEvidence(const TriggerCensus& t, double uptimeSeconds) {
    LogWarn("survived: focus=%u refSpace=%u sessionState=%u deviceLost=%u over %.0fs",
            t.focusEvents.load(), t.referenceSpaceChanges.load(),
            t.sessionStateTransitions.load(), t.deviceLostEvents.load(), uptimeSeconds);
}
```

## A4.7 Census what is in front of you, and log all of it

Also new to chapter 07: BioshockVR's containment fail-closes on one named layer, so any *future* implicit
layer reproduces the same crash signature with nothing in the log to distinguish it.

```cpp
// Blocklist only what you have PROVEN. Log everything you find -- visibility is free,
// exclusion is a policy decision that needs evidence.
void CensusImplicitLayers() {
    for (const LayerInfo& l : EnumerateOpenXrImplicitLayers()) {   // registry manifests
        const bool blocked = kProvenBadLayers.count(l.name) > 0;
        LogWarn("xr-layer %s v%s %s%s", l.name.c_str(), l.version.c_str(),
                l.enabled ? "enabled" : "disabled", blocked ? " [EXCLUDED by us]" : "");
    }
    for (const ModuleInfo& m : EnumerateLoadedModules())           // overlays, shims, DRM
        if (IsInterestingModule(m)) LogWarn("module %s v%s @ %p", m.name, m.version, m.base);
}
```

Pair it with the **environment fingerprint** from chapter 06 — the XR runtime's name *and file version* in
the same header block as your build banner. Both of BioshockVR's crash triggers lived outside the repo.

## A4.8 Patch a branch only with full ceremony

```cpp
// Verify the EXACT original bytes before writing. On any mismatch: log and leave stock behaviour
// completely untouched. (HaloVR: verified 74 05 before writing EB 18.)
bool PatchBranch(uint8_t* at, const uint8_t* expect, const uint8_t* replace, size_t n) {
    if (memcmp(at, expect, n) != 0) {
        LogWarn("branch patch refused at %p: bytes differ from expected", at);
        return false;                                   // stock behaviour preserved
    }
    DWORD old;
    if (!VirtualProtect(at, n, PAGE_EXECUTE_READWRITE, &old)) return false;
    memcpy(at, replace, n);
    VirtualProtect(at, n, old, &old);
    FlushInstructionCache(GetCurrentProcess(), at, n);
    return true;
}
```

## A4.9 Record base + RVA together, always

An RVA against a relocated module is meaningless on its own — and FarCry2-VR found its game DLLs collide
at their preferred base and get relocated.

```cpp
struct Anchor {
    const char* module;      // "Dunia.dll"
    uintptr_t   rva;         // what you write in the docs
    uintptr_t   liveBase;    // what it actually loaded at THIS run
    uintptr_t   Resolve() const { return liveBase + rva; }
};

void LogAnchor(const Anchor& a) {
    LogWarn("anchor %s+0x%zX base=0x%zX -> 0x%zX", a.module, a.rva, a.liveBase, a.Resolve());
}
```

---

**Related prose:** [07 · Hooking & native-call discipline](07-engine-integration-safety.md) ·
[07 · Module lifecycle](07-engine-integration-safety.md) ·
[06 · A hook that "does nothing" may simply never be reached](06-debugging-methodology.md) ·
[11 · Prologue scans lie in four specific ways](11-re-anchoring-and-discovery.md)
