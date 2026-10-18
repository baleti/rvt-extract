#!/usr/bin/env python3
"""report.py STATEDIR [rfacheck.tsv...] : anonymised results table (no names/paths) + failure causes by normalised error. Light: reads small json only."""
import sys, os, json, glob, re, collections
sd = sys.argv[1]
def norm(e): return re.sub(r'\d+', 'N', (e or '')[:100])
rows = []; causes = collections.Counter(); kcauses = collections.Counter(); kstat = collections.defaultdict(lambda: [0, 0, 0])
for mj in sorted(glob.glob(os.path.join(sd, '*.meta.json'))):
    m = json.load(open(mj)); fid = m['id']; fj = os.path.join(sd, fid + '.fam.jsonl')
    fam = [json.loads(l) for l in open(fj)] if os.path.exists(fj) else []
    emb = [f for f in fam if f['status'] != 'no-embedded-doc']; ok = [f for f in emb if f['status'] == 'written']
    for f in emb:
        if f['status'] != 'written': causes[norm(f.get('error'))] += 1
    kj = os.path.join(sd, fid + '.kinds.json'); k = json.load(open(kj)) if os.path.exists(kj) else {}
    for n, v in k.items():
        kstat[n][0] += 1
        if not v['ok']: kstat[n][1] += 1; kcauses[(n, norm(v.get('error')))] += 1
        elif not v.get('count'): kstat[n][2] += 1
    rows.append((fid, m.get('year'), m.get('size', 0) // 2**20, len(fam), len(emb), len(ok), sum(1 for v in k.values() if not v['ok']), m.get('total_s'), m.get('rss_peak_mb'), 'FAILED' if m.get('failed') else ''))
print('| file | year | MB | families | embedded | .rfa built | kinds failed | s | peak MB | note |\n|---|---|---|---|---|---|---|---|---|---|')
for r in rows: print('| ' + ' | '.join(str(x) for x in r) + ' |')
te = sum(r[4] for r in rows); tb = sum(r[5] for r in rows)
print('\nfiles %d, embedded families %d, built %d (%.1f%%)' % (len(rows), te, tb, 100 * tb / max(te, 1)))
print('\nby year:'); by = collections.defaultdict(lambda: [0, 0, 0])
for r in rows: by[r[1]][0] += 1; by[r[1]][1] += r[4]; by[r[1]][2] += r[5]
for y, v in sorted(by.items(), key=lambda t: str(t[0])): print(' ', y, 'files', v[0], 'embedded', v[1], 'built', v[2])
print('\nfamily failure causes:')
for c, n in causes.most_common(25): print(' %5d  %s' % (n, c))
print('\nextractor kinds (files run, crashed, empty):')
for n, v in kstat.items(): print(' %-20s %s' % (n, v))
for (n, c), x in kcauses.most_common(15): print(' %4d %s: %s' % (x, n, c))
