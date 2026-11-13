import os, subprocess, sys, tempfile, unittest, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.environ.get('RVTX_SAMPLE_RVT')  # any real rvt; opt-in


@unittest.skipUnless(SAMPLE and os.path.exists(SAMPLE), 'set RVTX_SAMPLE_RVT')
class Truncated(unittest.TestCase):
    def test_truncated_fails_clean_no_output(self):
        d = tempfile.mkdtemp(); data = open(SAMPLE, 'rb').read()
        for pct in (10, 50, 99):
            src = os.path.join(d, 't.rvt'); open(src, 'wb').write(data[:len(data) * pct // 100])
            out = os.path.join(d, 'o%d' % pct)
            r = subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'rvt-extract'), '--out', out, src], capture_output=True, text=True, timeout=300)
            self.assertEqual(r.returncode, 2, r.stderr[-300:]); self.assertNotIn('Traceback', r.stderr)
            self.assertEqual([f for _, _, fs in os.walk(out) for f in fs if f.endswith('.rfa')], [])
        shutil.rmtree(d)


@unittest.skipUnless(SAMPLE and os.path.exists(SAMPLE), 'set RVTX_SAMPLE_RVT')
class Garbage(unittest.TestCase):
    def _run(self, d, src, tag):
        out = os.path.join(d, 'o' + tag)
        r = subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'rvt-extract'), '--out', out, src], capture_output=True, text=True, timeout=300)
        self.assertNotIn('Traceback', r.stderr, tag)
        self.assertNotEqual(r.returncode, 0, tag)
        self.assertEqual([f for _, _, fs in os.walk(out) for f in fs if f.endswith('.rfa')], [], tag)

    def test_garbage_variants_refused_clean(self):
        d = tempfile.mkdtemp(); data = open(SAMPLE, 'rb').read()
        cases = {'empty': b'', 'zeros': bytes(4096), 'random': os.urandom(100000),
                 'head512': data[:512], 'hdrzero': bytes(2048) + data[2048:],
                 'tailzero': data[:len(data) // 2] + bytes(len(data) - len(data) // 2)}
        for tag, blob in cases.items():
            src = os.path.join(d, tag + '.rvt'); open(src, 'wb').write(blob)
            self._run(d, src, tag)
        shutil.rmtree(d)


@unittest.skipUnless(SAMPLE and os.path.exists(SAMPLE), 'set RVTX_SAMPLE_RVT')
class AppendedTail(unittest.TestCase):
    def test_appended_bytes_do_not_change_families(self):
        """item 21 (2026-11-13): 64 KiB of random bytes after the end of a real rvt are ignored; the family set is the same as for the clean copy."""
        d = tempfile.mkdtemp(); data = open(SAMPLE, 'rb').read(); names = []
        for tag, blob in (('clean', data), ('tail', data + os.urandom(65536))):
            src = os.path.join(d, tag + '.rvt'); open(src, 'wb').write(blob)
            out = os.path.join(d, 'o' + tag)
            r = subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'rvt-extract'), '--match', '^[A-Z]', '--only', 'families', '--out', out, src], capture_output=True, text=True, timeout=1500)
            self.assertEqual(r.returncode, 0, r.stderr[-300:]); self.assertNotIn('Traceback', r.stderr)
            names.append(sorted(os.path.relpath(os.path.join(a, f), out) for a, _, fs in os.walk(out) for f in fs if f.endswith('.rfa')))
        self.assertTrue(names[0]); self.assertEqual(names[0], names[1])
        shutil.rmtree(d)
