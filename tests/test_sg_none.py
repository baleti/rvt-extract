import unittest
from rvtx import items


class SgNone(unittest.TestCase):
    def test_absent_id_is_none(self):
        self.assertIsNone(items.sg(None))

    def test_ids_unchanged(self):
        self.assertEqual(items.sg(5), 5)
        self.assertEqual(items.sg((1 << 32) - 2002000), -2002000)


if __name__ == '__main__':
    unittest.main()
