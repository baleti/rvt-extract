"""pexp.py PROJECT IDS.pkl OUT.pkl : parse project partitions into docs; keep doc meta, doc0 items for the wanted ids, and the docs that contain wanted ids (remote-host)"""
import sys, os, pickle, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import partition as PT
import rvt2text as T, rvt_scan as S
path, idsf, out = sys.argv[1:4]
want = set()
for f in idsf.split(','): want |= set(pickle.load(open(f, 'rb')))
o, cls, ids = S.load(path); W = S.id_size(cls)
pn = [y for y in ['/'.join(e) for e in o.listdir(streams=True)] if y.startswith('Partitions/')][0]
j = T.joined(o.openstream(pn).read()); docs = PT.parse_joined(j, W); NEG = (1 << (8 * W)) - 1
meta = []
for i, d in enumerate(docs):
    xs = [x[0] for x in d['H'][:-1]]; meta.append((i, min(xs), max(xs), len(xs)))
doc0 = {}
H0 = {i: b for i, b in docs[0]['H']}; R0 = {i: (b, s) for i, b, s in docs[0]['R']}; Z0 = {i: (b, s) for i, b, s in docs[0]['Z']}
for i in want:
    if i in H0 or i in R0 or i in Z0: doc0[i] = (H0.get(i), R0.get(i), Z0.get(i))
sel = {}
for i, d in enumerate(docs):
    if i == 0: continue
    ids_ = {x[0] for x in d['H']}
    if len(ids_ & want) > 20 or (i, ) and sum(1 for x in ids_ if x in want) > len(ids_) // 2:
        sel[i] = d
pickle.dump({'meta': meta, 'doc0': doc0, 'docs': sel, 'W': W, 'ndocs': len(docs)}, open(out, 'wb'))
print(len(docs), len(doc0), list(sel))
