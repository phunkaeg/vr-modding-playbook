// a1_rotation.h -- the reference implementations from docs/a1-rotation-and-frames.md.
//
// The code here is the code in the appendix. If you change one, change both -- the
// tests in tests/test_a1.cpp are what the appendix's section A1.6 describes.
#pragma once

#include "vrmath.h"

namespace vrref {

// --- A1.1 Quaternion -> matrix, and the typo that survives review -------------

inline Mat3 QuatToMat3(const Quat& q) {
    const float xx = q.x * q.x, yy = q.y * q.y, zz = q.z * q.z;
    const float xy = q.x * q.y, xz = q.x * q.z, yz = q.y * q.z;
    const float wx = q.w * q.x, wy = q.w * q.y, wz = q.w * q.z;

    Mat3 r;
    r.m[0][0] = 1.0f - 2.0f * (yy + zz);
    r.m[0][1] =        2.0f * (xy - wz);   // xy, NOT yy. This is the one.
    r.m[0][2] =        2.0f * (xz + wy);

    r.m[1][0] =        2.0f * (xy + wz);   // xy again, opposite sign on wz
    r.m[1][1] = 1.0f - 2.0f * (xx + zz);
    r.m[1][2] =        2.0f * (yz - wx);

    r.m[2][0] =        2.0f * (xz - wy);
    r.m[2][1] =        2.0f * (yz + wx);
    r.m[2][2] = 1.0f - 2.0f * (xx + yy);
    return r;
}

// --- A1.2 The independent cross-check that catches it ------------------------

// v' = v + 2w(qv x v) + 2(qv x (qv x v))   -- no matrix, no shared code path
inline Vec3 RotateByQuat(const Quat& q, const Vec3& v) {
    const Vec3 qv{q.x, q.y, q.z};
    const Vec3 t = Cross(qv, v) * 2.0f;
    return v + t * q.w + Cross(qv, t);
}

// --- A1.3 Build a basis; never band-aid axes ---------------------------------

// Right-handed. If your engine is left-handed, swap the Cross() operands in `right`;
// the handedness test in A1.6 will tell you immediately which way round you are.
inline Mat3 BasisFromForwardUp(Vec3 forward, Vec3 upHint) {
    const Vec3 f = Normalize(forward);

    // Degenerate: forward parallel to the hint. Pick any perpendicular axis.
    if (std::fabs(Dot(f, Normalize(upHint))) > 0.9999f)
        upHint = (std::fabs(f.z) < 0.9f) ? Vec3{0, 0, 1} : Vec3{1, 0, 0};

    const Vec3 r = Normalize(Cross(upHint, f));   // right
    const Vec3 u = Cross(f, r);                   // already unit
    return Mat3FromColumns(r, u, f);
}

// --- A1.4 Signed roll, without acos and without gimbal -----------------------

// Signed roll of `up` about `forward`, measured from `referenceUp`. Radians, (-pi, pi].
inline float RollAboutAxis(const Vec3& forward, const Vec3& up, const Vec3& referenceUp) {
    const Vec3 f = Normalize(forward);
    const Vec3 a = Normalize(up          - f * Dot(up,          f));  // into the plane
    const Vec3 b = Normalize(referenceUp - f * Dot(referenceUp, f));  // perpendicular to f
    return std::atan2(Dot(Cross(b, a), f), Dot(b, a));                // signed; no acos, no gimbal
}

// --- A1.5 Integer rotators, and composing with a tracked rotation ------------

constexpr int32_t kRotUnitsPerTurn = 65536;   // UE1-3 FRotator. Verify for your engine.
constexpr float   kRotToRad = 6.28318530718f / kRotUnitsPerTurn;

inline int32_t WrapRot(int32_t r)  { return r & (kRotUnitsPerTurn - 1); }  // power-of-two only
inline float   RotToRad(int32_t r) { return WrapRot(r) * kRotToRad; }
inline int32_t RadToRot(float rad) { return WrapRot(static_cast<int32_t>(std::lround(rad / kRotToRad))); }

// A minimal three-axis integer rotator, in the shape UE1-3 uses.
struct Rotator { int32_t Pitch = 0, Yaw = 0, Roll = 0; };

// The axis ORDER here is the engine's convention, and it is the thing to verify
// against your target rather than to assume.
inline Quat QuatFromRotator(const Rotator& r) {
    return QuatFromEuler(RotToRad(r.Pitch), RotToRad(r.Yaw), RotToRad(r.Roll));
}

inline Rotator RotatorFromQuat(const Quat& qIn) {
    const Quat q = Normalize(qIn);
    // Intrinsic X-then-Y-then-Z, matching QuatFromEuler above.
    const float sinp = 2.0f * (q.w * q.x + q.y * q.z);
    const float cosp = 1.0f - 2.0f * (q.x * q.x + q.y * q.y);
    const float pitch = std::atan2(sinp, cosp);

    float sy = 2.0f * (q.w * q.y - q.z * q.x);
    sy = (sy > 1.0f) ? 1.0f : (sy < -1.0f ? -1.0f : sy);   // clamp: asin domain
    const float yaw = std::asin(sy);

    const float sinr = 2.0f * (q.w * q.z + q.x * q.y);
    const float cosr = 1.0f - 2.0f * (q.y * q.y + q.z * q.z);
    const float roll = std::atan2(sinr, cosr);

    return {RadToRot(pitch), RadToRot(yaw), RadToRot(roll)};
}

// A1.5b The SIGNED wrapped difference. `a - b` on a wrapping integer rotator does not
// wrap: two headings 0.3 degrees apart can differ by 65590 units, which reads as 360.3
// degrees, and every threshold test on that value is wrong near the seam.
inline int32_t WrapRotSigned(int32_t r) {
    const int32_t w = WrapRot(r);                       // 0 .. 65535
    return (w >= kRotUnitsPerTurn / 2) ? w - kRotUnitsPerTurn : w;
}

inline int32_t RotDelta(int32_t a, int32_t b) { return WrapRotSigned(a - b); }

// RIGHT: convert out, compose as rotations, convert back.
inline Rotator ComposeWithTracked(const Rotator& engine, const Quat& trackedDelta) {
    const Quat base = QuatFromRotator(engine);   // your engine's axis ORDER matters here
    return RotatorFromQuat(Normalize(QuatMul(trackedDelta, base)));
}

// WRONG -- and it passes a yaw-only test. Kept, and tested, so the appendix's claim
// that it passes a yaw-only test and fails a general one is checked rather than asserted.
inline Rotator ComposeWithTrackedNaive(const Rotator& engine, const Rotator& delta) {
    return {WrapRot(engine.Pitch + delta.Pitch),
            WrapRot(engine.Yaw   + delta.Yaw),
            WrapRot(engine.Roll  + delta.Roll)};
}

}  // namespace vrref
