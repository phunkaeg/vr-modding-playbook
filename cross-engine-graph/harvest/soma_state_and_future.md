# SOMAVR — CURRENT_STATE / FUTURE_SYSTEMS_RE / HYPOTHESES harvest

Files read: `CURRENT_STATE.md` (lines 1-1163, full), `FUTURE_SYSTEMS_RE.md` (lines 1-1838, full), `HYPOTHESES.md` (lines 1-647, full), `playbook_toc.md` (lines 1-199, full, for dedup reference).

### When retrofitting VR control into a native PID/error-based controller, feed an absolute target into the point where the engine already computes error once — never add your own delta as a second, independent error term
**What happened:** An early attempt (HYPOTHESES S12) added camera-relative controller displacement directly onto SOMA's existing Grab position-PID error (`wantedPosition - bodyPosition`), and a similar rotation attempt added tracked angular velocity onto the existing torque-PID error. Live testing showed exactly the predicted failure: the native target and the added controller target became near-exact opposites at the shared `6 rad/s` cap, so the two contributions fought instead of composing. The fix (S13/0.65.1) computed a full absolute controller-derived target, subtracted measured current state once, and fed that single error into the unmodified native PID — preserving SOMA's own `P=40/I=0/D=0.4` gains and `1000` torque cap.
**Why it generalises:** this is the general trap of two writers feeding one accumulator — any server-authoritative physics or animation controller that internally computes `error = target - current` will double-count or fight a delta added on top of its own error, rather than simply replacing the target it derives error from.
**Chapter:** 02-viewmodels-and-hands.md (Held tools and physical manipulation: drive the native system, share one basis)
**Status:** SHARPENS "Held tools and physical manipulation: drive the native system, share one basis"
**API-specific:** none

### A candidate "owner" pointer that doesn't crash and produces plausible-looking behavior is not proof it's correct — validate it against one independently-known-good call path first
**What happened:** SOMAVR's early locomotion/interaction hook dispatched `cLuxPlayer::OnAnalogInput` against the player root object and read a readiness flag at `root+0xc8`. It never crashed, but curtain/drawer/MovingButton interactions silently did nothing — 360+ queued events, zero native dispatches. Live Frida tracing (compared against a known-good keyboard `W`-press trace reaching the same native call) showed the real dispatch target is a helper subobject at `root+0x110`, and the readiness flag actually lives at `helper+0xc8` (== `root+0x1d8`) — an adjacent, similarly-shaped but wrong offset.
**Why it generalises:** plausible-looking sibling offsets on a "helper"/"context" pointer are a common RE trap on any engine, and a hook that fails silently gives false confidence that the owner is right. Always cross-check a suspected owner object against a second, independently-verified call path (e.g. an input method you know reaches the target) before trusting it.
**Chapter:** 06-debugging-methodology.md (Dynamic tracing finds the exact owner that static RE only approximates)
**Status:** SHARPENS "Dynamic tracing finds the exact owner that static RE only approximates"
**API-specific:** none

### FALSIFIED: before patching authored shader/material logic to explain a stereo-only visual defect, rule out shared-resource/eye-coherence bugs in the pipeline — a per-eye artifact is usually infrastructure, not content
**What happened:** HYPOTHESES S18 proposed that a moving translucent-boundary artifact on windows/water was the authored view-depth reflection fade (`avReflectionFadeStartAndLength` in the shipped water shader) — a plausible, correctly-named parameter. The team patched that exact program for 369 draws; the artifact was unchanged. FALSIFIED. The real cause (S15/S16) was that world reflections sample a texture rendered from a mirrored frustum shared across AFR eyes/frames rather than regenerated per eye — an ownership bug, not shader math.
**Why it generalises:** the wrong mental model is "a parameter with the right name is the cause." In any renderer, artifacts that only appear in stereo (not flat-screen) are far more likely to come from a resource that's shared across eyes/frames than from content nobody complained about before. Check whether the suspect buffer is per-eye or a singleton before touching shader logic.
**Chapter:** 14-render-pass-hazard-atlas.md
**Status:** NEW
**API-specific:** none

### MOSTLY FALSIFIED: when correlating a VR artifact with head movement, test translation and orientation as independent variables — don't assume the axis that feels intuitively "more VR-specific"
**What happened:** after projection centering fixed inter-eye shadow disagreement, shadow/lighting position still drifted as the player moved their head. HYPOTHESES S17 hypothesized tracked head *translation* was the driver, since 6DoF position is the obviously VR-specific new input. A dedicated test (rotation+IPD only, translation disabled) showed translation had almost no effect; the actual driver was HMD pitch and roll.
**Why it generalises:** VR adds two new motion channels simultaneously (full translation and expanded rotation range), and it's tempting to blame whichever feels more "VR-specific." That's not evidence. Isolate each channel independently — freeze translation and vary rotation, then the reverse — before writing a fix aimed at either.
**Chapter:** 06-debugging-methodology.md (Falsify your own hypothesis before shipping a fix)
**Status:** SHARPENS "Falsify your own hypothesis before shipping a fix"
**API-specific:** none

### Look for ground-truth source text before reverse-engineering blind: check whether the game ships its own scripting layer as plaintext, and whether the closed engine has an open-source sibling in the same lineage
**What happened:** two independent channels of ground truth repeatedly beat pure disassembly here. (1) SOMA ships its entire gameplay logic as uncompiled AngelScript `.hps` files in its data folders — reading `PlayerState_Interact_Grab.hps` revealed exact PID gains (`P=400/I=0/D=40` position, `40/0/0.4` rotation), the `InteractionMoveSpeedMul` mass-coupling rule, and that the throw script teleports the prop *before* applying impulse — facts that would have taken much longer to recover from x64 disassembly alone. (2) Frictional's older, fully open-source HPL2 engine (from Amnesia) is structurally close enough to HPL3 to confirm function identity (e.g. `cFrustum::SetupPerspectiveProj`) and matrix composition order before ever opening Ghidra.
**Why it generalises:** many commercial engines with a scripting layer (Lua, AngelScript, Python, custom DSLs) ship that layer as readable source even when the core binary is stripped, and many closed engines evolved from or share code with an open-source ancestor. Check both before reaching for a disassembler.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** NEW
**API-specific:** none

### 64-bit: don't assume every hookable callsite tolerates a standard 5-byte relative-jmp trampoline, and don't trust a hand-trimmed opcode signature to survive REX prefixes
**What happened:** two separate x64-specific failures. (1) SOMA's `AddImpulse` wrapper at `0x14049c720` was a 9-byte virtual-thunk (`mov rax,[rcx]; jmp [rax+0x130]`) — too small for a normal trampoline detour, requiring a guarded INT3-plus-absolute-jump patch applied only for a one-shot window instead of a permanent hook. (2) an inner raycast signature match silently failed because the trimmed byte pattern omitted the target function's leading `0x40` REX prefix byte, so the hook never installed even though the address was correct — controller aim rendered visually but produced zero hit data until the prefix was restored.
**Why it generalises:** x64 prologues routinely carry variable-length REX prefixes and short vtable thunks that x86-era hooking habits don't anticipate. Both failure modes present as "the hook silently does nothing" rather than a crash, making them expensive to diagnose on any 64-bit target.
**Chapter:** 07-engine-integration-safety.md (Hooking & native-call discipline)
**Status:** SHARPENS "Hooking & native-call discipline"
**API-specific:** 64-bit

### OpenGL: hooking the direct camera-matrix uniform upload does not guarantee every consumer sees your correction — deferred/reconstruction shaders often read camera state from a UBO instead
**What happened:** SOMA's per-eye asymmetric OpenXR projection was correctly alternated in the direct `glUniformMatrix4fv` uploads (confirmed by capture), yet realtime shadows (programs `942/944`) and screen-space reflection (`989`) still showed a horizontal offset matching exactly the per-eye projection-center displacement. Root cause: those programs read inverse-projection/reconstruction data from a uniform buffer object, not the directly-hooked uniform, so the direct-upload capture never saw it. Confirmed by dumping UBO offset `96`: values were `-0.242513/+0.242513` per eye until horizontal projection centering flattened both to `0/0`.
**Why it generalises:** any engine using UBOs/constant buffers for shared per-pass data (D3D cbuffers included) can route "the same" camera value through two independent paths — a direct uniform and a packed buffer — and a hook on only one path leaves the other stale. Enumerate bound UBOs/cbuffers for suspect programs, not just direct uniform calls.
**Chapter:** 14-render-pass-hazard-atlas.md / 10-graphics-apis.md (Reading the projection: hook the uniform upload)
**Status:** SHARPENS "There is no canonical G-buffer" / "Reading the projection: hook the uniform upload"
**API-specific:** OpenGL

### OpenGL: when a stereo retrofit exposes that many legacy passes assume a mono/symmetric projection, centering the per-eye projection is a legitimate, cheap first-order compatibility policy — try it before hunting pass-by-pass
**What happened:** centering the horizontal projection axis fixed shadow/reflection eye disagreement, but shadows, ceiling lighting, and window/oven reflections still shifted under head pitch and roll, tracing to a retained vertical projection offset of `-0.193187` in the same reconstruction data. Centering both projection axes together (full symmetric frustum) fixed every remaining reported shadow, lighting, window, and reflection artifact in the tested level in one pass, without touching shadow, reflection, or SSAO code individually.
**Why it generalises:** legacy renderers accumulate screen-space reconstruction math (shadows, SSAO, reflections, TAA) that implicitly assumes the projection center sits at 0.5/0.5 of the viewport. True per-eye asymmetric projection breaks that assumption in every pass relying on it, and auditing each one doesn't scale. Centering makes the stereo camera look mono-shaped to every pass you haven't audited yet — a blunt but effective global lever, at a small comfort/convergence cost.
**Chapter:** 09-d3d11-openxr-injection.md (Projection companions must remain coherent) / 10-graphics-apis.md (Projection companions are an OpenGL problem too)
**Status:** SHARPENS "Projection companions must remain coherent" / "Projection companions are an OpenGL problem too"
**API-specific:** OpenGL

### OpenGL: confirm the exact NDC/depth convention (finite vs reversed-Z, near/far mapping) from the matrix-setup code itself before wiring compositor depth submission
**What happened:** for `XR_KHR_composition_layer_depth` submission, the team traced the native perspective-setup call (`cFrustum::SetupPerspectiveProj` at `0x140270230`, cross-checked against matching HPL2 source) to confirm HPL3 maps near/far to a standard finite OpenGL NDC of `-1/+1` and normalized depth `0/1` — not a reversed-Z or infinite-far convention some newer engines use. Near/far are then divided by an engine world-scale constant to convert into OpenXR meters, and the build falls back to color-only submission on any format or clip-data mismatch.
**Why it generalises:** OpenGL doesn't dictate one depth convention — reversed-Z, infinite far planes, and non-standard near/far encodings are all common across engines and eras, and getting this wrong produces depth-based compositor effects that are subtly wrong rather than obviously broken. Verify the convention from the actual projection-matrix construction code, not from assumption.
**Chapter:** 10-graphics-apis.md (Depth submission differs in the details, not the intent)
**Status:** SHARPENS "Depth submission differs in the details, not the intent"
**API-specific:** OpenGL

### A crash immediately after your new subsystem starts up doesn't prove that subsystem's API rejected you — check DLL search-path/dependency resolution before blaming the runtime
**What happened:** the first live OpenXR session-creation attempt crashed with WER exception `0xc06d007e` before reaching the `openxr_extensions` log line — a signature consistent with a failed/delayed module load, not an OpenXR runtime error. It looked like "the OpenXR runtime rejected our binding," but the actual cause was that `openxr_loader.dll` wasn't resolvable from the injected process's default search path. Explicitly preloading `openxr_loader.dll` from beside the mod's own DLL fixed it, and every later OpenXR milestone built on that fix.
**Why it generalises:** any injected mod adds new DLL dependencies into a host process whose search path was never designed to expose them. A crash right at the boundary of "brand-new subsystem I just added" is more often a loader/dependency problem than a logic problem in the new subsystem — cheap to check, easy to misdiagnose as an API-level rejection.
**Chapter:** 07-engine-integration-safety.md
**Status:** NEW
**API-specific:** none

### In a numbered bone chain, the intermediate joints are usually twist-distribution bones, not independent anatomical hinges — driving only the endpoints creates a skinning crease wherever a mesh's weight painting straddles the middle of the chain
**What happened:** live traversal of SOMA's hand rig found a continuous chain `Clavicle -> Shoulder -> Arm_1..5 -> Elbow_1/2 -> Arm_6..10 -> Wrist`. Diffing the released mesh source showed the shirt mesh is weighted through `Arm_1..7` and both elbow nodes, while the hands mesh overlaps at `Elbow_2`/`Arm_6-7` and continues through `Arm_10` — so any solver transforming only `Arm_1` and `Arm_6` (shoulder and forearm start) while leaving the intervening numbered bones untouched would crease the mesh exactly at that overlap, since both mesh regions expect the twist bones between them to interpolate smoothly.
**Why it generalises:** a long humanoid bone chain with numbered intermediate twist joints is common across skinned-character rigs regardless of engine; a VR arm-IK retrofit that grabs "shoulder" and "wrist" and ignores the bones between risks the same crease unless twist is explicitly redistributed across them.
**Chapter:** 12-torso-calculations-and-ergonomics.md (Efficient two-bone arm IK)
**Status:** SHARPENS "Efficient two-bone arm IK"
**API-specific:** none
