# Audio & Haptics — the listener is another tracked camera

Audio is often left unchanged because a flat game already “has 3D sound”.
That can be acceptable, but it should be an explicit compatibility decision.
In VR the listener has a tracked position and orientation independent of body
yaw, roomscale can move it without moving the pawn, and UI/haptics require
clear semantic ownership.

The reference implementation here is Shock2Quest’s Rust audio system
`[SOURCE]`, with haptic event lessons from FEAR VR `[SOURCE]/[HEADSET]` and
the in-house interaction systems.

## First choose ownership: steer or replace

Prefer the game’s existing audio engine when it exposes a listener transform,
world emitters, channel priorities, occlusion and environmental processing.
Steer its listener with the same transformed HMD basis used by rendering.

Replace or supplement it only when:

- source-port/recreation work already owns decoding and mixing;
- the game listener cannot be detached from the body/camera;
- the engine emits stereo-baked or listener-relative audio incorrectly;
- a separate UI/narration/haptic lane is required.

Replacing playback also means inheriting streaming, channel limits,
preemption, looping, sample formats, environmental zones, save/load behavior
and device recovery. “Play a WAV at a position” is not the whole system.

## Treat the listener as a pose consumer

The correct dependency is:

```text
OpenXR head pose
  -> recenter/reference-space transform
  -> engine-world transform + one unit conversion
  -> listener basis
  -> left ear / right ear
```

The audio frame should declare which pose generation it consumed. It need not
run at render frequency, but using body origin while rendering from a translated
HMD creates a cross-system mismatch.

For head center (H), normalized head-right vector (R), and ear separation
(d):

```text
leftEar  = H - R * d/2
rightEar = H + R * d/2
```

Use the runtime/physical tracking scale. Do not multiply eye separation again
by a gameplay IPD setting.

### Roomscale and authored camera states

Decide explicitly:

- **Normal play:** ears follow tracked head translation and rotation.
- **Cutscene/authored camera:** either remain HMD-owned for comfort or follow
  the authored listener under a documented transition policy.
- **Pause/system UI:** world may freeze while head/listener continues.
- **Death/possession/remote camera:** name whether audio belongs to player body,
  HMD, viewed entity or cinematic camera.

Silent ownership switching is the audio version of a camera snap.

## Moving emitters need identity, not one-time positions

Shock2Quest stores positional sinks with a stable source key and refreshes the
emitter from live entity position during each audio update `[SOURCE]`.

The transferable pattern:

1. create a sound with an opaque handle;
2. optionally attach a stable entity/source ID;
3. on update, resolve the source ID to its current world position;
4. update emitter and both ears in the same unit system;
5. if the source disappears, choose stop, finish-at-last-position or detach;
6. remove completed sinks and retain loop/channel semantics.

Without step 3, engine hum, projectiles and attached voices freeze at their
spawn locations even though one-shot sounds appear correct.

## Convert units exactly once

Shock2Quest converts both emitters and ear positions through the same
`SOUND_SCALE_FACTOR` before passing them to `rodio::SpatialSink`
`[SOURCE]`. The numeric factor is project-specific; the invariant is not:

- source and ears use the same world-to-audio transform;
- orientation axes use the same handedness;
- scaling is not repeated at call sites;
- listener-relative audio bypasses world scaling.

Test with sources at known 1 m, 2 m and left/right offsets. A plausible pan does
not prove correct distance attenuation.

## Four audio lanes

| Lane | Position policy | Examples | Common error |
|---|---|---|---|
| World spatial | World emitter + tracked ears | enemies, machines, impacts | Head/body mismatch or frozen emitter |
| Listener-relative | Non-spatial or fixed head-local mix | UI, radio narration, accessibility cues | Accidentally attenuated/panned as world audio |
| Environment/ambience | Zone/bed policy, usually looping | wind, room tone, machinery beds | Re-appending loops with audible gaps |
| Music | Non-spatial authored state machine | score/cues | Restarting on level/pause transitions |

Shock2Quest moved listener-relative playback to a regular sink while preserving
the prior centered gain. Its old midpoint `SpatialSink` applied 0.75 to both
channels, so “replace it with a normal sink” required carrying that audible
baseline forward `[SOURCE]`. This is a good migration lesson: record the old
mix contract before cleaning up its implementation.

## Preserve channels and preemption

Flat engines often use named channels so a new voice line, weapon loop or UI
cue replaces the previous sound. Shock2Quest records channel-to-last-handle and
returns preempted handle IDs so diagnostics can close the earlier play even
when no explicit stop call occurred `[SOURCE]`.

For injected mods:

- prefer the engine’s channel/event route;
- if wrapping playback, log play, stop, natural completion and preemption;
- make looping live inside the source/mixer rather than periodically
  re-appending after it becomes empty;
- preserve authored gain/pan and priority.

Failure to record implicit preemption makes audio logs claim that sounds are
still playing long after the player stopped hearing them.

## Haptics begin at accepted game events

Triggering haptics from a raw controller edge is easy and often wrong:

- empty weapon still vibrates;
- blocked melee vibrates;
- rejected interaction vibrates;
- dual weapons vibrate the wrong hand;
- repeated automatic fire produces one long or missing pulse.

FEAR VR requests a pulse from the Retail fire-vector path, which runs once for
each accepted shot; empty-magazine trigger pulls therefore produce no haptic,
and dual pistols target the hand that actually fired `[SOURCE]/[HEADSET]`.

The hierarchy:

1. physical input proposes an action;
2. semantic/game system accepts or rejects it;
3. accepted event emits a haptic request with logical hand, amplitude,
   duration/frequency and event ID;
4. handedness/output mapping converts logical hand back to physical controller;
5. OpenXR host calls `xrApplyHapticFeedback`.

Contact haptics should similarly derive from the engine’s collision/contact
record where possible, not controller speed alone. Motion without contact is
not an impact.

## Haptic transport is a reverse lane

When a 64-bit OpenXR host and 32-bit game client are separate, input flows into
the game while haptics flow back out:

```text
OpenXR actions -> versioned input snapshot -> game semantic mapping
game event -> versioned haptic request -> OpenXR output action
```

Give haptic requests their own sequence number and freshness/consumption
policy. Do not reuse an old pulse after reconnect. If transport or runtime is
unavailable, drop haptics while leaving gameplay unchanged.

## Device and lifecycle handling

Audio output and haptics can disappear independently of the renderer:

- default Windows audio device changes;
- Bluetooth/USB device reconnects;
- Android activity pauses/resumes;
- OpenXR session loses focus;
- active interaction profile changes;
- controller becomes untracked;
- save/load destroys emitter objects.

Decide:

- whether mixer recreation preserves active loops/cues;
- whether world audio continues when XR is visible but unfocused;
- that haptic output stops immediately outside the valid focused/action state;
- how emitters are rebound by stable entity IDs after load.

Do not let audio-device recovery block the OpenXR frame loop.

## Audio and haptic validation matrix

| Test | Expected proof |
|---|---|
| Rotate head, body fixed | World source pans with head basis; UI remains centered |
| Translate head roomscale, pawn fixed | Distance/pan follows head without moving emitter |
| Move attached emitter | Logged entity ID remains; emitter position updates |
| Source destroyed mid-loop | Declared stop/detach policy occurs once |
| Enter pause/menu | Music/ambience policy is stable; head-relative UI remains correct |
| Lose XR focus while holding trigger | Haptics stop; no stale replay on focus return |
| Fire empty weapon | No shot haptic |
| Automatic fire | One bounded request per accepted shot or declared envelope |
| Switch handedness | Logical weapon event reaches the physical weapon hand |
| Audio device reconnect | Mixer recovers or fails softly without XR stall |
| Save/load | Persistent loops rebind or restart under documented policy |
| 1 m / 2 m known source | Unit conversion and attenuation are plausible and logged |

Headphones are required for subjective spatial acceptance, but much of the
ownership contract is desk-testable: ear algebra, unit conversion, source
identity, channel preemption, haptic routing and stale-transport behavior.

## Minimum audio ownership document

For each project, write `AUDIO_OWNERSHIP.md` with:

- listener source and pose generation;
- world-to-audio transform and scale;
- authored-camera/cutscene policy;
- world/listener/environment/music lane classification;
- moving-emitter identity and destruction behavior;
- channel/preemption rules;
- device recovery;
- haptic event sources and hand mapping;
- desktop tests and headset acceptance matrix.

That turns “the original audio seems fine” into a reviewable engineering
decision rather than an unexamined omission.
