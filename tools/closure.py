"""closure.py PROJECT SHARED.pkl : derive the shared set (builtin-category GStyleElem + referenced Material/patterns/assets/property sets) and compare with the Revit-saved rfa intersection (remote-host)"""
import sys, os, pickle, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import core
import rvt_decode as D
EID = D.EID
prj = core.Project(sys.argv[1]); recs = prj.recs
byid = {}
for (i, c), r in recs.items(): byid[i] = r
S0 = pickle.load(open(sys.argv[2], 'rb'))
keys = [set(v) for v in S0.values()]; inter = set.intersection(*keys)
inter_ids = {k[0] for k in inter}
import re
KEY = re.compile(r'(Id|Ids|ElemId|Pattern|Material)$')
def eids(o, out, key=''):
    if isinstance(o, EID): out.add(int(o.v) if hasattr(o, 'v') else int(o))
    elif isinstance(o, bool): pass
    elif isinstance(o, int):
        if KEY.search(key): out.add(o)
    elif isinstance(o, dict):
        for k, v in o.items(): eids(v, out, k)
    elif isinstance(o, list):
        for v in o: eids(v, out, key)
def sg(v): return v - (1 << 64) if v >= (1 << 63) else (v - (1 << 32) if v >= (1 << 31) and v < (1 << 32) else v)
TARGET = {'MaterialElem', 'FillPatternElem', 'LinePatternElem', 'AppearanceAssetElem', 'PropertySetElement'}
seed = set()
for (i, c), r in recs.items():
    if c == 'GStyleElem':
        cat = r['fields'].get('m_categoryId')
        if cat is not None and sg(int(getattr(cat, 'v', cat))) < 0: seed.add(i)
print('builtin gstyles', len(seed), 'in rfa inter', len(seed & inter_ids), 'inter gstyles', sum(1 for k in inter if k[1] == 'GStyleElem'))
CATSEED = set()
for (i, c), r in recs.items():
    if c == 'CategoryElem':
        out = set(); eids(r['fields'], out)
        for e in out:
            if e in byid and byid[e]['class'] in TARGET: CATSEED.add(e)
print('category-referenced', len(CATSEED), sorted(CATSEED)[:10])
shared = set(seed) | CATSEED; frontier = set(shared); step = 0
while frontier:
    nxt = set()
    for i in frontier:
        out = set(); eids(byid[i]['fields'], out)
        for e in out:
            if e in byid and byid[e]['class'] in TARGET and e not in shared: nxt.add(e)
    shared |= nxt; frontier = nxt; step += 1
print('closure', len(shared), 'steps', step, collections.Counter(byid[i]['class'] for i in shared))
print('inter', len(inter_ids), 'closure & inter', len(shared & inter_ids), 'closure - inter', len(shared - inter_ids), 'inter - closure', len(inter_ids - shared))
print('inter - closure', collections.Counter(byid[i]['class'] if i in byid else '?' for i in inter_ids - shared), sorted(inter_ids - shared)[:10])
print('closure - inter', collections.Counter(byid[i]['class'] for i in shared - inter_ids), sorted(shared - inter_ids)[:10])
