#!/usr/bin/env python3
"""fix_years.py STATEDIR LIST.tsv : rewrite meta.json year from the project's BasicFileInfo leading year (run on remote-host, reads a few KB per file)"""
import sys, os, json, re, olefile
sd, lst = sys.argv[1:3]
def basic_year(raw):
    import re
    for off in (0, 1):
        b = raw[off:].decode('utf-16le', 'ignore')
        m = re.search(r'Format:\s*(20[12]\d)', b) or re.search(r'Autodesk Revit (20[12]\d)', b)
        if m: return int(m.group(1))
    m = re.search(r'(20[12]\d)', raw[:40].decode('utf-16le', 'ignore'))
    return int(m.group(1)) if m else None
for l in open(lst):
    fid, path = l.rstrip('\n').split('\t')[:2]; mj = os.path.join(sd, fid + '.meta.json')
    try:
        o = olefile.OleFileIO(path); b = o.openstream('BasicFileInfo').read(); o.close()
        y = basic_year(b)
    except Exception: y = None
    m = json.load(open(mj)) if os.path.exists(mj) else {'id': fid}; m['year'] = y; json.dump(m, open(mj, 'w'))
