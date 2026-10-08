# Hero-gold absence cache

Retained on the isolated optimisation stack. No production changes or pushes.

The new cache stores only that the hero currently has no gold, in one cold byte per game context. It never stores an object pointer or quantity. Normal scans still handle unknown state, positive results, and monster inventories. Inventory insertion, object replacement and restoration invalidate absence. See ../gold60-audit.md for the mutation audit. NLE_GOLD_VERIFY scans the actual chain on every cached hit and panics on a stale absence.

Combined patch: ../retained-through-gold60.patch (10 files). It includes the earlier floor-index, SIMD match-mask, distant scare-check and movement-history changes. Frozen source: ../pgo61-source, source hashes: ../pgo61-source-manifest.json. Original 642-file baseline reverses exactly from this patch; forward application reproduces the frozen source. Writable data symbols are unchanged; context allocation owns the new byte.

Correctness: full selected32score and all512depth recordings with diagnostic cache checks; raw observation snapshots; same15 known raw historical export exceptions; explicit historical-view adapter passes34goldens/status/interleaved/shuffled and26fuzz cases with gold and floor diagnostics. No changed oracle or new exclusions.

Performance: repeated non-PGO score replay gains1.95%/2.31%, heldout1.32%; depth mixed, including a0.98% regression. Fresh matching PGO gives3.06% score gain and0.36% depth regression versusPGO44. Real fixed-policy rollout original controls24.665691/24.561175s, PGO44=21.366242s, PGO61=20.802041s for4,194,304measured decisions: combined18.32% higher throughput,2.71% overpreviousbest, control drift0.42%. Initial RNG and loaded weights match; all32 packed-observation boundary hashes match. Full replay is the separate action-level behaviour check.

Loaded training original26.320416/26.211750s versus24.624668s: observed combined6.67% gain. Different asynchronous trajectories mean this does not establish an incremental gold-cache training gain.

Reproduce in a fresh directory (do not overwrite recorded artifacts): copy ../pgo61.py and ../pgo61-source as engine-source, then run the copied script with the original ../pgo44/variant directory as its argument. This regenerates matching8score+8depth compiler profiles before building and measuring. Paths to preserved recordings, assets and build dependencies are in the script. Never reuse stale compiler profiles for changed source.
