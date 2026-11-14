import unittest
from rvtx import items


class T(unittest.TestCase):
    def test_bounded(self):
        for nm in ['x' * 400, '\u65e5\u672c' * 200, '..', '', '\ud800', 'a/b\\c']:
            fn = items.image_file(7, nm)
            leaf = fn.split('/', 1)[1]
            self.assertLessEqual(len(leaf.encode('utf-8')), 255, nm[:5])
            self.assertTrue(fn.startswith('images/7_') and fn.count('/') == 1)
