from rvtx import cli
def test_warns_when_short():
    w = cli.mem_warning(100_000_000, 2_000_000_000, False)
    assert w and '--low-memory' in w and 'rc 134' in w
def test_quiet_when_enough_or_unknown():
    assert cli.mem_warning(10_000_000, 64_000_000_000, False) is None
    assert cli.mem_warning(10_000_000, None, False) is None
def test_no_hint_if_already_lowmem():
    assert '--low-memory' not in cli.mem_warning(100_000_000, 1_000_000_000, True)
