#!/usr/bin/env python3
"""gtcmp.py GT_INDEX.tsv RFACHECK.tsv [...] : compare Revit-read facts of extracted rfa (oracle/rfacheck.py output) with the index of Revit's own EditFamily+SaveAs (gt_fam/<tag>/index.tsv: OK id category name types= params= forms= refplanes= ...).
Per family (matched by file stem = family name): types, params, refplanes equal? Prints counts and every mismatch; aggregate only."""
import sys, os, re, collections
gt = {}
for l in open(sys.argv[1], encoding='utf-8', errors='replace'):
    f = l.rstrip('\n').split('\t')
    if f[0] != 'OK' or len(f) < 8: continue
    kv = dict(x.split('=', 1) for x in f[4:] if '=' in x)
    v = {k: int(kv[k]) for k in ('types', 'params', 'refplanes') if k in kv}
    gt[f[3]] = v; gt[f[2] + '__' + f[3]] = v     # flat output names are Category__Name
got = collections.defaultdict(collections.Counter); openok = {}
for p in sys.argv[2:]:
    for l in open(p, encoding='utf-8', errors='replace'):
        f = l.rstrip('\n').split('\t')
        if len(f) < 2: continue
        n = re.sub(r'\.rfa$', '', f[1])
        if f[0] == 'OPEN': openok[n] = 'isFam=True' in l
        elif f[0] == 'TYPE': got[n]['types'] += 1
        elif f[0] == 'PARAM': got[n]['params'] += 1
        elif f[0] == 'REFPLANE': got[n]['refplanes'] += 1
same = diff = nogt = bad = 0
for n, ok in sorted(openok.items()):
    if not ok: bad += 1; print('NOTFAMILY', n); continue
    g = gt.get(n) or gt.get(n.split('__', 1)[-1])
    if g is None: nogt += 1; continue
    d = {k: (got[n][k], v) for k, v in g.items() if got[n][k] != v}
    if d: diff += 1; print('DIFF', n, d)
    else: same += 1
print('opened %d, not-family %d, no ground truth %d, identical %d, differ %d' % (len(openok), bad, nogt, same, diff))
