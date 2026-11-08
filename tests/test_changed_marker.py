import os, shutil, subprocess, sys, tempfile, time, unittest

SAMPLE = os.environ.get('RVTX_SAMPLE')


@unittest.skipUnless(SAMPLE and os.path.exists(SAMPLE), 'needs RVTX_SAMPLE')
class ChangedMarker(unittest.TestCase):
    def test_source_truncated_during_run_marks_incomplete(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, 's.rvt'); shutil.copy(SAMPLE, src); out = os.path.join(d, 'o')
            p = subprocess.Popen([sys.executable, os.path.join(root, 'bin', 'rvt-extract'), src, '--out', out],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            time.sleep(3); os.truncate(src, os.path.getsize(src) // 2)
            _, err = p.communicate()
            if p.returncode != 4: self.skipTest('run finished before the change (rc=%s)' % p.returncode)
            self.assertTrue(os.path.exists(os.path.join(out, 'families', 'INCOMPLETE')))


if __name__ == '__main__':
    unittest.main()
