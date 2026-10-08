# Completion audit

Goal started 2026-09-17 13:54:49 UTC. New-iteration cutoff 15:54:49 UTC. No new optimisation iterations started after cutoff. Final report packaging follows validation.

| Requirement | Result / evidence |
|---|---|
| Profile mature score and depth workloads | Warmed score05, depth08, profile08release profiles; warmed training timeline added at user request |
| Isolate candidates; exact replay and baseline/candidate/baseline | Candidate results and decisions retained; weak/regressing changes rejected |
| Measure combined changes directly | `combined512-summary.json`: +22.63% depth, +39.77% score; baseline drift below 0.5% |
| Check both actual trained policy families | Frozen 4B depth and score checkpoints, matching trainer versions |
| Preserve current observations | V5 raw files/settings/complete coverage and fresh native equality pass |
| Broad correctness | Full512 depth; preselected full32 score; historical-view34 goldens + variants +26 fuzz; adapter scope explicit |
| Scheduler correctness | Graph-disabled native full trace/raw equality; all512 concurrent fixed-action gates pass |
| Floor cache edge cases | `cursor14-results.json`: 380,292 comparisons pass |
| Loaded training comparison | Actual GPU weight hashes; final-step artifacts; finite metrics; +3.50% depth, noisy +3.31% score |
| Profile training as requested | Both warmed Nsight captures analysed; asynchronous overlap documented; failed launch and parser issue preserved |
| Do not conceal baseline failures | Raw historical15 mismatches, original env457 bug, graph-enabled baseline nondeterminism documented |
| Do not conceal compiler checker difference | Original LTO checker fails8; exhaustive separate rename/ELF audit passes; no whitelist changes |
| Preserve production, stock, weights and inputs | `final-preservation.json`:624 hashed files match, production diff unchanged, stock/engine tracked clean,1024 recordings unchanged sizes/mtimes |
| Portable retained changes | Applied source patch proof with15 matching files; separate scheduler patches; compiler flags and hashes recorded |
| No pushes or production trainer edits | All experiment changes isolated; no commits/pushes performed |
| Deliver evidence | `REPORT.md`, `TRAINING_PROFILE.md`, `BUILD.md`, final artifact manifest |
