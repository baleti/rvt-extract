#!/bin/bash
cd ~/src/rvt-extract
i=0
for id in studyx-033 ofc-002 ofc-003; do
  p=$(awk -F'\t' -v i=$id '$1==i{print $7}' private/map.tsv)
  python3 tools/lift_all.py "$p" out/lift_$id > out/lift_$id.log 2>&1
done
echo done
