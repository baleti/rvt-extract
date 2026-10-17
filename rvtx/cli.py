import argparse, json, os, re, sys, time
from . import core, manifest

KINDS = ['families']


def safe(s):
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', s or 'Unnamed').strip(' .') or 'Unnamed'


def main(argv=None):
    ap = argparse.ArgumentParser(prog='rvt-extract', description='Extract families and other content from a Revit project without Revit.')
    ap.add_argument('rvt'); ap.add_argument('--out', default=None, help='output folder')
    ap.add_argument('--only', default=None, help='comma list of output types: ' + ','.join(KINDS))
    ap.add_argument('--list', action='store_true', help='list what can be extracted and exit')
    a = ap.parse_args(argv)
    t0 = time.time()
    prj = core.Project(a.rvt)
    docs, st = core.scan_family_docs(prj)
    entries = []
    for fr in sorted(prj.families(), key=lambda r: r['fields'].get('m_name') or ''):
        if not fr['fields'].get('m_name'): continue
        doc = docs.get(fr['id'])
        entries.append(manifest.family_entry(prj, fr, doc))
    if a.list or not a.out:
        for e in entries:
            print('%-28s %-50s types=%-3d params=%-3d records=%d' % (e['category'], e['name'], len(e['types']), len(e['parameters']), e['embedded_records']))
        print('%d families, %d with embedded document (%.1fs)' % (len(entries), sum(e['embedded_doc'] for e in entries), time.time() - t0), file=sys.stderr)
        return 0
    os.makedirs(a.out, exist_ok=True)
    json.dump({'source': os.path.abspath(a.rvt), 'families': entries, 'scan': st}, open(os.path.join(a.out, 'manifest.json'), 'w'), indent=1, default=str)
    return 0
