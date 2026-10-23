import argparse, gc, json, os, re, sys, time
from . import core, manifest, items, files, safepath

KINDS = ['families'] + list(items.KINDS) + list(files.KINDS)
HELP = {'families': 'every family: manifest entry (category, types, parameters, embedded-record census); .rfa when validation passes',
        'fill_patterns': 'fill patterns (drafting/model, grid lines)', 'line_patterns': 'line patterns (dash/space/dot segments)',
        'shared_parameters': 'shared parameters as manifest + shared_parameters.txt', 'project_parameters': 'project parameters with category bindings',
        'filters': 'view filters (categories, rules)', 'phases': 'phases, phase filters, design options', 'levels_grids': 'levels with elevations, grids, named reference planes',
        'views': 'views, view templates, sheets with placed views', 'images': 'embedded raster images (PNG/JPEG blobs)', 'project_info': 'file/build info, project information, preview.png',
        'links': 'external file references (links, keynote tables) from TransmissionData', 'schedules': 'schedule views (columns, headers, category) and legend names', 'revisions': 'project revisions', 'line_styles': 'line styles (pattern, pen number, colour)', 'worksets': 'worksets (id, name, kind, default visibility)', 'cad_imports': 'imported/linked CAD files (name, units, size, layers)', 'materials': 'materials with appearance assets and textures (paths)'}


VALIDATION = {'2024': 'validated: opens in Revit 2024, facts equal to EditFamily+SaveAs (Snowdon 177/177, office project 100/100)',
              '2025': 'partly validated: 29 of 34 sampled families of one office project open in Revit 2026 (upgrade); families containing nested families (5 of 5 sampled) are rejected, do not rely on those',
              '2026': 'streams byte-identical to Revit 2026 output for tested families; open check pending'}


def safe(s):
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', s or 'Unnamed').strip(' .') or 'Unnamed'


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(data, open(path, 'w'), indent=1, default=str)


def main(argv=None):
    ap = argparse.ArgumentParser(prog='rvt-extract', description='Extract families and other content from a Revit project without Revit.')
    ap.add_argument('rvt', nargs='?'); ap.add_argument('--out', default=None, help='output folder')
    ap.add_argument('--only', default=None, help='comma list of output types (see --list-kinds): ' + ','.join(KINDS))
    ap.add_argument('--no-rfa', action='store_true', help='families: only the manifest, do not assemble .rfa files')
    ap.add_argument('--experimental', action='store_true', help='also write .rfa for Revit formats known to be rejected by Revit (2017-2023, 4-byte element ids)')
    ap.add_argument('--match', default=None, help='families: only those whose name or category matches this regular expression (case-insensitive)')
    ap.add_argument('--list', action='store_true', help='print what the file contains and exit')
    ap.add_argument('--list-kinds', action='store_true', help='print the output types and exit')
    a = ap.parse_args(argv)
    if a.list_kinds:
        for k in KINDS: print('%-20s %s' % (k, HELP.get(k, '')))
        return 0
    if not a.rvt: ap.error('rvt file required')
    only = [k.strip() for k in a.only.split(',')] if a.only else KINDS
    bad = [k for k in only if k not in KINDS]
    if bad: ap.error('unknown output type(s): %s' % ','.join(bad))
    t0 = time.time()
    prj = core.Project(a.rvt)
    log = []
    res = {}
    if 'families' in only:
        docs, st = core.scan_family_docs(prj)
        ents = []
        for fr in sorted(prj.families(), key=lambda r: r['fields'].get('m_name') or ''):
            if fr['fields'].get('m_name') and (not a.match or re.search(a.match, fr['fields']['m_name'] + ' ' + (manifest.family_entry(prj, fr, docs.get(fr['id']))['category'] or ''), re.I)): ents.append(manifest.family_entry(prj, fr, docs.get(fr['id'])))
        res['families'] = ents
        if a.list or not a.out:
            for e in ents: print('%-28s %-50s types=%-3d params=%-3d records=%d' % (e['category'], e['name'], len(e['types']), len(e['parameters']), e['embedded_records']))
    if 'families' in only and a.out and not a.no_rfa and not a.list:
        from . import rfa as RFA
        pd = RFA.ProjectDocs(prj); B = RFA.Builder(pd); byid = {e['family_id']: e for e in res['families']}; namer = safepath.Namer()
        for fr in prj.families():
            e = byid.get(fr['id'])
            if e is None or not e['embedded_doc']: continue
            if str(pd.fmt).isdigit() and int(pd.fmt) < 2024 and not a.experimental:
                e['rfa'] = {'status': 'skipped', 'validation': 'Revit %s files: .rfa assembly is not validated (Revit rejects it); use --experimental to write anyway' % pd.fmt}; continue
            try:
                B.build(fr)
                d = os.path.join(a.out, 'families', safepath.safe_name(e['category'])); os.makedirs(d, exist_ok=True); fn = os.path.join(d, namer.take(d, e['name'], '.rfa'))
                B.write(fn, e['name'], e['category']); B.last_trees = None; gc.collect(); nest = bool(B.nested_docs(B.k)); e['rfa'] = {'nested': nest, 'file': os.path.relpath(fn, a.out), 'status': 'written', 'validation': ('known-bad: nested families in a 2025 file are rejected by Revit 2026' if nest and str(pd.fmt) == '2025' else VALIDATION.get(str(pd.fmt), 'experimental: this Revit format is not validated yet (see RESULTS.md)'))}
            except Exception as ex:
                e['rfa'] = {'status': 'error', 'error': '%s: %s' % (type(ex).__name__, ex)}; log.append('%s: rfa failed: %s' % (e['name'], ex))
    for k in only:
        if k == 'families': continue
        try:
            fn = items.KINDS.get(k)
            data, fl = fn(prj) if fn else files.KINDS[k](a.rvt)
            res[k] = (data, fl)
        except Exception as e:
            log.append('%s: FAILED %s: %s' % (k, type(e).__name__, e)); res[k] = ([], [])
    summary = {k: (len(v) if k == 'families' else len(v[0]) if hasattr(v[0], '__len__') else 1) for k, v in res.items()}
    print('; '.join('%s=%s' % kv for kv in summary.items()) + ' (%.1fs)' % (time.time() - t0), file=sys.stderr)
    for l in log: print(l, file=sys.stderr)
    if a.list or not a.out: return 0
    os.makedirs(a.out, exist_ok=True)
    man = {'source': os.path.abspath(a.rvt), 'outputs': summary, 'errors': log}
    if 'families' in res:
        man['families'] = res['families']
        write_json(os.path.join(a.out, 'families', 'manifest.json'), res['families'])
        import csv
        for e in res['families']:      # type catalogue (Revit family type catalog .txt: ,Param##type##unit headers, one row per type); only named, non-element-id values
            if not e['types']: continue
            cols = sorted({k for t in e['types'] for k, v in t['values'].items() if not k.startswith('Param(') and not isinstance(v['value'], dict) and not v.get('instance')})
            rf = (e.get('rfa') or {}).get('file')      # Revit looks for the catalog next to the .rfa with the same base name
            base = os.path.join(a.out, os.path.splitext(rf)[0]) if rf else os.path.join(a.out, 'families', safepath.safe_name(e['category']), safe(e['name']))
            os.makedirs(os.path.dirname(base), exist_ok=True)
            with open(base + '.txt', 'w', encoding='utf-8') as fh:
                fh.write(','.join([''] + [c.replace(',', ' ') + '##other##' for c in cols]) + '\n')
                for t in e['types']: fh.write(','.join([t['name'].replace(',', ' ')] + [str(t['values'].get(c, {}).get('value', '')) for c in cols]) + '\n')
        import csv
        with open(os.path.join(a.out, 'families', 'families.csv'), 'w', newline='') as fh:      # one row per family for auditing / standards checks
            w = csv.writer(fh); w.writerow(['category', 'name', 'types', 'parameters', 'shared', 'in_place', 'embedded_records', 'nested', 'rfa_status', 'rfa_file', 'validation'])
            for e in res['families']:
                r = e.get('rfa') or {}
                w.writerow([e['category'], e['name'], len(e['types']), len(e['parameters']), e.get('shared'), e.get('in_place'), e['embedded_records'], r.get('nested', ''), r.get('status', 'no-embedded-doc' if not e['embedded_doc'] else ''), r.get('file', ''), r.get('validation', '')])
    for k, v in res.items():
        if k == 'families': continue
        data, fl = v
        write_json(os.path.join(a.out, k, k + '.json'), data)
        for rel, b in fl:
            fp = os.path.join(a.out, k, rel); os.makedirs(os.path.dirname(fp), exist_ok=True); open(fp, 'wb').write(b)
    write_json(os.path.join(a.out, 'manifest.json'), man)
    open(os.path.join(a.out, 'extract.log'), 'w').write('\n'.join(log) + '\n')
    return 0
