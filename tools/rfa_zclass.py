import sys,os,struct,glob,collections
sys.path.insert(0,os.path.join(os.path.dirname(os.path.realpath(__file__)),'..')); import rvtx, olefile, rvt2text as T, rvt_scan as S, rvt_decode as D
from rvtx import partition as PT
def reg(p):
    o=olefile.OleFileIO(p); rf=PT.parse_joined(T.joined(o.openstream('Partitions/0').read()),8)[0]; _,cls,_=S.load(p); return rf,D.Schema(cls)
emp=collections.Counter(); same=collections.Counter(); keep=collections.Counter()
for p in sorted(glob.glob('out/lift43t/*/*.rfa'))[::4]:
    g=os.path.expanduser('~/rvt-research/write-lab/gt_fam/2024_43/')+os.path.relpath(p,'out/lift43t')
    A,sa=reg(p); B,_=reg(g); a={r[0]:r[1] for r in A['Z']}; b={r[0]:r[1] for r in B['Z']}; R={r[0]:r[1] for r in A['R']}
    for i in a:
        if i not in b or i not in R or len(a[i])<=2: continue
        n=sa.name(struct.unpack_from('<H',R[i],0)[0])
        if a[i]==b[i]: same[(n,len(a[i])>138)]+=1
        elif len(b[i])==138: emp[n]+=1
        else: keep[n]+=1
print('emptied by Revit',emp); print('same',same); print('differ other',keep)
