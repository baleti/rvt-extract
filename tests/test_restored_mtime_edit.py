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


SAMPLE22 = os.environ.get('RVTX_SAMPLE_2022')


@unittest.skipUnless(SAMPLE22 and os.path.exists(SAMPLE22), 'needs RVTX_SAMPLE_2022 (public 2022 rst_basic)')
class HarmlessRestoredMtimeEdit(unittest.TestCase):
    def test_valid_edit_no_family_breaks_is_rc4(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, 's.rvt'); shutil.copy(SAMPLE22, src); out = os.path.join(d, 'o')
            os.utime(src, (1577836800, 1577836800))
            p = subprocess.Popen([sys.executable, os.path.join(root, 'bin', 'rvt-extract'), src, '--out', out, '--only', 'project_info'],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=dict(os.environ, RVT_NOCACHE='1'))
            time.sleep(2)
            with open(src, 'r+b') as f:      # F:\\Git -> G:\\Git (UTF-16) at 17478: bytes the extractor does not read, so no family breaks
                f.seek(17478); f.write('G'.encode('utf-16-le'))
            os.utime(src, (1577836800, 1577836800))
            _, err = p.communicate()
            if p.returncode == 0: self.skipTest('run finished before the edit')
            self.assertEqual(p.returncode, 4, err[-300:])



@unittest.skipUnless(SAMPLE and os.path.exists(SAMPLE), 'needs RVTX_SAMPLE')
class SourceDeletedDuringRun(unittest.TestCase):
    def test_deleted_source_is_rc4_not_traceback(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, 's.rvt'); shutil.copy(SAMPLE, src); out = os.path.join(d, 'o')
            p = subprocess.Popen([sys.executable, os.path.join(root, 'bin', 'rvt-extract'), src, '--out', out, '--only', 'project_info'],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=dict(os.environ, RVT_NOCACHE='1'))
            time.sleep(2); os.unlink(src)
            _, err = p.communicate()
            if p.returncode == 0: self.skipTest('run finished before the delete')
            self.assertEqual(p.returncode, 4, err[-300:]); self.assertNotIn('Traceback', err)


if __name__ == '__main__':
    unittest.main()
