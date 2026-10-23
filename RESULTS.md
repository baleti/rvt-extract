# rvt-extract results (anonymised ids; local only)

Status of .rfa lifting by Revit version (validated = opens in Revit with facts equal to EditFamily+SaveAs):
| Source | Status |
|---|---|
| Revit 2024 (Snowdon Structural, 177 families) | lifts; 177 of 177 (100 %) open in Revit 2024 (2026-10-21, build lift43x, verified last-page sizes; sweep out/rfa_chk/n43_*, 0 fail 0 missing); previous build lift43w: 160 of 177 (90 %) open in Revit 2024 (2026-10-21 sweep + one-session-per-file re-run of failures, build lift43w); 17 fail (Reinf Bar x4, Steel Shear Plate, W Shapes-Side, Level Head, Elevation Marks x2, Fabric Sheet Symbol A, SF_Reference Beam, Concrete Footing, Connection Triangle, Rebar Shape 07, Section Mark head, CMU Standard, Boundary Condition-Variable = nested); progress Oct 18: 77; fixes since: ParamElemExternal closure, ExternalParamTracking, CategoryTracking, m_deletion signed order, VarSketch cache emptied like Revit, verified ECC page sizes |
| Revit 2026 | streams byte-identical for Callout Head; broader validation pending |
| Revit 2017-2023 (4-byte ids) | rfa written but rejected by Revit 2024 (CorruptModelException); layouts unverified |
| Revit 2025 | no Contents stream sample; unverified |
| nested families | not written |

Layer (a) JSON/manifest extraction works for all years. Batch table (tools/sumtab.py, rfaOK = built without error, not Revit-validated unless stated):
    id       fmt       MB  fams   doc  inpl  rfaOK rfaERR rssMB fail
    studyx-001  2019       5   103    95     0      0     95   388 [] 
    studyx-002  2019       9    56    47     2      0     47  1167 [] 
    studyx-003  2019      12   742    18   717      0     18  1738 [] 
    studyx-021  2022      10    32    25     0      0     25  1739 [] 
    studyx-022  2022      12    47    39     0      0     39  2111 [] 
    studyx-023  2022      13    55    47     0      0     47  2129 [] 
    studyx-024  2022      23    77    69     0      0     69  2175 [] 
    studyx-031  2024       3   387     1   379      1      0   670 [] 
    studyx-032  2024       3   387     1   379      1      0   670 [] 
    studyx-033  2024       7   108   100     0    100      0   459 [] 
    ofc-002  2024      10    78    70     0     68      2  1876 [] 
    ofc-003  2024      11    79    71     0     68      3  1852 [] 
    ofc-006  2025       5    42    34     0      0     34   496 [] 
    ofc-007  2025      20    39    23     9      0     23  2231 [] 

## Offline record comparison, Snowdon 2024, RVTX_PEE=1 build vs Revit's own EditFamily+SaveAs rfa (tools/rfa_setcmp.py, 2026-10-20)
177 families lifted. Record id set identical to Revit's: 133; differ: 44 (typically 2-8 ids: regenerated dimension strings / derived records; larger for fabric symbols and framing families). Records byte-identical for all ids: 41; 1-3 byte-differing records: 85; more than 3: 51 (cosmetic: flags, parents lists, regeneration caches). Revit open results for this set: pending (oracle remote-host unreachable, jobs parked).

### Update 2026-10-20 (custom category / style / image closure)
After adding the closure of CategoryElem/GStyleElem referenced by the family's own records and ImageSymbol/ImageHolder referenced by the project-side Family record (rvtx/rfa.py EXTRA), 161 of 177 Snowdon 2024 families have exactly Revit's record id set (was 133). Remaining id differences: LinearDimString ids (Revit renumbers dimension strings: 65 on each side) and 9 extra FillPatternElem records in our output. Revit open checks of this set (out/lift43q) are parked until the Revit host is reachable.
Same comparison for Revit 2026 (Snowdon 55, out/lift55q vs gt_fam/2026_55): 177 lifted, 161 with Revit's exact record id set, 43 with every record byte-identical, 84 with 1-3 differing records; the same residual classes (LinearDimString renumbering, 9 extra FillPatternElem). Revit 2026 open checks pending (Revit host unreachable).

### 2026-10-21 lessons (oracle method)
- Never judge a family from a 10-file slice: one failure poisons later opens in the same Revit session; re-run each failure alone.
- ECC last-page sizes: sizes seen only by stream length (2197, 52813, 19227, 23331) are not safe; use sizes whose parity was reproduced on real Revit pages (rvtx.nladder.VERIFIED, tools/ecc_verify.py).
- Revit empties the VarSketch Z cache (138-byte record) exactly when element flag bit 24 is clear and m_allowResetLineEndConstr is 1 (459 of 459 sketches).

### 2026-10-22 facts diff, Snowdon 2024 (tools/facts_diff.py gt43 vs n43_*)
Oracle facts (category, types, parameters with formulas/storage/shared flag, element-class counts, reference planes, forms) of our 177 lifted families vs Revit's own EditFamily+SaveAs: 170 of 179 gt entries identical; the 9 differences: 6 FillPatternElement count +1..+4 in ours (over-inclusive closure), 1 extra blank type name (SCN_HAS), 2 gt duplicates ("Callout Head.0001", "SFD_Rectangle.0001": gt-side name collision, not families).

### 2026-10-22 real office project, Revit 2024 format (studyx-033, 7 MB, anonymised)
108 families, 100 with embedded documents lifted (8 without: in-place/system), 100 of 100 open in Revit 2024 with no errors or dialogs (oracle/rfacheck.py, slices out/rfa_chk/b33_*). Facts diff vs Revit EditFamily+SaveAs not yet run for this file.
Offline check of 4-byte-id years: partition serialisation (H/R/Z chains) round-trips byte-exactly on the real Revit samples 2016-2026, and the member framing matches for 2019-2026 (deflate bytes differ, as for 2024); so the 2020 failure is not in partition layout.

### 2026-10-22 Revit 2026, Snowdon Structural (build lift55x)
177 of 177 lifted families open in Revit 2026 with no errors or dialogs (oracle/rfacheck.py, out/rfa_chk/n55_*). Facts diff against Revit's own EditFamily+SaveAs (gt_fam/2026_55) not yet run (needs an rfacheck pass over gt_fam/2026_55).

### 2026-10-22 studyx-033 facts diff vs Revit EditFamily+SaveAs (famsave 2024, gt in out/gt_b33)
Found by the diff: the family document's own Family record can carry no types in office projects (94 of 100 lifted families listed no types in Revit although they opened). Fix: copy m_pFamilyTypes from the project-side Family record (rfa.py). After the fix: 100 of 100 open, type count equals Revit's for 96 of 100; type names equal for 23 of 100 (Revit's EditFamily shows the family's original names such as "Standard", the project record carries the project-side renamed names; both are valid); remaining differences: material and appearance asset counts (ours fewer by 2-5 per family, Revit adds default materials on save), a few pattern records, 6 FORM entries, 4 families with a different type count (Toposolid tags 0 vs 1).
Of the 4 type-count differences, 2 (Toposolid Tag, Toposolid Link Tag) are families without an embedded document, which Revit's EditFamily still rebuilds (8 such families in this file: not lifted, listed with status no-embedded-doc in the manifest); 2 differ by one type (Suspended Ceiling Tile Sec, Handrail Elliptical).

### 2026-10-22 LoadFamily into a new project (studyx-033, Revit 2024, RFA_LOAD=1 dedicated runs, 3 slices of 8)
24 of 24 sampled lifted families load (ok=True, family and symbol counts grow, loaded type count equals the family's types, e.g. Baluster_Square 2, Columns_Rectangular 3, Generic_Models_RWP_Square 4). Source: out/rfa_chk/ld33_*/rfacheck.tsv.
The 6 FORM differences (studyx-033) are parametric families whose current type differs: Revit's EditFamily lists the family's original type names in its own order (from the FamilySymbol m_symbolInfo.m_name / FamSymSurrogate records, e.g. 450x450mm), ours lists the project-side Family record (renamed types such as "450 x 450mm", project order and current type index), so form bboxes of the current type differ (Columns_Rectangular 0.98 vs 0.74 ft half width). Both are valid family documents; mapping each project pair to its original symbol name is possible (FamilySymbol.m_symbolInfo.m_name) but not done.
Update: type names now taken from the project-side FamilySymbol names (matched to the Family record's pairs by name ignoring spaces/underscores, rfa.ProjectDocs.symbol_names): names equal Revit's for the 4 spot-checked families (Columns_Rectangular, Doors_IntSgl, RWP_Square, Baluster_Square; all open in Revit 2024, out/rfa_chk/d33). Pair order and current type index still follow the project record (Revit reverses the order for renamed families).
Re-check after the type-name change (build lift_b33e): 100 of 100 open in Revit 2024, 0 failures (out/rfa_chk/e33_*). Snowdon 2024 regression of the type-name change checked offline: 0 of 463 stored types renamed, so the validated Snowdon output is unchanged.

## ofc-002 (office host model, Revit 2024) after the chunk-frame and GUID-order fixes (2026-10-23)
70 families with embedded documents lifted, 70/70 open in Revit 2024 (including the three nested-family title blocks that failed before).

### 2026-10-23 CLI end to end (bin/rvt-extract, all output types)
studyx-033 (Revit 2024): CLI output 100 of 100 .rfa open in Revit 2024 (out/rfa_chk/cli33_*). ofc-006 (Revit 2025, 34 .rfa): 29 open in Revit 2026 by upgrade; 5 fail alone in fresh sessions (out/rfa_chk/solo06_*), all five contain nested family documents (Level Head, Dummy Wall Section head, Elevation Mark Body Circle-12mm, Door Schedule table Hollow Metal1, a title block); non-nested 2025 families open. Revit's own 2026 EditFamily save (out/gt_o6) is in 2026 record format so it cannot be diffed byte for byte. Variants of the nested ContentDocuments segment (raw, unzeroed history) and the audit open did not change the result: the cause is elsewhere (partition of nested docs or ElemTable in 2025 format), needs a Revit 2025 ground truth.

## Summary table per project (measured 2026-10-23, re-sweeps with the current code; oracle = offline Revit via write-lab)
| Project | Revit format | families in file | with embedded doc / .rfa written | opens in Revit | facts vs Revit's own EditFamily+SaveAs |
|---|---|---|---|---|---|
| Snowdon Structural sample | 2024 | n/a | 177 / 177 | 177 of 177 (Revit 2024) | 170 of 177 identical, 7 cosmetic (extra pattern record, extra blank type name) |
| Snowdon Structural sample | 2026 | n/a | 177 / 177 | 177 of 177 (Revit 2026) | 170 of 177 identical |
| office project studyx-033 | 2024 | 108 | 100 / 100 | 100 of 100 (CLI output) | types equal 96 of 100; LoadFamily 24 of 24 sampled |
| office host model ofc-002 | 2024 | 78 | 70 / 70 (incl. 3 nested title blocks) | 70 of 70 | not run |
| office project ofc-006 | 2025 | 42 | 34 / 34 | 29 of 34 (Revit 2026, upgrade); 5 nested-family files rejected | not run |
| 4-byte-id years 2017-2023 | 2017-2023 | - | skipped by default | Revit rejects (CorruptModelException) | - |

### 2026-10-23 facts diff, office host model ofc-002 (Revit 2024, 70 families; Revit's own EditFamily+SaveAs in out/gt_o2full, facts via oracle/rfacheck.py, ours = out/rfa_chk/o2r_*)
- Material count differs in 70 of 70 (Revit adds 3 standard materials at free low ids 1236889-91; no other class differs in 42 of 70 families after ignoring materials and pattern counts).
- Types differ in 28 of 70 (20 by count, 8 by name): our .rfa carries the project-side Family record types (e.g. BL_Round: 1", 2", 3/4"), Revit's EditFamily lists the family's original types (25mm). Both are valid documents; ours reflects the types actually loaded in the project.
- 1 family (AN_CenterLine) differs in parameters: Revit's own save has 2 extra instance parameters (Detail_No, Sheet_Name) with 6 new ids (1237400-05) that do not exist in the project, so Revit creates them on EditFamily; not reproduced.
- 1 family (BL_Round) form bbox differs because the current type differs (see type note).
- Naming caveat: 5 families whose categories our tool cannot name get the folder `Unknown(-2005002)` etc. (category id table gap, tag-type categories).

### 2026-10-23 second 2025 project (ofc-007, Revit 2025 office model, 23 families with embedded documents)
CLI output opened in Revit 2026 (upgrade): 12 open, 11 rejected (CorruptModelException); the 11 rejected are exactly the 11 families that contain nested family documents. With ofc-006: 41 of 57 2025 families open (all non-nested: 41 of 41), nested 0 of 16. The failure is specific to nested documents in 2025-format files (out/rfa_chk/cli07_*, solo06_*).

### 2026-10-23 nested families as standalone .rfa (ofc-002, Revit 2024)
The CLI now also lifts families that exist only as nested documents (recursively): 11 extra .rfa on ofc-002 (81 written in total), 11 of 11 open in Revit 2024 (out/rfa_chk/nn/rfacheck.tsv). Run time 208 s on remote-host under 3 GB.
