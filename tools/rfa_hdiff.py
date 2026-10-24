"""rfa_hdiff.py A.rfa B.rfa : H-chain records byte-differing between two small rfas, decode-diffed (light)"""
import sys, os, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')); sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import rvtx, olefile, rvt2text as T, rvt_scan as S, rvt_decode as D
from rvtx import partition as PT, enc
from tdiff import walk_diff
def load(p):
    o = olefile.OleFileIO(p); pn = [y for y in ['/'.join(e) for e in o.listdir(streams=True)] if y.startswith('Partitions/')][0]
    rf = PT.parse_joined(T.joined(o.openstream(pn).read()), 8)[0]
    _, cls, _ = S.load(p); return {r[0]: r[1] for r in rf['H'] if r[0] != (1 << 64) - 1}, D.Schema(cls)
(a, sa), (b, sb) = load(sys.argv[1]), load(sys.argv[2])
dec = lambda sch, x: enc.decode_tree(sch, 8, x, 2, struct.unpack_from('<H', x, 0)[0], defined=(1, 2))[0]
print(len(a), len(b), 'only A', len(set(a) - set(b)), 'only B', len(set(b) - set(a)))
c = collections.Counter(); n = 0
for i in sorted(set(a) & set(b)):
    if a[i] != b[i]:
        out = []; walk_diff(dec(sa, a[i]), dec(sb, b[i]), '', out); k = sa.name(struct.unpack_from('<H', a[i], 0)[0]); c[k] += 1
        if n < int(os.environ.get('N', 12)): n += 1; print(i, k, [str(o)[:200] for o in out[:6]])
print(c)
