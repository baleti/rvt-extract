"""rfa_setcmp.py LIFTDIR GTDIR : per-file record-id set and byte comparison against Revit's own rfas (light)"""
import sys, os, glob, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx, olefile, rvt2text as T
from rvtx import partition as PT
def R(p):
    o = olefile.OleFileIO(p); pn = [y for y in ['/'.join(e) for e in o.listdir(streams=True)] if y.startswith('Partitions/')][0]
    d = PT.parse_joined(T.joined(o.openstream(pn).read()), 8)[0]; return {i: x for i, x, *_ in d['R'] if i != (1 << 64) - 1}
tot = collections.Counter()
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*', '*.rfa'))):
    rel = os.path.relpath(f, sys.argv[1]); g = os.path.join(sys.argv[2], rel)
    if not os.path.exists(g): tot['nogt'] += 1; continue
    try: a, b = R(f), R(g)
    except Exception as e: tot['err'] += 1; print(rel, 'ERR', e); continue
    ids = 'same' if set(a) == set(b) else 'ids-differ'; nd = sum(1 for i in set(a) & set(b) if a[i] != b[i])
    tot[ids] += 1; tot['bytes-equal' if nd == 0 else 'r-diff<=3' if nd <= 3 else 'r-diff>3'] += 1
    if ids != 'same' or nd > 3: print(rel, ids, len(set(a) ^ set(b)), nd)
print(dict(tot))
