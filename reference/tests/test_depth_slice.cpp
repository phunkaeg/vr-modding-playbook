// test_depth_slice.cpp -- pins ch14 / CAM-008.
//
// bfbc2-vr's claim: applying a correction built for projection P to a draw that uses its
// own projection P' leaves P'*inverse(P) in front of the correction, which passes rotation
// through and multiplies TRANSLATION by t'/t -- measured at 75x and 213x on Frostbite's
// 7.48 m and 21.34 m depth slices against a 0.1 m near plane.
//
// This test does not check a matrix element. It measures the thing a player sees: how far
// the world moves when the eye moves 3.3 cm, under the correct per-draw correction and
// under the global one.
#include <cstdio>

#include "check.h"
#include "vrref/a1_rotation.h"
#include "vrref/a3_projection.h"

using namespace vrref;

namespace {

FovAngles Fov() { return {-0.785398f, 0.698132f, 0.750492f, -0.820305f}; }

// A view-space correction becomes a clip-space one by conjugation: for column vectors,
//   P * C * V * W  ==  (P * C * inverse(P)) * (P * V * W)
Mat4 ClipSpaceCorrection(const Mat4& p, const Mat4& viewSpaceCorrection) {
    return p * viewSpaceCorrection * Inverse(p);
}

float NdcX(const Mat4& m, const Vec3& pt) {
    const Vec4 c = m * Vec4{pt, 1.0f};
    return c.x / c.w;
}

}  // namespace

TEST(DepthSliceOverScalesTranslation) {
    const FrustumTangents t = TangentsFromFov(Fov());
    const float farZ = 4000.0f;
    const float nearCorrected = 0.1f;                 // the projection the VP constant carried

    const Mat4 pCorrection = ProjectionFromTangents(t, nearCorrected, farZ);

    // 3.3 cm of eye offset -- bfbc2-vr's own figure.
    const Mat4 eyeShift = Translation({0.033f, 0, 0});
    const Vec3 worldPt{0.0f, 0.0f, -50.0f};           // 50 m out, in the far slice

    const float slices[2] = {7.48f, 21.34f};
    const float expected[2] = {74.8f, 213.4f};

    for (int i = 0; i < 2; ++i) {
        const Mat4 pDraw = ProjectionFromTangents(t, slices[i], farZ);

        const float base = NdcX(pDraw, worldPt);

        // RIGHT -- CAM-008: build the correction around the draw's own projection.
        const float right = NdcX(ClipSpaceCorrection(pDraw, eyeShift) * pDraw, worldPt);

        // WRONG -- the global form, built once from the projection the constant carried.
        const float wrong = NdcX(ClipSpaceCorrection(pCorrection, eyeShift) * pDraw, worldPt);

        const float dRight = std::fabs(right - base);
        const float dWrong = std::fabs(wrong - base);
        CHECK(dRight > 1e-6f);                        // the correct one does move the world

        const float ratio = dWrong / dRight;
        std::printf("      slice %.2f m: over-scale = %.1fx (bfbc2-vr measured %.0fx)\n",
                    slices[i], ratio, expected[i]);

        // The claim, pinned: the error is not a few percent, it is two orders of magnitude,
        // and its size is the near-plane ratio.
        CHECK(ratio > 50.0f);
        CHECK(Near(ratio, expected[i], expected[i] * 0.10f));
    }
}

// The other half of the claim, and the reason the bug reads as a tracking fault:
// ROTATION about the eye passes through the residue untouched.
TEST(DepthSliceLeavesRotationAlone) {
    const FrustumTangents t = TangentsFromFov(Fov());
    const float farZ = 4000.0f;
    const Mat4 pCorrection = ProjectionFromTangents(t, 0.1f, farZ);
    const Mat4 pDraw       = ProjectionFromTangents(t, 7.48f, farZ);

    // A pure rotation about the eye, as a view-space correction.
    const Mat4 rot = Mat4FromMat3(QuatToMat3(QuatFromAxisAngle({0, 1, 0}, 0.12f)));
    const Vec3 worldPt{0.0f, 0.0f, -50.0f};

    const float right = NdcX(ClipSpaceCorrection(pDraw, rot) * pDraw, worldPt);
    const float wrong = NdcX(ClipSpaceCorrection(pCorrection, rot) * pDraw, worldPt);

    // Within a fraction of a percent: looking around still works, which is exactly why
    // "the world warps around me but I can still look around" is the diagnostic signature.
    CHECK(Near(right, wrong, std::fabs(right) * 0.02f + 1e-4f));
}
