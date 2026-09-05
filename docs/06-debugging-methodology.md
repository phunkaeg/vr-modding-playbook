# Debugging Methodology

The meta-skill. VR mods fail in ways that are hard to see (it's in a headset, one frame, behind
your face) and easy to mis-attribute. More project time was lost to *method* failures —
testing the wrong build, theorizing instead of measuring — than to any technical problem.

## Make every build self-identify (do this on day one)

The single highest-ROI habit. The first line your injected code logs should be:

```
<mod>.dll loaded. version=<N> built=<date time> path=<actual loaded file path>
```

- **Version + build time** ends "is the fix even in this build?"
- **Loaded file path** ends "which copy got injected?" — when a Release and Debug build, or two
  folders, or a launcher-cached copy exist, you *will* run the wrong one eventually.
- Bump the version string on every behavior-relevant build, mechanically.

*SS2VR lost the better part of a day to a config-key bug that produced a symptom **identical**
to running a stale DLL; the self-ID banner is what finally proved the binary was current and
redirected the search to the real cause. It then immediately paid off again catching a
Debug-vs-Release mismatch.*

**Then extend the banner past your own build, to the environment.** Identifying your binary answers "did
*my* code change?" It cannot answer "did the *world* change?" — and on a VR target a startling amount of
the world sits outside your repo and updates without telling you: the XR runtime, its DLL versions, the
implicit API layers other software installs, driver and headset firmware.

(*BioshockVR's hardest crash had **two** triggers, and both were environmental — a streaming runtime
update moved the DLL the fault address pointed into, and a motion-compensation layer arrived via the
registry from an unrelated tool. Months later the same signature will reappear and the first question
will be "did the environment move?"*)

Log the runtime name **and its file version**, plus the enumerated implicit-layer list
([07](07-engine-integration-safety.md)), in the same header block as your build banner. It costs a few
lines once, and it converts the most expensive question in a stale-incident investigation into something
you read off the top of a log file you already have.

**The same logic applies to your own tools.** [Chapter 08](08-project-process.md) makes the case for
logging a config file's mtime and hash rather than just its values, for the same reason: the thing that
changed is frequently not the thing you edited.

## Measure, don't theorize: the readback probe

When a value the engine computes is wrong, don't reason about what it *should* be — **log what
it actually is.** The pattern that repeatedly cracked SS2VR:

- **Readback probe:** write your value X, then read back where the engine *actually put it*
  (`Object.Position`, the final matrix, the picked id) and log the delta. The delta moving when
  it shouldn't *is* the bug, quantified. Logs of your clean *inputs* can't show it — the bug is
  downstream of them.
- **Multi-candidate residual probe:** when you don't know which reference frame/timing the
  engine uses, reconstruct the result under *every* candidate (frame A now, frame A prev,
  frame B now, frame B prev…) and log the residual of each. The candidate that stays ~0 **is**
  the engine's convention — no guessing, no theory. (*SS2VR's `frameId=(N,Np,D,Dp)` probe ended
  a multi-day wobble investigation in one condump: native-same-tick won at 0.01 units.*)

Five theories cost a week each; one probe costs an afternoon and *ends* the question.

The multi-candidate residual probe is the highest-value twenty lines in this chapter, so here it is
concretely. The shape: enumerate every convention the engine *might* be using, score them all every
frame, and let the winner declare itself.

```cpp
/* Which frame and which tick does the engine actually use? Do not guess -- score
   all of them. SS2VR ended a multi-day wobble hunt with one condump of this. */
enum Cand { FRAME_A_NOW, FRAME_A_PREV, FRAME_B_NOW, FRAME_B_PREV, CAND_N };
static const char *kCandName[CAND_N] =
    { "native-same-tick", "native-prev-tick", "derived-same-tick", "derived-prev-tick" };

struct Residual {
    double sum = 0, worst = 0;
    uint32_t n = 0;
    void add(double r) { sum += r; if (r > worst) worst = r; ++n; }
    double mean() const { return n ? sum / n : 0.0; }
};
static Residual g_res[CAND_N];

void ProbeTick(const Frames& f, const Vec3& engineActual)
{
    /* Reconstruct the engine's result under every candidate convention. */
    const Vec3 pred[CAND_N] = {
        Reconstruct(f.aNow),  Reconstruct(f.aPrev),
        Reconstruct(f.bNow),  Reconstruct(f.bPrev),
    };

    for (int c = 0; c < CAND_N; ++c)
        g_res[c].add(Length(pred[c] - engineActual));
}

void ProbeReport()
{
    int best = 0;
    for (int c = 1; c < CAND_N; ++c)
        if (g_res[c].mean() < g_res[best].mean()) best = c;

    for (int c = 0; c < CAND_N; ++c)
        Log("residual %-18s mean %9.4f  worst %9.4f  n=%u%s",
            kCandName[c], g_res[c].mean(), g_res[c].worst, g_res[c].n,
            c == best ? "   <== WINNER" : "");

    /* Two candidates within noise of each other is NOT an answer: the probe has
       not separated them, and picking one is a coin flip you will pay for later. */
    double second = 1e30;
    for (int c = 0; c < CAND_N; ++c)
        if (c != best && g_res[c].mean() < second) second = g_res[c].mean();
    if (second < g_res[best].mean() * 3.0)
        Log("INCONCLUSIVE: best and runner-up are within 3x -- add a motion case "
            "that separates them (fast yaw, or a frame with translation only)");
}
```

Three things make it work, and all three are easy to leave out:

- **`worst` alongside `mean`.** A candidate that is right 99% of the time and catastrophically wrong on
  fast rotation has a good mean. The worst case is what the user feels.
- **The explicit `INCONCLUSIVE` branch.** Without it, the probe always names a winner — including when
  the test never exercised the difference. That is the same failure as reading a matcher's `score`
  without its `total_matches` ([11](11-re-anchoring-and-discovery.md)).
- **Exercising the discriminating motion.** Standing still, every candidate scores ~0. Yaw fast.

The result to aim for is unambiguous: *SS2VR's `frameId=(N,Np,D,Dp)` probe returned native-same-tick at
0.01 units against runners-up an order of magnitude worse* — a number that ends the discussion rather
than informing it.

**Dump every stage of the pipeline at the same instant, paired.** A defect visible only in the final
composited image is ambiguous about which of N stages introduced it — and you will burn builds guessing.
(*BioshockVR's `depthpairdump` wrote the private-eye colour buffer, the private-eye depth buffer, and the
final post-blit XR eye texture from one hotkey press. The holes were already present in the private-eye
**colour** dump, which killed the entire blit-stage theory in one capture and redirected the search
upstream.*) One hotkey, N synchronised artefacts, labelled by stage — this converts "which stage is
broken" from a hypothesis into a comparison.

**Pre-register the decision rule — including the "inconclusive" branch — before you run the probe.** Write
down, in advance, the exact observation that confirms, the one that refutes, and the explicit third
outcome. (*PreyVR's live protocols state the byte pattern meaning "retained," the pattern that "closes
negative," and reserve a third branch verbatim: "ambiguous — record what was seen and do not promote
either way. **An honest null is a result; a guessed layout is not.**" All three protocols were then run and
written up against those pre-stated branches, including one that refuted its own hypothesis — a candidate
structure turned out to be `ID3D11Query` GPU-timing objects rather than view data.*) The point is not
ceremony: it is that a rule written after seeing the data can be reshaped by the data without anyone
noticing, including you.

**And if you are timing GPU work, stop the clock on completion, not submission.** `Flush`, `Present` and
command-buffer submits return when the driver has *queued* the work. (*DishonoredVR's interop probe
originally timed to `CopyResource` + `Flush`; adding a `D3D11_QUERY_EVENT` and polling until complete split
the number into `completed` — 0.224 ms median, 0.291–0.397 ms p95 — versus `enqueue` at 0.196 ms p95. The
two diverge, and only the first is real.*) The fix is the same in every API: insert a completion primitive
(fence, event query, sync object), wait on it, then stop the clock.

## A config value is not evidence that a call happens {#config-is-not-a-call}

Mirror's Edge VR established "the game really is Direct3D 9" with a **pass-through proxy that forwards
every export and changes nothing**, and was right to treat it as a real question rather than a
formality: `[SOURCE]`

> the executable delay-loads `d3d10.dll` and `dxgi.dll`, so it has a DX10 path, and **a config value is
> not evidence that a call happens.**

`TdEngine.ini` said `AllowD3D10=False`. That is a statement of intent by whoever wrote the file, not an
observation of the running process - and the presence of a delay-load import proves the other path
*exists*. The two together are exactly the conditions under which a project builds a renderer bridge for
the wrong API.

**The cheapest possible instrument settles it.** A proxy that forwards everything and logs entry points
answers "which API, which entry, which SDK version, which real library" in one launch and cannot change
behaviour, because it changes nothing. Do that before the first architectural decision, not after.

## Coarse switches before fine instruments — and know when to stop toggling

Before instrumenting individual draws or shaders, build a **reversible switch for the whole stage**. A
negative result then eliminates an entire hypothesis class in one test.

- *SOMAVR* wired one key to bypass the entire post-effect composite. Toggling it changed contrast only
  and left the core eye-mismatch untouched — ruling out the whole post chain in a single test and
  redirecting to world/deferred-light rendering, where the bug actually was.
- *BioshockVR* built a sharper wedge for a specifically stereo question: one key forced **both** the
  render FOV and the submitted XR projection to the same *centered* value, changing nothing else. An
  artifact that only appears under asymmetric FOV implicates your projection reconstruction; an artifact
  **unchanged** in centered mode implicates a mono/centre-camera resource and rules projection maths out
  entirely. That is a reusable stereo diagnostic, not a one-off.
- When you don't know a sign or axis convention, **bracket it with symmetric opposite extremes** rather
  than testing one guess. Two failures that are symmetric tell you the magnitude is right and the frame
  is wrong; one failure tells you nothing.

**The counterweight, which matters just as much: when a hypothesis survives several A/B toggles without
dying, stop toggling and read the state.** Toggles test *behaviour*; they cannot settle questions about
*state*. (*BioshockVR spent three builds alternately skipping and mono-falling-back a suspect class of
draws with mixed, hard-to-read results. Direct output-merger telemetry then showed those draws had
`rt0WriteMask=0x0` and `depthWriteMask=0` — **they wrote nothing at all**. A red herring that no further
toggle could have exonerated.*) Read bind flags, write masks and resource IDs directly and the ambiguity
ends.

## Absence of errors is not evidence

Concretely: the counter you need is not "did it fail" but **"how many times was it offered the chance to
run, and how many times did it act"**. A hook that is never reached and a hook that is reached and
declines are indistinguishable in the logs unless you count both.

```c
/* Three counters, not one. The pair (offered, acted) is what makes silence readable. */
typedef struct {
    const char    *name;
    _Atomic uint64_t offered;   /* the seam was hit at all                     */
    _Atomic uint64_t acted;     /* we actually did the thing                   */
    _Atomic uint64_t declined;  /* we hit it, and chose not to -- with reasons */
    _Atomic uint64_t reason[8];
} seam_counter;

#define SEAM_OFFER(s)         atomic_fetch_add(&(s)->offered, 1)
#define SEAM_ACT(s)           atomic_fetch_add(&(s)->acted, 1)
#define SEAM_DECLINE(s, why)  (atomic_fetch_add(&(s)->declined, 1), \
                               atomic_fetch_add(&(s)->reason[(why)], 1))

void seam_report(const seam_counter *s, const char *const *reasons, int nreasons)
{
    uint64_t o = atomic_load(&s->offered), a = atomic_load(&s->acted);

    if (o == 0) {                       /* THE case a single counter cannot show */
        log_warn("%s: NEVER REACHED -- the hook is not installed, or this seam "
                 "is not on the live path. Do not debug the body.", s->name);
        return;
    }
    log_info("%s: offered %llu, acted %llu (%.1f%%), declined %llu",
             s->name, o, a, 100.0 * (double)a / (double)o,
             atomic_load(&s->declined));
    for (int i = 0; i < nreasons; ++i) {
        uint64_t r = atomic_load(&s->reason[i]);
        if (r) log_info("    declined[%s] = %llu", reasons[i], r);
    }
}
```

`offered == 0` is the reading that matters, and it is precisely the one a lone success counter cannot
produce. It redirects you from *"why is my transform wrong"* to *"my code never ran"* — which is a
different chapter ([A hook that "does nothing" may simply never be reached](#a-hook-that-does-nothing-may-simply-never-be-reached)).

Print the report on a hotkey **and** at shutdown. A counter you have to attach a debugger to read is a
counter you will not read.

A clean log means nothing crashed. It does not mean the thing you are testing ran. Any guarded or
optional path — a shader replace, a hook override, a patched draw — can silently degrade to a no-op
fallback while producing perfectly healthy output.

(*BioshockVR shipped a build whose HMD image was visibly mono, with the user reporting "zero shader
errors." The counters told the real story: `AttemptTotal=2137915` against `AppliedTotal=1765`. A broad
mono-depth fallback added that build was swallowing essentially every draw before the stereo mutation
could run. Clean logs and a live submit loop meant "nothing threw," not "the feature executed."*)

**Count applied *and* attempted for the specific mechanism under test, and read the ratio.** It is the
only signal that distinguishes "working" from "silently bypassed," and it costs two counters.

**The same trap has a second form, and it catches *guards* rather than features: a quiet run is not
evidence a guard works if the thing it guards against never fired.** Intermittent, trigger-driven faults
make wall-clock stability meaningless. (*BioshockVR's crash fired at frame 1 in one dump and frame 35 in
another, driven by headset focus changes, reference-space changes and sleep/wake — so a clean session
proves nothing unless you know how many of those events it actually survived. An earlier build "looked
fixed" for exactly this reason.*) **Count the trigger opportunities, not the minutes** — emit
`focusEvents=`, `referenceSpaceChanges=`, `sessionStateTransitions=` in the frame summary. Without them,
"the guard works" and "the trigger never happened" produce identical logs. This is the
same discipline as reading back after a mutation ([above](#falsify-your-own-hypothesis-before-shipping-a-fix)),
applied to a whole code path rather than a single value.

## Capture a log containing the failure *and* a success in the same session

A log of failures tells you what a broken run looks like. It cannot tell you what is **missing**, because
you have nothing to subtract. The diagnostic jump happens when one capture holds both.

(*Halo-MCC-VR had a long-standing bug where ODST stopped loading levels after some number of load/exit
cycles. **Four theories had been refuted and none replaced, because no log of the real event existed.**
One session finally captured three consecutive failed loads **and** three successful ones.*)

The discriminator fell out immediately, and it is visible only in the comparison:

```text
SUCCESSFUL load:  "camera WAIT" polls repeatedly, tailValid alternating 1 -> 0 -> 1
                  over 400-900 ms   (the engine's camera is ticking)
                  -> "stable stock camera detected" -> arms

FAILED load:      exactly ONE "WAIT" line (tailValid=1), then silence.
                  The tail never changes again. No heartbeat is ever published.
                  1.7-3 s later all six game modules reload = the bounce to menu.
```

Their conclusion — *"the level therefore dies before the game's own camera loop ever runs"* — **exonerated
the mod**, which every previous theory had been trying to convict. The mod installs cleanly, logs once,
and is silent for the whole window because there is nothing to hook into.

**Engineer the capture to contain both.** If the failure is intermittent, log continuously across many
cycles rather than starting the log when you suspect trouble; keep the artifact somewhere your own
`.gitignore` will not lose it. A single session containing both outcomes is worth more than twenty
sessions of failures.

### Make "never happened" legible

Their teardown diagnostic reported `heartbeat age = 18446744073709551615`. That is `UINT64_MAX` — an
unsigned subtraction from a timestamp that was never set. It reads as an absurd number rather than as
information, and only means "never" if you recognise it.

**Print the sentinel as words.** `heartbeat age = NEVER` costs nothing and survives being read by
someone who has not seen that number before — including you, in six weeks.

## Log raw bit patterns, not formatted floats

When you need to prove that *this* value is *that* value, print the bits. Formatted floats round, and a
comparison of two rounded values yields "close enough, probably the same" — which is a hypothesis, not a
finding.

(*FC2VR proved a state-contamination bug by exact bit match: the right eye's expected-primary camera was
`0x454D288F 0x4493E586 0x442D57EE`, identical to a transient value logged 41 sequence numbers earlier
during the left eye's camera rebuild, and different from the stock camera logged before that. Printed as
`3282.53, 1183.17, 693.37` it would have been suggestive; printed as bits it was an identity proof. See
[17](17-teardown-fc2vr-native-stereo.md).*)

Pair it with a **monotonic sequence number** on every event. "The same value appeared at seq 623770 and
was still there at 623811" is a causal chain; two timestamps a few milliseconds apart are not.

## Ship the coverage line: make the instrument say what it CANNOT see {#coverage-line}

The section below is about reading an index's silence correctly. This is the same problem solved from
the instrument's side, and Halo-MCC-VR's census does it as a shipped feature. `[SOURCE]`

Its diagnostic emits, alongside the data, **a periodic parity-coverage line that distinguishes observed
systems from systems the current proven hooks cannot observe** - and names the unobservable ones
explicitly:

```
NOT OBSERVABLE FROM CURRENT PROVEN HOOKS
```

for vehicle seat/camera/projectile ownership, cutscene state, and the native HUD-layout consumer. A
reader of that log cannot mistake "absent from the census" for "absent from the game", because the
instrument itself draws the boundary.

Two more rules from the same design:

- **A bounded table that overflows is a refusal, not a degradation.** Their identity table holds 32
  entries and the census is only complete when overflow reports zero: *"An overflow is a diagnostic
  refusal, not permission to merge IDs."* A truncating instrument that keeps reporting is producing a
  subset labelled as a total.
- **Coincidence in a diagnostic is not authorization.** *"Static or visual coincidence in this
  diagnostic is not authorization to copy a Halo 3, ODST, or Reach offset."* Worth stating out loud on
  any multi-title or multi-build project, because the census is exactly where two titles look alike.

## An empty result from a partial index is not a negative result {#partial-index-silence}

The section below is about what a knowledge graph is *good* at. This is about what its **silence**
means, and it cost this fleet five days. `[LIVE]`

Six projects carried an instruction to query a shared cross-engine graph for *"has another project hit
this?"*. Measured on 2026-09-01, that graph holds **1,328 nodes and zero edges**, and indexes **three of
eight** in-house projects. The terms that mattered most returned nothing at all - not because nobody had
hit them, but because neither the projects nor the topics were in it:

```
Swat4  0    Dishonored  0    FarCry  0    Prey  0    Sims4  0
9On12  0    D3D12       0    adapterLuid  0    xr-sim  0
```

A DishonoredVR session then spent five days building an architecture argument from first principles
**that Swat4-VR had already falsified by experiment** - and the query written to prevent exactly that
would have come back empty and read as confirmation.

> **Silence from an index means "not indexed", never "it does not exist."**

That is [the confident zero](#instrument-honesty) wearing a different hat: an instrument reporting a
clean result from a region it never covered. The discipline is the same one this chapter applies to
every other instrument:

- **Ask what the index covers before you trust what it does not return.** One coverage probe -
  grep the corpus for a term you *know* is in it and one you know is not - takes a minute and
  calibrates every later query.
- **Write the coverage next to the query**, not in the index's own README. The person who needs the
  caveat is reading the command, not the tool's documentation.
- **A citation is a door, not an answer.** The same session had *already quoted* the sibling project by
  name as prior art and moved on without opening its tree. **A good citation feels like an answer**,
  which is precisely why it stops the search. If a project is named as having solved something, open
  that project's `FAILURE_REGISTRY.md` - the write-up is the deliverable, the citation is not.

## A knowledge graph is bad at synthesis and good at structural questions

Worth recording as a correction. Earlier work in this fleet concluded that a knowledge graph over a
documentation corpus **did not beat hand-authored synthesis** — the paginated read was where the insight
came from, and the graph mostly restated what a good index already said. That finding stands for
*synthesis*.

It does not generalise to *structure*. PreyVR built a graph over their code-plus-docs corpus and ran
centrality on it, and it produced a result their intuition had got backwards — the busiest node in a
dependency lane was not the load-bearing one
([07](07-engine-integration-safety.md#check-articulation-points-not-degree)).

**The distinction is what the question is made of:**

| Question | Graph? |
|---|---|
| *"What did we learn about X?"* | **No.** A maintained index and a careful read win |
| *"What is the single writer of this value?"* | **Yes** |
| *"Which node disconnects this lane if removed?"* | **Yes** — you cannot eyeball articulation points |
| *"What reaches this function transitively?"* | **Yes** |
| *"Has anyone here hit this before?"* | **No.** That is what a cross-project index is for |

**Reach for a graph when the question is about reachability, cut vertices or transitive closure** — the
things that are tedious and error-prone by hand and exact once computed. Do not reach for it to be told
what your own notes say.

### Merging graphs is a union; reconciling them is a separate step {#graph-cross-source-limit}

The fleet built a three-project documentation corpus so that community detection would surface where
three engines hit the *same* problem. **The merge step does not do that, and the reason is worth knowing
before you build on one.** `[LIVE]`

`graphify merge-graphs` over per-project graphs of SS2VR, BioshockVR and SOMAVR produced **exactly the
sum of its inputs** - 1328 nodes, 616 links, and not one edge between projects. A query seeded in one
project's nodes could never reach another's. Asked *"which projects hit problems with the cull camera or
culling?"* it returned 22 nodes, all SS2VR.

**A merge combines node sets. It does not discover that two projects describe the same concept.** That
is entity resolution, and nothing in the pipeline performs it.

#### Exact matching cannot substitute

Across 1328 nodes, only **7 normalised labels recurred across projects - and 5 were document filenames**
(`build history`, `decision log`). Meanwhile **74 concept tokens appeared in all three**: stereo, camera,
pose, viewmodel, controller, comfort, interaction.

**The concepts recur; the vocabulary does not.** Each project names things in its own local dialect -
`FEATURE.ROOMSCALE_BODY_RECONCILIATION`, `Roomscale Crouch Research`, and
`Native MoveSmooth can own collision-aware roomscale reconciliation` are one concept in three houses.
String matching finds none of them.

#### The reconciliation pass, and what it costs

`tools/reconcile_graphs.py` reads the node **labels** - about 1300 short strings, not 700k words of
source - and asks a model which ones from different projects denote the same engineering concept. It is
cheap because the expensive reading is already banked in the per-project graphs.

| | Union | Reconciled |
|---|---|---|
| Links | 616 | **651** (35 cross-project) |
| Components | 724 | **696** |
| Largest component | 52 (3%) | **149 (11%)** |
| Cross-project query | impossible | **works** |

Cost: **$0.013**. Fifteen concepts linked, including frustum/culling, stereo strategy, depth submission,
HUD layering, viewmodel posing, interaction raycasting, haptics, recentre and roomscale. The same culling
query afterwards reaches SS2VR *and* BioshockVR documents by traversing `same_concept_as` edges.

**Validate every returned label against the real node set.** On one run the model invented five labels
that exist in no graph; all five were rejected before an edge was emitted. A false bridge is worse than a
missing one - it creates a path between two projects that never solved the same problem, and every
downstream query inherits it.

#### Two traps, both mine

**Coverage is the whole game, and a cautious prompt under-delivers.** A first pass produced 10 groups
covering 2% of nodes - the mechanism worked and the culling query still failed, because culling was not
among the ten. Telling the model to be exhaustive and naming the concept areas to sweep took it to 15
groups and made the query work. **A reconciliation that runs is not a reconciliation that covers.**

**On a reasoning model, `max_tokens` is a shared budget, not an output budget.** The exhaustive prompt
first returned truncated JSON. Raising `max_tokens` made it *worse*. The usage told the real story:
`prompt 14,902 + completion 641 = 15,543` against a `total` of **31,268** - the missing **15,725 were
reasoning tokens**, with `finish_reason` of `length`. Setting `reasoning_effort` low fixed it, which is
exactly what graphify's own gemini config already did. **When `prompt + completion` does not equal
`total`, the gap is thinking, and no output limit will move it.**

### Running one without burning tokens, and how to tell it failed {#graph-build-method}

The section above says *when* to reach for a graph. This is *how* to build one, written after a run that
technically succeeded and produced something worthless. `[LIVE]`

**One graph per project, or one graph per corpus?** Point `graphify extract` at a path and it does both
halves in one pass — deterministic AST over code (free) and LLM extraction over docs (billed). So:

| You point it at | You get |
|---|---|
| A **project root** | **One integrated graph**, code and docs together, with edges between a documented concept and the symbol it describes. This is what PreyVR did, and it is what made the centrality result above possible. |
| A **docs-only corpus** | A docs-only graph. Correct for cross-project comparison, and it forfeits the free half entirely. |

**For a single project, integrate.** The value in the table above is structural — reachability, cut
vertices, transitive closure — and those questions only span code. A docs-only graph over one project
answers "what did we learn about X", which is the row the table says a graph loses.

#### Extract per project, then merge — never one big corpus

Graphify derives a node ID from source path plus entity name. Across a multi-project corpus those
collide, and **the loser is silently dropped**:

```text
node 'ss2vr_interact_nut' is minted by two different files - keeping ... from BUILD_HISTORY.md,
dropping ... from VR_FINDINGS_INDEX.md ... the dropped node is lost
```

Its own advice is to extract per subfolder and combine with `graphify merge-graphs`. That fixes three
things at once: IDs are scoped per project so collisions cannot happen, each project's graph is
independently checkable **before** it is merged, and a project that fails can be re-run alone.

#### Price the API limits before choosing a backend, not after

A free tier is not a cheap paid tier, and the difference is structural. Gemini's free tier enforces
**two separate quotas**, and only one of them can be engineered around: `[LIVE]`

| Quota | Limit | Can you work around it? |
|---|---|---|
| `...InputTokensPerModelPerMinute` | 250,000 / minute | **Yes** - `--max-concurrency 1` serialises requests |
| `GenerateRequestsPerDayPerProjectPerModel` | **20 requests / day** | **No** |

The second is the wall. Extraction costs **one request per chunk**, and a 141-file corpus chunks into
about 25 - so a single full extraction **cannot complete in one day** on a free tier, however it is
scheduled. That was learned the expensive way: a first pass lost 8 of 25 chunks to per-minute throttling,
and the retry meant to repair it found the daily allowance already spent.

Worse, the two limits pull in opposite directions. Packing more files per request (a larger
`--token-budget`) uses fewer requests and fits the daily cap - and directly worsens the omission failure
below. Fewer files per request extracts better and exhausts the daily allowance sooner.

**If the corpus needs more requests than the daily allowance, enable billing and stop optimising.** The
run that hit this wall was estimated at **$0.67** in paid pricing for 1.09 M input tokens. An afternoon
spent scheduling around a 20-request ceiling costs more than the API does.

#### A successful response can still silently omit most of its input

Separate from any quota, and the failure that produced the worst result:

```text
WARNING: 21/25 dispatched file(s) produced no nodes and are absent from the graph ...
The model returned a response but omitted them; a re-run will retry them.
```

No error and no throttling - 65,877 tokens in, every request accepted. The model simply did not mention
21 of the 25 documents it was handed. Chunk packing is the likely driver: the omitted files were the
*small* ones (1.2k-9.3k words), while the files that extracted cleanly were large enough to occupy a
chunk nearly alone (23k-53k words). A long multi-document prompt gets partial attention, and nothing in
the exit code says so.

**Treat "files dispatched" and "files represented in the graph" as two numbers, and compare them.**
Graphify prints that warning; a home-grown pipeline usually will not.

#### Two checks before you believe a graph

Extraction failures do not fail the command. Exit code 0 wrote this graph:

```text
263 nodes, 137 links, 130 communities   from 702,007 words
```

**Check connectivity.** 130 communities across 263 nodes means roughly two nodes each — community
detection found nothing because there was no structure to find:

| Measure | Value | Reading |
|---|---|---|
| Connected components | 128 | Fragments, not a graph |
| Largest component | 33 nodes (13%) | No backbone |
| Isolated, zero edges | 83 (32%) | A third of the nodes relate to nothing |

A usable graph has most of its mass in one component. If the largest component is a small minority, stop.

**Check yield per source, against input.** The aggregate looked survivable; the per-project split did not:

```text
ss2vr        180 nodes / 360,723 words = 5.0 per 10k
bioshockvr    72 nodes / 234,367 words = 3.1 per 10k
somavr         7 nodes / 111,226 words = 0.6 per 10k
```

An 8x yield gap on comparable prose is not proportionality, it is near-total loss for that project — and
a cross-project graph missing one of three projects will answer "where do these engines disagree" with
confident nonsense. **Normalise node count by input size per source and compare.** A merged graph hides
this; per-project graphs cannot.

#### What it costs

That run: 1,093,011 tokens in, 42,307 out — a **26:1 ratio**, because extraction reads everything and
emits compact JSON. Input volume is the entire cost model. Excluding an already-structured index layer
from the corpus is worth more than any flag, and a docs-only corpus gets no free AST half at all.

## Some counters are only meaningful as a pair

A single counter tells you a rate. **Two counters that should move together tell you when your model of
the system is wrong** — and the discrepancy is often visible long before any symptom is.

(*FC2VR ran `XR_REQUEST=298, XR_PAIR=215, XR_SKIP=84` — and separately `MonoQuadAnchored=2`. Eighty-four
eye rejections should have produced far more than two mono anchors. Neither number is alarming alone;
together they said the rejected frames were going somewhere unaccounted for, which is exactly what was
happening.*)

When you add a counter, ask what *other* counter it should track, and log the pair. The
`offered`/`acted` pattern above is one instance of this; `requested`/`completed`/`skipped` triples that
must sum are another. **A conservation law you can check every frame is worth more than three counters
you read individually.**

## The measurement was right; the attribution was wrong {#wrong-attribution}

A distinct failure from [an instrument that cannot measure](#instrument-honesty). Here the number is
**correct** — it is simply not a property of the thing you were looking at. It is the most common way a
careful person ships a wrong conclusion, because every step feels rigorous.

Four from a single day in this fleet, all by the same author, all reported as fact before being caught:

| Reported | The number was | What it actually measured |
|---|---|---|
| "All validators pass" | The exit code of `... \| tail -1` | **`tail`'s** exit status. A shell pipeline returns the *last* command's code, so a failing checker printed its error and the chain sailed past |
| "Only 1 of 43 rows is affected" | A grep count over notes | Rows whose text *said* they were affected — not rows that *were*. The regex could only find the ones already labelled |
| "The scan regressed to 321 s" | A wall-clock timing | A machine running a graphify extraction and eleven agents. Measured idle: **9 s** |
| "48 stuck processes — a leak" | `Get-Process python` | The user's MCP servers, idle by design. None were mine |

**The shape is always the same: a real measurement, attached to the nearest plausible cause.**

### Four questions that would have caught all four

Before reporting a measurement as a property of X:

1. **Does the instrument measure the property, or a proxy?** `tail`'s exit code is a proxy for the
   checker's, and a bad one.
2. **Does absence of a signal mean absence of the thing, or absence of measurement?** This is
   [TEST-002](pattern-catalog.md#test-002) wearing different clothes — a query that finds only
   self-declaring cases cannot bound the non-declaring ones.
3. **What else was running?** A timing taken under contention measures the contention. If you cannot
   quiet the machine, measure the same thing twice under different loads and compare.
4. **Is the population what you assume?** "48 python processes" is only alarming if they are *your*
   python processes. Check ownership before checking count.

### Why this one is hard to catch

The three other failure modes in this chapter announce themselves eventually — a check that only prints
gets found, a sampler with poor coverage gets audited, an unstressed optimistic claim gets refuted. **A
correct number attached to a wrong cause produces confident, specific, wrong action** and survives review,
because reviewers check the number.

The tell is that **the fix does not work**. If a change that should have resolved the measurement leaves
it unmoved, suspect the attribution before suspecting the fix. See
[META-009](pattern-catalog.md#meta-009).

## An instrument that reports success when it failed to measure {#instrument-honesty}

BioShock-Trilogy-VR's FOV watch reported the number of lenses it saw in the constant-buffer stream, and
a reading of `lenses == 1` was taken as "the second lens is gone, the fix worked." It was not. The
sampler saw about **12 of 400-600 constant buffers**, and the pass it cared about was roughly 17 of
them - so **absence of a second lens was the ordinary case, not evidence of anything.** Reading it as
evidence produced **six false positives in a row**. `[SOURCE]`

> **An instrument that reports the SUCCESS state when it fails to measure is worse than no instrument.**

It is worse because no instrument leaves you knowing you are blind, while this one manufactures
agreement with whatever you just did. Note the asymmetry: had a spurious *second* lens appeared, they
would have investigated. A sampling gap can only ever fake the good news.

Their fix was not better coverage - **two attempts at that are recorded as dead ends in the code
itself**: a head-slot reservation (the pass moves between captures) and a rotating stride phase
(correct, and 20x the frame time, because copying from a different set of dynamic buffers each interval
defeats the driver's fast path). What they changed instead was the *header*, which now states what the
number is worth, and the acceptance criterion, which became a frame dump that sees every block.

**Where a cheap check cannot be made sound, say what it is worth rather than making it look sound.**
Coverage was the wrong goal; honesty about coverage was the right one. See
[TEST-002](pattern-catalog.md#test-002).

### A diagnostic on the present path gets a hard rate limit, not just a change test

The same log line was guarded by a change test, which was fine until sampling became intermittent - then
it flickered, fired at present rate, took the game to 40 fps and wedged it. A diagnostic became the
performance bug.

> **Change tests are policy, and policies get edited. The floor is the safety net.**

Rate-limit anything on the present path by construction, in addition to whatever cleverness decides
that it is interesting.

## A determinant check accepts a mirrored basis {#mirrored-basis}

The standard sanity check on a rotation basis is that its determinant is about 1. **That check passes for
a mirrored basis**, because a reflection composed with a rotation still has magnitude 1 - and `|det| = 1`
is what most implementations actually test. `[SOURCE]`

A mirrored basis is not a small error. Left and right are swapped, so hand tracking is inverted, aim goes
the wrong way off-centre, and stereo separation reverses - all while every orthonormality assertion
passes.

Test **handedness**, not just magnitude:

```text
det(M) == +1          not |det(M)| ~= 1
cross(forward, left) == up     the basis is right-handed in YOUR convention
```

One project in this survey pairs those two assertions, links the same object file into an **offline test
binary that must reject four named wrong composition orderings**, re-runs the check at DLL load, and
degrades to position-only tracking after 30 consecutive rejections rather than shipping a mirrored world.

That last part is the transferable half: **a runtime check needs a defined response.** A check that
detects a mirrored basis and then proceeds anyway is a log line, not a guard.

## Answer the second-pass question in a debugger, before you write a hook {#double-call-in-debugger}

[Chapter 17's first gate](17-teardown-fc2vr-native-stereo.md) asks whether the world render can be
invoked more than once per frame, and it is the most expensive question in a native-stereo project -
several fleet projects have it open right now. Psychonauts VR answered it **from x32dbg, with no mod
code at all**, in one session. `[SOURCE]`

The alternative they rejected is worth naming: manually auditing the function's *"89 combined nested
helper calls"*. An empirical answer is cheaper and stronger.

**One caveat they discovered later, and it is a general one.** The function was believed at the time to
be the outermost once-per-frame render dispatcher. Six sessions on, a full decompile showed it is **the
camera's own update tick and not a renderer at all** - after two further sessions had been spent walking
a neighbouring chain that turned out to be a world-space icon and HUD-marker overlay renderer. **The
re-entrancy result survived the reclassification**, because the test asks whether the function tolerates
a second call and nothing more. Do not let a safety result stand in for an identity claim: prove
separately what the function *is*, or you will build on the label rather than the evidence.

### The protocol

At the entry breakpoint of the function you intend to drive, per real frame:

1. **Break at the prologue, before `push ebp` executes.** The breakpoint sits on the `55 8B EC` bytes,
   so `esp` still points at what the real `call` instruction pushed - which is how you read the return
   address `ra` from `[esp]`. Break one instruction later and that is gone.
2. **Snapshot every GPR and `EFLAGS`.** For a function with no stack-passed arguments, *that register
   set **is** the arguments* - there is nothing else to reproduce.
3. **Run the real, unmodified call to completion** with a single-shot breakpoint planted at `ra`.
   Confirm it lands there with the stack popped.
4. **Push `ra` again, restore the snapshot, set `EIP` to the entry.** That is a second, fully
   independent invocation with the exact incoming state of the first.
5. **Run it to completion the same way**, confirming it also lands at `ra` with `esp` rebalanced.
6. **Let the game continue on the second call's state** - which is what a real dual-render hook does,
   since the caller only ever sees the last call's outcome.

### What to record, and the baseline that makes it evidence

Their fifteen consecutive double-called frames: `landed1_ok` 15/15, `landed2_ok` 15/15, `esp_balanced`
15/15, identical entry registers on every hit, a single fixed call site, and the synthetic call
returning **the same value as the real one every time**.

**The baseline is the part that turns "it did not crash" into a result.** They measured per-hit cadence
*before* and *after* the double-call window - `0.2029-0.2054 s` in both, statistically
indistinguishable - which rules out lasting damage: no growing lag, no degraded performance, no delayed
crash. A safety test with no after-baseline cannot tell "safe" from "broke something that has not
surfaced yet".

**And explain your anomalies rather than reporting them.** The synthetic call measured ~2x the real
one's duration, which reads exactly like the game doing twice the work. It was not: one extra retry
round-trip inside the debugger's own run-to-address helper, confirmed by the one hit that needed no
retry and came in at 1x. **In a debugger-driven measurement, most of what you are timing is the
debugger** - see [the instrument that changed its subject](#quantify-the-artifact).

Watch for: double-speed animation, crashes, hangs, corrupted stack or registers, and timing pathology.
See [TEST-009](pattern-catalog.md#test-009).

## Turn the visual bug into a number before you argue about it {#quantify-the-artifact}

"There is a black void behind the player" is a description. It cannot be trended, it cannot be compared
across builds, and two people can disagree about it forever. Psychonauts VR's void investigation ran for
dozens of sessions on screenshots and closed in one session once it became a scalar. `[SOURCE]`

Their metric was the share of near-black pixels, swept across camera yaw:

| yaw | 0 | 5 | 30 | 60 | 90 | 180 |
|---|---|---|---|---|---|---|
| near-black | 3.80% | 2.89% | 2.83% | 2.61% | **2.58%** | 2.44% |

**Turning the camera yields *less* black than not turning it** - so culling follows the camera completely
and there is no void. That verdict is unarguable in a way no screenshot is, and three properties make it
so: the trend is **monotone** across the sweep, the effect is **reversible** (3.80 to 2.58 to 3.88), and
the measurement is **bit-stable** (three dumps 1.5 s apart identical). They also explain the one outlier
rather than dropping it - 180 degrees points into terrain from a low chase-cam, so it is degenerate for a
reason unrelated to the transform.

**Reach for a scalar the moment a visual argument has run twice.** Percentage of near-black, mean
luminance difference between eyes, count of pixels differing by more than N - the metric barely matters
next to being able to plot it.

### And get a positive control before you trust a debug visualisation

The same project's other lesson, arrived at independently and worth pairing with
[TEST-006](pattern-catalog.md#test-006): they tested **four** different debug-menu visual toggles across
two sessions looking for collision geometry. All four showed no visible effect - and rather than reading
that as four negative results, they read it as **convergent evidence that the build's debug display
system does not work at all**, matching a caveat on the game's own documentation wiki.

> **Confirm a debug-menu option is actually rendering something (a positive control) before trusting more
> results from this menu.**

A borrowed debug facility is an instrument you did not write and cannot see inside. Until one of its
toggles has visibly changed something you expected, every clean result from it is worthless - and the
cost of learning that late is measured in sessions.

## A harness run that cannot prove itself must fail, not pass {#silence-is-not-a-pass}

The [section below](#self-proving-instrument) is about the checker. This is about the **run**, and the
fleet reached it twice in one day from opposite directions. `[SOURCE]`

Swat4-VR: *"a run that cannot prove itself now fails, and the gate is tested both ways."*
DishonoredVR: *"give a scripted run a verdict, and refuse to call silence a pass"*, alongside *"let a
test assert that something happened, without a person looking."*

**An automated run has three outcomes, and most harnesses only implement two.** Pass, fail, and **could
not tell** - and the third one is the common case: the game never reached the state, the capture was
empty, the script drove a menu that was not on screen, the log line never appeared. A harness that maps
"no failure observed" onto pass converts every one of those into a green result, and green results are
the ones nobody re-examines.

**Make the evidence a precondition of the verdict.** The run should carry what it saw - a frame that
says what it is, a counter that moved, a state file that advanced - and a run that produces none of
those returns *indeterminate*, which is a failure of the run rather than of the subject.

Two details worth copying from those two projects:

- **Test the gate in both directions.** Swat4's is *"tested both ways"* - a run that should pass does,
  and a run that should fail does. A gate only ever exercised on good input is the
  [instrument that has never seen the fault](#self-proving-instrument).
- **Make the captured frame self-describing.** DishonoredVR's *"make a captured frame say what it is"* -
  the image carries its own identity, so a later reader cannot mistake which eye, which phase or which
  build it came from. That is [META-001](pattern-catalog.md#meta-001) applied to evidence rather than to
  binaries, and it is what lets an agent read its own output without a human present.

**And name what the harness cannot judge.** ss2vr-work's harness doc is explicit that comfort, depth,
*"does the parry feel right"*, and whether an unlit hand reads in a dark corridor are irreducibly human
and still need the headset - *"do not let a green harness run stand in for a verdict it cannot make."*
A harness that does not state its own boundary will be asked to cross it.

## An instrument must prove it can see the fault before you trust its clean verdict {#self-proving-instrument}

DishonoredVR's FPU-precision reader is the cleanest statement of this in the fleet, and the shape
transfers to every checker you will write. `[SOURCE]`

The check itself is simple - read the x87 control word and report the precision. The part worth copying
is what it does *before* reporting:

> The reader demonstrates it can detect the degraded state before its verdict is trusted. It sets
> `_PC_24`, confirms the read-back, restores, and confirms the restore; **if that fails the probe exits
> 1 rather than reporting a clean control word it could not have distinguished from a broken one.**

**A checker that has never seen the fault is indistinguishable from a checker that is broken**, and both
print the same reassuring line. This is the same failure as
[an all-zero trigger census](pattern-catalog.md#meta-001) and the same failure as a passing test suite
that never exercised the breaking mechanism ([META-007](pattern-catalog.md#meta-007)) - stated as a
positive obligation: **make the instrument fail on demand, in-process, before you believe it.**

Swat4-VR reached the same place from the test side. Asserting the mirrored basis **passes** an
orthonormality check, alongside asserting the determinant catches it, means *"the test records why
magnitude is insufficient rather than just testing the right thing."* A test that only checks the
correct behaviour does not document the trap it exists for.

### And when the instrument was unguarded, measure before you retract

DishonoredVR found their interop probe had created both D3D9 devices without `D3DCREATE_FPU_PRESERVE`,
so every timing figure in a shipped document came off a thread whose precision had never been checked.
They did not retract it and they did not wave it through. They **simulated the arithmetic at both
precisions across three plausible QPC frequencies**: worst absolute error `4.4e-07 ms` against a
reporting granularity of `1e-03 ms`, and an identical p95 index. Nothing needed retracting.

Their own verdict on that is the transferable half: **"that is luck rather than design."** Sub-millisecond
tick counts are small integers that fit inside a 24-bit mantissa, and the maths was two multiplies and a
divide with no accumulation. **The same trap on rotation composition would not have been survivable,
because error accumulates there instead of cancelling** - which is where bo1-vr originally found it. When
you discover a systematic measurement fault, the question is not "is my data wrong" but **"does this
computation accumulate or cancel"**, and that question has an answer you can compute.

## Assert the gap, not the verdict {#assert-the-gap}

PreyVR shipped a render-camera check with `tolerance = 0.001f`, *"a number chosen by eye and never
derived"*, then replaced it after reading this playbook's own correction that a residual limit is a
property of a metric rather than of a problem. What they added is worth having explicitly. `[SOURCE]`

They built a **separation table** from the tests: the correct case scores `0.000000000`; the tightest
wrong case they could construct - a `0.004` asymmetry error - scores `0.004000008`, at **40x** the
`1e-4` limit; every other wrong case lands **600x to 7500x** above it. Then:

> The tests assert **the gap** rather than just the outcome, so widening the limit later breaks a test.

**A threshold with no test on its margin is a number anyone can quietly move.** Asserting the separation
turns "we loosened the gate" into a failing build rather than a commit nobody reviewed.

One more trap they caught in themselves, which applies to every reference implementation in this
playbook: their header claimed the correct case reproduces to `~1e-7`, written before it was measured.
It reproduces to **exactly zero** - because the test recomputes with the same formula on the same
inputs. **A self-referential test measures the arithmetic, not the engine.** The live path derives the
same block in the engine's own float ops, so the rounding floor there is an open question, and their fix
is to **log the residual as a number rather than a verdict** until it is known.

## Recover the projection from VERTEX data when the constant buffer is unreadable {#projection-from-vertices}

Constant buffers are frequently unreadable - reflection returns zeros, or the per-draw offset into a
large shared allocation is not reported, so reading at offset 0 silently returns another draw's data,
formatted plausibly. **Vertices do not have that problem.** `[LIVE]`

For a rigid draw, object-to-clip is one affine 4x4. Solve it by least squares from the vertex buffer and
the post-VS output:

```text
[x y z 1] . M = [xc yc zc wc],    M = W . V . P
```

Then, because D3D's perspective `P` has fourth column `(0,0,1,0)`:

- **`M`'s 4th column is `(W.V)`'s third column**, whose norm is the object's uniform scale `s`
- `xScale = |M_col0| / s`, `yScale = |M_col1| / s` -> **FOV, with no constant buffer at all**
- normalised columns give the view basis -> `det(V3x3)` -> **handedness**
- fitting `z_c = a.w_c + b` over the vertices gives **znear**, with no vertex pairing

Measured on one target: `fovX 42.4449`, `fovY 34.5159`, `znear 0.1`, `w_clip = +z_view`, and
**`det(V3x3) = -1` - the view basis is mirrored**, which is the opposite of what an unexamined
implementation assumes and exactly what
[the handedness assertion](#mirrored-basis) exists to catch.

### The guards are the important half, and one of them is not optional

All three fired on real data:

| Guard | What it caught |
|---|---|
| **conditioning** (`cond < 100`) | a **flat mesh** whose `y` was constant |
| residual (`< 1e-4`) | draws where no single affine map fits |
| uniform-scale + orthogonality | a non-uniform or sheared world matrix |

**The flat-mesh case is the one to carry.** Its residual was a *tiny* **3.4e-05** while the answer was
nonsense - aspect 0.61 against a true 1.25. **Only conditioning catches that.** A wrong answer with a
float-precision residual is the worst failure an instrument can produce, and the residual is structurally
incapable of detecting it.

**Free self-validation:** `yScale/xScale` must equal the render target's aspect. Registering that as a
*prediction before the measurement* turns the fit into a falsifiable test - `1.250000` against
`1280/1024 = 1.250000`.

**Trap:** post-VS output ordering is **not consistent between draws** - one draw came back in vertex
order, others matched neither vertex nor index order. Fit under every candidate ordering and require the
winner to beat the others by orders of magnitude.

## A census supporting a NEGATIVE claim must enumerate exhaustively {#negative-claims-exhaustive}

This one nearly shipped a wrong architecture. `[LIVE]`

A project concluded *"the mirror is an object-level redraw, not a second world render"* on the strength
of *"large room meshes each appear exactly once."* That census used a tool that **silently caps at
`max_results`**, plus a `min_vertices` filter that was a *sampling* decision rather than a neutral one.
Redone properly, static geometry is drawn repeatedly and **the conclusion reversed completely.**

> A claim of the form **"X appears only once"** or **"X never happens"** requires an exhaustive
> enumeration, or an explicit statement that the search was partial. **Filters and result caps are
> assumptions, and when they support a negative they are load-bearing assumptions.**

Two companions from the same investigation:

- **A hypothesis that explains the evidence *and finds a real bug* can still be the wrong cause.** Dead
  controller buttons were diagnosed as a rejected binding profile - a genuine defect in their code, and
  not the cause. A controller had disconnected.
- **When a symptom splits along a hardware boundary** - one hand, one eye, one device - **establish the
  hardware is present before reading code.**

## Ship a live kill mask, and bisect the artefact instead of the code {#artifact-bisector}

`Dishonored-VR` calls it *"the artifact bisector"* and it is the best single debugging affordance in
that project. `[SOURCE]`

Once draws are being **classified** - world, UI, shadow, additive, UP-path, quarter-res - expose a
**runtime kill mask over the classes** and a matching kill switch for whole features. Then a visual
artefact is diagnosed by *turning classes off while looking at it*, in one run, rather than by rebuilding
with a hypothesis.

This is `git bisect` applied to the frame rather than to history, and it is strictly better in one
respect: **the artefact and the toggle are visible at the same instant**, so the observation and the
change are not separated by a compile, a launch and a memory.

Two design notes from the same project. The mask is **live and writable** (as are their stereo separation
and convergence), so a wearer can move it without leaving the headset -
[which is the difference between a comparison and two memories](08-project-process.md#headset-reachable-controls).
And it pairs with an **on-demand per-draw verdict dump**: the mask says *which class*, the dump says
*which draw and why it was classified that way*.

**The precondition is the classifier**, so this arrives naturally at rung 2 and not before. If you are
already splicing per draw you have the taxonomy; exposing it costs almost nothing and repays it on the
first artefact.

## Three instrument artefacts that impersonate bugs {#artefacts-that-impersonate}

All three cost real time, and all three read as convincing failures of the thing under test. `[LIVE]`

**Capture cadence quantised to an even frame stride.** Six consecutive captures under alternate-eye
landed exactly **28 frames apart** - even, therefore the same parity, therefore the same eye. Six
identical images, no alternation visible, and it reads as broken alternation. *The capture
request-to-completion round trip has its own period and cannot sample both eyes at its natural cadence.*
Staggering the delays turned the artefact into the experiment: strides 30/32/34 gave the noise floor and
33 gave full parallax, and **frame-stride parity predicted the eye four times out of four** - stronger
evidence than the original test could have produced.

**Freezing the simulation on a menu background.** Time-scale zero while the game sat on a backdrop it
renders blurred and dimmed by design: near-zero frame differences, tiny cross-eye difference, because a
blurred depthless backdrop *has almost no parallax to show*. It reads exactly like a dead stereo path,
and cost two runs. **Fix: a scene-content guard** - two unfrozen captures a moment apart that must differ
before anything is frozen. A live scene animates; a menu backdrop does not.

**A control that silently disarms the thing under test.** Their stereo API treats an IPD of zero as
*disarm*, so the obvious control - "set IPD to zero, expect no difference" - would have produced two
identical frames **because the stereo path was never armed**, and read as a clean control while proving
nothing. The working control was **the same eye captured twice at full IPD**: everything identical,
including the path being live.

> **A control must hold the mechanism ON and vary only the quantity.**

## State an instrument's observation boundary in every test request {#observation-boundary}

An OpenXR contract recorder captures frame timing, located and submitted poses and projections, layer
sets, ordering and dimensions. It does **not** capture the pixels inside a swapchain image or the game's
skinned geometry. `[SOURCE]`

That still makes it a powerful **negative discriminator** - if a layer stays present with stable pose,
size and order while headset video shows the content flashing, the fault is **upstream, in source
rendering or capture**; if the layer itself changes contract, look at lifecycle, budget or submission.

> **A green contract trace can exonerate the compositor without proving the source image correct.**

So pair instruments deliberately and say which question each answers: headset video for what the user
sees, source-pixel captures for what was drawn, the mod's own log for state, and the contract trace for
the compositor boundary. One project reported *13 probe checks and 17 contract checks green* against a
visible gamma fault **none of them could have caught** - they measure geometry and contract, never a
pixel. That is not a gap in the instruments; it is a gap in the request.

## Check a derived value against a witness the engine never supplies {#external-witness}

Deriving a value from engine fields and then checking it by recomputing from the same fields proves the
arithmetic is consistent. **It cannot catch a wrong convention.** `[LIVE]`

PreyVR carried a project-wide error in which the engine's **vertical** FOV was recorded as though it were
horizontal. Every internal check passed. What settled it was checking the derived horizontal figure
against **the player's in-game FOV slider** - a number the engine never hands you, produced by a
different path entirely. Derived `120.000`, slider read `120`. **The engine's fields never contain 120,
so agreement is only possible if the convention is right.**

> For any derived quantity, find one external witness that does not share the derivation's assumptions -
> a settings menu, a config file, a physical measurement, a human observation. **One such check is worth
> many internal ones.**

This is the general form of [assert the gap](#assert-the-gap) and the answer to
[the self-referential test](#assert-the-gap): a witness outside the derivation is the only thing that can
falsify a convention.

## A metric that cannot come back bad is not a metric {#metric-cannot-fail}

Three of Swat4-VR's four judder instruments were measuring something other than their name, and all three
read healthy. `[LIVE]`

- **Pose age compared `predictedDisplayTime` to itself** - structurally always `0.00`.
- **Eye-pair span measured render time, not content divergence.** Both eyes display at the same instant,
  so identical content rendered 3 ms apart produces zero disparity. The number was real and answered a
  different question.
- One signal was simply invalid and was retracted.

Two rules, and the second is the one that generalises furthest:

> **Construct the input that would make the metric fail, before trusting it.** A metric that has never
> been observed bad is indistinguishable from a metric that cannot go bad.

> **Measuring the OPPORTUNITY for a fault is not measuring the fault.** Render-time spread is an
> opportunity for eye divergence; it is not divergence. Name instruments after what they measure, not
> after what you hope they detect.

## A liveness signal does not tell you WHICH thing is alive {#liveness-is-not-identity}

"The process is presenting frames" answers *is it running*, never *what is on screen*. FarCry2-VR's
`Start-Game` reported `state=MENU` from a liveness signal while the game was still on its **splash
screen**, which presents at 1223 fps and satisfies every liveness test there is. The boot script then
typed into it - with the one input API that screen cannot read.

Two things follow, and the second is the reusable one:

- **The input path is part of the screen's identity.** That splash reads window messages and needs the
  window **focused** (three `PostMessage` keys were swallowed until `SetForegroundWindow`, after which
  the identical call worked). The menus read **DirectInput** and ignore `PostMessage` entirely.
  *Neither path alone gets from launch to gameplay*, so a driver that knows only one will stall on
  whichever screen it cannot address, while every health check stays green.
- **Take the screenshot before concluding anything.** One image separated *"the game failed to load a
  level"* from *"we typed into the wrong screen with the wrong API"* - two diagnoses with no overlap,
  and the cheap instrument settled it. `[LIVE]` FarCry2-VR, `5a981f9`.

Identity needs a signal only that state emits: a window class, a title, a pixel signature, a log line
the state writes on entry. Presenting frames is emitted by all of them.

**And whether the target needs window focus is a per-target question, not a rule.** The fleet now has
three answers and they disagree, which is the finding:

- **FarCry2-VR:** the splash screen reads window messages and **needs focus** - three `PostMessage`
  keys were swallowed until `SetForegroundWindow`, after which the identical call worked. Its menus
  read DirectInput and ignore `PostMessage` entirely.
- **Swat4-VR:** a focus precondition, missed three separate times (`F-0028`), voided everything
  measured in the window where an ad-hoc command sequence skipped the launcher's focus step.
- **SS2VR:** `[AUTHOR]` keyboard focus is **not** required while the game keeps producing frames -
  the main menu works without it.

So "does this need focus?" belongs in the project's own notes with a receipt, and a harness ported
between projects must re-answer it rather than inherit it. It is also worth asking **per screen**
rather than per game: FarCry2's answer differs between its splash and its menus.

## A correct percept built from two cancelling errors - do not tidy it up {#correct-by-cancellation}

Swat4-VR's eye-separation and head-translation functions use **opposite right vectors**, `(+sin, -cos)`
and `(-sin, +cos)`. Both are independently confirmed correct in a headset. **Both cannot be right**, so a
second inversion exists somewhere they have not located. `[HEADSET]`

The hazard is the shape: two near-identical functions differing by a sign is exactly what a future
refactor tidies up - and unifying them would break a working percept **while every unit test still
passed.** They pinned it with a test asserting the two stay opposite.

> **When reality disagrees with your arithmetic, encode reality and label the disagreement. Do not
> resolve it by editing the arithmetic.**

A cancelling pair is a debt, not a bug: record where it is, assert it stays, and close it when the second
inversion is found - never by making the two sides agree.

## Declare the exact set each fault must flip {#falsification-exactness}

[The section above](#self-proving-instrument) says make the instrument fail on demand. This is the next
turn of the screw, and it caught two defects that had passed every other check. `[LIVE]`

A falsification matrix that asserts *"this fault makes something fail"* is much weaker than one that
asserts **exactly which checks fail and no others**:

- **a fault that flips nothing** is a check that does not work;
- **a fault that flips something extra** is a check measuring the wrong thing - and that is a failure
  too, not a curiosity.

Both happened building `xr-tape`'s twenty checks, on the first run of the matrix:

> A **toe-in** fault rotated both eyes the *same way*, so their relative orientation was unchanged and
> it was not toe-in at all. The matrix reported that it flipped nothing.

> With that fixed, toe-in flipped **vertical disparity**. The head frame was being taken from the *left
> eye alone*, so a toed-in rig rotated the measuring frame along with the thing being measured and the
> lateral baseline leaked into the vertical axis. Using the **mean of both eye orientations** fixed it.

Neither is exotic, and neither would have been found by "the checks pass on good input and fail on bad
input". **The second is the dangerous one**: it would have sent someone hunting a vertical-alignment bug
that did not exist.

Two supporting habits from the same build:

**Report any check with no fault case, by name.** A check nothing can reach is untested, and saying so
in the suite's own output is cheaper than discovering it during an incident.

**A finding that is true and expected is `XFAIL` with a reason, never a suppression** - and an
expectation that *stops firing* is itself a finding, because a stale expectation silently hides a
regression the day the thing it excused changes.

## Record the observation even when you cannot name it {#record-the-unnamed}

`xr-tape` identified an OpenXR graphics binding by matching struct types against a table, and wrote
`"binding": "unknown"` when nothing matched - discarding the number that would have identified it. The
first OpenGL client taped came back `unknown` because the table had a wrong constant. `[LIVE]`

The fix is one line and the rule is general: **when a lookup fails, record the raw value you looked
up.** A name you cannot resolve is a gap in your table; a value you did not keep is a gap in your
evidence, and only one of those is recoverable after the run.

## Expose the running game over HTTP, then drive it from a test {#http-control-plane}

A [substitute runtime](09-d3d11-openxr-injection.md#substitute-runtime) fakes the *runtime* so the game
can run headless. shock2quest takes the complementary route: it exposes the *game* over HTTP, so an agent
or a test can place a camera, drive input, step frames and take screenshots without a headset and without
a human. `[SOURCE]`

```bash
# place the debug camera anywhere and aim it
curl -X POST http://127.0.0.1:8080/v1/camera \
  -d '{"position": [-32, 1, 21], "look_at": [-35, 0, 21]}'
curl http://127.0.0.1:8080/v1/camera                            # read back eye_position/eye_rotation
curl -X POST http://127.0.0.1:8080/v1/camera -d '{"detached": false}'   # back to the player
```

Their own justification is the part worth quoting, because it names a capability nothing else gives you:

> the only way to photograph something the player's own eye cannot see, **the player and whatever they
> are holding included**

That is the answer to a whole class of VR bug that is otherwise unobservable. You cannot see your own
viewmodel from outside, you cannot see whether the body is where you think it is, and you cannot frame
the hands from the front — until the camera detaches from the eye.

On top of it sits a typed SDK, so a regression becomes an ordinary test file:

```ts
const game = await GameServer.launch({ mission: 'medsci2.mis' });
await game.input.rightHand.trigger(1.0);
await game.input.head.rotation([0, 0.707, 0, 0.707]);
const shot = await game.screenshot('test.png');
```

### Four traps they documented, and every one is a general hazard

These are written into their agent instructions rather than discovered per session, which is the right
place for them:

- **The placement needs a latch.** Placing turns a `free_camera` developer option on, because *nothing
  else would keep the placement past the next step* - the step re-attaches the camera while the option is
  off. A one-shot override that the next frame silently undoes reads as "the API did not work".
- **Detaching repurposes the locomotion sticks** to fly the camera instead of walking the player, so a
  later "walk forward" command moves the wrong thing. **Re-attach before driving.**
- **Aim the head *before* placing.** The runtime composes the tracked head pose onto the camera, and the
  placement divides out the head *as it was at request time* - so a later head change swings the camera
  off its `look_at`. This is the [pose-generation](shared-vr-spine.md#port-06) problem appearing in a
  tool: a value derived from a pose is only valid for that pose's generation.
- **Culling still follows the player.** A camera placed in another room sees geometry culled away for
  someone standing elsewhere, until a `free_camera_cull` parameter is set. That is
  [CAM-002](pattern-catalog.md#cam-002) - render camera and cull camera are different things - showing up
  in the debug tooling rather than the game.

**A debug camera is a second view, and every per-view hazard in this playbook applies to it.**

## Where agent tokens actually go, measured over 30 days {#agent-token-costs}

shock2quest ships a `audit-our-commands` skill that joins `tool_use` to `tool_result` across session
transcripts and ranks commands by result tokens. Its finding is not what most people would guess:
`[SOURCE]`

> most tool-result tokens go to **reading habits**, not to game tooling - `sed`-paging source files (much
> of it re-paging files already read that session), whole-file reads, wide greps, and full diffs.

Their rules, ranked by measured saving:

- **Outline before paging any file over ~800 lines.** Grep its structure
  (`grep -nE '^\s*(pub )?(fn|struct|impl|enum|trait)'`), then make **one** targeted read with
  offset/limit. On one file an outline was **~30x smaller** than the file, and serial `sed -n 'A,Bp'`
  windows tend to re-fetch regions already seen.
- **Never re-read what is already in context.** Repeat reads of the same path, repeat searches, and
  `cat` followed by `cat -n` of the same file measured at **~6% of all tool-result tokens**. If you saved
  a dump to a file yourself, grep it - do not page your own output back in.
- **`git diff --stat` first**, then diff only the files that matter. Never truncate a full diff with
  `head` - you pay for the whole thing and may still miss the file you needed.
- **Keep greps narrow.** `-A/-B/-C` context and unanchored patterns are where grep cost concentrates.
  Scope by path and tighten the pattern *before* adding context lines.

**The transferable move is the audit, not the rules.** They measured their own sessions and let the
ranking pick the fixes, which is why the answer was "how we read files" rather than any of the tooling
anyone would have suspected. If agent cost matters on a project, measure where it goes before optimising
what feels expensive.

## Build the control before you ask for the test {#build-the-control}

Anything a user must judge **by eye** belongs in an in-game overlay that renders into the backbuffer -
which *is* the eye image - not behind a console command. Driving an in-headset A/B by typing requires
alt-tab, and on more than one project **alt-tab is itself the pacing bug**, so command-driven headset
testing is both slower and actively destabilising. `[SOURCE]`

This is the cheapest lever on the headset round-trip problem described below: a comparison the user can
flip with a controller button costs one session; the same comparison behind a typed command costs one
session per variant.

## Sweep the hypothesis space inside the hook, not one guess per launch {#in-hook-sweep}

Every live test in a VR project is expensive - a launch, a load, a headset, sometimes a person. Manhunt
VR spent four live tests on single-field guesses at a `CreateDevice` failure, then stopped. `[SOURCE]`

> Rather than spend a sixth live test on one more single-field guess, built a probe sweep:
> `Hooked_CreateDevice` now creates a **private, hidden, invisible throwaway window** and tries **7
> candidate `D3DPRESENT_PARAMETERS`/`BehaviorFlags` variants** against it via `real_CreateDevice`
> directly - each device released immediately, none of it touching the game's real window or the real
> forwarded call - logging every outcome. **One live test now answers as many hypotheses as fit in the
> sweep, instead of one per launch.**

The playbook already uses a throwaway device to
[resolve vtable slots](09-d3d11-openxr-injection.md#resolve-vtable-slots-from-a-throwaway-device-then-hook-the-games-real-one).
This is the same object doing a different job: **a sandbox for questions you would otherwise ask the
real call, one per session.**

**A matrix answers more than a list does.** Their result was unambiguous *because* it varied several
fields at once: every variant that kept `FullScreen_PresentationInterval` at
`D3DPRESENT_INTERVAL_IMMEDIATE` failed **regardless of what else changed** - depth-stencil on or off,
backbuffer dimensions, software versus hardware vertex processing - and every variant that switched it
to `DEFAULT` succeeded **with nothing else required**. That is a controlled experiment, not a lucky
guess, and it names the sufficient condition as well as the necessary one.

Two disciplines around it. **The scaffolding came out once it had done its job**, keeping the hook back
to a narrow, minimal size - a sweep is an instrument, not a feature. And when an earlier fix turned out
not to be the blocker, they kept it anyway and said why: *"a real fix for a real restriction, just not
the (or not the only) actual blocker."* **Correct changes that did not solve the problem are still
correct**; deleting them to "get back to a clean baseline" reintroduces bugs you already paid for.

### A validation API validates only what it validates

The reason four sessions went the wrong way is worth its own line. `CheckDeviceType` returned
`hr=0x00000000` on the same configuration that `CreateDevice` kept rejecting - because it *"only
validates the format/windowed pairing, not `SwapEffect` at all."*

> That's exactly why the diagnostic looked clean while the real call kept failing.

**A clean check is not a clean call.** Before trusting a validation helper to narrow a failure, read what
it actually inspects - and when a checker and the real call disagree, the checker is usually right about
its own narrow question and silent about yours.

## Confirm the precondition, and look at the raw capture at least once {#confirm-the-precondition}

Two process failures from one Psychonauts VR session, published by them because both were **repeats**,
and both are cheap to avoid. `[SOURCE]`

**Running experiments without confirming the precondition.** Three camera tests ran with a pause menu
open - the game ignores camera input there. One mouse test ran without verifying the foreground grab.
One pad test ran while the user was not touching the stick. Every one produced a plausible number.

> **A screenshot was captured each time and not looked at** - only a derived brightness number, which
> happened to look plausible.

**That is the whole failure in one line.** A derived metric cannot tell you the experiment never ran;
the raw capture can, at a glance. [Turning the artifact into a number](#quantify-the-artifact) is right,
and it does not excuse you from opening the image once per experiment - the scalar is for *trending*,
the capture is for *validity*. Make the precondition an explicit gate: assert the menu is closed, the
window is focused, the input is moving, and abort the run rather than recording it.

**Blocking the shell for the whole probe window.** The instruction *"move the stick now"* was printed
**inside** a call that then blocked for 26 seconds, so it reached the user after the window had already
closed. A wrong conclusion - *"the pad path is dead"* - was published from that and had to be formally
withdrawn.

> **Arm the probe, return immediately, end the turn.**

Anything that needs a human to act during a measurement must reach them **before** the measurement
starts, which means the prompt and the wait cannot be in the same blocking call. This is the interactive
counterpart to [building the control before you ask for the test](#build-the-control).

## Arm diagnostics from config, because a headset session has no keyboard {#arm-from-config}

A diagnostic that had existed for **seventy-six runs** and had never once been usable, for a reason
nobody noticed: `[SOURCE]`

> The `UI element:` dump had existed since run 153 armed on the `[` key, and **`Debug=0` makes keyboard
> input inert** - so it had never once been usable in a headset.

Two gates in series, each individually sensible, and their intersection is exactly the case that
matters. **In a headset you cannot see the keyboard, and a build tuned for a real session usually has
debug input off** - so a hotkey-armed instrument is available in precisely the situations where you do
not need it.

Their fix is the general one: **make it armable from the config file, as a bounded countdown** - thirty
batches, one a second, then stop by itself. That inverts both problems. It needs no keypress, it is set
before launch alongside everything else, and it terminates without anyone reaching for a key to stop it.
Pair it with [armed, self-terminating capture](a5-flat-harness-stats.md) - same shape, same reasons.

**Audit your instruments for what arms them.** Anything reachable only by keyboard is a
monitor-session-only tool, whether or not it was meant to be.

## "It cannot be measured" is usually a claim about one instrument {#wrong-instrument}

A note in Singularity VR's code said the sniper rifle could not be aligned: *"it aims through its own
scope, so the laser is off and there is nothing to align it against."* It shipped untuned behind that
note for many runs. `[SOURCE]`

> That was wrong about the **instrument**, not the weapon. The laser is not the only reference a barrel
> can be aligned against: **the scope has a reticle**, and run 214 had already measured that scoped aim
> tracks that reticle.

Aligning against the reticle is *"the same judgement by eye through a different lens"*, and the values
were tuned in a headset that afternoon.

**Before recording an impossibility, enumerate the other references.** A statement of the form "X cannot
be measured" is almost always "X cannot be measured **with the instrument I reached for**", and the
difference is worth a minute because the note will outlive the session that wrote it and stop everyone
who reads it.

Note also where the answer was: **already measured, sixteen runs earlier, and never connected to the
problem it solved** - the same shape as
[a measurement nothing consumes](08-project-process.md#unconsumed-measurement).

## A tuned value that lands on the limit is the limit, not a preference {#value-at-the-clamp}

Small, easy to miss, and it invalidates the tuning result. `[SOURCE]`

> The chosen value came out **AT the clamp**. The floor was 40 and the comfortable setting was 40, and
> **from inside a clamp those two are indistinguishable** - one is a preference, the other is the
> boundary.

They lowered the floor to 25 *"so the answer sits somewhere in the range instead of on its edge"*, and
re-tuned. **Whenever a tuned parameter settles exactly on a range end, widen the range and repeat**: if
the value moves, you were measuring the clamp; if it stays, you have a real preference and now you can
say so.

Worth recording alongside it, because it is the reason to measure at all: *"65 was my guess and it was
far too big; the measured value is nearly half of it."*

## Can this run with the headset off? If not, is that essential or accidental?

The most expensive kind of dead diagnostic is one that is **silently** dead: the logs look healthy, they
are simply empty in the place that mattered, and you lose the session before noticing.

FarCry2-VR lost two test sessions to the same shape in one day, and neither cause had anything to do
with VR:

- **Camera angles were published *after* a "no headset pose" early-out**, so a flat run never identified
  the player pawn at all.
- **The RE probes' install lived inside the F8 VR bring-up handler**, so on a flat run they never
  installed. The camera write ran **11,649 frames** while all three probes sat at `installed=0`.

Every project here has a flat harness precisely so that reverse-engineering work does not need a charged
headset and a clear hour. **A capability that accidentally requires the HMD has quietly deleted that
harness**, and it will not announce itself.

**The check, cheap and worth making a habit:** *can this run with the headset off — and if not, is that
essential or accidental?* Publishing a camera angle is not a VR operation. Installing an RE probe is not
a VR operation. Neither belongs behind a VR gate.

The [`offered`/`acted` counter pair](#absence-of-errors-is-not-evidence) catches it after the fact —
`installed=0` across 11,649 frames is exactly that signal — but the question above catches it before the
session is spent.

## Demonstrated in production beats argued from a code path

There are two ways to show a diagnostic path is reachable, and they are not equivalent:

- **Argued:** you pass `nullptr` in a test, the branch fires, and you reason that production reaches it.
- **Demonstrated:** you run a real configuration and read the counter.

(*Swat4-VR's `noQueue` stage recorded **6,403** hits on the **default build** — not a contrived state,
just what every user who has not enabled that lane already sees. DishonoredVR, comparing their own
`no_device` proof against it: "mine fires in a real window, but I proved it by passing `nullptr` in a
test and then reasoned that production reaches it. Theirs required no reasoning."*)

**Prefer a real configuration that already exercises the path** over fault injection, and go looking for
one before you write the injection harness. Products usually have more genuinely-reachable states than
you remember — a disabled feature flag, a missing optional device, an un-woken headset.

### And fault injection can make a dead path look alive

The sharper half. Swat4-VR had planned to null an instance handle to demonstrate a `noInstance`
counter — then found the stage was **unreachable by construction**:

> The fix would have made a dead stage look alive, **and it would have looked like rigour.**

An injected fault proves the branch *compiles and runs*, never that anything real reaches it. If you
cannot find a production configuration that exercises a stage, that is a finding about the stage —
possibly that it should be deleted — not a gap to paper over with a test double.

## Spend the outside review on the code you have read most

Two projects independently split their defect records the same way, and the split predicts where a
cross-check pays:

- **Self-review catches defects in code you have just written** — before you have formed a habit around
  it.
- **Outside review catches defects in code you have read many times.** Merged return conditions walked
  past repeatedly; dead stages in a funnel one project *authored and described to a peer twice*.

(*One of them: "they'd read that line three times today, once to fix its memory ordering, and never saw
the merged condition. It wasn't unreviewed — it was **over-familiar**."*)

The scheduling consequence runs against instinct: **the unfamiliar file feels riskier, and it is not.**
Point a fresh reader at the file you know best. On this fleet that means the core loop, the transport,
and the funnel you designed — not the module you touched last week.

A related line worth keeping, from the same exchange: **"documenting a trap is not removing it."** A
registry entry marking a seam `OPEN` does not stop a later plan from quietly assuming it is closed.

## Falsify your own hypothesis before shipping a fix

Several SS2VR "fixes" shipped on a plausible theory and were later falsified by their own
diagnostic output (the value the fix was supposed to change didn't change). Before believing a
fix:

- Add the diagnostic that would **disprove** it, and check the disproof didn't fire.
- A fix with no proof line is a guess wearing a confidence costume.
- **Don't read a diagnostic's *precondition* as its *result*.** Read the value back *after* the
  mutation, in its own column. (*SS2VR: `cull_from_eye` was reported "no effect" because the probe showed
  `darkCam==renderCam` — but that near-equality was the space-*validity gate*, and the probe never read
  the cull global back after the `+=`. A working feature and a dead one printed identically until a
  `cullCamPost` column was added.*) A probe that only shows your clean inputs, or the gate you passed
  through, can't show whether the write landed.
- **A "validity" flag your own probe emits encodes an assumption, and the assumption can be the thing
  that's wrong.** The natural reading of `identityValid=0` is "the hook target is wrong" — but the
  classifier that computes it has its own model of which field means what. (*BioshockVR's camera-
  constructor hook was firing correctly, with plausible arguments and `readValid=1`, while reporting
  `identityValid=0` every sample. The classifier assumed constructor argument 4 was the controller; it
  was really the view-target pawn, a different vtable, and the real controller lived at `viewport+0x48` —
  confirmed by a ~60-unit eye-height offset between the two positions.*) Before treating a validity
  failure as proof the address is wrong, **audit what your own classifier assumes.**
- **A success return proves the call didn't throw — not that it had the intended effect.** `ok=1`,
  `override=1`, "flag accepted" are all statements about the API, not about the world. (*SS2VR spent a
  session on `weapon_probe_launch override=1` on the assumption that an accepted override meant visible
  aim must have changed; the override was accepted by a path that wasn't the one drawing the weapon.*)
  Pair every success return with an observation of the thing you wanted to move.
- **When a gated feature still fires, look for a second implementation before you re-poke the gate.**
  (*SS2VR "fixed the deny" on two-handed pistols three times, with a condump each time **proving** the
  Squirrel deny worked — because a separate DLL-side two-hand aim blend existed that the Squirrel switch
  could not reach.*) Same shape when a function has several branches doing one job: fix all of them, or
  you ship a fix that works everywhere except the case the user meant.
- **When a signal-driven visual doesn't respond, instrument the consumer, not the signal.** (*Same
  project chased a beam-brightness signal twice; the signal was correct throughout, and the bug was a
  render-path fallback to an always-bright texture.*)

These four, plus the stale-build trap above, were a single documented cluster of five consecutive builds
in which fixes were announced and were not fixes. The common thread is announcing an outcome from
something adjacent to it — the gate, the signal, the return code, the build you *think* you're running.

## An isolation gate is itself a second variable

A flag that isolates variable X by suppressing everything else has just introduced a second experiment.
If the suppression also cuts a fallback the scene needs in order to render at all, you get a blank or
degraded result — which reads exactly like "X failed."

(*BioshockVR did this twice. A strict stereo-matrix gate suppressed the already-proven mono fallback on
every draw the strict path rejected, so the headset showed only solid proof colours —
`stereoProofApplied=0`, `Fallback=49112` — while the pipeline under test was untouched. An over-broad
skip predicate later starved a mono accumulation path to `0` the same way. Both looked like the
hypothesis had failed; both were the isolation mechanism cutting the power.*)

Before reading a blank result as a verdict, **prove the baseline path is still alive** — a counter on the
fallback is usually enough. A result of zero from an instrument that is also switched off is not evidence.

**The nastier version produces a false *positive*, and needs a control capture.** If the mechanism you use
to run the experiment can itself move the measurement, then a *positive* result proves nothing either —
and positives are the ones nobody re-examines.

(*Swat4-VR's scene-re-entry proof doubles the scene draw and yaws the second pass, then diffs the image. But
if any once-per-frame mutable packet double-advances ([14](14-render-pass-hazard-atlas.md)), the second pass
differs for reasons that have nothing to do with the camera — so a yawed diff would read as a confident PASS
while proving nothing about re-entry. The control that catches it is trivial: **double the draw with no
yaw**. It was initially impossible to run, because `yaw != 0` was also the arm switch — the two had to be
split into separate levers before the control could even be expressed.*)

Two things generalise. **Make the confound expressible**: if your "on" switch and your treatment are the
same flag, you cannot build a control, and that is a design bug in the harness rather than a limitation of
the experiment. And **read the control first, with authority to veto** — their comparer reads the
no-yaw capture before anything else and exits `CONFOUNDED` if doubling alone moved pixels, refusing to
report the treatment as a verdict however large it is.

That last point is what makes it more than a nicety. A control you read *afterwards* gets rationalised; a
control that gates the verdict cannot be.

## Your control group must consume the variable under test

Dismissing an anomaly because "the working case has it too" is only valid if the working case actually
reads that value through the same path. Otherwise you haven't controlled for anything — you've excluded
your best lead. Before you write off a finding, name the code path that would consume it and confirm your
control runs that path. [05](05-assets-and-materials.md) has the worked example that cost a day.

## Promote claims, not branches {#claim-scoped-promotion}

An evidence label answers **how this was observed**; a promotion scope answers **what proposition the
observation is allowed to change**. They are independent. A `[LIVE]` run can prove one narrow role and
leave every neighboring address a candidate; a `[SOURCE]` validator can prove that a gate is enforced
without proving the runtime result that the gate describes.

Five MonsterDeadWood research trees converge on a small experiment contract that makes this distinction
mechanical. `[SOURCE]` Before a run, record:

1. the claim ID and its present scope (`candidate`, `cold-only`, `role-proven`, or globally locked);
2. the exact baseline revision and target-binary identity;
3. the one intended intervention, plus an observer-only control;
4. the artifacts that must exist for the result to be readable; and
5. the predeclared `CONFIRM / REFUTE / AMBIGUOUS` decision rule.

After the run, promote **that claim only** and attach the artifact hashes. Do not merge the branch as a
unit of truth. A prepared plan is not a result; donor evidence is not target evidence; static closure is
not runtime ownership; exact execution is not a visual verdict. Reopening a closed claim needs a written
new premise or new evidence. This is [META-010](pattern-catalog.md#meta-010).

## Observe the denominator before intervention {#observer-before-intervention}

An intervention can change the population it claims to measure. A force-pass patch, early return, draw
duplication or diagnostic hook may create/delete calls, alter culling, or move work to another phase;
after that, a clean percentage or association is about the instrumented program rather than the target.

Record the untouched denominator first: total candidates, total calls/draws, and how many satisfy the
association. Then run a passive observer with the same counting path. Only after both agree should the
causal mutation run. If the mutation changes the denominator, report the experiment `CONFOUNDED` unless
the changed population is itself the named subject. MonsterDeadWood FC2VR found this while forcing a
culling predicate: the mutation moved the very call population needed to identify the natural owner, so
the next useful run was observer-only rather than a stronger force-pass.
`[AUTHOR]`

## A hook that "does nothing" may simply never be reached

Before you conclude your hook is wrong, prove it *ran*. The common cause of a correct hook having zero
effect is that the normal-play code path branches around it — often behind an early-out for a mode you
aren't in (replay, demo playback, developer mode, splitscreen).

- *HaloVR:* hooking the obvious HUD element-submit function did nothing in-headset. The caller checks
  `game_is_playback` first, and **normal play short-circuits past both the class comparison and the
  hooked function entirely**. The fix wasn't a different hook — it was NOP-ing that one validated
  short-circuit so the engine's own classification actually ran, then hooking the site.

Put a bare hit-counter in the hook before you debug its logic. "Called 0 times" and "called but wrong"
are completely different investigations, and telling them apart costs one log line.

## Presence is not proof of loading

The same discipline applies one level up, to your own artifacts. A file being on disk, a package being
listed, a mod folder existing, an archive loading — none of it proves *your code ran*. This bit one
project at least three separate ways:

- **Installed but not in the load path.** A correct fix was written, packaged and shipped into a mod that
  simply wasn't listed in the engine's `mod_path`. The stock file won every frame; the symptom was
  identical to "the fix doesn't work." (*SS2VR, weapon-mesh strobe.*)
- **Loaded but shadowed.** Two packages ship the same relative path; first-in-chain wins. Load order and
  override order are different questions, and the answer is engine-specific.
- **Package present, script never executed.** The archive appeared in the save's mod list and in package
  load lines, while the script inside it never printed its own banner.

**Rule: every script, package or injected component prints one line proving *it* ran** — not that it was
found. Then gate the dependent machinery on that proof: the fix here was to require a fresh heartbeat
from the script side before the DLL would publish to it at all. Until you have that line, "the fix didn't
work" and "the fix never loaded" are indistinguishable, and you will debug the wrong one.

## Check the cheap environmental causes before you bisect code

Host-machine state is a silent input to every measurement, and it is free to check.

(*SS2VR chased a framerate regression through code across multiple sessions. Root cause: the **Windows
desktop refresh rate had silently reset to 50 Hz**. The desktop Present vsyncs to it, capping the entire
VR pipeline. Setting it back to 144 Hz fixed it instantly.*)

- A **round-number fps cap is almost always a refresh/vsync cap, not reprojection.** `frameMs ≈ 1000 /
  desktop_Hz` is the tell — and note 45 is half of 90 (reprojection) while 50 is just 50 Hz.
- For any "suddenly slow" report, check in this order *before touching code*: desktop refresh rate,
  runtime reprojection/motion-smoothing, headset refresh mode.
- A build bisect is the right way to *confirm* a cause is environmental (all versions identical ⇒ not the
  code) — but it's the confirmation step, not the first step.
- Present-to-present span is **not** a GPU-work metric; it counts idle and wait. Use real GPU counters.

## Frame-capture (RenderDoc) workflow

For "rendered but invisible," double-draws, wrong stereo, wrong materials — the GPU capture is
ground truth:

- Capture a frame with the broken thing *and* a known-good reference object both visible.
- Compare the two draws: shader pair, bound textures (size/format), render target, blend/depth
  state, and **constant buffer contents**.
- Watch for tooling gaps: read constants by fetching the cbuffer **resource** and dumping raw
  bytes if the reflection path returns zeros (a real MCP limitation hit on SS2VR — the
  "everything is zero" reading was the tool, not the data). **Confirmed a second time on Sims4VR,
  2026-08-25**, which makes it a standing defect rather than a one-off: `get_cbuffer_contents` returned
  `cb0_v0`..`cb0_v10` all `[0,0,0,0]` on every event in two different scene passes, while the raw bytes
  held correct matrices the whole time. Skip the reflection path entirely:

  ```python
  get_shader_bindings(stage="vertex", event_id=E)   # -> cbuffer0 resource_id + byte_size
  get_buffer_data(resource_id="ResourceId::471", length=176, format="floats")
  ```

  Two adjacent defects measured in the same session. `analyze_render_passes` reports
  `render_targets: []` for any pass whose target is bound through a **deferred context** — on Sims 4 that
  hid the two largest passes in the frame, 545 of 889 draws. **An empty render-target list means "not
  resolved", not "no target".** And `get_draw_call_state` returns `AttributeError` for blend / depth /
  stencil / rasterizer state, so depth-buffer *binding* is readable but depth *test/write* state is not —
  build conclusions on binding, vertex layout and indexed geometry, never on those fields.
- A draw can report rendered-this-frame and still output nothing; the capture shows *why*
  (degenerate verts, garbage constants, null SRV, wrong blend).

### Injection and API support are different problems — check support first

When a capture tool will not attach, the fix you reach for depends on which of two entirely separate
things is wrong, and they are easy to conflate:

| Problem | Symptom | Fix |
|---|---|---|
| **Injection** | The tool cannot get into the process — a launcher indirection, a wrapped or protected binary | Launcher hooking, different injection order, attach instead of launch |
| **API support** | The tool got in and has nothing to say | **None. Use a different tool.** |

(*FarCry2-VR nearly spent a session applying a launcher-hooking recipe before checking: Far Cry 2 is
**D3D10.1**, and RenderDoc covers D3D11/12, GL ≥ 3.2 and Vulkan only. No injection method can help — and
that target launches its executable directly, so there was no launcher indirection to defeat either.
Their working answer for D3D10 is apitrace: two captures on disk, 38,706 frames.*)

**Check the tool's supported-API list before debugging why it will not hook.** A recipe that reads as a
general "when RenderDoc won't attach" procedure is really a fix for one of these two problems, and
applying it to the other one costs a session.

### Budget for the capture tool failing — it is the normal case on old targets

Treat "I will just take a capture" as a hypothesis to test on day one, not a capability you have. Across
the fleet, **frame capture worked out of the box on a minority of targets**, and it failed for a different
way each time:

| Project | Capture tool | What happened |
|---|---|---|
| Swat4-VR | RenderDoc | **Cannot attach at all** — 32-bit, statically imports `ddraw.dll`, engine picks its real device at runtime; RenderDoc supports none of DirectDraw/D3D8/D3D9. apitrace works, and is used in anger. |
| DishonoredVR | apitrace | Adopted, then **abandoned after four attempts** — `0xC0000005` within 7–11 frames of real rendering. **Same API as Swat4-VR, opposite outcome.** |
| FarCry2-VR | RenderDoc | Not viable in a 32-bit address space; **built a bespoke frame inspector instead**, which became the project's primary instrument. |
| PreyVR | RenderDoc | **Null-derefs at the NVAPI vendor-extension query.** Expect this on NVIDIA targets. |
| BioshockVR | RenderDoc | Injected + RenderDoc under Virtual Desktop fails at `xrEndFrame`; private-eye captures still land, but captures past a certain point crash on **32-bit address exhaustion**. |
| Sims4VR | RenderDoc | **Launch-based hooking cannot work** - EA/Steam indirection means the launched process is a throwaway stub and the real game is spawned by pre-existing services. Solved by hooking on *appearance* rather than parentage; see below. |

Two rules fall out of that table.

**Do not generalise a capture path from one success.** "It is D3D9, so use apitrace" is exactly the
inference the first two rows refute — apitrace is the only D3D9 *option*, which is not the same as
saying it works. Prove the capture path on your own target before you plan any work that depends on it.

**A dead capture path is a finding, not a blocker.** It is what tells you to build the
capture-independent path below, or a bespoke inspector, *now* rather than after three weeks of fighting
the general-purpose tool. FarCry2-VR's inspector is the fleet's best instrument and it exists only
because RenderDoc could not run.

RenderDoc can destabilize an older game or conflict with an active OpenXR runtime. Build a
capture-independent path early: a hotkey that dumps final XR eye color, private eye color, and
private depth with synchronized frame/eye/sequence names. This cannot replace full pipeline
state, but it answers the highest-value question: *what image existed before the compositor?*

### A capture tool interposes, so it becomes the caller your hook attributes {#interposing-observer}

Separate from the launcher problem below, and nastier because it produces **data rather than a
failure**. `[SOURCE]`

RenderDoc does not merely watch D3D11 - it returns a **wrapped device context**. The call path becomes
`game → renderdoc's wrapper → real d3d11.dll`. So a Frida or detour hook placed on the *real* function,
asking "who called this?", records return addresses pointing into **`renderdoc.dll`** and not into the
game:

> plausible-looking data that is entirely wrong.

**Caller attribution and frame capture are mutually exclusive in one session.** If the question is *which
game code writes this constant buffer*, the capture tool must be **absent** - not idle, not paused,
absent - and that has to be stated as a precondition of the run, because the census will otherwise
complete and produce a clean, confident, meaningless writer column.

The same applies to anything else that wraps the device: ReShade, ENB, dgVoodoo, an overlay, or another
mod's proxy DLL. **Enumerate the modules in the process before trusting any caller attribution**, the way
you would [rule out an implicit API layer](07-engine-integration-safety.md).

And a companion trap from the same census: **walk two frames up the stack, not one.** The immediate
caller of an engine helper is usually another engine helper; one frame answers "what wrapper called it",
not "what system wanted it".

### When a launcher defeats your injector, hook by *appearance* — not by parentage

Every launch-based capture path — RenderDoc's *Launch Application*, `renderdoccmd capture`, apitrace's
`trace_launch` — rests on one assumption: **the process you launch is the process that renders.** On any
storefront-wrapped game (EA, Steam+EA, Ubisoft Connect, Battle.net) that assumption is false, and no
combination of settings in the launch dialog repairs it.

**Measured on Sims 4 (2026-08-25), `renderdoccmd capture --opt-hook-children`:**

```text
14:23:09.140  TS4_x64.exe          pid=143672  parent=renderdoccmd.exe   <- LAUNCHED AND HOOKED
14:23:10.596  EALaunchHelper.exe   pid=139760  parent=<exited>           <- hooked proc requests launch, exits
14:23:15.334  Link2EA.exe          pid=16624   parent=steam.exe          <- leaves the subtree (pre-existing)
14:23:23.553  EASteamProxy.exe     pid=136312  parent=EADesktop.exe      <- leaves it again (pre-existing)
14:23:24.151  TS4_Launcher_x64.exe pid=91424   parent=EASteamProxy.exe
14:23:25.346  TS4_x64.exe          pid=120208  parent=TS4_Launcher_x64   <- THE REAL GAME
```

Confirmed afterwards: `renderdoc.dll` absent from pid 120208's module list. Never hooked.

**Why `--opt-hook-children` cannot save you.** Child-process hooking follows *descendants of the launched
process*. Here the chain leaves the hooked subtree **twice** — through `steam.exe` and through
`EADesktop.exe` — and **both were already running before the injector started**. Descendant-tracking is
structurally the wrong relation. The corollary is worth stating because it costs an afternoon: **no choice
of executable in the launch dialog works**, including the game's own launcher, because the branch point is
outside the subtree either way.

#### The diagnostic: a process-tree watcher, armed before you launch

Do not infer the chain. Record it. This converts "it just doesn't connect" into an exact answer in one run:

```powershell
$seen = @{}; Get-CimInstance Win32_Process | ForEach-Object { $seen[$_.ProcessId] = $true }
while ($true) {
  $now = Get-CimInstance Win32_Process
  $map = @{}; $now | ForEach-Object { $map[$_.ProcessId] = $_.Name }
  foreach ($p in $now) {
    if ($seen.ContainsKey($p.ProcessId)) { continue }
    $seen[$p.ProcessId] = $true
    if ($p.Name -match 'YourGame|Launcher|EA|Steam|Origin|Ubisoft') {
      $pn = $map[$p.ParentProcessId]; if (-not $pn) { $pn = '<exited>' }
      "$(Get-Date -f 'HH:mm:ss.fff') START pid=$($p.ProcessId) $($p.Name) parent=$($p.ParentProcessId) ($pn)"
    }
  }
  Start-Sleep -Milliseconds 200
}
```

`parent=<exited>` is the signature of the failure: the parent died before you could read it, which is
exactly what a hand-off stub does.

#### The fix: poll for the process, inject by PID

`renderdoccmd inject --PID=<pid>` takes the same `--opt-*` options as `capture` and does not care how the
process was born. Poll at 25 ms, inject on sight, and **verify by module list, never by exit code**:

```powershell
$seen = @{}   # baseline already-running instances first
while ($true) {
  foreach ($c in Get-CimInstance Win32_Process -Filter "Name='Game.exe' OR Name='GameLauncher.exe'") {
    if ($seen.ContainsKey($c.ProcessId)) { continue }
    $seen[$c.ProcessId] = $true
    $a = @('inject', "--PID=$($c.ProcessId)", '-d', $bin, '-c', $out,
           '--opt-disallow-fullscreen', '--opt-capture-all-cmd-lists')
    if ($c.Name -like '*Launcher*') { $a += '--opt-hook-children' }
    & $renderdoccmd @a
  }
  foreach ($p in Get-Process Game -EA SilentlyContinue) {
    if ($p.Modules | Where-Object { $_.ModuleName -match 'renderdoc' }) { "HOOKED pid=$($p.Id)" }
  }
  Start-Sleep -Milliseconds 25
}
```

**Four traps, each of which produced a false "this does not work":**

1. **The first process bearing the game's name is a throwaway stub.** Sims 4's lived 1.1 s; the real game
   appeared **14.7 s later**. An injector that disarms after its first hit always injects into the stub and
   always reports failure. **Never disarm — keep injecting until a module check confirms a hook.**
2. **Injecting into a dying stub returns a misleading error.** Measured: *"Failed to inject renderdoc.dll...
   Check that the process did not crash or exit early in initialisation, e.g. if the working directory is
   incorrectly set."* The working directory was correct. The process had exited. Chasing the suggested
   cause wastes the run.
3. **RenderDoc's Global Process Hook is hidden by default.** It is absent from the UI until
   `"AllowGlobalHook"` is set in `UI.config`, reachable via **Settings → General → "Allow global process
   hooking"**. Users reasonably conclude their build lacks the feature.
4. **A successful hook can still fail to capture: "uncapped command list".** A D3D11 engine that records
   on deferred contexts needs `--opt-capture-all-cmd-lists` (GUI: *Capture all Cmd Lists*), and it must be
   set **at inject time** — it cannot be turned on once the process is running. Sims 4 hit this on its
   first capture attempt after a confirmed hook. **Pass it by default on D3D11 targets**; the cost is
   memory, and the alternative is discovering it one relaunch too late.

**Result on Sims 4:** `renderdoc.dll` loaded in the real game, verified by module enumeration, game
responsive at 156 threads.

**Which mechanism landed it: the launcher's `--opt-hook-children`.** A second run separated the two in
time and settled it:

```text
14:38:09.199  inject into TS4_Launcher_x64 pid=88004  (+ --opt-hook-children)
14:38:10.293  *** HOOKED pid=49736 ***                 <- hook confirmed HERE
14:38:10.902  detected TS4_x64 pid=49736 -> injecting  <- direct inject only STARTS now
14:38:10.943  Injecting into PID 49736
```

The hook was present **609 ms before the direct PID inject began**. Child-hooking installed
`renderdoc.dll` at process creation; the direct inject was redundant.

**The practical consequence: inject the *launcher* with `--opt-hook-children`, and treat per-PID injection
as the fallback.** Hooking at creation is strictly better than racing a running process, because it cannot
lose the device-creation race at all. Keep the per-PID path for targets with no intermediate launcher, or
where the launcher is not identifiable ahead of time.

**Prefer this over the global hook.** System-wide injection also catches by appearance, but it injects into
*every* process that starts, needs administrator, and must be turned off afterwards. Poll-and-inject is
scoped to one executable name and needs neither.

**Timing is a race you can lose.** Hooks must be installed before the target creates its graphics device,
and launching `renderdoccmd` costs ~200-300 ms. This target was reachable because it loads 146 modules plus
an activation layer and a Python runtime before touching D3D; a game that creates its device immediately
may not be. If you lose the race, the global hook is the fallback, not the first resort.

**Anti-tamper does not necessarily block this.** Sims 4's binary is wrapped by EA's activation layer — a
one-entry import table (`Core/Activation64.dll`) and a non-standard `.ooa` section — and accepted the
injection regardless. Assume a wrapped binary is hookable until measured otherwise; the wrapper usually
guards *tampering*, not *loading*.

## Tooling lies in specific, learnable ways — know them before you trust a reading

Every layer between you and the game (the capture tool, the MCP helper, the shader cache) has failure
modes that masquerade as game bugs. Learn each one's tell:

- **A 32-bit target runs out of address space, and the crash is the tool's, not yours.**
  (*BioshockVR: an equipped-wrench capture crashed inside RenderDoc's own null-write after
  "Allocation for N bytes failed" — a 2 MB request with ~62 MB free but only ~1.8 MB largest
  contiguous block in the x86 process.*) Don't stack 3DMigoto/geo-11 + RenderDoc + your mod in one
  32-bit process; fall back to a post-blit BMP/PNG dump. Related: 32-bit DXGI truncates modern cards'
  reported VRAM, so **identify GPUs/adapters by LUID and output count, not by name or memory size.**
- **Reflection-reported buffer sizes don't match runtime allocation.** (*BioshockVR: RenderDoc
  reflected `$Globals` as 544/752/560 bytes while the live `GetDesc().ByteWidth` was 576/832/1088.*)
  Classify draws by the *live* byte width; a layout keyed to the reflected size mis-keys every draw.
- **A cbuffer helper that returns all-zeros is usually the tool, not the data.** Fetch the cbuffer
  *resource* and decode raw bytes as floats instead. (*Hit on SS2VR and independently re-confirmed on
  BioshockVR — a documented MCP limitation, not "the constants are zero."*)
- **An automated matrix/camera finder will confidently name a matrix that is not a camera.** (*DishonoredVR
  recorded this as the false positive that cost its analysis a whole first pass: apitrace's
  `find_matrices` reports the **BT.601 YUV-to-RGB colour-conversion matrix** as a `viewproj` at
  **confidence 0.9**, with a plausible **57 degree FOV** derived from it.*) The discriminator is free and
  decisive: **a matrix that never changes cannot be a camera.** Check the tool's own
  `temporal_changes` / `distinct_values` before trusting any decode — and treat a high confidence score
  as a statement about pattern fit, not about semantics. The generalisation: **a video-heavy game hands
  you a confident false camera**, and the tell is the constancy fields, never the confidence score.
- **A tool that accepts bad input and answers anyway is more dangerous than one that rejects it.**
  (*PreyVR: four `emulate_function` runs passed `registers` as `RCX=0x...,RDX=0x0`. Every run returned
  `success: true`, `hit_return: true`, `stop_reason: "return"`, and `steps_executed: 5` — exactly right
  for a five-instruction function. **The inputs were silently discarded and it ran on zeroed registers**,
  and the resulting `RAX: 0x0` read naturally as a real finding. The format had to be JSON.*) This is
  the same shape as a matcher's `score`: the failure is not a wrong number, it is **a well-formed success
  wrapper around an unconfigured harness**. The defence is a round-trip control: **put an input the
  function never modifies into the outputs and confirm it comes back unchanged** before believing
  anything else the call returned. Apply it to every tool you have just started using — the calls you
  have no habit around are exactly the ones you have no calibration for.
- **A cache lookup lies where a live query wouldn't.** If you inject after shader creation, a
  cache-based classifier sees "PS is null" and mis-labels draws (e.g. mask draws as stencil-only
  volumes). D3D11 also *retains* stage bindings across draws, so a depth-only draw carries a **stale**
  PS/SRV it never samples. Query the pipeline **live at draw time** (`VSGetShader`/`PSGetShader`,
  `*GetConstantBuffers`) and require a live PS before classifying a consumer.

## You are probably using 10% of the tool you already have

A fleet audit found every RE tool in heavy use — Ghidra in 103 documents,
RenderDoc in 74, Frida in 44, Cheat Engine in 31 — and almost all of that use confined to a **narrow
slice** of each tool's surface. The gap is not which tools are installed. It is depth within them.

The failure mode is ordinary: you learn the four calls that solved your first problem, they keep working,
and you never go back to read what else is there. The correction is cheap — once per tool, list its
entire surface and ask which entries name a problem you have already had.

Concrete instances found in this fleet, each mapped to a problem that was solved the slow way:

| Capability | Sitting unused | Would have answered |
|---|---|---|
| `pixel_history` | RenderDoc | *"Which events wrote this pixel, and did they pass depth/stencil?"* — BioshockVR spent **three builds** toggling a suspect draw class before output-merger telemetry showed `rt0WriteMask=0x0`. This returns write-by-write history with pass/fail, directly |
| `get_post_vs_data` | RenderDoc | *"Did my per-eye matrix actually reach the vertices?"* — post-vertex-shader output, observed rather than inferred from a residual |
| `analyze_render_passes` | RenderDoc | The first pass of [14](14-render-pass-hazard-atlas.md)'s hazard atlas, which FarCry2-VR did by hand. Auto-detects pass boundaries from clears and render-target changes |
| `diff_draw_calls` | RenderDoc | Eye A versus eye B, as a state diff rather than two screenshots |
| pointer-chain tools | Cheat Engine | `playerRoot+0x110`, `AHands+0x40C`, `cNode3D+0x108` — every project derives these by hand; `analyze_pointer_access` / `validate_pointer_chains` / `pointer_rescan` exist for it |
| `generate_signature` | Cheat Engine | AOB signatures are hand-written here, and a **missing REX prefix broke two projects' hooks** ([11](11-re-anchoring-and-discovery.md)). A generator does not forget a prefix |
| `find_function_boundaries` | Cheat Engine | Chapter [11](11-re-anchoring-and-discovery.md) documents **four** ways a prologue scan lands on the wrong function |
| `emulate_function` | Ghidra | Prove what a function does with no game running — the offline half of the live-probe rule below |

**One worth a deliberate experiment rather than adoption:** Cheat Engine's DBVM watch
(`start_dbvm_watch` / `poll_dbvm_watch`) is hypervisor-level and **polled**, so it may observe memory
writes without the breakpoint stop that makes an ordinary debugger fatal to a VR process (see *You cannot
pause a VR process* above). If that holds it reopens a technique this playbook currently rules out
entirely. `UNVERIFIED` — nobody in the fleet has tried it, and it deserves the pre-registered decision
rule from [above](#measure-dont-theorize-the-readback-probe) rather than an afternoon of poking.

**A trap while shopping for capability: the same word means different things.** RenderDoc's
`diagnose_reflection_mismatch` analyses *rendered reflections* — SSR, mirrors, scene captures — and has
nothing to do with the *shader-reflection*-versus-runtime buffer-size mismatch documented below. Read the
tool's own description before mapping it onto your problem; a name that matches your vocabulary is not
evidence it matches your problem.

## Settings lie: read the value the consumer receives, not the one you wrote

A config file, a UI slider and the value the renderer actually uses are three different things, and on
an older engine they routinely disagree. Two mechanisms, both silent:

- **Dead keys.** Several plausibly-named settings exist; most are inert, and the live one is not the
  obviously-named one. (*Swat4-VR found `DesiredFOV` and `DefaultFOV` never change no matter what the
  sliders do, `FirstPersonFOV` did not take the user's value either, `BaseFOV` is the key the view slider
  actually writes — and the viewmodel's FOV is **on disk nowhere at all**, being a compiled package
  default.*)
- **Hidden clamps — one setting silently capping another.** This is the nastier one, because your change
  *appears* to do nothing and the obvious conclusion is that you found the wrong lever. (*Same project:
  `FOVBias = tan(min(FOV, DefaultFOV)/2)`, with `DefaultFOV` shipping at `85`. Setting the FOV to 120
  changed nothing until the clamp was raised. It was found by A/B against the value the constructor
  received, not by reading config.*)

**The rule: resolve the question at the consumer.** Hook the function that receives the value and log
what it was actually handed. A settings file tells you what someone intended; only the consumer tells you
what the engine got. This is the same discipline as reading back after a mutation, applied to
configuration.

**A third mechanism, specific to attach-mode injection: environment variables never arrive.** A process's
environment block is populated at *creation*; a DLL injected into an already-running process inherits
whatever that process was launched with, and nothing you set in your own shell afterwards. (*BioshockVR
set `..._VIEWMODEL_PROBE=1` before launch and watched three consecutive builds log `probe=0`. It was
settled by using Frida to read the live process's actual environment block, which showed the variable as
`null` inside the target. The toggle moved to an INI read at DLL load.*) If you support both launch and
attach modes, an env-var-based toggle works in one and silently fails in the other — which is worse than
not working at all. Read configuration from a file, and log the resolved value.

## Tools that cannot see the process report it as absent

If the game runs **elevated**, every tool must be elevated to see it at all — and the failure mode is
badly disguised: an unelevated tool typically reports the process as *not existing*, which is
indistinguishable from "the game isn't running."

(*Swat4-VR: their Frida MCP server was not elevated, so `enumerate_processes` omitted the game entirely.
The tell that separates the two cases is that a normal shell's process listing **does** show the process
but returns an **empty path** — visible, but unreadable.*)

Check elevation parity as a preflight for every RE tool, alongside "is the host app even running." And
record which tools on this target need it, because the answer is per-game and you will forget.

## You cannot pause a VR process

Every breakpoint-driven workflow you have — pause, inspect registers, single-step, sample the stack —
is unavailable the moment the target is presenting to a headset. Pausing freezes the XR submit loop, and
the runtime's watchdog takes the app down with it.

(*SS2VR tried to pause-and-sample a running VR build in x64dbg to profile a stutter. The first register
read after the pause returned "Resource temporarily unavailable," every subsequent call errored, the
automation bridge desynced, and both the debugger and the game crashed. Zero samples captured. It is
logged twice in that project's registry — it was repeated.*)

- A pausing debugger is for **flatscreen or already-broken** targets. Run the flat harness
  ([08](08-project-process.md)) when you need one.
- For a live VR session use **non-pausing instrumentation only**: in-process logging on the render
  thread, a dynamic tracer that doesn't stop the process, counters and ring buffers you read out later.
- Attaching a debugger is not free even when you never break: see the logging note below on
  `OutputDebugStringA`, and [07](07-engine-integration-safety.md) on attach windows and anti-debug.

## Dynamic tracing finds the exact owner that static RE only approximates

Static decompilation gives you candidate functions; a live tracer proves which object and field the
running game actually uses. When "the pointer looks right but the behavior is wrong," trace it.
(*SOMAVR: Frida tracing proved the analog-movement owner was the player-helper sub-object at
`playerRoot+0x110`, not the root pointer, and that a readiness check was reading `root+0xc8` instead of
the helper's `+0xc8` — a "close pointer, wrong object" bug that produced no error, just silence.*) Keep
a dynamic-trace option (Frida, a debugger script, or an instrumented hook) alongside the static map.

**Static RE is fine for control flow; any claim about a runtime *value or existence* needs a live
check before you ship it "verified."** (*SS2VR burned four headset sessions on four enemy-weapon-read
recipes that each decompiled correctly but failed live — wrong handler table, unresolved joint, empty
prop for that object class — until three Frida memory-read probes found the real read. And even a live
probe misleads if you trust a data label over the user's eyes: the `eCreatureJoint` "R/L" enum did not
indicate which arm a baked-in weapon was rigged to; only the visual calibration overlay resolved it.*)

When a visual problem is direction-dependent, correlate it with source/private draw counts and
render-target/depth-resource identity. A sudden jump in replay work can reveal that a mirror,
portal, environment capture, or vista view is being merged into the main stereo view.

## Crash-dump workflow

- Read the faulting **instruction bytes** and registers, not just the address — they often map
  directly to the data structure being walked (a loop counter that's your model's polygon
  count, an offset that's your section pointer).
- Scan the dump for strings in **both** ASCII and UTF-16; loaders store paths wide. A "no
  strings found" from an ASCII-only grep is a false negative.
- Distinguish crash *classes* by faulting address + nearby strings; "it crashed again" isn't a
  data point until you confirm it's the same RVA and the same structure.
- **Bound your own crash handler before you need it.** An in-process exception filter is itself a
  fault-recursion risk, and a fault that reproduces every frame will write dumps every frame. (*An
  independent BioShock mod's handler produced **2,083 minidumps totalling 115 GB** from a single failure
  mode before it was capped.*) Design in reentrancy protection, suppression of repeats at the same
  faulting address, and a hard per-session dump cap — retrofitting these happens after something fills a
  disk.
- **A 32-bit crash handler does not port to x64 by recompiling.** x86 uses frame-based SEH; 64-bit Windows
  uses table-based exception handling, so inherited crash-capture code from a 32-bit sibling project needs
  a real rewrite. (*Flagged in SOMAVR's transfer audit from BioshockVR — `UNVERIFIED`: scoped as planned
  work, not yet built, so treat the requirement as sound and the implementation as unproven.*)

## Native-engine RE shortcuts

For the full treatment of *locating* functions, globals, vtables, and struct fields in an unknown binary —
the anchor ladder, stratified fallbacks, emulation/tainting, version fingerprinting, and struct tooling —
see [11](11-re-anchoring-and-discovery.md). The short version follows.

- **String → reference → handler** works only if references are static. Runtime-registered
  tables have no static string refs to scrape; don't burn hours on a scan that can't succeed —
  pivot to the supported entry point (console/command system).
- Prefer the engine's **own documented commands/cvars** as the dispatch surface over a raw RVA
  call whenever they exist; they're stable across patches, an RVA isn't.
- An old open-source ancestor of the engine (if one exists) is gold for *vocabulary and
  architecture* — but confirm every name/offset against the actual shipping binary before
  calling it. (*SS2VR: old Dark/Shock source named the systems; the AE binary confirmed which
  survived.*)

## On a 32-bit target, unrelated crashes may be address-space exhaustion {#laa-address-space}

Worth knowing before you spend a week on a rendering crash, because the symptom points nowhere near the
cause. FEAR2VR: `[SOURCE]`

> F.E.A.R. 2 is a 32-bit game that normally runs without the `LARGE_ADDRESS_AWARE` flag, limiting it to
> roughly 2 GB of user-mode virtual address space. **With the VR mod loaded, the process approached that
> limit during normal play.** Memory fragmentation left very little contiguous address space available,
> causing allocations to fail and producing **misleading crashes in otherwise unrelated systems,
> including rendering and audio.**

**A VR mod is a large new tenant in that 2 GB**: a second set of eye targets, a runtime, its swapchains,
your own DLL and whatever you cache. The failure is not an out-of-memory message - it is a large
contiguous allocation failing under fragmentation, surfacing as a null nobody checked, in a subsystem
that has nothing to do with you. **If a 32-bit target crashes in varied and unrelated places once your
mod is loaded, measure the address space before debugging any of them.**

The flag itself is one bit in the PE header, and setting it grants the process 4 GB. The complication is
that **a DRM wrapper may validate the executable image and reject a modified one** - the usual reason the
easy fix is not available. FEAR2VR's launcher works around it without altering the shipped file: it
creates an LAA-enabled copy, starts it **suspended** (Windows reads the flag at process creation), and
uses a temporary entry-point stub to restore the process-visible executable path, module identity and
mapped PE characteristics to the original's before validation runs, then restores the original entry
bytes. **It verifies the restoration succeeded before letting execution continue** - which is the part to
copy whatever your mechanism is, because a half-applied identity fix is worse than none.

## Never derive a version from the same word as the identity it versions {#identity-and-generation}

A third witness for the same failure class as the pose-history index below, from a completely different
domain - which is why it earns its own section. SkyrimTogetherVR is a Skyrim VR compatibility port of a
multiplayer mod, and its avatar identity bridge maps: `[SOURCE]`

```
EntityId         = uint64_t(ServerId) + 1
EntityGeneration = (ServerId >> 20) + 1
```

`ServerId` is a **packed EnTT entity handle** - 20 index bits and 12 version bits in one 32-bit word. So
both halves of the identity are derived from the same value, and their review states the consequence
exactly:

> Reusing one EnTT entity slot changes the packed `ServerId`, so the current `EntityId` also changes. The
> ledger then cannot compare old and new generations for the same canonical slot; the separately
> transmitted generation is **redundant rather than authoritative**.

**A generation exists to tell you that the same slot now holds something else. If the identity changes
when the generation does, it cannot do that job** - you have spent the bits and kept none of the safety.
Unpack the index and the version separately, key the ledger on the stable index, and let the version be
the only thing that moves.

**The general class, now with three independent witnesses in this survey:**

| Project | What was passed | What broke |
|---|---|---|
| FEAR2VR | a sequence number into a pose history | rotation desynchronised - camera judder |
| shock2quest | a camera placement composed against the head pose *at request time* | a later head change swung the camera off its target |
| SkyrimTogetherVR | an identity and its generation packed in one word | slot reuse was undetectable |

**Passing a reference into a mutable table across a boundary is the bug; passing the value is the fix.**
When the value is genuinely too large to send, send the index *and* an independent generation that does
not move with it - and validate the pair on arrival rather than assuming it.

Their review protocol is worth a line too, given how much of this survey is agent-assisted work: every
evidence item carries a `[verified: file:line]` tag, the reviewer is explicitly **read-only** and told to
*"verify the cited implementation before critiquing the framing"*, and the brief names the scale of fix it
will accept up front - *"prefer a small defensible correction over a new general-purpose entity
framework."* That is [META-002](pattern-catalog.md#meta-002) applied to a review rather than a finding.

## Two ways an agent goes wrong on a VR mod, and what recovers it {#agent-failure-modes}

FEAR2VR was built with heavy agent involvement and its author documented where that went wrong. Both
failures are specific enough to watch for. `[SOURCE]`

**Failure one: plausible hypotheses that never touch the data path.** Camera judder, several rounds of
fixes, none of them right. What recovered it was refusing another hypothesis and demanding the chain be
traced end to end instead - four questions, in order:

1. Where on the mod/game side is headset rotation obtained from the XR bridge?
2. How is that rotation applied to the game?
3. How is it passed and synchronised back to the XR side - *what pose did we actually render with?*
4. How is that then consumed by the XR side?

The answer fell out immediately: they were passing **a sequence number into a pose history** rather than
the pose. The index desynchronised; the pose could not. **Carry the value across the boundary, not a
reference into a buffer the other side will index later** - the same lesson as
[META-005](pattern-catalog.md#meta-005) and as shock2quest's debug camera dividing out the head pose *as
it was at request time*. Three projects, one rule: a pose-derived value is only valid for that pose's
generation, so send the generation with it or send the pose.

**Failure two: reaching for the input layer when a direct write exists.** The agent built *"an enormous
pipeline for directing camera movement via injecting mouse inputs with the right sensitivity"* to do head
tracking. Pointed at the render/aim camera instead, it solved it quickly. **Synthesizing input to
achieve what a value write achieves is a characteristic wrong turn** - it is superficially safer, it
inherits every deadzone and curve the engine applies ([INPUT-004](pattern-catalog.md#input-004)), and it
cannot express what the input layer cannot express. Ask "what value am I trying to change?" before
"what button would change it?"

The author's summary of the working division is worth keeping as-is: they directed the project, made the
architectural decisions, **defined the testing and verification standards**, and kept the work grounded
in the behaviour of the live game; the agent explored implementations, reverse-engineered, wrote code and
iterated. The standards stayed human.

## A correction that never arrives invalidates every judgement made since {#dead-correction-term}

The companion to the section below, and the more expensive failure of the two. bfbc2-vr's FOV widen
matrix `K` was multiplied into `rot` *after* `r` had already been built from `rot`, and the
correction was built from `r` - so **`K` never reached it**. `[SOURCE]`

The game kept rendering its native ~69x45 degree field while the mod told the compositor the image
was 2.3x/3.4x wider, and the per-eye texture bounds simply **magnified** the native image to fill the
eye. It looked like a picture. It was a zoom. Their own note on the cost:

> it also means **every in-headset judgement since `0afea3b` was made on a 2-3x zoomed picture**.

**That is the part to internalise.** A dead correction term does not announce itself as a black
screen; it produces a plausible image, and every subjective call made while looking at it - "the gun
is too big", "that feels close", "comfort is worse here" - silently becomes evidence about the wrong
picture. Weeks of in-headset opinion can be invalidated by one ordering mistake, and unlike a crash
there is no moment where you find out.

Two defences, both cheap:

- **Make the correction observable, not just applied.** If a term is supposed to change the picture,
  log the value that actually reaches the matrix you submit - not the one you computed. This is
  [META-001](pattern-catalog.md#meta-001) at the level of a single term: prove which value ran.
- **Name the in-headset check the fix needs, at the point of the fix.** Theirs does exactly that:
  *"PgUp must now reveal more world rather than zoom. If the world looks warped at 90 degrees yaw,
  the ordering is wrong."* One sentence, and the next person can validate the change without
  re-deriving the algebra.

And when you do find one, **say what it invalidates.** A fix note that does not name the compromised
evidence leaves the bad conclusions in the document.

### "No visible difference" has two causes, and they point opposite ways {#no-visible-difference}

The section above is one half. Psychonauts VR supplies the other, and confusing them costs a session in
either direction. `[SOURCE]`

Their off-axis projection fix produced no visually obvious change on a flat monitor. Their verdict:

> The fix is executing correctly and computing mathematically correct values; **the lack of a visually
> obvious difference on a flat monitor is a genuine, expected property of this specific change, not a
> bug.** No code changes were made this session (none were needed).

| "I changed it and nothing happened" | Cause | Next move |
|---|---|---|
| The value never reached the consumer | **dead term** - [above](#dead-correction-term) | log the value that reaches the matrix you submit |
| The value arrived and the effect is not visible **in this medium** | **expected** | state what the change should look like, and where |

**An asymmetric-frustum correction changes convergence, and convergence is a stereo property.** On one
screen there is almost nothing to see. Judging it flat is judging it through a medium that cannot
express it - the same mistake as
[judging a backbuffer artifact through the headset's optics](14-render-pass-hazard-atlas.md#forced-projection),
running the other way.

**Before you debug an invisible change, write down what it should look like and in what.** If the answer
is "nothing, on a monitor", the test was wrong rather than the code. And rule out the mundane cause
first: theirs opened with *"Ruled out: wrong/stale DLL deployed - direct timestamp/size comparison, not
assumption"*, which is [META-001](pattern-catalog.md#meta-001) and takes a minute.

## When the correction is provably exact and the symptom survives {#exact-correction-survives}

This is the single most reusable thing in BioShock-Remastered-VR, and it is a rule about where to look
rather than a technique. `[SOURCE]`

Their mod rotates the movement stick so walking follows where you point. Players reported that turning
the controller 90 degrees made them walk 10-20 degrees off. Three builds went into refining the rotation
maths. Their own retrospective:

> **THIS WAS NEVER A TERM WE FAILED TO CANCEL.** R is algebraically exact and always was; the distortion
> happens AFTER the value leaves us. Three builds of refining the cancellation could not have touched it.
> **When a correction is provably exact and the symptom survives, stop refining the correction and go and
> measure what the other side actually received.**

The actual cause was on the far side of the boundary: the game applies a **square** deadzone - per axis,
0.225 - so rotating the stick moves magnitude between the two axes and the engine then shrinks each one
*independently*. See [the maths and its inverse](13-teardown-bioshock-vr.md#square-deadzone).

**The general shape:** when you hand a value across a boundary you do not own, a correct value on your
side is not a correct value on theirs. If your transform is provably exact - and yours can be, algebra is
checkable - then the residual is definitionally somebody else's transform, and the next move is to read
back what arrived, not to keep polishing what you sent. That is the same instinct as
[META-001](pattern-catalog.md#meta-001) applied to data rather than to code: prove which bytes arrived.

### Their probe was rebuilt because the first one could not answer {#probe-cannot-answer}

Worth copying separately, because the discipline shows up in a comment rather than a commit message:

> WARNING - **THE FIRST VERSION COULD NOT ANSWER**, and it is worth saying why rather than quietly
> widening it. It compared travel against `base.yaw` alone -- but the intended heading is
> `base.yaw + STICK ANGLE`, and the stick is not readable from `CalcView`. The limitation was written in
> the comment and shipped anyway, and the result was **+-7 degrees of noise at ZERO controller offset, as
> large as the signal**.

A probe missing a term does not fail; it produces noise the size of the effect, which reads as "no clear
result" and gets the instrument trusted anyway. The fix was to make the input side **publish the angle it
sent**, so `intended` became a real quantity rather than an inferred one. **If a measurement needs a value
that lives on the other side of a boundary, publish it across rather than reconstructing it** - and when
you ship an instrument with a known missing term, say so at the point of use, because the person reading
the output later will not know.

## Logging discipline (or your evidence destroys itself)

- The in-game console is usually a **small ring buffer**. A per-frame log wipes it in seconds,
  destroying the exact lines a test was run to capture. (*SS2VR: a per-frame publish flooded
  the buffer and ate the proof of every other test.*) Publish on-change or ≤1 Hz; throttle or
  transition-gate logs.
- Any proof needed for **test validity** (versions, mode flags, which path ran) must also reach
  a persistent log file, never only the volatile console.
- Build a **self-service explain probe**: a command that dumps the full classification/decision
  for one object/event on demand (`explain <id>`). It turns "why was this rejected?" from a
  code-reading exercise into one log line. (*SS2VR's `interact_explain` immediately revealed a
  suspected target was actually a different object — a decal — saving a wrong investigation.*)
- Capture logs that are time-boxed bursts (hotkey → N seconds) are *snippets*, not session
  boundaries — don't read session-level conclusions from one burst.
- Per-draw file logging is also a performance mutation. Prefer transition logs, bounded hotkey
  windows, and periodic summaries. Clear or rotate the persistent log when the DLL loads so
  one process maps cleanly to one test.
- **Instrumentation volume is not neutral, and it will be attributed to your feature.** The cost is in
  the *emitted* line, not the filtered one: open-append-close per line, plus a second write if a capture
  file is armed, plus `OutputDebugStringA` — which **balloons to milliseconds per call while a debugger
  is attached**, making debugger attachment itself a timing contaminant. (*SS2VR: left-hand tracking
  diagnostics made the left hand look like the source of gameplay chug when it was really acting as a
  log-volume multiplier. Separately, a probe issuing ~840 writes/s from the render thread took the global
  logger mutex **before** the level filter, so every dropped line still serialized the render thread
  against game-thread logging.*) Three rules fall out: take the level filter before the lock, never
  emit from the render thread at per-draw rates, and when you measure performance, measure with the
  instrumentation off — or record emitted-line count alongside frametime and treat it as a covariate.
  Capture windows that force lines through at a lower level are partly measuring themselves.
- GPU texture readback is synchronous unless carefully staged. If a visual glitch happens only
  while dumping, classify it as capture pressure/state-restoration evidence before treating it
  as a normal renderer regression.

**Your sampling budget will destroy exactly the evidence you wanted.** Bounded diagnostics are correct —
unbounded ones flood the buffer — but a naive budget fails in two specific ways, both of which read as
"the feature stopped working":

- **A shared budget gets spent by the boring case.** (*BioshockVR gave skip-rows and apply-rows one
  budget; 23 `pose_not_ready` skips consumed it before the pose ever became ready, producing **zero**
  `status=applied` lines — while cumulative counters later proved 109 applies had happened by frame 34.*)
  Budget skips and successes **separately**, or the failure path will always win the race.
- **A per-session cap spent at startup starves the whole tail of the run.** (*A 128-sample cbuffer-layout
  cap was consumed inside the first one or two pose frames; later summaries still showed ~100 matching
  lanes per frame with no samples describing them. Read naively: the lane vanished after startup. It had
  not.*)

Two rules fall out. **Track cumulative counters independently of what gets logged verbatim** — the
counter must not share the sample budget. And **emit an explicit "budget exhausted" state**, because
otherwise a healthy-but-capped system and a broken one produce identical output, and someone will debug
the healthy one. Always cross-check a raw-sample dropout against a coarse aggregate before concluding a
signal disappeared.

## Read a per-frame GPU value without paying for it

Chapter [09](09-d3d11-openxr-injection.md) warns that GPU readback stalls. But you often need a *live*
per-frame value — the projection actually being rendered, whether the frame is letterboxed — and polling
it must cost nothing. The pattern that achieves that:

1. Copy the bytes you need (a cbuffer head, a few pixel columns) into a small staging resource with an
   **async** copy during the frame.
2. **Map it on a *later* frame with the do-not-wait flag.** If it isn't ready, skip and try next frame.
3. Decode and apply hysteresis over several intervals before acting on it.

(*An independent BioShock mod watches the renderer's true FOV this way — an 80-byte copy off the first
depth-bound world draw, mapped `DO_NOT_WAIT` on a later present — at **zero measured stalls**, and uses
the same shape for a letterbox detector sampling three 1-pixel columns. See
[13](13-teardown-bioshock-vr.md).*)

**A detector must sample before your own writers touch the target.** If your probe reads the backbuffer at
the *end* of your present hook, it sees your own HUD composite, not the game's output — that project's
letterbox watch flapped for exactly this reason. Sample at the head of the hook, or from a copy taken
there.

## Your capture is phase-locked to your own stereo pair

Once you render alternate or paired eyes, **any capture armed from the game thread always opens on the
same phase of the pair.** This produces two confident wrong conclusions:

- **Screenshots stop being evidence of alternation.** Twelve consecutive same-eye screenshots is the
  *expected* result, not proof that eye alternation broke. (The two presents of a pair are separated by
  only the second eye's build — a few ms — while the second image then sits on the window through the
  next pair's blocking wait, ~8 ms at 90 Hz. So the window is overwhelmingly likely to be caught in one
  phase.) It also means **stereo disparity cannot be measured from window captures at all.**
- **A one-shot frame dump can only ever show you one eye.** One project's HUD "wasn't in any dump window"
  for half a session purely because of this.

### A throttled counter beats against the pair and invents a ratio {#throttled-counter-ratio}

The same phase-locking that ruins captures ruins **counters**, and the failure is harder to spot because
the output is a number rather than a picture. Psychonauts VR spent **two full rounds of fixes** on an
eye1:eye2 draw-call asymmetry of roughly 9:1 - earlier readings of 167:13 and 109:15 - all produced by
**throttle-sampled** counters. `[SOURCE]`

When they shipped exact, unthrottled per-real-frame counters and read them against a live session:

```
206/206 composite log lines: eye1 == eye2, EXACTLY, every time
session totals: eye1 = 16960, eye2 = 16960   (ratio 1.000)
per-frame 39-150, varying with scene complexity, always matched
```

**There was no asymmetry.** A sampler running at its own cadence against an alternating pair produces a
stable, plausible, entirely fabricated ratio - and unlike a wrong screenshot, a wrong ratio looks like
data and invites a mechanism to explain it. Theirs invited a frustum-culling-cache hypothesis that had
nothing left to explain.

**Count every event or count none.** Throttle the *logging* if you must, but never the *counting* - keep
exact totals and emit them periodically, rather than sampling the counter.

Two more things this cost them, both general:

- **Shipping a better instrument is not the same as reading it.** The correct counters existed for two
  sessions before anyone looked; work continued from the old numbers the whole time. When you replace an
  instrument because you distrust its output, **re-derive the conclusion that instrument produced**, and
  do it before the next change.
- **A live log is an evidence channel when you must not touch the process.** All of this came from
  passively reading the proxy log of a session already in progress - no attach, no kill, no file copied
  into the game directory. Design the log so it can answer questions on its own, and a running game you
  are not allowed to disturb stops being a dead end.

### Capture a burst, not a frame

**Under alternate-eye rendering a single captured frame is not merely incomplete — it is arbitrary.** You
do not know which eye it is, which phase of the pair it landed on, or whether alternation was happening at
all, and none of those are recoverable after the fact. (*Swat4-VR hit exactly this: a capture taken to
check the render landed mid-sequence, and one frame could not answer the question it was taken to
answer.*)

The fix is a **hotkey-armed burst of N consecutive frames**, and both halves of that matter:

- **Consecutive**, because alternation is a property of the *sequence*. One frame shows you an image; a
  burst shows you the pattern — L,R,L,R versus L,L,R,R versus no alternation at all. Size N to span
  several pairs: **8–16 frames** is plenty, and covers a stutter without turning into a video.
- **Hotkey-armed**, because a per-frame dump at 90 Hz fills a disk in minutes and — worse — the
  performance cost changes the thing you are measuring ([above](#logging-discipline-or-your-evidence-destroys-itself)).
  Arm it at the moment the artifact is visible; capture ends itself after N.

**Label every frame in the burst with the metadata you cannot reconstruct later**, in the filename itself
so the directory listing is the analysis:

```
burst03_seq00_eyeL_frame184213_pose+0.0312.png
burst03_seq01_eyeR_frame184213_pose+0.0312.png     <- same frame index: a real pair
burst03_seq02_eyeL_frame184214_pose+0.0324.png
```

At minimum: **burst id, sequence position, which eye your code believed it was rendering, the engine frame
index, and the pose or predicted display time.** The eye label is the important one — it records *your
belief*, so when the images disagree with it you have found an eye-phase attribution bug rather than a
rendering bug.

**Arm every capture stage from one trigger.** If separate stages poll the hotkey independently they will
disagree about a short press and you will get a burst from one stage and nothing from the other.
(*BioshockVR's `dumpsync` build exists solely to fix this: its D3D draw-stream probe caught a press its
OpenXR blit-stage dumper missed in the same window.*) One arm signal, mirrored to every stage.

A burst is also what makes the disparity question answerable at all — see
[A5.7](a5-flat-harness-stats.md) for the ring-buffer implementation.

**The same trap applies to timing statistics: tag by frame identity before you compute anything.** Any
instrument that diffs consecutive samples without first confirming they belong to the same logical unit
of work reports a number that is technically true and practically meaningless. (*SOMAVR's naive
frame-to-frame left/right comparison averaged **57.76 ms**, which looks like a serious stereo latency
problem. Restricting the statistic to genuinely same-frame eye pairs — 194 of them — gave a true average
of **2.61 ms**, p95 `4.36 ms`, max `12.29 ms`, with zero pose-frame gap. The 20× inflation was ordinary
inter-frame scheduling variance being counted as a same-frame stall.*)

## Prove stereo from a trace, without putting the headset on

"Is stereo actually working?" is usually answered subjectively, by one person wearing the device and
reporting. That is slow, it needs a human every time, and it is unreliable — **FarCry2-VR had a dead eye
missed by subjective report**, while every counter in the build claimed stereo was running.

It is measurable offline. Capture a trace with stereo enabled and the camera write armed, then run the
trace's camera track (apitrace's `track_camera`, or the equivalent decode of your own capture):

- **Correct alternation** shows eye positions alternating between **two tracks exactly one IPD apart**,
  while the forward vector stays continuous across the alternation.
- **A single continuous track** means the camera write is not being modulated at all — you are rendering
  two identical images while every counter reports stereo.

The cost is one trace instead of one headset session, and the output is a number rather than an opinion.
Do this **before** the headset run, not after it: it is the objective gate that tells you whether the
subjective test is worth anyone's time.

Note the shape — it is [the control-group rule](#your-control-group-must-consume-the-variable-under-test)
applied to the eye itself. Two tracks one IPD apart is the *positive* control; a single track is a
falsifier that no amount of "the counters look right" can outvote.

## Attribute by ownership before shader identity

Shader hashes and index counts are useful, but they are often too narrow or unstable to define
an engine view. For world-render contamination, classify in this order:

1. original color/depth resource pair
2. render-target/depth view and subresource
3. clear epoch and viewport
4. projection signature or camera identity
5. shader/material/draw identity

Draw ordinal is a quick bisection tool, not a durable key; visibility changes reorder draws.
Always preserve the original desktop draw while an isolation mode suppresses private replay.

**Two unrelated systems failing the same way is one bug upstream, not two bugs.** When independent
subsystems show an *identical signature*, raise the prior on a shared resource before triaging either.
(*SOMAVR's shadows and reflections are unrelated shader paths, but both showed left/right mismatch with
movement-dependent swimming. Treating the correlation as evidence pointed at AFR's shared per-frame
camera state as the common root — confirmed two releases later. Chasing them as two shader bugs would
have cost both investigations.*)

## Prove ownership by correlating two logs, without instrumenting either system

When you need to know whether subsystem A is driven by subsystem B — is the audio listener head-relative?
does the UI camera follow the player camera? — you do not need to reverse either one. **Log both over
time and look for one holding constant while the other moves.**

(*SOMAVR settled whether FMOD's listener was head-relative purely by logging. The HMD quaternion changed
strongly across two long frame ranges while the listener's forward/up vectors stayed pinned near constant
— moving only when the game's own authored camera changed. No audio-engine internals were touched, and
the conclusion was unambiguous.*)

This is the cheapest ownership test there is: zero invasion, no hooks inside the system under
question, and it produces a *falsifiable* pattern rather than an impression. Run it before writing any
correction code, because the correction you'd write for "A follows B" is worthless if A actually follows C.
