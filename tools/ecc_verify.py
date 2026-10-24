"""ecc_verify.py FILES... : last-page ECC check of every stream of Revit-written files -> N: (pass, fail) (light)"""
import sys,os,glob,collections; sys.path.insert(0,os.path.join(os.path.dirname(os.path.realpath(__file__)),'..')); import rvtx
sys.path.insert(0,os.path.expanduser('~/rvt-research/write-lab')); import ecc, olefile
res=collections.defaultdict(lambda:[0,0])
for p in sys.argv[1:]:
    try: o=olefile.OleFileIO(p)
    except Exception: continue
    for e in o.listdir(streams=True):
        nm='/'.join(e)
        if not (nm.startswith('Partitions/') or nm in ('Global/Latest','Global/ElemTable','Formats/Latest')): continue
        s=o.openstream(nm).read(); n=len(s)%65249
        if n<30 or ecc.params(n) is None: continue
        ok=ecc.check(s[-n:]); res[n][0 if ok else 1]+=1
import json; json.dump({str(k):v for k,v in res.items()},open(os.environ.get('OUT','/tmp/claude-1000/ecc_ver.json'),'w'))
print(len(res), sum(1 for v in res.values() if v[0] and not v[1]), 'fail-only', sorted(k for k,v in res.items() if v[1] and not v[0])[:40])
