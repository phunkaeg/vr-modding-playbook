# Using this playbook

**Read this file. Do not read the playbook.**

It is ~213,000 words across 40 documents. About 10% of that is a retrieval layer built
specifically so you never open the other 90%. A normal lookup is one table row plus one
linked section — a few hundred words. Reading a chapter end to end is almost always the
wrong move, and reading several is a sign you skipped the routing below.

---

## Route by what you have

| What you have | Go to | Why |
|---|---|---|
| **A symptom** — something looks or behaves wrong | [`docs/failure-atlas.md`](docs/failure-atlas.md) | 255 rows: symptom → *fast discriminator* → likely cause → route. The discriminator is the point: it is chosen to be cheap. |
| **A symptom, but you want the chapter** | [`docs/symptom-index.md`](docs/symptom-index.md) | 205 rows mapping what you see to the chapter that covers it |
| **A solved problem you need the recipe for** | [`docs/pattern-catalog.md`](docs/pattern-catalog.md) | 114 atomic patterns, stable IDs, five fixed fields each |
| **A new or inherited target** | [`docs/start-new-port.md`](docs/start-new-port.md) | The router. Classifies integration authority first, then sends you down the RE-owned or source-owned route |
| **Several plausible next steps** | [`docs/bottleneck-map.md`](docs/bottleneck-map.md) | The earliest uncleared dependency, in order. Its *Agent operating protocol* section is worth reading once. |
| **A question of "has anyone solved this?"** | [`docs/cross-project-index.md`](docs/cross-project-index.md) | Who solved what, and where the raw working lives |
| **A target whose engine/API you know** | `python tools/prior_art.py <engine> <api>` | Matching prior art from 98 tracked sources, with what was harvested and what is thin |
| **Maths you are about to write yourself** | `docs/a1`–`a5` | Working code with the test that catches the error. Rotation, pose pipeline, stereo projection, hook safety, noise floor. |
| **A term used oddly** | [`docs/glossary.md`](docs/glossary.md) | Camera, pose, stereo, lifecycle, render and evidence vocabulary |
| **"Did another project already hit this?"** | `graphify query "<question>" --graph cross-engine-graph/graphify-out/reconciled-graph.json` | A concept-linked graph over SS2VR, BioshockVR and SOMAVR documentation |

**On that graph, in short:** it tells you *where* a problem was solved — which project, which document,
which named symbol — and never *what the answer was*, so treat every hit as a lead and go read the
document it names. Cross-project edges are tagged `same_concept_as` with the reason they were linked, so
you can reject a bad link on sight. It indexes **documentation, not code**, and it is a **snapshot**:
absence means nobody wrote it down, or wrote it after the build. Rebuild and extension instructions are
in [`cross-engine-graph/README.md`](cross-engine-graph/README.md).

**If the first stereo image will not fuse**, skip all of the above and go straight to the
[five-minute alignment diagnosis](docs/09-d3d11-openxr-injection.md). Every project in the
fleet hit it and none recognised it first time.

## Two ID namespaces, deliberately distinct

- `CAM-001` — a **pattern**: a reusable recipe in the pattern catalog.
- `FAIL-CAM-001` — a **failure record**: a symptom row in the failure atlas.

They are never the same record. Cite the qualified form for failures. IDs are permanent and
are never recycled; a retired pattern keeps its ID and gains a status note.

## Three orthogonal axes

Knowing one tells you little about the others, and conflating them causes bad estimates:

- **Mode** — how you build it (injector, managed plugin, framework companion, source port,
  engine recreation). See chapter 18.
- **Stereo rung** — how the second eye is produced (`R1` native re-entry … `R4` reconstruction).
- **Completeness tier** — how much of the game becomes VR (`T0`–`T4`). See chapter 08.

A source port can ship at T1; an injector can reach T4.

---

## If you are working on a fleet project

Paste this into the project's own `AGENTS.md` and `CLAUDE.md`:

> **Playbook:** `D:\Dev Debug\VR Modding\` — read its `AGENTS.md` first, never the chapters
> end to end. Route by symptom (`docs/failure-atlas.md`), by recipe
> (`docs/pattern-catalog.md`), or by earliest blocker (`docs/bottleneck-map.md`). Cite pattern
> IDs (`CAM-001`) and failure IDs (`FAIL-CAM-001`) in this project's own docs so findings stay
> traceable in both directions.

Before acting on the playbook's picture of *your* project, **verify it against your own
current state**. The fleet ledgers summarise; your project's receipts are authoritative. If
they disagree, your receipts win — and say so, so the ledger gets fixed rather than quietly
diverging.

## If you are contributing back

**Grade every claim.** `SPEC` normative API fact · `SOURCE` read in the project's own source ·
`STATIC` binary/static RE · `LIVE` observed at runtime · `HEADSET` accepted in a headset ·
`AUTHOR` the author's claim, unchecked · `INFERENCE` transferable hypothesis, not established
on this target.

*Known limitation:* `LIVE` currently spans three different things — your code running inside
the target, external tools observing the target, and real-hardware measurement with no target
process at all. If your evidence is not in-game, say so in the note; do not let the grade imply
it.

**Preserve ambiguous outcomes as ambiguous.** Do not promote a maybe to a confirmed or a
refuted. A negative result with its reason attached is worth as much as a positive one, and
costs a session to re-derive if you drop it.

**Never hand-edit anything under `docs/generated/`.** It is produced from `sources.yml` and
`bottlenecks.yml`. Edit the ledger, then regenerate.

**Validate before you claim it works:**

```
python tools/verify.py
```

Five checks — source ledger, bottleneck ledger, retrieval-ID integrity, strict site build,
and every internal anchor. One line each, correct exit code.

Do **not** pipe validators through `tail` or `head` to trim their output. A shell pipeline
returns the *pipe's* exit status, so a failing check reports success. That mistake hid a real
regression here for an entire session. `verify.py` exists so there is no reason to.

## What not to do

- Do not read chapters end to end to "get up to speed". Route instead.
- Do not add a fact in a second place. Routers route, workflows establish authority, the spine
  owns artifacts and exit proofs, chapters own technical method, project receipts own
  target-specific facts. If a summary and a chapter disagree, **the chapter is authoritative**.
- Do not treat a source oracle as the shipping target. An SDK, an open ancestor, a sibling
  engine or a decompilation can name things correctly and still be the wrong bytes. Confirm
  against the shipping binary before relying on a layout, an address or an ABI.
- Do not mark a bottleneck cleared because code exists. Clear it when its named exit proof
  passes on the target whose row is changing.
