"""Partition stream model and writer (own analysis; see HANDOFF.md 'PARTITION FORMAT').

A partition payload holds, per document, three item chains:  H  [id][L][body]  (ElementHeader records, hs 16 with A),
R  [A][id][stamp][L][body]  (element records, stamp = adler32(body)),  Z  same layout (graphics/dummy 'zone' records).
Every chain ends with a terminator (id = -1, L = 0); A = L of the previous item (0 at a chain start, no A at the very first item).
The payload is cut into gzip members (<= LIMIT raw bytes, cut right after an A field, every chain starts a new member) with 32-byte frames."""
import os, struct, zlib, sys, os
WL = os.path.expanduser('~/rvt-research/write-lab')
if WL not in sys.path: sys.path.append(WL)
LIMIT = 131071
GZH = bytes.fromhex('1f8b080000000000000b')
REGION_CODE = {'H': 101, 'R': 102, 'Z': 103}
# year-specific markers (defaults = Revit 2024); filled from the project's own partition stream by rfa.ProjectDocs
K = {'version': 9, 'hdrtag': b'\x7b\x03', 'm0': b'\x75\x0e', 'm1': b'\x7c\x0e', 'blobm': b'\x8f\x0e', 'cdtag': b'\x7b\x03'}


def adler(body):
    return zlib.adler32(body) & 0xFFFFFFFF


def parse_joined(j, W=8, keep0=None):
    """-> list of docs {'H': [(id, body)], 'R': [(id, body, stamp)], 'Z': [...]}; stops at the trailing zero A.
    keep0: optional set of ids; in the FIRST document (the main document of a project partition) bodies of other ids are not copied (b''), which keeps 100+ MB projects small"""
    docs = []; p = 0; NEG = (1 << (8 * W)) - 1
    while p + W + 4 <= len(j):
        doc = {'H': [], 'R': [], 'Z': []}
        first = (p == 0); skip0 = keep0 is not None and not docs
        while True:
            if not first: p += 4
            first = False
            idv = int.from_bytes(j[p:p + W], 'little'); L, = struct.unpack_from('<I', j, p + W)
            doc['H'].append((idv, b'' if skip0 and idv not in keep0 else bytes(j[p + W + 4:p + W + 4 + L]))); p += W + 4 + L
            if idv == NEG: break
        for r in ('R', 'Z'):
            while True:
                p += 4
                idv = int.from_bytes(j[p:p + W], 'little'); st, L = struct.unpack_from('<II', j, p + W)
                doc[r].append((idv, b'' if skip0 and idv not in keep0 else bytes(j[p + W + 8:p + W + 8 + L]), st)); p += W + 8 + L
                if idv == NEG: break
        docs.append(doc)
        if p + 4 >= len(j) or j[p:p + 4] == b'\0\0\0\0' and p + 4 + W + 4 > len(j): break
    return docs


TRIM = 32 << 20


class _Rolling:
    """read-only view of a decoded stream that is produced chunk by chunk; bytes before the read position are dropped (bounded memory)"""
    def __init__(self, chunks):
        self.it = iter(chunks); self.buf = bytearray(); self.base = 0; self.done = False

    def _fill(self, end):
        while not self.done and self.base + len(self.buf) < end:
            try: self.buf += next(self.it)
            except StopIteration: self.done = True

    def get(self, p, n):
        self._fill(p + n)
        return self.buf[p - self.base:p - self.base + n]

    def at_end(self, p, n):
        """True when fewer than n bytes remain at p"""
        self._fill(p + n)
        return self.base + len(self.buf) < p + n

    def trim(self, p):
        if p - self.base > TRIM:
            self._fill(p)          # p may lie beyond what was loaded (skipped bodies)
            del self.buf[:p - self.base]; self.base = p


def parse_stream(chunks, W=8, keep0=None):
    return list(iter_stream(chunks, W, keep0))


def iter_stream(chunks, W=8, keep0=None):
    """generator of the documents of parse_joined over an iterable of decoded chunks without ever holding the whole stream (same result as parse_joined(b''.join(chunks), W, keep0))"""
    R = _Rolling(chunks); docs = []; p = 0; NEG = (1 << (8 * W)) - 1
    while not R.at_end(p, W + 4):
        doc = {'H': [], 'R': [], 'Z': []}
        first = (p == 0); skip0 = keep0 is not None and not docs
        while True:
            if not first: p += 4
            first = False
            idv = int.from_bytes(R.get(p, W), 'little'); L, = struct.unpack('<I', R.get(p + W, 4))
            doc['H'].append((idv, b'' if skip0 and idv not in keep0 else bytes(R.get(p + W + 4, L)))); p += W + 4 + L
            R.trim(p)
            if idv == NEG: break
        for r in ('R', 'Z'):
            while True:
                p += 4
                idv = int.from_bytes(R.get(p, W), 'little'); st, L = struct.unpack('<II', R.get(p + W, 8))
                doc[r].append((idv, b'' if skip0 and idv not in keep0 else bytes(R.get(p + W + 8, L)), st)); p += W + 8 + L
                R.trim(p)
                if idv == NEG: break
        docs.append(doc is None); yield doc
        if R.at_end(p, 5) or bytes(R.get(p, 4)) == b'\0\0\0\0' and R.at_end(p, 4 + W + 4): break


def serialize(docs, W=8):
    """-> (joined bytes, items) ; items = list of (region, doc_index, id_pos, apos_or_None)"""
    NEG = (1 << (8 * W)) - 1
    out = bytearray(); items = []; prevL = None
    for di, doc in enumerate(docs):
        for reg in ('H', 'R', 'Z'):
            recs = doc[reg]
            for idv, body, *stamp in recs:
                L = len(body)
                if reg == 'H':
                    apos = None if prevL is None else len(out)
                    if prevL is not None: out += struct.pack('<I', prevL)
                    items.append((reg, di, len(out), apos)); out += (idv & NEG).to_bytes(W, 'little') + struct.pack('<I', L) + body
                else:
                    apos = len(out); out += struct.pack('<I', prevL)
                    st = 1 if (idv & NEG) == NEG else adler(body)
                    items.append((reg, di, len(out), apos)); out += (idv & NEG).to_bytes(W, 'little') + struct.pack('<II', st, L) + body
                prevL = L
    out += struct.pack('<I', prevL)
    return bytes(out), items


def cut_points(items, total, limit=LIMIT, joined=None, W=8):
    """member start offsets: region starts are forced, otherwise greedy to the largest id-start within limit.
    A single item larger than the limit is cut like Revit does (oracle, LandingPage with an embedded image): its member starts at the item's id, the first chunk
    ends after the item header + 131072 body bytes, further chunks are 131072 bytes, the last chunk continues with the next item's A field."""
    cuts = [0]; idpos = [it[2] for it in items]
    reg_of = [(it[0], it[1]) for it in items]
    starts = {}
    for k, r in enumerate(reg_of): starts.setdefault(r, k)
    first_idx = set(starts.values())
    for k, p in enumerate(idpos):
        if k in first_idx and p != cuts[-1]: cuts.append(p); continue
        nxt = idpos[k + 1] if k + 1 < len(idpos) else total
        if joined is not None and nxt - p > limit:
            if p > cuts[-1]: cuts.append(p)
            hdr = (4 + W) if items[k][0] == 'H' else (8 + W)      # id + (stamp) + length
            end = p + hdr + struct.unpack_from('<I', joined, p + hdr - 4)[0]; b = p + hdr + 131072
            while b < end: cuts.append(b); b += 131072
            if nxt < total and nxt > cuts[-1]: cuts.append(nxt)      # the tail chunk is its own member; the next item starts a new one
            continue
        if nxt - cuts[-1] > limit and p > cuts[-1]: cuts.append(p)
    return cuts


def build_payload(docs, W=8, element_count=None, blob=None, text_len_pad=0, gz_override=None, tail_override=None, doc_guids=None, nf_seq=None, limit=None, hs_adj=0, plain_tail=False):
    """-> payload bytes (before ECC paging) for the Partitions/N stream"""
    joined, items = serialize(docs, W)
    cuts = cut_points(items, len(joined), joined=joined, W=W, **({'limit': limit} if limit else {})); cuts.append(len(joined))
    apos = [it[3] for it in items if it[3] is not None] + [len(joined) - 4]     # the trailing A after the last terminator
    # region code per member
    reg_at = {}
    for it in items: reg_at.setdefault(it[2], (it[0], it[1]))
    idpos = sorted(reg_at)
    members = []
    import bisect
    for k in range(len(cuts) - 1):
        lo, hi = cuts[k], cuts[k + 1]; raw = joined[lo:hi]
        x1 = sum(1 for a in apos if lo <= a < hi)
        reg = items[bisect.bisect_right([it[2] for it in items], lo) - 1][0] if True else 'H'
        # region of the member = region of the first item that starts at lo
        first = next((it for it in items if it[2] == lo), None) or items[bisect.bisect_right([it[2] for it in items], lo) - 1]      # a chunk of an oversized item starts inside it
        hs = ((8 + W) if first[0] == 'H' else (12 + W)) + hs_adj
        x2 = len(raw) - hs * x1; nf = 4
        # chunks of an oversized item (oracle: Revit's LandingPage): first chunk N=6, x1=1, x2=raw-(item header); middle N=7, x1=0, x2=raw; tail (holds the next A) N=5, x1=0, x2=raw-4
        ii = bisect.bisect_right([it[2] for it in items], lo) - 1
        if ii >= 0 and items[ii][2] <= lo and ii + 1 < len(items):
            p0, nx = items[ii][2], items[ii + 1][2]
            if hi - lo > 0 and nx - p0 > LIMIT and not (lo == p0 and hi >= nx - 4):
                if lo == p0: nf, x1, x2 = 6, 1, len(raw) - ((4 + W) if first[0] == 'H' else (8 + W))
                elif hi < nx - 4: nf, x1, x2 = 7, 0, len(raw)
                else: nf, x1, x2 = 5, 0, len(raw) - 4
        co = zlib.compressobj(6, zlib.DEFLATED, -15)
        comp = co.compress(raw) + co.flush()
        gz = GZH + comp + struct.pack('<II', zlib.crc32(raw) & 0xFFFFFFFF, len(raw) & 0xFFFFFFFF)
        if gz_override is not None: gz = gz_override[k]
        members.append(dict(gz=gz, nf=nf, x1=x1, x2=x2, code=REGION_CODE[first[0]] + 3 * 0, doc=first[1], region=first[0]))
    if nf_seq:      # Revit 2016/2017 (real rac_basic_sample_family 2016, 2017): the per-member field is 400 + 4 * member index, not the constant 4 of 2018 and later
        kk = 0; prev = None
        for m in members:
            if m['doc'] != prev: kk = 0; prev = m['doc']      # the sequence restarts with every document (real 2017 nested family)
            if m['nf'] == 4: m['nf'] = nf_seq[0] + nf_seq[1] * kk
            kk += 1
    n_elem = len([1 for it in items if it[0] == 'H' and it[1] == 0]) - 1 if element_count is None else element_count
    m0 = members[0]
    hdr = struct.pack('<Q', K['version']) + K['hdrtag'] + b'\0\0\0\0' + struct.pack('<I', n_elem) + K['m1'] + struct.pack('<I', m0['nf']) + struct.pack('<III', m0['x1'], len(m0['gz']) - 10 + 2, m0['x2']) + bytes([m0['code']]) + b'\0' * 7
    # NB: the stored comp length field is (deflate stream length + 8) = len(gz) - 10 - 8 + 8 ; recompute precisely below
    def comp_field(m): return len(m['gz']) + 8
    hdr = struct.pack('<Q', K['version']) + K['hdrtag'] + b'\0\0\0\0' + struct.pack('<I', n_elem) + K['m1'] + struct.pack('<I', m0['nf']) + struct.pack('<III', m0['x1'], comp_field(m0), m0['x2']) + bytes([m0['code']]) + b'\0' * 7
    assert len(hdr) == 44, len(hdr)
    out = bytearray(hdr)
    for k, m in enumerate(members):
        out += m['gz']
        if k + 1 < len(members):
            n = members[k + 1]
            if (os.environ.get('RVTX_DOCSEP', '0') == '1' or doc_guids is not None) and n['doc'] != m['doc'] and n['region'] == 'H':      # Revit (oracle: 2024 and 2026 own files): the frame after the last member of a document is all zero after the member size
                out += K['m0'] + struct.pack('<I', comp_field(m)) + K['m1'] + b'\0' * 16
                if doc_guids is not None and doc_guids.get(n['doc']):      # Revit (real 2022 nested family): each document ends with the tail block, naming the next document (element count, content GUID), then the descriptor of its first member
                    cnt, g = doc_guids[n['doc']]; t = 'Data generated by Autodesk® Revit®'; ct = struct.unpack('<H', K['cdtag'])[0]
                    out += ((K['blobm'] + struct.pack('<I', 64) + (blob or b'\0' * 64) + struct.pack('<I', len(t)) + t.encode('utf-16le')) if not plain_tail else b'') + K['cdtag'] + b'\xff' * 4 + struct.pack('<H', ct - 1) + struct.pack('<I', cnt) + g
                    out += K['m1'] + struct.pack('<I', n['nf']) + struct.pack('<III', n['x1'], comp_field(n), n['x2']) + bytes([n['code']]) + b'\0' * 7
                continue
            out += K['m0'] + struct.pack('<I', comp_field(m)) + K['m1'] + struct.pack('<I', n['nf']) + struct.pack('<III', n['x1'], comp_field(n), n['x2']) + bytes([n['code']]) + b'\0' * 7
    if tail_override is not None: return bytes(out) + tail_override
    out += K['m0'] + struct.pack('<I', comp_field(members[-1])) + K['m1'] + b'\0' * 16
    if plain_tail: return bytes(out) + K['cdtag'] + b'\0\0\0\0\xff\xff\xff\xff' + b'\0' * 4 + b'\0' * text_len_pad      # Revit 2016/2017: no blob and text block
    out += K['blobm'] + struct.pack('<I', 64) + (blob or b'\0' * 64)
    t = 'Data generated by Autodesk® Revit®'
    out += struct.pack('<I', len(t)) + t.encode('utf-16le') + K['cdtag'] + b'\0\0\0\0\xff\xff\xff\xff' + b'\0' * 4
    return bytes(out) + b'\0' * text_len_pad


PAGE_STORED, PAGE_PAYLOAD = 65249, 64896


def last_page_size(C):
    """size N of the last ECC page for C payload bytes: the smallest N that Revit is known to write (nladder.OBSERVED) or, from ~16.5 KB on, the
    L=2047 ladder with an odd number of codewords u, whose capacity holds C. Other N have plausible ECC parameters but Revit rejects them (oracle test)."""
    import ecc
    from .nladder import OBSERVED, VERIFIED
    vc = [N for N in VERIFIED if ecc.data_capacity(N) >= C]
    if vc: return min(vc)
    cands = [N for N in OBSERVED if ecc.data_capacity(N) >= C and (N < 16500 or (ecc.params(N) or (0, 0, 0))[2] == 2047)]   # large N off the 2047 ladder (19227, 23331, 52813) crash Revit 2024 (oracle, 2026-10-20)
    best = min(cands) if cands else None
    u = 67
    while u < 256:
        N = -(-u * 2047 // 8); p = ecc.params(N)
        if p and p == (11, u, 2047) and ecc.data_capacity(N) >= C:
            if best is None or N < best: best = N
            break
        u += 2
    if best is None: raise ValueError('payload remainder too large')
    return best


def page_stream(payload):
    """ECC-page a payload (Revit stream paging): full pages of 64896 data bytes + a last page sized by last_page_size (zero padded to its capacity)"""
    import ecc, rvtw
    if payload and len(payload) % PAGE_PAYLOAD == 0: payload = payload + b'\0' * 8      # Revit always ends a stream with a partial page; zero padding after the data is ignored
    full = len(payload) // PAGE_PAYLOAD; out = []
    for i in range(full): out.append(ecc.parity(payload[i * PAGE_PAYLOAD:(i + 1) * PAGE_PAYLOAD], PAGE_STORED))
    tail = payload[full * PAGE_PAYLOAD:]
    if tail:
        N = last_page_size(len(tail)); cap = ecc.data_capacity(N)
        out.append(ecc.parity(tail + b'\0' * (cap - len(tail)), N))
    return b''.join(out)
