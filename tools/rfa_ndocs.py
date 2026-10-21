import sys,collections
sys.path.insert(0,'.')
import rvtx, olefile, rvt2text as T
from rvtx import partition as PT
for l in open('private/cmp_list.tsv'):
    f,s,g=l.rstrip('\n').split('\t')
    o=olefile.OleFileIO(g); docs=PT.parse_joined(T.joined(o.openstream('Partitions/0').read()),8)
    print(f,s,len(docs),flush=True)
