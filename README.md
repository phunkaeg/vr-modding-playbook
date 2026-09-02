# VR Modding Playbook

An evidence-graded engineering playbook for building and debugging VR ports
across multiple engines, graphics APIs, and integration styles.

This repository is primarily a retrieval system, not a book to read from start
to finish. Start with [`AGENTS.md`](AGENTS.md), which routes a symptom, known
engine/API, solved problem, or current bottleneck to the smallest relevant
section.

## Main entry points

- [`docs/failure-atlas.md`](docs/failure-atlas.md) — observed symptom to fast
  discriminator, likely cause, and technical route.
- [`docs/pattern-catalog.md`](docs/pattern-catalog.md) — reusable implementation
  and debugging recipes with stable IDs.
- [`docs/start-new-port.md`](docs/start-new-port.md) — onboarding for a new or
  inherited target.
- [`docs/bottleneck-map.md`](docs/bottleneck-map.md) — choose the earliest
  uncleared dependency instead of the most visible problem.
- [`docs/cross-project-index.md`](docs/cross-project-index.md) — locate prior art
  and the project receipts behind it.

The cross-engine documentation graph is described in
[`cross-engine-graph/README.md`](cross-engine-graph/README.md). Its results are
leads with provenance; project receipts remain authoritative.

## Validate changes

Install the small Python dependency set, then run the repository gate:

```powershell
python -m pip install -r requirements.txt
python tools/verify.py
```

The reference maths tests can be rebuilt separately with:

```powershell
reference\build-and-test.bat
```

Do not edit files under `docs/generated/` directly. Update the owning ledger
and regenerate them.

## Evidence language

Claims are graded as `SPEC`, `SOURCE`, `STATIC`, `LIVE`, `HEADSET`, `AUTHOR`,
or `INFERENCE`. Preserve ambiguous findings as ambiguous, and clear a
bottleneck only when its named exit proof passes on the target.
