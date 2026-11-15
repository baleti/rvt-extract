import glob, os, shutil, subprocess, sys, tempfile, unittest
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sorted(glob.glob(os.path.expanduser('~/famlift-run/rl2022/families/*/*.rfa')))[:1]


@unittest.skipUnless(SRC, 'no local public-sample re-lift (famlift-run/rl2022)')
class T(unittest.TestCase):
    def streams(self, p):
        import olefile
        o = olefile.OleFileIO(p); return {'/'.join(e): o.openstream('/'.join(e)).read() for e in o.listdir(streams=True)}

    def test_path_removed_everything_else_identical(self):
        sys.path.insert(0, R)
        import re, struct, olefile
        from rvtx import cfbw
        st = self.streams(SRC[0]); b = st['BasicFileInfo']
        name = re.search(r'([^\x00-\x1f|]+\.rfa)', b[:len(b) - len(b) % 2].decode('utf-16le', 'replace')).group(1)
        new = 'lift_big/BIG009/families/Generic Models/' + name
        old = struct.pack('<I', len(name)) + name.encode('utf-16le')
        self.assertIn(old, b)
        dirty = dict(st); dirty['BasicFileInfo'] = b.replace(old, struct.pack('<I', len(new)) + new.encode('utf-16le'))
        part = [k for k in st if k.startswith('Partitions/')][0]
        with tempfile.TemporaryDirectory() as d:
            a = os.path.join(d, 'a.rfa'); o = os.path.join(d, 'o.rfa')
            open(a, 'wb').write(cfbw.write_rfa(dirty, part))
            sys.path.insert(0, os.path.join(R, 'tools')); import rfa_streamaudit as A
            self.assertTrue(any('host path' in x for x in A.audit(a)))
            r = subprocess.run([sys.executable, os.path.join(R, 'tools', 'rfa_fix_basicfileinfo.py'), a, o], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertEqual(self.streams(o), st)        # every stream equals the clean original, BasicFileInfo included
            self.assertEqual(A.audit(o), [])
            self.assertEqual(subprocess.run([sys.executable, os.path.join(R, 'tools', 'rfa_fix_basicfileinfo.py'), o, os.path.join(d, 'p.rfa')], capture_output=True).returncode, 1)
            self.assertEqual(subprocess.run([sys.executable, os.path.join(R, 'tools', 'rfa_fix_basicfileinfo.py'), a, o], capture_output=True).returncode, 2)   # exists


if __name__ == '__main__': unittest.main()
