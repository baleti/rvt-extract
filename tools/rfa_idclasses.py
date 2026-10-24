"""rfa_idclasses.py LIFTDIR GTDIR : classes of records present only in ours / only in Revit's rfa, summed over families (light)"""
import sys, os, glob, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx, olefile, rvt2text as T, rvt_scan as S, rvt_decode as D
from rvtx import partition as PT
def R(p):
    o = olefile.OleFileIO(p); pn = [y for y in ['/'.join(e) for e in o.listdir(streams=True)] if y.startswith('Partitions/')][0]
    d = PT.parse_joined(T.joined(o.openstream(pn).read()), 8)[0]; _, cls, _ = S.load(p)
    return {i: x for i, x, *_ in d['R'] if i != (1 << 64) - 1}, D.Schema(cls)
mine, gt = collections.Counter(), collections.Counter(); ex = {}
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*', '*.rfa'))):
    g = os.path.join(sys.argv[2], os.path.relpath(f, sys.argv[1]))
    if not os.path.exists(g): continue
    (a, sa), (b, sb) = R(f), R(g)
    for i in set(a) - set(b): c = sa.name(struct.unpack_from('<H', a[i], 0)[0]); mine[c] += 1; ex.setdefault(('m', c), os.path.basename(f))
    for i in set(b) - set(a): c = sb.name(struct.unpack_from('<H', b[i], 0)[0]); gt[c] += 1; ex.setdefault(('g', c), os.path.basename(f))
print('only ours', dict(mine)); print('only Revit', dict(gt))
print(ex)
