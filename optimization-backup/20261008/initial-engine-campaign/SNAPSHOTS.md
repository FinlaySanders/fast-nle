# Raw observation snapshots

Optional `NH_PERF_SNAPSHOTS=/empty/directory` in the isolated v4 harness writes one `envNNNNN.obs` file beside each ordinary NHPERF2 trace. Timing mode rejects this option. Existing v3 timing binaries and original corpora are unchanged.

Each sidecar starts with `NHOBS001`. Records have a little-endian uint64 trace-event number, one byte event kind (S/K/F engine or O policy), followed by fields encoded as uint32 byte length and raw bytes. NULL buffers have length zero. This campaign uses the frozen Linux64 ABI; these are not portable save files.

Engine fields, in order: glyphs, chars, colors, specials, blstats, message, misc, internal, inventory glyphs, true inventory glyphs, letters, classes, inventory state, done, how_done, tty_chars. The last field includes the temporary identify-menu screen. The first15 reconstruct the pre-existing observation hash; tty_chars was omitted from that hash and is checked by comparing raw sidecar files. Other terminal and inventory-string sinks are NULL in this headless vec backend. Policy fields are the complete packed observation and complete action mask.

`check_snapshots.py TRACE SNAPSHOTS --heads 21` (20 for original score) checks all sidecar records against trace event IDs and legacy hashes. It rejects corrupt/truncated payloads and missing/duplicate/out-of-order observation records in the consumed trace prefix. It deliberately allows an unconsumed trace suffix for bounded replay. Hash validation alone does not prove tty_chars equivalence; fresh-recording validation also compares the full sidecar bytes via SHA256.

Two distinct provenance cases:

- Replay-generated snapshots: baseline verification reconstructs raw bytes and checks the original trace hashes. Useful for diagnosis; not original recorded observations.
- Fresh vec snapshots: bytes saved while the actual policy performs inference, followed by full baseline/candidate replay without inference and exact sidecar comparison. This is the stronger recording test.

Neither retroactively supplies raw bytes for the old14K-game recordings. Their known full-score baseline failure remains in BASELINE_MESSAGE_BUG.md. Snapshot implementation and live checks remain provisional until the result files explicitly show success.
