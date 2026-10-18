"""cmp_checks.py REVIT_GT.tsv LIFTED.tsv [OUT.json] : per-file verdict (opens, facts identical to Revit's own EditFamily+SaveAs rfa)"""
import sys, json, collections
def load(p):
    d = collections.defaultdict(list); fail = {}
    for l in open(p, encoding='utf-8', errors='replace'):
        f = l.rstrip('\n').split('\t')
        if f[0] in ('OPENFAIL',): fail[f[1]] = f[2]; continue
        if len(f) < 3 or f[0] == 'LOAD': continue
        d[f[1]].append(tuple([f[0]] + f[2:]))
    return d, fail
a, af = load(sys.argv[1]); b, bf = load(sys.argv[2])
names = sorted(set(a) | set(af) | set(b) | set(bf)); res = {}
c = collections.Counter()
for n in names:
    if n in bf: v = {'opens': False, 'error': bf[n][:160]}
    elif n not in b: v = {'opens': None, 'error': 'not checked'}
    else:
        A, B = sorted(a.get(n, [])), sorted(b[n])
        if n in af: v = {'opens': True, 'facts': 'revit-gt-failed'}
        elif A == B: v = {'opens': True, 'facts': 'identical'}
        else:
            v = {'opens': True, 'facts': 'differ', 'revit_only': [str(x)[:140] for x in A if x not in B][:6], 'lifted_only': [str(x)[:140] for x in B if x not in A][:6]}
    res[n] = v; c[(v['opens'], v.get('facts'))] += 1
print(dict(c))
if len(sys.argv) > 3: json.dump(res, open(sys.argv[3], 'w'), indent=1)
for n, v in res.items():
    if v.get('facts') == 'differ' or v['opens'] is not True: print(n, v)
