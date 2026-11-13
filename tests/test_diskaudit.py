import json, subprocess, sys, pathlib, shutil
import olefile  # noqa
T = pathlib.Path(__file__).parent.parent / 'tools' / 'diskaudit.py'
def _run(d): return subprocess.run([sys.executable, str(T), str(d)], capture_output=True, text=True)
def test_flags_missing_and_unlisted(tmp_path):
    (tmp_path / 'manifest.json').write_text(json.dumps({'families': [{'name': 'a', 'rfa': {'file': 'a.rfa', 'status': 'written'}}]}))
    r = _run(tmp_path); assert r.returncode == 1 and 'missing' in r.stdout
    (tmp_path / 'manifest.json').write_text(json.dumps({'families': []}))
    (tmp_path / 'b.rfa').write_bytes(b'x'); r = _run(tmp_path); assert r.returncode == 1 and 'unlisted' in r.stdout
