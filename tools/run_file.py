#!/usr/bin/env python3
"""run_file.py PATH OUTDIR ANONID [--no-rfa] : robust full extraction run for one project (remote-host). Writes OUTDIR/summary.json; family names stay local."""
import sys, os, json, re, time, traceback, resource
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import core, manifest, items, files
path, out, aid = sys.argv[1], sys.argv[2], sys.argv[3]; norfa = '--no-rfa' in sys.argv
os.makedirs(out, exist_ok=True)
S = {'id': aid, 'size': os.path.getsize(path), 'steps': {}}
def step(name, fn):
    t0 = time.time()
    try:
        r = fn(); S['steps'][name] = {'ok': True, 'sec': round(time.time() - t0, 1)}; return r
    except Exception as e:
        S['steps'][name] = {'ok': False, 'sec': round(time.time() - t0, 1), 'error': '%s: %s' % (type(e).__name__, str(e)[:200]), 'trace': traceback.format_exc()[-500:]}
        return None
def flush():
    S['maxrss_mb'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024
    json.dump(S, open(os.path.join(out, 'summary.json'), 'w'), indent=1)
prj = step('load', lambda: core.Project(path)); flush()
if prj is None: sys.exit(0)
S['records'] = len(prj.recs); S['idwidth'] = prj.W
fams = [r for r in prj.families() if r['fields'].get('m_name')]
S['families'] = len(fams); S['with_doc'] = sum(1 for r in fams if r['fields'].get('m_oFamDoc'))
S['in_place'] = sum(1 for r in fams if r['fields'].get('m_inPlace'))
ents = step('manifest', lambda: [manifest.family_entry(prj, r, None) for r in fams])
if ents:
    S['categories'] = len({e['category'] for e in ents}); S['types'] = sum(len(e['types']) for e in ents)
# other extractors
S['kinds'] = {}
for k, fn in list(items.KINDS.items()) + list(files.KINDS.items()):
    t0 = time.time()
    try:
        d, fl = fn(prj) if k in items.KINDS else fn(path)
        S['kinds'][k] = {'ok': True, 'n': len(d) if hasattr(d, '__len__') else 1, 'sec': round(time.time() - t0, 1)}
    except Exception as e:
        S['kinds'][k] = {'ok': False, 'error': '%s: %s' % (type(e).__name__, str(e)[:120])}
flush()
if not norfa and S['with_doc']:
    from rvtx import rfa as RFA
    pd = step('docs', lambda: RFA.ProjectDocs(prj)); flush()
    if pd is not None:
        S['partition_docs'] = len(pd.docs) - 1; S['format'] = pd.fmt; B = RFA.Builder(pd); res = {}
        def safe(s): return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', s or 'Unnamed').strip(' .') or 'Unnamed'
        for n, fr in enumerate(fams):
            if not fr['fields'].get('m_oFamDoc'): continue
            nm = fr['fields']['m_name']; cat = manifest.category_name(fr['fields']['m_categoryId']); st = {'category': cat}
            try:
                b = B.build(fr); d = os.path.join(out, 'rfa', safe(cat)); os.makedirs(d, exist_ok=True); fn = os.path.join(d, '%s__%d.rfa' % (safe(nm)[:80], fr['id']))
                B.write(fn, nm, cat); st.update(status='written', file=os.path.relpath(fn, out), elements=len(b.all_ids), own=len(b.own), shared=len(b.shared), size=os.path.getsize(fn))
            except Exception as e:
                st.update(status='error', error='%s: %s' % (type(e).__name__, str(e)[:160]), trace=traceback.format_exc()[-400:])
            res['%s__%d' % (nm, fr['id'])] = st
            if n % 20 == 0: S['rfa_written'] = sum(1 for v in res.values() if v['status'] == 'written'); flush()
        json.dump(res, open(os.path.join(out, 'lift_status.json'), 'w'), indent=1)
        S['rfa_written'] = sum(1 for v in res.values() if v['status'] == 'written'); S['rfa_errors'] = sum(1 for v in res.values() if v['status'] == 'error')
        import collections
        S['rfa_error_kinds'] = dict(collections.Counter(v.get('error', '')[:60] for v in res.values() if v['status'] == 'error').most_common(8))
S['done'] = True; flush()
