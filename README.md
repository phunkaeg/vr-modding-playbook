# VR Modding Playbook

Build and debug flat-to-VR conversions using evidence-graded recipes, cheap
diagnostic tests, and lessons from multiple game engines. For human developers
and AI agents, the aim is the same: **find the next useful proof without
rediscovering another project's dead ends.**

This is an engineering reference, not an installer or a universal VR injector.
Read the section that answers your question, not the whole playbook.

## Start with what you have

| Your situation | Start here |
|---|---|
| Starting research from zero, or inheriting a port | [Start or unblock a VR port](docs/start-new-port.md) |
| Something looks or behaves wrong | [Failure atlas](docs/failure-atlas.md): symptom → cheap discriminator → likely cause → technical method |
| You need an implementation recipe | [Pattern catalog](docs/pattern-catalog.md): reusable recipes with stable IDs |
| Several problems compete for attention | [Bottleneck map](docs/bottleneck-map.md): find the earliest uncleared dependency |
| You want to know who already solved it | [Cross-project index](docs/cross-project-index.md) and [coverage dashboard](docs/coverage.md) |
| You need tested transform or stereo maths | [Reference code](reference/) and [rotation/frames appendix](docs/a1-rotation-and-frames.md) |

**AI agents:** read [AGENTS.md](AGENTS.md) and the target project's instructions
before acting. Human readers can use the routes above directly. No installation
is needed to read the Markdown files.

## Two integration routes, one shared engineering core

- **[Reverse-engineered — primary route](docs/reverse-engineered-route.md):**
  the shipping camera/render code is closed. Identify the target, prove its
  owners and ABI, find a reversible integration seam, and anchor it safely.
- **[Source-owned](docs/source-owned-route.md):** you can build, modify and
  ship the code owning the camera and world-render loop. Establish a matching
  baseline and integrate through that source.
- **[Shared VR engineering](docs/shared-vr-spine.md):** both routes still need
  coherent poses, stereo, culling, OpenXR lifecycle, input, hands, UI,
  performance and release proofs.

An SDK or open-source engine ancestor may be an oracle without being the code
you can ship. [Classify that boundary first](docs/start-new-port.md).

## What a lookup looks like

**Problem:** your stereo validator passes at neutral, then rejects the eyes
when the player turns their head.

Find `FAIL-TEST-037` in the [failure atlas](docs/failure-atlas.md). Its cheap
discriminator is a known-valid rotated/canted fixture. The linked
[geometry checks](docs/09-d3d11-openxr-injection.md#write-these-assertions-now-not-after-the-first-headset-session)
explain why world-X ordering and parallel-eye assumptions can reject valid
runtime poses. Test the instrument before rewriting the renderer.

That is the intended workflow: **symptom → discriminating test → scoped recipe
→ proof on your target.**

## What the evidence does — and does not — establish

The [coverage dashboard](docs/coverage.md) records the in-house fleet, external
prior art, review depth and stale snapshots. A solve on one engine is a lead
for another, not proof that its offsets, ABI or behavior transfer.

Claims distinguish source inspection (`SOURCE`), binary analysis (`STATIC`),
runtime observation (`LIVE`) and headset acceptance (`HEADSET`), alongside
specification facts, author claims and inference.
[The evidence vocabulary](docs/start-new-port.md#the-evidence-vocabulary)
defines the full set. A harness or substitute-runtime result is not headset
acceptance; preserve its environment and any ambiguous or failed baseline.

The optional [cross-engine documentation graph](cross-engine-graph/README.md)
helps locate project documents. It is a snapshot of in-house documentation,
not an exhaustive index of external mods. Graph hits are leads, not evidence.
Some underlying receipts and raw captures remain in project-local trees and
are not included in this repository.

## Contribute a finding or a failed approach

Follow [research receipts](docs/research-receipts.md): **record project-owned
evidence → validate and submit a candidate → editorial review → update the
canonical recipe.** Record what the result does not prove, baseline health,
dead ends and the next useful test. Submission alone never promotes a claim
or clears a bottleneck.

For a worked harvest, see the [September 10 fleet digest](briefs/fleet-harvest-2026-09-10.md).

## Preview and validate changes

The tested validation setup is **Windows, Python 3.12, and Visual Studio 2022
Build Tools with the C++ toolchain**. Run these commands from the repository
root in PowerShell, one at a time; stop if a command fails. Set `$vrPython`
to your actual Python 3.12 executable; the example uses the standard per-user
Windows install location:

```powershell
$vrPython = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
& $vrPython --version
& $vrPython -m pip install -r requirements.txt
.\reference\build-and-test.bat
& $vrPython tools/verify.py --portable
```

An explicit interpreter avoids an older `python`, an unconfigured pyenv shim,
or a `py` launcher that does not detect your installed runtime.
Building the reference tests is required for verification, not for reading.

`--portable` is the standalone-clone/CI route: it skips source coverage,
interaction coverage and instruction-pair checks requiring sibling project
trees. It still runs the reference tests, integration tests, ledger/ID checks,
site build and link checks. For maintainers with the configured source trees,
run the full gate:

```powershell
& $vrPython tools/verify.py
```

Do not hand-edit generated views. After changing `sources.yml` or
`bottlenecks.yml`, run the matching generator before verification:

```powershell
& $vrPython tools/coverage.py
& $vrPython tools/bottlenecks.py
```

The coverage generator requires the configured source trees. Active edits to
those trees can stale its snapshot between generation and checking; that is
a freshness warning to resolve, not a reason to disable the check.

For a searchable local reading view, after installing the Python dependencies:

```powershell
& $vrPython -m mkdocs serve
```

## License

Dual-licensed: the prose is **CC BY 4.0**, the code in `tools/`, `tests/` and the
embedded samples is **MIT**. See [LICENSE](LICENSE).

This covers the playbook's own content. The ~107 external projects it studies are
described, not redistributed, and each keeps its own terms — recorded per-source in
[sources.yml](sources.yml) and summarised in [NOTICE.md](NOTICE.md). Three are not
open source; read NOTICE.md before copying anything from a cited project.
