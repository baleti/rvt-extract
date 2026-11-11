from rvtx import cli
def test_2016_refused_unless_experimental():
    assert cli.pre2017_refused('2016', False) and cli.pre2017_refused(2015, False)
    assert not cli.pre2017_refused('2016', True)
def test_2017_up_and_unknown_not_refused():
    for f in ('2017', '2024', 2026, None, 'x'):
        assert not cli.pre2017_refused(f, False)
