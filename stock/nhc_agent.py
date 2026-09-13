"""Run the PufferLib NetHack policy on the real NetHackChallenge-v0 environment.

The policy, its observation packer and the stock-NLE reconstruction all live in
libnhagent.so. This file owns the gym environment and nothing else: every key the
C side wants -- a policy action or a reconstruction probe -- comes back here and
becomes one env.step(), so the challenge counts them all.
"""
import ctypes, os, sys, time, traceback
import numpy as np
import gym, nle
from nle import nethack

# The env's zero-time mask (nethack.h): the challenge ends an episode after 10,000 steps without a game turn, so an
# action the game refused for free twice in a row stays masked until the world changes. On for every stock evaluation.
os.environ.setdefault("NH_ZT_MASK", "1")

SP = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(SP, "libnhagent.so")

SEND = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int)
RESET = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p)


class OnlyResetStep:
    """The whole contract with the challenge environment, made checkable.

    Nothing but reset() and step() is reachable through this object, so the agent
    cannot read engine state, reseed, or reach past the environment for anything
    the competition would not have given it. Any other attribute raises.
    """

    __slots__ = ("_env", "n_reset", "n_step")

    def __init__(self, env):
        object.__setattr__(self, "_env", env)
        object.__setattr__(self, "n_reset", 0)
        object.__setattr__(self, "n_step", 0)

    def reset(self):
        object.__setattr__(self, "n_reset", self.n_reset + 1)
        return self._env.reset()

    def step(self, action):
        object.__setattr__(self, "n_step", self.n_step + 1)
        return self._env.step(action)

    def __getattr__(self, name):
        raise AttributeError(
            f"the agent may only call reset() and step() on the challenge environment (asked for {name!r})")

    def __setattr__(self, name, value):
        raise AttributeError("the challenge environment is read-only to the agent")


def _p(a, t):
    return a.ctypes.data_as(ctypes.POINTER(t))


class ChallengeRunner:
    def __init__(self, weights, seed=None, max_steps=None, verbose=False):
        self.lib = ctypes.CDLL(LIB)
        self.lib.nhg_set_callback.argtypes = [SEND, RESET, ctypes.c_void_p]
        self.lib.nhg_open.argtypes = [ctypes.c_char_p, ctypes.c_uint]
        self.lib.nhg_policy_step.argtypes = [ctypes.POINTER(ctypes.c_double)]
        self.lib.nhg_counters.argtypes = [ctypes.POINTER(ctypes.c_long)]
        self.lib.nhg_blstat.restype = ctypes.c_long

        raw = gym.make("NetHackChallenge-v0")
        self.actions = list(raw.unwrapped.actions)  # the published action set, read once
        # Instrumentation only, and only when --seed is given. NetHackChallenge
        # disables seeding by monkeypatching three methods on its Nethack object;
        # the object underneath still seeds. Scored runs never pass --seed, so they
        # play the unseeded random games the competition scored.
        self._pynethack = raw.unwrapped.nethack._pynethack if seed is not None else None
        self.env = OnlyResetStep(raw)               # from here on: reset() and step() only
        self.key2idx = {}
        for i, a in enumerate(self.actions):
            self.key2idx.setdefault(int(a), i)
        # The challenge action set carries Enter as carriage return (13) only. Our
        # macros emit newline (10) for the same keypress, and NetHack treats the two
        # identically at every prompt, so alias it rather than lose the keystroke.
        if 10 not in self.key2idx and 13 in self.key2idx:
            self.key2idx[10] = self.key2idx[13]
        self.verbose = verbose
        self.seed = seed
        self.episode = 0
        self.missing = {}
        self.keyhist = {}
        self.env_steps = 0
        self.done = True
        self.last = None
        self.ep_rows = []
        self.fatal = None
        self.out = None
        self.final = {}
        self.live = {}
        self._t0 = time.time()

        # keep the callbacks alive for the lifetime of the object
        self._send = SEND(self._on_key)
        self._reset = RESET(self._on_reset)
        self.lib.nhg_set_callback(self._send, self._reset, None)
        if self.lib.nhg_open(weights.encode(), 0) != 0:
            raise SystemExit(f"could not load weights: {weights}")

    # ---------------------------------------------------------------- plumbing
    def _push(self, obs, done, how_done=0):
        g = np.ascontiguousarray(obs["glyphs"], dtype=np.int16)
        bl = np.ascontiguousarray(obs["blstats"], dtype=np.int64)
        self.lib.nhg_fill(
            _p(g, ctypes.c_short),
            _p(np.ascontiguousarray(obs["chars"]), ctypes.c_ubyte),
            _p(np.ascontiguousarray(obs["colors"]), ctypes.c_ubyte),
            _p(np.ascontiguousarray(obs["specials"]), ctypes.c_ubyte),
            _p(bl, ctypes.c_long),
            _p(np.ascontiguousarray(obs["message"]), ctypes.c_ubyte),
            _p(np.ascontiguousarray(obs["inv_glyphs"], dtype=np.int16), ctypes.c_short),
            _p(np.ascontiguousarray(obs["inv_strs"]), ctypes.c_ubyte),
            _p(np.ascontiguousarray(obs["inv_letters"]), ctypes.c_ubyte),
            _p(np.ascontiguousarray(obs["inv_oclasses"]), ctypes.c_ubyte),
            _p(np.ascontiguousarray(obs["tty_chars"]), ctypes.c_ubyte),
            _p(np.ascontiguousarray(obs["tty_colors"], dtype=np.int8), ctypes.c_byte),
            _p(np.ascontiguousarray(obs["tty_cursor"]), ctypes.c_ubyte),
            _p(np.ascontiguousarray(obs["misc"], dtype=np.int32), ctypes.c_int),
            ctypes.c_int(1 if done else 0), ctypes.c_int(how_done))

    def _on_reset(self, _ud):
        # NetHackChallenge-v0 refuses seed changes by design: every game is a fresh
        # random one, exactly as the competition scored them.
        try:
            if self._pynethack is not None:
                self._pynethack.set_initial_seeds(self.seed + self.episode, self.seed + self.episode, False)
            obs = self.env.reset()
            self.episode += 1
            self.done = False
            self.last = obs
            self._push(obs, False)
            return 0
        except BaseException:
            self.fatal = sys.exc_info()
            traceback.print_exc()
            self.done = True
            return 1

    def _on_key(self, _ud, key):
        if self.done:
            return 1
        try:
            return self._key(key)
        except BaseException:
            self.fatal = sys.exc_info()
            traceback.print_exc()
            self.done = True
            return 1

    def _key(self, key):
        self.keyhist[key] = self.keyhist.get(key, 0) + 1
        idx = self.key2idx.get(key)
        if idx is None:
            self.missing[key] = self.missing.get(key, 0) + 1
            idx = self.key2idx.get(27, 0)          # ESC: the safest no-op the action set has
        obs, _rew, done, info = self.env.step(idx)
        self.env_steps += 1
        self.done = bool(done)
        self.last = obs
        bl = obs["blstats"]
        if not done and int(bl[20]) > 0:
            # NLE blanks blstats on the terminal step, so the last live reading is
            # the game's own score, taken from the challenge environment itself
            self.live = dict(env_score=int(bl[9]), env_turns=int(bl[20]), env_depth=int(bl[12]),
                             env_xp=int(bl[18]))
        if done:
            self.final = dict(self.live, end_status=int(info.get("end_status", 0)))
        how = int(info.get("end_status", 0)) if done else 0
        self._push(obs, done, how)
        return 1 if done else 0

    # ---------------------------------------------------------------- driving
    def run(self, episodes):
        out = (ctypes.c_double * 8)()
        cnt = (ctypes.c_long * 8)()
        polls = 0
        target = episodes
        done_n = 0
        while done_n < target:
            before = self.env_steps
            self.lib.nhg_policy_step(out)
            if self.fatal:
                raise RuntimeError("environment call failed inside the agent") from self.fatal[1]
            polls += 1
            if polls % 200 == 0:
                self.lib.nhg_counters(cnt)
                print(f"  t={polls} keys={cnt[0]} probes={cnt[1]} dr_probe_keys={cnt[4]} "
                      f"boundaries={cnt[5]} after_key={cnt[6]} refresh={cnt[7]}", flush=True)
            n = int(out[0])
            if n > done_n:
                done_n = n
                self.lib.nhg_counters(cnt)
                # out[] carries the env's running totals across episodes, so every
                # per-episode figure comes from the challenge env's own last reading
                row = dict(ep=done_n, plen=out[3], env_steps=self.env_steps,
                           keys=int(cnt[0]), probes=int(cnt[1]), maxnoprog=int(cnt[2]),
                           role=int(out[7]), **self.final)
                self.ep_rows.append(row)
                if self.out:
                    import json; self.out.write(json.dumps(row) + "\n")
                print(f"EP {done_n} score={self.final.get('env_score')} turns={self.final.get('env_turns')} "
                      f"depth={self.final.get('env_depth')} "
                      f"policy_steps={out[3]:.0f} env_steps={self.env_steps} "
                      f"probes={int(cnt[1])} maxnoprog={int(cnt[2])} "
                      f"end={self.final.get('end_status')} "
                      f"[{time.time()-self._t0:.0f}s]", flush=True)
                self.env_steps = 0
            elif self.verbose and self.env_steps - before > 30:
                print(f"  long macro: {self.env_steps-before} env steps", flush=True)
        return self.ep_rows


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True, help="policy checkpoint (.bin) from puffer train nethack")
    ap.add_argument("--episodes", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    r = ChallengeRunner(os.path.abspath(a.weights), seed=a.seed, verbose=a.verbose)
    r.out = open(a.out, "a", buffering=1) if a.out else None
    rows = r.run(a.episodes)
    import json as _j
    with open(os.environ.get("NH_KEYCENSUS", "/dev/null"), "w") as _f:
        _j.dump(r.keyhist, _f)
    if r.missing:
        print("keys not in the challenge action set:",
              {chr(k) if 32 <= k < 127 else k: v for k, v in sorted(r.missing.items())})
    sc = sorted(x["env_score"] for x in rows)
    print(f"episodes={len(rows)} median_score={sc[len(sc)//2]:.0f} mean_score={sum(sc)/len(sc):.0f}")
