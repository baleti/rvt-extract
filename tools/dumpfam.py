#!/usr/bin/env python3
"""dumpfam.py PROJECT OUT.pkl NAME[,NAME...] : decoded + raw records, content-doc segment bytes and Formats/Latest of the named embedded families (remote-host)"""
import sys, os, pickle
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
from rvtx import core
import olefile, rvtfmt
path, out, names = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
prj = core.Project(path)
docs, st = core.scan_family_docs(prj, raw=True, only=names)
o = olefile.OleFileIO(path)
cd = rvtfmt.inflate_stream(o.openstream('Global/ContentDocuments').read())[1]
fam = {r['id']: r for r in prj.families() if r['fields'].get('m_name') in names}
streams = {'/'.join(e): o.openstream('/'.join(e)).read() for e in o.listdir(streams=True) if not '/'.join(e).startswith('Partitions')}
pickle.dump({'docs': docs, 'fam': fam, 'cd': cd, 'streams': streams, 'stats': st, 'W': prj.W}, open(out, 'wb'))
print({k: len(v['records']) for k, v in docs.items()})
