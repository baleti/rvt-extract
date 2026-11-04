#!/usr/bin/env python3
"""oracle/famsave_async.py YEAR PROJECT.rvt OUTDIR ONLY,names : like famsave.py, but when the guest harness returns 'running' (280 s script limit) it keeps the VM up and polls for OUT/index.tsv (up to 45 min) before fetching. Takes the VM lock. FS_CS selects the cs (default famsave_det.cs)."""
import sys, os, re, shutil, time
WL = os.path.expanduser('~/rvt-research/write-lab'); sys.path.insert(0, WL + '/campaign')
import guest
year, f, od = int(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]); only = sys.argv[4] if len(sys.argv) > 4 else ''
base = os.path.basename(f); tag = 'fs_' + re.sub(r'\W', '_', base)[:40]
cs = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.environ.get('FS_CS', 'famsave_det.cs'))).read().replace('__FILE__', 'C:/wl/' + tag + '_' + base).replace('__TAG__', tag).replace('__ONLY__', only)
with guest.vmlock():
    try:
        guest.put(f, 'C:/wl/' + tag + '_' + base); p = guest.fresh(year); o = guest.run_job(year, p, cs, tag, 3000); print(base, o[-300:].replace('\n', ' '), flush=True)
        t0 = time.time()
        while time.time() - t0 < 2700:
            if 'True' in guest.script('Test-Path C:/wl/out/%s/index.tsv' % tag, 60): break
            time.sleep(60)
        shutil.rmtree(od, ignore_errors=True); os.makedirs(os.path.dirname(od), exist_ok=True); print('got', guest.get('C:/wl/out/' + tag, od), 'after', int(time.time() - t0), 's', flush=True)
    finally: guest.down(year)
