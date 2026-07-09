# fast-nle verification

Two oracles gate every engine change (see `docs/DESIGN.md`).

## Oracle (a): no mutable globals

```
tools/check_no_globals.sh --inventory build/libnethack.so   # the worklist
tools/check_no_globals.sh --ratchet   build/libnethack.so   # CI gate (transitional)
tools/check_no_globals.sh             build/libnethack.so   # strict gate (final)
```

Ratchet mode fails on any writable symbol not in `tools/global_baseline.txt`
(the stock build's 684 symbols). The migration shrinks the baseline toward
`tools/global_whitelist.txt` (expected final contents: one TLS ctx pointer +
justified const-in-practice tables).

## Oracle (b): golden-trajectory replay

Goldens under `tests/goldens/` were recorded from the **unmodified** engine
by `tools/record_goldens.py`: fixed seeds (`reseed=0`, `fix_moon_phase`),
deterministic scripted policy, one line per step with the action keycode and
an FNV-1a-64 hash over glyphs/chars/colors/specials/blstats/message.

Replay them against any build with:

```
cc -O2 -Iinclude -Ibuild/_deps/deboost_context-src/include \
   tests/replay_golden.c sys/unix/nledl.c -ldl -o build/replay_golden
build/replay_golden build/libnethack.so build/dat tests/goldens/*.golden
```

Any behavioral divergence fails at the first differing step. Recording
requires a venv with the stock package (`uv venv && uv pip install -e .`,
run via `python -P` so the repo's source tree doesn't shadow the install).

### Multi-env modes (tests/replay_multi.c)

The engine now supports many envs in ONE loaded library (no dlopen-copy):

```
cc -O2 -Iinclude tests/replay_multi.c -ldl -lpthread -o build/replay_multi
build/replay_multi --interleaved build/libnethack.so build/dat tests/goldens/*.golden
build/replay_multi --shuffled    build/libnethack.so build/dat tests/goldens/*.golden
```

`--interleaved` steps golden pairs alternately (A,B,A,B,...) in one process
— any cross-env leak diverges a hash. `--shuffled` additionally executes
every `nle_*` call on a rotating pool thread — any state hiding in a
thread-local other than the two sanctioned `__thread` ctx pointers
(`nh_cur`, `current_nle_ctx`) diverges. Both run in CI.

Current corpus: 28 episodes — all 13 roles x 2 seeds x 1500 steps plus two
6000-step runs; 6 episodes end in death; every 3rd episode also sets a
level-generation (lgen) seed. The policy pokes most subsystems: movement,
search, stairs, pickup/drop, eat/quaff/read/wear/wield/throw, kick, cast,
pray, engrave, open/close, pay — with deterministic prompt handling.
TODO(phase-0b): AutoAscend driver for genuinely deep games.

### Perf-mode blstats parity (!status_updates)

`NLE_REPLAY_OPTIONS_APPEND=",!status_updates"` replays the corpus with the
RL perf mode that skips the status pipeline; blstats then come from
`nle_rl_bot_direct` (winrl.cc), pumped from `bot()`/`timebot()` (botl.c) at
exactly the pipeline's trigger points. Hashes must match the stock-recorded
goldens byte-for-byte — including staleness timing (energy regen between
the last `bot()` and the observation point is visible in the obs; a
fill-time recompute FAILS this gate at deep AutoAscend steps). Runs in CI.

### Determinism

Stock NLE is NOT a pure function of its seeds — four distinct leaks
(wall-clock, a platform `#ifdef`, argument evaluation order, libc qsort
tie order) are catalogued with fixes and a debugging playbook in
**docs/DETERMINISM.md**. Summaries below.

### Wall-clock leak (ubirthday) — solved; zero mismatch tolerance

Stock NetHack sets `ubirthday = time(0)` at reset and it leaks into
GAMEPLAY: shopkeeper names (`shknam.c` buckets it by 257 seconds — and
when the derived index overflows the name list, an extra `rn2()` call
shifts the whole RNG stream, i.e. a true trajectory fork), used-item
price parity (`shk.c`), scroll labels (`read.c`), `mkroom.c`, bones pool
(`files.c`). Same seeds at different wall-clock times give different
games. This masqueraded for a long time as an "uninitialized read /
heap-layout heisenbug": any rebuild took minutes → new 257s bucket →
different shopkeeper name; ASan/MSan-clean because the data is
initialized (full hunt: msan-hunt branch).

fast-nle fixes it engine-side: `nle_birthday_maybe_fixed()` (hacklib.c)
derives ubirthday from `time_seed` when seeded. Goldens are recorded from
stock with `time(2)` pinned to the SAME epoch via `tools/faketime_shim.c`
(the recorder does this automatically; formula in `pinned_epoch()`).
Replays are therefore exact: the replayers have ZERO mismatch tolerance,
and CI replays a shop-reaching golden under two different fake clocks to
keep gameplay time-independence pinned. Seed 7010 — once dropped as
"forked" — was re-recorded under the pinned clock and replays all 58,436
steps bit-exactly. The AutoAscend recorder still verifies each golden in
a fresh subprocess before accepting it.

### Cross-platform: goldens are Linux-canonical

Stock NetHack compiles an Apple-specific apple-eating message on macOS
(`src/eat.c`, `#if defined(MACOSX)`: "Must be a Macintosh!" vs Unix's
"Core dumped.") — and the branches are not RNG-equivalent (the Unix one
draws `rnd(100)` when hallucinating), so identical seeds could fork
between platforms. fast-nle removes MACOSX from that condition: every
build takes the Unix branch, and deep goldens are recorded from stock on
Linux (`.github/workflows/record-goldens.yml`, manual trigger) so they
replay bit-exactly on both the Linux target and mac dev boxes.

And libc must not change the game: `sort_rooms()` compares rooms only by
`lx`, so ties made the dungeon depend on the platform's qsort (macOS vs
glibc disagreed at aa_7015's dlvl 2). The engine's `do_comp` is now a
total order; recording applies the identical change to stock via
`tools/stock_record.patch`.

Related: compiler flags must not change the game either. NetHack passes
multiple RNG-drawing expressions as sibling call arguments whose
evaluation order C leaves unspecified — gcc -O3 reordered them and
generated different dungeons than -O2/clang. All such sites are now
explicitly sequenced (grep `fast-nle: sequence rng draws`); CI replays
the corpus with a gcc -O3 build to catch regressions, and golden
recording builds stock with clang so its argument order matches the
canonical sequenced order.

### Regenerating / arbitrating the corpus

Goldens must capture STOCK behavior. To (re)record or arbitrate a
divergence, build a pristine library from the import commit in a worktree
— no need to touch the working tree:

```
git worktree add /tmp/fast-nle-stock 2319f298
cd /tmp/fast-nle-stock && cmake -S . -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build --target nethack dat -j
```

then verify `tests/goldens/*.golden` against it ONE FILE PER PROCESS
(stock keeps process-global state and is not multi-episode safe — that's
the very thing this fork fixes):

```
for g in tests/goldens/*.golden; do
  build/replay_golden /tmp/fast-nle-stock/build/libnethack.so \
      /tmp/fast-nle-stock/build/dat "$g" || echo "STOCK DIVERGES: $g"
done
```

Corpus history: the 28-episode corpus immediately caught two real bugs the
old 10-episode Monk-only corpus missed — deleted `nle_swap_to_lgen` hooks
in mklev.c (wholesale old-fork port removed a post-fork stock feature) and
garbage-initialized nle_ctx_t fields leaking into observations.

## Benchmark rules (when benchmarks land)

- Fresh envs idle at a "waiting for space" prompt; movement keys do NOT
  advance the game. Every throughput number must come with a
  `blstats[NLE_BL_TIME]` turn-counter check, or it is measuring key-eating
  (~4M fake SPS).
- Report step-phase SPS only; never include env-init time.
- Interleave A/B runs when comparing builds (thermal throttling swings
  laptop numbers ~40%).
