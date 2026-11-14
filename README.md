# rvt-extract

Extract families and other content from a Revit project (.rvt) without Revit. Own analysis only; local use.

    bin/rvt-extract PROJECT.rvt --list                 # what the file contains (families, counts)
    bin/rvt-extract --list-kinds                       # output types
    bin/rvt-extract PROJECT.rvt --out DIR [--only families,materials,...] [--match REGEX]   # --match: families whose name or category matches (e.g. 'tag|title')

Typical run (measured 2026-10-23, remote-host, one process, under 3 GB): a 7 MB Revit 2024 office project -> 108 families in the manifest, 100 .rfa written, all other output types, in 88 s. The 8 families without .rfa have no embedded document (system/in-place families; status `no-embedded-doc`). Revit itself cannot save system or in-place families as standalone .rfa files, so these are listed in the manifest with their parameters and geometry but get no .rfa by design.

Whole-project loads are heavy: on this machine run them on remote-host (`~/.local/share/offload/h1run`, see HANDOFF.md).

## Output types (DIR/<type>/...)
families (manifest.json + families.csv audit table: category, types, parameters, embedded-record census, nested flag, .rfa status, known_bad reason (empty when none); .rfa only where validated), materials (with appearance assets, textures by library path),
fill_patterns, line_patterns, shared_parameters (+ shared_parameters.txt), project_parameters, filters, phases (phases, phase filters, design options),
levels_grids, views (incl. view templates, sheets), schedules (columns, headers, category; legend names), revisions, line_styles (user-defined line styles: pattern, pen number, colour; built-in styles carry no name in the file), worksets (user worksets with default visibility), cad_imports (imported/linked DWG: name, units, size, layers), images (embedded PNG/JPEG), project_info (+ preview.png), links (TransmissionData).
Next to every .rfa a type catalogue `<Family>.txt` (Revit catalog layout, values in Revit internal units, length, number, angle, area and volume parameters typed with their internal unit (feet, radians), others `##other##`, only named non-instance values) is written.
DIR/manifest.json lists counts and errors per type.

Families that exist only as nested documents inside other families (not loaded in the project) are extracted as standalone .rfa too (manifest `origin: nested in <parent>`; ofc-002: 11 of 11 open in Revit 2024).

## How families are found
A project embeds the full document of each loaded family: Family.m_oFamDoc, a per-family segment in Global/ContentDocuments
(ADocument-like data plus table rows) and the family-internal element records in the partitions (header: family-local id, project id).
See HANDOFF.md for the evidence and status of the .rfa assembly.

## Exit codes and source safety
The source .rvt is only ever read (checked: read-only copy in a read-only directory, checksum/size/mtime unchanged). Outputs are written tmp + fsync + rename.
- 0 done (a family can still be listed with rfa.status error / no_embedded_doc / skipped / known_bad: read the manifest or the known_bad column of families.csv)
- families.csv is written verbatim (RFC 4180 quoting, names unmodified): a family or type name that starts with = + - @ is kept as is, so a spreadsheet may evaluate it as a formula when the CSV is opened. Import it as text, or read manifest.json instead.
- 2 bad usage or unreadable source (`--out` is the input or an existing file; truncated/garbage .rvt); nothing written
- 3 the source has damaged gzip members (manifest.source_damaged): failed families carry rfa.likely_cause=source_damaged, written ones rfa.from_damaged_source, and the family LIST can be incomplete (2019 sample with one flip: 50 of 61 families listed). A flip inside Global/Latest cannot be detected (no checksum)
- 4 the source changed (size/mtime) while it was being read: discard the output
- 5 at least one .rfa could not be written (I/O error such as disk full, quota, or an unwritable --out directory); no partial file or tmp residue is left, the manifest records rfa.status=error
`--low-memory` needs a research tree whose rvt_entities.extract accepts window/skip_eh/skip_stubs/reduce (RVT_RESEARCH=~/rvt-research-h1 on remote-host).
A stderr warning appears when available memory is under about 80 times the source size (measured once: a 28 MB project peaked at 1.9 GB); a native allocation failure otherwise aborts with rc 134 and no message.

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

Added 2026-11-13 (Revit 2026 open facts only, no LoadFamily/geometry; from c7x-famlift item 161, progress log): HEAD extraction of the Snowdon Structural 2026 wrote 276 rfa, Revit 2026 open 276/276 (isFam=True, 0 failures), diskaudit 0 findings; the 4 Boundary Condition families open (the earlier CorruptModelException came from a stale Oct-24 output, not HEAD).
Added 2026-11-13 (Revit 2026 open facts only, c7x-famlift item 163): HEAD extraction of the Snowdon Structural 2025 wrote 276 rfa, diskaudit 0 findings, Revit 2026 upgrade-open 276/276 (isFam=True, 0 exceptions; run as two slices of 147 and 131 with 2 overlapping).

Not covered: 2016 (no project). Real (non-sample) projects: big2 and big3 contain families nested at depth 2 to 5 (up to 125 depth-2 and 25 depth-3 to 5 families in a single project); the Revit open results for those are in the big3 line above (sampled, not exhaustive) and a targeted sample of 24 depth-2-to-5 rfa (b4 to b6) opened in Revit 2024: 24/24 isFam=True, 0 rejected (sample only).

Added 2026-11-07 (Revit 2024 upgrade-open, open facts only, no geometry/LoadFamily): HEAD 2017 and 2018 rst_basic outputs 52/52 open each; 30-file sample (every 27th) of the 800 families lifted from one 157 MB real 2019 project 30/30 open. Control for the 2020 Pile Cap known_bad: on the public 2020 rst_advanced sample both Revit's own copy and our lift of the 3 Pile families open (3/3 each), so that registry entry is specific to one local client project and its cause stays unproven. There is no native Revit 2019 oracle (add-in is signed only for 2024/2026 in the VM); 2019-2023 are always upgrade-open checks in Revit 2024.
Added 2026-11-11 (Revit 2024 upgrade-open, open facts only, no LoadFamily/geometry): HEAD extraction of the Door|Window|Furniture|Column families of the Autodesk rst_advanced samples (FLAT families: the manifests show 0 nested in 2017-2023 rst_advanced, so this is a flat-family check; the 2020 Commercial sample set has 1 nested of 10): 2017 14/14, 2018 14/14 (run as two slices; a single 14-file run lost its Revit connection once, not reproduced), 2019 14/14, 2021 14/14, 2022 14/14, 2023 14/14; 2020 Commercial sample 10/10. 2024-2026 are covered by the earlier rows.
Added 2026-11-11 (Revit 2024, open + LoadFamily, local real 2019 project of 157 MB, aggregate only): full HEAD extraction on a 60 GB host (no --low-memory) wrote 800 families (+7 without embedded document, 0 errors); random 100 of them open 100/100 and load 100/100. The same project on the 2.7 GB-capped host with --low-memory wrote the same 800 (AB_CL03: all streams identical except BasicFileInfo, Global/History, PartAtom); random 40 open and load 40/40; four sibling revisions (466-491 families each) 10 random each 40/40. An older (2026-11-07) capped run on a previous code state was bad (20 of 30 CorruptModelException, 242 rows failed at exit code 0); it is quarantined, and the CLI now prints a WARNING when more than 10% of families with an embedded document fail. The 'unverified risk' heuristic (nested + ProjectPhase, 2019-2023 formats) is a manifest risk_note, not known_bad: 0 of 6 flagged files were rejected.
Added 2026-11-11 (OPEN SEMANTIC GAP, real office project): first Revit ground truth (EditFamily+SaveAs) on a real 5.3 MB 2019 project, 59 families (50 written, 8 nested): all 50 open and 49 load; against Revit's own saves 26 of 38 comparable families are identical in types/params/refplanes and 12 differ in the TYPE COUNT only (params and refplanes equal in 38/38): 11 where Revit's save lists 1 type and ours 2-5, 1 (a structural column) where Revit lists 3 and ours 1 (W200/W250/W400 vs W400). rfa.py fills m_pFamilyTypes from the project-side Family record when the embedded family document carries none (office projects), which is a heuristic reconstruction; it is not yet proven to match what Revit lists. Autodesk samples do not show this (177/177 identical). Treat type lists of lifted real-project families as unverified until this is resolved.
Update 2026-11-12 (OPEN, per-type VALUES): new TVAL rows in oracle/rfacheck.cs + tools/tvalcmp.py compare every (type, parameter) value of an extracted .rfa with Revit's own EditFamily+SaveAs of the same family. Autodesk 2023 rst_basic, 30 families comparable: values identical in 5, differ in 25. Typical: our rfa has HasValue=false ("(none)") for parameters where Revit's save carries a value (e.g. a baluster 25mm type, Width 0.082 ft in Revit); some parameters are missing on one side. The type NAMES and counts are mostly right, but per-type parameter values of lifted families cannot be trusted yet; the files open and load. Suspected cause (not proven): the project-side Family/FamilySymbol type records reference parameter ids (e.g. 4293958673) of the project's family-side numbering, which have to be remapped onto the parameter ids of the lifted family document.
Update 2026-11-12 (per-type values, partial fix): type value records referenced PROJECT-side parameter ids; rfa.py now remaps them to the lifted family document's parameter ids by caption and clears project-side ElementId values on the remapped entries (RVTX_PARAMREMAP=0 disables). Autodesk 2023 rst_basic vs Revit's own EditFamily+SaveAs: per-type values identical 5/30 -> 15/30 families; type/param/refplane counts unchanged (37 identical, 4 differ in type count only), 52/52 open. A first version without the ElementId clearing dropped a parameter in 2 families (Revit ignores an ElementId value that points outside the family), hence the clearing. Remaining 15 value differences: missing/extra parameters in the compared set (Assembly Code, Cost), types Revit lists that we do not, Pile-Steel diameters (a differing value), shared-parameter keys; not yet analysed.
Year table 2026-11-12 (Autodesk rst_basic sample of each year, HEAD with all type/value switches, Revit 2024 open + LoadFamily, vs Revit's own EditFamily+SaveAs of the same file; 52 families lifted each): 
| year | open | LoadFamily ok (LOADFAIL) | counts identical (with ground truth) | per-type values identical |
|---|---|---|---|---|
| 2017 | 52/52 (after item-94 fix, merged slices) | 47/51 (0 LOADFAIL) | 40/40 (after item-94 fix) | 24/30 (re-measured after the own-family caption fix: 6 families differ, 8 values in all: 6 are ElementId values we clear on purpose, 2 are built-in defaults of timber_door_int; no regression) |
| 2018 | 52/52 | 49/52 (0) | 41/41 | 24/30 |
| 2019 | 52/52 (after item-94 fix, merged slices) | 50/51 (0 LOADFAIL) | 41/41 (after item-94 fix) | 24/30 (re-measured after the own-family caption fix: same 6 families differ, 9 values in all: 6 ElementId values cleared on purpose, 3 built-in defaults (door Analytic Construction, Define Thermal Properties by; Brick Height 0); no regression) |
| 2020 | 52/52 (HEAD 5bbdf8e, merged slices, 0 OPENFAIL) | 49/52 (0 LOADFAIL, HEAD) | 41/41 (earlier run; no ground-truth dir at HEAD, not re-compared) | 24/30 (earlier run, not re-measured at HEAD) |
| 2021 | 52/52 (HEAD 5bbdf8e, merged slices) | 49/52 (0 LOADFAIL) | 41/41 | 24/30 (re-measured at HEAD: 6 families differ: 5 are ElementId values cleared on purpose, 1 (timber_door_int) shows 2 built-in defaults Analytic Construction / Define Thermal Properties by) |
| 2022 | 52/52 (HEAD 5bbdf8e, merged slices, 0 OPENFAIL) | 49/52 (0 LOADFAIL, HEAD) | 41/41 (earlier run, not re-compared at HEAD) | 24/30 (earlier run) |
| 2023 | 52/52 (HEAD 5bbdf8e, merged slices, 0 OPENFAIL) | 49/52 (0 LOADFAIL, HEAD) | 41/41 (earlier run, not re-compared at HEAD) | 24/30 (earlier run) |
The not-ok loads are loads into a project that already holds the family name (not a file defect; single-file check 2026-11-13: Pile Cap-9 Pile loads ok alone for both our file and Revit's own save, so batch order matters; the 2 Circle-12mm Mark Pointer files that failed in a 12-file batch also load ok alone, both as Revit's original and as our CFB rewrite, identical results: the failures are batch effects, not file defects: in the batch, M_Elevation Mark Body_Circle-12mm1 loads first and adds 2 families (13->15), i.e. it carries the Pointer families nested, so the later loads of the Pointer files find the names already present). The 2 count differences in 2017, 2019, 2021, 2022 are the same two families (Brick - UK Standard, M_Elevation Mark Body_Circle-12mm1: 0 types vs Revit's 1), present before the type work; 2018, 2020, 2023 are free of them. These are flat+nested mixed (12 nested of 52); depth-2 and nested type values are not separately measured. 2024-2026 not re-run with the new switches.
Update 2026-11-12 (final state of the day, Revit 2024, fresh EditFamily+SaveAs ground truth, all three data sets): Autodesk 2020 rst_basic, Autodesk 2023 rst_basic and the real 5.3 MB 2019 office project: every lifted rfa opens (52/52, 52/52, 50/50), no LoadFamily failure (the 3+3+1 not-ok loads are the name-already-present case, loaded into a project that already holds the name), type/parameter/refplane counts identical to Revit's own save for all families with ground truth (41/41, 41/41, 38/38; 26/38 on the office project before the day's work), per-type parameter values identical in 24/30, 24/30 and 28/32 families (5/30 and 22/32 at the start). Remaining value differences are not analysed yet (a brick family, joist, door and some shared/ElementId parameters). Env switches: RVTX_SYMTYPES, RVTX_PARAMREMAP, RVTX_REMAPEID, RVTX_PRUNETYPES (all default on; 0 disables).
Update 2026-11-12 (types from project symbols): the type list of a lifted family is now built from the project-side FamilySymbols (name + their current parameter values, ids remapped), because Revit's EditFamily lists exactly those (RVTX_SYMTYPES=0 restores the Family-record list). Autodesk 2023 rst_basic vs Revit's EditFamily+SaveAs: 52/52 open; type/param/refplane counts identical in 41 of 41 families with ground truth (was 37 of 41); per-type parameter values identical in 27 of 30 comparable families (was 5 of 30 at the start of the day). The 3 remaining value differences: a brick family (extra parameter, missing values), a joist (2 values) and a door (2 values). Not yet re-run: other years, the real office project, LoadFamily on the new output.
Update 2026-11-12 (type-count gap): Revit's EditFamily lists exactly the project-side FamilySymbols. rfa.py now drops Family-record types without a project symbol by default (RVTX_PRUNETYPES=0 disables). Autodesk 2020 rst_basic, the 11 families the change affects, Revit 2024 vs Revit's own EditFamily+SaveAs: types identical 3/11 before, 10/11 after; all 11 open (LoadFamily 10/11, the 1 is a name-already-present case); real 2019 project, 30 of 50 re-checked: open 30/30, load 30/30, 23 identical, 0 differ. Still open: families where Revit lists MORE types than ours (project has symbols the Family record lacks: Rectangular(Timber)-Beam 1 vs 2, a structural column 1 vs 3): needs symbol-side type data to add types, not implemented.
Added 2026-11-11 (genuine nested sets, Revit 2024 upgrade-open, open facts only, no LoadFamily/geometry): HEAD extraction of the 13 families (12 nested, 1 at depth 2) of each Autodesk rst_basic sample 2017-2023: 13/13 open in every year (2018 needed a second full run: the first run lost its Revit session at one family, which opened fine alone and in the re-run).

## Semantic check against Revit's own save (Snowdon Structural 2024, 2026-11-04)
`tools/gtcmp.py INDEX.tsv rfacheck.tsv...` compares what Revit reads in an extracted .rfa (types, parameters, reference planes) with the index of the same family saved by Revit itself (EditFamily + SaveAs). On all 276 families opened in Revit 2024 (276 open as families, 0 open failures), the 177 that have an index row are identical on all three counts, 0 differ; 99 have no index row. Counts only, not values or geometry.
Note on type counts: manifest `types[]` (and the families.csv `types` column) include the blank-named default type that Revit stores next to real types, so it is one higher than the type list Revit shows when a family has named types (14 Autodesk 2022 families: non-blank names equal Revit's TYPE rows in 13, the 14th has only the blank type). Count names that are not blank when comparing with Revit.

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

Autodesk 2020 Residential sample, random 12 lifted families: 10 open in Revit 2024; the other 2 (TV_STAND_6078, Corner Shower) fail with "The input curve is not bound", and so do Revit's own EditFamily+SaveAs copies of the same two families in the same check, so this is a property of the source families or the open check, not of the lift (both are in rvtx/known_bad.tsv).

Title blocks: lifts made before the ElemTable owner-ring fix (bdcfd33) hung Revit 2024 in OpenDocumentFile for nested title blocks of 2020, 2021 and 2023 (no dialog). After the fix the 2020, 2021 and 2023 ones tested open; the title block rows above show the pre-fix state and are being re-lifted. Flat title blocks always opened.

Exit codes and the INCOMPLETE marker (verified by real kill/limit/truncate runs, 2026-11-08): 0 ok; 2 unreadable or hostile source (nothing written); 3 damaged gzip members (output kept, failed families listed in the manifest, no marker); 4 source changed during the run and 5 output could not be written (both leave `families/INCOMPLETE`); 143/137 after SIGTERM/SIGKILL (marker stays, checkpoint manifest). Re-running into the same `--out` completes, clears the marker and warns about overwritten rfa.

Added 2026-11-14 (sweep slices, Revit 2024 upgrade-open, open facts only): 8 slices of 45 extracted families each (360 families): 360 opened as families, 0 open failures. Partial: only these slices of the sweep were checked.

Added 2026-11-14: 12 pile families lifted at HEAD from a real 2020 project (kept local): Revit 2024 upgrade-open 12/12 opened as families, 0 failures (open facts only). Pile families lifted in October 2026 with the old encoder had been rejected (11/11, CArchiveException 105); that does not reproduce at HEAD.

Added 2026-11-14: Revit 2025 same-year open (not upgrade) of 26 families sampled evenly from the 2025 Snowdon Structural extraction: 26/26 opened as families, 0 failures (open facts only; a sample, the exhaustive 276/276 check was in Revit 2026).

Added 2026-11-14: Revit 2020 same-year open (not upgrade) of all 52 families extracted from the public 2020 rst_basic sample: 52/52 opened as families, 0 failures (open facts only).
