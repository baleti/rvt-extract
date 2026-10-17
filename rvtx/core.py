"""Project loading and embedded family document scan.

A project stores, per loaded family, a content document: Global/ContentDocuments holds one segment per family
(GUID = Family.m_oFamDoc.m_contentDocGUID) with the family doc's own table rows; the family's internal elements
(reference planes, forms, sketches, parameters) sit in the project partitions with header [A = family-local id]
[id = project id] and are NOT listed in the project ElemTable."""
import struct, collections, bisect
import numpy as np
from . import RESEARCH  # noqa
import rvt_scan as S, rvt_decode as D, rvt2text as T, rvt_inventory as I, rvtfmt, rvt_xcache as X


def _sid(v):
    if isinstance(v, dict): v = v['m_id'] if 'm_id' in v else v['m_id64']
    return eid(v)


def eid(v):
    return int(getattr(v, 'v', v))


class Project:
    def __init__(self, path, x=None):
        self.path = path
        self.x = x if x is not None else X.get_x(path)
        self.recs = self.x['recs']                       # {(id, class): record}
        self.W = self.x['W']
        self.by_class = collections.defaultdict(list)
        for (i, c), r in self.recs.items():
            self.by_class[c].append(r)

    def families(self):
        return self.by_class['Family']


def _segments(cd, fams):
    pos = []
    for fid, f in fams.items():
        g = cd.find(bytes.fromhex(f['guid']))
        if g >= 0: pos.append((g, fid))
    pos.sort()
    return pos


def scan_family_docs(prj, keep=True):
    """-> ({family_id: {'name','guid','l2p':{local:project},'records':{project_id: record}}}, stats). Heavy: run big files on remote-host."""
    fams = {}
    for r in prj.families():
        f = r['fields']; d = f.get('m_oFamDoc')
        if not d: continue
        o = d['obj']
        fams[r['id']] = {'name': f.get('m_name'), 'guid': o['m_contentDocGUID']['m_guid'],
                         'l2p': {eid(p['first']): _sid(p['second']) for p in o['m_big2SmallMap2']}, 'records': {}}
    o, cls, ids = S.load(prj.path); IDW = S.id_size(cls); dec = D.make_dec(D.Schema(cls), idsize=IDW)
    cd = rvtfmt.inflate_stream(o.openstream('Global/ContentDocuments').read())[1]
    seg = _segments(cd, fams); starts = [s for s, _ in seg]
    seg_of = {}
    for a in range(4):
        n = (len(cd) - a) // 4
        if n <= 0: continue
        arr = np.frombuffer(cd, dtype='<u4', count=n, offset=a)
        for j in np.nonzero((arr > 0) & (arr < 4000000))[0]:
            v = int(arr[j])
            if v in ids or v in seg_of: continue
            si = bisect.bisect_right(starts, int(j) * 4 + a) - 1
            seg_of[v] = seg[si][1] if si >= 0 else None
    etags = I.element_tags(cls)
    idarr = np.array(sorted(seg_of), dtype=np.uint32 if IDW == 4 else np.uint64); IDF = '<I' if IDW == 4 else '<Q'
    st = collections.Counter()
    for pn in sorted(y for y in ['/'.join(e) for e in o.listdir(streams=True)] if y.startswith('Partitions/')):
        chunk = T.joined(o.openstream(pn).read())
        for i in S.header_candidates(chunk, idarr, IDW):
            e = struct.unpack_from(IDF, chunk, i + 4)[0]
            for short in (False, True):
                tag = struct.unpack_from('<H', chunk, i + 12 + IDW - (4 if short else 0))[0]
                if tag not in etags: continue
                try: r, q = dec.record(chunk, i, short)
                except Exception: continue
                if r['fields'].get('m_id') != e: continue
                owner = seg_of[e]
                if owner is None: st['unowned'] += 1; continue
                if e in fams[owner]['records']: st['superseded'] += 1  # later copy of an element wins
                r['A'] = struct.unpack_from('<I', chunk, i)[0]; r['len'] = q - i; r['where'] = (pn, i)
                if not keep: r = {k: r[k] for k in ('id', 'class', 'A')}
                fams[owner]['records'][e] = r; st['ok'] += 1
    return fams, dict(st)
