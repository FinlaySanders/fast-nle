Verification contract for the engine (replay_golden gate: FNV-1a over glyphs, chars, colors, specials, blstats, message):
goldens/ (34) and fuzz/ (26) golden trajectories, gates/ binaries, dat/ = NetHack data dir used by the gates.
Not here (too large for GitHub): the 512 x 32768 recorded-action corpus (1.3 GB) and the 16,777,216 reference decision hashes
(129 MB, final_hash_opt61/hashes.bin) — host disk ~/puffertank/nethack-backup-20261011/oracles/. Both can be regenerated from the
recorders (tools/record_goldens.py; the corpus from a policy run) but the exact bit-for-bit continuity with past gates would be lost.
