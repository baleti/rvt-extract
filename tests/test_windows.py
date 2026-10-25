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
        parts = list(T.windows([st], win, ov)); self.assertGreater(len(parts), 1)
        rebuilt = bytearray(); 
        for buf, lim in parts:
            rebuilt += buf[:lim] if lim is not None else buf
        self.assertEqual(bytes(rebuilt), whole)
        self.assertEqual(bytes(T.joined_lowmem(st)), whole)
        self.assertEqual(b''.join(T.member_chunks([st])), whole)
        from rvtx import partition as PT
        W = 8
        for W in (8, 4):
            try: a = PT.parse_joined(whole, W); break
            except Exception: a = None
        if a is None: self.skipTest('sample partition not parseable as chain')
        b = PT.parse_stream(T.member_chunks([st]), W); self.assertEqual(a, b)
        PT.TRIM = 1000
        try: self.assertEqual(a, PT.parse_stream(T.member_chunks([st]), W))
        finally: PT.TRIM = 32 << 20
        ids = {x[0] for x in a[0]['H'][::3]}
        self.assertEqual(PT.parse_joined(whole, W, keep0=ids), PT.parse_stream(T.member_chunks([st]), W, keep0=ids))


if __name__ == '__main__': unittest.main()
