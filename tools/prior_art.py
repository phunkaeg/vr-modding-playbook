#!/usr/bin/env python3
"""Find recorded prior art for a target fingerprint.

Answers one question: "we are looking at an engine/API like THIS — who has
already done it, how did they deliver it, and how far did they get?"

The ledger owns every fact printed here. This tool only matches and ranks; it
measures nothing and writes nothing, so it can never disagree with sources.yml.

Usage:
  python tools/prior_art.py "unreal 2.5" d3d9
  python tools/prior_art.py unity
  python tools/prior_art.py cryengine --json
  python tools/prior_art.py --engines
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required. Install: pip install -r requirements.txt")

from strict_yaml import load_unique_yaml


ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "sources.yml"

# Written how people actually type a fingerprint, expanded to how the ledger
# spells it. Values are re-tokenised, so an alias may expand to several tokens.
ALIASES = {
    "ue": "unreal", "ue1": "unreal 1", "ue2": "unreal 2", "ue2.5": "unreal 2.5",
    "ue3": "unreal 3", "ue4": "unreal 4", "ue5": "unreal 5",
    "unrealengine": "unreal",
    "dx9": "d3d9", "dx10": "d3d10", "dx11": "d3d11", "dx12": "d3d12",
    "directx": "d3d", "direct3d": "d3d",
    "gl": "opengl", "ogl": "opengl", "gles": "opengl es",
    "vk": "vulkan",
    "idtech": "id tech", "goldsource": "goldsrc",
}

# Engine match dominates: the API narrows a route, the engine decides it.
W_ENGINE, W_API, W_NAME = 3, 2, 1


def tokens(value: Any) -> set[str]:
    if not value:
        return set()
    text = str(value).lower()
    # "D3D11/12" and "D3D9/11" are two APIs sharing a slash, not one token.
    text = re.sub(r"d3d(\d+)\s*/\s*(\d+)", r"d3d\1 d3d\2", text)
    raw = re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text)
    out: set[str] = set()
    for token in raw:
        expanded = ALIASES.get(token)
        if expanded:
            out.update(re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", expanded))
        else:
            out.add(token)
    return out


def reviewed(entry: dict[str, Any], depth: str) -> list[str]:
    areas = entry.get("areas") or {}
    return sorted(
        name for name, rec in areas.items()
        if isinstance(rec, dict) and rec.get("review") == depth
    )


def score(entry: dict[str, Any], query: set[str]) -> tuple[int, bool]:
    """Return (weighted score, whether any engine token matched)."""
    engine, api = tokens(entry.get("engine")), tokens(entry.get("api"))
    name = tokens(entry.get("game")) | tokens(entry.get("id"))
    total, hit_engine = 0, False
    for token in query:
        if token in engine:
            total += W_ENGINE
            hit_engine = True
        elif token in api:
            total += W_API
        elif token in name:
            total += W_NAME
    return total, hit_engine


def collect(cfg: dict[str, Any], query: set[str]) -> list[dict[str, Any]]:
    hits = []
    for section in ("fleet", "external"):
        for entry in cfg.get(section, []) or []:
            value, hit_engine = score(entry, query)
            if value:
                hits.append({
                    "section": section, "score": value,
                    "engine_match": hit_engine, "entry": entry,
                })
    # Fleet first at equal score (we can read its working, not just its README),
    # then whoever has actually been harvested -- an unread row is a lead, not
    # prior art.
    hits.sort(key=lambda h: (
        -h["score"],
        h["section"] != "fleet",
        -len(reviewed(h["entry"], "full")),
        h["entry"]["id"],
    ))
    return hits


def describe(hit: dict[str, Any]) -> str:
    e = hit["entry"]
    fleet = hit["section"] == "fleet"
    head = e.get("display_name") or e["id"]
    weak = "   (API-only match)" if not hit["engine_match"] else ""
    lines = [f"  {head}  [{e.get('engine', '-')} | {e.get('api') or 'API not recorded'}]{weak}"]

    if fleet:
        tier = e.get("tier", "-")
        target = e.get("tier_target")
        tier_text = f"{tier} (target {target})" if target else tier
        lines.append(
            f"    in-house | authority {e.get('authority', '-')}"
            f" | tier {tier_text} | stereo {e.get('stereo_rung', '-')}"
        )
        lines.append(f"    working: {e.get('root', '-')}")
    else:
        chapter = e.get("chapter")
        where = f"chapter {int(chapter):02d}" if chapter is not None else "no chapter teardown"
        lines.append(f"    external | vehicle {e.get('vehicle', '-')} | {where}")
        url = e.get("upstream_url")
        if url and url not in ("internal", "unknown"):
            lines.append(f"    upstream: {url}")

    full = reviewed(e, "full")
    lines.append(f"    harvested: {', '.join(full) if full else '(nothing at full depth)'}")
    thin = reviewed(e, "not_reviewed") + reviewed(e, "skimmed")
    if thin:
        lines.append(f"    thin here:  {', '.join(thin)}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Match a target fingerprint against recorded VR-mod prior art."
    )
    parser.add_argument("terms", nargs="*", help="engine and/or API, e.g. \"unreal 2.5\" d3d9")
    parser.add_argument("--engines", action="store_true", help="list every recorded engine")
    parser.add_argument("--json", action="store_true", help="emit matches as JSON")
    parser.add_argument("--limit", type=int, default=8, help="max matches to print (default 8)")
    args = parser.parse_args()

    try:
        cfg = load_unique_yaml(LEDGER.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        print(f"sources.yml validation failed:\n{error}", file=sys.stderr)
        return 2
    everything = (cfg.get("fleet") or []) + (cfg.get("external") or [])

    if args.engines:
        for engine in sorted({str(e.get("engine", "-")) for e in everything}):
            print(f"  {engine}")
        return 0

    if not args.terms:
        parser.print_help()
        return 2

    query = tokens(" ".join(args.terms))
    hits = collect(cfg, query)

    if args.json:
        print(json.dumps(
            [{"section": h["section"], "score": h["score"],
              "engine_match": h["engine_match"], **h["entry"]}
             for h in hits[:args.limit]],
            indent=2, default=str,
        ))
        return 0

    label = " ".join(args.terms)
    if not hits:
        print(f"No recorded prior art matches {label!r}.")
        print("Try a broader term, or run --engines to see what is recorded.")
        print("\nA blank result is a real finding: it means this fingerprint is new")
        print("to the fleet, so no chapter, tier or rung here was earned on it.")
        return 1

    shown = hits[:args.limit]
    print(f"Prior art for {label!r}: {len(hits)} match(es), showing {len(shown)}:\n")
    for hit in shown:
        print(describe(hit))
        print()
    if len(hits) > len(shown):
        print(f"  ... {len(hits) - len(shown)} more (raise --limit)\n")

    print("Every line above is a ledger claim, not a measurement of your target.")
    print("Confirm the engine and API against the loaded module list before routing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
