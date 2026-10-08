# Overnight results — provisional, goal still active

All comparisons start after the stream-safe cuBLAS fix. Model, policy weights, PPO, action/reward/observation semantics remain fixed. Deadline 2026-09-18 08:23 UTC.

| Candidate | Compared with | Score replay throughput | Depth replay throughput | Decision |
|---|---|---:|---:|---|
| Remove redundant floor-index invalidation in movemon | Original engine14 | +10.90% | +0.34% | Retained |
| Cache remaining SIMD matches in floor cursor | Previous row | +1.48% repeat | +3.85% repeat | Retained, combined gates passed |
| Empty-square scare prefilter | Previous row | -1.18% | -3.29% | Reverted |
| Hoist visibility predicate | Cached-match engine | +0.37% | +1.56%, drift4.38% | Parked, reverted |
| Profile-guided compilation | Cached-match engine, same source/LTO | +15.00% | +9.85% | Retained, broad gates passed |

Do not multiply these numbers or present them as end-to-end gains. Paired combined comparisons are required.

Loaded-policy training, same 3,932,160 measured steps:
- floor04 vs original engine14: 26.503 / 24.951 / 26.666 seconds ABA; +6.55% throughput, 0.62% control drift.
- combined floor04+mask05+PGO08 vs original engine14: 26.323 / 24.987 / 26.979 seconds ABA; +6.66% throughput, 2.49% control drift. No demonstrated extra training gain beyond floor04 yet.
- All runs finish32updates; loaded GPU master-weight dumps hash-match the fixed checkpoint; saved FP32 weights finite.

Fixed-policy rollout-only benchmark active (rollout11):512agents,4buffers,32workers,32blocks, first16 discarded,4,194,304 measured decisions. Separate from score certificates. Exact same source/binary across engine variants, proof of loaded weights captured. Initial game-age summaries match across completed arms. Final ABA result:combinedPGO08 +13.46% rollout throughput (21.785s vs24.716s control average),0.353%control drift. All32block step/game-age summaries identical across all5arms. floor04 +4.53%,mask05 +4.68% versus original.

Correctness for combined engine:
- Complete selected32score traces:4,472,832 decisions,10,315,606 keys.
- Complete512depth traces:23,855,104 decisions,56,604,291 keys.
- Raw observation snapshots match recorded reference.
- Raw historical goldens preserve the same15 baseline observation-export mismatches; not claimed to pass.
- Explicit historical-view adapter:34goldens, status, interleaved, shuffled,26fuzz pass; adapter is separate from raw export checks.
- Targeted floor-cursor734,156 comparisons include changing bounds, mutations, empty/overflow paths.
- Diagnostic floor-index consistency checks pass.
- Original late score env457 baseline exception remains documented; selected passing corpus is not a claim that every original trace passes.

Artifacts: best.json, ledger.jsonl, retained-floor04-mask05.patch, pgo08.py, pgo08/profiles, pgo08/profile-manifest.json, pgo08-gates/, pgo08-historical/, pgo08-training/.

Later screens: priority10 rejected (-10.90%depth); pause12 flat; scary09 parked(+1%score only); verified affinity13-inside rejected(-3.70%rollout); trap14 parked(-0.45%score/+1.11%depth). distant15 retained provisionally after repeat(+2.99%score/+1.90%depth vs non-PGO mask05); not yet included in best rollout/training figures.

PGO20 (adds distant15) passed samebroad gates and64heldoutstreams/workload. Heldout+2.75%score/+2.64%depth vsPGO08. New actual512rollout comparison: original24.403/24.649s,PGO08 21.800s,PGO20 21.559s. Combined13.77%,control drift1.01%. Increment1.12%overPGO08 modest/near drift; strongest evidence for sourcechange is repeated engine-only gain. All32blocks step/game-age summaries identical; GPUloadedproof hashesmatch. PGO20training pending.

PGO20 loadedtraining:26.335/24.673/27.096s ABA for3,932,160measuredsteps,observed+8.28%,control drift2.89%. Mean gameages23,343/22,113/24,143turns differ, so this is not an exacttrajectory or cleanincremental traininggain. All32updates finish,initialGPUweights match,checkpointweights/logsfinite. Frozen-policyrollout remains stronger identical-work throughput evidence.

## Further screens through 2026-09-18 01:20 UTC
The retained best remains PGO20. Gold-list unrolling, gas-region fast paths, neighbor-loop simplification, scare-function outlining, reciprocal RNG modulo, floor-prefix bitsets, and partial-training PGO were rejected or parked after exact replay and mixed/noisy timings. SIMD observation packing passed its oracle but produced no actual GPU rollout gain (-0.22%), so was parked too.

Eight scheduling groups versus four improved fixed-action CPU replay by 5.42% on score and 2.36% on depth at 512 games/32 workers. Both configurations passed full 25K-decision prefixes for all 512 games of each workload. However, GPU rollout with remapped identical initial RNG states produced different trajectories under eight groups; its raw +3.0% throughput is not a matched-workload result and is not retained. Four-group controls had identical observation hashes.

track40 is screening a conservative negative proximity cache for movement history. The unchanged original search still handles all potentially relevant queries. Its independent oracle passed 7,725,056 comparisons; game replay/timing is in progress.

## Movement-history cache (PGO44), 2026-09-18 01:36 UTC
Candidate only; loaded-training validation remains pending. The cache only rejects queries with no nearby history positions; all remaining queries use the original ordered search, including its distance-skipping heuristic.

- Non-PGO selected replay repeated: score +1.98% then +2.32%; depth approximately flat.
- Fresh matching PGO versus retained PGO20: selected score +3.11%; excluded-stream score +2.20% with 0.27% drift. Depth approximately flat.
- Actual frozen-policy 512-game rollout: original controls 24.418/24.563 sec; PGO20 21.523; PGO44 21.316 for4,194,304 measured decisions. Combined +14.89%, control drift0.60%. Increment versus PGO20 only0.97%, so treat cautiously. Initial RNG and32block-boundary packed-observation hashes match across all arms; full action-level correctness is independently supported by replay.
- Full selected32score and512depth recordings and raw-observation snapshots pass. Historical raw export retains exactly15 baseline exceptions; explicit historical-view adapter passes34goldens/status/interleaved/shuffled and26fuzz. No writable data symbol changes relative to PGO20.
- Expanded7,725,056-case tracking oracle includes stationary/walking/random histories and checks cache counts directly. Duplicate-position bookkeeping shortcut(track45) passed but was flat(-0.01%both), so reverted.
- Reviewable candidate-through-track40.patch changes6files. Reverse application matches original baseline source hashes; forward application matches frozenPGO44 hashes. Proof: pgo44/patch-check.json. No production edits or pushes.

huge43 independently tests2MiB context allocations atop the same non-PGO track40 source. Initial512game score replay passes. Timings and RSS comparison remain in progress; not retained.

PGO44 retained afterloadedtraining: original26.1846/26.3633seconds,candidate24.6530 for3,932,160measuredsteps (+6.575%,0.682%control drift). Mean gameages22,734/23,138/23,018 differ; no clean incrementaltrainingclaim. best.json andretained-through-track40.patch updated. Huge43 rejected: +1.13%score/-20.85%depth,~0.94GiBextraRSS, exact512+51225Kprefixespassed; allocatorrestored.

Further rejected screens: next-monsterprefetch46 (-1.20%score/-0.42%depth); equivalentloadthresholdarithmetic47 (-0.357%/-0.177%,5.57Moraclepass); AVX2floor48 (-0.404%/+0.402%,samecompilerflagscontrol,1.743Moraclepass). Allpassedselectedrecordedreplay andwere reverted. Newlate-gameprofile49 underway onretainedPGO44.

## 2026-09-18T02:11:55.083048+00:00 — second profile-led batch

Best remains PGO44: +14.89% fixed-policy rollout throughput versus the frozen original engine; +6.58% observed loaded-training throughput (different asynchronous trajectories, so not a matched-work claim).

Recent rejected screens, relative to the same non-PGO track40 source:

| Candidate | Score throughput | Depth throughput | Decision |
|---|---:|---:|---|
| gold51: scoped hero-gold absence | +1.37% | -2.21% | Reverted; depth regression |
| empty52: skip capacity division for empty inventory | +0.05% | +0.26% | Reverted; below control drift |
| worm53: same-monster prefilter | -0.96% | -1.61% | Reverted |
| inventory55: merge inventory export walks | +0.40% | +0.67% | Reverted; below control drift |

All four passed the selected score/depth replay checks. No broader correctness claim is made for rejected patches.

Depth profile54 (retry with existing harness-v3) covers two 512-decision windows inside an episode whose final maximum depth is22; depth is not asserted constant during the windows. Packing contributes35–36% of measured instructions, glyph gathering~6%, and vision recalculation~3.5–4%. These are instruction shares, not wall-time shares.

Current candidate glyph56 hoists the lazy screen-buffer pointer out of nle_copy_glyphs. Assembly confirms the per-cell buffer lookup is removed; timing is pending. Main cublas tracked files remain clean.

## 2026-09-18T02:24:35.357403+00:00 — broader compiler profiling

PGO59 used32 score+32 depth streams (20K warmup+20K measured decisions), compared with8+8 streams and20K+10K for retained PGO44. It passed both selected replays but did not improve timings: score -0.33%, depth +0.37% against1.05% control drift. Rejected; PGO44 remains best. Generation cost210.7s score+74.0s depth. No production source changes.

## 2026-09-18T02:44:36.752475+00:00 — gold absence cache retained

Gold60 caches only known absence of hero gold in a per-context cold byte, invalidated by inventory insertion/replacement/restore. Original scans remain for other chains. Diagnostic full replays and historical-view goldens/fuzz pass; raw historical exceptions unchanged. Source patch roundtrip and data-symbol audit pass.

Fixed-policy rollout: original24.665691/24.561175s, previousbest21.366242s, newbest20.802041s over4,194,304measured decisions. Combined+18.322%, incremental+2.712%, control drift-.424%. InitialRNG+32blockobs hashes match.

Loaded training: {"seconds": {"baseline-before": 26.320416453, "pgo61": 24.624667643, "baseline-after": 26.211749792}, "mean_turns": {"baseline-before": 23213.929333333333, "pgo61": 23267.148, "baseline-after": 23570.50866666667}, "gain_percent": 6.6657365829122295, "drift_percent": -0.41286072047547195, "measured_steps": 3932160, "caveat": "Asynchronous loaded-training trajectories differ; combined observation versus original, not exact work or an incremental gold-cache claim."}

## 2026-09-18T03:18:48.622381+00:00 — follow-up screens

Rejected allocation alignment, constant item-class checks, compact glyph buffers and deferred object-grid read (the latter lost under fresh PGO). Changed-row glyph cache parked for unconvincing gains. A compact-terrain moat shortcut failed depth replay; a diagnostic backtrace caught stale cached terrain during special-level generation, so it was reverted without changing the oracle. Pure moat-check reordering also lost.

A late8s Nsight rollout trace preserved all32observations, weights and initialRNG. Union of GPU graph envelopes+copies3.375s/8s; this is an envelope, not kernel utilization. CUDA waits occur on4coordinator threads; concurrent wait totals are not critical-path wall time. Benchmark-only removal of CUDA timing events was flat, within2.4%control drift, and was not adopted. Maincublas remains untouched; best still61.

## Retained result at 04:26 UTC — shared pool, 24 workers

The retained engine plus shared pool now completes the matched mature-policy rollout **47.65% faster in throughput** than the original engine/work-stealing baseline (16.6818 s versus mean24.6305 s; 4,194,304 measured decisions). Baseline drift0.115%. Every arm has matching loaded weights, initial GPU RNG and all32 full-observation block hashes. This is a direct combined measurement, not a product of separate speedups. See `rollout93/summary.json`.

Loaded mature-policy training shows **14.06% higher throughput** (23.0302 s versus26.6381/25.8989 s controls; 3,932,160 measured steps). Controls drift2.775%; learning trajectories differ, so this is an observational training comparison. See `pool89-training/summary.json`.

Use24sharedworkers+4submitting threads on this host. Code/library are unchanged from the fully checked shared-pool83/PGO61 stack. The20worker setting remains archived. Counter prechecks87, batched completion88, physical-core pinning91 and host-O3 compiler92 did not improve rollout throughput and are excluded.

## Cross-workload depth check (05:05 UTC)
CPU-only fixed-action replay of512depth streams,4buffers: engine changes alone improve throughput6.22%; engine plus24-worker sharedpool improves3.87%. Baseline drift0.078%. Eacharm measured4,096,000decisions and9,732,744keys, withmatchingworld-turnadvances. ThepoolisnotuniversallyfasterwhenallCPUbuffersarealwaysready. The47.65%resultaboveappliestothemeasuredscore-policyGPUrolloutpipeline,notthisdepthreplay. See `depth102/summary.json`.

## 1,024-game rollout check

The same retained stack improves matched score-policy rollout throughput by **17.42%** at 1,024 agents and four buffers. Engine-only improvement is **9.83%**. Original controls take 52.46892 / 52.44668 seconds, engine61 takes 47.76266 seconds, and engine61 plus pool24 takes 44.67617 seconds, each for 8,388,608 measured decisions. Control drift is -0.0424%. All 32 observation hashes, initial RNG states and loaded weights match within this workload. Mean world turn is 28,350.58 in every arm. See `rollout107/summary.json`.

The 512-agent and 1,024-agent trajectories differ; compare baseline versus candidate within each configuration, not across them. The pool advantage depends on workload and batch size.
