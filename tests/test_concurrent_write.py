import multiprocessing as mp, os, tempfile, unittest
from unittest import mock
from rvtx import rfa, cfbw


class B(rfa.Builder):
    def __init__(self): self.pd = mock.Mock(fmt='2024')
    def streams(self, *a): return {}


def worker(out, byte, n):
    data = bytes([byte]) * 3_000_000
    with mock.patch.object(cfbw, 'write_rfa', return_value=data):
        for _ in range(n): B().write(out, 'x', 'c')


class Concurrent(unittest.TestCase):
    def test_last_writer_wins_whole_file(self):
        d = tempfile.mkdtemp(); out = os.path.join(d, 'x.rfa'); ps = [mp.Process(target=worker, args=(out, b, 15)) for b in (0x41, 0x42, 0x43)]
        for p in ps: p.start()
        seen = set()
        while any(p.is_alive() for p in ps):
            try: blob = open(out, 'rb').read()
            except FileNotFoundError: continue
            if blob: self.assertEqual(len(blob), 3_000_000, 'torn read'); self.assertEqual(len(set(blob)), 1, 'mixed content'); seen.add(blob[0])
        for p in ps: p.join(); self.assertEqual(p.exitcode, 0)
        blob = open(out, 'rb').read(); self.assertEqual((len(blob), len(set(blob))), (3_000_000, 1))
        self.assertEqual(os.listdir(d), ['x.rfa'])      # no tmp residue
