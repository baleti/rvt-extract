import os, tempfile
from rvtx import cli
def test_missing_source_exits_2_without_traceback_or_output():
    d = tempfile.mkdtemp()
    out = os.path.join(d, 'o')
    assert cli.main([os.path.join(d, 'nope.rvt'), '--out', out]) == 2
    assert not os.path.exists(out)
