# Phase 4 — cohort-synchronous rollout (opened 2026-10-11, user: "implement the cohort architecture")

## Physics (measured)
- A policy step touches ~65 KB of a game's state (D1 misses x 64 B, final stack). Burst16 (16 consecutive steps of one game) is +67% at 2048
  games and +21% at 512: the cold-start factor is ~1.6x at 2048.
- Today's rollout is batch-synchronous: 4 buffers x 512 games; 32 workers; worker w steps games {i : i ≡ w mod 32} of every buffer, so it
  cycles through 64 games (4.2 MB) between visits to the same game. L2 on this i9-14900K: 2 MB per P-core (shared by its 2 hyperthreads),
  4 MB per 4-E-core cluster. Effective L2 per worker thread ≈ 1 MB. 16 games x 65 KB = 1 MB: ONE buffer's share per worker fits; four do not.
- Hence the regime gap: 512 games = 16 per worker (fits), 2048 = 64 (does not).

## Architecture
A worker owns cohorts (fixed game sets, 16 games at 2048/4/32). Rollout proceeds per cohort: step the cohort, send its observations to a
small inference call, step the same cohort again when its actions return. The learner still batches 2048 agents; the GPU sees many small
forwards; the core sees one or two cohorts' state repeatedly. Knobs: cohort size C (fit L2), cohorts alternated per worker A (1 = wait for
inference, 2 = ping-pong), inference latency L per cohort forward, burst length K (consecutive steps when actions are available).
Resident set per worker = A x C x footprint ≤ L2_eff is the design constraint; footprint reduction (Phase 2 layout) raises C or A.

## Stage 0 — sizing curve (running): step time vs games at 32 workers, 256..4096. Confirms the L2 model and the knee.
## Stage 1 — CPU prototype (replay_cohort.c, harness): recorded actions, so any latency model can be emulated exactly.
   Policies: A ∈ {1,2,4}, K ∈ {1,2,4,8,16}, L ∈ {0, 300, 600, 1000} µs, pinning on/off, cohort size via envs/buffers/workers.
   Correctness: identical per-game action order → identical final obs hash (b97835c62aaf388f for 2048/32/8192/2048).
   Output: SPS including idle, per-step CPU time → the achievable speedup surface. Decision: proceed to Stage 2 only if some (A,K,L)
   realistic for the trainer (L ≥ the measured small-batch forward latency) beats batch-synchronous by ≥ 10% at 2048.
## Stage 2 — GPU side: measure small-batch forward latency on the trainer (batch 16/32/64 with CUDA graphs, concurrent streams); the
   cohort design needs 64-128 forwards per round to overlap, or cohorts of 32-64 with partial warmth.
## Stage 3 — trainer patch: many small rollout buffers with worker ownership + per-buffer inference on streams (src/*.cu, env_pool.h);
   handed off as a patch (trainer infra). Gate: full every-action hash (scheduling-invariant) + the frozen-policy landing protocol.

## Stage 0/1 results (2026-10-11 ~05:30) — see PROGRAM.md tables
Curve: 16 games/worker 99.6 µs/step, 64+/worker 128 µs (plateau from 64 on): the knee is L2, not L3; scheduling prize at 65 KB/game = 1.29x
per step; cohort = 16 games. Matrix (bit-exact, hash b97835c62aaf388f): burst/wait bound +70..79% per core; ping-pong (A=2) at 300-1000 µs
latency = +38..43% per core with no idle; static ownership loses 13-25% wall to P/E imbalance; pinning irrelevant.

## Stage 3 design — trainer patch (dynamic batching), to be handed off
- Replace the 4 barrier-synchronized rollout buffers by a ring of cohort slots (16 agents each; 128 slots at 2048). Workers own cohorts
  (ownership table; 2 active per worker = ping-pong) and step a cohort as soon as its actions are present.
- Inference loop (CUDA graphs as today): every W µs (100-200) gather all cohorts whose observations are complete into one forward
  (128-256 agents typical), launch on a stream, scatter actions per cohort, mark ready. Cohort latency = W + forward.
- Trajectory buffers are per agent; the learner's batch assembly is unchanged; recurrent state is per agent as now.
- No global barrier: P/E workers run at their own pace; ownership weights (fewer cohorts per E-core worker) optional.
- Gate: identical per-agent action sequences under a frozen policy ⇒ the full every-action hash must match; then the fast-protocol landing.
Open measurement (Stage 2): forward latency vs batch (64/128/256/512 agents) with graphs on the 4090 — sets W and the expected regime.

## Stage 4 (2026-10-11 09:05) — where does the remaining rollout time go? (trainer anatomy before any patch)
Regime facts from BATCH_PERF (fast protocol, 44-epoch cohort runs): 5M/2048 rollout 0.862 s vs PPO 0.544 s concurrent (0.483 alone):
collection-bound by 0.32 s, ceiling ≈ 480K SPS if rollout matched PPO. 15M/2048 rollout 0.995 s ≈ PPO 0.984 s (0.842 alone; inference
contention costs PPO +17%): balanced; ≤ +18% left and only by shrinking the GPU footprint of inference together with rollout.
In-rollout rate at 5M/2048 = 262,144/0.862 = 304K steps/s with the worker's 16 games resident — the same footprint as the harness's
A1 burst bound (503K busy) and A2 ping-pong (355K busy). The 40% gap is one or more of: (1) pipeline bubbles (a buffer's env phase waits for
its forward + D2H; with 4 buffers per group the pipeline only hides latency while ≥2 regions are active), (2) region tails (last of 128 games
gates the upload; E-core stripes finish late; steals arrive cold), (3) group-boundary bubbles every 64 steps, (4) PPO sharing the GPU
stretching the forward. ablate_pooltiming.json (4 arms x 70 epochs, PUF_POOL_TIMING + PUF_ROLLOUT_DETAIL print at epoch ≥ 64) separates
them per buffer: claim_wall (submitter working) / tail_wall (waiting for the last worker) / drain, and model_ms / env_ms / copy_ms.
Decision rule: tail share of env wall > 20% → scheduling patch (stable ownership + P/E-weighted stripes, steal only at the tail);
model+copy per buffer step ≳ 2x env per buffer step → pipeline is GPU-latency-bound → dynamic batching / deeper pipeline;
both small → the engine's per-step cost is the lever (footprint toward two cohorts per L2, instructions).
