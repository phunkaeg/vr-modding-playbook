#!/usr/bin/env python3
"""Settings-coverage comparison across the shipped VR interaction stacks.

WHY THIS EXISTS
---------------
Four mods for two games that shipped IN VR - HIGGS, PLANCK, VRIK on Skyrim,
Heisenberg on Fallout 4 - plus Buffout 4 NG as the field-operations layer, have
between them spent years discovering what an interaction layer actually needs to
expose. Their configuration files are that discovery, written down.

This is NOT a search index (see the note in the generated document). It is a
CHECKLIST: for each concern, how many knobs each shipped mod needed. A concern
where four independent teams all shipped tuning is a concern our own mods will
meet, and a column of zeros against a populated row is a gap worth knowing about
before a headset session finds it.

Bucketing is by keyword and is therefore approximate. Every unmatched setting is
counted and the worst offenders are listed, because a classifier that silently
drops what it cannot place would overstate coverage - which is the one thing this
document must not do.

Usage:
  python tools/interaction_coverage.py            # write the document
  python tools/interaction_coverage.py --check    # fail if it is stale
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODS = Path("D:/Dev Debug/Other VR mods")
OUT = ROOT / "docs" / "generated" / "interaction-coverage.md"

# (label, path relative to Other VR mods, what it is)
SOURCES = [
    ("HIGGS", "SkyrimVR mods/HIGGS 1.10.10-43930-1-10-10-1768263289/SKSE/Plugins/higgs_vr.ini",
     "physical grab"),
    ("PLANCK", "SkyrimVR mods/PLANCK 0.8.1 66025 0.8.1 2026-07-30T03-35Z 4t2yDcbYt/"
     "SKSE/Plugins/activeragdoll.ini", "physics bodies"),
    ("VRIK", "SkyrimVR mods/VRIK Player Avatar 23416 0.8.6 2026-07-12T13-00Z Yj6wQRIkO/"
     "SKSE/Plugins/vrikslots.ini", "holsters"),
    ("VRIK-g", "SkyrimVR mods/VRIK Player Avatar 23416 0.8.6 2026-07-12T13-00Z Yj6wQRIkO/"
     "SKSE/Plugins/vrikgestures.ini", "gestures"),
    ("Heisenberg", "Fallout4VR mods/Heisenberg - Physical Interactions 99105 0.8.6 "
     "2026-08-02T10-39Z Q8oKHMMng/F4SE/Plugins/Heisenberg_F4VR.ini", "physical interactions"),
    ("Buffout", "Fallout4VR mods/Buffout4 NG-64880-1-38-3-1785297452/F4SE/Plugins/Buffout4.toml",
     "field operations"),
]

# Ordered: the first bucket whose pattern matches wins, so put specific before general.
CONCERNS: list[tuple[str, str]] = [
    ("selection & casting",
     r"cast|proximity|dotproduct|halfangle|requiredcast|select|beam|pointing|palmvector|palmposition"),
    ("held-object constraint",
     r"tau|damp|maxforce|constraint|spring|motor|stretch|inertia|recovery|forceratio|powered|"
     r"hierarchygain|velocitygain|positiongain|lerp"),
    ("grab lifecycle",
     r"grab|pull|loot|snap|sticky|telekines|yank|shove|throw|drop|stash|consume|pickup|equip"),
    ("holster & storage",
     r"slot|holster|storage|zone|shoulder|mouth|behindhead|quiver|sheath"),
    ("body, avatar & actor",
     r"ragdoll|biped|actor|race|body|avatar|arm|finger|selfie|getup|aggression|stamina|relationship"),
    ("gesture & input binding",
     r"gesture|action\d|button|trigger|grip|thumbstick|trackpad|binding|input|deadzone|swap.*ab|"
     r"castwhenhands|handanimation"),
    ("haptics",
     r"haptic|rumble"),
    ("collision & intersection",
     r"collision|collide|intersect|phase|push|contact|hitcooldown|weaponcollision"),
    ("physics stability",
     r"physics|havok|simulationisland|warp|maxlinear|maxangular|frameratemin|minphysics|"
     r"numsteps|shadowupdate|freeze"),
    ("comfort, seated & scale",
     r"seated|heightthreshold|comfort|vignette|speedreduction|slowmovement|jumpheight|worldscale|"
     r"maxreduction"),
    ("timing, leeway & cooldown",
     r"time$|times$|timems|delay|cooldown|leeway|duration|fadein|fadeout|preempt|throttle|"
     r"interval|frames"),
    ("UI, rollover & discoverability",
     r"rollover|hover|sphere|alpha|opacity|colou?r|visible|showmess|compass|hud|menu|subtitle"),
    ("diagnostics & crash",
     r"loglevel|debug|warn|symcache|waitfordebug|trace|logging"),
    ("memory & allocator",
     r"memorymanager|allocator|heap|smallblock|scaleform|maxstdio|texturestreamer"),
    ("engine defect fixes",
     r"^(actoris|backported|bgsai|bslighting|cellinit|created3d|encounterzone|greymovies|escape|"
     r"follower|interiornav|fixscript|fixtoggle|magiceffect|movementplanner|packageallocate|"
     r"safeexit|tesobject|unaligned|utilityshader|workbench|pipboylight|achievements|bsmta|"
     r"bsprecull|inisetting|workshopmenu|maxpapyrus|f4ee)"),
]

SETTING = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)\s*=")


def read_settings(path: Path) -> list[str]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = SETTING.match(line.strip())
        if m:
            out.append(m.group(1))
    return out


def bucket(name: str) -> str | None:
    low = name.lower()
    for label, pattern in CONCERNS:
        if re.search(pattern, low):
            return label
    return None


def collapse(names: list[str]) -> list[str]:
    """Fold indexed families (visibleSlot1..14, action1..999) into one entry.

    Counting 999 `actionN` entries as 999 knobs would say VRIK's gesture file is
    the most configurable thing here, when it is one binding table. The family is
    the unit of design; the index is not.
    """
    seen: dict[str, int] = {}
    order: list[str] = []
    for n in names:
        stem = re.sub(r"\d+$", "", n)
        if stem not in seen:
            seen[stem] = 0
            order.append(stem)
        seen[stem] += 1
    return [f"{s} x{seen[s]}" if seen[s] > 1 else s for s in order]


def build() -> str:
    raw: dict[str, list[str]] = {}
    for label, rel, _ in SOURCES:
        raw[label] = read_settings(MODS / rel)

    families = {k: collapse(v) for k, v in raw.items()}
    counts: dict[str, Counter] = {k: Counter() for k in raw}
    examples: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    unmatched: dict[str, list[str]] = defaultdict(list)

    for label, fam in families.items():
        for entry in fam:
            base = entry.split(" x")[0]
            b = bucket(base)
            if b is None:
                unmatched[label].append(base)
                continue
            counts[label][b] += 1
            if len(examples[b][label]) < 3:
                examples[b][label].append(entry)

    labels = [s[0] for s in SOURCES]
    L = []
    L.append("<!-- Generated by tools/interaction_coverage.py. Do not edit. -->")
    L.append("")
    L.append("# Interaction-layer settings coverage")
    L.append("")
    L.append("**What this is.** Four shipped VR interaction mods for two games that shipped *in* VR,")
    L.append("plus Buffout 4 NG as the field-operations layer, compared by **what they found it")
    L.append("necessary to expose**. Their configuration is years of discovery written down.")
    L.append("")
    L.append("**How to use it.** Read it as a checklist when building an interaction layer, not as a")
    L.append("search index. A concern where several independent teams all shipped tuning is a concern")
    L.append("your mod will meet. A concern where you have nothing is a gap - possibly a deliberate")
    L.append("one, but worth knowing before a headset session finds it for you.")
    L.append("")
    L.append("**Counting.** Indexed families are folded to one entry: `visibleSlot1..14` counts once,")
    L.append("as does VRIK's `action1..999` binding table. The family is the unit of design; the index")
    L.append("is not. Bucketing is by keyword and therefore approximate - **every unplaced setting is")
    L.append("counted below**, because a classifier that silently drops what it cannot place would")
    L.append("overstate coverage.")
    L.append("")
    L.append("| Source | What it is | Settings | Families |")
    L.append("|---|---|---:|---:|")
    for lab, _, what in SOURCES:
        L.append(f"| **{lab}** | {what} | {len(raw[lab]):,} | {len(families[lab]):,} |")
    L.append("")

    L.append("## Coverage by concern")
    L.append("")
    L.append("| Concern | " + " | ".join(labels) + " | teams |")
    L.append("|---|" + "---:|" * len(labels) + "---:|")
    for concern, _ in CONCERNS:
        row = [str(counts[l][concern] or "—") for l in labels]
        teams = sum(1 for l in labels if counts[l][concern])
        L.append(f"| {concern} | " + " | ".join(row) + f" | **{teams}** |")
    L.append("")

    shared = [c for c, _ in CONCERNS
              if sum(1 for l in labels if counts[l][c]) >= 3]
    L.append(f"**{len(shared)} concerns appear in three or more of these independently built mods.** "
             "Those are the ones to treat as load-bearing:")
    L.append("")
    for c in shared:
        who = ", ".join(l for l in labels if counts[l][c])
        L.append(f"- **{c}** — {who}")
    L.append("")

    L.append("## What each concern looks like in practice")
    L.append("")
    for concern, _ in CONCERNS:
        if not any(counts[l][concern] for l in labels):
            continue
        L.append(f"### {concern}")
        L.append("")
        for lab in labels:
            if examples[concern].get(lab):
                L.append(f"- **{lab}**: `" + "`, `".join(examples[concern][lab]) + "`")
        L.append("")

    L.append("## Unplaced settings")
    L.append("")
    total_un = sum(len(v) for v in unmatched.values())
    total_fam = sum(len(v) for v in families.values())
    pct = 100 * total_un / total_fam if total_fam else 0
    L.append(f"{total_un} of {total_fam} families ({pct:.0f}%) matched no concern above. They are "
             "listed so the table cannot look more complete than it is:")
    L.append("")
    for lab in labels:
        if unmatched[lab]:
            shown = ", ".join(f"`{x}`" for x in sorted(unmatched[lab])[:12])
            more = f" … and {len(unmatched[lab]) - 12} more" if len(unmatched[lab]) > 12 else ""
            L.append(f"- **{lab}** ({len(unmatched[lab])}): {shown}{more}")
    L.append("")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    missing = [lab for lab, rel, _ in SOURCES if not (MODS / rel).exists()]
    if missing:
        print(f"sources not found, skipping: {', '.join(missing)}")
        if args.check or len(missing) == len(SOURCES):
            return 2  # no usable input is not a clean result

    if not any(read_settings(MODS / rel) for _, rel, _ in SOURCES):
        print("NO_DATA: no settings were extracted from the source files")
        return 2

    text = build()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"{OUT.relative_to(ROOT)} is stale; run python tools/interaction_coverage.py")
            return 1
        print(f"{OUT.relative_to(ROOT)} is current")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
