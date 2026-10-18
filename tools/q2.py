import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import core
prj = core.Project(sys.argv[1]); byid = {i: r for (i, c), r in prj.recs.items()}
for i in (23, 43333, 260568, 260569, 260570):
    m = byid[i]['fields']['m_pMaterial']['obj']
    print(i, m['m_name'], {k: str(v) for k, v in m.items() if 'ppearance' in k or 'tructural' in k or 'attern' in k})
a = byid[529814]['fields']['m_pAppearanceAsset']['obj']; print(529814, {k: str(v)[:80] for k, v in a.items()})
