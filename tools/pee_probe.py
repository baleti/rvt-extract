"""pee_probe.py PROJECT : are the ParamElemExternal ids Revit adds to Rebar Shape rfas (187616..187627) in the project main doc? (remote-host)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')); sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import rvtx
from rvtx import core, rfa
prj = core.Project(sys.argv[1]); pd = rfa.ProjectDocs(prj)
import collections
print('ParamElemExternal in main:', sum(1 for r in pd.byid.values() if r['class'] == 'ParamElemExternal'))
for i in range(187612, 187630):
    r = pd.byid.get(i); print(i, r['class'] if r else None, (str({k: v for k, v in list(r['fields'].items())[:6]})[:300] if r else ''))
fr = next(r for r in prj.families() if r['fields'].get('m_name') == '00')
print('family 00 fields', list(fr['fields'].keys())[:40])
