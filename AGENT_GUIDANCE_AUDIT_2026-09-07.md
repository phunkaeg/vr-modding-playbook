# Agent guidance audit — 2026-09-07

Reviewed the AGENTS.md/CLAUDE.md pairs for all ten native VR mods listed in the
fleet's `sources.yml`, the shared playbook pair, general Claude instructions and
Codex instruction location, and both hosts' three shared RE/delegation skills.
This is an instruction consistency audit, not a benchmark of agent accuracy.

## Result and rationale

- [AGENT_RE_WORKFLOW.md](AGENT_RE_WORKFLOW.md) is the shared method: current gate,
  cheapest discriminating proof, target identity, receiver/ABI/vtable provenance,
  producer-to-consumer tracing, positive controls, and durable receipts.
- Removed fixed server counts, claims that Codex cannot read skills, universal
  startup-order requirements, and automatic user launch requests on tool failure.
  The current session's schemas, host health and selected target are separate checks.
  Existing authorization and project-specific runtime restrictions still govern actions.
- Static evidence can close a static question. Runtime execution, input acceptance,
  rendered-camera correctness and headset quality retain separate proof requirements.
  A passing xr-tape submission check does not establish correct scene rendering.
- Consolidated obsolete fleet-graph narratives around the current `fleet-graph.json`
  route. Graphs provide provenance leads; empty retrieval is not an absence proof.
  Exact-symbol searches use scoped rg. Graph setup/rebuild is not an unrelated blocker.
- Corrected stale BioShock first-implementation and Sims 4 pre-feasibility instructions
  using their current-state receipts. Future work starts from current code and evidence.
- Reconciled newer Claude skill procedures into both hosts' copies. Concise entrypoints
  link to detailed references preserving measured emulation, matching, capture and ABI
  failures. Historical observations are explicitly scoped; they were not rerun here.
- Local delegation is optional and verified. Removed claims that a model's lack of a
  thinking mode makes it safe, unqualified exhaustive-search claims, and blanket
  process-killing cleanup that could stop another agent's work.

## Preserved target rules

SS2/BioShock hardware-breakpoint restrictions, SS2 logging/config safeguards,
SOMA's source/feature maps, Prey's CryEngine/H-021 procedures, Dishonored's native
D3D9 distinction, Far Cry 2's image profiles and affinity/dxgi trace runbook,
SWAT4's per-executable addresses and script/config contracts, Sims' deferred-context
capture caveats and removable mod, SoF's opaque renderer ABI, and MoH's source-owned
route remain. MoH still requires explicit permission for every game launch, including
substitute runs; its retail-directory and upstream-PR restrictions are unchanged.

## Entry-point footprint

UTF-8 draft bytes, before preserving each destination's newline convention:

| Repository | Pair before (bytes) | Pair after (bytes) |
| --- | ---: | ---: |
| ss2vr-work | 29036 | 19361 |
| BioshockVR | 18651 | 10299 |
| SOMAVR | 16547 | 5995 |
| PreyVR | 17694 | 6854 |
| DishonoredVR | 15692 | 5823 |
| FarCry2-vr | 20890 | 14791 |
| Swat4-VR | 18196 | 11063 |
| Sims4VR | 12142 | 7590 |
| SoF-VR | 12314 | 9714 |
| Medal-of-Honor-vr | 8442 | 8879 |
| VR Modding | 9288 | 9435 |

Combined repository entry points: 178,892 → 109,804 bytes
(38.6% smaller). The shared method is read once per
RE approach; skill reference details are loaded only for the selected procedure.
General instructions remain short and scope their RE defaults to RE tasks.

## Instruction loading

Codex can read SKILL.md files and uses global/project AGENTS.md instructions; its
documented chain has a default size limit. The project pairs now explicitly tell
either reader to read the other file once, without assuming identical automatic
loading behavior. See [Codex instruction guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

Claude's CLAUDE.md files are instructions in context, not enforced permissions.
Concise, specific, non-conflicting guidance is the intended use. Ordinary path
references avoid introducing external `@` imports and their first-use approval flow.
See [Claude memory guidance](https://code.claude.com/docs/en/memory).

## Validation and recovery

Validation output is retained in
`D:/Dev Debug/PreyVR/captures/guidance-audit-2026-09-07/validation.json`.
The audit checks all ten mounted fleet pairs, skill frontmatter and reference anchors,
prohibited stale claims, key preserved restrictions, matching host skill copies,
and hashes of every destination before and after installation. It rejects a skipped
fleet audit rather than reporting it as a pass.

Original bytes, exact prepared drafts and `manifest.json` are preserved in that
same directory. `install_guidance.py` preflights every original hash before writing
any file and rechecks each destination immediately before replacement. If another
agent changes a target, installation stops rather than overwriting that change.
No game code, binaries, runtime/MCP configuration, live sessions, commits or pushes
are part of this audit. Restart affected agent sessions to load the revised entry
instructions and skill descriptions; existing sessions may retain earlier context.
