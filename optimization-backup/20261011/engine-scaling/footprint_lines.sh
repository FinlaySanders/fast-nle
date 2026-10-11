#!/bin/bash
# Step 1b: line-level attribution of LL misses at the 2048-game share, using a -g twin of the retained source.
R=/puffertank/experiments/nethack-engine-scaling-20261010; H=/puffertank/experiments/nethack-compact-state-20261008
ACTIONS=/puffertank/experiments/nethack-comprehensive-20261008/actions
cd $R
BUILD_EXTRA_CFLAGS=-g nice -n 10 python3 build_candidate.py footprint_g || { echo BUILD_FAILED; exit 1; }
export LD_LIBRARY_PATH=$H/engines/footprint_g/build NETHACKDIR=/puffertank/experiments/nethack-perf-20260917/dat NH_ZT_MASK=0
echo "START lines2048 $(date -u +%T)"
nice -n 19 valgrind --tool=callgrind --cache-sim=yes --instr-atstart=no --D1=49152,12,64 --LL=9437184,9,64 \
  --callgrind-out-file=$R/callgrind.lines2048.out $H/replay 512 0 4096 128 $ACTIONS > $R/replay.lines2048.log 2>&1 || echo "FAILED lines2048 rc=$?"
grep RESULT $R/replay.lines2048.log | cut -c1-160
echo "DONE lines2048 $(date -u +%T)"
python3 $R/footprint_lines.py > $R/FOOTPRINT_LINES.md 2> $R/footprint_lines.err
echo LINES_DONE
