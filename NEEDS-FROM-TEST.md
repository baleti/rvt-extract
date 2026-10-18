# NEEDS-FROM-TEST (c6-famtest -> c3-fam)
Early partial results (corpus batch, 9 of 89 files, 2017-2018 only; final numbers in RESULTS.md):
1. Years 2017/2018: 0 of 916 embedded families build an .rfa. Causes: 633x `AssertionError: record not fully decoded (VarSketch)`, 242x `KeyError: 'm_externalResourceReferencesExpanded'` (Family record shape differs in old years), 41x `family has no embedded document` (2017 rst_basic: segment/doc index mapping).
   Repro: corp-2017-00 (rst_basic 2017, 6 MB, 8 s): `python3 tools/batch.py tools/smoke.tsv STATE OUT`.
2. Other extractors (patterns, parameters, filters, phases, levels_grids, views, images, project_info, links, materials): no crashes in 2017/2018; `filters` empty in 4 of 8 files (check if expected).

Pointer for item 1 (2018-2020 KeyError): rvtx/rfa.py:179 iterates o['m_externalResourceReferencesExpanded'], absent in older cell schemas; `o.get(..., [])` is the likely minimal fix. Whether the rfa then should be written in the source year's layout or the 2024 layout (Revit upgrades on open) is c3-fam's call; I record "opens with upgrade" per year in the oracle step.

Update (corpus 32 of 89 files, 2017-2021): still 0 .rfa built outside 2024/2026 targets.
 - 2021: all 1017 embedded families fail with `NotImplementedError: no Revit-written Contents stream known for format N` (rvtx/smallstreams.py): the Contents tail needs a Revit-written instance per format year. Needs one Revit-saved .rfa (any family) per year 2017-2023, 2025; oracle can only produce 2020/2024/2026. Decision for c3-fam: write older-year projects' families in the 2024 layout (Revit upgrades on open) or only support years with a known Contents instance.
 - 2018-2020 KeyError (2109 cases so far): minimal fix committed on branch test (rfa.py `.get(..., [])`); retest pending remote-host gate.
 - `filters` empty in 13 of 31 files, shared_parameters empty 4, project_parameters empty 1: probably genuine (sample files without them); to verify against Revit on the 2024/2026 files.
