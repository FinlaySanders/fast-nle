# Warmed training profile

The score policy starts from the actual 4B s705 checkpoint. Both runs use the existing asynchronous training configuration: 512 environments, four buffers, 32 environment threads, original PPO and rewards, fresh optimizer. No trainer code was changed for profiling; `base.profile=1` enables existing NVTX markers.

Nsight captures CUDA graph nodes, NVTX and OS runtime calls for 15 seconds after a 120-second delay. Each run finishes 96 epochs / 25,165,824 steps. Checkpoint input hashes and final-step artifacts match. CPU sampling is disabled because hardware profiling permission was unavailable; this is a CPU API/GPU timeline, not a sampled CPU instruction profile.

| Capture | GPU kernel-active time | Fraction of 15 s | PPO kernel-active time | Inference kernel-active time | PPO/inference overlap |
|---|---:|---:|---:|---:|---:|
| Original/static | 13.220 s | 88.14% | 11.638 s | 4.983 s | 4.035 s |
| Optimised/work stealing | 13.934 s | 92.89% | 13.554 s | 4.588 s | 4.218 s |

GPU activity is the union of kernel intervals, not the sum of concurrent durations and not SM occupancy. Categories are assigned by matching CUDA correlation IDs to existing NVTX enqueue ranges. About 1.022 seconds of original GPU activity is unattributed, principally capture-boundary work; the optimised window has 0.009 seconds unattributed. Category times overlap and cannot be added. In the optimised capture, 91.9% of inference-active time overlaps PPO kernels.

The code confirms asynchronous collection: `rollout_start` begins the next buffer, `train_impl` trains the previous buffer, then `rollout_finish` joins collection. Thus reducing CPU simulation time need not reduce an epoch by the same fraction. This profile supports the GPU update path being the dominant constraint in this configuration, rather than the test simply using an untrained early-game policy. It does not establish that CPU simulation can never become limiting in longer games or other configurations.

GPU hotspots include matrix multiplies and action sampling. `sample_logits` accounts for 10.7% / 11.2% of summed kernel durations; the two largest GEMM variants together account for about 26.4% / 24.7%. These shares are diagnostic priorities, not exclusive wall-time percentages. Further work on the GPU path would be a separate change; protected trainer/algorithm files were not modified.

Profiler overhead and different stochastic trajectories prevent using these captures as a clean speed comparison. The separate unprofiled comparison measured +3.31% score-training throughput with +3.32% baseline drift; the controlled identical replay measured +39.77%.

## Run issues retained in the record

Nsight returned after capture while its trainer continued despite `--wait=all --kill=none`. The initial optimised launch therefore failed CUDA allocation. That failed run is preserved under `training-profile/optimized/` and is not analysed. The original capture had already finished. The successful retry waited for the exact original trainer PID to exit, and its trainer was likewise awaited explicitly.

The retry's final line-start-only parser counted 94 rather than 96 epochs because stdout/stderr interleaved two lines. A separate parser finds exactly epochs 0–95 and verifies the final checkpoint and original input-weight hash for both successful arms; see `training-profile/validated.json`. No training replay was repeated to repair a log parser.

Raw reports and SQLite data: `training-profile/original/` and `training-profile/optimized-retry/`. Analysis: `analyze_training_profile.py`, `training-profile/summary.json`. The failed initial launch and parser assertion remain in their logs.
