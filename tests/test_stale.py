import os, tempfile, shutil, unittest
from rvtx import safepath


class T(unittest.TestCase):
    def test_stale(self):
        t = tempfile.mkdtemp()
        try:
            for n in ('A/new.rfa', 'A/old.rfa', 'B/x.txt'):
                os.makedirs(os.path.join(t, 'families', os.path.dirname(n)), exist_ok=True); open(os.path.join(t, 'families', n), 'wb').write(b'x')
            fam = [{'rfa': {'file': os.path.join('families', 'A', 'new.rfa')}}, {'rfa': None}]
            self.assertEqual(safepath.stale_rfa(t, fam), [os.path.join('families', 'A', 'old.rfa')])
            self.assertEqual(safepath.stale_rfa(t, []), [os.path.join('families', 'A', 'new.rfa'), os.path.join('families', 'A', 'old.rfa')])
        finally:
            shutil.rmtree(t)


if __name__ == '__main__':
    unittest.main()
