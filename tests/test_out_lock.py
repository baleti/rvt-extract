import os, subprocess, sys, tempfile, time, unittest, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class OutLock(unittest.TestCase):
    @unittest.skipUnless(sys.platform != 'win32', 'flock')
    def test_second_run_into_same_out_refused(self):
        from rvtx import cli
        d = tempfile.mkdtemp(); cli._lock_out(d)       # this process holds the lock
        r = subprocess.run([sys.executable, '-c', 'import sys; sys.path.insert(0, %r); from rvtx import cli; cli._lock_out(%r)' % (ROOT, d)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2); self.assertIn('already running', r.stderr)
        shutil.rmtree(d, ignore_errors=True)
