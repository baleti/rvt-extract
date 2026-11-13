"""CFB read-write gap: any rfa (ours or Revit-saved) read with olefile and rewritten through cfbw.write_rfa keeps every stream payload
byte-identical and the same stream set. Opt-in: RVTX_RFA_DIR=<dir with .rfa> (searched recursively, first 60 used)."""
import os, sys, glob, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
D = os.environ.get('RVTX_RFA_DIR')


@unittest.skipUnless(D and os.path.isdir(D), 'set RVTX_RFA_DIR')
class T(unittest.TestCase):
    def test_streams_survive_rewrite(self):
        import olefile
        from rvtx import cfbw
        files = sorted(glob.glob(os.path.join(D, '**', '*.rfa'), recursive=True))[:60]
        self.assertTrue(files)
        for p in files:
            o = olefile.OleFileIO(p); names = ['/'.join(e) for e in o.listdir(streams=True)]
            st = {n: o.openstream(n).read() for n in names}; o.close()
            part = next(n for n in names if n.startswith('Partitions/'))
            q = olefile.OleFileIO(cfbw.write_rfa(st, part))
            self.assertEqual(sorted('/'.join(e) for e in q.listdir(streams=True)), sorted(names), p)
            for n in names: self.assertEqual(q.openstream(n).read(), st[n], (p, n))


if __name__ == '__main__':
    unittest.main()
