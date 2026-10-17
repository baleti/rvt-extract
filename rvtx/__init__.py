"""rvt-extract: lift families (and other content) out of Revit project files without Revit."""
import os, sys
RESEARCH = os.environ.get('RVT_RESEARCH', os.path.expanduser('~/rvt-research'))
if RESEARCH not in sys.path: sys.path.insert(0, RESEARCH)
os.environ.setdefault('RVT_GEOM', '1')
