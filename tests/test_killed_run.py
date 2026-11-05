import os, signal, subprocess, sys, tempfile, time, unittest, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.environ.get('RVTX_SAMPLE_RVT')  # any real rvt with many families; opt-in


def _rfas(out):
    return [os.path.join(r, f) for r, _, fs in os.walk(out) for f in fs if f.endswith('.rfa')]


@unittest.skipUnless(SAMPLE and os.path.exists(SAMPLE), 'set RVTX_SAMPLE_RVT')
class Killed(unittest.TestCase):
    def _run(self, sig):
        import olefile
        d = tempfile.mkdtemp(dir=os.environ.get('TMPDIR')); out = os.path.join(d, 'o')
        p = subprocess.Popen([sys.executable, os.path.join(ROOT, 'bin', 'rvt-extract'), '--out', out, SAMPLE], stderr=subprocess.PIPE)
        t0 = time.time()
        while time.time() - t0 < 600 and p.poll() is None and len(_rfas(out)) < 5: time.sleep(0.05)
        if p.poll() is not None: shutil.rmtree(d); self.skipTest('finished before kill')
        p.send_signal(sig); p.wait(timeout=60)
        self.assertTrue(os.path.exists(os.path.join(out, 'families', 'INCOMPLETE')))
        for f in _rfas(out):
            self.assertTrue(olefile.isOleFile(f), f); o = olefile.OleFileIO(f)
            for s in o.listdir(): o.openstream(s).read()
            o.close()
        shutil.rmtree(d)

    def test_sigkill(self): self._run(signal.SIGKILL)
    def test_sigterm(self): self._run(signal.SIGTERM)
