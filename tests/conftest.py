import atexit, shutil, tempfile

# many tests use tempfile.mkdtemp() without cleanup; on a shared tmpfs /tmp that leaked dirs until the disk was full.
# Route all of them into one session dir that is removed at exit.
_root = tempfile.mkdtemp(prefix='rvtx-tests-')
tempfile.tempdir = _root
atexit.register(shutil.rmtree, _root, True)
