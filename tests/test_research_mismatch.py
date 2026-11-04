import unittest
from unittest import mock
from rvtx import cli


class Mismatch(unittest.TestCase):
    def test_incompatible_research_lib_clean_exit(self):
        with mock.patch.object(cli, '_main', side_effect=TypeError("extract() got an unexpected keyword argument 'window'")):
            self.assertEqual(cli.main([]), 2)

    def test_other_typeerror_still_raises(self):
        with mock.patch.object(cli, '_main', side_effect=TypeError('bad operand')):
            with self.assertRaises(TypeError): cli.main([])


if __name__ == '__main__':
    unittest.main()
