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

## c8-famtest handoff 2026-10-21 (claude8)
Done/committed: corpus3 report (93.3% built), Revit 2024 open-check corp-2024-43 (94/138 non-Rebar open, facts 93/94 equal incl. types), older years 2018-2023 0/36 open in Rev 2024, 2026 sample 4/6, 2025->2026 hangs, RESULTS.md + NEEDS-FROM-TEST.md (PEE Rebar Shape rfa HANG Revit on open: regression; 2017 VarSketch).
Key finding: file 0033 (refused in batch) opens ALONE and its R records equal Revit's, so some of the 44 batch refusals are session poisoning. A single-file retest of all 44 is RUNNING: private/oracle_run5.sh (log private/oracle_run5.log, results private/oracle_single.tsv; HANG lines = hang). Kill leftovers on remote-host: ssh remote-host 'pkill -f job_rc_'. When ALLDONE: compare with private/failed44.txt, update RESULTS.md (true open rate), notify c3-fam.
Next: per-year single-file opens, real-world studyx files (30 exceed remote-host slice), Rebar Shape hang bisect.

## c8-famtest handoff 2 (2026-10-21 late)
All committed on branch test. Read NEEDS-FROM-TEST.md (bottom sections) and RESULTS.md: corpus3 93.3% built; Revit 2024 Snowdon: 102/138 non-Rebar open (single-file), Rebar Shape (PEE closure) hang Revit (regression, c3-fam), older years 0/36, 2025 hangs 2026.
Refusal bisect: Partitions/0 stream swap fixes (tools/rfa_streamswap.py), record-only swap does not: causes = missing derived records, nested second document, plus an unknown third (0039). RVTX_ZSTUB=1 is opt-in (net zero).
Tools: oracle/rfacheck.py (single-file sessions; after a hang run ssh remote-host 'pkill -f job_rc_'), tools/rfa_variants.py (id lists), rfa_ndocs.py, rfa_zdiff.py, rfa_zrule*.py. Check for leftover oracle loops (pgrep -f oracle_run) before starting new ones; private/ has all scripts/results.
Next: real-world studyx oracle checks, per-year single-file opens after c3-fam fixes, rerun corpus after fixes.

## c8-famtest takeover (claude8, 2026-10-24)
Merged main into test (clean; RESULTS-fam.md = c3-fam's results file). c3-fam/studyx now reports opens 177/177 (2024, 2026), flat old formats 111/111, nested 2025 still rejected. Launched corpus4 (all 78 corpus files, current main) on remote-host via tools/h1_launch.sh (log private/launch_corpus4.log, waits for gate). Next: report.py on results, oracle opens per year, extractor crash/empty check, update RESULTS.md headline, tell orchestrator.

## 2026-10-22 nested families + oversized-record partition framing (ofc-002 title blocks A0_TitleBlock, LandingPage, BV-BNE: failed with CorruptModelException)
Implemented (committed): nested family documents (rfa.nested_docs: Family records inside the doc with m_oFamDoc -> project docs appended to the partition, ContentDocuments segments with history/content table dropped and history ids zeroed (nested_blob), Latest ContentRecSet + LoadedFamilyInfo m_familyDocGUIDs), DataStorage tolerance (dec_loose, in-place m_famId patch), allocator id from the project ElemTable trailer (kn/ac = trailer+1), sorted m_deletion, cleared m_bindingIds on shared parameter records, tracking sets for DataStorage/ImageSymbol (latest._class_completion), GStyle/ImageHolder owner in ElemTable rows, page padding when a stream is an exact multiple of the page payload.
BISECT (hybrids of Revit's own LandingPage with one of our streams swapped, tools/hybrid2020b.py, hybridpart.py): our Latest, ElemTable, Formats, ContentDocuments, DIT, Contents all open; our partition stream fails even when rebuilt from Revit's own records (P0). Cause found: records larger than a member (embedded image records, 583 KB and 825 KB) must be chunked like Revit: member starts at the item's id, first chunk = item header + 131072 body bytes, further chunks 131072, tail chunk includes the next A, next item starts a new member. partition.cut_points now reproduces Revit's member sizes exactly (LandingPage 30/30, 10 Snowdon families all equal).
REMAINING: the per-member frame field after the 0x0e7c marker (u32 that is 4 in normal members) is 7 in the first and middle chunks of an oversized item and 5 in its last chunk (see frame dump gt vs ours, out/lift_o2m vs out/gt_o2); build_payload still writes 4. Also the first-member x fields. Fix build_payload frames for chunk members, rebuild A0_TitleBlock/LandingPage/BV (lift_all names), run oracle/rfacheck.py (job c8fam_o2m pattern), then the whole ofc-002 set (out/lift_ofc2, 70/70 open before these fixes except these 3) and re-check Snowdon 2024/2026 and studyx-033 for regressions (the ET owner, deletion sort, tracking and cut changes touch every family).

## c8-fam (claude8 takeover) 2026-10-23: oversized-record frames + GUID ordering DONE
- partition.build_payload now writes Revit's frame field for chunks of oversized records (first chunk N=6/x1=1/x2=raw-itemhdr, middle N=7/x1=0/x2=raw, tail N=5/x1=0/x2=raw-4); frames identical to Revit's for LandingPage (tools/frames_dump.py). LandingPage opens in Revit 2024.
- A0_TitleBlock / BV-BNE title block failure cause (bisect with tools/hybridpart.py, hybrid2020b.py, latpatch.py): Latest ContentRecSet and the ContentDocuments segments must be sorted by GUID bytes (Revit keeps them sorted; we used nested-doc order). Fixed in rfa.add_nested_to_latest / streams. All 3 ofc-002 title blocks now OPEN in Revit 2024 (out/rfa_chk/o2q).
- Regression sample (Callout Head, SFD_Rectangle, Boundary Condition-Variable, Hole Tag of Snowdon 2024): records identical to the validated lift (H: 2 cosmetic), all 4 open (out/rfa_chk/reg1).
- Revit also adds standard materials (3 at free low ids 1236889-91) to a family doc when the project lacks them; not required for opening.
- Tools: tools/docdiff.py (per-doc chain diff of two rfa), frames_dump.py, latpatch.py. Oracle caveat: out/rfa_chk/<dir>/rfacheck.tsv can be a STALE file from an earlier run until the queue job reaches done/.
- ofc-002 can be lifted on remote-host for small name sets: private/files/ofc-002.rvt (local copy, git-ignored), 3 GB cap.
- NEXT: full ofc-002 re-lift (70 families) + oracle open check when remote-host gate opens (H1-QUEUE); re-run Snowdon 2024/2026 + studyx-033 full sweeps for regressions; 4-byte years (needs Revit 2020 in oracle); 2025 Contents sample; studyx batch.

## c8-fam stop note 2026-10-23
All re-sweeps with current code open in Revit: Snowdon 2024 177/177 (y43), Snowdon 2026 177/177 (z55), studyx-033 100/100 (b33y), ofc-002 70/70 (o2r). Fixes this session: oversized-record chunk frames, GUID-sorted content records/segments, null m_oContentTable for nested families.
remote-host lift of 2026 project: chunks of 12 get OOM-killed at 3 GB, use 1-4. Local project copies in private/files (git-ignored).
NEXT: 2025 Contents sample (unverified format), 4-byte years 2017-2023 (needs Revit 2020 in oracle, NEEDS-FROM-ORACLE.md), CLI end-to-end run on a project with README numbers, standard materials Revit adds (optional).

## c8-fam (claude8) 2026-10-23 evening
- CLI end to end verified: studyx-033 100/100 open in Revit 2024 (cli33_*). 2025 file ofc-006: 29/34 open in Revit 2026; the 5 failures all have nested family docs (solo reruns fail too; audit open fails; nested segment variants v1/v2 (tools: /tmp script, out/v25) no change). Manifest marks them known-bad (cli.py VALIDATION['2025']).
- Next for 2025 nested: need a Revit 2025 ground truth (none in oracle: VMs 2024/2026) or bisect via hybrids of partition/ElemTable/PartitionTable (2025 uses SS.PT_SAMPLES, not partition_table()); suspect list: PartitionTable sample for 2025, ECC last-page size of multi-doc partition (>130 KB streams), Contents-stream tail.
- Other open items: 4-byte years (Revit 2020 oracle), standard materials Revit adds.
- 2025 nested negatives (all still OPENFAIL in Revit 2026): PartitionTable generated instead of 2025 sample (v3), raw/unzeroed nested segments (v1/v2), Audit open. Record id sets of doc 0/1 equal Revit's gt (only the usual +8/-0 extras), so the records are not the cause; remaining suspects: ElemTable rows of nested ids, partition framing of multi-doc 2025 streams, Latest. CLI got --match REGEX (tested: studyx-033 'tag' -> 15 .rfa in 14 s).
- 2025 nested: variant without the nested doc (v4) also fails (uninformative); ElemTable rows compared with Revit's 2026 save: same pattern as passing families. Everything about nested in 2025 now needs a Revit 2025 native file (a nested family loaded in a 2025-format rfa) to diff; ask orchestrator/user if a Revit 2025 VM or a Revit-2025-saved nested rfa exists.
- Extraction kinds added this session: schedules, revisions, cad_imports, worksets, line_styles (items.py, tests/test_items_new.py covers three). CLI flags: --match, --experimental (4-byte years skipped by default).
- 2025 nested, more negatives: Latest tree diff vs Revit's 2026 save shows only per-save tracking differences also present in non-nested families that open (appInfoArr[14]/[28]/[32]/[171] lengths); the [189] RevisionSettings m_data (4 atoms in Revit's) is empty in ours for Level Head/Dummy Wall but present for Elevation Mark Body (which also fails), so not the cause. Evidence base: 16 of 16 nested 2025 families rejected, 41 of 41 non-nested open (ofc-006, ofc-007).
- 2025 smallest nested bisect case: 'Graphic Scale 1 - 20' of ofc-006 (out/cli_o6n/families/Generic Annotations/Graphic Scale 1 - 20.rfa), nested leaf 'Graphic Scale 1 - 100 5M' opens alone.
- 2025 nested variant v5 (content records kept exactly as in the project, not zeroed): still OPENFAIL. Untested: partition member framing of multi-doc streams in 2025, Latest ptr/handle table of the added content table, ElemTable trailer.
- Doc-boundary zero frame (Revit writes N/x1/comp/x2 = 0 in the frame after the last member of a document; ours wrote a normal frame): implemented as opt-in RVTX_DOCSEP=1 (partition.build_payload), frames now equal Revit's at the boundary, but the 2025 nested files still fail (docsep25: 3 nested fail, non-nested open). Default off because 2024/2026 validated output opens without it.

## 2026-10-24 c8-fam handoff
State: all work committed (main). Nested fix done; README documents system/in-place families as no standalone .rfa.
Open: M_Boundary Condition-Fixed (2017-2023 samples, nested, ArchiveException classTag=32767). Not dangling refs, not class tags. Suspect ElementGroup records with curve/sketch members (only this family has them; TJL groups hold family instances and open). Variants built in out/bcfv/in (v_g, v_gm, v_grp_only; script scratchpad bcfvar.py: drops groups / groups+members / ElementGroup only from the 2022 sample's doc 29).
Running job: oracle queue 000043_bcfvar (rfacheck_j.py 2024), result in ~/rvt-research/write-lab/out/rfa_chk/bcfv/rfacheck.tsv. Whichever variant opens names the cause; then fix the encoder by that class, add test, re-run 2017-2023 samples.
Next: c7 census into NESTED-BY-CATEGORY.md and SCOREBOARD per category/year; 2016 untested (no project); ofc-007 h/k/l families need remote-host via h1run (one job, 11 GB gate); years x class proof table in README.

### BCF bisect result (job 000043, Revit 2024)
v_gm (groups + their CurveElem/SketchPlane/VarSketch/Pattern members dropped) OPENS. v_g (groups only dropped) and v_grp_only (12 ElementGroup only) still fail. So the cause is in the group MEMBER records (CurveElem/SketchPlane/VarSketch/Pattern referenced by the groups), not the group records. Next: bisect by member class (drop only Pattern; only CurveElem+VarSketch; only SketchPlane) using the same script, then diff those records against a working family's equivalents (the same classes occur in TJL Wood Open Web Joist, which opens) and fix the encoder.

## 2026-10-24 c8-fam (claude8, remote-host) stop note
DONE (committed): VarSketch empty-Z block (138 bytes, 8-byte layout) now only for Revit 2024/2026 files (rfa.use_empty_z, tests/test_emptyz.py). Fixed M_Boundary Condition-Fixed (2017-2023) and 2025 failures (Boundary Condition-Fixed, Sym_Detail Guide, Howe Flat Truss, 36 Rebar Shape cancels).
Measured (remote-host oracle, out/chk/*): rst_basic samples 2017-2023 52/52 each in Revit 2024; Snowdon Structural 2024 276/276 (Revit 2024); 2025 276/276 (237 + 42/42 re-lift, Revit 2026); 2026 slice 0 70/70.
Running/queued jobs (write-lab/pipeline/queue): c8x_s2026_70/140/210 (Revit 2026 open check of out/all/2026, results out/chk/s2026_N/rfacheck.tsv). out/all/2026 was lifted BEFORE the use_empty_z year restriction; the restriction does not change 2026 output, so results stand.
Env on remote-host: PYTHONPATH=~/h2/sp (numpy) with ~/rvt-env/bin/python; oracle jobs via pipeline/enqueue.sh; slice checks with RFA_SLICE=a:b (70 files max per job).
NEXT: collect s2026 slices -> README years x class table + SCOREBOARD; 2016 samples; in-place/system families; ofc-007 families; merge branch to remote-host owner (git fetch ssh://user@remote-host~/src/rvt-extract h2-fam).

## h1 studyx (claude8, remote-host) stop note 2026-10-25
Branch h1-studyx (remote-host merges with: git fetch ssh://user1@remote-host~/src/rvt-extract h1-studyx). Big-file low-memory lift: 157/231/461 MB studyx projects lift on remote-host under a 2.7 GB cap (peaks 1.9/1.8/1.7 GB); details in PROGRESS.md. Reader files changed additively OUTSIDE git (~/rvt-research/rvt2text.py: windows, joined_lowmem, member_chunks; rvt_entities.py: extract(window, skip_eh, skip_stubs, reduce)); pre-change copies in ~/studyx-tests/reader/*.pre_window.py. remote-host owner must copy these two files too.
Campaign: ~/studyx-tests/fam/big/campaign.sh (sequential, resumable through lift_big/bigNNN.done; 59 duplicates pre-marked skipped). 11 files done exit 0 (summary lift_big/summary.txt), file 12 was running when stopped; STOP file touched so it ends after the current file. Resume: rm STOP; nohup ./campaign.sh &. Output (client data) stays on remote-host lift_big/.
Open: Revit open-check of samples (out1/out4/out5, lift_big/*) needs remote-host oracle (NEEDS-FROM-ORCHESTRATOR.md); streams >~1.2 GB stored need remote-host (olefile loads whole stream); docdiff.py hardcodes W=8 (2019 files need W=4).

## 2026-11-04 c7x-famlift (remote-host) session note
Branch h2-famlift, all committed, nothing pushed. This session (all unit-tested, suite 67 pass; none opened in Revit, they change manifests and error paths, not rfa bytes):
- cli: dead-PID `.rfa.tmpPID`/`.json.tmpPID` swept from --out at start; --out equal to the input or an existing file exits 2; unreadable/truncated source exits 2 ("cannot read ... nothing written", no --out created); source gzip damage (Partitions/*, Global/*) prints WARNING + manifest.source_damaged (flip at 5/20/40/60/80 pct detected; a flip in Global/Latest is NOT detectable); families without embedded doc get rfa.status=no_embedded_doc.
- Evidence: Revit 2024 deep (depth 2 to 5) sample 24/24 open; big3 b4-b6 36/36; zero-type/zero-param rfa open (124/66 seen). Bit-flip test (Snowdon Structural, 6 offsets): no damaged rfa emitted; damaged families fail with a misleading 'no embedded document' text and rc stays 0.
- GOTCHA: `--low-memory` needs RVT_RESEARCH=~/rvt-research-h1 (default ~/rvt-research lacks window/skip_eh/skip_stubs/reduce args in rvt_entities.extract; TypeError, nothing written). Needs an owner decision on the canonical research tree.
- Open: 2016/2017 files, 2025 nested request (NEEDS-FROM-ORCHESTRATOR.md), real 2021 depth-2 and 2019 title-block data, nonzero rc for damaged sources, rfa determinism (~1070 bytes of GUID/time noise per rfa), Revit VM CID 30 shutdown once idle.

## c8-famtest handoff 3 (2026-10-24, end of session)
Branch test merged with main (b090b75 etc.). Results (valid batches = control before and after pass; all in NEEDS-FROM-TEST.md bottom and PROGRESS.md):
- corpus4 (78 corpus files, current main at launch) on remote-host: unit h1-famtest-corpus4 (state_corpus4, out_corpus4 under ~/src/rvt-extract-test on remote-host); at handoff it was at corp-2026-55/56. Then studyx (real-world, tools/studyx_ok.tsv, BATCH_AS_GB=5) auto-starts via waiter launched from remote-host (private/launch_studyx.log; if the waiter died, rerun: BATCH_AS_GB=5 bash tools/h1_launch.sh famtest-studyx tools/studyx_ok.tsv state_studyx out_studyx). One job at a time on remote-host (user rule).
- Flat .rfa open in Revit (single-file sessions): 2019 2/2, 2020 2/2, 2021 5/5, 2022 5/5, 2023 4/4 (2024 Rev 2024), 2025 5/5 (Revit 2026). 2017 and 2018: refused (CorruptModelException), 2017 re-lift with year fix b090b75 still 3/3 refused; 2018 not re-lifted with new code.
- corpus4 builds: 2017-2020 .rfa built 2589/2589; 17 non-family extractors 0 crashes on 23 files (empties: cad_imports, filters, shared_parameters).
- tools: tools/flatsplit.py (flat vs nested), tools/validate_year.sh (out_corpus4 layout), batch_one records nested.
- Oracle lessons: remote-host oracle is SHARED with c7-studyx; NEVER pkill job_rc_ (I did and caused URLError 10061 faults); a batch is only valid if a control (private/s22c/0002.rfa for 2024, private/c26/c.rfa for 2026) opens before and after. Scripts: private/retest.sh, private/t25.sh, private/t26.sh.
RUNNING: private/t26.sh (2026 flat check of corp-2026-54, result private/t26.res, FINISHED line at end); remote-host unit corpus4; waiter for studyx.
NEXT: (1) read private/t26.res (valid only if control and control_after OPEN) and note in NEEDS-FROM-TEST; (2) when corpus4 ends: python3 tools/report.py <state_corpus4 pulled via tar> -> headline table in RESULTS.md (built %, extractor failures/empties by kind); (3) studyx results with the nested flag; flat/nested open sampling per studyx file; (4) re-lift 2018 and nested families of 2019-2025 with current main and retest; (5) extractor empties vs Revit exports; (6) tell orchestrator headline numbers.
