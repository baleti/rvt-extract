"""facts_diff.py GT.tsv OURS.tsv... : per-family comparison of oracle facts (OPEN/TYPE/PARAM/CNT/REFPLANE/FORM) between Revit's own rfa and ours (light)"""
import sys,collections
def facts(files):
    d=collections.defaultdict(lambda: collections.defaultdict(list))
    for f in files:
        for l in open(f):
            p=l.rstrip('\n').split('\t')
            if len(p)<2 or p[0] in ('OPENFAIL','DIALOG'): continue
            if p[0]=='FORM': p=p[:4]+[x for x in p[4:] if not x.startswith('bbox')][:0] if False else p   # keep all form fields
            d[p[1]][p[0]].append(tuple(p[2:]))
    return d
g=facts([sys.argv[1]]); o=facts(sys.argv[2:])
bad=collections.Counter(); per=collections.defaultdict(list)
for fam in sorted(g):
    if fam not in o: per[fam].append('missing'); continue
    for k in set(g[fam])|set(o[fam]):
        a=sorted(g[fam].get(k,[])); b=sorted(o[fam].get(k,[]))
        if k=='OPEN': a=[(x[0],x[2]) if len(x)>2 else x for x in a]; b=[(x[0],x[2]) if len(x)>2 else x for x in b]
        if a!=b: bad[k]+=1; per[fam].append(k)
print('families',len(g),'with differences',len(per)); print(dict(bad))
for fam,k in list(per.items())[:25]: print(fam,k)
