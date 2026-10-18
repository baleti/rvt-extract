import sys,pickle,struct; sys.path.insert(0,'~/src/rvt-extract/tools'); sys.path.insert(0,'~/src/rvt-extract')
from lat_lib import *
from adiff import walk_diff
from rvtx import latest
rfa=sys.argv[1]; dump=sys.argv[2]; fid=int(sys.argv[3]); idsf=sys.argv[4]
ra,sch,W,tag,d=latest_tree(rfa)
rp,_,_,_,_=latest_tree('~/rvt-research/corpus/2024/43_Snowdon_Towers_Sample_Structural.rvt')
ids=set(pickle.load(open(idsf,'rb')))
dd=pickle.load(open(dump,'rb')); cd=dd['cd']; g=cd.find(bytes.fromhex(dd['docs'][fid]['guid'])); n,=struct.unpack_from('<I',cd,g+16); blob=cd[g+20:g+20+n]
rb,_,_=enc.decode_tree(sch,W,blob,2,tag)
kn,ac=max(ids)+1-2+0,0
# new table ids: the two highest ids of the rfa
si=sorted(ids); kn,ac=si[-2],si[-1]
PK,PA=int(sys.argv[5]),int(sys.argv[6])
t,notes=latest.build_tree(sch,rp,rb,ids,remap={PK:kn,PA:ac})
out=[]; walk_diff(ra,t,'',out); print('diffs',len(out))
for o in out[:30]: print(o)
bs=latest.encode(sch,W,tag,t); print('bytes',len(bs),len(d),bs==d)
