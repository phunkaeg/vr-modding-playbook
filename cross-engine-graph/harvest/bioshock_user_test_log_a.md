# BioshockVR — USER_TEST_LOG harvest (lines 1-2600)
Lines read: 1-2600

### Suspect your own capture/debug tool before the target process when a crash only appears under "more content on screen"
**What happened:** RenderDoc captures on `BioshockHD.exe` crashed reliably only once the wrench was equipped, looking like a BioShockVR regression. Breakpointing `renderdoc.dll+0xC22FB` under x32dbg found a fatal allocation with args `[ebp+8]=0x00200020, [ebp+0xC]=0`; an external VA query of the paused 32-bit process showed only ~62.7 MiB free address space, largest free block `0x1D0000` — too small for RenderDoc's second same-sized `0x200020` scratch allocation. Root cause was 32-bit RenderDoc running out of its own virtual address space once more foreground geometry existed, not a BioShockVR bug. First-chance `E06D7363` C++ exceptions seen in the debugger were noise around that same failure, not the real exception.
**Why it generalises:** any 32-bit target paired with a 32-bit external instrumentation tool (capture tool, debugger, profiler) is address-space-limited independent of the game's own code. A repro that only triggers under "more stuff on screen" is a classic signature of the *tool* running out of VA space, not a code-side regression.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Tooling lies in specific, learnable ways — know them before you trust a reading"

### A visual artifact that looks like one bad pass can be two engine views sharing one capture buffer
**What happened:** BioShockVR's "cyan shell" artifact survived many negative A/Bs (compact companion off, screen-space SRV fallback off, full-eye vs. cropped projection, ordinal draw-band skipping across modes 4-8). It was only explained once draws were grouped by (HDR color resource, depth resource, clear-epoch) identity instead: private replay was merging an exterior city/vista view into the same color+depth pair as the main camera, with per-frame source-draw counts swinging from ~171 to ~620 depending on whether the second view fired. Draw-order/ordinal bisection could suppress it but never isolate it, because ordinal position was never a stable ownership boundary.
**Why it generalises:** any engine that reuses one intermediate buffer across multiple logical render passes (main view plus reflection/portal/vista) produces artifacts that look shader- or pass-specific but are actually a resource-identity collision. Group candidate draws by render-target + depth + clear-epoch identity before trusting shader- or order-based attribution.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Attribute by ownership before shader identity"

### Attach-mode injection misses native objects the engine only constructs once, before your hook existed
**What happened:** Across nine builds (`0.3.169`-`0.3.178`), BioShockVR's native AimIK wrapper never appeared: `AHands+0x40C` stayed null through thousands of samples with zero recreate/tracker/target-update rows, even though the hook installed correctly (`signatureMatches=1`) and exact `AHands`/mesh/skeleton identity was found every time. Cause: the game had already constructed its `AHands` actor before attach-time injection ran, so the one-time IK-wrapper construction the hook waited for had already happened and would never recur in that process lifetime.
**Why it generalises:** any engine subsystem lazily constructed once per actor/object lifetime is invisible to a hook installed after that construction already occurred, on any engine. The fix isn't a better hook — it's a different injection lifecycle (suspended-launch injection, or deliberately forcing recreation) so hooks are live before the one-time construction seam runs.
**Chapter:** 07-engine-integration-safety.md
**Status:** SHARPENS "Attach versus launch injection — and one-time construction seams"

### A launcher-set environment variable does not reach a DLL injected into an already-running process
**What happened:** `BIOSHOCKVR_VIEWMODEL_PROBE=1` was set before launch, but three consecutive builds logged `viewmodelProbe=0` inside the injected DLL. It was only disproven by Frida reading the live process's actual environment block, which showed the variable as `null` inside the running `BioshockHD.exe`. The fix moved the toggle to an INI file read at DLL load instead of relying on process environment.
**Why it generalises:** environment variables are inherited only at process creation; attach-mode injection into an already-running process cannot retroactively add to that process's environment block, on any OS or engine. Verify configuration by reading what the live target process actually has (via a runtime inspector), not what you set in your own shell before injecting.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Settings lie: read the value the consumer receives, not the one you wrote"

### The immediate return address of a hooked shared utility is the utility's caller wrapper, not the route you want
**What happened:** Hooking BioShockVR's D3D11 cbuffer upload wrapper (`FUN_110c2f30`) and logging the immediate caller RVA always resolved to the same renderer-state-flush function (`0x789d92`/`0x789df7`) regardless of whether the write came from a material, BSP, or model-batch route. Only walking one frame further up the stack (frame 3: `FUN_110660b0`/`FUN_11065c60`/`FUN_11065ac0`, then frame 4) exposed route-distinguishing callers like `material_batch_FUN_10f76e30` vs `layer_model_batch_FUN_10f77db0`.
**Why it generalises:** any engine funnels many logically distinct call sites through one shared low-level utility (buffer upload, allocator, formatter); the immediate return address from inside that utility identifies its shared wrapper, not the semantically meaningful caller. Caller attribution needs enough stack depth to get past shared plumbing.
**Chapter:** 11-re-anchoring-and-discovery.md
**Status:** SHARPENS "An exported address is usually a thunk, and internal callers bypass it"

### A "validity" flag your own probe emits can encode a wrong assumption, not a bad hook
**What happened:** `0.3.118-cameraanalyzer` logged `identityValid=0` on every sample of a camera-constructor hook that was otherwise firing correctly (`readValid=1`, plausible arguments). The natural read is "the hook target is wrong." The actual cause: the classifier assumed constructor argument 4 was the controller; it was really the view-target/pawn (a different vtable), while the real controller lived at `viewport+0x48` — confirmed by the ~60-unit eye-height offset between camera and view-target positions.
**Why it generalises:** a boolean "is this correct" field your own instrumentation emits encodes an assumption about object layout that can be wrong even when the underlying hook and read are perfectly fine. Before treating a validity failure as proof the hook/address is wrong, audit what the classifier itself assumes about which field means what.
**Chapter:** 06-debugging-methodology.md
**Status:** NEW

### Offline shader-reflection buffer sizes and live runtime buffer sizes are not the same number
**What happened:** RenderDoc's shader reflection reported viewmodel constant buffers as 544 and 752 bytes; the live D3D11 buffer objects actually bound at those exact draws were 576 and 832 bytes. A classifier requiring exact 544/752 matches produced zero candidates for two full builds even while index-count/render-target/depth evidence proved the lane was live and correct.
**Why it generalises:** shader-reflection metadata describes the declared cbuffer layout, not necessarily the byte width of the buffer object the engine actually allocates and binds (padding, over-allocation, or a different code path can inflate it). Any cross-engine workflow that correlates static reflection data with live captures should treat reflected sizes as a hint and confirm the real matching predicate from runtime values.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Tooling lies in specific, learnable ways — know them before you trust a reading"

### A bounded diagnostic sample budget spent early makes late-session evidence look like it disappeared
**What happened:** Draw-correlated cbuffer layout samples were capped (e.g. 128 samples) and got consumed entirely within the first one or two HMD pose frames; later frame summaries kept showing ~100 matching lanes per frame, but zero detailed samples existed to describe them because the budget was already spent. Read naively, this looks like the candidate lane vanished after startup — it did not.
**Why it generalises:** any per-session cap on verbose diagnostics silently starves out evidence from later in a run once the cap is hit, and "no samples in the tail of the log" is easily misread as "the thing stopped happening" instead of "the counter ran out." Always cross-check a raw-sample dropout against coarse aggregate counters before concluding a signal disappeared.
**Chapter:** 06-debugging-methodology.md
**Status:** SHARPENS "Logging discipline (or your evidence destroys itself)"

### A cloud-synced config file can silently outrun the version you think you're testing
**What happened:** A run loaded `StereoWorldProjectionFarMilli=10000000` even though the on-disk INI at that path already read `65536000`, attributed to OneDrive sync lag between the edit and the DLL's read at injection time. The live/cached shader-derived value masked the stale read on most fields, but it was flagged as an ongoing correctness risk for every subsequent config-driven test.
**Why it generalises:** any workflow where the config a running/injected process reads lives in a cloud-synced folder has a race between "you edited the file" and "the sync client actually wrote the new bytes to disk" before injection reads it — a stale value loads with no error, silently changing which build variant you're actually testing.
**Chapter:** 08-project-process.md
**Status:** SHARPENS "Test-artifact config files silently outrank your code defaults"

### When reverting a regression, revert exactly the flag that broke, not the whole feature bundle
**What happened:** `0.3.179-viewmodelrecover` fixed a wrench/arm rotation regression by disabling `absoluteGripPlacement`, `absoluteGripOrientation`, `HandsAimIk`, and `HandsAimIkDriveTarget` together — but only orientation/native-IK had caused the regression. The bundled revert also threw away the previously confirmed-useful grip placement, requiring a second build (`0.3.180`) that restored only `WeaponViewmodelAbsoluteGripPlacement=1` and left the other three off.
**Why it generalises:** a "recovery" change has the same blast-radius risk as a forward experiment. Reverting an entire bundled feature set to fix one broken flag re-introduces every regression the bundle had already fixed; isolate the revert to the single variable actually implicated, the same way you'd isolate a forward A/B.
**Chapter:** 05-assets-and-materials.md
**Status:** SHARPENS "One-variable A/B, always"
