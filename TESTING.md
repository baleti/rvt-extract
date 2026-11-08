# Testing rvt-extract (c6-famtest)
Tools (all heavy runs on remote-host; remote-host only reads results):
- `tools/batch.py LIST.tsv STATE OUT` resumable per-file runner (per-file address-space cap `BATCH_AS_GB`, default 7; a file that kills the unit 3 times is recorded as killed); `tools/batch_one.py` does one file with per-family error capture and times every other extractor.
- `tools/h1_keep.sh NAME LIST STATE OUT` resubmits on remote-host until done; `tools/h1_job.sh NAME CMD...` one-off remote-host job.
- `tools/report.py STATE` anonymised table + failure causes by normalised error; `tools/fix_years.py` repairs the format year from BasicFileInfo.
- Oracle (Revit on remote-host, only when the VMs are up): `tools/validate_split.sh YEAR ID A B` opens .rfa files in slices (bisects failing slices), `oracle/rfacheck.py`; facts compared with `gt_fam/<tag>/index.tsv` (families sorted by name = our index order among embedded ones).
Rules: real-world files stay local; reports carry only ids (studyx-NNN, corp-YEAR-NN); `private/` and `out/` are git-ignored.
Known limits at 2026-10-19: see RESULTS.md and NEEDS-FROM-TEST.md (VarSketch decode in 2017, 12-parameter shortfall of Rebar Shape families, Revit refuses ~1/3 of lifted 2024 Structural families in the partial check, 30 of 71 real-world files exceed the 7 GB per-file cap).

## Revit VM open checks: queue wait is not a hang
`oracle/rfacheck.py` takes the shared VM lock, a FIFO ticket queue (write-lab/campaign/vmq) that other jobs also use and that can be 25+ tickets deep (hours). A wrapper `timeout` that is shorter than the queue wait kills the job while it is still waiting and sends the retry to the back, which looks like a Revit hang with no output. Use a long timeout (6 h), small slices, and check `ls write-lab/campaign/vmq` before concluding a file hangs Revit.
