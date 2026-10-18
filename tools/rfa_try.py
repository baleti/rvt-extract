"""rfa_try.py PROJECT OUTDIR FAMILY[,FAMILY...] [REVIT_RFA_DIR] : lift families out of PROJECT (remote-host); compare with Revit-saved rfa if given"""
import sys, os, pickle, struct, collections, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import core, rfa, partition as PT
path, out, names = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
ref = sys.argv[4] if len(sys.argv) > 4 else None
os.makedirs(out, exist_ok=True)
t0 = time.time(); prj = core.Project(path); pd = rfa.ProjectDocs(prj); print('loaded', time.time() - t0, flush=True)
B = rfa.Builder(pd)
for nm in names:
    fr = next(r for r in prj.families() if r['fields'].get('m_name') == nm)
    b = B.build(fr)
    cat = None
    fn = os.path.join(out, nm + '.rfa')
    try:
        B.write(fn, nm, 'Generic'); print(nm, 'written', os.path.getsize(fn), 'ids', len(b.all_ids), 'shared', len(b.shared), flush=True)
    except Exception as e:
        import traceback; traceback.print_exc()
    pickle.dump({'H': b.H, 'R': b.R, 'Z': b.Z, 'ids': b.all_ids, 'fid': b.fid, 'own': b.own, 'shared': b.shared}, open(os.path.join(out, nm + '.items.pkl'), 'wb'))
