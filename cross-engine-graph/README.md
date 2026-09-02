# Cross-Engine Docs Graph

A knowledge graph over the **documentation** of three in-house VR conversions — SS2VR (Dark/KEX, D3D11),
BioshockVR (Unreal 2.5 Vengeance, D3D11) and SOMAVR (HPL3, OpenGL) — built so that a question asked of
one project can reach the others.

> **Scope warning.** This is not the playbook's coverage engine. The authoritative source and harvest
> ledger is `..\sources.yml`, rendered in `..\docs\coverage.md`. This graph holds three projects only and
> must never be used to conclude that no *other* project solved a problem.

---

## Use this graph

**Cross-project questions — use `reconciled-graph.json`:**

```
graphify query "<question>" --graph "graphify-out\reconciled-graph.json" --budget 900
```

**One project only — use its own graph** (smaller, no cross-links to distract):

```
graphify query "<question>" --graph "per-project\<somavr|ss2vr|bioshockvr>\graphify-out\graph.json"
graphify path    "A" "B"   --graph <path>      # how two things connect
graphify explain "X"       --graph <path>      # a node and its neighbourhood
graphify affected "X"      --graph <path> --depth 2   # what a change would touch
```

Cross-project edges carry `relation: same_concept_as` plus the concept name and a one-line reason, so you
can see **why** two projects were linked and reject the link if it looks wrong.

**What it is for:** finding *where* a problem was solved — which project, which document, which named
symbol. **What it is not for:** telling you *what the answer was*. Go read the document it names. Every
node is a lead with provenance, not evidence.

---

## Rebuilding it

Three stages. Total cost **~$1.50** on Gemini flash; the reconciliation stage alone is ~$0.013, so
iterate on that freely and avoid re-running stage 2.

### 1. Stage the corpus (free)

```
bash stage_corpus.sh
```

Copies each project's top-level `docs/*.md` into `corpus/<project>/`, excluding the giant chronological
`USER_TEST_LOG.md` files as noise. Currently 141 files, ~702k words.

### 2. Extract per project — never one big corpus

```
graphify-key.bat graphify extract "<abs>\corpus\somavr"     --backend gemini ^
  --out "<abs>\per-project\somavr"     --max-concurrency 2 --token-budget 20000
```

…and the same for `ss2vr` and `bioshockvr`.

**Both flags are load-bearing, and the defaults are wrong for this corpus:**

- **`--token-budget 20000`.** At the 60k default the model returned successful responses that **silently
  omitted 21 of 25 files**. Yield went from 1.9 to 32.7 nodes per 10k words when reduced. The omitted
  files were the *small* ones, packed many-to-a-chunk — a long multi-document prompt gets partial
  attention and nothing in the exit code says so. Smaller chunks cost ~4x the input tokens; pay it.
- **`--max-concurrency 2`.** Free-tier Gemini caps input tokens per minute; higher concurrency loses
  chunks to `429`. (The free tier also caps **20 requests per day**, which no amount of scheduling gets
  around — billing must be enabled.)

**Per project, not one corpus:** graphify derives node IDs from source path plus entity name, so a
combined run produces collisions and **silently drops the loser**. Per-project runs also let you check
each yield before trusting the whole.

**Check before proceeding:** node yield per 10k words should be broadly comparable across projects, and
*files dispatched* should roughly equal *files represented*. Graphify prints a `WARNING: n/m dispatched
file(s) produced no nodes` line — read it.

### 3. Reconcile — this is the step that creates cross-project edges

```
graphify-key.bat <graphify-python> tools\reconcile_graphs.py
```

`<graphify-python>` is the uv tool venv interpreter (it has the `openai` package;
your system Python does not) — typically
`%AppData%\Roaming\uv\tools\graphifyy\Scripts\python.exe`.

**Do not use `graphify merge-graphs` for this.** It is a **union**: it stacks node sets and creates no
edge between projects. Measured, it produced exactly the sum of its inputs — 1328 nodes, 616 links, zero
cross-project. A query seeded in one project could never reach another.

Exact matching cannot substitute either: across 1328 nodes only **7 normalised labels recur across
projects, and 5 are document filenames**, while **74 concept tokens appear in all three**. The concepts
recur; the vocabulary does not.

---

## Measured results (2026-08-27)

| | Union (`merge-graphs`) | Reconciled |
|---|---|---|
| Nodes | 1328 | 1328 |
| Links | 616 | **651** (35 cross-project) |
| Components | 724 | **696** |
| Largest component | 52 (3%) | **149 (11%)** |
| Cross-project query | impossible | **works** |

Fifteen concepts linked: frustum/culling, stereo strategy, depth submission, HUD layering, viewmodel
posing, interaction raycasting, haptics, recentre, roomscale, comfort vignette, melee, input mapping,
shadow stability, OpenXR integration, injection.

Per-project extraction cost: somavr $0.27, ss2vr $0.72, bioshockvr $0.46.

---

## Traps, all paid for once already

**Reconciliation coverage is the whole game.** A cautious prompt returned 10 groups covering 2% of nodes
— the mechanism worked and a culling query *still* failed, because culling was not among the ten. Telling
the model to be exhaustive and naming the concept areas to sweep took it to 15 groups and made the query
work. **A reconciliation that runs is not a reconciliation that covers.**

**On a reasoning model, `max_tokens` is a shared budget, not an output budget.** An exhaustive prompt
first returned truncated JSON; raising `max_tokens` made it *worse*. The usage told the story:
`prompt 14,902 + completion 641 = 15,543` against a `total` of **31,268** — the missing **15,725 were
reasoning tokens**, `finish_reason` was `length`. `reasoning_effort="low"` fixed it, which is what
graphify's own gemini config already sets. **When `prompt + completion` does not equal `total`, the gap
is thinking.**

**Validate every label the model returns.** On one run it invented five labels present in no graph; all
five were rejected before an edge was emitted. A false bridge is worse than a missing one — it creates a
path between two projects that never solved the same problem, and every later query inherits it.

**The graph indexes docs, not code.** A symbol is absent because nobody wrote it down, not because it
does not exist. And it is a snapshot — anything written since the build is missing.

Full write-up, including why a graph loses to a careful read for *synthesis*:
`..\docs\06-debugging-methodology.md#graph-cross-source-limit`.

---

## Extending to more projects

Stage the new project into `corpus/`, run stage 2 for it alone, then re-run stage 3 — reconciliation
reads whatever per-project graphs exist. Add the project to `PROJECTS` in `tools/reconcile_graphs.py`.

Before advertising this as a *fleet* graph rather than a three-project subset, stage every `active_mod`
in `..\sources.yml` and pin the reviewed revisions.
