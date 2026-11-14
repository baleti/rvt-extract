"""A same-size in-place edit with mtime restored, done during a families run, must not exit 0 (was rc 0 with 4/4 families failed).
Opt-in: RVTX_SAMPLE=<public rst_basic .rvt> (needs ~2 min)."""
import os, shutil, subprocess, sys, tempfile, time, unittest

SAMPLE = os.environ.get('RVTX_SAMPLE')


@unittest.skipUnless(SAMPLE and os.path.exists(SAMPLE), 'needs RVTX_SAMPLE')
class RestoredMtimeEdit(unittest.TestCase):
    def test_edit_with_restored_mtime_is_rc4(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, 's.rvt'); shutil.copy(SAMPLE, src); out = os.path.join(d, 'o')
            os.utime(src, (1577836800, 1577836800)); sz = os.path.getsize(src)
            env = dict(os.environ, RVT_NOCACHE='1')
            p = subprocess.Popen([sys.executable, os.path.join(root, 'bin', 'rvt-extract'), src, '--out', out, '--only', 'families', '--match', 'Pile'],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
            time.sleep(25)
            with open(src, 'r+b') as f:
                f.seek(sz // 2); b = f.read(64); f.seek(sz // 2); f.write(bytes(x ^ 0xFF for x in b))
            os.utime(src, (1577836800, 1577836800))
            _, err = p.communicate()
            if p.returncode == 0 and 'could not be written' not in err: self.skipTest('run finished before the edit')
            self.assertEqual(p.returncode, 4, err[-400:])


if __name__ == '__main__':
    unittest.main()
