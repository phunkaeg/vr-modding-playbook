// vrmath.h -- the minimum linear algebra the appendices assume.
//
// This exists so the reference code in docs/a1..a5 COMPILES AND IS TESTED rather than
// being read-only pseudocode. Conventions are fixed here and asserted in the tests:
//
//   * COLUMN-VECTOR:  v' = M * v.  A row-vector engine reverses every product.
//   * RIGHT-HANDED,  -Z forward, +Y up  (OpenXR's convention).
//   * Mat3/Mat4 are stored ROW-MAJOR: m[row][col].  Column(m, i) reads down a column.
//
// If your engine differs, change it HERE and let the tests tell you what moved.
#pragma once

#include <cmath>
#include <cstdint>

namespace vrref {

constexpr float kPi = 3.14159265358979323846f;

// ------------------------------------------------------------------ vectors

struct Vec2 { float x = 0, y = 0; };

struct Vec3 {
    float x = 0, y = 0, z = 0;
};

inline Vec3 operator+(const Vec3& a, const Vec3& b) { return {a.x + b.x, a.y + b.y, a.z + b.z}; }
inline Vec3 operator-(const Vec3& a, const Vec3& b) { return {a.x - b.x, a.y - b.y, a.z - b.z}; }
inline Vec3 operator*(const Vec3& a, float s)       { return {a.x * s, a.y * s, a.z * s}; }
inline Vec3 operator/(const Vec3& a, float s)       { return {a.x / s, a.y / s, a.z / s}; }
inline Vec3 operator-(const Vec3& a)                { return {-a.x, -a.y, -a.z}; }

inline float Dot(const Vec3& a, const Vec3& b) { return a.x * b.x + a.y * b.y + a.z * b.z; }

inline Vec3 Cross(const Vec3& a, const Vec3& b) {
    return {a.y * b.z - a.z * b.y,
            a.z * b.x - a.x * b.z,
            a.x * b.y - a.y * b.x};
}

inline float Length(const Vec3& a) { return std::sqrt(Dot(a, a)); }

inline Vec3 Normalize(const Vec3& a) {
    const float len = Length(a);
    return (len > 1e-20f) ? a / len : Vec3{0, 0, 0};
}

struct Vec4 {
    float x = 0, y = 0, z = 0, w = 0;
    Vec4() = default;
    Vec4(float x_, float y_, float z_, float w_) : x(x_), y(y_), z(z_), w(w_) {}
    Vec4(const Vec3& v, float w_) : x(v.x), y(v.y), z(v.z), w(w_) {}
};

// ------------------------------------------------------------------ matrices

struct Mat3 {
    float m[3][3] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}};
};

inline Vec3 Column(const Mat3& a, int i) { return {a.m[0][i], a.m[1][i], a.m[2][i]}; }

inline Mat3 Mat3FromColumns(const Vec3& c0, const Vec3& c1, const Vec3& c2) {
    Mat3 r;
    r.m[0][0] = c0.x; r.m[0][1] = c1.x; r.m[0][2] = c2.x;
    r.m[1][0] = c0.y; r.m[1][1] = c1.y; r.m[1][2] = c2.y;
    r.m[2][0] = c0.z; r.m[2][1] = c1.z; r.m[2][2] = c2.z;
    return r;
}

inline Vec3 operator*(const Mat3& a, const Vec3& v) {
    return {a.m[0][0] * v.x + a.m[0][1] * v.y + a.m[0][2] * v.z,
            a.m[1][0] * v.x + a.m[1][1] * v.y + a.m[1][2] * v.z,
            a.m[2][0] * v.x + a.m[2][1] * v.y + a.m[2][2] * v.z};
}

inline float Determinant(const Mat3& a) {
    return a.m[0][0] * (a.m[1][1] * a.m[2][2] - a.m[1][2] * a.m[2][1])
         - a.m[0][1] * (a.m[1][0] * a.m[2][2] - a.m[1][2] * a.m[2][0])
         + a.m[0][2] * (a.m[1][0] * a.m[2][1] - a.m[1][1] * a.m[2][0]);
}

struct Mat4 {
    float m[4][4] = {{1, 0, 0, 0}, {0, 1, 0, 0}, {0, 0, 1, 0}, {0, 0, 0, 1}};
};

inline Vec3 Column3(const Mat4& a, int i) { return {a.m[0][i], a.m[1][i], a.m[2][i]}; }

inline Mat4 operator*(const Mat4& a, const Mat4& b) {
    Mat4 r;
    for (int i = 0; i < 4; ++i)
        for (int j = 0; j < 4; ++j) {
            float s = 0.0f;
            for (int k = 0; k < 4; ++k) s += a.m[i][k] * b.m[k][j];
            r.m[i][j] = s;
        }
    return r;
}

inline Vec4 operator*(const Mat4& a, const Vec4& v) {
    return {a.m[0][0] * v.x + a.m[0][1] * v.y + a.m[0][2] * v.z + a.m[0][3] * v.w,
            a.m[1][0] * v.x + a.m[1][1] * v.y + a.m[1][2] * v.z + a.m[1][3] * v.w,
            a.m[2][0] * v.x + a.m[2][1] * v.y + a.m[2][2] * v.z + a.m[2][3] * v.w,
            a.m[3][0] * v.x + a.m[3][1] * v.y + a.m[3][2] * v.z + a.m[3][3] * v.w};
}

inline Mat4 Mat4FromMat3(const Mat3& r) {
    Mat4 o;
    for (int i = 0; i < 3; ++i)
        for (int j = 0; j < 3; ++j) o.m[i][j] = r.m[i][j];
    return o;
}

inline Mat4 Translation(const Vec3& t) {
    Mat4 o;
    o.m[0][3] = t.x; o.m[1][3] = t.y; o.m[2][3] = t.z;
    return o;
}

// General 4x4 inverse by Gauss-Jordan with partial pivoting. Deliberately not the
// affine shortcut: a projection matrix is NOT affine, and A3 inverts one.
inline Mat4 Inverse(const Mat4& src) {
    double a[4][8] = {};
    for (int i = 0; i < 4; ++i) {
        for (int j = 0; j < 4; ++j) a[i][j] = src.m[i][j];
        a[i][4 + i] = 1.0;
    }
    for (int col = 0; col < 4; ++col) {
        int piv = col;
        for (int r = col + 1; r < 4; ++r)
            if (std::fabs(a[r][col]) > std::fabs(a[piv][col])) piv = r;
        if (std::fabs(a[piv][col]) < 1e-20) return Mat4{};   // singular: identity, and the caller's test fails
        if (piv != col)
            for (int j = 0; j < 8; ++j) { const double t = a[col][j]; a[col][j] = a[piv][j]; a[piv][j] = t; }
        const double inv = 1.0 / a[col][col];
        for (int j = 0; j < 8; ++j) a[col][j] *= inv;
        for (int r = 0; r < 4; ++r) {
            if (r == col) continue;
            const double f = a[r][col];
            if (f == 0.0) continue;
            for (int j = 0; j < 8; ++j) a[r][j] -= f * a[col][j];
        }
    }
    Mat4 o;
    for (int i = 0; i < 4; ++i)
        for (int j = 0; j < 4; ++j) o.m[i][j] = static_cast<float>(a[i][4 + j]);
    return o;
}

// ------------------------------------------------------------------ quaternion

struct Quat {
    float w = 1, x = 0, y = 0, z = 0;
};

inline Quat QuatMul(const Quat& a, const Quat& b) {
    return {a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
            a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
            a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
            a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w};
}

inline Quat Normalize(const Quat& q) {
    const float len = std::sqrt(q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z);
    if (len < 1e-20f) return Quat{};
    return {q.w / len, q.x / len, q.y / len, q.z / len};
}

inline Quat QuatFromAxisAngle(const Vec3& axis, float radians) {
    const Vec3 a = Normalize(axis);
    const float h = radians * 0.5f;
    const float s = std::sin(h);
    return {std::cos(h), a.x * s, a.y * s, a.z * s};
}

// Intrinsic X then Y then Z, applied in that order. The ORDER is a convention;
// what matters for the tests is that it is the same one on both sides.
inline Quat QuatFromEuler(float ax, float ay, float az) {
    const Quat qx = QuatFromAxisAngle({1, 0, 0}, ax);
    const Quat qy = QuatFromAxisAngle({0, 1, 0}, ay);
    const Quat qz = QuatFromAxisAngle({0, 0, 1}, az);
    return Normalize(QuatMul(qz, QuatMul(qy, qx)));
}

// ------------------------------------------------------------------ pose

struct Pose {
    Quat orientation{};
    Vec3 position{};
};

// ------------------------------------------------------------------ comparison

inline bool Near(float a, float b, float eps) { return std::fabs(a - b) <= eps; }

inline bool Near(const Vec3& a, const Vec3& b, float eps) {
    return Near(a.x, b.x, eps) && Near(a.y, b.y, eps) && Near(a.z, b.z, eps);
}

// ------------------------------------------------------------------ deterministic randomness
//
// Seeded, not std::rand: a failing case must reproduce exactly, on every machine.
class Rng {
public:
    explicit Rng(uint32_t seed) : s_(seed ? seed : 0x9E3779B9u) {}
    uint32_t NextU32() {
        s_ ^= s_ << 13; s_ ^= s_ >> 17; s_ ^= s_ << 5;   // xorshift32
        return s_;
    }
    float NextFloat() { return static_cast<float>(NextU32() >> 8) / 16777216.0f; }
    float NextSigned() { return NextFloat() * 2.0f - 1.0f; }
private:
    uint32_t s_;
};

inline Vec3 RandomUnitVec(uint32_t seed) {
    Rng rng(seed * 2654435761u + 1u);
    for (int i = 0; i < 64; ++i) {
        const Vec3 v{rng.NextSigned(), rng.NextSigned(), rng.NextSigned()};
        const float len = Length(v);
        if (len > 1e-3f && len <= 1.0f) return v / len;
    }
    return {0, 0, 1};
}

inline Quat RandomUnitQuat(uint32_t seed) {
    Rng rng(seed * 40503u + 7u);
    for (int i = 0; i < 64; ++i) {
        const Quat q{rng.NextSigned(), rng.NextSigned(), rng.NextSigned(), rng.NextSigned()};
        const float len = std::sqrt(q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z);
        if (len > 1e-3f && len <= 1.0f) return {q.w / len, q.x / len, q.y / len, q.z / len};
    }
    return Quat{};
}

}  // namespace vrref
