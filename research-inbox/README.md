# Research contribution inbox

Use [the receipt workflow](../docs/research-receipts.md). The tool writes immutable
candidate packets in `pending/` and editorial decisions in `reviews/`. Raw artifacts
stay in the owning project. No pending finding is a canonical rule. An empty inbox
is a normal queue state, not a successful evidence check.

`pending/` and `reviews/` are local, gitignored working records. Publish a reviewed
digest with receipt IDs, evidence limits and canonical destinations under `briefs/`;
do not upload the raw external archive or project-local artifacts as part of a harvest.
The 2026-09-10 harvest is recorded in
[the fleet digest](../briefs/fleet-harvest-2026-09-10.md).
