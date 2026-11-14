import os, subprocess, sys, tempfile, time, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOLD = "import sys,time; sys.path.insert(0, %r); from rvtx import cli; cli._lock_out(sys.argv[1]); print('held', flush=True); time.sleep(30)" % ROOT
TRY = "import sys; sys.path.insert(0, %r); from rvtx import cli; cli._lock_out(sys.argv[1]); print('got')" % ROOT


class T(unittest.TestCase):
    def test_second_run_refused_then_free_after_exit(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, 'o')
            h = subprocess.Popen([sys.executable, '-c', HOLD, out], stdout=subprocess.PIPE, text=True)
            try:
                self.assertEqual(h.stdout.readline().strip(), 'held')
                r = subprocess.run([sys.executable, '-c', TRY, out], capture_output=True, text=True)
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                self.assertIn('another extraction is already running', r.stderr)
            finally:
                h.kill(); h.wait()
            r = subprocess.run([sys.executable, '-c', TRY, out], capture_output=True, text=True)      # a killed holder leaves no stale lock
            self.assertEqual((r.returncode, r.stdout.strip()), (0, 'got'), r.stderr)
