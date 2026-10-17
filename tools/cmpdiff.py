"""cmpdiff.py PROJECT RFA OUT.pkl : for a sample of rfa records absent from the family-embedded set, raw bytes in both files (remote-host)"""
import sys, os, pickle, collections
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from rawrecs import rawrecs
rfa = rawrecs(sys.argv[2])
by = collections.defaultdict(list)
for k in rfa: by[k[1]].append(k)
sample = [k for c in ('GStyleElem', 'MaterialElem', 'LinePatternElem', 'FillPatternElem', 'AppearanceAssetElem', 'PropertySetElement') for k in sorted(by[c])[:4]]
prj = rawrecs(sys.argv[1], only_ids=[k[0] for k in sample])
pickle.dump({'rfa': {k: [(a, b) for a, b, *_ in rfa[k]] for k in sample}, 'prj': {k: [(a, b) for a, b, *_ in prj.get(k, [])] for k in sample}}, open(sys.argv[3], 'wb')); print(len(sample))
