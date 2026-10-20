"""probe_views.py PROJECT GT.tsv : DBView* records that Revit's element export lacks, with scope flags (remote-host)"""
import sys, os, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import core
path, gt = sys.argv[1:3]
rv = {}
for l in open(gt):
    p = l.rstrip('\n').split('\t')
    if p[0] == 'E' and (p[2].startswith('View') or p[2].endswith('ScheduleView')): rv[int(p[1])] = (p[2], p[4])
prj = core.Project(path)
def g(f, k):
    v = f.get(k); return getattr(v, 'v', v)
n = collections.Counter()
for c, lst in prj.by_class.items():
    if not c.startswith('DBView'): continue
    for r in lst:
        f = r['fields']
        if r['id'] in rv: n['in'] += 1; continue
        n['only-ours'] += 1
        if n['only-ours'] <= 25: print(c, r['id'], repr(f.get('m_viewName')), 'tmpl', f.get('m_isTemplate'), 'famId', g(f, 'm_famId'), 'dopt', g(f, 'm_designOptionId'), 'dep', g(f, 'm_primaryViewId') if 'm_primaryViewId' in f else None, 'moribund', g(f, 'm_moribund'))
print(n)
