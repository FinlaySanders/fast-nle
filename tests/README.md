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

Current corpus: 8 episodes x 500 steps + 2 x up-to-3000 steps (one full
death) from the scripted random-walk policy. TODO(phase-0b): AutoAscend
driver for deep-game coverage (shops, combat, prayer, multi-level descent);
add thread-shuffled and interleaved-pairs replay modes once the per-env
refactor makes multi-env stepping possible.

## Benchmark rules (when benchmarks land)

- Fresh envs idle at a "waiting for space" prompt; movement keys do NOT
  advance the game. Every throughput number must come with a
  `blstats[NLE_BL_TIME]` turn-counter check, or it is measuring key-eating
  (~4M fake SPS).
- Report step-phase SPS only; never include env-init time.
- Interleave A/B runs when comparing builds (thermal throttling swings
  laptop numbers ~40%).
