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
