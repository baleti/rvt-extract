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

fix1 result (2019 rst_basic, 41 embedded families, remote-host): with the `.get` fix the KeyError disappears; all 41 now stop at `NotImplementedError: no Revit-written Contents stream known for format 2019`. So the Contents-per-year instance is the real gate for every year other than 2024/2026.

## FULL CORPUS RESULT (78 files, 2017-2026; 10191 families with embedded doc; remote-host batch, no process crash, max RSS 4.2 GB)
 built .rfa: 2024 1196/1345 (89%), 2026 1027/1345 (76%), every other year 0.
 Top causes (families): 3687 `no Revit-written Contents stream known for format N` (2021-2023, 2025: needs a per-year Contents instance), 2109 KeyError m_externalResourceReferencesExpanded (2018-2020; fix on branch test, then falls into the Contents cause), 633 VarSketch not fully decoded (2017/2018 decoder), 466 `family has no embedded document` in 2024/2026 (see 4).
 4. WHOLE-FILE failure in 3 files: 2024 Site (corp-2024-47, 148 families), 2026 Electrical (corp-2026-56, 211), 2026 Facades (corp-2026-58, 107): every family with an embedded doc ends in `AssertionError: family has no embedded document` after ~15-20 s (the other six 2026 and eight 2024 files are 100%). Probably family_doc_index returns None for these (m_big2SmallMap2 ids not in docs[].id_doc) or the partition parse of the Site/Facades/Electrical files stops early. Repro: python3 tools/batch.py (one line tsv) or lift_all.py on those files; ids in tools/corpus.tsv.
 5. 1 family `record not fully decoded (DataStorage)` in 2024; 2 `KeyError: N`.
 Other extractors: no crash on any of the 78 files. Empty outputs: filters 18/78, project_parameters 12/78, shared_parameters 6/78 (to be checked vs Revit).

Hint for item 4 (from stream listing only, no big load): the three whole-file failures all have more than one Partitions/ stream (2024 Site 2, 2026 Electrical 4, 2026 Facades 2) while all other 2024/2026 files have exactly 1 (2026 Site has 2 and still built 100%, so it is not the whole story). rvtx/rfa.py ProjectDocs reads only `[...Partitions/...][0]`; family documents living in a later partition would give `family_doc_index` None. Worth checking which partition holds the family docs for corp-2026-56.

## Oracle facts diff, 2024 Structural (corp-2024-43), partial: 72 families that Revit 2024 opened so far, compared with Revit's own EditFamily+SaveAs facts (gt_fam/2024_43 index; mapping by sorted name, category match 177/177)
 types 72/72, reference planes 72/72, forms 72/72 equal. Parameters equal in 53/72; the 19 differences are exactly: 16 Rebar Shape families 12 parameters short (22 expected, 10 found: the shared-parameter ParamElemExternal closure, as in HANDOFF), 2 Generic Models and 1 Structural Column 2 parameters short (likely the same cause).
 Open failures so far (of 120 checked): 48; concentrated in Detail Items (11 of 13), Rebar Shape (10 of 26), Boundary Conditions (4 of 4), Profiles 2/5, Title Blocks 2/4. Messages: CorruptModelException "needs to be recovered" mostly. Oracle runs: 12-file slices intermittently exceed the 280 s harness cap (bisection tool tools/validate_split.sh).

## RUN 2 (corpus, after merging main): built 9508/10191 (93.3%). Remaining build failures: 671 x VarSketch not fully decoded (all 2017: corp-2017-*), 12 x DataStorage (2024). All other years 100% built. Next measured: do the 2018-2023/2025 .rfa OPEN in Revit 2024 (upgrade) - oracle sample runs per year queued after the 2024 Structural run.

## lift_cmp confirms (2024 Structural, Rebar Shape family "00", remote-host lc43): mine 1743 ids, Revit's 1755; 0 only mine, 12 only in Revit's rfa, all ParamElemExternal (ids 187616..187627 = the 12 missing parameters). Remaining diffs: Family R (m_familyIds +12 entries pointing at those 12 elements, m_nextAbsorbedIndex 4464->4476, deletion list shifted by 12 entries), VarSketch 951362 m_useCount 35->36 (regen cache), 4 flag words in H (SunAndShadowSettings 8202->8206, DBViewPlan 10->65546).
Fix path: add the project's ParamElemExternal elements referenced by the family's shared parameters to the closure AND to Family.m_familyIds / nextAbsorbedIndex / deletion list (+12 each). This is the same 12-parameter shortfall seen in the oracle facts diff (16 Rebar Shape families 10 of 22 params).
