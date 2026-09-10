# VRFramework vs the VR Modding Playbook — side by side

**Date:** 2026-09-10
**Subject:** [elliotttate/vrframework](https://github.com/elliotttate/vrframework), registered today as external source `vrframework`
**Method:** cloned to `Other VR mods/vrframework`, measured locally, four of its citations checked against the cited upstream file fetched with `curl` (no summariser in the loop), commit dates from the GitHub API.

## Verdict in one paragraph

Not a competitor and not a duplicate. It is a **code-reading of three shipped ports** — praydog's REFramework and mutars' starfield2vr / anvilengine2vr, all public, all MIT — written as a 17-part linear narrative with a reconstructed C++ scaffold beside it. Its own README says so: *"built by reading, line by line, three real open-source projects."* Topically it overlaps the playbook almost one-to-one, at roughly one-fifth the length, with **no evidence taxonomy and no retrieval layer** — but with **accurate receipts** (4 of 4 checked citations exact), a genuinely deeper treatment of **frame timing** than the playbook has, and **Creation Engine 2 / Starfield**, which the playbook does not cover at all. Take its three-clock timing model and its per-eye-history implementation; contribute back the headset counter-example to its TAA claim.

## What each thing is

| | vrframework | Playbook |
|---|---|---|
| Form | 17 guides, linear narrative, plus a C++ scaffold | 41 hand-written docs behind a retrieval layer (symptom index, failure atlas, pattern catalog) |
| Built from | Reading 3 public ports by two other authors | 10 in-house ports (unreleased) + 108 surveyed external sources |
| Ships code? | 5,760 lines of C++, described by the author as *"an independent reconstruction of that shape from the public REFramework, not a copy"*; the one reference integration (`fh5vr`) is a single `CMakeLists.txt` | No shipping code by design; 316 illustrative samples, all original |
| Runtime/headset evidence of its own | None — `_agent_reports/` are explicitly offline (*"FH5 was not launched or attached"*) | 70 `[LIVE]` and 28 `[HEADSET]` tagged claims from the fleet |
| Engines | RE Engine, Creation Engine 2, AnvilNext 2.0 | ~20 engine families in ch00 |
| History | 12 commits, 2026-05-31 → 06-05 (six days), untouched since; 14 stars | Continuous; 10 fleet agents committing |
| Licence | MIT, derivative of REFramework with copyright preserved | CC BY 4.0 prose / MIT code |

## Size

| Measure | vrframework | Playbook |
|---|---|---|
| Prose | **58,384** words (17 guides, 1,071–4,020 each) | **301,196** words hand-written (41 docs; generated `coverage.md` excluded) |
| Retrieval layer | none | **58,561** words (atlas + symptom index + pattern catalog + cross-project index) |
| Code | 5,760 lines C++ (23 headers, 19 sources) | 0 shipping; `tools/` are validators |

The striking number: **their entire corpus is the size of the playbook's index.** That is not a put-down — the index exists *because* 300k words cannot be read — but it frames what "more detailed" means: they are more detailed per topic *within the three engines they read*; the playbook is deeper on every topic and wider on every axis.

## Topic by topic

Word counts are theirs → ours for the nearest chapter(s). "Deeper" is by length and specificity, not quality of prose — theirs reads better as a first pass.

| Their guide | Words | Playbook | Words | Notes |
|---|---|---|---|---|
| 01 The Big Picture | 3,550 | ch00 engine profiles, AGENTS.md | 4,104 | Theirs is the better onboarding read |
| 02 Injection & Bootstrap | 2,919 | ch09, ch18 | 22,282 + 9,054 | Playbook ~10× |
| 03 Hooking & Pattern Scanning | 3,960 | ch11, A4 | 21,478 + 1,749 | Playbook ~6×; six-rung anchor ladder, prologue-scan lies, `/OPT:ICF` — nothing found here ch11 lacks |
| 04 Graphics API Interception | 3,672 | ch10 | 6,874 | Comparable shape |
| 05 The Framework Core | 3,189 | — | — | **They have it, we don't ship one**; nearest is ch18 architecture |
| 06 VR Runtime Integration | 3,633 | ch09, `openxr-submission` skill | — | Comparable |
| 07 Frame Timing & Sync | 3,835 | ch09 `#runtime-owns-pacing` | partial | **Theirs is deeper — see below** |
| 08 Stereo Rendering Strategies | 3,911 | a3, stereo rungs R1–R4 | 1,610 + | Their three-strategy cost table (1.4–1.8× / 2× / 2× engine rate) is a good summary; the rungs are finer-grained |
| 09 Camera & Coordinate Systems | 3,764 | ch01, a1 | 5,990 + 1,775 | Their term-by-term basis "sandwich" table is a candidate recipe |
| 10 Submission & the TAA Problem | 3,994 | ch14 | 7,658 | **Direct collision — see below** |
| 11 HUD, UI & Menus | 3,512 | ch04 | 6,345 | Anvil's one-dereference `bIsShowingUI` gate; Starfield's Scaleform-by-hash classifier — both ch04-shaped |
| 12 Input & Motion Controllers | 2,914 | ch03 | 10,140 | Playbook ~3.5× |
| 13 Reading the Engine Object Model | 3,777 | ch11 | — | Covered |
| 14 Engine Tweaks & Quirks | 3,550 | ch00 | 4,104 | Comparable; theirs is per-engine, ours is per-family |
| 15 Multi-Title Architecture | 3,113 | ch18 | 9,054 | Covered |
| 16 Porting Checklist | 4,020 | ch08, ch09:49 ordered gates, `AGENT_RE_WORKFLOW.md` | 14,241 + | Same shape (10 milestones, each with Goal / What to do / **How to verify** / Failure modes); their verify bar is "log it and eyeball", ours is "machine-checkable before promotion" |

## Evidence discipline — the sharpest difference

| | vrframework (58k words) | Playbook (301k words) |
|---|---|---|
| Evidence tags | none | `[SOURCE]` 236 · `[LIVE]` 70 · `[HEADSET]` 28 · `[STATIC]` 17 · `[SPEC]` 9 · `[AUTHOR]` 7 · `[INFERENCE]` 6 |
| "should" | 40 | — |
| "tested" / "measured" / "confirmed" | 1 / 3 / 2 | — |
| "we observed" / "I observed" | 0 / 0 | — |
| "in the headset" | 8 (the TAA one cites no test; the other seven were not audited) | — |

This is not a flaw in their document; it is what the document *is*. Every claim is `SOURCE`-grade by construction — a reading of someone else's shipped code — and the author is candid about it. What it cannot contain is a prediction that a headset later falsified. The playbook has those, and they are its most valuable rows.

## Receipt check — their citations hold

The README promises *"every claim … cited as repo/path/file:line."* Four citations into `mutars/anvilengine2vr/games/valhalla/engine/EngineCameraModule.cpp` were checked against the file fetched raw (210 lines). That file has **one commit, 2026-01-25**, and the repo's `pushed_at` is January — so the file the author read in June is byte-identical to today's, and drift is ruled out.

| Cited | Claimed content | True line | Result |
|---|---|---|---|
| `:58` | `if (vr->is_hmd_active() && farPlane > 1201.f)` | 58 | exact |
| `:106` | `if (vr->is_hmd_active() && !bIsShowingUI)` | 106 | exact |
| `:145` | `EngineCameraModule::onCopyGfxContext` definition | 145 | exact |
| `:11-49` | `memory::calc_projection_fn_addr()` | 15 | in range |

The 8 citations to `E:/Github/vrframework` are self-citations to this repo and resolve in the checkout (`push_stereo_to_adapter` at `VR.cpp:264`, `StereoView.hpp` documents `view[2]` as `world->view`).

**Two false negatives were nearly reported during this check, both the auditor's.** A web summariser returned two contradictory line counts for the same file (281 and 163; it is 210) and placed `:58` on `transform = result;` — wrong. A `grep | head -1` for `:145` hit the `safetyhook::create_inline` registration at line 27 rather than the definition — wrong. Both were caught only by going to the raw bytes. That is [META-013](../docs/pattern-catalog.md#meta-013) and the receipt discipline in [AGENT_RE_WORKFLOW.md](../AGENT_RE_WORKFLOW.md) applied to the reviewer, and it is recorded here because the next reviewer will use the same tools.

## The TAA collision

Their guide 10: *"Any effect that reads frame N-1 is hostile to AFR"* → ghosting, shimmering disparity, *"within a minute, nausea."* No headset test is cited; the fix (per-eye history: snapshot/restore `pastProjections`, `SwapBuffer` ping-pong keyed on `(fc - 1) & 1`) is given in code.

Playbook ch14 [`#velocity-not-temporal`](../docs/14-render-pass-hazard-atlas.md#velocity-not-temporal): PreyVR predicted exactly that, on exactly that reasoning — then a wearer cycled all four AA modes in the headset and **chose the temporal one**. The hazard is velocity-buffer effects, not temporal ones.

Both can be true. Severity is engine- and content-dependent, which is what ch14 already says (*"test them separately rather than banning a category"*). Their fix is the correct fix; the playbook's finding is that one title was tolerable without it. ch14 names "make history per-eye" in one line — **they have the implementation of it.** Their nausea claim is the thing to contribute back.

## What they have that the playbook lacks — ranked

1. **The three-clock frame timeline.** `include/spi/FrameTimeline.hpp` + guide 07: an AFR mod keeps *engine frame*, *render frame* and *presenter frame* in lockstep, derives eye cadence from `presenter % 2`, and recovers drift by skipping a present. Both shipped ports converge on it — Anvil via two engine hooks, Starfield by decoding **NVIDIA Reflex markers** (6/0/1 → engine, 2 → render, 4 → present) inside `setReflexMarkerInternal`. The generalisable insight: **an engine that integrates a latency SDK already emits its frame-phase timeline; hook the markers, not the game loop.** They also record the abandoned `worldTick`/Streamline attempt (*"sometimes give 2 ticks"*) as a dead end. The playbook has `#runtime-owns-pacing` (compositor vs engine cap) and a free-running-counter note at ch09:1720, and **zero** mentions of Reflex or Streamline. Complementary: ours is who owns cadence, theirs is reading the engine's cadence to alternate eyes.
2. **Per-eye temporal history, implemented.** See above.
3. **Creation Engine 2 / Starfield.** The playbook's only total blank among their three engines; CE1 is well covered but only as native-VR titles.
4. **A linear narrative for a newcomer.** Guides 01 → 16 read in order; the playbook deliberately does not.
5. **The eye-view basis sandwich, unpacked term by term** (guide 09, Anvil `:106-114`). Candidate recipe against a1; depth not compared.

## What the playbook has that they lack

- A retrieval layer: 144 patterns with stable IDs, 361 failure rows with cheap discriminators, 257 symptom rows.
- Evidence grading on every claim, and 98 `[LIVE]`/`[HEADSET]` claims they structurally cannot make.
- Falsified predictions, recorded as such.
- Breadth: ~20 engine families, 10 in-house ports, 108 surveyed sources with a per-source coverage ledger.
- Machine-checked integrity: 10 verifier checks, 844 internal anchors, 95,559 reference-maths assertions.

## Licence

MIT, an acknowledged derivative of praydog/REFramework. The two mutars ports it reads are public MIT. The playbook already tracks REFramework and credits praydog's write-ups in ch11. Since the playbook describes rather than copies, nothing is triggered; citing them is straightforward.

## Recommended actions

- **Harvest #1 and #2** into ch09 (timing) and ch14 (per-eye history), graded `[SOURCE]` with the receipts above.
- **Open a CE2/Starfield engine profile** in ch00 from guide 14 and starfield2vr directly (public, 57 commits).
- **Contribute the ch14 counter-example** to their guide 10 — it is the one thing in this comparison that would improve *their* document.
- Registered as source 108; `vehicle: documentation` because it ships no port.
