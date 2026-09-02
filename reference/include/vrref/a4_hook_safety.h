// a4_hook_safety.h -- the testable subset of docs/a4-hook-safety.md.
//
// SCOPE, stated honestly. Most of A4 is process work that cannot be unit-tested without a
// target process: signature scanning, trampoline length disassembly, SEH-guarded reads,
// VirtualProtect. What IS testable is the *decision logic* those wrap, and that is the part
// that has actually gone wrong in this survey:
//
//   * verify-then-write, and refusing on any mismatch          (PatchBranch)
//   * the re-entrancy depth guard                              (InternalScope)
//   * the counters that distinguish "guard worked" from
//     "trigger never fired"                                    (HookStats, TriggerCensus)
//   * module-relative anchors resolved against a live base     (Anchor)
//
// The memory-protection call is factored out behind `ProtectFn` so the logic is testable on
// an ordinary array and the real call site stays one line.
#pragma once

#include <atomic>
#include <cstdint>
#include <cstring>

namespace vrref {

// --- A4.5 Count what you guarded, and what you never saw ---------------------

struct HookStats {
    std::atomic<uint64_t> entered{0};     // the hook body ran
    std::atomic<uint64_t> attempted{0};   // we tried to do the thing
    std::atomic<uint64_t> applied{0};     // the thing actually happened
    std::atomic<uint64_t> skipped{0};     // and why -- keep a per-reason array in real code
};

// Count the OPPORTUNITIES, not the minutes. Without these, "the guard works" and
// "the trigger never happened" produce identical logs.
struct TriggerCensus {
    std::atomic<uint32_t> focusEvents{0};
    std::atomic<uint32_t> referenceSpaceChanges{0};
    std::atomic<uint32_t> sessionStateTransitions{0};
    std::atomic<uint32_t> deviceLostEvents{0};
};

// A census that is all zeroes is not evidence of survival - it is evidence that nothing was
// tested. This is the predicate the frame summary should carry, not a human reading the log.
inline bool CensusExercised(const TriggerCensus& t) {
    return t.focusEvents.load() || t.referenceSpaceChanges.load()
        || t.sessionStateTransitions.load() || t.deviceLostEvents.load();
}

// --- A4.4 One flag per thread, set around ALL of your own API work -----------

inline thread_local int g_internalDepth = 0;

struct InternalScope {
    InternalScope() { ++g_internalDepth; }
    ~InternalScope() { --g_internalDepth; }
    InternalScope(const InternalScope&) = delete;
    InternalScope& operator=(const InternalScope&) = delete;
};

inline bool IsReentrant() { return g_internalDepth > 0; }

// --- A4.8 Verify the EXACT original bytes before writing ---------------------

// Return codes, so a test can distinguish "refused" from "could not unprotect".
enum class PatchResult : int { Applied = 0, RefusedBytesDiffer = 1, ProtectFailed = 2 };

// In the mod this is VirtualProtect + FlushInstructionCache. Injected so the decision
// logic above it can be tested on an ordinary array.
using ProtectFn = bool (*)(void* at, size_t n, bool makeWritable);

inline bool NoProtect(void*, size_t, bool) { return true; }

// Verify the EXACT original bytes before writing. On any mismatch: leave stock behaviour
// completely untouched. (HaloVR: verified 74 05 before writing EB 18.)
inline PatchResult PatchBranch(uint8_t* at, const uint8_t* expect, const uint8_t* replace,
                               size_t n, ProtectFn protect = &NoProtect) {
    if (std::memcmp(at, expect, n) != 0)
        return PatchResult::RefusedBytesDiffer;      // stock behaviour preserved

    if (!protect(at, n, true)) return PatchResult::ProtectFailed;
    std::memcpy(at, replace, n);
    protect(at, n, false);
    return PatchResult::Applied;
}

// --- A4.9 Anchors are module-relative, resolved against the live base --------

struct Anchor {
    const char* module = nullptr;   // "Dunia.dll"
    uintptr_t   rva = 0;            // what you write in the docs
    uintptr_t   liveBase = 0;       // what it actually loaded at THIS run
    uintptr_t   Resolve() const { return liveBase + rva; }
};

}  // namespace vrref
