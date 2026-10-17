import sys
def align(a, b, W=32):
    """runs (a_off, b_off, len) where a[a_off:+len] == b[b_off:+len], greedy left to right with window anchors"""
    idx = {}
    for j in range(0, len(b) - W + 1):
        idx.setdefault(b[j:j + W], []).append(j)
    runs = []; i = 0; last_b = 0
    while i <= len(a) - W:
        c = idx.get(a[i:i + W])
        if not c: i += 1; continue
        j = min(c, key=lambda x: (abs(x - last_b)))
        n = W
        while i + n < len(a) and j + n < len(b) and a[i + n] == b[j + n]: n += 1
        runs.append((i, j, n)); i += n; last_b = j + n
    return runs
