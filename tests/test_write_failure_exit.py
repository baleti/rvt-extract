import errno, unittest
from unittest import mock
from rvtx import cli


class WriteFail(unittest.TestCase):
    def test_disk_full_exits_5(self):
        for en in (errno.ENOSPC, errno.EFBIG, errno.EDQUOT):
            with mock.patch.object(cli, '_main', side_effect=OSError(en, 'x')):
                self.assertEqual(cli.main([]), 5)

    def test_missing_input_still_raises(self):
        with mock.patch.object(cli, '_main', side_effect=FileNotFoundError(errno.ENOENT, 'x')):
            with self.assertRaises(FileNotFoundError): cli.main([])


if __name__ == '__main__':
    unittest.main()
