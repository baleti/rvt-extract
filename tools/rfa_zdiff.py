import sys,os,struct,collections
sys.path.insert(0,'.')
import rvtx, olefile, rvt2text as T
from rvtx import partition as PT
def parts(p):
    o=olefile.OleFileIO(p); return PT.parse_joined(T.joined(o.openstream('Partitions/0').read()),8)[0]
NEG=(1<<64)-1
for l in open('private/cmp_list.tsv'):
    f,s,g=l.rstrip('\n').split('\t')
    a=parts('private/rfa/corp-2024-43/'+f); b=parts(g)
    za={x[0]:x for x in a['Z'] if x[0]!=NEG}; zb={x[0]:x for x in b['Z'] if x[0]!=NEG}
    d=[(i,struct.unpack_from('<H',za[i][1],0)[0],len(za[i][1]),len(zb[i][1])) for i in sorted(set(za)&set(zb)) if za[i]!=zb[i]]
    print(f,s,len(set(za)^set(zb)),len(d),d[:3],flush=True)
