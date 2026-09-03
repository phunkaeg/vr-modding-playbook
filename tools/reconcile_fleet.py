#!/usr/bin/env python3
"""Build the fleet cross-project graph: all eight in-house projects, namespaced,
with semantic edges that only ever join DIFFERENT projects.

WHY THIS REPLACES reconcile_graphs.py
-------------------------------------
The three-project prototype was right about the hard part and wrong about the
bookkeeping. It established the finding this whole stage rests on:

    the concepts recur; the vocabulary does not

Across 1,328 nodes only 7 normalised labels recurred between projects and 5 of
those were document filenames - while 74 concept tokens (stereo, camera, pose,
viewmodel, comfort...) appeared in all three. So a union can never bridge the
projects, and exact label matching cannot either. Only semantic resolution over
the labels can, which is cheap: ~2,000 short strings, not 700k words.

What it got wrong, all traceable to one omission - it never namespaced the IDs:

  * per-project graphs use bare IDs, so two projects' distinct nodes collide.
    Measured in the shipped artifact: 1,328 nodes, 1,322 distinct - six pairs of
    unrelated nodes silently fused into one.
  * "different project" was checked, but the edge was written between bare IDs,
    so a validated cross-project pair could emit source == target. The shipped
    artifact contains exactly that self-loop (openxr_runtime -> openxr_runtime).
  * nothing de-duplicated, so the same pair appears twice.
  * 35 same_concept_as rows were reported; 33 are usable.
  * nodes carry no project field, so the graph whose stated purpose is finding
    *where* a problem was solved cannot always say which project a node is from.

Namespacing fixes all four structurally: once every ID is "<project>::<id>",
a same-project edge and a self-loop are the same impossible thing.

USAGE
  graphify-key.bat python tools/reconcile_fleet.py            # build
  python tools/reconcile_fleet.py --offline                   # structure only, no LLM
  graphify-key.bat python tools/reconcile_fleet.py --dry-run  # propose, write nothing
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graphio import GraphSchemaError, load_graph, write_graph  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "cross-engine-graph" / "per-project"
OUT = ROOT / "cross-engine-graph" / "graphify-out" / "fleet-graph.json"
REPORT = ROOT / "cross-engine-graph" / "FLEET_RECONCILIATION.md"

MODEL = os.environ.get("GRAPHIFY_GEMINI_MODEL", "gemini-3-flash-preview")
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Engine identity matters to the resolver: it has to tell a genuine shared
# concept from two projects that merely use the same English word. Sourced from
# docs/generated/fleet-table.md, which is generated from sources.yml.
PROJECTS: dict[str, str] = {
    "ss2vr":        "System Shock 2 Remastered - Dark/KEX engine, D3D11, x64, stereo R2 per-draw replay",
    "bioshockvr":   "BioShock Remastered - Unreal 2.5 Vengeance, D3D11, x86, stereo R2 per-draw replay",
    "somavr":       "SOMA - HPL3 engine, OpenGL 4.6, x64, stereo R3 alternate-eye",
    "preyvr":       "Prey (2017) - CryEngine (Arkane), D3D11, x64, stereo route unproven",
    "dishonoredvr": "Dishonored - Unreal Engine 3, D3D9, x86, stereo route unproven",
    "farcry2vr":    "Far Cry 2 - Dunia engine, D3D10 (D3D9 selectable), x86, stereo R2 per-draw replay",
    "swat4vr":      "SWAT 4 - Unreal 2.5 Vengeance, D3D9, x86, stereo route unproven",
    "sims4vr":      "The Sims 4 - EA custom engine, D3D11, x64, script-owned, stereo route unproven",
}

SEP = "::"
# One request holds this many labels before the run is split into passes. Every
# pass carries a slice of EVERY project, because a pass containing one project
# can produce no cross-project edge at all.
BATCH_LABELS = 1200

PROMPT_HEAD = """You are reconciling entities across independent VR-mod documentation graphs.

Each project converts a different game to VR and names things in its own local vocabulary:
{roster}

Below are node labels, grouped by project.

Find groups where nodes from DIFFERENT projects denote THE SAME underlying VR-engineering concept -
the same problem, subsystem, technique or artifact - even though the wording differs.

Rules:
- A group MUST contain labels from at least two different projects. Same-project groups are useless here.
- Copy labels EXACTLY as given. Do not paraphrase, shorten or invent.
- Match on engineering concept, not on generic English. "Build History" and "Decision Log" are document
  types, not concepts - skip them. So are bare project names, version strings and file names.
- Two projects using the same graphics API is not a concept. Two projects solving the same *problem*
  in that API is.
- Give each group a short concept name and one sentence on WHY these are the same thing.

BE EXHAUSTIVE. Work through the whole list systematically rather than reporting only the obvious
matches. Every VR conversion of this kind shares dozens of concepts. Expect matches across at least
these areas, and others besides:

  stereo / per-eye rendering        camera and view ownership        culling and frustum
  projection and FOV                pose and tracking                recentre and calibration
  hands, weapons, viewmodels        input mapping and locomotion     UI, HUD and menus
  interaction and selection rays    comfort and vignette             audio and haptics
  render hooks and frame boundary   OpenXR/OpenVR lifecycle          performance and frame pacing
  build identity and logging        packaging and install            testing and harnesses

Precision still matters more than volume: a wrong link creates a false path between two projects that
never solved the same problem. But a concept that plainly recurs under different names is exactly what
you are here to find, so do not omit it out of caution.

Return JSON only:
{{"groups":[{{"concept":"...","why":"...","members":[{{"project":"...","label":"..."}}]}}]}}
"""


# ----------------------------------------------------------------- loading --

def load_fleet(only: list[str] | None = None) -> tuple[dict, list, list, list]:
    """Load every per-project graph and namespace it.

    Returns (graphs, nodes, links, hyperedges). Hyperedge MEMBERS are namespaced
    too - graphify drops any hyperedge whose members do not match a built node,
    so namespacing the nodes while leaving the members bare silently deletes
    every hyperedge in the fleet.
    """
    graphs, nodes, links, hyper = {}, [], [], []
    missing = []
    for pid in PROJECTS:
        if only and pid not in only:
            continue
        gp = BASE / pid / "graphify-out" / "graph.json"
        try:
            g = load_graph(gp)
        except GraphSchemaError as exc:
            missing.append(f"{pid}: {exc}")
            continue
        graphs[pid] = g

        for n in g.nodes:
            m = dict(n)
            m["original_id"] = n.get("id")
            m["id"] = f"{pid}{SEP}{n.get('id')}"
            m["project"] = pid
            nodes.append(m)
        for l in g.links:
            m = dict(l)
            m["source"] = f"{pid}{SEP}{l.get('source')}"
            m["target"] = f"{pid}{SEP}{l.get('target')}"
            m["project"] = pid
            m["scope"] = "intra"
            links.append(m)

        for h in g.hyperedges:
            m = dict(h)
            m["id"] = f"{pid}{SEP}{h.get('id')}"
            m["nodes"] = [f"{pid}{SEP}{n}" for n in h.get("nodes", [])]
            m["project"] = pid
            hyper.append(m)

    if missing:
        print("WARNING - project graphs that could not be read:")
        for m in missing:
            print("   -", m)
    return graphs, nodes, links, hyper


def build_index(graphs: dict) -> dict[tuple[str, str], str]:
    """(project, exact label) -> namespaced id. Model output is validated against this."""
    index: dict[tuple[str, str], str] = {}
    for pid, g in graphs.items():
        for n in g.nodes:
            label = str(n.get("label") or n.get("name") or n.get("id") or "")
            if label:
                index.setdefault((pid, label), f"{pid}{SEP}{n.get('id')}")
    return index


# ------------------------------------------------------------------- model --

def batches(graphs: dict) -> list[dict[str, list[str]]]:
    """Stratified passes: every pass carries a slice of every project."""
    per = {pid: [str(n.get("label") or n.get("id") or "") for n in g.nodes
                 if (n.get("label") or n.get("id"))]
           for pid, g in graphs.items()}
    total = sum(len(v) for v in per.values())
    npass = max(1, -(-total // BATCH_LABELS))
    out = []
    for k in range(npass):
        out.append({pid: labels[k::npass] for pid, labels in per.items()})
    return out


def ask(batch: dict[str, list[str]], roster: str) -> list[dict]:
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("the 'openai' package is required: uv tool install \"graphifyy[gemini]\" --force")

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        sys.exit("No GEMINI_API_KEY in the environment. Run this through graphify-key.bat.")

    listing = []
    for pid, labels in batch.items():
        if not labels:
            continue
        listing.append(f"\n### {pid}")
        listing.extend(f"- {l}" for l in labels)
    body = PROMPT_HEAD.format(roster=roster) + "\n".join(listing)

    client = OpenAI(api_key=key, base_url=ENDPOINT)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": body}],
        temperature=0,
        response_format={"type": "json_object"},
        max_tokens=32768,
        # Without this the model spends its budget on reasoning and truncates
        # the JSON mid-string; graphify's own gemini config does the same.
        reasoning_effort="low",
    )
    u = resp.usage
    print(f"   tokens: {u.prompt_tokens:,} in / {u.completion_tokens:,} out"
          f"   est ${u.prompt_tokens/1e6*0.5 + u.completion_tokens/1e6*3:.4f}")

    raw = resp.choices[0].message.content or ""
    try:
        return json.loads(raw).get("groups", [])
    except json.JSONDecodeError as exc:
        print(f"   response did not parse ({exc}); salvaging complete groups")
        groups, depth, start, instr, esc = [], 0, None, False, False
        for i, ch in enumerate(raw):
            if instr:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    instr = False
                continue
            if ch == '"':
                instr = True
            elif ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    try:
                        obj = json.loads(raw[start:i + 1])
                        if isinstance(obj, dict) and "members" in obj:
                            groups.append(obj)
                    except json.JSONDecodeError:
                        pass
                    start = None
        print(f"   salvaged {len(groups)} complete groups")
        return groups


# -------------------------------------------------------------- edge build --

def slug(text: str) -> str:
    keep = [c.lower() if c.isalnum() else "_" for c in text]
    return "".join(keep).strip("_").replace("__", "_")[:60] or "concept"


def edges_from_groups(
    groups: list[dict], index: dict
) -> tuple[list[dict], list[dict], list[dict], Counter, list[str]]:
    """Cross-project edges only, de-duplicated, self-loops impossible by construction.

    Also materialises each surviving concept as a NODE. graphify's query seeds by
    lexical match on labels, so a question phrased in plain English ("stop geometry
    being culled") matches nothing when the only nodes are engine symbols like
    cFrustum::SetupPerspectiveProj. Measured on this graph: that question seeded on
    ICEBREAKER and SwineInputHandler and never reached the concept at all, while
    "frustum culling" reached four projects immediately. A concept node carries the
    plain-English name and the reason, so the question lands on it and every
    project's implementation is one hop away.
    """
    edges: list[dict] = []
    concept_nodes: list[dict] = []
    concept_edges: list[dict] = []
    seen: set[tuple[str, str]] = set()
    seen_concepts: set[str] = set()
    stats = Counter()
    invented: list[str] = []

    for g in groups:
        resolved: list[tuple[str, str]] = []
        for m in g.get("members", []):
            k = (m.get("project"), m.get("label"))
            if k in index:
                resolved.append((k[0], index[k]))
            else:
                invented.append(f"{m.get('project')}: {str(m.get('label'))[:60]}")
                stats["member_invented"] += 1

        if len({p for p, _ in resolved}) < 2:
            stats["group_single_project"] += 1
            continue
        stats["group_kept"] += 1

        for i in range(len(resolved)):
            for j in range(i + 1, len(resolved)):
                pi, ni = resolved[i]
                pj, nj = resolved[j]
                if pi == pj:
                    stats["edge_same_project"] += 1
                    continue
                if ni == nj:                      # unreachable once namespaced
                    stats["edge_self_loop"] += 1
                    continue
                key = (ni, nj) if ni < nj else (nj, ni)
                if key in seen:
                    stats["edge_duplicate"] += 1
                    continue
                seen.add(key)
                edges.append({
                    "source": ni, "target": nj,
                    "relation": "same_concept_as",
                    "scope": "cross",
                    "concept": g.get("concept", ""),
                    "why": g.get("why", ""),
                    # graphify's schema validator accepts only AMBIGUOUS /
                    # EXTRACTED / INFERRED. The playbook's own evidence taxonomy
                    # calls this grade INFERENCE, so carry both rather than
                    # silently failing validation or losing the playbook term.
                    "confidence": "INFERRED",
                    "evidence_grade": "INFERENCE",
                    "provenance": "reconcile_fleet.py",
                })
                stats["edge_kept"] += 1

        # Materialise the concept itself, once, and hang every member off it.
        name = (g.get("concept") or "").strip()
        if not name:
            continue
        cid = f"concept{SEP}{slug(name)}"
        if cid not in seen_concepts:
            seen_concepts.add(cid)
            concept_nodes.append({
                "id": cid,
                "label": name,
                "norm_label": name.lower(),
                "description": g.get("why", ""),
                "project": "concept",
                "file_type": "concept",
                "source_file": "FLEET_RECONCILIATION.md",
                "_origin": "reconcile_fleet",
                "community": 0,
            })
            stats["concept_node"] += 1
        for _, nid in resolved:
            key = (cid, nid)
            if key in seen:
                continue
            seen.add(key)
            concept_edges.append({
                "source": cid, "target": nid,
                "relation": "instance_of",
                "scope": "concept",
                "concept": name,
                "confidence": "INFERRED",
                "evidence_grade": "INFERENCE",
                "provenance": "reconcile_fleet.py",
            })
            stats["concept_edge"] += 1

    return edges, concept_edges, concept_nodes, stats, invented


# ----------------------------------------------------------------- report ---

def coverage_report(graphs: dict, nodes: list, intra: list, cross: list,
                    cnodes: list, cedges: list, stats: Counter, invented: list) -> str:
    pids = list(graphs)
    pair = Counter()
    touched = Counter()
    for e in cross:
        a = e["source"].split(SEP, 1)[0]
        b = e["target"].split(SEP, 1)[0]
        pair[tuple(sorted((a, b)))] += 1
        touched[a] += 1
        touched[b] += 1

    concepts = defaultdict(set)
    for e in cross:
        concepts[e["concept"]].add(e["source"].split(SEP, 1)[0])
        concepts[e["concept"]].add(e["target"].split(SEP, 1)[0])

    isolated = [p for p in pids if touched[p] == 0]

    L = []
    L.append("# Fleet reconciliation report")
    L.append("")
    L.append(f"Generated {date.today().isoformat()} by `tools/reconcile_fleet.py`.")
    L.append("")
    L.append("Cross-project edges carry `relation: same_concept_as` with the concept name and a")
    L.append("one-line reason, and are graded `INFERENCE` - a model proposed them from labels alone.")
    L.append("**Every node is a lead with provenance, not evidence.** Go read the document it names.")
    L.append("")
    L.append("## Totals")
    L.append("")
    L.append(f"- projects reconciled: **{len(pids)}**")
    L.append(f"- nodes: **{len(nodes):,}** (all namespaced `project{SEP}id`), of which "
             f"**{len(cnodes):,}** are concept nodes")
    L.append(f"- intra-project links: **{len(intra):,}**")
    L.append(f"- cross-project links: **{len(cross):,}**")
    L.append(f"- concept→implementation links: **{len(cedges):,}**")
    L.append(f"- distinct concepts bridging 2+ projects: **{len(concepts):,}**")
    L.append("")
    L.append("Concept nodes exist because graphify seeds a query by **lexical** match on labels.")
    L.append("A question in plain English (\"stop geometry being culled\") matches no engine symbol")
    L.append("and seeds on noise; a concept node carries the plain-English name and reason, so the")
    L.append("question lands on it and every project's implementation is one `instance_of` hop away.")
    L.append("")
    L.append("## Per-project coverage")
    L.append("")
    L.append("| Project | Nodes | Intra links | Cross-project edges | Reachable from |")
    L.append("|---|---:|---:|---:|---|")
    for p in pids:
        n = sum(1 for x in nodes if x["project"] == p)
        il = sum(1 for x in intra if x.get("project") == p)
        peers = sorted({(b if a == p else a) for (a, b) in pair if p in (a, b)})
        L.append(f"| **{p}** | {n:,} | {il:,} | {touched[p]:,} | "
                 f"{', '.join(peers) if peers else '**nothing**'} |")
    L.append("")

    if isolated:
        L.append(f"> **{len(isolated)} project(s) have NO cross-project edge: "
                 f"{', '.join(isolated)}.** A query seeded in one of these can never")
        L.append("> reach another project, and an empty result from it means *nothing was linked*,")
        L.append("> not *nobody solved this*.")
        L.append("")

    L.append("## Project pairs")
    L.append("")
    if pair:
        L.append("| Pair | Shared-concept edges |")
        L.append("|---|---:|")
        for (a, b), c in pair.most_common():
            L.append(f"| {a} ↔ {b} | {c} |")
    else:
        L.append("*No cross-project edges were produced.*")
    L.append("")

    L.append("## Concepts that bridge projects")
    L.append("")
    if concepts:
        L.append("| Concept | Projects |")
        L.append("|---|---|")
        for c, ps in sorted(concepts.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            L.append(f"| {c} | {len(ps)} — {', '.join(sorted(ps))} |")
    else:
        L.append("*none*")
    L.append("")

    L.append("## Rejections")
    L.append("")
    L.append("| Reason | Count |")
    L.append("|---|---:|")
    for k in ("group_kept", "group_single_project", "edge_kept", "edge_same_project",
              "edge_self_loop", "edge_duplicate", "member_invented"):
        L.append(f"| `{k}` | {stats.get(k, 0):,} |")
    L.append("")
    if invented:
        L.append(f"Labels the model returned that exist in no graph ({len(invented)}), rejected "
                 "rather than linked:")
        L.append("")
        for r in invented[:12]:
            L.append(f"- {r}")
        L.append("")
    return "\n".join(L)


# ------------------------------------------------------------------- main ---

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="propose groups; write nothing")
    ap.add_argument("--offline", action="store_true",
                    help="namespaced union and report only; no model call")
    ap.add_argument("--projects", help="comma-separated subset")
    args = ap.parse_args()

    only = [p.strip() for p in args.projects.split(",")] if args.projects else None
    graphs, nodes, intra, hyper = load_fleet(only)
    if not graphs:
        sys.exit("no project graphs could be loaded")

    print(f"loaded {len(graphs)} project graph(s): {len(nodes):,} nodes, {len(intra):,} intra links, "
          f"{len(hyper):,} hyperedges")
    for pid, g in graphs.items():
        print(f"   {pid:<14} {g.summary()}")

    dupes = len(nodes) - len({n['id'] for n in nodes})
    print(f"\nnamespaced ID collisions: {dupes}  (must be 0)")
    if dupes:
        sys.exit("namespacing failed - duplicate IDs survive")

    index = build_index(graphs)
    print(f"validation index: {len(index):,} (project, label) pairs")

    cross: list[dict] = []
    cedges: list[dict] = []
    cnodes: list[dict] = []
    stats: Counter = Counter()
    invented: list[str] = []

    if args.offline:
        print("\n--offline: skipping the model; structural union and report only.")
    else:
        roster = "\n".join(f"  {p:<14}= {d}" for p, d in PROJECTS.items() if p in graphs)
        passes = batches(graphs)
        print(f"\nresolving concepts in {len(passes)} pass(es)")
        groups: list[dict] = []
        for i, b in enumerate(passes, 1):
            print(f"  pass {i}/{len(passes)}: {sum(len(v) for v in b.values()):,} labels")
            groups.extend(ask(b, roster))
        print(f"\nmodel proposed {len(groups)} group(s)")
        cross, cedges, cnodes, stats, invented = edges_from_groups(groups, index)
        print(f"cross-project edges kept: {len(cross):,}   "
              f"concept nodes: {len(cnodes):,}   concept edges: {len(cedges):,}")
        for k, v in sorted(stats.items()):
            print(f"   {k:<22} {v:,}")

    nodes = nodes + cnodes
    report = coverage_report(graphs, nodes, intra, cross, cnodes, cedges, stats, invented)

    if args.dry_run:
        print("\n" + report)
        return 0

    # A hyperedge whose members do not resolve is dropped by graphify at load
    # time with a warning. Catch that here instead, where it is an error.
    ids = {n["id"] for n in nodes}
    orphan = [h["id"] for h in hyper if not (set(h.get("nodes", [])) & ids)]
    if orphan:
        print(f"WARNING: {len(orphan)} hyperedge(s) reference no built node and would be "
              f"dropped on load: {', '.join(orphan[:4])}"
              f"{' ...' if len(orphan) > 4 else ''}")

    write_graph(OUT, nodes, intra + cross + cedges, hyperedges=hyper,
                fleet={"projects": list(graphs), "generated": date.today().isoformat(),
                       "cross_project_links": len(cross)})
    REPORT.write_text(report, encoding="utf-8")
    print(f"\nwrote {OUT}")
    print(f"      {len(nodes):,} nodes, {len(intra) + len(cross) + len(cedges):,} links "
          f"({len(cross):,} cross-project, {len(cedges):,} concept)")
    print(f"wrote {REPORT}")

    if not args.offline and not cross:
        print("\nNO CROSS-PROJECT EDGES WERE PRODUCED - this graph cannot answer a "
              "cross-project question.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
