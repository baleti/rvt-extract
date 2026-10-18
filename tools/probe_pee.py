"""probe_pee.py PROJECT FAMILYNAME : list ParamElemExternal elements of the project and which ids the family's records / Family record reference (remote-host)"""
import sys, os, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import core, rfa
path, nm = sys.argv[1:3]
prj = core.Project(path)
pee = {i: r for (i, c), r in prj.recs.items() if c == 'ParamElemExternal'}
print('ParamElemExternal in project:', len(pee), 'ids', sorted(pee)[:3], '...', sorted(pee)[-3:])
r0 = pee[sorted(pee)[0]]; print('fields', {k: (str(v)[:60]) for k, v in r0['fields'].items()})
fr = next(r for r in prj.families() if r['fields'].get('m_name') == nm)
f = fr['fields']; print('family fields with ids:', [k for k in f if 'amil' in k or 'bsorb' in k][:12])
fi = f.get('m_familyIds'); print('familyIds type', type(fi).__name__, str(fi)[:300])
pd = rfa.ProjectDocs(prj); k = pd.family_doc_index(fr); print('doc', k, 'n h', len(pd.docs[k]['H']))
ids = {i for i, b in pd.docs[k]['H']}
print('pee ids inside this family doc:', len(ids & set(pee)), 'family doc ids near 187616..:', len([i for i in ids if 187616 <= i < 187640]))
