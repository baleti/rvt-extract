#!/usr/bin/env python3
"""batch.py LIST.tsv STATEDIR OUTDIR [maxretry] : run batch_one.py per file (id<TAB>path), resumable, crash-tolerant.
A child that dies (OOM, segfault) is retried; the family named in ID.cur is then recorded as crash and skipped."""
import sys, os, json, subprocess, time, resource
lst, sd, od = sys.argv[1:4]; maxr = int(sys.argv[4]) if len(sys.argv) > 4 else 3
LIM = int(float(os.environ.get('BATCH_AS_GB', '7')) * 2**30)  # address-space cap per file: MemoryError instead of a cgroup OOM kill of the whole unit
here = os.path.dirname(os.path.realpath(__file__)); os.makedirs(sd, exist_ok=True)
for l in open(lst):
    if not l.strip(): continue
    fid, path = l.rstrip('\n').split('\t')[:2]
    mj = os.path.join(sd, fid + '.meta.json')
    if os.path.exists(mj) and json.load(open(mj)).get('finished'): continue
    ap = os.path.join(sd, fid + '.attempts'); n = int(open(ap).read()) if os.path.exists(ap) else 0
    if n >= maxr:   # the whole unit was OOM-killed mid-file maxr times: record and move on
        m = json.load(open(mj)) if os.path.exists(mj) else {'id': fid}; m.update(finished=True, failed=True, killed=True); json.dump(m, open(mj, 'w')); continue
    open(ap, 'w').write(str(n + 1))
    for attempt in range(maxr):
        t = time.time(); p = subprocess.run([sys.executable, os.path.join(here, 'batch_one.py'), path, fid, sd, od], preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_AS, (LIM, LIM)), stdout=open(os.path.join(sd, fid + '.log'), 'a'), stderr=subprocess.STDOUT)
        print(fid, 'attempt', attempt, 'rc', p.returncode, '%.0fs' % (time.time() - t), flush=True)
        if p.returncode == 0: break
        cur = os.path.join(sd, fid + '.cur')
        if os.path.exists(cur):
            i = int(open(cur).read()); os.remove(cur)
            open(os.path.join(sd, fid + '.fam.jsonl'), 'a').write(json.dumps({'idx': i, 'status': 'crash', 'error': 'process died rc=%d' % p.returncode}) + '\n')
        else:
            open(os.path.join(sd, fid + '.fam.jsonl'), 'a')
    else:
        m = json.load(open(mj)) if os.path.exists(mj) else {'id': fid}; m.update(finished=True, failed=True); json.dump(m, open(mj, 'w'))
print('BATCHDONE', flush=True)
