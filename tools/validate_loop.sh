#!/bin/bash
# validate_loop.sh YEAR FILEID N [STEP] : oracle open-check in slices (harness script cap ~280 s). Each slice is retried (up to 3x) until its tsv lists every expected file exactly once;
# results merged into private/oracle_<FILEID>.tsv (OPEN/OPENFAIL lines etc.).
y=$1; id=$2; n=$3; st=${4:-12}; cd ~/src/rvt-extract-test; out=private/oracle_$id.tsv; : > $out
tot=$(ls private/rfa/$id/*.rfa | wc -l); [ $n -gt $tot ] && n=$tot
for ((a=0; a<n; a+=st)); do
  b=$((a+st)); [ $b -gt $n ] && b=$n; want=$((b-a)); d=private/rfacheck_${id}_$a-$b
  for try in 1 2 3; do
    rm -rf $d; tools/validate_year.sh $y $id $a:$b > /dev/null 2>&1
    got=$(grep -hE "^(OPEN|OPENFAIL)	" $d/rfacheck.tsv 2>/dev/null | cut -f2 | sort | uniq | wc -l); ok=$(ls private/rfa/$id/*.rfa | sort | sed -n "$((a+1)),${b}p" | xargs -n1 basename | sort | comm -12 - <(grep -hE "^(OPEN|OPENFAIL)	" $d/rfacheck.tsv 2>/dev/null | cut -f2 | sort) | wc -l); [ "$ok" = "$want" ] && got=$want || got=0; [ "$got" = "$want" ] && break; sleep 20
  done
  echo "slice $a:$b try $try got $got/$want"; cat $d/rfacheck.tsv >> $out 2>/dev/null
done; echo VALDONE
