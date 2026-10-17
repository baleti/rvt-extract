import argparse, json, os, re, sys, time
from . import core, manifest, items, files

KINDS = ['families'] + list(items.KINDS) + list(files.KINDS)
HELP = {'families': 'every family: manifest entry (category, types, parameters, embedded-record census); .rfa when validation passes',
        'fill_patterns': 'fill patterns (drafting/model, grid lines)', 'line_patterns': 'line patterns (dash/space/dot segments)',
        'shared_parameters': 'shared parameters as manifest + shared_parameters.txt', 'project_parameters': 'project parameters with category bindings',
        'filters': 'view filters (categories, rules)', 'phases': 'phases, phase filters, design options', 'levels_grids': 'levels with elevations, grids, named reference planes',
        'views': 'views, view templates, sheets with placed views', 'images': 'embedded raster images (PNG/JPEG blobs)', 'project_info': 'file/build info, project information, preview.png',
        'links': 'external file references (links, keynote tables) from TransmissionData', 'materials': 'materials with appearance assets and textures (paths)'}


def safe(s):
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', s or 'Unnamed').strip(' .') or 'Unnamed'


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(data, open(path, 'w'), indent=1, default=str)


def main(argv=None):
    ap = argparse.ArgumentParser(prog='rvt-extract', description='Extract families and other content from a Revit project without Revit.')
    ap.add_argument('rvt'); ap.add_argument('--out', default=None, help='output folder')
    ap.add_argument('--only', default=None, help='comma list of output types (see --list-kinds): ' + ','.join(KINDS))
    ap.add_argument('--list', action='store_true', help='print what the file contains and exit')
    ap.add_argument('--list-kinds', action='store_true', help='print the output types and exit')
    a = ap.parse_args(argv)
    if a.list_kinds:
        for k in KINDS: print('%-20s %s' % (k, HELP.get(k, '')))
        return 0
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
            if fr['fields'].get('m_name'): ents.append(manifest.family_entry(prj, fr, docs.get(fr['id'])))
        res['families'] = ents
        if a.list or not a.out:
            for e in ents: print('%-28s %-50s types=%-3d params=%-3d records=%d' % (e['category'], e['name'], len(e['types']), len(e['parameters']), e['embedded_records']))
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
    for k, v in res.items():
        if k == 'families': continue
        data, fl = v
        write_json(os.path.join(a.out, k, k + '.json'), data)
        for rel, b in fl:
            fp = os.path.join(a.out, k, rel); os.makedirs(os.path.dirname(fp), exist_ok=True); open(fp, 'wb').write(b)
    write_json(os.path.join(a.out, 'manifest.json'), man)
    open(os.path.join(a.out, 'extract.log'), 'w').write('\n'.join(log) + '\n')
    return 0
