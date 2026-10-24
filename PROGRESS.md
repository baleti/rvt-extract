# c6-famtest PROGRESS
- 2026-10-18: worktree test branch. tools/batch.py + batch_one.py (resumable per-family capture), tools/h1_launch.sh (remote-host only), tools/corpus.tsv (89 corpus files).
- studyx sample: 50 files (stratified by mtime year/size, <300 MB) listed in private/map.tsv (git-ignored); copied to remote-host ~/scratch-famtest/studyx/studyx-NNN.rvt (copy.sh niced, bwlimit).
- Smoke run (corp-2017-00) waits for the remote-host 11 GB gate. Rule: no scripts on remote-host beyond editing/git/reading.
- studyx sample extended with 21 files from the other project archives (user lifted the folder restriction; ids continue studyx-051..071, local only).
- corpus batch running on remote-host (started). State dirs landed in literal dir ~/src/rvt-extract-test/\$HOME/scratch-famtest/state_{corpus,studyx} on remote-host (quoting quirk, harmless); .rfa outputs in out_* beside. studyx batch chained after corpus (waiter on remote-host is a sleeping ssh loop).
- merged main (c3-fam: multi-partition docs, W=4, Contents samples) into test; corpus rerun 'corpus2' to measure.
- chain_years: Revit 2024 open check of 12 families per older-year sample (corpus2 output), after the 2024 structural split run.
- 2026-10-19: remote-host VMs down (reboot, user reconfiguring). Stopped my oracle loops. ORACLE QUEUE (run only when the orchestrator says the VMs are back; 10-file slices, one run at a time, no retry loops):
  1. 2024 Structural corp-2024-43: remaining open-checks (verified ranges so far in private/oracle_corp-2024-43.tsv), then facts diff vs gt_fam/2024_43.
  2. Per-year open (upgrade into Revit 2024): VAL_OUTS=out_corpus2 tools/validate_split.sh 2024 ID 0 12 for corp-2018-06, 2019-12, 2020-18, 2021-24, 2022-30, 2023-36, 2025-48.
  3. 2026 Structural corp-2026-55 vs gt_fam/2026_55 in the 2026 VM.
  4. After c3-fam fixes: re-check Rebar Shape / Detail Items / Profiles families.
- 2026-10-21 c8: corpus3 report done (93.3%). Oracle 2024 open-check of out_corpus3 corp-2024-43 slices hangs: rfacheck.py 0:2 inside run.ps1 job_rc_corp_2024_43 (port 23717) >15 min, no output (old 12-24 slice had worked with older rfa). Asked c8-writer to look at the VM; retry with single-file slices when it is free.
- 2026-10-24 c8: corpus4 running on remote-host (out_corpus4). 2017: builds 41/41, 137/137 but Revit 2024 opens 0/4 (NEEDS-FROM-TEST).
- 2026-10-24 c8: corp-2018-06 4/4 OPENFAIL CorruptModel in Revit 2024 as well (2017 and 2018 rejected; c3-fam validated only 2019-2022 flat). Next: 2019-12, 2020-18, 2021-24, 2022-30, 2023-36 when corpus4 reaches them.
- 2026-10-24 c8: corp-2019-12 (2019, Revit 2024 upgrade) first 3 .rfa: 0000 OPEN, 0002 OPEN, 0001 OPENFAIL (Corrupt; to retest alone). Source: private/v2019.log
- corp-2019-12 0001 refused ALONE (genuine). 0000, 0002 open.
- 2026-10-24 c8: corp-2020-18 first 3: 0000 OPEN, 0002 OPEN, 0001 OPENFAIL (same index/pattern as 2019-12, likely the same Detail Items family; private/v2020.log)
- 2026-10-24 rvt-extract corpus4 (current main, 23 of 78 corpus files done, 2017-2020): .rfa built 2589/2589 embedded families; 17 non-family extractors 0 crashes on 23 files (empty: cad_imports 13, filters 10, shared_parameters 3); Revit 2024 opens: 2017 0/4, 2018 0/4, 2019 2/3, 2020 2/3 (private/v20*.log, tools/validate_year.sh)
- corp-2019-12/0001 = nested (2 docs): expected refusal, resolved
- 2026-10-24 c8: corp-2021-24 flat families (flatsplit) 5/5 OPEN in Revit 2024 (private/f21.res)
- flat-only: 2017 0/4, 2018 0/4 (genuine), 2019 2/2, 2020 2/2, 2021 5/5 open in Revit 2024
