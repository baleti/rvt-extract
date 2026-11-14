import unittest
from rvtx import cli


class T(unittest.TestCase):
    def test_no_separators_survive(self):
        for v in ['a,b', 'x\ny', 'x\r\ny', 'p\u2028q', 5, 1.5]:
            out = cli.catalog_cell(v)
            self.assertFalse(any(ch in out for ch in ',\r\n\u2028\u2029'), repr(out))
        self.assertEqual(cli.catalog_cell('a,b'), 'a b')
        self.assertEqual(cli.catalog_cell(5), '5')
