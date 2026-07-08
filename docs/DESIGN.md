# fast-nle design

Goal: NetHack 3.6.6 as a C library stepping 1024–4096 envs across a 32-core
thread pool at maximum throughput, with machine-checkable proof that game
behavior is unchanged from stock NLE.

Base: fork of heiner/nle @ `2319f298` (engine = NetHack 3.6.6 + NLE's patches:
win/rl window port, obs extraction, RNG seed control, fcontext coroutine
driver). The deliverable is the C API (`nle_start`/`nle_step`/`nle_end`) for
PufferLib's native vecenv. The Python package stays, demoted to a
verification/debug surface: it lets existing bots (AutoAscend) run live
against the refactored engine, `nle/tests/` doubles as an extra oracle, and
tty_render/interactive play help debugging. It is excluded from performance
claims and the hot path; its dlopen-copy-per-instance hack becomes
unnecessary after the per-env refactor.

Prior art: liujonathan24/NetHack did this migration by hand over ten stages
(~13K diff lines, 441 ad-hoc ctx fields, per-file macro shims). Its mechanism
is sound and we keep it; its execution is what we fix. Measured on that fork:
2.6x single-thread from algorithmic+build fixes, then round-robin @1024 envs
costs 2.3x over tight-loop stepping — i.e. after CPU optimization the dominant
cost in our regime is cache locality. That drives this design.

## 1. Correctness is mechanically checked, not reviewed

Two oracles gate every commit:

**(a) Writable-section check.** After building `libnethack.so`, dump
`.data`/`.bss`/`.tbss`/COMMON symbols (`nm`/`objdump`) and fail on anything
not whitelisted (the one TLS ctx pointer; genuinely-immutable tables upstream
forgot to mark `const`, each whitelisted with a justification comment).
File-scope statics appear as local symbols, so this catches every missed
global — the scariest bug class (silent cross-env state leak). Bootstrapping
bonus: run it on the unmodified build and the failure list IS the migration
inventory.

**(b) Golden-trajectory replay.** Recorded from stock NLE at the import
commit, normalized only by (i) `time(2)` pinned via
`tools/faketime_shim.c` — stock leaks wall-clock into gameplay through
`ubirthday` (shopkeeper names, price parity, scroll labels), pinned to the
same epoch our engine derives from `time_seed`
(`nle_birthday_maybe_fixed()`, formula mirrored in
`tools/record_autoascend.py:pinned_epoch`) — and (ii)
`tools/stock_record.patch`, a minimal source patch mirroring the engine's
documented determinism fixes (currently: `sort_rooms` total order — libc
qsort tie order is implementation-defined and macOS vs glibc disagreed).
Every hunk in that patch must correspond to a documented engine deviation
and vice versa. Golden format:
`(seed, action, FNV-1a hash of glyphs+chars+blstats+message)` per step.
Corpus: AutoAscend-driven games (thousands of turns deep — shops, combat,
prayer, level changes; multiple roles/seeds) plus scripted edge cases
(save/load blobs, death, level teleport). AutoAscend targets the older NLE
Python API; run it in its own Docker if porting to 1.x is annoying — the C
engine and obs are identical. Replay harness is a C program driving our
library. Three mandatory modes:
  1. single-thread — basic equivalence;
  2. thread-shuffled — every step of every env executed from a randomly chosen
     pool thread (catches TLS/migration split-brain bugs, e.g. a counter left
     `__thread` while its array moved per-env);
  3. interleaved-pairs — envs A,B stepped alternately must hash identically to
     A,B run solo (catches cross-env leakage even when both games "work").

**(c) Wall-clock independence.** CI replays a shop-reaching golden under
two different interposed clocks (`faketime_shim` + `NLE_FAKE_TIME`); both
must pass. Guards against reintroducing any `time()`-derived gameplay
dependency (see tests/README.md "Wall-clock leak").

Full catalogue of stock's same-seed nondeterminism (wall-clock, platform
ifdefs, argument evaluation order, libc qsort ties), how each was found,
and the debugging playbook: **docs/DETERMINISM.md**.

**(d) Optimization-level independence.** C leaves function-argument
evaluation order unspecified, and NetHack passes multiple RNG-drawing
expressions as sibling arguments (`mkgold(0L, somex(croom),
somey(croom))`, …): gcc -O3 evaluated them in a different order than
-O2/clang, producing different (still deterministic) dungeons per build.
All such sites are explicitly sequenced into locals in the canonical
(clang/-O2) order — grep `fast-nle: sequence rng draws`. CI replays the
corpus with a gcc -O3 Release build to keep new sites out. This is what
lets the -O3 + LTO perf work proceed without invalidating goldens.

Platform note: the engine is normalized to Unix behavior everywhere — the
MACOSX-only apple message in `eat.c` is disabled (it differed textually
AND in RNG draws from the Unix branch, so seeds could fork across
platforms). Deep goldens are recorded from stock NLE on Linux
(`record-goldens.yml`, stock built with clang for canonical argument
order) and replay bit-exactly on mac dev builds.

Sanitizer builds (ASan/UBSan) run the replay in CI. The bump arena hides
use-after-free from ASan, so keep an `NH_ARENA=off` build that routes
allocations to libc malloc purely for sanitizer runs.

Order of work: **harness and goldens are committed before any engine change.**

## 2. State container

Single inventory file `globals.def` (X-macros), cross-checked against NetHack
3.7's `decl.h` (upstream already did the global inventory for its
`struct instance_globals g`) and against the section-check output:

```c
HOT(long,           moves)    /* touched every step — leading cache lines */
HOT(struct you,     u)
COLD(struct engr *, head_engr)
```

Generated from it: the `struct nh_ctx` definition (hot fields first, packed;
hot/cold classification from profiles, not intuition), accessor macros
(`#define moves (nh->moves)`), zero-init plus the non-zero `decl.c`
initializers in one place, and the fast-reset memcpy list. One naming scheme;
adding a field is one line.

Binding: `extern __thread nh_ctx *nh` (initial-exec TLS), assigned at every
public entry point. Nothing else is ever thread-local — enforced by the
section check (`.tbss` must contain exactly one pointer). Any thread can step
any env.

Irreducible mechanical cost: ~140 files still need their original
global/static declarations deleted (macro must not collide with definition).
Scripted transform, verified by oracle (a).

## 3. Per-env memory: one contiguous block

```
mmap:  [ nh_ctx (hot first) | coroutine stack | guard page | bump arena → ]
```

- One VA range per env: `madvise(MADV_HUGEPAGE)` on the hot prefix, one base
  pointer to prefetch for env i+1 while stepping env i, TLB entries cover
  ctx+stack+hot allocations together.
- `alloc()` and C++ `operator new/delete` (winrl) route to the bump arena once
  the ctx is set; libc fallback before that; `NH_ARENA=off` build for
  sanitizers.
- Reset = rewind: snapshot the dirty prefix right after `nle_start`, restore
  by memcpy. Pool of N snapshots from different seeds → diverse resets at
  memcpy speed (at 1024+ envs with a weak policy, full 0.9 ms resets arrive
  constantly and serialize on stepping threads).

## 4. Observations

Write directly into caller-provided buffers from store_glyph et al. — no
internal shadow copy + per-step memcpy. Rebind check at `nle_step` entry (obs
pointers may change between steps). tmt terminal emulation instantiated lazily
only when tty observations are actually bound.

## 5. Ported optimizations (proven trajectory-identical on the old fork)

- Build: -O3 (not -O2) + thin-LTO; `-Bsymbolic-functions` etc. on ELF. PGO
  re-tested there: no gain — skip.
- `can_reach_location` (dogmove.c): memoized visited-set, bounded clear window.
- `gettrack` (track.c): bounding box over the utrack ring, refreshed in
  `settrack`, early-out probe.
- `onscary` (monmove.c): player-on-square test before the `sengr_at`
  engraving walk.
- Per-env heartbeat/sentinel slots aligned to 256B (false-sharing).

Each lands as its own replay-gated commit.

## 6. Known levers deliberately NOT taken by default

- Engine-side prompt auto-advance: only ~21% of RL steps advance a game turn;
  auto-dismissing prompts inside the engine is worth ~2x but changes step
  semantics. If ever added: opt-in flag, off by default, separate golden set.

## 7. Benchmarks (in-tree, with the pitfalls baked in)

- Round-robin AND tight-loop modes (the rr/tight gap is the locality metric).
- Mandatory turn-counter sanity: fresh envs wait at a prompt; without
  dismissing it, "SPS" measures key-eating (~4M fake). Assert
  `blstats[NLE_BL_TIME]` advanced.
- Step-phase timing only (env-init excluded); per-thread stats; core pinning
  on Linux; `NLE_VARDIR_BASE` on tmpfs (`/dev/shm`).
- Interleave A/B runs when comparing builds (laptop thermal throttling swung
  identical binaries ~40% run-to-run).
- Target-hardware note: EPYC 7532 has 32 MB L3 per CCX; 1024 envs / 32 threads
  ≈ 5 MB hot state per thread — static env→thread sharding keeps a shard
  CCX-resident. Never dynamic scheduling across CCXs.

## 8. Phases

0. Harness first: golden recorder (stock NLE + AutoAscend), replay tool,
   section-check script, CI. Commit goldens. [DONE 2026-07-08]
1. Migration sweep: `globals.def` from section-check output → generate →
   scripted per-file edits → iterate until both oracles green. Python
   bindings kept building throughout (extra oracle: nle/tests/).
2. Port proven optimizations (replay-gated, one per commit).
3. Regime work: contiguous blocks, hugepages, prefetch pipelining, snapshot
   resets; validate scaling on the tinybox with the in-tree thread benchmark.
4. Phase-0b in parallel: AutoAscend deep goldens + live-agent runs against
   the refactored engine.

## Credits

Engine: NetHack 3.6.6 (NGPL — notices must remain intact). RL substrate:
NLE (facebookresearch/nle, continued at heiner/nle). Per-env refactor
approach informed by liujonathan24/NetHack.
