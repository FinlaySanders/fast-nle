# Current mature-rollout bottleneck

2026-09-18. Retained engine61 + original sharedpool83,24workers plus4submitters,
512agents, four buffers, mature4Bscore policy. No model or engine semantics changed.

**CPU environment work remains the main limiter.** This profile covers rollout
collection, not PPO updates or end-to-end training.

## Lower-overhead CPU phase trace

`profile113/analysis.json`, a3.5-second interior window from a4-second capture,
starting25seconds into evaluation:

| Phase | Mean fraction of each coordinator's time |
|---|---:|
| Environment phase |76.96%|
| Waiting for GPU results |13.28%|
| GPU work submission |6.28%|
| Upload submission |1.94%|
| Other work / boundaries |1.54%|

Within the environment phase, submitters execute work for57.62% of their total
time, wait for outstanding tasks for18.49%, and drain reader leases for0.51%.
These subphases are INCLUDED in76.96%, not additional costs. The24worker threads
average23.33 concurrent work-claim ranges; ranges include execution, atomic
claiming and OS preemption, so this is not hardware CPU-utilisation measurement.

For29.42% of wall time all4coordinators are inside the environment phase and
there is no GPU graph or copy active. Another9.89% has no GPU activity but a mix
of CPU phases. This supports CPU supply as the main limitation. All4coordinators
simultaneously tail-waiting with no GPU activity occupies only0.0065% of wall
time: local tail waits exist, but a global all-buffer tail stall is uncommon.

## Individual GPU kernels

`profile112/analysis.json` uses node-level CUDA-graph tracing. In its interior
window, actual kernel intervals cover38.48% of wall time; copies cover19.49%,
and their union52.28%. They overlap, so do not add these percentages. Active
kernel intervals are not SM occupancy. Dominant summed kernel costs include
matrix multiplications, bias/ReLU kernels, recurrent gates and entity pooling.
Action sampling is4.15% of summed kernel duration in this trace, not4.15% of
end-to-end wall time.

Node tracing inflates mean graph-launch API duration to325microseconds versus
114microseconds in the lighter graph-level pass. Therefore use the lighter
pass for CPU phase attribution. Its graph envelopes plus copies cover60.37%
of wall time, but graph envelopes include internal gaps and are NOT kernel
utilisation. Neither profile supplies a clean uninstrumented throughput claim.

## CPU optimisation targets

Fresh late-game Callgrind profile110 points to observation construction16.5%
of instructions, m_move13.4%, mfndpos7.87%, fill_obs3.52%, and the floor-object
iterator2.37%. Other monster-AI work is spread across functions. These are
instruction shares from a separate fixed-action scene, not wall-time shares
for the whole rollout. Preserve that distinction.

Prioritise simulation and observation construction. GPU inference and transfers
still matter, but the evidence does not support replacing the CPU focus with
more wait-loop tuning or assuming the GPU is continuously saturated.

## Validation and reproducibility

Both passes match all32full-observation block hashes, initial GPU RNG states and
loaded checkpoint bytes against the retained rollout. See
`profile112/validation.json`. Sources are isolated in`profile112-source`;
production checkout remains unchanged. Scripts: `setup_profile112.py`,
`profile112.py`, `profile113.py`, `analyze112.py`, `analyze113.py`. Exact commands
are recorded in each profile's command.json. Nsight reports and SQLite traces
are local artifacts; they may contain process environment metadata.

The first113stats command hit Nsight's export timestamp check; reading the
already-exported SQLite directly succeeded (`profile113/stats-graph.txt`). The
profiled program and equivalence checks passed; this was report processing.
