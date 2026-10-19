#!/bin/bash
# h1_launch.sh NAME LIST STATE OUT : rsync this worktree to remote-host and start a batch on remote-host (retries until the 11 GB gate opens)
n=$1; lst=$2; st=$3; out=$4
rsync -a --exclude=private --exclude=out --exclude=.git --exclude=__pycache__ ~/src/rvt-extract-test/ remote-host:src/rvt-extract-test/
rsync -a ~/src/rvt-extract-test/private/map.tsv remote-host:src/rvt-extract-test/private/ 2>/dev/null
until ~/.local/share/offload/h1run run "$n" --env rvt --dir ~/src/rvt-extract-test -- env BATCH_AS_GB=${BATCH_AS_GB:-7} KINDS_ONLY=${KINDS_ONLY:-} python3 tools/batch.py $lst $st $out; do [ $? -eq 75 ] || exit 1; sleep 120; done
