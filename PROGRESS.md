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
