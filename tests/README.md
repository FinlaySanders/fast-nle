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
