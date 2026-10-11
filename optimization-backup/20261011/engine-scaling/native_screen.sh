#!/bin/bash
# Native CPU replay screen, ABBA vs the non-PGO retained build: ./native_screen.sh <candidate_build_dir> [label]
# Protocol: 32 workers, warm 8192 steps/game, measure 2048; 512 and 2048 games. No GPU work may run concurrently.
set -u
CAND=$1; LABEL=${2:-cand}
CS=/puffertank/experiments/nethack-compact-state-20261008
CTRL=$CS/engines/movement_object_presence/build
ACTIONS=/puffertank/experiments/nethack-comprehensive-20261008/actions
OUT=/puffertank/experiments/nethack-engine-scaling-20261010/screens/$LABEL; mkdir -p $OUT
export NETHACKDIR=/puffertank/experiments/nethack-perf-20260917/dat NH_ZT_MASK=0
run() { # name engine envs
  LD_LIBRARY_PATH=$2 $CS/replay $3 32 8192 2048 $ACTIONS > $OUT/$1_$3.log 2>&1
  grep -o 'sps=[0-9.]*' $OUT/$1_$3.log | tail -1 | sed "s/^/$1 $3 /"
  grep -o 'obs=[0-9a-f]*' $OUT/$1_$3.log | tail -1 | sed "s/^/$1 $3 /"
}
for envs in 512 2048; do
  run ctrl_a $CTRL $envs; run cand_a $CAND $envs; run cand_b $CAND $envs; run ctrl_b $CTRL $envs
done | tee $OUT/summary.txt
