"""rfa_zdiff.py OURS_DIR GT_DIR : Z-region byte-differing records over all families (light)"""
import sys,os,struct,glob,collections
sys.path.insert(0,os.path.join(os.path.dirname(os.path.realpath(__file__)),'..')); import rvtx, olefile, rvt2text as T
from rvtx import partition as PT
def reg(p):
    o=olefile.OleFileIO(p); return PT.parse_joined(T.joined(o.openstream('Partitions/0').read()),8)[0]
c=collections.Counter(); ex=[]
for p in sorted(glob.glob(sys.argv[1]+'/*/*.rfa')):
    g=os.path.join(sys.argv[2],os.path.relpath(p,sys.argv[1]))
    if not os.path.exists(g): continue
    A=reg(p); B=reg(g); a={r[0]:r[1] for r in A['Z']}; b={r[0]:r[1] for r in B['Z']}
    for i in a:
        if i in b and a[i]!=b[i]: c[(len(a[i])>len(b[i]), len(b[i]))]+=1; ex.append((os.path.relpath(p,sys.argv[1]),i,len(a[i]),len(b[i])))
print(c); print(ex[:30])
