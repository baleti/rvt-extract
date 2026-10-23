# rvt-extract PROGRESS (c8-fam, account claude8)
- 2026-10-20 takeover. remote-host oracle reachable again. Finding: lift43q slices r070+ hang 600 s on Revit task dialog "required internal settings are missing" (journal: unique element 'View Referencing Setting' missing) for Rebar Shape families. rfacheck.cs now auto-dismisses/logs dialogs (DIALOG lines). cmp1 job compares our Rebar Shape 00/09 against Revit's own (G*).
- Slices r000..r060 of lift43q (families 0-70) done; held r130-r170 in pipeline/hold3.
- 2026-10-22: Snowdon 2024 facts diff 170/179 identical; studyx-033 (real 2024 office file) 100/100 lifted families open in Revit 2024. 2020 (4-byte) bisect: ElemTable build4 shared/special rows were 24 bytes (fixed to 28); partition stream must be named like Revit's per year (Partitions/63 for 2020: hybrid A (renamed to 0) InternalException, hybrid D (real name) opens); still CorruptModelException for lifted 2020 -> famsave on Revit 2020 oracle queued (gt_fam/2020_18) for native 4-byte ground truth.
- 2026-10-23 claude8 takeover: oversized-record frames fixed, GUID-sorted content records; ofc-002 title blocks 3/3 open in Revit 2024 (out/rfa_chk/o2q); 4-family Snowdon regression 4/4 open (reg1).
- 2026-10-23: ofc-002 70/70 lifted rfa open in Revit 2024.
- 2026-10-23: Snowdon 2024 re-sweep 177/177 open (y43).
- 2026-10-23: Snowdon 2026 re-sweep 177/177 open (z55); lift chunks of 12 get OOM-killed on 2026 project, use 4/1.
- 2026-10-23: studyx-033 100/100 open (b33y); null m_oContentTable fix for nested.
