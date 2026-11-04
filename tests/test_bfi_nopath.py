import os, unittest
from rvtx import smallstreams as SS


class NoPath(unittest.TestCase):
    def test_rfa_builder_passes_basename_only(self):
        src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'rvtx', 'rfa.py')).read()
        self.assertIn("SS.basic_file_info(os.path.basename(path),", src)   # absolute output dir must not be embedded in a shareable rfa

    def test_bfi_text_carries_given_path_only(self):
        b = SS.basic_file_info('x.rfa', '11111111-1111-1111-1111-111111111111')
        self.assertIn('Last Save Path: x.rfa'.encode('utf-16le'), b) if 'Last Save Path'.encode('utf-16le') in b else self.assertIn(b'Last Save Path: x.rfa', b)


if __name__ == '__main__':
    unittest.main()
