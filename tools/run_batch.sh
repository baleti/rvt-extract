#!/bin/bash
# run_batch.sh MAP.tsv OUTROOT [ids...] : run_file.py for each id (remote-host), sequentially, continuing on failure. Private paths are read from MAP.tsv.
cd ~/src/rvt-extract; map=$1; root=$2; shift 2
ids="$@"; [ -z "$ids" ] && ids=$(awk -F'\t' 'NR>1{print $3"\t"$1}' $map | sort -n | cut -f2)
for id in $ids; do
  p=$(awk -F'\t' -v i=$id '$1==i{print $7}' $map); [ -z "$p" ] && continue
  echo "== $id $(date +%T)"
  timeout 5400 python3 tools/run_file.py "$p" $root/$id $id > $root/$id.log 2>&1 || echo "FAILED rc=$?"
done
echo ALLDONE
