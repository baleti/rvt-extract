import os, tempfile
from rvtx import cli
def test_helper_cases():
    d = tempfile.mkdtemp(); f = os.path.join(d, 'file'); open(f, 'w').close()
    assert cli.out_unwritable(os.path.join(d, 'a', 'b', 'c')) is None and not os.path.exists(os.path.join(d, 'a'))
    assert cli.out_unwritable(os.path.join(f, 'x')) is None      # left to the later guard
    ro = os.path.join(d, 'ro'); os.mkdir(ro); os.chmod(ro, 0o500)
    try:
        if os.access(ro, os.W_OK): return      # root: cannot test
        assert 'cannot write' in cli.out_unwritable(os.path.join(ro, 'x', 'y'))
    finally: os.chmod(ro, 0o700)
def test_main_refuses_unwritable_parent_before_reading(capsys):
    d = tempfile.mkdtemp(); ro = os.path.join(d, 'ro'); os.mkdir(ro); os.chmod(ro, 0o500)
    try:
        if os.access(ro, os.W_OK): return
        assert cli.main([os.path.join(d, 'x.rvt'), '--out', os.path.join(ro, 'o')]) == 2
        assert 'cannot write in' in capsys.readouterr().err
    finally: os.chmod(ro, 0o700)
