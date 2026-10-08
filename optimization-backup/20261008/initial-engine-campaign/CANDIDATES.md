# Candidate ledger

All libraries are frozen under `variants/`. None is applied to production or finally accepted yet.

| Candidate | Incremental change | Current correctness evidence | Performance evidence |
|---|---|---|---|
| 01 | Copy display glyphs in bulk before the existing conversion | Full backend depth1.49M + score4.47M decisions pass | Three32-env ABA pairs: median depth+7.36%; score−0.31%, effectively unchanged |
| 02 | Generate immutable appearance table at build time | Strict globals passes; full depth23.86M and balanced score4.47M pass | Three ABA repeats vs01: depth+2.55%,score−0.18% (flat) |
| 03 | Count gold only for the xorn branch that uses it | Strict globals, balanced full depth+score, and stock-view historical/fuzz gates pass | Three ABA repeats vs02: depth+0.32%,score+5.38%; cumulative vsbaseline depth+8.59%,score+5.19% |

The raw historical stock golden hashes fail on the unchanged production baseline:19pass,15fail. Appearance canonicalisation and eager map refresh explain those differences. The explicitly labelled stock-view diagnostic adapter restores that old observation projection. Its golden successes do not validate eager-refresh code, which is checked separately against current-policy traces. The original mutable appearance cache fails the strict global check; candidate02 removes it rather than modifying the whitelist.

Old engine-only score replay failed because the recorder omitted a refresh in automatic skill enhancement. The frozen baseline reproduces that failure; adding the missing operation fixes it. NHPERF2 conversion verifies every original event and adds those refreshes. Complete-format engine-only checks are queued before the next timing comparisons. Old full-backend checks and timings execute the helper and are unaffected.

Broader512-env timings, precisely bounded late-game comparisons, final live vec evaluation and short training remain outstanding. Instruction profiles suggest floor-object indexing as a next candidate; it has not been applied.

Full score augmentation later exposed an independent uninitialised-name baseline defect in environment457. Original/fresh libraries and both full-backend replay versions reproduce it. This is preserved as a failure, not waived by the missing-refresh repair. Timing work uses the same32 streams selected before the defect was discovered; it does not establish a full-score corpus pass. See BASELINE_MESSAGE_BUG.md.

## Later candidate status (supersedes earlier pending notes)

04: non-object glyph early return passes current-policy replay and live native/short random-init training. Incremental balanced gain over03 only+0.23%depth/+0.41%score, too small to accept as a demonstrated speedup. Broader/late comparisons completed; do not attribute cumulative03benefits to04.

05: ordered floor-object cache on03 (excluding04) prepared under engine-floor. Cold24KiB/context; overflow and mid-search mutation fallbacks. Added explicit clear_level_structures invalidation after finding the alternate level.objlist spelling. No build/gate/performance result yet. Validation queued behind scheduler tests.

Scheduling: WS eight-core first4000decision replay gains+10.38%depth/+14.45%score;32-thread results have drift. Multi-buffer nested-OMP timings rejected as unrepresentative (actualnativeusespthreadsubmitters); corrected persistent-pthread replay in progress. Sharedpool fixed-action depth verification and concurrency sanitizer stress pass; nativeonebuffer matches; graph-disabledfourbuffer matches. Graph-enabledfourbuffer WSbaseline itselfnondeterministic, failures preserved. No final scheduler acceptance pending mature-state timing/integration.

### 2026-09-17T13:02:47.549767+00:00 candidate05 diagnostic gates
Selected32depthand32score complete full-backendANDengine-onlyreplayspassedwithNLE_FOBJ_VERIFY enabled. Scorecovers4,472,832decisions/10,315,606keys. Normalbuild/replays,full512depth,historicalprojectionandtimingremainpending. Contextdelta24,592bytes/env(measured),about12MiBfor512. Noperformanceacceptanceyet.

### 2026-09-17T13:11:38.996029+00:00 candidate05 broader gates complete
Full512depthdiagnosticANDnormalpass. Explicitstock-viewdiagnosticadapterall34goldens,statusoff,interleaved,shuffledand26fresh-stockfuzzreplaysPASS. Current-policyselected32scorebothnormal/diagnosticfull+enginepass. Rawhistoricalbaseline15mismatchesandfullscoreenv457failureunchanged; nofullscoreclaim. Initialandbroader05validationcomplete,performancepending. Portablecompletepatchprovenonbasee7underpatch-review/. Repaired512schedulerdriverall3depthbuildspass,validationactive.
