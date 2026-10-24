#!/usr/bin/env python3
"""batch_one.py FILE ID STATEDIR OUTDIR : run the rvt-extract pipeline on one project with per-family and per-kind error capture.
Resumable: STATEDIR/ID.fam.jsonl gets one line per finished family (status written|error|no-embedded-doc), ID.kinds.json per finished kind,
ID.cur holds the family being built (so a hard crash names its culprit). Output .rfa under OUTDIR/ID/<n>.rfa (anonymous names)."""
import sys, os, json, time, traceback, re, resource
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import core, rfa as RFA, manifest, items, files
path, fid, sd, od = sys.argv[1:5]
os.makedirs(sd, exist_ok=True); os.makedirs(os.path.join(od, fid), exist_ok=True)
J = lambda n: os.path.join(sd, fid + n)
def rss(): return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024
def basic_year(raw):
    import re
    for off in (0, 1):
        b = raw[off:].decode('utf-16le', 'ignore')
        m = re.search(r'Format:\s*(20[12]\d)', b) or re.search(r'Autodesk Revit (20[12]\d)', b)
        if m: return int(m.group(1))
    m = re.search(r'(20[12]\d)', raw[:40].decode('utf-16le', 'ignore'))
    return int(m.group(1)) if m else None
def year_of(p):
    import olefile
    o = olefile.OleFileIO(p); b = o.openstream('BasicFileInfo').read(); o.close()
    return basic_year(b)
meta = json.load(open(J('.meta.json'))) if os.path.exists(J('.meta.json')) else {}
t0 = time.time(); meta.setdefault('id', fid); meta['size'] = os.path.getsize(path)
try: meta['year'] = year_of(path)
except Exception as e: meta['year'] = None; meta['year_err'] = str(e)[:100]
done = {}
if os.path.exists(J('.fam.jsonl')):
    for l in open(J('.fam.jsonl')):
        try: d = json.loads(l); done[d['idx']] = d
        except Exception: pass
prj = core.Project(path); meta['load_s'] = round(time.time() - t0, 1); meta['rss_load_mb'] = rss()
fams = sorted([fr for fr in prj.families() if fr['fields'].get('m_name')], key=lambda r: r['fields'].get('m_name') or '')
meta['families_total'] = len(fams)
json.dump(meta, open(J('.meta.json'), 'w'))
todo = [i for i in range(len(fams)) if i not in done] if not os.environ.get('KINDS_ONLY') else []
fl = open(J('.fam.jsonl'), 'a')
if todo:
    t1 = time.time(); docs, st = core.scan_family_docs(prj); meta['scan_s'] = round(time.time() - t1, 1); meta['rss_scan_mb'] = rss()
    pd = RFA.ProjectDocs(prj); B = RFA.Builder(pd); meta['rss_pd_mb'] = rss(); json.dump(meta, open(J('.meta.json'), 'w'))
    for i in todo:
        fr = fams[i]; open(J('.cur'), 'w').write(str(i)); t2 = time.time()
        r = {'idx': i}
        try:
            e = manifest.family_entry(prj, fr, docs.get(fr['id']))
            r.update(category=e['category'], embedded=e['embedded_doc'], types=len(e['types']), params=len(e['parameters']), records=e['embedded_records'],
                     manifest_ok=True)
        except Exception as ex:
            r.update(manifest_ok=False, manifest_error='%s: %s' % (type(ex).__name__, ex)); e = None
        if not fr['fields'].get('m_oFamDoc'): r['status'] = 'no-embedded-doc'
        else:
            try:
                b = B.build(fr); fn = os.path.join(od, fid, '%04d.rfa' % i)
                B.write(fn, fr['fields']['m_name'], r.get('category', 'Unknown'))
                r['nested'] = bool(B.nested_docs(B.k)); r.update(status='written', file='%s/%04d.rfa' % (fid, i), bytes=os.path.getsize(fn), elements=len(b.all_ids), own=len(b.own), shared=len(b.shared))
            except Exception as ex:
                r.update(status='error', error='%s: %s' % (type(ex).__name__, str(ex)[:300]), trace=traceback.format_exc()[-500:])
        r['secs'] = round(time.time() - t2, 2); r['rss_mb'] = rss()
        fl.write(json.dumps(r) + '\n'); fl.flush()
    if os.path.exists(J('.cur')): os.remove(J('.cur'))
kinds = json.load(open(J('.kinds.json'))) if os.path.exists(J('.kinds.json')) else {}
for k in list(items.KINDS) + list(files.KINDS):
    if k in kinds: continue
    t3 = time.time(); r = {}
    try:
        fn = items.KINDS.get(k)
        data, fls = fn(prj) if fn else files.KINDS[k](path)
        r.update(ok=True, count=(sum(len(x) if hasattr(x, '__len__') else 1 for x in data.values()) if isinstance(data, dict) else len(data) if hasattr(data, '__len__') else 1), top=(sorted((k, len(x) if hasattr(x, '__len__') else 1) for k, x in data.items()) if isinstance(data, dict) else None), files=len(fls), file_bytes=sum(len(b) for _, b in fls))
        r['json_bytes'] = len(json.dumps(data, default=str))
        if k == 'views' and isinstance(data, dict):
            import collections; r['by_class'] = dict(collections.Counter(x.get('class') for x in data.get('views', [])))
        if k == 'levels_grids' and isinstance(data, dict): r['main'] = {a: sum(1 for x in data.get(a, [])) for a in ('levels', 'grids')}
    except Exception as ex:
        r.update(ok=False, error='%s: %s' % (type(ex).__name__, str(ex)[:300]), trace=traceback.format_exc()[-400:])
    r['secs'] = round(time.time() - t3, 2); kinds[k] = r
    json.dump(kinds, open(J('.kinds.json'), 'w'))
meta['total_s'] = round(time.time() - t0, 1); meta['rss_peak_mb'] = rss(); meta['finished'] = True
json.dump(meta, open(J('.meta.json'), 'w'))
