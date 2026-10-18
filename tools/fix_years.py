#!/usr/bin/env python3
"""fix_years.py STATEDIR LIST.tsv : rewrite meta.json year from the project's BasicFileInfo leading year (run on remote-host, reads a few KB per file)"""
import sys, os, json, re, olefile
sd, lst = sys.argv[1:3]
for l in open(lst):
    fid, path = l.rstrip('\n').split('\t')[:2]; mj = os.path.join(sd, fid + '.meta.json')
    try:
        o = olefile.OleFileIO(path); b = o.openstream('BasicFileInfo').read().decode('utf-16le', 'ignore'); o.close()
        m = re.match(r'\s*(20[12]\d)\b', b); y = int(m.group(1)) if m else None
    except Exception: y = None
    m = json.load(open(mj)) if os.path.exists(mj) else {'id': fid}; m['year'] = y; json.dump(m, open(mj, 'w'))
