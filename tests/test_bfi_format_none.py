from rvtx.rfa import parse_format, SS


def test_format_lines():
    assert parse_format('Format: 2024\nBuild: x') == '2024'
    assert parse_format('Autodesk Revit 2017') == '2017'


def test_unrecognised_is_none_and_has_no_contents_stream():
    f = parse_format('garbage without a year')
    assert f is None                      # must not default to 2024
    assert SS.CONTENTS_BY_FORMAT.get(f, (None, None)) == (None, None)
