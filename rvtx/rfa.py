"""Lift a family document out of a project into a standalone .rfa (Revit 2024 layout). Own analysis; validated against Revit-saved rfa (tools/rfa_check*.py)."""
import struct, zlib, copy, uuid, time, re, os, bisect, collections
import numpy as np
from . import RESEARCH  # noqa
from . import partition as PT, enc, latest as LAT, elemtable as ET, smallstreams as SS, cfbw, dit_samples as DITS
import olefile
import rvt_scan as S, rvt_decode as D, rvt2text as T, rvtfmt, fmt_parser as fp

EID = D.EID
TARGET = {'MaterialElem', 'FillPatternElem', 'LinePatternElem', 'AppearanceAssetElem', 'PropertySetElement'}
if os.environ.get('RVTX_PEE', '1') != '0': TARGET = TARGET | {'ParamElemExternal'}  # shared-parameter closure (Rebar Shape: record set == Revit's); RVTX_PEE=0 disables
EXTRA = {'ImageSymbol', 'ImageHolder', 'CategoryElem', 'GStyleElem'}  # custom categories / subcategory styles / raster images referenced by the family (own records or the project-side Family record)
SPECIAL_MATERIALS = {'Default', 'Poche', 'Phase-Demo', 'Phase-Exist', 'Phase-Temp'} | set(x for x in os.environ.get('RVTX_MATS', '').split(',') if x)
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


_EMPTY_Z = bytes.fromhex('3f08ffffffffffffffffa69f0e00000000000480080000000000' + 'ea8ca039593e2946' * 3 + 'ea8ca039593e29c6' * 3 + 'ea8ca039593e2946' * 3 + 'ea8ca039593e29c6' * 3 + 'a69f0e00000000000200000000000000')


def use_empty_z(W):
    """the 138-byte empty VarSketch cache is the 8-byte-id layout: 4-byte years keep the project Z unless RVTX_EMPTYZ4=1"""
    return os.environ.get('RVTX_EMPTYZ', '1') != '0' and (W == 8 or os.environ.get('RVTX_EMPTYZ4', '0') == '1')


def empty_varsketch_z(i):
    return _EMPTY_Z.replace(struct.pack('<Q', 0xE9FA6), struct.pack('<Q', i))


# partition stream numbers Revit wrote in its sample families (a 2024 lift with Partitions/0 opens; older formats need the year's number)
PARTITION_NUMBER = {2017: 60, 2018: 61, 2019: 62, 2020: 63, 2021: 64, 2022: 65, 2023: 66}


def _norm_type(n):
    return re.sub(r'[\s_]+', '', n or '').lower()


def _null_exprs(o):
    """decoded project records show an absent expression as None; the encoder wants the pointer form {'null': 0}"""
    if isinstance(o, dict):
        for k, v in o.items():
            if k == 'm_oExpression' and v is None: o[k] = {'null': 0}
            else: _null_exprs(v)
    elif isinstance(o, list):
        for v in o: _null_exprs(v)
    return o


class ProjectDocs:
    """everything about a project needed to lift families out (heavy: whole partition parsed)"""
    def __init__(self, prj):
        self.prj = prj; path = prj.path; self.path = path
        self.o, self.cls, self.ids = S.load(path); self.W = S.id_size(self.cls); self.sch = D.Schema(self.cls)
        self.byid = {i: r for (i, c), r in prj.recs.items()}
        # items of the main document that may be copied into family documents (graphics styles, materials, patterns, assets, property sets, keynote/assembly tables)
        keep = {i for i, r in self.byid.items() if r['class'] in TARGET or r['class'] in EXTRA or r['class'] in ('KeynoteTable', 'AssemblyCodeTable')}
        self.docs = [None]; self.doc0 = {'H': {}, 'R': {}, 'Z': {}}
        pns = sorted((y for y in ['/'.join(e) for e in self.o.listdir(streams=True)] if y.startswith('Partitions/')), key=lambda s_: int(s_.split('/')[1]))
        for pn in pns:
            try:
                j = T.joined(self.o.openstream(pn).read()); ds = PT.parse_joined(j, self.W); del j
            except Exception as e:
                self.errors = getattr(self, 'errors', []) + ['%s: %s' % (pn, e)]; continue
            for kdoc, d in enumerate(ds):
                if kdoc == 0:      # first document of every partition = part of the main document
                    for i, b_ in d['H']:
                        if i in keep: self.doc0['H'][i] = b_
                    for i, b_, st_ in d['R']:
                        if i in keep: self.doc0['R'][i] = (b_, st_)
                    for i, b_, st_ in d['Z']:
                        if i in keep: self.doc0['Z'][i] = (b_, st_)
                else: self.docs.append(d)
        self.cd = rvtfmt.inflate_stream(self.o.openstream('Global/ContentDocuments').read())[1]
        self.formats_raw = self.o.openstream('Formats/Latest').read()
        self.id_doc = {}
        for k, d in enumerate(self.docs):
            if k == 0: continue
            for i, b in d['H']: self.id_doc.setdefault(i, k)
        lat = rvtfmt.inflate_stream(self.o.openstream('Global/Latest').read())[1]
        self.tag_adoc = struct.unpack_from('<H', lat, 0)[0]
        self.latest_tree = enc.decode_tree(self.sch, self.W, lat, 2, self.tag_adoc)[0]
        self.max_id = max(i for i in self.ids if i < (1 << (8 * self.W - 1)) and i < (1 << 40))
        self.kn_proj = next((i for i, r in self.byid.items() if r['class'] == 'KeynoteTable'), None)
        self.ac_proj = next((i for i, r in self.byid.items() if r['class'] == 'AssemblyCodeTable'), None)
        self.guid_pos = {}
        self._project_constants()
        self.standard = self._standard_shared()

    def symbol_names(self, family_id):
        """{normalised name: name} of the project-side FamilySymbols of a family (unique normalised names only)"""
        if not hasattr(self, '_symnames'):
            self._symnames = {}
            for i, r in self.byid.items():
                if r['class'] != 'FamilySymbol': continue
                si = r['fields'].get('m_symbolInfo'); nm = si.get('obj', {}).get('m_name') if isinstance(si, dict) else None
                if nm: self._symnames.setdefault(int(r['fields'].get('m_familyId', -1)), []).append(nm)
        names = self._symnames.get(int(family_id), []); out = {}; bad = set()
        for n in names:
            k = _norm_type(n)
            if k in out and out[k] != n: bad.add(k)
            out[k] = n
        return {k: v for k, v in out.items() if k not in bad}

    def _project_constants(self):
        o = self.o; g = lambda n: rvtfmt.inflate_stream(o.openstream(n).read())[1]
        SS.TAGS.update({'History': g('Global/History')[:2], 'DIT': g('Global/DocumentIncrementTable')[:2], 'PT': g('Global/PartitionTable')[:2]})
        cd = g('Global/ContentDocuments')
        SS.TAGS['CD'] = cd[:2] if len(cd) < 20 else cd[-14:-12]        # the empty marker of a family document is the last 14 bytes of the project's (a project ends with an empty marker too)
        et = g('Global/ElemTable'); ET.TAG = et[:2]
        alloc = struct.unpack_from('<Q', et, len(et) - 12)[0] if self.W == 8 else struct.unpack_from('<I', et, len(et) - 8)[0]
        if alloc < (1 << 40): self.max_id = max(self.max_id, alloc)      # the id allocator state in the ElemTable trailer: Revit creates the new KeynoteTable/AssemblyCodeTable above it
        if self.W == 8: ET.TRAILER_CONST = et[-24 + 8:-24 + 10]
        else: ET.TRAILER4 = et[-12:-8]
        self._partition_markers()
        t = o.openstream('BasicFileInfo').read().decode('utf-16le', 'ignore') + o.openstream('BasicFileInfo').read()[1:].decode('utf-16le', 'ignore')
        m = re.search(r'Format: (\d+)', t) or re.search(r'Autodesk Revit (20\d\d)', t); self.fmt = m.group(1) if m else '2024'      # BasicFileInfo of 2016-2018 files has no 'Format:' line
        m = re.search(r'Build: (\S+\(x64\))', t); self.build = m.group(1) if m else SS.BUILD
        self.contents_guid, self.contents_stream = SS.CONTENTS_BY_FORMAT.get(self.fmt, (None, None))

    def _partition_markers(self):
        import rvtw
        pn = sorted((y for y in ['/'.join(e) for e in self.o.listdir(streams=True)] if y.startswith('Partitions/')), key=lambda s_: int(s_.split('/')[1]))[0]
        pay = rvtw.Stream(self.o.openstream(pn).read()).payload
        PT.K['version'] = struct.unpack_from('<Q', pay, 0)[0]; PT.K['hdrtag'] = pay[8:10]; PT.K['m1'] = pay[18:20]
        t = pay.rfind('Data generated by Autodesk'.encode('utf-16le'))
        if t > 0:
            PT.K['blobm'] = pay[t - 4 - 4 - 64 - 2:t - 4 - 4 - 64]
            k = pay.rfind(PT.K['m1'] + b'\0' * 16, 0, t)
            if k >= 6: PT.K['m0'] = pay[k - 6:k - 4]
        else:      # 2016/2017 partitions have no blob and text block: the last member frame still carries the marker
            k = pay.rfind(PT.K['m1'] + b'\0' * 16)
            if k >= 6: PT.K['m0'] = pay[k - 6:k - 4]
        PT.K['cdtag'] = SS.TAGS.get('CD', PT.K['cdtag'])

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

    def close(self, seed, allowed=None):
        allowed = allowed or TARGET
        shared = set(seed); frontier = set(seed)
        while frontier:
            nxt = set()
            for i in frontier:
                r = self.byid.get(i)
                if r is None: continue
                out = set(); _eids(r['fields'], out)
                for e in out:
                    q = self.byid.get(e)
                    if q is not None and q['class'] in allowed and e not in shared: nxt.add(e)
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

    def dec_loose(self, body):
        """decode for reference scanning: a record with an undecodable Extensible Storage tail (DataStorage) yields the decoded part"""
        try: return self.dec(body)
        except AssertionError:
            tag = self.tag_of(body); return tag, enc.decode_tree(self.sch, self.W, body, 2, tag, defined=(1, 2))[0]

    def edit(self, body, fn):
        tag, t = self.dec(body); fn(t); return self.encode(tag, t)

    def tag_of(self, body):
        return struct.unpack_from('<H', body, 0)[0]

    def class_of(self, body):
        return self.sch.name(self.tag_of(body))

    # --- build
    def build(self, fam_rec, out_path=None, when=None, own_only_report=False):
        pd = self.pd; f = fam_rec['fields']
        k = pd.family_doc_index(fam_rec); assert k, 'family has no embedded document'; kdoc = k
        doc = pd.docs[k]
        oH = {i: b for i, b in doc['H'][:-1]}; oR = {i: (b, s) for i, b, s in doc['R'][:-1]}; oZ = {i: (b, s) for i, b, s in doc['Z'][:-1]}
        own = set(oH)
        if self.W == 4 and os.environ.get('RVTX_DROPOBS', '1') != '0':      # Revit 2024 saves no LynxTracker (obsolete class of the older formats)
            self.dropped = {i for i, (b, s_) in oR.items() if len(b) > 2 and self.class_of(b) in self.OBSOLETE}; own -= self.dropped
        fid = next(i for i, (b, s) in oR.items() if self.class_of(b) == 'Family')
        # shared set: standard + dependencies of the family's own records
        deps = set()
        nest_recs = [] if os.environ.get('RVTX_NESTDEPS', '0') == '0' else [(kn_, b) for kn_, _g in self.nested_docs(kdoc) for i, b, *_ in pd.docs[kn_]['R'][:-1]]     # nested documents reference materials / shared parameters of the parent (Revit keeps them; dangling ones make the family 'corrupt' on open)
        nest_own = set(i for kn_, _g in self.nested_docs(kdoc) for i, _b in pd.docs[kn_]['H'] if i != NEG)
        nest_set = set(kn_ for kn_, _g in self.nested_docs(kdoc)) if os.environ.get('RVTX_NESTDEPS', '0') != '0' else set()
        nest_fam = [{k_: v for k_, v in r['fields'].items() if k_ != 'm_oFamDoc'} for r in pd.byid.values() if r['class'] == 'Family' and nest_set and pd.family_doc_index(r) in nest_set]     # the project-level Family element of each nested family holds its shared-parameter references
        for fl in [self.dec_loose(b)[1] for i, (b, s) in oR.items()] + [self.dec_loose(b)[1] for _kn, b in nest_recs] + nest_fam + ([f] if os.environ.get('RVTX_FAMDEPS', '0') != '0' else []):      # the family's own project-level Family element (m_oFamDoc id map included) references its shared parameters (ParamElemExternal) and materials; missing ones make a nesting family 'corrupt' in Revit
            out = set(); _eids(fl, out)
            for e in out:
                q = pd.byid.get(e)
                if q is not None and q['class'] in TARGET and e not in pd.standard and e not in own and e not in nest_own: deps.add(e)
        extra = set()
        if os.environ.get('RVTX_EXTRA', '1') != '0':
            IMG = {'ImageSymbol', 'ImageHolder'}
            for k, fl in enumerate([self.dec_loose(b)[1] for i, (b, s) in oR.items()] + [{k_: v for k_, v in f.items() if k_ != 'm_oFamDoc'}]):
                out = set(); _eids(fl, out)
                for e in out:
                    q = pd.byid.get(e)
                    if q is not None and q['class'] in EXTRA and e not in pd.standard and e not in own and (k < len(oR) or q['class'] in IMG): extra.add(e)
        shared = set(pd.standard) | pd.close(deps | extra, TARGET | EXTRA if extra else None)
        if os.environ.get('RVTX_DBG_DEPS'): print('DEPS', len(oR), 'nestrecs', len(nest_recs), 'deps', len(deps), 'shared', len(shared), 'has', {w: (w in deps, w in shared, w in own, w in nest_own) for w in (486487, 77923, 754284, 152314)}, flush=True)
        nest_ids = [i for kn_, _ in self.nested_docs(kdoc) for i, _b in pd.docs[kn_]['H'] if i != NEG]
        mx = max([pd.max_id] + nest_ids)      # Revit allocates the new KeynoteTable/AssemblyCodeTable ids above the nested documents' ids too
        kn, ac = mx + 1, mx + 2
        if self.nested_docs(kdoc) and pd.kn_proj is not None and os.environ.get('RVTX_KEEPKN', '1') != '0': kn, ac = pd.kn_proj, mx + 1      # Revit keeps the project's KeynoteTable id when nested families exist (their records reference it), the AssemblyCodeTable is new
        fam_guid = f['m_famDocGUID']['m_guid']
        g, blob = pd.segment(f['m_oFamDoc']['obj']['m_contentDocGUID']['m_guid'])
        # ---- items
        H, R, Z = {}, {}, {}
        for i in own: H[i] = oH[i]; R[i] = oR[i]; Z[i] = oZ.get(i)
        if use_empty_z(self.W):      # the 138-byte empty cache is the 8-byte-id layout; in 4-byte years it is opt-in (default keeps the project Z): writing it made M_Boundary Condition-Fixed (34 VarSketch) unopenable, oracle 2026-10-24     # Revit's saved family carries an empty guess cache (138-byte Z) for VarSketch elements whose project Z holds data
            for i in own:
                if Z[i] is not None and len(Z[i][0]) > 138 and len(oR[i][0]) > 2 and self.sch.name(struct.unpack_from('<H', oR[i][0], 0)[0]) == 'VarSketch' and self.sketch_cache_emptied(oH[i], oR[i][0]):
                    zb = empty_varsketch_z(i); Z[i] = (zb, zlib.adler32(zb) & 0xFFFFFFFF)
        def fix_h(b):
            def fn(t):
                t['m_familyId'] = EID(fid)
                t['m_parents']['obj']['m_deletion'].append(EID(fid))
                t['m_parents']['obj']['m_deletion'].sort(key=lambda x: int(x) - (1 << 64) if int(x) >= 1 << 63 else int(x))     # Revit keeps every deletion list sorted (signed)
                t['m_abFlags4Bytes'] = t['m_abFlags4Bytes'] & ~0x10
                t['m_regenHistory']['m_historyMap'] = []
            return self.edit(b, fn)
        def fix_r(b):
            def fn(t):
                t['m_famId'] = EID(fid)
                if 'm_bindingIds' in t and t['m_bindingIds']: t['m_bindingIds'] = []     # shared-parameter records: the project-side parameter bindings do not exist in the family (Revit's EditFamily empties them)
            try: return self.edit(b, fn)
            except AssertionError:      # records with an Extensible Storage tail (DataStorage) are not fully decodable: patch m_famId in place
                tag = self.tag_of(b); v, p, c = enc.decode_tree(self.sch, self.W, b, 2, tag, defined=(1, 2))
                old = (int(v['m_famId']) & ((1 << (8 * self.W)) - 1)).to_bytes(self.W, 'little'); k = b.find(old, 2, 200)
                if k < 0 or b.find(old, k + 1, 200) >= 0: raise
                return b[:k] + int(fid).to_bytes(self.W, 'little') + b[k + self.W:]
        for i in shared:
            H[i] = fix_h(pd.doc0['H'][i]); R[i] = (fix_r(pd.doc0['R'][i][0]), None); Z[i] = pd.doc0['Z'].get(i)
        for new, old in ((kn, pd.kn_proj), (ac, pd.ac_proj)):
            def hh(t, new=new, old=old):
                dl = t['m_parents']['obj']['m_deletion']
                t['m_parents']['obj']['m_deletion'] = [EID(new) if int(x) == old else x for x in dl]
            H[new] = self.edit(fix_h(self.edit(pd.doc0['H'][old], hh)), lambda t: t['m_parents']['obj']['m_deletion'].reverse())
            def rr(t, new=new):
                t['m_id'] = EID(new); t['m_famId'] = EID(fid); t['m_lastReadSucceeded'] = 0
                t['m_oKeyBasedTreeEntries'] = {'null': 0}
                for cell in t['m_cellList']['obj']['m_cells']:
                    o = cell.get('obj') or {}
                    if 'm_externalResourceReferences' in o:
                        o['m_externalResourceReferences'] = []
                        for e in o.get('m_externalResourceReferencesExpanded', []):
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
            if not t['m_pFamilyTypes']['obj']['m_pairs'] and f.get('m_pFamilyTypes') and f['m_pFamilyTypes'].get('obj', {}).get('m_pairs'):
                # the family document's own Family record carries no types (office projects): Revit's EditFamily fills them from the project-side Family record
                t['m_pFamilyTypes'] = _null_exprs(copy.deepcopy(f['m_pFamilyTypes']))
            pr = t['m_pFamilyTypes']['obj']['m_pairs']
            for pair in pr:      # Revit's EditFamily lists the project-side symbol names ("450x450mm"), the Family record keeps the names at load time ("450 x 450mm")
                nm = pd.symbol_names(fam_rec['id']).get(_norm_type(pair['name']))
                if nm: pair['name'] = nm
            if len(pr) == 1 and pr[0]['name'] == f.get('m_name'): pr[0]['name'] = ' '
            elif len(pr) > 1 and pr[0]['name'] == ' ': del pr[0]; ft = t['m_pFamilyTypes']['obj']; ft['m_idx'] = max(0, int(ft['m_idx']) - 1)       # leading unnamed scratch type (SCN_HAS): Revit's EditFamily drops it
        R[fid] = (self.edit(R[fid][0], fam_r), None)
        def fam_h(t):
            d = t['m_parents']['obj']['m_deletion']
            t['m_parents']['obj']['m_deletion'] = [EID(e) for e in sorted({int(x) for x in d} | set(shared_sorted), key=lambda v: v - (1 << 64) if v >> 63 else v)]   # signed order: negative ids first (Revit)
        H[fid] = self.edit(H[fid], fam_h)
        self.fam_rec = fam_rec; self.fid = fid; self.kn = kn; self.ac = ac; self.shared = shared; self.own = own; self.all_ids = all_ids; self.H, self.R, self.Z = H, R, Z; self.blob = blob; self.k = kdoc
        return self

    # ---- assemble streams
    def doc_items(self):
        NEGW = (1 << (8 * self.W)) - 1
        ids = self.all_ids
        Hl = [(i, self.H[i]) for i in ids] + [(NEGW, b'')]
        Rl = [(i, self.R[i][0], 0) for i in ids] + [(NEGW, b'', 1)]
        Zl = [(i, self.Z[i][0], 0) for i in ids if self.Z.get(i)] + [(NEGW, b'', 1)]
        return {'H': Hl, 'R': Rl, 'Z': Zl}

    def guid_map(self):
        """nested content document GUIDs -> new GUIDs sorted in document (depth-first) order: Revit writes the ContentDocuments segments in GUID order and pairs them with the partition documents by position, and it regenerates the GUIDs of the nested families when it saves a family; with the project's GUIDs the two orders differ as soon as a family is nested two levels deep ('Family X is corrupt and needs to be reloaded')"""
        if getattr(self, '_gmap', None) is not None: return self._gmap
        nested = self.nested_docs(self.k); m = {}
        if nested and os.environ.get('RVTX_NEWGUID', '1') != '0':
            new = sorted(uuid.uuid5(uuid.NAMESPACE_OID, g_ + str(n)).bytes.hex() for n, (_, g_) in enumerate(nested))
            m = {g_: new[n] for n, (_, g_) in enumerate(nested)}
        self._gmap = m; return m

    def remap_fam(self, body):
        m = self.guid_map()
        if not m or self.class_of(body) != 'Family': return body
        tree = self.dec_loose(body)[1]; fd = tree.get('m_oFamDoc')
        if not (isinstance(fd, dict) and 'obj' in fd) or fd['obj']['m_contentDocGUID']['m_guid'] not in m: return body
        def fn(t): t['m_oFamDoc']['obj']['m_contentDocGUID']['m_guid'] = m[t['m_oFamDoc']['obj']['m_contentDocGUID']['m_guid']]
        return self.edit(body, fn)

    OBSOLETE = ('LynxTracker',)      # classes Revit 2024 discards when it upgrades an older file; inside a nested document they make it 'corrupt' ("can't load top object ... runtime class LynxTracker")

    def drop_obsolete(self, d):
        if self.W != 4 or os.environ.get('RVTX_DROPOBS', '1') == '0': return d
        gone = {i for i, b, *_ in d['R'] if len(b) > 2 and self.class_of(b) in self.OBSOLETE}
        if not gone: return d
        return {'H': [x for x in d['H'] if x[0] not in gone], 'R': [x for x in d['R'] if x[0] not in gone], 'Z': [x for x in d['Z'] if x[0] not in gone]}

    def partition_stream(self):
        main = self.doc_items(); m = self.guid_map()
        if m: main['R'] = [(i, self.remap_fam(b) if len(b) > 2 else b, z) for i, b, z in main['R']]
        docs = [main]
        for kn, _ in self.nested_docs(self.k):
            d = self.pd.docs[kn]
            d = self.drop_obsolete(d)
            if m: d = {'H': d['H'], 'Z': d['Z'], 'R': [(i, self.remap_fam(b), *rest) if len(b) > 2 else (i, b, *rest) for i, b, *rest in d['R']]}
            docs.append(d)
        if os.environ.get('RVTX_DROPCLS'):      # bisect aid: drop records of these classes from every document
            dc = set(os.environ['RVTX_DROPCLS'].split(',')); docs = [{k: [x for x in d[k] if len(x[1]) < 3 or self.class_of(x[1]) not in dc] for k in 'HRZ'} for d in docs]
        dg = None
        if os.environ.get('RVTX_DOCBLK', '1') != '0' and len(docs) > 1:      # old formats: Revit writes a tail block + next document header between documents
            dg = {i + 1: (len(docs[i + 1]['R']) - 1, bytes.fromhex(m.get(g_, g_))) for i, (_, g_) in enumerate(self.nested_docs(self.k))}
        payload = PT.build_payload(docs, self.W, doc_guids=dg, nf_seq=(400, 4) if str(self.pd.fmt) in ('2016', '2017') else None, hs_adj=-4 if str(self.pd.fmt) in ('2016', '2017') else 0, plain_tail=str(self.pd.fmt) in ('2016', '2017'))
        return PT.page_stream(payload)

    def global_stream(self, name, raw):
        co = zlib.compressobj(6, zlib.DEFLATED, -15); z = co.compress(raw) + co.flush()
        gz = PT.GZH + z + struct.pack('<II', zlib.crc32(raw) & 0xFFFFFFFF, len(raw))
        return PT.page_stream(struct.pack('<Q', SS.PREFIX[name]) + gz)

    def sketch_cache_emptied(self, hb, rb):
        """Revit empties the VarSketch Z cache when element flag bit 24 is clear and m_allowResetLineEndConstr is set (0 errors on 459 sketches of Snowdon 2024 vs Revit's own rfa)"""
        dec = lambda x: enc.decode_tree(self.sch, self.W, x, 2, struct.unpack_from('<H', x, 0)[0], defined=(1, 2))[0]
        return not (int(dec(hb)['m_abFlags4Bytes']) >> 24) & 1 and int(dec(rb)['m_allowResetLineEndConstr']) == 1

    def nested_depth(self, k):
        """nesting depth of the families inside document k: 0 = none, 1 = nests families that nest nothing, ..."""
        nd = self.nested_docs(k)
        return 0 if not nd else 1 + max(self.nested_depth(kn) for kn, _g in nd)

    def nested_docs(self, k, seen=None):
        """[(project doc index, content GUID hex)] of the families nested in document k (depth first): Family records inside the document that carry their own m_oFamDoc"""
        pd = self.pd; seen = seen if seen is not None else {k}; out = []
        for i, b, *_ in pd.docs[k]['R'][:-1]:
            if self.class_of(b) != 'Family': continue
            fd = self.dec_loose(b)[1].get('m_oFamDoc')
            if not (isinstance(fd, dict) and 'obj' in fd): continue
            cnt = collections.Counter(pd.id_doc.get(int(x['second'].get('m_id') or x['second'].get('m_id64'))) for x in fd['obj']['m_big2SmallMap2'])
            cnt.pop(None, None); cnt.pop(k, None)
            if not cnt: continue
            kn = cnt.most_common(1)[0][0]
            if kn in seen: continue
            seen.add(kn); out.append((kn, fd['obj']['m_contentDocGUID']['m_guid']))
            if os.environ.get('RVTX_DBG_NEST'): print('NEST parent doc', k, 'family rec', i, 'child doc', kn, 'guid', fd['obj']['m_contentDocGUID']['m_guid'], 'map', dict(cnt), flush=True)
            out += self.nested_docs(kn, seen)
        return out

    def nested_names(self, k):
        """names of the Family records inside document k that carry their own embedded document (direct children)"""
        out = []
        for i, b, *_ in self.pd.docs[k]['R'][:-1]:
            if self.class_of(b) != 'Family': continue
            t = self.dec_loose(b)[1]; fd = t.get('m_oFamDoc')
            if isinstance(fd, dict) and 'obj' in fd and t.get('m_name'): out.append(t['m_name'])
        return out

    def shared_owners(self):
        """ElemTable owner of shared rows that Revit does not attribute to the family: a GStyleElem belongs to its CategoryElem and an ImageHolder to its ImageSymbol when those are in the document"""
        ids = set(self.all_ids); out = {}
        for i in self.shared:
            r = self.pd.byid.get(i)
            if r is None: continue
            f = r['fields']
            if r['class'] == 'GStyleElem' and int(f.get('m_categoryId', -1)) in ids: out[i] = int(f['m_categoryId'])
            elif r['class'] == 'ImageHolder' and int(f.get('m_idImageSymbol', -1)) in ids: out[i] = int(f['m_idImageSymbol'])
        return out

    def nested_blob(self, guid, max_id):
        """content document segment of a nested family as Revit writes it into a family file: the project's segment with the history and content table dropped, the element history ids zeroed and the allocation marker raised"""
        pd = self.pd; g, blob = pd.segment(guid); tag = pd.tag_adoc
        t = enc.decode_tree(self.sch, self.W, blob, 2, tag)[0]
        t['m_pHistory'] = {'null': 0}; t['m_oContentTable'] = {'null': 0}
        if self.W == 4 and os.environ.get('RVTX_DROPOBS', '1') != '0':      # element table rows of records dropped from the nested document (obsolete classes)
            kn_ = next((k_ for k_, g_ in self.nested_docs(self.k) if g_ == guid), None)
            if kn_ is not None:
                gone = {i for i, b, *_ in pd.docs[kn_]['R'] if len(b) > 2 and self.class_of(b) in self.OBSOLETE}
                if gone: t['m_elemTable']['obj']['m_elemArr'] = [e for e in t['m_elemTable']['obj']['m_elemArr'] if int(e['m_id']) not in gone]
        for e in t['m_elemTable']['obj']['m_elemArr']:
            h = e.get('m_history')
            if isinstance(h, dict):
                for k_, v in h.items():
                    if isinstance(v, dict) and 'm_id' in v:
                        v['m_id'] = 0xFFFFFFFF if k_ == 'm_lastUserModificationDate' else (int(e['m_id']) if k_ == 'm_originalElementId' and self.W == 4 and os.environ.get('RVTX_ORIG4', '1') != '0' else 0)      # 4-byte formats: Revit's own 2019 nested segment keeps the element id in m_originalElementId
        src = t['m_elemTable']['obj'].get('m_pSource')
        if isinstance(src, dict) and src.get('obj') and 'm_last' in src['obj']:
            if self.W == 4 and os.environ.get('RVTX_LAST4', '1') != '0': src['obj']['m_last']['m_id'] = max_id      # was left at the project's small counter (1294) while the ids are 281886+; Revit's own file holds a value above every id
            else: src['obj']['m_last']['m_id64'] = max_id
        return struct.pack('<H', tag) + enc.Enc(self.sch, self.W).body(tag, t)

    def add_nested_to_latest(self, lt, nested):
        """content records (taken from the project's Latest) and the family document GUID list of the nested families"""
        guids = [g_ for _, g_ in nested]; want = set(guids)
        recs = [copy.deepcopy(e) for e in self.pd.latest_tree['m_oContentTable']['obj']['m_ContentRecSet'] if e['m_ContentKey']['m_guidKey']['m_guid'] in want]
        gm = self.guid_map()
        kn_of = {g_: kn_ for kn_, g_ in nested}; nelem = {id(e): len(self.pd.docs[kn_of[e['m_ContentKey']['m_guidKey']['m_guid']]]['R']) - 1 for e in recs if e['m_ContentKey']['m_guidKey']['m_guid'] in kn_of}
        for e in recs: e['m_ContentKey']['m_guidKey']['m_guid'] = gm.get(e['m_ContentKey']['m_guidKey']['m_guid'], e['m_ContentKey']['m_guidKey']['m_guid'])
        recs.sort(key=lambda e: bytes.fromhex(e['m_ContentKey']['m_guidKey']['m_guid']))      # Revit keeps the content record set sorted by GUID bytes (BV-BNE title block: 4 records, A0 title block: 2)
        c4 = self.W == 4 and os.environ.get('RVTX_CREC4', '1') != '0'      # content record as in a real 2019 nested family: original id ffffffff, modification 1
        for e in recs:      # Revit zeroes the project history ids in the content records it writes into a family
            h = e.get('m_history')
            if isinstance(h, dict):
                for k_, v in h.items():
                    if isinstance(v, dict) and 'm_id' in v: v['m_id'] = 0xFFFFFFFF if k_ == 'm_lastUserModificationDate' or (k_ == 'm_originalElementId' and c4) else (1 if k_ == 'm_lastModificationDate' and c4 else 0)
            eps = e.get('m_EpisodeCounts') or []
            if c4:
                for ep in eps:
                    if isinstance(ep.get('second'), int) and ep['second'] > 0: ep['second'] = nelem[id(e)] if (id(e) in nelem and len(eps) == 1 and os.environ.get('RVTX_EPCOUNT', 'n') == 'n') else ep['second'] - 1      # real 2019-2022 nested files: the child document's element count without its terminator (224 records -> 223)      # Revit's own 2019 file: the element count without the terminator (223 for 223 elements, the project holds 224)
            for n_, ep in enumerate(eps):      # RVTX_EPI (default keep): '0' zero every key (duplicates when several: Revit rejects the file, journal "can't fix the ordering of container m_EpisodeCounts"), 'keep' leave multi-entry keys, 'seq' keys 0,1,2.. in order
                if isinstance(ep.get('first'), dict) and 'm_id' in ep['first']:
                    mode = os.environ.get('RVTX_EPI', 'keep')
                    if len(eps) == 1 or mode == '0': ep['first']['m_id'] = 0
                    elif mode == 'seq': ep['first']['m_id'] = n_
        if 'obj' not in lt['m_oContentTable']:      # the family had no content records of its own (null pointer): instantiate the table from the project's
            tbl = copy.deepcopy(self.pd.latest_tree['m_oContentTable']); tbl['obj']['m_ContentRecSet'] = []; lt['m_oContentTable'] = tbl
        lt['m_oContentTable']['obj']['m_ContentRecSet'] = recs
        sur = {}      # surrogates of the nested Family records of the document -> GUID list of their LoadedFamilyInfo
        for i, b, *_ in self.pd.docs[self.k]['R'][:-1]:
            if self.class_of(b) == 'Family':
                t = self.dec_loose(b)[1]; fd = t.get('m_oFamDoc')
                if isinstance(fd, dict) and 'obj' in fd:
                    sur[int(t['m_surrogateId'])] = self.nested_chain(fd)
        for s_ in lt['m_pAppInfoManager']['obj']['m_appInfoArr']:
            for li in ((s_.get('obj') or {}).get('m_arrLoadedFamilyInfo') or []):
                if int(li['m_surrogateId']) in sur:
                    ch = sur[int(li['m_surrogateId'])]
                    li['m_familyDocGUIDs'] = [{'m_guid': gm.get(g_, g_)} for g_ in reversed(ch if ch and os.environ.get('RVTX_CHAIN', '1') != '0' else guids)]

    def strip_ids(self, v, gone):
        """remove element ids of dropped records from every id list of a decoded tree (Latest)"""
        if isinstance(v, dict):
            for x in v.values(): self.strip_ids(x, gone)
        elif isinstance(v, list):
            v[:] = [x for x in v if not (isinstance(x, EID) and int(getattr(x, 'v', x)) in gone)]
            for x in v: self.strip_ids(x, gone)

    def nested_chain(self, fd):
        """GUIDs a nested Family's LoadedFamilyInfo lists in a family file (Revit, TC_9 Pile with a family nested two levels deep): its own content document, then the documents nested in it (depth first)"""
        pd = self.pd
        cnt = collections.Counter(pd.id_doc.get(int(x['second'].get('m_id') or x['second'].get('m_id64'))) for x in fd['obj']['m_big2SmallMap2'])
        cnt.pop(None, None); cnt.pop(self.k, None)
        if not cnt: return None
        kn = cnt.most_common(1)[0][0]
        return [fd['obj']['m_contentDocGUID']['m_guid']] + [g_ for _kn, g_ in self.nested_docs(kn, {self.k, kn})]

    def streams(self, family_name, category, path, when=None):
        pd = self.pd; when = when or time.time()
        save_guid = str(uuid.uuid4()); doc_guid = str(uuid.uuid4()); part_guid = pd.contents_guid
        if part_guid is None: raise NotImplementedError('no Revit-written Contents stream known for format %s' % pd.fmt)
        n = len(self.all_ids)
        g, blob = pd.segment(self.fam_rec['fields']['m_oFamDoc']['obj']['m_contentDocGUID']['m_guid'])
        tag = pd.tag_adoc
        bt, _, _ = enc.decode_tree(self.sch, self.W, blob, 2, tag)
        lt, notes = LAT.build_tree(self.sch, pd.latest_tree, bt, set(self.all_ids), remap={pd.kn_proj: self.kn, pd.ac_proj: self.ac}, cls_of=lambda i: self.class_of(self.R[i][0]) if i in self.R else (pd.byid[i]['class'] if i in pd.byid else None))
        nested = self.nested_docs(self.k)
        mx_ids = self.kn - 1
        if self.W == 4 and os.environ.get('RVTX_LAST4', '1') != '0': mx_ids = max([i for i in self.all_ids if 0 <= i < (1 << 31)] or [0]) + 1      # nested ADoc m_last: above every id of the family (Revit's own 2020 file: 325626 for ids up to 321437)
        gone = set(getattr(self, 'dropped', ()))
        for kn_, _g in nested: gone |= {i for i, b, *_ in pd.docs[kn_]['R'] if len(b) > 2 and self.class_of(b) in self.OBSOLETE} if self.W == 4 and os.environ.get('RVTX_DROPOBS', '1') != '0' else set()
        if gone: self.strip_ids(lt, gone)
        if nested: self.add_nested_to_latest(lt, nested)
        latest = LAT.encode(self.sch, self.W, tag, lt)
        if self.W == 8:
            rows = ET.cd_rows(pd.cd[g:g + 400000]); et = ET.build(self.all_ids, self.own, rows, self.fid, special_neg=(self.fid, self.kn, self.ac), shared_owner=self.shared_owners())
        else:
            rows = ET.cd_rows4(pd.cd[g:g + 400000]); ids_ = set(self.all_ids); rows = {i_: (v_ if int.from_bytes(v_[:4], 'little') in ids_ or v_[:4] == b'\xff' * 4 else b'\xff' * 4 + v_[4:]) for i_, v_ in rows.items()}      # an owner that is not an element of the document (DimensionStyle with owner 617) would be a missing owner for Revit
            et = ET.build4(self.all_ids, self.own, rows, self.fid, special_neg=(self.fid, self.kn, self.ac))
        st = {}
        st['Formats/Latest'] = pd.formats_raw
        st['Global/Latest'] = self.global_stream('Global/Latest', latest)
        st['Global/ElemTable'] = self.global_stream('Global/ElemTable', et)
        st['Global/History'] = self.global_stream('Global/History', SS.history(doc_guid, save_guid))
        st['Global/DocumentIncrementTable'] = self.global_stream('Global/DocumentIncrementTable', open(os.environ['RVTX_DITFILE'], 'rb').read()) if os.environ.get('RVTX_DITFILE') else self.global_stream('Global/DocumentIncrementTable', DITS.DIT_BY_FORMAT[str(pd.fmt)] if self.W == 4 and str(pd.fmt) in DITS.DIT_BY_FORMAT and os.environ.get('RVTX_OLDDIT', '1') != '0' else SS.document_increment_table(n + (sum(len(self.pd.docs[kn_]['H']) - 1 for kn_, _ in nested) if os.environ.get('RVTX_DITN', '1') != '0' else 0), when))
        st['Global/PartitionTable'] = self.global_stream('Global/PartitionTable', SS.PT_SAMPLES[pd.fmt] if (pd.fmt not in ('2024', '2026') and pd.fmt in SS.PT_SAMPLES and not (nested and self.W == 4 and os.environ.get('RVTX_PT4', '1') != '0')) else SS.partition_table(part_guid))      # real Revit nested 2022 family: a single 'Workset1' entry, not the sample's two named partitions
        st['Global/ContentDocuments'] = self.global_stream('Global/ContentDocuments', SS.content_documents([(self.guid_map().get(g_, g_), self.nested_blob(g_, mx_ids)) for _, g_ in sorted(nested, key=lambda n: bytes.fromhex(self.guid_map().get(n[1], n[1])))]) if nested else SS.content_documents_empty())
        st['Partitions/0'] = self.partition_stream()
        st['BasicFileInfo'] = SS.basic_file_info(path, save_guid, pd.build, pd.fmt)
        st['Contents'] = pd.contents_stream
        st['TransmissionData'] = SS.transmission_data(self.kn, self.ac)
        st['PartAtom'] = SS.part_atom(family_name, category, os.path.basename(path), when, pd.fmt)
        st['RevitPreview4.0'] = SS.preview()
        self.last_trees = (lt, bt)
        return st

    @staticmethod
    def _deflate(raw):
        co = zlib.compressobj(6, zlib.DEFLATED, -15); return co.compress(raw) + co.flush()

    def write(self, out_path, family_name, category):
        st = self.streams(family_name, category, out_path)
        fmt = int(self.pd.fmt) if str(self.pd.fmt).isdigit() else 2024
        part = 'Partitions/%d' % PARTITION_NUMBER[fmt] if fmt in PARTITION_NUMBER else 'Partitions/0'   # Revit 2024 rejects a 2020 file whose partition stream is not named like Revit's (oracle bisect 2026-10-22)
        part = os.environ.get('RVTX_PNAME') or part
        open(out_path, 'wb').write(cfbw.write_rfa(st, part)); return st
