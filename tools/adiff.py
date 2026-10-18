import sys,pickle
sys.path.insert(0,'~/src/rvt-extract/tools')
from adoc import decode_adoc
def norm(v):
    return v
def walk_diff(a,b,path,out,depth=0):
    if type(a)!=type(b): out.append((path,'type',str(a)[:60],str(b)[:60])); return
    if isinstance(a,dict):
        for k in a.keys()|b.keys():
            if k not in a: out.append((path+'/'+str(k),'only_b',None,None))
            elif k not in b: out.append((path+'/'+str(k),'only_a',None,None))
            else: walk_diff(a[k],b[k],path+'/'+str(k),out,depth+1)
    elif isinstance(a,list):
        if len(a)!=len(b): out.append((path,'len',len(a),len(b)))
        for i,(x,y) in enumerate(zip(a,b)):
            if len(out)<4000: walk_diff(x,y,path+'[%d]'%i,out,depth+1)
    else:
        if str(a)!=str(b): out.append((path,'val',str(a)[:60],str(b)[:60]))
if __name__=='__main__':
    ra=decode_adoc('~/rvt-research/write-lab/gt_fam/2024_test/Callout Heads/Callout Head.rfa',maxh=1)
    rb=decode_adoc('~/rvt-research/corpus/2024/43_Snowdon_Towers_Sample_Structural.rvt',maxh=1)
    print('proj',{k:str(rb[k])[:300] for k in rb if k in('end','len','complete','err','error')})
    out=[]; walk_diff(ra['fields'],rb['fields'],'',out)
    print(len(out))
    import collections
    c=collections.Counter(o[0].split('/')[1] if o[0].count('/')>=1 else o[0] for o in out); print(c)
    for o in out[:50]: print(o)
