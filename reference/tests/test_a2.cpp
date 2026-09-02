// test_a2.cpp -- the pose pipeline: the seqlock, the latch, the epoch, the settle.
#include <thread>

#include "check.h"
#include "vrref/a2_pose.h"

using namespace vrref;

// A2.2's own test, verbatim in intent: two distinct generations of data, and every
// field of a successfully-read snapshot must belong to the same one.
TEST(NoTornReads) {
    PoseChannel ch;
    std::atomic<bool> stop{false};
    std::atomic<int> bad{0};
    std::atomic<int> reads{0};

    std::thread w([&] {
        for (int i = 0; i < 200000; ++i) {
            PoseSnapshot s{};
            s.frameIndex = i;
            const float v = (i & 1) ? 1.0f : -1.0f;           // two distinct generations
            s.head.position = {v, v, v};
            s.handGrip[0].position = {v, v, v};
            s.handAim[0].position  = {v, v, v};
            ch.Publish(s);
        }
        stop = true;
    });
    std::thread r([&] {
        PoseSnapshot s{};
        while (!stop) if (ch.TryRead(s)) {
            ++reads;
            const float v = s.head.position.x;                // every field must agree
            if (s.handGrip[0].position.x != v || s.handAim[0].position.x != v) ++bad;
        }
    });
    w.join();
    r.join();
    CHECK(bad == 0);
    // A test that never actually read anything proves nothing -- assert the instrument ran.
    CHECK(reads > 0);
}

// A2.3: the latch must derive from the pristine value, so composing the same delta
// twice gives the same answer. Reading live state would drift instead.
TEST(TransformLatchDoesNotAccumulate) {
    TransformLatch latch;
    CHECK(!latch.Compose(Mat4{}).has_value());     // nothing latched: no answer, not a guess

    const Mat4 pristine = Translation({1, 2, 3});
    latch.OnAcquire(pristine);

    const Mat4 delta = Translation({0.5f, 0, 0});
    const Mat4 a = *latch.Compose(delta);
    const Mat4 b = *latch.Compose(delta);          // same input, same output, every time

    for (int i = 0; i < 4; ++i)
        for (int j = 0; j < 4; ++j) CHECK(Near(a.m[i][j], b.m[i][j], 1e-6f));

    CHECK(Near(a.m[0][3], 1.5f, 1e-6f));           // base * delta, once

    latch.OnRelease();
    CHECK(!latch.Held());
}

// A2.4: one recentre event must rebase every lane exactly once, and in the same frame.
TEST(RecenterEpochRebasesEveryLaneOnce) {
    RecenterBus bus;
    CameraLane camera, weapon, hud;

    PoseSnapshot s{};
    s.head.position = {0, 1.7f, 0};
    s.recenterEpoch = bus.Epoch();

    // First frame: every lane takes its initial baseline.
    camera.Update(s); weapon.Update(s); hud.Update(s);
    CHECK(camera.Rebases() == 1);

    // Steady state: no epoch change, no rebase.
    for (int i = 0; i < 10; ++i) { s.head.position.y += 0.01f; camera.Update(s); weapon.Update(s); hud.Update(s); }
    CHECK(camera.Rebases() == 1);
    CHECK(weapon.Rebases() == 1);

    // One recentre request -> one epoch bump -> every lane rebases, on the same snapshot.
    bus.Request();
    s.recenterEpoch = bus.Epoch();
    s.head.position = {0.4f, 1.8f, -0.2f};
    camera.Update(s); weapon.Update(s); hud.Update(s);

    CHECK(camera.Rebases() == 2);
    CHECK(weapon.Rebases() == 2);
    CHECK(hud.Rebases() == 2);
    // ...and to the same value, which is the whole point of routing it through the snapshot.
    CHECK(Near(camera.Baseline().position, weapon.Baseline().position, 1e-6f));
    CHECK(Near(camera.Baseline().position, hud.Baseline().position, 1e-6f));
}

// A2.5: a jump must RESET the latch rather than become a permanent offset.
TEST(PoseSettleLatchRejectsAJump) {
    PoseSettleLatch latch;
    Pose p{};
    p.position = {0, 1.7f, 0};

    // Eight consecutive agreeing samples settle it.
    bool settledOn = false;
    for (int i = 0; i < 8; ++i) settledOn |= latch.Offer(p);
    CHECK(settledOn);
    CHECK(latch.Settled());

    // A big jump un-settles it rather than averaging in.
    Pose jump = p;
    jump.position = {0, 1.7f, 3.0f};        // 3 m: far past kMaxMetres
    latch.Offer(jump);
    CHECK(!latch.Settled());

    // And the new candidate is the jump, not the old value -- so it settles THERE.
    for (int i = 0; i < 8; ++i) latch.Offer(jump);
    CHECK(latch.Settled());
    CHECK(Near(latch.Value()->position.z, 3.0f, 1e-6f));
}

// The failure this guards against: fewer than N samples must NOT settle.
TEST(PoseSettleLatchNeedsEnoughAgreement) {
    PoseSettleLatch latch;
    Pose p{};
    p.position = {0, 1.7f, 0};
    for (int i = 0; i < 7; ++i) latch.Offer(p);
    CHECK(!latch.Settled());
    latch.Offer(p);
    CHECK(latch.Settled());
}
