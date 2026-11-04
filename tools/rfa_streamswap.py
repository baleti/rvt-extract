"""rfa_streamswap.py LIFTED.rfa GT.rfa OUTDIR : variants of the lifted rfa with whole streams replaced by Revit's (P=Partitions/0, S=Global/ElemTable+PartitionTable+Latest+Formats/Latest, M=BasicFileInfo+PartAtom+RevitPreview+TransmissionData, ALL)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import olefile
from rvtx import cfbw
def st(p):
    o = olefile.OleFileIO(p); return {'/'.join(e): o.openstream('/'.join(e)).read() for e in o.listdir(streams=True)}
A, B = st(sys.argv[1]), st(sys.argv[2]); out = sys.argv[3]; os.makedirs(out, exist_ok=True)
name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
G = {'P': ['Partitions/0'], 'S': ['Global/ElemTable', 'Global/PartitionTable', 'Global/Latest', 'Formats/Latest'], 'M': ['BasicFileInfo', 'PartAtom', 'RevitPreview4.0', 'TransmissionData']}
G['ALL'] = [k for k in A if k in B and k != 'Contents']
for g, ks in G.items():
    d = dict(A)
    for k in ks:
        if k in B: d[k] = B[k]
    open(os.path.join(out, '%s_%s.rfa' % (name, g)), 'wb').write(cfbw.write_rfa(d))
