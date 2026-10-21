import sys,struct,collections
sys.path.insert(0,'.')
import rvtx, olefile, rvt2text as T
from rvtx import partition as PT
def parts(p):
    o=olefile.OleFileIO(p); return PT.parse_joined(T.joined(o.openstream('Partitions/0').read()),8)[0]
NEG=(1<<64)-1
S=[];K=[]
for l in list(open('private/cmp_list.tsv'))[::3]:
    f,s,g=l.rstrip('\n').split('\t'); a=parts('private/rfa/corp-2024-43/'+f); b=parts(g)
    ra={x[0]:x[1] for x in a['R']}; ha={x[0]:x[1] for x in a['H']}
    za={x[0]:x[1] for x in a['Z'] if x[0]!=NEG}; zb={x[0]:x[1] for x in b['Z'] if x[0]!=NEG}
    for i in za:
        if i in zb and struct.unpack_from('<H',ra[i],0)[0]==4228 and len(za[i])!=138:
            (S if len(zb[i])==138 else K).append((ra[i],ha[i],za[i],f,i))
print(len(S),len(K))
for nm,ix in (('R',0),('H',1)):
    Ls=collections.Counter(len(x[ix]) for x in S); Lk=collections.Counter(len(x[ix]) for x in K); print(nm,'len S',Ls.most_common(4),'K',Lk.most_common(4))
    L=min(min(len(x[ix]) for x in S),min(len(x[ix]) for x in K))
    for p in range(L):
        vs=collections.Counter(x[ix][p] for x in S); vk=collections.Counter(x[ix][p] for x in K)
        if len(set(vs)|set(vk))<=3 and set(vs)!=set(vk) or (set(vs)&set(vk)==set() and len(vs)<=3 and len(vk)<=3):
            print(nm,p,dict(vs),dict(vk))
def rule(x):
    r,h=x[0],x[1]
    return r[113:119]==b'\xff'*6 and h[61]==0 and h[64:68]==b'\0'*4 and h[68]==255 and r[146:151]==b'\0'*5
print('rule S',sum(map(rule,S)),'of',len(S),'K',sum(map(rule,K)),'of',len(K))
for x in K:
    if rule(x): print('K match',x[3],x[4],len(x[0]),len(x[2]))
print(sorted(collections.Counter((len(x[0]),len(x[2])) for x in S if rule(x)).items()))
print(sorted(collections.Counter((len(x[0]),len(x[2])) for x in K if rule(x)).items()))
S2=[x for x in S if rule(x)]; K2=[x for x in K if rule(x)]
for nm,ix in (('R',0),('H',1),('Z',2)):
    L=min(min(len(x[ix]) for x in S2),min(len(x[ix]) for x in K2))
    for p in range(L):
        vs=set(x[ix][p] for x in S2); vk=set(x[ix][p] for x in K2)
        if not (vs&vk) : print(nm,p,sorted(vs)[:6],sorted(vk))
