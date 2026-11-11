from rvtx import cli
def test_rfa_source_with_zero_families_warns():
    assert 'family document' in cli.family_source_warning('/x/Door.RFA', 0)
def test_project_or_nonzero_silent():
    assert cli.family_source_warning('/x/p.rvt', 0) is None
    assert cli.family_source_warning('/x/Door.rfa', 3) is None
