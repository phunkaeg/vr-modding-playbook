# SOMAVR — RUNTIME_ANALYSIS 0.5.1-0.5.6 harvest
Files read: RUNTIME_ANALYSIS_0.5.1.md, RUNTIME_ANALYSIS_0.5.2.md, RUNTIME_ANALYSIS_0.5.3.md, RUNTIME_ANALYSIS_0.5.4.md, RUNTIME_ANALYSIS_0.5.5.md, RUNTIME_ANALYSIS_0.5.6.md

### Screen-space depth reconstruction bakes in a projection-center assumption; asymmetric stereo can violate it on more than one axis
**What happened:** HPL3's deferred shadow/light shaders rebuild view-space position from depth + screen UV. The AFR bridge submitted true per-eye asymmetric projection (horizontal center `-0.242513` eye0 / `+0.242513` eye1, UBO offset `96`). Zeroing that (F5, 0.5.5) made shadows stereo-consistent — but 0.5.6 found a *second*, unnoticed instance of the same assumption: vertical center `-0.193187`, identical on both eyes, still moved shadows under pitch/roll and produced the visible sharp ceiling boundary. The planned fix (0.5.7) decouples render-time projection (centered, so legacy reconstruction works) from the OpenXR-submitted FOV (kept fully asymmetric via preserved tangent spans), so the compositor still reprojects correctly.
**Why it generalises:** Any deferred/screen-space technique (SSAO, SSR, volumetric shadow, fog) that reconstructs position from depth+UV instead of carrying true world-space position has an implicit camera-center baked into its math — an API-agnostic hazard in D3D and GL deferred renderers alike. Fixing one axis of that assumption does not prove the other axis is clean.
**Chapter:** 10-graphics-apis.md / 09-d3d11-openxr-injection.md
**Status:** SHARPENS "Projection companions must remain coherent" / "Projection companions are an OpenGL problem too"
**API-specific:** none

### Two unrelated shader features failing the same way is evidence of one shared upstream resource, not two bugs
**What happened:** Shadows and reflections are unrelated shader paths, but both showed the identical symptom — left/right eye mismatch and movement-dependent swimming. 0.5.3 explicitly used that correlation to raise the prior that AFR's alternating camera state / shared per-frame resources were the common root, rather than chasing two independent shader bugs — a call later confirmed exactly right in 0.5.5.
**Why it generalises:** When independent-looking symptoms share a signature, check upstream ownership before triaging each shader individually; it collapses the search space fast and is true regardless of engine or API.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Attribute by ownership before shader identity"
**API-specific:** none

### A uniform hook reporting zero uploads may mean the value moved into a UBO, not that your hypothesis is wrong
**What happened:** 0.5.3's F7 hooked `glUniform2f`/`glUniform2fv` for `avShadowMapOffsetMul` and got `uploads=0 overrides=0` on every toggle — looking like a dead end. 0.5.4's fuller capture showed programs `942`/`944` (the live deferred shadow programs) report `-1` for projection, view, inverse-view, and related uniforms because they are members of an OpenGL uniform block, invisible to direct-uniform hooks entirely.
**Why it generalises:** In any GPU API with a "grouped constants" mechanism (UBOs in GL, constant buffers in D3D), a hook aimed at the loose-uniform/individual-set path can report total silence while the value is live and flowing through a block path — silence from one instrumentation point is not proof of absence.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "A hook that 'does nothing' may simply never be reached"
**API-specific:** OpenGL

### A clean shader compile/link log only proves shader *creation* succeeded, not that the render output is correct
**What happened:** 0.5.1 found visible stereo shader defects with zero GLSL compile/link or OpenGL/OpenXR errors in the log. Rather than treat "no error" as "no lead," the analysis explicitly enumerated non-error causal classes from source review (temporal history buffers, screen-space desktop assumptions, incomplete per-eye state rebuild) and picked the cheapest one to falsify first.
**Why it generalises:** Build/link success and runtime correctness are different claims in every graphics API; a clean log rules out one narrow failure class and nothing else. Convert "it compiled fine" into a specific list of remaining hypotheses instead of stalling.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Presence is not proof of loading"
**API-specific:** none

### A whole-subsystem reversible kill switch cheaply falsifies (or confirms) an entire hypothesis class before per-shader debugging
**What happened:** F12, a full post-effect-composite bypass, was toggled repeatedly between calls `4808`-`6304` in 0.5.2. The result — increased contrast only, core eye mismatch unchanged — definitively ruled out the entire post-effect chain in one cheap test and redirected the investigation into world/deferred-light rendering, where the real bug lived.
**Why it generalises:** Before instrumenting individual shaders, build a coarse on/off switch for an entire pipeline stage; a negative result eliminates a whole hypothesis class in one test instead of many narrow ones.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Falsify your own hypothesis before shipping a fix"
**API-specific:** none

### Prove system ownership by correlating two independently-logged signals over time, without instrumenting either system's internals
**What happened:** 0.5.1 proved FMOD's listener was not head-relative purely by logging: HMD quaternion changed strongly across frames `2583-3060` and `3899-4499` while listener forward/up stayed pinned near constant values (`0.22721,0.20276,0.95250` and `0.88992,0.15906,-0.42749`), moving only when the game's own authored camera changed. No FMOD internals were touched to reach this conclusion.
**Why it generalises:** Whenever two subsystems (audio, physics, UI camera) might or might not share a data source, logging both over time and watching for a held-constant-while-the-other-moves pattern is a zero-invasion way to settle ownership before writing any correction code.
**Chapter:** 06-debugging-methodology.md
**Status:** NEW
**API-specific:** none

### A worker thread whose exit condition is signaled only at DLL unload — while the thread itself is what's keeping the process alive — can never exit
**What happened:** 0.5.3 found that after the visible game window closed, `Soma_NoSteam.exe` persisted with exactly one thread: the mod's own worker, blocked waiting on a stop event that was only signaled during DLL detach — which cannot happen while that same worker keeps the process alive. 0.5.4 broke the cycle by detecting "I am the process's last thread" and returning without calling teardown against an already-destroyed GL context; 0.5.6 fixed it properly with a signature-guarded destructor hook that shuts the injected runtime down while the graphics context is still valid.
**Why it generalises:** Any injected DLL with a background thread can create this exact mutual-liveness deadlock — the thread outlives the host because it's waiting on a signal that requires the host to have already died. Recognize the cycle and break it by hooking an earlier, still-valid teardown point instead of waiting on unload.
**Chapter:** 07-engine-integration-safety.md
**Status:** NEW
**API-specific:** none

### A missing REX prefix byte in an x64 signature scan fails the hook closed rather than silently corrupting memory
**What happened:** 0.5.5's lifecycle-shutdown hook failed with `signature_mismatch` in production. Ghidra and static bytes showed the real prologue begins `40 53 48 83 EC 20 48 8D 05`; 0.5.5's guard had omitted the leading `0x40` REX prefix byte. Because the guard was strict, the hook simply refused to install rather than patching the wrong location — 0.5.6 corrected the pattern and confirmed installation at `Soma_NoSteam.exe+0x3b16e0`.
**Why it generalises:** REX prefixes are an x64-only encoding wrinkle (they don't exist in x86 disassembly), so byte-pattern signatures hand-copied or re-derived between 32- and 64-bit builds are one easy byte short of matching nothing. A strict, fail-closed signature guard turns that mistake into a loud no-op instead of a wild write — always prefer fail-closed guards on RE-derived offsets.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "Prologue scans lie in four specific ways"
**API-specific:** 64-bit

### An exit dump's surviving thread count plus its instruction-pointer module is enough to triage a shutdown hang without a live debugger attach
**What happened:** `Soma_NoSteam-10384.dmp` contained exactly one thread. Its start address, `Soma_NoSteam.exe+0x642bb4`, was the CRT entry path, and its instruction pointer sat at `opengl32.dll+0x10399`, with Virtual Desktop OpenXR/LibOVR frames on the stack. That combination — thread count plus IP module — was sufficient to identify the hang as blocked inside the graphics runtime's teardown path, directing the fix straight at destructor-time OpenXR shutdown ordering.
**Why it generalises:** A capture-only minidump (no debugger session, no live attach) still yields two cheap, high-signal triage facts on any platform: how many threads survived, and which module each one's IP falls inside. That's often enough to pick the next investigation target before doing any deeper analysis.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Crash-dump workflow"
**API-specific:** OpenGL
