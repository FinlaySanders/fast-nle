# Optional allocator tuning

The installed `/lib/x86_64-linux-gnu/libtcmalloc_minimal.so.4` loaded via per-process `LD_PRELOAD` improved matched mature-score rollouts by2.02% and1.51% in two ABA screens. Peak memory rose by about47MB (1.93GB to1.98GB). The executable, engine and24-worker shared-pool setting were unchanged.

All32 observation block hashes, starting RNG and loaded weights matched. Full32 score and512 depth recorded streams passed (4,472,832 and23,855,104 decisions). Loaded training was flat; see `../alloc94-training/summary.json`. This is an optional runtime tuning result, not part of the retained default or its47.65% combined claim. No system allocator settings were changed.
