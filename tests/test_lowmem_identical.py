"""normal vs --low-memory extraction must give byte-identical .rfa (uuid4/time pinned). Slow (about 2 min): set RVTX_SLOW=1 and RVTX_SAMPLE=<Autodesk Structural 2024 sample .rvt>."""
import os, sys, unittest, subprocess, tempfile, shutil, glob

PIN = '''import sys, uuid, time, runpy
n = [0]
def u(): n[0] += 1; return uuid.UUID(int=n[0])
uuid.uuid4 = u; time.time = lambda: 1.7e9
sys.argv = ['rvt-extract'] + sys.argv[1:]
runpy.run_path(%r, run_name='__main__')
'''
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@unittest.skipUnless(os.environ.get('RVTX_SLOW') == '1' and os.path.exists(os.environ.get('RVTX_SAMPLE', '')), 'slow; needs RVTX_SLOW=1 and RVTX_SAMPLE')
class T(unittest.TestCase):
    def test_identical(self):
        tmp = tempfile.mkdtemp()
        try:
            pin = os.path.join(tmp, 'pin.py'); open(pin, 'w').write(PIN % os.path.join(ROOT, 'bin', 'rvt-extract'))
            res = {}
            for mode in ('n', 'l'):
                out = os.path.join(tmp, 'same')
                args = [sys.executable, pin] + (['--low-memory'] if mode == 'l' else []) + ['--match', '^000_BreakLine_Pick', '--out', out, os.environ['RVTX_SAMPLE']]
                subprocess.run(args, check=True, capture_output=True, timeout=600)
                res[mode] = {os.path.relpath(p, out): open(p, 'rb').read() for p in glob.glob(os.path.join(out, 'families', '**', '*.rfa'), recursive=True)}
                shutil.rmtree(out)
            self.assertTrue(res['n'])
            self.assertEqual(res['n'], res['l'])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
