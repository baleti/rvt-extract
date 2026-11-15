#!/usr/bin/env python3
"""rfa_streamaudit.py DIR [DIR...] : VM-free structural audit of every .rfa below the directories (public-sample or local runs; prints aggregate counts and short ids only).
Checks per file: OLE opens; PartAtom parses as XML; TransmissionData = 4-byte length + UTF-16 XML that parses and whose length matches; the first gzip member of Contents and Partitions/* decompresses completely (CRC valid); BasicFileInfo non-empty. Exit 1 on any finding."""
import re, sys, os, glob, zlib, struct
import xml.etree.ElementTree as ET
import olefile


def members(data):
    n = 0
    while data:
        if data[:2] != b'\x1f\x8b': return n, 'trailing non-gzip bytes (%d)' % len(data)
        d = zlib.decompressobj(31)
        try: d.decompress(data)
        except zlib.error as e: return n, 'gzip error %s' % e
        if not d.eof: return n, 'truncated gzip member'
        data = d.unused_data; n += 1
    return n, None


def audit(f):
    bad = []
    try: o = olefile.OleFileIO(f)
    except Exception as e: return ['ole: %s' % e]
    try:
        names = {'/'.join(x) for x in o.listdir()}
        try: ET.fromstring(o.openstream('PartAtom').read())
        except Exception as e: bad.append('PartAtom xml: %s' % e)
        t = o.openstream('TransmissionData').read() if 'TransmissionData' in names else b''
        try:
            n = struct.unpack('<I', t[:4])[0]
            if n * 2 != len(t) - 4: bad.append('TransmissionData length %d chars vs %d bytes' % (n, len(t) - 4))
            ET.fromstring(t[4:].decode('utf-16le').lstrip('﻿'))
        except Exception as e: bad.append('TransmissionData: %s' % e)
        bfi = o.openstream('BasicFileInfo').read()
        if not bfi: bad.append('BasicFileInfo empty')
        elif re.search(r'(?:[/\\]home[/\\]|[A-Za-z]:[/\\])', bfi.decode('utf-16le', 'replace')): bad.append('BasicFileInfo carries an absolute host path (pre-fix output: re-lift)')
        for s in sorted(names):
            if s == 'Contents' or s.startswith('Partitions/'):
                d = o.openstream(s).read(); i = d.find(b'\x1f\x8b\x08')      # a short header precedes the gzip data
                if i < 0: bad.append('%s: no gzip member' % s); continue
                z = zlib.decompressobj(31)
                try: z.decompress(d[i:])
                except zlib.error as e: bad.append('%s: gzip error %s' % (s, e)); continue
                if not z.eof: bad.append('%s: truncated gzip member' % s)
    finally: o.close()
    return bad


if __name__ == '__main__':
    files = [f for d in sys.argv[1:] for f in glob.glob(os.path.join(d, '**', '*.rfa'), recursive=True)]
    nbad = 0
    for f in sorted(files):
        b = audit(f)
        if b: nbad += 1; print('FINDING', os.path.basename(f)[:40], '; '.join(b)[:200])
    print('rfa %d, with findings %d' % (len(files), nbad)); sys.exit(1 if nbad else 0)
