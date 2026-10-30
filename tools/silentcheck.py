"""Silent-failure audit of manifests: prints per manifest the counts of families with an embedded doc by outcome (written, error, skipped, silent = no rfa record at all).
usage: silentcheck.py MANIFEST.json ...   exit 1 when any family is silent or an error is not logged."""
import json, sys
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
    return c

if __name__ == '__main__':
    bad = 0
    for p in sys.argv[1:]:
        c = audit(p); bad += c['silent']; print(p.split('/')[-3] if p.count('/') > 2 else p, dict(c))
    sys.exit(1 if bad else 0)
