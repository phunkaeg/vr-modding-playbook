# Coverage dashboard

**Generated deterministically by `tools/coverage.py` from `sources.yml` (ledger updated 2026-09-03) plus a filesystem scan. Do not edit by hand.**

This page makes both knowledge gaps and stale reviews visible. `Last change` and `current revision` are measured; review depth, evidence and `reviewed revision` are human/agent judgements.

| Grade | Meaning |
|---|---|
| `SPEC` | normative API fact |
| `SOURCE` | read in the project's own source |
| `STATIC` | binary / static reverse engineering |
| `LIVE` | observed at runtime |
| `HEADSET` | accepted in a headset |
| `AUTHOR` | the author's claim only |
| `INFERENCE` | hypothesis, not established on this target |

Coverage mix uses `F / P / S / NR / —` = full / partial / skimmed / explicitly not reviewed / no entry.
Fleet `authority` and external `vehicle` are different controlled axes. `tier` is achieved; `tier_target` is optional intent (fleet only).
External `Tier` and `Rung` are **inferred from the review**, not measured by us — `[INFERENCE]` unless the source states it. `—` means not assessed; `?` means assessed as indeterminable, which is the honest answer for a binary-only source.
A full `source_integration` review counts as source-owned coverage only for a `source-port` or `engine-recreation` vehicle.

## Named gaps — material identified but not yet harvested

| Area | Source | What is sitting there |
|---|---|---|
| `hands_interaction` | **Buffout4 NG-64880-1-38-3-1785297452** | Not an interaction mod - it is the FIELD OPERATIONS layer, and included in the interaction-coverage comparison for contrast. |
| `hands_interaction` | **FRIK 78.2 53464 v0.78.2 2026-08-17T16-42Z 86DAb33jN** | REGISTERED NOT REVIEWED 2026-09-05. FRIK - the Fallout 4 VR body and holster mod, VRIK's counterpart. Distribution is binary (F4SE plugin plus meshes/materials, 73 MB); the SOURCE is upstream on GitHub and the runtime config lives in Documents\My Games\Fallout4VR\FRIK_Config, so neither is in this tree. Only README.txt has been read. |
| `hands_interaction` | **Fallout 4 Script Extender VR (F4SEVR)-42159-0-6-21-1719284892** | F4SEVR 0.6.21. src/ read selectively 2026-09-05 (150 .h / 144 .cpp; f4se_loader_common) -> ch08 #loader-preflight and PACK-004. The transferable part is the LOADER, not the game layer: IdentifyEXE maps the target read-only and classifies it by PE section (a UPX0 section means packed, a Steam section means wrapped; four outcomes, and the packed case is refused BY NAME), then compares versions three ways - older, NEWER than supported, and right version but wrong build branch - each with its own actionable message. The newer-than-supported case is the one that happens to every user the day the game updates. Version comes from the version resource rather than a file hash. The game-structure layer (BS*/Game*) was not read. |
| `hands_interaction` | **Main Wabbajack 20.0 96013 20 2026-08-28T01-06Z bnEVTOJ7D** | REGISTERED NOT REVIEWED 2026-09-05. A single 694 MB Wabbajack modlist archive, not a mod. Kept as a source only because it names a working Fallout 4 VR stack. |
| `packaging_deploy` | **Talemann-RE4** | Inno Setup installer that refuses to run without RE4 present; the user installed it against a renamed stand-in. Ships REFramework Lua/JSON plus upscaler and plugin DLLs beside the game. |
| `re_discovery` | **Dishonored-VR** | REGISTERED NOT REVIEWED 2026-09-02. ALREADY MINED by the in-house DishonoredVR project (2026-09-02), which took the render path instead and avoided its blockers - read for method and negative results, not as an open task. GingasVRFO/Dishonored-VR is a SEPARATE VR conversion of the SAME GAME as the in-house DishonoredVR project. A d3d9.dll proxy built on a FORKED DXVK, with true stereo, 6DoF, motion controls, roomscale and a hand-aimed Blink. DISCONTINUED and explicitly offered for pickup (author burned out on unreproducible reports). Its 13 numbered fork-patches read as a complete rung-2 development history: M2 frame-map instrumentation, M3 stereo splice per-eye draw replay, mirrored-VP skip, world-quad splice via a c6 identity test, depth-test state REPLACING that c6 heuristic, an explicit revert to proven M3.1, measured gates, live projection scales, live writable separation and convergence, per-draw splice verdicts, world-space UP effects (the fire fix), and the Blink marker. The real payload is dllmain.cpp (~23k lines of in-game research log); its negative results are worth more than its code. |
| `re_discovery` | **Quake2Quest** | REVIEWED 2026-09-02. Team Beef (drbeef), built on Yamagi Quake II, uses OpenXR, active (2026-06-16). VR code is ISOLATED at Projects/Android/jni/Quake2VR - no diff needed. Same author as JKXR, so likely shares its house style. Yamagi keeps the renderer split (refresh/gl1,gl3,soft + ref_shared.h), so id's ref_gl/ref_soft seam survives to 2026. Android/Quest, so the platform layer does not transfer to a Win32 injection; the engine integration does. |
| `re_discovery` | **quake2vr** | REVIEWED 2026-09-02. dghost/quake2vr, archived 2021. Full Q2 VR source port on KMQuake II + RiftQuake, libOVR 0.2.5 (pre-OpenXR). Stated features map onto playbook lanes: projected HUD/2D UI, decoupled view and aiming. Diff baseline is KMQuake II, NOT id's tree - diffing against id-Software/Quake-2 mixes decades of non-VR modernisation. |
| `stereo` | **Dishonored-VR-fork** | REGISTERED NOT REVIEWED 2026-09-04. In-house fork of the shipped external mod, carrying local commits (Meta Link OpenXR backend selection; build.sh portability). The 52-patch upstream series is already distilled in ch17 #dishonored-splice; this tree adds the fork's own changes, which are not yet read. |
| `stereo` | **FUS** | REGISTERED NOT REVIEWED 2026-09-05. A Wabbajack modlist/preset rather than a mod: README, images, a bundled openvr_api.dll and a Mantella folder. Kept as a source only because it names a working VR mod stack. |
| `stereo` | **Fallout-New-Vegas-FNVR** | NOT HARVESTABLE AS SHIPPED: 'Fallout New Virtual Reality' is a 12 KB FNVR.esp plus a 3 KB .7z - a plugin, not a native VR conversion, and no source. What IS readable in this directory is xNVSE, the New Vegas Script Extender, which is general modding tooling rather than a VR implementation. Extract the archive and re-assess only if the script-extender route to VR becomes relevant to a project. |
| `stereo` | **GRAND-alien-isolation** | BINARY ONLY: XINPUT1_3.dll proxy. Built on Nibre's MotherVR. No source to read. |
| `stereo` | **HIGGS 1.10.10-43930-1-10-10-1768263289** | REGISTERED NOT REVIEWED 2026-09-05. HIGGS - Hand Interaction and Gravity Gloves. The reference implementation of physical grabbing in a shipped VR title: grab, throw, two-handed hold, weapon interaction. Carries a Source/ tree. Read 2026-09-05: higgs_vr.ini (593 settings) and the Papyrus API. The C++ core is binary. |
| `stereo` | **IRON-NEST-VR** | BINARY ONLY: managed code driving OpenXR and D3D11 directly via Silk.NET rather than through Unity XR. No source. |
| `stereo` | **PLANCK 0.8.1 66025 0.8.1 2026-07-30T03-35Z 4t2yDcbYt** | REGISTERED NOT REVIEWED 2026-09-05. PLANCK - Physical Animation and Character Kinetics. Read 2026-09-05 (activeragdoll.ini, 758 settings, plus the Papyrus API) -> ch02 #physics-bodies, ch03 #roomspace-velocity, HAND-015, INPUT-010. Taken: yankRequiredHandSpeedRoomspace, which names the axis that stops player locomotion from satisfying a hand-speed gate - the most transferable finding here. Checked against SS2VR manualReload rather than assumed: that code is already immune, because every quantity in it is a difference between two tracked hands, which cancels locomotion, turning and the play-space origin at once. INPUT-010 now ranks that formulation above room space; blend rather than swap between animation and physics, with separate blends for entering, leaving, getting up and recomputing world-from-model, and constraint parameters per PHASE; clamped bone velocities plus two chosen degradation paths for when physics cannot win (warp back beyond a distance, phase through with an alpha fade beyond an intersection depth, larger in combat); active ragdoll as a distance-gated LOD; cooldowns on every physical event because contact is continuous; THREE separate ignore lists (general, aggression, ragdoll collision) rather than one; and a consequence model - accumulated aggression with three thresholds and dialogue, stamina cost, speed reduction by race size, and intent inferred from aggressionRequiredHandWithinHmdConeHalfAngle so brushing past someone while looking away is not an assault. The C++ core is binary. |
| `stereo` | **REFramework** | REGISTERED NOT REVIEWED 2026-09-04. praydog REFramework, full source (139 MB, upstream github.com/praydog/REFramework). This is THE framework that supplies VR to RE Engine titles and the direct upstream of Talemann-RE4 - which is why it arrived. Nothing in it has been read yet; it is registered so an empty search result cannot read as absence. |
| `stereo` | **ReclaimerVR** | NOT HARVESTABLE: the checkout contains a README and nothing else. Third Halo MCC entry by name only. |
| `stereo` | **SkyrimVR FBT 185070 1.0.3 2026-07-22T11-37Z HZCMOyLlG** | REGISTERED NOT REVIEWED 2026-09-05. Full-body tracking support (SKSE plugin only, no source in the tree). |
| `stereo` | **Sterallax6DOF-silksong** | NOT HARVESTABLE without RE: a single DLL, no source, no config, no readme. Retained in the ledger because 6DOF applied to a 2D game is a conversion class with no other example here - worth an RE pass if that class ever matters. |
| `stereo` | **SubmersedVR** | NARROW PULL: produces no stereo, XR lifecycle or perf work; forces Seated and hard-snaps the rig each frame. |
| `stereo` | **Talemann-RE4** | Not a stereo mod. REFramework supplies VR; this supplies the HANDS. Installed build is RE4VR_2.0_Setup.exe; the mod is ~31k lines of Lua under reframework/autorun plus JSON data under reframework/data/re4_vr. |
| `stereo` | **VRIK Player Avatar 23416 0.8.6 2026-07-12T13-00Z Yj6wQRIkO** | REGISTERED NOT REVIEWED 2026-09-05. VRIK Player Avatar. Full-body IK avatar and, more importantly here, the mod that established the BODY-ANCHORED HOLSTER paradigm most VR mods now copy - which ch02's holster guidance and RE4VR's Spine_1 anchoring both descend from. Ships Scripts/, meshes/, an .esp. |
| `stereo` | **XIII2003-vr-mod** | BINARY ONLY: ships D3DDrv.dll plus CONTRIBUTING/CREDITS/README and no source - an Unreal render-device replacement. This is the MOD repo of the six-repository family whose research repo (XIII2003-vr-external-research) is already harvested into ch18 #stock-cheat-commands, so the structure is documented even though the implementation is not. |
| `ui_hud` | **MELE-VR** | HDR must be off or the headset image is blue/doubled (FAIL-STR-012). Binary only - no source. |

## External coverage by area

| Area | full | partial | skimmed | not reviewed | no entry |
|---|--:|--:|--:|--:|--:|
| `stereo` | 19 | 21 | 14 | 33 | 16 |
| `xr_lifecycle` | 6 | 7 | 0 | 46 | 44 |
| `xr_input` | 4 | 0 | 4 | 46 | 49 |
| `camera_tracking` | 12 | 13 | 1 | 37 | 40 |
| `render_hazards` | 5 | 9 | 1 | 13 | 75 |
| `ui_hud` | 5 | 13 | 5 | 40 | 40 |
| `hands_interaction` | 6 | 12 | 5 | 32 | 48 |
| `input_locomotion` | 2 | 4 | 1 | 13 | 83 |
| `performance` | 8 | 8 | 3 | 40 | 44 |
| `audio` | 1 | 1 | 0 | 50 | 51 |
| `packaging_deploy` | 6 | 23 | 18 | 25 | 31 |
| `re_discovery` | 14 | 14 | 5 | 32 | 38 |
| `source_integration` | 2 | 8 | 7 | 33 | 53 |

⚠ = **no source in this group has been reviewed in full for this area.**

## Fleet harvest coverage by area

| Area | full | partial | skimmed | not reviewed | no entry |
|---|--:|--:|--:|--:|--:|
| `stereo` | 5 | 3 | 0 | 2 | 0 |
| `xr_lifecycle` | 3 | 3 | 0 | 1 | 3 |
| `xr_input` ⚠ | 0 | 3 | 1 | 2 | 4 |
| `camera_tracking` | 6 | 4 | 0 | 0 | 0 |
| `render_hazards` | 6 | 3 | 0 | 0 | 1 |
| `ui_hud` | 3 | 1 | 0 | 1 | 5 |
| `hands_interaction` | 3 | 1 | 0 | 2 | 4 |
| `input_locomotion` | 4 | 1 | 1 | 2 | 2 |
| `performance` ⚠ | 0 | 5 | 0 | 2 | 3 |
| `audio` ⚠ | 0 | 3 | 0 | 2 | 5 |
| `packaging_deploy` | 5 | 3 | 0 | 1 | 1 |
| `re_discovery` | 8 | 2 | 0 | 0 | 0 |
| `source_integration` | 1 | 3 | 0 | 0 | 6 |

⚠ = **no source in this group has been reviewed in full for this area.**

## External sources

| Source | Status | Engine | Delivery vehicle | Tier | Rung | Ch | Files | Code | Docs | Last change | Freshness | Area completeness |
|---|---|---|---|:--:|:--:|--:|--:|--:|--:|---|---|---|
| **Aliens-Versus-Predator-VR** | external reference | AvP Classic (1999) via the NakedAvP source port | source-port | T2 | ? | 18 | 1019 | 790 | 4 | 2026-08-29 | ⚪ unpinned | 0F / 0P / 3S / 8NR / 2— |
| **anvilengine2vr** | external reference | AnvilNext 2.0 | native-injector | — | — | 18 | 51 | 40 | 3 | 2026-08-22 | 🟩 current | 1F / 1P / 2S / 0NR / 9— |
| **BendyVR** | external reference | Unity | managed-plugin | — | — | 18 | 94 | 56 | 1 | 2025-06-26 | 🟩 current | 0F / 0P / 1S / 0NR / 12— |
| **BF2VR** | external reference | Frostbite | native-injector | — | — | 18 | 28 | 16 | 2 | 2026-08-25 | 🟩 current | 3F / 2P / 1S / 2NR / 5— |
| **bfbc2-vr** | external reference | Frostbite 1.5 | native-injector | T2 | R3 · alternate-eye | 14 | 60 | 37 | 14 | 2026-08-28 | 🟥 source changed | 2F / 4P / 0S / 5NR / 2— |
| **BFVR-Battlefield-1942** | external reference | Refractor | native-injector | — | — | — | 492 | 363 | 31 | 2026-08-26 | 🟩 current | 4F / 2P / 0S / 0NR / 7— |
| **Bioshock-Remastered-VR** | external reference | Unreal 2.5 fork (BioShock Remastered, 32-bit) | native-injector | T3 | R3 · alternate-eye | 13 | 112 | 59 | 37 | 2026-08-28 | ⚪ unpinned | 2F / 6P / 0S / 3NR / 2— |
| **bioshock-trilogy-vr** | external reference | UE2.5 Vengeance / UE3 (Infinite) | native-injector | — | — | 13 | 243 | 164 | 26 | 2026-08-26 | 🟩 current | 2F / 3P / 2S / 0NR / 6— |
| **BL1GOTYVR** | external reference | Unreal Engine 3 (Borderlands GOTY Enhanced, 2019) | native-injector | T2 | — | 9 | 74 | 66 | 4 | 2026-08-30 | ⚪ unpinned | 0F / 0P / 4S / 7NR / 2— |
| **black-mesa-l4d2vr** | external reference | Source (Black Mesa) | native-injector | — | — | 9 | 1780 | 1370 | 89 | 2026-08-28 | ⚪ unpinned | 1F / 5P / 0S / 5NR / 2— |
| **bo1-vr** | external reference | Treyarch T5 (Black Ops) | native-injector | — | — | — | 177 | 72 | 49 | 2026-08-27 | 🟩 current | 2F / 2P / 0S / 0NR / 9— |
| **Buffout4 NG-64880-1-38-3-1785297452** | external reference | Creation Engine (Fallout 4 / Fallout 4 VR) - a NATIVE VR title, not a conversion | framework-companion | T4 | ? | — | 7 | 0 | 1 | 2026-07-29 | ⚪ unpinned | 0F / 2P / 0S / 10NR / 1— |
| **CallOfDuty4_VR** | external reference | IW (CoD4) | source-port | — | — | 18 | 1125 | 1030 | 27 | 2026-08-22 | 🟩 current | 2F / 3P / 1S / 1NR / 6— |
| **condemned-vr** | external reference | LithTech Jupiter EX (Condemned: Criminal Origins) | native-injector | T2 | R1 · native re-entry | 17 | 213 | 132 | 32 | 2026-08-30 | ⚪ unpinned | 1F / 0P / 4S / 6NR / 2— |
| **crysis_vrmod** | external reference | CryEngine 2 | native-injector | T3 | R1 · native re-entry | 17 | 813 | 695 | 18 | 2026-08-28 | ⚪ unpinned | 2F / 1P / 1S / 7NR / 2— |
| **CSVR** | archived reference | GoldSrc / Xash3D | source-port | — | — | — | 1001 | 307 | 5 | 2026-03-09 | 🟩 current | 0F / 0P / 1S / 0NR / 12— |
| **cyberpunk-vr-port** | external reference | REDengine 4 | native-injector | — | — | 17 | 572 | 301 | 91 | 2026-09-05 | 🟥 source changed | 1F / 4P / 0S / 3NR / 5— |
| **Dishonored-VR** | external reference | Unreal Engine 3 (Dishonored) | native-injector | ? | ? | 18 | 61 | 1 | 3 | 2026-09-04 | ⚪ unpinned | 0F / 0P / 0S / 11NR / 2— |
| **Dishonored-VR-fork** | external reference | Unreal Engine 3 (Dishonored, 32-bit) | native-injector | T1 | R2 · per-draw replay | — | 59 | 1 | 1 | 2026-09-04 | 🟥 source changed | 0F / 0P / 0S / 13NR / 0— |
| **DOOM-3-BFG-VR** | external reference | idTech 4 (Doom 3 BFG) | source-port | — | — | — | 2155 | 1348 | 83 | 2026-08-27 | 🟩 current | 1F / 3P / 0S / 0NR / 9— |
| **edvr-unofficial-patch** | external reference | Cobra (Elite Dangerous: Odyssey) | native-injector | — | — | 14 | 185 | 147 | 17 | 2026-08-28 | ⚪ unpinned | 2F / 2P / 0S / 7NR / 2— |
| **Fallout 4 Script Extender VR (F4SEVR)-42159-0-6-21-1719284892** | external reference | Creation Engine (Fallout 4 VR) - a NATIVE VR title, not a conversion | framework-companion | T4 | ? | — | 392 | 294 | 5 | 2024-06-25 | ⚪ unpinned | 0F / 0P / 0S / 12NR / 1— |
| **Fallout-New-Vegas-FNVR** | external reference | Gamebryo (Fallout New Vegas) | script-native-hybrid | — | — | 18 | 342 | 279 | 28 | 2026-08-29 | ⚪ unpinned | 0F / 0P / 1S / 10NR / 2— |
| **fear-vr** | external reference | LithTech Jupiter EX | native-injector | T3 | R1 · native re-entry | 17 | 163 | 82 | 32 | 2026-08-22 | 🟩 current | 7F / 3P / 0S / 1NR / 2— |
| **FEAR2VR** | external reference | LithTech Jupiter EX (F.E.A.R. 2) | native-injector | — | — | 6 | 330 | 294 | 17 | 2026-08-28 | ⚪ unpinned | 2F / 2P / 1S / 6NR / 2— |
| **ForerunnerVR** | external reference | Blam / Saber (MCC) | native-injector | — | — | — | 101 | 87 | 3 | 2026-08-26 | 🟩 current | 1F / 1P / 1S / 0NR / 10— |
| **FRIK 78.2 53464 v0.78.2 2026-08-17T16-42Z 86DAb33jN** | external reference | Creation Engine (Fallout 4 VR) - a NATIVE VR title, not a conversion | framework-companion | T4 | ? | — | 128 | 0 | 1 | 2026-08-18 | ⚪ unpinned | 0F / 0P / 0S / 12NR / 1— |
| **FUS** | external reference | Creation Engine (Skyrim VR) - a NATIVE VR title, not a conversion | framework-companion | T4 | ? | — | 66 | 0 | 4 | 2026-09-05 | ⚪ unpinned | 0F / 0P / 0S / 12NR / 1— |
| **gmcl_openvr** | external reference | Source (Garry's Mod) | script-native-hybrid | — | — | — | 82 | 24 | 1 | 2026-08-27 | 🟩 current | 0F / 2P / 1S / 0NR / 10— |
| **goldeneye-omniport** | external reference | N64 decompilation (GoldenEye 007) | source-port | — | — | 18 | 2309 | 2045 | 24 | 2026-08-28 | ⚪ unpinned | 1F / 1P / 1S / 8NR / 2— |
| **GRAND-alien-isolation** | external reference | Alien Isolation (custom) | native-injector | ? | ? | — | 4 | 0 | 1 | 2026-06-30 | 🟩 current | 0F / 1P / 0S / 1NR / 11— |
| **gta-sa-vr-quest** | external reference | RenderWare (GTA San Andreas, Android) | native-injector | T1 | — | 18 | 91 | 51 | 8 | 2026-08-30 | ⚪ unpinned | 0F / 0P / 2S / 9NR / 2— |
| **GTA-VRV-Patcher** | external reference | RAGE | framework-companion | — | — | — | 29 | 12 | 2 | 2026-08-26 | 🟩 current | 1F / 0P / 0S / 0NR / 12— |
| **GTFO_VR_Plugin** | external reference | Unity IL2CPP | managed-plugin | — | — | 18 | 251 | 148 | 2 | 2026-08-23 | 🟩 current | 1F / 2P / 1S / 1NR / 8— |
| **Halo-MCC-VR** | external reference | Blam / Saber | native-injector | — | — | 18 | 148 | 93 | 36 | 2026-08-23 | 🟥 source changed | 2F / 3P / 0S / 2NR / 6— |
| **Heisenberg - Physical Interactions 99105 0.8.6 2026-08-02T10-39Z Q8oKHMMng** | external reference | Creation Engine (Fallout 4 VR) - a NATIVE VR title, not a conversion | framework-companion | T4 | ? | — | 45 | 0 | 1 | 2026-08-02 | ⚪ unpinned | 0F / 1P / 0S / 11NR / 1— |
| **HIGGS 1.10.10-43930-1-10-10-1768263289** | external reference | Creation Engine (Skyrim VR) - a NATIVE VR title, not a conversion | framework-companion | T4 | ? | — | 6 | 0 | 0 | 2026-01-13 | ⚪ unpinned | 0F / 0P / 0S / 12NR / 1— |
| **IRON-NEST-VR** | external reference | Unity | managed-plugin | ? | ? | — | 14 | 0 | 1 | 2026-07-01 | 🟩 current | 0F / 0P / 1S / 1NR / 11— |
| **JKXR** | external reference | id Tech 3 / OpenJK | source-port | — | — | 18 | 2548 | 1969 | 70 | 2026-08-23 | 🟩 current | 1F / 4P / 0S / 2NR / 6— |
| **KSA_XR** | external reference | Brutal (RocketWerkz) | managed-plugin | — | — | — | 19 | 8 | 3 | 2026-08-26 | 🟩 current | 1F / 2P / 1S / 0NR / 9— |
| **l4d2vr** | external reference | Source (Left 4 Dead 2) | native-injector | — | — | — | 42 | 23 | 3 | 2026-08-27 | 🟩 current | 0F / 3P / 1S / 0NR / 9— |
| **Luke-Ross-REAL-mods** | external reference | multiple (CP2077, HZD, Mafia DE 1/2, GTAV, NOLF2) | native-injector | — | — | — | 3 | 0 | 0 | 2023-03-13 | 🟩 current | 0F / 0P / 1S / 0NR / 12— |
| **Main Wabbajack 20.0 96013 20 2026-08-28T01-06Z bnEVTOJ7D** | external reference | Creation Engine (Fallout 4 VR) - a NATIVE VR title, not a conversion | framework-companion | T4 | ? | — | 1 | 0 | 0 | 2026-08-28 | ⚪ unpinned | 0F / 0P / 0S / 12NR / 1— |
| **manhunt-2003-vr-modding-notes** | external reference | RenderWare (Manhunt 2003) | native-injector | — | — | 7 | 10 | 0 | 9 | 2026-08-29 | ⚪ unpinned | 1F / 1P / 1S / 8NR / 2— |
| **MELE-VR** | external reference | UE3 (Mass Effect Legendary) | native-injector | ? | ? | — | 18 | 0 | 3 | 2026-08-23 | 🟩 current | 0F / 2P / 0S / 1NR / 10— |
| **mirrors-edge-vr-mod** | external reference | Unreal Engine 3.536 (Mirror's Edge, 2008) | native-injector | T1 | — | 9 | 37 | 17 | 9 | 2026-08-30 | 🟥 source changed | 2F / 0P / 2S / 8NR / 1— |
| **MonsterDeadWood-BF3VR** | external reference | Frostbite 2 / Venice Unleashed (Battlefield 3) | native-injector | T1 | R4 · reconstruction | 14 | 55 | 4 | 44 | 2026-09-03 | 🟩 current | 2F / 4P / 0S / 1NR / 6— |
| **MonsterDeadWood-C2VR** | external reference | CryEngine 3 (Crysis 2) | native-injector | T1 | R4 · reconstruction | 9 | 105 | 12 | 85 | 2026-09-03 | 🟩 current | 1F / 5P / 0S / 1NR / 6— |
| **MonsterDeadWood-DiRT2VR** | external reference | EGO (DiRT 2) | native-injector | T1 | R1 · native re-entry | 17 | 44 | 4 | 36 | 2026-09-03 | 🟩 current | 3F / 2P / 0S / 1NR / 7— |
| **MonsterDeadWood-FC2VR** | external reference | Dunia (Far Cry 2) | native-injector | T1 | R1 · native re-entry | 17 | 111 | 19 | 63 | 2026-09-05 | 🟥 source changed | 0F / 5P / 0S / 1NR / 7— |
| **MonsterDeadWood-TimeShiftVR** | external reference | Saber3D (TimeShift) | native-injector | T1 | R1 · native re-entry | 14 | 27 | 4 | 19 | 2026-09-03 | 🟩 current | 3F / 2P / 0S / 1NR / 7— |
| **MyFriendlyNeighborhoodVR** | external reference | Unity | managed-plugin | — | — | 18 | 35 | 15 | 6 | 2026-08-22 | 🟩 current | 0F / 0P / 1S / 0NR / 12— |
| **novr** | external reference | Unity | managed-plugin | — | — | — | 387 | 303 | 2 | 2026-08-26 | 🟩 current | 0F / 0P / 1S / 1NR / 11— |
| **openmw-vr** | external reference | OpenMW (OSG / OpenGL) | source-port | — | — | — | 3825 | 3023 | 208 | 2026-08-26 | 🟩 current | 0F / 2P / 1S / 1NR / 9— |
| **Outlast-Vr-Mod** | external reference | Unreal Engine 3 (Outlast) | native-injector | T1 | — | 18 | 49 | 16 | 8 | 2026-08-30 | ⚪ unpinned | 0F / 0P / 2S / 9NR / 2— |
| **payday2-vr-improvements** | external reference | Diesel (PAYDAY 2) | script-native-hybrid | — | — | — | 55 | 34 | 3 | 2026-08-27 | 🟩 current | 0F / 1P / 1S / 0NR / 11— |
| **perfect_dark_VR** | external reference | Perfect Dark decompilation (N64) | source-port | — | — | — | 2422 | 1095 | 12 | 2026-08-26 | 🟩 current | 1F / 3P / 0S / 1NR / 8— |
| **PLANCK 0.8.1 66025 0.8.1 2026-07-30T03-35Z 4t2yDcbYt** | external reference | Creation Engine (Skyrim VR) - a NATIVE VR title, not a conversion | framework-companion | T4 | ? | — | 5 | 0 | 0 | 2026-07-29 | ⚪ unpinned | 0F / 0P / 0S / 12NR / 1— |
| **portal2vr** | external reference | Source (Portal 2) | native-injector | — | — | — | 49 | 30 | 3 | 2026-08-27 | 🟩 current | 0F / 0P / 1S / 0NR / 12— |
| **prince-of-persia-2008-vr-external-research** | external reference | Scimitar / Anvil (Prince of Persia 2008) | framework-companion | — | — | 11 | 13 | 0 | 11 | 2026-08-29 | ⚪ unpinned | 1F / 1P / 0S / 9NR / 2— |
| **psychonauts-vr-dev-archive** | external reference | Runtime (Psychonauts 2005) | native-injector | — | — | 6 | 147 | 12 | 77 | 2026-08-29 | ⚪ unpinned | 1F / 1P / 1S / 8NR / 2— |
| **psychonauts-vr-modding-notes** | external reference | Runtime (Psychonauts 2005) | native-injector | T1 | ? | 11 | 67 | 0 | 67 | 2026-08-29 | ⚪ unpinned | 3F / 1P / 1S / 6NR / 2— |
| **Quake2Quest** | external reference | id Tech 2 (Quake II, via Yamagi) | source-port | ? | ? | 9 | 1057 | 707 | 28 | 2026-09-02 | 🟥 source changed | 0F / 0P / 0S / 11NR / 2— |
| **quake2vr** | external reference | id Tech 2 (Quake II, via KMQuake II) | source-port | ? | ? | 9 | 1090 | 338 | 24 | 2026-09-02 | 🟥 source changed | 0F / 0P / 0S / 11NR / 2— |
| **ravenfield-vr-mod** | external reference | Unity | managed-plugin | — | — | — | 40 | 10 | 1 | 2026-08-26 | 🟩 current | 0F / 0P / 1S / 0NR / 12— |
| **Rea-Virtua-Cop-2-VR** | external reference | 1997 fixed-function | native-injector | — | — | 16 | 8 | 3 | 1 | 2026-08-21 | 🟩 current | 3F / 2P / 0S / 0NR / 8— |
| **ReclaimerVR** | external reference | Blam / Saber (MCC) | native-injector | ? | ? | — | 1 | 0 | 1 | 2026-08-26 | 🟩 current | 0F / 0P / 0S / 1NR / 12— |
| **REFramework** | external reference | RE Engine (multi-title) | framework | T3 | ? | — | 1374 | 1284 | 25 | 2026-09-05 | 🟥 source changed | 0F / 0P / 0S / 13NR / 0— |
| **RepoXR** | external reference | Unity | managed-plugin | — | — | — | 146 | 132 | 3 | 2026-08-26 | 🟩 current | 1F / 1P / 1S / 1NR / 9— |
| **RoR2VRMod** | external reference | Unity Mono | managed-plugin | — | — | 18 | 81 | 61 | 5 | 2026-01-20 | 🟩 current | 0F / 2P / 2S / 0NR / 9— |
| **satisfactory-uevr-enhancements** | external reference | Unreal 5 | framework-companion | — | — | 18 | 433 | 18 | 5 | 2026-08-22 | 🟩 current | 0F / 2P / 0S / 0NR / 11— |
| **Scrap-Mechanic-Native-VR** | external reference | Scrap Mechanic (proprietary) | script-native-hybrid | — | — | — | 74 | 38 | 11 | 2026-08-27 | 🟩 current | 0F / 3P / 1S / 0NR / 9— |
| **Shipwright-VR** | external reference | libultraship / Ship of Harkinian | source-port | — | — | — | 11943 | 3243 | 22 | 2026-08-26 | 🟩 current | 1F / 3P / 0S / 0NR / 9— |
| **shock2quest** | external reference | Dark engine recreation (Rust) | engine-recreation | — | — | 18 | 989 | 617 | 63 | 2026-08-28 | 🟩 current | 3F / 0P / 1S / 3NR / 6— |
| **Silent-Hill-3-VR-Mod** | external reference | Silent Hill 3 (2003) | native-injector | T2 | ? | 18 | 478 | 133 | 56 | 2026-08-29 | ⚪ unpinned | 0F / 2P / 0S / 9NR / 2— |
| **sims4-vr** | archived reference | EA custom (Sims 4) | script-native-hybrid | — | — | 18 | 131 | 81 | 26 | 2026-08-23 | 🟩 current | 3F / 0P / 0S / 0NR / 10— |
| **singularity-vr-mod** | external reference | Unreal Engine 3.584 (Singularity 2010) | native-injector | T1 | R2 · per-draw replay | 9 | 84 | 39 | 16 | 2026-08-29 | ⚪ unpinned | 6F / 2P / 0S / 3NR / 2— |
| **SkyrimTogetherVR** | external reference | Creation Engine (Skyrim VR 1.4.15, SKSEVR) | native-injector | — | — | 6 | 2585 | 1562 | 552 | 2026-08-28 | ⚪ unpinned | 1F / 1P / 1S / 8NR / 2— |
| **SkyrimVR FBT 185070 1.0.3 2026-07-22T11-37Z HZCMOyLlG** | external reference | Creation Engine (Skyrim VR) - a NATIVE VR title, not a conversion | framework-companion | T4 | ? | — | 2 | 0 | 0 | 2026-07-22 | ⚪ unpinned | 0F / 0P / 0S / 12NR / 1— |
| **Snowrunner-VR** | external reference | SnowRunner (Steam) | native-injector | T2 | R3 · alternate-eye | 19 | 57 | 50 | 2 | 2026-08-29 | ⚪ unpinned | 1F / 1P / 1S / 8NR / 2— |
| **SonsVR_Mod** | external reference | Unity HDRP (Sons of the Forest) | managed-plugin | — | — | — | 32 | 22 | 1 | 2026-08-27 | 🟩 current | 1F / 2P / 0S / 0NR / 10— |
| **SPT-VR** | external reference | Unity | managed-plugin | — | — | 18 | 149 | 88 | 2 | 2026-08-22 | 🟩 current | 0F / 0P / 1S / 0NR / 12— |
| **Sterallax6DOF-silksong** | external reference | Unity (Silksong) | managed-plugin | ? | ? | — | 1 | 0 | 0 | 2026-08-02 | 🟩 current | 0F / 0P / 0S / 1NR / 12— |
| **SubmersedVR** | external reference | Unity 2019.4 (Subnautica) | managed-plugin | — | — | — | 81 | 31 | 3 | 2026-08-27 | 🟩 current | 0F / 2P / 0S / 1NR / 10— |
| **SystemReShock-UEVR-Plugin** | external reference | Unreal | framework-companion | — | — | — | 4760 | 4741 | 1 | 2026-05-22 | 🟩 current | 0F / 1P / 0S / 0NR / 12— |
| **Talemann-RE4** | external reference | RE Engine (Resident Evil 4 Remake), via praydog's REFramework | framework-companion | T4 | — | — | 106 | 30 | 0 | 2026-09-05 | ⚪ unpinned | 0F / 1P / 0S / 11NR / 1— |
| **TechtonicaVR** | external reference | Unity 2021.3.15f1 | framework-companion | — | — | — | 1777 | 288 | 6 | 2026-08-27 | 🟩 current | 0F / 0P / 1S / 0NR / 12— |
| **the-evil-within-vr-external-research** | external reference | id Tech 5 (The Evil Within) | framework-companion | — | — | 9 | 8 | 0 | 8 | 2026-08-29 | ⚪ unpinned | 1F / 0P / 1S / 9NR / 2— |
| **thedarkmodvr** | external reference | idTech 4 (TDM) | source-port | — | — | — | 2604 | 2122 | 25 | 2026-05-22 | 🟩 current | 0F / 3P / 1S / 0NR / 9— |
| **theHunterCotW-VR** | external reference | Apex / Avalanche (theHunter: Call of the Wild) | native-injector | T2 | R1 · native re-entry | 17 | 167 | 139 | 18 | 2026-08-30 | ⚪ unpinned | 1F / 0P / 2S / 8NR / 2— |
| **TwoForksVR** | external reference | Unity | managed-plugin | — | — | — | 73 | 0 | 0 | 2022-03-18 | 🟩 current | 0F / 0P / 1S / 0NR / 12— |
| **UEVR** | external reference | Unreal (generic) | framework | — | — | — | 267 | 223 | 14 | 2026-08-23 | 🟩 current | 0F / 1P / 0S / 0NR / 12— |
| **unreal-gold-vr-external-research** | external reference | Unreal Engine 1 (Unreal Gold) | framework-companion | — | — | 18 | 5 | 0 | 5 | 2026-08-29 | ⚪ unpinned | 1F / 0P / 0S / 9NR / 3— |
| **VirtualFortress2** | external reference | Source (Team Fortress 2) | source-port | — | — | — | 4613 | 3839 | 22 | 2026-08-27 | 🟩 current | 0F / 0P / 3S / 0NR / 10— |
| **visceral-re2-vr-mod** | external reference | RE Engine (Resident Evil 2, 2019) | framework-companion | T2 | — | 2 | 14 | 5 | 5 | 2026-08-30 | 🟥 source changed | 0F / 0P / 2S / 9NR / 2— |
| **Vostok-VR-Mod** | external reference | Godot 4 | native-injector | — | — | — | 78 | 14 | 10 | 2026-08-26 | 🟩 current | 1F / 1P / 0S / 0NR / 11— |
| **VRIK Player Avatar 23416 0.8.6 2026-07-12T13-00Z Yj6wQRIkO** | external reference | Creation Engine (Skyrim VR) - a NATIVE VR title, not a conversion | framework-companion | T4 | ? | — | 20 | 0 | 0 | 2026-07-12 | ⚪ unpinned | 0F / 1P / 0S / 11NR / 1— |
| **WeWereInVR** | external reference | Unity (We Were Here) | managed-plugin | — | — | 18 | 33 | 17 | 3 | 2026-08-28 | ⚪ unpinned | 1F / 2P / 0S / 8NR / 2— |
| **White_Knuckle_VR** | external reference | Unity | managed-plugin | — | — | 18 | 4 | 0 | 3 | 2026-08-22 | 🟩 current | 1F / 1P / 0S / 0NR / 11— |
| **witcher3-vr** | external reference | REDengine 3 | native-injector | — | — | 18 | 79 | 51 | 8 | 2026-08-22 | 🟥 source changed | 1F / 3P / 0S / 3NR / 6— |
| **WorldWarVR-Releases** | external reference | IW (World at War) | source-port | — | — | 18 | 5 | 0 | 4 | 2026-08-23 | 🟩 current | 1F / 1P / 0S / 0NR / 11— |
| **XIII2003-vr-external-research** | external reference | Unreal Engine 2 (XIII 2003) | framework-companion | — | — | 11 | 7 | 0 | 7 | 2026-08-29 | ⚪ unpinned | 1F / 0P / 0S / 10NR / 2— |
| **XIII2003-vr-mod** | external reference | Unreal Engine 2 (XIII, 2003) | native-injector | ? | ? | 18 | 4 | 0 | 3 | 2026-08-30 | ⚪ unpinned | 0F / 0P / 0S / 11NR / 2— |

## Review freshness

A red row means the source tree no longer matches the snapshot that was reviewed. Re-review the affected areas; do not merely copy the new fingerprint.

| Source | Reviewed at | Reviewed tree | Current tree | Reviewed Git commit | Result | Upstream | License |
|---|---|---|---|---|---|---|---|
| **BioshockVR** | 2026-08-28 | `tree:ca2163ed64a3a5d7` | `tree:f739d4177dd41381` | `—` | 🟥 source changed | internal | internal-unreleased |
| **DishonoredVR** | 2026-08-28 | `tree:f79696e6df81c47e` | `tree:35ab1dc2354b0092` | `—` | 🟥 source changed | internal | internal-unreleased |
| **FarCry2-vr** | 2026-09-03 | `tree:f8a7972fa42c8fde` | `tree:cc0feb54ce2f4edd` | `—` | 🟥 source changed | internal | internal-unreleased |
| **Medal-of-Honor-vr** | 2026-09-04 | `tree:86e9768fb217f5cc` | `tree:be0ea8804e195391` | `—` | 🟥 source changed | internal | internal-unreleased |
| **PreyVR** | 2026-08-28 | `tree:ea9020b75685cf9d` | `tree:605c3d4ae63524b1` | `—` | 🟥 source changed | internal | internal-unreleased |
| **Sims4VR** | 2026-08-28 | `tree:ca949b5a4fc0d490` | `tree:f31b82ea3ce79d04` | `—` | 🟥 source changed | internal | internal-unreleased |
| **SoF-VR** | 2026-09-04 | `tree:381555bafe5d9010` | `tree:762a48d6bc781596` | `—` | 🟥 source changed | internal | internal-unreleased |
| **SOMAVR** | 2026-08-28 | `tree:ef4d52fb846535b5` | `tree:3ce075f4d3c87a95` | `—` | 🟥 source changed | internal | internal-unreleased |
| **ss2vr-work** | 2026-08-28 | `tree:4d9e7c06edd1a483` | `tree:05f086a4a569bf89` | `—` | 🟥 source changed | internal | internal-unreleased |
| **Swat4-VR** | 2026-08-28 | `tree:39a751f1ad836d40` | `tree:5dbc4303c1264b3d` | `—` | 🟥 source changed | internal | internal-unreleased |
| **Aliens-Versus-Predator-VR** | 2026-08-29 | `unknown` | `tree:bf8bb2bf9d6c7c4a` | `—` | ⚪ unpinned | unknown | unknown |
| **anvilengine2vr** | 2026-08-25 | `tree:64c6afb808b9af48` | `tree:64c6afb808b9af48` | `—` | 🟩 current | unknown | unknown |
| **BendyVR** | 2026-08-25 | `tree:d87f8cff726a8460` | `tree:d87f8cff726a8460` | `—` | 🟩 current | unknown | unknown |
| **BF2VR** | 2026-08-25 | `tree:b5d85b406c734579` | `tree:b5d85b406c734579` | `—` | 🟩 current | unknown | unknown |
| **bfbc2-vr** | 2026-08-28 | `tree:2577103b3f59826b` | `tree:e1bd02050dcf90fa` | `—` | 🟥 source changed | unknown | unknown |
| **BFVR-Battlefield-1942** | 2026-08-26 | `tree:2776363bdd1bbbf9` | `tree:2776363bdd1bbbf9` | `cb01120313f56c85c68413a04066f898e2bdd49d` | 🟩 current | https://github.com/JayBiggsGMG/BFVR-Battlefield-1942-VR-Mod | unknown |
| **Bioshock-Remastered-VR** | 2026-08-28 | `unknown` | `tree:fec8e3da1b68d509` | `—` | ⚪ unpinned | unknown | unknown |
| **bioshock-trilogy-vr** | 2026-08-26 | `tree:cab3312723aad2ca` | `tree:cab3312723aad2ca` | `5bc599923bf73bf154cc35f7265ff2c568e82016` | 🟩 current | https://github.com/VR-Stereo-Hub/bioshock-trilogy-vr | MIT |
| **BL1GOTYVR** | 2026-08-29 | `unknown` | `tree:3e8e104d25c19bb5` | `—` | ⚪ unpinned | unknown | unknown |
| **black-mesa-l4d2vr** | 2026-08-28 | `unknown` | `tree:58c62c9565e8c260` | `—` | ⚪ unpinned | unknown | unknown |
| **bo1-vr** | 2026-08-27 | `tree:f5a5f9cf94ed8e4f` | `tree:f5a5f9cf94ed8e4f` | `—` | 🟩 current | unknown | unknown |
| **Buffout4 NG-64880-1-38-3-1785297452** | 2026-09-05 | `unknown` | `tree:c5822dd551ad3a17` | `—` | ⚪ unpinned | unknown | unknown |
| **CallOfDuty4_VR** | 2026-08-25 | `tree:146efc09f95cba26` | `tree:146efc09f95cba26` | `—` | 🟩 current | unknown | unknown |
| **condemned-vr** | 2026-08-29 | `unknown` | `tree:375521a55d72feca` | `—` | ⚪ unpinned | unknown | unknown |
| **crysis_vrmod** | 2026-08-28 | `unknown` | `tree:72edce18458cccd3` | `—` | ⚪ unpinned | unknown | unknown |
| **CSVR** | 2026-08-25 | `tree:b317ecb80018cb2d` | `tree:b317ecb80018cb2d` | `—` | 🟩 current | unknown | unknown |
| **cyberpunk-vr-port** | 2026-08-25 | `tree:22383c11593f8750` | `tree:e4fe5418281f1c41` | `—` | 🟥 source changed | unknown | unknown |
| **Dishonored-VR** | 2026-09-02 | `unknown` | `tree:ec8b8c0d1fa6e210` | `—` | ⚪ unpinned | unknown | zlib (DXVK) - covers fork-patches ONLY; dllmain.cpp is unlicensed |
| **Dishonored-VR-fork** | 2026-09-04 | `tree:0d7e87ff7f68876e` | `tree:89e9c521e1893b4e` | `—` | 🟥 source changed | https://github.com/phunkaeg/Dishonored-VR | see LICENSE in tree |
| **DOOM-3-BFG-VR** | 2026-08-27 | `tree:b68fb6734c12a28c` | `tree:b68fb6734c12a28c` | `—` | 🟩 current | unknown | unknown |
| **edvr-unofficial-patch** | 2026-08-28 | `unknown` | `tree:a27fb9fe577f1279` | `—` | ⚪ unpinned | unknown | unknown |
| **Fallout 4 Script Extender VR (F4SEVR)-42159-0-6-21-1719284892** | 2026-09-05 | `unknown` | `tree:1346c9ecdc86400f` | `—` | ⚪ unpinned | unknown | unknown |
| **Fallout-New-Vegas-FNVR** | 2026-08-29 | `unknown` | `tree:c979d571dbef665b` | `—` | ⚪ unpinned | unknown | unknown |
| **fear-vr** | 2026-08-29 | `tree:7437c5bc33a9688d` | `tree:7437c5bc33a9688d` | `—` | 🟩 current | unknown | unknown |
| **FEAR2VR** | 2026-08-28 | `unknown` | `tree:25ecac968c4146d1` | `—` | ⚪ unpinned | unknown | unknown |
| **ForerunnerVR** | 2026-08-26 | `tree:6c2023683d68eff9` | `tree:6c2023683d68eff9` | `ae37120becad289ed404bb7b848367e923033bf8` | 🟩 current | https://github.com/LivingFray/ForerunnerVR | unknown |
| **FRIK 78.2 53464 v0.78.2 2026-08-17T16-42Z 86DAb33jN** | 2026-09-05 | `unknown` | `tree:ff5f7db0f385d23d` | `—` | ⚪ unpinned | https://github.com/rollingrock/Fallout-4-VR-Body | unknown |
| **FUS** | 2026-09-05 | `unknown` | `tree:4d835bf05872284e` | `—` | ⚪ unpinned | unknown | unknown |
| **gmcl_openvr** | 2026-08-27 | `tree:d9da74ebf2d2629d` | `tree:d9da74ebf2d2629d` | `—` | 🟩 current | unknown | unknown |
| **goldeneye-omniport** | 2026-08-28 | `unknown` | `tree:3d329e089afebd29` | `—` | ⚪ unpinned | unknown | unknown |
| **GRAND-alien-isolation** | 2026-08-26 | `tree:b6fc9c9e7cc2e607` | `tree:b6fc9c9e7cc2e607` | `—` | 🟩 current | unknown | unknown |
| **gta-sa-vr-quest** | 2026-08-29 | `unknown` | `tree:a211e6ff6f8bbfd8` | `—` | ⚪ unpinned | unknown | unknown |
| **GTA-VRV-Patcher** | 2026-08-26 | `tree:c597e6967613fc1c` | `tree:c597e6967613fc1c` | `225df5859976d5f485ed8fddf029ea5e8fbe6c2f` | 🟩 current | https://github.com/FranciscoManzanilla/GTA-VRV-Patcher | unknown |
| **GTFO_VR_Plugin** | 2026-08-25 | `tree:3b8bc8dedc3cb478` | `tree:3b8bc8dedc3cb478` | `—` | 🟩 current | unknown | unknown |
| **Halo-MCC-VR** | 2026-08-25 | `tree:fe9e1846706a63da` | `tree:eb934c8e30b766b5` | `—` | 🟥 source changed | https://github.com/pancreations/Halo-MCC-VR | MIT |
| **Heisenberg - Physical Interactions 99105 0.8.6 2026-08-02T10-39Z Q8oKHMMng** | 2026-09-05 | `unknown` | `tree:58a5b1f5db6072ee` | `—` | ⚪ unpinned | unknown | unknown |
| **HIGGS 1.10.10-43930-1-10-10-1768263289** | 2026-09-05 | `unknown` | `tree:11ade5e7d012caae` | `—` | ⚪ unpinned | unknown | unknown |
| **IRON-NEST-VR** | 2026-08-26 | `tree:e65f3b7698f9edea` | `tree:e65f3b7698f9edea` | `—` | 🟩 current | unknown | unknown |
| **JKXR** | 2026-08-25 | `tree:5c5bd57858afdbe2` | `tree:5c5bd57858afdbe2` | `—` | 🟩 current | unknown | unknown |
| **KSA_XR** | 2026-08-26 | `tree:09b84dde7a415db5` | `tree:09b84dde7a415db5` | `8467599b9389652d4a74d50f965b829dd3dee43e` | 🟩 current | https://github.com/Ybalrid/KSA_XR | unknown |
| **l4d2vr** | 2026-08-27 | `tree:0a633263d8116124` | `tree:0a633263d8116124` | `—` | 🟩 current | unknown | unknown |
| **Luke-Ross-REAL-mods** | unknown | `tree:06153e074416cd40` | `tree:06153e074416cd40` | `—` | 🟩 current | unknown | unknown |
| **Main Wabbajack 20.0 96013 20 2026-08-28T01-06Z bnEVTOJ7D** | 2026-09-05 | `unknown` | `tree:35b3173db0af61f0` | `—` | ⚪ unpinned | unknown | unknown |
| **manhunt-2003-vr-modding-notes** | 2026-08-29 | `unknown` | `tree:e8d969134352da0f` | `—` | ⚪ unpinned | unknown | unknown |
| **MELE-VR** | 2026-08-28 | `tree:b8d87bff0fecabf1` | `tree:b8d87bff0fecabf1` | `—` | 🟩 current | unknown | unknown |
| **mirrors-edge-vr-mod** | 2026-08-29 | `tree:a64e71450006b5d5` | `tree:ba6ab5363d9090ac` | `—` | 🟥 source changed | unknown | unknown |
| **MonsterDeadWood-BF3VR** | 2026-09-03 | `tree:a434e6fd4ed2c819` | `tree:a434e6fd4ed2c819` | `—` | 🟩 current | unknown | unknown |
| **MonsterDeadWood-C2VR** | 2026-09-03 | `tree:5c9a476fdb91dfb4` | `tree:5c9a476fdb91dfb4` | `—` | 🟩 current | unknown | unknown |
| **MonsterDeadWood-DiRT2VR** | 2026-09-03 | `tree:e1f675860774af3f` | `tree:e1f675860774af3f` | `—` | 🟩 current | unknown | unknown |
| **MonsterDeadWood-FC2VR** | 2026-09-03 | `tree:0f01206573f0c260` | `tree:6ddcccada41c56ca` | `—` | 🟥 source changed | unknown | unknown |
| **MonsterDeadWood-TimeShiftVR** | 2026-09-03 | `tree:f90d5188debf073d` | `tree:f90d5188debf073d` | `—` | 🟩 current | unknown | unknown |
| **MyFriendlyNeighborhoodVR** | 2026-08-25 | `tree:2bd54d6d8674a6a7` | `tree:2bd54d6d8674a6a7` | `—` | 🟩 current | unknown | unknown |
| **novr** | 2026-08-26 | `tree:6823115a691200c6` | `tree:6823115a691200c6` | `7cf34b3e480671cfbd34bc7b89f5f1692ddfe9fb` | 🟩 current | https://github.com/InfernoSuperNova/novr | unknown |
| **openmw-vr** | 2026-08-26 | `tree:7155f265d832b125` | `tree:7155f265d832b125` | `0f520f65c3e085369e66d6a90ce871e817d4533f` | 🟩 current | https://gitlab.com/madsbuvi/openmw/-/tree/openmw-vr | GPL-3.0 (OpenMW) |
| **Outlast-Vr-Mod** | 2026-08-29 | `unknown` | `tree:bfa0db61dfab071e` | `—` | ⚪ unpinned | unknown | unknown |
| **payday2-vr-improvements** | 2026-08-27 | `tree:ceff8eb529473d2e` | `tree:ceff8eb529473d2e` | `—` | 🟩 current | unknown | unknown |
| **perfect_dark_VR** | 2026-08-26 | `tree:7b24c19fafd8b3f7` | `tree:7b24c19fafd8b3f7` | `67ea20c86986c6bc85687f26a27418b266af309c` | 🟩 current | https://github.com/Alex-LeTux/perfect_dark_VR | unknown |
| **PLANCK 0.8.1 66025 0.8.1 2026-07-30T03-35Z 4t2yDcbYt** | 2026-09-05 | `unknown` | `tree:cd5be93c7cedb47d` | `—` | ⚪ unpinned | unknown | unknown |
| **portal2vr** | 2026-08-27 | `tree:6fccc2a8dab60ec6` | `tree:6fccc2a8dab60ec6` | `—` | 🟩 current | unknown | unknown |
| **prince-of-persia-2008-vr-external-research** | 2026-08-29 | `unknown` | `tree:05fa0ca45f7a63b8` | `—` | ⚪ unpinned | unknown | unknown |
| **psychonauts-vr-dev-archive** | 2026-08-29 | `unknown` | `tree:90e822bc3d53f345` | `—` | ⚪ unpinned | unknown | unknown |
| **psychonauts-vr-modding-notes** | 2026-08-29 | `unknown` | `tree:45d31d43bf8ad326` | `—` | ⚪ unpinned | unknown | unknown |
| **Quake2Quest** | 2026-09-02 | `tree:6762626f4c1aed86` | `tree:af131bfd6663683b` | `—` | 🟥 source changed | unknown | unknown |
| **quake2vr** | 2026-09-02 | `tree:461b476dadb7b80e` | `tree:a203a1a1bb26e4e1` | `—` | 🟥 source changed | unknown | unknown |
| **ravenfield-vr-mod** | 2026-08-26 | `tree:5ff2383f8ff12840` | `tree:5ff2383f8ff12840` | `4ed67514aa3302ba255b6ddb870854f9c992737e` | 🟩 current | https://github.com/GDani31/ravenfield-vr-mod | unknown |
| **Rea-Virtua-Cop-2-VR** | 2026-08-25 | `tree:d5c76a58e1e614ca` | `tree:d5c76a58e1e614ca` | `—` | 🟩 current | unknown | unknown |
| **ReclaimerVR** | 2026-08-26 | `tree:cf2ce2d8fb2ea250` | `tree:cf2ce2d8fb2ea250` | `9f746e07e6a34c5d23189bad1b2fb87b08d1c6e3` | 🟩 current | https://github.com/Nibre/ReclaimerVR | unknown |
| **REFramework** | 2026-09-04 | `tree:168b893ee9b40862` | `tree:1c02807bf9e55ed3` | `—` | 🟥 source changed | https://github.com/praydog/REFramework | see LICENSE in tree |
| **RepoXR** | 2026-08-26 | `tree:987e89a6065d2301` | `tree:987e89a6065d2301` | `15b4aec0e1411c7de5d9fdd184e02b8b1870119d` | 🟩 current | https://github.com/DaXcess/RepoXR | unknown |
| **RoR2VRMod** | 2026-08-25 | `tree:19fb84a75b171a5f` | `tree:19fb84a75b171a5f` | `—` | 🟩 current | unknown | unknown |
| **satisfactory-uevr-enhancements** | 2026-08-25 | `tree:33a7aa8069455a16` | `tree:33a7aa8069455a16` | `—` | 🟩 current | unknown | unknown |
| **Scrap-Mechanic-Native-VR** | 2026-08-27 | `tree:b34922f3c587f2ce` | `tree:b34922f3c587f2ce` | `8aabe24ec62c5c4d8ef9852250a358e1296f9bf2` | 🟩 current | https://github.com/21Suspect/Scrap-Mechanic-Native-VR | MIT |
| **Shipwright-VR** | 2026-08-26 | `tree:6847d39fbf2e86de` | `tree:6847d39fbf2e86de` | `7afef6987c7f0fb51e09bfb2f7a8f902428a38f2` | 🟩 current | https://github.com/ShinyWindow/Shipwright-VR | unknown |
| **shock2quest** | 2026-08-27 | `tree:781ad86feeac5eda` | `tree:781ad86feeac5eda` | `—` | 🟩 current | unknown | unknown |
| **Silent-Hill-3-VR-Mod** | 2026-08-29 | `unknown` | `tree:f1f0674d9d679091` | `—` | ⚪ unpinned | unknown | unknown |
| **sims4-vr** | 2026-08-25 | `tree:1dec2736beb2f5e5` | `tree:1dec2736beb2f5e5` | `—` | 🟩 current | unknown | unknown |
| **singularity-vr-mod** | 2026-08-29 | `unknown` | `tree:50b0c75b563c385d` | `—` | ⚪ unpinned | unknown | unknown |
| **SkyrimTogetherVR** | 2026-08-28 | `unknown` | `tree:549f15c81edd5a6d` | `—` | ⚪ unpinned | unknown | unknown |
| **SkyrimVR FBT 185070 1.0.3 2026-07-22T11-37Z HZCMOyLlG** | 2026-09-05 | `unknown` | `tree:381cbb4b4c660656` | `—` | ⚪ unpinned | unknown | unknown |
| **Snowrunner-VR** | 2026-08-29 | `unknown` | `tree:0d822ae5b0b2ac8d` | `—` | ⚪ unpinned | unknown | unknown |
| **SonsVR_Mod** | 2026-08-27 | `tree:6db3fde18d9a2cc3` | `tree:6db3fde18d9a2cc3` | `—` | 🟩 current | unknown | unknown |
| **SPT-VR** | 2026-08-25 | `tree:3e000668126c723f` | `tree:3e000668126c723f` | `—` | 🟩 current | unknown | unknown |
| **Sterallax6DOF-silksong** | 2026-08-26 | `tree:d0f4634655052b15` | `tree:d0f4634655052b15` | `—` | 🟩 current | unknown | unknown |
| **SubmersedVR** | 2026-08-27 | `tree:6f1c537947774a46` | `tree:6f1c537947774a46` | `—` | 🟩 current | unknown | unknown |
| **SystemReShock-UEVR-Plugin** | 2026-08-25 | `tree:00679eccfd4d256f` | `tree:00679eccfd4d256f` | `—` | 🟩 current | unknown | unknown |
| **Talemann-RE4** | 2026-09-04 | `unknown` | `tree:509eecb1574a62d1` | `—` | ⚪ unpinned | unknown | unknown |
| **TechtonicaVR** | 2026-08-27 | `tree:9bd62050d21c6d75` | `tree:9bd62050d21c6d75` | `—` | 🟩 current | unknown | unknown |
| **the-evil-within-vr-external-research** | 2026-08-29 | `unknown` | `tree:86941594e13fb4ae` | `—` | ⚪ unpinned | unknown | unknown |
| **thedarkmodvr** | 2026-08-25 | `tree:7874ef99aa2ed9e7` | `tree:7874ef99aa2ed9e7` | `—` | 🟩 current | unknown | unknown |
| **theHunterCotW-VR** | 2026-08-29 | `unknown` | `tree:f8b750f433504b25` | `—` | ⚪ unpinned | unknown | unknown |
| **TwoForksVR** | unknown | `tree:d638ddb7289ba69f` | `tree:d638ddb7289ba69f` | `—` | 🟩 current | unknown | unknown |
| **UEVR** | 2026-08-25 | `tree:ed8c07a5139dfdb0` | `tree:ed8c07a5139dfdb0` | `—` | 🟩 current | unknown | unknown |
| **unreal-gold-vr-external-research** | 2026-08-29 | `unknown` | `tree:83ff5ed3badace3f` | `—` | ⚪ unpinned | unknown | unknown |
| **VirtualFortress2** | 2026-08-27 | `tree:a20f91fac220f18e` | `tree:a20f91fac220f18e` | `—` | 🟩 current | unknown | unknown |
| **visceral-re2-vr-mod** | 2026-08-29 | `tree:dfbb912f1ec1c758` | `tree:b54e8fb8f08ff568` | `—` | 🟥 source changed | unknown | unknown |
| **Vostok-VR-Mod** | 2026-08-26 | `tree:12bd87bb2b93482c` | `tree:12bd87bb2b93482c` | `74f73105d1e7326d60dedd525a3e6cd68bf30839` | 🟩 current | https://github.com/Blah64/Vostok-VR-Mod | unknown |
| **VRIK Player Avatar 23416 0.8.6 2026-07-12T13-00Z Yj6wQRIkO** | 2026-09-05 | `unknown` | `tree:a9678ae3c00b1813` | `—` | ⚪ unpinned | unknown | unknown |
| **WeWereInVR** | 2026-08-28 | `unknown` | `tree:73ae278c47bffb04` | `—` | ⚪ unpinned | unknown | unknown |
| **White_Knuckle_VR** | 2026-08-25 | `tree:0e9bfa4ea9f7dd43` | `tree:0e9bfa4ea9f7dd43` | `—` | 🟩 current | unknown | unknown |
| **witcher3-vr** | 2026-08-25 | `tree:ea13c4e9680cad41` | `tree:37b6d0281492167f` | `—` | 🟥 source changed | unknown | unknown |
| **WorldWarVR-Releases** | 2026-08-25 | `tree:063d02ae99714575` | `tree:063d02ae99714575` | `—` | 🟩 current | unknown | unknown |
| **XIII2003-vr-external-research** | 2026-08-29 | `unknown` | `tree:3e9cdbe38f8f12f6` | `—` | ⚪ unpinned | unknown | unknown |
| **XIII2003-vr-mod** | 2026-08-29 | `unknown` | `tree:72fc043a98da5f11` | `—` | ⚪ unpinned | unknown | unknown |

## Untracked directories

None. Every directory under `Other VR mods/` is tracked or explicitly classified as not-a-source.

### Deliberately not sources

- `Dishonored-VR-metalink-test` — one built d3d9.dll plus its hash and a readme - a test artifact of Dishonored-VR-fork, not a source tree
- `DishonoredVR-alpha` — binary alpha distribution (Binaries/, INSTALL.txt, a resolution .bat) - no source
- `Immersive HUD-5-1-4-1751974538` — texture pack, not a mod
- `SS2 AE 1.3 nointro and scp beta8-3-1-3-1774982605` — installer
- `SS2 OG` — game assets + tweak packs; reference material for SS2VR
- `UEVR-UEVR_AFW_v1.0-beta.5` — UEVR release binaries; superseded by the UEVR source checkout
- `Elden Ring - Luke Ross` — empty directory - no files present
- `Farcry VrMod` — a single installer .exe; nothing readable without running it
- `MechWarrior 5 Mercenaries` — cockpit/shader mods plus MechShaker (a bass-shaker haptics tool with its own Settings.yaml) - not a VR conversion
- `X-Wing Alliance` — TIE Fighter Total Conversion installer and readme - a total conversion, not a VR mod
- `VR_HEADSET_MANAGER` — headset/runtime management utility - not a VR conversion or a mod of a game
- `skyrim-vr-automation` — install/automation scripting around Skyrim VR - no VR implementation of its own
- `BigWalkVRInstaller` — installer for a third-party VR mod - packaging only, no VR implementation
- `Ship-9.2.3-win64-ship-1.3.1` — build output of Shipwright-VR (assets + binaries, no source)

## Fleet projects

| Project | Status | Engine | Integration authority | API | Arch | Tier achieved | Tier target | Stereo route | Files | Docs | Last change | Freshness | Area completeness |
|---|---|---|---|---|---|---|---|---|--:|--:|---|---|---|
| **ss2vr-work** | active mod | Dark / KEX | hybrid-re+script | D3D11 | x64 | T3 | — | R2 · per-draw replay | 3800 | 351 | 2026-09-05 | 🟥 source changed | 9F / 3P / 0S / 0NR / 1— |
| **BioshockVR** | active mod | UE2.5 Vengeance | re-owned | D3D11 | x86 | T3 | — | R2 · per-draw replay | 4912 | 2582 | 2026-09-03 | 🟥 source changed | 7F / 4P / 0S / 1NR / 1— |
| **SOMAVR** | active mod | HPL3 | hybrid-re+source-oracle | OpenGL 4.6 | x64 | T3 | — | R3 · alternate-eye | 18085 | 1446 | 2026-09-05 | 🟥 source changed | 7F / 6P / 0S / 0NR / 0— |
| **PreyVR** | active mod | CryEngine (Arkane) | re-owned | D3D11 | x64 | pre-T1 | — | unproven | 1871 | 264 | 2026-09-05 | 🟥 source changed | 2F / 3P / 1S / 0NR / 7— |
| **DishonoredVR** | active mod | UE3 | re-owned | D3D9 | x86 | pre-T1 | — | unproven | 474 | 97 | 2026-09-04 | 🟥 source changed | 2F / 3P / 0S / 0NR / 8— |
| **FarCry2-vr** | active mod | Dunia | re-owned | D3D10 (D3D9 selectable) | x86 | T1 | — | R2 · per-draw replay | 5619 | 132 | 2026-09-05 | 🟥 source changed | 7F / 2P / 0S / 0NR / 4— |
| **Swat4-VR** | active mod | UE2.5 Vengeance | hybrid-re+sdk-oracle | D3D9 | x86 | pre-T1 | — | unproven | 221 | 33 | 2026-09-05 | 🟥 source changed | 4F / 5P / 1S / 0NR / 3— |
| **Sims4VR** | research target | EA custom (Sims 4) | script-owned | D3D11 | x64 | pre-T1 | T2 | unproven | 160 | 18 | 2026-09-04 | 🟥 source changed | 0F / 2P / 0S / 1NR / 10— |
| **SoF-VR** | active mod | id Tech 2 / Raven fork | hybrid-re+sdk-oracle | OpenGL 1.x | x86 | pre-T1 | T2 | unproven | 69 | 30 | 2026-09-04 | 🟥 source changed | 2F / 3P / 0S / 8NR / 0— |
| **Medal-of-Honor-vr** | active mod | id Tech 3 / FAKK2 via OpenMoHAA | source-owned | OpenGL | x64 | T1 | T3 | R1 · native re-entry | 3605 | 306 | 2026-09-05 | 🟥 source changed | 4F / 4P / 0S / 5NR / 0— |

## Per-source area detail

### Fleet

#### BioshockVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `HEADSET` | — |
| `xr_lifecycle` | 🟨 partial | `LIVE` | — |
| `xr_input` | 🟨 partial | `SOURCE` | — |
| `camera_tracking` | 🟩 full | `HEADSET` | — |
| `render_hazards` | 🟩 full | `LIVE` | — |
| `ui_hud` | 🟨 partial | `LIVE` | — |
| `hands_interaction` | 🟩 full | `SOURCE` | 2026-08-28 re-review. NOTE ON PROVENANCE: this project's change since 2026-08-25 is entirely UNCOMMITTED working-tree work (33 modified files, last commit 2026-07-22), so the reviewed revision is a tree fingerprint of the working copy and not of any commit. docs/native-arm-controller-aim.md now states a degrees-of-freedom ownership split that adopts ch12: the native player heading owns planar body yaw (and snap/smooth/native turning must update that same heading so locomotion, weapon and shoulders agree); HMD position translates the inferred shoulder centre for lean/room-scale/crouch, while HMD pitch and roll do NOT rotate the shoulder bar and head-only yaw does not turn the torso; the calibrated grip pose owns the wrist endpoint, with the aim pose kept as a separate gameplay-ray contract; and the game's own post-animation AimIKTargetTracker owns the upper-arm/forearm/hand solve. +804 lines across HYPOTHESES, RE_FINDINGS and a new USER_TEST_LOG. |
| `input_locomotion` | 🟩 full | `LIVE` | — |
| `performance` | 🟨 partial | `LIVE` | — |
| `audio` | 🟥 not reviewed | `—` | No fleet audio harvest has been normalised yet. |
| `packaging_deploy` | 🟩 full | `SOURCE` | — |
| `re_discovery` | 🟩 full | `LIVE` | — |
| `source_integration` | — no entry — | — | — |

#### DishonoredVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `STATIC` | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟨 partial | `STATIC` | — |
| `render_hazards` | 🟩 full | `LIVE` | 2026-08-28 re-review. The interop probe created both D3D9 devices WITHOUT D3DCREATE_FPU_PRESERVE, so every timing figure in their doc 08 came off a thread whose precision had never been checked. Measured rather than retracted: simulating the arithmetic at both precisions across three plausible QPC frequencies gives a worst absolute error of 4.4e-07 ms against a reporting granularity of 1e-03 ms and an identical p95 index, so nothing needed retracting - and they name that as luck rather than design, since the same trap on rotation composition accumulates instead of cancelling. Both devices now pass the flag. SOURCE of TEST-006: the probe proves it can SEE the degraded state before its clean verdict is trusted - sets _PC_24, confirms read-back, restores, confirms restore, and exits 1 if that round trip fails. |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | — |
| `re_discovery` | 🟩 full | `STATIC` | — |
| `source_integration` | — no entry — | — | — |

#### FarCry2-vr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `HEADSET` | — |
| `xr_lifecycle` | 🟨 partial | `LIVE` | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟩 full | `LIVE` | — |
| `render_hazards` | 🟩 full | `LIVE` | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | 🟩 full | `HEADSET` | 2026-08-28 re-review, 40 commits since 2026-08-25. The lane advanced from a bone census to a driven hand: the bone array is PROVEN the render source; bone 80 is the weapon attach point, confirmed two ways; the grip drives a bone CLUSTER rather than one bone, because a hand is not a single transform; two-bone arm IK is wired behind config keys with positional tracking and the left hand both live; live grip-tuning verbs (grip.trim / grip.cluster / grip.bone / grip.on / grip.off) tune in the headset. Bone indices are never hardcoded - Far Cry 2 has nine playable characters. SOURCE of HAND-006: a projected fixed pole is degenerate along AND against its direction (pure-down 95 mm at the hanging rest pose; down-and-back 131 mm chicken wing aiming up-forward); pole = cross(armAxis, sideAxis) has one singularity, placed where nobody aims. Measured after: rest sweep 95 -> 1.8 mm, old antipode 236 -> 1.1 mm. |
| `input_locomotion` | 🟩 full | `LIVE` | 2026-08-28: aim takeover built at the provider seam, overwriting the shot direction, and using the SHARED play-space zero rather than one of its own. Caught in the process: the takeover stopped after exactly ten shots because a LOG cap was gating the WRITE - an instrument changing the behaviour it measured. |
| `performance` | 🟨 partial | `LIVE` | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟩 full | `SOURCE` | — |
| `re_discovery` | 🟩 full | `LIVE` | Getter census (92,298 calls, 3 pairs) missed full rigs; the animator writer exposed contiguous 106/101/101-bone arrays. Canonical receipt: FarCry2-vr/docs/RE_FINDINGS.md. STARTUP STALL RESOLVED 2026-08-28 (supersedes the earlier caveat): reproduced on the COMPLETELY UNMODIFIED game - 126 threads, two burning 95 s and 86 s of CPU, working set flat at ~350 MB for over two minutes, never presented. Burning CPU while allocating nothing is a spin, not a deadlock, and vanilla loads none of our DLLs and no OpenXR loader, so it is the GAME's fault and not the mod's. Four theories died first. A peer report of the MODDED stall tracking a sleeping headset is recorded as POSSIBLY DISTINCT rather than merged. Their timing/stability numbers are usable again, with the vanilla stall named as an environment property. |
| `source_integration` | — no entry — | — | — |

#### Medal-of-Honor-vr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `HEADSET` | Stereo ladder rungs 0a-0c and 1-7 cleared, rung 8 partial: the headset found the first culling defect on 2026-09-04 - the vertical cull planes were paired with the opposite tangents, which a vertically symmetric substitute cannot show (FAIL-CAM-025) - fixed and confirmed in the headset the same day. Geometric stereo accepted in a headset 2026-09-03 on a Quest 3. Rung 7 is cleared on real optics: predicted principal-point offset 162.9 px, measured -163 px far and mid, -167 px near, i.e. the constant optics offset plus parallax only where there is depth. |
| `xr_lifecycle` | 🟩 full | `HEADSET` | Session IDLE through FOCUSED, two 2688x2880 sRGB swapchains, 561 and 588 frames submitted without error. Result-driven fallback proven: with no headset reachable the instance is created, xrGetSystem fails, and the flat path is untouched. |
| `xr_input` | 🟥 not reviewed | `—` | Milestone 2, not started. vrInputSnapshot_t, VR_GetInput and VR_Haptic are stubs; no action sets, bindings, snap turn or aim decoupling exist. |
| `camera_tracking` | 🟨 partial | `LIVE` | Headset yaw composed once per frame onto the body after first-person eye placement, verified in the log and in pixels at 30.0 degrees, correlation 0.96. World scale is still open as H-005. |
| `render_hazards` | 🟨 partial | `SOURCE` | Census drafted from source; a RenderDoc capture of the flat build is still owed. Sky portal, cutscene camera and inventory views unexercised. |
| `ui_hud` | 🟩 full | `HEADSET` | HUD layer v2 accepted in a headset 2026-09-04: body-locked quad in LOCAL space, coverage alpha via glBlendFuncSeparate, premultiplied submission, kill switch. Layer budget peak 2 of 16. The HUD is compiled into the client executable, which is why a cgame-only mod cannot own it. Open: the flat menu draws on the layer with no cursor, because the engine hands the pointer to the OS whenever it ungrabs the mouse for a windowed menu (FAIL-HUD-011). |
| `hands_interaction` | 🟥 not reviewed | `—` | Milestone 3, open. |
| `input_locomotion` | 🟥 not reviewed | `—` | VR input must fit the existing usercmd with no protocol change. |
| `performance` | 🟥 not reviewed | `—` | VR_Init sets com_maxfps 0 once a session exists so the runtime paces the frame; the substitute keeps a pinned cap. |
| `audio` | 🟨 partial | `LIVE` | OpenAL dlopen'd through the System32 router; device opens and the default device is the Virtual Desktop audio endpoint. No spatialisation work yet. |
| `packaging_deploy` | 🟥 not reviewed | `—` | packaging/README.md only. |
| `re_discovery` | 🟨 partial | `SOURCE` | RE is not the route: retail binaries are a behaviour reference, and the shipping binary is the fork build. |
| `source_integration` | 🟩 full | `SOURCE` | Every layer is source-owned through the OpenMoHAA fork. Frame loop, stereo loop, camera construction, projection, culling, renderer and UI all buildable and shippable under GPL-2.0. Fork maintenance contract written; the fork remote is not yet created on GitHub. |

#### PreyVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `STATIC` | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟩 full | `SOURCE` | 2026-08-28 re-review. RenderCameraMatchesSource no longer uses a tolerance chosen by eye: RenderCameraResidual() takes its limit from a measured separation table (correct 0.000000000; tightest wrong case, a 0.004 asymmetry error, 0.004000008 at 40x the 1e-4 limit; the rest 600x-7500x above), and the tests assert THE GAP so widening the limit later breaks a test. SOURCE of TEST-007. AsymmetryFromFovTangents inverts the SetCamera formula to solve OpenXR XrFovf tangents to Prey's fWL/fWR/fWB/fWT asymmetry shifts, round-trip tested, guarded by 'a symmetric FoV must yield all-zero shifts' because a sign error survives every other check while quietly symmetrising the eye. CAVEAT THEY RAISED THEMSELVES: the correct case reproduces to exactly zero because the test recomputes with the same formula on the same inputs - the live rounding floor is unmeasured, and LIVE_CAPTURE_PLAN now logs the residual as a number rather than a verdict. |
| `render_hazards` | 🟨 partial | `SOURCE` | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | 🟧 skimmed | `STATIC` | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | — |
| `re_discovery` | 🟩 full | `STATIC` | — |
| `source_integration` | — no entry — | — | — |

#### Sims4VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | Research target; no stereo proof yet. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟨 partial | `STATIC` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | 🟨 partial | `STATIC` | — |
| `source_integration` | — no entry — | — | — |

#### SoF-VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | Stereo ladder is authored with 10 rungs; every rung OPEN. R1 native re-entry is declared, not proven. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | 32-bit runtime shortlist checked; no session yet. Runtime choice OPEN until M5. |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟩 full | `LIVE` | M2 confirmed refdef_t live: prefix shift +1, unique match, fov_y residual 0.0000 against CalcFov, fov_x exactly the install's fov cvar. Viewport, FOV, position and angles each carry a receipt. Two static inferences corrected (F-009): time is at +0x44 not +0x50, and +0x00 is written every frame. |
| `render_hazards` | 🟨 partial | `LIVE` | M1 slot census: 52 wrapped slots, ABI-transparent, no crash or frame-rate change. Slot 16 is world-render only, absent through menu and loading, 1:1 with the frame bracket in gameplay. |
| `ui_hud` | 🟥 not reviewed | `—` | 2D slots 17-43 are visible to the proxy; HUD quad planned from the backbuffer between RenderFrame and EndFrame. |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | 🟥 not reviewed | `—` | refimport_t carries Cmd_ExecuteText and Cvar_Set, so the proxy can drive binds without RE of SoF.exe; the index map is OPEN. |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟨 partial | `LIVE` | Ships as ref_vr.dll beside ref_gl.dll, selected by +set vid_ref vr. No byte of SoF.exe or ref_gl.dll is patched for T1. |
| `re_discovery` | 🟩 full | `LIVE` | Live export table reproduces REF_API_DRIFT section 2 exactly across all 54 slots. Slots 26 and 32 return uninitialised debug fill, confirming from the client side that GetRefAPI never assigns them. |
| `source_integration` | 🟨 partial | `SOURCE` | SoF SDK (June 2000, 1.0x) and id's Quake 2 tree are oracles only. The shipped DLLs are 1.07f, so an SDK rebuild may not match retail behaviour or save format (FAIL-ACCESS-001 risk). Source lane is reserved for T3/T4. |

#### SOMAVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `HEADSET` | 2026-08-28 re-review: AFR pair coherence now enforced, XR freshness added, and mirrored native transform bases rejected (the \|det\| = 1 hazard from ch06, adopted). Stable elbow poles landed in the same pass. |
| `xr_lifecycle` | 🟨 partial | `HEADSET` | — |
| `xr_input` | 🟨 partial | `SOURCE` | — |
| `camera_tracking` | 🟩 full | `HEADSET` | — |
| `render_hazards` | 🟩 full | `LIVE` | — |
| `ui_hud` | 🟩 full | `HEADSET` | — |
| `hands_interaction` | 🟨 partial | `LIVE` | — |
| `input_locomotion` | 🟩 full | `HEADSET` | — |
| `performance` | 🟨 partial | `LIVE` | — |
| `audio` | 🟨 partial | `SOURCE` | — |
| `packaging_deploy` | 🟩 full | `SOURCE` | — |
| `re_discovery` | 🟩 full | `LIVE` | — |
| `source_integration` | 🟨 partial | `SOURCE` | HPL2 source is used as an architectural oracle; SOMA retail remains an injected target. |

#### ss2vr-work

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `HEADSET` | — |
| `xr_lifecycle` | 🟩 full | `HEADSET` | — |
| `xr_input` | 🟨 partial | `SOURCE` | — |
| `camera_tracking` | 🟩 full | `HEADSET` | — |
| `render_hazards` | 🟩 full | `LIVE` | — |
| `ui_hud` | 🟩 full | `HEADSET` | — |
| `hands_interaction` | 🟩 full | `SOURCE` | 2026-08-28 re-review. Same provenance caveat as BioshockVR: the change is UNCOMMITTED working-tree work (42 modified files, last commit 2026-07-30), so the reviewed revision fingerprints the working copy. Two new design documents, both instances of META-006 applied to GAMEPLAY rather than to a render interface, which is why neither became a new pattern. MELEE_VR_REPORT: SS2 melee is charge-based and the whole lifecycle is already exposed - attack down/up input, native WeaponCharge/WeaponSwing events, Squirrel OnChargeSwing/OnReleaseSwing/OnHitSwing stubs, and a SwingExpose property carrying the hit arc - so the work is to TRIGGER the engine's existing two attack tiers from controller motion rather than to rebuild animation, hit detection and damage. WEAPON_MODEL_REPORT: the viewmodel is an ordinary Dark object and Dark objects carry a settable Scale vector property, so the ~2-3x viewmodel oversize is a Squirrel property write in the handler that already forces CameraObj - no hook needed. |
| `input_locomotion` | 🟩 full | `HEADSET` | — |
| `performance` | 🟨 partial | `LIVE` | — |
| `audio` | 🟨 partial | `SOURCE` | — |
| `packaging_deploy` | 🟩 full | `SOURCE` | — |
| `re_discovery` | 🟩 full | `LIVE` | — |
| `source_integration` | — no entry — | — | — |

#### Swat4-VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `HEADSET` | — |
| `xr_lifecycle` | 🟩 full | `HEADSET` | — |
| `xr_input` | 🟧 skimmed | `SOURCE` | — |
| `camera_tracking` | 🟨 partial | `STATIC` | — |
| `render_hazards` | 🟩 full | `SOURCE` | 2026-08-28 re-review. Adopted two playbook items against shipped code. (1) \|det\| = 1 accepted a MIRRORED world and projectionResidual's ortho term tested lengths and dot products only, so it would have shipped one; nothing in 814 checks pinned the sign. determinant3() and basisHandedness() now exposed, basisFromDirection pinned across seven directions, and the mirrored case asserted to PASS an orthonormality check so the suite records WHY magnitude is insufficient. 814 -> 849 checks. Mutation testing caught a subtlety worth keeping: one handedness mutation SURVIVED because reordering the degenerate branch's cross flips right, and up = cross(right, forward) flips with it, so they cancel - not a mirror but a 180-degree ROLL, in a branch reached only when the player looks straight up. Real bug, wrong assertion. (2) C8 ships: reads the x87 control word on the render thread and names the precision (ch10 #d3d9-x87-precision). |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | 🟨 partial | `LIVE` | — |
| `performance` | 🟨 partial | `LIVE` | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟩 full | `SOURCE` | — |
| `re_discovery` | 🟩 full | `LIVE` | — |
| `source_integration` | 🟨 partial | `SOURCE` | UnrealScript/SDK/exports illuminate the retail native-injector route; no source-owned deliverable. |

### External

#### Aliens-Versus-Predator-VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟧 skimmed | `SOURCE` | NOT AvP2 - this is AvP CLASSIC (1999) forked from atsb/NakedAvP, so full source is available and none of the cross-bitness bridge problem applies. Confirmed on Quest 1 (v50), Quest 2 and Quest 3, with flat builds for Android, Windows and Linux from the same tree. STANDALONE ANDROID VR is the notable class here: ships libopenxr_loader.so for arm64-v8a and armeabi-v7a with an Android app target, alongside x64vr Windows and Linux builds - the first standalone-Android target in this ledger with VR actually working (goldeneye-omniport's VR sections are still TBD). |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟧 skimmed | `AUTHOR` | 0.6 changed the app folder name, so saved progress does not carry across - an install-path change is a save-data migration whether or not it was meant to be. Known open issue: alien wall-walking broken. |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟧 skimmed | `SOURCE` | source-port vehicle: OpenXR added directly to an open-source port rather than injected |

#### anvilengine2vr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟧 skimmed | `AUTHOR` | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟨 partial | `SOURCE` | — |
| `render_hazards` | 🟧 skimmed | `AUTHOR` | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | 🟩 full | `SOURCE` | — |
| `source_integration` | — no entry — | — | — |

#### BendyVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟧 skimmed | `AUTHOR` | lifecycle/abandonment finding only; source unread |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### BF2VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟧 skimmed | `SOURCE` | ActionsService.cpp not read in detail |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | 🟨 partial | `SOURCE` | — |
| `ui_hud` | 🟩 full | `SOURCE` | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟨 partial | `AUTHOR` | — |
| `re_discovery` | 🟩 full | `SOURCE` | — |
| `source_integration` | — no entry — | — | — |

#### bfbc2-vr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | harvested 2026-08-28 into ch14 + CAM-008: depth-slice residue P'.P-1 multiplies every translation by t'/t (measured 75x and 213x); per-draw correction around each draw's own recovered projection, ~4 distinct per frame |
| `xr_lifecycle` | 🟨 partial | `SOURCE` | 32-bit openvr_api.dll directly - the simplest of the three bitness routes in ch09 |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟩 full | `SOURCE` | harvested into CAM-009: widening the projection does not widen culling - engine culls at its native frustum, settings.ini Fov has no effect on tangents; auto-widen off by default |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟨 partial | `SOURCE` | weapon on the aim controller; aim convergence designed but not built |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | build/install/uninstall scripts; PunkBuster makes singleplayer-only a hard constraint |
| `re_discovery` | 🟨 partial | `SOURCE` | in-process memory scanner with an autonomous engine-FOV hunt; Frostbite 1.5 reflection names as the memory-patch starting points |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### BFVR-Battlefield-1942

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | docs/stereo-math.md is a runtime-independent C++ boundary with no OpenXR/D3D/game dependency - OpenXR metres to D3D8 row-vector left-handed via C = diag(1,1,-1), inverse(C*[R,t]*C), off-centre projection from tangents. Fourth instance of desk-testable maths. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟩 full | `SOURCE` | ui-pointer-design.md harvested to ch04 #pointer-coordinate-spaces: three coordinate spaces (800x600 native canvas derived from ortho m00=2/w, 1920x1080 raster, 1872x2016 padded XR texture at z=-1.5m/1.6m wide) and two discriminators - error varying with POSITION means conflated spaces, error varying with MOVEMENT HISTORY means relative deltas mixed with an absolute point. |
| `hands_interaction` | 🟩 full | `SOURCE` | weapon-pose-design.md harvested: explicit non-ownership statement (the game keeps firing/recoil/reload/spread/projectiles/hit detection/network), one generic route with no per-item pose code, an enumerated list of states that keep the flat view model, and separate pose-VALID vs pose-TRACKED gating so only pose-dependent features degrade (FAIL-HAND-003). grip for the model, aim for the ray. ELBOW: src/client/BFSoldierNativeArmPole + src/stereo/ArmPoleVectorMath (tested, runtime-independent) harvested as HAND-005 - they HOOK BF1942's own MayaApplyIk2BoneSolver and substitute ONLY the pole argument; anatomical bend in the shoulder/body frame, continuous blend to a fixed singularity-safe direction, 12 deg/sample slerp rate limit, result flags saying which branch answered, fail-closed to the native pole. |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟩 full | `SOURCE` | ambient-occlusion-feasibility.md harvested to ch08 #feasibility-rejection-table as the model closed-families artifact. Generalisable reasons: one-eye screen-space effects disagree binocularly, replay cost tracks draw count, and a generic Present-hooking injector cannot see owned eye targets. Distinguishes Reject from Defer with named missing preconditions. |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | PACK-002: one parent folder, no proxy DLL in the game root, no replaced executable, no game-data edits, uninstall = delete the folder. |
| `re_discovery` | 🟩 full | `SOURCE` | docs/early-d3d8-observer.md harvested as RE-005: chained one-shot hardware breakpoints, debug-register save/restore etiquette, partial-result honesty, suspended-start init off the loader lock, IAT observation without interface substitution, and a probe permanently removed because it froze a session. |
| `source_integration` | — no entry — | — | — |

#### Bioshock-Remastered-VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `AUTHOR` | — |
| `xr_lifecycle` | 🟩 full | `SOURCE` | harvested 2026-08-28 into ch09: OpenXR-over-OpenVR shim as a BITNESS bridge (SteamVR's OpenXR runtime has no 32-bit support); __cdecl vs __stdcall split in openvr_api.dll; compositor-model mismatch re-composited as a quad at 50 m |
| `xr_input` | 🟩 full | `SOURCE` | harvested 2026-08-28 into ch13 + INPUT-004/INPUT-005: square (per-axis) deadzone distorts synthesized stick DIRECTION by ~11 deg with the exact inverse; measured turn-rate cliff at the rail |
| `camera_tracking` | 🟨 partial | `AUTHOR` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟨 partial | `AUTHOR` | four named placement routes for 2D screens - anchor / follow / scene / panel - routed per screen name rather than one global policy |
| `hands_interaction` | 🟨 partial | `SOURCE` | harvested 2026-08-28 into ch13: weapon parent is itself animated; grip offsets do not scale with resolution/FOV (scaling law ruled out); shared-value aim/crosshair/shot makes calibration exact |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | harvested 2026-08-28 into CFG-003: game rewrites its config at exit with what it actually ran at, so startup values must be written before the process starts |
| `re_discovery` | 🟨 partial | `SOURCE` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### bioshock-trilogy-vr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | IStereoPolicy ladder (STR-006). BS1 and BS2 both ultimately required separately derived structural single-thread paths; BS2's earlier threaded-safe verdict was explicitly refuted when the Draw-tail flush handshake was found. Infinite (UE3 6829) reached SequentialReentry with no 1t machinery on its threaded ring buffer. Rule: test threaded first, port no cure until a measured stall demands it, then derive every seam and constant fresh. Infinite's re-entry root is the viewport draw (client-draw-only double is a recorded negative); pass 2 is deny-by-default on a known caller return RVA; pair pacing is one wait/locate/prediction per game tick. |
| `xr_lifecycle` | 🟨 partial | `AUTHOR` | Symmetric subsystem toggle (XR-004), its hang/crawl symptom (FAIL-XR-005), and non-FOCUSED ~10 Hz pacing inherited by the game. |
| `xr_input` | 🟧 skimmed | `AUTHOR` | Synthetic-XInput lane plus a gesture-detection layering rule; full controller map read, code not. |
| `camera_tracking` | 🟩 full | `SOURCE` | CAM-004 now has three title-specific FOV contracts: BS1 true-horizontal; BS2 16:9-referenced horizontal with a live option that animates 73-96 degrees; Infinite's rendered lens is vertical-referenced, while its later camera-degrees lever is horizontal at a fixed 16:9 anchor (the same lens expressed at a different ownership boundary). Infinite claimRatioH baseline 0.5576. |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | 🟧 skimmed | `AUTHOR` | Swing-to-attack gesture pattern: gate on identity not plausibility, hysteresis AND cooldown, sim command with repetition count. |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | CHAPTER 13 REWRITTEN for this repo. The project moved from mohamad-balouza/bioshock-vr to VR-Stereo-Hub/bioshock-trilogy-vr; the reviewed 640-commit checkout is tagged v0.8.2. One branch and release line serve three games across UE2.5 and UE3; the same XINPUT1_3 proxy delivery vehicle survives both engine generations, while old per-game branches are historical. One game owns the headset at a time, enforced by a preflight script that exempts build/install/package/log-tail. |
| `re_discovery` | 🟨 partial | `SOURCE` | No raw addresses outside patterns.cpp; FName-chain scan; kiero-style D3D11 vtable discovery. Infinite imports XINPUT1_3 by ordinal 2/3 and does not statically import d3d11/dxgi; it is x86 at fixed base 0x00400000 with no ASLR. src/tools/xrsim harvested in full to ch09 #substitute-runtime-build: 5,296 lines, one .def-pinned xrNegotiateLoaderRuntimeInterface export, ~65 entry points, bidirectional negotiation validation, no same-thread ordering assumptions, a NO UNBOUNDED WAIT invariant, session-scoped abort separate from wake, and a declarative .xrs scenario DSL carrying its own noise floor. |
| `source_integration` | — no entry — | — | — |

#### BL1GOTYVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟧 skimmed | `AUTHOR` | geometric stereo, stable rotational and positional 6DoF, and - the phrase worth chasing - 'RESOLUTION-INDEPENDENT PROJECTION AND COMPOSITOR FOV MATCHING', which is the CAM-009/CAM-010 problem stated as a solved feature. Headset-tested on SteamVR/Steam Link and VDXR/Virtual Desktop. Win64/D3D11 only: explicitly NOT the 2009 release. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟧 skimmed | `AUTHOR` | motion-controller aiming plus native gamepad input; Quest Touch bindings |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟧 skimmed | `AUTHOR` | VR HUD |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟧 skimmed | `AUTHOR` | no modification of the game executable |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### black-mesa-l4d2vr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | fused stereo submit; per-milestone honest status table distinguishing compiled / installed / user-verified |
| `xr_lifecycle` | 🟩 full | `SOURCE` | harvested 2026-08-28 into ch09 bitness table: out-of-process x64 OpenXRHelper64.exe owns the OpenXR session and imports eye textures as OPAQUE_WIN32_KMT shared handles over a magic-tagged, versioned shared-memory bridge; falls back to OpenVR if the helper is missing so the game still launches |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟨 partial | `SOURCE` | L4D2VR-style HMD on view copies plus SetViewAngles and CreateMove |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟨 partial | `SOURCE` | uncoupled viewmodel on the aim controller, hidden FP arms, independent hand markers |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟨 partial | `SOURCE` | per-symbol offset table with MATCH/mismatch columns against the reference build |
| `source_integration` | 🟨 partial | `SOURCE` | transplanting a working VR architecture onto a sibling game on the same engine |

#### bo1-vr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | 🟨 partial | `SOURCE` | DXVK submission-queue race: hold the queue lock across WaitGetPoses, not just Submit. Also hosts under Proton/Linux via xrizer -> OpenXR -> Monado/WiVRn. |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟩 full | `SOURCE` | MIRRORED-BASIS CHECK harvested to ch06 #mirrored-basis: requires det==+1 AND forward x left == up, because the naive \|det\|~=1 accepts a mirrored basis. Same object file linked into an offline test binary that must REJECT four named wrong composition orderings; re-run at DLL load; degrades to position-only after 30 rejects. |
| `render_hazards` | 🟩 full | `SOURCE` | D3D9 x87 24-bit-mantissa trap harvested to ch10 #d3d9-x87-precision - silently degrades pose maths in EVERY D3D9-era injector unless D3DCREATE_FPU_PRESERVE is set. |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | 🟨 partial | `SOURCE` | Hand-written asm detours against LTCG non-standard calling conventions on a CEG-protected exe. Rule harvested: hook UPSTREAM of where the engine caches vieworg into lighting/PVS globals. |
| `source_integration` | — no entry — | — | — |

#### Buffout4 NG-64880-1-38-3-1785297452

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | 🟥 not reviewed | `—` | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | Not an interaction mod - it is the FIELD OPERATIONS layer, and included in the interaction-coverage comparison for contrast. |
| `input_locomotion` | 🟥 not reviewed | `—` | — |
| `performance` | 🟨 partial | `SOURCE` | harvested 2026-09-05 into ch07 #engine-hardening. Five patches replace bespoke allocators with the OS ones - global memory manager, Scaleform, small-block, Havok memory system, texture streamer local heap - plus MemoryManagerDebug which traces allocations to ATTRIBUTE faults to modules, and MaxStdIO raising the CRT 512-handle limit to 2048. Reasonable engineering for 2008 hardware, now slower and more fragile than the default allocator, and several fleet targets are that vintage. |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟨 partial | `SOURCE` | harvested 2026-09-05 into ch06 #symbolised-crash-reports and TEST-018. Ships the GAME's PDBs (Fallout4.pdb 65 MB, Fallout4VR.pdb 30 MB, both genuine Microsoft C/C++ MSF 7.00) beside msdia140.dll, Microsoft's Debug Interface Access library, and resolves the crash stack AT FAULT TIME so reports name functions rather than addresses. Two config options worth copying with it: Symcache so symbolisation is not repeated work, and WaitForDebugger which attaches a debugger WHEN A CRASH OCCURS rather than at startup, turning an unreproducible field crash into a live session. Also a 22-entry engine defect registry where every fix is individually toggleable (a bisection axis) and carries its cause in one sentence, sometimes with a link to the community report - including SafeExit, which fixes crashes caused by PLUGIN HOOKS at shutdown. And a [Warnings] tier that fires where malformed data is ACCEPTED rather than where it later crashes. |
| `source_integration` | — no entry — | — | — |

#### CallOfDuty4_VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | src/vr/ read - 24 files, 31k lines. vr_openxr.cpp alone is 25k and remains unread in detail; that is the only stereo work outstanding here. |
| `xr_lifecycle` | 🟨 partial | `SOURCE` | XR-006 harvested from vr_d3d9ex_interop_probe: a one-time NON-INVASIVE bridge proof that creates a temporary device and never replaces the game renderer, asserting Direct3DCreate9Ex availability, adapter-LUID match against the OpenXR request, a shared D3D9Ex render-target texture opened by D3D11, AND that the running game device is on the same adapter. Requirements: D3D9Ex not plain D3D9, D3DUSAGE_RENDERTARGET, D3DFMT_A8R8G8B8, D3DPOOL_DEFAULT, shared handle into OpenSharedResource. DishonoredVR reached the same goal by a DIFFERENT route (9On12 to D3D12). |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟧 skimmed | `AUTHOR` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | 🟨 partial | `SOURCE` | Per-weapon profiles harvested to ch02 #per-item-data-not-code: 128 weapon and 32 GUNSTOCK profiles, every entry the same bounded Pose{offset[3], angles[3]} with hard limits (12in, 90deg). Resolves the apparent contradiction with BFVR, which refuses per-item pose CODE - per-item DATA in a uniform schema is a table, not a branch. |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟩 full | `SOURCE` | KNOWN-ISSUES.md harvested to ch09 #thirty-two-bit-preflight: reports the 32-bit AND 64-bit OpenXR registry views independently and BLOCKS an OpenXR-only launch when the 32-bit manifest is absent; labels the experimental x86 OpenVR fallback a Warning rather than an equivalent; states its own evidence grade to users (offline preflight, NOT a synthetic VR session) and names the action that upgrades it to live; refuses an unrecognised install layout before writing and never guesses, downloads or moves original assets; defers layout normalisation with a named precondition. |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | 🟩 full | `SOURCE` | Reviewed as a source-port architecture. VR is a self-contained src/vr/ module (24 files) beside the engine subsystems, split by concern: openxr, openvr_input, openxr_profiles, d3d9_capture, d3d9ex_interop_probe, hud_layout, input_bindings, prompt_labels, weapon_profiles, compatibility, calibration, gestures, interactions. That module boundary is how a 634k-line port stays navigable, and is the transferable part. |

#### condemned-vr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟧 skimmed | `AUTHOR` | THIRD Jupiter EX mod in the ledger after fear-vr and FEAR2VR - the densest single-engine cluster here. Native stereo, OpenXR head tracking and motion controls with the game install unchanged. M1-M4 have passed LIVE gates; M5 is building controller-driven physical melee, per-weapon handling and an in-headset calibration menu. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟩 full | `SOURCE` | 2026-08-29, harvested into ch01 #roomscale-handoff and CAM-011 - the most complete statement of the roomscale handoff in the survey. Camera-only translation (clamped 0.25 m, added per eye, restored after render) is where everyone starts and is NOT roomscale: the player object, collision capsule, triggers, movement direction, body model and gameplay position do not move with the step. The constraint that shapes everything: add a player-controller handoff WITHOUT applying the same motion twice. Route translation and horizontal YAW ONLY through the game's own movement commands so collision, triggers and scripts stay authoritative - never SetObjectPos or an equivalent teleport. Four frames: tracking anchor, player anchor, CONSUMED motion the game demonstrably applied, and RESIDUAL it has not; subtract consumed from eye, aim, controller, weapon, IK and interaction poses. Publish one command snapshot per SIMULATION frame - never integrate inside the per-eye loop, which doubles silently. Collision has TWO layers and the second is forgotten: native movement protects the player root but not the residual HEAD volume, so the head leans through geometry the body never entered - constrain it separately with hysteresis and fade/vignette while stalled. Full stall spec recorded. Two discipline points worth as much as the design: a hook verified for ONE CALLSITE is not a general API ('do not turn the forensic hook's partial layout into an assumed general collision API'), and a sibling project's FAILURE transfers where its numbers do not - F.E.A.R.'s body-follow was disabled after oscillation and body-lag, taken as 'negative design evidence only'. RS1 was live-rejected and rolled back with the plan and evidence deliberately retained. |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟧 skimmed | `AUTHOR` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟧 skimmed | `AUTHOR` | guarded fix for Jupiter EX's redundant HID initialisation performance loss - an engine-level defect, so it should transfer to fear-vr and FEAR2VR |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟧 skimmed | `SOURCE` | run like a fleet project: AGENTS.md as the entry point, docs/CURRENT_STATE.md carrying the active gate, and a milestone doc per M0-M5 alongside PORT-PLAN, PERFORMANCE, ROOMSCALE-PLAN, ARM-IK-HANDOFF and INTERACTION-AUTHORING |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### crysis_vrmod

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | harvested 2026-08-28 into ch17: two-eye loop with a mandatory RenderBegin between passes (culling breaks without it); borrowing the engine's own e_particles_debug cvar with VF_CHEAT cleared to suppress once-per-frame work on eye 1, restored after |
| `xr_lifecycle` | 🟨 partial | `SOURCE` | harvested into HOOK-004: hook-loss detection by swapchain identity OR 1000 ms of Present silence, then reinstall the whole set |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟩 full | `SOURCE` | by-value camera borrow/restore with an m_viewCamOverridden latch; EFQ_DrawNearFov keeps viewmodel FOV in step with eye FOV |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟧 skimmed | `SOURCE` | refuses to render the world behind menus as a comfort decision |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### CSVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | 🟧 skimmed | `AUTHOR` | NOT a VR mod — it is CS16Client, a flat reverse-engineered client |
| `source_integration` | — no entry — | — | — |

#### cyberpunk-vr-port

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `AUTHOR` | 80+ RE docs; read the roadmap and mirror docs only |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | 🟩 full | `SOURCE` | Harvested 2026-08-25 into ch19: pass census, resource-state compensation, aliasing/transient-memory wall, cross-queue feeder failure and descriptor immutability. |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | 🟨 partial | `AUTHOR` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟨 partial | `SOURCE` | Pass counts and replay cost harvested into ch19; exact GPU-time attribution still needs Nsight/PIX GPU trace. |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | 🟨 partial | `AUTHOR` | — |
| `source_integration` | — no entry — | — | — |

#### Dishonored-VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | REGISTERED NOT REVIEWED 2026-09-02. ALREADY MINED by the in-house DishonoredVR project (2026-09-02), which took the render path instead and avoided its blockers - read for method and negative results, not as an open task. GingasVRFO/Dishonored-VR is a SEPARATE VR conversion of the SAME GAME as the in-house DishonoredVR project. A d3d9.dll proxy built on a FORKED DXVK, with true stereo, 6DoF, motion controls, roomscale and a hand-aimed Blink. DISCONTINUED and explicitly offered for pickup (author burned out on unreproducible reports). Its 13 numbered fork-patches read as a complete rung-2 development history: M2 frame-map instrumentation, M3 stereo splice per-eye draw replay, mirrored-VP skip, world-quad splice via a c6 identity test, depth-test state REPLACING that c6 heuristic, an explicit revert to proven M3.1, measured gates, live projection scales, live writable separation and convergence, per-draw splice verdicts, world-space UP effects (the fire fix), and the Blink marker. The real payload is dllmain.cpp (~23k lines of in-game research log); its negative results are worth more than its code. |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### Dishonored-VR-fork

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | REGISTERED NOT REVIEWED 2026-09-04. In-house fork of the shipped external mod, carrying local commits (Meta Link OpenXR backend selection; build.sh portability). The 52-patch upstream series is already distilled in ch17 #dishonored-splice; this tree adds the fork's own changes, which are not yet read. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | 🟥 not reviewed | `—` | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | 🟥 not reviewed | `—` | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### DOOM-3-BFG-VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | Computes VRScreenSeparation = 0.5*(r+l)/(r-l) from the projection matrix and uses it to shift 2D quads - independent cross-engine corroboration of the projection-centre quantity. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟨 partial | `SOURCE` | Render-backend LATE-LATCH that also regenerates every per-entity MVP (harvested to CAM-007). Body-yaw decoupled via a single bodyYawOffset scalar every rendered-transform consumer subtracts. Complete constant-bearing lean/roomscale solver; head displacement converted to velocity over one HMD frame period, run through the engine's own SlideMove, then zeroed. |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟩 full | `SOURCE` | Harvested to ch04 #hud-as-world-geometry, resolving the third HUD placement option the playbook lacked. The HUD is a REAL MAP OBJECT (models/mapobjects/hud.lwo) with a custom vr/hud material, and weaponDepthHack - idTech's existing viewmodel depth trick - is toggled by vr_hudOcclusion, so occlusion-vs-always-visible is one boolean. Placement defaults: 32in distance, 7in vertical, 30deg angle; vr_hudPosLock defaults to BODY (not face, not world). vr_hudType defaults to LOOK-ACTIVATE at a 48deg reveal pitch, with vr_hudLowHealth=20 forcing it visible below 20 health - the comfort feature yields automatically where hiding data could cost the player the game. 12 element toggles. vr_weaponSightToSurface maps the reticle onto the surface the ray hits rather than a fixed depth. |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | 🟨 partial | `SOURCE` | Candidate for the ledger's FIRST full source_integration review - the batch's one complete source-port VR implementation. |

#### edvr-unofficial-patch

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | harvested 2026-08-28 into ch14 + STR-009/STR-010: per-eye auto-exposure measured 1.5 stops apart, 0.4 with the fix; one-frame wrong-viewpoint transition dropped rather than submitted; culling frustum narrower than the render frustum, fixed by over-reporting FOV and cropping (~6% GPU) |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟨 partial | `SOURCE` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟩 full | `SOURCE` | both-edges overlay stamped identically into each eye lands on the nose; screen-space-sampled hologram pattern and star glare become head-locked |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟨 partial | `AUTHOR` | every fix individually switchable back to stock, so a regression attributes to one change |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### Fallout 4 Script Extender VR (F4SEVR)-42159-0-6-21-1719284892

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | 🟥 not reviewed | `—` | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | F4SEVR 0.6.21. src/ read selectively 2026-09-05 (150 .h / 144 .cpp; f4se_loader_common) -> ch08 #loader-preflight and PACK-004. The transferable part is the LOADER, not the game layer: IdentifyEXE maps the target read-only and classifies it by PE section (a UPX0 section means packed, a Steam section means wrapped; four outcomes, and the packed case is refused BY NAME), then compares versions three ways - older, NEWER than supported, and right version but wrong build branch - each with its own actionable message. The newer-than-supported case is the one that happens to every user the day the game updates. Version comes from the version resource rather than a file hash. The game-structure layer (BS*/Game*) was not read. |
| `input_locomotion` | 🟥 not reviewed | `—` | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | — no entry — | — | — |

#### Fallout-New-Vegas-FNVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | NOT HARVESTABLE AS SHIPPED: 'Fallout New Virtual Reality' is a 12 KB FNVR.esp plus a 3 KB .7z - a plugin, not a native VR conversion, and no source. What IS readable in this directory is xNVSE, the New Vegas Script Extender, which is general modding tooling rather than a VR implementation. Extract the archive and re-assess only if the script-extender route to VR becomes relevant to a project. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟧 skimmed | `SOURCE` | xNVSE present as the script-extender substrate; the VR plugin itself is not source |

#### fear-vr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | Harvested 2026-08-25, EXTENDED 2026-08-29 from STEREO-RESEARCH.md into ch17 #second-pass-seam - the clearest worked instance of this chapter's rung-1 gate in the survey. The rule they derive is engine-independent: THE SMALLEST SAFE HOOK LIES BELOW ALL CLIENT UPDATES AND ABOVE THE PURE ENGINE WORLD RENDER, established by reading four sites (GameClientShell 4071-4104 runs PreRender/FX/shatter/ClientFX/streaming before the camera render; 4124-4134 calls CPlayerCamera::Render then dynamic FX and interface; PlayerCamera.cpp:417-419 clears the target and calls ILTRenderer::RenderCamera exactly once; iltrenderer.h:353-355 makes that a one-arg alias). Nine-step frame order matching ch17. Fallback ladder opens with 'do not blindly build a complete D3D9 command replayer' and ends with depth+image reprojection as a clearly marked compatibility mode only, with INTZ/RESZ called out as vendor-dependent and never the sole basis of the main path. NOTE: their docs are in GERMAN, which is why English keyword sweeps missed this material on earlier passes. |
| `xr_lifecycle` | 🟩 full | `SOURCE` | Harvested 2026-08-25 into ch09 (session state machine, focus-loss input neutralization, keep-submitting fallback, 10-row recovery matrix). EXTENDED 2026-08-29 from M2-D3D9-BRIDGE.md into ch09 #d3d9ex-vs-classic, #bridge-protocol and #late-attach: F.E.A.R. creates a CLASSIC IDirect3DDevice9 and a shared texture on it is refused with D3DERR_INVALIDCALL, so the project carries a GPU path for D3D9Ex (StretchRect into three shared slots per eye, D3DQUERYTYPE_EVENT fence, versioned IPC, OpenSharedResource + CopyResource, fullscreen shader into both swapchains, NO CPU readback) and a flagged CPU compatibility path for classic D3D9 - published as FEARVR_BF_CPU_FALLBACK, logged as path=cpu_d3d9ex, and named in the doc as debt against the stated invariant 'no per-frame CPU readback'. Protocol: three slots per eye with EMPTY/WRITING/READY/CONSUMING, separate host and game heartbeats, BOTH adapter LUIDs checked before import, a seqlock, and every kernel object carrying a RANDOM SESSION ID so two instances cannot collide; magic, version, header size, slot size and slot count all validated on connect, header exactly 432 bytes in x86 and x64. Late attach is mandatory here - the -archcfg GameClient module loads AFTER the engine creates its device, so an IAT hook on Direct3DCreate9 is too late; they create a hidden helper device to read the Present/Reset targets and detour outside DllMain. |
| `xr_input` | 🟩 full | `SOURCE` | Harvested 2026-08-25 into ch03: physical action transport, semantic mapping at the game boundary, profile-change logging, focus/staleness neutralization, action edges and reverse haptics. |
| `camera_tracking` | 🟩 full | `SOURCE` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟨 partial | `SOURCE` | — |
| `hands_interaction` | 🟩 full | `SOURCE` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟩 full | `SOURCE` | 2026-08-29 (was not_reviewed, and it held the largest unharvested material in the ledger). Harvested into ch19. THREE PER-FRAME DRIVER CALLS THAT DID NOT BELONG, with before/after: OpenSharedResource per eye per game frame is 'a kernel call with a driver lock, not a pointer copy' - six slots exist, so open once and memoise by handle; CreateRenderTargetView per eye per XR image, when the swapchain image count is fixed after enumeration (release views BEFORE the images, a view holds a reference); Flush per eye when once per frame suffices. copy_avg_us 310-440 with spikes to 3772 became 82-106 with max 612, and xr_fps went from dipping to 72.8 to never below 89.4 over 102 windows / 30,600 frames. THE BUDGET DECOMPOSITION is the reusable part: frame_cpu_max_us is own work between xrBeginFrame and xrEndFrame MINUS the compositor-controlled waits, with section peaks that together cover the frame - which is how they could show all 19 long frames were >90% xrEndFrame rather than their own code. pose_fallback: an imported image with no remembered render pose gets the CURRENT pose forced on it, so the compositor believes it fresh and STOPS reprojecting - and only the first occurrence had ever been logged. Two hypotheses recorded as wrong (async logger, Flush). |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | MATURITY, recorded here because the external schema has no tier or stereo_rung field: this is at M6 with M5 confirmed in-headset on Quest 3 and SteamVR - native stereo world rendering, head tracking, world-locked menu, stereo HUD, OpenXR controllers driving movement, turning, weapon selection, reloading, crouching, slow-mo, melee and lean by left-hand tilt, plus a visible first-person body and a native VR settings page. Roughly a T3 equivalent on a 2005 D3D9 title. Loads through the official -archcfg module layer, leaving the retail directory unmodified. |
| `re_discovery` | 🟩 full | `SOURCE` | — |
| `source_integration` | 🟨 partial | `SOURCE` | Official SDK used to define native stereo and expose the CRT ABI shipping boundary. |

#### FEAR2VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `AUTHOR` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟩 full | `SOURCE` | harvested into ch06 agent-failure section: passing a sequence number into a pose history rather than the pose itself caused camera judder; the four-question data-path trace that found it |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟧 skimmed | `AUTHOR` | world-space HUD claimed; not yet released |
| `hands_interaction` | 🟨 partial | `AUTHOR` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟩 full | `SOURCE` | harvested 2026-08-28 into ch06: 32-bit target without LARGE_ADDRESS_AWARE exhausts ~2 GB once the VR mod loads, presenting as misleading crashes in unrelated subsystems; LAA-enabled copy started suspended with entry-point stub restoring process-visible identity before DRM validation, verified before continuing |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### ForerunnerVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | Runtime is OPENVR, not OpenXR. src/common/vr/IVR.h is the seam (112 lines): EarlyInit / Init(device,context) / Shutdown / Update(dt) / SubmitEye(eye, texture, VR_Bounds sub-rect defaulting to full) / EndFrame. Split early/late init matches an injected mod's real lifecycle; the bounds sub-rect makes side-by-side and per-eye targets one call. Emulated backend 544 lines vs real OpenVR 570 - the measured price of a headset substitute when the seam already exists. Payload is per-title (delta = Halo 2) with a blam/ subtree mirroring the original codebase structure. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟧 skimmed | `SOURCE` | A Debug Emu build config swaps the VR backend for an emulated one drawing to a separate window - the cheapest of the three headset substitutes found in this batch (see TEST-001). |
| `re_discovery` | 🟨 partial | `SOURCE` | Per-title modules for a multi-engine container; launcher+payload split handles anti-cheat-disabled launch and injection. Style rule: mirror the original codebase's own symbol/file names in a per-title blam/ directory. |
| `source_integration` | — no entry — | — | — |

#### FRIK 78.2 53464 v0.78.2 2026-08-17T16-42Z 86DAb33jN

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | 🟥 not reviewed | `—` | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | REGISTERED NOT REVIEWED 2026-09-05. FRIK - the Fallout 4 VR body and holster mod, VRIK's counterpart. Distribution is binary (F4SE plugin plus meshes/materials, 73 MB); the SOURCE is upstream on GitHub and the runtime config lives in Documents\My Games\Fallout4VR\FRIK_Config, so neither is in this tree. Only README.txt has been read. |
| `input_locomotion` | 🟥 not reviewed | `—` | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | — no entry — | — | — |

#### FUS

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | REGISTERED NOT REVIEWED 2026-09-05. A Wabbajack modlist/preset rather than a mod: README, images, a bundled openvr_api.dll and a Mantella folder. Kept as a source only because it names a working VR mod stack. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | 🟥 not reviewed | `—` | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | 🟥 not reviewed | `—` | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | — no entry — | — | — |

#### gmcl_openvr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟧 skimmed | `SOURCE` | NEGATIVE: its stereo is mono duplicated - no GetEyeToHeadTransform anywhere, both eyes from one origin. A 4-arg max() with no NOMINMAX compiles as warning C4002 and silently builds the frustum from the left eye only. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | 🟨 partial | `SOURCE` | D3D9Ex -> D3D11 SurfaceQueue bridge with five constraints: Ex-device requirement, format whitelist including sRGB collapse, SetPrivateData handle hack, 16x16 staging-Lock sync. Directly relevant to DishonoredVR's D3D9 interop lane. |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | 🟨 partial | `SOURCE` | Script-armed capture latch: arm a bool from Lua, catch the next CreateTexture. Throwaway device on a hidden window of class BUTTON, vtable slots 17 (Present) / 23 (CreateTexture). |
| `source_integration` | — no entry — | — | — |

#### goldeneye-omniport

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟧 skimmed | `SOURCE` | Fast3D display lists interpreted on the CPU into OpenGL; audio microcode interpreted on the host |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | struct-layout guards against the console ABI every build, a 483-check self test, and a scripted input regression replaying a full solo run of Dam with no human, driven by GE007_* environment variables |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟩 full | `SOURCE` | harvested 2026-08-28 into ch18 + TEST-005: staged decomp -> desktop -> Android -> VR; host-only changes guarded with #ifndef TARGET_N64 so the N64 build still byte-matches the retail ROM (sha1 abe01e4a...) after every change - a bit-exact regression oracle |

#### GRAND-alien-isolation

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | BINARY ONLY: XINPUT1_3.dll proxy. Built on Nibre's MotherVR. No source to read. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟨 partial | `STATIC` | grand.ini harvested for CFG-002: a [Debug] block carries one kill switch per risky subsystem (culling, engine-settings override, static smoke, physical throwing) plus OGMotherVRMode to revert to the parent mod's behaviour. Ships both snap and smooth turning; RecenterOnFirstLevelLoad defaults on; HideBody is three-state, not boolean; a named per-effect workaround exists for the game's static smoke. |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### gta-sa-vr-quest

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟧 skimmed | `AUTHOR` | STANDALONE ANDROID VR - a Java loader (com.savr.SavrApplication) plus a native C++ layer (Appearance, Calib, Cheats, Driving) over the Android GTA:SA build. Third standalone-Android target after Aliens-Versus-Predator-VR and goldeneye-omniport. Shipped as a 'source kit' at v0.1.1 alpha with build/install batch scripts rather than a binary release. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟧 skimmed | `AUTHOR` | BUILD_AND_INSTALL / EXPORT_PLAY_APKS / RESET_VR_SETTINGS scripts for both Windows and Linux |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### GTA-VRV-Patcher

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟩 full | `SOURCE` | CAM-006 harvested: re-trigger a mod's unreachable init through a benign engine event (SET_PLAYER_MODEL to the same model), then restore everything it disturbed - 12 component and 8 prop variations, restored after IS_PED_FALLING ends. Same handler covers death and arrest. Not a VR mod itself: a compat shim for RealVR.asi. |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### GTFO_VR_Plugin

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | 🟨 partial | `SOURCE` | — |
| `ui_hud` | 🟧 skimmed | `SOURCE` | — |
| `hands_interaction` | 🟩 full | `SOURCE` | VelocityTracker harvested into the three-way melee synthesis (ch02 #motion-gestures, HAND-004): pose history queued over a 50 ms window rather than a single-frame delta, tracking BOTH positional and angular velocity (Quaternion.Angle/deltaTime, degrees) - a flick is high-angular/low-positional, a thrust the reverse. |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### Halo-MCC-VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟨 partial | `AUTHOR` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | 🟨 partial | `AUTHOR` | — |
| `performance` | 🟩 full | `LIVE` | harvested 2026-08-25 into ch19 xr-frame-pacing: Begin-vs-Wait stall localisation, wait-ahead ordering (PERF-003), aggregate-vs-edge-row refutation, app cadence vs panel rate, rejected-code disposal |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟩 full | `AUTHOR` | — |
| `re_discovery` | 🟨 partial | `AUTHOR` | — |
| `source_integration` | — no entry — | — | — |

#### Heisenberg - Physical Interactions 99105 0.8.6 2026-08-02T10-39Z Q8oKHMMng

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | 🟥 not reviewed | `—` | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟨 partial | `SOURCE` | harvested 2026-09-05 into ch02 #holsters-and-grab and HAND-012/013, from its 906-line annotated F4SE/Plugins/Heisenberg_F4VR.ini (25 sections). Taken: the DYNAMIC motor-driven held body (credited in its own comments as 'HIGGS-style', object stays dynamic, never keyframed while the motor is active), grip tau ramping 0.10 -> 0.65 over 0.30 s so a grab does not snap, soft 6-DOF limits capping 40 units of stretch and 90 degrees of twist to stop runaway, storage zones with an IN-HEADSET config mode, activators with a two-radius design (25 cm pointing pose, 8 cm activation), SmartGrab context retrieval that pulls ammo when the magazine is below 30%, and seated-mode detection from HMD height under 110 units with extended reach. The plugin itself is binary. |
| `input_locomotion` | 🟥 not reviewed | `—` | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | — no entry — | — | — |

#### HIGGS 1.10.10-43930-1-10-10-1768263289

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | REGISTERED NOT REVIEWED 2026-09-05. HIGGS - Hand Interaction and Gravity Gloves. The reference implementation of physical grabbing in a shipped VR title: grab, throw, two-handed hold, weapon interaction. Carries a Source/ tree. Read 2026-09-05: higgs_vr.ini (593 settings) and the Papyrus API. The C++ core is binary. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | 🟥 not reviewed | `—` | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | 🟥 not reviewed | `—` | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | — no entry — | — | — |

#### IRON-NEST-VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | BINARY ONLY: managed code driving OpenXR and D3D11 directly via Silk.NET rather than through Unity XR. No source. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟧 skimmed | `AUTHOR` | IL2CPP Unity requiring BepInEx 6 (NOT BepInEx 5/Mono) - the loader generation is a hard target property. Ships its own openxr_loader.dll beside the game exe, the third project in this batch to do so. Supports VR/flatscreen CROSSPLAY multiplayer - second multiplayer-VR data point after RepoXR (NET-001). |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### JKXR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | command-buffer replay read; rest of 780k lines unread |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟨 partial | `SOURCE` | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | 🟨 partial | `SOURCE` | — |
| `performance` | 🟩 full | `SOURCE` | harvested 2026-08-25 into ch19 mobile-extension-negotiation: optional-extension negotiation, xrPerfSettingsSetPerformanceLevelEXT CPU/GPU domains, xrSetAndroidApplicationThreadKHR with vendor gate, PERF_SETTINGS thermal events, vendor foveation via XR_PICO_CONFIGS_EXT |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | 🟨 partial | `SOURCE` | Command-buffer stereo replay and input ownership sampled; full source-port frame/render architecture remains unread. |

#### KSA_XR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | FIRST Vulkan target in the ledger. Proof of concept runs THREE complete game frames per displayed frame (desktop + two eyes), copying each eye out of the main viewport offscreen colour image - the same architecture BioshockVR reached independently, with the same next problem. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | 🟩 full | `SOURCE` | Vulkan submit lifecycle is atomic: acquire, command recording, queue submission, semaphore/fence transitions and presentation are one unit, and partial skips produced NotReady, freezes and VK_ERROR_DEVICE_LOST. Harvested to ch10 #vulkan-submit-lifecycle and FAIL-RND-001. |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟨 partial | `SOURCE` | KSA_XR calls its desktop-plus-two-eyes complete-frame proof knowingly inefficient. Its independent Vulkan result corroborates BN-PERF-001: once stereo is correct, make the desktop mirror a copy instead of a third world render. |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | 🟧 skimmed | `SOURCE` | BRUTAL framework is a thin C# layer over Vulkan/GLFW/ImGui with no engine abstraction to hook; target is pre-alpha and its API moves. |
| `source_integration` | — no entry — | — | — |

#### l4d2vr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟨 partial | `SOURCE` | Roomscale triple: m_CameraAnchor + forwardmove fed from Dot2D + wall-clip trace + runaway reset past 150 units. Dot-product test detects the engine taking control. |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟨 partial | `SOURCE` | UI drawn last into an opaque target has no usable alpha: ClearBuffers(false,true,true) -> original push -> OverrideAlphaWriteEnable + ClearColor4ub(0,0,0,0) + ClearBuffers(true,false), unwound on Pop. |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟧 skimmed | `AUTHOR` | Kills the threaded renderer (mat_queue_mode 0); README names the resulting CPU underutilisation as a known problem. |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | 🟨 partial | `SOURCE` | OPENS THE SOURCE-ENGINE GAP - the ledger had no Source entry. Call-order fingerprinting to identify an unnamed render pass; usercmd bit-stuffing into sign bits and digit-packed fields with the MANDATORY CVerifiedUserCmd::m_crc repair (symptom of missing it was desynced gunshot audio, not a disconnect). |

#### Luke-Ross-REAL-mods

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟧 skimmed | `STATIC` | STATIC harvest done (ch08 #host-settings-policy): one binary reading per-game data overrides at RealRepo/<GAMECODE>/settings/. CP2077 option.replace forces aim assist, additive camera movement, sway, motion blur, DoF, film grain, chromatic aberration and lens flares OFF while KEEPING anisotropy 16, TextureQuality High and ContactShadows on. HZD graphicsconfig.ini sets a SQUARE 2700x2700 at AspectRatio 1:1 with UpscaleMethod Off - independent corroboration of the square-backbuffer finding in chapter 13, different author and engine. MDE1/1st_person/tables.sds ships a replacement data table to enable the game's OWN first-person mode instead of hooking the camera. dbghelp.dll is the proxy vector. Distribution is .rar archives; no source. |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### Main Wabbajack 20.0 96013 20 2026-08-28T01-06Z bnEVTOJ7D

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | 🟥 not reviewed | `—` | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | REGISTERED NOT REVIEWED 2026-09-05. A single 694 MB Wabbajack modlist archive, not a mod. Kept as a source only because it names a working Fallout 4 VR stack. |
| `input_locomotion` | 🟥 not reviewed | `—` | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | — no entry — | — | — |

#### manhunt-2003-vr-modding-notes

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟧 skimmed | `AUTHOR` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟩 full | `SOURCE` | harvested 2026-08-29 into ch07 #dead-drm-sabotage and FAIL-PACK-006: a STRIPPED SecuROM leaves 16 tripwires whose call sites now reach the REAL Windows APIs (GetVersion, GetCurrentThread, GetLastError), which can never return the magic values the checks expect - and on failure the game writes a poison value into its own state and carries on, so damage surfaces later as ordinary-looking bugs. Fires on every copy, every launch, permanently. Also: the three-way self-exclusion before blaming the game, and dumping the unpacked image once so the whole investigation runs offline. |
| `re_discovery` | 🟨 partial | `SOURCE` | the exe is packed at rest and a debugger cannot attach; the memory dump of the unpacked image is what made static analysis possible |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### MELE-VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `STATIC` | Zips extracted. Ships FOUR runtime-selectable modes (2=Stereo 1=AER 3=DIBR 0=Mono) - independent corroboration of STR-006 including a depth-reprojection fallback. Stereo uses a near-square per-eye target. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | HDR must be off or the headset image is blue/doubled (FAIL-STR-012). Binary only - no source. |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟨 partial | `STATIC` | CFG-001 (installer writes the mod's per-mode resolution AND the game's GamerSettings.ini together, because a mode switch re-asserts resolution) and CFG-002 (short config, tuned defaults baked in, expands on first save; F1-F4 profile hotkeys chosen to avoid Mass Effect's 1-4 weapon keys). Delivery is a dxgi.dll proxy plus its own openxr_loader.dll. Three separate builds for ME1/2/3. |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### mirrors-edge-vr-mod

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟧 skimmed | `AUTHOR` | d3d9.dll proxy forwarding every export, stereo to OpenXR with 6-DOF head tracking. PRE-ALPHA and honest about it: HUD broken in VR, tested on very few machines, expect crashes. UE3.536 sits alongside singularity-vr-mod (UE3.584) and DishonoredVR as a third UE3-era D3D9 witness. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | 🟩 full | `SOURCE` | 2026-08-29, harvested into ch03 #gated-mechanic from ARM_SWING_LOCOMOTION.md (22,404 samples). Arm-swing locomotion against a GATED mechanic: InputMaxSprintRaduisLimit = 0.7 needs near-full deflection in both radius and forward height AND an energy accumulator that decays over three seconds, so an envelope sagging to 0.6 at each swing reversal drops SprintRequested twice a second and the player is capped at a jog permanently however hard they swing. A gated mechanic cares about the MINIMUM of the signal, not the peak. A linear deadband-to-full map is also ruled out - it puts a jog-cadence swing at ~0.55, under the gate. And the units differ: the game's limits are in POST-DEADZONE units, so a 0.7 limit is 0.784 raw against a measured 0.280 dead band. |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟧 skimmed | `AUTHOR` | three files into one folder, no installer and no game file modified - but REQUIRES Virtual Desktop; SteamVR and Meta Link are stated as unable to run it, which is a constraint worth understanding rather than accepting |
| `re_discovery` | 🟩 full | `SOURCE` | 2026-08-29 deep read - badly under-rated on the first pass as 'pre-alpha'. ENGINE_NOTES and FEASIBILITY follow the same shape as singularity-vr-mod and produced three engine traps plus a correction to the DRM procedure. (1) ch10 #validate-every-upload: c0 carries MORE THAN ONE MATRIX - the derived FOV alternates between the scene view-projection and a 160x160 deg shadow or light transform on consecutive uploads to the SAME register, and injecting into it corrupts that pass INVISIBLY, with the symptom appearing elsewhere. 'The register says where to look. It is never permission to modify.' Gated by the clip.w test on every write - four multiply-adds against a cached camera position - at 220,000 accepted against 91 rejected, which is why a one-shot validation would have passed. (2) ch11 #pointer-not-identity: Direct3DCreate9 is called TWICE per run and in one run returned the SAME address both times, because the first object was released before the second was created and the allocator reused the slot. (3) ch09 #typeless-swapchain: OpenXR returns DXGI format 90 (B8G8R8A8_TYPELESS) for a requested 91, so CreateRenderTargetView with a null description FAILS - a typeless format cannot be a view format. (4) ch11 entropy triage, the OPPOSITE outcome to Singularity: .text is 6.480 on both Steam and GOG and the sections are BYTE-IDENTICAL by SHA-256, so the older SteamStub variant only wraps the entry point - static analysis can target the Steam binary directly. |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### MonsterDeadWood-BF3VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `AUTHOR` | Two-Key native same-Present scheduling is author-reported; exact L/R output ownership remains separate. The proven delivered fallback is center color+depth reprojection, with disocclusion visually falsifying it as final stereo. |
| `xr_lifecycle` | 🟨 partial | `AUTHOR` | x86 game to x64 OpenXR GPU transport and Quest delivery are documented but not independently replayed. |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟨 partial | `AUTHOR` | Distinct L/R states or images do not prove physical stereo; acceptance requires disparity that varies with inverse depth. |
| `render_hazards` | 🟩 full | `AUTHOR` | Harvested into STR-004 and FAIL-STR-045: one logical resource may contain LEFT then RIGHT serially, so COM pointer identity is not image identity; semantic phase/role and generation decide. |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | Research-integrity and document-integrity gates are present; the research-integrity selftest currently rejects one unreviewed checker blob. |
| `re_discovery` | 🟨 partial | `AUTHOR` | Existing result payloads are treated as evidence to recover before creating replacement experiments. |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### MonsterDeadWood-C2VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | Harvested into STR-002 and FAIL-STR-044: source publishes pair metadata while owning both keyed mutexes, barriers before release, and forbids old pixels plus new pose/FOV. Runtime acceptance figures remain AUTHOR. |
| `xr_lifecycle` | 🟨 partial | `AUTHOR` | Startup/session-reentry rendezvous: missing first contract must WAIT/no-submit and retry, not latch a global fault. Harvested into STR-002 and FAIL-XR-023. |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟨 partial | `AUTHOR` | Complete cached pair retains its original render pose/FOV/contract; pose freshness cannot relabel older pixels. |
| `render_hazards` | 🟨 partial | `AUTHOR` | Serial/contract sandwich around both copies and one-fresh/one-stale rejection are documented; result artifacts were not independently replayed. |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟨 partial | `AUTHOR` | Bounded-wait history and pose-age telemetry separate producer cadence misses from coherence failures. |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | Finalist integrity scripts and package manifests are present. |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### MonsterDeadWood-DiRT2VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `AUTHOR` | Same-frame L/R render path and submitted-buffer oracle are documented. The oracle separates mono, normal, swapped and exaggerated phases using the exact submitted buffers. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟩 full | `AUTHOR` | A 400-byte VS-slot-3 camera buffer is traced backward from the first consuming draw; projection metadata follows live P00/P11/P8/P9 rather than a fixed host FOV. |
| `render_hazards` | 🟨 partial | `AUTHOR` | Clone substitution leaves the original game buffer untouched and ranks active bind ordinals instead of assuming a fixed count. |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | Research-integrity tooling is present; its selftest currently rejects one unreviewed checker blob. |
| `re_discovery` | 🟩 full | `AUTHOR` | Harvested into RE-005 and FAIL-RE-022: x86 execution breakpoints require EFLAGS.RF before resume; DR6 clearing alone retriggers. Also contributes consumer-to-caller stack ranking. |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### MonsterDeadWood-FC2VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `AUTHOR` | AUTHOR runtime record: same-frame D3D9 stereo and 400 completed pairs. Harvested only as prior art; not replayed independently. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟨 partial | `AUTHOR` | Build-specific culling seam and sphere center/radius layout are documented against GOG Dunia.dll SHA256 7B82...; the in-house UPLAY/Steam bytes differ, so addresses are leads only. |
| `render_hazards` | 🟨 partial | `AUTHOR` | Side planes 2-5 versus depth planes 0-1 support a side-only binocular-union candidate. An intrusive force-pass changed the call denominator, establishing the observer-before-intervention rule. |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | Hash-locked golden baseline, byte-identical rebuild check and one-click experiment packaging are present in source. |
| `re_discovery` | 🟨 partial | `AUTHOR` | Useful culling dataflow and exact-build receipts; no address or ABI was promoted across builds. |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### MonsterDeadWood-TimeShiftVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `AUTHOR` | Author reports proven same-frame D3D9-to-x64-OpenXR stereo. Runtime counters were not independently replayed. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | 🟩 full | `AUTHOR` | Harvested into STR-004 and FAIL-TEST-016: per-shader last-texture replay aliases unrelated state; draw ordinal plus primitive/geometry/VS/PS signature is safer. An exact D16 bind replay executed yet did not restore visible shadows. |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟨 partial | `AUTHOR` | Controlled ten-mode replay sweep preserved the baseline and showed further widening of the same replay algorithm was low-information duplicate research. |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | Research-integrity tooling is present; its selftest currently rejects one unreviewed checker blob. |
| `re_discovery` | 🟩 full | `AUTHOR` | Registry/string/RTTI candidates remain candidates until a runtime method shows direct D3D9 COM activity; structural proximity is not ownership. |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### MyFriendlyNeighborhoodVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟧 skimmed | `AUTHOR` | AI-authored disclosure recorded; source unread |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### novr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟧 skimmed | `SOURCE` | Rework of Raicuparta's UUVR. Ships BOTH OpenVR and OpenXR backends behind Unity's own XR Management plugin abstraction, plus a patcher, an SFX installer and a GUI installer. Low novelty beyond that - the dual-backend comes from the engine, not the mod. |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### openmw-vr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | stereomanager.hpp read (components/vr and mwvr implementations still unread): the keystone is UpdateViewCallback::updateView(View& left, View& right) - the ENGINE owns stereo and asks an abstract supplier for two views, which is exactly why the layer is upstreamable. Multiview negotiated via GL_OVR_Multiview if supported. Ships CustomViewCallback, a fourth headset substitute costing one class. components/vr, components/xr and mwvr implementations still unread. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟨 partial | `STATIC` | SRC-002 harvested and VERIFIED against upstream: components/stereo IS in origin/master while components/vr and components/xr are fork-only, and the VR maintainer is the majority author of the upstreamed layer. Factoring the VR-independent half upstream shrinks the permanently-diverging fork. |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | 🟧 skimmed | `SOURCE` | Delta vs upstream merge-base measured, code not yet read: 370 files changed, 154 added / 216 modified. New VR code concentrates in components/vr (31), components/xr (26) and apps/openmw/mwvr, but 146 changed files sit in apps/openmw and the engine is touched in components/sceneutil, myguiplatform, bsa and stereo. Note components/stereo is a SEPARATE engine-level concern from components/vr. |

#### Outlast-Vr-Mod

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟧 skimmed | `AUTHOR` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟧 skimmed | `AUTHOR` | the deployment story is the notable part: a DROP-IN release with 'no injector, no build tools, no extra launcher' - extract into the game folder, the Binaries folder merges, VR starts automatically on a normal Steam launch. Warns to close other VR injectors and mod loaders, which is the dxgi/d3d9 single-owner contention again. |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### payday2-vr-improvements

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟨 partial | `SOURCE` | The batch's ONLY witness for modding an OFFICIAL VR mode. Deliberately holds the camera one frame BEHIND to match the engine's transform-application latency, explicitly never touching hmd_rotation() - the delay half of CAM-007. |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟧 skimmed | `AUTHOR` | CAVEATS: only an original Vive is actually tested, so every other mapping is AUTHOR-grade. menus/defaults.lua uses dest[name] = override or val, so a per-HMD default can never override a truthy default with false. |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### perfect_dark_VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | docs/vr-projection-fix fully harvested: the physical-vs-stick discriminator (FAIL-STR-009), the four simultaneous projection faults, and the symmetric-base + per-eye-centre decomposition (STR-007). |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | 🟨 partial | `SOURCE` | VR shader prelude (~3.2 KiB) overflowed an unchecked 4 KiB generated-shader buffer (FAIL-STR-011). |
| `ui_hud` | 🟨 partial | `SOURCE` | Vertical asymmetry must not reach clip-space UI; Quest 3 vertical centre -0.193 moved menus ~19% of clip space (FAIL-STR-010). |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | 🟨 partial | `SOURCE` | Implements VR inside Fast3D - the same seam Shipwright-VR used. Dual-target PCVR + Quest standalone from one tree. src/ beyond port/vr and port/fast3d not read. |

#### PLANCK 0.8.1 66025 0.8.1 2026-07-30T03-35Z 4t2yDcbYt

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | REGISTERED NOT REVIEWED 2026-09-05. PLANCK - Physical Animation and Character Kinetics. Read 2026-09-05 (activeragdoll.ini, 758 settings, plus the Papyrus API) -> ch02 #physics-bodies, ch03 #roomspace-velocity, HAND-015, INPUT-010. Taken: yankRequiredHandSpeedRoomspace, which names the axis that stops player locomotion from satisfying a hand-speed gate - the most transferable finding here. Checked against SS2VR manualReload rather than assumed: that code is already immune, because every quantity in it is a difference between two tracked hands, which cancels locomotion, turning and the play-space origin at once. INPUT-010 now ranks that formulation above room space; blend rather than swap between animation and physics, with separate blends for entering, leaving, getting up and recomputing world-from-model, and constraint parameters per PHASE; clamped bone velocities plus two chosen degradation paths for when physics cannot win (warp back beyond a distance, phase through with an alpha fade beyond an intersection depth, larger in combat); active ragdoll as a distance-gated LOD; cooldowns on every physical event because contact is continuous; THREE separate ignore lists (general, aggression, ragdoll collision) rather than one; and a consequence model - accumulated aggression with three thresholds and dialogue, stamina cost, speed reduction by race size, and intent inferred from aggressionRequiredHandWithinHmdConeHalfAngle so brushing past someone while looking away is not an assault. The C++ core is binary. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | 🟥 not reviewed | `—` | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | 🟥 not reviewed | `—` | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | — no entry — | — | — |

#### portal2vr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | 🟧 skimmed | `SOURCE` | FORK OF l4d2vr - tree is literally portal2vr/L4D2VR/vr.cpp, identical formulas, comments and submodules. NOT an independent witness; harvest as a DIFF only. Its diff: sentinel-byte (-2) plus Tell()/Seek() rollback usercmd extension, wasTrue nest-safe EyeAngles bracketing, and a third full RenderView for the desktop mirror. |

#### prince-of-persia-2008-vr-external-research

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | StarForce recorded as 'likely present, not confirmed' with the resolution route named - research discipline worth copying: reports the honest gap (no vorpX precedent, unlike two sibling projects) rather than padding |
| `re_discovery` | 🟩 full | `SOURCE` | harvested 2026-08-29 into ch11 #stereo-fix-prior-art: a TWICE-ITERATED HelixMod 3D Vision fix is stronger prior art than one, and the second fix existing proves the first's shader matching was too blunt for this binary (blanket-match vs shader/texture pairs). Its known-issues list is a starter pass inventory (skybox depth, doubled lens/sun flare, flat UI). Two specifics worth a session each: SEPARATE CONVERGENCE PRESETS FOR CUTSCENES VS GAMEPLAY (evidence of two camera paths, not one), and skybox correction for BOTH dark and sunny weather variants. Also: DRM profile differs per distribution channel - PoP 2008's retail boxed release was deliberately DRM-free while digital versions were not. |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### psychonauts-vr-dev-archive

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟩 full | `SOURCE` | 2026-08-29, harvested into ch19 #blocking-wait-floor and PERF-006 - the first FULL performance review in the ledger. Per-span QueryPerformanceCounter timing overturned three sessions of assumption: GetRenderTargetData costs 0.003-0.015 ms and the whole readback chain 0.35-0.45 ms per eye, while IVRCompositor::WaitGetPoses costs 25-27 ms EVERY call - and an A/B that skips it restores framerate but breaks every Submit with VRCompositorError_DoNotHaveFocus (101), so it is a required floor, not a defect. Two textbook architecture fixes measured ~zero effect and were published as a negative result. Two measurement bugs found: moving the game window off-screen triggers Windows DWM occlusion throttling that caps Present at ~30 fps REGARDLESS of VR state (caught only by running the bridge-OFF control through the same convention), and a per-Present frame counter counts EYES not frames, inflating three sessions of absolute figures ~2x - the relative 2x regression survived because the artifact applied to both sides. |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟧 skimmed | `SOURCE` | opt-in IAT patch PSYVR_SUPPRESS_AUTOPAUSE makes the game's own GetForegroundWindow return its own handle, fixing a per-tick auto-pause poll that had blocked live testing |
| `re_discovery` | 🟨 partial | `SOURCE` | companion archive to psychonauts-vr-modding-notes: raw recon, probes and dead ends kept separately from the readable ledger - the dev-archive role in the six-repo topology harvested into ch18 #repo-topology |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### psychonauts-vr-modding-notes

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | shader-constant stereo hook; gameplay stereo working milestone recorded at notes/23 |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟩 full | `SOURCE` | 2026-08-29, harvested into ch03 #clamped-view-second-mechanism and INPUT-006. Free-look is an ABSOLUTE CLAMPED OFFSET, not a rotation rate - held at maximum for 12 s the camera sat at -82.2 deg byte-identical - and is hard-clamped at ~87 deg. BODY FACING drives the same camera unclamped: 317.7 deg total excursion through the wrap. Five attempts to lift the clamp failed before anyone asked whether it needed beating. The catch is that body facing is COUPLED TO LOCOMOTION (blocked movement froze yaw at 168.0 across seven steps), and the fix is to PULSE: 8 x 90 ms taps gave 60.2 deg per 100 units travelled against 7.7 for one 720 ms hold, about 7.8x. Also ch03 #input-synthesis-layer: four sessions forging DirectInput buffer contents delivered state that did nothing, because the engine's edge detection keys off the REAL input stack - plain SendInput with KEYEVENTF_SCANCODE worked first try. |
| `camera_tracking` | 🟩 full | `SOURCE` | 60+ numbered sessions; head-follow camera wired 2026-08-28 |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟧 skimmed | `SOURCE` | dialogue navigation and UI depth, 2026-08-27 |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟩 full | `SOURCE` | harvested 2026-08-29 into ch11 #derived-output and RE-006: three camera matrices (+0x20/+0x50/+0x90) accept a write, hold it all frame and change nothing - they are DERIVED OUTPUTS nothing reads; the real input is at +0x150 and culling follows it. 'Wrong field, not wrong timing.' The earlier dump misled because it sampled BEFORE the write in both runs. Also: write absolute from a snapshot because the engine does not refresh a stationary camera (a 15-degree hold became a spin, c0.z 0.5160 -> 0.1235 in 1.5 s); rotate all four columns (c2/c3 are a matched pair); the translation row must follow, or error GROWS WITH ANGLE - clean at 2-5 deg, wrecked at 15+. Columns carry projection scale (\|c1\|/\|c0\| = 1.334 = 4:3), so the basis is not orthonormal. |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### Quake2Quest

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | REVIEWED 2026-09-02. Team Beef (drbeef), built on Yamagi Quake II, uses OpenXR, active (2026-06-16). VR code is ISOLATED at Projects/Android/jni/Quake2VR - no diff needed. Same author as JKXR, so likely shares its house style. Yamagi keeps the renderer split (refresh/gl1,gl3,soft + ref_shared.h), so id's ref_gl/ref_soft seam survives to 2026. Android/Quest, so the platform layer does not transfer to a Win32 injection; the engine integration does. |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### quake2vr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | REVIEWED 2026-09-02. dghost/quake2vr, archived 2021. Full Q2 VR source port on KMQuake II + RiftQuake, libOVR 0.2.5 (pre-OpenXR). Stated features map onto playbook lanes: projected HUD/2D UI, decoupled view and aiming. Diff baseline is KMQuake II, NOT id's tree - diffing against id-Software/Quake-2 mixes decades of non-VR modernisation. |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### ravenfield-vr-mod

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟧 skimmed | `SOURCE` | 10 code files (VRCameraManager, VRControllers, VRCanvasHelper, Patches). Value is as a minimal complete OpenVR/Unity example, not as a source of new technique. Nothing harvested. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### Rea-Virtua-Cop-2-VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟩 full | `SOURCE` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟨 partial | `SOURCE` | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | 🟨 partial | `SOURCE` | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | 🟩 full | `SOURCE` | — |
| `source_integration` | — no entry — | — | — |

#### ReclaimerVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | NOT HARVESTABLE: the checkout contains a README and nothing else. Third Halo MCC entry by name only. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### REFramework

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | REGISTERED NOT REVIEWED 2026-09-04. praydog REFramework, full source (139 MB, upstream github.com/praydog/REFramework). This is THE framework that supplies VR to RE Engine titles and the direct upstream of Talemann-RE4 - which is why it arrived. Nothing in it has been read yet; it is registered so an empty search result cannot read as absence. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | 🟥 not reviewed | `—` | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | 🟥 not reviewed | `—` | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### RepoXR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | Source/Rendering read: comfort vignette implemented as a native Unity PostProcessEffectSettings at PostProcessEvent.AfterStack inside the GAME'S OWN post stack and config-gated, rather than as an overlay quad. Patches/ camera and post-processing files not exhaustively read. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟩 full | `SOURCE` | HAND-002 and HAND-003 harvested: the whole conversion repoints ONE existing accessor (PlayerLocalCamera.GetOverrideTransform) plus PhysGrabber.RayCheck via Harmony transpilers, so hand-origin interaction is a redirect not a rewrite; flat-tuned push/pull rate halved AND converted from fixed to analog; haptics driven from an evaluated curve over the game's own grab-loop AUDIO PITCH, suppressed during scripted holds. VRRig carries a 4-level per-arm transform chain and shoulder-mounted pickup colliders. |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | 🟧 skimmed | `SOURCE` | NET-001 harvested: VR side-channel tunnelled over the game's own Photon transport, tagged with a magic constant and an explicit PROTOCOL_VERSION, RPCs resolved by type/method hashcode. First multiplayer-VR evidence in the ledger. |

#### RoR2VRMod

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | StereoProjectionFix read |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | 🟧 skimmed | `AUTHOR` | — |
| `camera_tracking` | 🟨 partial | `SOURCE` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | 🟧 skimmed | `AUTHOR` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### satisfactory-uevr-enhancements

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟨 partial | `AUTHOR` | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟨 partial | `AUTHOR` | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### Scrap-Mechanic-Native-VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟧 skimmed | `SOURCE` | The batch's only OpenXR-native repo. Uses ReShade addon64 bind_render_targets as a general D3D11 interception substrate. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | 🟨 partial | `SOURCE` | Sacrificial 64x64 burn-in pass for once-per-frame state (SSAO/decals desyncing between eyes). |
| `ui_hud` | 🟨 partial | `SOURCE` | Clear-to-transparent UI separation needing NO engine symbols: clear the live backbuffer to {0,0,0,0} between world and UI passes, capture at Present, un-premultiply. More general than the Source-engine alpha-write approach. |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟨 partial | `SOURCE` | The desktop mirror reuses the finished left eye instead of rendering the world a third time: bind the eye SRV and desktop backbuffer RTV, apply an aspect-crop constant, then Draw(3,0) with no vertex buffer. The live log names the acceptance condition: 'without a third full scene render'. |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### Shipwright-VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | vr_openxr.cpp is compiled XR_USE_GRAPHICS_API_D3D11 and pulls device/context from gfx_direct3d11.cpp via extern accessors - THAT is why the README says OpenGL will not work. In a multi-backend renderer (libultraship), binding the VR layer to one backend silently unsupports the others; a legitimate scope decision that must be stated where users read it. Harvested to ch18 #engine-native-xr. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟨 partial | `SOURCE` | Game pushes the head anchor, VR composes the view; VR_GetCullingFovy exports a binocular cull FOV back into the engine View for culling, audio panning and LOD (FAIL-CAM-006). Roomscale negotiated against collision (CAM-005). |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟨 partial | `SOURCE` | Flat 2D contexts render on a world-locked panel with the last world frame frozen but still head-tracked behind (HUD-003). |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | 🟨 partial | `SOURCE` | vr_interface.h harvested as the worked example of a narrow SRC-04 boundary: one extern C header, ~40 functions, ownership named per call, phases labelled. VR code lives in the libultraship-vr submodule (branch vr-integration), NOT in the main repo - fetched separately. |

#### shock2quest

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟩 full | `SOURCE` | Harvested 2026-08-25 into ch04: world-locking, honest panel basis, shared pointer arbitration, input edges and zero-quaternion guards. |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟩 full | `HEADSET` | Harvested 2026-08-25 into ch19 from the full Quest mission baseline and Oculus profiling workflow. |
| `audio` | 🟩 full | `SOURCE` | Harvested 2026-08-25 into ch20 from engine/src/audio/mod.rs: moving emitters, two-ear listener updates, listener-relative lanes, channel preemption and unit scaling. |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | 🟧 skimmed | `SOURCE` | dark/ crate identified as a format oracle; NOT read |
| `source_integration` | — no entry — | — | — |

#### Silent-Hill-3-VR-Mod

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | 2026-08-29, harvested into ch09 #d3d8-route. The floor case: D3D8 has NO shared surfaces, so the frame leaves the process through system memory - GetBackBuffer (vtable slot 16) -> CopyRects (28) into a SYSTEMMEM surface -> LockRect (9) -> memcpy into a shared section -> SetEvent, consumed by a 64-bit host. The architectural statement is the transferable part: 'nothing here touches OpenXR or D3D11 - the 32 bit game process stays clean and every headset facing call happens in the 64 bit host', which is a better argument for out-of-process than bitness alone. Lifetime: the proxy starts the host itself and passes the game PID so it exits with the game, and the host refuses to run standalone. The modern SDK no longer ships d3d8.h, so interfaces are reached by named vtable slot constants. Proxy is dinput8.dll - a fourth project avoiding the contended graphics DLL. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟨 partial | `AUTHOR` | STANDS ON TWO PRIOR COMMUNITY MODS as hard prerequisites - Silent Hill 3 PC Fix (Steam006) and the SH3 Camera Mod - rather than reimplementing them; a dependency posture worth noting when a game already has mature community fixes |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### sims4-vr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | confirmed it never had real stereo |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | 🟩 full | `SOURCE` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | 🟩 full | `SOURCE` | — |
| `source_integration` | — no entry — | — | — |

#### singularity-vr-mod

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | 2026-08-29 deep read of ENGINE_NOTES. CLOSES the widen-vs-cull problem bfbc2-vr left open, harvested into ch14 #forced-projection and CAM-010. (1) Their projection layer submitted the HEADSET's FOV while the game rendered 65 deg at 16:9 - a uniform stretch, so head movement, world scale and object size were all wrong TOGETHER and nothing could be judged against anything else. (2) Read the frustum OUT OF THE MATRIX rather than asking the engine: column lengths are the projection scales, tan(halfFov) the reciprocal - no need to know whether FOVAngle is horizontal or vertical. (3) Match the headset's VERTICAL FOV: a 16:9 game against a near-square per-eye view already has horizontal surplus. (4) Widening THROUGH the engine widens its culling too. (5) But the engine will not HOLD it - against a steady 127.9 deg the matrix reported 125.3 / 127.2 / ... / 80.7, because the camera update interpolates back each tick with step size set by frame duration. (6) THE FIX: force the frustum in the matrix (rescaling x/y columns IS an FOV change), demote the engine's FOV to culling and ask it for 15% more than you render, and submit the forced constant to OpenXR - a submitted frustum that tracks the engine inherits every wobble. |
| `xr_lifecycle` | 🟩 full | `SOURCE` | 2026-08-29, harvested into ch09 #no-d3d9-binding and #decay-not-freeze. OpenXR has NO D3D9 graphics binding and the game calls Direct3DCreate9 not ...9Ex, so shared-surface interop is unavailable; three ranked routes recorded, with D3D11_RESOURCE_MISC_SHARED_KEYEDMUTEX having no D3D9 counterpart. 'Do not build scaffolding around an unproven pipe' - three independent scoping steps precede writing the mod. Separately: a 6-DOF offset FROZE at 0.9 m permanent displacement because orientation and position do not fail together (IMU carries rotation, position needs cameras) and skipping the update held the last value forever; the fix decays toward neutral when XR_VIEW_STATE_POSITION_VALID_BIT is clear. |
| `xr_input` | 🟩 full | `SOURCE` | 2026-08-29, harvested into ch03 #resting-controller and ch18 #xinput-emulation-traps. A Touch controller SET DOWN reports a sustained partial trigger pull - left 0.34-0.43, right 0.23-0.28, isActive true on all 120 frames - which clears a 0.10 deadzone, reaches the game as LT~97/RT~64 and maps to AIM and FIRE, so the weapon fires by itself and framerate drops from 120 to 98. Nine runs and five buried mechanisms preceded it because the fault was never in the engine's input plumbing. Separately, two silent XInput-emulation traps: the exe imports BY ORDINAL so a name-keyed IAT patch finds nothing and REPORTS SUCCESS (detour the function body instead), and dwPacketNumber must advance only on change - incrementing every call defeats the game's skip-unchanged path, never incrementing makes it ignore you, and both fail quietly. |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟨 partial | `SOURCE` | 2026-08-29: ch04 #silent-glyph-fallback - GlyphIndex returns SPACE for unknown characters, so '*RESTART*' drew as ' RESTART ' and the > / < page markers had been invisible since they shipped. A missing-glyph box is a bug report; a space looks like a design decision. Also ch09 #clip-space-immune: a fullscreen quad already in clip space reads no camera register, so a constant-remap stereo path is a NO-OP on it - both copies land at identical coordinates and each is scissored to its own half. The HUD was always fine because its shader does read the registers being transformed. And a SECOND view-projection at vs c13 was never remapped, surfacing as mis-projected shadows rather than mis-placed geometry. |
| `hands_interaction` | 🟩 full | `HEADSET` | 2026-08-29 HISTORY.md read. Harvested into ch02 #identity-latch: latching onto a runtime-identified mesh needs THREE states, not two - a retry keyed on an EMPTY result cannot detect a latch onto WRONG data, and their menu latch took two non-gun entries, returned true and silenced its own retry ('the report that came back was accurate; the labels on it were fiction'). The fix validates continuously against whether the latched mesh is still drawn, with an EMPTY list counted as neither hit nor miss because cutscenes have no first-person pass. Also ch12 #one-scale-three-users: kMetresToUU = 52.5 is UE3's documented 16 units per foot exactly, and the stereo baseline, the 6-DOF translation and the hand position must all flow through it - scaling IPD alone makes the world resize AS YOU MOVE, the exact complaint a world-scale slider exists to fix. A held object that shifts on recentre is anchored to the engine's eye rather than the player's. |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟩 full | `SOURCE` | 2026-08-29, harvested into ch19 and ch14. THE WAIT IS THE DISCRIMINATOR: their reprojection warning tested frame time against display period and fired on a run with reprojection off, because 60 fps against 120 Hz is 2.00x by definition; the real test is xrWaitFrame - large means the runtime is holding you back, near zero (they measured 0.1-0.9 ms of a 16 ms frame) means you are genuinely busy. An app that is merely slow never idles. Also: the engine issues a D3DQUERYTYPE_OCCLUSION query per primitive and skips the primitive on a LATER frame if it returned zero - a per-view decision applied to both eyes with a frame of latency; overriding GetData to report visible took draws from ~1000 to a peak of 2272-3809 and 'can never wrongly delete geometry, only fail to save work'. |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | harvested into ch18 #uncontended-proxy: XINPUT1_3 proxy rather than d3d9/dxgi, which ReShade, DXVK and Special K all contend for - and because the game already reads XInput, motion controllers compose into an XINPUT_STATE with ZERO engine hooks, so playability arrives before any gameplay RE does. |
| `re_discovery` | 🟩 full | `SOURCE` | 2026-08-29. Major contributor across ch11. UObject property reflection walk (Children +0x4C, Next +0x40, Offset +0x64, FName index +0x2C, SuperField +0x3C) makes any property addressable BY NAME, retiring per-field signature scans - validated by solving against two known answers (Actor.Location +0x54 AND Actor.Rotation +0x60) and then corroborated by a spacing never fitted (SkeletalMeshComponent Translation/Rotation/Scale/Scale3D at UE3's declared sizes). Also: #entropy-triage (.text at exactly 8.000 = encrypted, .rdata plaintext, which is why symbols read but code does not); #drm-free-twin (the GOG copy is the SAME build - identical PE timestamp and section sizes, file-size delta exactly the .bind size - so analyse that and the addresses hold in the Steam process); #probe-point and RE-007 (the w-cancellation test goes vacuous at the origin, and dotFwd against the known facing both rejects false hits and resolves ROW vs COL); #silent-write-two-causes (Translation +50 UU moved the mesh +0.0 - a CACHED consumer, not a derived output, which CORRECTS RE-006 as first written); #field-level-authority (mCurrentPOV.FOV is read, mCurrentPOV.Rotation is a copy - one struct, opposite verdicts, and the real source is AActor::Rotation two levels upstream of four mirrors); #per-probe-tolerance (1 UU at the origin where nothing goes stale, 25 UU for world probes). |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### SkyrimTogetherVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟧 skimmed | `SOURCE` | VRAvatarService represents a VR player to other clients; behaviour/animation-graph sync |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | review protocol worth copying: every evidence item carries [verified: file:line], the reviewer is read-only, and the brief names the acceptable scale of fix up front |
| `re_discovery` | 🟩 full | `SOURCE` | harvested 2026-08-28 into ch06: EntityId and EntityGeneration both derived from the same packed EnTT handle, so slot reuse changes the identity and the generation cannot detect it - a third witness for passing a reference into a mutable table across a boundary |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### SkyrimVR FBT 185070 1.0.3 2026-07-22T11-37Z HZCMOyLlG

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | REGISTERED NOT REVIEWED 2026-09-05. Full-body tracking support (SKSE plugin only, no source in the tree). |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | 🟥 not reviewed | `—` | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | 🟥 not reviewed | `—` | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | — no entry — | — | — |

#### Snowrunner-VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | harvested 2026-08-29 into ch19 #composed-reprojection: AER with two smoothing options where the second is built ON the first. Stale-eye warp brings that eye's own last real render forward, in three escalating modes (headset rotation / plus game-camera rotation / plus 6-DoF by camera translation) and is the DEFAULT for having the fewest artefacts. DIBR shift reprojects the rendered eye into the other using the depth buffer, and its disocclusion hole is filled from the stale-eye warp - two approximations with disjoint failure modes covering each other. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟨 partial | `SOURCE` | no motion vectors available, so camera motion substitutes for per-pixel motion on the grounds that most of the world is static, with dynamic elements (trucks, trailers) explicitly excluded. Stated cost: those objects show the AER offset, so the COCKPIT feels lower-framerate than the world - which in a cockpit game lands on what the player looks at most. |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟧 skimmed | `AUTHOR` | dxgi.dll proxy; nothing patched on disk |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### SonsVR_Mod

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | Mod owns stereo rather than riding Unity XR: two cameras, per-eye RTs, hand-rolled OpenVR submit. Both eye position AND rotation from GetEyeToHeadTransform, never a hardcoded IPD. Argues crop must be a clip-space scale because reducing the runtime matrix to four tangents drops the shear canted displays fold in. |
| `xr_lifecycle` | 🟩 full | `SOURCE` | THE reference frame contract, harvested as XR-005: wait once early, cache, submit from WaitForEndOfFrame after all cameras render, then PostPresentHandoff. Names the cost of each deviation. Five of eleven surveyed mods got this wrong; this one is right. |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | 🟨 partial | `SOURCE` | Two-threshold discipline: 35/55 degree shoulder engage/release plus Latch() with a 0.75x release fraction. |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### SPT-VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟧 skimmed | `AUTHOR` | README only; 33k lines of C# unread |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### Sterallax6DOF-silksong

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | NOT HARVESTABLE without RE: a single DLL, no source, no config, no readme. Retained in the ledger because 6DOF applied to a 2D game is a conversion class with no other example here - worth an RE pass if that class ever matters. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### SubmersedVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | NARROW PULL: produces no stereo, XR lifecycle or perf work; forces Seated and hard-snaps the rig each frame. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟨 partial | `SOURCE` | Laser pointer driving a screen-space cursor, with the world-unit drag-threshold trap and an unfocused-window early-out. |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | 🟨 partial | `SOURCE` | Audio listener must sit on the NON-ROTATING root - second engine witness for a rule the playbook already states, and the fleet audio row is 0-full. |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### SystemReShock-UEVR-Plugin

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | UEVR COMPANION PLUGIN, harvested to ch18 #companion-plugin-scope as the Mode 3 case study. ~2,900 first-party lines (one dllmain.cpp) plus a ~300-line D3D11/12 shim and a GENERATED UObject SDK, against UEVR's ~40,000. Its entire feature list is game semantics - crosshair classes, HUD, body-anchored minimap, hotbar, cyberspace aiming - and none of it is stereo, tracking, projection or submission. Build-specific (no GOG/demo), Defender removes the DLL on profile import, and profile sites carry different versions. Rendering internals and the generated SDK not read in detail. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### Talemann-RE4

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | Not a stereo mod. REFramework supplies VR; this supplies the HANDS. Installed build is RE4VR_2.0_Setup.exe; the mod is ~31k lines of Lua under reframework/autorun plus JSON data under reframework/data/re4_vr. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | 🟥 not reviewed | `—` | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟨 partial | `SOURCE` | harvested 2026-09-04 into ch02 #physical-reload and HAND-008/009/010. THE SHIPPED VERSION of what visceral-re2-vr-mod lists as planned. Physical reload across seven Lua modules (reload, reload2/3, reload4/5_dlc, reload_adv) plus holster, gestures and capacitive touch. Key findings taken: the mag DOCK is a named weapon joint plus a per-WeaponID offset, explicitly because starting at the hand cut the insertion path through the weapon mesh and drifted while walking; insert distance is per weapon CATEGORY with a per-weapon override, never one global; mag drop is two phases, an eased LOCAL slide out of the chamber then a CONTROLLED world fall (free gravity 'flies away'), with floor Y read off the player body root; holster is a Spine_1 joint plus offset and a box zone, with grab_trigger 0.333 below grab_release 0.363 for hysteresis. The per-weapon tables encode a taxonomy far wider than category: top-loaders with a chamber and no magazine (Red9, positive Y/Z and annotated as NOT a sign error), break actions whose slide joint is a pitch lever, rotary cycles whose slide joint turns, weapons the engine closes the slide for, and three distinct representations of a carried shell (static sub-mesh part, spawned entity, mesh clone). Ported from the same author's RE9 mod, so several modules carry their RE9 lineage in comments. |
| `input_locomotion` | 🟥 not reviewed | `—` | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | Inno Setup installer that refuses to run without RE4 present; the user installed it against a renamed stand-in. Ships REFramework Lua/JSON plus upscaler and plugin DLLs beside the game. |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | — no entry — | — | — |

#### TechtonicaVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | 🟧 skimmed | `SOURCE` | MOSTLY SKIP: all VR lives in an unvendored external PiVRLoader NuGet, so the repo contains no stereo, XR lifecycle, projection or perf work. Two rules worth taking without opening it: assert an exact IL substitution count on every Harmony transpiler, and engine XR-subsystem discovery runs BEFORE any plugin can - so the launch that installs VR can never be the launch that enables it. Budget a documented restart. |

#### the-evil-within-vr-external-research

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟩 full | `SOURCE` | 2026-08-29, harvested into ch09 #submit-thread-affinity. IVRCompositor::Submit 'should only be called from the same thread you are rendering on' - the thread owning the D3D11 immediate context - and getting it wrong yields intermittent corruption rather than a clean error. The tidy architecture (a dedicated VR thread) is the forbidden one. Present is an immediate-context operation a deferred context cannot call, so a working Present hook is BY CONSTRUCTION on the right thread. Sharpened by this game's unusual frame structure: six worker threads record command lists on deferred contexts and a seventh replays them, so 'the render thread' names one of seven without care. On native D3D11 the submission itself is trivial - TextureType_DirectX with a live ID3D11Texture2D*, no readback or interop. |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟧 skimmed | `SOURCE` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### thedarkmodvr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟧 skimmed | `INFERENCE` | WGL_NV_DX_interop2 route cited second-hand; source NOT read |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟨 partial | `SOURCE` | Full shipped vr_* vocabulary harvested to ch08 #shipped-settings-vocabulary as a completeness checklist: five independent UI-overlay placement knobs, comfort vignette WITH a corridor variant, ranged-vs-melee aim indicator sizing, disableUITransparency and disableZoomAnimations as flat affordances that turn unpleasant in stereo. |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟨 partial | `SOURCE` | Three-zone radial foveation profile (inner/mid/outer) plus a reconstruction-quality knob, behind vr_useFixedFoveatedRendering. |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | 🟨 partial | `SOURCE` | renderer/vr/VRFoveatedRendering harvested to ch19 #source-side-foveation: TWO foveation routes behind one class - hardware VRS with a PER-EYE lookup image, and a radial density mask punched into depth plus a reconstruction pass for GPUs without VRS. Also vr_useHiddenAreaMesh and vr_useLightScissors: existing flat per-view optimisations made eye-aware rather than replaced. VR call sites in RenderBackend/FrameBufferManager/RenderSystem/tr_render and Player/PlayerView/Physics_Player are NOT yet read. |

#### theHunterCotW-VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟧 skimmed | `AUTHOR` | states native per-eye rendering outright - 'the world is drawn from the game's own camera, once per eye - real depth, your head turns the view, you can lean and step around inside it, and your weapon has depth. Not a screen-in-a-void wrapper.' Targets a specific game update (9.2, Peru Hunting Reserve). DLSS interaction noted in requirements. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟩 full | `SOURCE` | 2026-08-29, harvested into ch02 #scoped-optics and HAND-007 - the best-argued design document in the survey and a topic nothing else here covers. A real telescopic sight has an EXIT PUPIL and only one eye fits in it; in VR there is none, so both eyes see the magnified image from their own position. The reticle, lens disc and mask sit at ZERO disparity while the world is magnified - measured 1.08 -> 2.98 reciprocal tangent, M = 0.9254/0.3360 ~= 2.75x - and world disparity is multiplied by that M while the reticle's stays at 0. The resulting reticle-to-target disparity is 30/12/6/4 arcmin at 20/50/100/150 m against Panum's fusional limit of roughly 6-10 arcmin, so at every playable range one of them doubles. And because the eye offset is a PURE TRANSLATION, a one-eye-centred reticle puts the bullet 32 mm laterally off at ANY range and magnification - a fixed error that never looks like a scaling bug. Decision: while scoped, render BOTH EYES FROM ONE CAMERA (the one the bullet leaves from), behind a default-off switch. Rendering the scope to one eye is rejected as a binocular-rivalry generator (0.5-2 Hz), and blanking the other eye costs binocular summation, lets the covered eye drift to its phoria, and an LCD's black is grey with mura. |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟧 skimmed | `AUTHOR` | single zip dropped in the game folder |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### TwoForksVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟧 skimmed | `STATIC` | Firewatch VR mod, extracted from TwoForksVR-0.0.16.zip. BepInEx/Harmony managed plugin that also ships AssetsTools.NET and classdata.tpk - it REWRITES GAME ASSETS at install time rather than only patching code at runtime. Not yet read. |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### UEVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | Core architecture harvested to ch18 #uevr-fake-stereo and META-006: UEVR IMPLEMENTS Unreal's built-in FFakeStereoRendering stereo device (8,133-line hook) and IXRTrackingSystem rather than bolting a renderer alongside - the engine then drives its own stereo path. Fourth independent instance of an engine-honoured seam. Also harvested: vtable slot identification by function-body fingerprint (xmm usage >= 10 for CalculateStereoViewOffset; 'B0 01' for IsStereoEnabled), E9 thunk unwrapping, exhaustive control-flow decode for obfuscated binaries, and the devirtualisation hazard (HOOK-003). D3D11/D3D12 components, UObjectHook and the Lua API remain unread. PLUGIN-FACING half also harvested, to ch18 #framework-extension-surface and META-008: plain-C ABI (include/uevr/API.h, 648 lines) with C++ ergonomics kept separate (API.hpp 1711, Plugin.hpp 170); semver plugin ABI 2.39.0 handed to the plugin so it can refuse an incompatible host; 24 callbacks as pre/post pairs around engine tick, stereo view offset (THREE - pre/early/post), viewport draw, slate draw, present, device reset and xinput get/set; Unreal reflection exposed to plugins so companions query metadata instead of reverse-engineering it. Plugin.hpp carries its OWN MIT licence so plugin authors do not inherit the framework terms. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### unreal-gold-vr-external-research

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟩 full | `SOURCE` | harvested 2026-08-29 into ch18 #repo-topology: the canonical statement of the six-repository layout with a strict ONE-WAY dependency, so a research-only session can run concurrently with RE/coding work without collision. Research never writes to the other five. The index carries a status lifecycle whose failure state - DEAD END - is kept 'so it isn't re-investigated from scratch', and the CONSUMING side updates the index so the producing side never polls. Seeded 2026-08-24 with no topics yet: structure, not findings. |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | — no entry — | — | — |

#### VirtualFortress2

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟧 skimmed | `SOURCE` | NARROW PULL ONLY - least finished Source implementation. Keep the projection-centre-offset-into-bounds variant. Demonstrable IPD bug: left -(ipd*scale)/2 vs right +(ipd*scale) gives 1.5x separation and a shifted cyclopean centre; the captured left transform is never used. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | 🟧 skimmed | `SOURCE` | Hand-aim breaks server authority - recorded as a failure. Locomotion driven by issuing the console command for forward movement rather than through the input path. |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | 🟧 skimmed | `SOURCE` | MinHooks CreateTexture (vtable slot 23) and coerces the first texture created while armed; throwaway device on a hidden BUTTON-class window, same as gmcl_openvr. |
| `source_integration` | — no entry — | — | — |

#### visceral-re2-vr-mod

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟧 skimmed | `AUTHOR` | an INTERACTION OVERHAUL layered on praydog's REFramework rather than a stereo mod - the framework supplies VR, this supplies the hands. Planned: motion-controller weapon handling, manual reloads, hand-pose slide racking and pump action, holsters, body IK and posture. v0.1.0 ships the FIRST SLICE ONLY (body and posture): torso straightening, feet planted while aiming, cutscene/grab safety. Weapon handling, reloads and holsters still to come. |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟧 skimmed | `SOURCE` | companion to an existing VR framework - the vehicle class that lets a mod start at interaction instead of at stereo |

#### Vostok-VR-Mod

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | 196 lines total. XRInitializer activates GODOT'S OWN XRInterface/OpenXR rather than implementing XR - activate_openxr() returns a four-value Result (SUCCESS/NO_INTERFACE/INIT_FAILED/ALREADY_ACTIVE) and apply_settings takes render_scale/refresh_rate/foveation. Harvested to ch18 #engine-native-xr: when the engine has first-class XR, the mod is activation plus configuration, ~200 lines against ~5,300 for a substitute runtime. |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟨 partial | `SOURCE` | FIRST Godot target. Bootstrap hooks GetCommandLineW (guarded by call_once) to make Godot load a GDExtension - injection exists only to get the extension registered, after which VR runs as engine-sanctioned native code. Harvested to ch18 #engine-sanctioned-loading. Vehicle recorded as native-injector but the taxonomy fits poorly. |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### VRIK Player Avatar 23416 0.8.6 2026-07-12T13-00Z Yj6wQRIkO

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | REGISTERED NOT REVIEWED 2026-09-05. VRIK Player Avatar. Full-body IK avatar and, more importantly here, the mod that established the BODY-ANCHORED HOLSTER paradigm most VR mods now copy - which ch02's holster guidance and RE4VR's Spine_1 anchoring both descend from. Ships Scripts/, meshes/, an .esp. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | 🟥 not reviewed | `—` | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟨 partial | `SOURCE` | harvested 2026-09-05 into ch02 #holsters-and-grab and HAND-013, from SKSE/Plugins/vrikslots.ini. The canonical holster data model: FOURTEEN anatomical slots (hips, thighs, calves, upper arms, forearms, shoulders, stomach, chest), each carrying a pose (posX/Y/Z plus rotA..rotI, a raw 3x3 matrix written by the in-game calibration UI), a hand assignment that is CROSS-BODY by default (left hip is right-hand-only), and a six-way accept-list (small/medium/large/ranged/shield/torch). Also taken: activation/release hysteresis via slotChangeDistanceMultiplier 1.75, hover spheres gated to sheathed-but-not-combat, per-slot hover haptics with an enable-when-EMPTY third state, and repeatBlockedInputs - replaying a grip the mod consumed but did not act on. Plugin is binary. vrikgestures.ini read 2026-09-05 -> ch03 #stroke-grammar and INPUT-009: one rebindable gesture button plus a stick stroke yields 13 actions per hand (press, six cardinal directions, six out-and-return pairs), 26 across two hands, with no menu and no dwell; the button is selectable from nine physical inputs; the game binding is suppressed during a gesture and replayed if none matched; hand animation degrades by controller capability rather than disappearing; and palm orientation is used as a zero-button UI trigger. |
| `input_locomotion` | 🟥 not reviewed | `—` | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | — no entry — | — | — |

#### WeWereInVR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟩 full | `SOURCE` | harvested 2026-08-28 into ch18: patches globalgamemanagers BuildSettings.enabledVRDevices to ['OpenVR'], enabling Unity's built-in stereo path rather than hooking rendering; backs the original up first |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟨 partial | `SOURCE` | BepInEx managed mod for hands, poses, haptics and laser pointers - the gameplay half of the split |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟨 partial | `AUTHOR` | asset edit breaks on game update; README opens by saying the current game version is unsupported |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### White_Knuckle_VR

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | 🟨 partial | `AUTHOR` | — |
| `input_locomotion` | 🟩 full | `AUTHOR` | README only — no source in repo |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### witcher3-vr

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟨 partial | `SOURCE` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | 🟨 partial | `SOURCE` | — |
| `ui_hud` | 🟨 partial | `SOURCE` | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟩 full | `SOURCE` | harvested 2026-08-25 into ch19 presentation-scale: presentation size as FOV not resolution (PERF-005), mode-matrix route predicates, stale-resolve must not move pair authority |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | — no entry — | — | — |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### WorldWarVR-Releases

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | — no entry — | — | — |
| `xr_lifecycle` | — no entry — | — | — |
| `xr_input` | — no entry — | — | — |
| `camera_tracking` | — no entry — | — | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | — no entry — | — | — |
| `hands_interaction` | — no entry — | — | — |
| `input_locomotion` | 🟨 partial | `AUTHOR` | — |
| `performance` | — no entry — | — | — |
| `audio` | — no entry — | — | — |
| `packaging_deploy` | 🟩 full | `AUTHOR` | binaries + 4 docs only |
| `re_discovery` | — no entry — | — | — |
| `source_integration` | — no entry — | — | — |

#### XIII2003-vr-external-research

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | — |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟩 full | `SOURCE` | 2026-08-29, harvested into ch18 #stock-cheat-commands. XIII ships a native F2 console whose command set is NOT XIII-specific - it is the stock Unreal GameInfo/cheat-manager surface unchanged since UE1. Fly (gravity off, collision kept), Ghost (collision off), Walk, and PlayersOnly (freezes NPCs and vehicles while the player still moves) give a detached camera and a frozen world with no hooks, no injection and no RE - the cheapest rung of the control-plane ladder, available on day one. The transferable point is that the surface belongs to the ENGINE, so expect it on any UE1/UE2 target even when undocumented. |
| `source_integration` | 🟥 not reviewed | `—` | — |

#### XIII2003-vr-mod

| Area | Review | Evidence | Note |
|---|---|---|---|
| `stereo` | 🟥 not reviewed | `—` | BINARY ONLY: ships D3DDrv.dll plus CONTRIBUTING/CREDITS/README and no source - an Unreal render-device replacement. This is the MOD repo of the six-repository family whose research repo (XIII2003-vr-external-research) is already harvested into ch18 #stock-cheat-commands, so the structure is documented even though the implementation is not. |
| `xr_lifecycle` | 🟥 not reviewed | `—` | — |
| `xr_input` | 🟥 not reviewed | `—` | — |
| `camera_tracking` | 🟥 not reviewed | `—` | — |
| `render_hazards` | — no entry — | — | — |
| `ui_hud` | 🟥 not reviewed | `—` | — |
| `hands_interaction` | 🟥 not reviewed | `—` | — |
| `input_locomotion` | — no entry — | — | — |
| `performance` | 🟥 not reviewed | `—` | — |
| `audio` | 🟥 not reviewed | `—` | — |
| `packaging_deploy` | 🟥 not reviewed | `—` | — |
| `re_discovery` | 🟥 not reviewed | `—` | — |
| `source_integration` | 🟥 not reviewed | `—` | — |

