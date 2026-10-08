# NetHack performance campaign

Start: 2026-09-17 09:59:32 UTC. Stop new optimisation iterations at 17:59:32 UTC.
Everything here is isolated from the production PufferLib checkout and stock NLE.

## Workloads

`depth-record/`: 512 simultaneous environments, 14,111 completed games, 23,855,104 policy decisions and 56,604,437 engine keys. Maximum completed depth29; 1,290 games reach depth20+. Current 21-head depth4B model with replacement discovery enabled.

`score-record/`: 512 simultaneous environments, 14,035 completed games, 71,565,312 policy decisions and 161,829,715 engine keys. Maximum score288,300; 11,003 games exceed10,000 turns. Original 20-head score4B model with its matching historical policy/backend source. Maximum depth13.

The JSON command manifests and trace headers preserve seeds, reward/config values, role options, and engine settings. Each environment's complete chronological stream includes resets, policy actions, expanded keys, raw engine observation hashes, complete packed policy observation/mask hashes, rewards, terminal flags, and episode statistics. These are regression hashes, not lossless stored screenshots. The binary format uses native little-endian 64-bit Linux struct layout and is documented in `source/ocean/nethack/perf_trace.h`.

## Replay

`replay_vec` uses depth source; `score/replay_vec` uses score source. It performs no neural inference. Replay starts at the beginning of each environment stream to preserve reset history, rather than assuming arbitrary episodes are independently restorable.

```
NH_DISC_SWAP=1 NETHACKDIR="$RUN/dat" LD_LIBRARY_PATH="$RUN/engine-baseline/build" \
  "$RUN/replay_vec" verify 8 0 1000000 "$RUN/depth-record/env00257.trace"
```

Modes `verify` and `time` execute the complete C observation/action/reward backend. Verification compares the keys and every recorded hash/reward/terminal event. Timing parses the same stream without computing hashes. `engine-verify` and `engine-time` bypass action expansion and policy observation construction, executing recorded engine keys and refreshes; only engine observation hashes are checked in engine verification. These engine-only modes therefore do not validate policy observations or rewards.

Initialization and configurable warmup are measured separately and excluded from throughput. Episode resets occurring within the measurement window remain included. Environments run round-robin with static OpenMP assignment. `positive_turn_advances` currently omits advances across an episode-reset boundary; it is a lower-bound diagnostic, not an exact world-turn count. `measured_steps` is the number of policy decisions, not engine keystrokes.

`time_candidate01.py` runs three baseline/candidate/baseline triplets for each workload, pinned to eight physical cores, after verification processes exit. Its selected streams mix high scores, high depth and ordinary env IDs. Warmup20,000 decisions per env is excluded; the next20,000 decisions are measured. Selection does not imply every measured decision is late-game. Full512-agent and precisely bounded late-game windows remain required before final acceptance.

## Historical correctness gates

The unmodified current engine fails historical stock glyph hashes and the mutable-global gate. Do not report otherwise. The two intentional observation-export changes responsible for stock mismatches are appearance canonicalisation and eager glyph refresh. `engine-stock-view` is a diagnostic adapter restoring only the old observation projection. It passes all34 historical goldens, !status_updates variants, interleaved/shuffled multi-env replay and26 fresh stock differential fuzz cases.

The adapter removes eager refresh, so its passes do NOT test a candidate optimisation of eager refresh. Current-policy traces independently cover that interface. Raw failures, adapters and exact test logs are preserved; goldens are not regenerated to hide failures. The mutable gem_canon cache remains an unresolved baseline issue.

## Acceptance

No candidate is accepted solely on smoke tests or instruction counts. Require full relevant replay verification, complementary historical/fuzz gates with limitations explicit, and reproducible uncontended paired timings for both models, with memory recorded. Final combined code also needs live vec eval and short training. No source changes are pushed.

## Complete refresh coverage (NHPERF2)

A long score trajectory exposed an omitted out-of-band observation refresh in automatic skill enhancement. The original full-backend replay was correct because it executed that helper; engine-only replay omitted the refresh and eventually compared a stale glyph at a partial observation boundary. The frozen baseline reproduced the same failure. `check-refresh.log` and `check-v3.log` demonstrate that adding the operation fixes the full139,776-decision stream, without changing a keystroke.

`harness-v3/{depth,score}/replay_vec` supports the complete NHPERF2 event stream. Its full-backend verification can read an original NHPERF1 stream with `NH_PERF_AUGMENT=<new directory>`: every original event must still match, and the formerly omitted refresh hashes are inserted into a new stream. Original files remain untouched. New files use exclusive creation. Engine-only replay rejects NHPERF1 rather than quietly omitting work. Completed converted corpora are marked `VERIFIED_ORIGINAL` only after successful full verification. Conversion is additional evidence about the baseline, not a replacement for the historical stock goldens.

The v3 reporter scans the measured trace interval after the timer stops to count actual engine keys. It reports both decision and key throughput; these include the same reset/probe/refresh costs that occur in that interval. Table-generation and gold-counting candidates are frozen separately under `variants/`, preventing later builds from changing an in-flight test.

## Reusable command

`replay_workload.py` selects a frozen balanced, all512-env, or final-episode window and records the exact command, environment and binary hashes. Example from this directory:

```
python replay_workload.py depth verify --library "$PWD/variants/candidate03/libnethack.so"
python replay_workload.py score time --corpus "$PWD/score-balanced-v2" --library "$PWD/variants/candidate03/libnethack.so"
python replay_workload.py score engine-time --corpus "$PWD/score-balanced-v2" --selection late --threads 1 --library "$PWD/variants/candidate03/libnethack.so"
```

Run timing commands without competing jobs. The `late` selection uses the final512decisions (or the whole episode if shorter) of the highest-score/highest-depth completed episode; it is a reproducible episode-tail window, not a claim that every step remains at maximum depth. `--warmup` and `--steps` can override the window. Verification checks the warmup as well as the measured segment. The data directory is now a byte-identical frozen copy, independently hashed in `data-hashes.json`.

## Full score baseline failure

The all512 score pass is not green: environment457 produces a transient uninitialised-name message on the unchanged engine. See BASELINE_MESSAGE_BUG.md and the preserved failing trace. Its partial score-record-v2 output is not a usable completed corpus. The original preselected32 timing streams are independently converted into score-balanced-v2; using them requires an explicit --corpus argument, and the scope text is saved in each result. --selection all requires512 files and does not accept the smaller selection. No message hash is masked or normalised in accepted verification.
