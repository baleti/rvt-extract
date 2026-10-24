"""lat_two.py A.rfa B.rfa : decoded Global/Latest tree diff of two rfas (light)"""
import sys; sys.path.insert(0,'~/src/rvt-extract/tools'); sys.path.insert(0,'~/src/rvt-extract')
from lat_lib import *
from tdiff import walk_diff
a=latest_tree(sys.argv[1]); b=latest_tree(sys.argv[2])
out=[]; walk_diff(a[0],b[0],'',out); print('diffs',len(out))
for o in out[:int(sys.argv[3]) if len(sys.argv)>3 else 40]: print(str(o)[:300])
