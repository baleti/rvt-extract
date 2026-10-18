#!/bin/bash
# validate_year.sh YEAR FILEID [SLICE a:b] : pull the built .rfa of one batch file from remote-host and open them in the Revit YEAR oracle on remote-host (write-lab harness, offline).
# Light on remote-host (VM does the work). Do NOT set RFA_LOAD here (load-back poisons later opens: dedicated runs only).
y=$1; id=$2; sl=${3:-}
for st in out_corpus out_studyx; do ssh remote-host "test -d ~/src/rvt-extract-test/\\\$HOME/scratch-famtest/$st/$id" && src=$st; done
d=~/src/rvt-extract-test/private/rfa/$id; mkdir -p $d
ssh remote-host "cd ~/src/rvt-extract-test/\\\$HOME/scratch-famtest/$src && tar cf - $id" | tar xf - -C ~/src/rvt-extract-test/private/rfa
ssh remote-host 'free -m|sed -n 2p' | awk '{ if ($7<6000) {print "remote-host low memory", $7; exit 1} }' || exit 1
RFA_SLICE=$sl python3 ~/src/rvt-extract-test/oracle/rfacheck.py $y $d ~/src/rvt-extract-test/private/rfacheck_${id}${sl:+_${sl/:/-}}
