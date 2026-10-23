"""latpatch.py OURS.rfa GT.rfa OUT.rfa MODE[,MODE..] : OURS with parts of its Global/Latest tree replaced by GT's (bisect helper)
modes: cat (m_categoryData of appInfo 28), win (appInfo 6 window fields)"""
import sys, os, struct, olefile
sys.path[:0] = [os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'), os.path.dirname(os.path.realpath(__file__)), os.path.expanduser('~/rvt-research')]
from lat_lib import *
from rvtx import cfbw, latest as L
ours, gt, out, modes = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(',')
a = latest_tree(ours); g = latest_tree(gt)
at, gtt = a[0], g[0]
def arr(t, i): return t['m_pAppInfoManager']['obj']['m_appInfoArr'][i]['obj']
if 'cat' in modes: arr(at, 28)['m_categoryData'] = arr(gtt, 28)['m_categoryData']
if 'win' in modes:
    for k in ('m_openWindowStates', 'm_horzRes', 'm_vertRes'): arr(at, 6)[k] = arr(gtt, 6)[k]
raw = L.encode(a[1], a[2], a[3], at)
o = olefile.OleFileIO(ours); st = {'/'.join(e): o.openstream('/'.join(e)).read() for e in o.listdir(streams=True)}
import zlib
from rvtx import smallstreams as SS, partition as PT
co = zlib.compressobj(6, zlib.DEFLATED, -15); z = co.compress(raw) + co.flush()
gz = PT.GZH + z + struct.pack('<II', zlib.crc32(raw) & 0xFFFFFFFF, len(raw))
st['Global/Latest'] = PT.page_stream(struct.pack('<Q', SS.PREFIX['Global/Latest']) + gz)
pn = next(n for n in st if n.startswith('Partitions/'))
os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
open(out, 'wb').write(cfbw.write_rfa(st, pn))
