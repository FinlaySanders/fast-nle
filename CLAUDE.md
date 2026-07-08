# fast-nle

A from-scratch rework of NLE (NetHack Learning Environment) for high-throughput RL
training with PufferLib's native C vecenv: 1024–4096 parallel envs on a 32-core
tinybox (EPYC 7532-class), stepped by a thread pool, no Python in the hot path.

Fork of [heiner/nle](https://github.com/heiner/nle) (base commit `2319f298`,
NetHack 3.6.6 engine). Approach informed by
[liujonathan24/NetHack](https://github.com/liujonathan24/NetHack)'s per-env
refactor — see `docs/DESIGN.md` for what we keep and what we do differently.

## Non-negotiables

1. **Game behavior must be bit-identical to stock NLE.** Every engine change is
   gated by golden-trajectory replay: recorded `(seed, action, per-step obs hash)`
   sequences from unmodified NLE (driven by AutoAscend for depth) must replay
   identically. No commit that changes hashes, ever, without an explicit opt-in
   flag defaulting to off.
2. **No mutable globals.** All per-game state lives in one generated per-env
   context struct. CI dumps the built library's writable sections
   (`.data`/`.bss`/`.tbss`/COMMON) and fails on any non-whitelisted symbol.
   Nothing is `__thread` except the single context pointer.
3. **Benchmarks must prove the game advanced.** Fresh envs start at a
   "waiting for space" prompt; movement keys do NOT advance the game. Any
   throughput number must be accompanied by a `blstats[NLE_BL_TIME]` turn-counter
   check or it is measuring key-eating (~4M fake SPS). Report step-phase SPS
   only — never include env-init time in the denominator.

## Architecture in one paragraph

One `struct nh_ctx` per env, generated from a single X-macro inventory
(`globals.def`), hot fields (touched every step) packed first. One
initial-exec `__thread nh_ctx *` pointer set at every API entry, so any pool
thread can step any env. Each env owns one contiguous mmap:
`[ctx | coroutine stack | guard | bump arena]` — hugepage-friendly, reset =
snapshot rewind. fcontext coroutines drive NetHack's mainloop; observations are
written directly into caller buffers (no copy-then-fill). See `docs/DESIGN.md`.

## Prior-art performance facts (from the liujonathan24 fork, measured July 2026)

- Optimized single-thread step: ~2.7 µs tight-loop, ~6.3 µs round-robin @1024
  envs on M1 — the gap is cache locality, now the dominant cost in the target
  regime. Design layout for locality; don't retrofit.
- Proven trajectory-identical optimizations to port: -O3 + thin-LTO (~1.25x),
  memoized `can_reach_location` in dogmove.c (up to ~1.8x late-game),
  `gettrack` bounding-box early-out, `onscary` cheap-test-first reorder,
  direct-write observation path, 256-byte-aligned per-env heartbeat slots.
- PGO: measured, no gain over LTO. Don't re-try.
- Only ~21% of RL steps advance a game turn (prompts/blocked moves). Engine-side
  prompt auto-advance is a ~2x lever but CHANGES STEP SEMANTICS — opt-in only.
- Thread scaling is memory-bandwidth-bound, not lock-bound (multi-process was
  no better than multi-thread).
