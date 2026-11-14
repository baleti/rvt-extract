import os, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RFA = os.path.expanduser('~/rvt-samples/racbasicsamplefamily-2024.rfa')


@unittest.skipUnless(os.path.exists(RFA), 'needs the Autodesk sample rfa')
class NameTooLong(unittest.TestCase):
    def test_out_component_over_255_is_clean(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'rvt-extract'), RFA, '--out', os.path.join(d, 'x' * 300)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2, r.stderr[-300:])
            self.assertNotIn('Traceback', r.stderr)
            self.assertIn('too long', r.stderr)


if __name__ == '__main__':
    unittest.main()
