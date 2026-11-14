import unittest
from rvtx import items


class T(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(items._sp_clean('a\tb\nc\r\nd'), 'a b c d')
        self.assertEqual(items._sp_clean(None), '')
