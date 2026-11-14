import unittest, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from rvtx.cli import exit_status


class T(unittest.TestCase):
    def test_unavailable_check_is_not_reported_as_damage(self):
        code, msgs = exit_status(False, {'(damage check failed)': 'AttributeError: x'}, [])
        self.assertEqual(code, 3)
        self.assertTrue(any('could not run' in m for m in msgs))
        self.assertFalse(any('damaged gzip members' in m for m in msgs))

    def test_real_damage_message_kept(self):
        code, msgs = exit_status(False, {'Partitions/47': 1}, [])
        self.assertEqual(code, 3)
        self.assertTrue(any('damaged gzip members' in m for m in msgs))


if __name__ == '__main__':
    unittest.main()
