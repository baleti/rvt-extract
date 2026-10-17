"""rawrecs(path): {(id,class): [(A, raw bytes, partition, offset)]} for every decodable record of a (small) file"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
import numpy as np
import rvt_scan as S, rvt_decode as D, rvt2text as T, rvt_inventory as I
def rawrecs(path, only_ids=None):
    o, cls, ids = S.load(path); IDW = S.id_size(cls); dec = D.make_dec(D.Schema(cls), idsize=IDW); etags = I.element_tags(cls)
    use = set(only_ids) if only_ids else ids
    idarr = np.array(sorted(use), dtype=np.uint32 if IDW == 4 else np.uint64); IDF = '<I' if IDW == 4 else '<Q'
    out = {}
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
                out.setdefault((e, r['class']), []).append((struct.unpack_from('<I', chunk, i)[0], bytes(chunk[i:q]), pn, i, r))
    return out
