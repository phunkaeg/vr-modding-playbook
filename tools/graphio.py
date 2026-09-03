#!/usr/bin/env python3
"""One accessor for graphify's graph JSON. Import this; never index the dict.

WHY THIS EXISTS
---------------
graphify writes NetworkX **node-link** JSON, in which edges live under the key
``links``. A script that reaches for ``d["edges"]`` gets an empty result and
*no exception* - so it reports ZERO EDGES and looks entirely correct.

That has now happened twice on this fleet, in two different agent sessions,
within a week. Both times the conclusion reached a human as "it has no edges,
so it isn't a graph - you could grep it faster." Both times the graph in
question had hundreds of edges.

A missing key must raise, never return zero. That is the whole point of this
module: reading a graph wrong should be *loud*.

    from graphio import load_graph
    g = load_graph(path)
    print(len(g.nodes), len(g.links))      # never silently 0
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# NetworkX node-link format uses "links". Some exporters emit "edges". Both are
# accepted on read; anything else is an error rather than an empty list.
EDGE_KEYS = ("links", "edges")


class GraphSchemaError(ValueError):
    """The file is not a graph we recognise - raised instead of returning empty."""


@dataclass
class Graph:
    path: Path
    nodes: list[dict[str, Any]]
    links: list[dict[str, Any]]
    hyperedges: list[dict[str, Any]] = field(default_factory=list)
    edge_key: str = "links"
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def node_ids(self) -> set[str]:
        return {n["id"] for n in self.nodes if "id" in n}

    def degree(self) -> float:
        return (2 * len(self.links) / len(self.nodes)) if self.nodes else 0.0

    def isolated(self) -> int:
        touched: set[str] = set()
        for l in self.links:
            touched.add(l.get("source"))
            touched.add(l.get("target"))
        return len(self.node_ids - touched)

    def summary(self) -> str:
        return (f"{self.path.name}: {len(self.nodes):,} nodes, {len(self.links):,} "
                f"{self.edge_key}, {len(self.hyperedges):,} hyperedges, "
                f"deg {self.degree():.1f}, {self.isolated():,} isolated")


def load_graph(path: str | Path) -> Graph:
    """Load a graphify graph, or raise. Never returns a silently empty edge list."""
    p = Path(path)
    if not p.exists():
        raise GraphSchemaError(f"no graph at {p}")

    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GraphSchemaError(f"{p} is not valid JSON: {exc}") from exc

    if not isinstance(d, dict):
        raise GraphSchemaError(f"{p} is {type(d).__name__}, expected a JSON object")
    if "nodes" not in d:
        raise GraphSchemaError(f"{p} has no 'nodes' key; keys are {sorted(d)}")

    present = [k for k in EDGE_KEYS if k in d]
    if not present:
        raise GraphSchemaError(
            f"{p} has none of {EDGE_KEYS}; keys are {sorted(d)}. "
            "Refusing to report zero edges for a graph whose edge key is unknown."
        )
    # If both exist, take the populated one; if both are populated they disagree
    # about the truth and a human needs to look.
    if len(present) == 2 and d.get("links") and d.get("edges"):
        raise GraphSchemaError(
            f"{p} has BOTH 'links' ({len(d['links'])}) and 'edges' ({len(d['edges'])}) "
            "populated; which one is authoritative is undecidable here."
        )
    key = present[0] if d.get(present[0]) or len(present) == 1 else present[1]

    return Graph(
        path=p,
        nodes=list(d.get("nodes") or []),
        links=list(d.get(key) or []),
        hyperedges=list(d.get("hyperedges") or []),
        edge_key=key,
        raw=d,
    )


def write_graph(path: str | Path, nodes: list, links: list, **extra: Any) -> Path:
    """Write node-link JSON with the canonical 'links' key."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"directed": False, "multigraph": False, "graph": {},
               "nodes": nodes, "links": links}
    payload.update(extra)
    p.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return p


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        sys.exit("usage: graphio.py <graph.json> [...]")
    for a in sys.argv[1:]:
        try:
            print(load_graph(a).summary())
        except GraphSchemaError as exc:
            print(f"ERROR {exc}")
