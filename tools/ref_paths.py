"""ref_paths.py PROJECT NAME[,NAME] : field paths in the project-side Family record that reference EXTRA-class records (remote-host)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import core, rfa
prj = core.Project(sys.argv[1]); pd = rfa.ProjectDocs(prj)
def walk(o, path, out):
    if isinstance(o, rfa.EID):
        i = int(getattr(o, 'v', o)); q = pd.byid.get(i)
        if q is not None and q['class'] in rfa.EXTRA: out.append((path, i, q['class']))
    elif isinstance(o, dict):
        for k, v in o.items():
            if k != 'm_oFamDoc': walk(v, path + '/' + k, out)
    elif isinstance(o, list):
        for n, v in enumerate(o): walk(v, '%s[%d]' % (path, n), out)
for nm in [x for a in sys.argv[2:] for x in a.split(',')]:
    fr = next(r for r in prj.families() if r['fields'].get('m_name') == nm)
    out = []; walk(fr['fields'], '', out)
    import collections
    print('==', nm, fr['id'], len(out)); 
    seen = collections.Counter(); 
    for p, i, c in out:
        key = (p.split('[')[0], c); seen[key] += 1
    for k, v in seen.items(): print('  ', k, v)
