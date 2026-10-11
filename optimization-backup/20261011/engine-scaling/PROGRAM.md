# NetHack engine scaling program — opened 10 October 2026

Goal: a fast-nle engine whose per-step CPU cost does not grow with the number of resident games, so hyperparameter
sweeps over agent count / batch size are not collection-bound. Companion to the regime ablation grid in
/puffertank/experiments/nethack-24h-20261009 (ablate_*.results.json, summarize_ablate.py).

## Established premise (do not re-derive)

- Collection sets the throughput floor in every regime except 15M/512 (ablation grid, 10 Oct). The engine ladder
  stock -> sept14 -> precompact -> retained is worth 1.75x (15M/512), 2.1x (5M/512), 1.57x (15M/2048), with
  identical observation hashes at every level on the recorded workload.
- At 2048 games the retained engine costs 130.7 us/step interleaved vs 79.9 us cache-hot (burst16); 78% of the gap
  closes when the same data is pre-touched (compact-state full_gap_20261009/REPORT.md). Gap by subsystem (us):
  monster movement 12.8, misc engine 8.2, player movement 6.2, obs export 5.1, inventory weight 4.3,
  vision/display 4.0, other monster 3.7, floor index 2.6.
- Scheduling fixes are exhausted on this stack: cohorts -5..-38%, grouped 16x128 -8%, affinity 0, huge pages +0.1%.
- Hardware counters blocked by host sysctl perf_event_paranoid=4 (PMU present: cpu_core/cpu_atom). Host-side fix
  unblocks perf mem/c2c in this container. Until then: callgrind cache simulation.

## Step 1 — footprint, not time (queued: footprint.sh, runs after the GPU grid finishes)

Question: which subsystems' data spill the last-level cache as the game count grows, in bytes per step?
Method: ./replay (compact-state harness, callgrind markers after warm-up), retained engine, 512 games, serial,
warm 4096 steps/game (matched to the fast-protocol game age), measure 128 steps/game, cache simulation with
D1 = 48 KB/12-way and LL = 36 MB (each game's L3 share at 512 games) vs LL = 9 MB (share at 2048 games).
Output: per-function Dr/Dw/D1mr/DLmr aggregated into the gap-report subsystem categories (footprint_report.py).
Decision rule: if the top three subsystems carry >= 60% of the extra LL misses at the 9 MB share, step 2 targets
them with hot/cold splits; if misses are diffuse, step 2 is a whole-context hot/cold packing instead.

### Step 1 result (12:52 UTC) — FOOTPRINT.md
Per step a game touches ~1,240 lines beyond L1 (~79 KB); 512 games x 79 KB ~ 40 MB = the L3, which explains the
512->1024 step and the flat 2048->4096 curve. LL read misses/step: 37 at the 512-game share -> 285 at the 2048 share
(+104 writes). Spill by subsystem: monster movement 28% (m_move, mfndpos_masked, movemon), observation export 22%
(fill_obs, pufferlib nethack_pack_obs, blstats, nle_weight), misc engine 18% (minliquid, moveloop, gethungry),
inventory weight 6% (encumber_msg), floor objects 6% (nh_fobj_next), player movement 5%, display 5%, RNG 3% (ISAAC
4 KB state). Decision rule met (top three >= 60%): targeted work, not whole-context packing.
Already present in the retained engine, so NOT candidates: per-column monster occupancy masks in mfndpos (movement
masks), object-presence tile bit, movement-first monster layout + per-game pools, separate glyph/dirty planes.
Step 1b (queued): line-level attribution with a -g twin (footprint_lines.sh -> FOOTPRINT_LINES.md) to name the
statements inside m_move/mfndpos/fill_obs/newsym that miss L3.

### Step 1b result (13:08 UTC) — FOOTPRINT_LINES.md (self-cost LL read misses/step at the 2048 share, 295 total)
pufferlib nethack_pack_obs full-grid obj_mem pass 17.7 + a memcpy 17.1 (not the glyph copy: glyphs are bound into the
obs buffer) | inv_weight inventory walk (hack.c:2419-2423) 23.9 | floor-object coordinate cache rebuild (monmove.c:752-755)
14.2 | movemon fmon walk (mon.c:518) 10.4 | MON_AT in mfndpos (mon.c:1364) 8.5 | neighbourhood terrain reads (hack.h:27/64,
mon.c:1130/1290) ~20 | per-game objects[] table reads (winrl.cc:92/435/465/18, nle.c:554, mon.c:990, weapon.c:445) ~17.6 |
monster inventory walks (mthrowu.c:987-988, monmove.c:1082/1002, steal.c:80) ~15.6 | display gbuf ~11 | vision ~10 |
ISAAC RNG 12 | nh_track_near 3.6 | C++ std::string in RL export 5.4 | dungeons[] walk 2.8.
Candidate ranking (addressable LL lines/step): A pack_obs incremental via exported dirty rows ~18 (+~45 D1) low risk;
B inv_weight cache ~24 (92 owt + 102 quan write sites in 29 files -> generation counter + verify build) moderate risk;
C re-screen parked engines in collection-bound full pipeline (zero code): dry-tile liquid fast path (terrain ~20; native
+1.3%/+0.8%), immutable object metadata (objects[] ~17.6; native +0.56% parked), floor_index_incremental (fobj ~14,
needs port to retained source); D per-monster inventory-search cache ~15.6 moderate; E RNG swap ~12 = user decision.
Not actionable by layout: movemon list walk, display/vision incremental already.

### Candidate A result (13:50 UTC) — incremental glyph export + incremental packer
Engine (engines/incexport, incexport2): fill_obs rewrites only glyph rows that changed (window-port dirty rows | display
pending rows), full re-copy when objects[].oc_name_known changes (hook in discover_object / forget_single_object) or the
buffer changes; exports the rewritten-row mask (nle_glyph_dirty_rows) and reports the hero row under the underfoot patch.
Packer (harness_incpack, trainer_incpack): obj_mem/token lists updated only on exported rows via row-major bitmasks.
Quick gates PASS (incexport). Native replay, obs hash identical in all 16 runs: engine only +1.8% (512) / +3.4% (2048);
engine+packer +2.8% (512) / +4.1% (2048). incexport2 quick gates PASS. Full pipeline (fast protocol, non-PGO retained controls, drift <=0.2%):
5M/2048 engine-only +3.6%, engine+packer +4.3%; 15M/2048 +3.5% / +4.5%; 15M/512 +0.1% / +0.1% (GPU-bound, as expected).
Stacked engine (incstack = incexport2 + liquid + immutable), quick gates PASS, native with packer: +4.5% (512), +6.0%
(2048), obs hashes identical; full pipeline + full every-action hash gate running (chain_c).
Parked patches re-screened vs the fair non-PGO control in the full pipeline: liquid +1.1%/+1.9%, immutable +1.0%/+1.6%
(5M/2048, 15M/2048); PGO itself +4.9%. Stacked candidate engines/incstack = incexport2 + liquid + immutable (building).

## Step 2 — hot/cold split of per-game state (candidates written after step 1b)

Expected first targets from the time gap: monster records (per-step hot subset ~32 B of 120), current level tiles,
hero struct, floor-object index. Keep names, saved levels, TTY buffers, RNG tables cold.

## Step 3 — incremental whole-level work

Vision/display and observation export walk 80x21 every step; dirty-region tracking. Inventory weight: cache and
invalidate on inventory change (4.3 us of gap).

## Step 4 — worker-affine env slices (only once hot set <= ~30 KB/game so 64 games fit a 2 MB P-core L2)

## Step 5 — inference latency (collectors wait 41% of their cycle at 512 agents; separate GPU-side item)

## Candidate loop and gates (each candidate = isolated engine copy, never the vendored tree)

1. Source: copy engines/movement_object_presence_pgo_followthrough/source (retained) -> engines/<name>/source;
   build with the compact-state recipe (Release, LTO, TLS initial-exec, -fno-semantic-interposition); PGO later.
2. Quick gates: compact-state check.py <name> --quick (golden 34, fuzz 26, status, interleaved, shuffled).
3. Full gate: check.py <name> (every-action hashes, 512 games x 32768 steps vs reference).
4. Native CPU screen: ./replay 512 and 2048 games, 32 workers, warm 8192, measure 2048, LD_LIBRARY_PATH=<build>.
5. Full pipeline, fast protocol, collection-bound corners: nethack-24h-20261009 campaign_ablate.py with a spec
   setting LD_LIBRARY_PATH=<build> at 5M/512 and 15M/2048 (12 measured epochs, paired controls).
Retain if: all gates pass, native 2048 >= +2%, full pipeline >= +1% at a collection-bound corner, 512 not worse.

## Targets

Closing the locality gap alone: 2048-agent collection ~210k -> ~330k SPS (then 15M/2048 becomes GPU-bound).
Work reduction on top: 50-60 us/step plausible. Projections from the gap table, not measurements.

### OPEN ISSUE (14:35 UTC) — full every-action gate on incstack: 504 of 16,777,216 decision hashes differ
Layout is hashes[game*32768+step]: 45 runs in 29 games, each a run of consecutive steps (1..176) that then self-heals.
That is the signature of a stale glyph row in the incremental export (a gbuf change not covered by dirty|pending), not of
the liquid/immutable patches (those would diverge permanently). Attribution run: check.py incexport2 (full) ->
compact-state/checks/incexport2.json (0 differences = patches at fault; 504 = export at fault).
Fix plan: add NLE_INCEXPORT_VERIFY build that computes the old full copy+remap alongside and asserts equality per fill,
replay the 29 games (indices from checks/incstack.hashes.bin vs cpu-scaling/runs/final_hash_opt61/hashes.bin) to catch
the first stale cell and its writer. shuffled_glyph depends only on objects[].oc_name_known/oc_descr_idx (hook sufficient).
Until fixed, incexport2/incstack are NOT landable despite identical end-state hashes in all screens.
Chain D (chain_d.sh, log scratchpad/chain_d.log) runs unattended: incstack_pgo build -> quick gates -> native screen ->
landing comparison (ablate_landing.json: retained PGO + v37 vs incstack PGO + incpack_v38) -> REGIME_RESULTS.md.

### Landing comparison (chain D, 14:20 UTC) — current full stack (PGO retained + v37) vs incstack PGO + incpack_v38
5M/2048: 216,402/216,550 -> 230,259/230,536 (+6.4%); 15M/2048: 210,961/210,965 -> 223,282/222,684 (+5.7%);
15M/512: 228,195/228,060 -> 228,585/228,501 (+0.2%). incstack_pgo quick gates PASS. Native (vs non-PGO) at 2048: +12%.
Attribution of the 504 hash differences: incexport2 alone reproduces exactly 504 -> the incremental export is at fault.
Verify engine: engines/incexport_verify (logs INCEXPORT_MISMATCH with row dirty/pending state, self-corrects).

### Hash-gate issue RESOLVED (15:00 UTC) — root cause and fix
Glyphs 2378/2401-2421 decode as S_room (floor) vs trap glyphs. The underfoot patch writes back_to_glyph (terrain) into
the hero's obs cell every fill; the old full copy repaired the cell after the hero moved on, the incremental copy left the
terrain glyph on top of the trap until the row was redrawn (self-healing runs; far cells = travel/run between fills).
Fix (engines/incexport3): remember the patched cell, restore it from glyph_at() + remap when its row is not recopied, and
report its row in the exported mask. Verify replay over 512 games x 32768 steps: 0 mismatches (was 45). Method that found
it: verify engine computing the old full export per fill + per-cell event trace (incexport_verify3/4/5).
incstack2 = incexport3 + liquid + immutable; chain_e: full gate -> PGO -> landing2 -> native screen -> report.

### Layer 1 (heat re-annotation) — 17:15 UTC
engines/heat1 = incstack2 + tools/globals.def re-annotated (99 hot entries, was 28; ordered: per-step scalars/list heads,
hero/flags/iflags/context/youmonst/dungeons, per-step planes, then showsyms + ISAAC last) and regenerated nh_ctx:
hot prefix 24.4 KB (u at +1256, RNG at +16.4 KB), total 175,856 B. Quick gates PASS. Native vs incstack2 (packer harness
both sides): +0.7% (512), +0.8% (2048), hashes identical. Footprint comparison fp_incstack2 vs fp_heat1 -> FOOTPRINT_HEAT1.md.
Footprint (2048 share, packer harness both): LL read misses 225.5 -> 219.0/step (-2.9%), LL writes 78.8 -> 73.6 (-6.6%),
D1 -1.9%; savings in moveloop/rhack ("other" -3.0), monster movement -1.2, player movement -0.6; RNG +0.5 (moved to the end).
Matches the +0.8% native gain. KEEP (zero-risk); a second pass inside struct you is not worth it. Note incstack2+packer = 225
LL lines/step vs 285 for the retained engine: this session's export work removed 21% of the spill.

### Cross-game asynchronous prefetch experiment (engines/heat1pf, harness_pf, pf_screen.sh) — 17:15 UTC
nle_prefetch(next_ctx, mode) in nle.c: bit1 ctx hot prefix 4 KB, bit2 24 KB, bit4 window-port instance 1 KB, bit8 coroutine
stack top 4 KB (from generatorcontext up to stack.sptr), bit16 hero neighbourhood (3 columns of locations/monsters/objs/
typ plane/track plane); harness bit32 = prefetchw of the next game's obs buffer. Pool claims home + n*workers, so the next
game for a worker is i + workers (same buffer). Modes screened at 2048: 0,1,13,29,61 (ABBA-ish), then 512.
Semantics check: identical obs hash across modes (smoke). Rationale: misses are latency-bound (~4 GB/s used of ~80);
pre-touching recovered 78% of the gap in the campaign's diagnostic but was synchronous; this overlaps it with the current step.

### Cross-game prefetch experiment — RESULT (18:05 UTC): closed, negative
Native replay at 2048 games, heat1pf engine + harness_pf, 32 workers. Guessed-next prefetch (i+workers): modes 1/13/29/61
within +-1% of controls (one segfault: racing a stolen game's reset -> replaced by owned prefetch in the claim loop).
Owned prefetch (claim next, prefetch it, step current): controls 235,193/235,046/235,768; modes 29/93/221/93 = 233,781/
233,845/233,379/234,071 (-0.4..-0.8%). Pinned workers: controls 241,378/241,248; modes 93/221 = 240,205/239,664 (-0.5/-0.7%).
Reading: the step is miss-bound; software prefetch competes with demand misses for fill buffers/bandwidth, and the
address-known hot set (ctx prefix, pool heads, stack top, hero neighbourhood) is not where the misses are (pointer-chased
monsters/objects/grids). "Streaming through L3" is not reachable with prefetch hints; only footprint reduction and
fewer dependent chains remain. Keep nle_prefetch out of the stack.
SIDE FINDING: pinning pool workers one per logical CPU = +2.6% native at 2048 (CPU_PIN_WORKERS in harness_pf). The
campaign's full-pipeline affinity arms were null; re-test in the full pipeline (trainer pool PUF_CPU_AFFINITY).

### Worker pinning, full pipeline (18:30 UTC): incpack_v39 (PUF_CPU_AFFINITY=2: worker w -> logical CPU w%32, main thread
unpinned) vs incpack_v38, both incstack2 PGO. 5M/2048: 231,590/231,819 -> 233,626/233,283 (+0.8%); 15M/2048: 224,710/224,732 ->
225,502/225,666 (+0.4%). Real, below the 1% gate; candidate for the collection-bound phase config, not a landing item alone.

## 2026-10-10 invwt (inventory-weight cache) — RESULTS
Stack: incstack2 → heat1 → invwt. Verify build 0 INVWT_MISMATCH over the gate corpus; quick gates PASS (golden/fuzz/status/interleaved/shuffled); full every-action gate 512x32768 = 0/16,777,216 diffs.
Native screen vs heat1 (control = heat1 build, same harness, ABBA):
| agents | ctrl a/b | cand a/b | delta |
|---|---|---|---|
| 512 | 295,740 / 293,933 | 303,083 / 302,879 | +2.8% |
| 2048 | 233,986 / 235,102 | 236,749 / 237,586 | +1.1% |
obs hash b97835c62aaf388f all 8 runs. KEPT: invwt is now part of the stack. Footprint arm fp_invwt running (compare vs fp_heat1 → FOOTPRINT_INVWT.md).
Next: mload (monster-load cache, make_mload.py) built on invwt.

## 2026-10-10 mload (monster-load cache) — DROPPED
Built on invwt. Verify replay 0 MLOAD_MISMATCH / 16.7M steps; quick gates PASS. Native vs invwt:
512: ctrl 301,905 / 303,235, cand 297,531 / 301,239 (-1.1%, cand_a run perturbed by a source copy); 2048: ctrl 237,685 / 236,644, cand 237,047 / 237,106 (flat, -0.04%).
curr_mon_load never appeared in the footprint; the walk was not hot. Lesson: convert only walks the footprint names. Source kept in engines/mload (10 hooks, make_mload.py) if a future footprint makes it hot. Full gate and footprint arm not spent on it.
Stack stays: incstack2 → heat1 → invwt. fobj2 rebased onto invwt (make_fobj2.py).

## 2026-10-10 fobj2 (incremental floor-object index) — NATIVE RESULTS
Built on invwt (make_fobj2.py). Index kept as a window parked at the top of the 2048-entry arrays: place_object = one store at --lo,
remove_object = pointer scan from lo + memmove of the newer prefix; splitobj/replace_object/level change still invalidate.
Verify twin (NLE_FOBJ_VERIFY now logs FOBJ_MISMATCH + rebuilds): 0 mismatches / 16.7M steps, obs b79eb25d93ca6d29, turns 115413681 (= reference).
Quick gates 5/5 PASS. Native vs invwt (ABBA):
| agents | ctrl a/b | cand a/b | delta |
|---|---|---|---|
| 512 | 299,920 / 302,434 | 302,097 / 303,327 | +0.5% |
| 2048 | 237,971 / 237,631 | 242,099 / 242,524 | +1.9% |
obs b97835c62aaf388f all 8 runs. Full every-action gate + footprint arm running (chain_k2.sh); line-level footprint of the current stack (lines_invwt) running alongside.
FULL GATE: PASS, 0/16,777,216 diffs. KEPT. Stack: incstack2 → heat1 → invwt → fobj2. Cumulative native over heat1 at 2048: invwt +1.1% then fobj2 +1.9%.

## 2026-10-10 fresh line footprint of the invwt stack (FOOTPRINT_LINES_lines_invwt.md) and misc1 candidate
Self LL misses 221.4 lines/step at the 2048 share (retained source was 294.7). Remaining clusters: monster grid lookups in mfndpos/minliquid ~25;
fobj rebuild 13.5 (→ fobj2); inventory export (winrl.cc objects[] lookups + std::string + memcpy) ~19; newsym ~11; packer ~9; nmon walk 7.6;
m_carrying minvent walk 7.0; hidden_gold 6.4 + deepest_lev_reached 3.1 (both every step via botl_score/fill_obs); inv_weight residual 4.3;
check_leash 2.1; isaac64 ~10.
misc1 (make_misc1.py, on fobj2): nh_invgen hero-inventory generation (bumped at the 8 insertion sites that clear nh_no_hero_gold,
extract_nobj(&invent), and container content changes whose top-level carrier is the hero); hidden_gold cached by generation;
check_leash skipped when the cached leash count for this generation is 0; deepest_lev_reached cached per noquest slot,
invalidated at the 2 dunlev_reached writes, init_dungeons and restore_dungeon. Verify twin -DNLE_MISC_VERIFY logs
HGOLD_/LEASH_/DEEPEST_MISMATCH. Expected ≤ 11.6 lines/step (5%). chain_l.sh.
Parser fix: footprint_lines.py no longer counts call-edge rows as source lines (earlier FOOTPRINT_LINES.md line numbers were shifted; text column was right).
fobj2 footprint (FOOTPRINT_FOBJ2.md, 2048 share vs invwt): LL read misses 251.3 → 228.1 lines/step (−9.2%), LL writes −8.7%, D1 misses −3.4%;
floor-objects subsystem 19.3 → 7.0 lines/step. Dr +0.6% (the pointer scan in nh_fobj_removed). Consistent with +1.9% native at 2048.

## 2026-10-10 misc1 — NATIVE RESULTS (marginal)
Verify twin 0 HGOLD/LEASH/DEEPEST mismatches / 16.7M steps (obs b79eb25d93ca6d29, turns 115413681); quick gates 5/5.
Native vs fobj2 (ABBA): 512: ctrl 300,038 / 305,469 (mean 302,754), cand 304,725 / 307,864 (mean 306,295) = +1.2% (control spread 1.8%);
2048: ctrl 242,337 / 243,554 (mean 242,946), cand 244,548 / 243,497 (mean 244,023) = +0.4% (within noise).
Decision deferred to the footprint (expected ~11 LL lines/step removed) and a second ABBA if the footprint confirms the miss reduction.
Full gate + footprint arm running (chain_l.sh); chain_m.sh (mbits) builds/verifies now and screens after fp_misc1.
Line-report fix #2: callgrind_annotate prints only annotated regions with "-- line N ---" markers; the parser now resets the line counter
at each marker. FOOTPRINT_LINES.md and FOOTPRINT_LINES_lines_invwt.md regenerated; spot-checked (monmove.c:804 fobj build, mon.c:1968 MON_AT,
winrl.cc:727 inv_state oc_name_known, vault.c:1120 hidden_gold, dungeon.c:1083 deepest).
misc1 footprint (FOOTPRINT_MISC1.md vs fobj2): LL read misses 228.1 → 193.3 lines/step (−15.3%), LL writes −14.7%, D1 misses −7.0%; the drop is spread
over every subsystem (monster movement −9.2, obs export −9.9, other −7.4), i.e. the removed walks were also evicting other games' lines.
Native showed only +1.2% / +0.4%, inconsistent with −15% LL misses → second ABBA (misc1b, vs fobj2) inserted into chain_n2.sh before the kbits screen.
misc1 full gate: 0/16,777,216 diffs.
LANDMINE: pkill -f 'chain_n.s[h]' killed my own shell because the same command also mentioned chain_n.sh literally; keep pkill in a command of its own.

## 2026-10-10 mbits (per-monster carried-otyp filter) — DROPPED
Verify 0 MBITS_MISMATCH / 16.7M steps; quick gates 5/5. Native vs misc1: 512 ctrl 304,850 / 308,042 vs cand 305,529 / 308,222 (+0.1%);
2048 ctrl 244,936 / 244,557 vs cand 244,381 / 243,982 (−0.2%). Flat both regimes although mthrowu.c:1123 was 7 LL lines/step in the footprint:
the dwarf pick-axe walks are overlapped by the hardware, not stalled on. Second confirmation that footprint lines no longer predict native gains 1:1.
Full gate/footprint not spent. kbits rebased onto misc1.

## 2026-10-10 misc1 re-screen (misc1b, vs fobj2) — KEPT
512: ctrl 302,551 / 306,424 (mean 304,488), cand 304,596 / 309,100 (mean 306,848) = +0.8%; 2048: ctrl 242,301 / 242,588 (mean 242,444), cand 243,054 / 244,565 (mean 243,810) = +0.6%.
Two ABBAs combined: +1.0% (512), +0.5% (2048); 7 of 8 paired comparisons positive. Small, consistent, gate-clean (0/16.7M), LL −15%: KEPT.
Stack: incstack2 → heat1 → invwt → fobj2 → misc1. kbits screen vs misc1 running.

## 2026-10-10 kbits (discovery bitset for export reads) — DROPPED
Verify 0 KBITS_MISMATCH / 16.7M; quick gates 5/5. Native vs misc1: 512 ctrl 307,197 / 307,595 vs cand 304,716 / 305,073 = −0.8%;
2048 ctrl 243,680 / 243,902 vs cand 244,958 / 246,243 = +0.7%. A regime trade of under 1% each way with extra code on the export path: dropped.
CACHE LADDER CLOSED. Final stack: incstack2 → heat1 → invwt → fobj2 → misc1 (engines/misc1). Next: PGO build (build_pgo.py misc1), trainer landing (make_landing3.py), handoff.

## 2026-10-10 landing3 — trainer landing of the final stack (incpack_v39 + misc1_pgo vs incpack_v39 + incstack2_pgo), fast protocol, ABBA
| regime | ctrl a/b | cand a/b | delta | note |
|---|---|---|---|---|
| 5M/2048 | 230,794 / 229,052 | 237,008 / 236,640 | +3.0% | collection-bound; rollout tail 563/570 → 534 ms |
| 15M/2048 | 223,257 / 223,806 | 228,535 / 230,034 | +2.6% | rollout tail 115/108 → 85/77 ms |
| 15M/512 | 228,327 / 228,521 | 228,448 / 228,402 | 0.0% | GPU-bound (ppo_est = epoch), engine invisible as expected |
misc1_pgo quick gates 5/5. Stacked on this morning's incstack2 landing (+6.6% / +5.8% / +0.2%), today's engine work is ≈ +9.8% / +8.5% / +0.2% in the trainer.
Phase 1 (cache ladder) CLOSED. USER DECISION 2026-10-10: fix the root problem (per-step touched set ≈ 65 KB vs 18 KB L3 share at 2048) structurally; no scheduler work.

# PHASE 2 — structural (opened 2026-10-10 21:40, user decision: fix the root problem, no scheduler work)
Premise (measured): a policy step touches 1,082 lines beyond L1 = 67.6 KB (D1mr, lines_invwt), of which 221 lines (14 KB) miss the
emulated 2048-game L3 share (18 KB per game). Burst16 ceiling (+67% at 2048) is what zero cold-start would give.
Footprint by DATA STRUCTURE (FOOTPRINT_DATA_lines_invwt.md, footprint_data.py): object records 12.5 KB/step (18.5%), monster records 7.8 (11.6%),
obs buffers/packer 5.5 (8.1%), display gbuf 5.0 (7.5%), grid terrain 4.2, RNG state 3.8 (isaac64: 2 KB state + 2 KB output per game),
monster map 3.5, summary/pile planes 3.4, hero/ctx 3.4, floor index 2.5, vision 2.3, objects[] 2.1, unclassified ~10 (mostly object walks).
Two legs:
 A. Observation pipeline (≈ 15 KB/step: obs buffers + tty/gbuf path + objects[] + the inventory object reads of the export): export the packed
    4184-byte observation directly and incrementally from engine state; retire the NLE-format intermediate (glyphs/chars/colors/specials/inv strings)
    for training. Contract: packed obs hash b97835c62aaf388f over the corpus, full gate 0 diffs. Contained (winrl.cc fill_obs + ocean/nethack/nethack.h packer).
 B. Game-state layout (≈ 45 KB/step): unified per-cell record for the movement query (terrain + monster + pile summary + trap/gas in one line),
    struct obj hot prefix (the export and pile scans read ~16 fields; keep them in the first 32 B), struct monst hot/cold with hot records packed
    consecutively in movemon order. Touches most of mon.c/monmove.c/mkobj.c; the Oct-8 design document applies.
HONEST PROJECTION: both legs fully done bring the touched set to ~40 KB, still > 18 KB share; LL misses maybe −35-40%; at tonight's
realized ratio (fobj2 −9% LL → +1.9%, misc1 −15% → +0.5%) that is +5-10% native at 2048, ~0 at 15M/512 (GPU-bound). RNG (3.8 KB/step, 5.7%)
is a separate user decision because a compact RNG is not bit-exact.
Decision rule per structural step: verify twin 0 mismatches → quick gates → ABBA ≥ +1% at 2048 without loss at 512 → full gate 0 diffs → footprint.
Order: A first (contained, best-defined contract), then B.1 unified cell record, B.2 obj hot prefix, B.3 monster packing.
Sizing correction (20:50): the grid planes are already compact (struct rm 6 B, typ plane 1 B/cell, summary 2 B/cell, column bitmasks); with the
[COLNO][ROWNO] layout a 3x3 neighbourhood of each plane is 1-3 lines, so merging planes into one 8 B cell does NOT cut lines per query
(3 columns x 168 B = 8 lines vs ~10 today). The earlier campaign's grid/tile arms (+0.3-0.7%, parked) agree. B.1 is demoted.
The largest class is OBJECT RECORDS (14.8 KB/step, 22%): the per-step export walks every inventory object twice (inv_state + inv_true), monsters
scan piles, inv_weight residual. A.1 = invview (make_invview.py): inv_state/inv_true computed in update_inventory_method (NetHack's own
"inventory display changed" hook, 96 call sites) and on discoveries-generation change; fill_obs copies. Verify twin -DNLE_INVVIEW_VERIFY
recomputes per step and logs INVVIEW_MISMATCH slot/field: this measures how faithful update_inventory() is as a change hook. chain_q.sh.
Env side already binds NULL for colors/inv_strs/tty_* in training (tty_emit off) — no waste there.

## 2026-10-10 invview (inventory export as a materialized view) — DROPPED
Verify twin: 3,563 INVVIEW_MISMATCH / 16.7M steps (3,559 field 0 = BUC: bless/curse/unbless/uncurse never call update_inventory; 4 field 1 = spe).
Native vs misc1 (obs differs as expected, timing still valid): 512 ctrl 304,357 / 304,137 vs cand 304,910 / 304,845 (+0.2%);
2048 ctrl 244,653 / 244,031 vs cand 243,516 / 244,093 (−0.2%). Flat: the per-step inventory walk is NOT a native cost at 2048 either.
invview2 (hooks at the BUC setters) generated but not run. Fifth footprint-named candidate in a row that is flat natively.
CONCLUSION for Phase 2 sizing: the emulated-LL footprint mis-ranks native costs. Use the native causal method instead (read-only warming of a
structure before the step, movement_causal_tsc_20261009): all five data-structure groups together = 21 us of a 129 us step (16%); floor objects
9.7 us (fobj2 took part), grids 7.5 us, monster records 4.2 us. Data layout cannot be worth more than ~12% more at 2048.
The burst ceiling (+67%) therefore lives mostly OUTSIDE data-structure layout: pages/TLB (70-87 distinct 4 KiB pages touched per step;
one-hugepage-per-game tried once: small gain, 4x RSS; a multi-game 2 MiB slab was prepared, never tested), instruction/branch state, obs write path.
NEXT: TLB census = owned page-touch (one real load per 4 KiB page of ctx + pools + stack) one step ahead in the pipelined pf harness (mode 256).

## 2026-10-10 22:15 TLB census (heat1pf mode 256 = one real load per 4 KiB page of ctx 171 KB + mon/obj pools + coroutine stack, one step ahead on the owning worker)
2048: mode 0 234,074 / 233,328 vs mode 256 232,688 / 232,451 (−0.5%); mode 288 (+obs buffer touch) 231,478 (−1.0%). obs hash unchanged.
REFUTED: page-walk/TLB cost is not a recoverable part of the 2048 step (touching ~60 pages ahead costs more than it saves). Agrees with the
earlier context_slab huge-page result (+0.6% @2048, within drift). Follow-up queued: page touch + line prefetch combined (258, 458) to test
whether earlier line prefetches were being dropped on TLB misses.
512: mode 0 293,745 / 295,736 vs mode 256 290,154 / 291,320 (−1.4%). TLB warming negative in both regimes; census closed.
Follow-up (2048): mode 0 235,678 / 233,203 vs 258 (page touch + 24 KB ctx line prefetch) 228,688 (−2.4%), 458 (+ stack, pools, neighbourhood) 228,124 (−2.7%).
Software warming one step ahead is negative in every form tried (lines, pages, both): the owned-prefetch idea is CLOSED.

## PHASE 2 STATUS (22:30): attribution of the 40%-of-step cold-start cost (burst16 +67% @2048)
named data structures 16 pts (native warming census; ~4 taken by fobj2/invwt/misc1; ≤12 left = ceiling of a data-layout rewrite);
pages/TLB 0 (page-touch census + context_slab); remainder ~24 pts = branch/instruction state + L1/L2 residency of everything else,
unreachable by engine rewrite, reachable only by running consecutive steps of a game on one core (temporal locality / scheduling).
Decision handed to the user (see chat 2026-10-10 22:25): bank the misc1 stack (paired-seed A/B) + choose between data-layout rewrite (≤12%),
regime-gated temporal-locality scheduler (ceiling several x larger; earlier recheck +9.5% @2048 / −3.7% @512), or GPU inference latency (15M/512).

## 2026-10-10 22:45 INSTRUCTION CENSUS of the warm step (callgrind Ir, lines_misc1 dump; exact counts, no emulation caveat)
555K instructions per policy step. Self cost: m_move 89K (16%), mfndpos_masked 90K (16%), dochug+dochugw 32K, movemon 11K, distfleeck 11K,
should_displace 9K, mcalcmove 8K, set_apparxy 8K, minliquid 7K, mcalcdistress 6K, linedup 6K, muse find_* 11K, place_monster 4K, nh_fobj_next 29K (5%);
display/obs: newsym 23K, show_glyph 7K, nethack_pack_obs 26K, fill_obs 5K; RNG 15K; vision 14K. Inclusive: movemon 407K/step (73%), dochug 371K,
m_move 303K (inclusive numbers across the coroutine boundary (rhack/moveloop/pack_obs) are cycle-inflated; movemon's is credible).
~99 monster-movement entries per decision (mature games advance several game turns per policy step): ≈ 4K instructions per monster move.
CORRECTION to the Phase 2 framing: the 40% cold-start attribution bounds only LAYOUT work. The warm 60% of the step is compute, 70% of it the
monster turn (movemon → dochug → m_move → mfndpos). A rewrite of the movement query (the Oct-8 MOVEMENT_ARCHITECTURE design: same ordered
candidates + flags + RNG consumption, far fewer instructions) is a compute lever, regime-independent, plausibly 20-30% of the step. THIS is the
fundamental rewrite worth doing; it is sized by exact instruction counts, not by the mis-ranking footprint.

# PHASE 3 — monster-turn subsystem redesign (opened 2026-10-10 23:10, user: "ok do it")
Scope: movemon → dochug/dochugw → m_move → mfndpos/mfndpos_masked + helpers (should_displace, m_digweapon_check, monhaskey, gettrack, minliquid,
onscary, region/worm checks); ~1,700 lines. Consumers (dog_move, move_special, movemon) and all signatures unchanged. Contract: identical ordered
candidates + flags + RNG draws → packed obs hash b97835c62aaf388f on the corpus, full gate 0 diffs. Sizing metric: callgrind Ir (exact), not misses.
Baseline (misc1): 555K instructions/step; monster turn ≈ 405K inclusive (73%); m_move 89K self, mfndpos_masked 90K self (~96 calls/decision,
~8 candidate cells each → ~117 instr/cell), dochug 32K, nh_fobj_next 29K, distfleeck 11K, should_displace 9K, mcalcmove 8K, set_apparxy 8K.
Method per step: isolated engine (make_mt<N>.py on the previous), verify twin (-DNH_MOVEMENT_MASK_VERIFY: mfndpos_reference compared per call,
panics turned into MFNDPOS_MISMATCH lines), corpus replay, quick gates, ABBA vs previous, full gate, instruction census (footprint_lines2 -g twin → Ir).
Step 1 = mt1: terrain facts as a pure function of (typ, rmflags) in a static 64x32 table (pthread_once init); per-cell rock/tree/dig/passwall/bars/
door/pool/lava checks become one load + bit tests; arboreal-STONE and Juiblex-drawbridge handled by two per-query booleans; origin door facts hoisted.
Expected: −40..60 instr/cell → −35..45K/step (6-8%). chain_s.sh.
Planned next steps: mt2 per-monster capability word (species predicates, dig tools) cached across calls with invalidation at data/inventory change;
mt3 m_move per-move facts (canspotmon once, permission word from the capability word), object-scan gating by per-column object masks (bit-exact
only as an emptiness pre-check); mt4 dochug/distfleeck/set_apparxy arithmetic; mt5 movemon/mcalcmove/minliquid loop.

## mt1 (terrain LUT in mfndpos_masked) — NATIVE: flat/negative
Verify twin (mfndpos_reference per call): 0 mismatches / 16.7M steps, obs b79eb25d93ca6d29. Quick gates 5/5.
Native vs misc1: 512 ctrl 307,321 / 304,053 vs cand 305,441 / 304,643 (−0.2%); 2048 ctrl 244,120 / 243,712 vs cand 242,058 / 243,305 (−0.5%).
Reading: the terrain predicates it replaced (IS_ROCK = one compare, IS_DOOR = one compare, pool ≈ 6 compares) cost about as much as a table lookup
plus bit tests; the per-cell 117 instructions are spread over ~15 small checks (monster-at, aggression/displacement, scary, temple, onlineu,
squeeze, trap block, loop bookkeeping), none of which a terrain table touches. Instruction census (lines_mt1) pending to quantify.
mfndpos_masked line profile (misc1): 52K self instructions/step spread over 126 lines, largest line 2.3K (4.5%): loop bookkeeping (nx/ny from bit,
info[]=0, poss[] stores) ~8K, per-call species predicates (lines 1823-1840) ~10K = ~100 instr/call, summary-bit tests ~6K, monster-at/worm/
displacement ~5K, the rest ≤1K each. The other ~38K of the function's 90K are inlined helpers (nh_move_cell, scary, bad_rock, pool/lava).
No concentrated hotspot: a terrain table cannot matter (mt1 confirmed). Reducing this function materially means restructuring it: per-call species
word cached per monster (−10K), gas/pile/trap/scary bits folded into column masks so failing cells never enter the loop (−10-15K), trap block as
precomputed per-species trap-avoid mask (−3-5K) → realistic 90K → 55-60K (−6% of the step). m_move (89K self) is spread the same way.
REVISED PHASE 3 EXPECTATION: 10-15% of the step from a full restructure of mfndpos + m_move + dochug (~1,000 lines), not 20-30%. Each lever is 1-3%.
mt1 instruction census: 554.7K → 558.7K/step (+0.7%); mfndpos_masked 91.9K → 95.1K (+3.2K: table index + more bit tests than the compares it
replaced), pthread_once 0.6K. DROPPED. Lesson for S3: masks that remove cells from the loop, never tables that re-express per-cell predicates.
Next build mt2 = S1 species word + S2 per-move fact record (+ permission word from S1) on misc1.
mt2 (species word, make_mt2.py): LANDMINE — can_track(ptr) reads uwep (Excalibur grants tracking): not species-only; the load-time table
constructor segfaulted on nh_cur==NULL. Removed from the word; every other predicate in the word was checked to read only the species record.
Rule for the species word: a predicate may enter it only if its macro/function body touches nothing but *ptr and mons[].

## mt2 (S1 species word + vampshifter-gated sawmon) — NATIVE positive
Verify twin (SPW bits vs macros at 94 sites + mfndpos_reference): 0 mismatches / 16.7M steps, obs b79eb25d93ca6d29. Quick gates 5/5.
Native vs misc1: 512 ctrl 306,142 / 306,888 vs cand 308,247 / 309,824 (+0.8%, both candidates above both controls);
2048 ctrl 244,216 / 242,286 vs cand 244,101 / 245,173 (+0.6%). Full gate + instruction census (lines_mt2) running.
mt2 instruction census: 554.7K → 540.6K/step (−14.1K, −2.55%); S1 delivered ~70% of its 20K budget. Full gate 0/16.7M. mt2 KEPT (Phase 3 layer 1).
mt3 (always_inline on distfleeck/set_apparxy/should_displace/m_digweapon_check/monhaskey/dochugw): verify 0, gates 5/5; first screen vs mt2
PERTURBED (mt4 builds + verify overlapped it: ctrl_a 2048 fell to 234K) → repeat screen (mt3b) queued before mt4. LANDMINE (again): never start
builds/verify replays while a native screen runs; chains must wait for the previous NATIVE_*_DONE/CHAIN*_DONE before any heavy step.
mt3 full gate 0/16.7M. Clean-run reading of the perturbed screen: 512 cand_b 316,458 vs ctrl_b 311,927 (+1.5%); 2048 cand 246,572 / 246,974 vs ctrl_b 245,579 (+0.5%);
census lines_mt3 pending; repeat screen mt3b queued (chain_w.sh), then mt4 (S3 masks). Generators ready: make_mt5.py (S4a: MDISP implies monster, track mask),
make_mt6.py (S2b: hero perception snapshot + 6 central-mutator invalidations, verify twin -DNLE_HP_VERIFY).
mt3 instruction census: 540.6K → 523.1K/step (−17.5K, −3.24%): the inlined helpers' 47K of self cost became 30K inside dochug/m_move/movemon
(prologues gone, cross-call optimization). Cumulative Phase 3: 554.7K → 523.1K (−5.7%). mt3 full gate 0/16.7M → KEPT pending the clean mt3b screen.
mt3b (clean repeat, mt3 vs mt2): 512 ctrl 309,290 / 312,940 vs cand 314,278 / 288,216 (cand_b PERTURBED by the mt5/mt6/mt7 source generation I ran during the screen; clean pair +1.0%); 2048 ctrl 245,119 / 246,043 (mean 245,581) vs cand 248,580 / 248,699 (mean 248,640) = +1.2%.
mt3 KEPT (Phase 3 layer 2). Native since misc1: 2048 ≈ 243.8K → 248.6K (+2.0%); instructions −5.7%.
LANDMINE: even source-tree copies + gen_ctx (make_mt*.py) during a native run cost it 8%. From here nothing but log appends runs while a screen is active.

## mt4 (S3 mask-structured mfndpos) — DROPPED
Verify (reference query) 0 mismatches / 16.7M, gates 5/5, but native vs mt3: 512 ctrl 316,463 / 316,600 vs cand 307,316 / 312,538 (−2.1%);
2048 ctrl 247,336 / 247,345 vs cand 243,559 / 242,954 (−1.7%). Assembling 9 neighbourhood masks per call (~3 loads + 8 ops each) costs about
what 8 cells of bit tests save, and the 56 B column records turn a 1-line neighbourhood read into 3. Lesson: with 8 cells per query the per-cell
summary-byte tests are already near the floor; masks only pay for rules that are rejected for most cells. Census (lines_mt4) will quantify.
mt5/mt6/mt7 rebased onto mt3.
mt4 census: 523.1K → 532.2K (+1.75%); mfndpos_masked 88.6K → 95.9K (+7.3K): mask assembly > per-cell savings, as the clock said. Full gate 0/16.7M (exact but slower). DROPPED.
Running: mt5 (S4a) on mt3, then mt6, mt7.

## mt5 (S4a: ALLOW_MDISP implies monster-at; track mask gates the avoidance loop) — NATIVE positive
Verify 0 mismatches / 16.7M (reference query + species twin), gates 5/5.
Native vs mt3: 512 ctrl 316,080 / 316,818 (mean 316,449) vs cand 319,697 / 322,513 (mean 321,105) = +1.5%, both above both;
2048 ctrl 247,747 / 247,482 (mean 247,614) vs cand 249,158 / 248,646 (mean 248,902) = +0.5%. Full gate + census running.
mt5 census: 523.1K → 525.8K (+0.5%; m_move +2.7K: the per-call track-mask build costs more instructions than the short j-loops it gates),
yet the clock gained +1.5% / +0.5% with all candidates above all controls: the dropped MON_AT loads (cold 13 KB monster-pointer plane) were
stall-heavy. Full gate 0/16.7M. KEPT on the clock (Phase 3 layer 3). Note for the ledger: instruction count is the design metric, the ABBA clock decides.
mt6 first build failed: the static inline reader of the perception snapshot sat in hack.h before the ctx include (same landmine as kbits);
moved next to the floor-index cursor. mt6 (on mt5) and mt7 (on mt6) relaunched; chain_fold.sh <final> <tag> ready for the fold.

## mt6 (S2b hero perception snapshot) — DROPPED (flat)
Verify 0 HP mismatches / 16.7M (the 6 central mutators cover the corpus), gates 5/5. Native vs mt5: 512 ctrl 316,210 / 318,599 vs cand 319,660 / 317,934 (+0.4%);
2048 ctrl 250,117 / 249,322 vs cand 249,146 / 248,362 (−0.4%). Flat both ways: canspotmon's property chains are cheap, well-predicted loads at the
hero record. Not worth six mutator hooks. Census (lines_mt6) for the record. mt7 rebased onto mt5.
Phase 3 stack so far: misc1 → mt2 → mt3 → mt5 (all full-gated, each a positive ABBA).
mt6 census: see chain_mt6.log — net change within ±1K (mfndpos −0.6K, dochug −0.5K, m_move −0.2K, nh_hp_refresh +0.7K): the property-macro chains it replaced
were already cheap after inlining (the 6.9K "canspotmon" line of the misc1 profile was mostly dochugw's prologue, removed by mt3). Confirms the drop.

## 2026-10-11 ~02:20 — session cut by usage limit; unattended finish queued
mt7 (16-lane byte fobj scan, on mt5): verify 0, gates 5/5; screen vs mt5 in progress (512: ctrl_a 320,585, cand 321,506 / 317,443).
chain_finish.sh: waits for CHAIN_mt7_DONE, picks FINAL = mt7 if its ABBA is not negative in either regime and the full gate is 0, else mt5;
then chain_fold.sh FINAL landing4 = PGO build (engines/FINAL_pgo), quick gates, trainer landing ablate_landing4.json (incpack_v39 + FINAL_pgo vs
incpack_v39 + misc1_pgo, 3 regimes ABBA; summarize with `python3 summarize_ablate.py landing4`), final census ir_compare lines_misc1 lines_FINAL.
Logs: scratchpad/chain_mt7.log, chain_finish.log, landing4_campaign.log. Results to read next session: PROGRAM.md "FINAL=", chain_finish.log.
PHASE 3 LEDGER: kept mt2 (−14K instr, +0.8/+0.6%), mt3 (−17.5K, +1.0/+1.2%), mt5 (+2.7K instr but +1.5/+0.5% clock); dropped mt1 (+3K), mt4 (+9K, −2%),
mt6 (−2.7K, flat). Instructions 554.7K → 525.8K (−5.2%) at mt5; native 2048 243.8K → ~249.7K (+2.4%) vs misc1. Remaining monster-turn self cost is
rule evaluation + RNG draws; further bit-exact reductions are ≤10K each (minliquid typ tests, in_rooms, wipe_engr_at). Beyond that needs RNG/rule changes (user decision).
FINAL=mt7

## mt7 (16-lane byte-coordinate fobj scan, on mt5) — NATIVE marginal-positive, full gate 0/16.7M
512 ctrl 320,585 / 317,012 (mean 318,799) vs cand 321,506 / 317,443 (mean 319,475) = +0.2%; 2048 ctrl 249,435 / 248,995 (mean 249,215) vs cand 251,355 / 249,728 (mean 250,541) = +0.5%.
Census running; chain_finish.sh decides FINAL (mt7 qualifies under the ≥ −0.2% rule) and runs the fold (PGO, landing4, census).

# PHASE 3 RESULT (2026-10-11 ~03:00) — FINAL = mt7 (misc1 → mt2 → mt3 → mt5 → mt7), all full-gated 0/16.7M
mt7 census: 525.8K → 520.2K (nh_fobj_next 28.7K → 23.0K). Phase 3 total: 554.7K → 520.2K instructions/step (−6.22%).
Native vs misc1 (chained ABBAs): 2048 243.8K → ~250.5K (+2.7%); 512 ~302K → ~319K (+5.6%, partly box drift between sessions).
mt7_pgo: quick gates 5/5. Trainer landing4 (incpack_v39 + mt7_pgo vs incpack_v39 + misc1_pgo, fast protocol, ABBA):
| regime | ctrl a/b | cand a/b | delta |
|---|---|---|---|
| 5M/2048 | 237,638 / 238,004 | 241,595 / 241,512 | +1.6% |
| 15M/2048 | 229,066 / 230,172 | 234,018 / 232,942 | +1.7% |
| 15M/512 | 228,622 / 228,466 | 228,634 / 228,749 | 0.0% (GPU-bound) |
Day total (morning stack → mt7_pgo): ≈ +11.6% / +10.3% / +0.2% in the trainer.
Dropped with full records: mt1 (+3K instr), mt4 (+9K, −2%), mt6 (−2.7K, flat); mload, mbits, kbits, invview from Phase 2.
Where the remaining 520K go: monster turn ≈ 380K (m_move 102K, mfndpos 89K, dochug 29K incl. inlined helpers, movemon 22K, fobj scan 23K,
mcalcmove/mcalcdistress 14K, muse find_* 11K, minliquid 7K), obs/display ~60K, RNG ~15K, vision ~14K. The remaining monster-turn cost is rule
evaluation and RNG draws; bit-exact levers left are ≤5K each. Beyond this: RNG change (not bit-exact), rule changes, or temporal locality (scheduling).

## Compiler-target check (mt7n = mt7 source + -march=native -mtune=native; host i9-14900K: AVX2/BMI2, no AVX-512) — NEGATIVE
Quick gates 5/5 (integer code, identical outputs). Native vs the generic x86-64 build: 512 ctrl 320,213 / 320,503 vs cand 318,978 / 319,521 (−0.3%);
2048 ctrl 250,502 / 249,834 vs cand 247,538 / 248,191 (−1.0%). The engine is branchy integer code with no vectorizable hot loops beyond the
hand-written SSE2 scans; AVX2 codegen only widens the code. Keep the generic build. Full gate 0/16.7M (record only).

# PHASE 4 — cohort-synchronous rollout (opened 2026-10-11 ~04:30; user: "implement the cohort architecture"); design in PHASE4_COHORT.md
Stage 0 running: curve_screen.sh (step time vs games 256..4096 at 32 workers, mt7 engine) → screens/curve/summary.txt.
Stage 1 built: harness_cohort/replay_cohort.c (static cohort ownership per worker x buffer; knobs COHORT_A alternation, COHORT_K burst,
COHORT_LAT_US emulated inference latency with sleep-until, COHORT_PIN); same init/hash as replay.c (hash b97835c62aaf388f must hold).
cohort_screen.sh (queued after the curve): baseline vs A4/lat0 (today's interleaving, no stealing), A1/lat0 (burst upper bound), A1 and A2 with
lat 300/600/1000 µs, pinned variants → screens/cohort/*.log. Metrics: wall SPS, busy_sps (= SPS if perfectly balanced), idle per worker.
Decision rule (PHASE4_COHORT.md): go to the trainer only if a realistic (A, lat) beats batch-synchronous by ≥ 10% at 2048.

## Stage 0 result — step time vs games (32 workers, mt7, fast protocol; µs per step per worker = 32e6/SPS)
| games | per worker | SPS (a/b) | µs/step | vs 512 |
|---|---|---|---|---|
| 256 | 8 | 289,875 / 289,481 | 110.5 | harness/sync overhead dominates at 2 games per worker per buffer |
| 512 | 16 | 321,783 / 320,946 | 99.6 | 1.00x |
| 1024 | 32 | 281,787 / 282,962 | 113.3 | 1.14x |
| 1536 | 48 | 256,937 / 256,744 | 124.6 | 1.25x |
| 2048 | 64 | 249,112 / 250,355 | 128.1 | 1.29x |
| 3072 | 96 | 248,415 / 248,674 | 128.7 | 1.29x |
| 4096 | 128 | 249,141 / 249,080 | 128.5 | 1.29x |
Reading: the knee is between 16 and 48 games per worker (1-3 MB of per-step state per worker thread against ~1 MB effective L2 per
hyperthread), and it PLATEAUS from 64 games on: once the per-worker set exceeds L2 the cost saturates; L3 size is not the binding level
(2048 → 4096 adds nothing). So the scheduling prize at the current footprint is 1.29x (128 → 100 µs), not burst16's 1.67x (which also keeps
L1 warm and never changes game). The natural cohort is 16 games per worker = one buffer's share today. Cohorts of 8 do not pay (overhead).

## mt8 design (per-turn movement-class planes) — to build after the cohort matrix
Why mt4 failed: it assembled 9 neighbourhood masks per CALL (~100 instr) to save ~120 instr of per-cell tests at 8 cells. Amortize per TURN instead:
- Movement class = (species movement bits, the caller's flag bits that gate unconditional cell rules: ALLOW_WALL/ALLOW_DIG(rockok,treeok)/ALLOW_BARS/
  OPENDOOR/UNLOCKDOOR/BUSTDOOR, instance bits: poisongas_ok, fog/amorphous, wantpool/poolok/lavaok, mconf). Few distinct classes per level per turn.
- Per game turn (movemon), lazily per class on first use: a 21-row "enterable" plane (uint128 per row or 2x uint64) = rows of
  ~rock(unless passwall/dig) & ~bars(unless allowed) & ~closed/locked door(unless openable/thrudoor) & ~gas(unless ok) & pool/lava per class,
  built from the column words mt4 maintains (bars/door/pool/lava/dbridge/altar/tree/garlic/boulder/scare/trap/gas) transposed to rows once per
  turn when any changed (dirty flag per plane). Small cache (≤16 classes, keyed by the class word), invalidated when the facts change.
- Per call: candidates = 3 row words >> (x-1) & 7 of the class plane, & ~occupied(unless ALLOW_M/MDISP...), minus hero/image bits as today;
  diagonal rules (origin/cell door, rogue, worm) per surviving diagonal; then the per-cell monster-specific checks exactly as today
  (scary, hero/image → mux/muy side effect, aggression/displacement, temple, garlic/boulder info bits, onlineu, squeeze, trap block).
- Correctness: same cell order (bit order), same rejections before the hero side effect, same info flags → reference-query twin.
- Budget: mfndpos ~90K → ~25-30K per step; plane builds ~5-10K per step → net −50..−60K (−10%). Also consider the object-interest scan.

## Stage 1 result — cohort scheduler matrix (2048 games, 32 workers, mt7, fast protocol; all hashes b97835c62aaf388f = bit-exact)
| policy | wall SPS | vs baseline | busy SPS (balanced bound) | idle/worker | note |
|---|---|---|---|---|---|
| baseline pool (stealing) | 247,762 / 249,170 | — | — | — | today's batch-synchronous interleaving |
| A4 lat0 (4 cohorts alternate, static) | 240,193 | −3% | 275,717 (+11%) | 0 | ownership alone +11% per core; P/E imbalance −13% wall |
| A1 lat0 (1 cohort, burst) | 327,404 | +32% | 421,279 (+70%) | 0 | upper bound: matches burst16's +67% |
| A1 lat300 (wait) | 279,990 | +13% | 442,646 (+79%) | 2.5 s/12 | sleeping frees the sibling hyperthread |
| A1 lat600 | 245,948 | −1% | 473,706 (+91%) | 4.9 s/13.8 | idle eats it |
| A1 lat1000 | 208,330 | −16% | 503,414 | 8.2 s | |
| A2 lat300 (ping-pong) | 292,810 | +18% | 355,109 (+43%) | 0 | BEST realistic: no idle |
| A2 lat600 | 285,035 | +15% | 347,117 (+40%) | 0.1 s | |
| A2 lat1000 | 266,398 | +7.5% | 340,726 (+38%) | 0.6 s | |
| pinned variants | ≈ unpinned (A4 238K, A1 310K, A1/600 243K, A2/600 270K) | | | | pinning worker w→cpu w: no gain |
Readings: (1) cohort residency is worth up to +70% per core at the current footprint; (2) ping-pong (A=2) hides 300-1000 µs of inference
latency with no idle at +38..43% per core — two 1 MB cohorts partially evict each other, so a ~30 KB/game footprint would lift A2 toward A1's +79%;
(3) static ownership loses 13-25% of wall to P/E imbalance → the trainer design must avoid a global barrier (dynamic batching) and/or weight ownership;
(4) pinning irrelevant. Design consequence: inference by time-windowed DYNAMIC BATCHING across cohorts (forwards of 128-256 agents every
~100-200 µs), not per-cohort forwards; cohort latency = window + forward ≈ 300-600 µs → the A2 regime.

## Stage 2/3 discovery (2026-10-11 ~06:00): the trainer already has cohort knobs
src/pufferl.cu (trainer infra — patch only, never edited in place): PUF_COHORT_BUFFERS = buffers per resident group, PUF_COHORT_STEPS = horizon steps a
group runs before the ticket passes to the next group (asserts buffers % cohort == 0, horizon % steps == 0); --vec.num_buffers via run_scale --buffers 4/8/16.
With 16 buffers of 128 agents and PUF_COHORT_BUFFERS=4, the resident group is 512 agents = 16 games per worker (the L2-fit cohort) and the 4
buffers in the group pipeline inference among themselves (the A4@16 design). Queued: ablate_cohort.json (14 arms: ctrl a/b, b16c4 with steps
16/64/128, b8c2s32, b16c8s32; widths 512 and 1024; incpack_v39 + mt7_pgo) behind the inference-latency scan (ablate_inflat.json).
Decision rule: a cohort config beating the 4-buffer control by ≥ 10% at 5M/2048 → adopt as the default for collection-bound regimes and
hand off; the dynamic-batching patch (PHASE4_COHORT.md Stage 3) becomes the follow-up only if the knob route stalls below the harness's +40%.
Stage 2 scan (ablate_inflat, incpack_v39 + mt7_pgo, width 512): agents 128/256 abort (apb % 128 assert); agents 512 → reported sps 1,183,789,
1024 → 526,913; the epoch is a fixed 262144 agent-steps so the report scales by 2048/agents: real ≈ 296K @512 and 263K @1024 vs 242K @2048 —
the trainer reproduces the native L2 curve (321K/282K/249K). Forward latency itself not isolated; the trainer cohort campaign measures the thing that matters.

## Stage 3 RESULT (trainer, existing cohort knobs; incpack_v39 + mt7_pgo; fast protocol) — 5M/2048 complete, 15M/2048 partial
| arm | buffers x agents | group | steps/turn | 5M/2048 SPS | vs ctrl | 15M/2048 SPS | vs ctrl |
|---|---|---|---|---|---|---|---|
| ctrl a/b | 4 x 512 | — | — | 238,710 / 240,749 (239,730) | — | 233,487 / … | — |
| b16c4s16 | 16 x 128 | 4 bufs = 512 agents (16/worker) | 16 | 290,869 | +21.3% | 252,945 | +8.3% |
| b16c4s64 | 16 x 128 | 512 | 64 | 302,434 | +26.2% | 262,408 | +12.4% |
| b16c4s128 | 16 x 128 | 512 | 128 | 302,977 | +26.4% | … | |
| b8c2s32 | 8 x 256 | 512 | 32 | 285,955 | +19.3% | … | |
| b16c8s32 | 16 x 128 | 1024 (32/worker) | 32 | 266,229 | +11.0% | … | |
Reading: the resident-group size is the lever (512 agents = 16/worker: +26%; 1024 = 32/worker: +11%), longer residency helps up to 64 steps,
and 4 buffers per group hide inference better than 2. No code change: PUF_COHORT_BUFFERS=4 PUF_COHORT_STEPS=64 with --vec.num_buffers=16.
15M/2048 complete: ctrl 233,487 / 233,395 (233,441); b16c4s64 262,408 (+12.4%); b16c4s128 261,475 (+12.0%); b16c4s16 252,945 (+8.3%);
b16c8s32 252,098 (+8.0%); b8c2s32 216,038 (−7.5%: two buffers per group cannot hide the 15M inference → bubbles).
RECOMMENDED DEFAULT for collection-bound regimes: --vec.num_buffers=16 PUF_COHORT_BUFFERS=4 PUF_COHORT_STEPS=64 (+26% at 5M/2048, +12% at 15M/2048).
Day total 5M/2048: ~219K (morning) → 303K (+38%).
NOTE: ablate_cohort512 (15M/512 cohort check, b4c2s64) started early (its wait matched the aborted first mt8 log) and overlaps mt8's build/verify/gates:
its 4 runs are perturbed by CPU contention and are indicative only (reported sps scales by 2048/512 = 4x). Rerun cleanly if the regime matters.
mt8 first verify: hash DIVERGED (7010264807c7d952) with "0 mismatches" — the twin's panics were silent to the harness (game ends, replay resets), and the
plane admitted map column 0 (move_columns index i = map column i-1; valid indices are 2..COLNO). Fixed both: column range, and panic → MFNDPOS_MISMATCH lines.
Note: killing a chain_step.sh does not kill its running native_screen2.sh/replay children; they must be stopped separately (done).

## mt8 (per-turn movement-class planes) — DROPPED (2026-10-11 ~08:10 UTC)
Verify twin 0 mismatches, obs b79eb25d93ca6d29, turns 115413681; quick gates 5/5. ABBA vs mt7 (clean screen, nothing else running):
| games | ctrl a/b | cand a/b | delta |
|---|---|---|---|
| 512 | 319,989 / 319,463 | 313,295 / 313,023 | −2.1% |
| 2048 | 248,096 / 248,255 | 240,647 / 241,623 | −2.8% |
Negative in both regimes → dropped; full gate cancelled (not needed for a dropped layer), census kept for the record (ir_compare lines_mt7 lines_mt8 below).
Lesson (with mt4): the cell-by-cell mfndpos loop is cheaper than any mask assembly for a 3x3 neighbourhood — 8 candidates per monster is too small a
batch to amortise building a plane, and the per-turn planes add a second data structure (8 x 81 words) to the working set. Phase 3 final stack stays mt7.
mt8 census: 520.2K → 522.7K instructions/step (+0.47%), mfndpos_masked 88.6K → 88.9K. Instructions flat, clock −2..−3% ⇒ the loss is data
(8 x 81-word planes + three column lines per neighbourhood), confirming the Phase 4 reading: at 16 games/worker the engine is at the L2 edge and any
new per-game structure costs more than it saves. Chain closed 09:11; pool-timing anatomy (chain_pooltiming.sh) started 09:11:49.

## Stage 4 RESULT — rollout anatomy (pool timing + rollout detail, 70-epoch runs, epochs 64-68; 2026-10-11 09:30)
| arm | batch ms | rollout_tail | per 128-agent buffer-step: env / model / copy ms | step period ms | pool busy est. |
|---|---|---|---|---|---|
| 5M ctrl 4x512 | 1072 | 553 | 6.7 / 0.36 / 0.49 (512 agents) | 8.4 | ~95% at 135 µs/game-step (64/worker) |
| 5M b16c4s64 | 867 | 325 | 1.04 / 0.29-0.39 / 0.13 | 1.69 | ~92% at 100 µs/game-step (16/worker) |
| 15M ctrl 4x512 | 1112 | 180 | 6.3 / 0.95 / 0.50 (512 agents) | 8.7 | — |
| 15M b16c4s64 | 1003 | 22 | 0.88 / 0.79 / 0.13 | 1.96 | ~79% (forward latency not hidden) |
Reading: (1) the cohort gain is exactly the per-game-step L2 cost (135 → 100 µs, the Stage 0 curve); the pool is near saturation in both 5M
configs, so there is no scheduling slack worth a patch at 5M (submitter tail 32-39% is the 1-of-33 thread waiting for the GPU, ≈3% of capacity).
(2) Forward latency is launch/contention-bound, not batch-bound: 0.36 ms for 512 agents vs 0.29-0.39 for 128 at width 512; 0.95 vs 0.79 at width
1024 (PPO sharing the GPU doubles it). (3) At 15M/2048 the 0.79 ms forward leaves ~21% of the pool idle; deeper pipelines cost L2 (b16c8 = 32/worker
lost), 2-deep cannot hide it (b8c2 −7.5%), and merging forwards needs lockstep buffers which kills the pipeline → dynamic batching is NOT the lever;
the lever is forward latency itself (kernel count / SM partitioning) and PPO (0.84 s alone, 0.98 under inference contention) — GPU-side work, ≤ +19%.
(4) 5M/2048: rollout 0.867 s vs PPO 0.544 s → the only remaining lever is per-game-step CPU cost (≈100 µs = 520K instructions at IPC ≈ 1).
Decision: no scheduler patch, no dynamic-batching patch. Deliverables: (a) cohort knobs as pufferlib [vec] ini keys (patch), (b) per-step engine
cost program (instructions + branches across all subsystems; footprint only insofar as it cuts L1 misses). Pool utilisation check running
(chain_util.sh: per-thread CPU over the window) to confirm the ~92% estimate.

## Instruction census by function, final engine (lines_mt7, callgrind Ir/step; FUNCTIONS_lines_mt7.txt, 2026-10-11 09:27)
520.2K instructions per policy step; top self-cost: m_move 97K (all inlined pieces), mfndpos_masked 88K, dochug 24.6K, newsym 23.4K,
nethack_pack_obs 26K (both levels), nh_fobj_next 23K, movemon 21K, isaac64 15.4K, mcalcmove 8.2K, vision_recalc 8.1K, show_glyph 7.0K,
minliquid 6.7K, mcalcdistress 5.9K, linedup/lined_up 9.6K, muse find_* 11.4K, fill_obs 5.5K. Monster turn ≈ 310K = 60% even after Phase 3;
display+vision ≈ 45K (9%); obs export ≈ 32K (6%); RNG 15K (3%). At 100 µs/step on a 5.7 GHz P-core that is IPC ≈ 0.9: the step is
branch/dependency-bound, not instruction-bound; branch census (footprint_branch.sh mt7 branch_mt7, callgrind --branch-sim) running to size it.

## Branch census, final engine (callgrind --branch-sim, 512 games x 128 steps; BRANCH_branch_mt7.md, 2026-10-11 09:35)
Per step: 520.2K instructions, 91.2K conditional branches, 5.4K mispredicted (5.9%), 0.5K indirect (14.9% mispredicted) → ~5,450 mispredicts/step.
Top: m_move 1,078 (8.3% of its branches), mfndpos_masked 753 (6.2%), newsym 387, nh_fobj_next 285, nethack_pack_obs 235, movemon 172, dochug 169,
vision_recalc 103, fill_obs 101; vision's right_side/left_side 13-15% rates (small), muse find_* 13%.
Time model per hyperthread-step (~100 µs ≈ 60 µs of a full core): instructions 520K @ IPC 2.5 ≈ 38 µs; mispredicts 5.4K x ~17 cycles ≈ 17 µs;
cache (I1 misses 1,910/step!, D1 1,290/step, L2 hits ~15 cycles) ≈ 9 µs; LL ≈ 3 µs. The instruction count is the biggest term and the monster
turn is 60% of it; I-cache misses (122 KB of code lines per step) are the second structural signal — the per-step code path is wide.

## Cohort ini keys — patch VALIDATED (2026-10-11 09:40; handoff/trainer_cohort_ini_keys.patch, built as 24h binaries/cohort_ini from trainer_cohort/source)
Keys: [vec] cohort_buffers (0 = off) and cohort_steps (0 = horizon) in config/default.ini; env vars PUF_COHORT_BUFFERS/STEPS still override. Fast protocol, 5M/2048, 44 epochs:
| arm (patched binary) | buffers | cohort source | SPS | BATCH_PROOF (44 epochs) |
|---|---|---|---|---|
| ini5_ctrl | 4 x 512 | none | 239,009 | reference |
| ini5_env | 16 x 128 | PUF_COHORT_BUFFERS=4 PUF_COHORT_STEPS=64 | 298,293 | identical |
| ini5_keys | 16 x 128 | --vec.cohort_buffers=4 --vec.cohort_steps=64 | 296,658 | identical |
Rollout obs hashes identical across all three arms (the schedule is trajectory-invariant under a frozen policy); weights unchanged (initial == final checkpoint sha).
Harness: run_scale.py gained --extra (passthrough args) and --source (trainer cwd/source tree); the trainer reads config/default.ini from its cwd, so a patched
binary must run from the patched tree (landmine: "missing key [vec] cohort_buffers" otherwise). Utilisation pair (chain_util4.sh) pending.

## Pool utilisation, measured (per-thread CPU time over an in-run window; thread_util.sh; 2026-10-11 09:55)
Control 4x512 (util4_ctrl, 239,061 SPS): 48 threads; the 32 pool workers at 0.87-0.92 each (≈ 29 cores of 32 hyperthreads), the 4 buffer threads at
0.59-0.60 (claim + tail spin), main 0.05. The pool is ~90% busy in the control → the cohort gain (+25%) is per-step cost, not recovered idle.
Sampler landmines: the trainer tears its pool down ~2 s before exit (a window reaching the end sees 6 threads); 44-epoch runs are 38 s (cohort) / 47 s (control)
including ~4 s startup, so windows must sit inside [6 s, wall-3 s]. Cohort sample rerun as util6_env (window 12-28 s).
Cohort 16x128 g4 s64 (util6_env, 300,232 SPS): 54 threads; the 32 pool workers at 0.76-0.78 each (≈ 24.6 cores), 16 buffer threads 0.13-0.16, main 0.07;
26.9 cores total vs 31.0 in the control. So the cohort config leaves the pool 23% IDLE (control 10%) while cutting per-step cost ~35%: there IS scheduling
slack, ≈ +17% if the workers were as busy as in the control (303K → ~355K at 5M/2048), and the earlier "no slack" reading (from submitter tails) was wrong.
HYPOTHESIS (convoy): the 4 buffers of a group share the pool, so their env phases lengthen together and they fall into lockstep; then all four are in their
GPU phase at the same time (forward 0.35 + copies/sync ≈ 0.5 ms of a 1.69 ms period ≈ 30%) and the pool starves. The control's env phases (6.7 ms) dwarf its
GPU phases (0.9 ms), so convoying costs it little. Test: PUF_COHORT_ACTIVE = max buffers of a group in their env phase at once (semaphore around ep_run);
ACTIVE=2 should force alternation (2 in env, 2 on the GPU) and lift utilisation. Proof gate: BATCH_PROOF unchanged (trajectory-invariant).

## PUF_COHORT_ACTIVE screen — convoy hypothesis REFUTED (2026-10-11 10:03; binary cohort_act, 5M/2048, 16x128 g4 s64 via ini keys)
| cap on buffers in env phase per group | SPS | proof |
|---|---|---|
| none (ctrl) | 298,186 | reference |
| 1 | 110,435 | identical |
| 2 | 279,644 (−6.2%) | identical |
| 3 | 284,465 (−4.6%) | identical |
act2 utilisation 26.0 cores (uncapped 26.9): the cap does not raise worker busy time, it only removes overlap. The idle is not a convoy.
Next hypothesis: pool WAKE LATENCY. Workers sleep on a condvar whenever no region has unclaimed work; every region activation (one per buffer step,
~4 per 1.7 ms period) broadcasts to 32 sleeping workers, and futex wake + scheduling costs each worker tens of µs per activation — negligible when
regions last 6.7 ms (control: 90% busy), ~20% when they last 0.4-1.0 ms (cohort: 77%). Test: PUF_POOL_SPIN_US — workers spin (pause) for a bounded
budget before sleeping. Semaphore knob stays in the source (default off) for the record.

## PUF_POOL_SPIN_US screen — wake-latency hypothesis REFUTED (2026-10-11 10:06; binary cohort_spin, 5M/2048 cohort config)
spin_ctrl 299,077 | spin100 289,569 (−3.2%) | spin300 268,784 (−10.1%; utilisation 29.3 cores vs 26.9 — the spin itself) | spin1000 / spin_sleeptail pending.
Spinning costs more than the wake latency it hides, and more with budget. Reading: the "23% idle" is logical-CPU idle on a hyperthreaded part
(8 P-cores x 2 + 16 E-cores): an idle hyperthread hands its physical core to its sibling, so the siblings run faster and the idle is largely fake
capacity. Any scheme that keeps all 32 logical CPUs busy (spin) or removes overlap (semaphore) loses. Physical cores are near saturation in the cohort
config → the per-game-step CPU cost is the lever, as the 09:30 decision said; the 10:00 "correction" was the hyperthread illusion.
Follow-up screen queued (ablate_workers.json): 24 / 28 / 36 pool workers — does HT help or hurt this branchy integer workload at 16 games/worker?

## Pool size under the cohort config (2026-10-11 10:10; binary cohort_spin, 5M/2048 16x128 g4 s64, PUF_POOL_WORKERS; 32 = spin_ctrl 299,077)
w28 309,702 (+3.6%) | w24 319,929 (+7.0%) | w36, w26, w22, w20, w16 running. Fewer workers than logical CPUs is FASTER: with 16 resident games the
step is core-bound, and two hyperthreads per P-core slow each other more than they add; 24 workers ≈ one per physical core (8P + 16E).
Note the group stays 512 agents, so games per worker rise (24 → 21, 16 → 32) past the L2 knee and it still wins → HT contention outweighs L2 here.
Full ladder (5M/2048, cohort config, PUF_POOL_WORKERS; single runs, repeat spread of this config ≈ ±1.2%):
| workers | 16 | 20 | 22 | 24 | 26 | 28 | 32 | 36 |
|---|---|---|---|---|---|---|---|---|
| SPS | 278,648 | 309,213 | 315,171 | 319,929 | 321,942 | 309,702 | 299,077 | 294,811 |
Peak 24-26 (one worker per physical core, +7..+7.6% over 32); all proofs identical. 15M/2048 check (32/24/20) running: chain_workers15m.sh.
Open: with 24 workers the 512-agent group is 21 games/worker; a 16/worker group needs 384 agents = 3 x 128, which 16 buffers cannot form
(cohort must divide num_buffers) — a 2304-agent config (18 x 128, cohort 3) would test it but changes the regime.
15M worker check, first attempt INVALID: the spec generator turned args into a dict, so the two --extra entries collided and --vec.cohort_buffers=4 was
dropped (cohort OFF; w15m_32 229.6K / w15m_24 227.1K are 16x128 FREE-RUN numbers, ≈ the 4x512 control 233K — a useful aside: 16 small buffers without
grouping are not slower than 4 big ones). Rerun with both keys (ablate_workers15m.json regenerated with an assert on the --extra count); the rerun's
32-worker arm was then killed by my own cleanup pkill (pattern matched the new trainer) → chain_workers15m_fix.sh reruns it. LANDMINES: never dict()
an args list that repeats a flag; a pkill aimed at a stale trainer also hits the next arm if the campaign has already moved on — kill the campaign first,
then wait for the GPU to be free, then kill the trainer.
15M/2048 worker check (cohort config, corrected spec): 32 → 261,568 | 24 → 263,175 | 20 → 263,233; proofs identical. Neutral: the 15M regime is balanced
against PPO, so the pool size only matters where the CPU binds (5M/2048: +7%). Recommendation stands: 24-26 workers with the cohort config.

## PHASE 4 FINAL LEDGER (2026-10-11 10:40)
| step | 5M/2048 | 15M/2048 | 15M/512 |
|---|---|---|---|
| morning (4x512, 32 workers) | 239,730 | 233,441 | 228,5xx (GPU-bound) |
| cohort knobs 16x128 g4 s64 | 302,434 (+26%) | 262,408 (+12%) | 0 |
| + 24-26 pool workers | 319,929-321,942 (+34% total) | 263,175 (+13% total) | — |
Delivered: handoff/trainer_cohort_ini_keys.patch (validated, proofs identical), HANDOFF.md close-out + addendum. Refuted: convoy cap, worker spin.
Remaining lever at 5M/2048: per-game-step CPU cost (520K instr, 60% monster turn; 5.4K mispredicts; I1 1,910 misses) — engine work, not scheduling.

## Batch scaling at 4096 agents (2026-10-11 11:05; SPS from BENCH_CLOCK via sps_from_log.py, batches 15..20 after 8.4M warm-up steps; runner cannot count 4096 batches)
| regime | 2048 control (4x512) | 2048 cohort + 24-26 workers | 4096 control (4x1024, 32 w) | 4096 cohort (32x128 g4 s64, 24 w) |
|---|---|---|---|---|
| 5M | 239,730 | 319,929-321,942 | 253,862 | 344,115 (+36% vs its control, +7.5% vs 2048 cohort) |
| 15M | 233,441 | 263,175 | 247,669 | 262,961 (+6% vs control; = 2048 cohort → PPO-bound) |
Reading: the env side is now batch-invariant (the resident group is 512 agents whatever the batch), so SPS rises with agents at 5M instead of sitting on
the L2 plateau; at 15M the GPU/PPO side caps both batch sizes at ≈ 263K. Harness fix: run_scale.py --buffers choices now include 32/64.

## Shape probes (2026-10-11 11:25; cohort config, 24 workers; ablate_shapes.json; SPS from BENCH_CLOCK)
8192 agents at horizon 128 does not fit the 4090: 8.3 GB at 2048, 15.5 GB at 4096 → both 8192 arms died at start-up (5M cudaGraphInstantiate,
15M cuBLAS workspace cudaMalloc). No horizon-64 variant was run (user stopped it).
| arm | SPS | batch s | rollout s | PPO concurrent s |
|---|---|---|---|---|
| 5M/2048 mb 4096 (ref) | 302K | 0.867 | 0.867 | 0.544 |
| 5M/2048 mb 32768 | 299,208 | 0.854 | 0.854 | 0.435 |
| 15M/2048 mb 8192 (ref) | 262K | 0.995 | 0.995 | 0.984 |
| 15M/2048 mb 32768 | 259,036 | 1.011 | 1.011 | 0.805 |
| 15M/4096 mb 32768 | 266,495 | 1.957 | 1.957 | 1.617 |
CORRECTION: the 15M regime is ROLLOUT-bound, not PPO-bound. A 4x larger minibatch cut PPO by 18% and SPS did not move, because the rollout stays at
1.0 s per 262K steps: the per-buffer step period (env 0.88 + forward 0.79 + copies 0.13 ≈ 1.96 ms per 512-agent group step) sets it, and the forward
latency barely depends on PPO contention. So the 15M lever is the actor forward itself (0.79 ms for 128 agents at width 1024 — kernel count / gaps inside
the graph), not Muon. 5M: collection-bound as before; minibatch irrelevant to throughput there.

## TARGET SET BY USER (2026-10-11 11:40): env side only; 500K SPS on this box, 1M on a bigger box. Motivation: sweeps that explore more rollouts, faster.
Ceiling arithmetic: pool-bound at 343K (24 workers x ~70 µs/game-step) — 5M/4096 is already there. 500K needs −31% per-step cost or equivalent cores.
Ladder (expected): (1) host-thread noise off physical cores (PUF_POOL_SLEEP, PUF_CPU_AFFINITY; running: ablate_knobs4k.json) 0..+5%;
(2) heterogeneous ownership (P-cores 2 MB L2 vs E-cores 512 KB; weighted stripes + HT on P) +10..15%, needs per-worker step stats first;
(3) pipeline depth 8 at 15M (64-agent buffers) +14% at 15M; (4) display/vision/obs-export bit-exact pass +5..8%; (5) exact 16/worker groups +3%.
Stacked ≈ 440-460K at 5M/4096. The last 10% is the monster turn → needs RNG-order freedom (declined so far). 1M on a bigger box: env scales with
cores (~14K steps/s/core here → ~70 such cores), the 4090's PPO (~485K steps/s at 5M) becomes the limiter → GPU question too.
Landmine: PUF_CPU_AFFINITY in the experiment trainer asserts num_buffers == 4 (submitter pinning) → the pin arms of knobs4k will fail with 32 buffers.

## Knob screen 5M/4096, 24 workers (2026-10-11 11:55; ablate_knobs4k.json, SPS from BENCH_CLOCK)
ctrl24 344,824 | PUF_POOL_SLEEP 348,737 (+1.1%) | 26 workers + sleep 348,901 (+1.2%); proofs identical. Host-thread noise ≈ 1%: ladder item (1) closed.
Pin arms crashed on the trainer's `assert(vec->buffers == 4)` submitter pinning → generalised (pin submitters only when 4 buffers; workers: 24 → one per
physical core, 32 → one per logical cpu) in trainer_cohort/source + per-worker stats (PUF_POOL_WORKER_STATS=<first epoch>: POOL_WORKER id steps busy_ms
us_per_step) → binary cohort_pin, chain_pinstats.sh (pin24 / unpin24 / pin32 at 5M/4096).

## Per-worker cost by core type (2026-10-11 ~12:10; cohort_pin, 5M/4096, PUF_POOL_WORKER_STATS; CPU time per game step, worker side only)
| arm | SPS | P-core workers µs/step | E-core workers µs/step |
|---|---|---|---|
| 24 pinned (one per physical core) | 350,061 | 41-52 (mean ≈ 45) | 53-61 (mean ≈ 56) |
| 24 unpinned | 341,100 | 50-60 mixed (mean ≈ 55) | |
| 32 pinned (one per logical cpu) | 301,668 | 54-65 (two HT per P-core) | 53-64 |
Findings: (1) E-cores are only ~25% slower per step than P-cores and stealing already balances the load (P workers stepped ~25% more games) →
weighted P/E ownership (ladder item 2) is worth little; dropped. (2) Pinning one per physical core: +1.5..2.5% (keep: PUF_CPU_AFFINITY=1 at 24 workers).
(3) THE GAP: CPU-time capacity = 8/45 + 16/56 = 464K steps/s, achieved 350K → ~25% of pool time is not spent stepping: off-CPU (host threads
sharing the 24 cores: 16 buffer threads, main, CUDA), pool overhead (region scan: every wake scans all 32 regions taking each mutex), or idle
(no claimable region). Next instrument: per-worker wall split busy / scan / sleep + off-CPU (wall − cpu) → cohort_pin2.

## Pipeline depth 8 — DROPPED (2026-10-11 ~12:25; cohort_d8, 64-agent buffers x 8 per group, same 512 resident, 24 workers)
| arm | depth 8 (64 x 8) | depth 4 (128 x 4) |
|---|---|---|
| 15M/2048 | 249,725 | 263,964 (same binary) |
| 15M/4096 | 250,034 | 262,961 |
| 5M/2048 | 312,010 | 319,929-321,942 |
−3..−5% everywhere; proofs identical to the 128-agent layout (the replay now maps agent slot s to stream s mod 128 for sub-frame buffers).
The queue model's assumption (GPU think time independent of region size) fails: each 64-agent forward costs the same 0.79 ms as a 128-agent one,
so depth 8 doubles GPU inference traffic and doubles the pool's region-scan work per step. Ladder item 3 closed. Replay relaxation kept (harmless).

## Pool wall-time split, 24 pinned workers, 5M/4096 (2026-10-11 ~12:35; cohort_pin2, epochs 17-21 = mature games; split24_pin 350,885 SPS)
Per worker: stepping (on CPU) 90.6% of wall | sleeping (no claimable region) 8.9% | region scan 0.4% | off-CPU while claiming 0.1%.
Steady-state cost per game step: P-cores 51-67 µs (≈ 59), E-cores 65-79 µs (≈ 71) — the earlier 45/56 figures included the cheap warm-up epochs.
CPU-time capacity at these costs = 8/59 + 16/71 = 361K; achieved 351K = 97% of busy-capacity; pool 91% busy. THE POOL IS SATURATED.
The "25% gap" is resolved: it was warm-up-biased µs/step, not lost time. Host threads cost nothing measurable (off-CPU 0.1%); scan is nil.
Why 32 workers lose (301K): with 4 regions of 128 in flight the pool runs out of claimable games — at 32 workers each region is drained in ~4 steps
per worker (~0.25 ms) and the GPU round trip (~0.6 ms) cannot refill it; deeper pipelines cost L2 (b16c8: 32 games/worker) → 24 is the balance point.
CEILING at current per-step cost ≈ 385K (idle → 0). 500K requires ≈ −30% per game step. Scheduling line CLOSED (+9% banked: 24 workers + pinning;
convoy cap, spin, depth 8, heterogeneous ownership, host-thread knobs all null or negative).

## ITEM 1 OPENED (2026-10-11 ~12:50, user: "Do 1 for now"): bit-exact pass on display / vision / observation export
Census (lines_mt7, per policy step): newsym 221 calls, 33.8K incl (≈150/call) + show_glyph 223 calls 8.1K; vision_recalc 1.38 calls, 21.3K incl
(right/left_side 10.4 calls, clear_path 10.3); nethack_pack_obs self 26K (1 call); fill_obs 5.5K; bot 2.6 calls 1.7K; flush_screen 9.9 calls 8.0K.
Workload fact behind it: 12.6 movemon rounds and 110 m_move calls per policy step (multi-turn occupations: eating/searching) → the 221 newsym calls
are the two per monster move, most of them for cells the hero cannot see.
QUESTION: can display+vision+obs-export (≈85K instr/step, 16%) be cut by ≥ 1/3 with identical observations and identical game state?
DECISION RULE (per layer): verify twin 0 mismatches over the gate corpus (obs b79eb25d93ca6d29, turns 115413681) → quick gates → ABBA vs mt7 not negative
at 512 and ≥ +1% at 2048 → full every-action gate 0/16,777,216 → census confirms the cut. Candidates: (a) skip-equivalent newsym for unseen monster moves
(must replicate newsym's branch conditions exactly; gbuf/lev->glyph identical), (b) packer dirty-cell path, (c) vision inner loops, (d) bot/fill_obs trims.

## dv1 (2026-10-11 ~13:15): nh_newsym_moved() at the two display refreshes of a monster move — RUNNING (chain_step2.sh dv1 mt7; verify define NLE_DISPLAY_VERIFY)
Facts: 86 monster moves per policy step → 172 of the 221 newsym calls (newsym ≈100 instr + show_glyph ≈35 each; 23.4K + 7.0K self per step).
Most are out of the hero's sight, where newsym() ends in show_glyph(lev->glyph), a no-op when the screen buffer already shows the remembered glyph.
Fast path: fall through to newsym() unless (out of sight, not hero square, not swallowed/underwater/rogue level, no sensing possible for a monster
there [Blind&&Blind_telepat, Unblind_telepat, Warn_of_mon, Detect_monsters, !Blind&&Infravision, Warning all false], no lit-memory fixup pending,
gbuf_glyph == lev->glyph) → skip. Twin: on skip, run newsym() and compare gbuf glyph/changed/bbox and lev glyph/waslit/seenv → NEWSYM_MISMATCH.
Expected: ≈ −16K instructions/step (−3%); clock decides.
dv1 verify: 0 mismatches over the corpus, obs b79eb25d93ca6d29, turns 115413681; quick gates 5/5. The fast path skipped 97.9% of the move-time
refreshes (1,820,327,936 skips vs 38,793,993 fall-throughs), every skip checked against the real newsym(). Native ABBA vs mt7 running.
dv1 ABBA vs mt7 (clean screen): 512: ctrl 320,451 / 321,337 vs cand 320,312 / 321,085 (−0.06%); 2048: ctrl 249,384 / 249,783 vs cand 250,300 / 250,572 (+0.34%).
Flat on the clock despite skipping 98% of 172 refresh calls per step. Full gate ∥ census running; the census says how many instructions went.
Reading (if the census confirms ≈ −16K): removing cheap, well-predicted instructions does not move this clock — the step is bound by the monster
turn's mispredicts and misses, so the instruction census overstates what display/vision/obs trims can buy. Below the +1% rule → not a keeper on its own.
dv1 census: 520.2K → 520.8K (+0.12%): nh_newsym_moved costs 17.9K for 173 calls = 103 instr/call — the same as newsym's unseen path (newsym 24.9K →
12.3K, show_glyph 8.1K → 3.5K). The "fast path" re-did newsym's checks (Blind/telepathy/warning/infravision property lookups, m_at, Is_rogue_level,
gbuf blob call): newsym's unseen branch IS those checks. Full gate 0/16,777,216. dv1 = null on instructions and clock → DROPPED as built.
dv2: hoist the hero-global part (sensing flags, rogue level, mklev, background glyph, dark_room) into one per-movemon() flag (recomputed at
movemon entry and invalidated by make_blinded), leaving ~25 instr per call: cansee, hero square, uswallow/underwater, lit-memory fixup, gbuf compare.
Expected −13K/step; this is the real test of whether cheap instructions move the clock.
dv2 verify: 154 NEWSYM_MISMATCH in 16.7M steps (a monster displayed on an out-of-sight square while the per-movemon flag said no sensing was
possible): sensing can switch ON mid-movemon without make_blinded() — a blindfold stolen (Blindf_off → !Blind → infravision), the hero's form
changing when a polymorphed hero dies (rehumanize → set_uasmon → infravision/eyes). Chain stopped; its first 512 readings were flat again
(ctrl 321,811 vs cand 322,677 / 322,048). dv3 = dv2 + flag cleared in Blindf_on, Blindf_off, set_uasmon; the twin decides coverage.
dv3 (dv2 + invalidation in Blindf_on/Blindf_off/set_uasmon): verify 0 mismatches (obs b79eb25d93ca6d29), quick gates 5/5. ABBA vs mt7:
512: ctrl 321,997 / 322,931 vs cand 322,924 / 320,601 (−0.2%); 2048: ctrl 250,584 / 249,960 vs cand 252,149 / 250,724 (+0.47%). Full gate ∥ census running.
dv3 census: 520.2K → 517.2K (−0.57%, −3.0K). newsym 24.9K → 15.7K only: the per-movemon flag is 0 for most heroes (non-human races have
Infravision; several roles gain Warning; worn telepathy) so most move squares fell through; nh_newsym_moved 49 instr/call. Full gate 0/16,777,216.
Exchange rate observed: −0.57% instructions → +0.47% clock, i.e. cheap instructions DO move this clock ~1:1 — dv1's "null" was no cut at all.
dv4: keep the hoist but as a sense BITMASK (tp-blind, tp, warn-of-mon, detect, infra, warning, special) and apply newsym's exact per-monster
predicates per call only when a monster stands on the square (vacated squares skip the monster test entirely) → expect dv1's 98% skip rate at
~40 instr/call ≈ −15K/step.
dv4 verify: 0 mismatches (obs b79eb25d93ca6d29), skip share 97.7% (2,365,587,456 skips / 54,489,443 fall-throughs), quick gates 5/5. ABBA vs mt7 running.
dv4 ABBA vs mt7: 512: ctrl 320,820 / 321,212 vs cand 325,349 / 325,055 (+1.30%, both pairs agree); 2048: ctrl 251,227 / 250,787 vs cand 251,743 / 252,009 (+0.35%).
RULE UPDATE: the trainer now runs the cohort config (16-21 games per worker, L2-resident), which is the 512-game harness regime, not the 2048 one
the old "≥ +1% at 2048" rule assumed. From here the representative number is 512 (≥ +1%), with 2048 only required not to lose. dv4 passes.
Full gate ∥ census running.
dv4 census: 520.2K → 511.9K (−1.60%, −8.3K); full gate 0/16,777,216. KEPT: Phase-1 engine stack becomes mt7 → dv4.
Exchange rate: −1.6% instructions → +1.3% clock at 512 (the trainer's regime), +0.35% at 2048. Per-call cost of the fast path ≈ 40 instr incl. the
m_at load; the hoist removed the property lookups. Display refresh work per step is now ~8K instead of ~31K.

## dv5 (lazy screen flush) — RUNNING (chain_step2.sh dv5 dv4): flush_screen() marks pending; nh_flush_deferred() runs the real print (+bot) at
the top of the window port's fill_obs(), i.e. once per observation instead of ~10 times per policy step (moveloop 6.8, vpline 1.8, rhack 1.0).
Same final screen store; the corpus obs hash is the verifier. Expected ≈ −6K/step (flush_screen 8.0K incl. print_glyph → ~2.4 real flushes per step).
dv5 verify: corpus obs hash identical (b79eb25d93ca6d29) BUT the golden gate FAILS: aa_seed7001/7002/7003 HASH MISMATCH at steps 21-23 (after action 98).
The goldens hash something the packed corpus obs does not (tty mirror fields, or status-line values that the deferred bot() now computes at
observation time instead of at the eager flush — NLE's blstats are "as last drawn", i.e. deliberately stale). Chain stopped; diagnosing.
dv5 DROPPED: replay_golden hashes glyphs + chars + colors + specials + blstats + message; chars/colors/specials come from mapglyph() at PRINT time
(object-pile flag, hero square, colour rules), so NLE's reference observation carries the values as of the eager flush. Deferring the print to
observation time makes them fresh instead of stale → 3/34 goldens diverge at the first pile/pet interaction. Lazy flushing cannot be bit-exact at the
NLE level; the corpus hash passed only because the packed training obs does not use chars/colors/specials. Lesson: the golden gate is the contract.
ITEM 1 CLOSES with dv4 (+1.3% at 512, +0.35% at 2048, −1.6% instructions). Remaining display/vision/obs items are each ≤ 1% or algorithmic (vision).
Landing chain first attempt: all 8 arms died on `assert(vec->buffers == 4)` — binary cohort_spin predates the pinning generalisation
(PUF_CPU_AFFINITY with 32 buffers). LANDMINE: pinned cohort configs need cohort_pin/cohort_pin2/cohort_d8 (all from trainer_cohort/source). Rerun on cohort_d8.

## dv4 landing in the trainer (PGO vs PGO, cohort regime 24 workers pinned, binary cohort_d8; SPS from BENCH_CLOCK; 2026-10-11 ~17:00)
5M/4096: ctrl mt7_pgo 349,484 / 350,317 vs cand dv4_pgo 349,756 / 351,971 → +0.28% (noise band ±1%). 15M/2048 pending.
Reading: the harness's +1.3% at 512 (plain builds) shrinks to ≈ +0.3% once both engines are PGO'd and the pool is 91% busy — PGO already lays out
newsym's cold branch well, and 8K instructions of a 512K step is 1.6% at best. dv4 is correct and gated but marginal in production.
15M/2048: ctrl 264,041 / 262,762 vs cand 262,943 / 262,694 → −0.2% (noise). Proofs identical both regimes. dv4 in the trainer = NEUTRAL (+0.3% / −0.2%).
ITEM 1 VERDICT: the display/vision/obs pass yields nothing measurable in production. Engine stack for the handoff stays mt7 (dv4 offered as an
optional, gated, neutral layer). The per-step cost that matters is the monster turn; bit-exact restructuring of it is exhausted.
