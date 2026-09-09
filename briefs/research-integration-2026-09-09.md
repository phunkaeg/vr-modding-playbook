# MonsterDeadWood research workflow integration — 2026-09-09

## Delivered

The Bible's postflight method now has a project-owned receipt format and a validated
playbook intake queue. Start at [the canonical workflow](../docs/research-receipts.md).
This is an explicit contribution workflow, not a background scraper or auto-publisher.

- `tools/research_receipt.py`: draft, hash, validate, submit, list and editorial review.
  Raw artifacts stay in the owning project. Identical submissions are idempotent;
  conflicting run IDs fail. Acceptance rechecks original-receipt and artifact hashes.
- Validity, fact verdict, baseline health, observation environment and evidence grade
  are separate fields. INVALID cannot confirm/refute. Baseline failure does not erase
  a valid observation or approve a build. Negative approaches include reopening conditions.
- `tools/research_checks.py`: bounded numerical camera-mapping analysis and strict
  same-frame eye metadata checks. Empty or incomplete input cannot pass. Neither
  checker establishes camera ownership, correct stereo geometry or headset acceptance.
- [Numerical camera-mapping recipe](../docs/11-re-anchoring-and-discovery.md#numerical-camera-mapping):
  controlled signed perturbations, explicit dimensions, derivative noise tolerances,
  held-out predictions and restoration. RE-owned and source-owned applicability is explicit.
- `tools/verify.py`: clean/broken/absent-input regression controls for its nine original
  checks, plus a tenth check that runs the integration suite. Zero tests cannot pass.
  `docs-check.bat` now uses this canonical verifier instead of a smaller parallel checklist.
- The Bible has a partial, SOURCE-graded entry in `sources.yml`, pinned to the measured
  `01_BIBLE/SPLIT` fingerprint `tree:00139a13544026eb`. Permission is recorded as relayed
  by the user, not asserted as a blanket licence for third-party material.

No donor addresses or reported success counts became fleet facts. No synthetic fixture
was submitted as research. No game was launched, no bottleneck cleared, and no fleet graph
was rebuilt. Existing project documentation remains authoritative for target-specific facts.

## Agent rollout

26 files installed and SHA-256 checked:

| Surface | Updates |
|---|---|
| Ten fleet projects | Both `AGENTS.md` and `CLAUDE.md` receive a short contribution route: 20 files |
| Codex global instructions | `C:/Users/meise/.codex/AGENTS.md` |
| Claude global instructions | `C:/Users/meise/.claude/CLAUDE.md` |
| Existing workflow skills | `vr-re-workflow/SKILL.md` in both desktop skill directories |
| New focused skill | `vr-research-receipts/SKILL.md` in both desktop skill directories |

Projects: SS2VR (`ss2vr-work`), BioShockVR, SOMAVR, PreyVR, DishonoredVR,
FarCry2-vr, SWAT4-VR, Sims4VR, SoF-VR and Medal-of-Honor-vr.
No root `CODEX.md` files were present in these projects; the existing instruction pairs
were updated rather than introducing a competing rule file. All prior project instructions,
including runtime restrictions and source-owned OpenMoHAA rules, were preserved.

The shared playbook `AGENTS.md`, `CLAUDE.md` and `AGENT_RE_WORKFLOW.md` also route to
the integration. The skill-creator guidance kept the new skill focused on substantial
findings and contributions, rather than imposing receipt work on every edit.

Installation source: `tools/agent-guidance/`; installer: `tools/install-research-guidance.ps1`.
Original external files, staged replacements and before/after hashes are preserved locally
in `D:/Dev Debug/VR Modding/.guidance-staging/20260909-integration/manifest.json`
and its numbered `.original` / `.draft` files. This directory is ignored by Git.
Do not blindly restore a backup over later agent edits; compare current hashes first.

A currently running agent is not retroactively given new instructions. Ask it to read
the canonical workflow, or start a fresh session so the updated skill catalog can be loaded.

## Verification observed

Interpreter: `C:/Users/meise/AppData/Local/Programs/Python/Python312/python.exe`.

- `python -m unittest discover -s tests -v`: **22 tests passed**.
- `python tools/verify.py`: **all 10 checks passed**.
- Real compiled reference suite: **28 tests, 95,559 checks passed**.
- Strict MkDocs build passed; anchor audit checked **818 links across 42 files**.
- Installer `-Mode Check`: **26 files matched the installation manifest**.
- Skill creator's `quick_validate.py`: **all four installed skill files validated**.

The unit controls for external compiler/site processes simulate verdict propagation;
the full verifier separately ran the actual existing reference executable and site build.
These results establish the plumbing and offline checks, not any game's runtime outcome.

## First use

At the next substantial finding, its owning agent records the evidence while fresh and
submits a candidate. A reviewer inspects those artifacts, updates the existing owning
chapter or ledger, regenerates outputs as needed, runs the verifier and records the decision.
Until that happens, the intake queue is legitimately empty. Use an already-authorized
investigation for the first real receipt; this integration grants no new launch authority.
