"""pstruct.py PROJECT : structure of the project partitions (docs, chains, id ranges)"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import partition as PT
import olefile, rvt2text as T, rvt_scan as S
path = sys.argv[1]; o, cls, ids = S.load(path); W = S.id_size(cls)
for pn in sorted(y for y in ['/'.join(e) for e in o.listdir(streams=True)] if y.startswith('Partitions/')):
    j = T.joined(o.openstream(pn).read()); print(pn, len(j))
    docs = PT.parse_joined(j, W)
    for i, d in enumerate(docs):
        def rng(L): 
            xs = [x[0] for x in L[:-1]]; return (min(xs), max(xs), xs == sorted(xs)) if xs else None
        print(' doc', i, 'H', len(d['H']), rng(d['H']), 'R', len(d['R']), rng(d['R']), 'Z', len(d['Z']), rng(d['Z']))
