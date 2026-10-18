# c6-famtest PROGRESS
- 2026-10-18: worktree test branch. tools/batch.py + batch_one.py (resumable per-family capture), tools/h1_launch.sh (remote-host only), tools/corpus.tsv (89 corpus files).
- studyx sample: 50 files (stratified by mtime year/size, <300 MB, no officeA/officeB) listed in private/map.tsv (git-ignored); copied to remote-host ~/scratch-famtest/studyx/studyx-NNN.rvt (copy.sh niced, bwlimit).
- Smoke run (corp-2017-00) waits for the remote-host 11 GB gate. Rule: no scripts on remote-host beyond editing/git/reading.
- studyx sample extended with 21 files from the other project archives (user lifted the folder restriction; ids continue studyx-051..071, local only).
