"""probe_levels.py PROJECT GT.tsv : list Level records with flags and mark which ids Revit's element export also has (remote-host)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import core
path, gt = sys.argv[1:3]
rv = {}
for l in open(gt):
    p = l.rstrip('\n').split('\t')
    if p[0] == 'E' and p[2] == 'Level': rv[int(p[1])] = p[4]
prj = core.Project(path)
def g(f, k):
    v = f.get(k); return getattr(v, 'v', v)
for r in sorted(prj.by_class['Level'], key=lambda r: r['id']):
    f = r['fields']
    print(r['id'], 'inRevit' if r['id'] in rv else 'ONLY-OURS', repr(f.get('m_text')), 'moribund', g(f, 'm_moribund'), 'dummy', g(f, 'm_dummy'), 'famId', g(f, 'm_famId'), 'dopt', g(f, 'm_designOptionId'), 'ownerView', g(f, 'm_ownerDBViewId'), 'phase', g(f, 'm_createdPhaseId'),
          'elev', (f.get('m_pSurface') or {}).get('obj', {}).get('m_origin') if isinstance(f.get('m_pSurface'), dict) else None)
print('revit-only ids', sorted(set(rv) - {r['id'] for r in prj.by_class['Level']}))
