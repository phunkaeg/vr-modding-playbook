# Finding Things in the Binary: Anchors, Discovery, and Version Robustness

## Measure a camera mapping instead of guessing storage order {#numerical-camera-mapping}

Use when you have a bounded candidate block and an observable downstream payload,
but transpose, packing or component correspondence is uncertain. This method is
adapted from MonsterDeadWood's analyzer Bible; it is an experimental recipe, not
confirmation of its FC2 addresses or success counts. `[SOURCE]` method inspected;
application to a different target remains `[INFERENCE]` until tested there.

1. Pin the actual build, receiver, byte range, observation point, frame/thread/eye
   and restoration mechanism. For source-owned work use the real producer/consumer
   interface. For RE-owned work confirm the field is safe to perturb; a plausible
   64-byte block is not automatically a mutable matrix.
2. Record an unmodified control, then perturb one independent scalar by `+epsilon`
   and `-epsilon`, restoring the original bytes after each bounded observation.
   Repeat around multiple translated and rotated poses. Keep scene/time/jitter
   controlled or measure their contribution to the noise floor.
3. Log **every output component**, including unchanged zeros, for every input/sign.
   Store `input_index,output_index,delta_input,delta_output`; deltas are relative to
   the matched control. Keep phase, pose, writer and capture identity in the raw
   receipt. Split CSVs by pose/pass; do not average unrelated owners together.
4. Analyze with `python tools/research_checks.py jacobian samples.csv --inputs 16
   --outputs 16 --atol 0.0001 --rtol 0.05`. These tolerances are examples: choose
   them from measured noise in **derivative units**, and record the choice. Dimensions
   are declared so missing trailing components cannot masquerade as a smaller map.
5. The tool requires both perturbation signs for every cell, rejects nonfinite data,
   distinguishes unmeasured from measured zero, and reports unstable slopes, rank
   and conditioning. A sparse permutation pattern suggests component correspondence;
   it does not establish view-versus-pose semantics or camera ownership.
6. Predict downstream values for a **held-out perturbation and pose** using the proposed
   mapping. Compare prediction with measured payload, then verify the intended draw or
   pixels and exact restoration. Record the result through [research receipts](research-receipts.md).

The numerical Jacobian is a local sensitivity estimate: each cell is the average of
observed `delta_output / delta_input`. Sign disagreement can reveal nonlinear response,
noise, overwrites or the wrong consumer. Collect a smaller perturbation or improve the
instrument instead of increasing a tolerance until the result passes.

Do not require rank 16 by habit. A rigid camera pose has six independent degrees of
freedom; a legal parameterized camera can produce a lower-rank matrix response.
Only use `--expected-rank` when the independent input contract justifies that rank.
Direct writes that violate orthonormality can produce full rank while leaving the
valid camera manifold. Full rank alone never proves a correct VR camera.

The integrated checker is offline and does not inject, launch or mutate game memory.
Its tests establish behavior on synthetic fixtures; each project's runtime and headset
acceptance remain separate. Prefer an already established source/math contract over
running a new perturbation experiment when that contract answers the question.

Chapter [06](06-debugging-methodology.md) is about *proving* things once your code runs. This chapter is
about the step before: **locating the function, global, vtable, or struct field in the first place**, and
doing it in a way that survives a game patch.

If you are beginning or routing active work, start with the
[RE-owned workflow](reverse-engineered-route.md). It defines the ordered gates,
artifacts, live confirmations and stereo-architecture exit. This chapter is the
deeper reference for discovery and anchoring once a gate points here.

Much of the technique here is distilled from Praydog's write-ups on
[UEVR](https://praydog.com/reverse-engineering/2023/07/03/uevr.html) and
[Source 2](https://praydog.com/reverse-engineering/2015/06/24/source2.html), cross-checked against what
SS2VR, BioshockVR, and SOMAVR actually needed. UEVR is the most battle-tested example of the problem in
its hardest form — one injector that must work across a decade of Unreal versions it has never seen.

## Prove a slice's owner and count; do not infer an allocation header {#slice-owner-count}

An adjacent DynArray does not make every pointer a prefixed array. Prey's September
10 native getter takes the absolute QuatT base from `CPoseData+0x18`, indexes it
with stride 28, and obtains count from the owning pose at `+8`. The word before
the live slice was float bits, not count. Earlier offline fixtures had reproduced
the same wrong header assumption as the implementation. `[STATIC; LIVE in-game simulator]`

Trace the concrete getter and allocation/owner independently. Test a valid owner
with a poisoned false prefix, boundary indices and mismatched owners. Preserve the
separate measured prefix contract for real joint/attachment/ADIK DynArrays; a fix
to one field is not permission to rewrite every container reader. Evidence:
`PreyVR/docs/RE-VR-INTERFACE-2026-09-10.md`; target identity is pinned there.

### Order an override after the real latch, not a similarly named frame {#override-after-latch}

Prey's `RT_BeginFrame` writes the near-FOV cvar to the renderer before returning.
The corrected detour calls that original and then overrides through its verified
renderer receiver on the same thread. Earlier game-thread `CSystem::Render` writes
did not establish ordering against the render-thread latch. Disable delegates to
the next native latch, not a stale saved cvar. `[STATIC; LIVE harness]`

The production-callback fixture covers post-latch ordering, fallback sentinels,
disable and fail-closed receivers; it does not establish live cadence or downstream
projection agreement. Equal pre-write readback also cannot exclude another writer
that writes the same value. Evidence: `PreyVR/docs/RE-BUILD-TAKEOVER-2026-09-09.md`.

## The anchor ladder — prefer higher rungs

Rank your discovery method by how well it survives a patch. Climb down only when the rung above is
unavailable.

1. **The engine's own reflection/schema system.** If the engine can describe its own types, you don't
   need to reverse them. This is the jackpot.
2. **A symbol-bearing sibling build.** A Mac/Linux port, a dedicated server, or a debug build of the
   *same* engine may ship full symbols.
3. **An open-source ancestor or sibling engine.** Names and architecture for free (already the SS2VR and
   SOMAVR pattern — see below).
4. **String references.** The workhorse. Human-readable, maintainable, and likely to survive updates.
5. **Vtable / RTTI structure.** Stable-ish shape, but indices drift between versions.
6. **Byte-pattern (AOB) scanning.** Last resort. Use it *only* when necessary and *only* localized —
   inside a known function or near an anchor you already trust — never as a lone global signature.

### Rung 1 — the engine's own reflection system

Modern engines often carry a self-describing type system. Find it and generate your SDK instead of
hand-writing offsets. (*Source 2 ships an entire `schemasystem.dll`; `CreateInterface("SchemaSystem_001")`
hands you the interface, and the system is recursive — it describes the very classes it uses to describe
other classes. Class bindings live at a known offset in `CSchemaSystemTypeScope`. That discovery is what
made auto-generated headers possible.*) Unreal's `GUObjectArray`/UObject reflection is the same idea from
a different angle. Before you reverse a single struct by hand, ask whether the engine already knows its
own layout.

### Rung 1b — the engine's native-function registration table

A scripted engine has to connect script names to C++ implementations, which means it **ships a symbol
table** — usually an array of `{ const char* name; void* impl; }` built by static initializers. Find the
name string, find the dword that references it, read the pointer beside it. No hardcoded address, no
prologue scan, and it survives patches.

(*An independent BioShock mod found **1822** such entries in Vengeance/UE2.5, each named
`int<Class>exec<Function>` — e.g. `intAWeaponexecApplyAimError` — with the implementation pointer written
by static init. All five lookups in one session resolved first try, and dumping the whole table offline
became "the fastest first stop for any future engine question," giving a per-class inventory of every
native the engine exposes. See [13](13-teardown-bioshock-vr.md).*)

Two cautions that cost real time there:

- **The linker pools wide strings by *suffix*.** `AimError` is literally the tail of `ApplyAimError`, so a
  substring match proves nothing — **require the null terminator at the expected end**.
- **The registered thunk is usually *not* the seam you want.** A script-entry thunk
  (`exec…(FFrame&, void*)`) is called only from script; native C++ callers go straight to the
  implementation. Hooking all four aim thunks in that project caught **zero** calls during live
  shooting. Use the table to *find* the implementation, then hook the implementation
  ([06](06-debugging-methodology.md) on proving a hook ran).

Dumping the whole table is a one-pass scan of `.data` for pointer pairs whose first member points into a
string region and whose second points into `.text`. Both cautions above are encoded in the check —
note the explicit terminator test, which is what stops `AimError` matching the tail of `ApplyAimError`:

```c
/* UE2/Vengeance: static initialisers write { const char *name; void *impl; } pairs.
   Scan .data for that shape rather than hunting one name at a time. */
typedef struct { const char *name; void *impl; } native_entry;

static bool in_range(const void *p, const uint8_t *lo, const uint8_t *hi)
{ return (const uint8_t *)p >= lo && (const uint8_t *)p < hi; }

int dump_native_table(const uint8_t *data_lo, const uint8_t *data_hi,
                      const uint8_t *rdata_lo, const uint8_t *rdata_hi,
                      const uint8_t *text_lo,  const uint8_t *text_hi,
                      native_entry *out, int max_out)
{
    int n = 0;
    for (const uint8_t *q = data_lo; q + sizeof(native_entry) <= data_hi;
         q += sizeof(void *)) {
        const native_entry *e = (const native_entry *)q;

        if (!in_range(e->name, rdata_lo, rdata_hi)) continue;
        if (!in_range(e->impl, text_lo,  text_hi))  continue;

        /* plausible identifier, NUL-terminated inside the section */
        const char *s = e->name; size_t len = 0;
        while (in_range(s + len, rdata_lo, rdata_hi) && s[len] && len < 128) {
            char c = s[len];
            if (!(isalnum((unsigned char)c) || c == '_')) { len = 0; break; }
            ++len;
        }
        if (len < 4 || len >= 128) continue;

        if (n < max_out) out[n] = *e;
        ++n;
    }
    return n;   /* BioShock/UE2.5: 1822 entries, named int<Class>exec<Function> */
}

/* Exact-name lookup. The terminator test is the whole point: the linker pools
   strings by SUFFIX, so strstr()-style matching finds ApplyAimError for AimError. */
static bool name_is(const char *cand, const char *want)
{
    size_t n = strlen(want);
    return strncmp(cand, want, n) == 0 && cand[n] == '\0';
}
```

Dump it **once, offline, to a file** and grep that afterwards. The BioShock project's finding was that a
per-class inventory of every native the engine exposes becomes "the fastest first stop for any future
engine question" — which only pays off if the dump outlives the session that produced it.

### Rung 2a — the *retail* binary that shipped symbols

Before hunting for a sibling platform build, check the export table of the binary you already have.
Some retail games — especially pre-2010 titles built as a set of DLLs — ship with **thousands of named,
decorated C++ symbols exported**, because the modules had to link against each other. When that is true
the entire anchor ladder collapses to `GetProcAddress`.

(*Swat4-VR's `Engine.dll` exports **7,682** named decorated C++ symbols. Its frame-draw, camera,
secondary-view and console seams were all located **by name**, in one session, with no pattern scanning
at all. A debugger even named a global unprompted from the export table.*)

Run `dumpbin /exports` (or an equivalent) plus `undname` demangling as the *first* action on any new
target — it costs a minute and can save the entire signature-scanning phase. But mind the trap in the
next section: an exported address is often not the implementation address.

In-process, the whole rung is this much code. Note that it answers the negative case in the same pass —
a zero `VirtualAddress` in the export directory *is* the BioShock result, and it is what tells you to
stop looking for a shortcut that does not exist:

```c
/* Walk a loaded module's export directory, resolving each export past its thunk.
   cb receives (name, exported_address, resolved_body) -- they differ ~80% of the time. */
static void *resolve_thunk(void *p)
{
    uint8_t *b = (uint8_t *)p;
    if (b[0] == 0xE9) {                       /* jmp rel32 -- the common ILT thunk  */
        int32_t rel; memcpy(&rel, b + 1, 4);
        return b + 5 + rel;
    }
    if (b[0] == 0xEB)                         /* jmp rel8                           */
        return b + 2 + (int8_t)b[1];
    if (b[0] == 0xFF && b[1] == 0x25) {       /* jmp [mem] -- import stub           */
        int32_t disp; memcpy(&disp, b + 2, 4);
#ifdef _WIN64
        return *(void **)(b + 6 + disp);      /* RIP-relative on x64                */
#else
        return *(void **)(uintptr_t)disp;     /* absolute on x86                    */
#endif
    }
    return p;
}

int for_each_export(HMODULE mod,
                    void (*cb)(const char *name, void *exported, void *body))
{
    uint8_t *base = (uint8_t *)mod;
    IMAGE_DOS_HEADER *dos = (IMAGE_DOS_HEADER *)base;
    IMAGE_NT_HEADERS *nt  = (IMAGE_NT_HEADERS *)(base + dos->e_lfanew);
    IMAGE_DATA_DIRECTORY *dd =
        &nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT];

    if (!dd->VirtualAddress || !dd->Size)
        return 0;   /* structurally zero exports. A finding, not a failure. */

    IMAGE_EXPORT_DIRECTORY *ed = (IMAGE_EXPORT_DIRECTORY *)(base + dd->VirtualAddress);
    uint32_t *names = (uint32_t *)(base + ed->AddressOfNames);
    uint16_t *ords  = (uint16_t *)(base + ed->AddressOfNameOrdinals);
    uint32_t *funcs = (uint32_t *)(base + ed->AddressOfFunctions);

    for (DWORD i = 0; i < ed->NumberOfNames; ++i) {
        const char *nm = (const char *)(base + names[i]);
        void *exported = base + funcs[ords[i]];
        cb(nm, exported, resolve_thunk(exported));
    }
    return (int)ed->NumberOfNames;
}
```

**Run the thunk census before you plan anything around the export table.** Counting how many exports
survive `resolve_thunk` unchanged tells you immediately whether you are looking at bodies or at a jump
table — 6,057 of 7,682 in Swat4-VR's `Engine.dll` were thunks, and every cross-binary match attempted
from an unresolved export RVA returned zero hits at every threshold.

**The negative result is worth the same minute, because it retires a whole rung.** The habit was
era-specific and it ended: (*BioShock's 2007 Remastered executable has **no export table at all** — export
directory RVA `0`. The 2005-era practice of exporting engine symbols was gone by then, which means that
project's byte-pattern and RTTI ladder was **necessary rather than an oversight**, and knowing that early
would have saved second-guessing it.*) Parse the PE export directory and record the answer either way:
"thousands of symbols" and "structurally zero" are both findings, and the second one tells you to stop
looking for a shortcut that does not exist.

### Rung 2b — a build that shipped symbols

Different platform builds of the same engine are compiled from the same source with different symbol
policies. (*Source 2: the Mac binaries carried debug symbols, exposing every function, class, and
variable name — which is what the whole analysis was built on.*) Check Mac/Linux ports, dedicated
servers, SDK/editor builds, and older demo releases before assuming you're working blind.

### Rung 3 — the open-source ancestor, editing kit, or reimplementation

Already proven repeatedly: *SS2VR* used the released Dark/Shock source for system vocabulary and
architecture, and *SOMAVR* uses **HPL2 (Amnesia) source** to seed string and control-flow searches for
the closed HPL3 binary. Two more sources belong on this rung:

- **An official editing/modding kit.** If the developer shipped one, it names the game's own data
  structures and lets you *experiment offline*. (*HaloVR used H3EK both as a naming source and as a
  test bench — re-laying out the HUD in the kit proved which authored value controlled layout before
  anyone touched the running game.*)
- **A community reimplementation.** An open reimplementation of the engine gives you plausible function
  names and structure layouts to match against. (*HaloVR matched a HUD draw function to ManagedDonkey's
  `chud_draw_widget` and used its `s_chud_curvature_info` layout to interpret nearby fields.*)

The standing rule from [06](06-debugging-methodology.md) applies to all of them — they give you *names
and shapes*, but only the shipping binary is authoritative. Confirm every name and offset against what
actually ships.

### Rung 4 — string references, and how to resolve them

Strings are the preferred anchor because they're semantic: a developer is unlikely to rename
`"vr.InstancedStereo"` between patches, whereas the surrounding code is recompiled constantly. Find the
string, find its reference, then disassemble outward to the function or global you actually want (globals
usually via a `LEA`).

On x86-64 the reference is RIP-relative, so resolve the displacement:

```c
uintptr_t calculate_absolute(uintptr_t address, uint8_t instruction_length) {
    int32_t displacement = *(int32_t*)address;
    return address + instruction_length + displacement;
}
```

SOMAVR's semantic anchors are exactly this pattern applied to HPL3 — shader uniform names
(`a_mtxModelViewProjection`), config values (`FOV=70`, `NearClipPlane=0.03`) — and SS2VR located native
climb functions from their warning strings (`"BreakClimb: %s has no active physics models"`).

The operational form is a five-call loop. The concept is obvious; the sequence is the part worth having
written down, because each call's output is the next call's input and it is easy to stall halfway:

```text
search_strings(pattern="BreakClimb")            -> 0x005E1A4C  "BreakClimb: %s has no ..."
get_xrefs_to(address=0x005E1A4C)                -> [0x004C2871 (DATA, in FUN_004c2790)]
get_function_by_address(address=0x004C2871)     -> FUN_004c2790, size 0x1F4
decompile_function(name="FUN_004c2790")         -> read it: is this the climb break, or a logger?
rename_function_by_address(0x004C2790, "Physics_BreakClimb")   <- bank the name immediately
```

**Two failure modes at step two.** If `get_xrefs_to` returns nothing, the string is probably referenced
by an offset into a pooled blob rather than at its head — search the address *range*, not the exact
address. If it returns dozens, you have hit a shared format string; move to a *neighbouring* string that
is unique to the function you want.

**Bank the rename at step five, every time.** The most common waste in this fleet is re-deriving a
function someone already found because nobody wrote the name back into the database. A rename costs one
call and it is the only artifact of the work that survives the session.

#### Rung 4b — a naming convention in the string table can enumerate a whole type system

Rung 4 uses one string to find one thing. There is a stronger version: **look for a systematic
suffix or prefix that pairs entries**, and you can enumerate every type the engine has.

(*Frostbite ships each settings class name twice — once bare, once with an `-Array` suffix. BF2VR's
Ghidra script harvests every string ending `-Array`, strips the suffix, and now holds a list of **every
settings class in the game**. It then finds, for each bare name, the xref that is *itself a pointer* —
that is the class definition.*)

```python
# 1. the convention gives you the type list, for free
class_names = [s.replace("-Array", "") for s in defined_strings if s.endswith("-Array")]

# 2. for each name, the xref that IS a pointer is the class definition
for ref in XReferenceUtil.getXRefList(string):
    if getDataAt(ref).isPointer():
        all_refs[name] = ref; break
```

This is rung 1's self-describing type system reached from below: the engine did not hand you a
reflection API, but its *build process* left a regular pattern you can exploit. **Scan the string table
for repeated suffixes, prefixes and paired spellings before assuming there is no type inventory.**

**Their uniqueness handling is the part to copy**, and it is this chapter's rule implemented rather than
described:

```python
for fro, text in get_strings():
    if text in used:
        ban.append(fro)          # seen twice -> it is not an anchor
    used[text] = fro
keep = {k: v for k, v in used.items() if k not in ban}   # only names with EXACTLY one site
```

A name that resolves to two addresses is discarded outright rather than resolved by position. That is
`SCAN_AMBIGUOUS` as a filter, applied at harvest time.

### Rung 4c — hook an instruction where the object is already in a register

Every rung above tries to find a *function* — its entry, its prototype, its thunk. There is a different
move: **find any instruction at which the pointer you want is live in a known register, and hook
there.**

```cpp
// The RenderView is in RBX at this instruction. No prototype, no prologue, no thunk.
safetyhook::MidHookFn buildViewsFn = [](safetyhook::Context& ctx) {
    BuildViews(reinterpret_cast<RenderView*>(ctx.rbx));
};
buildViewsHook = safetyhook::create_mid(OFFSETBUILDVIEWS, buildViewsFn);

// Same trick to force the game's own render resolution to the headset's:
safetyhook::MidHookFn resizeScreenFn = [](safetyhook::Context& ctx) {
    Screen* screen = reinterpret_cast<Screen*>(ctx.rbx);
    screen->bufferWidth  = OpenXRService::swapchainWidth;
    screen->bufferHeight = OpenXRService::swapchainHeight;
};
```

**What it buys.** No calling convention to work out, no prologue to match, no
[thunk problem](#an-exported-address-is-usually-a-thunk-and-internal-callers-bypass-it), and it works
*mid-function* where the object is already resolved — often the only place a nested pointer exists as a
single value. It is frequently the cheapest way to reach an object that is never passed as an argument
anywhere you can hook.

**What it costs, and it is steep.** The anchor is now an *instruction plus a register allocation*, and
register allocation changes on any recompile — a far more fragile binding than a function entry. Treat a
mid-hook as the most version-brittle thing in your project: guard it with a byte check at the exact
instruction, and expect to re-derive it every patch.

**And confirm the register by observation, not by reading the disassembly once.** Log the pointer,
dereference a field you can predict, and check it matches before you write anything through it.

## Rung 6 — why AOB scanning is last

A long byte pattern encodes compiler output, not intent. It breaks on any recompile, and when it breaks
it either fails silently or matches the wrong address. Keep patterns short, scoped to a function you
already located, and always followed by a validation step ([07](07-engine-integration-safety.md)'s
prologue check).

If you must scan, scan *anchored* — inside a range you reached by a higher rung — and make a multiple
match as loud as a zero match. Silent first-match-wins is how a scanner returns the wrong address
without anyone noticing:

```c
/* Wildcards: mask[j] != 0 means "must match", 0 means "don't care".
   Distinguishes "no hit" from "more than one hit" -- the second is a broken pattern. */
typedef enum { SCAN_OK, SCAN_NONE, SCAN_AMBIGUOUS } scan_result;

scan_result scan_unique(const uint8_t *begin, size_t len,
                        const uint8_t *pat, const uint8_t *mask, size_t plen,
                        const uint8_t **out)
{
    const uint8_t *hit = NULL;
    *out = NULL;
    if (plen == 0 || plen > len) return SCAN_NONE;

    for (size_t i = 0; i + plen <= len; ++i) {
        size_t j = 0;
        for (; j < plen; ++j)
            if (mask[j] && begin[i + j] != pat[j]) break;
        if (j != plen) continue;

        if (hit) return SCAN_AMBIGUOUS;      /* second hit: refuse to guess */
        hit = begin + i;
    }
    if (!hit) return SCAN_NONE;
    *out = hit;
    return SCAN_OK;
}
```

Two properties matter more than the search itself. **`SCAN_AMBIGUOUS` is a distinct outcome** — a
pattern that matches twice is a broken pattern, and returning the first hit hides that. And **the scan
range should be a function you already own**, not the whole `.text` section: a pattern scoped to the 500
bytes you reached by string xref is a different risk class from one scoped to eight megabytes.

## Identify a vtable slot by what its code does, not by its index {#vtable-slot-by-behaviour}

UEVR supports Unreal 4.8 through UE5, where slot indices move between versions, so it cannot hardcode
any of them. Its answer is worth taking wholesale: **resolve the slot by fingerprinting the function
body.** `[SOURCE]`

For a two-way ambiguity, fingerprint the bytes:

```cpp
// In 4.18 the destructor virtual doesn't exist, or is at the very end of the vtable.
const auto is_stereo_enabled_index = sdk::is_vfunc_pattern(*(uintptr_t*)vtable, "B0 01") ? 0 : 1;
```

`B0 01` is `mov al, 1` — a function that returns true. If slot 0 does that, it is `IsStereoEnabled`
rather than a destructor, and everything after it shifts by one.

For a harder case, fingerprint **behaviour** instead of bytes. To find `CalculateStereoViewOffset` they
walk the first 30 slots and pick the one whose body uses **xmm registers at least ten times** — because
the view-offset maths is float-heavy and its neighbours are not:

```cpp
if (std::string_view{txt}.find("xmm") != std::string_view::npos && ++xmm_register_usage_count >= 10) {
    found = true;   // this slot does heavy float work; its neighbours don't
}
```

**A slot's index is a version artifact; what its code does is the thing you actually care about.** Pick a
property of the target function that its neighbours cannot accidentally satisfy — heavy SIMD, a
distinctive constant, a call to a known import — and search for that.

### Resolve jump thunks before you analyse

Slots routinely point at a relative jump rather than the function:

```cpp
while (*(uint8_t*)func == 0xE9) {      // E9 = rel32 jmp
    func = utility::calculate_absolute(func + 1);
}
```

Analysing the thunk instead of the body is how a fingerprint scan finds nothing in a binary that
plainly contains the function.

### Exhaustive decode, not a linear scan

Their comment names the reason, and it is one this playbook has met from the other direction:

> We do an exhaustive decode (disassemble all possible code paths) that correctly follows the control
> flow because **some games are obfuscated and do huge jumps across gaps of junk code**, so we can't just
> linearly scan forward as the disassembler will fail at some point.

They step **over** unconditional calls rather than into them, and bound the walk. A linear disassembler
desynchronises the moment it hits data or padding in the code stream; following control flow does not.
See [Disassembly has to follow every branch](#disassembly-has-to-follow-every-branch).

## Your vtable hook can be installed correctly and never run {#devirtualisation-hazard}

This is the subtlest failure in the survey, and UEVR carries a patch for it with an honest disclaimer
attached — *"I've only seen this in one game so far..."* — so treat it as `INFERENCE` until you see it
on yours. `[SOURCE]`

The compiler can **devirtualise a call it can prove the type of**, emitting something shaped like:

```text
if (obj->vtable == &FFakeStereoRendering::vtable)   // known type?
    <inlined body of the virtual, compiled in place>
else
    call obj->vtable[n]                             // the slot you hooked
```

**When the check passes, your hook never executes** — the engine runs an inlined copy of the original
instead. The hook is installed, the address is right, the log line saying "hook installed" is true, and
the behaviour is unchanged. UEVR's remedy is to locate those comparison sites against the class's vtable
address and patch them so the indirect path is always taken.

**The tell is a comparison against a vtable address near the call site.** If you have proved a vtable
hook is installed and it still never fires, this belongs on the list alongside
[a hook that is never reached](06-debugging-methodology.md) and
[`/OPT:ICF` folding](#two-different-functions-can-share-one-address-opticf). See
[HOOK-003](pattern-catalog.md#hook-003).

## Hardware breakpoints are a shared, finite resource {#hardware-breakpoint-etiquette}

BFVR's early D3D8 observer is the most disciplined use of execution breakpoints in this survey, and
every rule it follows exists because the debug registers are **four slots shared with every other tool
in the process**. `[SOURCE]`

**Chain one-shot breakpoints through a startup sequence.** They arm `IDirect3D8::CreateDevice`, `Clear`,
`BeginScene`, `EndScene`, the first `Present`, and then `Reset`; each handler copies only entry values
and **disables its target after the first hit**, freeing the slot for the next stage. Six observation
points, four registers, no permanent instrumentation.

**When you run out, say so instead of guessing.** If startup reaches `Reset` before scene-phase evidence
is complete, they reuse the three freed slots for one `SetRenderTarget`, `SetTransform` and `BeginScene`
entry each — and if any target is still absent when the bounded diagnostic exits, **it reports partial
results**. That is [TEST-002](pattern-catalog.md#test-002)'s rule in a different domain: an instrument
that cannot complete its census must not present as though it did.

**Save, restore, and yield to whatever was already there.** Their thread-ownership pass arms a one-shot
`Present` breakpoint on other existing game threads, but only after saving and later restoring that
thread's unused debug-register context — and **threads that already have an active debug-register
setting are skipped entirely.** Clobbering another debugger's or another tool's breakpoint is a real and
easily-caused failure, and the polite form costs almost nothing.

**A probe that hurt once stays absent, with its reason.** Their source deliberately omits a local-player
probe at one address because it sits on a hot null-return path and **froze a map-load diagnostic
session**. The absence is documented where the probe would be. A negative result recorded in the code is
worth more than the same result in a chat log.

### Keep IAT mutation off the loader lock

The same prototype shows the safe shape for entering a process early: start the game **suspended**,
`LoadLibrary` the client, invoke the client's exported initializer **on a second remote thread while the
game is still suspended**, and only then resume. This keeps the IAT write outside `DllMain` and the
Windows loader lock entirely.

Their initializer replaces only the game executable's in-memory `Direct3DCreate8` IAT entry and
**returns the original `IDirect3D8` interface unchanged** — no wrapper, no vtable edit, no patched D3D8
code. Observation first; substitution only once you know what you are substituting. See
[A4](a4-hook-safety.md) and [RE-005](pattern-catalog.md#re-005).

## Never rely on a single discovery method

For anything critical, implement **stratified fallbacks** and take the first that validates. UEVR's
approach for a single critical function is the model: try string-reference options, then vtable analysis,
then call-stack analysis from an already-installed hook, then exhaustive static analysis of code paths.
Four independent routes to the same answer means one patch rarely kills all four.

Log *which* method succeeded. When a game updates and behavior changes, "we fell back from method 1 to
method 3 this time" is the first clue.

## Enumerate mutable instances from the writer, not the getter {#writer-census}

A getter census answers **which records its callers requested**. It is not an
inventory of the records that exist. For mutable arrays—bones, particles,
lights, transforms, animation jobs—the code that creates or writes the records
has the broader view. More precisely: a writer hook sees every record passing
through *that evaluation seam*; it still does not prove that every producer in
the engine uses that seam.

Far Cry 2 supplied a measured example in one day of live work. A bone-accessor
census recorded **92,298 calls** but only **three distinct `(entity, bone)`
pairs** across 2-, 6- and 9-bone rigs. The accessor was an attachment query:
callers only asked for muzzle and shell-eject sockets. A write watchpoint found
the matrix-writing instruction; intercepting that writer for three seconds
observed **291,108 calls** and 318 distinct record addresses. Sorting those
addresses and grouping runs separated by the proven `0xA0` record stride
exposed contiguous rigs of **106, 101 and 101 bones**. The consumer trace had
never named any of them. `[LIVE]`

Use this ladder:

1. **Static layout.** Follow any trustworthy getter to the backing store and
   record base/count offsets, record stride and the mutable field within each
   record. Static analysis gives the shape, not the live population.
2. **Live writer.** Put a hardware write watchpoint on one known live record.
   Record the instruction and full register context. This crosses virtual-
   dispatch holes that can make a static call graph look complete when it is
   not. The mechanics - and the three ways a data watchpoint fails without
   reporting anything - are [RE-009](pattern-catalog.md#re-009); a write
   breakpoint traps *after* the store, so the address you capture is the
   instruction following the writer.
3. **Writer census.** Intercept the writer briefly; collect record bases only.
   Sort and group them by the proven stride. A contiguous run is a candidate
   array. Far Cry 2 ignored runs shorter than four because its shared matrix
   helper had unrelated callers; that cutoff is target evidence, not a
   universal constant.
4. **Ship discovery, not addresses.** Reimplement the bounded census inside the
   mod and reacquire on every process/level/object generation. Heap addresses
   are session receipts, never anchors.

The writer is often the hottest hook in the project. Far Cry 2's ran roughly
97,000 times per second. Its common path became one armed-state read and return;
the armed path performed one bounded fixed-capacity hash insertion—no scan, heap
allocation, formatting or logging. Sorting, grouping and reporting ran cold
from the frame loop after sampling stopped. A full table must degrade into
dropped samples with an explicit `truncated` result, never an unbounded probe
loop inside animation.

### Prove the consumer with pixels

A successful write and readback prove only memory access. In the same project:

| Lever | Machine-visible result | Render result |
|---|---|---|
| weapon-camera offset | write landed and read back | camera moved |
| player aim-angle field | value held | no player effect |
| 9-bone attachment rig | 41,263 writes, zero rejects | no pixels moved |
| 101-bone rig | writes landed | body rose 0.5 m and its shadow moved |

Make the treatment deliberately unmistakable: half a metre on one axis, with
an armed zero-delta control and a clean off state. A moved shadow is especially
strong evidence because it proves a downstream render consumer, not merely a
debug overlay or cached CPU value. Until an external pixel, shadow, projectile
or similarly independent effect changes, the candidate is only writable—not
authoritative.

Read sporadic single-frame motion correctly. The proven 101-bone poke survived
only 4–5 frames per second out of 60 (about 7%): the write was correct, but the
engine's later skeleton evaluation overwrote it. That symptom is a **writer
race**, not a dead address. Two viable ownership strategies are:

- become the last writer and suppress/clear the engine's evaluate-if-dirty
  rebuild for that frame, restoring the flag when the feature is disabled; or
- write inside evaluation, immediately after the engine finishes the record.
  In Far Cry 2 the animator visited records in order, so the detour reapplied
  the modification to record `N-1` when record `N` arrived.

Prove ordering before using the second technique; adjacency in one sample is
not an API contract. Guard target range, record stride, finite matrix contents,
object generation and disable restoration.

### Three ways to manufacture a false negative

- **Unverified tool parameters.** Confirm the requested parameter exists in the
  tool schema and that the response reports the effective value. One Far Cry 2
  read-watch test passed a nonexistent `trigger` field; it was silently dropped
  and the real `access_type` defaulted to write. The read experiment never ran.
- **A stale target.** A holstered/swapped rig may stop animating. Reconfirm live
  writes before blaming the monitor or hook.
- **A short-lived instrumentation script.** Some Frida wrappers evaluate a new
  script per command. An “arm now, fetch later” sequence then destroys its own
  hook. Install, sample, wait and report inside one script when persistence is
  not guaranteed.

Finally, a complete writer census does not identify the first-person
viewmodel. Far Cry 2's full rigs moved NPC bodies and shadows but not the
player's arms; the viewmodel uses a separate render/animation path. The census
proves which arrays exist at one writer. Draw provenance still decides which
one appears in front of the camera. Use the copy-ready
[`MUTABLE_ARRAY_CENSUS.md`](project-evidence-templates.md#mutable_array_censusmd)
receipt and the atomic [RE-004 pattern](pattern-catalog.md#re-004).

## Disassembly has to follow every branch

Simple linear disassembly from an anchor misses things, because inlining decisions move code between call
levels across builds. (*UEVR: the `"vr.InstancedStereo"` string isn't guaranteed to sit at the same
call-stack level as a neighbouring anchor string, so the analyzer exhaustively disassembles and follows
all branches, adding each call it sees to a queue.*) If a string-anchored search fails, the target is
usually one branch deeper, not absent.

## Emulation and data-flow tainting

When static reading isn't enough — obfuscation, or a value assembled across many instructions — run the
code in an emulator (UEVR uses `bddisasm`/`bdshemu`) and *watch* it:

- **Observe** register values and memory writes to learn what a function actually computes.
- **Taint**: write a magic number into a register or memory location at an anchor point, then track where
  that value flows. This turns "which field does this end up in?" into an observation instead of a guess —
  the static-analysis sibling of the runtime readback probe in [06](06-debugging-methodology.md).

Budget for it: emulation and exhaustive path analysis are fast on clean builds (string scans are
millisecond-scale) but can be extremely slow on obfuscated ones. Gate them behind the cheaper methods.

## Validate a discovery by provenance, not by hope

The strongest confirmation that you found the right thing is a property only the right thing has.

- **Provenance of a returned pointer.** (*UEVR bruteforces a texture vtable to find the function returning
  an `ID3D12Resource*` — by calling candidates and checking whether the returned object's vtable address
  lands inside a DirectX DLL.*) The module a vtable lives in is a strong identity signal.
- **Structure sanity checks.** When bruteforcing a struct layout (UEVR does this for `GUObjectArray`),
  assert that integer fields look like plausible integers and pointer fields are actually valid, readable
  pointers — and handle known layout variants (inlined vs chunked arrays) explicitly rather than assuming
  one shape.
- **Instrumented/dummy vtables.** To learn *which* virtual index or member offset the engine uses, install
  a vtable of near-identical functions (template metaprogramming generates the variants) and see which one
  gets called. (*UEVR uses this to find the frame-count offset inside `ViewFamily`.*) This is the
  multi-candidate residual probe from [06](06-debugging-methodology.md), applied to vtables.
- **A numeric self-consistency residual — but prove the metric can see the error you care about, and
  derive your own threshold.** When you reconstruct a matrix from disassembly or captured constants, you
  usually have an algebraic identity that must hold if the reconstruction is right. Assert it — then
  attack the assertion, because this has now gone wrong twice in two different ways.

  **First failure: the bound was decoration.** (*BioshockVR validated a derived per-draw projection by
  checking that `oldWVP · P_center⁻¹` comes out affine, with a first gate allowing residual 250.0 — loose
  enough that a **guessed** 75° FOV passed and silently corrupted geometry. Tightening to 1.0 rejected it
  at 96.65.*)

  **Second failure, and the more instructive one: the metric was blind to the error class.** (*FarCry2-VR
  built the same gate and found a pure affine check is **mathematically incapable** of detecting a wrong
  FOV — `P⁻¹`'s last column is built purely from near/far, while FOV and aspect live in the `w`/`h` terms
  and never touch it. Their guessed 75° FOV scored **0.000031, identical to correct**. The fix was an added
  orthonormality term: a view matrix's upper-3×3 is a rotation, and a wrong FOV rescales the recovered
  basis, so basis scale is the thing that actually carries the error.*)

  **Then they imported the other project's 1.0 threshold and it was looser than no gate at all**, because
  the two metrics are scaled differently — their normalised term is bounded near 1, so every wrong case
  they tested still scored under it:

  | case | residual |
  |---|---|
  | correct | 0.000031 |
  | 5° FOV error | 0.094 |
  | wrong aspect | 0.216 |
  | guessed 75° FOV | 0.250 |
  | wrong near/far | 0.800 |

  They derived **0.01** from their own gap — ~300× above correct, ~9× below the tightest wrong case — and
  asserted every wrong case fails, so raising the threshold later breaks a test rather than quietly
  weakening the gate.

  **Three rules, in order.** Build a table of *deliberately wrong* inputs before you pick a number. Confirm
  the metric separates them at all — if a wrong input scores like a correct one, the metric is blind and no
  threshold will save it. Then derive the threshold from your own gap, and never import someone else's:
  a residual limit is a property of a metric, not of a problem.

  (*Unplanned dividend: the same residual settled row-vector versus column-vector convention empirically —
  column residual 0.000031, translation in the last row — instead of by assumption.*)

## An exported address is usually a thunk, and internal callers bypass it

Two different mechanisms, one lesson, and both have now bitten projects in this playbook:

- **Incremental-link thunks.** With incremental linking, an exported symbol resolves to a five-byte
  `jmp` stub, not the function body. Callers *inside the same module* are linked directly to the
  implementation and never touch the stub — so a hook on the export catches only external calls, which
  for engine internals is usually **none**. Follow the `jmp` and hook the destination. (*Swat4-VR.*)
- **Script-entry thunks.** On engines with a script VM, the registered native is a script-entry wrapper;
  native C++ callers go straight to the implementation. (*bioshock-vr hooked all four aim thunks and
  caught **zero** calls during live shooting — see the native-function-table section above.*)

A third variant catches you on the *way out* rather than the way in: **the immediate return address inside
a shared utility identifies the utility's own wrapper, not the caller you care about.** Every engine
funnels many logically distinct call sites through one low-level helper — a buffer upload, an allocator,
a formatter. (*BioshockVR hooked its cbuffer-upload wrapper and logged the immediate caller RVA; it
resolved to the same renderer-state-flush function every time, whether the write came from a material, a
BSP or a model-batch route. Only walking to stack frames 3 and 4 exposed the route-distinguishing
callers.*) If you are attributing *routes*, you need enough stack depth to clear the shared plumbing —
and you should verify how much depth by checking that two known-different routes actually differ at that
frame.

The general rule: **an address you obtained by name is a starting point, not a hook site.** Verify what
is actually at it, follow any jump, and then prove the hook *fires* before designing on it
([06](06-debugging-methodology.md)).

## A vtable *slot* can be a thunk too — and declaration order is not slot order

The thunk trap above has a vtable-shaped sibling, and it catches people who think they have escaped it
by resolving through an interface rather than an export.

**Overload declaration order in a header does not determine slot order in the shipped vtable.** Old
toolchains ordered them differently, so counting declarations in the SDK header to derive a slot index
produces a confident wrong number.

(*FEAR VR probed the retail VC7.1 vtable read-only and found **slot 17 is not the implementation** —
it is the one-argument alias, whose entire body forwards to slot 19 with `techniqueOverride = nullptr`:*)

```text
slot 17:  8B 54 24 04    mov edx,[esp+4]
          8B 01          mov eax,[ecx]
          6A 00          push 0            ; the defaulted argument
          52             push edx
          FF 50 4C       call [eax+0x4c]   ; 0x4C / 4 = slot 19  <- the real one
          C2 04 00       ret 4
```

Two defences, both cheap, both from that project:

1. **Verify the forwarding stub's bytes before patching**, and leave the vtable *completely untouched*
   if they do not match. Fail closed — a slot index that is wrong by one on an unrecognised build is a
   wild call through an unrelated function pointer.
2. **Tie the magic number to the constant at compile time**, so the byte pattern and the slot index
   cannot drift apart during a later edit:

   ```cpp
   static_assert(0x4C / sizeof(void*) == kRenderCameraWithOverrideSlot,
                 "Retail RenderCamera forwarding slot changed.");
   ```

The general rule is the same as for exports: **resolve to the body, and prove you are at the body.** A
short function whose only job is to push a constant and jump is a forwarder, whatever kind of table you
reached it through.

## An official SDK can compile and still be unshippable: the CRT ABI wall

Rung 3 says the ancestor gives vocabulary, not truth. There is a harder version of that for games with
an **official** source release, and it decides your whole architecture.

(*FEAR ships Public Tools 1.08. FEAR VR built it successfully as PE32/x86 with VS2022 + v141 —
`GameClient.dll` 1.08.282.0 — and then refused to ship it. The retail module imports
`MSVCP71.dll`/`MSVCR71.dll` (Visual C++ 7.1); the v141 build imports `MSVCP140`/`VCRUNTIME140` and the
UCRT. The engine exchanges C++ and CRT objects across the module boundary, so **source compatibility is
not enough**. A live test with only the rebuilt module reproducibly killed the game with `0xC0000005`
inside `MSVCR71.dll`. Their deploy script now aborts on ABI grounds before copying a single file.*)

**Check this before you plan any rebuild-based mod:** read the shipping module's imports and ask whether
you have that toolchain. For anything built before roughly 2010 the answer is usually no — and then the
SDK's role changes from *artifact* to **oracle**: it gives you exact call sites, struct layouts, enum
orders and semantics, every one of which you then confirm against, and patch into, the retail binary.

That is a promotion, not a consolation. Reading the source is how FEAR VR found the one call that
renders the world and does nothing else ([17](17-teardown-fc2vr-native-stereo.md)) — a seam that would
have taken far longer to find, and to trust, from disassembly alone.

## When the decompiler is unusable, raw byte decode is a complete workflow

Sometimes the best tool on the bench simply will not run on your target. It is worth knowing that this
does not stop the work — it only slows it.

(*The Cyberpunk 2077 port carries a hard project rule: **never** call `decompile_function` or
`disassemble_function` against that IDB, because IDA crashes repeatedly, even on small functions, and a
crash loses the whole session. Their entire 80-document reverse-engineering effort was conducted with
raw byte reads plus xref navigation.*)

The substitute toolkit is smaller than you would expect:

```text
read_memory_bytes   + manual x86-64 decode     <- function bodies, prologues, call targets
get_xrefs_to / get_callers                     <- navigation
data_read_qword / list_globals_filter          <- vtables, globals, registries
```

That is enough to resolve vtable slots, decode `E8`/`E9` targets, walk call graphs and read struct field
offsets — everything this chapter asks for. **A decompiler is a convenience, not a prerequisite.**

Two practical notes from the same project. Their rule also says **MCP calls may time out at one second**
— re-check the connection rather than assuming a crash, because treating a timeout as a crash costs you
the session you were trying to protect. And a decompiler that crashes on *some* functions is worse than
one that crashes on all of them: they started with a "hostile functions only" exemption and eventually
banned it outright, because the exemption required predicting which functions were hostile.

## Anchor a pattern scan on its rarest byte

A naive signature scan compares at every offset. You can usually skip most of them: **find candidate
positions with `memchr` on one byte of the pattern, then verify the rest only there.**

(*Halo-MCC-VR: "memchr-anchored signature scan — **7x faster, byte-identical results**." Their commit
states the correctness guarantee alongside the speedup, which is the right way to describe an
optimisation to a search.*)

```c
/* Anchor on the pattern's first REQUIRED byte -- and prefer a rare one.
   memchr is usually SIMD-accelerated by libc; a hand-rolled loop is not. */
const uint8_t *p = begin;
size_t remaining = len - plen;
while ((p = memchr(p, pat[anchorIdx], remaining - (p - begin))) != NULL) {
    const uint8_t *cand = p - anchorIdx;
    if (cand >= begin && matches(cand, pat, mask, plen)) { /* verify fully here */ }
    ++p;
}
```

Two notes. **Pick the anchor byte for rarity, not position** — anchoring on `0x48` in x64 code matches
almost everywhere, while an opcode or an immediate from the middle of the pattern may occur a handful of
times in the whole section. And **byte-identical results is the property to assert**: a faster scan that
returns a different address is not an optimisation, so keep the naive implementation as a test oracle
and compare them over the whole module once.

This matters more than it sounds when the scan runs at injection time on an eight-megabyte `.text`, and
when [anchoring the scan to a known range](#rung-6-why-aob-scanning-is-last) is not possible.

## Two different functions can share one address: `/OPT:ICF`

MSVC's **identical COMDAT folding** merges functions with identical machine code into a single body.
The linker does this by default in release builds, and it means **two semantically unrelated functions
can resolve to the same address**.

(*PreyVR measured it: `IRenderView::GetFrameId` and `ISystem::GetGlobalEnvironment` had folded onto the
same address. Both are one-line getters returning a member, so their code is byte-identical.*)

The consequence is not a wrong name — it is a **wrong hook**. Hook a folded address and you hook *every
caller of every function folded onto it*, including callers you never wanted and cannot see. Simple
accessors are the highest-risk class precisely because they are the most likely to be byte-identical.

**The defence is free, because you already have it:** the uniqueness test used for signature promotion.
Before hooking, ask whether this address is reached under more than one name, or whether the byte
sequence you matched occurs more than once. It is the same `SCAN_AMBIGUOUS` outcome from
[Rung 6](#rung-6-why-aob-scanning-is-last) — a second hit is a finding, not a tie to break.

**When you must hook a folded function**, filter inside the detour rather than at install time: check
the return address ([§ Disambiguate a shared callee by its return
address](#disambiguate-a-shared-callee-by-its-return-address)) or the `this` pointer, and pass everything
else straight through.

### Measured: it is real, rare, and often *aliasing* rather than folding

Swat4-VR ran the census across three binaries:

| Binary | Exported names | Distinct bodies | Shared-body groups |
|---|---|---|---|
| UE2.5 `Engine.dll` | 7,682 | 7,669 | **7** |
| UE2.0 `Engine.dll` | 7,497 | 7,484 | **7** |
| UE2.5 `Core.dll` | 2,687 | 2,682 | **4** |

**0.09% of names.** Rare — but the ones it hits are the dangerous ones: `?IsLocallyControlled@APawn@@`
and `?PlayerControlled@APawn@@` share one body. Two accessors, one class, nothing to tell them apart.

**And the mechanism there is not classic ICF.** Each non-primary name resolves in three hops, routed
*through the primary's own thunk*:

```text
?Render@FSkySceneNode@@ -> 0x1DE4E0 -> 0x131C4 -> body 0x1DB4C0
                                       ^^^^^^^ FLevelSceneNode::Render's OWN thunk
```

That is linker symbol resolution, not two identical bodies merged. **The observable is the same — N
names, one body — and so is the hazard.**

**The check to adopt, from them:** *before trusting any name a matcher hands you, resolve it and check
whether another export lands on the same body.* One lookup. It is the difference between naming a
function and naming its neighbour — and it applies to **your own resolver** too. They audited the 13
symbols their mod resolves, across both executables separately: 12 clean, and the 13th was a **live
collision on a hook they ship** (`FLevelSceneNode::Render`, shared with `FSkySceneNode::Render`, four
vtables dispatching there). It had been silently over-counting.

> **It does not explain the 46%.** I implied it might. Seven groups in 7,682 names is 0.09%; for
> aliasing to account for their class-A miss, that single sampled miss would have to be one of ~20
> aliased names — a ~0.3% coincidence. **`total_matches` and tie counts remain the better explanation**,
> and are unaffected.

## Function *attribution* is less sound than call-site detection

A related warning about your own tooling, from the same project. Sweeping for call sites is reliable;
deciding **which function each site belongs to** is not.

(*PreyVR swept for `CALL [reg+0x388]`, found 144 candidate sites, and attributed each to a function by
scanning backwards to `CC CC` padding. **MSVC does not always pad function boundaries**, and one known
call site was mis-bucketed and appeared missing entirely.*)

Two rules follow. **Report the two separately** — "144 sites found" is a measurement, "in these 84
functions" is an inference, and they deserve different confidence. And **seed the sweep with an answer
you already know**: they caught the mis-bucketing only because a site they had previously confirmed came
back missing. A sweep with no known-good needle in it cannot tell you it is broken.

The `entry_from_padding` helper earlier in this chapter carries the same caveat: it returns `NULL` when
it cannot find a padding run precisely so that a missing boundary is visible rather than guessed.

## Record the module base alongside every RVA

An RVA is meaningless without knowing which module it is relative to *and where that module actually
loaded*. In a multi-DLL game some modules hold their preferred base while others get relocated — so the
same recorded number can be valid one run and garbage the next.

(*FarCry2-VR: `Dunia.dll` holds its preferred base `0x10000000` in the live process while the other game
DLLs collide with it and relocate. Their rule: **any RVA recorded against a relocated module is
meaningless without its live base — record base + RVA together, always.***)

This is the operational half of "RVAs are evidence, signatures are authority": record freely, but record
*completely*, and resolve at runtime.

## Prologue scans lie in four specific ways

Walking backwards for `55 8B EC` (`push ebp; mov ebp,esp`) is the standard "find the function start"
move, and it fails in ways that produce a *plausible wrong answer* rather than an error:

- **Frameless functions have no such prologue at all** — a thread-main loop starting `push esi` is
  invisible, and the scan walks straight past it into the previous function.
- **Aligned-stack functions use a different form** (e.g. `push ebx; mov ebx,esp; sub esp,N; and esp,-16`),
  so the scan overshoots them too.
- **It lands on decoys.** In one case the backwards scan found an SEH helper sitting immediately before
  the real target.
- **On x64, an optional `REX` prefix moves the entry by one byte** — and everything after it still reads
  as plausible code. REX bytes (`40`–`4F`) are compiler-dependent, so two builds of "the same" function
  can differ by exactly one leading byte. This bit SOMAVR **twice**: a raycast signature expected
  `57 48 83 EC 60` where the binary had `40 57 48 83 EC 60`, which shifted the RIP-relative displacement
  from `+8/+12` to `+9/+13` and broke an outer and an inner hook simultaneously — presenting as two
  unrelated failures. Separately, a shutdown hook's guard omitted the leading `0x40` of
  `40 53 48 83 EC 20 48 8D 05` and refused to install at all.
  **Signatures hand-copied or re-derived between 32- and 64-bit builds are one byte short of matching
  nothing**, so anchor on the true prefix rather than an assumed instruction start.

That last one carries a second lesson worth stating separately: because SOMAVR's guard was **strict**, the
mismatch made the hook *refuse to install* rather than patch the wrong address. A fail-closed signature
guard turns a one-byte mistake into a loud no-op instead of a wild write. Both failures also presented as
"the hook silently does nothing" — expensive to diagnose, which is why the diagnostic should report
**actual-vs-expected bytes and the RVA**, not just `signature_mismatch`.

**The reason this one is worth auditing for proactively: its signature is that it doesn't look like a
failure mode.** It presents either as several unrelated faults, or as one function that is merely
*inconvenient to anchor*. (*SOMAVR hit it and saw two unrelated broken hooks. PreyVR hit it and had already
**logged it as a workaround** — a signature note reading "unique interior begins at `+0x27`" is someone
silently routing around a broken prologue match without recognising it as a class.*) **The tell is any
signature where somebody abandoned the prologue for an interior anchor.** If your registry contains even
one, audit the rest before trusting any cross-build translation.

Scope it correctly, though: **REX prefixes are x64-only.** Do not audit a 32-bit target for this — of the
projects in this playbook it applies to the 64-bit ones (SOMAVR, PreyVR) and not to the 32-bit ones.

The four failures side by side, as bytes. Every row after the first is something a `55 8B EC` scan
walks straight past:

```text
55 8B EC                    push ebp; mov ebp,esp        <- the only form the scan finds
56                          push esi                     <- frameless: thread-main loops, leaf fns
53 8B DC 83 EC 08 83 E4 F0  push ebx; mov ebx,esp;       <- aligned-stack form (BioShock's real
                            sub esp,8; and esp,-16          scene-build root)
40 57 48 83 EC 60           REX.W=0 + push rdi; sub      <- x64: the 0x40 shifts entry by one byte,
                            rsp,60h                         and every RIP displacement with it
```

The reliable boundary marker is the **`CC` padding run** the linker inserts between functions: find the
run, and the next byte is the true entry. (*The first three failures above are from the same BioShock
project's hunt for its scene-build root — the real prologue was `53 8B DC 83 EC 08 83 E4 F0`, and the
boundary was an 11-byte `CC` run.*)

```c
/* Walk back to the true function entry using linker padding, not a prologue guess.
   Requires a RUN of padding -- a lone 0xCC is a legitimate int3, and 0x00 bytes
   appear inside instruction encodings constantly. */
#define MIN_PAD_RUN 4

const uint8_t *entry_from_padding(const uint8_t *inside,
                                  const uint8_t *lo,      /* section start */
                                  size_t max_walk)
{
    const uint8_t *q = inside;
    const uint8_t *stop = (inside - lo > (ptrdiff_t)max_walk) ? inside - max_walk : lo;

    while (q > stop) {
        if (q[-1] == 0xCC || q[-1] == 0x90) {
            size_t run = 0;
            const uint8_t *r = q;
            while (r > stop && (r[-1] == 0xCC || r[-1] == 0x90)) { --r; ++run; }
            if (run >= MIN_PAD_RUN)
                return q;          /* first byte after the run == true entry */
            q = r;                 /* short run: a real int3, keep walking   */
            continue;
        }
        --q;
    }
    return NULL;                   /* say so; do not return a guess */
}
```

**Return `NULL` rather than a best effort.** The whole failure class here is *plausible wrong answers*,
and a resolver that always produces an address is what converts a missed boundary into a wild hook. Pair
it with a fail-closed guard at the call site:

```c
/* Fail closed, and report enough to diagnose in one shot: the SOMAVR lesson was
   that "signature_mismatch" alone cost days, while actual-vs-expected + RVA is instant. */
bool verify_site(const uint8_t *addr, const uint8_t *expect, const uint8_t *mask,
                 size_t n, const uint8_t *modbase, const char *what)
{
    for (size_t i = 0; i < n; ++i) {
        if (mask[i] && addr[i] != expect[i]) {
            log_error("%s: byte %zu at RVA +0x%zX -- expected %02X, found %02X",
                      what, i, (size_t)(addr - modbase) + i, expect[i], addr[i]);
            log_error("  expected: %s", hexdump(expect, n));
            log_error("  actual:   %s", hexdump(addr,   n));
            return false;      /* loud no-op beats a wild write */
        }
    }
    return true;
}
```

## Look for ground-truth source before you disassemble

Two channels of ground truth routinely beat disassembly, and both are cheap to check first:

- **The game may ship its own scripting layer as readable source.** Many commercial engines with a Lua,
  AngelScript, Python or custom-DSL layer ship it in plaintext even when the core binary is stripped.
  (*SOMA ships its entire gameplay logic as uncompiled AngelScript `.hps` files. Reading one interaction
  script gave the exact PID gains — `P=400 / I=0 / D=40` for position, `40 / 0 / 0.4` for rotation — the
  mass-coupling rule, and the fact that the throw path **teleports the prop before applying impulse**.
  Recovering any of that from x64 disassembly would have taken far longer, and the last item is the kind
  of ordering detail disassembly makes easy to miss.*)
- **The closed engine may have an open-source ancestor or sibling.** (*Frictional's fully open HPL2, from
  Amnesia, is structurally close enough to HPL3 to confirm function identity and matrix composition order
  before opening Ghidra at all.*)
- **Someone may have already reversed the exact thing you need — as a 3D-fix mod.** Legacy stereoscopic-3D
  packages (3D Vision / Helix / 3Dmigoto), ReShade fixes and fan shader-patches encode *already-solved
  constant layouts* for the specific game. (*An old stereo 3D-fix for BioShock Remastered named
  `screenDataToCamera` at `c3`, `worldViewProj` at `c10–c13` and `localEyePos` at `c14`. Live probes
  confirmed those exact offsets on the shipping shaders, collapsing roughly twenty builds of blind cbuffer
  scanning into direct verification.*) These mods solve a neighbouring problem — getting stereo out of a
  mono renderer — so their findings are unusually well-aligned with yours. Search for one before you scan.

Chapter [06](06-debugging-methodology.md) already warns that an open-source ancestor gives *vocabulary and
architecture*, not truth — confirm every name and offset against the shipping binary. The point here is
sequencing: check for both channels **before** the first disassembly session, not after twenty builds of
blind scanning.

## Borrow names from a sibling *binary*, by matching functions

Rung 3 says an open-source ancestor gives you vocabulary. There is a binary-only version of the same
idea that this playbook has been leaving on the table: **when two binaries share a code lineage and one
of them has symbols, function matching can carry names across.**

The fleet has an unusually clean instance of this and has not used it:

> **Swat4-VR's `Engine.dll` exports 7,682 named, decorated C++ symbols.
> BioshockVR's executable has no export table at all.** Both are Unreal 2.5 "Vengeance."

Every function SWAT4 can name by `GetProcAddress`, BioShock has to find by pattern. If a matcher can pair
them, SWAT4's symbol table becomes a naming oracle for a binary that ships none. The same shape recurs
wherever you have: two builds of one game, a demo and a retail release, two games on one engine, or a
patched and unpatched binary.

**Three levels, in increasing order of what they survive:**

1. **Exact bytes / hashes.** Trivially fast, and breaks on any recompile. Useful only for *"is this the
   same build?"* — which is a question worth asking (see the build-identity rule in
   [06](06-debugging-methodology.md)).
2. **Structural / fuzzy similarity** — control-flow shape, call-graph position, constant sets. Survives
   minor recompiles and is the mainstream answer (BinDiff and Diaphora are the well-known
   implementations). **You already have this**: Ghidra ships function-similarity and bulk-hash tooling,
   exposed in this setup through the Ghidra MCP as `find_similar_functions`,
   `find_similar_functions_fuzzy`, `bulk_fuzzy_match`, `get_bulk_function_hashes` and `diff_functions`.
   It runs on Windows PE and on 32-bit, which the fleet is.
3. **Behavioural fingerprinting** — emulate the function with synthetic inputs and fingerprint its *side
   effects*, so the match survives different compilers and optimisation levels where bytes and even
   control-flow graphs diverge. ([fnprint](https://github.com/1rhino2/fnprint) is a current example of
   this approach; see the caveat below before reaching for it.)

**Start at level 2, because you already have it and it reads your actual files.** The reason to know
about level 3 is that it degrades differently, not that it is strictly better.

### It was measured, and it is a lead generator — not a name-transfer machine

Swat4-VR ran the calibration described above, on **the easiest case such a matcher will ever see**: two
builds of one game, one toolchain, symbols on both sides.

| | |
|---|---|
| rank-1 accuracy | **6/13 = 46%** |
| when it returned any candidate at all | 6/10 = 60% |
| returned nothing | **3/13 = 23%** |

That is an `INCONCLUSIVE` against their pre-registered rule, so the BioShock probe correctly did not
proceed. **A poor score on the easiest case transfers**: use this to check one function you already
suspect for another reason, not to bulk-transfer names.

**The prediction in this playbook was not supported.** This chapter predicted the matcher would do well
on meaty side-effecting seams and badly on tiny pure-compute helpers. Measured: serialisation/plumbing
went **2/2**, render and camera seams went **3/8** — the class the prediction cared about did *worse*.
The sample is far too small to call that a reversal, but it is not confirmation, and the prediction is
withdrawn rather than quietly left standing.

The maths-helper class turned out **unmeasurable, not unmeasured**: UE2 defines `FVector`/`FMatrix`
operators inline in headers, so they never reach an export table and there is no ground-truth name on
either side to score against.

### Three traps that each fake a "this tool is useless" result

Every one of these produces a near-zero score for reasons that have nothing to do with the matcher:

1. **Most exports are `jmp` thunks.** 6,057 of 7,682 in that binary. The export RVA is a **five-byte
   jump**, not the function body, and matching from it returns **0 hits at any threshold — including
   0.05**. Do it the obvious way (take exported names, feed their addresses in) and you score ~0% on
   four-fifths of your sample. **Resolve `E9 rel32` to the body first**; the resolved bodies paired at
   0.76. This is the same thunk trap named earlier in this chapter, wearing different clothes.
2. **Ghidra reports `analyzed: true` when it is not.** One imported binary showed `function_count: 874`
   against its twin's 33,700; `reanalyze` took it to 32,951. Matching against a near-empty program scores
   ~0 and looks exactly like matcher failure. **Compare `function_count` across the two programs before
   you match anything.**
3. **`score` is not confidence — read `total_matches` first.** A copy constructor with **1,007 candidates
   all scoring 1.0** missed; a function with **1 candidate at 0.63** hit. A perfect score shared with a
   thousand others carries no information. (Not a clean rule: three correct matches also had 674–740
   candidates. Treat a high tie count as a warning, not a verdict.)

One unresolved question worth settling before trusting any cross-*game* number: a possible
**address-proximity bias** — one match landed near the source address when the truth was further away. If
the implementation tiebreaks by address it is flattered by similarly-laid-out builds and would collapse
on unrelated binaries. A counter-example exists, so it is not established.

### The caveat that matters for game binaries

Behavioural matchers state their own weak spots, and they land awkwardly on this domain: **tiny
functions, pure compute, and logic sitting behind deep preconditions** all reduce accuracy. Engine code
is full of exactly those — vector normalise, matrix multiply, one-line accessors. The functions you most
want named (`cCamera::GetFrustum`, `FPlayerSceneNode`, a projection setter) are usually meatier and
side-effecting, so they fare better; the maths helpers appendix [A1](a1-rotation-and-frames.md) cares
about are the weakest case.

**And check the binary format before spending an afternoon.** A matcher that only reads x86-64 ELF cannot
open a single target in this playbook — every one of them is a **Windows PE**, and four of seven are
**32-bit x86**. That is not a criticism of any particular tool, it is a reminder that "does it parse my
file at all" is the first question, not the last. (*fnprint is x86-64 ELF only at the time of writing,
which rules it out for this fleet today regardless of how well it matches.*)

### How you would actually use a match

A pairing is a **lead, not a fact** — the whole of this chapter applies to it. Treat a matched name as a
rung-3 borrowing: it gives you vocabulary and a place to look, and it must still be confirmed against the
shipping binary before it goes in `ADDRESS_REGISTRY.md`. A high-confidence match onto a function whose
behaviour you have not observed is exactly the "helpful name is a hypothesis, not evidence" trap named
elsewhere in this chapter.

Two practical notes if you try the SWAT4 → BioShock case:

- **Match within the layer that actually shares lineage.** Both are Vengeance/UE2.5 *engine* code; the
  game-specific classes (`ASwatPawn`, BioShock's plasmid systems) share nothing and will produce noise.
- **The two SWAT executables are themselves a matching problem.** `Swat4.exe` (UE2.0 b2226) and
  `Swat4X.exe` (UE2.5 b2500) are different links of one codebase — which makes them a *free* calibration
  set. Run the matcher on a pair whose answer you can check with symbols on both sides before trusting it
  on a pair where you cannot.

## Rung 1c — an override pointer the engine already honours

Before you hook a matrix write, look for a **nullable override the engine reads on its own**. Debug
cameras, cutscene rigs, photo modes and replay systems all need one, so a mature engine usually has it —
and setting a pointer is far more robust than intercepting a computation.

(*AnvilNext 2.0, inside `UpdateCameraMatricesAndFrustum`:*)

```c
v24 = *(Matrix4x4 **)(pCamera + 576);   // worldMatrixOverride
if ( v24 )
  *pOutViewMatrix = *v24;               // the engine adopts YOUR view matrix
```

Write a matrix, point the field at it, and the engine's own code uses it — **before** it builds the
view-projection and the frustum planes, so culling follows automatically. That is most of what
[17](17-teardown-fc2vr-native-stereo.md) works hard to achieve, handed over for free.

**How to find one:** in the function that assembles the view matrix, look for an early
`if (ptr) { *out = *ptr; }` guarded by a pointer read from the camera object — an unconditional-looking
matrix builder with one nullable escape near the top. Then confirm nothing else writes that field during
normal play, or you are fighting the engine for it every frame.

## SIMD density narrows the search before any string does

On a modern 64-bit engine, camera and matrix code is dense in `__m128` / `_mm_*` intrinsics —
`_mm_shuffle_ps`, `_mm_dp_ps`, `_mm_unpacklo_ps` in tight runs. **Searching for that shape is a cheap
first filter** when you have no string anchor, and it works on stripped binaries where names give you
nothing.

Treat it as a *shape* heuristic rather than a byte pattern: you are looking for regions of high SIMD
density with float constants nearby, then reading them to see which is a projection build. It narrows
megabytes to a handful of candidates in minutes.

## Disambiguate a shared callee by its return address

When one function is called from several sites and you need to behave differently per site, you do not
need a separate hook per call site — **read the return address and switch on it**:

```cpp
constexpr int caller_kind(uintptr_t return_rva) {
    switch (return_rva) {
    case 0x01E0AB0F: return 0;
    case 0x01E0ADDC: return 1;
    default:         return -1;   // unknown caller: fall through to stock behaviour
    }
}
```

(*Witcher 3 VR uses exactly this to give two shadow-cascade call sites different per-eye authority.*)

Two properties make it safe. **The `-1` default is mandatory** — an unrecognised caller must get stock
behaviour, not an arbitrary branch, because a patch or a different build will introduce call sites you
have never seen. And **the RVAs belong in your version-guard**: they are as build-specific as any other
address, so they need the same fail-closed validation as everything else in this chapter.

## Your search is an instrument. Calibrate it before you trust a result — especially a negative one

**Three projects here hit this in the same week, in three different forms.** It is the single most
reliable way to produce a confident wrong answer during discovery, and the defence is the same in all
three cases.

**Form 1 — the substring census inflates.** Counting names that *contain* a token is not counting the
thing the token names.

> Swat4-VR's first pass reported **148 "TAA" exports in a 2005 engine** — a startling result. Every one
> was `intAActorexec…`, matching on `in`**`tAA`**`ctor`.

**Form 2 — a broad term floods a capped result set and manufactures a false negative.**

> DishonoredVR concluded the game had no stereo remnants, having searched `eye` — which matched
> animation bones (`eye_L_jnt`, `EyeControl_Left`, `UpdateEyeHeight`) and flooded a length-limited
> result set. **Dishonored does ship NVIDIA 3D Vision.**

**Form 3 — the attribution is unsound even when the matching is fine.**

> PreyVR's call-site sweep was correct, but bucketing each site to a function by scanning back to `CC CC`
> padding was not — MSVC does not always pad boundaries, and a known call site came back missing.

### The single defence: put a known answer in the input

**Search first for something you are certain is there. If the control does not come back, the search is
not measuring what you think it is.** That one habit catches all three forms:

- A capped result set reveals itself when your known item is missing from it.
- A bad matcher reveals itself when your known item does not match.
- A bad attributor reveals itself when your known item lands in the wrong bucket — which is exactly how
  PreyVR caught theirs.

Three supporting habits, cheap:

- **Anchor the match** — word boundary, known prefix, or a demangled-name field, never a raw substring.
- **Print ten matches before believing a count.** A surprising number is far more often a broken query
  than a discovery.
- **Say what the search was over.** Swat4-VR's UE2.5 hazard census concluded no TAA, no history buffer,
  no velocity buffer — and tagged it as an **export-table** census, which proves absence of *names*, not
  of functionality. Inlined and non-exported implementations are invisible to it. That caveat is what
  makes the result usable rather than merely encouraging.

**A negative result is a claim, and it needs a control like any other.** "I looked and found nothing" and
"I looked, my instrument was working, and found nothing" are different statements, and only the second
one retires a question.

## Publishing decompiled pseudocode is a legitimate porting artifact

When moving a mod between two builds of the same engine, the highest-value thing you can write down may
be **the decompiled body of each target function**, verbatim.

(*`anvilengine2vr`'s Assassin's Creed Origins porting guide ships full IDA output for
`CalculatePerspectiveProjectionMatrix`, `UpdateCameraMatricesAndFrustum` and `CameraNode::GetForward`,
explicitly so a reader can visually match a similar function in the sibling binary — "the variable names
and addresses will differ, but the structure and SIMD operations should be recognizable."*)

Set that against the measurement earlier in this chapter: automated cross-binary matching scored **46%
rank-1 on the easiest case it will ever see**. A human — or an agent — reading two pseudocode listings
side by side is not obviously worse, and the listing keeps working after the tool changes, the database
is lost, or the analysis is redone from scratch. **Commit the pseudocode next to the offsets.**

Their porting rule of thumb is worth carrying with it: within one engine family, *functions* port and
**field offsets drift**. Verify every struct member even when the byte signature matched first try.

## Classify an unknown value by its magnitude, not its declared type

When you are reading out-params or struct fields you have not yet typed, **the bit pattern lies**. The
canonical trap: a rotation stored as three **int32s** (Unreal's `FRotator`, 65536 units per turn)
reinterpreted as floats reads as three *denormals* — it prints `(0.000, 0.000, 0.000)` and looks like an
empty/unwritten slot. (*That cost one project a whole session chasing a "missing" direction that was
right there.*)

Their shipped fix is a good general habit: tag each slot by **magnitude class** and log the tag —
small int32s ⇒ rotator, unit-length floats ⇒ direction vector, values in the thousands ⇒ world position.
A related trap on the data side: an integer config property (`HorizontalFOV=130`, no decimal point) is
**invisible to a float scan** — sweep both `f32` and `u32` when you don't know the type.

The habit is cheap to make mechanical. **Print every interpretation at once and let the reading that
makes sense win** — this is strictly better than picking a type up front and being quietly wrong:

```c
/* Dump an unknown 32-bit slot every way simultaneously. One line per word,
   annotated with which readings are plausible. Costs nothing, ends arguments. */
void probe_word(const void *p, const char *label)
{
    uint32_t u; memcpy(&u, p, 4);
    float    f; memcpy(&f, p, 4);
    int32_t  i = (int32_t)u;

    char tag[160]; tag[0] = 0;
    int  exp    = (int)((u >> 23) & 0xFF);
    bool denorm = (exp == 0 && (u & 0x7FFFFF) != 0);

    /* An FRotator component read as float lands here -- and prints as 0.000. */
    if (denorm)                        strcat(tag, "[DENORMAL: int-as-float? FRotator?] ");
    else if (exp == 0xFF)              strcat(tag, "[NaN/Inf: not a float] ");
    else if (fabsf(f) <= 1.0001f
             && fabsf(f) >= 1e-4f)     strcat(tag, "[unit-ish: quat/dot/axis/param] ");
    else if (fabsf(f) > 1.f
             && fabsf(f) < 200.f)      strcat(tag, "[degrees/FOV/scale?] ");
    else if (fabsf(f) >= 200.f
             && fabsf(f) < 1e6f)       strcat(tag, "[world position?] ");

    if (i > -65536 && i < 65536 && i != 0) strcat(tag, "[small int: rotator unit/index/count] ");
    if (u >= 0x00010000 && u < 0x7FFF0000)  strcat(tag, "[plausible 32-bit pointer] ");
    if (u == 0)                             strcat(tag, "[zero: unwritten, or genuinely zero] ");

    log_line("%-24s hex %08X  i32 %11d  f32 %14.6g  %s", label, u, i, f, tag);
}
```

Two readings of the same word are the *normal* case, not a failure — `[small int]` and `[DENORMAL]`
together is the FRotator signature, and `[plausible 32-bit pointer]` plus `[world position?]` is the
ambiguity that dereferencing settles in one step. **The trap is only ever a slot printed one way.**

And sweep both types when scanning for a known value. An integer-valued config property is invisible to
a float scan and vice versa:

```text
HorizontalFOV=130   ->  f32 scan for 130.0f   finds 0x43020000
                    ->  u32 scan for 130      finds 0x00000082   <- the shipped one
```

**A pointer read as a float is the version of this that survives longest.** It comes out either
NaN-adjacent and obviously wrong, or — worse — coincidentally reasonable, at which point you build months
of work on a misread layout. (*SOMAVR originally read a "closest entity" result struct with a pointer's
raw bits treated as a distance. The real layout was distance at `+0x18`, physics body pointer at `+0x20`,
entity pointer at `+0x28`; reticle depth, semantic focus and selected-body identity all worked
immediately once the actual fields were consumed.*) Test each candidate field for *plausibility given its
assumed type* — finite, in range, not pointer-shaped — before designing on the layout.

**And never gate a mutation on one cheap identity signal.** Allocation sizes, index counts and buffer
byte-widths are attractive because they are free to read, and ambiguous because padding, pooling and
compiler layout make them collide. (*BioshockVR had reflected+runtime cbuffer sizes of 576/832 bytes match
both the viewmodel lane **and** unrelated world draws; a confirmed hand/forearm index count of `26178`
failed to recur in a later build that still had the right cbuffer sizes; and a 36-index signature used to
identify a shadow-mask producer recurred on many unrelated draws.*) The redesign that worked required a
**joint key** — shader identity *and* resource identity *and* pass position *and* content — before any
replay was authorised. Cheap signals are fine for *finding* a candidate; they are not sufficient for
*acting* on one.

## A dynamically-loaded dependency is invisible to the import table

If an engine loads its graphics API at runtime rather than linking it, `D3D11CreateDevice` and the DXGI
entry points **do not appear in the import table at all**, and an import-based search returns a confident
false negative.

Find it in `.rdata` instead: a `LoadLibrary`/`GetProcAddress` loader has to store the literal names it
resolves, and they sit together. (*PreyVR's `PreyDll.dll` imports none of them; the dependency was a
contiguous ASCII cluster — `CreateDXGIFactory1`, `dxgi.dll`, `D3D11CreateDevice`, `d3d11.dll` — at a known
`.rdata` offset. Once analysis completed, xrefs to `CreateDXGIFactory1` resolved to exactly **two** code
sites, one of which decompiled as the real device/adapter/swapchain creator.*)

This is the string-cluster form of the data-signature idea below, and it applies to any dynamically-loaded
dependency, not just graphics.

**A cheap structural fingerprint for the objects you then find: count the vtable entries.** With RTTI
stripped — common, and Arkane stripped it here — entry count discriminates COM/virtual-dispatch types
before any decompilation. (*PreyVR's leading candidate for a per-eye render-view was a 2-entry ring whose
entries shared one `d3d11.dll` vtable with exactly **11** contiguous entries — matching `ID3D11Query`'s
shape, not `ID3D11DeviceContext`'s ~145. Candidate closed as GPU timing queries; the search redirected to
the real view block, eventually found by scanning for an orthonormal 3×3 rotation followed by a plausible
world position.*)

## Signature-scan the data, not just the code

Not everything worth finding is an instruction. Layout, tuning and behaviour are often **authored data**
the engine loads into a read-write heap — which means no module-relative RVA will ever point at it, and
a code-only scanner will never see it.

Scan for a **data** signature instead: an immutable prefix of known constants adjacent to the values you
want. (*HaloVR locates Halo's HUD layout floats by a 24-byte prefix of known canvas/sensor constants,
with the two "global safe frame" values at `+24/+28`.*) Three disciplines make this safe:

- **Expect an exact population.** Know how many blocks should exist (HaloVR expects exactly three, one
  per HUD skin) and confirm you found all of them with bit-exact payloads. A different count means your
  signature is wrong, not that the game varies.
- **Require the payload to be plausible, not just the prefix to match.** A hit counts only when the
  prefix *and* the surrounding values look like the structure you think it is.
- **Re-validate on every write.** The heap moves between loads and levels; a pointer cached at startup
  can go stale and land somewhere unrelated. Re-check the prefix each time before writing, and reject
  the slot rather than corrupting it.

Data signatures are also how you find things the developer never exposed to code you can hook — and they
often let you change behaviour by writing a float instead of detouring a renderer
([04](04-ui-and-hud.md)).

## Two more ephemeral-value hazards, and an annotation one

The chapter already insists on recording a module base alongside every RVA. Two other values look stable
and are not:

- **A GPU adapter LUID is a per-boot handle, not a machine identifier.** (*The same physical card reported
  `00000000-0001667A` on one day and `00000000-00016A92` six days later — different value, same hardware,
  after a reboot/driver restart.*) Any adapter-matching code across D3D9/11/12, DXGI or OpenXR must read
  **both** values within the same boot. A LUID copied into config or pasted out of a document produces a
  hard mismatch on a single-GPU machine that reads exactly like a real adapter fault.
- **Your disassembler's annotations do not necessarily survive its own re-analysis — and the loss is
  *structured*, not random.** (*A full auto-analysis pass over 86,434 functions reverted the previous day's
  renames on one function pair while all 24 other annotations survived. PreyVR's follow-up identified the
  pattern by direct testing: **names are the thing that gets lost, and end-of-line comments survive.**
  What is *not* established is the fate of plate comments — the renderer pair's originals were overwritten
  before anyone could check them, so that case is genuinely open.*) The safe instruction is therefore
  narrow: **re-verify anything you renamed**, and do not assume a companion comment protected it until you
  have tested that on your own database. Partial silent loss is worse than total loss, because the
  surviving majority makes the database look intact — and a rename is exactly the kind of annotation you
  would never think to re-check.

## Differential state scanning: capture the same process in known states

When you need "which byte means *paused* / *scoped* / *dead*," don't reason about it — **capture the
process in alternating known states and intersect the candidates.** Snapshot state A, state B, state A,
state B; keep only addresses that changed *every* time in the right direction. It's the memory-scanning
technique from Cheat Engine, formalised into a repeatable script.

- *HaloVR:* four read-only module snapshots (paused, unpaused, paused, unpaused) narrowed the pause flag
  to a handful of repeated candidates; a 2 ms timing trace then identified the one that changed **before**
  the host's generic suspension flags on both entry and exit — i.e. the *owner*, not a downstream copy.
  Ordering in time is what separates cause from effect when several bytes all change.
- **Beware the named decoy.** The editing kit exposed a boolean literally called `game_paused`, and live
  testing proved it stays zero — it's a developer override, not the shipping pause state. A helpful name
  is a hypothesis, not evidence (the same trap as SS2VR's `eCreatureJoint` "R/L" enum in
  [06](06-debugging-methodology.md)).

**The state that most often settles a "two of the same thing" question is standing perfectly still.** When
a candidate structure holds a *pair* — two cameras, two views, two buffers — the tempting read is "that's
stereo." The stationary, no-input state is the cheapest state that forces the competing hypotheses to
predict different observations. (*PreyVR found two candidate camera slots in a per-frame view block and
read them at rest: **byte-identical, separation `0.00000`**. A genuine left/right pair must differ by a
constant lateral IPD offset *at all times*, including at rest — so identical-at-rest slots can only be
frame double-buffers. That closed the question outright instead of leaving it a probability.*) Generalise
the shape: for any paired candidate, find the state in which the two hypotheses disagree, and go there
first.

Ship the *signature*, not the address you found this way: HaloVR's production code resolves the flag
through a unique 45-byte owner signature that recovers the RIP-relative write target and additionally
requires the value to look boolean — and disables the whole lane, falling back to a controller-edge
heuristic, on anything missing, ambiguous, out-of-module or non-boolean.

## Seed the scan from what the *consumer* consumed, not from what an API reports

A value scan is only as good as its seed, and the most convenient seed is usually the worst one. When a
target hands you a scripting API that reports the quantity you want — a camera position, a player
transform — the obvious move is to read it and scan for it. **Do that second.** If the value also reaches
the GPU, the constant buffer the driver actually consumed is a strictly better seed, and the difference is
not marginal.

**Measured on Sims 4 (2026-08-25).** The game ships a Python `camera` module exposing
`camera._camera_position`. Seeding an exact float32 scan from it, on a stationary camera, across 3.96 GB
of committed memory, returned **exactly one match** — a textbook-clean unique hit.

**It was garbage.** Commanding the camera to move proved the address never changed. `_camera_position` is
*reassigned* rather than mutated, so the superseded value is left behind in the interpreter's heap; and
because it is refreshed sparsely (**once** in a four-second window with the camera moving) the live engine
copies had already moved on. **The only exact match for the just-read value was a dead object.** Scanning
for a value the camera genuinely held instead returned **126–129 hits**.

So the API seed produced, in sequence: a false unique (which invites confidence), then unusable ambiguity.

### The constant-buffer seed, and why it is better

Reading the same camera out of the vertex shader's constant buffer in a frame capture gave a
**unit-length basis vector** that changed as the camera moved. Four properties, none of which the API
value has:

1. **It is what the renderer used.** Provenance is exact — there is no mirror, no staleness window, and no
   question of whether some other copy is authoritative.
2. **It is self-validating.** `|v| = 1.0` is a free checksum on every candidate. A basis row that is not
   unit length is not the one you want, and you learn that without a second observation.
3. **It is high-entropy.** Three unconstrained floats, versus a position whose components are often round
   or shared with nearby objects.
4. **It moves continuously.** Orientation changes on almost every frame of ordinary play, so the
   differential filter below has something to bite on immediately.

### The procedure

```text
1. Capture a frame. Find a world-geometry draw.
2. Dump the vertex-stage cbuffer as RAW BYTES (see ch06 - the reflection path may return zeros).
3. Identify the view basis: in a world-view-projection, the w-row's xyz is a unit-length
   direction. Confirm |v| = 1 before going further.
4. Scan process memory for that float triple.
5. Move the camera to >=3 known, distinct orientations, filtering candidates that fail to follow.
6. Count the survivors. More than one is a finding, not a tie to break.
```

**Step 5 is not optional, and step 4 alone is actively misleading.** Uniqueness measured on a *stationary*
subject is evidence of **staleness**, not correctness — the dead copies are the ones nothing else is
writing, so they are the ones that look cleanest. Never count candidates until they have survived motion.

### When this applies

Any target where a weak seed and a strong seed both exist:

- A script or console API that reports a value, versus a shader constant that receives it.
- A getter that returns a *copy* — the copy's address is not the field's address.
- A value written to a log or debug overlay, which is invariably a formatted snapshot.
- Any engine that double-buffers or interpolates its camera; the API commonly exposes the settled value
  while the renderer consumes the current one.

**The general form: prefer the observation closest to the consumer.** An API is a *report about* state; a
constant buffer is state that was *used*. When the two disagree, the consumer is right, and when they
agree you have two independent methods — which ch11 asks for anyway.

**It also inverts a common assumption about capture tooling.** A frame capture is usually treated as a
graphics-debugging instrument. Here it is a *memory-discovery* instrument: the capture supplies the seed
that makes the CPU-side scan tractable. If you have a working capture path and an intractable scan, look
at what the GPU received before you write another heuristic.


## A counter-example worth seeing: the flat offset table

Everything in this chapter argues for discovery over hardcoding. Here is what the alternative looks
like in a shipped mod, so the trade is concrete rather than theoretical.

BF2VR's entire anchor set is one header of absolute virtual addresses:

```cpp
static const DWORD64 OFFSETGAMECONTEXT        = 0x143DD7948;
static const DWORD64 OFFSETWORLDRENDERSETTINGS = 0x143D7B068;
static const DWORD64 OFFSETCAMERA             = 0x146FD3E90;
static const DWORD64 OFFSETBUILDVIEWS         = 0x147c4e1a4;   // a mid-function instruction
static const DWORD64 OFFSETUIDRAW             = 0x140e23e28;   // "the instruction after a call to..."
```

No signatures, no string anchors, no validation — and several entries are *mid-function instruction
addresses*, which are more fragile still ([rung 4c](#rung-4c-hook-an-instruction-where-the-object-is-already-in-a-register)).
On a live-service EA title this breaks on every patch.

**And it is not obviously the wrong call for that project.** The mod is version-locked by intent, the
author ships a Ghidra script to re-derive the table
([rung 4b](#rung-4b-a-naming-convention-in-the-string-table-can-enumerate-a-whole-type-system)), and the
alternative — signature-scanning eight mid-function instructions — is genuinely hard. The honest reading
is that they moved the cost from *every run* to *every patch*, deliberately.

**The lesson is the tooling, not the table.** A hardcoded offset set is survivable exactly as long as
re-deriving it is cheap and scripted. If you choose this route, **write the re-derivation script first**
— and note that it is the thing you must keep working, not the numbers.

## Version robustness

Assume you will meet a build you've never seen.

- **Fingerprint the engine generation from codegen, not a version string.** (*UEVR detects UE5 by the
  presence of double-precision `xmm` instructions — a consequence of the float→double transition — and
  detects older UE builds by virtual-table layout, e.g. missing virtuals or runs of functions that just
  return nullptr.*)
- **Relative-offset assumptions are pragmatic but must fail closed.** (*UEVR locates `ViewExtensions` by
  assuming it sits a fixed distance from `StereoRenderingDevice` — an assumption that has held for years
  of Unreal development.*) That's a legitimate shortcut; just validate the result and disable the lane on
  mismatch rather than writing to a guessed address.

The shape that makes all of this survivable is **one resolver per target, each carrying its own
validator, resolved once at startup, with every failure reported before anything installs**. Resolving
lazily at the call site is what produces "the mod works except one feature, silently":

```c
typedef struct {
    const char *name;
    void      *(*resolve)(const module_t *m);   /* string xref, export, table, pattern */
    bool       (*validate)(void *p);            /* MUST be independent of resolve()    */
    void      **slot;
    bool        required;                       /* false => feature disables, mod runs */
} anchor_t;

bool resolve_all(const module_t *m, anchor_t *a, size_t n)
{
    size_t ok = 0, failed_required = 0;

    for (size_t i = 0; i < n; ++i) {
        void *p = a[i].resolve(m);

        if (!p) {
            log_error("anchor %-28s UNRESOLVED", a[i].name);
        } else if (!a[i].validate(p)) {
            log_error("anchor %-28s resolved +0x%zX but FAILED VALIDATION",
                      a[i].name, (size_t)((uint8_t *)p - m->base));
            p = NULL;
        } else {
            log_info("anchor %-28s +0x%zX  ok", a[i].name, (size_t)((uint8_t *)p - m->base));
            ++ok;
        }

        *a[i].slot = p;
        if (!p && a[i].required) ++failed_required;
    }

    /* Report the whole picture, THEN decide. Aborting on the first failure hides
       the other nine, and you get one bug report per build instead of one total. */
    log_info("anchors: %zu/%zu resolved, %zu required missing", ok, n, failed_required);
    return failed_required == 0;
}
```

Three properties earn their keep. **`validate` must not reuse `resolve`'s evidence** — a prologue check
on an address found by prologue scan proves nothing (see *Validate a discovery by provenance* above).
**`required` splits fatal from degraded**, so a patch that moves one optional anchor costs a feature
rather than the mod. And **the run reports every anchor before returning**, because the expensive version
of this is discovering failures one build at a time.
- **PDB dumps are not the shipped code.** Compiler optimizations, obfuscation, and build differences mean
  a public PDB can disagree with the binary in your hands. Analyze the binary you actually inject into.
  (This is the same rule as "the open-source ancestor gives vocabulary, not truth.")
- **An RVA in your notes is evidence for one build; the signature in your source is the authority.**
  Write the distinction into the documents themselves so nobody later mistakes a recorded address for a
  shipping one. (*HaloVR's RE notes open by naming the exact build the RVAs came from and close with
  "never treat an RVA in this document as a shipping address," and its project rules forbid shipping a
  guessed hardcoded address outright.*) Record RVAs freely — they're how you re-find things — but resolve
  them at runtime.
- **Verify uniqueness before you trust a signature.** Zero matches and *multiple* matches are both
  failures, and both must disable the lane rather than take the first hit. This is cheap to automate: a
  20-line script that scans the shipped binary and asserts a pattern occurs exactly once will catch a
  bad signature before it ever reaches a headset.

## The engine's own debug commands are a validation oracle

Both a shipped console command and a hidden developer command can prove a discovery *before* you write
code against it — and they're the cheapest test you will ever run.

- *Source 2:* `schema_list_bindings`, `schema_dump_binding`, and `schema_detailed_class_layout` validated
  the reconstructed schema live.
- *SS2VR:* the remaster's own debug `teleport` command exercises the exact native relocation primitive the
  VR teleport feature needs — so `teleport $10,0,0` validated the whole feature end-to-end before a line
  of mod code existed ([03](03-input-and-locomotion.md)).

Hunt the command table early. A verb that already does the thing you want is both a proof and a
supported entry point ([03](03-input-and-locomotion.md)).

## If the engine has its own stereo path, use it

The single biggest architectural lesson from UEVR: rather than replaying the world twice from outside,
it drives Unreal's **built-in** stereo rendering — the `-emulatestereo` mechanism and the
`FFakeStereoRendering : IStereoRendering` class, whose virtuals already exist to override projection and
view matrices. Using the engine's native stereo pipeline is both more correct and inherently faster than
an external double-render.

This is [lesson 8](README.md) in its strongest form. Before committing to private per-eye replay
([09](09-d3d11-openxr-injection.md)), check whether the engine has a latent stereo/multi-view path
(split-screen, mirror/portal cameras, a cvar-gated second view) you can drive instead. None of SS2VR,
BioshockVR, or SOMAVR had a usable one — which is *why* all three ended up replaying draws — but the check
is cheap and the payoff is large.

Two attached warnings from UEVR's experience:

- Turning on a dormant engine path can trip **asserts the engine only raises in development builds** —
  UEVR must wrap the call that creates the second eye's view state in a vectored exception handler and
  pre-emptively patch out the asserting instructions, because the engine asserts if a view state already
  exists for an eye. Expect a dormant path to be under-tested.
- Engine-native UI usually needs its own redirection. UEVR hijacks the UI render target with mid-hooks
  placed immediately before and after the texture-creation call, hooks the viewport-presentation method to
  place UI in world space, and forces UI to a separate target via the engine's own
  `Slate.DrawToVRRenderTarget` cvar. The generalizable move: **find the engine's existing "render UI to a
  target" switch rather than intercepting individual UI draws** ([04](04-ui-and-hud.md)).

## Reading a stereoscopic fix properly: what the known-issues list tells you {#stereo-fix-prior-art}

This chapter already recommends 3D Vision / HelixMod / 3Dmigoto packages as prior art. A research pass on
Prince of Persia (2008) shows how much more is in one than the shader constants. `[SOURCE]`

That game has two HelixMod fixes four years apart, and **the second one existing is itself evidence**:
it was built specifically to repair collateral damage from the first, whose skybox and lens-flare fixes
had also broken unrelated combat-effect shaders. The newer HelixMod could distinguish shader/texture
**pairs** rather than blanket-matching. **A twice-iterated fix tells you the first attempt's matching was
too blunt for this binary** - which is a warning about your own draw classifier, on this exact game.

**Their known-issues list is a starter pass inventory.** Incorrect skybox depth, doubled lens/sun-flare
imagery at the wrong depth, UI rendered flat at screen depth - somebody already enumerated which passes
misbehave in stereo, before you have written a line.

Two specifics from the 2016 update that would each cost a session to discover:

- **Separate convergence presets for cutscenes versus exploration gameplay.** That is direct evidence the
  camera and projection setup **differs between cinematic and gameplay modes**. Scope your camera
  investigation for two paths rather than assuming one.
- **Skybox depth correction for both dark and sunny weather variants.** The skybox is not a single static
  case; there are at least two distinct sky-rendering states to classify.

**And read the research discipline as well as the findings.** The same sweep's DRM note refuses to
overclaim - *"treat this as likely StarForce present, not confirmed"* - and names how to settle it
(the project's own static binary recon). It also flags an honest gap rather than padding: no vorpX
precedent found for this title, unlike two sibling projects. A prior-art sweep that reports only hits is
not a survey.

One non-obvious fact from it worth carrying: **the DRM profile can differ per distribution channel.**
Prince of Persia's 2008 retail boxed release was deliberately shipped DRM-free - a widely covered
decision at the time - while the digital versions were not part of that move. *Which copy the user owns*
can decide whether you are facing a protected executable at all.

## A write that reads back correctly and changes nothing found a derived output {#derived-output}

Psychonauts VR spent several sessions on the wrong matrix, and the way they eliminated candidates is
reusable on any camera struct. `[SOURCE]`

The camera object carries four plausible 4x4s. Three of them - at `+0x20`, `+0x50` and `+0x90` - accept a
write, hold it, and read back unchanged at end of frame **with the picture completely unaffected**. Their
conclusion: *"all three matrices are derived outputs nothing reads."* The real input was a fourth at
`+0x150`, and culling followed it.

**A write that survives the frame and changes nothing is not a failed write - it is a successful write to
the wrong field.** That is a *positive* result and it eliminates a candidate cheaply. The trap is reading
it as "my hook is not landing" and going to look at timing, which is exactly what happened here:

> **"It's a timing problem, land the write inside `CandB`"** - wrong. Probing at
> BeforeEye1/BeforeEye2/AfterBoth showed the write surviving the whole frame. **Wrong field, not wrong
> timing.**

And the reason the earlier evidence had pointed at timing is worth its own line: **the dump was taken
before the write in both the yaw-0 and yaw-90 runs, so it showed the engine's value either way.** An
instrument sampling on the wrong side of the thing it is measuring returns a result that looks like data.

### Three things that all had to be right, and the signature of each being wrong

Once the field was correct, three separate errors each had a distinct fingerprint:

- **Write absolute from a snapshot, never incrementally.** *While the camera is stationary the engine does
  not rewrite this matrix*, so rotating it in place each frame compounds - a 15-degree hold became a spin,
  with `c0.z` drifting `0.5160` to `0.1235` in 1.5 s. This is the
  [pristine-latch rule](a2-pose-pipeline.md) with a number attached: if the engine does not refresh a
  field, your own previous output is the input you are reading.
- **Rotate every column, including the ones you do not understand.** `c2`/`c3` were a matched pair
  (forward and forward-previous); divergence broke it.
- **The translation row must follow the rotation.** Leaving it on the old axes produces an error that
  **grows with angle** - clean at 2-5 degrees, sheared by 8-10, wrecked at 15+. **An error that scales
  with the magnitude of your change means a term you did not transform**, and a test at small angles will
  pass.

Two details on the matrix itself. Row 3 was `dot(O, c_i)` with `O = -camera position`, **recovered by
solving the system rather than assumed** - worth the extra hour, because an assumed convention that
happens to work at small angles is the previous bullet waiting to happen. And the columns are **not
unit**: `c0` scaled 1.538, `c1` scaled 2.052, with `|c1|/|c0| = 1.334` - the 4:3 aspect. **A matrix that
looks like a basis may carry projection scaling**, so an orthonormality assertion on it will fail
correctly and tell you nothing.

## If the engine has a property system, stop scanning for offsets and query it {#reflection-walk}

The single highest-leverage discovery on a reflective engine, and it retires a whole category of work.
`[SOURCE]`

> UE3 stores every property's byte offset in the object model, so offsets never have to be scanned for
> again.

Singularity's mod walks it directly. On UE3, with the class object in hand:

| Field | Offset | Role |
|---|---|---|
| `UStruct::Children` | `+0x4C` | head of the property linked list on a `UClass` |
| `UField::Next` | `+0x40` | next property (`SuperField` sits immediately before, at `+0x3C`) |
| `UProperty::Offset` | `+0x64` | the property's byte offset within an instance |

Walk `Children`, follow `Next`, compare the `FName` index at `prop + 0x2C` against the name you want,
then read `prop + 0x64`. Climb `SuperField` for inherited properties - `Engine.Pawn`'s `Health` turned up
at **super-chain depth 10**.

**You find this metadata once and then every property in the game is addressable by name**, across
patches and across builds, with no per-field signature scan. Unreal is the obvious case; anything with a
runtime type system - Frostbite's reflection, Unity's managed metadata, a scripting layer's symbol table
- is worth the same question before you scan for a single field.

### Two validation moves that turn a fit into a discovery

The layout above was not guessed, and how they established it is more transferable than the numbers.

**Solve against answers you already have.** *"The only candidate accepted was the one that reproduced
`Actor.Location = +0x0054` **and** `Actor.Rotation = +0x0060`."* Two known answers, not one - a single
target admits coincidences.

**Then check it against a constraint you did not use.** `SkeletalMeshComponent` came out as
`Translation +0x190` → `Rotation +0x19C` → `Scale +0x1A8` → `Scale3D +0x1AC` - spacings of +12, +12 and
+4, which is **UE3's declared field order at exactly its declared sizes** (`FVector`, `FRotator`,
`float`). Nothing in the solve asked for that. **A constraint held that was never fitted is evidence; a
constraint you optimised against is only consistency**, and the distinction is the whole difference
between a layout you can build on and one that will fail on the next class you try.

## The same symptom has two causes: derived output, or cached consumer {#silent-write-two-causes}

[The section above](#derived-output) says a write that survives the frame and changes nothing has found
a derived output you can cross off. **That is only half the rule, and taking it alone will make you
discard the right field.** Singularity VR hit the other half. `[SOURCE]`

They wrote `SkeletalMeshComponent.Translation` (`+0x190`) with +50 UU on Z, on all three live meshes,
and read back the derived world transform: **it moved by `+0.0` UU in every case.** Identical symptom -
and the opposite diagnosis. *"The input holds our value; UE3 does not recompose `LocalToWorld` from it
without a reattach."* The field **is** the input. The consumer caches, and nothing marked the cache
dirty.

| Symptom | Cause | What to do |
|---|---|---|
| Write survives, nothing changes, and the value is genuinely read elsewhere | **derived output** | cross the field off, keep hunting |
| Write survives, nothing changes, and a cached transform is recomposed only on invalidation | **stale cache** | find the dirty flag or reattach path |

**The discriminator is whether the engine has a transform-caching concept for that object type at all.**
UE3 does - `BeginDeferredReattach` / `ConditionalUpdateTransform` - so a silent write on a component
transform means the flag, not the field. An engine with no such concept leaves only the first
explanation. Ask that question before you cross anything off, because the two conclusions send you in
opposite directions.

Their own verdict on the cost is worth recording: driving the first-person weapon through the object
model *"is a materially harder problem than anything else attempted here"*, so **the render-matrix
transform remained the only mechanism that moved the gun.** A field being writable does not make it the
cheap route.

## Authority is per field, not per struct {#field-level-authority}

The corollary, from the same project, and it is the reason read-only evidence is not enough. `[SOURCE]`

One struct, two members, opposite verdicts:

- **`mCurrentPOV.FOV`** - writing it works. The rendered view visibly widens 65 to 110 degrees. **This
  member is read.**
- **`mCurrentPOV.Rotation`** - writing it does nothing to the view, *"despite the write persisting
  perfectly (`survived=120 clobbered=0` every sample, yaw cycling exactly as written). The engine
  neither fights the write nor reads it."*

A snapshot-look-around-diff hunt found the real source: the standard `AActor` layout on both the camera
and the controller - `Location` at `+0x0054`, `Rotation` at `+0x0060` - with that one pair then
**mirrored into four downstream copies** (`+0x0328`, `+0x0350`, `mCurrentPOV +0x0420`,
`mDesiredPOV +0x0458`). The POV structs are written *by* the camera update and read only for FOV.

> **A struct containing a rotator is not necessarily *the* rotation. Verify by writing, not by reading -
> the read-only evidence pointed confidently at the wrong field.**

**Test every member you intend to drive, separately.** A struct that responds to one write is proven
reachable and proven read, which makes a *non*-responding sibling member look like a bug in your hook
rather than what it is. And when you find a value mirrored into several structs, the one you want is the
one furthest upstream - here, two levels above the four copies.

## Derive each tolerance from what it is absorbing {#per-probe-tolerance}

A flat tolerance across a scan is a third way to get a confident wrong answer. Singularity's matrix scan
let three spurious windows through at `w` around `-10.5` (4 uploads each) beside the real matrix at
`w = -0.0020` (50 uploads); their 3-register spacing suggests a block of `float3x4` transforms that the
sliding 4-register window straddles. `[SOURCE]`

The fix comes from asking what the tolerance is *for*. It exists to absorb the one-frame staleness of
the camera position being substituted - **which applies to the world-position probes and not to the
origin probe**, where the test reduces to "is `r[3].w` near zero": pure matrix content, no camera
reading, nothing to go stale. So the origin probe gets **1 UU** and the world probes keep **25 UU**, and
1 UU separates `-0.002` from `-10.5` decisively.

**Different probes inside one test can have different error sources, and a single tolerance has to be
loose enough for the worst of them.** Name what each one absorbs and size it accordingly - this is
[TEST-007](pattern-catalog.md#test-007)'s rule one level finer, inside a single scan rather than across
a suite.

## The render camera may be an OUT-PARAMETER, not a field anywhere {#camera-as-out-param}

**This explains a class of failure the fleet keeps re-encountering**, and it fails in the worst possible
way: like a wrong offset rather than a wrong premise. `[LIVE]`

UE3's `ULocalPlayer::CalcSceneView` fetches the view fresh every frame and builds the matrices as
**locals**:

```text
if (bOverrideView) { ViewLocation = OverrideLocation; ... }
else               { Actor->eventGetPlayerViewPoint( ViewLocation, ViewRotation ); }
... ViewMatrix and ProjectionMatrix built as LOCALS into a new FSceneView
```

**There is no persistent "view rotation the renderer reads."** So hunting the camera *object* for a field
that steers the render cannot work - and a sibling project spent its largest effort block proving it,
recording the defeat as *"Writing the camera object does nothing: confirmed twice now, from two different
angles."* Its `FTPOV` blocks (`Location`/`Rotation`/`FOV`) are **caches - per-frame outputs**, not inputs.

**What to do instead: hook the producer and rewrite its out-params.** Then gate it, because:

### Gate by return address - the callee has many consumers and one of them is the camera

`eventGetPlayerViewPoint` runs about **ten times per rendered frame** for mixed consumers - audio
listener, AI, weapons - and **only one call is the render camera**. Measured: **6,516 view calls against
666 presents in 5 s**, with the gate reporting `wrong_caller 284,597` against `applied 34,073`.

Ungated, your offset moves the audio listener and the AI along with the camera. And the gate is not just
damage control - **it buys aim/view decoupling for free**, because every non-render consumer keeps the
engine's own values.

### Prefer the hook on the path that must run for a frame to exist {#hook-the-render-path}

This generalises well past UE3 and it is the rule to take away.

A sibling drove head-look through `ProcessViewRotation` - the engine's *sanctioned script-level* view
adjustment - and its own telemetry records the failure: *"Zero per heartbeat during gameplay = the engine
is not dispatching ProcessViewRotation (cutscene/scripted state)."* They shipped **"cutscene cameras are
fixed (no head-look)"** as an unfixable known issue, and it made their first mission unplayable in VR.

The render path has no such gate: **if a frame is drawn, it ran.** Hooking `CalcSceneView` instead gave
head-look *inside cutscenes*, measured twice.

> **Script and tick paths are gated by game state; render paths are gated by rendering.** When choosing
> between two hook sites, prefer the one that must run for a frame to exist.

See [HOOK-006](pattern-catalog.md#hook-006) and [CAM-014](pattern-catalog.md#cam-014).

## An export's name proves a bracket exists, not what passes through it {#export-bracket}

Swat4-VR's three commits in one night are the arc in miniature. `[STATIC]` then `[LIVE]` then `[STATIC]`

1. The export table carried `??0FActorSceneNode@@QAE@PAVUViewport@@PAVFRenderTarget@@PAVAActor@@...` -
   UE2 renders a single actor through its own scene node, and that node re-issues the projection. So
   *"the weapon is an `FActorSceneNode`"*: the bit-identical second projection had a name.
2. A headless run named what actually came through it: `OfficerRedOne0`, `OfficerBlueTwo0` and their
   colleagues at FOV 43 - **the squad portraits on the HUD**, not the first-person weapon. 16,660
   nodes, 0 transforms through the proxy, rotations tracking neither camera nor pawn. Cleanly dead,
   which is the point of testing it cheaply.
3. Ghidra on `FPlayerSceneNode::Render` settled the structure: pre-render interactions, then
   `FLevelSceneNode::Render`, then post-render, and **no separate weapon call anywhere** - the weapon
   is one actor among many inside the level render. The static call graph could go no further because
   UE2 dispatches the actor loop through virtuals; **the export table could**:
   `?Render@FDynamicActor@@...` is the per-actor render proxy, one call per actor drawn, with the actor
   reachable from `this`. That build *names* what comes through and modifies nothing - *"the last two
   times I acted on a structure I had inferred rather than read, the structure was wrong."*

Two discriminators from the same work generalise past UE2:

- **The pointee's name must vary between instances.** Finding the `AActor*` inside `FDynamicActor` by
  scanning for a pointer to a named object is not enough - a slot holding the level, the class or the
  outer package has a name too, and it is the *same* name every time. Require the candidate slot's
  pointee name to **differ across instances**, refuse to settle from a scene with one repeated actor,
  and say so rather than locking in a slot the evidence cannot distinguish. This is
  [two-part signature](#two-part-signature) with *variance* as the second part.
- **A wrapper's `GetName` is the wrapper's name.** `Modifier.uc`: a `FinalBlend` *wraps* the texture
  it decorates, so `GetName` on what `DrawTile` hands you returns `FinalBlend13` and
  `HUD.CenterReticle` stays inside it - no string test could ever have matched. Follow the wrapper's
  pointer to the wrapped object, found by signature with **three independent wrappers required to
  agree**, and depth-bound the chain, because a Modifier may wrap a Modifier and a cycle hangs the
  render thread.

Two toolkit traps on the way, both cheap to lose an hour to: `switch_program` returned success while
the current program stayed the previous one (`open_program` worked); and every export in this build is
a **five-byte `jmp` thunk**, so the function body is not at the export RVA.

## An object pointer is not an identity when the object can be recreated {#pointer-not-identity}

Mirror's Edge VR logged `Direct3DCreate9` twice per run and got two different answers about whether that
mattered. `[SOURCE]`

| Run | call #1 | call #2 | |
|---|---|---|---|
| 21:39:00 | `028C1120` | `028C1120` | **same address reused** |
| 21:40:07 | `0286DFE0` | `028D5540` | distinct addresses |

**The same address twice means the first object was released before the second was created and the
allocator handed back the slot.** So a pointer identity test - "is this the device I hooked?" - answers
*yes* for an object that is not the one you hooked, and *no* on the very next run for a setup that is
otherwise identical.

**Two consequences.** A cached pointer cannot be a key: comparing it tells you about an address, not an
object. And **run-to-run variation here is not noise** - it is the allocator, and a test that passes on
Tuesday and fails on Wednesday for this reason will be blamed on everything else first.

Use something the object cannot share with its successor: a **creation counter**, a generation stamped
at hook time, or a re-derived vtable check. This is the
[identity-and-generation problem](06-debugging-methodology.md#identity-and-generation) at the level of a COM object rather than an
entity handle, and the third instance of it in this survey - a reused slot is a reused slot whether it
holds a pawn, a pose, or a `IDirect3D9`.

**And note that the interface being created twice at all is worth knowing**: a mod that assumes one
creation and hooks on the first will be attached to a dead object for the whole session.

### When aliasing hides the answer, change the run - not the instrument

The follow-up is a lesson about test design, and the project states it against itself. `[SOURCE]`

The open question was *which* of the two `IDirect3D9` instances receives `CreateDevice`. The first
attempt could not answer it, because both calls returned `0278D960` and `CreateDevice` arrived on
`0278D960` - **the address identified nothing.** A later run happened not to alias, and settled it
immediately:

```
Direct3DCreate9 (call #1) -> IDirect3D9* 02717260
Direct3DCreate9 (call #2) -> IDirect3D9* 07539EC0
CreateDevice    on          IDirect3D9* 07539EC0     <- the second one
```

So the first instance is a throwaway - consistent with adapter and display-mode enumeration for the
video options - and the second is real.

Their own note on how that went is the transferable part:

> *An instrument that reads an address cannot distinguish objects that share one.* **The trap was
> written down before the test was designed, and the test was still built around reading an address.**
> Repeating the run under different allocator conditions is what answered it - not a better instrument.

**Knowing a trap does not protect you from it.** When an instrument cannot separate two hypotheses,
reach first for a *run* that separates them - different allocator pressure, a different load order, a
cold start - because varying the conditions is usually cheaper than building a better instrument, and it
is the only option when no instrument can see the difference at all.

And keep the caveat they kept: the answer arrived from a non-aliasing run, so **no address-based test
can reproduce it on demand.** Nothing there depends on the distinction only because vtable patching
covers every instance regardless.

## Guard bytes in a dispatch slot mean "never call this" - and they falsify a static claim {#guard-bytes-mean-never-call}

A slot in an exported function table that comes back as `0xfefefefe`, `0xcccccccc` or `0xbaadf00d` is
not a function. It is uninitialised MSVC debug fill: the factory never assigned it.

That is useful twice over. **Defensively**, the slot must be flagged and passed through, never
called and never assumed to be some function whose position you inferred from a reference header.
**Evidentially**, it confirms a static claim *from the other side of the boundary* - SoF-VR predicted
statically that `GetRefAPI` never assigns slots 26 and 32, and the client received guard bytes at
exactly those two slots out of 54. A static prediction and a runtime observation agreeing on an
**absence** is stronger evidence than either alone, and absences are otherwise hard to prove.

Log the fill pattern rather than normalising it to null - `0xfefefefe` names the toolchain and the
build flavour, and a slot that is genuinely null means something different. `[LIVE]` SoF-VR, M0.

## Section entropy tells you in seconds whether static analysis is possible {#entropy-triage}

Before planning any reverse engineering, measure per-section Shannon entropy. Singularity's answer
arrived before a disassembler was opened. `[SOURCE]`

| Section | Entropy | Reading |
|---|--:|---|
| `BINK` | 5.859 | plaintext |
| **`.text`** | **8.000** | **fully encrypted** |
| `.rdata` | 5.092 | plaintext |
| `.data` | 4.987 | plaintext |
| `.reloc` | 6.572 | plaintext |
| **`.bind`** | 7.993 | encrypted - the DRM stub itself |

**Exactly 8.000 is the ceiling for a byte stream** - it means no byte value is more common than any
other, which real code never is. And the table explains a state that is otherwise confusing: **symbol
names were readable while the code was not**, because symbols live in plaintext `.rdata`. Do not
conclude from readable strings that the binary is analysable.

## The DRM-free twin: prove it is the same build, then analyse that one instead {#drm-free-twin}

The best answer to an encrypted `.text` is not to unpack it. Singularity is sold DRM-free on GOG, and a
section-level comparison settles whether the two copies are the same compiled build or merely similar
code: `[SOURCE]`

| | Steam | GOG |
|---|---|---|
| PE timestamp | 2010-07-08 14:50:05 | **identical** |
| `.text` size | 20,447,514 / 20,447,744 | **identical** |
| `.rdata` / `.data` / `.reloc` size | - | **identical** |
| `.text` entropy | **8.000** (encrypted) | **6.526** (plaintext) |
| Sections | 8 (has `.bind`) | 7 (no `.bind`) |
| File size | 27,444,736 | 27,084,288 |

**The file-size difference is exactly the size of `.bind`.** That is the whole proof: Steam's copy is
this exact binary with the DRM stub appended and `.text` encrypted **in place**, nothing else changed.
Static analysis therefore targets the GOG executable exclusively, with no unpacking step, and the
addresses and byte patterns found there resolve identically in a running Steam process - because the
code is decrypted in memory at runtime whatever it was shipped as.

**Check both directions before assuming, because the opposite case is just as common.** Far Cry 2 ships
*genuinely different* `Dunia.dll` builds on GOG, Steam and Ubisoft Connect, and needed a second
build-specific outer layer to cope ([17](17-teardown-fc2vr-native-stereo.md)). Identical section sizes
and an identical PE timestamp are what distinguish "same build, different wrapper" from "different
build" - and that is a five-minute check that decides weeks of work.

They still scan by byte signature rather than fixed offset, and say why: robustness against patches,
ASLR and ini-driven build variance - **not** because the parity is in doubt. A stated reason keeps a
later reader from "simplifying" it away.

### Find an offset by SIGNATURE, and make the signature need two things {#two-part-signature}

An SDK header gives you **declaration order, which is vocabulary, not truth** - offsets must come from
the shipped bytes. A worked example that generalises: `[LIVE]`

To locate a canvas's dimensions, Swat4-VR searched the object for a float run `{0, 0, W, H}` **whose
`W` and `H` reappear later in the same object as an int32 pair**.

> Requiring **both** is what turns a guess into a signature. An unrelated rectangle that happens to read
> `{0,0,W,H}` will not also carry its integer twin.

**Zero matches and multiple matches are both failures** - the lane disables itself and dumps 24 words so
one run settles it. And they cross-check the result at runtime: the discovered canvas centre is compared
against **the furthest tile actually drawn**. If those disagree the coordinate spaces differ and any
scale would pivot on the wrong point, so it says so rather than silently producing a HUD that slides
toward a corner.

**A discovery routine that can fail must log its evidence on failure.** One of theirs failed *silently*
and its own report said *"see the errors above"* with no errors above. Once it was made to speak, **the
very next run printed the answer.**

### A shared callee tells you what a function NEEDS, not what it does {#shared-callee-inference}

DishonoredVR concluded a function was "a second render path" because it shared two callees with the main
viewport draw - and recorded that conclusion *"regardless of what the array turns out to be."* Source
later named the shared callee as the **texture-streaming view update**. The loop draws nothing. `[LIVE]`

The sharing was real and correctly measured. **The inference was that sharing machinery with a render
path makes something a render path.** Both functions call the view builder because **both need a view**,
for unrelated reasons.

> **A callee tells you what a function consumes. What it does with the result is not in the call graph.**

And the tell was inside their own document: it explicitly set aside the array's identity as the less
important question - **and that was the question that would have settled it.** When a write-up defers an
identity question as secondary, check whether it is actually the load-bearing one.



### When the file is packed, dump the RUNNING image - and prove the dump is real {#dump-the-running-image}

Entropy triage tells you *whether* a binary is packed. This is what to do next, and how to know it
worked. `[LIVE]`

**The symptom is misleading and costs time on its own.** A packed binary makes Ghidra report **almost no
xrefs**, which reads as a configuration problem - a bad language spec, a failed analysis pass, a wrong
base. It is none of those. **The code is not in the file.**

**Dump the module's virtual address space from the running process** - about 120 lines of Frida.
Enumerate the readable ranges, write them out, and **zero-fill the gaps so every file offset equals
`VA - image base`**. Load the result into Ghidra as **Raw Binary at that base** and runtime addresses map
straight onto file offsets with no arithmetic anywhere.

**Do not rebuild the PE.** If the binary is stripped there are no symbols to preserve either way, and
section-table reconstruction buys nothing a flat image at the right base does not already give you.

### Two numbers that prove the dump is clean

The important half, because a dump that silently captured the *still-packed* image looks identical in a
file browser: `[LIVE]`

| | in memory | on disk |
|---|--:|--:|
| `.text` bytes differing | — | **99.61%** over 8 MB |
| common x86-64 opcode density | **34.8%** | 6.6% |
| zero bytes | **6.9%** | 0.4% |

**Encrypted or compressed data has a near-uniform byte distribution and almost no zero padding. Real code
has roughly five times the opcode density and normal alignment zeros.**

> That two-number comparison - **opcode density and zero-byte fraction** - is a reusable packing test. It
> diagnoses packing *and* proves the dump is clean, using the same measurement.

It is the complement to [entropy triage](#probe-point): entropy answers *"is this packed"*; opcode
density answers *"is what I just dumped actually code"*. A high-entropy section and a low-opcode-density
dump are the same finding seen twice, and only the second one tells you your dump failed.

**Cost: about a minute of game time**, after which every static question is offline work.

### The same measurement, the opposite answer - and that is what makes it a procedure

Singularity's `.text` came back at exactly **8.000** and cost a second purchase. Mirror's Edge VR ran the
identical check and got the other result, which is worth recording because it turns entropy triage from
an anecdote into a decision procedure. `[SOURCE]`

| Section | Steam | GOG |
|---|--:|--:|
| `.text` | **6.480** | **6.480** |
| `.rdata` | 5.502 | 5.502 |
| `.data` | 5.621 | 5.621 |
| `.reloc` | 6.651 | 6.651 |
| `.bind` | 7.986 | *(absent)* |

**There are (at least) two SteamStub variants**, and one number tells them apart in seconds: the older
one **only wraps the entry point** and leaves `.text` in the clear, while the one Singularity met
encrypts it outright. *"Steam's copy is the GOG image with a 344 KB `.bind` section appended and nothing
encrypted."*

**And they proved sameness harder than by section size.** Where the earlier project matched sizes and a
file-size delta, this one hashed the sections:

```
.text  sha256   Steam = GOG = 9F74B055D2A0AC7019FDE9A3DB12CDE55502AD19FDE694CC76108813A6DC8893
.rdata sha256   Steam = GOG = E6BB376BBC803094F470B2951AF6ED515062038DA8B53D965E1208B5B56F958A
```

**Byte-identical, not merely similar** - which retires the "do these addresses hold on the other build?"
question entirely rather than making it probable. Hash the sections; it costs nothing over measuring
them.

Their own caveat is the one to keep: **unencrypted is not the same as runnable.** The Steam copy still
carries the stub, so being able to *read* it is a statement about static analysis, not about launching
it.

## Identifying a matrix: pick a probe point where the test is not vacuous {#probe-point}

Singularity's view-matrix spike is a clean worked example of a scan that found the right matrix, and of
the two ways such a scan lies. `[SOURCE]`

**The engine renders in translated-world space.** Every match landed on the **origin** probe point and
never on the camera's world position, because UE3 pre-subtracts the view origin on the CPU to protect
float precision at large world coordinates. *"Probing `(0,0,0)` as a third point is the only reason the
scan found anything at all."* **If your world-position probe finds nothing, the engine may have already
subtracted it** - and that is common in any engine with large maps, not a UE3 quirk.

**But at the origin the usual test degenerates.** The scan's discriminator was that `clip.w` should
cancel to zero for a point on the camera. At `p = (0,0,0)`, `clip.w` collapses to `r[3].w` under **both**
storage conventions, so the test cannot tell ROW from COL and admits any matrix with a near-zero `w`
constant - which is most of them. It returned 18 candidates, most spurious, several with `w` of exactly
`+1.0000`. **The zero-cancellation argument only carries information when the probe point is far from
the origin**, which is exactly where translated-world space will not let you probe.

**The fix is a second, independent test that also resolves the convention.** For a genuine world-to-clip
matrix, the xyz of the `w` term **is the camera's forward axis**, and the camera's real facing is already
known from its rotator. Requiring `dotFwd >= 0.99` rejects the unrelated matrices *and* settles ROW
versus COL on identical bytes:

```
** c0  ROW  w=-0.0020  dotFwd=+1.0000  hits=50    <- the view matrix
   c0  COL  w=-0.0020  dotFwd=+0.0023  hits=9     <- same bytes, wrong convention
```

**A second test that discriminates on a different physical quantity is worth more than a tighter
threshold on the first one** - and where it also resolves an ambiguity you were going to have to settle
separately, it costs nothing. See [RE-007](pattern-catalog.md#re-007).

## Tooling worth adopting

- **[ReGenny](https://github.com/cursey/regenny)** (+ [SdkGenny](https://github.com/cursey/sdkgenny)) —
  interactively reconstruct structs against a live process and generate C++ headers. This maps directly
  onto the struct-offset work all three projects already do by hand (`ADDRESS_REGISTRY.md`,
  `cNode3D+0x108`, `AHands+0x40C`, `playerRoot+0x110`). Its `.genny` project files are **plaintext and
  git-friendly**, so struct definitions get diffed and reviewed like the rest of the docs, and it exposes
  an HTTP API plus an MCP server for AI-assisted analysis. The [ReGenny book](https://praydog.com/regenny-book/)
  is the reference.
  **Setup notes that aren't in the README.** Build with `cmake -B build` then
  `cmake --build build --config Release`; CPM fetches every dependency automatically — including
  **LuaGenny**, so you don't install that separately. The MCP server is a *separate* .NET project under
  `mcp-server/` targeting **net10.0**, so it needs the .NET 10 SDK (`dotnet build -c Release`), and it is
  a **stdio** server you register with your agent by pointing at the built `McpServer.exe`. The
  non-obvious part: **ReGenny's HTTP API is off by default and the MCP server is only a proxy to it** —
  enable it with the "HTTP API (MCP)" checkbox under the menu, or by setting `"api_enabled": true` in
  `cfg.json` in ReGenny's app-data folder (`%APPDATA%/cursey/ReGenny/`), and override the port with
  `REGENNY_API_PORT`. **ReGenny must be running** for any MCP tool to return data; a dead port looks
  exactly like a broken MCP registration.
- **[LuaGenny](https://github.com/praydog/luagenny)** — Lua bindings for sdkgenny, used by ReGenny's REPL.
  Worth it when you want to *script* structure analysis: walk an object graph, validate a field offset
  across many instances, or dump a layout automatically, rather than clicking through a UI. It complements
  the live-tracing workflow (Frida/debugger) in [06](06-debugging-methodology.md).
- **A small read-only script kit of your own.** You will re-run the same four or five queries on every
  project, and they're each ~100 lines. Worth having: RIP-relative **string-xref finder** over a PE, an
  **AOB uniqueness verifier**, an **offline disassembler** (on-disk PE → RVA addressing) *and* a **live
  one** (attach with read-only access and disassemble by RVA), and a **differential state scanner**.
  (*HaloVR's `tools/` is exactly this — `find_string_xrefs.py`, `verify_sig.py`, `pedis.py`, `disasm.py`,
  `pause_scan.py`, `snapshot_xrefs.py` — every one explicitly read-only and documented as never modifying
  the game.* Keeping them read-only by construction is what makes them safe to run against a live
  session.)
- **In-process live editors** — Praydog's [RE-BHVT-Editor](https://github.com/praydog/RE-BHVT-Editor) is
  RE Engine-specific (it rides REFramework) and so is **not usable on any engine in this playbook**. The
  transferable idea is the *shape*: an in-process ImGui overlay that inspects and edits live engine data
  structures, extended with Lua. Given how expensive the headset test loop is
  ([08](08-project-process.md)), an in-process inspector that lets you retune and re-inspect without a
  rebuild is worth real investment — the same argument that makes live cvars beat rebuild-required config.
