import unittest
from rvtx.cli import exit_status


def fam(status=None, error=None):
    return {'rfa': {'status': status, **({'error': error} if error else {})}} if status else {}


class T(unittest.TestCase):
    def test_codes(self):
        ok = [fam('written'), fam('no_embedded_doc'), fam('skipped')]
        self.assertEqual(exit_status(False, {}, ok), (0, []))
        self.assertEqual(exit_status(False, {}, ok + [fam('error', 'AssertionError: x')])[0], 0)      # plain family error: listed in the manifest, rc stays 0
        self.assertEqual(exit_status(False, {'Partitions/1': 1}, ok)[0], 3)
        self.assertEqual(exit_status(False, {}, ok + [fam('error', 'OSError: [Errno 28] No space left on device')])[0], 5)
        self.assertEqual(exit_status(True, {}, ok)[0], 4)

    def test_precedence_and_all_messages(self):
        c, m = exit_status(True, {'Partitions/1': 1}, [fam('error', 'OSError: full')])
        self.assertEqual(c, 4); self.assertEqual(len(m), 3)
        c, m = exit_status(False, {'Partitions/1': 1}, [fam('error', 'OSError: full')])
        self.assertEqual((c, len(m)), (5, 2))
