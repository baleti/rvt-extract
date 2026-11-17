"""cfbscan must report 0 bad on every lifted rfa under the local run dirs (skipped when absent)."""
import glob, os, subprocess, sys, pytest
DIRS = sorted(glob.glob(os.path.expanduser('~/famlift-run/hd22y*/f')))
@pytest.mark.skipif(not DIRS, reason='no local lift outputs')
def test_cfbscan_clean():
    for d in DIRS:
        r = subprocess.run([sys.executable, 'tools/cfbscan.py', d], capture_output=True, text=True)
        assert ' bad 0 ' in r.stdout, (d, r.stdout[-300:])
