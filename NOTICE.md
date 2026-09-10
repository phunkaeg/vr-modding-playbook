# Notice and attribution

This playbook is distilled from 10 in-house VR ports and roughly 107 external
projects. It **describes** those projects; it does not include, redistribute or
relicense them. The playbook's own terms are split in two: code under MIT in [`LICENSE`](LICENSE),
prose under CC BY 4.0 in [`LICENSE-docs`](LICENSE-docs).

[`sources.yml`](sources.yml) is authoritative for every source: its path, upstream
URL, licence, the revision reviewed, and which areas were reviewed at what evidence
grade. This page is a stable summary and does not list all 107 by name, so that it
does not go stale each time a source is added.

## Licences of the projects studied

As recorded on 2026-09-10, read from the `LICENSE`/`COPYING` file present in each
local checkout:

| Licence | Sources |
|---|---|
| MIT | 29 |
| GPL-3.0 | 13 |
| GPL-2.0 | 3 |
| Apache-2.0 | 1 |
| zlib | 1 |
| stated in-tree, not yet classified | 3 |
| **not open source — see below** | **3** |
| no licence file found in the checkout | 54 |

The 54 with no licence file are, by default, **all rights reserved by their
authors**. Absence of a licence is not permission.

## Sources that are NOT open source

Read this before copying anything from a project this playbook cites.

- **UEVR** — `Copyright (c) 2022-2025 praydog. All rights reserved.`
  The playbook cites UEVR's *technique* extensively and contains none of its code.
  Every code sample in this repository is original. Describing how a program
  behaves is not copying it — but **do not lift UEVR source** on the strength of
  this playbook's discussion of it.

- **crysis_vrmod** — carries Crytek's *Limited License Agreement for the
  CryENGINE 2 Modification SDK*. Proprietary; redistribution restricted.

- **MonsterDeadWood analyzer bible** — the grant recorded in `sources.yml`, verbatim:

  > Integration permission from MonsterDeadWood relayed by user 2026-09-09; no
  > blanket license claim for bundled third-party sources.

  That permission covers integrating the **method**. It is explicitly not a claim
  over the third-party repositories bundled inside that donor package, which remain
  under their own terms.

## On copyleft sources

Sixteen cited projects are GPL-2.0 or GPL-3.0. The playbook links against none of
them, includes none of their source, and is not a derivative work of any of them.
Copyleft attaches to derivative works of the code, not to factual descriptions of
its behaviour, so no licence obligation flows from citing them here.

## Attribution in the text

External projects are credited inline where their work informed a finding — the
convention throughout is a parenthetical naming the project, for example
*(UEVR bruteforces a texture vtable to find the function returning an
`ID3D12Resource*`)*. Chapter 11 additionally records that much of its anchoring
technique is distilled from praydog's published write-ups.

The in-house fleet projects (SS2VR, BioshockVR, SOMAVR, PreyVR, DishonoredVR,
FarCry2-VR, Swat4-VR, Sims4VR, SoF-VR, Medal-of-Honor-VR) are unreleased and
internal; findings from them are published here with permission.

## Not part of this repository

Game assets, engine SDKs, proprietary binaries, and the contents of any local
`External/` or reference-checkout directory are excluded from version control and
are not covered by either of this repository's licences.
