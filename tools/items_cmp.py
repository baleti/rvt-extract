import sys,pickle,struct,collections; sys.path.insert(0,'~/src/rvt-extract/tools'); sys.path.insert(0,'~/src/rvt-extract'); sys.path.insert(0,'~/rvt-research'); sys.path.insert(0,'~/rvt-research/write-lab')
from pwalk import *
from rvtx import partition as PT
import rvtx
def cmp(mine_pkl, revit_rfa):
    P,j,cls=load(revit_rfa); rf=PT.parse_joined(j)[0]
    m=pickle.load(open(mine_pkl,'rb'))
    H={i:b for i,b in rf['H']}; R={i:(b) for i,b,s in rf['R']}; Z={i:b for i,b,s in rf['Z']}
    NEG=(1<<64)-1
    st=collections.Counter(); bad=collections.defaultdict(list)
    print('ids equal', sorted(i for i in H if i!=NEG)==m['ids'])
    for i in m['ids']:
        if i not in H: st['missing in revit']+=1; continue
        for nm,a,b in (('H',m['H'][i],H[i]),('R',m['R'][i][0],R.get(i)),('Z',(m['Z'].get(i) or (None,))[0],Z.get(i))):
            if a==b: st[nm+' eq']+=1
            else: st[nm+' DIFF']+=1; bad[nm].append(i)
    print(st)
    for k,v in bad.items(): print(k,len(v),v[:12])
    return bad
if __name__=='__main__': cmp(sys.argv[1],sys.argv[2])
