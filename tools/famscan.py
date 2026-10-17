import sys,os,struct,collections,pickle
sys.path.insert(0,'~/rvt-research'); os.environ['RVT_GEOM']='1'
import numpy as np
import rvt_scan as S, rvt_decode as D, rvt2text as T, rvt_inventory as I
def famrecs(path, xpkl):
    x=pickle.load(open(xpkl,'rb'))
    small={}   # small id -> (family id, big id)
    for k,v in x['recs'].items():
        if k[1]=='Family' and v['fields'].get('m_oFamDoc'):
            for p in v['fields']['m_oFamDoc']['obj']['m_big2SmallMap2']:
                small[p['second']['m_id']]=(v['id'],int(p['first'].v) if hasattr(p['first'],'v') else p['first'])
    o,cls,ids=S.load(path); IDW=S.id_size(cls); sch=D.Schema(cls); dec=D.make_dec(sch,idsize=IDW)
    etags=I.element_tags(cls)
    idarr=np.array(sorted(small),dtype=np.uint32 if IDW==4 else np.uint64)
    IDF='<I' if IDW==4 else '<Q'
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
                st['dec']+=1
                if r['fields'].get('m_id')!=eid: st['idmismatch']+=1; st[('mid',r['fields'].get('m_id') is None)]+=1; continue
                r['A']=struct.unpack_from('<I',chunk,i)[0]; r['len']=q-i; r['where']=(pn,i); out.setdefault(eid,[]).append(r); st['ok']+=1
    return out,small,st
if __name__=='__main__':
    out,small,st=famrecs(sys.argv[1],sys.argv[2])
    print(dict(st), len(out),'of',len(small))
    c=collections.Counter(r[-1]['class'] for r in out.values()); print(c.most_common(60))
    pickle.dump((out,small),open(sys.argv[3],'wb'))
