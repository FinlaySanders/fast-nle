# Selective review of perf-planes-wip

Reviewed `c967fcf7c54e6210f73b8c42209eaefbd9399042` directly. Its commit explicitly records three golden failures (hea1006 step140, aa7003 step38295, aa7010 step36010). It bundles observation-export changes, an allocator, multiple spatial indexes and monster logic changes across33 files. Do not cherry-pick wholesale.

Candidates to isolate, subject to current profiles:

* `set_apparxy`: currently walks hero inventory via `money_cnt(invent)` for every monster, but only a xorn uses the result. The parked patch defers the walk until that branch. Smallest independent candidate; must confirm money_cnt has no side effects and that any intervening functions cannot modify inventory before moving it.
* Trap lookup: replace ftrap walk with per-cell first-match pointers. Preserve linked-list precedence for duplicate positions; update creation/deletion/level transitions. Extra memory ~13KB per environment. Verify pointers against list at mutation boundaries.
* Engraving lookup: same first-match rule and similar memory. Relocation must invalidate both old and new coordinates. The parked patch also contains player-visible engraving-belief edits; exclude these from a performance-only extraction.
* Floor-object index: preserves fobj order but filters spatial candidates. More mutation sites and fallback capacity handling; not first choice without a substantial profile hotspot.
* Scare checks: rearrangement and necessary-condition guards need special-coordinate (0,0) and displaced-hero handling. Avoid assuming boolean reordering is safe if a subcall consumes RNG.
* Track occupancy: maintains auxiliary counters/bitsets on track insertion/reset. Worth considering only if gettrack is significant in a representative profile.
* Arena allocation: deferred. It changes lifetimes/allocation reuse, and the bundled commit already fails correctness; first try simpler independent optimisations.

None of these parked changes has been applied or accepted in this campaign yet.

## Late score profile follow-up

The top-score episode's final sampled window attributes28.27% of instructions to m_move itself. Annotated source shows roughly89.6M instructions in the bounding-box predicate and76.2M in the fobj linked-list iteration. This makes the compact ordered index more promising than trap lookup (2.23%) for this workload.

Correctness constraints from current source inspection:

* Preserve fobj traversal order exactly. Each successful candidate changes minr and bounds; later equally distant items can replace the target.
* Skip only entries outside the current bounds (and optionally plain ROCK, which currently returns immediately without side effects). Do not reorder calls to touch_artifact, can_carry, onscary or searches_for_item.
* A cache must invalidate on place/remove, split and replacement, restore-chain reversal, level clear/free and any coordinate mutation bypassing place/remove. Pointer-to-head equality alone is insufficient.
* Overflow must fall back to the original linked list, not silently drop items.
* A diagnostic build should compare cached pointer order and coordinates with the full list, without consuming RNG or allocating during verification.
* Account for per-environment memory. Keep generated context fields separate from serialized game structures so saved-data compatibility is not accidentally changed.

The smaller money_cnt change is already isolated as candidate03. Source inspection confirms that function only follows nobj links and reads coin quantity; the code between its old and new call sites only reads monster/player fields. Timing is still pending; no claimed speedup yet.

### Floor index audit detail
The WIP nh_fobj_next_in keeps a numeric iterator into a rebuilt array. If touch_artifact or a downstream callback mutates the floor list during a search, dirty/rebuild plus old numeric index can skip/revisit entries. A fresh implementation must explicitly reason about mid-iteration mutations, not only invalidate between calls. This is an additional reason not to import the WIP bundle. Smaller independent should_displace guard: no ALLOW_MDISP in any candidate implies FALSE and skips no side effects because undesirable_disp is only reached under that bit. Candidate not applied.

## New ordered-cache candidate (prepared, not validated)

`engine-floor` isolates this idea on candidate03, excluding04 and the other WIP planes/allocator. Cache stores up to2048 pointers and signed coordinates in fobj order, ~24KiB/context. Overflow walks the original list. Each iterator records generation; if a mutation happens during search, it permanently resumes the original `prev->nobj` walk rather than rebuilding and reusing a numeric cursor. Bounds remain live and may shrink after each selected object. Calls that can consume RNG remain in original order in m_move.

Explicit invalidation: place/remove/split/replace, restore-list reversal/replacement, free/reset, clear_level_structures (level.objlist spelling), each public nle_step and each movemon pass. Swallowed ball/chain coordinate updates operate only on OBJ_FREE; observed container coordinates resolve to the same existing floor location. Remaining direct-coordinate paths require diagnostic replay coverage; do not infer complete correctness from this source audit alone. Diagnostic build compares every cached pointer/coordinate against the full list at use. Engine cursor unit exercises shrink, mutations, overflow, empty. No performance result or acceptance yet.
