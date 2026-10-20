"""nested_probe.py PROJECT GTRFA NAME : compare the nested documents of a Revit-saved rfa with the project's documents (remote-host)"""
import sys, os, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx, olefile, rvt2text as T
from rvtx import core, rfa, partition as PT
prj = core.Project(sys.argv[1]); pd = rfa.ProjectDocs(prj)
o = olefile.OleFileIO(sys.argv[2]); gd = PT.parse_joined(T.joined(o.openstream('Partitions/0').read()), 8)
fr = next(r for r in prj.families() if r['fields'].get('m_name') == sys.argv[3])
k = pd.family_doc_index(fr); print('own doc k', k, 'project docs', len(pd.docs) - 1)
NEG = (1 << 64) - 1
for gi, doc in enumerate(gd):
    ids = [i for i, *_ in doc['H'] if i != NEG]
    ks = collections.Counter(pd.id_doc.get(i) for i in ids)
    print('gt doc', gi, len(ids), 'id range', min(ids), max(ids), 'project doc of ids:', ks.most_common(4))
    best = ks.most_common(1)[0][0]
    if best and gi:
        pdoc = pd.docs[best]; Hp = {i: b for i, b in pdoc['H']}; Rp = {i: b for i, b, s in pdoc['R']}; Zp = {i: b for i, b, s in pdoc['Z']}
        Hg = {i: b for i, b in doc['H']}; Rg = {i: b for i, b, s in doc['R']}; Zg = {i: b for i, b, s in doc['Z']}
        for nm, a, b in (('H', Hp, Hg), ('R', Rp, Rg), ('Z', Zp, Zg)):
            print('  ', nm, 'project', len(a), 'gt', len(b), 'only proj', len(set(a) - set(b)), 'only gt', len(set(b) - set(a)), 'bytes differ', sum(1 for i in set(a) & set(b) if a[i] != b[i]))
