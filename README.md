# rvt-extract

Extract families and other content from a Revit project (.rvt) without Revit. Own analysis only; local use.

    bin/rvt-extract PROJECT.rvt --list                 # what the file contains (families, counts)
    bin/rvt-extract --list-kinds                       # output types
    bin/rvt-extract PROJECT.rvt --out DIR [--only families,materials,...] [--match REGEX]   # --match: families whose name or category matches (e.g. 'tag|title')

Typical run (measured 2026-10-23, remote-host, one process, under 3 GB): a 7 MB Revit 2024 office project -> 108 families in the manifest, 100 .rfa written, all other output types, in 88 s. The 8 families without .rfa have no embedded document (system/in-place families; status `no-embedded-doc`). Revit itself cannot save system or in-place families as standalone .rfa files, so these are listed in the manifest with their parameters and geometry but get no .rfa by design.

Whole-project loads are heavy: on this machine run them on remote-host (`~/.local/share/offload/h1run`, see HANDOFF.md).

## Output types (DIR/<type>/...)
families (manifest.json + families.csv audit table: category, types, parameters, embedded-record census, nested flag, .rfa status; .rfa only where validated), materials (with appearance assets, textures by library path),
fill_patterns, line_patterns, shared_parameters (+ shared_parameters.txt), project_parameters, filters, phases (phases, phase filters, design options),
levels_grids, views (incl. view templates, sheets), schedules (columns, headers, category; legend names), revisions, line_styles (user-defined line styles: pattern, pen number, colour; built-in styles carry no name in the file), worksets (user worksets with default visibility), cad_imports (imported/linked DWG: name, units, size, layers), images (embedded PNG/JPEG), project_info (+ preview.png), links (TransmissionData).
Next to every .rfa a type catalogue `<Family>.txt` (Revit catalog layout, values in Revit internal units, length, number, angle, area and volume parameters typed with their internal unit (feet, radians), others `##other##`, only named non-instance values) is written.
DIR/manifest.json lists counts and errors per type.

Families that exist only as nested documents inside other families (not loaded in the project) are extracted as standalone .rfa too (manifest `origin: nested in <parent>`; ofc-002: 11 of 11 open in Revit 2024).

## How families are found
A project embeds the full document of each loaded family: Family.m_oFamDoc, a per-family segment in Global/ContentDocuments
(ADocument-like data plus table rows) and the family-internal element records in the partitions (header: family-local id, project id).
See HANDOFF.md for the evidence and status of the .rfa assembly.

## Limits
.rfa output status by Revit format (details and numbers in RESULTS.md):
- 2024: validated. 177 of 177 Snowdon families and 100 of 100 families of a real office project open in Revit 2024; oracle facts (category, types, parameters, formulas, element counts) equal Revit's own EditFamily+SaveAs for 170 of 179 compared (residual: extra pattern records).
- 2026: 177 of 177 Snowdon families open in Revit 2026; facts diff pending.
- 2017-2023 (4-byte element ids): flat and nested families are written (Autodesk sample projects 2017, 2018, 2019, 2020, 2021, 2022, 2023: 52 of 52 families each open in Revit 2024, which upgrades them on open; 2026-10-24). 2016: skipped unless `--experimental` (no test project). JSON/manifest extraction works for all.
- 2025: 57 of 57 sampled families of two office projects (ofc-006, ofc-007; including every nested-family .rfa, 0 of 20 before) open in Revit 2026 (upgrade open, 2026-10-24).
Shared-parameter closure (needed by Rebar Shape families) is on by default; RVTX_PEE=0 disables it. The manifest field `rfa.validation` states the status per file.

## Years x class (lifted / opens in Revit; Autodesk sample projects only, 2026-10-30, tools/yeartable.py)
Projects: 2017-2023 = rst_basic_sample_project of that year (opened in Revit 2024, upgrade open); 2024, 2025, 2026 = Snowdon Towers Structural of that year (2024 checked in Revit 2024, 2025 and 2026 in Revit 2026). Classes: flat = no nested family; parent = family that contains nested families; depth2 = nested depth >= 2; standalone = copy of a family that exists only nested inside another.

| year | flat | parent | depth2 | standalone nested | no .rfa (system/in-place) |
|---|---|---|---|---|---|
| 2017-2023 (each) | 30/30 | 10/10 | 1/1 | 11/11 | 9 |
| 2024 | 141/141 | 32/32 | 4/4 | 99/99 | 8 |
| 2025 | 141/141 | 32/32 | 4/4 | 99/99 | 8 |
| 2026 | 141/141 | 32/32 | 4/4 | 99/99 | 8 |

Not covered: 2016 (no project), a real (non-sample) 2017-2023 project, depth 2 beyond 1 to 4 families per project.

## Real-project campaign sample (opens in Revit 2024, 2026-11-01; aggregate numbers only, files stay local)
Families lifted from real office projects and opened in Revit 2024 (rfacheck, upgrade open). Stratified sample (382 + 64 families, 2019-2025): 0 rejected among 430 checked non-title-block families (2019 64, 2020 63, 2021 52, 2022 62, 2023 63, 2024 64, 2025 62). Cells are opened / checked.

| year | stratified sample flat | stratified sample nested | nested title blocks |
|---|---|---|---|
| 2019 | 28/28 | 36/36 | none in sample |
| 2020 | 29/29 | 34/34 | 0/1 pre-fix (hang), opens after ring fix |
| 2021 | 30/30 | 22/22 | 0/10 pre-fix (hang), 10/10 open after ring fix |
| 2022 | 27/27 | 35/35 | flat title blocks 2/2 open |
| 2023 | 30/30 | 33/33 | 0/1 pre-fix (hang), opens after ring fix |
| 2024 | 31/31 | 33/33 | none in sample |
| 2025 | 26/26 | 36/36 | 2/2 open (1 nested) |

Big-file sample (96 families from 12 large projects): before the 2026-11-01 fix 84 open and 12 rejected ("needs recovery"), all 2022 nested. Cause: an integer 0 under an ...Id key was treated as an element reference and pulled the project CategoryElem with id 0 into the family (rfa._eids, tests/test_eids_zero.py). Re-lifted with the fix: 12 of 12 open (the nested title block also needed the ElemTable owner-ring fix), the old versions still rejected.

remote-host lift of 6 further large projects (one 2019 format, the rest mostly 2022; 3387 rfa from 3440 families; the 53 families without .rfa are system families with no embedded document, status by design): Revit 2024 spot check of 96 sampled families, 96 opened, 0 rejected. Spot check only (about 3% of the lifted files).

big3 (remote-host, 2026-11-02, aggregate): 3 further large projects (about 160 MB each). b2 and b3 completed (124 rfa each, 29 min each); b1 hit the 10000 s limit with 528 rfa written. Revit 2024 upgrade-open of sampled rfa: 12/12 (b1), 12/12 (b2), 12/12 (b3), 0 rejected. A killed or timed-out run now leaves `families/INCOMPLETE` and a manifest checkpointed after every family (before the fix b1 left 304 of 528 rfa unlisted); do not trust a directory containing INCOMPLETE as a finished extraction. b4 (722 rfa), b5 (571), b6 (573) also completed (rc 0, manifest equals disk, every stream readable); Revit 2024 open of 12 sampled each: 36/36 open, 0 rejected. b4 was re-run into a dir holding 583 rfa of a killed run, flagged as overwritten_rfa in its manifest.

Title blocks: lifts made before the ElemTable owner-ring fix (bdcfd33) hung Revit 2024 in OpenDocumentFile for nested title blocks of 2020, 2021 and 2023 (no dialog). After the fix the 2020, 2021 and 2023 ones tested open; the title block rows above show the pre-fix state and are being re-lifted. Flat title blocks always opened.
