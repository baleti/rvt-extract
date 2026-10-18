#!/bin/bash
# validate_split.sh YEAR FILEID A B : open-check files [A,B) of a batch dir; a slice that fails is bisected down to single files (single failures recorded as HANG lines)
y=$1; id=$2; a=$3; b=$4; cd ~/src/rvt-extract-test; out=private/oracle_$id.tsv
run() { local a=$1 b=$2 d=private/rfacheck_${id}_$1-$2; rm -rf $d; tools/validate_year.sh $y $id $a:$b > /dev/null 2>&1
  local want=$((b-a)); local ok=$(ls private/rfa/$id/*.rfa | sort | sed -n "$((a+1)),${b}p" | xargs -n1 basename | sort | comm -12 - <(grep -hE "^(OPEN|OPENFAIL)	" $d/rfacheck.tsv 2>/dev/null | cut -f2 | sort) | wc -l)
  [ "$ok" = "$want" ] && { cat $d/rfacheck.tsv >> $out; return 0; }; return 1; }
split() { local a=$1 b=$2
  if run $a $b; then echo "ok $a:$b"; return; fi
  if [ $((b-a)) -le 1 ]; then echo "HANG	$(ls private/rfa/$id/*.rfa | sort | sed -n "$((a+1))p" | xargs -n1 basename)" >> $out; echo "hang $a"; return; fi
  local m=$(( (a+b)/2 )); split $a $m; split $m $b; }
split $a $b; echo SPLITDONE
