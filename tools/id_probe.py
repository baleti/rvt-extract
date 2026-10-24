"""id_probe.py PROJECT ID[,ID..] : class / presence of element ids in the project main doc and which main-doc records reference them (remote-host)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')); sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import rvtx
from rvtx import core, rfa
prj = core.Project(sys.argv[1]); pd = rfa.ProjectDocs(prj); ids = [int(x) for a in sys.argv[2:] for x in a.split(',')]
print('id_doc sample', {i: pd.id_doc.get(i) for i in ids})
for i in ids:
    r = pd.byid.get(i); print(i, 'main:', r['class'] if r else None)
refs = {i: [] for i in ids}
for j, r in pd.byid.items():
    out = set(); rfa._eids(r['fields'], out)
    for i in ids:
        if i in out: refs[i].append((j, r['class']))
for i in ids: print(i, 'referenced by', refs[i][:8])
