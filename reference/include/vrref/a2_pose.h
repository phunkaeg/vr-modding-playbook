// a2_pose.h -- the reference implementations from docs/a2-pose-pipeline.md.
#pragma once

#include <atomic>
#include <cstdint>
#include <optional>

#include "vrmath.h"

namespace vrref {

// --- A2.1 One snapshot per frame --------------------------------------------

// Sampled exactly once per frame, at a known point. Const thereafter.
struct PoseSnapshot {
    uint64_t frameIndex     = 0;
    int64_t  predictedNs    = 0;      // the display time these poses were predicted for
    uint32_t recenterEpoch  = 0;      // see A2.4 -- bumped by ONE recenter event

    Pose  head;                       // in the app/stage space you chose, ONE space, named
    Pose  handGrip [2];               // where the model sits      (chapter 02)
    Pose  handAim  [2];               // where the ray points      -- NOT the same thing
    bool  handValid[2] = {false, false};

    Vec2  stick    [2];
    float trigger  [2] = {0, 0};
    float grip     [2] = {0, 0};
};

// --- A2.2 Publishing it across threads without a lock ------------------------

// Single writer (game thread), many readers (render thread, etc.). No mutex, no torn reads.
class PoseChannel {
    std::atomic<uint32_t> seq_{0};      // even = stable, odd = write in progress
    PoseSnapshot          data_{};      // written only between seq_ bumps

public:
    void Publish(const PoseSnapshot& s) {
        seq_.fetch_add(1, std::memory_order_release);          // -> odd
        data_ = s;
        std::atomic_thread_fence(std::memory_order_release);
        seq_.fetch_add(1, std::memory_order_release);          // -> even
    }

    // false = a write was in flight; caller keeps last good snapshot and tries next frame.
    bool TryRead(PoseSnapshot& out) const {
        const uint32_t before = seq_.load(std::memory_order_acquire);
        if (before & 1u) return false;
        out = data_;
        std::atomic_thread_fence(std::memory_order_acquire);
        return seq_.load(std::memory_order_acquire) == before;
    }
};

// --- A2.3 Latch the pristine value; never derive from live state -------------

// Latch the pristine engine value ONCE per object/session; derive from the latch, never from live state.
class TransformLatch {
    std::optional<Mat4> pristine_;
public:
    void OnAcquire(const Mat4& engineValueBeforeWeTouchedIt) { pristine_ = engineValueBeforeWeTouchedIt; }
    void OnRelease() { pristine_.reset(); }
    bool Held() const { return pristine_.has_value(); }

    // Always base * delta. NEVER read the live transform here -- that is the feedback loop.
    std::optional<Mat4> Compose(const Mat4& delta) const {
        if (!pristine_) return std::nullopt;
        return (*pristine_) * delta;
    }
};

// --- A2.4 Recentre as an epoch, not an event ---------------------------------

class RecenterBus {
    // STARTS AT 1, and that is load-bearing. A lane's `seen_` starts at 0, so epoch 0
    // means "no lane has ever taken a baseline". Start the bus at 0 and the first frame
    // does not rebase, leaving every lane running off a default-constructed pose until
    // the user's first recentre. Caught by RecenterEpochRebasesEveryLaneOnce.
    std::atomic<uint32_t> epoch_{1};
public:
    void Request() { epoch_.fetch_add(1, std::memory_order_release); }   // ONE caller
    uint32_t Epoch() const { return epoch_.load(std::memory_order_acquire); }
};

// Each lane holds its own last-seen epoch and rebases when it changes -- in the SAME frame as the
// others, because they all read the epoch out of the same PoseSnapshot.
class CameraLane {
    uint32_t seen_ = 0;
    Pose     baseline_{};
    uint32_t rebases_ = 0;
public:
    void Update(const PoseSnapshot& s) {
        if (s.recenterEpoch != seen_) { baseline_ = s.head; seen_ = s.recenterEpoch; ++rebases_; }
        /* ... derive from baseline_ ... */
    }
    const Pose& Baseline() const { return baseline_; }
    uint32_t Rebases() const { return rebases_; }
};

// --- A2.5 A neutral pose must settle before it is believed -------------------

// Accept a neutral pose only after N consecutive samples agree. A big jump RESETS the latch
// rather than becoming a permanent offset.
class PoseSettleLatch {
    static constexpr int   kNeeded     = 8;
    static constexpr float kMaxMetres  = 0.25f;
    static constexpr float kMaxRadians = 0.785398f;   // 45 degrees

    int  agreed_ = 0;
    Pose candidate_{};
    std::optional<Pose> settled_;

public:
    // Returns true on the frame the pose becomes settled.
    bool Offer(const Pose& sample) {
        if (agreed_ == 0) { candidate_ = sample; agreed_ = 1; return false; }

        const float dPos = Length(sample.position - candidate_.position);
        // Angle between two orientations, via the quaternion dot product.
        const Quat& a = candidate_.orientation;
        const Quat& b = sample.orientation;
        float d = std::fabs(a.w * b.w + a.x * b.x + a.y * b.y + a.z * b.z);
        if (d > 1.0f) d = 1.0f;
        const float dAng = 2.0f * std::acos(d);

        if (dPos > kMaxMetres || dAng > kMaxRadians) {
            // A big jump is a NEW candidate, not an outlier to average in.
            candidate_ = sample;
            agreed_ = 1;
            settled_.reset();
            return false;
        }

        if (++agreed_ >= kNeeded && !settled_) { settled_ = candidate_; return true; }
        return false;
    }

    bool Settled() const { return settled_.has_value(); }
    const std::optional<Pose>& Value() const { return settled_; }
    void Reset() { agreed_ = 0; settled_.reset(); }
};

}  // namespace vrref
