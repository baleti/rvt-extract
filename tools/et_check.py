import sys,pickle,struct,olefile; sys.path.insert(0,'~/src/rvt-extract'); sys.path.insert(0,'~/rvt-research')
import rvtx
from rvtx import elemtable as ET
import rvtfmt
rfa,dump,key,fid,clsf=sys.argv[1:6]; fid=int(fid); key=int(key)
dd=pickle.load(open(dump,'rb')); cd=dd['cd']; doc=dd["docs"][key]; g=cd.find(bytes.fromhex(doc['guid']))
seg=cd[g-13:g+80000]
own=set(doc['records']); rows=ET.cd_rows(seg)
cls=pickle.load(open(clsf,'rb'))
A=olefile.OleFileIO(rfa); ae=rvtfmt.inflate_stream(A.openstream('Global/ElemTable').read())[1]
mine=ET.build(sorted(cls), own, rows, fid, special_neg=(fid,1028040,1028041))
print(len(mine),len(ae), mine==ae)
bad=[i for i in range(0,len(ae)-6,40) if mine[6+i:46+i]!=ae[6+i:46+i]]; print('bad rows',len(bad))
for b in bad[:6]: print(ae[6+b:46+b].hex()); print(mine[6+b:46+b].hex())
