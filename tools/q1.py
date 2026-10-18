import sys, os, pickle, collections, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import core
import rvt_decode as D
prj = core.Project(sys.argv[1]); recs = prj.recs; byid = {i: r for (i, c), r in recs.items()}
want = {23, 43333, 260568, 260569, 260570, 529814, 529815, 529816}
for i in sorted(want):
    r = byid.get(i)
    if not r: print(i, 'absent'); continue
    f = r['fields']; m = f.get('m_pMaterial'); m = m.get('obj', m) if isinstance(m, dict) else None
    a = f.get('m_pAppearanceAsset'); a = a.get('obj', a) if isinstance(a, dict) else None
    print(i, r['class'], (m or {}).get('m_name'), (a or {}).get('m_Name'))
# referrers
refs = collections.defaultdict(list)
def walk(o, key, rid, rc):
    if isinstance(o, bool): return
    if isinstance(o, int) or hasattr(o, 'v'):
        v = int(getattr(o, 'v', o))
        if v in want: refs[v].append((rc, rid, key))
    elif isinstance(o, dict):
        for k, x in o.items(): walk(x, k, rid, rc)
    elif isinstance(o, list):
        for x in o: walk(x, key, rid, rc)
for (i, c), r in recs.items():
    if i in want: continue
    walk(r['fields'], '', i, c)
for v in sorted(want):
    rr = refs[v]; print(v, len(rr), collections.Counter((a, k) for a, b, k in rr).most_common(6))
