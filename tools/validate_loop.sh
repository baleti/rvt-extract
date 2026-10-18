#!/bin/bash
# validate_loop.sh YEAR FILEID N [STEP] : oracle open-check in slices (STEP default 15 files: the harness script cap is ~280 s)
y=$1; id=$2; n=$3; st=${4:-15}; cd ~/src/rvt-extract-test
for ((a=0; a<n; a+=st)); do tools/validate_year.sh $y $id $a:$((a+st)); done; echo VALDONE
