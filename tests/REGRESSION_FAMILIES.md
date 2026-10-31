# Permanent regression families (Autodesk sample projects only; Revit-open check required, run via oracle/rfacheck.py)
Re-lift these after any encoder change and open them in Revit; each failed once.
| family (project) | years | failure | cause / fix |
|---|---|---|---|
| M_Boundary Condition-Fixed (rst_basic) | 2017-2023 | Revit 2024 ArchiveException too many corrupt elements | 138-byte empty VarSketch Z block belongs only to the 8-byte layout; use_empty_z year restriction (tests/test_emptyz.py) |
| Boundary Condition-Fixed, Sym_Detail Guide, Howe Flat Truss, 36 Rebar Shape (Snowdon Structural) | 2025 | rejected in Revit 2026 | same empty Z block, now only 2024/2026 |
| every nested family (rst_basic, Snowdon, office files) | 2017-2025 | rejected | doc-boundary tail block between documents of a multi-document partition stream (tests/test_nested.py) |
| Rebar Shape 00-xx | 2024+ | task dialog 'required internal settings missing' | shared-parameter closure (RVTX_PEE) |
| title blocks (ofc-002) | 2024 | rejected | GUID-sorted content records |
| 20 nested families of each of two real 2020 projects (office files, local only; ids n00-n19) | 2020 | formerly 0/17 rejected in Revit 2024 | same doc-boundary tail fix; re-lifted with current code: 20/20 open (8 MB project), 20/20 open (38 MB project). Not a test input (files stay local); keep re-lifting after any partition/rfa change. Autodesk 2020 sample nested guard stays tests/test_nested.py |
| 12 of 20 nested families of the big-file sample (office projects, local only; ids big002-big012) | 2022 | rejected in Revit 2024 (needs recovery) | int 0 under an ...Id key treated as element reference, pulling the project CategoryElem id 0 into the family (tests/test_eids_zero.py); studyx_CW301 re-lifted: opens, old file still rejected (local var_zero set). Other 11 not yet re-lifted |
