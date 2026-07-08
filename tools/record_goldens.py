#!/usr/bin/env python
"""Record golden trajectories from *stock* NLE for equivalence testing.

Oracle (b) from docs/DESIGN.md. Drives the low-level nle.nethack.Nethack
class (raw keycodes, no gym layer) with fixed seeds and a deterministic
scripted policy, and writes one text file per episode:

    # fast-nle golden v1
    meta core=<seed> disp=<seed> reseed=0
    meta options=<full NETHACKOPTIONS string incl. name:>
    meta fix_moon_phase=1
    init <fnv1a64 hex of initial observation>
    step <keycode> <fnv1a64 hex of observation AFTER the step>
    ...
    end <done reason: done|steplimit>

The hash covers, in order: glyphs (int16), chars, colors, specials (u8),
blstats (int64), message (u8) — native little-endian bytes, exactly the
buffers the C API exposes. tests/replay_golden.c computes the identical
hash; any engine change that alters game behavior flips it.

Run with `python -P` (or from outside the repo root) so the installed nle
package is used, not the repo's source tree:
    .venv/bin/python -P tools/record_goldens.py --outdir tests/goldens

The scripted policy is a placeholder for depth: it random-walks, searches,
and dismisses prompts. TODO(phase-0b): add an AutoAscend driver (via its
Docker image or a ported NLE 1.x API) for corpus depth — shops, combat,
prayer, multi-level descent.
"""

import argparse
import os
import random

import numpy as np

from nle.nethack import Nethack

OBS_KEYS = ("glyphs", "chars", "colors", "specials", "blstats", "message", "misc")

FNV_OFFSET = 0xCBF29CE484222325
FNV_PRIME = 0x100000001B3
MASK64 = 0xFFFFFFFFFFFFFFFF


def fnv1a64(data: bytes, h: int = FNV_OFFSET) -> int:
    for b in data:
        h = ((h ^ b) * FNV_PRIME) & MASK64
    return h


def obs_hash(obs) -> int:
    glyphs, chars, colors, specials, blstats, message, _misc = obs
    h = FNV_OFFSET
    for arr in (glyphs, chars, colors, specials, blstats, message):
        assert arr.dtype in (np.int16, np.uint8, np.int64), arr.dtype
        h = fnv1a64(arr.tobytes(), h)  # native little-endian on all targets
    return h


# Deterministic scripted policy: enough variety to exercise movement,
# search, kicks, item interaction and prompt handling. Depth comes later
# from AutoAscend; this corpus mainly locks down early-game equivalence.
MOVE_KEYS = [ord(c) for c in "hjklyubn"]
MISC_KEYS = [ord(c) for c in "s" * 4 + ".:,i@"]  # search-heavy, some UI


def pick_action(rng: random.Random, misc) -> int:
    in_yn, in_getlin, waiting_space = int(misc[0]), int(misc[1]), int(misc[2])
    if in_getlin:
        return ord("\r")
    if waiting_space or in_yn:
        # ESC occasionally to exercise the other prompt-exit path.
        return 0x1B if rng.random() < 0.1 else ord(" ")
    return rng.choice(MOVE_KEYS + MISC_KEYS)


def record_episode(outdir: str, core: int, disp: int, max_steps: int) -> str:
    game = Nethack(observation_keys=OBS_KEYS, ttyrec=None, fix_moon_phase=True)
    try:
        game.set_initial_seeds(core, disp, False)
        obs = game.reset()
        rng = random.Random(core)  # policy RNG seeded by episode seed

        path = os.path.join(outdir, f"seed{core}_{disp}.golden")
        with open(path, "w") as f:
            f.write("# fast-nle golden v1\n")
            f.write(f"meta core={core} disp={disp} reseed=0\n")
            f.write(f"meta options={game._nethackoptions}\n")
            f.write("meta fix_moon_phase=1\n")
            f.write(f"init {obs_hash(obs):016x}\n")
            reason = "steplimit"
            turns = 0  # max turn seen: the final obs of a done episode is zeroed
            for _ in range(max_steps):
                action = pick_action(rng, obs[6])
                obs, done = game.step(action)
                f.write(f"step {action} {obs_hash(obs):016x}\n")
                turns = max(turns, int(obs[4][20]))  # blstats[NLE_BL_TIME]
                if done:
                    reason = "done"
                    break
            f.write(f"end {reason}\n")
        print(f"{path}: {reason}, game turns advanced to {turns}")
        if turns == 0:
            raise RuntimeError(
                f"{path}: turn counter never advanced — policy is key-eating, "
                "golden is worthless (see CLAUDE.md non-negotiable #3)"
            )
        return path
    finally:
        game.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="tests/goldens")
    ap.add_argument("--episodes", type=int, default=8)
    ap.add_argument("--steps", type=int, default=500)
    ap.add_argument("--seed-base", type=int, default=1000)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    for i in range(args.episodes):
        record_episode(args.outdir, args.seed_base + i, 2 * (args.seed_base + i) + 1,
                       args.steps)


if __name__ == "__main__":
    main()
