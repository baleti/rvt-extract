import os, sys, json, glob, hashlib, subprocess, tempfile, unittest
from rvtx.cli import _digest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.environ.get('RVTX_SAMPLE_RVT')   # opt-in: Autodesk sample only


class Digest(unittest.TestCase):
    def test_digest(self):
        with tempfile.NamedTemporaryFile() as f:
            f.write(b'abc' * 1000000); f.flush()
            d = _digest(f.name)
        self.assertEqual(d, {'sha256': hashlib.sha256(b'abc' * 1000000).hexdigest(), 'bytes': 3000000})

    @unittest.skipUnless(SAMPLE and os.path.exists(SAMPLE), 'set RVTX_SAMPLE_RVT')
    def test_every_rfa_in_manifest_matches_disk(self):
        with tempfile.TemporaryDirectory() as out:
            subprocess.run([sys.executable, os.path.join(ROOT, 'bin/rvt-extract'), '--only', 'families', '--match', 'Tag', '--out', out, SAMPLE], check=True, capture_output=True)
            m = json.load(open(os.path.join(out, 'manifest.json')))
            n = 0
            for e in m['families']:
                r = e.get('rfa') or {}
                if r.get('status') == 'written':
                    b = open(os.path.join(out, r['file']), 'rb').read(); n += 1
                    self.assertEqual(r['sha256'], hashlib.sha256(b).hexdigest()); self.assertEqual(r['bytes'], len(b))
            self.assertGreater(n, 0)
