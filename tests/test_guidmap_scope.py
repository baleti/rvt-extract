"""Nested content-document GUIDs must not depend on which other families were lifted in the same run (the guid map was cached on the Builder and never reset, so
in a full run later families kept the SOURCE nested GUID while a --match run regenerated it). Opt-in (slow, ~4 min): RVTX_SAMPLE_RVT=<public rst_basic 2017-2023 .rvt>."""
import os, subprocess, sys, tempfile, unittest, shutil, glob, zlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.environ.get('RVTX_SAMPLE_RVT')


def _cd_first_guid(rfa):
    import olefile
    o = olefile.OleFileIO(rfa)
    return zlib.decompressobj(31).decompress(o.openstream('Global/ContentDocuments').read()[8:])[12:28].hex()


@unittest.skipUnless(SAMPLE and os.path.exists(SAMPLE), 'set RVTX_SAMPLE_RVT')
class GuidMapScope(unittest.TestCase):
    def test_full_equals_match(self):
        d = tempfile.mkdtemp(); env = dict(os.environ, RVT_NOCACHE='1')
        try:
            res = {}
            for tag, extra in (('match', ['--match', 'timber_door_int']), ('full', [])):
                out = os.path.join(d, tag)
                r = subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'rvt-extract'), '--only', 'families', '--out', out, SAMPLE] + extra, capture_output=True, text=True, timeout=1500, env=env)
                self.assertEqual(r.returncode, 0, r.stderr[-300:])
                f = glob.glob(out + '/families/**/timber_door_int.rfa', recursive=True)
                if not f: self.skipTest('sample has no timber_door_int')
                res[tag] = _cd_first_guid(f[0])
            self.assertEqual(res['match'], res['full'])
        finally:
            shutil.rmtree(d, ignore_errors=True)
