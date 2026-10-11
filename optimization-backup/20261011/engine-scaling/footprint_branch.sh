#!/bin/bash
# Branch-predictor census for an engine (callgrind --branch-sim): ./footprint_branch.sh <engine> <label>; reuses the -g build from footprint_lines2.
R=/puffertank/experiments/nethack-engine-scaling-20261010; H=/puffertank/experiments/nethack-compact-state-20261008
ACTIONS=/puffertank/experiments/nethack-comprehensive-20261008/actions; E=$1; L=$2
cd $R; [ -d $H/engines/${E}_g/build ] || { echo "no ${E}_g build"; exit 1; }
export LD_LIBRARY_PATH=$H/engines/${E}_g/build NETHACKDIR=/puffertank/experiments/nethack-perf-20260917/dat NH_ZT_MASK=0
echo "START $L $(date -u +%T)"
nice -n 19 valgrind --tool=callgrind --branch-sim=yes --cache-sim=no --instr-atstart=no \
  --callgrind-out-file=$R/callgrind.$L.out $R/harness_incpack/replay 512 0 4096 128 $ACTIONS > $R/replay.$L.log 2>&1 || echo "FAILED $L rc=$?"
grep RESULT $R/replay.$L.log | cut -c1-160
echo "DONE $L $(date -u +%T)"
STEPS=$((512*128))
callgrind_annotate --inclusive=no callgrind.$L.out | grep -m1 -A2 "PROGRAM TOTALS" | tr -s ' ' > $R/BRANCH_$L.md
echo "per step (Ir Bc Bcm Bi Bim):" >> $R/BRANCH_$L.md
callgrind_annotate --inclusive=no callgrind.$L.out | awk -v st=$STEPS '/PROGRAM TOTALS/{for(i=1;i<=5;i++){gsub(",","",$i); printf "%.1fK ", $i/st/1000}; print ""; exit}' >> $R/BRANCH_$L.md
echo "top functions by conditional mispredicts (Bcm/step):" >> $R/BRANCH_$L.md
callgrind_annotate --inclusive=no --sort=Bcm --threshold=95 callgrind.$L.out | awk -v st=$STEPS 'BEGIN{p=0} /^-+$/{p++} p>=2 && $1 ~ /^[0-9,]+$/ {gsub(",","",$3); if(n++<40) printf "%8.1f /step  %s\n", $3/st, $NF}' >> $R/BRANCH_$L.md
echo "BRANCH_DONE $L"
