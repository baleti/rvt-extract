import os, subprocess, sys, tempfile, unittest, hashlib
SAMPLE = os.environ.get('RVTX_SAMPLE')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PER_RUN = {'BasicFileInfo', 'Global/History', 'PartAtom'}      # per-run id/time streams, differ by design

def streams(path):
    import olefile
    o = olefile.OleFileIO(path)
    try: return {'/'.join(s): hashlib.sha256(o.openstream(s).read()).hexdigest() for s in o.listdir()}
    finally: o.close()

@unittest.skipUnless(SAMPLE and os.path.exists(SAMPLE), 'needs RVTX_SAMPLE project with embedded families')
class HashSeed(unittest.TestCase):
    def test_streams_independent_of_hash_seed(self):
        outs = []
        for seed in ('1', '777'):
            d = tempfile.mkdtemp(); outs.append(d)
            r = subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'rvt-extract'), SAMPLE, '--only', 'families', '--match', 'Head', '--out', d], env=dict(os.environ, PYTHONHASHSEED=seed), capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr[-500:])
        rel = lambda d: sorted(os.path.relpath(os.path.join(a, f), d) for a, _, fs in os.walk(d) for f in fs if f.endswith('.rfa'))
        names = rel(outs[0]); self.assertTrue(names); self.assertEqual(names, rel(outs[1]))
        for n in names:
            a, b = streams(os.path.join(outs[0], n)), streams(os.path.join(outs[1], n))
            self.assertEqual(set(a), set(b))
            self.assertEqual(sorted(k for k in a if a[k] != b[k] and k not in PER_RUN), [], n)
