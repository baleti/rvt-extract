import sys,os,struct,collections,pickle
sys.path.insert(0,'~/rvt-research'); os.environ['RVT_GEOM']='1'
import numpy as np, olefile
import rvt_scan as S, rvt_decode as D, rvt2text as T, rvt_inventory as I, rvtfmt
path=sys.argv[1]
o,cls,ids=S.load(path); IDW=S.id_size(cls); sch=D.Schema(cls); dec=D.make_dec(sch,idsize=IDW)
cd=rvtfmt.inflate_stream(o.openstream('Global/ContentDocuments').read())[1]
cand=set()
for a in range(4):
    n=(len(cd)-a)//4
    arr=np.frombuffer(cd,dtype='<u4',count=n,offset=a)
    cand|=set(int(v) for v in np.unique(arr) if 0<v<2000000)
cand-=ids
print('cand ids',len(cand))
etags=I.element_tags(cls)
idarr=np.array(sorted(cand),dtype=np.uint32 if IDW==4 else np.uint64); IDF='<I' if IDW==4 else '<Q'
out={}; st=collections.Counter()
for pn in sorted(x for x in ['/'.join(e) for e in o.listdir(streams=True)] if x.startswith('Partitions/')):
    chunk=T.joined(o.openstream(pn).read())
    for i in S.header_candidates(chunk,idarr,IDW):
        eid=struct.unpack_from(IDF,chunk,i+4)[0]
        for short in (False,True):
            tag=struct.unpack_from('<H',chunk,i+12+IDW-(4 if short else 0))[0]
            if tag not in etags: continue
            st['cand']+=1
            try: r,q=dec.record(chunk,i,short)
            except Exception as e: st['desync']+=1; continue
            if r['fields'].get('m_id')!=eid: st['idmismatch']+=1; continue
            r['A']=struct.unpack_from('<I',chunk,i)[0]; r['len']=q-i; r['where']=(pn,i); out.setdefault(eid,[]).append(r); st['ok']+=1
print(dict(st),len(out))
c=collections.Counter(r[-1]['class'] for r in out.values()); print(c.most_common(80))
pickle.dump(out,open(sys.argv[2],'wb'))
