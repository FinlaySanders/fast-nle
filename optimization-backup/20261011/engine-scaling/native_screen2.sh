#!/bin/bash
# Native CPU replay screen with a candidate harness binary: ./native_screen2.sh <cand_engine_build> <cand_replay_bin> <label>
set -u
CAND=$1; CREPLAY=$2; LABEL=$3
CS=/puffertank/experiments/nethack-compact-state-20261008
CTRL=${CTRL_OVERRIDE:-$CS/engines/movement_object_presence/build}; CTRLREPLAY=${CTRLREPLAY_OVERRIDE:-$CS/replay}
ACTIONS=/puffertank/experiments/nethack-comprehensive-20261008/actions
OUT=/puffertank/experiments/nethack-engine-scaling-20261010/screens/$LABEL; mkdir -p $OUT
export NETHACKDIR=/puffertank/experiments/nethack-perf-20260917/dat NH_ZT_MASK=0
run() { LD_LIBRARY_PATH=$2 $3 $4 32 8192 2048 $ACTIONS > $OUT/$1_$4.log 2>&1
  grep -o 'sps=[0-9.]*' $OUT/$1_$4.log | tail -1 | sed "s/^/$1 $4 /"; grep -o 'obs=[0-9a-f]*' $OUT/$1_$4.log | tail -1 | sed "s/^/$1 $4 /"; }
for envs in 512 2048; do
  run ctrl_a $CTRL $CTRLREPLAY $envs; run cand_a $CAND $CREPLAY $envs; run cand_b $CAND $CREPLAY $envs; run ctrl_b $CTRL $CTRLREPLAY $envs
done | tee $OUT/summary.txt
