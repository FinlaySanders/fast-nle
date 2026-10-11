# Engine backup — 11 October 2026
Tip of this branch = mt7 stack + dv4 (two commits above the 8 October state). mt7 is the recommended engine; dv4 is an optional, gated,
production-neutral layer (its parent commit is the mt7 tip). Ledgers, generators (make_*.py), gates (chain_step*.sh), footprint/branch censuses
and the engine patches against the fork head and against mt7 are under engine-scaling/. Companion: the same branch in PufferLib
(trainer cohort patches, trainer overlay, 24h harness). Verification: corpus obs hash b79eb25d93ca6d29, every-action gate 0/16,777,216.
