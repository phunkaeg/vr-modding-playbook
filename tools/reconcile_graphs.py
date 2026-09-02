#!/usr/bin/env python3
"""Create cross-project edges between per-project graphs by resolving entities.

WHY THIS EXISTS
---------------
`graphify merge-graphs` is a UNION, not a join: it combines node sets and never
discovers that two projects describe the same concept. Measured on this fleet's
three-project corpus, the merge produced exactly the sum of its inputs
(1328 nodes, 616 edges) and no edge bridged projects - so a query seeded in one
project's nodes could never reach another's.

Exact label matching does not fix it. Across 1328 nodes only 7 normalised labels
recur across projects, and 5 of those are document filenames. Meanwhile 74
concept tokens (stereo, camera, pose, viewmodel, comfort...) appear in all three.
The concepts recur; the vocabulary does not.

So the missing step is semantic entity resolution over the LABELS - which is
cheap, because it reads ~1300 short strings rather than 700k words of source.

Every returned label is validated against the real node set before an edge is
emitted; a model that invents a label produces no edge rather than a fake one.

Usage (run through graphify-key.bat so GEMINI_API_KEY is in the environment):
  graphify-key.bat python tools/reconcile_graphs.py
  graphify-key.bat python tools/reconcile_graphs.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "cross-engine-graph" / "per-project"
OUT = ROOT / "cross-engine-graph" / "graphify-out" / "reconciled-graph.json"
PROJECTS = ["somavr", "ss2vr", "bioshockvr"]
MODEL = os.environ.get("GRAPHIFY_GEMINI_MODEL", "gemini-3-flash-preview")
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/openai/"


def load():
    graphs, nodes = {}, []
    for p in PROJECTS:
        g = BASE / p / "graphify-out" / "graph.json"
        if not g.exists():
            sys.exit(f"missing graph: {g}")
        d = json.loads(g.read_text(encoding="utf-8"))
        graphs[p] = d
        for n in d.get("nodes", []):
            label = n.get("label") or n.get("name") or n.get("id") or ""
            nodes.append({"project": p, "id": n.get("id"), "label": str(label)})
    return graphs, nodes


PROMPT = """You are reconciling entities across three independent VR-mod documentation graphs.

Each project converts a different game to VR and names things in its own local vocabulary:
  somavr      = SOMA, HPL3 engine, OpenGL
  ss2vr       = System Shock 2, Dark/KEX engine, D3D11
  bioshockvr  = BioShock, Unreal 2.5 Vengeance, D3D11

Below are node labels, grouped by project.

Find groups where nodes from DIFFERENT projects denote THE SAME underlying VR-engineering concept -
the same problem, subsystem, technique or artifact - even though the wording differs.

Rules:
- A group MUST contain labels from at least two different projects. Same-project groups are useless here.
- Copy labels EXACTLY as given. Do not paraphrase, shorten or invent.
- Match on engineering concept, not on generic English. "Build History" and "Decision Log" are document
  types, not concepts - skip them. So are bare project names.
- Give each group a short concept name and one sentence on WHY these are the same thing.

BE EXHAUSTIVE. Work through the whole list systematically rather than reporting only the obvious
matches. A previous run over this same data returned 10 groups covering 2% of the nodes, which is far
too few to be useful - every VR conversion of this kind shares dozens of concepts. Expect to find
matches across at least these areas, and others besides:

  stereo / per-eye rendering        camera and view ownership        culling and frustum
  projection and FOV                pose and tracking                recentre and calibration
  hands, weapons, viewmodels        input mapping and locomotion     UI, HUD and menus
  interaction and selection rays    comfort and vignette             audio and haptics
  render hooks and frame boundary   OpenXR/OpenVR lifecycle          performance and frame pacing
  build identity and logging        packaging and install            testing and harnesses

Precision still matters more than volume: a wrong link creates a false path between two projects that
never solved the same problem. But a concept that plainly recurs across projects under different names
is exactly what you are here to find, so do not omit it out of caution.

Return JSON only:
{"groups":[{"concept":"...","why":"...","members":[{"project":"...","label":"..."}]}]}
"""


def ask(nodes):
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("the 'openai' package is required: uv tool install \"graphifyy[gemini]\" --force")

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        sys.exit("No GEMINI_API_KEY in the environment. Run this through graphify-key.bat.")

    listing = []
    for p in PROJECTS:
        listing.append(f"\n### {p}")
        for n in nodes:
            if n["project"] == p:
                listing.append(f"- {n['label']}")
    body = PROMPT + "\n".join(listing)

    client = OpenAI(api_key=key, base_url=ENDPOINT)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": body}],
        temperature=0,
        response_format={"type": "json_object"},
        max_tokens=16384,
        # Without this the model spends its whole budget thinking and truncates.
        # Measured: prompt 14,902 + completion 641 = 15,543, but total = 31,268 -
        # the missing 15,725 were reasoning tokens, and finish_reason came back
        # "length" with the JSON cut mid-string. graphify's own gemini config
        # sets reasoning_effort low for the same reason.
        reasoning_effort="low",
    )
    usage = resp.usage
    print(f"tokens: {usage.prompt_tokens:,} in / {usage.completion_tokens:,} out"
          f"   est ${usage.prompt_tokens/1e6*0.5 + usage.completion_tokens/1e6*3:.4f}")

    raw = resp.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        # A truncated response is still worth most of its groups. Salvage every
        # complete {...} object inside "groups" rather than discarding the call.
        print(f"response did not parse ({exc}); salvaging complete groups")
        groups, depth, start, instr, esc = [], 0, None, False, False
        for i, ch in enumerate(raw):
            if instr:
                if esc: esc = False
                elif ch == "\\": esc = True
                elif ch == '"': instr = False
                continue
            if ch == '"': instr = True
            elif ch == "{":
                if depth == 0: start = i
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
        print(f"salvaged {len(groups)} complete groups from the truncated response")
        return {"groups": groups}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report groups; write nothing")
    args = ap.parse_args()

    graphs, nodes = load()
    print(f"loaded {len(nodes)} nodes from {len(PROJECTS)} projects")

    # exact label -> id, per project. Validation happens against this.
    index = {}
    for n in nodes:
        index.setdefault((n["project"], n["label"]), n["id"])

    data = ask(nodes)
    groups = data.get("groups", [])
    print(f"model proposed {len(groups)} groups")

    edges, kept, rejected = [], 0, []
    for g in groups:
        members = g.get("members", [])
        resolved = []
        for m in members:
            key = (m.get("project"), m.get("label"))
            if key in index:
                resolved.append((key[0], index[key]))
            else:
                rejected.append(f"{m.get('project')}: {str(m.get('label'))[:60]}")
        # must still span 2+ projects AFTER validation
        if len({p for p, _ in resolved}) < 2:
            continue
        kept += 1
        for i in range(len(resolved)):
            for j in range(i + 1, len(resolved)):
                if resolved[i][0] == resolved[j][0]:
                    continue
                edges.append({
                    "source": resolved[i][1],
                    "target": resolved[j][1],
                    "relation": "same_concept_as",
                    "concept": g.get("concept", ""),
                    "why": g.get("why", ""),
                    "provenance": "reconcile_graphs.py",
                })

    print(f"groups surviving validation: {kept}   cross-project edges: {len(edges)}")
    if rejected:
        print(f"rejected {len(rejected)} labels that do not exist in any graph (model invention):")
        for r in rejected[:8]:
            print("   -", r)

    if args.dry_run:
        for g in groups[:15]:
            ms = ", ".join(f"{m.get('project')}:{m.get('label')}" for m in g.get("members", []))
            print(f"  [{g.get('concept','')}] {ms}")
        return 0

    merged_nodes, merged_edges = [], []
    for p in PROJECTS:
        d = graphs[p]
        merged_nodes.extend(d.get("nodes", []))
        merged_edges.extend(d.get("links", d.get("edges", [])))
    merged_edges.extend(edges)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"nodes": merged_nodes, "links": merged_edges}, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT}: {len(merged_nodes)} nodes, {len(merged_edges)} links "
          f"({len(edges)} of them cross-project)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
