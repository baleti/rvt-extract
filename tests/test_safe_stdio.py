import os, subprocess, sys, unittest

CODE = "import sys; sys.path.insert(0, %r); from rvtx import cli; cli.safe_stdio(); print('\\u65e5'); print('\\u65e5', file=sys.stderr)" % os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class T(unittest.TestCase):
    def test_ascii_locale_does_not_crash(self):
        env = {'PATH': os.environ.get('PATH', ''), 'LC_ALL': 'C', 'LANG': 'C', 'PYTHONCOERCECLOCALE': '0', 'PYTHONUTF8': '0'}
        r = subprocess.run([sys.executable, '-c', CODE], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('\\u65e5', r.stdout)
