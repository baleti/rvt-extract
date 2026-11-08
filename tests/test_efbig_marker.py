import os, resource, shutil, subprocess, sys, tempfile, unittest

SAMPLE = os.environ.get('RVTX_SAMPLE')


@unittest.skipUnless(SAMPLE and os.path.exists(SAMPLE), 'needs RVTX_SAMPLE project with embedded families')
class EfbigMarker(unittest.TestCase):
    def test_marker_present_after_size_limit_failure(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, 'o')
            lim = lambda: resource.setrlimit(resource.RLIMIT_FSIZE, (200 * 1024, 200 * 1024))
            r = subprocess.run([sys.executable, os.path.join(root, 'bin', 'rvt-extract'), SAMPLE, '--out', out],
                               capture_output=True, text=True, preexec_fn=lim)
            if r.returncode == 0: self.skipTest('sample produced no file above the limit')
            self.assertEqual(r.returncode, 5, r.stderr[-300:])
            self.assertTrue(os.path.exists(os.path.join(out, 'families', 'INCOMPLETE')))
            self.assertNotIn('Traceback', r.stderr)


if __name__ == '__main__':
    unittest.main()
