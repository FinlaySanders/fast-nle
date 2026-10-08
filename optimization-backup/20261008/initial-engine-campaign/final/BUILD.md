# Retained build and patches

All work is isolated under `/puffertank/experiments/nethack-perf-20260917`. No production checkout edits or pushes are part of this campaign.

The retained game source is `engine-glyph-simd`, represented by `patch-review/candidate08.patch` against fast-nle commit `e7f6568568242745a7f7ebd8f730367123522cac`. `candidate08-proof.json` records clean application and exact resulting source hashes. Candidates09–12 are not included.

The fastest verified compiler build of that source is `variants/candidate14-lto-local/libnethack.so`, SHA256 `70fe544048cd5f9e159d98be3222f35536e508299228e88f61a3c10c968bc403`. On the tested Linux/GCC13.3 toolchain:

```sh
cmake -S engine-glyph-simd -B engine-glyph-simd/build-lto-local \
  -DCMAKE_BUILD_TYPE=Release \
  -DNLE_TLS_INITIAL_EXEC=ON \
  -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON \
  -DCMAKE_C_FLAGS=-fno-semantic-interposition \
  -DCMAKE_CXX_FLAGS=-fno-semantic-interposition
cmake --build engine-glyph-simd/build-lto-local --target nethack -j8
```

Run from the experiment root. Actual campaign commands also pin FetchContent dependency source directories; those exact commands are in `lto14-results.json`. These compiler flags were tested on Linux, where the existing engine already links with `-Bsymbolic-functions`. They are not a cross-platform validation claim. No fast-math flags were added.

The original mutable-global checker does not recognise GCC's LTO symbol suffixes and its C exception-personality reference. Its failure is preserved, not overwritten. `audit_lto14.py` and `lto-global-audit/proof.json` exhaustively check the eight differences against the baseline symbol inventory and ELF relocation. The whitelist and original checker remain unchanged.

Optional work stealing is separate: `patch-review/depth-ws.patch` and `score-ws.patch` target their respective frozen trainer source versions. They are scheduling changes only; do not replace a newer trainer with the old20-head score source. Production trainer sources have not been edited. `patch-review/scheduler-manifest.json` records the original/result hashes and defines. The experimental training binaries also contain checkpoint-loading/timing instrumentation; that instrumentation is not part of the proposed scheduler patch.

The floor-object cache adds24,592bytes per environment (about12MiB for512 environments). It preserves linked-list order, bounds changes and mutation fallback; overflow uses the original list. Both SIMD paths retain scalar fallbacks.

For result reproduction, use the exact per-arm commands in `combined512-results.json` and `training-combined/results.json`, together with the environment setup in `combined512.py` and `train_combined.py`, the frozen weights/corpora and the library hashes in `final-hardware-libraries.json`. Timing excludes recorded-game warm-up. The score40Kprefix scope avoids the documented original env457 failure at decision131399; it is not a claim that the entire original score corpus passes.
