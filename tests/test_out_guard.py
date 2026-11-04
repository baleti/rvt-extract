import os, shutil, subprocess, sys, tempfile, unittest, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class OutGuard(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'rvt-extract'), *args], capture_output=True, text=True, timeout=60)

    def test_out_is_input_or_a_file(self):
        d = tempfile.mkdtemp(); src = os.path.join(d, 'p.rvt'); open(src, 'wb').write(b'NOTREALRVT' * 10)
        h = hashlib.sha1(open(src, 'rb').read()).hexdigest()
        for out in (src, os.path.join(d, '.', 'p.rvt')):
            r = self.run_cli('--out', out, src)
            self.assertEqual(r.returncode, 2); self.assertNotIn('Traceback', r.stderr); self.assertIn('--out must', r.stderr)
            self.assertEqual(hashlib.sha1(open(src, 'rb').read()).hexdigest(), h)
        shutil.rmtree(d)
