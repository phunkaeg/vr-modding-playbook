// test_a1.cpp -- the five tests A1.6 specifies, made runnable.
#include "check.h"
#include "vrref/a1_rotation.h"

using namespace vrref;

// 1. ORTHONORMALITY -- unit columns, mutually perpendicular, determinant +1.
//    A determinant of -1 is a reflection: you flipped a cross product somewhere.
static void AssertRotationMatrix(const Mat3& m, float eps = 1e-5f) {
    const Vec3 c0 = Column(m, 0), c1 = Column(m, 1), c2 = Column(m, 2);
    CHECK(std::fabs(Length(c0) - 1.0f) < eps);
    CHECK(std::fabs(Length(c1) - 1.0f) < eps);
    CHECK(std::fabs(Length(c2) - 1.0f) < eps);
    CHECK(std::fabs(Dot(c0, c1)) < eps);
    CHECK(std::fabs(Dot(c0, c2)) < eps);
    CHECK(std::fabs(Dot(c1, c2)) < eps);
    CHECK(std::fabs(Determinant(m) - 1.0f) < eps);
}

// 2. TWO INDEPENDENT PATHS AGREE -- catches the A1.1 typo class outright.
TEST(QuatMatrixAgreement) {
    for (int i = 0; i < 1000; ++i) {
        const Quat q = RandomUnitQuat(i);        // seeded: a failure must reproduce
        const Mat3 m = QuatToMat3(q);
        AssertRotationMatrix(m);
        for (int j = 0; j < 8; ++j) {
            const Vec3 v = RandomUnitVec(i * 8 + j);
            CHECK(Near(m * v, RotateByQuat(q, v), 1e-4f));
        }
    }
}

// 3. EXTREME ANGLES, EXPLICITLY. The typo class is invisible near identity by construction,
//    so a suite that only samples gentle rotations PASSES ON BROKEN CODE.
TEST(ExtremeAngles) {
    const float a[] = {0.0f, 0.5f, 1.0f, 2.0f, 3.0f, 3.14159f, -3.14159f};
    for (float ax : a) for (float ay : a) for (float az : a) {
        const Quat q = QuatFromEuler(ax, ay, az);
        AssertRotationMatrix(QuatToMat3(q));
        CHECK(Near(QuatToMat3(q) * Vec3{0, 0, 1}, RotateByQuat(q, Vec3{0, 0, 1}), 1e-4f));
    }
}

// 4. ROUND-TRIP the integer rotator, deliberately crossing the wrap boundary.
TEST(RotatorRoundTrip) {
    for (int32_t r = -200000; r <= 200000; r += 997)
        CHECK(WrapRot(RadToRot(RotToRad(r))) == WrapRot(r));
}

// 5. HANDEDNESS, pinned once. Change engine, this test tells you.
TEST(Handedness) {
    const Mat3 b = BasisFromForwardUp(Vec3{0, 0, 1}, Vec3{0, 1, 0});
    CHECK(Near(Column(b, 2), Vec3{0, 0, 1}, 1e-5f));   // forward is column 2
    CHECK(Near(Column(b, 1), Vec3{0, 1, 0}, 1e-5f));   // up is column 1
    CHECK(Determinant(b) > 0.0f);                      // right-handed
}

// --- beyond A1.6: the claims the prose makes, turned into assertions ---------

// A1.3 says the basis builder must not blow up when forward is parallel to the hint.
TEST(BasisDegenerateHint) {
    const Mat3 b = BasisFromForwardUp(Vec3{0, 1, 0}, Vec3{0, 1, 0});
    AssertRotationMatrix(b);
    CHECK(Near(Column(b, 2), Vec3{0, 1, 0}, 1e-5f));
}

// A1.4 says roll is signed and continuous across pi -- which is the whole reason
// it is atan2 and not acos.
TEST(RollIsSignedAndContinuous) {
    const Vec3 fwd{0, 0, 1};
    const Vec3 refUp{0, 1, 0};
    // Rolling by +a and -a about forward must give exactly opposite signs.
    for (float a = 0.1f; a < 3.0f; a += 0.37f) {
        const Vec3 upPos = QuatToMat3(QuatFromAxisAngle(fwd,  a)) * refUp;
        const Vec3 upNeg = QuatToMat3(QuatFromAxisAngle(fwd, -a)) * refUp;
        const float rp = RollAboutAxis(fwd, upPos, refUp);
        const float rn = RollAboutAxis(fwd, upNeg, refUp);
        CHECK(std::fabs(rp - a) < 1e-4f);
        CHECK(std::fabs(rn + a) < 1e-4f);
    }
    // acos would lose this: the two differ only in sign, not in magnitude.
}

// A1.5's central claim: adding rotator components "passes a yaw-only test" and is
// nonetheless wrong in general. Both halves are asserted, so the warning is evidence.
TEST(NaiveRotatorAdditionPassesYawOnlyAndFailsGeneral) {
    // Yaw-only: the naive path agrees with the correct one.
    {
        const Rotator engine{0, 8000, 0};
        const Rotator delta {0, 3000, 0};
        const Rotator good = ComposeWithTracked(engine, QuatFromRotator(delta));
        const Rotator bad  = ComposeWithTrackedNaive(engine, delta);
        CHECK(std::abs(WrapRot(good.Yaw) - WrapRot(bad.Yaw)) < 64);   // ~0.35 degrees
    }
    // General: with pitch and roll in play, the two diverge by a lot.
    {
        const Rotator engine{6000, 8000, 4000};
        const Rotator delta {5000, 3000, 7000};
        const Rotator good = ComposeWithTracked(engine, QuatFromRotator(delta));
        const Rotator bad  = ComposeWithTrackedNaive(engine, delta);
        const int32_t dp = std::abs(WrapRot(good.Pitch) - WrapRot(bad.Pitch));
        const int32_t dy = std::abs(WrapRot(good.Yaw)   - WrapRot(bad.Yaw));
        const int32_t dr = std::abs(WrapRot(good.Roll)  - WrapRot(bad.Roll));
        CHECK(dp + dy + dr > 1000);    // > ~5 degrees of total disagreement
    }
}

// The quaternion round trip the rotator composition depends on.
TEST(RotatorQuatRoundTrip) {
    for (int32_t p = -30000; p <= 30000; p += 7919)
        for (int32_t y = -30000; y <= 30000; y += 7919) {
            const Rotator r{p, y, 0};
            const Rotator back = RotatorFromQuat(QuatFromRotator(r));
            // Compare as rotations, not as component triples: two rotators can name
            // the same rotation. This is exactly why A1.5 says to compose as rotations.
            const Vec3 v{0.3f, 0.5f, 0.81f};
            CHECK(Near(RotateByQuat(QuatFromRotator(r), v),
                       RotateByQuat(QuatFromRotator(back), v), 2e-3f));
        }
}

// A1.5b: the bug that cost Singularity VR twenty false camera handoffs in one run.
// The naive difference is unbounded; the wrapped one is always the short way round.
TEST(WrappedAngleDifference) {
    // Two headings 0.3 degrees apart, straddling the wrap seam.
    const int32_t small = 55;                       // ~0.3 deg in 65536-unit rotator
    const int32_t a = 20, b = WrapRot(a - small);   // b is just below zero, so wraps high

    CHECK(std::abs(a - b) > 60000);                 // the naive difference: reads as ~360 deg
    CHECK(std::abs(RotDelta(a, b)) == small);       // the wrapped one: the real 0.3 deg

    // A threshold test is only correct on the wrapped difference.
    const int32_t fifteenDeg = static_cast<int32_t>(15.0 / 360.0 * kRotUnitsPerTurn);
    CHECK(std::abs(RotDelta(a, b)) < fifteenDeg);   // correctly "no big turn"
    CHECK(!(std::abs(a - b) < fifteenDeg));         // the naive form fires the threshold

    // Exhaustive: the wrapped difference is always the short way round.
    for (int32_t x = 0; x < kRotUnitsPerTurn; x += 331)
        for (int32_t y = 0; y < kRotUnitsPerTurn; y += 337) {
            const int32_t dl = RotDelta(x, y);
            CHECK(dl >= -kRotUnitsPerTurn / 2 && dl <= kRotUnitsPerTurn / 2);
            CHECK(WrapRot(y + dl) == WrapRot(x));   // and it still gets you there
        }
}
