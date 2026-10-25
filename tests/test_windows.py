import os, sys, glob, unittest
from rvtx import RESEARCH  # noqa
import olefile, rvt2text as T


class WindowsMatchJoined(unittest.TestCase):
    def test_windows_reassemble_joined(self):
        files = sorted(glob.glob(os.path.expanduser('~/rvt-research/samples/*.rvt')), key=os.path.getsize)
        if not files: self.skipTest('no sample project')
        o = olefile.OleFileIO(files[0]); pn = [y for y in ('/'.join(e) for e in o.listdir(streams=True)) if y.startswith('Partitions/')][0]
        st = o.openstream(pn).read(); whole = T.joined(st)
        win, ov = 200_000, 20_000
        parts = list(T.windows(st, win, ov)); self.assertGreater(len(parts), 1)
        rebuilt = bytearray(); 
        for buf, lim in parts:
            rebuilt += buf[:lim] if lim is not None else buf
        self.assertEqual(bytes(rebuilt), whole)
        self.assertEqual(bytes(T.joined_lowmem(st)), whole)


if __name__ == '__main__': unittest.main()
