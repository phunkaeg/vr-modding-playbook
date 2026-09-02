# Teardown: the IL-2 1946 VR mod

A study of the **IL-2 Sturmovik 1946 VR mod** ([SAS1946 topic 75791](https://www.sas1946.com/main/index.php/topic,75791.0.html)),
a working true-stereo 6DOF conversion of a 2006 flight sim, shipped as `il2vr.dll` plus a set of
replacement Java classes. Builds analysed: `il2vr_4122_dev202608170057_icon-anchor` (IL-2 4.12.2m +
SAS ModCat 5.3) and `il2vr_up34p2hf23_dev202608170044_icon-anchor` (UP3.4 P2 HF23). Credited as a
refactor of **firepolo's** 2020 OpenVR mod, with the Java layer rewritten against the 4.10.1 baseline.

It earns a chapter for a reason none of the other externals do: **it is the first target in this
playbook where the game's own logic is a managed, moddable layer.** Every project in the fleet — and
every external folded in so far — is a native binary you must reverse-engineer. IL-2's flight model,
camera, HUD and render orchestration are Java bytecode, and the SAS/UP mod frameworks already load
replacement classes by hash. The author did not *find* a camera; they *edited* it.

That makes this the controlled experiment for a question the rest of the playbook cannot answer:
**how much of our method is essential, and how much is a tax on not having source?**

Everything below is derived from the shipped artifacts — `javap` over the 63 hash-named classes and a
string/import census of `il2vr.dll` — cross-checked against the author's release notes. Claims marked
*(verified)* come from bytecode or the binary; claims marked *(author)* are their changelog. No code was
copied.

---

## The headline: when the mod surface is the game's own source, chapter 11 evaporates

There is no injector, no hook, no signature scan, no RVA. `il2fb.exe` is untouched. The install is a
file copy:

```
game root\
+-- il2vr.dll            <- JNI bridge, x86, imports only OPENGL32 + openvr_api
+-- openvr_api.dll
+-- arial.ttf / arialbd.ttf
+-- #SAS\MOD_VR\<63 hash-named .class files>     (or #UP#\IL2_VR\ on UP3)
+-- vr_aircraft_conf\
```

The Java layer splits cleanly into three new classes and nine patched ones *(verified)*:

| New | Role |
| --- | --- |
| `com.maddox.il2.game.OpenVR` | The entire native surface: **64 JNI methods**, nothing else in the DLL |
| `com.maddox.il2.game.VRHudManager` | Per-aircraft x per-seat gaze-interactive button panels |
| `com.maddox.il2.gui.VRMapHotKeys` | `VRMAP_*` / `VRHUD_*` commands as native `HotKeyCmd` subclasses |

| Patched | Why |
| --- | --- |
| `com.maddox.il2.engine.Renders` | The three-pass stereo frame loop (`doVRStereoPaint`) |
| `com.maddox.il2.engine.Camera3D` | HMD pose composition + per-eye projection load |
| `com.maddox.il2.game.Main3D` | Per-eye and `*Mirror` render objects, `Camera3DR`, `Render3D0R` |
| `HUD`, `GUIRenders`, `GUIMainMenu`, `GLContext`, `HookPilot` | 2D suppression, map interception, menu mode, netplay head sync |

**The generalizable rule: before you open a disassembler, find out what language the game's logic is
actually in.** Java, C#/Mono, Lua, Squirrel, UnrealScript and shipped `.uc`/`.hps` sources all move you
up [11](11-re-anchoring-and-discovery.md)'s anchor ladder — sometimes off the top of it. The playbook
already says "check the export table and for shipped script source before disassembling"; this is the
target where that check returns *everything*.

Note the boundary precisely, because it bites later: **the managed layer gives you the scene graph, the
camera and the HUD. It does not give you the renderer.** IL-2's shader pipeline is C++ inside the game's
native DLLs, and that is exactly where this mod's remaining unfixable-looking bugs live.

---

## The frame loop: same-frame three-pass, from one pose sample

`Renders.doVRStereoPaint` *(verified, bytecode)*:

```
PrePreRenders()                       <- stock IL-2 native, unchanged
camera.activate(); render.preRender() <- ONE shared prepass (shadows, mirrors, plates)
PostPreRenders()

OpenVR.preRenderLeft()                <- bind left eye FBO
   currentEyeLocation = leftEyeLocation ; bVRLeftEye = true
   vrClearPass() ; vrRenderLoop()     <- full scene
OpenVR.postRenderLeft()

bVRDesktopPass = true                 <- default framebuffer, i.e. the desktop window
   vrClearPass() ; vrRenderLoop()     <- full scene, game's OWN FOV and window aspect
bVRDesktopPass = false

OpenVR.preRenderRight()               <- bind right eye FBO
   currentEyeLocation = rightEyeLocation
   vrClearPass() ; vrRenderLoop()     <- full scene
OpenVR.postRenderRight()

vrCaptureFrames() ; PostRenders()     <- submit
```

Three full scene renders per frame. Both eyes are drawn from **one HMD pose sample and one shared
prepass**, so this is same-frame stereo — the [13](13-teardown-bioshock-vr.md) `SequentialReentry`
shape, not [10](10-graphics-apis.md)'s AFR.

**The whole "AFR stereo coherence" section of [10](10-graphics-apis.md) is inapplicable here, and that
is a finding, not an omission.** SS2VR and SOMAVR took alternate-eye because re-entering a native
pipeline twice was expensive or non-repeatable. IL-2's Java scene graph replays cleanly and cheaply, so
the mod pays CPU for a third pass and buys immunity to the entire pair-slip bug class: no inter-eye yaw,
no eye-phase desync, no comfort blackout masking broken pairs. The author's cost note is honest — *"two
rendering passes per frame plus the old Java/OpenGL stack cannot fully use multi-core CPUs"* *(author)*.

> **When the engine's render orchestration is replayable, same-frame stereo is strictly better than
> alternate-eye, and the decision is about replay cost alone.** Price the replay before you accept AFR's
> coherence tax.

### The desktop mirror is a first-class pass, not leftover

Most of the fleet treats the flat window as whatever falls out. Here it is a deliberate third pass with
its own object graph — `Render3D0Mirror`, `Render3D1Mirror`, `Render2DMirror`, `RenderCockpitMirror`,
`Camera3DMirror`, `TransformMirror` *(verified)* — and a `bVRDesktopPass` flag threaded all the way into
the camera:

```java
// Camera3D.activate (decompiled shape)
if (OpenVR.loaded && !bVRDesktopPass) Camera.SetFOV(OpenVR.fov, ZNear, ZFar);
else                                  Camera.SetFOV(this.FOV,   ZNear, ZFar);
```

So the mirror keeps the game's native FOV and the window's own aspect while the eyes get the headset's.
This is the general form of [04](04-ui-and-hud.md)'s "do not stretch a 16:9 source across a tall eye
texture" — applied in the other direction, to stop the *headset's* geometry leaking into the flat view.
Their changelog records the bug it fixed: the desktop window was previously *"stretched by the headset's
single-eye aspect ratio"* *(author)*.

**Worth stealing. Worth also pricing:** that pass is a third of the CPU frame on a CPU-bound target, and
most VR users never look at it. See recommendation 1.

---

## Head pose: two matrices and a swizzle

`Camera3D.activate` *(verified, constant pool + bytecode order)*:

```java
vrHmdMat  <- OpenVR.hmdRotMatrix[0..8]     // 3x3 from the DLL
vrAcMat   <- tmpO.getMatrix()              // aircraft / seat orientation
vrMat.mul(vrAcMat, vrHmdMat)               // head composed onto the airframe

tmpEyeP.set(eyeLoc.z, eyeLoc.x, eyeLoc.y)  // OpenVR -> IL-2 basis
```

That last line is the whole "6DOF is broken on Pimax" saga. OpenVR is `x=right, y=up, z=back`; IL-2 is
`x=forward, y=left, z=up`. The 2026-08-09 fix is described as *"the old mapping crossed forward/back
with left/right — confirmed root cause, verified in-game"* *(author)*. It is a wrong permutation on one
`set()` call, and it survived for months.

This is [A1](a1-rotation-and-frames.md)'s trap in its purest form, and it reproduces the playbook's
diagnosis exactly: **an axis-mapping error is invisible at rest and only expresses under a motion that
separates the crossed axes.** Users who leaned reported it; users who only turned their heads did not.

The recenter story is [01](01-camera-and-tracking.md) rediscovered the hard way: the fix was to *"unify
the Seated tracking space (root cause of panel positioning errors)"*, take *"only the current yaw plus
position, with pitch/roll set absolute-level"*, and *"remove all uncontrolled auto-recentering (init /
menu / 30 s)"* *(author)*. The DLL confirms the mechanism *(verified)*:

```
[VR] recenter: ResetZeroPose(Seated) seatXform pos=(...)->(...) yaw=%.1f->%.1f
[VR] recenter: level origin pos=(...) fwdH=(-Z col projected) fwd=(...)
```

> **One recenter event, one tracking space, consumed by every lane.** Panels drifting relative to the
> view is not a panel bug; it is two lanes on two origins.

---

## UI: 100% compositor overlays, including the main menu

This is the most complete execution of [04](04-ui-and-hud.md)'s central rule anywhere in the playbook,
internal projects included. **Nothing is drawn into the eye buffers.** Every UI surface is:

1. a **Dear ImGui 1.91.8** frame (`imgui_impl_opengl3`) rendered **once** into a private GL FBO
   *(verified — the ImGui build string and its shader-compile error strings are in the DLL)*, then
2. handed to **`IVROverlay_026`** as a world-anchored quad, posed in metres relative to the HMD via
   `setXxxPose(x,y,z,yaw,pitch,roll)`.

The surfaces: tactical map, flight data (IAS/TAS, alt + VSI, heading, G), popup messages, the **flat
menu mirror**, and up to **32 gaze-interactive button widgets** per seat *(verified — `MAX_WIDGETS` /
`MAX_BUTTONS` in `VRHudManager`; `initWidget` / `setWidgetPose` / `setWidgetStyle` in the bridge)*.

Three things here are better than what the playbook currently documents:

**The menu mirror is a mirror, not a re-render.** `copyWindowToMenuFBO()` blits the desktop window into
an overlay and blacks out both eyes. The physical mouse then works with zero extra code, because the
pointer is *in the mirrored image* and the click paths are identical by construction *(author)*. This
sidesteps [04](04-ui-and-hud.md)'s "never re-invoke an immediate-mode GUI's render path just to capture
its output" (the SOMAVR terminal-overlay failure) by never invoking anything twice — and it sidesteps the
SS2VR Game-Pig input problem, where cursor injection overrode the OS mouse and the physical path was
never reached.

> **A desktop-window mirror on a quad layer is the cheapest correct menu solution, and it makes input
> free.** Reach for it before building a laser pointer.

**Font-atlas rebuilds are bracketed.** `fontRebuildBegin()` / `fontRebuildRestorePanels()` /
`fontRebuildEnd()` *(verified)* — panels survive an atlas rebuild instead of turning into garbage for a
frame. The kind of lifecycle detail [07](07-engine-integration-safety.md) says to expect and nobody
enjoys discovering.

**Sharpness is decoupled from size.** `widget_N_texdens` is *pixels per metre* (default 1024), so a small
panel is not automatically a blurry one and a large panel is not automatically expensive *(author)*.
Every project in the fleet has instead argued about texture dimensions. This is the better
parameterisation.

### Gaze-angle fade

Panels fade by gaze angle — full opacity within `fade_min_angle` (5 deg), gone by `fade_angle` (30 deg),
`always_visible=1` to opt out *(verified — `setWidgetFade(int, boolean, float, float)`)*. A comfort and
legibility trick [04](04-ui-and-hud.md) does not currently carry: it lets a dense instrument overlay stay
permanently configured without cluttering peripheral vision.

### The authoring loop is the real lesson

`vr_aircraft_conf/VR-HUD editor.html` is a self-contained three.js editor (98 KB + `three.min.js` +
`OrbitControls.js`) with a 224-command picker, a simulated cockpit/HMD preview, gaze-fade reproduction,
and en/zh/ru UI. It writes a plain INI; `VRHUD_RELOAD` hot-reloads it in-game with no restart *(verified
— the files ship; behaviour per author)*.

This is the mature form of SS2VR's "expose grid/font-cell metrics as live config keys." The playbook's
version is *make the constants configurable*; this is *ship the tool that writes the config, and a hotkey
that applies it live*. For anything spatially placed — panels, anchors, offsets — the edit loop dominates
the maths.

> **For spatial configuration, build the editor.** Guessing coordinates in an INI and relaunching is the
> single most wasteful loop in VR modding.

---

## What it confirms (independent corroboration)

Different author, different engine class, no contact with this playbook — and the spine held:

| Playbook item | How this mod hit it |
| --- | --- |
| **L1 — which camera does each consumer use** | `Camera3D.activate` is *the* chokepoint; every view in IL-2 passes through it. One class patched. |
| **L8 — drive the engine's own systems** | Rendering is never reimplemented; IL-2's own `Render`/`Camera` objects are re-driven three times a frame. |
| **[04] get UI off the backbuffer onto a layer** | Taken further than any internal project — 100% of UI, menus included. |
| **[04] never re-run an immediate-mode GUI to capture it** | ImGui renders once per surface into a dedicated FBO. |
| **[10] own state in a global machine** | Explicit bind/unbind pairs (`preRenderLeft`/`postRenderLeft`, `bindMapFBO`/`unbindMapFBO`) around every private FBO operation. |
| **[01] one recenter, one tracking space** | The 2026-08-09 rework, verbatim. |
| **[14] hazard atlas** | Water reflection and cloud/smoke billboards both surfaced as stereo-only artifacts. |
| **[A1] rotation and frames** | The forward/back to left/right swizzle. |
| **[06] make it self-identify** | `vr_debug=1` emits an init banner (HMD model, render resolution, FOV) plus per-frame pose — added *because* remote HMD triage was impossible without it. |

---

## Where it diverges, and why

**No OpenXR at all.** Zero OpenXR strings in the binary *(verified)*; the roadmap lists *"long term:
OpenXR submission backend migration"* *(author)*. The cost is concrete and user-visible: a hard SteamVR
dependency, Quest Link / Virtual Desktop black-screening on the legacy OpenGL path, and a documented
workaround of swapping in OpenComposite's `openvr_api.dll` to reach OpenXR via WiVRn.

**`IVROverlay` instead of quad layers.** Functionally equivalent, but overlay count is a real runtime
resource and is very likely what sets the 32-widget cap.

**Culling and rendering use different frusta.** The one architectural divergence that is a defect rather
than a choice — see recommendation 2.

---

## What it teaches us (net new)

### 1. A new engine profile: managed mod layer over a native renderer

Worth adding to [00](00-engine-profiles.md) as a category. The properties:

- **You get a source-grade seam for free.** Class replacement *is* the hook; it cannot miss, drift across
  builds, or fire on the wrong thread.
- **You are locked out of everything the native side owns.** Here: the shader pipeline. The mod's answer
  to modern shaders is to *turn them off* (`ForceShaders1x=1`). That is what "no hook" costs you.
- **Version coupling is total.** Class replacement means the mod is a fork of one exact baseline. The
  author maintains two builds and has *abandoned four* (4.10.1, 4.13.4, UP3 RC4, UP3.4 P0/P1) as *"too
  many accumulated bugs to be worth keeping"* *(author)*. A signature-guarded native hook would have
  spanned all of them. **Source-level modding trades version robustness for access.**

### 2. Class-shadowing: a new form of "present is not loaded is not ran"

Lesson 2 says a fix present on disk is not a fix that ran. This target adds a mechanism the fleet has
never faced: **two mods shipping the same hash-named class, with framework directory resolution order
silently deciding the winner.**

Their FAQ Q7 documents it precisely: when another mod ships e.g. `HookPilot` (`6EABC2640E2C18C4`) or `HUD`
(`0A535B74072406CC`), *"the UP3 framework loads whichever is first in resolution order"*, and VR fails
**open** — the game runs, looks normal, and silently renders flat. The fix is to delete the conflicting
hash from the higher-priority folder, safe because *"this mod's classes are strict supersets of the
baselines"* *(author)*. It re-breaks on every JSGME re-apply.

> **On any framework that resolves mods by load order, enumerate what actually resolved and log it.** The
> failure is silent, looks like "the mod does nothing", and cannot be diagnosed from behaviour.

### 3. Same-frame stereo as the default on replayable engines

See the frame loop above. Belongs in [10](10-graphics-apis.md)'s AFR section as the counter-case: AFR is
a concession to expensive or side-effectful re-entry, not a stereo strategy in its own right.

---

## Improving it: what the playbook would change

Ordered by expected value. Recommendations 1-3 are backed by findings in the shipped artifacts; the rest
are method transfers.

### 1. Make the desktop mirror optional — probably the largest single CPU win available

*(verified)* The mirror pass is a **full scene render** (`vrClearPass` + `vrRenderLoop`, identical to the
eye passes), not a blit. On a target the author describes as CPU-bound, that is roughly a third of the
frame spent on a window most users in a headset never look at.

A `vr_mirror=0|1|2` key (off / current full render / cheap blit of one eye FBO into the window) is a small
change to `doVRStereoPaint` with a large payoff. Instrument it per pass first —
[A5](a5-flat-harness-stats.md)-style per-pass CPU timings for left/desktop/right will size the win before
anyone writes the option.

### 2. Split the cull frustum from the render frustum — this likely fixes two T0 bugs at once

**The finding** *(verified, `Camera3D.activate` bytecode)*: the mod sets **two different frusta** per eye,
and only one of them is asymmetric.

```java
Camera.SetFOV(OpenVR.fov, ZNear, ZFar);                     // offset 108  -- a single SCALAR fov
...
gl.MatrixMode(GL_PROJECTION);
gl.LoadMatrixf(OpenVR.getProjectionMatrix(eye, near, far));  // offset 1157 -- correct ASYMMETRIC matrix
```

The GL projection is right. But `Camera.SetFOV` is IL-2's own native frustum setter and takes a
**symmetric half-angle**. That frustum drives the engine's visibility work — `Main3D$FarActorFilter`,
`Main3D$ShadowPairsFilter`, LOD selection, actor submission. So **the renderer sees the headset's real
off-axis frustum while the culler sees a symmetric cone approximating it.**

[A3.1](a3-stereo-projection.md) names exactly this: *"the two entries people get wrong are the off-centre
ones — with a symmetric frustum they are zero, so a bug here is invisible until you use a real headset."*
[01](01-camera-and-tracking.md)'s spine point is the consequence: *you cannot render your way out of
missing geometry.*

Both of the author's open T0 issues fall out of it:

- **If `OpenVR.fov` is inflated to cover the widest half-angle** (the safe choice), the cull cone is much
  larger than either eye needs and every pass submits actors that can never be visible -> *"CPU load
  spikes / frame drops when certain scenes or 3D objects are in view"* *(author)*.
- **If it is not inflated enough**, geometry pops at the outer edge, worst under head translation ->
  *"lean your head out of the cockpit and you will see texture glitches"* *(author)*, currently attributed
  to the original game's designed range.

**The cheap diagnostic first** ([06](06-debugging-methodology.md) — measure, don't theorize): log
`OpenVR.fov` alongside the four `GetProjectionRaw` tangents for each eye. If `fov ~= 2*atan(max|tan|)` you
are in the over-cull case; if it tracks the symmetric average you are in the pop case. The `vr_debug`
channel already exists.

**The fix:** keep the exact per-eye asymmetric matrix for rendering (already correct), and feed the culler
the **union frustum of both eyes plus a lean margin** — two deliberately different numbers, with the
margin exposed as a config key. This is SS2VR's "drive the engine's culling inputs, never the render view"
applied to a far friendlier engine.

### 3. Root-cause the near-plane factor of two instead of shipping a magic constant

The docs instruct users *(author)*:

> *"the SteamVR projection matrix near clip plane equals half of the value passed in; `vr_world_near=1.8`
> -> actual 0.9 m (cockpit glass no longer clips)"*

That is not OpenVR behaviour — `IVRSystem::GetProjectionMatrix(eye, near, far)` honours `near` exactly. A
factor of two sitting unexplained in the depth row is a live bug wearing a tunable as a disguise, and it
is why near-clipping still needs per-aircraft attention on their roadmap.

[A3](a3-stereo-projection.md) resolves this in an afternoon and is worth following literally:

- **[A3.2]** Push known points through the *loaded* matrix. Frustum corners must land on the NDC box edges
  by construction. Include the asymmetry assertion — without it, a silently symmetrised projection passes
  every other check.
- **[A3.4]** Score the residual with **both** terms. The affinity term alone *cannot see a wrong FOV*
  (FarCry2-VR measured a deliberately wrong 75-degree FOV at `0.000031`, identical to correct); the
  orthonormality term is the one with teeth. A wrong near/far scores ~`0.800` against a `0.01` gate — this
  failure is loudly detectable.
- **Derive the threshold from your own gap.** Do not import `0.01`.

Three candidates worth testing in order, once the residual confirms it is the depth row: (a) a
world-unit/metre scale collision between IL-2's `ZNear` and OpenVR's metres; (b) an NDC-range convention
mismatch (`[-1,1]` GL vs `[0,1]` D3D) in whatever consumes the matrix after `LoadMatrixf`; (c) the matrix
being transposed and partially compensated elsewhere.

### 4. Recover the modern shader path with a uniform hook instead of disabling it

The docs state *(author)*: *"the engine's C++ side cannot be modified through mods, so this is the only
workaround"* — hence `ForceShaders1x=1` plus `water=0` whenever `HardwareShaders=1`.

That is true for *class replacement*. It is not true for this mod, **which already ships a native DLL that
already imports `OPENGL32.dll`** *(verified)*. The shader-2.0 path breaks because the projection reaches
those shaders as uniforms the Java layer cannot reach — which is precisely [10](10-graphics-apis.md)'s
"reading the projection: hook the uniform upload":

- track `glUseProgram`, map `(program, location)` to name via `glGetUniformLocation`, intercept
  `glUniformMatrix4fv`, and rewrite the projection family per eye under the existing `bVRLeftEye` /
  `bVRDesktopPass` flags;
- **budget for the UBO path too.** [10](10-graphics-apis.md)'s warning applies exactly: passes sourcing
  matrices from a bound uniform-buffer range never call `glUniform*`, so a plain uniform hook reports
  nothing and you conclude — wrongly — that those passes have no projection. SOMAVR lost time to this on
  its deferred shadow and water programs.

Payoff: "modern shaders are incompatible with VR" becomes "modern shaders work," which is the largest
visual win on the board.

### 5. Water and cloud asymmetry are known hazard classes, not unfixables

Both are currently accepted as engine problems *(author)*. [14](14-render-pass-hazard-atlas.md) and
[09](09-d3d11-openxr-injection.md) classify both:

- **Water reflection misaligned, therefore disabled.** A reflection is a *separate render view* and must
  be rendered from the eye's own reflected camera, never sharing the eye's private depth/colour space
  (Lesson 6). `Main3D$HookReflection.computeRenderPos(Actor, Loc, Loc)` is the exact seam — and it is
  **already a patched class in the shipping package** *(verified)*. Feeding it `currentEyeLocation`
  instead of the mono camera is a bounded experiment, not a research project.
- **Cloud/smoke left-right asymmetry.** The signature of a billboard/screen-space orientation computed
  once from a cached mono camera basis and reused for both eyes. Check whether the sprite basis is
  recomputed under `bVRLeftEye`; if it is cached across passes, that is the bug — and it is in the Java
  layer.

### 6. Ship a build banner and a resolved-class manifest

FAQ Q6 (*"no change after updating"*) and Q7 (class shadowing) are Lesson 2, and they are the two most
expensive threads on the forum. The infrastructure already exists — `OpenVR.log()`, `logEarly()`,
`flushEarlyLog()` *(verified)*.

One init block would end both:

```
IL2VR build <id> <date>   il2vr.dll=<full path> <build time>   openvr_api=<version>
resolved: 63/63 mod classes   SHADOWED: HookPilot(6EABC2640E2C18C4) <- !UP 3.4 Hotfix
```

The shadow line is the valuable half: it turns a silent fail-open into a self-diagnosing log the user can
paste. **Enumerate what actually resolved, not what you shipped.**

### 7. Verify world scale end-to-end before trusting stereo separation

`currentEyeLocation` is set from OpenVR's eye positions (metres) and swizzled directly into IL-2 space
*(verified)* with no scale factor visible in `Camera3D`. If IL-2's world unit is not exactly 1 m, stereo
separation and 6DOF translation are both systematically wrong — the classic that survives casual testing
because everything looks *fine*, just subtly wrong-sized.

[09](09-d3d11-openxr-injection.md)'s world-scale derivation settles it against a known object: a
Bf-109E-4 wingspan is 9.925 m. Measure it in-headset; if it reads short or long, every translation in the
mod is off by that ratio. (Compare the fleet's spread: SS2VR `3.28`, BioShock `~65 units/m`.)

### 8. Consider depth submission — this is the target where it actually pays

[10](10-graphics-apis.md) is careful that depth feeds only *positional* timewarp, which is near-zero value
at room scale on a stale-pair AFR design. **Neither caveat applies here.** The mod is same-frame (no
staleness to correct) and its entire selling point is 6DOF head translation inside a cockpit at 40-80 cm
from the instruments — exactly where positional reprojection earns its keep. The eye FBOs already carry
depth attachments *(verified — the 2026-08-06 "eye FBO depth/stencil attachment fix")*, so this is a
submit-flag change plus a near/far conversion. The reversed-Z convention is the documented trap: wrong
near/far produces no error, just subtle world wobble.

### 9. When the OpenXR migration happens, preserve two properties

- **One XR frame per *pair*.** One `xrWaitFrame`, one `xrLocateViews`, one predicted display time covering
  both eyes. The current design satisfies this by construction; a naive per-eye port would break it and
  reintroduce motion-dependent shear — the failure the independent BioShock mod hit and fixed by holding
  one XR frame open across both presents ([13](13-teardown-bioshock-vr.md)).
- **Overlays to quad layers, 1:1**, which also lifts the 32-widget cap and fixes the streaming
  compatibility problem that currently pushes users toward OpenComposite.

### 10. If cockpit interaction grows, use a picker rather than more config

Gaze buttons are currently panel-space rays with a global pitch fudge (`vr_gaze_pitch=-10`) compensating
for panels sitting below eye level *(verified — `setGazePitch`, "positive = ray up")*. That is the right
call for floating panels. If the goal ever becomes *actual cockpit levers*, the fudge does not generalise
— [04](04-ui-and-hud.md)'s rule is to read the engine's own hit result rather than fire your own ray, and
IL-2 already has cockpit geometry and named hook points. A semantic picker beats a growing pile of
per-aircraft offsets.

---

## Verification notes

Reproducible with a JDK and any strings tool:

```bash
# The 63 classes are Java 1.3 (major 47), hash-named with no extension.
for f in "#SAS/MOD_VR"/*; do cp "$f" "/tmp/cls/$(basename "$f").class"; done
cd /tmp/cls && for f in *.class; do javap -p "$f" | head -2; done   # -> real class names
javap -p -s <OpenVR hash>.class                                     # -> the 64 native signatures
javap -c -p <Renders hash>.class                                    # -> doVRStereoPaint
```

`il2vr.dll` is x86 (`__stdcall` `@N` export decoration) and imports **only** `OPENGL32.dll`,
`openvr_api.dll` and the CRT — no `jvm.dll`, because JNI callbacks go through the `JNIEnv` table. All 64
exports are `Java_com_maddox_il2_game_OpenVR_*`. `Renders.PrePreRenders` / `PostPreRenders` /
`PostRenders` are **stock IL-2 natives** in the game's own DLLs, not mod additions — the mod only calls
them at the right points. Interface versions in use: `IVRSystem_022`, `IVRCompositor_027`,
`IVROverlay_026`.

---

**Related:** [00 · Engine profiles](00-engine-profiles.md) ·
[01 · Cull-camera ownership](01-camera-and-tracking.md) ·
[04 · UI & HUD](04-ui-and-hud.md) ·
[10 · OpenGL dialect, AFR, uniform hooks](10-graphics-apis.md) ·
[13 · The other teardown](13-teardown-bioshock-vr.md) ·
[14 · Render-pass hazard atlas](14-render-pass-hazard-atlas.md) ·
[A1 · Rotation & frames](a1-rotation-and-frames.md) ·
[A3 · Stereo projection & validation](a3-stereo-projection.md)
