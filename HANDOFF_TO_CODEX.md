# Handoff to Codex — 2026-08-27

Counterpart to `CLAUDE_CHAT_HANDOFF.md`. One bug in `tools/coverage.py` that is yours to decide on,
plus an inventory of what was added today so nothing surprises you.

---

## Bug: `coverage.md` is counted in its own corpus metric

**Symptom.** `coverage.py --check` intermittently reports `docs\coverage.md` stale *immediately after a
successful regeneration*. It cost several false diagnoses today before I isolated it.

**Cause.** `reader_corpus_metrics()` (around line 325) walks `docs/**/*.md` and excludes only
`generated/`:

```python
files = [
    path
    for path in docs_root.rglob("*.md")
    if "generated" not in path.relative_to(docs_root).parts
]
```

`docs/coverage.md` is generated output but does **not** live under `generated/`, so it counts itself. The
metric is therefore self-referential:

1. a chapter is edited — the corpus changes;
2. regen computes the word count, then **writes `coverage.md`**, which changes the corpus again;
3. `--check` recomputes, sees a different total, and calls the file stale;
4. a **second** regen reaches a fixed point.

**Evidence it is this and not non-determinism.** Two consecutive regens produced **identical SHA-256
hashes** for `docs/coverage.md`, and `--check` passed immediately afterwards. The generator is
deterministic; it simply needs one extra iteration after any docs change.

**Suggested fix**, though the call is yours since it alters a reported number:

```python
    if "generated" not in path.relative_to(docs_root).parts
    and path.name != "coverage.md"
```

`coverage.md` is generated output rather than reader-written prose, so excluding it is consistent with
how `generated/` is already treated — and it makes the metric converge in one pass.

**Second, smaller note.** A full `coverage.py` regen takes **~180 s** on an idle machine. The source scan
across all 50 roots is only **10.4 s** (measured per-root), and `--check` alone runs in ~9 s, so roughly
170 s is elsewhere in the regen. I did not isolate it and am not guessing: my working hypothesis is the
untracked-directory detection walking the whole `Other VR mods` tree, which grew a lot today
(Shipwright-VR alone is 11,998 files). Worth a profile if regen time starts to matter.

---

## Added today — tool inventory

| Tool | Purpose |
|---|---|
| `tools/verify.py` | Runs all checks, one line each, correct exit code. Exists because piping validators through `tail` returns the *pipe's* status and hid a failing check for a whole session. Also adds an **anchor audit** — `mkdocs --strict` validates linked pages, not `#fragments`; 247 anchor links had never been checked. |
| `tools/prior_art.py` | Fingerprint (engine/API) → matching sources from `sources.yml`, with what was harvested and what is thin. |
| `tools/build_public.py` | Builds a shareable site variant to `site-public/` with the internal status report removed, and **fails the build** if any banned string survives into the output. |
| `tools/reconcile_graphs.py` | Adds cross-project edges between per-project graphify graphs. `merge-graphs` is a union and creates none. |
| `serve-shared.bat` / `host-shared.bat` | Serve or tunnel the shareable variant; both refuse to run if the sanitise check fails. |
| `graphify-key.bat` | Loads the Gemini key into one shell and launches a command with it. Propagates the child's exit code. |

`docs-check.bat` is untouched.

## Conventions followed

- **`FAIL-` namespace adopted.** All new atlas rows use it; pattern IDs keep the short form.
- **Generated fragments never hand-edited.** Ledger edited, then regenerated.
- **Ambiguous outcomes preserved as ambiguous** — e.g. `CallOfDuty4_VR.stereo` is `partial` with a note
  that `vr_openxr.cpp` is 25k lines and unread, rather than being marked done.
- Ledger grew from **40 to 53 external sources**; `0 untracked`.

## One schema question left open

DishonoredVR argues the `evidence` vocabulary needs a value **below `LIVE`**, because `LIVE` currently
spans three different things: our code running inside the target, external tools observing the target,
and real-hardware measurement with **no target process at all** (their D3D9→D3D12 interop probe).

Measured: 43 `LIVE`-graded bottleneck rows, and Sims4VR carries seven at pre-feasibility — including
`BN-LOAD-001` graded `LIVE` with the note *"there is no mod build yet"*. So a fleet view asking "which
projects have reached the game" answers wrong today.

I did not change the enum — it is controlled in two ledgers with two validators and a new value implies
regrading 43 rows. Flagging it as yours.
