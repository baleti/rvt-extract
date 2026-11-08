import os, tempfile, unittest
from unittest import mock
from rvtx import rfa, cfbw
from tests.test_atomicwrite import B


class FileMode(unittest.TestCase):
    def test_rfa_mode_follows_umask_and_is_not_executable(self):
        d = tempfile.mkdtemp(); out = os.path.join(d, 'x.rfa'); old = os.umask(0o027)
        try:
            with mock.patch.object(cfbw, 'write_rfa', return_value=b'NEW'): B().write(out, 'x', 'c')
        finally: os.umask(old)
        self.assertEqual(os.stat(out).st_mode & 0o777, 0o640)


if __name__ == '__main__': unittest.main()
