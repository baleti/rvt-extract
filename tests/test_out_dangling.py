import os, subprocess, sys, tempfile, unittest

class Dangling(unittest.TestCase):
    def test_dangling_symlink_out_is_refused_cleanly(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, 's.rvt'); open(src, 'wb').write(b'x' * 100)
            out = os.path.join(d, 'o'); os.symlink(os.path.join(d, 'nowhere'), out)
            r = subprocess.run([sys.executable, os.path.join(root, 'bin', 'rvt-extract'), src, '--out', out], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2, r.stderr[-300:])
            self.assertNotIn('Traceback', r.stderr)
            self.assertIn('symlink', r.stderr)

if __name__ == '__main__':
    unittest.main()
