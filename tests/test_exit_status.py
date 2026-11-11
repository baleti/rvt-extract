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


class MassFailure(unittest.TestCase):
    def test_mass_error_on_embedded_rows_warns(self):
        def emb(status): return {'embedded_doc': True, 'rfa': {'status': status}}
        fams = [emb('written')] * 34 + [emb('error')] * 242      # shape of the bad memory-capped big-file run: rc 0 but must warn
        code, msgs = exit_status(False, {}, fams)
        self.assertEqual(code, 0); self.assertTrue(any('failed run' in m for m in msgs))
        self.assertEqual(exit_status(False, {}, [emb('written')] * 30 + [emb('error')]), (0, []))      # 1 of 31: quiet
        self.assertEqual(exit_status(False, {}, [{'embedded_doc': False, 'rfa': {'status': 'no_embedded_doc'}}] * 9), (0, []))


class RiskNote(unittest.TestCase):
    def test_risk_note_is_not_known_bad(self):
        from rvtx.cli import known_bad_files
        e = {'rfa': {'status': 'written', 'file': 'a.rfa', 'risk_note': 'unverified risk: x'}}
        self.assertEqual(known_bad_files([e]), [])
        e['rfa']['known_bad'] = 'y'; self.assertEqual(known_bad_files([e]), ['a.rfa'])

    def test_cli_does_not_promote_risk_to_known_bad(self):
        import inspect, rvtx.cli as c
        self.assertNotIn("setdefault('known_bad', B.risk)", inspect.getsource(c))
