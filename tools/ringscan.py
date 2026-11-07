"""ringscan.py DIR : owner-ring scan of lifted 2020 .rfa files (4-byte ElemTable rows). Reads the OUTPUT convention (owner = trailing word of each written row, RVTX_OWNER4=next); the default extraction-side convention reports false rings on written files. Prints RING lines and a summary."""
import sys, os, glob
os.environ['RVTX_OWNER4'] = 'next'
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
import rvtx
import olefile, rvt2text as T
from rvtx import elemtable as ET
n = rings = skipped = 0
for p in sorted(glob.glob(os.path.join(sys.argv[1], '**', '*.rfa'), recursive=True)):
    if os.sep + 'compact' + os.sep in p: continue
    try:
        o = olefile.OleFileIO(p); seg = o.openstream('Global/ElemTable').read()
        try: seg = T.joined(seg)
        except Exception: pass
        rows = ET.cd_rows4(seg); fix = ET.owner_cycles4(list(rows), set(rows), rows)
    except Exception as e:
        skipped += 1; print('SKIP', os.path.basename(p)[:30], type(e).__name__); continue
    n += 1
    if fix: rings += 1; print('RING', os.path.basename(p)[:30], sorted(fix)[:5])
print('scanned', n, 'with rings', rings, 'skipped', skipped)
