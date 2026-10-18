#!/bin/bash
# h1_job.sh NAME CMD... : run a one-off command in the remote-host worktree via h1run (retries while the 11 GB gate is closed)
n=$1; shift
until ~/.local/share/offload/h1run run "$n" --env rvt --dir ~/src/rvt-extract-test -- "$@"; do [ $? -eq 75 ] || exit 1; sleep 120; done
