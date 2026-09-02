# A1 · Rotation, Frames & Angles — reference code

!!! note "This code is compiled and tested"
    Every function below also lives in the repository's `reference/` directory as real,
    building C++ — `reference/include/vrref/` for the code, `reference/tests/` for the
    tests — and `tools/verify.py` runs them. Until it was compiled this was pseudocode,
    and compiling it found three genuine defects. Read the appendix for the reasoning;
    take the version something has actually executed from `reference/`.

Chapter [02](02-viewmodels-and-hands.md) says reference-frame and Euler maths is *"usually the single
largest time sink."* This page is the implementation half: the shapes that are correct, the traps they
avoid, and — more importantly — **the tests that catch you getting them wrong.**

> **Read this first.** Every convention below (handedness, row vs column vectors, axis order) is stated
> explicitly, and **your engine's may differ**. Do not paste and hope. Paste, then run the tests in
> §A1.6 — they are written to *fail loudly* on a convention mismatch, which is what you want on day one
> rather than at 180° of roll three weeks later.
>
> Conventions here unless a snippet says otherwise: **right-handed**, **column-vector** (`v' = M * v`),
> quaternion `(w, x, y, z)`, **unit length**.

---

## A1.1 Quaternion → matrix, and the typo that survives review

This is the function SOMAVR shipped with `2*y*y` where `2*x*y` was required. The error is proportional to
angle — identity looks perfect, and the skew only appears where testers stop looking.

```cpp
struct Quat { float w, x, y, z; };      // unit length
struct Mat3 { float m[3][3]; };         // column-vector: v' = M * v

Mat3 QuatToMat3(const Quat& q) {
    const float xx = q.x*q.x, yy = q.y*q.y, zz = q.z*q.z;
    const float xy = q.x*q.y, xz = q.x*q.z, yz = q.y*q.z;
    const float wx = q.w*q.x, wy = q.w*q.y, wz = q.w*q.z;

    Mat3 r;
    r.m[0][0] = 1.0f - 2.0f*(yy + zz);
    r.m[0][1] =        2.0f*(xy - wz);   // xy, NOT yy. This is the one.
    r.m[0][2] =        2.0f*(xz + wy);

    r.m[1][0] =        2.0f*(xy + wz);   // xy again, opposite sign on wz
    r.m[1][1] = 1.0f - 2.0f*(xx + zz);
    r.m[1][2] =        2.0f*(yz - wx);

    r.m[2][0] =        2.0f*(xz - wy);
    r.m[2][1] =        2.0f*(yz + wx);
    r.m[2][2] = 1.0f - 2.0f*(xx + yy);
    return r;
}
```

**Why the typo survives review:** the products are two-letter locals differing by one character, and the
matrix is visually symmetric enough that a wrong term looks plausible. Naming the nine products up front,
as above, rather than inlining `2.0f*q.x*q.y` at each site, is most of the defence.

## A1.2 The independent cross-check that catches it

Rotate a vector *directly by the quaternion*, no matrix involved, and compare. Two implementations of one
rotation must agree; a typo in one is not mirrored in the other.

```cpp
// v' = v + 2w(qv x v) + 2(qv x (qv x v))   -- no matrix, no shared code path
Vec3 RotateByQuat(const Quat& q, const Vec3& v) {
    const Vec3 qv{ q.x, q.y, q.z };
    const Vec3 t = Cross(qv, v) * 2.0f;
    return v + t * q.w + Cross(qv, t);
}
```

That is the whole fix SOMAVR shipped: **assert the matrix path and the direct path agree** across many
random rotations and vectors. See §A1.6.

## A1.3 Build a basis; never band-aid axes

Chapter 02's rule — *per-axis scalar calibration cannot fix a wrong frame* — in code. Given a forward
direction and an up **hint**, produce an orthonormal basis by Gram-Schmidt:

```cpp
// Right-handed. If your engine is left-handed, swap the Cross() operands in `right`;
// the handedness test in A1.6 will tell you immediately which way round you are.
Mat3 BasisFromForwardUp(Vec3 forward, Vec3 upHint) {
    const Vec3 f = Normalize(forward);

    // Degenerate: forward parallel to the hint. Pick any perpendicular axis.
    if (fabsf(Dot(f, Normalize(upHint))) > 0.9999f)
        upHint = (fabsf(f.z) < 0.9f) ? Vec3{0,0,1} : Vec3{1,0,0};

    const Vec3 r = Normalize(Cross(upHint, f));   // right
    const Vec3 u = Cross(f, r);                   // already unit
    return Mat3FromColumns(r, u, f);
}
```

**The degenerate branch is not optional.** Look straight up or down and `Cross(upHint, f)` collapses to
zero; without the guard you normalise a zero vector and NaNs propagate into the pose. It presents as
"tracking randomly explodes when I look up," which is not a phrase that makes you think about
Gram-Schmidt.

## A1.4 Roll from the up-vector, not from Euler decomposition

Chapter 02: *compute bank from the controller's up vector projected off the forward axis, not from Euler
decomposition* — because inverse-cos heading plus bank correction blows up near ±90° pitch. Signed, and
with no singularity in the usable range:

```cpp
// Signed roll of `up` about `forward`, measured from `referenceUp`. Radians, (-pi, pi].
float RollAboutAxis(const Vec3& forward, const Vec3& up, const Vec3& referenceUp) {
    const Vec3 f = Normalize(forward);
    const Vec3 a = Normalize(up          - f * Dot(up,          f));  // into the plane
    const Vec3 b = Normalize(referenceUp - f * Dot(referenceUp, f));  // perpendicular to f
    return atan2f(Dot(Cross(b, a), f), Dot(b, a));                    // signed; no acos, no gimbal
}
```

`atan2(cross·axis, dot)` is the standard signed-angle-in-a-plane idiom. Well-conditioned everywhere the
projection is non-degenerate — i.e. everywhere except `up` parallel to `forward`.

## A1.5 Fixed-width integer angles (Unreal rotators and friends)

DishonoredVR shipped `pitch += / yaw += / roll +=` against a UE3 rotator — correct only for its
single-axis test, and missing the wrap. Integer angle units are **not** floats, and **per-axis addition
is not rotation composition.**

```cpp
constexpr int32_t kRotUnitsPerTurn = 65536;   // UE1-3 FRotator. Verify for your engine.
constexpr float   kRotToRad = 6.28318530718f / kRotUnitsPerTurn;

inline int32_t WrapRot(int32_t r)  { return r & (kRotUnitsPerTurn - 1); }  // power-of-two only
inline float   RotToRad(int32_t r) { return WrapRot(r) * kRotToRad; }
inline int32_t RadToRot(float rad) { return WrapRot((int32_t)lroundf(rad / kRotToRad)); }
```

**And then do not add them.** To combine an engine rotator with a tracked rotation:

```cpp
// RIGHT: convert out, compose as rotations, convert back.
Rotator ComposeWithTracked(const Rotator& engine, const Quat& trackedDelta) {
    const Quat base = QuatFromRotator(engine);   // your engine's axis ORDER matters here
    return RotatorFromQuat(Normalize(QuatMul(trackedDelta, base)));
}

// WRONG -- and it passes a yaw-only test:
//   out.Yaw = engine.Yaw + delta.Yaw;   out.Pitch = ...
```

**Operand order is the other half.** `QuatMul(trackedDelta, base)` applies the authored base *first*,
then the live delta — chapter 02's "authored offset is the baseline, not an overlay." Swap the operands
and you get a persistent quarter-turn that no amount of sign-flipping will fix, because the sign was
never the problem.

## A1.5b The difference of two wrapped angles must itself be wrapped {#angle-difference}

The single most expensive one-line rotation bug in this survey, and it hides behind a comment claiming
the opposite. `[SOURCE]`

```cpp
int32_t delta = camYaw - ctlYaw;     // WRONG on a wrapping integer rotator
```

**Subtracting two values that live on a circle gives you a number that does not.** UE3 uses 65536 units
per turn, so two headings **0.3 degrees apart** can differ by **65590 units - which reads as 360.3
degrees.** Singularity VR had this at two sites, and:

> **Both carried a comment claiming `// wraps correctly`.**

The consequences were not cosmetic. Their camera-ownership test used a 15-degree threshold, so every
false reading handed the camera to the game and re-anchored the base yaw - *"yanking the view somewhere
the player was not looking."* One 8,476-line run:

```
camera handed to the GAME (360.3 deg from the pawn)     x20
view drift  +358.4 / +359.9 / +360.0 / -359.8 / -360.3 deg
```

**Every one of those is ~0 degrees misread as a full turn**, which is also the diagnostic signature:
**a log full of values just under +/-360 is a wrap bug, not a spinning camera.** After the fix, under
heavy turning at full stick deflection, the same conditions produced **0 handoffs**.

The fix is to wrap the difference, not the operands:

```cpp
int32_t delta = WrapRotSigned(camYaw - ctlYaw);   // -32768 .. +32767
```

and the same applies in radians - `atan2(sin(a - b), cos(a - b))` rather than `a - b`. **Any comparison
against an angular threshold needs the wrapped difference**, because the unwrapped one is unbounded and
every threshold test on it is wrong near the seam.

## A1.6 The tests — this is the part that saves you

Everything above is ordinary maths. **The tests are the deliverable.** They are pure: no game, no headset,
no engine. They belong in whatever desk-test target you already have
([08](08-project-process.md)).

```cpp
// 1. ORTHONORMALITY -- unit columns, mutually perpendicular, determinant +1.
//    A determinant of -1 is a reflection: you flipped a cross product somewhere.
void AssertRotationMatrix(const Mat3& m, float eps = 1e-5f) {
    const Vec3 c0 = Column(m,0), c1 = Column(m,1), c2 = Column(m,2);
    CHECK(fabsf(Length(c0) - 1.0f) < eps);
    CHECK(fabsf(Length(c1) - 1.0f) < eps);
    CHECK(fabsf(Length(c2) - 1.0f) < eps);
    CHECK(fabsf(Dot(c0, c1)) < eps);
    CHECK(fabsf(Dot(c0, c2)) < eps);
    CHECK(fabsf(Dot(c1, c2)) < eps);
    CHECK(fabsf(Determinant(m) - 1.0f) < eps);
}

// 2. TWO INDEPENDENT PATHS AGREE -- catches the A1.1 typo class outright.
void TestQuatMatrixAgreement() {
    for (int i = 0; i < 1000; ++i) {
        const Quat q = RandomUnitQuat(i);        // seeded: a failure must reproduce
        const Mat3 m = QuatToMat3(q);
        AssertRotationMatrix(m);
        for (int j = 0; j < 8; ++j) {
            const Vec3 v = RandomUnitVec(i*8 + j);
            CHECK(Near(m * v, RotateByQuat(q, v), 1e-4f));
        }
    }
}

// 3. EXTREME ANGLES, EXPLICITLY. The typo class is invisible near identity by construction,
//    so a suite that only samples gentle rotations PASSES ON BROKEN CODE.
void TestExtremeAngles() {
    const float a[] = { 0.0f, 0.5f, 1.0f, 2.0f, 3.0f, 3.14159f, -3.14159f };
    for (float ax : a) for (float ay : a) for (float az : a) {
        const Quat q = QuatFromEuler(ax, ay, az);
        AssertRotationMatrix(QuatToMat3(q));
        CHECK(Near(QuatToMat3(q) * Vec3{0,0,1}, RotateByQuat(q, Vec3{0,0,1}), 1e-4f));
    }
}

// 4. ROUND-TRIP the integer rotator, deliberately crossing the wrap boundary.
void TestRotatorRoundTrip() {
    for (int32_t r = -200000; r <= 200000; r += 997)
        CHECK(WrapRot(RadToRot(RotToRad(r))) == WrapRot(r));
}

// 5. HANDEDNESS, pinned once. Change engine, this test tells you.
void TestHandedness() {
    const Mat3 b = BasisFromForwardUp(Vec3{0,0,1}, Vec3{0,1,0});
    CHECK(Near(Column(b,2), Vec3{0,0,1}, 1e-5f));   // forward is column 2
    CHECK(Near(Column(b,1), Vec3{0,1,0}, 1e-5f));   // up is column 1
    CHECK(Determinant(b) > 0.0f);                   // right-handed
}
```

**If you add one test from this page, add number 3.** It is the entire reason the SOMAVR bug shipped:
error proportional to angle means a suite sampling only gentle rotations passes on broken code, and a
human eyeballing the result near neutral sees nothing wrong.

---

**Related prose:** [02 · Euler/quaternion traps](02-viewmodels-and-hands.md) ·
[02 · Authored offset or live delta](02-viewmodels-and-hands.md) ·
[11 · Classify an unknown value by its magnitude](11-re-anchoring-and-discovery.md) — integer rotators
read as floats print as denormal zeros, which looks like an empty slot.
