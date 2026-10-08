# Campaign completion audit

This is an outstanding-work audit, not a pass certificate. Deadline for starting iterations: 2026-09-17 17:59:32 UTC.

| Requirement | Evidence / remaining work |
|---|---|
| Preserve production dirty tree and stock NLE | Isolated source/worktrees and original patches exist; final hash/status comparison still required. No pushes. |
| Freeze engine, policies, configs, seeds, game data | manifest.json, frozen-input-hashes.json, data-hashes.json; final independent hash audit required. |
| Record actions, all keys, settings, rewards and termination | Original NHPERF1 corpora retained; NHPERF2 adds previously omitted auto-enhance refresh. Recorder equivalence evidence currently aggregate only. |
| Record engine and complete policy observations | Current traces store hashes, not full observation payloads. Equality checking exists; lossless observation recording remains a scope gap. Do not describe hashes as full snapshots. |
| Baseline replay | Complete depth passes. Full score fails at env457 on original and fresh libraries; BASELINE_MESSAGE_BUG.md preserves the uninitialised-message diagnosis. Preselected32 score streams pass; this is not a full-corpus pass. |
| Existing34 goldens, interleaved/shuffled/status/fuzz | Raw original current-export engine fails15 historical glyph goldens. Explicit stock-view adapter passes, but excludes eager refresh code. Both result sets must remain reported. |
| Mutable globals | Original appearance cache fails; generated immutable table candidate02 passes unchanged checker. |
| Separate startup/warmup/timing and late-game work | v3 harness separates intervals; representative full windows recorded. Final precisely bounded late-game and512-env timings remain. |
| Repeated uncontended ABA, both policies, memory | Current32-env comparisons running. Inspect fixed work, process snapshots, drift and RSS; mapped trace RSS is not engine heap alone. |
| One optimisation at a time | Frozen variants01/02/03 and incremental comparisons; no final acceptance yet. |
| Final combined live vec evaluation and short training | Pending after candidate selection. Correct20/21-head score/depth source must be used. |
| Durable reproducible commands and conclusions | Ledger, CLI and summaries exist; final report must retain failed gates, exact workloads, hashes and excluded scope. |

## Evidence update, 2026-09-17 12:08 UTC

The table above preserves the earlier audit; these entries supersede its pending statuses where specified.

- Full raw observation recording is implemented in harness-v4 and checked by `check_snapshots.py`, including policy observation/action mask and optional identify-screen tty chars. `fresh-snapshot-results.json` records new actual native inference for both policies, replayed with matching whole-file raw payload hashes on original and candidate04 engines. This closes lossless recording for these representative new runs, not retroactively for the old 14K-game corpora. The old corpora remain hash-only. Malformed/missing/duplicate snapshot rejection checks also pass.
- `v3-final-summary.json` contains completed54 balanced timing arms. `expanded04-final-summary.json` contains completed512-env comparisons with score explicitly limited to4000 decisions/env. `candidate04-window-results.json` contains completed incremental and six late-window comparisons; short late windows need cautious interpretation.
- `candidate04-integration.json` contains live native eval equivalence for both policies and baseline/candidate04 short training, all successful. This validates04, not any future combined scheduler.
- Production diff was byte-identical at the earlier recorded check (`working-tree-check.json`); final check still pending.
- Scheduler changes now occupy separate copied sources. WS native/replay correctness checks have passed, repeated timings and real training remain active. Shared-pool repair is queued behind WS and unvalidated; no scheduler accepted yet.
- Baseline full-score uninitialised-message failure and historical golden observation mismatch remain unresolved and explicitly reported. Neither successful prefix checks nor diagnostic stock-view adapters turn those gates into unconditional passes.

## Remaining final acceptance requirements after scheduler expansion

- Do NOT multiply individually measured engine and scheduler gains and call that an observed total. Run direct original-engine/static vs retained-engine/retained-scheduler ABA on identical fixed work after final selection.
- Earlier candidate04 training was random-initialised, not4B-loaded; it remains only a smoke check. Mature warm-start path must pass saved master-weight hash proof and inspect late interval game-state counters.
- Corrected replay must use persistent pthread submitters, not nested OpenMP; rejected partial nested results remain evidence of that harness limitation only.
- Native graph-enabled4buffer exact trajectory gate fails on WS baseline repeated against itself. Graph-disabled1/4buffer diagnostic parity and fixed-action engine parity have narrower scope; retain this limitation and do not claim unconditional native multi-buffer determinism.
- Engine05 is new and not validated. If retained, needs strict globals, full current-policy replay including all512depth/explicit score scope, historical stock-view gates/fresh fuzz, representative repeated ABA, and finalcombinedintegration. If rejected, preserve reason and failing examples; no need to pretend its incomplete gates passed.

## 2026-09-17T12:55:25.488325+00:00 snapshot completeness audit
Earlier check_snapshots_v5.py permits a missing trace suffix. New check_snapshots_complete.py defaults to full coverage and checks scalar field widths. test_complete_snapshots.py verifies complete input accepted and missing suffix, duplicate, truncation and empty rejected. MUST run complete checker on every native v5 observation file once available, require exactly8matching trace/obs/settings files per policy, then verify existing replay wholefile hashes. The queued v5 runner alone is insufficient for this stricter gate. Midcampaign-preservation.json confirms236frozeninputs unchanged and productiondiffidentical.

## 2026-09-17T13:09:00.033267+00:00 current evidence
V5native8envbothpoliciesandrawwholefile/settingsreplaybaseline+03finishedsuccessfully(proof.json16rowsperpolicy). Strictfullcoveragecheckerremainsqueued; do notinferitsgatepassed. Floor05allinitialselected32normal/diagnosticfull+enginepass; diagnosticall512depthalsoPASS. Larger512schedulingrunnerinitialcompilefailedrelativeinclude,repairedandqueuedafteractiveextendedfloor; oldfailurearchived. CAS sanitizerunexpectedmappingisruntimefailure,notraceorpass.
