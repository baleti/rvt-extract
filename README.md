# rvt-extract

Extract families and other content from a Revit project (.rvt) without Revit. Own analysis only; local use.

    bin/rvt-extract PROJECT.rvt --list                 # what the file contains (families, counts)
    bin/rvt-extract --list-kinds                       # output types
    bin/rvt-extract PROJECT.rvt --out DIR [--only families,materials,...]

Whole-project loads are heavy: on this machine run them on remote-host (`~/.local/share/offload/h1run`, see HANDOFF.md).

## Output types (DIR/<type>/...)
families (manifest: category, types, parameters, embedded-record census; .rfa only where validated), materials (with appearance assets, textures by library path),
fill_patterns, line_patterns, shared_parameters (+ shared_parameters.txt), project_parameters, filters, phases (phases, phase filters, design options),
levels_grids, views (incl. view templates, sheets), images (embedded PNG/JPEG), project_info (+ preview.png), links (TransmissionData).
DIR/manifest.json lists counts and errors per type.

## How families are found
A project embeds the full document of each loaded family: Family.m_oFamDoc, a per-family segment in Global/ContentDocuments
(ADocument-like data plus table rows) and the family-internal element records in the partitions (header: family-local id, project id).
See HANDOFF.md for the evidence and status of the .rfa assembly.

## Limits
.rfa output status by Revit format (details and numbers in RESULTS.md):
- 2024: validated. 177 of 177 Snowdon families and 100 of 100 families of a real office project open in Revit 2024; oracle facts (category, types, parameters, formulas, element counts) equal Revit's own EditFamily+SaveAs for 170 of 179 compared (residual: extra pattern records).
- 2026: 177 of 177 Snowdon families open in Revit 2026; facts diff pending.
- 2017-2023 (4-byte element ids): .rfa is written but Revit rejects it so far; JSON/manifest extraction works for all years.
- 2025: no reference Contents stream; unverified. Nested families (a family loaded inside another) are not written into the .rfa yet.
Shared-parameter closure (needed by Rebar Shape families) is on by default; RVTX_PEE=0 disables it. The manifest field `rfa.validation` states the status per file.
