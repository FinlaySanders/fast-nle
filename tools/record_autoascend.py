#!/usr/bin/env python
"""Record deep-game golden trajectories by driving stock NLE with
AutoAscend (NeurIPS 2021 NetHack Challenge winner).

Setup (see tests/README.md):
    uv venv --python 3.11 .venv-aa
    uv pip install --python .venv-aa numpy scipy numba opencv-python \
        toolz pandas matplotlib nltk pillow
    git worktree add /tmp/fast-nle-stock 2319f298   # pristine engine
    uv pip install --python .venv-aa /tmp/fast-nle-stock
    git clone https://github.com/maciej-sypetkowski/autoascend <dir>
Run:
    .venv-aa/bin/python -P tools/record_autoascend.py \
        --autoascend <dir> --outdir tests/goldens --seeds 1,2,3 \
        --max-steps 40000

The recording hook sits on the *raw* nle.nethack.Nethack.step, below the
gym layer, so every keypress — including any the gym env issues during
reset — lands in the golden. The result replays with the same C harnesses
as the scripted corpus (tests/replay_golden.c / replay_multi.c).

AutoAscend is deterministic per seed (it seeds its own
np.random.RandomState from the env seed), so recordings are reproducible.
"""

import argparse
import os
import subprocess
import sys

import numpy as np

# Stock NLE's ubirthday = time(0) leaks wall-clock into gameplay
# (shopkeeper names etc.). Pin time(2) to the same epoch the fast-nle
# engine derives from time_seed (= core seed + 1); keep this formula in
# sync with nle_birthday_maybe_fixed() in src/hacklib.c.
def pinned_epoch(core_seed):
    return 1600000000 + ((core_seed + 1) % 100000) * 257


def ensure_faketime_shim():
    """Re-exec with the time(2) interposer loaded if it isn't already."""
    if os.environ.get("NLE_FAKETIME_SHIM_LOADED"):
        return
    tools = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(tools, "faketime_shim.c")
    if sys.platform == "darwin":
        shim = os.path.join(tools, "faketime_shim.dylib")
        cc = ["clang", "-O2", "-dynamiclib", src, "-o", shim]
        ld_var = "DYLD_INSERT_LIBRARIES"
    else:
        shim = os.path.join(tools, "faketime_shim.so")
        cc = ["clang", "-O2", "-shared", "-fPIC", src, "-o", shim]
        ld_var = "LD_PRELOAD"
    if not os.path.exists(shim) or (os.path.getmtime(shim)
                                    < os.path.getmtime(src)):
        subprocess.run(cc, check=True)
    env = dict(os.environ)
    env[ld_var] = shim + (":" + env[ld_var] if env.get(ld_var) else "")
    env["NLE_FAKETIME_SHIM_LOADED"] = "1"
    os.execve(sys.executable, [sys.executable, "-P"] + sys.argv, env)


FNV_OFFSET = 0xCBF29CE484222325
FNV_PRIME = 0x100000001B3
MASK64 = 0xFFFFFFFFFFFFFFFF

HASH_KEYS = ("glyphs", "chars", "colors", "specials", "blstats", "message")


def fnv1a64(data: bytes, h: int) -> int:
    for b in data:
        h = ((h ^ b) * FNV_PRIME) & MASK64
    return h


def obs_hash(nethack) -> int:
    bufs = dict(zip(nethack._obs_buffers.keys(), nethack._obs))
    h = FNV_OFFSET
    for k in HASH_KEYS:
        h = fnv1a64(np.ascontiguousarray(bufs[k]).tobytes(), h)
    return h


class StepLimit(Exception):
    pass


class Recorder:
    """Logs (keycode, post-step hash) below the gym layer."""

    def __init__(self, nethack, fh, max_steps):
        self.nethack = nethack
        self.fh = fh
        self.n = 0
        self.max_steps = max_steps
        self.turns = 0
        self._orig_step = nethack.step
        nethack.step = self._step

    def _step(self, action):
        result = self._orig_step(action)
        h = obs_hash(self.nethack)
        self.fh.write(f"step {int(action)} {h:016x}\n")
        self.n += 1
        bufs = dict(zip(self.nethack._obs_buffers.keys(), self.nethack._obs))
        self.turns = max(self.turns, int(bufs["blstats"][20]))
        if self.n >= self.max_steps:
            raise StepLimit()
        return result


class OldGym:
    """gymnasium-era NLE env -> the gym-0.19 surface AutoAscend expects."""

    def __init__(self, inner):
        self._e = inner

    def reset(self):
        out = self._e.reset()
        return out[0] if isinstance(out, tuple) else out

    def step(self, idx):
        out = self._e.step(idx)
        if len(out) == 5:
            obs, r, term, trunc, info = out
            return obs, r, term or trunc, info
        return out

    def render(self, *a, **k):
        return None

    @property
    def _actions(self):
        return self._e.unwrapped.actions

    @property
    def _steps(self):
        return getattr(self._e.unwrapped, "_steps", 0)

    @property
    def _turns(self):
        return getattr(self._e.unwrapped, "_turns", 0)

    def get_seeds(self):
        return self._e.unwrapped.get_seeds()

    def __getattr__(self, name):
        return getattr(self._e.unwrapped, name)


def run_one(outdir, seed, max_steps):
    # Must be set before env creation; the shim re-reads it per call, so
    # per-seed values work within one process.
    os.environ["NLE_FAKE_TIME"] = str(pinned_epoch(seed))

    import gymnasium as gym  # noqa: F401  (nle registers on import)
    import nle.env.tasks as tasks

    class SeedableChallenge(tasks.NetHackChallenge):
        """The challenge env forbids seeding (contest rules); we are
        recording reproducible goldens, so re-enable the base seeding."""
        def seed(self, core=None, disp=None, reseed=False, lgen=None):
            try:
                return super(tasks.NetHackChallenge, self).seed(
                    core, disp, reseed, lgen)
            except TypeError:  # older base without lgen param
                return super(tasks.NetHackChallenge, self).seed(
                    core, disp, reseed)

    env = SeedableChallenge(
        savedir=None, no_progress_timeout=1000, fix_moon_phase=True
    )
    # The challenge ctor also stubs out nethack.set_initial_seeds with a
    # raiser; restore the real method from the class.
    env.nethack.set_initial_seeds = type(env.nethack).set_initial_seeds.__get__(
        env.nethack)
    env.seed(seed, seed, reseed=False)

    nethack = env.nethack
    path = os.path.join(outdir, f"aa_seed{seed}_{seed}.golden")
    fh = open(path, "w")
    fh.write("# fast-nle golden v1 (AutoAscend-driven)\n")
    fh.write(f"meta core={seed} disp={seed} reseed=0\n")
    fh.write(f"meta options={nethack._nethackoptions}\n")
    fh.write("meta fix_moon_phase=1\n")

    rec = Recorder(nethack, fh, max_steps)

    # init hash: state right after the raw engine reset, before ANY step.
    orig_reset = nethack.reset

    def reset_hook(*a, **k):
        out = orig_reset(*a, **k)
        fh.write(f"init {obs_hash(nethack):016x}\n")
        nethack.reset = orig_reset  # only the first reset
        return out

    nethack.reset = reset_hook

    from autoascend.env_wrapper import EnvWrapper

    wrapper = EnvWrapper(
        OldGym(env),
        visualizer_args=dict(enable=False),
        agent_args=dict(panic_on_errors=False, verbose=False),
        interactive=False,
    )

    reason = "done"
    try:
        wrapper.main()
    except StepLimit:
        reason = "steplimit"
    except BaseException as e:  # noqa: BLE001 — record whatever we got
        reason = f"agent-exception ({type(e).__name__})"
        print(f"seed {seed}: agent raised {type(e).__name__}: {e}",
              file=sys.stderr)
    fh.write("end %s\n" % ("done" if reason == "done" else "steplimit"))
    fh.close()
    env.close()
    print(f"{path}: {reason}, steps={rec.n}, turns={rec.turns}")
    return rec.n, rec.turns


def verify(golden_path):
    """Replay the recorded actions in a fresh raw Nethack and confirm every
    hash. With time(2) pinned (faketime shim + NLE_FAKE_TIME) recordings
    replay exactly; any mismatch here is a real problem with the recording
    environment. Returns list of mismatching step indices.
    """
    from nle.nethack import Nethack

    core = disp = None
    options = None
    acts, hashes = [], []
    init_hash = None
    for line in open(golden_path):
        if line.startswith("meta core="):
            parts = line.split()
            core = int(parts[1].split("=")[1])
            disp = int(parts[2].split("=")[1])
        elif line.startswith("meta options="):
            options = line[len("meta options="):].rstrip("\n")
        elif line.startswith("init "):
            init_hash = int(line.split()[1], 16)
        elif line.startswith("step "):
            _, a, h = line.split()
            acts.append(int(a))
            hashes.append(int(h, 16))

    opt_list = options.split(",")
    name = [o for o in opt_list if o.startswith("name:")][0][5:]
    opts = [o for o in opt_list if not o.startswith("name:")]
    os.environ["NLE_FAKE_TIME"] = str(pinned_epoch(core))
    g = Nethack(observation_keys=OBS_KEYS_V, playername=name, options=opts,
                ttyrec=None, fix_moon_phase=True)
    bad = []
    try:
        g.set_initial_seeds(core, disp, False)
        obs = g.reset()
        if obs_hash_arrays(obs) != init_hash:
            bad.append(-1)
        for i, a in enumerate(acts):
            obs, done = g.step(a)
            if obs_hash_arrays(obs) != hashes[i]:
                bad.append(i)
            if done:
                break
    finally:
        g.close()
    return bad


OBS_KEYS_V = ("glyphs", "chars", "colors", "specials", "blstats", "message",
              "misc")


def obs_hash_arrays(obs):
    h = FNV_OFFSET
    for arr in obs[:6]:
        h = fnv1a64(np.ascontiguousarray(arr).tobytes(), h)
    return h


def main():
    ensure_faketime_shim()
    ap = argparse.ArgumentParser()
    ap.add_argument("--autoascend",
                    help="path to the autoascend checkout")
    ap.add_argument("--outdir", default="tests/goldens")
    ap.add_argument("--seeds", default="1,2,3")
    ap.add_argument("--max-steps", type=int, default=40000)
    ap.add_argument("--no-verify", action="store_true",
                    help="skip the post-record replay verification")
    ap.add_argument("--verify-only", metavar="GOLDEN",
                    help="internal: verify a golden and exit")
    args = ap.parse_args()

    if args.verify_only:
        bad = verify(args.verify_only)
        if bad:
            print(f"mismatch at {bad[:5]}")
            sys.exit(1)
        sys.exit(0)

    sys.path.insert(0, args.autoascend)
    os.makedirs(args.outdir, exist_ok=True)
    for seed in [int(s) for s in args.seeds.split(",")]:
        run_one(args.outdir, seed, args.max_steps)
        if not args.no_verify:
            path = os.path.join(args.outdir, f"aa_seed{seed}_{seed}.golden")
            # fresh process: the uninit-read noise tracks heap layout, so an
            # in-process verify can be blind to it
            import subprocess
            out = subprocess.run(
                [sys.executable, "-P", os.path.abspath(__file__),
                 "--verify-only", path], capture_output=True, text=True)
            bad = [] if out.returncode == 0 else [out.stdout.strip() or "?"]
            if bad:
                print(f"{path}: RECORD-TIME TRANSIENT at step(s) {bad[:5]} — "
                      "re-record this seed", file=sys.stderr)
                os.rename(path, path + ".unverified")
            else:
                print(f"{path}: verified (replay-clean)")


if __name__ == "__main__":
    main()
