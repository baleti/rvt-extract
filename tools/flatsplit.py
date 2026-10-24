#!/usr/bin/env python3
"""flatsplit.py DIR : print FLAT or NESTED for each .rfa in DIR (nested = more than one document in the partition stream; 4-byte ids for formats < 2024 use W=4)."""
import sys, os, glob, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, os.path.expanduser('~/rvt-research'))
import olefile, rvt2text as T
from rvtx import partition as PT
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.rfa'))):
    o = olefile.OleFileIO(f)
    p = [s for s in o.listdir() if s[0] == 'Partitions'][0]
    d = o.openstream(p).read(); n = None
    for W in (4, 8):
        try: n = len(PT.parse_joined(T.joined(d), W)); break
        except Exception: pass
    print(os.path.basename(f), 'FLAT' if n == 1 else 'NESTED' if n else 'UNKNOWN', n)
