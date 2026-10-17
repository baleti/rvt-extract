# rvt-extract HANDOFF (c3-fam)

Rule from user (2026-10-17): remote-host is the daily driver. Heavy/whole-project scans go to remote-host via ~/.local/share/offload/h1run
(env rvt), remote-host only tiny single-file checks (MemoryMax 1.5G, nice 19). Queue in ~/demo-state/H1-QUEUE.md.

## Feasibility evidence so far (2026-10-17)
1. A project .rvt DOES embed the family documents of loaded families. Evidence (2020 rst_basic, 50 Family elems, 41 with FamilyBase.m_oFamDoc):
   - Family.m_oFamDoc = FamilyDocument{m_contentDocGUID, m_big2SmallMap2 [(family-local id -> project id)], m_coreIds}.
   - Global/ContentDocuments (rfa: 82 bytes; project: 187 KB, 940 KB inflated) = list of per-family content docs,
     one GUID-keyed segment (13-60 KB) per family: ElemTable-like 28-byte rows (4-byte-id era) + history strings.
   - Partition records of family-internal elements have header [A = family-local id][id = project-unique id][stamp][tag]
     and are NOT in the project Global/ElemTable, which is why rvt_inventory/rvt_scan never decode them
     (they only accept ids of the project ElemTable). Seeding the id candidate set from ContentDocuments u32 values
     decodes them (tools/famscan2.py): ExtrusionElem, RefPlane, CurveElem, SketchPlane, VarSketch, Alignment, ParamElemFamily,
     FilledRegion, FamilySymbol, ... on 2020 rst_basic (18k records over 41 families).
2. Standalone .rfa = same OLE container: BasicFileInfo, Contents, Formats/Latest, Global/{ContentDocuments(82 B),
   DocumentIncrementTable, ElemTable, History, Latest, PartitionTable}, PartAtom (xml), Partitions/N, RevitPreview4.0,
   TransmissionData. Samples: ~/rvt-research/samples-rfa/ (rac_basic_sample_family 2016-2026, only one family).
## Next
- parse ContentDocuments segment layout (per-family ElemTable rows, A/id mapping, history), then full per-family record set
- layer A: JSON/manifest extraction (names, category, types, params, geometry) from the reader; CLI skeleton rvt-extract
- layer B: .rfa assembly (re-key ids A<->project id, rebuild ElemTable/Global/Latest/History/PartAtom), validate in Revit oracle
- ask c3-writer (write-lab) what it knows about rfa assembly (NEEDS-FROM-ORACLE.md)

## Result 1 (2026-10-17, tools/famcensus.py, remote-host 14 s / <1.5 GB for one file): 2020 rst_basic
41 of 50 Family elements carry an embedded family doc; 18,056 family-internal records decoded across them
(RefPlane, CurveElem, VarSketch, ExtrusionElem, SweepElem, BlendElem?, FilledRegion, ParamElemFamily, FamilySymbol, Alignment...).
E.g. M_Baluster - Square: 448 records (14 RefPlane, 19 CurveElem, 2 ExtrusionElem, 7 VarSketch, 3 ParamElemFamily).
Output out/fam_rst20.json (local only).

## RULE (user, 2026-10-17, enforced by a memory guard that SIGKILLs niced jobs <3.5 GB avail on remote-host)
Anything that loads a whole project (rvt-extract on a file, famcensus, geometry) runs ONLY on remote-host via
`~/.local/share/offload/h1run run NAME --env rvt --dir ~/src/rvt-extract -- CMD`; remote-host: edit, git, grep, tiny checks of
already-extracted JSON/pickles. Queue in ~/demo-state/H1-QUEUE.md when remote-host < 11 GB free.

## Result 2 (2026-10-17)
- Censuses on remote-host (out/census_*.json, local): 2017 rst_basic 41 fams/16.6k records, 2023 41/17.8k, 2024 Snowdon Structural 177 fams/76.4k, 2026 177/76.6k.
- Global/ContentDocuments segment per family = [13-byte preamble 0b03ffffffff 0a03ffffffff 00][GUID16][ADocument-like bytes, same layout as an
  .rfa Global/Latest ("1c00ffffffff dc04 ... version strings Revit 20xx ...")][ElemTable-like 28-byte rows (4-byte ids)]. So the three
  rfa pieces (Global/Latest, Global/ElemTable, partition records) all exist per family inside the project.
- Rows to rfa mapping, id re-keying (A<->project id, refs inside records), History/DocumentIncrementTable/PartAtom/Contents: NOT done; waiting for
  Revit-made rosetta rfas (NEEDS-FROM-ORACLE.md item 3, ~/rvt-research/write-lab/gt_fam/).
- fam2 (rvt-extract CLI on Snowdon 2024+2026) queued via tools/h1_retry.sh; results to pull from remote-host ~/src/rvt-extract/out.
