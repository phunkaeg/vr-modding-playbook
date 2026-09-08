# Symptom Index

**Start here when something is wrong.** The chapters are organised by topic; you arrive with a symptom.
This page translates.

Find the line that matches what you are *observing* — not what you think the cause is. The whole point is
that the observation and the cause are usually in different chapters.

---

## "It does nothing"

| What you're seeing | Go to |
|---|---|
| Hook installed at a verified-correct address, never fires | [07](07-engine-integration-safety.md) — you probably hooked a wrapper, or the runtime rewrites its own dispatch table. **Read the two addresses first**: if the replaced pointer still lands inside the API's own module, it's not an interposer. Guards + counters: [A4](a4-hook-safety.md) |
| Hook fires but has no effect | [06](06-debugging-methodology.md) — prove it ran (bare hit-counter) before debugging its logic |
| Your fix "didn't work" | [06](06-debugging-methodology.md) — check the build banner first. Then [08](08-project-process.md): is your code even in the load path? Present ≠ loaded ≠ ran |
| A config key you added does nothing | [07](07-engine-integration-safety.md) config-system rigor — the whitelist. Then [06](06-debugging-methodology.md): read the value at the *consumer* |
| The value you wrote isn't taking effect | [06](06-debugging-methodology.md) — settings lie; a write is not applied until you read it back from the system that consumes it |
| An API returned success and nothing changed | [06](06-debugging-methodology.md) — a success return proves the call didn't throw, not that it had an effect |
| A gated feature still fires despite the kill-switch | [06](06-debugging-methodology.md) — look for a *second implementation* before re-poking the gate |
| A value scan seeded from a script/console API returns exactly one hit | [11](11-re-anchoring-and-discovery.md) — on a **stationary** subject, uniqueness is evidence of *staleness*. The clean hit is often a dead copy nothing is writing any more. Filter by motion across ≥3 commanded states *before* counting |
| Value scan returns one hit when still, hundreds when moving | [11](11-re-anchoring-and-discovery.md) — the API value is a sparsely-refreshed mirror. Reseed from the constant buffer the GPU consumed: unit-length, high-entropy, self-validating |
| RenderDoc/apitrace "just doesn't connect" when you launch the game through it | [06](06-debugging-methodology.md) — on a storefront-wrapped game the process you launched is a throwaway stub; the real game is spawned by **pre-existing** services, so `--opt-hook-children` cannot reach it. Watch the process tree, then inject by PID on appearance |
| Hook confirmed loaded, but capture fails "uncapped command list" | [06](06-debugging-methodology.md) — D3D11 deferred contexts; needs `--opt-capture-all-cmd-lists` set **at inject time**, it cannot be enabled on a running process |
| RenderDoc's Global Process Hook is missing from the UI | [06](06-debugging-methodology.md) — hidden until **Settings → General → "Allow global process hooking"**; it is a preference, not a missing build feature |
| Injected DLL can't find a library shipped next to it | [07](07-engine-integration-safety.md) — Windows' search order uses the *host exe's* folder, not yours |
| Your rebuild didn't replace the DLL | [07](07-engine-integration-safety.md) — Windows won't hot-swap a loaded image; the file is locked |
| Mod installed correctly, game runs, feature silently absent | [15](15-teardown-il2-1946-vr.md) — on a load-order mod framework, another mod shipping the **same class/asset name** shadows yours and it fails *open*. Enumerate what actually resolved |

## "It worked, then it broke"

| What you're seeing | Go to |
|---|---|
| Worked before, broken now, code looks fine | [06](06-debugging-methodology.md) — check cheap environmental causes (desktop refresh rate, runtime reprojection) **before** bisecting |
| A "recovery" revert made things worse | [05](05-assets-and-materials.md) — revert has the same blast radius as a forward experiment; isolate to the one flag |
| A working narrow fix regressed things when widened | [14](14-render-pass-hazard-atlas.md) — widening is a *new experiment*, not a generalisation |
| A value drifts or grows every frame | [07](07-engine-integration-safety.md) — you're reading your own output back as fresh input |

## "It looks wrong in the headset"

| What you're seeing | Go to |
|---|---|
| Artifact appears in stereo but never appeared flat | [14](14-render-pass-hazard-atlas.md) — **infrastructure until proven content.** Check whether the suspect buffer is per-eye or a singleton before touching shader logic |
| Shading swims with your head instead of sticking to surfaces | [14](14-render-pass-hazard-atlas.md) — a mono screen-space buffer sampled with per-eye UVs |
| Ghosting / trails / motion-blur wrongness | [14](14-render-pass-hazard-atlas.md) — temporal effects under alternate-eye; the "previous frame" is the other eye |
| Subtle per-eye difference in grain or noise | [14](14-render-pass-hazard-atlas.md) — a once-per-frame mutable packet double-advancing |
| Captured a frame to check the render and it landed mid-sequence | [06](06-debugging-methodology.md) — a single frame under alternate-eye is *arbitrary*. Capture a hotkey-armed burst: [A5.7](a5-flat-harness-stats.md) |
| Can't tell whether eye alternation is actually happening | [06](06-debugging-methodology.md) — window captures are phase-locked and can never show it. Burst + labelled filenames: [A5.7](a5-flat-harness-stats.md) |
| Geometry doubled, mirrored, or phantom | [09](09-d3d11-openxr-injection.md) — two projection bases in one frame |
| Weapon/hand at the wrong angle, and fixing one angle breaks another | [02](02-viewmodels-and-hands.md) — you are correcting a wrong *frame* per-axis. Stop and find the frame |
| Bone getter/accessor census exposes only a few tiny rigs | [RE-004](pattern-catalog.md#re-004) — a getter is a consumer-demand trace. Find and census the writer |
| Bone/array writes succeed and read back, but no pixels move | [11](11-re-anchoring-and-discovery.md#writer-census) — poke one live candidate unmistakably; writable does not mean render-authoritative |
| Bone poke flickers for isolated frames and snaps back | [11](11-re-anchoring-and-discovery.md#writer-census) — correct target, wrong writer order; win the evaluate/last-writer race |
| Model correct at rest, skews as you rotate | [02](02-viewmodels-and-hands.md) — quaternion/matrix conversion typo; error is proportional to angle. Code + the test that catches it: [A1](a1-rotation-and-frames.md) |
| Viewmodel drawn twice, or bleeding between eyes | [02](02-viewmodels-and-hands.md), [09](09-d3d11-openxr-injection.md) |
| **The two eyes don't line up / won't fuse** | [09](09-d3d11-openxr-injection.md#the-two-eyes-dont-line-up-a-five-minute-differential-diagnosis) — **start here.** Four projects hit this. Ask first: does the offset change with distance? |
| Everything offset by the same angle regardless of depth | [09](09-d3d11-openxr-injection.md#the-two-eyes-dont-line-up-a-five-minute-differential-diagnosis) — submitted FOV ≠ rendered FOV. Not an IPD problem |
| FOV looks plausible but is a few degrees out | [09](09-d3d11-openxr-injection.md#the-two-eyes-dont-line-up-a-five-minute-differential-diagnosis) — halved in degrees instead of tangent space |
| Vertical offset between the eyes | [09](09-d3d11-openxr-injection.md#the-two-eyes-dont-line-up-a-five-minute-differential-diagnosis) — always a bug; vertical disparity cannot be fused |
| Vertical offset worse at the edges than the centre | [09](09-d3d11-openxr-injection.md#the-two-eyes-dont-line-up-a-five-minute-differential-diagnosis) — toe-in keystone. Translate the eyes, don't rotate them |
| Image doubled and diverging outward, depth inverted | [09](09-d3d11-openxr-injection.md#the-two-eyes-dont-line-up-a-five-minute-differential-diagnosis) — eyes swapped or offset sign inverted |
| Flipping the eye-swap setting changes nothing | [09](09-d3d11-openxr-injection.md#the-two-eyes-dont-line-up-a-five-minute-differential-diagnosis) — the flag is a no-op: it flips the label then derives the offset from the flipped label |
| Separation far too wide, eyes ache, can't fuse near objects | [09](09-d3d11-openxr-injection.md#the-two-eyes-dont-line-up-a-five-minute-differential-diagnosis) — IPD units, or world scale applied twice |
| Stereo works but looks flat | [09](09-d3d11-openxr-injection.md#the-two-eyes-dont-line-up-a-five-minute-differential-diagnosis) — eye offset dropped or scaled to ~0 |
| Geometry missing at the edges when you lean | [01](01-camera-and-tracking.md) — cull-camera ownership. You cannot render your way out of missing geometry |
| Render looks right but culling misbehaves | [15](15-teardown-il2-1946-vr.md) — you may be feeding the renderer an **asymmetric** per-eye matrix and the engine a **symmetric scalar FOV**. Two frusta, one of them wrong |
| Near geometry clips, and the clip-plane config takes effect at half what you set | [A3](a3-stereo-projection.md) — an unexplained constant factor in the depth row is a live bug wearing a tunable. Run the residual gate; a wrong near/far scores loudly |
| Eyes pull apart / won't converge / "opposite of cross-eyed" | [09](09-d3d11-openxr-injection.md#q-distance) — declared frustum vs rendered frustum; [FAIL-STR-031](failure-atlas.md) |
| Edges stretch or swim on head motion but not on stick turning | [09](09-d3d11-openxr-injection.md#q-stick-vs-head) — the same frustum-declaration fault, second presentation |
| The weapon converges but the world doesn't (or the reverse) | [STR-011](pattern-catalog.md#str-011) — the near pass has its own projection |
| `xrCreateInstance` fails with no useful message | [09](09-d3d11-openxr-injection.md#api-version-negotiation) — the runtime may implement an older API version than your SDK |
| A probe cannot name its own OpenXR error | [09](09-d3d11-openxr-injection.md#api-version-negotiation) — `xrResultToString` needs an instance |
| First pixels in the headset are milky / washed out | [09](09-d3d11-openxr-injection.md#first-pixels-gamma) — gamma encoded twice; settle it with a two-hypothesis luma read |
| It passed the simulator and failed the headset immediately | [09](09-d3d11-openxr-injection.md#permissive-substitute) — the substitute enforced less than production |
| The horizon tilts / head movement isn't stabilised | [CAM-012](pattern-catalog.md#cam-012) — three distinct defects; the symptom tells you which |
| Everything is tilted even looking straight ahead | [01](01-camera-and-tracking.md) — the recenter reference stored roll; it must be yaw-only |
| "Who called this?" answers with another tool's DLL | [06](06-debugging-methodology.md#interposing-observer) — a capture tool wraps the device and becomes the caller |
| Shared-surface creation refused on a format that looks correct | [09](09-d3d11-openxr-injection.md#format-from-surface) — read the format from the surface, not the creation parameters |
| Two objects share an address and the test cannot tell them apart | [11](11-re-anchoring-and-discovery.md#pointer-not-identity) — change the run, not the instrument |
| A gate never opens no matter how long I wait | [07](07-engine-integration-safety.md#module-presence-is-not-ownership) — a rearm running on the sampling poll |
| Switching games inside a collection breaks the mod | [HOOK-005](pattern-catalog.md#hook-005) — ownership is a fresh unique heartbeat, not module presence |
| A rebuild regresses something the change never touched | [08](08-project-process.md#irreproducible-artifact) — a post-build layer source cannot reproduce |
| The body floats off the floor in a braced or crouched pose | [CAM-013](pattern-catalog.md#cam-013) — an HMD-anchored body lifted by its own animation |
| Uninstalling doesn't stick, or files come back | [08](08-project-process.md#self-healing-uninstall) — a self-healing step restoring them |
| Updating a dependency lost a feature | [08](08-project-process.md#dependency-binary-not-version) — the feature was on a fork; count symbols |
| Rays are slightly off after cropping the submitted image | [09](09-d3d11-openxr-injection.md#subimage-fov-pair) — derive the FOV from the integer rect, not the reverse |
| A setting works in one place and is quietly applied in another | [TEST-012](pattern-catalog.md#test-012) — assert the read count in the source text |
| Near objects look soft or out of focus, far ones fine | [14](14-render-pass-hazard-atlas.md#velocity-not-temporal) — motion blur under alternate-eye, not depth of field |
| Everything passes on the desk and the headset is wrong | [09](09-d3d11-openxr-injection.md#simpler-substitute) — the substitute was simpler than the runtime |
| My metrics are all green and the tester is unhappy | [06](06-debugging-methodology.md#metric-cannot-fail) — a metric that cannot come back bad |
| Writing the camera does nothing, confirmed twice | [CAM-014](pattern-catalog.md#cam-014) — the render view is an out-parameter, not a field |
| Head-look works but freezes in cutscenes | [HOOK-006](pattern-catalog.md#hook-006) — hook the render path, not the script path |
| Shoulders start reversed or unwind slowly | [12](12-torso-calculations-and-ergonomics.md#mixed-frame-yaw) — two yaws in different coordinate frames |
| Each eye refreshes far below the frame rate | [STR-012](pattern-catalog.md#str-012) — carry the eye, do not wait for it |
| HUD edges cut off and no scale factor helps | [04](04-ui-and-hud.md#hud-cropped-not-scaled) — cropped, not mis-scaled |
| A hook installs, reports success and never fires | [07](07-engine-integration-safety.md#deferred-context-vtable) — deferred and immediate D3D11 contexts have different vtables |
| VR never recovers after alt-tab | [10](10-graphics-apis.md#device-loss-three-faults) — a latch set from a call the engine stopped making |
| Fire or particles stay mono while the world is stereo | [17](17-teardown-fc2vr-native-stereo.md#dishonored-splice) — the user-pointer draw path is a second path |
| A proxy DLL crashes on load, blaming its own logger | [07](07-engine-integration-safety.md#no-log-in-static-init) — logging from a static initialiser |
| I cannot tell which draws cause an artefact | [TEST-013](pattern-catalog.md#test-013) — ship a live kill mask over the draw classes |
| A captured screen's shell is solid but its content flashes | [10](10-graphics-apis.md#translate-dont-disable-scissor) — clips in the source viewport's coordinates |
| Hands reach correctly but forearms stretch or crease | [12](12-torso-calculations-and-ergonomics.md#endpoint-is-not-the-mesh) — the endpoint solved, the mesh did not |
| Ghidra shows almost no xrefs and looks misconfigured | [11](11-re-anchoring-and-discovery.md#dump-the-running-image) — the binary is packed; dump the running image |
| A discovery routine fails and says nothing useful | [11](11-re-anchoring-and-discovery.md#two-part-signature) — log the evidence on the failure path |
| Is this a second camera or a mirrored object? | [17](17-teardown-fc2vr-native-stereo.md#instance-format-expressiveness) — ask what the instance format can express |
| Head tilt does not tilt the stereo baseline | [12](12-torso-calculations-and-ergonomics.md#body-model-sequencing) — roll drives the eye axis, not the shoulder bar |
| Where is this engine's camera, and can I pass a second one? | [17](17-teardown-fc2vr-native-stereo.md#camera-delivery) — global, parameter, or parameter across a module boundary |
| Can I avoid injecting into this game at all? | [CAM-015](pattern-catalog.md#cam-015) — proxy a published module contract if it exports one |
| Testers disagree about how aiming should work | [INPUT-008](pattern-catalog.md#input-008) — split the axes and ship it as a setting |
| How much engine work is a VR source port really? | [18](18-beyond-the-native-injector.md#source-port-vr-layer) — measured: ~13 globals, 23 files, head orientation read once |
| A camera write runs for thousands of frames and moves nothing | [CAM-016](pattern-catalog.md#cam-016) — you are writing to a direction, not the position |
| Module version check passes but the struct offsets are wrong | [RE-008](pattern-catalog.md#re-008) — count the `rep movsd`; the version is a name, not a size |
| An audit reports the same error every run on something that is fine | [TEST-015](pattern-catalog.md#test-015) — check the metric's premise before its verdict |
| Two-process bridge: all checks pass, no message arrives | [TEST-016](pattern-catalog.md#test-016) — a self-test that only talks to itself |
| A defect only a headset can see, that every desk test passes | [TEST-014](pattern-catalog.md#test-014) — make the fixture asymmetric where the headset is |
| Choosing between alternate-eye and a same-frame two-view family | [STR-013](pattern-catalog.md#str-013) — per-view culling inverts the ranking |
| Building physical reload, and wondering what it actually involves | [02](02-viewmodels-and-hands.md#physical-reload) — the anatomy, from two shipped implementations |
| A magazine cuts through the weapon on the way in | [HAND-008](pattern-catalog.md#hand-008) — dock on the weapon, not the hand |
| A held object lags or shakes against the hand while moving | [HAND-010](pattern-catalog.md#hand-010) — lead by its own step, never by root velocity |
| About to build physical reload, and unsure where to start | [HAND-011](pattern-catalog.md#hand-011) — census the arsenal first; the schema is in ch02 |
| A reload gesture works on one weapon and not the rest | [HAND-011](pattern-catalog.md#hand-011) — the treatment must follow the implementation column |
| An animation event fires at the wrong moment for a reload | [02](02-viewmodels-and-hands.md#weapon-census) — an `eject` in a `shoot` clip is a casing |
| Automation stops for a whole session after one early error | [TEST-017](pattern-catalog.md#test-017) — the catch disabled it; a caught exception is not a handled one |
| A harness works for you and is dead for someone else | [07](07-engine-integration-safety.md#fault-permanence) — check whether it depends on a diagnostic flag |
| Building holsters, and unsure of the data model | [HAND-013](pattern-catalog.md#hand-013) — a pose, a hand, and an accept-list |
| A held object jitters, lags, or will not collide | [HAND-012](pattern-catalog.md#hand-012) — three routes, and each fails a different test |
| A grabbed object snaps into the hand or stretches away | [HAND-012](pattern-catalog.md#hand-012) — ramp the grip, clamp the motor |
| Out of buttons on the controller | [INPUT-009](pattern-catalog.md#input-009) — a stroke grammar gives 13 actions per hand |
| Grab, pull and press keep triggering each other | [HAND-014](pattern-catalog.md#hand-014) — split by distance tier, cone and hand speed |
| Reaching into clutter launches the clutter | [HAND-014](pattern-catalog.md#hand-014) — damp the neighbours while a grab starts |
| A gesture fires while the player is walking | [INPUT-010](pattern-catalog.md#input-010) — measure hand motion in room space |
| A physics body pops, explodes, or vibrates in a wall | [HAND-015](pattern-catalog.md#hand-015) — blend, clamp, and choose the losing case |
| Users report crashes on a build you never supported | [PACK-004](pattern-catalog.md#pack-004) — classify the exe before injecting |
| Crash reports from testers are just addresses | [TEST-018](pattern-catalog.md#test-018) — symbolise at fault time |
| A crash bisects to somewhere unrelated to its cause | [07](07-engine-integration-safety.md#engine-hardening) — warn where bad data is accepted, not where it faults |
| Building an interaction layer, and unsure what it needs to expose | [interaction-coverage](generated/interaction-coverage.md) — what four shipped VR mods found necessary |
| Yaw right, pitch and roll inverted | [CAM-017](pattern-catalog.md#cam-017) — a missing yaw conjugation; do not flip signs |
| Weapon swings to the wrong side when the player turns around | [CAM-017](pattern-catalog.md#cam-017) — a world-oriented column |
| An instrument says 'no change' and the wearer says otherwise | [TEST-019](pattern-catalog.md#test-019) — compare at the effect's scale; give it a NO case |
| An experiment installs cleanly and measures nothing | [TEST-020](pattern-catalog.md#test-020) — arm and value separate; refuse the wrong precondition by name |
| A headset run is the only way to tell two causes apart | [TEST-021](pattern-catalog.md#test-021) — pre-register the owner for every outcome |
| Every write matches, nothing on screen changes | [02](02-viewmodels-and-hands.md#identity-latch) — the pinned object was recreated |
| Two builds share a timestamp | [08](08-project-process.md#sibling-build-identity) — hash the file and its size; never the timestamp |
| An export name looked like the seam and was not | [11](11-re-anchoring-and-discovery.md#export-bracket) — a bracket exists; what passes through it is a separate question |
| Adopting a world scale from another project on the same engine | [CAM-018](pattern-catalog.md#cam-018) — derive it from shipped content; a sibling's number is a prior |
| Missing geometry in one eye, and the hazard census says clean | [14](14-render-pass-hazard-atlas.md#cpu-visibility-history) — look in the culling, not the renderer |
| A green run under the substitute, refused by the real runtime | [TEST-022](pattern-catalog.md#test-022) — pin the instrument's version too |
| Native re-entry survives a few frames then wedges | [17](17-teardown-fc2vr-native-stereo.md) — something advanced twice per frame |
| A weapon interaction zone sits behind the hand | [HAND-016](pattern-catalog.md#hand-016) — re-place the anchor against the rendered wield |
| Out of buttons, and hands need different meanings | [INPUT-011](pattern-catalog.md#input-011) — bind by hand and position, resolve by what it holds |
| A physical control is reported dead but the log says it declined | [20](20-audio-and-haptics.md#cue-policy-three-outcomes) — a refusal must be audible |
| Building physical reload for System Shock 2 specifically | [02](02-viewmodels-and-hands.md#s2q-clip-insert) — shock2quest shipped one, same game, readable source |
| Adding climbing, vaulting or any body-performed verb | [INPUT-012](pattern-catalog.md#input-012) — caps, acquisition state, and the failure case |
| A feature must handle a family of world shapes | [TEST-023](pattern-catalog.md#test-023) — bench first, one station each, one that must fail |
| A gesture behaves differently on a different headset | [03](03-input-and-locomotion.md#physical-locomotion-verb) — express it in physics steps, not seconds |
| Walking into an enemy deals melee damage | [03](03-input-and-locomotion.md#physical-locomotion-verb) — bill closing speed at the contact, not raw weapon velocity |
| Crouching lowers the view but not the hands | [03](03-input-and-locomotion.md#physical-locomotion-verb) — one head-resolved translation for the whole rig |
| Keeping an external reference clone up to date | [08](08-project-process.md#refresh-external-sources) — fetch everything, fast-forward what you will re-read |
| Most sources show `source changed` and nobody acts | [META-011](pattern-catalog.md#meta-011) — a flag that always fires is not a signal |
| Adding a second hand to a held weapon | [HAND-017](pattern-catalog.md#hand-017) — one owner, and a region rather than a socket |
| Saved poses load on desktop and are refused on Quest | [PACK-005](pattern-catalog.md#pack-005) — resolve by identity, hash is provenance |
| Aim and view disagree by an amount that depends on arm pose | [03](03-input-and-locomotion.md#one-pose-origin) — one reference yaw for every lane |
| A bone write from a render hook does nothing | [03](03-input-and-locomotion.md#one-pose-origin) — write inside the skeleton evaluation |
| A run "failed" but you are unsure the experiment even happened | [06](06-debugging-methodology.md#run-validity) — grade validity before the hypothesis |
| The fact was proven but something unrelated regressed | [06](06-debugging-methodology.md#run-validity) — keep the fact, refuse the build |
| A checker is green and you suspect it saw nothing | [META-013](pattern-catalog.md#meta-013) — clean and empty must differ |
| Which memory scalar drives which matrix element | [11](11-re-anchoring-and-discovery.md#perturbation-jacobian) — measure the derivative matrix |
| Stretched, zoomed or wrong-scale view | [09](09-d3d11-openxr-injection.md) — FoV/aspect/full-eye presentation |
| Camera through the roof / world scale absurd after startup | [01](01-camera-and-tracking.md) — a fresh reference space can report a valid-but-wrong first pose |
| Hands and camera at different "zero" | [01](01-camera-and-tracking.md) — one recenter event, consumed by every lane |

## "I can't find it"

| What you're seeing | Go to |
|---|---|
| Where do I even start on an unknown binary? | [11](11-re-anchoring-and-discovery.md) — the anchor ladder, top rung first |
| The game is old enough to have no camera object, no shaders, no reflection | [16](16-teardown-virtua-cop-2-vr.md) — check for a **renderer plugin ABI** first; then run the [four preconditions](16-teardown-virtua-cop-2-vr.md#the-four-preconditions-with-the-test-for-each) before committing to draw-stream reconstruction |
| Looking for a function | [11](11-re-anchoring-and-discovery.md) — **check the export table and for shipped script source before disassembling** |
| Prologue scan finds the wrong function | [11](11-re-anchoring-and-discovery.md) — four documented failure modes, incl. x64 REX prefixes |
| Found the symbol, hook catches nothing | [11](11-re-anchoring-and-discovery.md) — it's a thunk; internal callers bypass it |
| A struct field reads as zeros or nonsense | [11](11-re-anchoring-and-discovery.md) — classify by magnitude, not declared type |
| Two candidate structures and can't tell them apart | [11](11-re-anchoring-and-discovery.md) — find the state where the hypotheses disagree (often: standing still) |
| Graphics API entry point isn't in the import table | [11](11-re-anchoring-and-discovery.md) — dynamically loaded; find the loader's name-string cluster |
| No symbols, but a sibling binary on the same engine has them | [11](11-re-anchoring-and-discovery.md) — cross-binary function matching can carry names across. Start with Ghidra's fuzzy matching; it reads PE and 32-bit |

## "It crashed or hung"

| What you're seeing | Go to |
|---|---|
| Crash on a custom asset | [05](05-assets-and-materials.md) — structural validity ≠ semantic safety |
| **Hang** (not crash) while loading a model | [05](05-assets-and-materials.md) — sample the main thread; usually an un-remapped offset |
| Crash only when attaching a debugger | [07](07-engine-integration-safety.md) — anti-debug, attach windows |
| The whole HMD freezes but the flat game runs | [07](07-engine-integration-safety.md) — OpenXR layer budget; over- *and* under-submission both do this |
| Crash under a streaming/compositor runtime | [07](07-engine-integration-safety.md) — third-party implicit API layers in your call chain |
| Game dies when you pause it in a debugger | [06](06-debugging-methodology.md) — **you cannot pause a VR process.** Use non-pausing instrumentation |
| Process won't exit / hangs on shutdown | [07](07-engine-integration-safety.md) — an injected worker thread waiting on a signal that will never come |

## "I can't tell whether it worked"

| What you're seeing | Go to |
|---|---|
| Clean logs, no errors, but is it running? | [06](06-debugging-methodology.md) — **absence of errors is not evidence.** Count applied *and* attempted |
| Diagnostic output vanished mid-session | [06](06-debugging-methodology.md) — a shared sample budget spent by the boring case |
| An isolation test came back blank | [06](06-debugging-methodology.md) — the gate may have disabled the fallback the scene needs |
| An isolation test came back *positive* | [06](06-debugging-methodology.md) — can your mechanism itself move the measurement? Run the control — [A5.4](a5-flat-harness-stats.md) has the veto pattern |
| Image diff says "changed" and you don't trust it | [08](08-project-process.md) — your threshold is an experiment; capture a control pair in the same scene. Working stats: [A5](a5-flat-harness-stats.md) |
| Hypothesis survives several A/B toggles | [06](06-debugging-methodology.md) — stop toggling, read the pipeline state directly |
| Dismissed a lead because "the working case has it too" | [05](05-assets-and-materials.md) — does your control actually *consume* the variable? |
| Can I trust the reverse-engineered matrix? | [11](11-re-anchoring-and-discovery.md) — residual gate, and **prove your metric can see the error class**. Working gate: [A3.4](a3-stereo-projection.md) |

## "It's slow"

| What you're seeing | Go to |
|---|---|
| Framerate dropped, code unchanged | [06](06-debugging-methodology.md) — cheap environmental causes first. A round-number cap is a vsync cap |
| Perf regression appears with a feature enabled | [06](06-debugging-methodology.md) — instrumentation volume is not neutral; measure with logging off |
| Need a per-frame GPU value without stalling | [06](06-debugging-methodology.md) — async copy, map `DO_NOT_WAIT` on a later frame |
| Benchmark numbers look too good | [06](06-debugging-methodology.md) — stop the clock on *completion*, not submission |
| CPU spikes when particular scenery comes into view | [15](15-teardown-il2-1946-vr.md), [01](01-camera-and-tracking.md) — an inflated symmetric cull cone submits actors neither eye can see. Log the cull FOV against the eye tangents |
| The desktop mirror costs real frame time | [15](15-teardown-il2-1946-vr.md) — check whether it is a full scene render rather than a blit, and make it optional |

## "It makes people sick"

| What you're seeing | Go to |
|---|---|
| Which mechanics will hurt, before I build? | [01](01-camera-and-tracking.md) — mechanic triage: does it write roll? does it move the up-vector? |
| Camera seized by an animation | [01](01-camera-and-tracking.md) — yield to authored cameras; triage per mechanism |
| Turning feels bad | [01](01-camera-and-tracking.md), and [03](03-input-and-locomotion.md) for what shipped mods defaulted to |
| Should I build teleport locomotion? | [03](03-input-and-locomotion.md) — **no shipped mod in the survey did.** Snap turn is the shipped comfort lever |

## "I need working code, not a rule"

| What you need | Go to |
|---|---|
| Quaternion↔matrix, basis building, roll without gimbal, integer rotators | [A1](a1-rotation-and-frames.md) |
| Pose snapshot, cross-thread handoff, recenter epoch, settle latch, input arbitration | [A2](a2-pose-pipeline.md) |
| Asymmetric per-eye projection, eye-transform conjugation, the residual gate, depth linearisation | [A3](a3-stereo-projection.md) |
| Signature resolution, SEH wrapper, reentrancy guard, hook counters, layer census | [A4](a4-hook-safety.md) |
| Flat harness, robust noise floor, the control that vetoes a verdict, command seam | [A5](a5-flat-harness-stats.md) |
| Burst capture for alternate-eye — a single frame tells you nothing | [A5.7](a5-flat-harness-stats.md) |

## "I'm about to start something new"

| Question | Go to |
|---|---|
| What exact order should I do this in? | [Start or Unblock a VR Port](start-new-port.md) — classify authority, take the RE/source route, then rejoin the shared spine |
| The game is closed-source / needs reverse engineering | [RE-owned route](reverse-engineered-route.md) — target fingerprint through stable seam and stereo architecture |
| I can build and ship the engine/game source | [source-owned route](source-owned-route.md) — baseline, ownership map, per-frame/per-view split and fork maintenance |
| Several things are open; what actually blocks progress? | [fleet bottleneck map](bottleneck-map.md) — critical-path class, fast discriminator and current per-project next proof |
| What should my project evidence files actually contain? | [project evidence templates](project-evidence-templates.md) — copy-ready authority, address, camera, experiment, pass and handoff schemas |
| I know the problem class and want the smallest recipe | [pattern catalog](pattern-catalog.md) — stable IDs such as `CAM-001`, `XR-002`, `STR-003` |
| Has this symptom already been diagnosed? | [failure atlas](failure-atlas.md) — namespaced IDs such as `FAIL-CAM-001`; discriminator before theory |
| Which engine is mine most like? | [00](00-engine-profiles.md) |
| What has every project got wrong? | [README](README.md) — the nine lessons |
| Where do the projects agree and disagree? | [cross-engine-map](cross-engine-map.md) |
| Has another project solved this? | [cross-project-index](cross-project-index.md) |
| How do I get controller input into the game? | [03](03-input-and-locomotion.md) — **find the funnel the engine already listens on** |
| How do I structure the work? | [08](08-project-process.md) — de-risking battery, two gates, proof ladder |
| My renderer is D3D9 / D3D10 / OpenGL | [10](10-graphics-apis.md) — and resolve the D3D9 decision table *statically*, first |
| My renderer is D3D12 / command-list replay hangs | [19](19-d3d12-and-performance.md) — resource state is only one part of the recorded execution context |
| It reports headset refresh rate but still feels uneven | [19](19-d3d12-and-performance.md) — report stale/reprojected frames and prove the measured workload visually |
| Spatial audio follows the body or a moving source freezes | [20](20-audio-and-haptics.md) — tracked two-ear listener and stable emitter identity |
| My target is 32-bit and the XR runtime is 64-bit | [16](16-teardown-virtua-cop-2-vr.md) — a shipped two-process split over seqlock shared memory, incl. the crash-isolation upside |
| View blinks between true VR and a flat rectangle in space | [17](17-teardown-fc2vr-native-stereo.md) — one flag is answering both "what mode are we in" and "what just happened". Do not add hysteresis; split the flag |
| Stereo looks subtly wrong rather than broken | [17](17-teardown-fc2vr-native-stereo.md) — a mono frame may be publishing into **both** eye slots. Publish pairs atomically, hold the last good pair |
| Eye rejected in a yaw-dependent pattern, or only far from map origin | [17](17-teardown-fc2vr-native-stereo.md) — you are thresholding raw view-matrix coefficients. Decompose and validate rotation and position separately |
| Second eye disagrees with a camera you restored correctly | [17](17-teardown-fc2vr-native-stereo.md) — the engine kept observing while you held its camera and latched your transient value |
| Stereo looks right but the game runs at half speed / particles age wrong | [17](17-teardown-fc2vr-native-stereo.md) — you are re-running the *frame*, not the *world render*. The gate is a side-effect assertion, not a visual one |
| HUD or menus drawn twice, or doubled in one eye | [17](17-teardown-fc2vr-native-stereo.md) — world twice, everything else exactly once; Present exactly once |
| Rebuilt an official SDK module and the game crashes in an old CRT | [11](11-re-anchoring-and-discovery.md#an-official-sdk-can-compile-and-still-be-unshippable-the-crt-abi-wall) — CRT ABI wall. The SDK is an oracle, not a shippable artifact |
| Vtable slot index from the SDK header points at the wrong function | [11](11-re-anchoring-and-discovery.md#a-vtable-slot-can-be-a-thunk-too-and-declaration-order-is-not-slot-order) — declaration order is not slot order, and the slot may be a forwarding alias |
| Geometry is correct but motion feels wrong in the headset | [17](17-teardown-fc2vr-native-stereo.md) — check which pose you attach to the submitted frame; the rendered pose may be two XR frames behind |
| Is this a VR mod yet? / when am I done? | [08](08-project-process.md#how-vr-is-it-declare-a-completeness-tier-and-ship-to-it) — pick a completeness tier T0–T4, declare it, build to it. A project with no declared tier reads as permanently unfinished |
| How far should we take this one? | [08](08-project-process.md#how-vr-is-it-declare-a-completeness-tier-and-ship-to-it) — higher is not automatically better; a rock-solid T1 beats a broken T3 |
| Hand/interaction work is producing weird bugs | [08](08-project-process.md#how-vr-is-it-declare-a-completeness-tier-and-ship-to-it) — the tiers gate each other. T3 on a subtly-wrong T1 produces bugs that look like hand bugs |
| Which approach should I even use on this game? | [00](00-engine-profiles.md), [18](18-beyond-the-native-injector.md) — decide the *mode* first: source port, managed plugin, UEVR + companion, or native injector |
| The game is Unity — where do I start? | [18](18-beyond-the-native-injector.md) — BepInEx build must match the scripting backend (IL2CPP vs Mono) and bitness |
| It's an Unreal game and I'm writing a native injector | [18](18-beyond-the-native-injector.md) — be able to say why UEVR is insufficient first |
| World rotates wrongly after a recenter | [01](01-camera-and-tracking.md) — near-vertical headset has no usable yaw. Reject it, don't invent one |
| Shadow edges shimmer or differ between the eyes | [14](14-render-pass-hazard-atlas.md) — cascades recomputed per eye. One eye seeds, the other reuses, keyed on (pair, generation) |
| Ghosting that differs between the eyes | [14](14-render-pass-hazard-atlas.md) — temporal upscaler history is being shared across eyes |
| Pimax/canted headset needs parallel projection | [09](09-d3d11-openxr-injection.md) — consume each eye's *orientation*, not just position, and the cant handles itself |
| Engine only exposes symmetric FOV | [09](09-d3d11-openxr-injection.md) — look for a projection/optical-centre offset field; centre offset + symmetric FOV = asymmetric frustum |
| 32-bit game, OpenXR won't initialise | [09](09-d3d11-openxr-injection.md) — a 64-bit runtime registration proves nothing; check `WOW6432Node\Khronos\OpenXR\1` |
| Reticle sticks to the player's own body | [04](04-ui-and-hud.md) — skip only the player's shapes and retry; never globally disable character collision |
| I need a value the native side can't cheaply reach | [18](18-beyond-the-native-injector.md) — if the game has a scripting layer, use it as a state channel |
| Hooks cost measurable performance | [18](18-beyond-the-native-injector.md) — scope hook sets per mode and select them at launch |
| One function, several call sites, different behaviour needed | [11](11-re-anchoring-and-discovery.md) — switch on the return address, with a stock-behaviour default |
| Porting a mod to a sibling game on the same engine | [11](11-re-anchoring-and-discovery.md), [18](18-beyond-the-native-injector.md) — functions port, field offsets drift. Commit the decompiled pseudocode |
| Elbow snaps through the arm as the hand crosses a line | [02](02-viewmodels-and-hands.md) — pole-vector singularity. Needs hemisphere memory *and* a spatial fade near the cone |
| Arm IK returns NaN or nothing in some poses | [02](02-viewmodels-and-hands.md) — no deterministic final fallback for a straight bind pose with no history |
| Melee fires on reloads, sweeps and hand retractions | [02](02-viewmodels-and-hands.md) — thresholding speed magnitude. Project onto the pose's own forward axis |
| Gesture never fires and I can't tell why | [02](02-viewmodels-and-hands.md) — log `evaluatedSamples` beside peak speed: zero means time base or poses, not the threshold |
| Gesture velocity is wrong, zero, or wildly spiky | [02](02-viewmodels-and-hands.md) — you are dividing by `predictedDisplayTime`. Use a monotonic clock you control |
| Every ladder grab also throws a punch | [02](02-viewmodels-and-hands.md) — the free hand's grab must exclude melee; contexts have to be mutually exclusive |
| Jump kick only works if I jump before thrusting | [02](02-viewmodels-and-hands.md) — queue the gesture ~250 ms and let the engine's airborne flag classify it |
| Weapon becomes unsteerable during a two-handed grip | [02](02-viewmodels-and-hands.md) — the visual hand pose has leaked into the control path: hand follows weapon follows hand |
| Weapon stops dead or springs back at some hand angle | [02](02-viewmodels-and-hands.md) — a hard clamp in a tracked path reads as a wall. Compress asymptotically instead |
| Aim axis unstable when the hands are close together | [02](02-viewmodels-and-hands.md) — a direction from two tracked points needs a minimum baseline (~12 cm) or it is noise |
| Weapon flickers in and out near a doorframe or edge | [02](02-viewmodels-and-hands.md) — per-frame world rays chatter at edges. Hold the deepest hit ~90 ms |
| Weapon smears across the room after a teleport or weapon swap | [02](02-viewmodels-and-hands.md) — your follow/weight filter has no enumerated reset list |
| Recoil feels dead while the player is moving | [02](02-viewmodels-and-hands.md) — recoil is layered before the weight filter; it must come after |
| Hiding a mesh piece removed more than intended | [02](02-viewmodels-and-hands.md) — a piece is an artist grouping, not a semantic unit. Reach for the material, not the mesh |
| Near-body geometry pops for a single frame on a hitch | [02](02-viewmodels-and-hands.md) — a one-frame fallback to a different source. Hold the last good value instead |
| Engine interaction still activates what the *head* points at | [02](02-viewmodels-and-hands.md) — borrow the camera for the duration of the engine's own intersect call |
| Full-screen UI misclassified as gameplay, or the reverse | [04](04-ui-and-hud.md) — stop inferring from pixel coverage or menu focus; find the engine's game-state enum |
| Left-handed mode breaks in one specific combination | [03](03-input-and-locomotion.md) — mirror the input state once at the boundary, never per mapping |
| Leaning tilts the view but does not let you see round the corner | [03](03-input-and-locomotion.md) — the engine's own lean tilts the camera without moving the viewpoint |
| Crash at one specific cutscene, only with VR on | [03](03-input-and-locomotion.md) — one switch per group of writes, plus one that keeps the hook installed but neuters its effect |
| Can I make the engine render twice, properly? | [17](17-teardown-fc2vr-native-stereo.md) — the four preconditions for native stereo, and the build order |
| There is no camera to take over at all | [16](16-teardown-virtua-cop-2-vr.md) — reconstruct from the draw stream; recover camera motion by cancellation. Decide with [when to reach for this](16-teardown-virtua-cop-2-vr.md#when-to-reach-for-this-and-when-not-to) — the rule is *un-project when the camera was never yours to move* |
| I don't know whether to reconstruct or to hook the camera | [16](16-teardown-virtua-cop-2-vr.md#when-to-reach-for-this-and-when-not-to) — four preconditions with a fast test each, and the frustum-culling ceiling that decides it |
| My reconstructed scene is empty where I turn my head | [16](16-teardown-virtua-cop-2-vr.md#the-hard-ceiling-you-get-what-was-submitted-and-nothing-else) — not a bug. Everything outside the original frustum was culled and never submitted |
| I want to see a whole project end to end | [13](13-teardown-bioshock-vr.md) |

## Console command startup faults

| What you're seeing | Go to |
|---|---|
| Verified executor calls address zero during loading, same command succeeds later | [07: subsystem readiness](07-engine-integration-safety.md#subsystem-readiness) — capture the return site and observe the downstream callback/table initialization; executor availability is not subsystem readiness (SS2VR v3.72) |
