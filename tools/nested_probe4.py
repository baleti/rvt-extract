"""nested_probe4.py PROJECT NAME : content-document GUIDs referenced from a family's own segment (remote-host)"""
import sys, os, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
from rvtx import core, rfa, elemtable as ET
prj = core.Project(sys.argv[1]); pd = rfa.ProjectDocs(prj)
import struct
for nm in sys.argv[2:]:
    fr = next(r for r in prj.families() if r['fields'].get('m_name') == nm)
    guid = fr['fields']['m_oFamDoc']['obj']['m_contentDocGUID']['m_guid']; g0, blob = pd.segment(guid)
    own = bytes.fromhex(guid); print(nm, 'own guid', guid, 'seg len', len(blob))
    W = set(blob[k:k + 16] for k in range(len(blob) - 16) if len(set(blob[k:k + 16])) >= 13)
    cd = pd.cd; hits = []
    for k in range(len(cd) - 20):
        w = cd[k:k + 16]
        if w in W and w != own:
            n, = struct.unpack_from('<I', cd, k + 16)
            if 2000 < n < 400000 and k + 20 + n <= len(cd): hits.append((k, w, n))
    print('  candidate guid hits', len(hits))
    for k, w, n in hits[:10]:
        rows = ET.cd_rows(cd[k + 20:k + 20 + n]); docs = collections.Counter(pd.id_doc.get(i) for i in list(rows)[:300])
        print('   guid', w.hex(), 'cd pos', k, 'len', n, 'blob pos', blob.find(w), 'rows', len(rows), 'docs of rows', dict(docs))
