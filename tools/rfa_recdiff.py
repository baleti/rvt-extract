"""rfa_recdiff.py A.rfa B.rfa TAGNAME : decode-diff byte-differing R records of one class between two small rfas"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')); sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import rvtx, olefile, rvt2text as T, rvt_scan as S, rvt_decode as D
from rvtx import partition as PT, enc
from tdiff import walk_diff
def load(p):
    o = olefile.OleFileIO(p); pn = [y for y in ['/'.join(e) for e in o.listdir(streams=True)] if y.startswith('Partitions/')][0]
    rf = PT.parse_joined(T.joined(o.openstream(pn).read()), 8)[0]
    _, cls, _ = S.load(p); return {i: x for i, x, *_ in rf['R'] if i != (1 << 64) - 1}, D.Schema(cls)
(a, sa), (b, sb) = load(sys.argv[1]), load(sys.argv[2])
dec = lambda sch, x: enc.decode_tree(sch, 8, x, 2, struct.unpack_from('<H', x, 0)[0], defined=(1, 2))[0]
for i in sorted(set(a) & set(b)):
    if a[i] != b[i] and sa.name(struct.unpack_from('<H', a[i], 0)[0]) == sys.argv[3]:
        out = []; walk_diff(dec(sa, a[i]), dec(sb, b[i]), '', out); print(i, len(a[i]), len(b[i]), [str(o)[:300] for o in out[:12]])
