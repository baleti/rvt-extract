import os, tempfile, unittest
from unittest import mock
from rvtx import rfa, cfbw


class B(rfa.Builder):
    def __init__(self): self.pd = mock.Mock(fmt='2024')
    def streams(self, *a): return {}


class AtomicWrite(unittest.TestCase):
    def test_failure_keeps_original_and_leaves_no_temp(self):
        d = tempfile.mkdtemp(); out = os.path.join(d, 'x.rfa'); open(out, 'wb').write(b'OLD')
        with mock.patch.object(cfbw, 'write_rfa', side_effect=OSError('disk full')):
            with self.assertRaises(OSError): B().write(out, 'x', 'c')
        self.assertEqual(open(out, 'rb').read(), b'OLD'); self.assertEqual(os.listdir(d), ['x.rfa'])

    def test_replace_failure_cleans_temp(self):
        d = tempfile.mkdtemp(); out = os.path.join(d, 'x.rfa'); open(out, 'wb').write(b'OLD')
        with mock.patch.object(cfbw, 'write_rfa', return_value=b'NEW'), mock.patch('os.replace', side_effect=OSError('x')):
            with self.assertRaises(OSError): B().write(out, 'x', 'c')
        self.assertEqual(os.listdir(d), ['x.rfa']); self.assertEqual(open(out, 'rb').read(), b'OLD')

    def test_success(self):
        d = tempfile.mkdtemp(); out = os.path.join(d, 'x.rfa')
        with mock.patch.object(cfbw, 'write_rfa', return_value=b'NEW'): B().write(out, 'x', 'c')
        self.assertEqual(open(out, 'rb').read(), b'NEW'); self.assertEqual(os.listdir(d), ['x.rfa'])
