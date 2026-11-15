"""rfa_fix_partatom.py IN.rfa OUT.rfa : repair an rfa written before the PartAtom XML-escape fix (raw '&' or '<' in a title).
Only PartAtom is changed; every other stream is copied byte for byte and the file is re-assembled with rvtx.cfbw (the writer that produced it).
Never writes in place (OUT must differ from IN, must not exist). Exit 0 fixed or already fine (OUT written either way), 2 refused."""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import olefile
import xml.dom.minidom as M
from rvtx import cfbw

BARE = re.compile(rb'&(?!(?:amp|lt|gt|quot|apos|#[0-9]+|#x[0-9A-Fa-f]+);)')

def fix_partatom(d):
    """bytes -> repaired bytes (unchanged if already well-formed). Raises ValueError if still not well-formed."""
    try: M.parseString(d); return d
    except Exception: pass
    e = BARE.sub(b'&amp;', d)
    m = re.search(rb'<title>(.*?)</title>', e, re.S)
    if m: e = e[:m.start(1)] + m.group(1).replace(b'<', b'&lt;') + e[m.end(1):]
    try: M.parseString(e)
    except Exception as x: raise ValueError('PartAtom still not well-formed: %s' % x)
    return e

def main(a, b):
    if os.path.abspath(a) == os.path.abspath(b) or os.path.exists(b): print('refused: OUT must be a new file'); return 2
    o = olefile.OleFileIO(a)
    st = {'/'.join(e): o.openstream('/'.join(e)).read() for e in o.listdir(streams=True)}; o.close()
    part = [k for k in st if k.startswith('Partitions/')]
    if 'PartAtom' not in st or len(part) != 1: print('refused: unexpected stream layout'); return 2
    st['PartAtom'] = fix_partatom(st['PartAtom'])
    data = cfbw.write_rfa(st, part[0]); tmp = b + '.tmp%d' % os.getpid()
    open(tmp, 'wb').write(data); os.replace(tmp, b)
    o2 = olefile.OleFileIO(b)
    for k, v in st.items():
        if o2.openstream(k).read() != v: print('refused: readback mismatch ' + k); os.remove(b); return 2
    return 0

if __name__ == '__main__': sys.exit(main(sys.argv[1], sys.argv[2]))
