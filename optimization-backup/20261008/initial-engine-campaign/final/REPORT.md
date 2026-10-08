# NetHack optimisation campaign

Started 2026-09-17 13:54:49 UTC. New-iteration cutoff: 15:54:49 UTC. Optimisation iterations are closed. Final validation and profiling completed; packaging follows.

## Direct combined result

The retained engine and optional work-stealing scheduler were measured together against the frozen original production engine and static scheduler. These are direct measurements, not products of separate improvements.

| Recorded workload | Original before | Optimised | Original after | Throughput gain |
|---|---:|---:|---:|---:|
| 4B depth policy | 30.367 s | 24.769 s | 30.379 s | **22.63%** |
| 4B score policy | 147.672 s | 105.433 s | 147.060 s | **39.77%** |

Each arm replays all 512 streams on eight physical CPU cores, warming each stream for 20,000 policy decisions before timing the next 20,000. Each timed arm performs exactly 10,240,000 decisions. Depth advances 9,246,154 game turns through 24,390,564 keys; score advances 69,609,415 turns through 23,556,640 keys. Baseline drift is +0.04% depth and -0.41% score. Gains use the mean baseline duration divided by candidate duration, minus one.

These are simulation/observation throughput measurements, not whole-training speedups. Score games at the timing boundary average 27,715 turns, with 373/512 beyond 10,000 and a maximum of 150,611. Depth episodes reset much sooner: mean 998 turns, maximum 6,179, with 191/512 currently at dungeon depth 8 or deeper. The measured populations therefore represent the different workloads rather than assuming equal game ages.

Evidence: `combined512-summary.json`, `combined512-results.json`, `combined512.py`, `combined512-maps.json`, `final-hardware-libraries.json`.

## Loaded-policy training

Final loaded-policy baseline/candidate/baseline measurements completed successfully. GPU master-weight hashes matched the intended 4B checkpoints before rollout. Optimizers were fresh; the policy, PPO and reward configurations were preserved. Depth ran 4,194,304 steps per arm; score ran 33,554,432. Timings cover the latter half and include rollout, inference and PPO updates, excluding checkpoint writing and inline evaluation.

| Training workload | Original before | Optimised | Original after | Observed throughput gain | Baseline drift |
|---|---:|---:|---:|---:|---:|
| Depth, 256 environments, 2,097,152 measured steps | 11.285 s | 10.925 s | 11.328 s | +3.50% | +0.38% |
| Score, 512 environments, 16,777,216 measured steps | 154.252 s | 151.785 s | 159.377 s | +3.31% | +3.32% |

The score training estimate is not a precise isolated speedup: baseline drift is as large as the observed gain. Graph-enabled sampling has an existing reproducibility limitation, so trajectories differ even at a fixed seed. Mean score game ages were 20,185 / 25,931 / 23,441 turns across the three arms; maxima were 139,413 / 194,641 / 174,126. These are already mature-policy workloads, not randomly initialized early training. The controlled replay gains do not translate directly to whole-training gains in this configuration.

Evidence: `training-combined-summary.json` and `training-combined/results.json`. Warmed Nsight Systems captures show kernel activity during 88.14% of the original 15-second window and 92.89% of the optimised window. In the optimised capture, PPO kernels are active for 13.55 seconds, inference kernels for 4.59 seconds, and their overlap is 4.22 seconds. These durations overlap and must not be added. This supports asynchronous GPU work limiting the gain from faster environments. See `TRAINING_PROFILE.md`; profiler overhead means these are diagnostic timings, not additional speedup estimates.

## Retained changes

1. Export the glyph buffer in bulk before the unchanged mapping pass.
2. Generate an immutable canonical-appearance lookup at build time, replacing a mutable global cache.
3. Defer inventory gold counting until the branch that needs it.
4. Cache floor-object coordinates in original linked-list order, with live bounds, mutation invalidation and original-list fallback on overflow or mid-iteration mutation.
5. Use SSE2 to filter eight cached floor coordinates at once, keeping original selection order and scalar fallbacks.
6. Use SSE2 to filter object glyphs before calling the unchanged mapping function.
7. Build the same source with Release, LTO and `-fno-semantic-interposition`. Existing linking already uses `-Bsymbolic-functions`; no fast-math flags are added.
8. Optional, separate trainer patch: workers steal remaining environment work within the existing buffer/barrier structure. Each environment is stepped once; no PPO or reward changes.

The floor cache costs 24,592 bytes per environment, about 12 MiB for 512 environments. Compiler measurements apply to this Linux/GCC 13.3 build; they are not a portability claim. The two trainer patches target their respective frozen versions and must not be copied wholesale over the newer production trainer.

The cumulative source patch is candidate08; candidate14 is that identical source built with the retained compiler options. Portable source application was checked against fast-nle base `e7f6568568242745a7f7ebd8f730367123522cac`, and all 15 patched source files matched the tested tree.

## Correctness evidence and limits

* Current-format V5 raw observation files, settings and complete event coverage match the original for both policy families. Fresh native runs reproduce their saved observations and traces.
* Complete 512-stream depth replay passes: 23,855,104 decisions and 56,604,291 keys. A preselected 32-stream full score sample also passes: 4,472,832 decisions and 10,315,606 keys.
* The final concurrent 512-stream gates pass for both original/static and candidate/work-stealing before timing: 20,480,000 decisions per policy/arm, including warm-up.
* Native eight-environment, four-buffer runs with CUDA graphs disabled have identical full trace and observation hashes across original/static, candidate/work-stealing and original/static repeats.
* A documented historical-observation adapter passes all 34 old goldens, status-update variants, interleaved and shuffled runs, and 26 fuzz cases. It also enables explicit floor-cache checks. This adapter changes the observation projection, so it is not evidence for the current exporter; the V5 checks above cover that.

Known failures are retained, not hidden:

* Raw old goldens have the same 15 observation mismatches on original and candidate, reflecting the newer appearance export. They are not reported as passing.
* Original score stream 457 fails at decision 131,399 due to an uninitialized message buffer in the original `mdamagem` gold-stealing path. The preselected full score subset excludes that stream; the all-512 test uses a 40,000-decision prefix before the known failure. No game-behaviour fix was folded into this performance campaign.
* Default CUDA-graph native sampling is not repeatable on the unchanged baseline. Exact native scheduler checks disable graphs. The final training comparison uses its existing normal configuration and reports this limitation.
* The original mutable-global checker rejects the LTO build: seven GCC `.lto_priv` symbol renames plus `DW.ref.__gcc_personality_v0`. Its failure log is preserved. A separate exhaustive audit matches the renamed objects to the existing whitelist and baseline sizes/sections, and verifies the remaining eight-byte object is a relocation to GCC's exception personality. The original checker and whitelist were not edited. Candidate08 without these compiler options passes the original checker.

Evidence is in `validation14-audited`, `historical14`, `native-combined`, and `lto-global-audit/proof.json`. The final package retains the original checker failure as well as its explanatory audit.

## Rejected changes and attribution

Weak or regressing candidates were rejected: broader floor buckets, terrain-packing SIMD, a pointer-hoist variant, extra displacement/scare guards, and LTO alone. Local binding without LTO was measured but was slower than the chosen combined compiler build. The older shared-pool/CAS approach was not retained.

Profiles start after replay warm-up; mature score profiling found floor-object scanning and monster movement dominant. Individual and incremental results remain in the experiment directory. They use different sampled populations and are not combined arithmetically with the final all-512 result.

## Preservation and delivery

All work is isolated under `/puffertank/experiments/nethack-perf-20260917`. No production edits, commits, pushes, reward changes or policy architecture changes are part of this campaign. Preservation checks pass: 624 hashed files match, the production working diff is byte-identical, stock NLE and the production engine have clean tracked status, and all 1,024 original recordings retain their indexed sizes and pre-campaign modification times. No pre-campaign whole-corpus SHA manifest existed, so recording preservation is not described as retroactive hash verification. The final candidate also passes 380,292 explicit floor-cursor edge-case comparisons. Portable changes and evidence are packaged in `final/`. `BUILD.md` documents reproduction, source base, compiler flags and the optional scheduler patches.
