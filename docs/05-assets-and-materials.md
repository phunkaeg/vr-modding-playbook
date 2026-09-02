# Custom Assets & Materials

When VR needs new geometry (a hand mesh, a clean viewmodel) you're exporting custom models
into an old format through tooling that wasn't built for it. This is where silent data bugs
live.

## Exporter header traps

Custom model exporters frequently **copy header fields from a donor model without relocating
them** for the new layout. The result is a structurally-valid file with one stale pointer/
offset that aims into the wrong data — and the engine reads garbage from it.

- *SS2VR (the canonical example):* every exported model carried a stale "material extras"
  offset copied from the donor. The engine read garbage floats (e.g. illumination = 5×10⁸)
  from it. Unshaded materials never read that field, so they looked fine; **shaded** materials
  multiplied by the garbage and rendered fullbright white. The fix was a 12-byte patch zeroing
  three header fields; it became a mandatory post-export step.
- *General lesson:* after any custom export, **diff the header fields against a known-good
  donor** and confirm every offset points where the new layout actually placed that section.
  Don't trust "the file loads" — loading and being correct are different gates.

## Compacting/rewriting model data

If you rewrite or compact a model's internal tables (vertices, BSP nodes, material slots), you
must **remap every cross-reference** (child offsets, slot indices). Forgetting one produces an
AV in the engine's loader/converter at a garbage index — a crash that looks like corruption
but is actually your un-remapped pointer. (*SS2VR: compacting BSP node records without
remapping child offsets; and a five-slot×multi-pass material combination that crashed the
converter until the stale extras were zeroed.*)

## Your validator checks structure; the engine checks meaning

The natural way to gain confidence in a rewritten asset is to re-parse it with your own tooling. That
proves the *structure* survived. It says nothing about the invariants the engine relies on, and those are
where the crashes are:

- A **header count** that no longer matches the section it describes parses fine and kills the loader.
  (*SS2VR: a stale LGMD header vhot count.*)
- A rebuild that is **parser-clean but changes animated subobject identity or index ranges** loads and
  then breaks the thing that indexes into it. (*SS2VR: a shotgun vhot rebuild.*)
- **Metadata that is valid in general but illegal in this shape** — joint metadata preserved on a
  one-subobject standalone hand crashed the engine outright.

So: round-tripping through your own parser is a necessary check, not a sufficient one. Add assertions for
the *semantic* invariants you can name (every child offset lands exactly on a record start; counts agree
with the sections they describe; metadata is only present in shapes that support it), and treat a clean
parse as the beginning of validation rather than the end.

**Tell:** if the engine **hangs** instead of crashing while loading a model, sample the main thread before
you touch anything else. A traversal that has walked into the middle of a compacted stream spins building
an ever-growing structure — it looks like a freeze, and it points straight at an un-remapped offset.

## One-variable A/B, always

When a custom asset misbehaves, change **exactly one thing** between the working reference and
the broken candidate, and keep a byte-level diff to prove it:

- Make the broken variant byte-identical to a known-good one except the single field under
  test (model name, one material flag, one offset). (*SS2VR: the crashing model was byte-
  identical to a visible one except two name bytes; that's how the crash was isolated to the
  material stack, not the geometry.*)
- This turns "it doesn't work" into "this specific byte does it."

**A revert has the same blast radius as a forward experiment, and deserves the same discipline.** When
something regresses, the instinct is to switch off the whole bundle that shipped with it — which
re-introduces every problem that bundle had already fixed. (*BioshockVR disabled four flags together to
recover from a rotation regression when only two were implicated; a second build was needed to restore the
one confirmed-useful setting the bundled revert had thrown away.*) Isolate the revert to the single
variable actually implicated, exactly as you would isolate a forward A/B.

The mirror-image rule — **widening a working narrow fix to its whole resource class is a new experiment,
not a generalisation** — has bitten hard enough to earn its own treatment in
[14](14-render-pass-hazard-atlas.md).

## Pick the right control group

A test only proves something if the control actually exercises the variable. (*SS2VR: the
stale-material-extras garbage was dismissed as a red herring for a day because the "it works"
control was an **unshaded** material — which never reads the extras table. An unshaded material
is not a control for a lighting bug.*) Before trusting "X also has this and X is fine," confirm
X consumes the suspect value through the same path.

## Material/include resolution

Custom material include chains resolve relative to *something* — the package root, the engine
root, a search path. If your package doesn't ship the includes (or ships them at the wrong
relative path), the engine hits a null resource and may crash or render nothing. Package the
full include chain, or inline it. (*SS2VR: a custom material referencing an unpackaged include
crashed with a null in the loader.*)

## Know the engine's real package format — a parse failure isn't proof of absence

Remasters and engine forks routinely ship **non-stock serialization**, and the community tools you'd
reach for (UELib/UModel and friends) were written for the stock format. When they choke, that is a
tooling mismatch, not evidence that a class or asset doesn't exist.

- *BioshockVR:* BioShock's "Vengeance" engine (a UE2.5 fork with early-UE3 features: Epic version
  `141`, licensee `56`, package tag `0x9E2A83C1`) uses `.bsm` packages with CompactIndex references,
  8-byte FName flags, and a **BioShock-specific FString sign convention** (positive length = UTF-16LE,
  negative = ANSI), plus external `.blk` bulk resources indexed by `Catalog.bdc`. Stock UModel fails on
  these outright. Useful correlation vocabulary for static material/shader work: `ShaderTag` values map
  to `MaterialFactory_*` HLSL factories, alongside `MaterialTextureBinder`, `shaders.spk`,
  `ShaderCache.pcs`, and `.pcs10`.

Before building an asset pipeline, confirm the exact container format, index encoding, and string
convention against the *shipping* files (and, if it exists, the engine's own source lineage). "The
importer errored" and "the game can't use this asset" are different claims.

## Validate the asset on the GPU, not just in the loader

"It loaded without crashing" ≠ "it renders correctly." Use a frame capture to confirm the draw
actually has your texture bound, your shader, sane constants. A model can load, report
`renderedThisFrame=1`, and still contribute zero visible pixels (wrong blend, degenerate
verts, null SRV, garbage constants). The GPU capture is the only ground truth for "rendered but
invisible." (*SS2VR spent days on "renders but invisible" before a capture showed the bound
constants were garbage.*)

The distinction between the three validation layers, as three checks that fail differently:

```python
# 1. STRUCTURAL -- the file parses. Necessary, and proves almost nothing.
def validate_structure(path):
    hdr = read_header(path)
    assert hdr.magic == EXPECTED_MAGIC, f"not this format: {hdr.magic!r}"
    assert hdr.vertex_count * hdr.vertex_stride == len(hdr.vertex_blob), \
        "declared counts disagree with payload size"
    return hdr

# 2. SEMANTIC -- the engine's rules, which the format does not encode.
#    This is the layer that catches "loads fine, renders as garbage".
def validate_semantics(hdr, mesh):
    problems = []
    if hdr.bone_count > ENGINE_MAX_BONES:                 # silent clamp -> wrong skinning
        problems.append(f"{hdr.bone_count} bones > engine max {ENGINE_MAX_BONES}")
    for i, w in enumerate(mesh.weights):
        if abs(sum(w) - 1.0) > 1e-3:                      # renders, but limbs collapse
            problems.append(f"vertex {i} weights sum to {sum(w):.4f}")
    if mesh.uv_count == 0 and mesh.material.needs_uv:
        problems.append("material samples a texture but mesh has no UV set")
    if not is_convex(mesh.collision_hull):                # accepted, then falls through world
        problems.append("collision hull is not convex")
    return problems

# 3. GPU -- did it actually draw? The only layer that cannot be faked.
#    A mesh can pass 1 and 2 and still submit zero triangles.
def validate_on_gpu(capture, draw_id):
    d = capture.get_action(draw_id)
    assert d.num_indices > 0,        "draw submitted with zero indices"
    post_vs = capture.get_post_vs_data(draw_id)
    assert post_vs.vertex_count > 0, "vertex shader produced no output"
    assert not all_degenerate(post_vs.positions), \
        "all post-VS positions are degenerate -- bad transform or bad stride"
```

**Layer 2 is the one people skip, and it is where the expensive bugs live.** A structurally perfect file
whose bone weights do not sum to 1 loads without complaint and produces a character that renders
correctly at rest and collapses when animated — three days of chasing an animation bug that was a data
bug. Encode the engine's unwritten rules as assertions the moment you learn them.

## Asset-pipeline hygiene

- **Package format matters:** ship the archive format the engine expects (e.g. ZIP/PK with the
  right internal structure), with forward-slash paths, and **no extra root folder**. A mod that
  "doesn't load" is often a packaging-shape bug, not a content bug. (*SS2VR/FlatAim: tar-instead-
  of-zip, Windows backslashes, and an extra `mod/` root each cost a session.*)
- **Verify the package's contents after building**, programmatically — open the archive, check
  the version string and that the changed files are actually inside. Don't assume your build
  script did what you think.
