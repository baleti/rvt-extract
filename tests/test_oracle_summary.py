import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
import oracle_summary as O

T1 = "OPEN\tA__x.xfa\tisFam=True\nCNT\tA__x.xfa\tFoo\t3\nOPENFAIL\tA__y.xfa\tCorruptModelException: bad\nDIALOG\tA__y.xfa\tid\ttext\n\nOPEN\n"
T2 = "OPEN\tA__y.xfa\tok\nOPENFAIL\tB__z.xfa\tInternalException: boom\nOPEN\tsolo.xfa\tx\n"

def test_parse():
    assert O.parse(T1) == [('open', 'A__x.xfa', ''), ('fail', 'A__y.xfa', 'CorruptModelException')]

def test_merge_last_wins():
    m = O.merge([O.parse(T1), O.parse(T2)])
    assert m['A__y.xfa'] == ('open', '')
    assert m['B__z.xfa'] == ('fail', 'InternalException')

def test_by_category():
    m = O.merge([O.parse(T1), O.parse(T2)])
    c = O.by_category(m)
    assert list(c) == ['A', 'B', 'solo']
    assert c['A'] == {'open': 2, 'fail': 0} and c['B'] == {'open': 0, 'fail': 1}

def test_missing_and_table():
    m = O.merge([O.parse(T1)])
    assert O.missing(m, ['A__x.xfa', 'Q__q.xfa', 'A__w.xfa']) == ['A__w.xfa', 'Q__q.xfa']
    t = O.table(m, ['A__x.xfa', 'A__y.xfa', 'Q__q.xfa']).split('\n')
    assert t[0].split() == ['category', 'open', 'fail', 'missing']
    assert t[-1].split() == ['TOTAL', '1', '1', '1']
    assert all(l == l.rstrip() for l in t)
