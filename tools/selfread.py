"""selfread.py DIR... : re-read every .rfa with our own reader (offline sanity, not a Revit open): OLE magic, required streams, Project loads, >0 records. Prints failures and an aggregate."""
import sys, os, glob, olefile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
from rvtx import core
NEED = [['BasicFileInfo'], ['Global', 'ElemTable'], ['Global', 'Latest'], ['Global', 'PartitionTable'], ['Contents']]
ok = bad = 0
for d in sys.argv[1:]:
    for f in sorted(glob.glob(os.path.join(d, '**', '*.rfa'), recursive=True)):
        try:
            o = olefile.OleFileIO(f); have = o.listdir()
            miss = [n for n in NEED if n not in have]
            if miss: raise ValueError('missing %s' % miss)
            n = len(core.Project(f).recs)
            if n < 1: raise ValueError('no records')
            ok += 1
        except Exception as e:
            bad += 1; print('FAIL', os.path.basename(f)[:12], type(e).__name__, str(e)[:80])
print('ok', ok, 'fail', bad)
