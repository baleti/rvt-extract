"""pstruct2.py FILE : partition/doc structure summary (all partitions)"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import partition as PT
import rvt2text as T, rvt_scan as S
path = sys.argv[1]; o, cls, ids = S.load(path); W = S.id_size(cls)
for pn in sorted((y for y in ['/'.join(e) for e in o.listdir(streams=True)] if y.startswith('Partitions/')), key=lambda s: int(s.split('/')[1])):
    try:
        j = T.joined(o.openstream(pn).read()); docs = PT.parse_joined(j, W)
        print(pn, len(j), 'docs', len(docs), [(len(d['H']), len(d['R']), len(d['Z'])) for d in docs[:4]], flush=True)
    except Exception as e: print(pn, 'ERR', type(e).__name__, str(e)[:80], flush=True)
