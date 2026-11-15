import glob, os, shutil, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
SRC = sorted(glob.glob(os.path.expanduser('~/famlift-run/rl2019/families/*/*.rfa')))[:1]


@unittest.skipUnless(SRC, 'no local public-sample re-lift (famlift-run/rl2019)')
class T(unittest.TestCase):
    def mut(self, stream, off):
        import olefile, rfa_streamaudit as A
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'x.rfa'); shutil.copy(SRC[0], p)
            o = olefile.OleFileIO(p, write_mode=True)
            data = bytearray(o.openstream(stream).read()); data[off] ^= 0x40; o.write_stream(stream, bytes(data)); o.close()
            return A.audit(p)

    def test_control_clean_and_flips_found(self):
        import rfa_streamaudit as A
        self.assertEqual(A.audit(SRC[0]), [])
        self.assertTrue(self.mut('Contents', 200))
        self.assertTrue(self.mut('TransmissionData', 50))
        import olefile
        part = [n for n in olefile.OleFileIO(SRC[0]).listdir() if n[0] == 'Partitions'][0]
        self.assertTrue(self.mut('/'.join(part), 2000))

    def test_late_chunk_flip_found_by_full_parse(self):
        import olefile
        part = '/'.join([n for n in olefile.OleFileIO(SRC[0]).listdir() if n[0] == 'Partitions'][0])
        n = len(olefile.OleFileIO(SRC[0]).openstream(part).read())
        hits = [self.mut(part, n * k // 20) for k in range(11, 20)]      # past the first gzip member: only the whole-stream parse can see these
        self.assertTrue(any(any('do not parse' in x for x in h) for h in hits), hits)


@unittest.skipUnless(SRC, 'no local public-sample re-lift (famlift-run/rl2019)')
class TPath(unittest.TestCase):
    def test_host_path_in_basicfileinfo_found(self):
        import olefile, rfa_streamaudit as A
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'x.rfa'); shutil.copy(SRC[0], p)
            self.assertEqual(A.audit(p), [])
            o = olefile.OleFileIO(p, write_mode=True)
            b = o.openstream('BasicFileInfo').read()
            tail = ('/home/u/x.rfa').encode('utf-16le')
            o.write_stream('BasicFileInfo', b[:40] + tail + b[40 + len(tail):]); o.close()
            self.assertTrue(any('host path' in x for x in A.audit(p)))

    def test_relative_host_path_in_basicfileinfo_found(self):
        import olefile, rfa_streamaudit as A
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'x.rfa'); shutil.copy(SRC[0], p)
            o = olefile.OleFileIO(p, write_mode=True)
            b = o.openstream('BasicFileInfo').read()
            tail = ('out5/families/Doors/x.rfa').encode('utf-16le')
            o.write_stream('BasicFileInfo', b[:40] + tail + b[40 + len(tail):]); o.close()
            self.assertTrue(any('host path' in x for x in A.audit(p)))
