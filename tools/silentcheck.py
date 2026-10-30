"""Silent-failure audit of manifests: prints per manifest the counts of families with an embedded doc by outcome (written, error, skipped, silent = no rfa record at all).
usage: silentcheck.py MANIFEST.json ...   exit 1 when any family is silent or an error is not logged."""
import json, os, sys
from collections import Counter

def audit(path):
    m = json.load(open(path)); fs = m['families'] if isinstance(m, dict) else m
    c = Counter()
    for f in fs:
        if not f.get('embedded_doc'): c['no_doc'] += 1; continue
        r = f.get('rfa')
        if not r: c['silent'] += 1
        else: c[r.get('status', 'silent')] += 1
        if r and r.get('known_bad'): c['known_bad'] += 1
        if r and r.get('status') == 'written':      # file must exist, be non-empty and an OLE compound file
            fp = os.path.join(os.path.dirname(path), r.get('file', ''))
            try:
                with open(fp, 'rb') as fh: ok = fh.read(8) == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
            except OSError: ok = False
            if not ok: c['missing_or_bad_file'] += 1
    listed = {os.path.normpath(f['rfa']['file']) for f in fs if f.get('rfa') and f['rfa'].get('file')}
    root = os.path.join(os.path.dirname(path), 'families')
    for dp, _d, fns in os.walk(root):
        for fn in fns:
            rel = os.path.normpath(os.path.relpath(os.path.join(dp, fn), os.path.dirname(path)))
            if fn.endswith('.rfa') and rel not in listed: c['orphan_file'] += 1      # stale output of an earlier run, or a leftover of a failed write
            elif '.tmp' in fn: c['leftover_tmp'] += 1
    return c

if __name__ == '__main__':
    bad = 0
    for p in sys.argv[1:]:
        c = audit(p); bad += c['silent'] + c['missing_or_bad_file'] + c['orphan_file'] + c['leftover_tmp']; print(p.split('/')[-3] if p.count('/') > 2 else p, dict(c))
    sys.exit(1 if bad else 0)
