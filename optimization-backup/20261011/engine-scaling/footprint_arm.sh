#!/bin/bash
# One callgrind arm at the 2048-game LL share: ./footprint_arm.sh <engine_build_dir> <label> [harness_replay]
R=/puffertank/experiments/nethack-engine-scaling-20261010; H=/puffertank/experiments/nethack-compact-state-20261008
ACTIONS=/puffertank/experiments/nethack-comprehensive-20261008/actions
REPLAY=${3:-$H/replay}
export LD_LIBRARY_PATH=$1 NETHACKDIR=/puffertank/experiments/nethack-perf-20260917/dat NH_ZT_MASK=0
cd $R; echo "START $2 $(date -u +%T)"
nice -n 19 valgrind --tool=callgrind --cache-sim=yes --instr-atstart=no --D1=49152,12,64 --LL=9437184,9,64 --callgrind-out-file=$R/callgrind.$2.out $REPLAY 512 0 4096 128 $ACTIONS > $R/replay.$2.log 2>&1 || echo "FAILED $2 rc=$?"
grep RESULT $R/replay.$2.log | cut -c1-120; echo "DONE $2 $(date -u +%T)"
