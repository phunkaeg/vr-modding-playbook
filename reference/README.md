# `reference/` — the appendix maths, compiled and tested

The five appendices (`docs/a1`–`a5`) carry the maths and the primitives this playbook
tells you to copy. Until now they were **read-only**: the code referenced types that
existed nowhere, so nothing in them had ever been compiled, let alone run.

This directory is that code, made real. Every function here is the function in the
appendix, and the tests are the tests the appendices describe — A1.6's five checks are
`tests/test_a1.cpp`, and the rest are the assertions the prose already claims.

## Run it

```bash
cmake -S . -B build && cmake --build build && ctest --test-dir build --output-on-failure
```

or, on Windows with VS 2022 Build Tools and no CMake:

```bash
reference\build-and-test.bat
```

Both propagate the real exit code.

`tools/verify.py` does **not** invoke a compiler — shelling out to a vcvars batch file from
there hangs, and a check that hangs is worse than no check. It runs the binary the build
produced and **fails if any source is newer than it**, naming the stale files. So a change
without a rebuild is a red line rather than a silent pass, and the check stays fast.

## What is covered, and what is not

Stating this honestly matters more than the coverage number, because "there are tests"
is the kind of claim [META-007](../docs/pattern-catalog.md#meta-007) warns about.

| Appendix | Covered | Not covered |
|---|---|---|
| **A1** rotation and frames | all of it — quaternion↔matrix, the independent rotate path, basis construction, signed roll, integer rotators, composition | — |
| **A2** pose pipeline | the seqlock channel (with a real two-thread torn-read test), the transform latch, the recentre epoch, the settle latch | nothing that needs a live runtime |
| **A3** stereo projection | tangents, asymmetric projection build, corner mapping, the eye-adjust identity, the two-term residual — plus ch14's depth-slice multiplier | recovering a projection from a *live* captured WVP |
| **A4** hook safety | the decision logic: verify-then-write and its two refusal paths, the re-entrancy depth guard, the census predicate, module-relative anchors | signature scanning, trampoline length disassembly, SEH-guarded reads, `VirtualProtect` — none testable without a target process |
| **A5** flat harness | the burst-capture state machine: armed, bounded, self-terminating, and the filename carrying the evidence | the command file, PNG writing, hotkeys — plumbing, not logic |

Memory protection in A4 is injected behind a `ProtectFn` so the *decision* is testable on
an ordinary array while the real call site stays one line.

## Conventions, fixed in one place

`include/vrref/vrmath.h` pins them, and the tests assert them:

- **column-vector**, `v' = M * v` — a row-vector engine reverses every product;
- **right-handed**, `-Z` forward, `+Y` up (OpenXR's convention);
- `Mat3`/`Mat4` stored **row-major**, `m[row][col]`.

Change them there and the tests will tell you what moved. That is the point of
`TestHandedness` being pinned rather than derived.

## Two things worth knowing before you copy from here

**The tests use a seeded RNG, not `std::rand`.** A failing case must reproduce exactly, on
every machine, or the test is a rumour.

**`ComposeWithTrackedNaive` is deliberately wrong.** A1.5 claims that adding rotator
components passes a yaw-only test and fails a general one; both halves are asserted in
`NaiveRotatorAdditionPassesYawOnlyAndFailsGeneral`, so the warning in the appendix is
evidence rather than folklore. Do not copy that function into a mod.
