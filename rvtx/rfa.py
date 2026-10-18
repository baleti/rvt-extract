"""Lift a family document out of a project into a standalone .rfa (Revit 2024 layout). Own analysis; validated against Revit-saved rfa (tools/rfa_check*.py)."""
import struct, zlib, copy, uuid, time, re, os, bisect, collections
import numpy as np
from . import RESEARCH  # noqa
from . import partition as PT, enc, latest as LAT, elemtable as ET, smallstreams as SS, cfbw
import olefile
import rvt_scan as S, rvt_decode as D, rvt2text as T, rvtfmt, fmt_parser as fp

EID = D.EID
TARGET = {'MaterialElem', 'FillPatternElem', 'LinePatternElem', 'AppearanceAssetElem', 'PropertySetElement'}
SPECIAL_MATERIALS = {'Default', 'Poche', 'Phase-Demo', 'Phase-Exist', 'Phase-Temp'}
KEY = re.compile(r'(Id|Ids|ElemId|Pattern|Material)$')


def _sg(v):
    return v - (1 << 64) if v >= (1 << 63) else (v - (1 << 32) if (1 << 31) <= v < (1 << 32) else v)


def _eids(o, out, key=''):
    if isinstance(o, EID): out.add(int(getattr(o, 'v', o)))
    elif isinstance(o, bool): pass
    elif isinstance(o, int):
        if KEY.search(key): out.add(o)
    elif isinstance(o, dict):
        for k, v in o.items(): _eids(v, out, k)
    elif isinstance(o, list):
        for v in o: _eids(v, out, key)


class ProjectDocs:
    """everything about a project needed to lift families out (heavy: whole partition parsed)"""
    def __init__(self, prj):
        self.prj = prj; path = prj.path; self.path = path
        self.o, self.cls, self.ids = S.load(path); self.W = S.id_size(self.cls); self.sch = D.Schema(self.cls)
        pn = [y for y in ['/'.join(e) for e in self.o.listdir(streams=True)] if y.startswith('Partitions/')][0]
        j = T.joined(self.o.openstream(pn).read()); self.docs = PT.parse_joined(j, self.W); del j
        self.cd = rvtfmt.inflate_stream(self.o.openstream('Global/ContentDocuments').read())[1]
        self.formats_raw = self.o.openstream('Formats/Latest').read()
        self.byid = {i: r for (i, c), r in prj.recs.items()}
        self.doc0 = {'H': dict(self.docs[0]['H']), 'R': {i: (b, s) for i, b, s in self.docs[0]['R']}, 'Z': {i: (b, s) for i, b, s in self.docs[0]['Z']}}
        self.id_doc = {}
        for k, d in enumerate(self.docs):
            if k == 0: continue
            for i, b in d['H']: self.id_doc.setdefault(i, k)
        d = enc.decode_tree(self.sch, self.W, self.o and rvtfmt.inflate_stream(self.o.openstream('Global/Latest').read())[1], 2, 28)
        self.latest_tree = d[0]; self.tag_adoc = 28
        self.max_id = max(i for i in self.ids if i < (1 << 40))
        self.kn_proj = next((i for i, r in self.byid.items() if r['class'] == 'KeynoteTable'), None)
        self.ac_proj = next((i for i, r in self.byid.items() if r['class'] == 'AssemblyCodeTable'), None)
        self.guid_pos = {}
        self.standard = self._standard_shared()

    # ---- shared (standard) elements: builtin-category graphics styles + referenced materials/patterns/assets + the special materials
    def _standard_shared(self):
        seed = set()
        for i, r in self.byid.items():
            c = r['class']
            if c == 'GStyleElem':
                cat = r['fields'].get('m_categoryId')
                if cat is not None and _sg(int(getattr(cat, 'v', cat))) < 0: seed.add(i)
            elif c == 'MaterialElem':
                m = r['fields'].get('m_pMaterial'); m = m.get('obj', m) if isinstance(m, dict) else {}
                if m.get('m_name') in SPECIAL_MATERIALS: seed.add(i)
        return self.close(seed)

    def close(self, seed):
        shared = set(seed); frontier = set(seed)
        while frontier:
            nxt = set()
            for i in frontier:
                r = self.byid.get(i)
                if r is None: continue
                out = set(); _eids(r['fields'], out)
                for e in out:
                    q = self.byid.get(e)
                    if q is not None and q['class'] in TARGET and e not in shared: nxt.add(e)
            shared |= nxt; frontier = nxt
        return shared

    def family_doc_index(self, fam_rec):
        d = fam_rec['fields'].get('m_oFamDoc')
        if not d: return None
        cnt = collections.Counter()
        for p in d['obj']['m_big2SmallMap2']:
            s = p['second']; s = s['m_id'] if 'm_id' in s else s['m_id64']
            k = self.id_doc.get(int(getattr(s, 'v', s)))
            if k: cnt[k] += 1
        return cnt.most_common(1)[0][0] if cnt else None

    def segment(self, guid_hex):
        g = self.cd.find(bytes.fromhex(guid_hex)); n, = struct.unpack_from('<I', self.cd, g + 16)
        return g, self.cd[g + 20:g + 20 + n]


NEG = (1 << 64) - 1


class Builder:
    def __init__(self, pd):
        self.pd = pd; self.sch = pd.sch; self.W = pd.W
        self.E = enc.Enc(self.sch, self.W)

    # --- record tree helpers
    def dec(self, body, defined=(1, 2)):
        tag = struct.unpack_from('<H', body, 0)[0]
        v, p, c = enc.decode_tree(self.sch, self.W, body, 2, tag, defined=defined)
        assert c and p == len(body), 'record not fully decoded (%s)' % self.sch.name(tag)
        return tag, v

    def encode(self, tag, tree):
        return struct.pack('<H', tag) + self.E.body(tag, tree)

    def edit(self, body, fn):
        tag, t = self.dec(body); fn(t); return self.encode(tag, t)

    def tag_of(self, body):
        return struct.unpack_from('<H', body, 0)[0]

    def class_of(self, body):
        return self.sch.name(self.tag_of(body))

    # --- build
    def build(self, fam_rec, out_path=None, when=None, own_only_report=False):
        pd = self.pd; f = fam_rec['fields']
        k = pd.family_doc_index(fam_rec); assert k, 'family has no embedded document'
        doc = pd.docs[k]
        oH = {i: b for i, b in doc['H'][:-1]}; oR = {i: (b, s) for i, b, s in doc['R'][:-1]}; oZ = {i: (b, s) for i, b, s in doc['Z'][:-1]}
        own = set(oH)
        fid = next(i for i, (b, s) in oR.items() if self.class_of(b) == 'Family')
        # shared set: standard + dependencies of the family's own records
        deps = set()
        for i, (b, s) in oR.items():
            out = set(); _eids(self.dec(b)[1], out)
            for e in out:
                q = pd.byid.get(e)
                if q is not None and q['class'] in TARGET and e not in pd.standard and e not in own: deps.add(e)
        shared = set(pd.standard) | pd.close(deps)
        kn, ac = pd.max_id + 1, pd.max_id + 2
        fam_guid = f['m_famDocGUID']['m_guid']
        g, blob = pd.segment(f['m_oFamDoc']['obj']['m_contentDocGUID']['m_guid'])
        # ---- items
        H, R, Z = {}, {}, {}
        for i in own: H[i] = oH[i]; R[i] = oR[i]; Z[i] = oZ.get(i)
        def fix_h(b):
            def fn(t):
                t['m_familyId'] = EID(fid)
                t['m_parents']['obj']['m_deletion'].append(EID(fid))
                t['m_abFlags4Bytes'] = t['m_abFlags4Bytes'] & ~0x10
                t['m_regenHistory']['m_historyMap'] = []
            return self.edit(b, fn)
        def fix_r(b):
            return self.edit(b, lambda t: t.__setitem__('m_famId', EID(fid)))
        for i in shared:
            H[i] = fix_h(pd.doc0['H'][i]); R[i] = (fix_r(pd.doc0['R'][i][0]), None); Z[i] = pd.doc0['Z'].get(i)
        for new, old in ((kn, pd.kn_proj), (ac, pd.ac_proj)):
            def hh(t, new=new, old=old):
                dl = t['m_parents']['obj']['m_deletion']
                t['m_parents']['obj']['m_deletion'] = [EID(new) if int(x) == old else x for x in dl]
            H[new] = fix_h(self.edit(pd.doc0['H'][old], hh))
            def rr(t, new=new):
                t['m_id'] = EID(new); t['m_famId'] = EID(fid); t['m_lastReadSucceeded'] = 0
                t['m_oKeyBasedTreeEntries'] = {'null': 0}
                for cell in t['m_cellList']['obj']['m_cells']:
                    o = cell.get('obj') or {}
                    if 'm_externalResourceReferences' in o:
                        o['m_externalResourceReferences'] = []
                        for e in o['m_externalResourceReferencesExpanded']:
                            for r in e['second']['m_refs']:
                                x = r['second']; x['m_displayPath'] = ''; x['m_version'] = ''
                                x['m_referenceInformation'] = [{'first': 'ModelIdentity', 'second': '00000000-0000-0000-0000-000000000000'}, {'first': 'Path', 'second': ''}, {'first': 'PathType', 'second': 'Absolute'}]
            R[new] = (self.edit(pd.doc0['R'][old][0], rr), None)
            Z[new] = pd.doc0['Z'].get(old)
        all_ids = sorted(H)
        # ---- Family record + header
        shared_sorted = sorted(shared | {kn, ac})
        def fam_r(t):
            t['m_appVersionAtLoad'] = 0xFFFFFFFE; t['m_appVersionAtInitialLoad'] = 0xFFFFFFFE
            t['m_famDocGUID']['m_guid'] = fam_guid
            base = t['m_nextAbsorbedIndex']
            t['m_nextAbsorbedIndex'] = base + len(shared_sorted)
            idx = {e: base + n for n, e in enumerate(shared_sorted)}
            ent = {int(x['m_elementId']): x for x in t['m_familyIds']['obj']['m_data']}
            tmpl = next(iter(ent.values()))
            data = []
            for e in all_ids:
                if e == fid: continue
                if e in idx: x = copy.deepcopy(tmpl); x['m_elementId'] = EID(e); x['m_index'] = idx[e]; data.append(x)
                elif e in ent: data.append(ent[e])
            t['m_familyIds']['obj']['m_data'] = data
            pr = t['m_pFamilyTypes']['obj']['m_pairs']
            if len(pr) == 1 and pr[0]['name'] == f.get('m_name'): pr[0]['name'] = ' '
        R[fid] = (self.edit(R[fid][0], fam_r), None)
        def fam_h(t):
            d = t['m_parents']['obj']['m_deletion']
            t['m_parents']['obj']['m_deletion'] = [d[0]] + [EID(e) for e in sorted({int(x) for x in d[1:]} | set(shared_sorted))]
        H[fid] = self.edit(H[fid], fam_h)
        self.fam_rec = fam_rec; self.fid = fid; self.kn = kn; self.ac = ac; self.shared = shared; self.own = own; self.all_ids = all_ids; self.H, self.R, self.Z = H, R, Z; self.blob = blob; self.k = k
        return self

    # ---- assemble streams
    def doc_items(self):
        NEGW = (1 << (8 * self.W)) - 1
        ids = self.all_ids
        Hl = [(i, self.H[i]) for i in ids] + [(NEGW, b'')]
        Rl = [(i, self.R[i][0], 0) for i in ids] + [(NEGW, b'', 1)]
        Zl = [(i, self.Z[i][0], 0) for i in ids if self.Z.get(i)] + [(NEGW, b'', 1)]
        return {'H': Hl, 'R': Rl, 'Z': Zl}

    def partition_stream(self):
        payload = PT.build_payload([self.doc_items()], self.W)
        return PT.page_stream(payload)

    def global_stream(self, name, raw):
        co = zlib.compressobj(6, zlib.DEFLATED, -15); z = co.compress(raw) + co.flush()
        gz = PT.GZH + z + struct.pack('<II', zlib.crc32(raw) & 0xFFFFFFFF, len(raw))
        return PT.page_stream(struct.pack('<Q', SS.PREFIX[name]) + gz)

    def streams(self, family_name, category, path, when=None):
        pd = self.pd; when = when or time.time()
        save_guid = str(uuid.uuid4()); doc_guid = str(uuid.uuid4()); part_guid = str(uuid.uuid4())
        n = len(self.all_ids)
        g, blob = pd.segment(self.fam_rec['fields']['m_oFamDoc']['obj']['m_contentDocGUID']['m_guid'])
        tag = pd.tag_adoc
        bt, _, _ = enc.decode_tree(self.sch, self.W, blob, 2, tag)
        lt, notes = LAT.build_tree(self.sch, pd.latest_tree, bt, set(self.all_ids), remap={pd.kn_proj: self.kn, pd.ac_proj: self.ac})
        latest = LAT.encode(self.sch, self.W, tag, lt)
        rows = ET.cd_rows(pd.cd[g:g + 400000])
        et = ET.build(self.all_ids, self.own, rows, self.fid, special_neg=(self.fid, self.kn, self.ac))
        st = {}
        st['Formats/Latest'] = pd.formats_raw
        st['Global/Latest'] = self.global_stream('Global/Latest', latest)
        st['Global/ElemTable'] = self.global_stream('Global/ElemTable', et)
        st['Global/History'] = self.global_stream('Global/History', SS.history(doc_guid, save_guid))
        st['Global/DocumentIncrementTable'] = self.global_stream('Global/DocumentIncrementTable', SS.document_increment_table(n, when))
        st['Global/PartitionTable'] = self.global_stream('Global/PartitionTable', SS.partition_table(part_guid))
        st['Global/ContentDocuments'] = self.global_stream('Global/ContentDocuments', SS.content_documents_empty())
        st['Partitions/0'] = self.partition_stream()
        st['BasicFileInfo'] = SS.basic_file_info(path, save_guid)
        raw = SS.contents(part_guid)
        st['Contents'] = SS._CONTENTS_HEAD + PT.GZH + self._deflate(raw) + struct.pack('<II', zlib.crc32(raw) & 0xFFFFFFFF, len(raw)) + b'\0' * 46
        st['TransmissionData'] = SS.transmission_data(self.kn, self.ac)
        st['PartAtom'] = SS.part_atom(family_name, category, os.path.basename(path), when)
        st['RevitPreview4.0'] = SS.preview()
        self.last_trees = (lt, bt)
        return st

    @staticmethod
    def _deflate(raw):
        co = zlib.compressobj(6, zlib.DEFLATED, -15); return co.compress(raw) + co.flush()

    def write(self, out_path, family_name, category):
        st = self.streams(family_name, category, out_path)
        open(out_path, 'wb').write(cfbw.write_rfa(st)); return st
