# A5 · Flat Harness & Noise-Floor Statistics — reference code

!!! note "This code is compiled and tested"
    Every function below also lives in the repository's `reference/` directory as real,
    building C++ — `reference/include/vrref/` for the code, `reference/tests/` for the
    tests — and `tools/verify.py` runs them. Until it was compiled this was pseudocode,
    and compiling it found three genuine defects. Read the appendix for the reasoning;
    take the version something has actually executed from `reference/`.

    **Partial by design.** Signature scanning, trampoline disassembly, guarded reads and
    the file/PNG plumbing need a target process and are not covered; the *decision logic*
    they wrap is. `reference/README.md` states the boundary exactly.

A flat harness answers *"did this change the image?"* without a human or a headset. That answer is
worthless until you know what the **unchanged** case scores — and measuring that is a real experiment
with four documented ways to get it wrong ([08](08-project-process.md)).

Two projects built one independently, and between them hit all four. This page is the arithmetic.

---

## A5.1 First: prove your capture actually contains the 3D scene

Swat4-VR's `PrintWindow` captures were ~8 % non-black, completely static, and produced **eleven
exactly-zero diffs**. A 0.0000 floor is not a quiet scene — it is *no scene* — and it would have made
every later diff read as "changed."

```python
def capture_sanity(img_a, img_b):
    """Run ONCE when you build the harness. A zero floor is a red flag, not a green one."""
    nonblack = fraction_nonblack(img_a)
    if nonblack < 0.30:
        raise HarnessError(
            f"only {nonblack:.0%} of the capture is non-black -- you are probably capturing the "
            f"GDI/UI layer, not the 3D scene. Capture from inside the engine instead.")

    # Two captures of a MOVING scene must differ. If they don't, you are capturing a static layer.
    if mean_abs_diff(img_a, img_b) == 0.0:
        raise HarnessError(
            "two captures during motion are byte-identical -- the capture path does not contain "
            "the renderer's output.")
```

**Capturing from inside the engine sidesteps the whole class.** Swat4-VR uses the game's own `Shot`
console command; FarCry2-VR drives its own in-process dump. Either beats an OS-level window grab.

## A5.2 The naive statistic is actively harmful on a bimodal sample

Your measurement pairs are a *mixture*: genuinely-quiet frames, plus frames where something moved.
Swat4-VR's mean + 3σ over that mixture gave a threshold of **47.26** — which would have hidden every real
change while looking rigorous. Their true quiet floor is 0.25–0.58 and real changes read 13.6–15.8.

Use median and MAD, fit to the **quiet population only**, and list what you excluded.

```python
import statistics

MAD_TO_SIGMA = 1.4826          # makes MAD a consistent estimator of sigma for normal data

def robust_floor(samples, k_outlier=3.0, k_threshold=6.0):
    """
    samples: mean-abs-diff values from pairs you BELIEVE are quiet.
    Returns (threshold, quiet, excluded). Never silently drops the excluded ones.
    """
    if len(samples) < 5:
        raise HarnessError(f"need >=5 samples to estimate a floor, got {len(samples)}")

    med = statistics.median(samples)
    mad = statistics.median([abs(s - med) for s in samples]) * MAD_TO_SIGMA
    if mad == 0.0:
        # Every sample identical. Either a perfectly static scene or -- far more likely -- A5.1.
        raise HarnessError("MAD is zero; re-check the capture path before trusting this floor")

    quiet    = [s for s in samples if abs(s - med) <= k_outlier * mad]
    excluded = [s for s in samples if abs(s - med) >  k_outlier * mad]

    q_med = statistics.median(quiet)
    q_mad = statistics.median([abs(s - q_med) for s in quiet]) * MAD_TO_SIGMA
    threshold = q_med + k_threshold * q_mad

    return threshold, quiet, excluded


def report_floor(samples):
    threshold, quiet, excluded = robust_floor(samples)
    print(f"quiet population : n={len(quiet)}  median={statistics.median(quiet):.4f}  "
          f"min={min(quiet):.4f} max={max(quiet):.4f}")
    print(f"threshold        : {threshold:.4f}")
    if excluded:
        # LIST them. Silently dropping outliers is how the mixture problem hides.
        print(f"EXCLUDED as motion pairs ({len(excluded)}): "
              + ", ".join(f"{s:.4f}" for s in sorted(excluded)))
    return threshold
```

## A5.3 There may be no single floor for the target

FarCry2-VR measured **0.1285** in a still scene and **6.79 mean / 8.85 max** in a busy one — high enough
to swallow a real change. Their delay sweep was non-monotonic (0 ms → 2.24, 700 ms → 12.98, 2000 ms →
5.10), the signature of periodic content: fire flicker, cloud shadows, a ~30 s weapon idle.

**A floor is a property of a scene, not of a game.** Capture a control pair in the same scene,
immediately before the treatment.

```python
def measure(scene, treatment_fn, capture_fn, delay_s=0.3):
    """Control and treatment in the same scene, seconds apart. Never compare against a
       number measured earlier, elsewhere, or by another project."""
    a1 = capture_fn(); sleep(delay_s); a2 = capture_fn()
    control = mean_abs_diff(a1, a2)                      # this scene, right now

    treatment_fn()
    b1 = capture_fn(); sleep(delay_s); b2 = capture_fn()
    treated = mean_abs_diff(b1, b2)

    return {
        "control":    control,
        "treatment":  treated,
        "separation": (treated / control) if control > 0 else float("inf"),
    }
```

**Report separation, not the floor.** The number that licenses a conclusion is the ratio — FarCry2-VR's
control 0.1285 vs treatment 23.5611 is **183×**, and that is the sentence worth writing down.

## A5.4 The control that can veto the verdict

Swat4-VR's addition, and the sharpest idea on this page. If the *mechanism* you use to run the experiment
can itself move the pixels, then a positive result proves nothing either — and positives are the ones
nobody re-examines.

Their scene-re-entry proof doubles the scene draw and yaws the second pass. But a double-advancing
once-per-frame packet ([14](14-render-pass-hazard-atlas.md)) would move pixels *without any camera
change*. The control is: **double the draw with no yaw.**

```python
def run_b1(harness):
    """Three captures. The control is read FIRST and can refuse the whole verdict."""
    a = harness.capture(double=False, yaw=0)      # A  stock
    b = harness.capture(double=True,  yaw=0)      # B  CONTROL: mechanism on, treatment off
    c = harness.capture(double=True,  yaw=30)     # C  treatment

    floor = harness.threshold

    # Read B before anything else.
    if mean_abs_diff(a, b) > floor:
        return Verdict.CONFOUNDED, (
            "doubling the draw alone moved pixels -- the mechanism is a second variable. "
            "A->C cannot be reported as a verdict at any magnitude.")

    delta = mean_abs_diff(a, c)
    return (Verdict.PASS if delta > floor else Verdict.NULL), delta
```

Two things generalise beyond this experiment:

- **Make the confound expressible.** Swat4-VR could not run this control at first, because `yaw != 0` was
  *also* the arm switch — "double without yawing" was not a state the harness could reach. That is a
  design bug in the harness, not a limitation of the experiment. Split your levers.
- **The control gates the verdict.** A control read *afterwards* gets rationalised; one that can return
  `CONFOUNDED` cannot.

## A5.5 Two capture traps worth paying for once

```python
# 1. DPI. A 1920x1080 window measures 1536x864 at 125% scaling -- silently, and every diff is then
#    comparing resampled images. Do this before creating any window.
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2)      # PROCESS_PER_MONITOR_DPI_AWARE

def assert_capture_size(img, expected_w, expected_h):
    if img.width != expected_w or img.height != expected_h:
        raise HarnessError(
            f"capture is {img.width}x{img.height}, expected {expected_w}x{expected_h} -- "
            f"DPI virtualisation. Fix awareness before measuring anything.")

# 2. Captures are NOT frame-synchronised. Even a zero-delay pair differs by ~2.2 in a moving scene,
#    so a single pair is never evidence. Take N and use the median.
def stable_diff(capture_fn, n=5, delay_s=0.3):
    diffs = []
    prev = capture_fn()
    for _ in range(n):
        sleep(delay_s)
        cur = capture_fn()
        diffs.append(mean_abs_diff(prev, cur))
        prev = cur
    return statistics.median(diffs)
```

## A5.6 The command seam

The whole loop needs a channel into the running mod that requires no hotkey and no window focus.
Chapter [08](08-project-process.md): **a plain text file the injected DLL polls once a second is enough.**
No console, no IPC library, and scriptable from anything.

```cpp
// In the mod: poll once a second on a worker, execute on the game thread.
void PollCommandFile() {
    const auto mtime = LastWriteTime(kCommandPath);
    if (mtime == g_lastSeen) return;
    g_lastSeen = mtime;

    for (const std::string& line : ReadAllLines(kCommandPath))
        QueueToGameThread([line] { ExecuteCommand(line); });   // never execute on the poll thread

    // Ack so the driver knows the command was consumed, not just written.
    WriteFile(kAckPath, std::to_string(++g_ackCounter));
}
```

**Write an ack file.** Without it the harness cannot distinguish "the command ran" from "the mod is dead,"
and you are back to inferring from pixels — which is exactly what you built the harness to stop doing.

## A5.7 Burst capture for alternate-eye rendering

A single captured frame from an alternate-eye renderer is **arbitrary** — you cannot tell which eye it is,
which phase of the pair it landed on, or whether alternation happened at all
([06](06-debugging-methodology.md)). Capture a *sequence*, armed by a hotkey so the disk survives.

```cpp
// Ring buffer of N frames, armed on demand, self-terminating. 90 Hz x forever fills a disk in
// minutes AND changes the timing you are measuring -- so this must be armed, not always-on.
class BurstCapture {
    static constexpr int kFrames = 12;     // ~6 pairs: enough to see the pattern, not a video

    std::atomic<bool> armed_{false};
    int   remaining_ = 0;
    int   seq_       = 0;
    int   burstId_   = 0;

public:
    // Call from ONE place. Mirror the arm to every capture stage (see below).
    void Arm() { armed_.store(true, std::memory_order_release); }

    // Called at your present/submit seam, once per rendered eye.
    void OnFrame(const EyeImage& img, EyeIndex believedEye,
                 uint64_t engineFrameIndex, const Pose& pose) {
        if (armed_.exchange(false, std::memory_order_acq_rel)) {
            remaining_ = kFrames; seq_ = 0; ++burstId_;
        }
        if (remaining_ <= 0) return;

        // Everything you cannot reconstruct later goes in the FILENAME. The directory
        // listing then IS the analysis -- no tooling required to read the pattern.
        char name[256];
        snprintf(name, sizeof name,
                 "burst%02d_seq%02d_eye%c_frame%llu_posY%+.4f.png",
                 burstId_, seq_, (believedEye == EyeIndex::Left ? 'L' : 'R'),
                 (unsigned long long)engineFrameIndex, pose.position.y);
        WritePng(name, img);

        ++seq_; --remaining_;
    }
};
```

**Read the resulting listing as a sequence, not as images.** The pattern is the data:

```
burst03_seq00_eyeL_frame184213_posY+0.0312.png
burst03_seq01_eyeR_frame184213_posY+0.0312.png   <- same frame index => a genuine pair
burst03_seq02_eyeL_frame184214_posY+0.0324.png
burst03_seq03_eyeR_frame184214_posY+0.0324.png
```

- `L,R,L,R` with **frame indices pairing up** — alternation is working.
- `L,L,R,R`, or a frame index that advances between the two eyes of a "pair" — your eye phase and the
  engine's frame boundary disagree.
- The eye letter records **what your code believed it was rendering.** When the images contradict it, you
  have found an eye-phase *attribution* bug, not a rendering bug — and those are very different fixes.

**Arm every stage from one signal.** Independent hotkey polls on different stages will disagree about a
short press, and you get a burst from one and nothing from the other — the exact defect BioshockVR's
`dumpsync` build exists to fix.

```cpp
// One poller, many consumers. Never let each stage poll the key itself.
void PollCaptureHotkey() {
    if (!RisingEdge(VK_F9)) return;
    g_drawStreamBurst.Arm();
    g_privateEyeBurst.Arm();
    g_xrBlitBurst.Arm();        // add a stage, add a line -- and it stays in sync by construction
}
```

**Budget it like any other diagnostic.** `kFrames` is a hard cap and the burst ends itself; there is no
"stop capturing" key to forget. Log the burst id and frame count in the summary so a burst that produced
fewer files than expected is visible rather than silently short.

---

**Related prose:** [06 · Your capture is phase-locked to your own stereo pair](06-debugging-methodology.md) ·
[08 · Your pixel-diff threshold is an experiment, not a constant](08-project-process.md) ·
[08 · Two gates per milestone](08-project-process.md) ·
[06 · An isolation gate is itself a second variable](06-debugging-methodology.md) ·
[13 · A closed-loop flat-screen test harness](13-teardown-bioshock-vr.md)
