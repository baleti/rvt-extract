#!/usr/bin/env python3
"""diskaudit.py OUT_DIR : VM-free audit of an extraction. Every manifest family with an rfa entry must have a readable OLE file on disk,
no *.rfa on disk may be unlisted, no tmp/INCOMPLETE residue. Exit 1 on any finding."""
import sys, os, json, glob, hashlib
import olefile
out = sys.argv[1]
m = json.load(open(os.path.join(out, 'manifest.json')))
bad = []
listed = set()
for f in m['families']:
    r = f.get('rfa')
    p = r.get('file') if isinstance(r, dict) else r
    if not p or (isinstance(r, dict) and r.get('status') != 'written'): continue
    p = p if os.path.isabs(p) else os.path.join(out, p)
    listed.add(os.path.realpath(p))
    if not os.path.isfile(p): bad.append(('missing', p)); continue
    try:
        o = olefile.OleFileIO(p)
        if not o.exists('BasicFileInfo'): bad.append(('no BasicFileInfo', p))
        o.close()
        if isinstance(r, dict) and r.get('sha256') and hashlib.sha256(open(p, 'rb').read()).hexdigest() != r['sha256']: bad.append(('sha256 mismatch', p))
    except Exception as e: bad.append(('unreadable %s' % e, p))
for p in glob.glob(os.path.join(out, '**', '*.rfa'), recursive=True):
    if os.path.realpath(p) not in listed: bad.append(('unlisted', p))
for p in glob.glob(os.path.join(out, '**', '*.tmp*'), recursive=True) + glob.glob(os.path.join(out, '**', 'INCOMPLETE*'), recursive=True):
    bad.append(('residue', p))
for k, p in bad: print(k, p)
print('families', len(m['families']), 'listed rfa', len(listed), 'findings', len(bad))
sys.exit(1 if bad else 0)
