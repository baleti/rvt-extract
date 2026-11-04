import sys,struct,collections
sys.path.insert(0,'.')
import rvtx, olefile, rvt2text as T
from rvtx import partition as PT
def parts(p):
    o=olefile.OleFileIO(p); return PT.parse_joined(T.joined(o.openstream('Partitions/0').read()),8)[0]
NEG=(1<<64)-1
c=collections.Counter(); ex={}
for l in list(open('private/cmp_list.tsv'))[::3]:
    f,s,g=l.rstrip('\n').split('\t'); a=parts('private/rfa/corp-2024-43/'+f); b=parts(g)
    ra={x[0]:x[1] for x in a['R']}
    za={x[0]:x[1] for x in a['Z'] if x[0]!=NEG}; zb={x[0]:x[1] for x in b['Z'] if x[0]!=NEG}
    for i in za:
        if i in zb and struct.unpack_from('<H',za[i],0)[0]==2111:
            rt=struct.unpack_from('<H',ra[i],0)[0]
            k=(rt,'stub' if len(zb[i])==138 else ('same' if za[i]==zb[i] else 'diff'),'oursstub' if len(za[i])==138 else 'oursfull')
            c[k]+=1
for k,v in sorted(c.items(),key=lambda x:-x[1])[:30]: print(v,k)
