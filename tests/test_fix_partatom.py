import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools')); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import olefile
import rfa_fix_partatom as F
from rvtx import cfbw

def synth(title):
    st = {e[0]: (b'x%d' % i) * 40 for i, e in enumerate(cfbw.RFA_DIR) if e[1] == 2}
    st['PartAtom'] = b'<?xml version="1.0" encoding="UTF-8"?>\r\n<entry><title>' + title + b'</title><id></id></entry>'
    return st

class T(unittest.TestCase):
    def run_fix(self, title):
        d = tempfile.mkdtemp(); a = os.path.join(d, 'a.rfa'); b = os.path.join(d, 'b.rfa')
        open(a, 'wb').write(cfbw.write_rfa(synth(title))); return a, b, F.main(a, b)

    def test_repair_changes_only_partatom(self):
        a, b, rc = self.run_fix(b'A & B <x> &amp; C')
        self.assertEqual(rc, 0)
        oa, ob = olefile.OleFileIO(a), olefile.OleFileIO(b)
        diff = [e for e in oa.listdir(streams=True) if oa.openstream(e).read() != ob.openstream(e).read()]
        self.assertEqual(diff, [['PartAtom']])
        self.assertIn(b'<title>A &amp; B &lt;x&gt;'.replace(b'&gt;', b'>'), ob.openstream('PartAtom').read())

    def test_fine_file_unchanged_streams(self):
        a, b, rc = self.run_fix(b'Plain'); oa, ob = olefile.OleFileIO(a), olefile.OleFileIO(b)
        self.assertEqual(rc, 0); self.assertTrue(all(oa.openstream(e).read() == ob.openstream(e).read() for e in oa.listdir(streams=True)))

    def test_never_in_place(self):
        a, b, rc = self.run_fix(b'x'); self.assertEqual(F.main(a, a), 2); self.assertEqual(F.main(a, b), 2)

    def test_unexpected_stream_refused_cleanly(self):
        d = tempfile.mkdtemp(); st = synth(b'A & B'); a = os.path.join(d, 'a.rfa'); b = os.path.join(d, 'b.rfa')
        open(a, 'wb').write(cfbw.write_rfa(st))
        orig = F.cfbw.write_rfa
        def boom(*x, **k): raise AssertionError('unexpected stream Foo')
        F.cfbw.write_rfa = boom
        try: rc = F.main(a, b)
        finally: F.cfbw.write_rfa = orig
        self.assertEqual(rc, 2); self.assertFalse(os.path.exists(b))

if __name__ == '__main__': unittest.main()
