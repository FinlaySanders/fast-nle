# Overnight optimisation — current state
Updated 2026-09-18T04:01:41.057339+00:00. Goal ACTIVE, deadline **2026-09-18 08:23 UTC**.

## Retained best
`best.json`: engine floor04+mask05+distant15+track40+gold60+PGO61 **plus recovered original shared pool with20workers+4submitters**.
- Combined matched rollout gain **37.62%** versus original engine/scheduler; original controls24.6075/24.6590s, candidate17.8997s, drift0.209%. `rollout83/summary.json`.
- Incremental pool gain repeated17–19% versus retained engine/WS. Thread-count control `scheduler84`: WS24 was10.97%slower thanWS32; pool20 was18.28%faster, drift0.167%. All32fullobservationblock hashes/RNG/loadedweights match.
- Loadedtraining **observed+5.90% incremental versusPGO61/WS**, controls24.3782/24.4048s versus23.0335s. Async trajectories differ; NOT exact-work or combined-original trainingclaim. Final combinedtrainingstilldue.
- Poolconcurrency: full32score4,472,832decisions/10,315,606keys; full512depth23,855,104decisions/56,604,291keys exact.60Kregionsregular,ASAN/UBSAN,TSAN pass. TSanstartupmappingfailures preserved; nonPIE fourthlaunch passed. `pool83-gates`.
- Reviewable enginepatch `retained-through-gold60.patch`; schedulerpatch `shared-pool83.patch` reverse/forward reproduces testedsource. `pool83-review/REVIEW.md`,manifest,source-manifest. Originalsharedpoolheader identical tooldprototype. **Centralcounter83variant rejected (slower)**.
- Engine immutable `pgo61/variant/libnethack.so`,sha5c302a62f31b21f449b093b985b66f93626c8281fdd90e1bea1f3150a8681274. Enginefrozen `pgo61-source`; all642mutableengine-sourcehashesmatch61. No enginechangesactive.
- Scheduler executable/source `pool83-control-source/puffer_pool`; builddefines PUF_ENV_POOL,PUF_PERF_LOAD,PUF_HEAD_SAMPLER (latterbaseline/benchmarkfeatures). PUF_POOL_WORKERS=20,4buffers512agents. OldWS executable `buffers42-source/puffer_rollout`. Maincublasuntouched, no pushes.

## Active work (only this compute)
**Session2545**: `python pool85.py`, fourfullrolloutarms pool20/pool16/pool24/pool20 on same verified poolbinary+PGO61. Changesonlysharedworker count. All32hashes/RNG/weightsrequired. Poll2545, inspect`pool85/summary.json`; keeponlymeaningfulgain, repeatifneeded. No otherlivebuild/replay/training; prior sessions66152,17677,11326,89007terminal.

## Next
1. Decidepool85. Ifworkerwinner validateappropriately; don'trerunallenginegatesforconfigurationonly.
2. ContinuefreshCPU/rolloutideas with5–10min screens. Keepalltimingsalone. Strongwinner83 validationextended~15min justifiedby17–19%incremental gain.
3. Reservefinal60–90min fororiginal-versus-best matchedrollouts and **combined** loadedtraining, patch/sourceaudit, finalreport by08:23. No earlygoalcompletion.
4. Source/commands/evidencein`ledger.jsonl`,`STATUS.md`; previousCURRENTarchived`CURRENT-before-pool83.md`.

## Recent rejected candidates / caveats
Hands74 nonPGO~1%gain lostwithmatchingPGO76. Line75 andappar77 score/depthtradeoffs,reverted. Helmet78bflat. Soa82 glyphSoA initialdepthgainnotrepeat,reverted. Clear81 packingstore had~1%replaygain butactualrolloutflat(-.32%,1.97%drift),parked. Mutableengineclean61.
Profile79 deepdepthenv199warm45700/512decisions: pack39%instructions. Profile80-O3onlydiagnostic: actualrolloutNVCCusesO2, notO3 (earliercommentarycorrected). Existingpack31/32SIMDactualrolloutno gains. Do notredo withoutnewmechanism.
Pool83workerimplementationusesmutex-protectedregionreadersleases; do notweaken lifetimeprotocol. Globalsharedwork makesworkersavailableacross4buffers. PreviousprototypewasnotretainedbeforecuBLASfix; nowrepeatablywins and isvalidated.
LastgoalturnPROGRESS: discoveredsharedpoolwin, validatedfullreplay+sanitizers+training+threadcontrol, retained, launched85.

## Update 2026-09-18T04:07:40.534362+00:00
Session2545 and55754 DONE. pool85/86 prefer24workers: +7.67/+4.54% vs20, allobs/RNGmatch. best.json remains verified20pendingfinaltraining/combinedrefresh. **ACTIVEONLYsession63005**: setup_pool87.py→pool87_fastgate.py→pool87_bench.py; exhaustedqueue readcheck before atomicclaim, same regionguards. Finalbenchmark uses24sharedworkers botharms. Noothercompute.

## 2026-09-18T04:13:47.906857+00:00
63005(87),59704(88),44750(profile90)DONE.87-.914% and88-.499%rejected, both60Kstress+all32obs/RNGpass. Originalpoolsource unchanged. Profile90 all32obs/RNG/weightsmatch: 8s capture coordinatorcondwait .012–.026s vs72 .69–1.04s; graph+copyenvelope56.34%vs42.19%, notkernelutilization, notspeedclaim. **ACTIVEONLY71394** pool89_train.py: originalengine/WS vs61/pool24 vsoriginal, loadeds70532epochs. Firstarmrunning. Scriptpreparedwhilebenchinactive; no competingcompute. Nextinspect89 then freshpool/CPUidea. Deadline08:23, still~4h.

## 04:16 update — combinedtraining complete
71394DONE. pool89-training/summary.json: originalcontrols26.6381/25.8989s;61+pool24 23.0302s; observedcombined+14.061%,control drift-2.775%;asyncages22843/23392/23681, notexactwork. **ACTIVEONLY30901** setup_pool91.py→pool91_bench.py; pins24workers tophysicalCPUs0,2,..14,16..31; coordinatorsunmodified,perthreadonly. Host92O3compiler scriptpreparednotrun. rollout93.py preparednotrun:original/61WS/61pool24/original directcombinedrefresh. Best.jsonstill20pending93. No pushes/mainchanges.

## 04:20 host92
30901affinity91DONE flat-.043% rejected.11537host92buildDONE; initialrawfatbincheckfailed solely builddirectory in nvlinktoolkitnote. DeviceSASS7MBbyteidentical; bothELFs allsections except .note.nv.tkinfo identical (host92-codecheck/device-sections.json). Source/configzerochanges. pyelftools unavailable; stdlibELF64sectionparserverified. Host92matchedrollout now launched separately, querysessionnext. Noothercompute. Host92notretainedyet.
**ACTIVEONLY62836 host92_bench.py**, samepool24+PGO61, O3hostflags versusO2. Pollthenkeep/reject. rollout93.py combinedoriginal-vs-pool24readyNOTRUN; finalcombinedtraining89done14.061%with2.775%drift. PreviousgoalturnPROGRESS: completedcombinedtraining, rejectedphysicalpin91, verifieddevice-equivalence92andstartedmatchedrollout.

## 2026-09-18T04:25:09.800440+00:00 — best promoted to24workers
93DONE. Directcombined47.6488%rollout,16.68184svs24.6164/24.64465controls,.1148%drift;all32obs+RNG+weightsmatch,meangameturn28589.95. best.json noworiginalsharedpool24+PGO61, binaries/sourceunchanged. Training89observedcombined14.061%,2.775%drift. **Allocator94justlaunched** unchanged24workerbinary+LD_PRELOADtcmalloc_minimal armvscontrols. Prefetch95.py preparedonly, boundedenginepointer-slotprefetch withauto-restoresource. Mainunchanged.
**ACTIVEONLY33865 alloc94.py**. Currentbest47.65%rollout/observed14.06%training nowrecordedinRESULTS_RUNNING.md. Needreview94thenprefetch95orotherqueue. ThisgoalturnPROGRESS:rejected92, directcombined93completed, promoted24workerbest, launched94. Deadline08:23unchanged.

## 04:30 update — allocator optional screen
33865initial94 and31983repeat94DONE. tcmalloc_minimal first+2.019%rollout/.104%drift, repeat+1.510%/.463%drift; all32obs+RNG+weightsmatch. Repeatpeak1978276KBcandidate vs1931340/1929620controls (~47MBextra). `alloc94-repeat2/summary.json`. First`alloc94-repeat`emptyattemptfailedmissing/usr/bin/time beforebenchmark; repairedusingos.wait4resourcecounts, recorded.
**ACTIVEONLY65294 alloc94_gates.py**: full32score and512depth exactrecordedreplay with tcmalloc, retained61engine, originalsharedpool28totalthreads(24workers+4submitters). Mustcheckcompletioncounts32/512aswellasexitcode beforepromotion.
`alloc94_train.py` PREPAREDnotrun: incremental24pool/glibc→tcmalloc→glibc loaded32updates; runifgatespass,thenreview(optionalruntimegain). Best.jsonunchanged47.65%rollout/14.06%observedtraining(noallocator).
`prefetch95.py` preparednotrun: insertonebuiltinpointer-slotprefetch inmfndpos beforeterrainchecks; comparetoPGO61sourceassert, backup/patch, engine_screen_alloc62.py baselinegold60; finallyrestoremutablemon.c. `setup_pool96.py`,`pool96_fastgate.py`,`pool96_bench.py` preparednotrun: no submitterhelps,24dedicatedworkers, originalguards. QueuePLANupdated. Mainunchanged. LastgoalturnPROGRESS:94repeatedwithmemoryproof,fullreplaystarted; no repeatedspeculativewaitrestart. Deadline08:23.

## 04:31 update
65294FULL allocatorreplayDONE:32/32score4472832decisions,512/512depth23855104decisions,10.3156M/56.6043Mkeys exact;countsverified independently. **ACTIVEONLY64124 alloc94_train.py** threeincrementalarms pool24glibc/tcmalloc/glibc, same61engine. 94notretainedyet. Onfinishsummarize3result.json beforedecision; thenprefetch95.py preparedandauto-restoresource. Best47.65%/observed14.06% unchanged.

## 04:34 allocator closed; engine95 active
64124DONE. `alloc94-training/summary.json` gain+.0301%, drift-.0272%, flat; controls23.01776/23.01150s vs23.00771s. Fullreplay32/512counts alreadypass. Allocator remains optional documented rollout-only1.5–2%/+47MB setting (`alloc94/REVIEW.md`), NOTbestdefault, no combinedclaim multiplication.
**ACTIVEONLY27231 prefetch95.py**: builds `prefetch95` onepointer-slot prefetch in mfndpos→exact32score/32depth warmup+20K path→ABA vsnonPGOgold60. Mutableengine-source/src/mon.c currentlyoneprefetch ahead of61. Scriptfinallyrestores originalfrommemory; backup `prefetch95-before-mon.c`,patchfile saved. Oncompletioninspectsummary andsourcehash; ifnoise/regressionpark, ifgainrepeat/freshmatchingPGO beforepromotion. No competingcompute. Next96no-submitterhelp scriptsready. Mainuntouched, beststill47.65%rollout/observed14.06%training. GoalturnPROGRESS: completedallocatorfullgates/training,documentedoptionaldecision,launched95. Deadline08:23UTC.
