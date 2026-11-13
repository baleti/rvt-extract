"""Simulated write failure (RLIMIT_FSIZE => EFBIG): failed families are marked status=error in the manifest, exit code is 5,
no *.tmp residue, every listed rfa is a readable OLE file and no unlisted rfa exists (diskaudit). Opt-in: RVTX_SAMPLE_RVT=<rvt with >5 families>."""
import os, sys, unittest, subprocess, tempfile, shutil, resource
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.environ.get('RVTX_SAMPLE_RVT')


def _limit():
    import signal
    signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
    resource.setrlimit(resource.RLIMIT_FSIZE, (300 * 1024, 300 * 1024))


@unittest.skipUnless(SAMPLE and os.path.exists(SAMPLE), 'set RVTX_SAMPLE_RVT')
class T(unittest.TestCase):
    def test_efbig_never_leaves_truncated_rfa(self):
        tmp = tempfile.mkdtemp()
        try:
            out = os.path.join(tmp, 'o')
            r = subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'rvt-extract'), '--only', 'families', '--out', out, SAMPLE],
                               capture_output=True, timeout=1500, preexec_fn=_limit)
            self.assertEqual(r.returncode, 5, r.stderr[-500:])
            a = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'diskaudit.py'), out], capture_output=True, text=True)
            self.assertEqual(a.returncode, 0, a.stdout + a.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
