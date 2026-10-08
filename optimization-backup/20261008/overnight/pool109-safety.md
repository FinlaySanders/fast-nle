# Cost-ordering experiment 109: pre-test audit

This is an isolated candidate, not a retained change. It adds per-region costs
and a permutation of local task indices. Sampling and sorting occur every
16 submissions, or sorting occurs when the range changes.

The submitter constructs the permutation while holding the region mutex before
publishing the region. It starts a new generation only after every prior reader
has released its lease. Workers read the permutation without modifying it.
Atomic strided counters still assign each permutation position exactly once;
a permutation therefore preserves exactly-once execution of every environment.
Each worker writes only its own claimed task's cost, before incrementing done
with release semantics. The submitter acquires done and drains reader leases
before reading costs or reallocating arrays. No new ordering of operations
within a game is introduced.

Count changes reconstruct the permutation; start changes also clear old costs.
Zero work does not dereference null arrays. Destruction frees arrays only after
joining submitters and workers, following the original pool contract.

The original stress changes size every round, so an additional stress holds
sizes constant across sampling intervals to exercise cached permutation reuse.
Both must pass before rollout timing. If timing wins, run sanitizer/race tests,
full recorded replay, a repeat and loaded training before retaining anything.
