#!/usr/bin/env python3
"""tvalcmp.py A_rfacheck.tsv B_rfacheck.tsv : compare TVAL rows (per-type parameter values) of the same-named families; ElementId values (id:) are ignored. Aggregate counts + first mismatches."""
import sys, collections
def load(p):
    d = collections.defaultdict(dict)
    for l in open(p, encoding='utf-8', errors='replace'):
        f = l.rstrip('\n').split('\t')
        if f[0] == 'TVAL' and len(f) >= 5 and not f[4].startswith('id:'): d[f[1]][(f[2], f[3])] = f[4]
    return d
a, b = load(sys.argv[1]), load(sys.argv[2]); same = diff = 0; bad = []
for n in sorted(set(a) & set(b)):
    ka, kb = a[n], b[n]; d = [k for k in set(ka) | set(kb) if ka.get(k) != kb.get(k)]
    if d: diff += 1; bad.append((n, len(d), sorted(d)[:2], [(ka.get(k), kb.get(k)) for k in sorted(d)[:2]]))
    else: same += 1
for x in bad[:15]: print('DIFF', *x)
print('families with TVAL on both sides %d: identical %d, differ %d' % (same + diff, same, diff))
