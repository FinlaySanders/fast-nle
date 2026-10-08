# Ten-hour NetHack rollout optimisation goal

Start: 2026-09-17 22:23 UTC. Hard deadline: 2026-09-18 08:23 UTC.
Goal: improve mature-policy NetHack simulation/rollout throughput without changing game behaviour. Existing stream-safe cuBLAS, model, PPO, reward, observations and actions are fixed. Do not trade away work, episode length, inference accuracy, or game semantics.

## Tight-loop contract

- Reuse existing recordings, replay binaries, build scripts and correctness corpus. Infrastructure budget <=20 min initially; afterwards only repair an actual blocker. Do not rebuild an experimental framework.
- Default candidate budget 5–10 minutes, hard investigation budget 15 minutes. At 15 minutes record evidence and either justify one bounded extension or park it and try the next idea.
- Keep an ordered queue of >=5 concrete hypotheses. Each entry names the measured cost, smallest change, acceptance check, and expected mechanism.
- One behavioural/performance change per candidate. Freeze each tested binary/library; never replace a mapped library. Preserve rejected patches and why they lost.
- Screen with one short exact replay window for score and depth; then paired fixed-work timing. Warm-up is required and reported game age must be mature. A replay pass must include the warm-up path. Known baseline failures remain documented; never silently change the oracle or exclude a new divergence.
- Reject obvious regressions immediately. If gain is within noise, repeat once then park it unless strong evidence merits a bounded follow-up. No benchmark reruns merely to find a favourable number.
- Promote only repeatable improvements to a current-best stack. Validate promising engine changes in the real loaded-policy async trainer: per-epoch time, final rollout tail, PPO time, actual game ages, finite weights, proof of loaded checkpoint. Initial fresh-optimizer training is not resumed-training equivalence.
- Log rollout-only and whole-training gains separately. Because overlap can hide engine gains, useful verified engine improvements may be kept separately, but must not be sold as training wins. Never multiply independent speedups.
- Broad golden/fuzz/full replay gates run for retained batches, not after every failed micro-experiment. Run relevant additional tests immediately when a specific risk demands them.
- Give live commentary after each candidate and at least every minute of active work, including keep/reject decisions. No silent detached autonomous agent. Tool jobs may run independently, but this chat owns the adaptive decisions.
- Keep trying distinct evidence-led ideas throughout the window. Aim for at least two screened ideas per productive hour, not a quota of accepted changes. Every hour review the queue and avoid sinking the night into one speculative rewrite.
- Reserve final 60–90 minutes for combined validation, baseline/best comparison and reviewable patches. Finish earlier if the remaining ideas have no credible upside; do not manufacture busywork. Otherwise continue until the deadline.

## Safety / isolation

Production /puffertank/pufferlib remains on cublas; do not edit its trainer or algorithm files. Preserve named stash. Never modify stock NLE trees or original recordings. Engine/rollout experiments live here or in isolated copies. No push/PR. Never kill by pattern; inspect exact PIDs and re-list. Do not stop nethack_demo or puffer_drone.

## Fixed baseline

- Source/binary: /puffertank/experiments/nethack-workspace-safe-20260917/source/puffer_safe
- Engine: /puffertank/experiments/nethack-perf-20260917/variants/candidate14-lto-local/libnethack.so
- Score checkpoint: resources/nethack/fixwt4b_s705.bin (prove GPU master weights match file).
- 512 agents, 4 buffers, 32 workers; existing work stealing; score 20-head frozen env. Do not replace this with the newer identification-policy env: checkpoint layouts differ.
- NetHack latest matched baseline: 26.16 seconds / 3,932,160 timed steps; re-establish locally before claiming further gain.
- Keep depth recording workload as a regression/cross-workload check.
- Existing corpus/gates: /puffertank/experiments/nethack-perf-20260917/{RUNBOOK.md,STATE.md,HARNESS.md,SNAPSHOTS.md}, tight-loop/campaign2h/final/REPORT.md. Earlier deadlines there are historical; this PLAN controls this goal.
- Known exceptions: baseline raw historical 15 observation-export mismatches; original score env457 has a late uninitialised-message divergence; graph-enabled multi-buffer inference repeatability has a historical baseline issue. Do not claim full determinism from selected passing windows. candidate14 LTO global checker requires documented symbol audit, not a relaxed whitelist.

## Initial candidate queue

1. Worker count 16/24/32: reduce oversubscription / barrier overhead on hybrid CPU; same 512 agents/4 buffers/workload.
2. OMP_WAIT_POLICY passive / GOMP_SPINCOUNT=0: stop idle workers consuming cores while GPU work proceeds. One environment setting at a time.
3. CPU affinity P-cores vs all cores, keeping worker count matched; measure hybrid-core stragglers. Preserve task/sample ordering.
4. Work-stealing chunk sizes: amortise atomic fetches without creating long-tail batches.
5. Per-buffer completion imbalance: profile late batches and explore deterministic cost-aware scheduling without modifying per-env RNG/order.
6. Re-profile mature engine hotspots (mfndpos, m_move, ordered floor object lookup, onscary); try cheap redundant-work removal and validity-preserving fast paths.
7. Observation packing/copying only where unchanged byte output can be demonstrated. Avoid revisiting already-rejected glyph-pointer hoist, tile bitset and terrain SIMD without new evidence.
8. Persistent worker pool only if timing shows team/synchronisation costs dominate; prior shared-pool failures must be reviewed first and rewrite time boxed.

## Ledger protocol

Append JSONL entries to ledger.jsonl: timestamp, candidate, hypothesis, patch/source hash, commands, correctness, timings, drift, decision, next. Human-readable STATUS.md tracks current best, active PID, remaining queue, next action. Save report and patches at deadline. Update the explicit chat goal only when work is complete, not just because a turn ends.

## Queue refinement after first late-game profile

- scary06: empty ordinary tile cannot scare; skip resistance checks there. Active.
- hoist07: monster visibility predicate is invariant across mfndpos neighbour candidates; move outside loop, preserve mux/muy updates.
- PGO08: use fixed mature score+depth replay to gather GCC profiles, then rebuild same source with profile-use; compare against same-source LTO build. Bound setup plus screen to15min; do not confuse profile counts with timing.
- Keep hybrid-core affinity and per-buffer completion-tail scheduling as independent rollout candidates after engine batch.

- pause12: add x86 processor pause hint to CPU rollout worker/coordinator polling loops in isolated trainer; fixed-policy rollout ABA then training if useful. No algorithm/model change. Larger futex redesign only if evidence justifies it.

- If priority10 wins at512/32 and loaded rollouts: try reordering every8steps to amortise sorting. Keep the history clock overhead included. Reject if only small benchmark improves.

## Queue at23:46 after affinity rejection

1. trap14 (active): t_at linked-list lookup in monster neighbours -> per-context spatial index; audit mutations, exact score/depth replay, diagnostic original-lookup oracle. Keep only repeatable gain.
2. distant15: distfleeck computes onscary even when !nearby and ignores it. Skip for distant ordinary monsters; preserve RNG call and shopkeeper/priest scratch-buffer effects. Exact replay then ABA.
3. pile16: mfndpos garlic+boulder merged scan can stop once both found; no RNG/callbacks. Small patch, quick screen; park if too rare/noise.
4. floor17: profile current remaining nh_fobj_next cost and evaluate wider coordinate reject only if portable runtime dispatch or explicit target acceptable. Prior native03 inconclusive, so requires a specific kernel hypothesis rather than blanket march-native.
5. empty18: profile repeated empty/no-op observation encoder clearing/copying; only skip writes with byte-identical output and explicit validity, avoid prior rejected pointer-hoist.
6. priority19: only if engine wins shift scheduling balance, revisit per-step priority sorting amortized every8steps; prior depth regression10.9% sets a high bar. Otherwise skip.

- bounds21 (next beforepool18): m_move rechecks four object-coordinate bounds immediately after nh_fobj_next returns an object proven within those exact live bounds. No mutating callback lies between. Remove redundant condition; cursor oracle+exact replay and diagnostic index checks must still pass. Stronger current hotspot rationale than rare pile16.

- key22: floor index still invalidates on every nle_step, despite mutation hooks at object place/remove/split/replace and level changes. Test removing only this per-key invalidation; diagnostic NLE_FOBJ_VERIFY must check live pointer/order/coordinate equality on every lookup across keys, plus complete score/depth and fuzz. Audit existing95mutation references before promotion. Unlike floor04 this extends validity across keys, so missing mutation hook is an explicit risk and any mismatch rejects/requires targeted fix. One-line screen, broad diagnostic only if useful.

- buffers23: after engine batch, screen2/4/8rollout buffers with fixed512agents and32CPUworkers, samecheckpoint and totalsteps. Smaller cohorts may reduce slow-environment tail but shrinkGPUinferencebatches. Require identical loadedweights and inspect per-block game-age/step summaries; if inference rounding changes sampled trajectories, use fixed replay scheduling for attribution rather than calling it exactsamework. Model size/PPO/reward unchanged. Prior history checked: scheduler tests held4buffers, no comparable currentbest buffer-count screen found.

buffers23 audit: native RNG uses curand_init(base_seed+buffer_id, local_agent_index,0), so changing buffer count DEFINITELY changes samples, beyond floating-point batch effects. Do not call different-buffer native runs an identical trajectory comparison. If pursued, use CPU fixed-action replay for scheduling or an explicitly benchmark-only RNG mapping reproducing4buffer baseline per globalenv (seed=base+globalenv/128,sequence=globalenv%128), then prove block/trajectory match. No production RNG change authorised or needed.

- incremental24 (conditional onkey22 gain andnewprofile): if floor-index rebuild stillmaterial, update validcache oncommon head insertion/removal rather than linked-list rebuild. Must maintain exact fobjorder, bumpgeneration so activecursors fall back, invalidate onrare mutation paths. Profile/count rebuildfrequency first; do not addbookkeeping speculatively.

- cursor25: mask05 caches remaining matching lanes, but after the last match it resumes at last_match+1 and re-tests the already-rejected tail of that SIMD block. Track validblock end separately (base initialized-1); when bounds unchanged and mask exhausted, advance scan tobase+8. Boundschange must resume logical last_match+1, never skip newly admissible entries; invalidate block metadata on scalar path/new query/mutationfallback. Existing cursororacle plus explicit shrink/expand andsparse-match cases. Small specific algorithmic candidate before speculative alignment/AVX.

## Queue after byte-identical PGO20 debug profile (~00:30)
- gold27: two-node findgold unroll rejected (-1.14% score/-0.94% depth). Hero inventory scan dominates this cost; persistent gold cache parked pending bounded mutation design, do not introduce dangling pointers for small gains.
- region28 ACTIVE: no-region fast path skips poison-resistance and gas lookup work in mfndpos. Existing context region count only; no new cache. Verify region creation/destruction cannot occur inside pure neighbor search.
- neighbors29 PREPARED ONLY: eight immutable ordered coordinate offsets replace nested 3x3 loops and self-cell skip. Preserve x-major/y-minor order and boundary exclusions; explicit exhaustive coordinate oracle before timing.
- pile16 still untested: stop garlic/boulder scan once both known, relevant only if profile suggests long piles; reject cheaply otherwise.
- buffers23 scheduling experiment remains an independent direction after bounded engine candidates. RNG caveats above mandatory.
- observation empty-write optimisation needs new profile evidence, not speculative invalidation.

## Queue at actual 01:20 UTC
1. track40: negative movement-history proximity cache. 7.725M oracle comparisons and selected score/depth replay pass; first screen +1.98%/+1.37%. One repeat active; if repeat supports it, fresh matching PGO then heldout test, otherwise park.
2. huge43: prepared only in prepare_huge43.py. Align fresh mmap contexts to 2MiB and request MADV_HUGEPAGE; no global host setting changes. Measure actual AnonHugePages and RSS, reset overhead and mature fixed replay. Material ~1GB memory tradeoff at512env, keep only meaningful gain. Restore track40 first to keep candidates isolated.
3. pile16: conservative early exit once both garlic and boulder found in mfndpos pile scan; profile actual pile cost first. Tiny bounded source patch/oracle, no broader index maintenance.
4. track variant: if negative cache wins but bookkeeping matters, update only changed position neighborhoods; repeated positions can skip decrement/increment when overwritten position equals inserted position. Requires full history/cache oracle; no change to gettrack ordering.
5. Buffer scheduling: CPU-only eight-group gain confirmed, GPU matched-workload comparison failed because trajectories differ even with identical RNG initialisation. Park unless a bounded fixed-action GPU replay can reuse existing traces without framework rewrite. Do not promote raw GPU speedup.
Keep immutable PGO20 as best until fresh matching PGO and retained-candidate gates finish. No parallel timing or builds beside timing.

## Queue refreshed after depth profile54
1. inventory55 active: merge inv_state and inv_true_glyphs live inventory walks; optional outputs and partial-fill semantics retained. Exact replay and paired timing.
2. glyph56 preparedONLY: nle_copy_glyphs repeatedly invokes lazy gbuf accessor; bind const screen pointer once before copy loops. No mutation between reads. Exact replay; profile says copy contributes6% depth-window instructions.
3. If glyph56 leaves gather cost material: contiguous short glyph mirror, only show_glyph/clear_glyph_buffer write canonical gbuf. Audit whole tree, diagnostic compare every copy and full replay before promotion. Adds3.3KB percontext; avoid if hoist solves bottleneck.
4. Redundant dirty-row glyph copy: fill_obs copies glyphs_ then immediately overwrites all cells with nle_copy_glyphs; remove only first glyph memcpy, retain chars/colors/specials and dirty bookkeeping. No callbacks between.
5. Valid-coordinate store_glyph fast path avoids constant modulo (fallback original for invalid coordinates). Only pursue if profile/assembly shows nontrivial cost.
6. Fresh depth vision_recalc profile if export ideas flat; functions account~3.5-4% instructions plus newsym. No RNG/order or visibility semantics changes.

## Queue after gold60 held-out result
1. PGO61 active: original8+8 compiler-profile recipe with gold60 source. Compare against retained44. Gold60 screen/repeat/heldout score +1.95/+2.31/+1.32%; depth mixed(flat/-0.98%/noise). No promotion before final optimized-binary measurement and diagnostic validity checks.
2. If PGO61 merits retention, build gold60-diag with NLE_GOLD_VERIFY and run gold60_diag_gate.py; explicit historical-view fuzz adapter must also include this diagnostic. Audit addresses all live inventory->gold mutations.
3. alloc62: measured monster AI/cache traffic suggests trying64-byte monster allocation alignment while preserving struct layout and all field semantics. newmonst currently alloc(sizeof(struct monst)); inspect actual size/offsets and try aligned allocation helper only at this macro. Track RSS/reset cost; no general malloc replacement, no save-format change, no field reordering. Exact replay first and profile/rollout validation if useful.
4. If allocator alignment has no gain, do not chase allocator rewrites; use fresh slower heldout mature score-window profile to avoid overfitting env20 leprechaun scene.
5. Persistent per-context caches must offer clear gain beyond their mutation-hook maintenance cost; gold60 is a bounded exception to test, not a reason to cache all linked-list queries.

## Queue at 02:46UTC after retained PGO61
1. alloc62 ACTIVE: align only heap monster allocations to64B, unchanged structure/save layout; same-source nonPGO gold60 control. Exact32score/32depth replay then ABA; revert if noise/regression.
2. profile63 PREPARED: byte-identical debug PGO61, two previously excluded mature score episodes (env452 warm8500, env149 warm50000),512decisions each, instruction+simulated cache counts. Do not mistake simulated misses for measured stalls or final episode depth for window depth.
3. class64 PREPARED: replace three tiny constant strchr class-membership checks in m_move with compiler-visible comparisons, retaining NUL-match semantics. Profile50 shows26K calls/512decisions but only~0.13% instructions directly, so low ceiling; one cheap screen, no extended pursuit if noise.
4. Distinct monster-lookup prefetch: only if profile63 confirms map lookup misses still material. Prefetch next neighbor's pointer slot (not next linked monster; that already lost), preserve order/RNG. Maxone screen before parking.
5. Revisit rollout worker count only after another material engine gain or measured critical-path change. Previous16/24worker attempts lost; do not blindly repeat. Profile rollouts with retained engine to see if worker stalls/tail now dominate before rescreening.
6. Garlic/boulder pile scan early exit remains cheap but low priority. Run only if profile63 finds meaningful pile-scan cost; preserve output flags, early stop only after both types found. Avoid persistent pile cache without measured upside/mutation audit.

## Queue refresh at04:24UTC
1. rollout93 ACTIVE: direct original/engine61/sharedpool24/original comparison; same32block workload proof. Replace20worker best only after reading results; combinedloadedtraining89 completed+14.06% observational.
2. allocator94 PREPARED: unchanged pool24 binary, installed tcmalloc_minimal via per-processLD_PRELOAD. Sharedpool cross-thread allocation/free is new context versus old alignment62. Exact32block proof; one ABA, reject memory or correctness regression, inspect RSS if meaningful gain. No allocator rewrite.
3. Neighbor-slot prefetch (95): profile63 monster-map lookup/cache traffic; inspect mfndpos hot path then one bounded prefetch of next valid neighbour pointer slot, preserving order/RNG. Earlier next-linked-monster prefetch46 lost; do not repeat it. Exactscore/depth screen; no build alongside rollout timings.
4. Sharedpool no-submitter-help screen:24persistentworkers, coordinators only publish/wait. Hypothesis remove extra CPU contenders and keep coordinator scheduling predictable; same24worker control, fullblock equality. One ABA only unless meaningful. Existing counter87/88,affinity91 flat; don't repeat those.
5. Sharedpool bounded-spin completion: replace immediate sched_yield on unfinished region with a bounded pause interval then yield. New pool's completion path differs from old pause12 worker-state wait. Profile evidence required before pursuing; preserve acquire done check and reader leases. No unbounded spin.
6. Fresh single-engine profile on depth window if scheduler/allocator directions flat. Preserve depth regression checks; don't redesign interface or change model. Stop new candidates07:00–07:23 for final audit.

## Queue refresh04:52
1.97pause64repeat ACTIVE; initial+.681%/-.391%drift. Decideafterrepeat,don'tpromote smallnoise.
2.101boundedcrossbufferhelp PREPARED: whileownregionwaiting, every64pollsleaseanotherregionandexecuteatmostoneunclaimedjob. Retainatomicclaim,done-release,readerleaseprotocol. Stressbeforetiming; broadconcurrency/fullreplayifwinner. Doesnotinclude97untildecision.
3.102cross-workload CPU depth rollout comparison: same512depthrecordings and4buffer pthreadreplay, original14engine+WS32 vs61+pool24workers/28total. Native score gain47.65%doesnotimplydepthgain. Reuse existingfull512depthproof; validate matching measuredsteps/keys/worldturn advances in timedarms. This is fixed-action CPU-onlyscope, notGPUrollout/training. Prepareonce101decisionknown.
4.Ifpool97/101fail,don'tkeepmicrotuningwaits. Profile99depthengine windowhaspacking20.5%,vision~5%,monsterAIspread; seekboundedsourcechangeonlyfromspecificredundancy. No cachemutation complexityforfractionalnoise.
5.Finalcombinedaudit/reportstill07:00–07:23start; separatecodewins fromoptionalallocator94, no multiplicationofgains.

## Queue05:05
1. pack103 active: eight-terrain SIMD block skip in observation memory/list scan; original scalar mixed-block fallback. Profile99 >10%instructions here. CPU prefixoracle+ABA then native pool24 rollout if useful.
2. If103wins, avoid repeatedSIMDchecks on mixedblocks by testingonce per8-alignedcells; separatevariant, preservelogicaliteration order and tail.
3. If103wins, compare16-cell block only afternativeproof; lessbranching butlowerall-terrainhitprobability. Onecheapscreen,don'tkeepwithoutgain.
4. Recheck slower mature score windows for packing gain vs depth; whole32-block rollout mandatory, no claimfrominstructioncounts alone.
5. Ifpackingflat, refresh scheduler tail data bybuffer/actionduration, withoutchangingactions; no more sched_yield variants.
6. Finalauditstarts07:00–07:23; no candidateframeworkrewrite.

## 05:12 queue
105cacheline separation rejected,stress/hashpassbut-1.82%.
106skipreadybroadcastwhenzero sleepers; countguardedbyexistingp.mu,epochalwaysadvances,no wake lost. Stress+nativeABA,notcombinedwith105.
107preparedrollout107.py:1024agents,orig/61WS/61pool24/orig;32blocks; compareWITHIN1024only,nevercross512hashes. Checkall32hash/RNG/loadmatchthenreport scaling scope. No modelchange.
108conditional: if106noise, inspect new1024schedulerbalance beforemorepooltuning. Keepcurrent24workerdefaultuntilnewproof.
Finalaudit07:00–07:23deadline08:23,retainedbestunchanged.

## 05:18 pending sequence
1071024pipeline comparison running.108worker-countscreenpreparedconditional.109costprioritizationpreparedonly:originalpool, perregioncostEMA andpermutation,clock+sortevery16runsorcount/startchange. Nextmustinspectoriginal stress; countersdone releaseaftercostwrites/readersleasebeforegenerationreuse. Unlikepriority10/34(originalindependentWS),thisusesretainedsharedpool; oneboundedtestonly.110freshhigh-scoreprofileprepared:scoreenv40warm62000+512,episode10score254262/end64987/start38674/turn187606/depth6. EndpointstatsNOTwindowstats. Verifyfullprefixbeforecallgrind;retained61debuglibrarybyteidentical. No concurrentprofiling/timing.

## 05:28 profile110 follow-up
Highscoreenv40verified/profiled. Ir:pack16.5%,m_move13.4%,mfndpos7.87%,fill_obs3.52%,nh_fobj_next2.37%; flooriterator topssimulatedD1readmisses. No hardwarestallclaim.
111preparedprefetch111.py: prefetch next remaining matched floor-object pointer fromalreadyvalidSIMDmask before returningcurrentobject. No newfilter/order/indexvalidity changes; bothmaskreuse/newblock branches. Exactprefix+ABAnonPGOgold60controlviaengine_screen_alloc62;finallyrestoresmonmove.c. Earlierprefetch46(nextmonster)/95(neighbor-slot)lost;thisisdistinctobjectiterator localitycase. NOTRUNuntil109terminal. Onecheap screen,parkifnoise.
