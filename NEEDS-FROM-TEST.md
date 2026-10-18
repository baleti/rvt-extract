# NEEDS-FROM-TEST (c6-famtest -> c3-fam)
Early partial results (corpus batch, 9 of 89 files, 2017-2018 only; final numbers in RESULTS.md):
1. Years 2017/2018: 0 of 916 embedded families build an .rfa. Causes: 633x `AssertionError: record not fully decoded (VarSketch)`, 242x `KeyError: 'm_externalResourceReferencesExpanded'` (Family record shape differs in old years), 41x `family has no embedded document` (2017 rst_basic: segment/doc index mapping).
   Repro: corp-2017-00 (rst_basic 2017, 6 MB, 8 s): `python3 tools/batch.py tools/smoke.tsv STATE OUT`.
2. Other extractors (patterns, parameters, filters, phases, levels_grids, views, images, project_info, links, materials): no crashes in 2017/2018; `filters` empty in 4 of 8 files (check if expected).
