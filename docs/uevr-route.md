# UEVR route — when a framework already owns the stereo

**Use this route when the target is an Unreal title with working UEVR injection.** You are in
[Mode 3](18-beyond-the-native-injector.md#mode-3-framework-plus-companion-mod-let-uevr-do-the-vr):
framework plus companion mod. It changes what you build, and — just as importantly — it changes which
parts of this playbook apply to you.

Distilled from a feature-rich production companion (SystemReShock-UEVR-Plugin for System Shock Remake,
UE 4.27.2) plus the tracked UEVR corpus. `[SOURCE]`

---

## What UEVR already owns — do not rebuild any of it

Stereo rendering, projection, frame submission, the OpenXR lifecycle, HMD and controller poses, and the
fake stereo device it presents to the engine
([#uevr-fake-stereo](18-beyond-the-native-injector.md#uevr-fake-stereo)).

**This is the mode precondition, and it is the most useful thing on this page.** Roughly half of this
playbook is about acquiring exactly those things on engines that do not hand them to you. Under UEVR:

| These chapters are background, not instructions | Because |
|---|---|
| [09](09-d3d11-openxr-injection.md) D3D11 & OpenXR injection | UEVR owns the device, the swapchain and the submission |
| [10](10-graphics-apis.md) Graphics APIs | you are not hooking a graphics API |
| [11](11-re-anchoring-and-discovery.md) RE anchoring & discovery | you have UE reflection and a generated SDK; you are not pattern-scanning for a camera |
| [A3](a3-stereo-projection.md) Stereo projection | the projection is not yours to derive |

Read them when something underneath you misbehaves. Do **not** read a recipe from them as a thing to
implement — a recipe that assumes you own the render path will quietly mislead you, and that
mode-mismatch is a more dangerous failure than not finding the page at all.

## The two layers — and the declarative one comes first

A UEVR profile is **not** just a DLL. It has a declarative layer that solves a surprising amount with no
code at all, and most of what people write plugins for belongs in it.

**Declarative — UObjectHook state and property overrides, addressed by UE object path:**

```text
uobjecthook/<hash>_mc_state.json   attach a component to a motion controller
uobjecthook/<hash>_props.json      override properties on an object
uobjecthook/camera_state.json      bind the VR camera to a component, with an offset
```

Three real examples from the production profile, each replacing code:

- The **camera** bound by path to `Acknowledged Pawn > Components > ArrowComponent AnimCameraPosition`
  with a small Z offset — the engine already had an arrow marking the camera position.
- The **headlamp** attached to hand 1 (`SpotLightComponent HeadlampLight`, offset `0, -10, 40`,
  `permanent: true`) — a light follows your hand with no plugin involvement.
- An **idle animation silenced** by overriding `RateScale` to `0` on the equipped weapon's `IdleSequence`
  — the cheapest way to stop an engine animation fighting a hand pose you are driving.

**Imperative — a C++ plugin against `uevr/API.h` plus a generated UObject SDK.** Reach for it only for
game semantics the declarative layer cannot express.

> **Measured, and it reframes the job:** in ~6,000 first-party lines of a feature-rich companion, the
> UEVR API surface actually used is tiny — a handful of `param()` calls, `uevr::Plugin`,
> `uevr::API::UStruct`. Everything else is written against the **game's own UObject graph** through the
> generated SDK. A UEVR companion is therefore mostly **UE game-code modding that happens to run inside
> UEVR's process**, not framework extension. Budget for UE gameplay/UMG/animation knowledge, not for
> graphics work. See [UEVR-001](pattern-catalog.md#uevr-001).

## What is still yours, and where it lives

Everything downstream of "there is a correct stereo image" — which is most of the actual work:

| The problem | Route |
|---|---|
| Game UI and HUD into 3D, widgets onto hands | [04](04-ui-and-hud.md), [UEVR-003](pattern-catalog.md#uevr-003) |
| Hands, arms, full-body IK, weapon attachment | [02](02-viewmodels-and-hands.md), [12](12-torso-calculations-and-ergonomics.md) |
| Gestures, physical interaction, holsters, locomotion, comfort | [03](03-input-and-locomotion.md), [02](02-viewmodels-and-hands.md#holsters-and-grab) |
| Physical interaction breaking the game's own rules | [HAND-018](pattern-catalog.md#hand-018) — read this before shipping physical grab |
| Per-game-state VR behaviour (cinematics, menus, cyberspace) | [UEVR-002](pattern-catalog.md#uevr-002) |
| Host-game settings the mod must force | [08](08-project-process.md#host-settings-policy) |
| Temporal, per-eye and render-pass hazards you inherit | [14](14-render-pass-hazard-atlas.md) |
| Shipping a profile that includes assets | [08](08-project-process.md), [FAIL-PACK-019](failure-atlas.md) |

## Three hazards specific to this route

**A profile that ships assets has two artifacts that must stay in sync.** If your profile carries PAK
files alongside the DLL, the pair is version-coupled with **nothing enforcing it** — the production
profile's README has to tell users in bold to re-copy PAKs after every update, and warns that mismatched
versions break the mod. Stamp a version into both and refuse to run on a mismatch; see
[FAIL-PACK-019](failure-atlas.md).

**Assets are also how you get code loaded.** To make a custom Blueprint class resident, the production
profile **hard-references it from a modified AnimBP shipped in a PAK** — the class is loaded because an
asset the game already loads points at it. That is the UE form of
[#engine-sanctioned-loading](18-beyond-the-native-injector.md#engine-sanctioned-loading), and it is the
real reason the PAKs and the DLL are coupled.

**Object paths are the addressing scheme, so they are the fragility.** Declarative state is keyed to
exact UE object paths; the production profile is build-specific and explicitly does not support the GOG
or demo builds. Treat a path like an address: record the build it was resolved against
([META-014](pattern-catalog.md#meta-014)).

## When source access arrives, you change mode

Getting engine source moves you from Mode 3 to
[Mode 4 — source ports](18-beyond-the-native-injector.md#mode-4-source-ports-when-the-developer-released-the-engine)
and the [source-owned route](source-owned-route.md). Two consequences worth planning for now:

- **On UE 4.27+ the likely answer is activation, not implementation.** The engine ships OpenXR support;
  with source you shape and enable the engine's own XR path rather than injecting a stereo device. This
  playbook's rule for that case is
  [#engine-native-xr](18-beyond-the-native-injector.md#engine-native-xr) — *when the engine already has
  XR, the mod is activation, not implementation.*
- **The UEVR mod becomes an oracle, not an architecture.** It remains the best available answer to "what
  should this feel like, and what did someone already solve?" — a feature checklist and a behavioural
  reference to diff against. Its findings stay valid even when its mechanism stops being yours.

## The eye index is not a constant {#uevr-view-index}

A UEVR plugin that touches per-eye state has to know which eye it is in, and the answer depends on a
flag. UVOSuit's `on_post_calculate_stereo_view_offset` resolves it as **left = index 0 when
`is_double`, otherwise index 1**, with right as 1 or 2 correspondingly, because the non-double path
carries a centre view at index 0. `[SOURCE]` UVOSuit (MIT).

Meanwhile its OpenXR-side hook indexes `views[0]` and `views[1]` as left and right unconditionally,
because that array is the runtime's and has its own convention. **So one plugin holds two different
index conventions at once**, and both are correct only because each is used against the API it came
from. Getting either wrong swaps the eyes, which looks like a rendering bug and is a one-character fix
you will not find by staring at the render code.

Write the mapping down once, in a named helper, and never index a view array inline.

