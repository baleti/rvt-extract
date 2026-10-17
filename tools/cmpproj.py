"""cmpproj.py PROJECT HASHES.json OUT.json : which of the rfa's records (id|class -> sha1) exist byte-identical in the project (remote-host)"""
import sys, os, json, hashlib, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
from rawrecs import rawrecs
H = json.load(open(sys.argv[2])); ids = {int(k.split('|')[0]) for k in H}
rr = rawrecs(sys.argv[1], only_ids=ids)
res = collections.Counter(); bycls = collections.defaultdict(collections.Counter)
for k, h in H.items():
    i, c = k.split('|'); v = rr.get((int(i), c))
    s = 'missing' if not v else ('identical' if any(hashlib.sha1(x[1]).hexdigest() == h for x in v) else 'differ')
    res[s] += 1; bycls[c][s] += 1
json.dump({'total': dict(res), 'by_class': {c: dict(v) for c, v in bycls.items()}}, open(sys.argv[3], 'w'), indent=1); print(dict(res))
