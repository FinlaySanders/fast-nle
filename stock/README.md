# Evaluating a fast-nle-trained PufferLib policy on stock NLE

This directory is built from a PufferLib checkout (`vendor/fast-nle` is this repo) and adds nothing to PufferLib's own build. It evaluates a PufferLib NetHack policy on **unmodified stock NLE** and on the real
`NetHackChallenge-v0` gym environment, so its score can be compared with agents
scored on the NetHack Challenge interface (AutoAscend: median 5,336 in 2021).

The policy is trained on the `fast-nle` fork, which exports a few things the stock
observation does not carry (terrain under the hero, shop prices, peaceful monsters,
known spells, inventory weight and carrying capacity, intrinsics, the player's
identity). `nh_derive.h` rebuilds every one of those from stock's public
observation, using zero-time probe keystrokes (`;` farlook, `#terrain`, the
discoveries list) that the challenge counts as ordinary steps. The env, observation
packer, action masks and policy above the engine are byte-identical on both engines.

| rung | engine | how the hooks are answered | seedable | speed |
|---|---|---|---|---|
| fork | `vendor/fast-nle`, linked | read from engine memory | yes | ~30K steps/s |
| stock C | stock `libnethack.so`, one private copy per env (dlopen from a memfd) | reconstructed | yes | ~10K games/hour |
| gym | stock NLE inside `NetHackChallenge-v0`, reset/step only | reconstructed | no (NLE seeds itself) | ~20 games/hour/worker |

The stock C rung emits the same key stream as the gym rung on a seeded game; it is
the fast certification instrument, the gym rung the confirmation on the literal
competition interface.

## Build

```
./build.sh nethack                  # PufferLib: fork engine + trainer (puffer), unchanged
bash vendor/fast-nle/stock/build.sh # this directory: stock/build/libnethack.so (the stock backend) + stock/libnhagent.so (gym driver)
```

PufferLib's build is not modified. The stock backend is compiled as a `libnethack.so` that exports
the same `nle_*` API as the fork library; `stock/puffer_stock` runs the ordinary `puffer` binary
with that library placed first on the loader's path, so the fork engine is never loaded.

Stock NLE itself: clone https://github.com/facebookresearch/nle, build it, and
`pip install -e .` into the Python env used for the gym rung. Two paths are needed:

```
export NLE_STOCK_LIB=/path/to/nle/nle/libnethack.so
export NETHACKDIR=/path/to/nle/nle/nethackdir       # stock's data files, not the fork's
```

## Run

Fork (the trainer's own eval):

```
./puffer eval --base.load_model_path=ckpt.bin --base.eval_agents=512 --base.eval_episodes=6000 --base.seed=21
```

Stock C, same arguments, same seed protocol:

```
NH_EPLOG=stock.ep vendor/fast-nle/stock/puffer_stock eval --base.load_model_path=ckpt.bin --base.eval_agents=512 --base.eval_episodes=6000 --base.seed=21
python vendor/fast-nle/stock/analyze.py stock.ep
```

Gym (24 workers × 20 games is a common shape; each worker is one sequential
NetHackChallenge-v0 environment):

```
for i in $(seq 1 24); do python vendor/fast-nle/stock/nhc_agent.py --weights ckpt.bin --episodes 20 --out r4/w$i.jsonl & done; wait
python vendor/fast-nle/stock/gym_analyze.py r4/
```

## Protocol notes

- **Burn-in.** A 512-agent eval finishes short games first, so the first completed
  episodes are biased low. With `NH_EPLOG=<file>` the stock backend writes one line per
  finished episode in completion order (score, end reason, turn, worst clock-less run,
  role, race, gender); `analyze.py` drops the first 4,000 and reports the next ones.
  `gym_analyze.py` pools workers at equal episode counts instead.
- **Options.** The stock backend passes NLE's own option string
  (`pickup_types:$?!/`, NetHack's pile limit, random character), the NetHack
  Challenge's configuration; `NH_STOCK_OPTIONS` overrides it. The env's default
  training options are the same set.
- **Zero-time mask.** The challenge ends an episode after 10,000 steps without a
  game turn. The env's zero-time memory (masks an action refused for free twice in
  a row until the world changes) is on for both stock rungs (`NH_ZT_MASK=1`, set by
  the backends) and off in training.
- **Clock.** Stock NetHack reads the wall clock: moon phase and Friday the 13th at
  game start, night and midnight during play (new moon: every cockatrice hiss
  stones; full moon: +1 Luck; midnight: undead deal double damage). Scores on stock
  therefore carry the date they were run on. `NH_STOCK_FIXEDCLOCK=<unix seconds>`
  pins every game of a C-rung eval to one instant; `fixclock.c` is the equivalent
  `LD_PRELOAD` shim for the gym rung.
- **Noise.** Per-game scores are heavy-tailed (standard deviation ~15–20K for a
  strong policy). 480 gym games pin the median to about ±13%, 4,000 to ±4%.

## Files

- `nh_derive.h`, `nh_tables.h`: the reconstruction and its static object/monster tables.
- `nh_stock_backend.c`: stock C rung, built as a drop-in `libnethack.so`. Implements the fork's `nle_*` entry points over stock's,
  with per-env engine copies, crash isolation for stock's known in-engine faults, the
  top-line message preserved across probes, and the challenge step accounting.
- `nh_gym_backend.c`, `nh_gym_runner.c`, `nhc_agent.py`: gym rung. The engine transport is a
  callback into Python; every keystroke, policy action and probe alike, is one `env.step()`.
- `analyze.py`, `gym_analyze.py`: the two protocols above.
- `fixclock.c`: `clang -shared -fPIC -o fixclock.so fixclock.c` then `LD_PRELOAD=./fixclock.so`.
