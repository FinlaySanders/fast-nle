# NetHack overnight loop — current handoff

Last updated: 2026-09-18 05:29 UTC. Goal is ACTIVE.
Start: 2026-09-17 22:23 UTC. Deadline: 2026-09-18 08:23 UTC.
Start final verification / packaging between 07:00 and 07:23.

## Active computation

No experimental compute active. User-requested fresh profile completed:
`PROFILE_CURRENT.md`,profile112node trace andprofile113lower-overheadphase trace.
Both32obs/RNG/weights proofs match. CPUenv76.96% coordinator time;29.42%wall
all4buffers simulating with no graph/copy active. Node trace has measurable
launch overhead; use113forCPUphase attribution,112foractualkernelbreakdown.
Session47633/29465/10374terminal (113stats timestamp processing error recovered
byreadingSQLite directly). No production source change; goal remains active.

## Retained implementation

`best.json` is authoritative. Engine61 plus ORIGINAL shared pool83, 24 workers
and4 submitters. No candidate since83 has changed the retained code.

- Engine: `pgo61/variant/libnethack.so`, SHA256
  `5c302a62f31b21f449b093b985b66f93626c8281fdd90e1bea1f3150a8681274`.
- Engine source: `pgo61-source`,642-file manifest. Mutable `engine-source` restored
  to the same source; verify before using it. Changes are floor-index invalidation,
  cached SIMD matching lanes, distant scare check, movement-history negative cache,
  hero-gold absence cache, and matching PGO.
- Pool binary: `pool83-control-source/puffer_pool`, SHA256
  `dafb68d4174e62b4c65a7b8f93e4c5f29d782c5636c63be3b99ccbb2a6691c68`.
- Patches: `retained-through-gold60.patch` and `shared-pool83.patch`.
  Do NOT use `pool83.patch` (rejected central counter).
- Reviews: `pgo61/REVIEW.md`, `pool83-review/REVIEW.md`.

## Current measured results and limits

All comparisons are against the frozen START-OF-NIGHT baseline, which already
includes the stream-safe cuBLAS change. They are NOT stock-NLE speedups.

- 512-agent mature score-policy GPU rollout: **+47.6488% throughput** combined,
  +16.6777% engine alone. Controls24.61640/24.64465s; pool16.68184s;
  4,194,304 measured decisions; control drift0.1148%. `rollout93/summary.json`.
- Loaded-policy training: **+14.0610% observed**, controls26.63806/25.89886s,
  pool23.03018s, control drift2.775%. Asynchronous trajectories differ; this is
  observational, not exact-work causal attribution. `pool89-training/summary.json`.
- 1,024-agent score-policy GPU rollout: **+17.41785% combined**, +9.83014% engine
  alone; controls52.46892/52.44668s, engine47.76266s, pool44.67617s.
  8,388,608 decisions; drift-0.0424%; all32 hashes/RNG/load match within1024.
  `rollout107/summary.json`. Do not compare trajectories across agent counts.
- CPU-only512-depth-stream replay: +6.2166% engine alone, **+3.8711% combined**.
  4,096,000 decisions /9,732,744 keys /3,711,945 positive turn advances match.
  Control drift0.0782%. `depth102/summary.json`. The pool gain is workload-specific.
- Optional tcmalloc94: repeated rollout gains1.5–2%, ~47MB extra RSS; training flat.
  Full replay passes. Documented in `alloc94/REVIEW.md`, NOT default best.

## Immediate next steps

1. Inspect58516 result, confirm wrapper restores monmove.c byte-identical to61.
  111prefetchesnextremainingmatchfromvalidSIMDmask;no filtering/order changes.
   Profile110 flooriterator topssimulatedD1readmisses (not hardwarestallproof).
2.110completed exact warm62000+512scoreenv40; pack16.5%instructions,m_move13.4%,
   mfndpos7.87%,fill_obs3.52%,nh_fobj_next2.37%. Endpoint254262score/depth6 isnot
   windowstate. `profile110/analysis.json` andIr/D1mrannotatedsources.
3.109parked:120Kstresscasesandall32observation/RNG/loadproofpass,but+1.33%gain
   within1.84%control drift. No repeat or retainedsourcechange.
4. Seek anotherboundedprofile-ledcandidateafter111. Finalaudit07:00–07:23,
   deadline08:23. No overlappingtimings/builds/profiles/replaygates.

## Recent decisions

-103 SIMD all-terrain8-cell skip: exact32score/32depth prefixes and20K-map
  sanitizer oracle pass. CPUdepth+3.02%, score flat; actualGPUrollout-0.836%.
  Parked.104 aligned-only variant: CPUdepth+1.22%, score flat; parked.
-105 separate completion counter cacheline: stress+32block proofs pass,
  throughput-1.82%, rejected.
-106 skip broadcasts with no sleepers: stress+32block proofs pass,
  throughput-0.477%, drift-0.438%; rejected.
-97 bounded pause,98 CUDA wait policy,101 cross-buffer helping: gains within
  noise or regressions; parked/rejected. No changes retained.
-102 depth check and107 larger-batch check are completed and ledgered.

## Correctness and scope reminders

Engine61: full32score/512depth replay with GOLD_VERIFY; raw snapshot equality;
15 known raw-historical exporter exceptions unchanged. Explicit historical-view
adapter passes34goldens/status/interleaved/shuffled and26fuzz cases with floor
and gold diagnostics. Do NOT call raw historical suite a clean pass.
Pool83: full32score/512depth concurrent replay;60K-region regular/ASAN/UBSAN/TSAN
checks including24workers. TSan startup mapping failures preserved; non-PIE fourth
launch passed. Patch/source round trips verified. Block hashes alone are not
full action traces; recorded replay supplies separate step-level evidence.

No model/PPO/reward/action/observation changes. No pushes or PRs. Keep main
`/puffertank/pufferlib` cublas branch and stock-NLE trees untouched. Never kill by
pattern; protected demos stay. No attribution trailers. Build only in isolated
copies. Use set-e for dependent shell steps; do not edit executing scripts.

Full history: `CURRENT-through107.md`, `STATUS.md`, `PLAN.md`, `ledger.jsonl`.
Previous goal turn made progress: CURRENT consolidated and stale state archived;
108arms28/32finished,closingcontrolverifiedlive. Decision: no further1024tuning
becauseabsoluteSPSstillbelow512;next109thenfreshprofile110. Finalauditrequired.

108terminal25614:1024workers28+5.5725%,32+2.0744%,controlsdrift-1.0407%;32hash/RNG/loadallmatch. No defaultpromotion/furtherrepeat;absolute196289SPSstillbelow512retained251429. Ledgered. Previousgoalturnprogress108closed,110+109pipeline47223launched.

Goalturnprogress:108completed/ledgered,110freshprofilecompleted,109testedandparked,111started. Session47223terminal. Bestunchanged.

Latest user steering: asked forfresh detailedbottleneckprofile; fulfilled inPROFILE_CURRENT.md. ResumeCPU/observation optimisations; don'tclaimPPOtrainingprofilefromrollout-onlytrace.111alreadyrejected/restored;newprimarynextcandidatecanfocussearches_for_itemorpackingbased110. Finalaudit07:00–07:23/deadline08:23.

## Focused goal continuation 2026-09-18T05:54:14.219659+00:00
New goal retains original08:23deadline/finalaudit07:23. CPUfocus, GPU/model fixed.
item114 class-negative shortcut REJECTED: score+0.70%within1.01%drift,depth-1.36%;32+32prefixexact; muse.c restored to61.
pack115 precomputes monster distances once per pack, preserving first-minimum order.32+32prefixexact;score+0.86%,depth+3.17%with3.28%drift. GPUrollout build+ABA now live session44419; inspect it before launching any more computation. Scripts setup_pack115.py and pack115_rollout.py; pack115-rollout-build.log.
pack116 floor-clear early-continue prepared only, NOT run: patch_pack116.py/pack116.py. Do not overlap timing. Best unchanged. This turn made progress:114 rejected,115screen passed and rollout launched.

## 2026-09-18T05:58:03.209541+00:00
44419terminal:pack115GPU+0.2315%within1.3019%drift,32obs/RNG/loadexact; PARKED.
16556terminal:pack116earlyfloorcontinue32score32depthprefixexact,score-0.67%,depth-4.24%;REJECTED.
Active session3834 runs pack117.py (class eligibility before form/zero-time tests), scoreverify passed, timing in progress. Poll before further compute.
Next prepared candidate patch_pack118.py/pack118.py removes duplicate welded inventory scan inside sole-caller slot helper; caller already excludes welded WIELD once. Profile110 attributes1.87%instructions to redundantloop. NOT RUN YET. No production changes; maintrackedclean. Best unchanged. Turnprogress:115rolloutclosed,116tested/rejected,117running,118preparedfromprofile.

## 2026-09-18T06:02:40.473603+00:00
3834terminal:117reject -1.05%score/-0.58%depth, exactprefixpass.25791terminal:118prefixpass/+1.07%score/+.93%depth;48745GPUterminal +.5698%with.5717%drift,32obs/RNG/loadmatch =>PARK.
Active40585 pack119.py: compute identical throw/zap ray mask once; read-onlypeacequeries verified fork+stock+gym. Scoreverify passed; CPUtimingrunning. Poll before morecompute.
Prepared NOT RUN: patch_pack120.py/pack120.py caches typedmaptokens with exactmemcmpglyphs/samehxhy;invalidates onbothobj_mem clears(reset/floor);refresheseachmonsterpeaceflag onhit; validherocoordinatesonly. Need compile,replay,timing; no promotion. Cache stores privateglyph/tokenbytes, leavesobj_mem unchanged onhits (idempotentmapping), allotherpack/maskwork stillruns. No productionchanges. Best unchanged. Turnprogress117closed,118tested&parked,119running,120prepared.

## 2026-09-18T06:06:08.995492+00:00
91790terminal:pack120exact32score32depthprefixpass, CPUscore+.331%within.587%drift/depthflat-.033 =>PARKEDcachecomplexityunjustified.
Active60875 pack119GPUrollout; buildfinished, before16.81675,candidate16.82956,closingcontrolrunning. Poll before anycompute.119CPU32+32passed,+.495%score/+1.56%depth.
Prepared next121fullSSE2glyphclassification+objectmemoryupdate withlanecompaction; patch_pack121.py/pack121.py. Generates monster and remembered-item capped lists inoriginalcellorder, preservesnegative/unknown glyph memory,scalar3celltail. setup_oracle121.py alreadygeneratedpack121-oracle.c from actualpatch SIMDblock+existing103scalaroracle. Compile/run ASAN+UBSAN oracle BEFOREscreen, after60875terminal. Then pythonpack121.py. Nothing121tested/compiledyet. ModelGPUunchanged. Turnprogress120tested/parked,119GPUlive,121prepared. Bestunchanged.

## 2026-09-18T06:11:29.026876+00:00
60875terminal:119GPU-.275%/-.399%drift=>PARKED.9084terminal:121ASANUBSANoracle20Kmaps33.18Msignedglyphspassed;32score32depthprefixexact;CPUscore+.534%depthflat.33799terminal:121GPU-.182%within1.507%drift,32obs/RNG/loadmatch=>PARKED.
Active8853:pack122.py combines118duplicateweldscan+119reusedrays+121SIMDgrid. Need inspect CPU result then decide one combinedGPUcheck with setup_pack122.py/pack122_rollout.py already prepared.
PotentialNEXTengineidea123 (NOT IMPLEMENTED): compact240bytepercontext trap occupancy bitmap, negative t_at lookups returnnull, positives retainlinearfirst-match. Earliertrap14 full13KBpointerindex was flat-score/+1%depth andparkedforcomplexity; bitmapdifferentmemorytradeoff. Reuseauditedtrap14.patch mutationhooks(maketrap/deltrap/save/restore/bubble-relocation), validate all coordinate/listmutations again; optionalNLE_TRAP_VERIFY negativeoracle. Would needsourcebackups/finallyrestore andactualPGOcheck ifclearwinner. Priorraw historical15exceptionsmustremainexplicit.
No productionchanges;bestunchanged. Turnprogress121validatedandparked;122launched;enginecandidateinvestigation.
