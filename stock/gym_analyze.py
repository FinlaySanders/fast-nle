"""Summarise nhc_agent.py jsonl output (one file per worker, one line per finished episode).

Two traps this accounts for, both hit on 2026-09-11:
- `plen` is the env's running total across a worker's episodes (cumulative); `probes` and
  `env_steps` are per-episode. Ratios must use the per-episode delta of `plen`.
- Workers that draw short games finish more episodes, so a pooled sample taken before every
  worker has finished over-represents short (low-scoring) games. Report the equal-k pooled
  statistics (first k episodes of every worker, k = the smallest worker count) as the headline.
Also reports episode-1 vs later-episode medians: a gap there is a cross-episode state leak.
"""
import sys, json, glob, os, collections, statistics as st

workers = {}
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.jsonl"))):
    rows = [json.loads(l) for l in open(f) if l.strip()]
    if rows:
        workers[os.path.basename(f)] = rows
if not workers:
    print("no episodes"); raise SystemExit
counts = [len(v) for v in workers.values()]
k = min(counts)
allrows = [r for v in workers.values() for r in v]
eq = [r for v in workers.values() for r in v[:k]]

def q(v, p): v = sorted(v); return v[min(len(v) - 1, int(p * len(v)))]
def summary(label, rows):
    sc = [r["env_score"] for r in rows]
    print(f"{label:22s} n={len(sc):<5d} median {st.median(sc):7.0f}  mean {st.mean(sc):7.0f}  "
          f"p10 {q(sc,.1):6.0f}  p25 {q(sc,.25):6.0f}  p75 {q(sc,.75):6.0f}  p90 {q(sc,.9):6.0f}  max {max(sc):6.0f}")

print(f"workers {len(workers)}   episodes/worker min {k} max {max(counts)}   total episodes {len(allrows)}")
summary("EQUAL-K (headline)", eq)
if len(eq) != len(allrows):
    summary("pooled, all (biased)", allrows)

byidx = collections.defaultdict(list)
for v in workers.values():
    for i, r in enumerate(v):
        byidx[i + 1].append(r["env_score"])
if len(byidx) > 1:
    later = [s for i, v in byidx.items() if i >= 2 for s in v]
    print(f"episode 1 median      {st.median(byidx[1]):7.0f} (n={len(byidx[1])})   episodes 2+ median {st.median(later):7.0f} (n={len(later)})"
          f"   <- a gap here is a cross-episode state leak")

ratios, envr, turns, depth, noprog = [], [], [], [], []
for v in workers.values():
    prev = 0
    for r in v:
        dl = r["plen"] - prev; prev = r["plen"]
        if dl > 0:
            ratios.append(r["probes"] / dl); envr.append(r["env_steps"] / dl)
for r in eq:
    turns.append(r["env_turns"]); depth.append(r["env_depth"]); noprog.append(r["maxnoprog"])
print(f"per episode: env steps/policy step median {st.median(envr):.1f}   probes/policy step median {st.median(ratios):.1f}")
print(f"median turns {st.median(turns):.0f} (max {max(turns)})   median depth {st.median(depth):.0f} (max {max(depth)})")
print(f"max no-progress p50 {q(noprog,.5)}  p99 {q(noprog,.99)}  max {max(noprog)}   (challenge aborts at 10000)")
print(f"end status {dict(collections.Counter(r['end_status'] for r in eq))}")
ROLE = ["Arc", "Bar", "Cav", "Hea", "Kni", "Mon", "Pri", "Rog", "Ran", "Sam", "Tou", "Val", "Wiz"]
by = collections.defaultdict(list)
for r in eq: by[r["role"]].append(r["env_score"])
print("per role (equal-k): " + "  ".join(f"{ROLE[r] if r < 13 else r}:{len(v)}/{st.median(v):.0f}" for r, v in sorted(by.items())))
