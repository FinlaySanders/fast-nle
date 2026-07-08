#!/usr/bin/env python
"""Record golden trajectories from *stock* NLE for equivalence testing.

Oracle (b) from docs/DESIGN.md. Drives the low-level nle.nethack.Nethack
class (raw keycodes, no gym layer) with fixed seeds and a deterministic
scripted policy, and writes one text file per episode:

    # fast-nle golden v1
    meta core=<seed> disp=<seed> reseed=0
    meta lgen=<seed>              (only if a level-gen seed was used)
    meta options=<full NETHACKOPTIONS string incl. name:>
    meta fix_moon_phase=1
    init <fnv1a64 hex of initial observation>
    step <keycode> <fnv1a64 hex of observation AFTER the step>
    ...
    end <done reason: done|steplimit>

The hash covers, in order: glyphs (int16), chars, colors, specials (u8),
blstats (int64), message (u8) — native little-endian bytes, exactly the
buffers the C API exposes. tests/replay_golden.c / replay_multi.c compute
the identical hash; any engine change that alters game behavior flips it.

IMPORTANT: record against a STOCK build. The venv's editable install
compiles its own engine at pip-install time; if in doubt, reinstall from
the pristine import commit (or verify the corpus against a stock-worktree
library with replay_golden before trusting it).

Run with `python -P` (or from outside the repo root) so the installed nle
package is used, not the repo's source tree:
    .venv/bin/python -P tools/record_goldens.py --outdir tests/goldens

Policy: a weighted random "prodder" that exercises many subsystems —
movement, search, stair descent, inventory, eat/quaff/read/wear/wield,
kick, throw, open/close, pray, engrave, cast — with deterministic prompt
handling (getline -> a name + return; y/n -> mix of y/n/ESC; menus ->
ESC/space). Depth still comes from episode length; TODO(phase-0b):
AutoAscend driver for real deep-game coverage.
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

# All 13 roles, with valid race/gender/alignment combos for coverage of
# role-specific inventories, pets, intrinsics and quest plumbing.
ROLES = [
    "Agent-arc-hum-law-fem",
    "Agent-bar-orc-cha-mal",
    "Agent-cav-gno-neu-fem",
    "Agent-hea-gno-neu-mal",
    "Agent-kni-hum-law-fem",
    "Agent-mon-hum-neu-mal",
    "Agent-pri-elf-cha-fem",
    "Agent-ran-elf-cha-mal",
    "Agent-rog-orc-cha-fem",
    "Agent-sam-hum-law-mal",
    "Agent-tou-hum-neu-fem",
    "Agent-val-dwa-law-fem",
    "Agent-wiz-elf-cha-mal",
]


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


# Weighted action pool. Movement dominates (games must progress), but the
# rest pokes items, terrain, prayer, spellcasting, engraving, kicking...
# Prompt-heavy commands are safe: the handler below dismisses anything.
ACTIONS = (
    [ord(c) for c in "hjklyubn"] * 6      # movement (dominant: games must progress)
    + [ord("s")] * 8                       # search (advances turns reliably)
    + [ord(">")] * 4                       # descend when on stairs
    + [ord("<"), ord("."), ord(".")]       # up, rest
    + [ord(",")] * 2                       # pickup
    # one of each subsystem poke (~15% of the pool): eat quaff read wear
    # wield takeoff throw open close kick cast pay drop fight inventory
    # engrave
    + [ord(c) for c in "eqrWwTtoc"]
    + [4, ord("Z"), ord("p"), ord("d"), ord("F"), ord("i"), ord("E")]
)


def pick_action(rng: random.Random, misc, step_no: int) -> int:
    in_yn, in_getlin, waiting_space = int(misc[0]), int(misc[1]), int(misc[2])
    if in_getlin:
        # type a short deterministic name sometimes, else just return
        return ord("\r") if rng.random() < 0.8 else ord("x")
    if waiting_space:
        return 0x1B if rng.random() < 0.1 else ord(" ")
    if in_yn:
        r = rng.random()
        if r < 0.5:
            return ord("y")
        if r < 0.8:
            return ord("n")
        return 0x1B
    # rarely pray (exercises alignment/luck/god plumbing)
    if step_no and step_no % 1201 == 0:
        return ord("#")  # extended prompt; dismissed by the handlers above
    return rng.choice(ACTIONS)


def record_episode(outdir, core, disp, max_steps, role, lgen=None):
    game = Nethack(observation_keys=OBS_KEYS, playername=role, ttyrec=None,
                   fix_moon_phase=True)
    try:
        game.set_initial_seeds(core, disp, False, lgen)
        obs = game.reset()
        rng = random.Random(core)  # policy RNG seeded by episode seed

        tag = role.split("-", 2)[1]
        path = os.path.join(outdir, f"{tag}_seed{core}_{disp}.golden")
        with open(path, "w") as f:
            f.write("# fast-nle golden v1\n")
            f.write(f"meta core={core} disp={disp} reseed=0\n")
            if lgen is not None:
                f.write(f"meta lgen={lgen}\n")
            f.write(f"meta options={game._nethackoptions}\n")
            f.write("meta fix_moon_phase=1\n")
            f.write(f"init {obs_hash(obs):016x}\n")
            reason = "steplimit"
            turns = 0  # max turn seen: the final obs of a done episode is zeroed
            for i in range(max_steps):
                action = pick_action(rng, obs[6], i)
                obs, done = game.step(action)
                f.write(f"step {action} {obs_hash(obs):016x}\n")
                turns = max(turns, int(obs[4][20]))  # blstats[NLE_BL_TIME]
                if done:
                    reason = "done"
                    break
            f.write(f"end {reason}\n")
        depth_seen = int(obs[4][12]) if reason != "done" else -1
        print(f"{path}: {reason}, turns={turns}")
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
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--seed-base", type=int, default=1000)
    ap.add_argument("--roles", default="all",
                    help="'all', or comma list of 3-letter role codes")
    ap.add_argument("--episodes-per-role", type=int, default=2)
    ap.add_argument("--lgen-every", type=int, default=3,
                    help="every Nth episode also sets a level-gen seed")
    args = ap.parse_args()

    roles = ROLES if args.roles == "all" else [
        r for r in ROLES if r.split("-", 2)[1] in args.roles.split(",")
    ]
    os.makedirs(args.outdir, exist_ok=True)
    n = 0
    for role in roles:
        for k in range(args.episodes_per_role):
            core = args.seed_base + n
            disp = 2 * core + 1
            lgen = (7777 + core) if (args.lgen_every
                                     and n % args.lgen_every == 0) else None
            record_episode(args.outdir, core, disp, args.steps, role, lgen)
            n += 1


if __name__ == "__main__":
    main()
