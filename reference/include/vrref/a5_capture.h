// a5_capture.h -- the testable subset of docs/a5-flat-harness-stats.md.
//
// SCOPE. A5 is mostly harness plumbing: a command file, PNG writing, hotkeys. What is worth
// pinning with tests is the BurstCapture state machine, because it is the part with a real
// invariant - arm once, capture exactly N, self-terminate - and the part whose failure mode
// ("it captured forever and changed the timing I was measuring") is expensive.
//
// The PNG write is injected so the ring logic is testable with no filesystem.
#pragma once

#include <atomic>
#include <cstdint>
#include <cstdio>
#include <string>

#include "vrmath.h"

namespace vrref {

enum class EyeIndex { Left = 0, Right = 1 };

// Ring buffer of N frames, armed on demand, self-terminating. 90 Hz x forever fills a disk in
// minutes AND changes the timing you are measuring -- so this must be armed, not always-on.
template <typename WriteFn>
class BurstCapture {
public:
    static constexpr int kFrames = 12;     // ~6 pairs: enough to see the pattern, not a video

    explicit BurstCapture(WriteFn write) : write_(write) {}

    // Call from ONE place. Mirror the arm to every capture stage.
    void Arm() { armed_.store(true, std::memory_order_release); }

    // Called at your present/submit seam, once per rendered eye.
    void OnFrame(EyeIndex believedEye, uint64_t engineFrameIndex, const Pose& pose) {
        if (armed_.exchange(false, std::memory_order_acq_rel)) {
            remaining_ = kFrames; seq_ = 0; ++burstId_;
        }
        if (remaining_ <= 0) return;

        // Everything you cannot reconstruct later goes in the FILENAME. The directory
        // listing then IS the analysis -- no tooling required to read the pattern.
        char name[256];
        std::snprintf(name, sizeof name,
                      "burst%02d_seq%02d_eye%c_frame%llu_posY%+.4f.png",
                      burstId_, seq_, (believedEye == EyeIndex::Left ? 'L' : 'R'),
                      static_cast<unsigned long long>(engineFrameIndex), pose.position.y);
        write_(name);

        ++seq_; --remaining_;
    }

    int  Remaining() const { return remaining_; }
    int  BurstId() const { return burstId_; }
    bool Capturing() const { return remaining_ > 0; }

private:
    std::atomic<bool> armed_{false};
    int      remaining_ = 0;
    int      seq_       = 0;
    int      burstId_   = 0;
    WriteFn  write_;
};

template <typename WriteFn>
BurstCapture<WriteFn> MakeBurstCapture(WriteFn f) { return BurstCapture<WriteFn>(f); }

}  // namespace vrref
