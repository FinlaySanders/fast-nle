## Phase 4 — cohort-synchronous rollout (11 October, 06:30 UTC): ADOPT THE KNOBS
The trainer already has resident-group scheduling: `--vec.num_buffers=16` with `PUF_COHORT_BUFFERS=4 PUF_COHORT_STEPS=64` keeps 512 agents
(16 games per worker, the L2-fit cohort) resident for 64 horizon steps while the 4 buffers of the group pipeline inference among themselves.
Measured (incpack_v39 + mt7_pgo, fast protocol): 5M/2048 239,730 → 302,434 (+26%); 15M/2048 233,441 → 262,408 (+12%). Residency 64-128 steps
is best; 2-buffer groups lose at 15M; 1024-agent groups give half the gain. No engine or trainer code change; the knobs exist in src/pufferl.cu.
Physics and prototype: PHASE4_COHORT.md, PROGRAM.md "Stage 0/1/3" (curve: 16 games/worker 99.6 µs vs 64+ 128 µs; harness ping-pong +43% per core,
burst bound +70%). Follow-ups in order: (1) P/E-aware ownership (static ownership loses 13-25% wall to E-cores), (2) dynamic-batching inference
loop replacing the per-group barrier (PHASE4_COHORT.md Stage 3; trainer patch), (3) footprint toward 30 KB/game so two cohorts fit L2.
15M/512 (GPU-bound) unaffected; check queued (ablate_cohort512.json).

# Engine scaling program — handoff (11 October 2026, 03:00 UTC)

## Final stack: incstack2 → heat1 → invwt → fobj2 → misc1 → mt2 → mt3 → mt5 → mt7 (engines/mt7/source; PGO: engines/mt7_pgo)
Phase 3 (monster-turn restructure, bit-exact) added four layers, each full-gated (16,777,216 per-decision hashes, 0 differences) and
positive on an ABBA screen against the previous layer:
- mt2 species word: 43 species-only predicates as bits of a per-species 64-bit word built at library load (mons[] is const); 94 sites.
- mt3 forced inlining of the per-move helpers (distfleeck, set_apparxy, should_displace, m_digweapon_check, monhaskey, dochugw).
- mt5 m_move: ALLOW_MDISP already implies a monster on the cell (no MON_AT loads); recent-track avoidance gated by a 9-bit mask.
- mt7 floor-object index with byte coordinates: the SSE box filter rejects 16 objects per iteration.
Instructions per policy step 554.7K → 520.2K (−6.2%). Trainer landing (landing4, mt7_pgo vs misc1_pgo): 5M/2048 +1.6%, 15M/2048 +1.7%,
15M/512 0.0% (GPU-bound). Day total vs the morning stack ≈ +11.6% / +10.3% / +0.2%.
Dropped with full records in PROGRAM.md: mt1 terrain table (+3K instr), mt4 mask-structured query (+9K, −2%), mt6 perception snapshot (flat).

## Patches and binaries (handoff/)
- `engine_mt7stack_vs_fork_HEAD.patch` (119 files): complete engine delta against vendored fast-nle HEAD e7f656856.
- `engine_mt7stack_vs_retained.patch` (80 files): against the retained compact-state source.
- `engine_mt7stack_vs_misc1.patch` (6 files: hack.h, nh_ctx_gen.h, mon.c, mondata.c, monmove.c, globals.def): Phase 3 only.
- `libnethack_mt7_pgo.so` (sha256 7d29eab18c6d…): PGO build, quick gates 5/5; the trainer selects it via LD_LIBRARY_PATH.
- Generators: make_mt2.py … make_mt7.py (each reproducible from the previous layer); chain_step.sh runs a layer's full pipeline;
  ir_compare.py gives per-function instruction deltas; chain_fold.sh does PGO + landing + census.
- Verify twins: -DNLE_SPW_VERIFY (species bits vs macros), -DNH_MOVEMENT_MASK_VERIFY (reference neighbour query per call),
  -DNLE_HP_VERIFY (perception snapshot; mt6 only). Replay the corpus with harness_incpack/replay 512 32 0 32768 and expect 0 MISMATCH,
  obs b79eb25d93ca6d29, turns 115413681.

## Where the step's instructions go now (520K): monster turn ~380K (m_move 102K, mfndpos 89K, dochug 29K, movemon 22K, fobj scan 23K,
mcalcmove/mcalcdistress 14K, item-use scans 11K, minliquid 7K), observation/display ~60K, RNG ~15K, vision ~14K. What remains in the monster
turn is rule evaluation and RNG draws; the bit-exact levers left are ≤5K each. Larger steps need an RNG change (not bit-exact), rule changes,
or the temporal-locality scheduler (burst ceiling +67% at 2048).

## Before landing: the user's paired-seed learning A/B on mt7_pgo (from-scratch seeds, never resumed).

## Previous handoff (21:00 UTC, 10 October) — superseded stack, still valid notes
### Engine scaling program — handoff (10 October 2026, 21:00 UTC)

## Final stack of the cache ladder: incstack2 → heat1 → invwt → fobj2 → misc1 (engines/misc1/source)
Every kept layer passes the full every-action gate (512 games x 32768 steps, 16,777,216 per-decision hashes, 0 differences),
the five quick suites, and a verify-twin replay of the same corpus (old computation recomputed alongside, 0 mismatches).
Native replay deltas, each layer against the previous one (ABBA, 512 / 2048 agents):
- heat1: ctx fields re-sorted from the footprint: +0.8% at 2048, LL misses −2.9%.
- invwt: inventory weight cached (4 chain hooks + 75 owt writes): +2.8% / +1.1%.
- fobj2: floor-object index maintained in place on place/remove: +0.5% / +1.9%, LL misses −9.2%.
- misc1: hidden gold, deepest level and leash check cached behind a hero-inventory generation: +1.0% / +0.5% over two screens, LL misses −15.3%.
- Dropped after full verification: mload (monster load cache, flat), mbits (carried-type filter, flat), kbits (discovery bitset, −0.8% at 512 / +0.7% at 2048).
Cumulative native at 2048 over heat1's control: 234.5K → 243.8K (+4.0%); LL read misses per step 295 (retained) → 193 (misc1) in the 2048-share emulation.
The ladder is closed: the remaining footprint is layout (monster grid lookups ~25 lines/step), export, display and RNG, none of them a walk to cache.

## Patches and binaries
- `handoff/engine_misc1stack_vs_fork_HEAD.patch`: complete engine delta against the vendored fast-nle HEAD (e7f656856): 119 files.
- `handoff/engine_misc1stack_vs_retained.patch`: against the retained compact-state source (movement_object_presence): 80 files.
- `handoff/engine_misc1stack_vs_incstack2.patch`: only heat1 + invwt + fobj2 + misc1 (the work since the 15:30 handoff): 44 files.
  Highlights: tools/globals.def + include/nh_ctx_gen.h (heat, nh_fobj_lo, nh_invgen and the misc1 cache fields), include/hack.h
  (nh_set_owt / nh_invwt_dirty / nh_deepest_dirty, nh_fobj_placed / nh_fobj_removed), src/hack.c (inv_weight), src/monmove.c (index
  window), src/mkobj.c (hooks, nh_cont_dirty), src/vault.c (hidden_gold), src/apply.c (check_leash), src/dungeon.c (deepest_lev_reached),
  src/do.c (deepest invalidation), and the 30 files whose `X->owt = weight(X)` became `nh_set_owt(X)`.
- Generators (reproducible from the previous layer's source): make_mload.py, make_fobj2.py, make_misc1.py, make_mbits.py, make_kbits.py.
- Verify twins: -DNLE_INVWT_VERIFY, -DNLE_FOBJ_VERIFY, -DNLE_MISC_VERIFY. Replay the gate corpus with
  `NETHACKDIR=/puffertank/experiments/nethack-perf-20260917/dat NH_ZT_MASK=0 LD_LIBRARY_PATH=<verify build> harness_incpack/replay 512 32 0 32768 <actions>`
  and expect 0 MISMATCH lines, obs b79eb25d93ca6d29, turns 115413681.
- PGO: engines/misc1_pgo (build_pgo.py misc1, the campaign's recipe); the trainer selects the engine through LD_LIBRARY_PATH, so the
  landing comparison (nethack-24h ablate_landing3.json: incpack_v39 + incstack2_pgo vs incpack_v39 + misc1_pgo, 3 regimes, ABBA) needs no trainer rebuild.
- Landing results (trainer, fast protocol, ABBA, vs incstack2_pgo): 5M/2048 +3.0% (229.9K → 236.8K), 15M/2048 +2.6% (223.5K → 229.3K), 15M/512 0.0% (GPU-bound). With the morning's incstack2 landing: ≈ +9.8% / +8.5% / +0.2% for the day.
- The incremental-packer header patch and the trainer binary recipe below are unchanged.


## Phase 2 findings (22:30 UTC) — read before planning a rewrite
- Cold-start cost at 2048 games = 40% of the step (burst16 +67%). Attribution: named data structures 16 points (native warming census;
  fobj2/invwt/misc1 took ~4; a full data-layout rewrite can take at most ~12 more, realistically 5-8, zero at 15M/512); pages/TLB 0
  (page-touch census tonight, huge-page slab earlier); the remaining ~24 points are branch/instruction state and general L1/L2 residency,
  which only temporal locality (several consecutive steps of a game per core) can recover.
- The callgrind 2048-share footprint mis-ranks native cost once the large walks are gone: mload, mbits, kbits, invview were all flat on the
  CPU harness despite visible footprint lines. Size future work with the native warming method (movement_causal_tsc_20261009), never the footprint alone.
- Software warming one step ahead (lines, pages, both; owned-prefetch pipeline in harness_pf) is negative in every form: closed.
- Generators left for reuse: make_mbits.py, make_kbits.py, make_invview.py/make_invview2.py (invview2 adds view-dirty hooks at bless/curse/
  unbless/uncurse/set_bknown; never run). footprint_data.py classifies the line footprint by data structure.

## Previous handoff (15:30 UTC) — still valid

## What is ready
- `handoff/engine_incstack2_vs_fork_HEAD.patch`: the complete engine delta against the vendored fast-nle HEAD
  (e7f656856). It contains the entire uncommitted retained ladder (September lookup/SIMD/LTO, October locality work,
  compact structs + object pool, movement path) PLUS the new work: incremental glyph export (incexport3), dry-tile
  liquid fast path, immutable object metadata reads.
- `handoff/engine_incstack2_vs_retained.patch`: only the new work, against the retained source
  (compact-state engines/movement_object_presence/source).
- `handoff/env_nethack_h_incremental_packer.patch`: ocean/nethack/nethack.h against the live tree: the packer processes
  only rows the engine reports via `nle_glyph_dirty_rows()` (new exported symbol; the header declares it).
- `handoff/libnethack_incstack2_pgo.so`: PGO build of incstack2 (recipe: build_incstack2_pgo.py, same as the campaign's).
- Trainer binary with the packer: /puffertank/experiments/nethack-24h-20261009/binaries/incpack_v38
  (experimental stack source + env header patch; built with build_flags.txt + -DPUF_MUON_OUTPLACE -lcuda).

## Verification (all on recorded workloads)
- Quick gates (34 goldens, 26 fuzz, status, interleaved, shuffled): PASS for incexport3, incstack2, incstack2_pgo.
- Full every-action gate (512 games x 32768 steps, 16,777,216 per-decision hashes vs reference): 0 differences for
  incexport3 and incstack2 (the first version had 504 transient differences: underfoot patch left terrain over traps in
  the hero's previous cell; fixed by restoring that cell from the screen buffer).
- Native replay with the packer harness: observation hashes identical in every run (b97835c62aaf388f).
- Not covered: learning quality. Observations are bit-identical, so training behaviour should be unchanged, but the
  user's protocol (from-scratch paired seeds) still applies before promotion.

## Measured gain, fast protocol, each regime bracketed by controls (drift <= 0.2%)
| regime | current full stack (PGO retained + v37) | incstack2 PGO + incpack_v38 | gain |
| 5M/2048 | 216,554 | 230,884 | +6.6% |
| 15M/2048 | 211,190 | 223,387 | +5.8% |
| 15M/512 | 228,124 | 228,547 | +0.2% (GPU-bound, expected) |
CPU-only replay (vs non-PGO retained): +16% at 512 games, +12% at 2048.

## Also found this session (see REGIME_RESULTS.md, PROGRAM.md)
Phase-aware GPU defaults: gradient overlap + 32 connections and 4 Muon lanes help only when GPU-bound; collection-bound
regimes gain 2-3% with overlap off and 1 lane; NEVER overlap with the CUDA default 8 connections (-27%/-41%).
Fused small-matrix Muon +1.85% at 15M/512 (not bitwise). Minibatch 8192 +11% at 15M/512 only.

## Next candidates (PROGRAM.md step 2+)
B inventory-weight cache (~24 LL lines/step; 92 owt + 102 quan write sites -> generation counter + verify build);
D per-monster inventory-search cache (~16); E RNG state (ISAAC 4 KB, ~12) = user decision; inference-latency fused
forward (collectors wait 41% of cycle at 512 agents). Hardware counters: host sysctl kernel.perf_event_paranoid=4 blocks
perf in this container.

## Phase 4 close-out (11 October, 09:45 UTC): cohort knobs as pufferlib ini keys + what is left
PATCH: handoff/trainer_cohort_ini_keys.patch (against the 24h experiment trainer, nethack-24h-20261009/source: src/pufferl.cu + config/default.ini; 45 lines).
Adds [vec] cohort_buffers (0 = off) and cohort_steps (0 = horizon); PUF_COHORT_* env vars still override. Depends on the shared env pool (PUF_ENV_POOL,
src/env_pool.h) from the 2026-09-05 handoff — the repo trainer has neither, so land that first or carry both. Validated on binaries/cohort_ini (fast protocol,
5M/2048): control 239,009 / env-var cohort 298,293 / ini-key cohort 296,658 SPS, BATCH_PROOF rollout hashes identical across all three (44 epochs).
Recommended NetHack config (collection-bound regimes): num_buffers = 16, cohort_buffers = 4, cohort_steps = 64 (+26% at 5M/2048, +12% at 15M/2048, 0 at 15M/512).
Default stays off; changing the NetHack ini default is yours after the paired-seed learning A/B.
ANATOMY (PROGRAM.md Stage 4): the cohort gain is exactly the L2 per-game-step cost (135 → 100 µs); the pool is near saturation at 5M; forward latency is
launch/contention-bound (same for 128 and 512 agents), so dynamic batching is not a lever and the 15M/2048 regime is balanced (rollout 1.00 s vs PPO 0.98 s
concurrent, 0.84 alone). 5M/2048 remains collection-bound (rollout 0.86 s vs PPO 0.54 s): the only lever left is per-game-step CPU cost.
PER-STEP COST (FUNCTIONS_lines_mt7.txt, BRANCH_branch_mt7.md): 520K instructions, 5.4K branch mispredicts (5.9% of 91K), 1,910 I1 + 1,290 D1 misses per step;
≈ 38 µs instructions + 17 µs mispredicts + 12 µs cache per full-core step. Monster turn = 60% of instructions (m_move 97K, mfndpos 88K) and of mispredicts.
NOT DONE: scheduler patch (no slack to recover), dynamic-batching patch (not a lever), footprint-to-30KB program (L2 residency is already achieved at 16/worker;
further footprint cuts only pay through L1/I-cache misses, ~12 µs of ~67). Next engine program, if wanted: instruction/branch reduction in the monster turn
beyond the bit-exact restructures (which failed on the clock: mt4, mt8) — i.e. the "clean-slate" direction the rules constraint makes hard.

## Phase 4 addendum (11 October, 10:30 UTC): pool size, and two refuted scheduling hypotheses
POOL SIZE: under the cohort config, one pool worker per PHYSICAL core beats one per logical CPU. 5M/2048, 16x128 g4 s64, PUF_POOL_WORKERS ladder:
16 278.6K | 20 309.2K | 22 315.2K | 24 319.9K | 26 321.9K | 28 309.7K | 32 299.1K | 36 294.8K (single runs, ±1.2% repeat spread; rollout proofs identical).
Recommend 24-26 workers with the cohort config (+7% over 32 → 5M/2048 ≈ 320K, +34% over the 4x512 control). In the experiment trainer the pool size
is PUF_POOL_WORKERS, else num_threads/num_buffers*num_buffers − 12; in the repo it derives from vec.num_threads — map it so the pool has 24-26 threads.
15M/2048 check (32/24/20 workers) in PROGRAM.md when it lands.
REFUTED (keep for the record, knobs default off in trainer_cohort/source and handoff/trainer_cohort_knobs.patch):
- PUF_COHORT_ACTIVE (cap on buffers of a group in their env phase; "convoy" hypothesis): 2 → −6.2%, 3 → −4.6%, 1 → −63%.
- PUF_POOL_SPIN_US (workers spin before sleeping; "wake latency" hypothesis): 100 → −3.2%, 300 → −10.1%, 1000 → −22%; +sleeping submitters no better.
Why both lose: the "23% idle" measured per logical CPU in the cohort config is hyperthread idle — an idle sibling hands its physical core to the busy one,
so physical cores are near saturation and anything that fills logical CPUs steals from real work. The pool-size result is the same fact from the other side.
PATCHES: handoff/trainer_cohort_ini_keys.patch (45 lines: [vec] cohort_buffers / cohort_steps; the one to land) and handoff/trainer_cohort_knobs.patch
(115 lines: the same plus the two refuted knobs, for the record). Both apply with patch -p1 to nethack-24h-20261009/source.
15M/2048 pool-size check landed: 32 → 261,568 | 24 → 263,175 | 20 → 263,233 (neutral; proofs identical). Final recommended config for collection-bound
regimes: num_buffers 16, cohort_buffers 4, cohort_steps 64, pool workers 24-26 → 5M/2048 ≈ 320K (+34% over this morning's 240K), 15M/2048 ≈ 263K (+13%).
BATCH SCALING (11:05): with the cohort config SPS now rises with agents at 5M — 4096 agents 344,115 vs 2048's 320K (controls: 254K / 240K); at 15M both
sit at ≈ 263K (PPO-bound). The env side is batch-invariant; sweeps at 512 agents remain GPU-bound and gain nothing from engine or scheduling work.
SHAPES (11:25): 8192 agents x horizon 128 OOMs the 4090 (15.5 GB at 4096). Minibatch 32768 vs 8192 at 15M/2048: 259,036 vs 262K — PPO fell 18% but the
rollout (1.0 s) binds, so the 15M regimes are rollout-bound by the actor forward latency (0.79 ms per 128-agent forward at width 1024), not by PPO/Muon;
that forward is the next GPU-side target. 5M unaffected by minibatch (collection-bound). Minibatch is a learning hyper — the sweep decides the shape.

## Item 1 close-out (11 October, ~17:15 UTC): display / vision / observation-export pass
Four layers built, each verify-twinned over the 16.7M-step corpus and full-gated:
- dv1: per-call fast path for the two display refreshes of a monster move — null (its checks cost what newsym costs). Dropped.
- dv2/dv3: hero-global sensing hoisted per movemon — dv2 twin caught 154 mid-turn sensing changes (blindfold theft, form change); dv3 fixed the
  invalidation but the flag is dark for infravision/warning heroes → −3K instr, +0.5%. Superseded.
- dv4: sense bitmask + exact per-monster predicates; 97.7% of 172 move-time refreshes skipped; −8.3K instr (−1.6%); harness +1.3% @512, +0.35% @2048;
  TRAINER (PGO vs PGO, cohort regime): 5M/4096 +0.3%, 15M/2048 −0.2% → neutral. Patches: handoff/engine_dv4stack_vs_mt7.patch (10 files),
  engine_dv4stack_vs_fork_HEAD.patch (119), libnethack_dv4_pgo.so (sha aae28964d8c3bf77). Optional; the recommended stack stays mt7.
- dv5: lazy screen flush (print once per observation) — corpus obs hash identical but 3/34 goldens diverge: chars/colors/specials are print-time
  values in NLE, so eager-flush staleness is the reference. Dropped. LESSON: the golden gate is the bit-exact contract; the packed-obs hash is weaker.
Net: item 1 is worth ≈ 0 in production. Day total stands at the scheduling result (5M/2048 240K → 320K, 5M/4096 344-350K, 15M/2048 263K).
What is left for env speed is the monster turn (60% of instructions, 60% of mispredicts) under relaxed RNG-order rules, or a batched engine.
