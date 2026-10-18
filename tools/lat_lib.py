import sys,struct,olefile,pickle
sys.path.insert(0,'~/src/rvt-extract')
import rvtx
from rvtx import enc
import fmt_parser as fp, rvt_decode as D, rvt_scan as S
from rvtfmt import inflate_stream
def load_schema(path):
    o=olefile.OleFileIO(path); cls,_=fp.parse(inflate_stream(o.openstream('Formats/Latest').read())[1]); return o,cls,D.Schema(cls),S.id_size(cls)
def latest_tree(path):
    o,cls,sch,W=load_schema(path); d=inflate_stream(o.openstream('Global/Latest').read())[1]
    tag=struct.unpack_from('<H',d,0)[0]; v,p,c=enc.decode_tree(sch,W,d,2,tag); return v,sch,W,tag,d
def shift(v):
    if isinstance(v,dict):
        if 'ref' in v and v['ref']>=2: v['ref']-=1
        if 'handle' in v and v['handle']!=0xffffffff and v['handle']>=2: v['handle']-=1
        for x in v.values(): shift(x)
    elif isinstance(v,list):
        for x in v: shift(x)
