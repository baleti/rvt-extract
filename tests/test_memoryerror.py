import io, unittest
from unittest import mock
from contextlib import redirect_stderr
from rvtx import cli


class OutOfMemory(unittest.TestCase):
    def test_memoryerror_is_a_clean_exit_6(self):
        err = io.StringIO()
        with mock.patch.object(cli, '_main', side_effect=MemoryError), redirect_stderr(err):
            rc = cli.main([])
        self.assertEqual(rc, 6)
        self.assertIn('--low-memory', err.getvalue())


if __name__ == '__main__':
    unittest.main()
