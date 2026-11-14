import os, subprocess, sys, tempfile, unittest

SRC = os.path.expanduser('~/rvt-research/corpus/2022/30_rst_basic_sample_project.rvt')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@unittest.skipUnless(os.path.exists(SRC), 'public 2022 rst_basic sample not present')
class T(unittest.TestCase):
    def test_zero_match_warns(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'rvt-extract'), SRC, '--out', os.path.join(d, 'o'), '--only', 'families', '--match', 'zzzz_no_such_family'], capture_output=True, text=True, timeout=300)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('matched 0 families', r.stderr)
