#!/bin/bash
# h1_keep.sh NAME LIST STATE OUT : keep resubmitting a batch on remote-host until it reports BATCHDONE (a unit-wide OOM kill ends the unit; batch.py then skips the culprit after 3 kills)
n=$1; i=0
while true; do
  i=$((i+1)); tools/h1_launch.sh $n$i "$2" "$3" "$4"
  while ssh remote-host "systemctl --user is-active -q h1-$n$i"; do sleep 120; done
  ssh remote-host "grep -q BATCHDONE ~/offload/$n$i.log" && break
  sleep 30
done
