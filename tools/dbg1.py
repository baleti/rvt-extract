import sys; sys.path.insert(0,'~/src/rvt-extract')
import rvtx; from rvtx import core
p=core.Project(sys.argv[1])
for r in p.families():
    d=r['fields'].get('m_oFamDoc')
    if d: print(str(d['obj']['m_big2SmallMap2'][:3])[:600]); break
