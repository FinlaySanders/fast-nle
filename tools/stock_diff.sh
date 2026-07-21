#!/bin/bash
# One-command differential verification against stock NLE.
#
#   tools/stock_diff.sh <seed-base> [episodes=4] [steps=2000] [roles=mon]
#
# Records fresh goldens from a pinned STOCK build at arbitrary seeds, then
# replays them against the current fork build, failing at the first
# divergent step. Complements the fixed corpus in tests/goldens/ with
# on-demand, any-seed coverage — run it over a wide seed range before and
# after any engine surgery.
#
# One-time stock setup (see docs/DETERMINISM.md — clang is REQUIRED, stock
# behavior is compiler-dependent):
#   git worktree add <STOCK_DIR> 2319f298
#   cd <STOCK_DIR> && git apply <fork>/tools/stock_record.patch
#   uv venv .venv && CC=clang CXX=clang++ uv pip install -e . --python .venv/bin/python
#   gcc -shared -fPIC -O2 -o <STOCK_DIR>/faketime.so <fork>/tools/faketime_shim.c -ldl
set -euo pipefail
FORK="$(cd "$(dirname "$0")/.." && pwd)"
STOCK="${STOCK_NLE_DIR:?set STOCK_NLE_DIR to the stock worktree (see header)}"
SEED="${1:?usage: stock_diff.sh <seed-base> [episodes] [steps] [roles]}"
EPS="${2:-4}"; STEPS="${3:-2000}"; ROLES="${4:-mon}"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

LD_PRELOAD="$STOCK/faketime.so" "$STOCK/.venv/bin/python" -P \
    "$FORK/tools/record_goldens.py" --outdir "$OUT" --steps "$STEPS" \
    --seed-base "$SEED" --roles "$ROLES" --episodes-per-role "$EPS" >&2

# replayer must be current: rebuild cheaply every run (stale-binary trap:
# an old binary silently misreads a grown nle_obs as garbage)
cc -O2 -I"$FORK/include" -I"$FORK/build/_deps/deboost_context-src/include" \
   "$FORK/tests/replay_golden.c" "$FORK/sys/unix/nledl.c" -ldl \
   -o "$OUT/replay_golden" 2>/dev/null

"$OUT/replay_golden" "$FORK/build/libnethack.so" "$FORK/build/dat" "$OUT"/*.golden
