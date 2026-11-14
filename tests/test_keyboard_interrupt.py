import io, unittest
from unittest import mock
from contextlib import redirect_stderr
from rvtx import cli


class Interrupt(unittest.TestCase):
    def test_ctrl_c_is_a_clean_exit_130(self):
        err = io.StringIO()
        with mock.patch.object(cli, '_main', side_effect=KeyboardInterrupt), redirect_stderr(err):
            rc = cli.main([])
        self.assertEqual(rc, 130)
        self.assertIn('INCOMPLETE', err.getvalue())
        self.assertNotIn('Traceback', err.getvalue())


if __name__ == '__main__':
    unittest.main()
