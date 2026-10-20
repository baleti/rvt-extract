"""nested_probe2.py PROJECT GTRFA NAME : nested family content-document segments, project vs Revit-saved rfa (remote-host)"""
import sys, os, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx, olefile, rvt2text as T, rvtfmt
from rvtx import core, rfa, partition as PT
prj = core.Project(sys.argv[1]); pd = rfa.ProjectDocs(prj); B = rfa.Builder(pd)
o = olefile.OleFileIO(sys.argv[2]); gcd = rvtfmt.inflate_stream(o.openstream('Global/ContentDocuments').read())[1]
fr = next(r for r in prj.families() if r['fields'].get('m_name') == sys.argv[3]); k = pd.family_doc_index(fr)
doc = pd.docs[k]; fid = fr['id']
print('gt CD len', len(gcd), 'head', gcd[:40].hex())
cnt = collections.Counter(); first = {}
for i, b, s in doc['R']:
    if i == (1 << 64) - 1: continue
    out = set(); rfa._eids(B.dec(b)[1], out)
    for e in out:
        k2 = pd.id_doc.get(e)
        if k2 and k2 != k: cnt[k2] += 1; first.setdefault(k2, (i, B.class_of(b), e))
print('docs referenced from own records', dict(cnt)); print('first refs', first)
