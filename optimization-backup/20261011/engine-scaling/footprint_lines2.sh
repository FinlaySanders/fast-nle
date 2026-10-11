#!/bin/bash
# Line-level LL-miss attribution for an existing engine: ./footprint_lines2.sh <engine> <label>  (builds <engine>_g with -g, uses harness_incpack/replay)
R=/puffertank/experiments/nethack-engine-scaling-20261010; H=/puffertank/experiments/nethack-compact-state-20261008
ACTIONS=/puffertank/experiments/nethack-comprehensive-20261008/actions; E=$1; L=$2
cd $R
if [ ! -d $H/engines/${E}_g/source ]; then mkdir -p $H/engines/${E}_g && cp -r $H/engines/$E/source $H/engines/${E}_g/source; fi
BUILD_EXTRA_CFLAGS=-g nice -n 10 python3 build_candidate.py ${E}_g || { echo BUILD_FAILED; exit 1; }
export LD_LIBRARY_PATH=$H/engines/${E}_g/build NETHACKDIR=/puffertank/experiments/nethack-perf-20260917/dat NH_ZT_MASK=0
echo "START $L $(date -u +%T)"
nice -n 19 valgrind --tool=callgrind --cache-sim=yes --instr-atstart=no --D1=49152,12,64 --LL=9437184,9,64 \
  --callgrind-out-file=$R/callgrind.$L.out $R/harness_incpack/replay 512 0 4096 128 $ACTIONS > $R/replay.$L.log 2>&1 || echo "FAILED $L rc=$?"
grep RESULT $R/replay.$L.log | cut -c1-160
echo "DONE $L $(date -u +%T)"
python3 $R/footprint_lines.py $L ${E}_g > $R/FOOTPRINT_LINES_$L.md 2> $R/footprint_lines_$L.err
echo "LINES_DONE $L"
