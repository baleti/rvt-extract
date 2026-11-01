#!/usr/bin/env python3
"""oracle/rfajournal.py (rfacheck + Revit journal tail saved to OUT_DIR/journal.txt, for files that hang) -- based on oracle/rfacheck.py YEAR RFA_DIR OUT_DIR : open every .rfa (flat or nested dirs are flattened) in Revit YEAR, report facts and LoadFamily into a new project -> OUT_DIR/rfacheck.tsv (write-lab harness, takes the VM lock)"""
import sys, os, re, shutil, glob, subprocess
WL = os.path.expanduser('~/rvt-research/write-lab'); sys.path.insert(0, WL + '/campaign')
import guest
year, src, od = int(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
tag = 'rc_' + re.sub(r'\W', '_', os.path.basename(src.rstrip('/')))[:30]
files = sorted(glob.glob(os.path.join(src, '**', '*.rfa'), recursive=True))
if os.environ.get('RFA_SLICE'): tag += '_' + os.environ['RFA_SLICE'].replace(':', '_')   # fresh guest dir per slice (a reused dir kept the first slice's files)
if os.environ.get('RFA_SLICE'):
    a, b = os.environ['RFA_SLICE'].split(':'); files = files[int(a):int(b)]
cs = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rfacheck.cs')).read().replace('__DIR__', 'C:/wl/in_' + tag).replace('__TAG__', tag).replace('__LOAD__', os.environ.get('RFA_LOAD', '0')).replace('__FAILH__', 'false' if os.environ.get('RFA_FAILH') == '0' else 'true').replace('__AUDIT__', 'true' if os.environ.get('RFA_AUDIT') == '1' else 'false')
with guest.vmlock():
    guest.script("Remove-Item -Recurse -Force C:/wl/in_%s -ErrorAction SilentlyContinue; New-Item -ItemType Directory -Force C:/wl/in_%s | Out-Null" % (tag, tag))
    for f in files: guest.put(f, 'C:/wl/in_%s/%s' % (tag, os.path.relpath(f, src).replace(os.sep, '__') if os.environ.get('RFA_FLAT') else os.path.basename(f)))
    p = guest.fresh(year); o = guest.run_job(year, p, cs, tag, 2400); print(len(files), 'files', o[-400:].replace('\n', ' ')); import time; time.sleep(int(os.environ.get('JW', '0'))); jt = guest.journal_tail(year, int(os.environ.get('JN', '120')))
    shutil.rmtree(od, ignore_errors=True); os.makedirs(os.path.dirname(od), exist_ok=True); guest.get('C:/wl/out/' + tag, od); open(os.path.join(od, 'journal.txt'), 'w').write(jt if isinstance(jt, str) else str(jt)); guest.down(year)
