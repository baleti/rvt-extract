"""extraction must never modify or write beside its input project (the in-place-safety priority). Slow: RVTX_SLOW=1 and RVTX_SAMPLE=<Autodesk sample .rvt>. Runs on a read-only copy; compares sha256, size and mtime before/after and that no new file appears next to it."""
import os, sys, unittest, subprocess, tempfile, shutil, hashlib, stat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


@unittest.skipUnless(os.environ.get('RVTX_SLOW') == '1' and os.path.exists(os.environ.get('RVTX_SAMPLE', '')), 'slow; needs RVTX_SLOW=1 and RVTX_SAMPLE')
class T(unittest.TestCase):
    def test_untouched(self):
        tmp = tempfile.mkdtemp()
        try:
            d = os.path.join(tmp, 'in'); os.mkdir(d)
            src = os.path.join(d, 'src.rvt'); shutil.copy(os.environ['RVTX_SAMPLE'], src)
            os.utime(src, (1.6e9, 1.6e9)); os.chmod(src, stat.S_IREAD)
            os.chmod(d, stat.S_IREAD | stat.S_IEXEC)  # no new file may appear next to the input
            before = (sha(src), os.stat(src).st_size, os.stat(src).st_mtime_ns, sorted(os.listdir(d)))
            out = os.path.join(tmp, 'out')
            subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'rvt-extract'), '--only', 'families', '--low-memory', '--match', '^000_BreakLine_Pick', '--out', out, src], check=True, capture_output=True, timeout=900)
            after = (sha(src), os.stat(src).st_size, os.stat(src).st_mtime_ns, sorted(os.listdir(d)))
            self.assertEqual(before, after)
        finally:
            os.chmod(os.path.join(tmp, 'in'), 0o755)
            shutil.rmtree(tmp, ignore_errors=True)

    def test_stale_rfa_flagged(self):
        """a leftover .rfa from an earlier run in the same --out must be reported in the manifest, not silently sit unlisted"""
        import json
        tmp = tempfile.mkdtemp()
        try:
            out = os.path.join(tmp, 'out'); stale = os.path.join(out, 'families', 'X'); os.makedirs(stale); open(os.path.join(stale, 'old.rfa'), 'wb').write(b'x')
            r = subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'rvt-extract'), '--only', 'families', '--low-memory', '--match', '^NoSuchFamilyXYZ', '--out', out, os.environ['RVTX_SAMPLE']], check=True, capture_output=True, timeout=900)
            self.assertEqual(json.load(open(os.path.join(out, 'manifest.json')))['stale_rfa_not_in_manifest'], [os.path.join('families', 'X', 'old.rfa')])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
