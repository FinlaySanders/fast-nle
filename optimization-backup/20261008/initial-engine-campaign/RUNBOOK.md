# NetHack performance campaign

All paths below are relative to this directory. Production PufferLib and stock NLE are not modified. No patches are approved for deployment merely because a build or smoke test passes.

## Frozen inputs and verification scope

`manifest.json`, `frozen-input-hashes.json`, `data-hashes.json`, and `deboost-header-hashes.json` identify source, policies, game data, and dependencies. The score and depth policies have different architectures/action-head counts; always use their matching harness directories and `NH_DISC_SWAP` values (score 0, depth 1).

The original policy-produced recordings are `depth-record/` and `score-record/`. NHPERF2 recordings add an explicitly verified refresh omitted by the initial recorder. Use `depth-record-v2/` and `score-balanced-v2/` for engine-only replay. Do not use the incomplete `score-record-v2/` as a passing corpus. Legacy full-backend replay supports the original format; legacy engine-only replay does not.

Raw observation/settings recording is separate from the earlier hashed observations. `SNAPSHOTS.md` describes the earlier format; `harness-v5/` adds all engine scalar fields and complete native settings. Check `snapshot-v5-runner.log` AND its process and `harness-v5/*/proof.json` before claiming those checks passed.

## Tight iteration

1. Copy the next candidate into an isolated engine tree. Record the exact incremental patch and freeze the built library under `variants/`. Do not overwrite a library already used by a benchmark.
2. Run strict mutable-global checks and current-policy verification with the matching `harness-v3/{depth,score}/replay_vec verify` and `engine-verify` modes. Arguments are mode, thread count, warm-up decisions, measured decisions, then trace paths. Verification must cover the complete requested window, including warm-up.
3. Run historical golden, status-update, interleaved/shuffled and stock differential checks. Historical stock-view projection is a separately labelled diagnostic adapter; it does not erase raw baseline failures.
4. Run uncontended fixed-work baseline/candidate/baseline triples, at least three repeats, with identical CPU affinity, traces, and warm-up. `time_candidate05.py` is a concrete example of an incremental engine comparison, gated on prior correctness checks. Run only after checking the existing queue is terminal; it is not safe to launch it a second time into the same output directory.
5. Summarize completed triples with `summarize_timings.py`. Inspect baseline drift and work counts. Keep score and depth results separate, and compare the final combination directly instead of multiplying independent gains.
6. Validate the final combination with native policy evaluation and checkpoint-loaded short training. Merely passing `--base.load_model_path` to this trainer's training command does not load the policy; the isolated `PUF_PERF_LOAD` hook proves loading by saving and hashing the initial weights.

## Late-game measurement

First-episode or first-few-thousand-decision SPS is not a late-game performance claim. `late-window-manifest.json` identifies explicit windows from completed high-score/deep episodes. `late512/` replays 512 actual streams with 20,000 warm-up and 20,000 timed policy decisions per stream, reporting the actual game states at the measurement boundary. Resets mean decision index is not game turn. The small final-episode windows can be too short for robust timing and must be interpreted alongside longer batches.

Scheduler timing uses four persistent pthread submitters, matching the native trainer. The earlier nested-OpenMP submitter experiment was rejected as unrepresentative; do not quote its speedups. Raw replay excludes inference and optimization. End-to-end training measurements include those costs and are reported separately.

## Current evidence and exceptions

`CANDIDATES.md` and append-only `LEDGER.md` describe candidate decisions. Later entries supersede earlier pending notes. `COMPLETION_AUDIT.md` lists remaining acceptance requirements.

* Raw baseline historical goldens: 19/34 pass, 15 observation-export mismatches. Diagnostic stock-view goldens can pass without making this raw gate green.
* Full original score corpus: an uninitialised message in environment 457 is a reproduced baseline failure. `BASELINE_MESSAGE_BUG.md` preserves it. Passing the preselected 32 streams or bounded 512 prefixes is not a full-corpus pass.
* Four-buffer graph-enabled native inference is not repeatable even for unchanged work-stealing baseline. Graph-disabled repeats match; see `shared-pool/INFERENCE_SCOPE.md`.
* Initial training smoke comparisons were random-initialized. Corrected mature-depth tests prove checkpoint loading; see `TRAINING_SCOPE.md` and `warmtrain/summary.json`. Their observed games average about 900 turns and do not represent long score farming.

## Queue and stopping rule

Runner PID files identify individual processes, but are not evidence those processes are still alive. Inspect `/proc/PID/cmdline` and result artifacts. Never restart solely because an observation timed out. Never kill by a command-line pattern.

The campaign began 2026-09-17 09:59:32 UTC. Stop starting optimization iterations at 17:59:32 UTC, finish in-flight validation, and report verified gains and outstanding limitations. Preserve failed candidates and diagnostic evidence. No push is authorized.

## Final combined runner

`run_combined.py --engine candidate03 --scheduler ws --output /absolute/new/output` is prepared for direct engine+scheduler measurement, native evaluation and loaded-policy training. It must only run after the existing queue has drained and the chosen variant has passed its gates. It also supports candidate05-normal and the repaired pool, but not the later CAS pool variant. Syntax checked; no combined result yet. The script intentionally refuses to reuse an existing output directory.

The complete snapshot validator uses `snapshot_hash.so` to accelerate the same FNV byte hash. Rebuild with `cc -O2 -shared -fPIC snapshot_hash.c -o snapshot_hash.so`. The Python-only reference remains `check_snapshots_complete_python.py`; `snapshot-hash-proof.json` and the negative-format tests record equivalence checks.
