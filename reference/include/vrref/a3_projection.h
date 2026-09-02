// a3_projection.h -- the reference implementations from docs/a3-stereo-projection.md.
#pragma once

#include "vrmath.h"

namespace vrref {

// Stand-in for XrFovf, so this compiles with no OpenXR headers. Field names and
// units (radians, signed, left/down typically negative) match the real one.
struct FovAngles {
    float angleLeft = 0, angleRight = 0, angleUp = 0, angleDown = 0;
};

// --- A3.1 Tangents, not angles ----------------------------------------------

struct FrustumTangents { float l, r, u, d, width, height; };

inline FrustumTangents TangentsFromFov(const FovAngles& fov) {
    FrustumTangents t;
    t.l = std::tan(fov.angleLeft);      // typically negative
    t.r = std::tan(fov.angleRight);
    t.u = std::tan(fov.angleUp);
    t.d = std::tan(fov.angleDown);      // typically negative
    t.width  = t.r - t.l;
    t.height = t.u - t.d;
    return t;
}

// The asymmetric projection those tangents describe. Right-handed, -Z forward,
// NDC z in [-1, 1] (OpenGL-style). A [0,1] depth engine changes the last two rows
// only -- and the corner test in A3 will tell you if you got it wrong.
inline Mat4 ProjectionFromTangents(const FrustumTangents& t, float nearZ, float farZ) {
    Mat4 p;
    for (int i = 0; i < 4; ++i)
        for (int j = 0; j < 4; ++j) p.m[i][j] = 0.0f;

    p.m[0][0] = 2.0f / t.width;
    p.m[0][2] = (t.r + t.l) / t.width;
    p.m[1][1] = 2.0f / t.height;
    p.m[1][2] = (t.u + t.d) / t.height;
    p.m[2][2] = -(farZ + nearZ) / (farZ - nearZ);
    p.m[2][3] = -(2.0f * farZ * nearZ) / (farZ - nearZ);
    p.m[3][2] = -1.0f;
    return p;
}

// --- A3.3 Adjusting an already-combined WVP ---------------------------------

// Column-vector (v' = M * v). Row-vector engines reverse every product below.
//   M_eye = P_eye * T_eye * inverse(P_center)
// applied to an already-combined WVP:
inline Mat4 EyeAdjustedWVP(const Mat4& wvpCenter, const Mat4& pCenter,
                           const Mat4& pEye, const Mat4& tEyeViewSpace) {
    return pEye * tEyeViewSpace * Inverse(pCenter) * wvpCenter;
}

// --- A3.4 Recovering the centre projection from an observed WVP -------------

// Two independent terms. The first alone will pass a wrong FOV.
// COLUMN-VECTOR (wvp = P * V * W), so the projection is divided out on the LEFT.
// A row-vector engine - which is how a D3D9 shader constant usually arrives - stores
// the transpose, and there the term is `wvp * Inverse(pCenterCandidate)`. Getting this
// backwards makes the residual meaningless rather than merely wrong, because the product
// is not affine in either candidate. Caught by ResidualFindsTheTrueProjection.
inline float ProjectionResidual(const Mat4& wvp, const Mat4& pCenterCandidate) {
    const Mat4 A = Inverse(pCenterCandidate) * wvp;     // expected: view * world, i.e. affine

    // TERM 1 -- affinity. Catches a wrong near/far and a wrong projective row.
    float affine = std::fabs(A.m[3][0]) + std::fabs(A.m[3][1]) + std::fabs(A.m[3][2])
                 + std::fabs(A.m[3][3] - 1.0f);

    // TERM 2 -- orthonormality of the upper 3x3 after dividing out uniform scale.
    // THIS is the term that sees a wrong FOV.
    Vec3 c0 = Column3(A, 0), c1 = Column3(A, 1), c2 = Column3(A, 2);
    const float s = (Length(c0) + Length(c1) + Length(c2)) / 3.0f;   // uniform scale is legitimate
    if (s < 1e-6f) return 1e9f;
    c0 = c0 / s; c1 = c1 / s; c2 = c2 / s;

    float ortho = std::fabs(Length(c0) - 1.0f) + std::fabs(Length(c1) - 1.0f) + std::fabs(Length(c2) - 1.0f)
                + std::fabs(Dot(c0, c1)) + std::fabs(Dot(c0, c2)) + std::fabs(Dot(c1, c2));

    return affine + ortho;
}

// --- ch14 / CAM-008: the depth-slice residue --------------------------------
//
// Not from A3, but it belongs with it: bfbc2-vr measured that applying a correction
// built for projection P to a draw whose own projection is P' leaves P'*inverse(P)
// in front of it, which passes rotation through and multiplies TRANSLATION by t'/t.
// The test pins the multiplier, so the claim in ch14 is checked rather than quoted.
inline Mat4 DepthSliceResidue(const Mat4& pDraw, const Mat4& pCorrection) {
    return pDraw * Inverse(pCorrection);
}

}  // namespace vrref
