"""rfa_variants.py LIFTED.rfa GT.rfa OUTDIR : variants of the lifted rfa with H / R / Z records replaced by Revit's, to find which difference breaks the open (oracle experiment)"""
import sys, os, struct, itertools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx, olefile, rvt2text as T
from rvtx import partition as PT, cfbw
def parts(p):
    o = olefile.OleFileIO(p); st = {'/'.join(e): o.openstream('/'.join(e)).read() for e in o.listdir(streams=True)}
    return st, PT.parse_joined(T.joined(st['Partitions/0']), 8)[0]
A, da = parts(sys.argv[1]); _, db = parts(sys.argv[2]); out = sys.argv[3]; os.makedirs(out, exist_ok=True)
NEG = (1 << 64) - 1
def variant(regs, only=None):
    d = {k: list(v) for k, v in da.items()}
    for k in regs:
        gb = {x[0]: x for x in db[k]}
        d[k] = [gb[x[0]] if x[0] != NEG and x[0] in gb and (only is None or x[0] in only) else x for x in d[k]]
    st = dict(A); st['Partitions/0'] = PT.page_stream(PT.build_payload([d], 8)); return cfbw.write_rfa(st)
name = os.path.splitext(os.path.basename(sys.argv[1]))[0].replace(' ', '_')
ONLY = [set(int(y) for y in x.split(',')) for x in sys.argv[4:]]   # optional: id lists, one H-only variant per list
for n_, ids in enumerate(ONLY): open(os.path.join(out, '%s_Hid%d.rfa' % (name, n_)), 'wb').write(variant(['H'], ids))
for regs in ([] if ONLY else ([], ['Z'], ['H'], ['R'], ['H', 'R', 'Z'])):
    open(os.path.join(out, '%s_%s.rfa' % (name, ''.join(regs) or 'none')), 'wb').write(variant(regs))
