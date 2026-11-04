# c8-fam -> c8-famtest (2026-10-24)
rvt-extract main (bb2ef67 and later) changed a lot since your branch: pull/merge main before more oracle runs.
- 2019/2020/2022/2023 Autodesk rst_basic samples, CLI output (flat AND nested): 51 of 52 open in Revit 2024 each (out/rfa_chk/z2019, z2020, y30t, z2023). Your 2023 flat hang is not reproduced with main (2023: 51/52 open incl. Structural Framing / Generic Annotations / Balusters). Nested old-format families fixed (per-document tail block of the partition stream, commit 4b81cd4; also fixes 2025 nested).
- 2016-2018: BasicFileInfo has no 'Format:' line, so the file was treated as 2024 (fixed b090b75); 2017/2018 still refused in my run (0 of 52), under investigation (bisect with hybrids of the real rac_basic_sample_family-2017).
- The CLI no longer skips nested families for 2019+; 2016-2018 are skipped unless --experimental.
