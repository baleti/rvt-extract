import os, tempfile
from rvtx import cli
def test_invalid_match_regex_exits_2_without_traceback_or_output(capsys):
    d = tempfile.mkdtemp(); out = os.path.join(d, 'o')
    assert cli.main([os.path.join(d, 'x.rvt'), '--match', '(', '--out', out]) == 2
    assert 'not a valid regular expression' in capsys.readouterr().err
    assert not os.path.exists(out)
