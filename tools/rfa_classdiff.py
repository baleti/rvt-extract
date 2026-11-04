"""rfa_classdiff.py A.rfa B.rfa : per-class record counts of H chain in two small rfas (light, remote-host ok)"""
import sys, os, collections, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
import olefile, rvt2text as T
from rvtx import partition as PT
def recs(p):
    o = olefile.OleFileIO(p); pn = [y for y in ['/'.join(e) for e in o.listdir(streams=True)] if y.startswith('Partitions/')][0]
    j = T.joined(o.openstream(pn).read())
    try: rf = PT.parse_joined(j, int(os.environ.get('W', 8)))[0]
    except Exception:
        if os.environ.get('W'): raise
        rf = PT.parse_joined(j, 4)[0]  # 2020 and older files use 4-byte ids
    return {i: x for i, x, *_ in rf['R'] if i != (1 << 64) - 1}
a, b = recs(sys.argv[1]), recs(sys.argv[2])
tag = lambda x: struct.unpack_from('<H', x, 0)[0] if len(x) > 1 else -1
ca = collections.Counter(tag(x) for x in a.values()); cb = collections.Counter(tag(x) for x in b.values())
print(len(a), len(b), 'ids only A', len(set(a) - set(b)), 'only B', len(set(b) - set(a)))
for t in sorted(set(ca) | set(cb)):
    if ca[t] != cb[t]: print('tag', t, ca[t], cb[t])
import difflib
dif = collections.Counter(tag(a[i]) for i in set(a) & set(b) if a[i] != b[i])
print('byte-differing R records by tag', dict(dif), 'only A tags', collections.Counter(tag(a[i]) for i in set(a)-set(b)), 'only B tags', collections.Counter(tag(b[i]) for i in set(b)-set(a)))
