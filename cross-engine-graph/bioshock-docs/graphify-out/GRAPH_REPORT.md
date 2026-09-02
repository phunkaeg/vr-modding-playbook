# Graph Report - .  (2026-08-07)

## Corpus Check
- 41 files · ~293,243 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 746 nodes · 917 edges · 52 communities (43 shown, 9 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 189 edges (avg confidence: 0.8)
- Token cost: 2,026,572 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]

## God Nodes (most connected - your core abstractions)
1. `D3D11Hooks module` - 11 edges
2. `P_center Projection Matrix` - 9 edges
3. `FShadowDepthTestPass11::UploadConstants` - 8 edges
4. `AHands::vftable` - 7 edges
5. `AimIKTargetTracker Constructor` - 7 edges
6. `UModel + BSP Serialization` - 7 edges
7. `Catalog.bdc Index Format` - 7 edges
8. `screenDataToCamera Constant` - 7 edges
9. `Shadow-Mask Producer/Consumer Contract` - 7 edges
10. `FShadowMaskSceneContext::Render` - 6 edges

## Surprising Connections (you probably didn't know these)
- `0.3.167/0.3.168: alleged tracked-mask HDR consumers of the shadow-mask resource are themselves PS-null draws, making them false positives caused by retained SRV state rather than genuine consumers of the shadow producer` --semantically_similar_to--> `Do not hook shader registration functions as camera writers`  [INFERRED] [semantically similar]
  USER_TEST_LOG.md → FAILURE_REGISTRY.md
- `Do not trust current MCP cbuffer numeric values` --semantically_similar_to--> `0.3.108-shelltrace log loaded StereoWorldProjectionFarMilli=10000000 even though the current on-disk INI was 65536000, flagging OneDrive-synced/stale-config risk as a recurring evidence-quality hazard separate from any code bug`  [INFERRED] [semantically similar]
  FAILURE_REGISTRY.md → USER_TEST_LOG.md
- `Shadow-Mask Producer/Consumer Contract` --semantically_similar_to--> `MaterialFactory_Shader.hlsl`  [INFERRED] [semantically similar]
  RE_FINDINGS.md → Engine Findings/BioShock_Materials_And_Shaders.md
- `Shared wrench-root rigid-group pivot (0.3.162)` --semantically_similar_to--> `Wrench pickup object and equipped viewmodel use distinct HDR sublanes`  [INFERRED] [semantically similar]
  CURRENT_STATE.md → HYPOTHESES.md
- `Do not trust current MCP cbuffer numeric values` --semantically_similar_to--> `Repeated hook_config viewmodelProbe=0/detailedInspection=0 logs across several sessions were a test-setup problem: the diagnostic environment variables never reached the injected game process, confirmed by Frida reading them as null in-process`  [INFERRED] [semantically similar]
  FAILURE_REGISTRY.md → USER_TEST_LOG.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **0.3.191 combined crash-containment stack** — current_state_0_3_191_internald3dguard, current_state_internal_d3d_call_guard, current_state_openxr_startup_visibility_handshake, current_state_virtual_desktop_fail_fast_crash [EXTRACTED 1.00]
- **Native BioShock shadow-mask render chain** — address_registry_bs_rendersceneshadowcontexts, address_registry_fshadowmaskscenecontext_render, address_registry_fobjectshadowdepthpass11_uploadconstants, address_registry_fshadowdepthtestpass11_uploadconstants, address_registry_fshadowdepthstencilpass11_uploadconstants [EXTRACTED 1.00]
- **Native AimIK lifecycle proof chain** — address_registry_aimiktargettracker_constructor, address_registry_ahands_vftable, current_state_native_aimik_lifecycle, hypotheses_torso_space_aimik_target_model [INFERRED 0.85]

## Communities (52 total, 9 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (51): 0.3.65-perfab: StereoWorldDiscoveryProbe gate decouples classification from perf, 0.3.66-compact320: 320-byte compact-world VS cbuffer tracking/classification, 0.3.68-launchinject: injector suspended-launch + LoadLibrary injection, 0.3.69-eyedump: post-blit OpenXR eye texture BMP dump, 0.3.70-dumphotkey: Ctrl+F10 hotkey arms burst eye-texture dump, 0.3.71-artifactprobe: draw manifest + screen-space SRV mono fallback, 0.3.72-srvfilter: narrows SRV fallback by slot mask + min index count, 0.3.73-compact320gate: sparse compact-WVP preflight promotion (+43 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (44): BS_RenderSceneShadowContexts, ConstructD3D11RenderPassBundle, FObjectShadowDepthPass11::UploadConstants, FShadowDepthStencilPass11::UploadConstants, FShadowDepthTestPass11::UploadConstants, FShadowMaskSceneContext::Render, 0.3.173-shadowautopsy: Foreground-Pass Pose-Coherence Fix, 0.3.174-shadowcontract: Bounded Shadow Autopsy Contract (+36 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (44): 0.3.60-pcenterfitprobe: fit probe scans P_center FOV/near/far, 0.3.61-screendatapcenter: derive P_center from screenDataToCamera+WVP depth, 0.3.63-vscompanions: VS companion vertexClipPlane/localEyePos transform, 0.3.64-coherencescout: log-only PS reconstruction scout, 0.3.57-matrixstereoproof: First Native Private-Eye Geometry Stereo Proof, 0.3.58-nativevs-pcenter: Projection-Conjugated Eye Translation newWVP, 0.3.59-nativevs-isolate: Matrix-Only Isolation + Affine Requirement, 0.3.60-pcenterfitprobe: P_center FOV/Near/Far Fit Probe (+36 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (39): 0.3.100-exactsrv: exact index-count SRV fallback list (narrow, reversible), 0.3.101-bspexact: BSP-route exact slot-mask+index SRV fallback for curved architecture, 0.3.103-vrfov-eye: OpenXR-sized private eye targets + per-eye FOV projection (full-eye VR), 0.3.105-frustumlock: XR-FOV near/far fix, all-or-nothing frustum rule, mono-fallback frustum remap, head-aim mouse injection, 0.3.106-skyfarfog: cached near/far fallback + per-eye screenDataToCamera companion rewrite (fixes camera-centered fog shell), 0.3.89-depthpairdump: synchronized private-eye color+depth BMP dumps prove holes are already in private color, 0.3.90-fallbackcolorpass: narrow mono-fallback color-pass depth override (negative result: no visible change), 0.3.91-wvpcandidates: tries alternate WVP starts (c9/c10/c40) when affine gate fails (+31 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (36): 0.3.102-vrpivot-fill: FOV-Zero Crop Fill Mode, 0.3.103-vrfov-eye: OpenXR-Sized Private Eye Targets, 0.3.104-portrait: Forced Portrait Swapchain Override, 0.3.107-shellattrib: Compact Companion Rewrite A/B for Shell, 0.3.108-shelltrace: Full-Eye Target-Size Shell A/B (Falsified), 0.3.109-0.3.111: Draw-Order Ordinal-Band Shell Bisection, 0.3.112-uevrlanes: UEVR-Informed D3D11 State Guards + Engine Hook Scout, 0.3.113-0.3.114: Render-Target-Manager View Provenance/Epoch Tracking (+28 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (36): 0.3.118-cameraanalyzer: Player-Camera Constructor Hook (RVA 0x56DC30), Auto-build after decisive log triage (workflow rule), Bridge the flat BioShock image before projection mutation, Copy SS2VR structure without SS2-specific implementation, Default runtime proof to RenderDoc capture-safe mode, Prioritize stereo 3D and 6DoF over gamma, Promote numeric cbuffer proof to temporal per-eye OpenXR bridge, Promote OpenXR smoke to confirmed and move to game-image bridge (+28 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (36): ControllerInputRouter module, OpenXRInput module, XInputBridge module, 0.3.32-wideview: widen cloned-cbuffer stereo proof to more route families, accepting visual distortion to test whether larger per-eye separation is possible without crashing, 0.3.33-wideeye: add dedicated proof-eye latch so temporal left/right OpenXR capture becomes deterministic instead of starving on eye=1 only, 0.3.34-sustainedwide: clamp out-of-range scales only under wide-proof mode so the visual proof survives HMD motion without weakening the non-wide fail-closed gate, 0.3.35-directdraw: replay DrawIndexed twice with forced left/right cbuffers into the same HDR target, accepting a ghosted overlay as an acceptable interim visual signal, 0.3.36-stalefallback: invalidate cached temporal eye readiness when no fresh stereo candidate exists, fixing a frozen-HMD-while-desktop-updates bug (+28 more)

### Community 7 - "Community 7"
Cohesion: 0.08
Nodes (35): AActor::MoveSmooth, AHands::vftable, AimIKTargetTracker Constructor, AShockPlayer::vftable, SkeletonInstance::SetAnimationWeight (vtable slot 0x1d), 0.3.148-roomscaleprobe: MoveSmooth Roomscale Probe, 0.3.152-autorecenter: Automatic Recentering on Player/World Replacement, 0.3.153-cameranimprobe: Camera-Animation Attribution Probe (+27 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (35): AShockPlayerController::UpdateFocus, AShockPlayerController::vftable, AWeapon::GetPerfectFireStart, CameraAnimationModifier_HeadbobContextController::vftable, FPlayerSceneNode::vftable, UAttackAbility::GetPerfectFireStart, 0.3.141-weaponaimprobe: GetPerfectFireStart Log-Only Hook, 0.3.142-viewmodelpose: Controller-Relative Viewmodel Pose Owner (+27 more)

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (32): 0.3.67-shadowmaskab: neutral shadow-mask SRV replacement A/B (diagnostic), HookConfig module, BS4_wrench.rdc capture, Projected-light/gobo screen-space defect, VR-primary desktop-foreground suppression (0.3.184), Shared wrench-root rigid-group pivot (0.3.162), 0.3.67-shadowmaskab: replace target-sized s_shadowMask (PS slot 2) with a cached 1x1 white SRV during private eye replay only, as a cheap falsifiable test for eye-dependent black boulder shading, Do not classify loose pickup props as equipped foreground from index count alone (+24 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (31): AWrench::ProcessCollisionContacts, AWrench::TickCollisionPhantom, AWrench::vftable, 0.3.143-reference-reticle: Stereo-Safe OpenXR Reference Reticle, 0.3.144-hudquad: HUD Capture + OpenXR HUD Quad Layer, 0.3.145-depthperf: OpenXR Depth Layer + Performance Telemetry, 0.3.146-physicalcrouch: Physical-Crouch Native Duck Owner, 0.3.147-configprofiles: Config Schema/Profile Overlays (+23 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (31): Class Rollup (Part D.2), dyn_* Props Sidecar System, Havok Rigid-Body Physics Gap, Material Flattening (Shader to Texture), Native UClass Shells (Part D.3), rollup.txt Mapping File, SkeletalMesh Gap (Havok Packfile), Type-Safety Filter (IsSafeBioshockMaterial) (+23 more)

### Community 12 - "Community 12"
Cohesion: 0.07
Nodes (28): 0.3.137-shadowviewrect: Bounded Shadow-Pass Diagnostic Scout, 0.3.157-calibration: LOCAL/STAGE Application-Space Calibration, 0.3.159-shadowmaskreplay: First Guarded Per-Eye Screen-Space Producer, 0.3.161-inputrecenter-shadowbind: Recenter Gesture + Slot-Search Shadow Consumer, 0.3.162-inputlatch-sharedpivot: XInput Latch + Shared Wrench Pivot, 0.3.163-worldhorizon-shadowviewport: OpenXR World-Horizon Recenter + Shadow Viewport Fix, 0.3.164-handscensus: Bounded Read-Only AHands Runtime Census, 0.3.165-idlesuppress-shadowresolve: Idle-Weight Suppression + Shadow-Resolve Falsification (+20 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (27): StereoProjection module, 0.3.22-familyprofile VS0/PS0 Byte-Size Profiling, 0.3.58 Native VS row-vector P_center Proof, 0.3.25-pairpreflight Paired Route Readiness, 0.3.61 P_center Derived From screenDataToCamera, P_center extraction from screenDataToCamera, layer_model_batch_FUN_10f77db0 stereo route family, material_batch_FUN_10f76e30 stereo route family (+19 more)

### Community 14 - "Community 14"
Cohesion: 0.10
Nodes (26): BioshockHD.exe Image Base, FUN_10fb1c10 (D3D11 Device/Context Init), 0.3.189-layerisolation: Motion-Comp Layer Env Isolation, 0.3.190-statehandshake: OpenXR Startup Event Repoll Fix, 0.3.191-internald3dguard: Self-Interception Ownership Guard Fix, 0.3.192-layerrestore: Motion-Comp Layer Restored, 0.3.193-motioncompguard: Motion-Comp Layer Re-Disabled, D3D11Hooks module (+18 more)

### Community 15 - "Community 15"
Cohesion: 0.09
Nodes (26): 0.3.160-inputshadow320: centered frusta, 320-byte shadow producer selector, equipped-hand-gated controller pose, XInput snap-turn pulse, 0.3.167-gripplacement: absolute shared-pivot grip placement + uniform wrench/arm model scale, 0.3.168-shadowlifecycle: tightens shadow consumers to live-PS requirement, adds resource lifecycle/BMP evidence logging, After 0.3.166 confirmed a stable authored grip with no flashing, make the next build an opt-in absolute head-relative grip placement/scale step, kept separate from AimIK/lighting/melee/aim changes, Arbitrate physical and VR sticks at the confirmed XInput boundary, Bridge native XInput vibration to OpenXR haptics, Build controller acquisition before gameplay routing, Promote centered render/submission frusta to the startup baseline after Ctrl+F6 gave repeatable lighting-stability evidence matching SOMAVR's deferred-shadow fix; route snap-turn through native XInput right-stick since Windows mouse delivery never rotated BioShock (+18 more)

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (24): 0.3.119-cameraidentity: Corrected ViewTarget/Controller Identity, 0.3.120-nativeorientation: Native Pose Handoff to Camera Constructor, 0.3.121-orientationstability: Startup Tracking-Settlement Fix, 0.3.122-native6dof: Ownership Split Between HMD View and Weapon Model, 0.3.123-6dofaxisfix: Corrected Scene-Position Sign / Roll Invert, 0.3.124-horizontalbasis: Yaw-Offset Fix for Quarter-Turned Mapping, 0.3.125-recenterbasis3x: Proper Recentered Position Basis, 0.3.126-0.3.128: HookConfig/HeadPoseControls/HookSettings Refactor (+16 more)

### Community 17 - "Community 17"
Cohesion: 0.14
Nodes (16): 0.3.179-0.3.180: Viewmodel Grip-Placement Regression Recovery, 0.3.182-0.3.183: Grip-Yaw + Neutral Shadow-Mask A/B Saga, 0.3.184-vrprimaryfg: VR-Primary Desktop Foreground Suppression, 0.3.185-ownedsnap: Head-Pose Yaw-Bias Snap Turn, 0.3.186-bodysnap: Native Mouse Body-Yaw Impulse Test, Snap-turn body/gameplay yaw ownership problem, Treat grip yaw as authored mount correction, not live delta, Move snap turn to native head-pose yaw and gate foreground by equipped evidence (+8 more)

### Community 18 - "Community 18"
Cohesion: 0.24
Nodes (13): UTexture::Serialize (bsm), .blk Bulk File Format, Catalog.bdc Index Format, DynamicBulkFileTextures.blk, Texture Block Mip Splitting, blockSize(Format,w,h) Formula, ETextureFormat Enum, Mip Tail Layout (SkipOffset/BulkA/BulkB) (+5 more)

### Community 19 - "Community 19"
Cohesion: 0.17
Nodes (12): AShockHUD::vftable, UFlashMovie::vftable, Keep fixed HUD/crosshair in the final-LDR/Flash capture domain rather than hooking AShockHUD::RenderHealthBars, since that function renders world-space actor bars under a different projection contract, Replace zero-layer xrEndFrame comfort frames with black-cleared eye swapchains submitted through the normal projection layer, to keep runtime/D3D swapchain ownership stable across the recurring Virtual Desktop fail-fast crash, Stop vanilla-only live tracing on the desktop-mirror shell artifact; reproduce it under the injected build and correlate native pass-call counts with D3D targets/SRVs before any new suppression rule, AShockHUD::RenderHealthBars is not the fixed player meter path, AShockHUD::vftable (RVA 0xD89F80), HDR (R11G11B10_FLOAT) / Final-LDR (R8G8B8A8_UNORM) Render Targets (+4 more)

### Community 20 - "Community 20"
Cohesion: 0.20
Nodes (10): CompactIndex Object Reference, Light Actor Property Quirks, Serial Boundary Protection, Tagged Property Serialization (FPropertyTag), TLazyArray Bulk Data, CompactIndex / FName Package Parsing, Vengeance Engine (UE2.5 Fork), UEVR prior-art architecture lessons (+2 more)

### Community 21 - "Community 21"
Cohesion: 0.22
Nodes (9): BioShock 3DMigoto $Globals Layout (WIP1 Reference), 0.3.144 Isolated HUD Quad Test, Prior-Art Depth-Aware HUD/Crosshair Lane, 0.3.144 First Final-LDR HUD Composition Path, 0.3.143 Stereo-Safe Reference Reticle, ShaderOverride_BS1_HUD0 / TextureOverride_BS1_Crosshair, UE3 Regex Fix Strategy (3D Vision Clip-Space Correction), Bioshock 1 Remastered 3D Fix WIP1 Package (+1 more)

### Community 22 - "Community 22"
Cohesion: 0.29
Nodes (8): FBspNode (100 bytes), FBspSurf, FLeaf, FVert, FZoneProperties (128-bit), UModel + BSP Serialization, BSP Lightmap (LightMaps_BSP DXT), UModel/BSP Serialization (FBspNode/FBspSurf, Lightmap Atlas)

### Community 23 - "Community 23"
Cohesion: 0.29
Nodes (7): BioShock .bsm Map Format, Epic 141 / Licensee 56 Version, Package Tag 0x9E2A83C1, FStateFrame (Vengeance), Vengeance 8-byte Per-Object Header, Zlib Chunk Compression, BioShock Lightmap/Static-Mesh Engine-Findings Docs

### Community 24 - "Community 24"
Cohesion: 0.33
Nodes (7): FName NameIndex+Number, FObjectExport, FObjectImport, FPackageFileSummary Header, ObjectFlags, UPolys + FPoly, FName Number-to-Text Off-by-one Rule

### Community 25 - "Community 25"
Cohesion: 0.29
Nodes (7): BioShockVR Project Memory Index, Current State, Failure Registry, Hypotheses, Next Chat Handover, Project Phases, Reverse Engineering Findings

### Community 26 - "Community 26"
Cohesion: 0.40
Nodes (6): OpenXR eye-resolution scale (startup-only), Direct same-frame draw replay can bridge cloned-buffer proof to real stereo, OpenXR-sized private eye targets replace 16:9 crop presentation, Private per-eye HDR/depth targets bridge same-target proof to true stereo, Temporal OpenXR eye cache must use fresh stereo candidates, B1.4/B1.3 OpenXR Bootstrap/Stereo-Smoke/Game-Bridge checklist

### Community 27 - "Community 27"
Cohesion: 0.40
Nodes (5): 0.3.132-openxrinput: OpenXR Action-Set Input Foundation, 0.3.133-controllerturn: Snap/Smooth Body Turn via Relative Mouse, 0.3.134-136: XInput Movement/Actions/Haptics Bridge, 0.3.140-inputsafety: Physical/Synthetic Input Arbitration, 0.3.155-handedness: Controller-Role Handedness Resolution

### Community 28 - "Community 28"
Cohesion: 0.40
Nodes (5): Calibration Profile (Set-BioShockVRCalibration.ps1), 0.3.157 Standing/Seated Calibration Test, Head Or Crouch Origin Calibration, Floor-Aware Calibration (STAGE), Normal Calibration (LOCAL)

### Community 29 - "Community 29"
Cohesion: 0.40
Nodes (5): Make first-frame submission follow refreshed OpenXR visibility state, Isolate the loaded Motion Compensation API layer without rolling back VR features, Isolate OpenXR internal D3D/DXGI calls from BioShock game hooks, Restore Motion Compensation after crash containment, Restore Motion Compensation isolation as a safety default

### Community 30 - "Community 30"
Cohesion: 0.40
Nodes (5): XR_APILAYER_NOVENDOR_motion_compensation_32.dll, OpenXR Bootstrap Sequence, OpenXR Game Bridge (Flat Blit), Virtual Desktop Freed-Object Fail-Fast (0xDEDEDEDE), VirtualDesktopXR Runtime

### Community 31 - "Community 31"
Cohesion: 0.50
Nodes (4): 0.3.138-comfortblackout: Bounded Comfort-Blackout Request Lane, 0.3.139-releaseidentity: Build Manifest + Injector Doctor, 0.3.156-portable: Portable Release Packaging/Installer, 0.3.158-compatreport: Host/Runtime Compatibility Report Tool

### Community 32 - "Community 32"
Cohesion: 0.50
Nodes (4): ConfigSchemaVersion / config_identity Gate, hmd-only / motion-control / debug Profile Overlays, Set-BioShockVRProfile.ps1, Profiles And Hands Selection

### Community 33 - "Community 33"
Cohesion: 0.50
Nodes (4): FNameEntry QWORD Flags, FString Reversed Sign Convention, BioShock FString Convention (signed length = UTF-16LE/ANSI), UELib Package/Script Extraction Pattern

### Community 34 - "Community 34"
Cohesion: 0.50
Nodes (4): FLightMapIndex, FLightMapLight, Lightmap UV Math (WorldToLightMap), Luminance DXT Swizzle (.yzx)

### Community 35 - "Community 35"
Cohesion: 0.50
Nodes (4): Matrix-Stereo Fallback Classification (should-stereo vs correctly-excluded), PS Reconstruction (screenToWorld/worldEyePos) Location In Deferred Passes, Older Bioshock_fix Pixel (screenToWorld/worldEyePos) Layout Families, Older Bioshock_fix Vertex Layout Families

### Community 36 - "Community 36"
Cohesion: 0.67
Nodes (3): UI module, Late-LDR HUD tee and head-locked OpenXR quad, HMD-forward binocular reference reticle (0.3.143)

### Community 37 - "Community 37"
Cohesion: 0.67
Nodes (3): Mouse Sensitivity String Leads (unconfirmed), Native Crouch Input Ownership (Duck alias / XENON_LTHUMB_BUTTON), 0.3.146 Physical Crouch Plus Depth/Performance Test

### Community 38 - "Community 38"
Cohesion: 1.00
Nodes (3): UnrealPort Cross-Reference, UnrealPort Repository (UE1/UE2/UE3 Content Tooling), Legacy SkyZoneInfo/Camera/ViewTarget Vocabulary

### Community 39 - "Community 39"
Cohesion: 0.67
Nodes (3): 0.3.130 VR Lifecycle/Performance Test, Performance Is Poor, Part D: Frustum-Coherence Hygiene

### Community 40 - "Community 40"
Cohesion: 0.67
Nodes (3): UGamepadPlayerInput::CalculateInput, XInputGetState Import, XInputSetState Import

## Ambiguous Edges - Review These
- `Native Crouch Input Ownership (Duck alias / XENON_LTHUMB_BUTTON)` → `Mouse Sensitivity String Leads (unconfirmed)`  [AMBIGUOUS]
  console-commands.md · relation: conceptually_related_to

## Knowledge Gaps
- **113 isolated node(s):** `FUN_10fb1c10 (D3D11 Device/Context Init)`, `ConstructD3D11RenderPassBundle`, `UFlashMovie::vftable`, `RenderStateTracker module`, `RenderClassification module` (+108 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Native Crouch Input Ownership (Duck alias / XENON_LTHUMB_BUTTON)` and `Mouse Sensitivity String Leads (unconfirmed)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Shadow-Mask Producer/Consumer Contract` connect `Community 9` to `Community 1`, `Community 4`, `Community 11`, `Community 13`, `Community 15`?**
  _High betweenness centrality (0.195) - this node is a cross-community bridge._
- **Why does `Mono screen-space s_shadowMask / attenuation-mask producer sampled once for the center/mono view, causing eye-dependent black shading and stretched projected-light artifacts` connect `Community 15` to `Community 0`, `Community 9`?**
  _High betweenness centrality (0.145) - this node is a cross-community bridge._
- **Why does `P_center Projection Matrix` connect `Community 13` to `Community 2`, `Community 4`, `Community 5`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `FShadowDepthTestPass11::UploadConstants` (e.g. with `FShadowDepthTestPass11 400-byte PS Layout` and `FShadowDepthTestPass11_UploadConstants (RVA 0x007762e0)`) actually correct?**
  _`FShadowDepthTestPass11::UploadConstants` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `AHands::vftable` (e.g. with `AHands::vftable (RVA 0xD8A28C)` and `AHands Actor`) actually correct?**
  _`AHands::vftable` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `AimIKTargetTracker Constructor` (e.g. with `AimIKTargetTracker::TrackTarget (RVA 0x5A36E0)` and `AimIKTargetTracker`) actually correct?**
  _`AimIKTargetTracker Constructor` has 2 INFERRED edges - model-reasoned connections that need verification._