#!/usr/bin/env python3
"""Census of embedded family documents in a project: records per family, by class. Usage: famcensus.py FILE OUT.json  (heavy: run on remote-host via h1run)"""
import sys,os,struct,collections,json,bisect
sys.path.insert(0,os.path.expanduser('~/rvt-research')); os.environ['RVT_GEOM']='1'
import numpy as np
import rvt_scan as S, rvt_decode as D, rvt2text as T, rvt_inventory as I, rvtfmt, rvt_xcache as X

def run(path):
    x=X.get_x(path)
    fams={}
    for k,v in x['recs'].items():
        if k[1]=='Family' and v['fields'].get('m_oFamDoc'):
            f=v['fields']; fams[v['id']]={'name':f.get('m_name'),'guid':f['m_oFamDoc']['obj']['m_contentDocGUID']['m_guid'],'nmap':len(f['m_oFamDoc']['obj']['m_big2SmallMap2'])}
    o,cls,ids=S.load(path); IDW=S.id_size(cls); sch=D.Schema(cls); dec=D.make_dec(sch,idsize=IDW)
    cd=rvtfmt.inflate_stream(o.openstream('Global/ContentDocuments').read())[1]
    starts=sorted((cd.find(bytes.fromhex(f['guid'])),fid) for fid,f in fams.items() if cd.find(bytes.fromhex(f['guid']))>=0)
    seg_of={}
    for a in range(4):
        n=(len(cd)-a)//4; arr=np.frombuffer(cd,dtype='<u4',count=n,offset=a)
        for j,v in enumerate(arr):
            v=int(v)
            if 0<v<2000000 and v not in ids and v not in seg_of:
                pos=j*4+a; si=bisect.bisect_right([s for s,_ in starts],pos)-1
                seg_of[v]=starts[si][1] if si>=0 else None
    etags=I.element_tags(cls)
    idarr=np.array(sorted(seg_of),dtype=np.uint32 if IDW==4 else np.uint64); IDF='<I' if IDW==4 else '<Q'
    per=collections.defaultdict(collections.Counter); st=collections.Counter(); seen=set()
    for pn in sorted(y for y in ['/'.join(e) for e in o.listdir(streams=True)] if y.startswith('Partitions/')):
        chunk=T.joined(o.openstream(pn).read())
        for i in S.header_candidates(chunk,idarr,IDW):
            eid=struct.unpack_from(IDF,chunk,i+4)[0]
            for short in (False,True):
                tag=struct.unpack_from('<H',chunk,i+12+IDW-(4 if short else 0))[0]
                if tag not in etags: continue
                try: r,q=dec.record(chunk,i,short)
                except Exception: continue
                if r['fields'].get('m_id')!=eid or (eid,r['class']) in seen: continue
                seen.add((eid,r['class'])); per[seg_of[eid]][r['class']]+=1; st['ok']+=1
    out={'file':path,'families':{str(fid):dict(fams[fid],classes=dict(per.get(fid,{})),nrec=sum(per.get(fid,{}).values())) for fid in fams},'unassigned':dict(per.get(None,{})),'stats':dict(st)}
    return out
if __name__=='__main__':
    json.dump(run(sys.argv[1]),open(sys.argv[2],'w'),indent=1); print('done')
