import io, os, unittest
import olefile
from rvtx import cfbw

PATHS = [e[0] for e in cfbw.RFA_DIR if e[1] == 2]
SIZES = [0, 1, 63, 64, 65, 4095, 4096, 4097, 8191, 8192, 8193, 70000]


def payload(n, seed):
    return bytes((seed * 31 + i * 7) & 255 for i in range(n))


class Boundaries(unittest.TestCase):
    def check(self, sizes):
        st = {p: payload(sizes[i % len(sizes)], i) for i, p in enumerate(PATHS)}
        b = cfbw.write_rfa(st)
        self.assertEqual(len(b) % 4096, 0)
        o = olefile.OleFileIO(io.BytesIO(b))
        for p, d in st.items():
            self.assertEqual(o.openstream(p).read(), d, (p, len(d)))
        o.close()

    def test_every_size_in_every_stream_slot(self):
        # rotate the size list so each boundary size lands in different streams (mini vs regular stream, empty)
        for r in range(len(SIZES)):
            self.check(SIZES[r:] + SIZES[:r])

    def test_all_streams_the_same_boundary_size(self):
        for n in SIZES:
            self.check([n])

    def test_many_fat_sectors(self):
        self.check([3_000_000])      # forces more than one FAT sector (>1024 sectors in total)


if __name__ == '__main__':
    unittest.main()
