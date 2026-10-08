# Current overnight state
Updated 2026-09-18T04:38:07.465492+00:00. Goal ACTIVE; deadline **2026-09-18 08:23 UTC**. Main `/puffertank/pufferlib` cublas/a8ad6448 untouched. Never push. Isolate timings from all other compute. Keep candidate budget5–10min, park15min. Final audit starts07:00–07:23.

## Retained best
`best.json`: engine floor04+mask05+distant15+track40+gold60+PGO61 plus original shared pool83, **24workers+4submitters**,512agents4buffers. This is relative to the frozen start-of-night baseline (already stream-safe cuBLAS and earlier engine work), not stock NLE.
- **47.6488% higher matched rollout throughput**,16.68184s vs24.61640/24.64465s controls,4,194,304measureddecisions,drift0.1148%. `rollout93/summary.json`; all32full-observation block hashes/initialGPU RNG/loadedweights match,meanworldturn28589.95. Block hashes are not full action-stream proof; separate fullreplays exist.
- **Observed combined loadedtraining+14.061%**,23.03018s vs26.63806/25.89886s controls,3,932,160timedsteps,drift2.775%. `pool89-training/summary.json`; async trajectories differ, notexactwork. Finiteweights/epochs/checkpointloadproof allpass.
- PGO61library `pgo61/variant/libnethack.so`,SHA5c302a62f31b21f449b093b985b66f93626c8281fdd90e1bea1f3150a8681274; frozen `pgo61-source`,642filemanifest.
- Scheduler binary `pool83-control-source/puffer_pool`,source same. `shared-pool83.patch`, `pool83-review/REVIEW.md`+source/patch manifests. Enginepatch `retained-through-gold60.patch`. No source change from20to24; two worker screens85/86 supported24, fullstress included24.
- Engine61 broad fullscore/depth, mutation diagnostics, historical-view goldens+fuzz audited. Rawhistorical15baselineexportexceptions documented, notrawpass. Pool83 full32score+512depth replay,60Kregionsregular/ASAN/UBSAN/TSAN passed; TSanhostmappingfailures preserved, nonPIE4thlaunchpassed. See earlierCURRENT-before-pool83.md for detailed enginehistory.

## Active ONLY
**Session10020**: setup_pool101.py→pool101_fastgate.py→pool101_bench.py. Boundedone-job crossbufferhelp every64own-done polls; ORIGINALpool83base, no97pause. Acquiresotherregionreaderlease beforeclaim/execution; releaseslease beforeowncompletionrecheck. Atomicclaim/done-release unchanged. Build→60Kstress→24workerABA matchedrollout. Noothercompute. 98197/29455 pause97terminal.

## Next
1. Inspect98,keep/reject. Ifwinner repeat thenloadedtraining. Do notretain basedoninitialarm.
2. `setup_wait98.py` + `wait98_bench.py` now active. UsesCUDA host wait blocking/yield vsdefault. LocalCUDA13 header documentsdefaultauto spins whencontexts<=CPUcount; newprofile90 shows~1sStreamSync/thread/8s. Setflags AFTER `cudaSetDevice(hypers.gpu_id)` increate path, notbeforetrainingfork. Preserveotherflags, assertrequestedactualmask, printCUDA_WAIT_POLICY. Same24pool+61. Sourceonlyisolatedpufferl.cu. Fourarms auto/block/yield/auto, full32hash+RNG+loadedchecks.
3. RemainingqueuePLAN: boundedpause completiononlyifinstrumentationjustifies, freshdepthengineprofile. Don'tredo counter/affinity/compiler rejectedideas. Reservefinal60–90minforcombinedrepeat/audit/reviewableartifactreport.

## Recent decisions
- Allocator94 installedtcmalloc_minimal: rollout+2.019% then+1.510%,drift.104/.463%; peakRSS~47MBhigher. Fullscore4,472,832decisions anddepth23,855,104/512streams exact, countschecked. Loadedtraining+.0301%flat,controls23.01776/23.01150vs23.00771. **Optionaldocumentedruntimeonly**,notbestdefault/no combinedclaimmultiplication. `alloc94/REVIEW.md`, `alloc94-repeat2`, `alloc94-gates`, `alloc94-training`. Initialrepeatattemptmissing/usr/bin/timefailedbeforebenchmark; repairedwithos.wait4ru_maxrss.
- Prefetch95 DONE27231: monster-slotprefetch beforeterraincheck; exact32score/32depthprefixpass;score-.246% depth+.044%noise. Rejected; scriptfinallyrestoredmon.c and exact61bytesverified. `prefetch95.patch` archived. Mutableengine-source currentlyunchanged61.
- Host92O3 flat+.0305%/.321%drift, rejected. GPU SASS byteidentical, allELFsections excludingnvlinkbuildpathnoteidentical; rawfatbin hashdiffonlypath. Nohost-O3retained.
- Physicalpin91 flat-.043%/.013%drift,rejected. Counter87-.914%,88-.499%,bothstress/hashpassbutrejected.
- Profile90 originalpool24 diagnostic: coordinatorcondwait .012–.026s vsprofile72 .69–1.04s/8s; GPUgraph+copy envelope56.34%vs42.19%,NOTkernelutilization orspeedmeasurement. All32obs/RNG/weightsmatch.

Prior goal turn PROGRESS:closedallocatorvalidation/training,started95. Currentturn95rejected/restored,96running,98preparedwithAPI-sourcecheck. Oldcurrent archivedCURRENT-before96.md. No goalcompletionbeforefinalaudit.

## 04:45 latest
98yield first+2.001%/.674%drift,repeat+.281%/1.513%drift;parkedbothyield/block,neitherretained,no98training(nextscriptpreparedNOTRUN). All32obs/RNG+flagschecked.
99freshdepthprofile DONE52682: env366warm26500+512,838worldturnadvances,1669keys; exactverify+source642hashpass. Profile99/Ir.txt:obs20.5%instructions,monmove3.64+mfndpos3.40%,vision_recalc3.52/vision_reset1.69%; noobviouslargeenginefastpath. Endpointepisode26depthnotassertedwindowdepth. Profilediagnosticnotbenchmarkgain.
100diagnostic must verifyall32digest/RNGagainstrollout93/pool83 beforeinterpreting. LogPOOL_WAIT atdestroy contains calls/measured/claim_ns/wait_ns/drain_ns/yields. Timesoverlapacrossbuffers; don'tsumascriticalwallcost. Basedonresultchooseboundedpause97 orotherhelpingstrategy,notblindspinrewrite. Retainedbest47.65%/14.06%unchanged. Prior turnPROGRESS98repeatparked,profile99completed,newtimingdiagnostic100started.

## Latest100→97
75975pool100diagnosticDONE. All32obs+initialRNGmatched93;16384calls/8192measured perbuffer confirmed. Summedover4coordinators claim39.124s, donewait12.983s, readerdrain.185s;63,130,940sched_yieldcalls inmeasuredsegment. ~24.8%ofcoordinatorenvphase summedtime isdonewait, NOTwall-criticalfraction. Instrumentationtimingsnotthroughputclaim.
Thisjustifies97boundedpauseinsteadofsyscallyieldeverypoll. Source100diagnosticsNOTincluded97. Keep/rejectfromtimingandhashproof, stresschecksmandatory. Ifgainrepeatthenfullreplay/sanitizerchecks/training; ifflatstopwaitmicrotweaks. Retainedbestunchanged. CurrentgoalturnPROGRESS:98repeatparked,99profiledone,100waitdiagnosticverified,97running. Deadline08:23.

## Latest97→101
97pause64parked: first+.681%/-.391%drift;repeat+.875%/-1.897%drift,closingcontrol16.5358s candidate16.5508. All32obs/RNG/stresspass but no meaningfulrepeatablegain; no97sourcepromotion.
101helper safety audit: neverholdsownmutexwhilehelping; leasesotherregionbeforeallreads, atomicallyclaimsonejob, incrementsdone-release, decrementsreadersunderlock/signalsquietbeforecheckingowndone. Relaxedprecheckavoidsincrementingexhaustedqueuesindefinitely. Crosshelp maydelaycoordinatorbehindoneotherlongjob, so timeit; don'tassumegain. Ifwinsmustfullconcurrency/sanitizer/replay+loadedtraining.
Next102CPU-onlydepthcross-workload comparison preparedasPLANidea, no scriptyet: old/shared-pool/depth/replay_pthread_ws exists; `pool83-gates/depth/replay_pool` currentoriginalpool. 512traces,20Kwarm+20Kmeasure. BaselineWS32total, candidatepool28total=24workers+4submitters;matchmeasuredsteps/keys/turns. FinalreportmustnotclaimscoreGPUgaintransfersunchangedtodepth.
PreviousgoalturnPROGRESS:97repeatclosed/parked,101prepared+safetyaudited+running,queueupdated. Bestunchanged47.65%rollout/observed14.06%training. Deadline08:23.

## 05:05 latest
101 rejected (noise);102 DONE, CPU-onlydepth engine+6.22%,combined+3.87%,not47.65%GPUscoreclaim. Noactivepriorjobs. pack103 next: SSE2 skips8cells only whenALLglyphs terrain; clearsobjectmemoryexactly, mixedcells originalpath. Separatecopiedheaders, immutablepool83/engine61. Fastreplay thennativeABAtestifpromising. Deadline08:23.

Session5489 active:setup_pack103.py pack103 thenpack103_rollout.py. 103CPUscore-.203%/drift.245%,depth+3.024%/drift.028%; both32streamsexact. Noothercomputejobs. Retainedbestunchanged.

## 05:07 latest / authoritative active state
103parked: CPU32score-.203%,depth+3.024%; actualGPUscore rollout-.836% at.862%drift,all32hash/RNG/loadpass. 20K randommaps/33.18M signedglyph oracle ASAN/UBSANpassed;memory+ordered256cappedlists identical. No source retained.
**Active ONLY session32749**: pack104.py, same103fastpath onlywhen(cell&7)==0. CPUexactprefix thenABAscore/depth. Ifmeaningful buildnativeusingsetup_pack103 adaptedimportpatch_pack104 andlabelpack104, benchmarkpack103_rollout adaptedpaths. Otherwisepark. Mutableengine-source61andpool83unchanged;maintrackedclean05:06.
5489/89386terminal. Beststill47.65%matchedscoreGPUrollout/14.06%observationaltraining. Depth102CPU-onlyengine+6.22/combined+3.87,alreadyledgerandRESULTS_RUNNINGrecorded.
After104moveon; no more waitmicrotuning. Need freshboundedidea/profilescheduler tails orengine hotspots. Finalauditstarts07:00–07:23/deadline08:23. Prior goalturn PROGRESS:closed101/102reporting,103testedCPU+GPU+oracleandparked,104running.

## Latest05:11
104terminal32749;32score/depthexact,score-.381%,depth+1.218%,parked (lessCPUgainthan103whichfailednative).
**Active ONLY session67802** setup_pool105.py →pool105_fastgate.py→pool105_bench.py. Originalpool83 scheduling;moveatomicdone ontoown64Bline,explicitposix_memalign64regionarray+zero; alignedfieldforcesstructsizeofmultiple64. Nootherchanges. Stressgate60Kregions thenmatched32blockrollout. Ifnoise reject; ifwin repeatthenfullsanitizer/replay/training. Noengine/productionchanges.
Goalturnprogress:104closed,rejected;105newcachecontentioncandidateimplementedandrunning. Retainedbestunchanged. Finalaudit07:00–07:23,deadline08:23.

## Latest authoritativeactive05:12
67802pool105terminal:separatecompletioncacheline-1.820%with1.102%drift;all32obs/RNG/load+60Kstresspass;rejected.
**Active ONLY session59534** setup_pool106.py→pool106_fastgate.py→pool106_bench.py. Originalpool83base,sleeperscountguardedbyp.mu,cond_waitincrements/decrementsundermu,ep_runalwaysincrements epochbutonlybroadcastsifsleepers>0. Destroybroadcastunchanged. No105alignment/nootherchanges. Ifwinsrepeat;noisepark.
Next prepared `rollout107.py`:1024agentsdirectoriginalengineWS/61WS/61pool24/original;existingbinaries,noedits. All32within1024hash/RNG/loadmustmatch;no512vs1024trajectoryclaim. LaunchonlyAFTER106terminal; no overlappingtimings/builds/profiles.
Goalturnprogress:105finishedandrejected,106implemented+running,107readynewcross-workloadscalecheck. Retainedbestunchanged47.65/14.06.

## Latest05:13
106terminal59534 rejected-.477%/.438%drift,all32hash/RNG/weights+stresspass.
**Active ONLY session84931** rollout107.py:1024agents directbefore(original14/WS32),61/WS32,61/pool24,after(original).32blocks,measuredlast16. Allload/RNG/32observationhashesmustmatchWITHIN1024. Nooverlap.
Next preparedworkers108.py: unchangedpool83+61,1024agents,24before/28/32/24after;32blockproof. Onlyrunafter107terminalandinspection. Thisisnewbatchsizecontext,notrepeating512workerscreens. No candidatecode promoted.
Updatedpool83-review/REVIEW.mdwithlatest24workernumbers anddepthCPUlimitation,old20workerevidenceretained. Goalturnprogress106rejected,107running,108prepared;bestunchanged. Finalaudit07:00–07:23/deadline08:23.

## Latest05:19 active
84931rollout107stillLIVEclosingoriginalarm. 1024agents before52.468919s,61WS47.762660s,pool24 44.676169s; finalcontrol/equalitypending. Measured8,388,608decisions. Do NOT reportfinalgainbeforeclosingchecks.
Prepared109setup_pool109.py/fastgate/bench: sampleper-taskcost+sortevery16callsorcount/startchange; sharedpool originalbase, no106. CostwrittenBEFOREdone-release, regionleaseprotectsarrays; qsortpermutationkeepsuniqueoffsets. Oldpriority10/34lost withindependentWS; oneboundedsharedpooltestjustifieddifferentcontext. NOTRUN.
Prepared110profile110.py highscoreenv40warm62000+512,fullprefixverifythenCallgrind,sourcehashcheck/debug61same.text. Highestscoreepisodeunder100Kendpointscore254262,turn187606,depth6,notcurrentwindowstats. NOTRUN.
Sequenceafter107inspect:108workers1024conditional,109newcostcandidate,110freshprofile. No concurrenttiming/build/profile. Prior goalturnprogressprepared109+110,reviewdocupdated,107verifiedlive.

## Latest05:20 authoritativeactive
107terminal84931:1024agents combined+17.41785%,enginealone+9.83014%,control drift-.04239%;32hash/RNG/loadproofallpass,meanworldturn28350.57625inallarms. Fullresultsledger/RESULTS_RUNNINGwritten. Notclaim512+47.65%transfers.
**Active ONLY25614** workers108.py (1024agents24workersbefore/28/32/24after, originalpool83+61). Inspectterminalresults+hashesbeforedecision; no build/profilingbesidetimings.
109costordering+110highscoreprofilingpreparedNOTRUN, nextafter108. No bestchange. Goalturnprogress107completedvalidated,108launched,109/110preparedsafetyreview. Deadline08:23/finalaudit07:00–07:23.

## Latest05:23
25614workers108confirmedLIVE, before45.353486s done,workers28active. Allarms1024agents,24/28/32/24workers,originalpool+61. Next109then110, no overlappingtimings/builds/profiles.
109pretestauditwrittenpool109-safety.md. Fastgate now original60Kvaryingsize AND extra60Kmostlyfixedsize/periodiczero toexercisepermutationreuseacross16-call samplinginterval. No109sourcebuilt/timingyet. Sourcearraysownedperregion,costwritesbeforedone-release,readonlypermutationleased,sort/reallocafterpriorreadersdrained.
110expectedcheap:priorprofile63deepwarm50Kwas15.4seconds;freshwarm62Knotexpectedlongframeworktask.
Currentgoalturnprogress:109safetyaudit+meaningfulmissinggateadded,108verifiedlive. Retainedbestunchanged.
