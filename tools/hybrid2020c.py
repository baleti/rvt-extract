"""hybrid2020c.py OURS.rfa SAMPLE.rfa OUTDIR STREAM[,STREAM...] : our lifted rfa with the named streams taken from the real sample (bisect helper)"""
import sys, os, olefile
sys.path[:0] = [os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')]
from rvtx import cfbw
ours, src, od, names = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(',')
os.makedirs(od, exist_ok=True)
a, b = olefile.OleFileIO(ours), olefile.OleFileIO(src); st = {}
pn = '/'.join(next(e for e in a.listdir(streams=True) if e[0] == 'Partitions'))
for e in a.listdir(streams=True):
    n = '/'.join(e); st[n] = (b if n in names else a).openstream(n).read()
open(os.path.join(od, 'h.rfa'), 'wb').write(cfbw.write_rfa(st, pn))
