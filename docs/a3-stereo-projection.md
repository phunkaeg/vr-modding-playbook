# A3 · Stereo Projection & Validation — reference code

!!! note "This code is compiled and tested"
    Every function below also lives in the repository's `reference/` directory as real,
    building C++ — `reference/include/vrref/` for the code, `reference/tests/` for the
    tests — and `tools/verify.py` runs them. Until it was compiled this was pseudocode,
    and compiling it found three genuine defects. Read the appendix for the reasoning;
    take the version something has actually executed from `reference/`.

    **Correction found by that first compile:** `ProjectionResidual` divides the candidate
    out on the **left** (`Inverse(P) * wvp`) in the column-vector convention used
    throughout this appendix. The row-vector form — which is how a D3D9 shader constant
    usually arrives — is the transpose, `wvp * Inverse(P)`. Getting it backwards makes the
    residual meaningless rather than merely wrong, because the product is not affine for
    *any* candidate. See `ResidualFindsTheTrueProjection`.

Everything on this page exists because two projects shipped a plausible-looking projection and only found
out later. The maths is short. **The validation is the part with teeth**, and §A3.4 is the single most
load-bearing section in this appendix.

Prose: [09](09-d3d11-openxr-injection.md) and [10](10-graphics-apis.md).

---

## A3.1 Per-eye projection from the runtime's four angles

OpenXR hands you `XrFovf { angleLeft, angleRight, angleUp, angleDown }` — four **signed** angles from the
view axis, in radians, and **they are not symmetric.** A single FOV-plus-aspect pair cannot represent
them, which is why chapter 09 tells you to check how your engine stores its frustum before assuming you
must rebuild the pipeline.

```cpp
struct FrustumTangents { float l, r, u, d, width, height; };

FrustumTangents TangentsFromFov(const XrFovf& fov) {
    FrustumTangents t;
    t.l = tanf(fov.angleLeft);      // typically negative
    t.r = tanf(fov.angleRight);
    t.u = tanf(fov.angleUp);
    t.d = tanf(fov.angleDown);      // typically negative
    t.width  = t.r - t.l;
    t.height = t.u - t.d;
    return t;
}
```

The two entries people get wrong are the **off-centre** ones — with a symmetric frustum they are zero, so
a bug here is invisible until you use a real headset:

```
x-scale  =  2 / width          x-offset  =  (r + l) / width
y-scale  =  2 / height         y-offset  =  (u + d) / height
```

**The depth row is where conventions bite**, and I am deliberately not giving you one to paste:
D3D uses `z_ndc ∈ [0,1]`, OpenGL `[-1,1]`; reversed-Z flips near and far; row-vector engines transpose the
whole thing. Take your engine's *existing* projection builder and change only the four scale/offset terms
above, leaving its depth row untouched. Then prove it with §A3.2 — which is cheaper and more reliable than
reasoning about which convention you are in.

## A3.2 Prove a projection by where it puts known points

Do not eyeball a matrix. Push points through it whose answers you already know.

```cpp
// A correct projection maps the frustum's own corners to the NDC box edges, by construction.
void TestProjectionMapsFrustumCorners(const Mat4& P, const FrustumTangents& t,
                                      float nearZ, float farZ) {
    // A point on the LEFT plane at distance `nearZ` must land at NDC x = -1.
    const Vec3 onLeft { t.l * nearZ, 0.0f, -nearZ };      // -Z forward; flip if yours is +Z
    const Vec4 clip = P * Vec4{ onLeft, 1.0f };
    CHECK(fabsf(clip.x / clip.w + 1.0f) < 1e-4f);

    const Vec3 onRight{ t.r * nearZ, 0.0f, -nearZ };
    const Vec4 cr = P * Vec4{ onRight, 1.0f };
    CHECK(fabsf(cr.x / cr.w - 1.0f) < 1e-4f);

    // Centre of the frustum is NOT NDC x=0 under an asymmetric FOV -- assert the asymmetry
    // is actually present, or a symmetric bug passes silently.
    const Vec4 cc = P * Vec4{ 0.0f, 0.0f, -nearZ, 1.0f };
    const float expected = -(t.r + t.l) / t.width;
    CHECK(fabsf(cc.x / cc.w - expected) < 1e-4f);
}
```

That last assertion is the one that matters. Without it, a projection that silently symmetrises passes
every other check — and symmetrising is the most common way to "fix" an asymmetric frustum that looked
wrong.

## A3.3 The eye transform: conjugate through the projection

A constant horizontal shift in clip space gives two displaced flat images. It **cannot** produce
depth-varying parallax, because it is by construction independent of `z`. BioshockVR shipped
`clip.x += eyeShift * clip.w` before replacing it with the conjugated form.

```cpp
// Column-vector (v' = M * v). Row-vector engines reverse every product below.
//   M_eye = P_eye * T_eye * inverse(P_center)
// applied to an already-combined WVP:
Mat4 EyeAdjustedWVP(const Mat4& wvpCenter, const Mat4& pCenter,
                    const Mat4& pEye, const Mat4& tEyeViewSpace) {
    return pEye * tEyeViewSpace * Inverse(pCenter) * wvpCenter;
}
```

`tEyeViewSpace` is a pure translation of ±IPD/2 **in view space**, scaled to world units — see
[09](09-d3d11-openxr-injection.md) on deriving world scale before you trust it.

**Do not guess row versus column.** The residual in §A3.4 tells you empirically: build it both ways, score
both, and the correct convention scores near zero while the other does not. FarCry2-VR settled exactly
this question that way — column residual `0.000031`, translation in the last row — instead of assuming.

## A3.4 The residual gate — and why the obvious one is blind

**This section is a correction to advice this playbook previously gave.** The natural validation is: if
`P_center` is right, then `WVP · P_center⁻¹` should come out **affine** (it is world × view). That check
is real, and it is **mathematically incapable of detecting a wrong FOV.**

FarCry2-VR measured it: a deliberately guessed 75° FOV scored **0.000031 — identical to correct.** The
reason is structural. FOV and aspect live in the *scale* terms of the projection; the affine test reads
the *projective* row. They never touch.

The fix is a second term. A correct `P_center⁻¹` leaves an upper-3×3 that is a rotation times a **uniform**
scale; a wrong FOV rescales it **non-uniformly**, which orthonormality detects and affinity does not.

```cpp
// Two independent terms. The first alone will pass a wrong FOV.
float ProjectionResidual(const Mat4& wvp, const Mat4& pCenterCandidate) {
    const Mat4 A = wvp * Inverse(pCenterCandidate);     // expected: world * view, i.e. affine

    // TERM 1 -- affinity. Catches a wrong near/far and a wrong projective row.
    float affine = fabsf(A.m[3][0]) + fabsf(A.m[3][1]) + fabsf(A.m[3][2])
                 + fabsf(A.m[3][3] - 1.0f);

    // TERM 2 -- orthonormality of the upper 3x3 after dividing out uniform scale.
    // THIS is the term that sees a wrong FOV.
    Vec3 c0 = Column3(A,0), c1 = Column3(A,1), c2 = Column3(A,2);
    const float s = (Length(c0) + Length(c1) + Length(c2)) / 3.0f;   // uniform scale is legitimate
    if (s < 1e-6f) return 1e9f;
    c0 = c0 / s; c1 = c1 / s; c2 = c2 / s;

    float ortho = fabsf(Length(c0) - 1.0f) + fabsf(Length(c1) - 1.0f) + fabsf(Length(c2) - 1.0f)
                + fabsf(Dot(c0,c1)) + fabsf(Dot(c0,c2)) + fabsf(Dot(c1,c2));

    return affine + ortho;
}
```

### Derive your own threshold. Never import one.

FarCry2-VR imported BioshockVR's `1.0` and got **a gate looser than no gate at all**, because the two
metrics are scaled differently — the normalised term above is bounded near 1, so every wrong case still
scored under it. Their measured separation:

| case | residual |
|---|---|
| correct | 0.000031 |
| 5° FOV error | 0.094 |
| wrong aspect | 0.216 |
| **guessed 75° FOV** | **0.250** |
| wrong near/far | 0.800 |

Threshold derived from the gap: **0.01** — roughly 300× above correct, 9× below the tightest wrong case.

```cpp
// Build the table FIRST. Assert every wrong case fails, so raising the threshold later
// breaks a test instead of quietly weakening the gate.
void TestResidualSeparates() {
    const Mat4 correct = BuildProjection(kFovTruth, kNear, kFar);
    CHECK(ProjectionResidual(kKnownWVP, correct) < 0.01f);

    struct Wrong { const char* name; Mat4 p; };
    const Wrong wrong[] = {
        { "5 degree FOV error", BuildProjection(FovOffsetDeg(kFovTruth, 5.0f), kNear, kFar) },
        { "wrong aspect",       BuildProjection(FovWithAspect(kFovTruth, 4.0f/3.0f), kNear, kFar) },
        { "guessed 75 deg",     BuildProjection(FovFromDegrees(75.0f), kNear, kFar) },
        { "wrong near/far",     BuildProjection(kFovTruth, kNear * 4.0f, kFar * 0.5f) },
    };
    for (const auto& w : wrong)
        CHECK_MSG(ProjectionResidual(kKnownWVP, w.p) > 0.01f, w.name);
}
```

**Three rules, in order.** Build the wrong-input table before you pick a number. Confirm the metric
*separates* them at all — if a wrong input scores like a correct one, the metric is blind and no threshold
saves it. Then derive the threshold from your own gap. **A residual limit is a property of a metric, not
of a problem.**

## A3.5 Linearise depth before deriving disparity

Hardware depth is non-linear. Computing per-eye disparity or distance weights straight from the buffer
concentrates the entire effect in the near field — BioshockVR hit this twice.

```cpp
// D3D-style depth in [0,1], standard (not reversed) Z.
inline float LinearizeDepth01(float d, float nearZ, float farZ) {
    return (nearZ * farZ) / (farZ - d * (farZ - nearZ));
}

// Reversed-Z (1 at the near plane) -- increasingly the default, check before assuming.
inline float LinearizeDepthReversed(float d, float nearZ, float farZ) {
    return LinearizeDepth01(1.0f - d, nearZ, farZ);
}

// OpenGL NDC z in [-1,1]: rescale first, then use the [0,1] form.
inline float LinearizeDepthGL(float zNdc, float nearZ, float farZ) {
    return LinearizeDepth01((zNdc + 1.0f) * 0.5f, nearZ, farZ);
}
```

```cpp
void TestLinearizeEndpoints() {
    CHECK(fabsf(LinearizeDepth01(0.0f, 0.05f, 1000.0f) -   0.05f) < 1e-4f);   // near plane
    CHECK(fabsf(LinearizeDepth01(1.0f, 0.05f, 1000.0f) - 1000.0f) < 1e-1f);   // far plane
    // Mid-buffer is NOT mid-distance -- if this passes, you are not actually linearising.
    CHECK(LinearizeDepth01(0.5f, 0.05f, 1000.0f) < 1.0f);
}
```

That last assertion is the point of the section: at `d = 0.5` the true distance is about **0.1 m**, not
500 m. Anything treating the raw buffer as distance is wrong by three orders of magnitude in the middle of
its range.

---

**Related prose:** [09 · Stereo math: translate in view space](09-d3d11-openxr-injection.md) ·
[09 · FoV, aspect, and full-eye presentation](09-d3d11-openxr-injection.md) ·
[11 · Validate a discovery by provenance, not by hope](11-re-anchoring-and-discovery.md) ·
[10 · D3D9 and D3D10](10-graphics-apis.md)
