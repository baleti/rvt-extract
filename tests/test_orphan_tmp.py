import os, subprocess, tempfile, unittest
from rvtx import cli


class Orphan(unittest.TestCase):
    def test_dead_pid_removed_live_and_real_kept(self):
        d = tempfile.mkdtemp(); os.makedirs(d + '/families/c')
        p = subprocess.Popen(['true']); p.wait()
        dead = '%s/families/c/a.rfa.tmp%d' % (d, p.pid); live = '%s/families/c/b.rfa.tmp%d' % (d, os.getpid()); real = d + '/families/c/a.rfa'
        for f in (dead, live, real): open(f, 'wb').write(b'x')
        gone = cli.sweep_orphan_tmp(d)
        self.assertEqual(gone, [dead]); self.assertTrue(os.path.exists(live) and os.path.exists(real) and not os.path.exists(dead))
