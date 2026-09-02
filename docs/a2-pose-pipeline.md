# A2 · Motion Controls & the Pose Pipeline — reference code

!!! note "This code is compiled and tested"
    Every function below also lives in the repository's `reference/` directory as real,
    building C++ — `reference/include/vrref/` for the code, `reference/tests/` for the
    tests — and `tools/verify.py` runs them. Until it was compiled this was pseudocode,
    and compiling it found three genuine defects. Read the appendix for the reasoning;
    take the version something has actually executed from `reference/`.

    **Correction found by that first compile:** `RecenterBus`'s epoch now starts at **1**,
    not 0. A lane's `seen_` starts at 0, so with the bus also at 0 the first frame never
    rebased and every lane ran off a default-constructed pose until the user's first
    recentre. See `RecenterEpochRebasesEveryLaneOnce`.

The path from "the runtime gave me a pose" to "the game moved" is where most VR mods accumulate their
worst bugs — not because any one step is hard, but because the steps are owned by different threads, in
different frames, in different spaces, and each consumer quietly assumes something the others don't
guarantee.

This page is the skeleton that avoids that. Prose lives in [01](01-camera-and-tracking.md),
[02](02-viewmodels-and-hands.md) and [03](03-input-and-locomotion.md).

---

## A2.1 One snapshot per frame, many narrow consumers

The single most reusable pattern in the surveyed shipped mods. **Sample every pose once, into one
immutable struct, and hand narrow views of it to consumers** — instead of letting the viewmodel code, the
aim code, the UI ray and the locomotion code each poll the runtime whenever they feel like it.

Independent consumers polling independently is how you get the hands and the camera at different zeros,
and it is *invisible* until something disagrees.

```cpp
// Sampled exactly once per frame, at a known point. Const thereafter.
struct PoseSnapshot {
    uint64_t frameIndex     = 0;
    int64_t  predictedNs    = 0;      // the display time these poses were predicted for
    uint32_t recenterEpoch  = 0;      // see A2.4 -- bumped by ONE recenter event

    Pose  head;                       // in the app/stage space you chose, ONE space, named
    Pose  handGrip [2];               // where the model sits      (chapter 02)
    Pose  handAim  [2];               // where the ray points      -- NOT the same thing
    bool  handValid[2] = {false,false};

    Vec2  stick    [2];
    float trigger  [2];
    float grip     [2];
};
```

Two things earn their place here:

- **`handGrip` and `handAim` are separate fields, always.** On Touch controllers they differ by tens of
  degrees. One pose used for both is the "weapon points where the model isn't" bug, and it is
  unfixable by trimming because the two are genuinely different poses ([02](02-viewmodels-and-hands.md)).
- **`predictedNs` travels with the poses.** A consumer that re-predicts, or uses a pose from a different
  display time, silently reintroduces the latency you removed.

## A2.2 Handing it across a thread boundary — seqlock, not a bool

DishonoredVR's original handoff was `exchange(false)` → write six atomics → re-enable. A reader arriving
mid-write sees a **torn mix of two generations**, each field individually valid. That is the bug the
sequence counter exists to prevent.

```cpp
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
```

**The reader must have a fallback.** `TryRead` returning false is normal, not exceptional — hold the last
good snapshot rather than rendering a zeroed pose.

**Verify this with an adversarial stress test, not code review.** Code review cannot find torn reads and
cannot prove their absence. DishonoredVR's validation was **200,000 alternating writes against concurrent
snapshots, zero mixed-generation reads, in both Debug and Release.** That is the shape to copy.

```cpp
void TestNoTornReads() {
    PoseChannel ch; std::atomic<bool> stop{false}; std::atomic<int> bad{0};
    std::thread w([&]{
        for (int i = 0; i < 200000; ++i) {
            PoseSnapshot s{}; s.frameIndex = i;
            const float v = (i & 1) ? 1.0f : -1.0f;           // two distinct generations
            s.head.position = {v,v,v};
            s.handGrip[0].position = {v,v,v};
            s.handAim[0].position  = {v,v,v};
            ch.Publish(s);
        }
        stop = true;
    });
    std::thread r([&]{
        PoseSnapshot s{};
        while (!stop) if (ch.TryRead(s)) {
            const float v = s.head.position.x;                // every field must agree
            if (s.handGrip[0].position.x != v || s.handAim[0].position.x != v) ++bad;
        }
    });
    w.join(); r.join();
    CHECK(bad == 0);
}
```

## A2.3 Don't read your own output back as input

Chapter [07](07-engine-integration-safety.md): SOMAVR hit this three times under three names, with a
distance growing `0.4272 → 1.4772` because each frame multiplied an already-modified matrix again.

```cpp
// Latch the pristine engine value ONCE per object/session; derive from the latch, never from live state.
class TransformLatch {
    std::optional<Mat4> pristine_;
public:
    void OnAcquire(const Mat4& engineValueBeforeWeTouchedIt) { pristine_ = engineValueBeforeWeTouchedIt; }
    void OnRelease() { pristine_.reset(); }

    // Always base * delta. NEVER read the live transform here -- that is the feedback loop.
    std::optional<Mat4> Compose(const Mat4& delta) const {
        if (!pristine_) return std::nullopt;
        return (*pristine_) * delta;
    }
};
```

**The tell is a quantity that drifts monotonically while every individual step looks correct.** If you
see that, look for a hook that both writes a value and later reads "the current value."

## A2.4 Recenter: one event, one epoch, every lane

Chapter [01](01-camera-and-tracking.md): BioshockVR had three independent recenter detectors and they
latched on different frames. The fix is a **monotonic epoch** that every consumer keys off.

```cpp
class RecenterBus {
    std::atomic<uint32_t> epoch_{0};
public:
    void Request() { epoch_.fetch_add(1, std::memory_order_release); }   // ONE caller
    uint32_t Epoch() const { return epoch_.load(std::memory_order_acquire); }
};

// Each lane holds its own last-seen epoch and rebases when it changes -- in the SAME frame as the others,
// because they all read the epoch out of the same PoseSnapshot.
class CameraLane {
    uint32_t seen_ = 0;
    Pose     baseline_{};
public:
    void Update(const PoseSnapshot& s) {
        if (s.recenterEpoch != seen_) { baseline_ = s.head; seen_ = s.recenterEpoch; }
        /* ... derive from baseline_ ... */
    }
};
```

## A2.5 Don't trust the first pose out of a fresh reference space

SOMAVR calibrated at head `Y = -1.244683`; the next frame settled near `+0.543`. That spurious **1.79 m**
jump put the camera through the roof and read convincingly as a world-scale bug.

```cpp
// Accept a neutral pose only after N consecutive samples agree. A big jump RESETS the latch
// rather than becoming a permanent offset.
class PoseSettleLatch {
    static constexpr int   kNeeded    = 8;
    static constexpr float kMaxMetres = 0.25f;
    static constexpr float kMaxRadians = 0.785398f;   // 45 degrees

    int  stable_ = 0;
    Pose last_{};
    bool have_ = false;

public:
    // Returns true on the frame the pose is accepted.
    bool Feed(const Pose& p, bool positionTracked, bool orientationTracked) {
        if (!positionTracked || !orientationTracked) { stable_ = 0; have_ = false; return false; }
        if (have_ &&
            Distance(p.position, last_.position) < kMaxMetres &&
            AngleBetween(p.orientation, last_.orientation) < kMaxRadians) {
            if (++stable_ >= kNeeded) { stable_ = 0; return true; }
        } else {
            stable_ = 0;                      // the jump resets progress; it does not get baked in
        }
        last_ = p; have_ = true;
        return false;
    }
};
```

**Applies at startup *and* at every recenter**, because a recenter creates the same discontinuity. Note
the guard requires *both* tracked bits — "valid" is not "settled."

## A2.6 Arbitration: pick the simplest thing that works

Seven shipped mods, and only the generic injector needed a recency window
([03](03-input-and-locomotion.md)). Prefer, in order:

```cpp
// 1. ELIMINATE -- BendyVR hard-zeroes the mouse axes. Simplest, and it shipped.
// 2. DEVICE LAYER -- RoR2 registers as a real device and inherits the engine's own arbitration.
// 3. ADDITIVE SATURATION -- GTFO/JKXR sum onto the engine's own value and clamp once.
float MergeAxis(float engineValue, float vrValue) {
    return std::clamp(engineValue + vrValue, -1.0f, 1.0f);
}

// 4. RECENCY WINDOW -- only when you cannot control or predict the other source.
class RecencyArbiter {
    static constexpr double kHoldSeconds = 0.25;
    double lastPhysical_ = -1e9;
public:
    void NotePhysicalActivity(double now) { lastPhysical_ = now; }
    bool PhysicalOwns(double now) const { return (now - lastPhysical_) < kHoldSeconds; }
};
```

**Summing is only the double-driving trap when the two sources can disagree about the same intent.** Where
one is provably idle, or the semantics saturate cleanly, it is the cheapest correct answer — which is why
two shipped mods use it.

## A2.7 Synthetic device presence is a latch, not a poll

If you advertise a virtual controller, its *presence* is an input signal in its own right. Answering
"truthfully" per-poll from noisy state makes the engine flap the device connected/disconnected.

```cpp
class SyntheticPresence {
    bool everActivated_ = false;
public:
    void OnFirstDeliberateActivation() { everActivated_ = true; }   // edge, not level
    // Stable for the whole process lifetime once true. Release BUTTONS through tracking gaps,
    // never the connection.
    bool IsConnected() const { return everActivated_; }
};
```

---

**Related prose:** [01 · Recenter & horizon](01-camera-and-tracking.md) ·
[02 · Grip pose places the model; aim pose points the ray](02-viewmodels-and-hands.md) ·
[03 · The input ladder](03-input-and-locomotion.md) ·
[07 · A boolean gate around several atomics is not a safe handoff](07-engine-integration-safety.md)
