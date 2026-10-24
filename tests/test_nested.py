import os, unittest
from rvtx import rfa, elemtable


class FakeBuilder:
    """nested_docs from a parent -> descendants table (flattened, like Builder.nested_docs)"""
    nested_depth = rfa.Builder.nested_depth

    def __init__(self, tree):
        self.tree = tree

    def nested_docs(self, k, seen=None):
        out = []
        for c in self.tree.get(k, []):
            out.append((c, 'g%d' % c)); out += self.nested_docs(c)
        return out


class NestedDepthTests(unittest.TestCase):
    def test_depths(self):
        b = FakeBuilder({0: [1, 2], 1: [3], 3: [4]})
        self.assertEqual(b.nested_depth(4), 0)
        self.assertEqual(b.nested_depth(3), 1)
        self.assertEqual(b.nested_depth(1), 2)
        self.assertEqual(b.nested_depth(2), 0)
        self.assertEqual(b.nested_depth(0), 3)      # 0 -> 1 -> 3 -> 4

    def test_flat_has_depth_zero(self):
        self.assertEqual(FakeBuilder({}).nested_depth(0), 0)


class ElemTableDatesTests(unittest.TestCase):
    def rows(self, mode):
        os.environ['RVTX_ETDATES'] = mode
        try: t = elemtable.build4([5, 9], {9}, {9: b'\x01\x02\x03\x04' + b'\xcf\x03\0\0' + b'\xef\x03\0\0'}, 77)
        finally: os.environ.pop('RVTX_ETDATES', None)
        return t[6:6 + 56]

    def test_real_mode_has_no_project_dates(self):
        r = self.rows('real')[28:56]      # row of element 9
        self.assertEqual(r[8:16], b'\0' * 8)      # a = b = 0, so Revit does not drop the row as a 'missing element'
        self.assertEqual(r[16:20], b'\xff' * 4)

    def test_old_mode_keeps_project_dates(self):
        self.assertEqual(self.rows('old')[28:56][8:12], b'\xcf\x03\0\0')


if __name__ == '__main__':
    unittest.main()
