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
.rfa output is Revit-validated only for Revit 2024 (see RESULTS.md); other years and nested families are JSON/manifest only. Shared-parameter closure (needed by Rebar Shape families) is on by default; RVTX_PEE=0 disables it.

Measured (RESULTS.md, 2026-10-21): the .rfa builder succeeds for 93.3% of the 10,191 embedded families of the 78-file Autodesk corpus (all of 2018-2026 except 12 in 2024; 2017 fails on the VarSketch decode). Revit acceptance of the built files: 2024 Snowdon Structural 102 of 138 non-Rebar-Shape families open (74%), their parameters, reference planes, forms and category equal Revit's own EditFamily+SaveAs; the Rebar Shape families built with the shared-parameter closure hang Revit 2024 on open (use RVTX_PEE=0 for those); lifted files of 2018-2023 and 2025 are not accepted by Revit 2024/2026 (0 of 36 sampled in 2024; 2025 hangs 2026). Treat .rfa output from any year but 2024 as experimental; the JSON/manifest outputs work for all years.
