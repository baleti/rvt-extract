import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import rvtx  # noqa
from rvtx import partition as PT, nladder
import ecc


def test_last_page_size_is_verified_and_fits():
    for C in (1, 500, 2117, 2153, 10000, 52353, 64000):
        N = PT.last_page_size(C)
        assert ecc.data_capacity(N) >= C
        assert N in nladder.VERIFIED


def test_known_bad_sizes_never_chosen():
    for C in range(1900, 2200, 7):
        assert PT.last_page_size(C) != 2197
    assert PT.last_page_size(52353) != 52813


def test_page_stream_roundtrip_parity():
    s = PT.page_stream(b'\x01' * 5000)
    assert ecc.check(s[-(len(s) % 65249):])
