#!/bin/bash
# retry h1run until remote-host has memory; usage: h1_retry.sh NAME -- cmd...
n=$1; shift
until ~/.local/share/offload/h1run run "$n" --env rvt --dir ~/src/rvt-extract "$@"; do [ $? -eq 75 ] || exit 1; sleep 300; done
