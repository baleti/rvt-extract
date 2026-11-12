"""docdiff.py A.rfa B.rfa : per document (main + nested) and chain: record counts, id set differences with classes, byte-differing common records"""
import sys, os, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')); sys.path.insert(0, os.path.expanduser('~/rvt-research'))
import rvtx, olefile, rvt2text as T
from rvtx import partition as PT
def load(p):
    o = olefile.OleFileIO(p); pn = [y for y in ['/'.join(e) for e in o.listdir(streams=True)] if y.startswith('Partitions/')][0]
    j = T.joined(o.openstream(pn).read())
    if os.environ.get('W'): return PT.parse_joined(j, int(os.environ['W']))
    try: return PT.parse_joined(j, 8)
    except Exception: return PT.parse_joined(j, 4)  # 2020 and older files use 4-byte ids
A, B = load(sys.argv[1]), load(sys.argv[2])
print('docs', len(A), len(B))
for di in range(max(len(A), len(B))):
    if di >= len(A) or di >= len(B): print('doc', di, 'only in', 'A' if di < len(A) else 'B'); continue
    for ch in 'HRZ':
        a = {x[0]: x[1] for x in A[di][ch] if x[0] != (1 << 64) - 1}; b = {x[0]: x[1] for x in B[di][ch] if x[0] != (1 << 64) - 1}
        onlya, onlyb = sorted(set(a) - set(b)), sorted(set(b) - set(a))
        diff = [i for i in set(a) & set(b) if a[i] != b[i]]
        tag = lambda x: struct.unpack_from('<H', x, 0)[0] if len(x) >= 2 else -1
        print('doc', di, ch, 'A', len(a), 'B', len(b), 'onlyA', len(onlya), collections.Counter(tag(a[i]) for i in onlya).most_common(5), 'onlyB', len(onlyb), collections.Counter(tag(b[i]) for i in onlyb).most_common(5), 'bytediff', len(diff), collections.Counter(tag(a[i]) for i in diff).most_common(5))
