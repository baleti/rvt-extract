"""Years x class table: lifted .rfa per class (flat, parent with nested families, nested depth>=2, standalone copy of a nested family) vs opens-in-Revit.
usage: yeartable.py YEAR=out/all/YEAR[:out/chk/dirA,out/chk/dirB] ...   (rfacheck.tsv OPEN lines give the opened file names)"""
import json, os, sys
from collections import Counter

def row(root, chks):
    m = json.load(open(os.path.join(root, 'families', 'manifest.json')))
    fs = m['families'] if isinstance(m, dict) else m
    opened = set()
    for c in chks:
        p = os.path.join(c, 'rfacheck.tsv')
        if os.path.exists(p):
            for l in open(p, encoding='utf-8', errors='replace'):
                t = l.rstrip('\n').split('\t')
                if t[0] == 'OPEN' and len(t) > 1: opened.add(t[1])
    c = Counter()
    for f in fs:
        r = f.get('rfa') or {}
        if r.get('status') != 'written': c['no_rfa'] += 1; continue
        k = 'standalone_nested' if str(f.get('origin', '')).startswith('nested') else ('depth2' if r.get('nested_depth', 0) >= 2 else ('parent_with_nested' if r.get('nested') else 'flat'))
        c[k + '_lifted'] += 1
        if os.path.basename(r['file']) in opened or os.path.relpath(r['file'], 'families').replace('/', '_').replace(' ', '_') in opened: c[k + '_open'] += 1
    return c

if __name__ == '__main__':
    cls = ['flat', 'parent_with_nested', 'depth2', 'standalone_nested']
    print('year\t' + '\t'.join(k + ' open/lifted' for k in cls) + '\tno_rfa')
    for a in sys.argv[1:]:
        y, _, rest = a.partition('=')
        root, _, ch = rest.partition(':')
        c = row(root, ch.split(',') if ch else [])
        print(y + '\t' + '\t'.join('%d/%d' % (c[k + '_open'], c[k + '_lifted']) for k in cls) + '\t%d' % c['no_rfa'])
