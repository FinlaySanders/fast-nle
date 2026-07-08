# Determinism: why same-seed NetHack games can differ, and how fast-nle pins them

fast-nle guarantees: **a seeded game is a pure function of
`(core, disp, lgen)` — on any platform, any compiler, any optimization
level.** Stock NLE does not have this property. This document lists every
leak we found (2026-07-08 investigation), how each was diagnosed, the fix,
and the CI gates that keep them fixed. Read this before debugging any
golden-replay mismatch — every symptom below initially looked like
something else.

## The invariant and its gates

| Oracle | What it pins | Where |
|---|---|---|
| (b) golden replay | engine == stock-at-record-time, bit-exact | `ci.yml`, 3 modes |
| (c) wall-clock independence | replay identical under two fake clocks | `ci.yml` |
| (d) optimization independence | gcc -O3 Release replays the corpus | `ci.yml` |

Goldens are recorded from stock NLE (import commit `2319f298`) normalized
by exactly two mechanisms, each mirroring a documented engine deviation:

1. **`tools/faketime_shim.c`** — pins `time(2)` to
   `1600000000 + ((core+1) % 100000) * 257` (same formula as the engine's
   `nle_birthday_maybe_fixed()`).
2. **`tools/stock_record.patch`** — minimal source patch (currently: the
   `sort_rooms` total order). Every hunk must correspond to a documented
   engine deviation and vice versa.

Recording runs on Linux CI with a **clang**-built stock
(`record-goldens.yml`) — see leak #3 for why the compiler matters.

## Leak 1: wall-clock via `ubirthday`

**What:** `u_init.c` sets `ubirthday = time(0)` at reset; NLE's seeding
never fixed it. Gameplay consumers: shopkeeper names (`shknam.c:517`,
bucketed by 257 seconds — and when the derived index overflows the name
list, an **extra `rn2()` call shifts the whole RNG stream**, a true
trajectory fork), used-item price parity (`shk.c`), scroll-label RNG
(`read.c`), `mkroom.c` anthole species, bones pool (`files.c`).

**Symptoms it produced:** deep goldens flickered ~1 frame per 100k steps
(shop greeting messages) or hard-forked; the value changed with every
rebuild ("heisenbug"), because rebuilds take minutes → a new 257 s bucket.
MSan/ASan/MallocScribble all clean (the data is initialized and
in-bounds); ASLR-stable (not address-dependent).

**Diagnosis:** interpose `time(2)` and sweep the 65 possible
`(nseed%13, nseed%5)` bucket combos — five consecutive buckets replayed a
"forked" 58k-step golden with zero mismatches, and every historical
mystery hash reappeared as some bucket.

**Fix:** `nle_birthday_maybe_fixed()` (`hacklib.c`) derives `ubirthday`
from `time_seed`; recording pins the stock clock to the same epoch.

## Leak 2: platform-conditional gameplay (`#if defined(MACOSX)`)

**What:** eating an apple prints "Delicious!  Must be a Macintosh!" on
mac builds and "Core dumped." on Unix (`eat.c`) — and the Unix branch
draws `rnd(100)` when hallucinating, so the branches are not even
RNG-equivalent: same seeds can fork across platforms.

**Symptoms:** mac-recorded goldens diverged on Linux at exactly the
apple/pear-eating frames (aa_7010 @11222, aa_7014 @7613, aa_7015 @5330…),
at every wall-clock bucket — i.e. "not time, genuinely platform".

**Fix:** `MACOSX` removed from the condition; every fast-nle build takes
the Unix branch. Linux stock takes it natively, so recording needs no
patch hunk for this.

## Leak 3: unspecified argument evaluation order

**What:** C does not define the evaluation order of function arguments,
and NetHack passes multiple RNG-drawing expressions as sibling arguments:
`mkgold(0L, somex(croom), somey(croom))` and ~15 similar sites. gcc -O3
(after inlining) evaluated them in a different order than gcc -O2/clang —
two RNG draws swap, and the dungeon differs. Deterministic per build,
**invisible to every sanitizer** (unspecified, not undefined, behavior —
`-fwrapv`/`-fno-strict-aliasing` etc. change nothing).

**Symptoms:** the pip-installed stock (gcc -O3 Release) generated a
different level-1 gold position than every -O2/clang build; "recorded on
Linux, fails everywhere else".

**Diagnosis:** per-step RNG-draw tracing (`NLE_RNG_TRACE` /
`NLE_TRACE_AT_STEP` in the msan-hunt branch replayer): the first
differing draw names the call site. Confirmed by hand-sequencing one site
and reproducing the other compiler's hash exactly.

**Fix:** all such sites sequence their draws into locals in canonical
(clang/-O2, left-to-right) order — grep `fast-nle: sequence rng draws`.
Recording builds stock with clang so its order matches. Oracle (d) keeps
new sites out; if it ever fires, use the RNG tracer to find the site.

## Leak 4: libc qsort tie order

**What:** `sort_rooms()` (`mklev.c`) sorts rooms with a comparator that
ties whenever two rooms share `lx`. qsort's tie order is
implementation-defined; macOS libc and glibc disagree, so the same seeds
generated different dungeons per platform (found at aa_7015's dlvl 2,
rooms with lx 16,16 and 56,56 — a doorway existed on one platform and not
the other). Mac libc's tie order is neither stable nor any simple total
order, so it cannot be matched; it had to be replaced.

**Fix:** `do_comp` is a total order (geometry tiebreak: ly, hx, hy —
room rectangles are unique). The identical change is applied to stock at
record time (`tools/stock_record.patch`). This invalidated 8 goldens
whose trajectories hit tie levels; they were re-recorded under the full
protocol.

## Practical rules

- **Never record a golden outside `record-goldens.yml`'s environment**
  (patched stock, clang, pinned clock, Linux). A locally recorded golden
  can encode any of the four leaks and will look like an engine bug later.
- **A golden mismatch is a real regression** — the replayers have zero
  tolerance, deliberately. Before suspecting the corpus, check which
  oracle-class the divergence falls into: message-only flicker that
  realigns → time-like leak; init/level differences → generation-order
  leak; per-build differences → evaluation order.
- **Any new engine normalization needs a matching recording-side story**:
  either stock already behaves canonically in the recording environment
  (like clang argument order), or the change goes into
  `stock_record.patch` (like the sort tiebreak).
- The investigation tooling (RNG tracer, obs frame dumper, keep-going
  replay, time sweep, two-build agreement) lives on the `msan-hunt`
  branch.
