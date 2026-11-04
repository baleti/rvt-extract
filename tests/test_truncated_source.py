import os, subprocess, sys, tempfile, unittest, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.environ.get('RVTX_SAMPLE_RVT')  # any real rvt; opt-in


@unittest.skipUnless(SAMPLE and os.path.exists(SAMPLE), 'set RVTX_SAMPLE_RVT')
class Truncated(unittest.TestCase):
    def test_truncated_fails_clean_no_output(self):
        d = tempfile.mkdtemp(); data = open(SAMPLE, 'rb').read()
        for pct in (10, 50, 99):
            src = os.path.join(d, 't.rvt'); open(src, 'wb').write(data[:len(data) * pct // 100])
            out = os.path.join(d, 'o%d' % pct)
            r = subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'rvt-extract'), '--out', out, src], capture_output=True, text=True, timeout=300)
            self.assertEqual(r.returncode, 2, r.stderr[-300:]); self.assertNotIn('Traceback', r.stderr)
            self.assertEqual([f for _, _, fs in os.walk(out) for f in fs if f.endswith('.rfa')], [])
        shutil.rmtree(d)
