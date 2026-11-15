#!/usr/bin/env python3
"""rfa_fix_basicfileinfo.py IN.rfa OUT.rfa: strip a lift path (absolute or relative) from the filename in BasicFileInfo, leaving the bare file name.
Pre-2026-11-04 lifts embedded e.g. 'lift_big/BIG009/families/Generic Models/X.rfa'. Only BasicFileInfo is changed; every other stream is copied byte for byte and the file is
re-assembled with rvtx.cfbw. OUT must be a new file (never in place). rc 0 = written and read back, 1 = nothing to fix, 2 = refused."""
import sys, os, re, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import olefile
from rvtx import cfbw

PATH = re.compile(r'((?:[A-Za-z]:)?(?:[^\x00-\x1f|/\\]+[/\\])+)([^\x00-\x1f|/\\]+\.rfa)')


def fix(b):
    """BasicFileInfo bytes -> (new bytes, number of replacements); the name is stored as u32 char count + UTF-16LE"""
    out = bytearray(); pos = 0; n = 0
    for a in (0, 1):                       # the string is not always 2-byte aligned in the stream
        t = b[a:len(b) - ((len(b) - a) % 2)].decode('utf-16le', 'replace')
        if PATH.search(t): break
    else: return b, 0
    for m in PATH.finditer(t):
        full = m.group(0).encode('utf-16le'); bare = m.group(2).encode('utf-16le')
        k = b.find(struct.pack('<I', len(m.group(0))) + full, pos)
        if k < 0: continue
        out += b[pos:k] + struct.pack('<I', len(m.group(2))) + bare; pos = k + 4 + len(full); n += 1
    out += b[pos:]
    return bytes(out), n


def main(a, b):
    if os.path.abspath(a) == os.path.abspath(b) or os.path.exists(b): print('refused: OUT must be a new file'); return 2
    try:
        o = olefile.OleFileIO(a)
        st = {'/'.join(e): o.openstream('/'.join(e)).read() for e in o.listdir(streams=True)}; o.close()
    except Exception as x: print('refused: unreadable (%s)' % x); return 2
    part = [k for k in st if k.startswith('Partitions/')]
    if 'BasicFileInfo' not in st or len(part) != 1: print('refused: unexpected stream layout'); return 2
    new, n = fix(st['BasicFileInfo'])
    if not n: print('nothing to fix'); return 1
    st['BasicFileInfo'] = new
    try: data = cfbw.write_rfa(st, part[0])
    except AssertionError as x: print('refused: %s' % x); return 2
    tmp = b + '.tmp%d' % os.getpid()
    open(tmp, 'wb').write(data); os.replace(tmp, b)
    o2 = olefile.OleFileIO(b)
    for k, v in st.items():
        if o2.openstream(k).read() != v: print('refused: readback mismatch ' + k); os.remove(b); return 2
    return 0


if __name__ == '__main__': sys.exit(main(sys.argv[1], sys.argv[2]))
