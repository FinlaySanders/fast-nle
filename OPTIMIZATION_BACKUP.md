# NetHack optimisation backup — 8 October 2026

Branch: `backup/nethack-optimizations-20261008`.
Base: `e7f6568568242745a7f7ebd8f730367123522cac` (`nethack challenge`).
Companion: the same branch in `FinlaySanders/PufferLib`.

The engine source at this branch's root is the retained September 18 PGO61
source. All 642 files in its historical source manifest were checked byte for
byte when making this backup. No game or observation changes were invented
during packaging.

It preserves bulk glyph export, immutable canonical-appearance lookup,
deferred inventory gold counting, ordered floor-object caching and SIMD
filtering, cached remaining SIMD matches, redundant-invalidation removal,
the distant scare-check guard, movement-history negative caching, and the
hero-gold absence cache.

## Build and evidence

`optimization-backup/20261008/overnight/` contains the cumulative patch,
source manifest, build scripts, retained/rejected candidate patches, reports,
and the PGO61 compiler profiles with their original checksum manifest.
`initial-engine-campaign/final/` records the earlier source baseline and
Release/LTO/local-binding build recipe. PGO61 adds profile-guided compilation;
the saved profiles are tied to the original compiler, source and build paths.
The archived scripts retain those original paths. Reproducing their timings
also requires the external recorded trajectories and policy checkpoints.

Historical evidence includes complete selected score/depth replays, current
observation comparisons, and historical-view golden/fuzz checks. Reports retain
known baseline exceptions and compiler-checker limitations. These checks were
not rerun as part of making a source backup.

The older `perf-planes-wip` commit is already on GitHub. Its patch and provenance
are also saved under `parked/`; it has documented golden failures and is not
part of the retained source at the root of this branch. Other archived candidate
patches are not all accepted optimisations; consult the retained `best.json`
and reports.

`optimization-backup/20261008/MANIFEST.json` gives the original path, size and
SHA-256 for each preserved file. This backup covers optimisation code and
supporting evidence, not checkpoints, raw rollout corpora, or all research data.
