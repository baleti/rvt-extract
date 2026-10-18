import sys,struct,olefile
sys.path.insert(0,'~/rvt-research')
import fmt_parser as fp, rvt_decode as D, rvt_scan as S
from rvtfmt import inflate_stream
def decode_adoc(path_or_streams, maxh=1, stream='Global/Latest', data=None, cls=None):
    o=olefile.OleFileIO(path_or_streams)
    if cls is None: cls,_=fp.parse(inflate_stream(o.openstream('Formats/Latest').read())[1])
    sch=D.Schema(cls); W=S.id_size(cls)
    d=data if data is not None else inflate_stream(o.openstream(stream).read())[1]
    tag=struct.unpack_from('<H',d,0)[0]
    dec=D.Dec(sch,idsize=W); dec.STOP=(); dec.visited=[]; dec.err=None; dec.maxh=maxh; dec.defined={1}
    try:
        v,pp,complete=dec.body(d,2,tag,[sch.name(tag)],top=True)
        return dict(fields=v,end=pp,len=len(d),complete=complete,err=dec.err,dec=dec,sch=sch)
    except D.Desync as e:
        return dict(error=str(e)[:500],len=len(d),dec=dec)
