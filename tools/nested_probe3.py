"""nested_probe3.py PROJECT NAME : docs hit by the Family.m_oFamDoc big2small map (remote-host)"""
import sys, os, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import core, rfa
prj = core.Project(sys.argv[1]); pd = rfa.ProjectDocs(prj)
for nm in sys.argv[2:]:
    fr = next(r for r in prj.families() if r['fields'].get('m_name') == nm)
    d = fr['fields']['m_oFamDoc']; cnt = collections.Counter(); keys = {}
    for p in d['obj']['m_big2SmallMap2']:
        s = p['second']; s = s['m_id'] if 'm_id' in s else s['m_id64']; i = int(getattr(s, 'v', s)); k = pd.id_doc.get(i); cnt[k] += 1; keys.setdefault(k, i)
    print(nm, 'map size', len(d['obj']['m_big2SmallMap2']), 'docs', dict(cnt), keys, 'other fields', [k for k in d['obj'].keys()])
    cc = d['obj']['m_coreIds']; print('  m_coreIds', str(cc)[:300])
    ids = set(); rfa._eids(cc, ids); print('  coreIds docs', collections.Counter(pd.id_doc.get(i) for i in ids))
own = {}
for r in prj.families():
    dd = r['fields'].get('m_oFamDoc')
    if dd: own.setdefault(pd.family_doc_index(r), []).append(r['fields'].get('m_name'))
print('doc 173 owners', own.get(173), 'doc 248', own.get(248))
