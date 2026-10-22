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

## KEY RESULTS 2026-10-17 evening (Revit oracle works for 2024/2026 only; 2020 add-in unsigned)
- oracle/famsave.py (+famsave.cs): EditFamily+SaveAs of every family -> ~/rvt-research/write-lab/gt_fam/<tag>/<Category>/<Family>.rfa + index.tsv. Enqueue via write-lab pipeline/enqueue.sh (jobq). Test 2024 Snowdon 43: 2 families, 96 s. Full run 0992_famsave_43 queued -> gt_fam/2024_43.
- A Revit-saved .rfa of a project family has the family's own records BYTE-IDENTICAL to the ones embedded in the project (same A, same project id,
  213/216 for Callout Head; differing: Family (rfa bigger), Viewer, DimensionStyle). NO id re-keying needed.
- The rfa additionally holds ~1490 shared records (GStyleElem, MaterialElem, patterns, assets) with the same ids as the project's but different bytes (diff being analysed: tools/cmpdiff.py).
- Global/Latest of the rfa = 99.3% verbatim runs of the project Global/Latest + parts of the CD segment (tools/align.py). ADocument root decodes with u16 tag at 0 and fields from offset 2
  (rvt_global.decode_global used u32 tag: wrong); m_ownerFamilyId = family project id.

## PARTITION FORMAT (own analysis 2026-10-17 from Revit-saved rfa gt_fam + write-lab wlpart notes) -> rvtx/partition.py
joined payload (all gzip members concatenated, frames removed) = 3 chains, then (for families with nested families) further H,R,Z triples of the nested documents:
 H: [id W][L u32][body L] first record without A; next records [A4=prev L][id][L][body]; body starts with u16 tag (ElementHeader); sorted by id; ends with terminator id=-1,L=0
 R: [A4=prev total len - 20][id W][stamp4 = adler32(body)][L4][body L]  (hs=12+W=20); sorted by id; ends with terminator (id=-1, stamp 1, L=0)
 Z: same layout as R; tag SerializedDummy (L=2, 22 bytes) per element, GElement/other for graphic elements; ends with terminator; then 4 zero bytes at the very end of the last triple
 members: <= ~131071 raw bytes, cut right after an A field; each region starts a new member; frames 32 B between members: 75 0e | comp_k+8 u32 | 7c 0e 04 00 00 00 | x1_next u32 (#A fields starting in next member) | comp_next+8 | x2_next = raw_next - hs*x1_next (hs 16 in H, 20 in R/Z) | region counter u8 (101 H,102 R,103 Z) | 7 zero bytes
 44-byte header: u64 9 | 7b03 | 0000 | element count u32 | 7c0e 04000000 | x1_0 | comp_0+8 | x2_0 | 0x65 ...; whole stream is ECC-paged (write-lab rvtw.Stream/ecc.parity).
 Element record stamp = adler32(body after L). Shared elements (GStyleElem, MaterialElem, patterns, assets) copied into a family doc have Element.m_famId (8 bytes at record offset 74) set to the family id (project has -1) and stamp recomputed; family-own records are byte-identical to the project ones.
 Global/Latest of an rfa = project Global/Latest verbatim runs + family content-doc segment parts (ADocument decodes with u16 tag at offset 0, fields from 2). Global/History etc. small, GUIDs fresh.

## MILESTONE 2026-10-18: lifted .rfa open in Revit 2024 (oracle: oracle/rfacheck.py)
Callout Head and SFD_Rectangle (2024 Snowdon Structural) lifted from the project with rvtx/rfa.py: Revit 2024 opens them; API facts (category, types, 22 params + formulas,
element-class counts, forms/bbox) are IDENTICAL to Revit's own EditFamily+SaveAs rfa (gt_fam). Stream-level: Global/Latest and Global/ElemTable are byte-identical to Revit's;
partition items: R records 100% equal, Z equal except 1 regen cache, H equal except 3 own cosmetic (flags/parents). Recipe (rvtx/rfa.py Builder):
 - partition = project doc k (own H/R/Z, k via Family.m_oFamDoc.m_big2SmallMap2) + shared standard elements from the main doc (builtin-category GStyleElem + referenced Material/patterns/assets/
   PropertySets + materials Default/Poche/Phase-*; + dependency closure of the family's own records) with m_familyId/m_famId := family id, m_deletion += family id, flags &= ~0x10, regenHistory cleared;
   KeynoteTable/AssemblyCodeTable re-created (ids max+1, max+2, blank resource references); Family record: m_familyIds, m_nextAbsorbedIndex, versions, famDocGUID, deletion list.
 - Latest = ADocument tree: family blob (ContentDocuments segment) with handles shifted, tracking sets filled from the project's (filtered to ids present), ESSchemaStorage copied (rvtx/latest.py, encoder rvtx/enc.py, exact round trip).
 - ElemTable rows rvtx/elemtable.py; small streams rvtx/smallstreams.py; container rvtx/cfbw.py; partition framing/ECC paging rvtx/partition.py (last page size must be one Revit writes: rvtx/nladder.py + odd-u L=2047 ladder).
 - Contents stream: Revit validates its 46-byte tail (depends on exact compressed bytes): a Revit-written instance is reused (SS.CONTENTS_STREAM + GUID). The 64-byte partition tail blob may be zero.
 - LoadFamily into a project in the same oracle session poisons later opens: rfacheck RFA_LOAD=1 only for a dedicated run.
Next: all 177 families (lift_all.py on remote-host) + oracle open/facts diff vs gt_fam; nested families; 2026 and older years; CLI wiring; README.

## USER REQUEST 2026-10-18 (priority): broad testing across years 2017-2026 and real studyx office projects
Rules: studyx files only (never officeA/officeB), files stay local, never committed; anonymous ids studyx-NNN; private mapping in private/map.tsv (git-ignored; out/ and private/ are ignored and were purged from history).
Candidate list: private/studyx_all.tsv (1145 rvt, via the `search` CLI), format scan private/studyx_versions.tsv (tools/scan_versions.py on remote-host).
Plan: pick 30-60 files (years/sizes/disciplines) + Autodesk samples; run `rvt-extract` per file on remote-host with per-family error capture (tools/lift_all.py style, robust); oracle opens (2024/2026; older = upgrade);
facts diff vs EditFamily+SaveAs for a sample per file; failure classification and fixes; RESULTS.md (anonymised) + README limits.
Known state: 2024 Snowdon: 177 families lift OK; Revit opens ~all except Profiles/Rebar Shape/Level Head families (being diagnosed: Rebar Shape lacks ParamElemExternal shared parameter closure; others VarSketch R diffs);
2026: Latest/ET/PartitionTable/ContentDocuments byte-identical to Revit's for Callout Head. Oracle jobs must stay < 280 s per job (10-file slices).

## STATE 2026-10-18 evening (weekly budget nearly spent: finish with documentation)
DONE: .rfa lifting works and is Revit-validated for Revit 2024 (177 families of Snowdon 2024: most open; facts identical to EditFamily+SaveAs), 2026 streams byte-identical for Callout Head.
Known failing classes (2024): Profiles/Rebar Shape/Level Head families refuse to open (diagnosis tools/lift_cmp.py: VarSketch R and some H differ; Rebar Shape lacks ParamElemExternal (shared parameter)
elements that Revit adds -> add ParamElemExternal to rfa.TARGET closure); nested families (second doc partition + ContentDocuments + LoadedFamilyInfo not written).
Older formats (4-byte ids, 2019-2023): code path written (elemtable.build4, W-aware partition) but lifted 2020 rfa do NOT open in Revit 2024 yet (CorruptModelException) -> format-specific row/stream layouts unverified.
2025: no Contents instance (CONTENTS_SAMPLES from sample families added, unverified).
Batch: tools/run_batch.sh over private/map.tsv (53 files: 40 studyx-NNN + 13 ofc-NNN; officeA/officeB now allowed locally, shown only as ofc-NNN) -> out/studyx/<id>/summary.json; table: python3 tools/sumtab.py.
Oracle: oracle/rfacheck.py (keep jobs < 280 s: RFA_SLICE=a:b, RFA_FLAT=1), oracle/famsave.py. gt_fam/2024_43 and 2026_55 are the ground truth sets.
Next if budget allows: ParamElemExternal closure; VarSketch diffs; per-file Revit open sampling for studyx 2024 files; RESULTS.md.

## c7-fam takeover 2026-10-19 (claude7)
Read all state. Blockers today: remote-host MemAvailable ~3 GB (monero VM + gpu-host; gate 11 GB closed), remote-host Revit VMs down, remote-host ~3 GB free (guard kills niced jobs <3.5 GB). No heavy runs or oracle validation possible; nothing was run or changed in code.
Priority list when unblocked: (1) ParamElemExternal closure in rfa.TARGET (Rebar Shape), (2) VarSketch R diffs for Profiles/Level Head, (3) nested families (2nd doc partition, ContentDocuments, LoadedFamilyInfo), (4) 4-byte-id years 2017-2023 (CorruptModelException on 2024 open: verify on a 2023 Revit-saved rfa, needs oracle for older year), (5) 2025 Contents sample, (6) RESULTS.md table per sample project, README limits section.
Layer (a) JSON/manifest extraction is already in rvtx/cli.py + manifest.py.
- Added opt-in env RVTX_PEE=1 (ParamElemExternal in TARGET closure), committed, UNTESTED. Test: h1run lift_cmp.py (see H1-QUEUE), then oracle open check of the rebuilt Rebar Shape when VMs are up. remote-host gate still closed (3.8 GB) at this point; I keep polling it via `ssh remote-host grep MemAvailable /proc/meminfo`.
- EVIDENCE (c7-fam 2026-10-19, tools/rfa_classdiff.py, light): lifted Rebar Shape 00.rfa has 1743 records, Revit's own gt_fam has 1755: the 12 extra are all ParamElemExternal (tag 3008), nothing else differs by class. So the Rebar Shape open failure = missing ParamElemExternal closure. Next: on remote-host check whether those 12 ids exist in the project main doc and whether own records reference them (RVTX_PEE=1 test queued, c7fam-pee).
- EVIDENCE Profiles/Level Heads (rfa_classdiff): same record set except LinearDimString ids differ (Revit regenerates dimension strings with new ids: W Shapes 2, Level Head 1) and byte diffs in 1 VarSketch (all), RadialDim (3-4 in W Shapes/Level Head), Family. Roof Deck: only 1 VarSketch differs and it still fails to open => the VarSketch R difference is the prime suspect for Profiles. Next: decode-diff that VarSketch (tools/lift_cmp.py walk_diff, needs project load on remote-host).
- EVIDENCE 2 (tools/rfa_recdiff.py, light): Roof Deck (fails to open) differs from Revit's rfa in R only by a VarSketch guess-cache useCount (6 vs 7): cosmetic, so NOT the cause. ElemTable/PartitionTable/Formats/Latest streams differ in size from gt for both failing and OPENING families (Hole Tag) so those are not diagnostic. Profiles failure cause remains open: look at H/Z chains and Global/Latest of Roof Deck vs a Profiles family Revit accepts (dimension tracking sets: LinearDimString ids differ, m_ArrSegInfo id 14 vs 15 in RadialDim/dims). Rebar Shape cause is established (12 missing ParamElemExternal).
- 2026-10-19 BISECT: tools/rfa_variants.py re-serialises a lifted rfa with H/R/Z records swapped for Revit's (round trip of 'none' is byte-identical). Oracle run (out/rfa_chk/var1): ALL variants incl. Roof Deck unchanged ('none') OPEN fine in Revit 2024 now, although the same file bytes were OPENFAIL on Oct 18 (lift43_* runs). So the Oct 18 failures for Profiles may be an oracle-session artefact (order/poisoning), not a file defect. Full re-check of all 177 queued as c7fam_full_* slices -> out/rfa_chk/f43_*/.
- 2026-10-20 00:25: remote-host unreachable (ssh: No route to host), oracle jobs fail at scp. PEE rebuild of all 177 Snowdon 2024 families is DONE (out/lift43p, 177 written; Rebar Shape 00 record set == Revit's, Family R record identical). The 18 oracle slice jobs (c7fam_p000..p170, 10 files each, output out/rfa_chk/p43_NNN) are PARKED in write-lab/pipeline/hold/: move back to pipeline/queue when remote-host is up. Also var2 (out/var2) for the Roof Deck order question: enqueue again from the same command (oracle/rfacheck.py 2024 out/var2 out/rfa_chk/var2).
- NOTE: h1run does not sync ~/src/rvt-extract; rsync it by hand: rsync -a --exclude=.git --exclude=out --exclude=private ./ remote-host:src/rvt-extract/ before each remote-host job.

## c8-fam state 2026-10-21 evening
- 177/177 Snowdon 2024 lifted .rfa open in Revit 2024 (out/lift43x, sweep out/rfa_chk/n43_*). Fix chain: ParamElemExternal + ExternalParamTracking + CategoryTracking (latest.py), Family H m_deletion signed sort, VarSketch Z emptied by rule (flag bit24 clear and allowResetLineEndConstr==1), verified ECC page sizes (nladder.VERIFIED). Tools: oracle/rfacheck.py (auto-dismiss dialogs; run each failure alone, a crash/failure poisons later opens in the same session), tools/oracle_summary.py, rfa_hdiff/zdiff/zclass, lat_two, ecc_verify.
- Oracle hygiene: timed-out jobs leave orphan python procs queued on the VM lock (kill them); jobq job timeouts must exceed a slice.
- TODO next: (1) facts diff (params/types/geometry) of all 177 vs gt_fam, LoadFamily into a project (RFA_LOAD=1 dedicated run); (2) same for 2026 Snowdon (gt_fam/2026_55); (3) 4-byte-id years 2017-2023 and 2025 (needs Revit of that year or 2024 upgrade open); (4) nested families (2nd doc partition; ids only A 4 for Boundary Condition-Variable now opens but nested docs not written); (5) studyx/other projects batch; (6) README limits.

## c8-fam state 2026-10-22 (session stopped by orchestrator, user limit)
DONE: Snowdon 2024 facts diff 170/179 identical (RESULTS.md); studyx-033 (real office 2024 file) 100/100 lifted families open in Revit 2024; README limits and per-format `rfa.validation` in the manifest.
4-byte years (2017-2023) bisect: fixed build4 shared/special row width (24 -> 28 bytes); partition stream must carry Revit's per-year name (rfa.PARTITION_NUMBER, 2020 -> Partitions/63; hybrid tools/hybrid2020.py: real 2020 streams open only with the real name). Lifted 2020 files still raise CorruptModelException in Revit 2024. Verified offline: partition H/R/Z serialisation and member framing (2019-2026), Global/Latest encode round trip (2016-2026).
OPEN: native 4-byte ground truth needs Revit 2020 in the oracle: guest.fresh(2020) returns None (unsigned add-in); request filed in ~/rvt-research/NEEDS-FROM-ORACLE.md (job c8fam_fs20 failed for that reason). Unknown: the 4-byte own/shared ElemTable row layout (own row may equal the ContentDocuments row verbatim, as in 8-byte; cd_rows4 may be off by one word). Then: nested families, 2025 Contents sample, facts diff for studyx-033 (famsave 2024), LoadFamily run.
PENDING oracle jobs in write-lab/pipeline/queue: c8fam_n55_0..17 (Revit 2026 open check of out/lift55x; slices 0 and 1 were 10/10 open); results land in out/rfa_chk/n55_*/rfacheck.tsv (check with grep -c '^OPEN').
- 2026-10-22: Revit 2026 open check of out/lift55x: slices n55_0,1,16,17 = 37/37 open; n55_2..15 failed (Revit did not start) and were requeued as c8fam_m55_2..15 (results out/rfa_chk/n55_N).
- 2026 open check complete: 177/177 (RESULTS.md).

## 2020 bisect findings (2026-10-22, hybrids via tools/hybrid2020.py, hybrid2020b.py, hybrid2020c.py; results out/rfa_chk/hyb*)
Base = real Revit 2020 sample family (opens in Revit 2024). Opens: A/D (our container writer, real partition name; renamed partition fails), E (partition re-serialised and re-framed by rvtx.partition with our deflate and ECC paging), S1/S3/S4/S5/S6 (our History, PartAtom, BasicFileInfo, Preview, ContentDocuments). Fails: S2 = our 2024-template Global/DocumentIncrementTable (InternalException): the 2020 DIT has a different layout (tag 6c04, entries with 12 x ffffffff runs, user name, element count 0x6d6 repeated), the 2024 template must not be used for older years. Lifted 2020 files fail earlier (CorruptModelException, CArchiveException 105, also with Audit) and still do after: ElemTable shared/special row width fix, owner+a,b words from the CD rows, year-specific partition name. Replacing only the DIT by the sample's does not change that (T1), so at least one more stream is wrong: remaining suspects Global/Latest (ADocument tree of a 4-byte project, lat_two diff vs sample shows ids/maps only), ElemTable shared-row semantics, record content. Next step needs Revit 2020 in the oracle (NEEDS-FROM-ORACLE.md) to get a native lifted ground truth; then diff stream by stream (rfa_setcmp/lat_two/et diff) as done for 2024.
- 2026-10-22: lift_all on ofc-002 (Host-Model_General.rvt, 2024) exceeds the remote-host 3 GB cap (dies after 6 families); queued for remote-host in H1-QUEUE.md; then rsync ~/src/rvt-extract (excluding out/private) to remote-host and run the oracle open check on the output.
- remote-host sees the office files under <private-corpus> (not /mnt/remote-host-backups): run lift_all there with that path, e.g. h1run run NAME --env rvt --dir ~/src/rvt-extract -- python3 tools/lift_all.py '<private-corpus> samples/DGCL/BEP/References/Host-Model_General.rvt' out/lift_ofc2 (gate 11 GB closed at 9.6 GB on 2026-10-22).
