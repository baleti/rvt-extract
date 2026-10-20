# HANDOFF c6-famtest (2026-10-20)
State: everything committed on branch test (merged with main incl. c3-fam PEE closure). Read RESULTS.md, NEEDS-FROM-TEST.md, TESTING.md.
Headline: corpus run2 built 9508/10191 .rfa (93.3%); real-world (41 files that fit 7 GB) 94.3%; 30 of 71 real-world files exceed remote-host's 9 GB slice.
Revit-free accuracy vs EditFamily+SaveAs (tools/lift_cmp.py, 177 families): 2024 missing records 685->183, H/R/Z identity 99.27/99.80/99.93%; 2026 with my committed m_deletion rule H 99.18%.
Extractor counts equal Revit exports on 40 of 42 files (levels/filters/shared fixed in rvtx/items.py); views: panel schedules missing, +9 sections unexplained.
Running on remote-host: corpus3 (full 78-file rerun, h1_keep loop on remote-host: private/keep_corpus3.log; state in remote-host ~/src/rvt-extract-test/$HOME/scratch-famtest/state_corpus3). When done: python3 tools/report.py <state copy> and update RESULTS.md. Kill loop: pgrep -f "[h]1_keep.sh corpus3".
Rejected experiments (measured): flag-bit rule, 2026 family-first deletion for all shared (see NEEDS-FROM-TEST.md).
Blocked: remote-host VMs unreachable, so no Revit-open checks; oracle queue is in PROGRESS.md.
