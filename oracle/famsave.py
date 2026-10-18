#!/usr/bin/env python3
"""oracle/famsave.py YEAR PROJECT.rvt OUTDIR [ONLY,names] : Revit EditFamily+SaveAs of every family (write-lab guest harness; takes the VM lock). Output: OUTDIR/<Category>/<Family>.rfa + index.tsv"""
import sys, os, re, shutil
WL = os.path.expanduser('~/rvt-research/write-lab'); sys.path.insert(0, WL + '/campaign')
import guest
year, f, od = int(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]); only = sys.argv[4] if len(sys.argv) > 4 else ''
base = os.path.basename(f); tag = 'fs_' + re.sub(r'\W', '_', base)[:40]
cs = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'famsave.cs')).read().replace('__FILE__', 'C:/wl/' + tag + '_' + base).replace('__TAG__', tag).replace('__ONLY__', only)
with guest.vmlock():
    guest.put(f, 'C:/wl/' + tag + '_' + base); p = guest.fresh(year); o = guest.run_job(year, p, cs, tag, 3000); print(base, o[-400:].replace('\n', ' '))
    shutil.rmtree(od, ignore_errors=True); os.makedirs(os.path.dirname(od), exist_ok=True); guest.get('C:/wl/out/' + tag, od); guest.down(year)
