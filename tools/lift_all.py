"""lift_all.py PROJECT OUTDIR [names...] : lift every family with an embedded document into OUTDIR/<Category>/<Family>.rfa (remote-host); writes lift_status.json"""
import sys, os, json, re, time, traceback
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import core, rfa, manifest
path, out = sys.argv[1], sys.argv[2]; only = set(sys.argv[3:])
def safe(s): return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', s or 'Unnamed').strip(' .') or 'Unnamed'
t0 = time.time(); prj = core.Project(path); pd = rfa.ProjectDocs(prj); print('loaded %.1fs' % (time.time() - t0), flush=True)
B = rfa.Builder(pd); status = {}
for fr in sorted(prj.families(), key=lambda r: r['fields'].get('m_name') or ''):
    nm = fr['fields'].get('m_name')
    if not nm or (only and nm not in only): continue
    cat = manifest.category_name(fr['fields']['m_categoryId'])
    st = {'category': cat, 'family_id': fr['id']}
    try:
        if not fr['fields'].get('m_oFamDoc'): st['status'] = 'no-embedded-doc'; status[nm] = st; continue
        b = B.build(fr)
        d = os.path.join(out, safe(cat)); os.makedirs(d, exist_ok=True); fn = os.path.join(d, safe(nm) + '.rfa')
        B.write(fn, nm, cat); st.update(status='written', file=os.path.relpath(fn, out), elements=len(b.all_ids), own=len(b.own), shared=len(b.shared))
    except Exception as e:
        st.update(status='error', error='%s: %s' % (type(e).__name__, e), trace=traceback.format_exc()[-600:])
    status[nm] = st; print(nm, st['status'], st.get('error', ''), flush=True)
json.dump(status, open(os.path.join(out, 'lift_status.json'), 'w'), indent=1)
print('done %.1fs' % (time.time() - t0), sum(1 for s in status.values() if s['status'] == 'written'), 'written of', len(status))
