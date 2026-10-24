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
- 2017-2023 (4-byte element ids): flat and nested families are written (Autodesk sample projects 2017, 2018, 2019, 2020, 2021, 2022, 2023: 51 of 52 families each open in Revit 2024, which upgrades them on open; the one failure is a nested boundary-condition family, under investigation; 2026-10-24). 2016: skipped unless `--experimental` (no test project). JSON/manifest extraction works for all.
- 2025: 57 of 57 sampled families of two office projects (ofc-006, ofc-007; including every nested-family .rfa, 0 of 20 before) open in Revit 2026 (upgrade open, 2026-10-24).
Shared-parameter closure (needed by Rebar Shape families) is on by default; RVTX_PEE=0 disables it. The manifest field `rfa.validation` states the status per file.
