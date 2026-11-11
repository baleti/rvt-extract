import os, tempfile, pytest
from rvtx import cli
@pytest.mark.skipif(not hasattr(os, 'mkfifo'), reason='posix only')
def test_fifo_source_refused_not_hung(capsys):
    d = tempfile.mkdtemp(); f = os.path.join(d, 'p.rvt'); os.mkfifo(f)
    assert cli.main([f, '--out', os.path.join(d, 'o')]) == 2
    assert 'not a regular file' in capsys.readouterr().err
    assert not os.path.exists(os.path.join(d, 'o'))
