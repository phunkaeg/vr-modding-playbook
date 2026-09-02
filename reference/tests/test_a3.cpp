// test_a3.cpp -- stereo projection: corners, asymmetry, the eye-adjust identity,
// the residual's two terms, and the depth-slice multiplier ch14 quotes.
#include "check.h"
#include "vrref/a1_rotation.h"
#include "vrref/a3_projection.h"

using namespace vrref;

// A representative asymmetric headset FOV, in radians. Asymmetric on purpose: a
// symmetric one hides exactly the bug this appendix is about.
static FovAngles SampleFov() {
    return {-0.785398f, 0.698132f, 0.750492f, -0.820305f};   // -45, +40, +43, -47 degrees
}

// A3.2's own test: a correct projection maps the frustum's own corners to the NDC
// box edges, by construction.
static void TestProjectionMapsFrustumCorners(const Mat4& P, const FrustumTangents& t,
                                             float nearZ, float /*farZ*/) {
    // A point on the LEFT plane at distance `nearZ` must land at NDC x = -1.
    const Vec3 onLeft{t.l * nearZ, 0.0f, -nearZ};      // -Z forward; flip if yours is +Z
    const Vec4 clip = P * Vec4{onLeft, 1.0f};
    CHECK(std::fabs(clip.x / clip.w + 1.0f) < 1e-4f);

    const Vec3 onRight{t.r * nearZ, 0.0f, -nearZ};
    const Vec4 cr = P * Vec4{onRight, 1.0f};
    CHECK(std::fabs(cr.x / cr.w - 1.0f) < 1e-4f);

    // Centre of the frustum is NOT NDC x=0 under an asymmetric FOV -- assert the asymmetry
    // is actually present, or a symmetric bug passes silently.
    const Vec4 cc = P * Vec4{0.0f, 0.0f, -nearZ, 1.0f};
    const float expected = -(t.r + t.l) / t.width;
    CHECK(std::fabs(cc.x / cc.w - expected) < 1e-4f);
}

TEST(ProjectionCorners) {
    const FrustumTangents t = TangentsFromFov(SampleFov());
    const Mat4 P = ProjectionFromTangents(t, 0.05f, 1000.0f);
    TestProjectionMapsFrustumCorners(P, t, 0.05f, 1000.0f);

    // The vertical pair too -- an appendix test that only checks x passes a swapped
    // up/down.
    const Vec3 onUp{0.0f, t.u * 0.05f, -0.05f};
    const Vec4 cu = P * Vec4{onUp, 1.0f};
    CHECK(std::fabs(cu.y / cu.w - 1.0f) < 1e-4f);

    // And the asymmetry is real, not an artefact of a symmetric test FOV.
    CHECK(std::fabs(t.r + t.l) > 0.1f);
}

// A3.1: tangents, not angles. Averaging ANGLES and averaging TANGENTS give different
// answers on an asymmetric frustum, which is the reason the appendix insists.
TEST(TangentsAreNotAngles) {
    const FovAngles f = SampleFov();
    const FrustumTangents t = TangentsFromFov(f);
    const float midAngle   = std::tan((f.angleLeft + f.angleRight) * 0.5f);
    const float midTangent = (t.l + t.r) * 0.5f;
    CHECK(std::fabs(midAngle - midTangent) > 1e-3f);   // they genuinely differ
}

// A3.3: the eye-adjust identity. With the centre projection and no eye offset, the
// adjusted WVP must be the original one -- a correction that changes an unchanged
// case is a correction with a sign or an order error.
TEST(EyeAdjustIsIdentityWithNoOffset) {
    const FrustumTangents t = TangentsFromFov(SampleFov());
    const Mat4 P = ProjectionFromTangents(t, 0.05f, 1000.0f);
    const Mat4 view = Mat4FromMat3(QuatToMat3(QuatFromEuler(0.2f, -0.4f, 0.1f))) * Translation({1, 2, -3});
    const Mat4 wvp = P * view;

    const Mat4 out = EyeAdjustedWVP(wvp, P, P, Mat4{});
    for (int i = 0; i < 4; ++i)
        for (int j = 0; j < 4; ++j) CHECK(Near(out.m[i][j], wvp.m[i][j], 2e-3f));
}

// ...and with a real eye offset it must move the world by exactly the IPD half-step.
TEST(EyeAdjustAppliesTheOffset) {
    const FrustumTangents t = TangentsFromFov(SampleFov());
    const Mat4 P = ProjectionFromTangents(t, 0.05f, 1000.0f);
    const Mat4 wvp = P;                                   // view = identity, so world == view space
    const float halfIpd = 0.032f;
    const Mat4 tEye = Translation({-halfIpd, 0, 0});      // move the world right eye-ward

    const Mat4 out = EyeAdjustedWVP(wvp, P, P, tEye);

    const Vec3 pt{0.0f, 0.0f, -2.0f};
    const Vec4 a = out * Vec4{pt, 1.0f};
    const Vec4 b = P * Vec4{Vec3{pt.x - halfIpd, pt.y, pt.z}, 1.0f};
    CHECK(Near(a.x / a.w, b.x / b.w, 1e-3f));
}

// A3.4: the residual is minimal at the true projection, and -- the point of the
// section -- TERM 2 is what sees a wrong FOV. Term 1 alone does not.
TEST(ResidualFindsTheTrueProjection) {
    const FrustumTangents t = TangentsFromFov(SampleFov());
    const Mat4 P = ProjectionFromTangents(t, 0.05f, 1000.0f);
    const Mat4 view = Mat4FromMat3(QuatToMat3(QuatFromEuler(0.3f, 0.7f, -0.2f))) * Translation({4, -1, 9});
    const Mat4 wvp = P * view;

    const float atTruth = ProjectionResidual(wvp, P);
    CHECK(atTruth < 1e-2f);

    // A wrong FOV: same near/far, different tangents.
    FovAngles wrongFov = SampleFov();
    wrongFov.angleRight += 0.15f;
    const Mat4 wrongP = ProjectionFromTangents(TangentsFromFov(wrongFov), 0.05f, 1000.0f);
    CHECK(ProjectionResidual(wvp, wrongP) > atTruth * 10.0f);

    // A wrong near plane, which term 1 is the one that catches.
    const Mat4 wrongNear = ProjectionFromTangents(t, 0.2f, 1000.0f);
    CHECK(ProjectionResidual(wvp, wrongNear) > atTruth * 10.0f);
}
