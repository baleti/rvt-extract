"""sharedset.py RFA_ROOT OUT.pkl : (id,class,sha1) of every record of every rfa under RFA_ROOT (remote-host)"""
import sys, os, glob, pickle, hashlib
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from rawrecs import rawrecs
res = {}
for f in sorted(glob.glob(os.path.join(sys.argv[1], '**', '*.rfa'), recursive=True)):
    try:
        rr = rawrecs(f)
        res[os.path.relpath(f, sys.argv[1])] = {k: hashlib.sha1(v[-1][1]).hexdigest() for k, v in rr.items()}
        print(f, len(rr), flush=True)
    except Exception as e: print('FAIL', f, e, flush=True)
pickle.dump(res, open(sys.argv[2], 'wb'))
