#!/usr/bin/env python3
"""Structural scan of extracted rfa (CFB): every stream reads to its declared size, no sector
shared between streams, FAT chains end properly, file length consistent; with --manifest
also checks sha256 of each rfa against the manifest. usage: cfbscan.py OUTDIR [--manifest]"""
import sys, os, glob, struct, hashlib, json
import olefile
def scan(p):
    err = []
    b = open(p, 'rb').read()
    if len(b) % 512 or len(b) < 1536: err.append('len %d' % len(b))
    try: o = olefile.OleFileIO(p)
    except Exception as e: return ['open: %s' % e]
    ss = o.sectorsize; seen = {}
    for s in o.listdir(streams=True, storages=False):
        e = o.direntries[o._find(s) if False else o._find('/'.join(s))]
        try: d = o.openstream(s).read()
        except Exception as ex: err.append('read %s: %s' % (s, ex)); continue
        if len(d) != e.size: err.append('size %s %d!=%d' % (s, len(d), e.size))
        if e.size >= o.minisectorcutoff:
            sec = e.isectStart; n = 0
            while sec < 0xFFFFFFFA and n <= len(o.fat):
                if sec in seen: err.append('shared sector %d: %s %s' % (sec, seen[sec], s)); break
                seen[sec] = '/'.join(s); sec = o.fat[sec]; n += 1
            if sec != 0xFFFFFFFE: err.append('chain end %s %x' % (s, sec))
            if n * ss < e.size: err.append('chain short %s' % (s,))
    if (len(b) - 512) // ss < max(seen, default=-1) + 1: err.append('sector beyond EOF')
    o.close(); return err
def main():
    d = sys.argv[1]; bad = 0; n = 0
    man = {}
    if '--manifest' in sys.argv:
        m = json.load(open(os.path.join(d, 'manifest.json')))
        for f in m.get('families', []):
            r = f.get('rfa') or {}
            if r.get('sha256') and r.get('path'): man[os.path.basename(r['path'])] = r['sha256']
    for p in glob.glob(os.path.join(d, '**', '*.rfa'), recursive=True):
        n += 1; e = scan(p)
        h = man.get(os.path.basename(p))
        if h and h != hashlib.sha256(open(p, 'rb').read()).hexdigest(): e.append('manifest sha mismatch')
        if e: bad += 1; print(os.path.basename(p), e[:3])
    print('scanned', n, 'bad', bad, 'manifest-checked', len(man)); sys.exit(1 if bad else 0)
main()
