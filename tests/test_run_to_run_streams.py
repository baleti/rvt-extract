"""Two unpinned extractions of the same family differ ONLY in the GUID/time metadata streams
(BasicFileInfo, Global/History, PartAtom, Global/DocumentIncrementTable [save time]). Any other stream differing means the encoder is
nondeterministic (would hide regressions in hash comparisons). Opt-in: RVTX_SAMPLE_RVT=<any rvt>."""
import os, sys, unittest, subprocess, tempfile, shutil, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.environ.get('RVTX_SAMPLE_RVT')
# DocumentIncrementTable holds the save time twice (smallstreams.document_increment_table); it is compressed, so one changed second shows as ~66 differing stored bytes
META = {'BasicFileInfo', 'Global/History', 'PartAtom', 'Global/DocumentIncrementTable'}


@unittest.skipUnless(SAMPLE and os.path.exists(SAMPLE), 'set RVTX_SAMPLE_RVT')
class T(unittest.TestCase):
    def test_only_metadata_streams_differ(self):
        import olefile
        tmp = tempfile.mkdtemp()
        try:
            runs = []
            for i in (1, 2):
                out = os.path.join(tmp, 'r%d' % i)
                subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'rvt-extract'), '--match', '^[A-Z]', '--only', 'families', '--out', out, SAMPLE],
                               check=True, capture_output=True, timeout=1500)
                runs.append(out)
            files = sorted(os.path.relpath(p, runs[0]) for p in glob.glob(os.path.join(runs[0], 'families', '**', '*.rfa'), recursive=True))
            self.assertTrue(files)
            for f in files[:10]:
                a = olefile.OleFileIO(os.path.join(runs[0], f)); b = olefile.OleFileIO(os.path.join(runs[1], f))
                self.assertEqual(sorted(a.listdir(streams=True)), sorted(b.listdir(streams=True)))
                diff = {'/'.join(p) for p in a.listdir(streams=True) if a.openstream(p).read() != b.openstream(p).read()}
                self.assertLessEqual(diff, META, f)
                a.close(); b.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
