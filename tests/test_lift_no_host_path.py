import glob, os, re, sys, unittest
FILES = sorted(glob.glob(os.path.expanduser('~/famlift-run/rl20*/families/*/*.rfa')))[::7]


@unittest.skipUnless(FILES, 'no local public-sample re-lift (famlift-run/rl20xx)')
class T(unittest.TestCase):
    def test_basicfileinfo_has_bare_name_only(self):
        # pre-2026-11-04 output embedded the lift path (absolute or relative) in BasicFileInfo; current output must not
        import olefile
        for f in FILES:
            b = olefile.OleFileIO(f).openstream('BasicFileInfo').read().decode('utf-16le', 'replace')
            self.assertIsNone(re.search(r'(?:[/\\]home[/\\]|[A-Za-z]:[/\\]|\w[/\\]\w)', b), f)


if __name__ == '__main__': unittest.main()
