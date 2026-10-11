#!/bin/bash
# Generic Phase 3 step: chain_step.sh <name> <base> <marker_log> <marker_text>
# builds <name> + <name>_verify (all twins on), verify replay, quick gates, waits for the marker, ABBA vs <base>, full gate || census, ir_compare.
N=$1; B=$2; ML=$3; MT=$4
R=/puffertank/experiments/nethack-engine-scaling-20261010; CS=/puffertank/experiments/nethack-compact-state-20261008
export NETHACKDIR=/puffertank/experiments/nethack-perf-20260917/dat NH_ZT_MASK=0
while ! grep -q "$MT" $ML; do sleep 20; done; echo "WAIT_${MT}_DONE"
cd $R && rm -rf $CS/engines/${N}_verify && mkdir -p $CS/engines/${N}_verify && cp -r $CS/engines/$N/source $CS/engines/${N}_verify/source
(python3 build_candidate.py $N || echo BUILD_FAILED $N) & (BUILD_EXTRA_CFLAGS="-DNLE_SPW_VERIFY -DNH_MOVEMENT_MASK_VERIFY -DNLE_HP_VERIFY -DNLE_DISPLAY_VERIFY" python3 build_candidate.py ${N}_verify || echo BUILD_FAILED ${N}_verify) & wait; echo BUILD_${N}_DONE
[ -f $CS/engines/$N/build/libnethack.so ] && [ -f $CS/engines/${N}_verify/build/libnethack.so ] || { grep -m4 "error:" $CS/engines/$N/build.log $CS/engines/${N}_verify/build.log | cut -c1-220; echo CHAIN_ABORT_BUILD; exit 1; }
LD_LIBRARY_PATH=$CS/engines/${N}_verify/build nice -n 5 ./harness_incpack/replay 512 32 0 32768 /puffertank/experiments/nethack-comprehensive-20261008/actions > ${N}_verify_run.log 2>&1
echo "VERIFY_$N mismatches=$(grep -c -i 'MISMATCH\|panic\|desync' ${N}_verify_run.log) $(grep -o 'obs=[0-9a-f]* age=[0-9.]* turns=[0-9]*' ${N}_verify_run.log)"
grep -i "MISMATCH\|panic\|desync" ${N}_verify_run.log | sed 's/turn=[0-9]* //; s/at [0-9]*,[0-9]*//; s/idx=[0-9]*//' | sort | uniq -c | sort -rn | head -8
cd $CS && nice -n 5 python3 check.py $N --quick 2>&1 | grep -E "^PASS|^FAIL|Traceback"; echo GATES_${N}_DONE
cd $R && CTRL_OVERRIDE=$CS/engines/$B/build CTRLREPLAY_OVERRIDE=$R/harness_incpack/replay ./native_screen2.sh $CS/engines/$N/build $R/harness_incpack/replay $N; echo NATIVE_${N}_DONE
(cd $CS && nice -n 10 python3 check.py $N; echo FULLGATE_${N}_DONE) & (cd $R && ./footprint_lines2.sh $N lines_$N; echo LINES_${N}_DONE) & wait
cd $R && python3 ir_compare.py lines_$B lines_$N 16; echo "CHAIN_${N}_DONE"
