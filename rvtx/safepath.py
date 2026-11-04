"""Pure helpers for safe file names and bounded output paths."""

import os
import re
import unicodedata
import zlib


_FORBIDDEN = frozenset('<>:"/\\|?*')
_DEVICE = re.compile(r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$", re.I)


def _shorten(name: str, maxlen: int, original: str) -> str:
    if len(name) <= maxlen:
        return name
    if maxlen < 9:
        raise ValueError("A shortened name needs at least nine characters")
    checksum = zlib.crc32(original.encode("utf-8"))
    return name[:maxlen - 9] + f"~{checksum:08x}"


def safe_name(s: str | None, maxlen=120, maxbytes=200) -> str:
    """Sanitize a name, preserving NFC Unicode and hashing truncations.

    The checksum covers the entire original input, before sanitization.
    A length below nine is supported only when no truncation is needed.
    """
    original = re.sub("[\ud800-\udfff]", "\ufffd", s or "")   # lone UTF-16 surrogates cannot be encoded as UTF-8
    normalized = unicodedata.normalize("NFC", original)
    name = "".join(
        "_" if char in _FORBIDDEN or unicodedata.category(char) == "Cc"
        else char
        for char in normalized
    ).strip(" .") or "Unnamed"
    if _DEVICE.fullmatch(name.split(".", 1)[0]):
        name += "_"
    name = _shorten(name, maxlen, original)
    if len(name.encode("utf-8")) > maxbytes:
        # file systems limit a name component to 255 BYTES; 120 CJK/emoji characters are 360-480 bytes
        tail = f"~{zlib.crc32(original.encode('utf-8')):08x}"
        head = name
        while len((head + tail).encode("utf-8")) > maxbytes:
            head = head[:-1]
        name = head + tail
    return name


class Namer:
    """Allocate names in memory, with independent state per directory key."""

    def __init__(self):
        self._seen: dict[str, set[str]] = {}

    def take(self, directory: str, name: str, ext: str = "") -> str:
        """Return an unused sanitized name, preserving the supplied extension."""
        seen = self._seen.setdefault(directory.lower(), set())
        base = safe_name(name)
        candidate = base + ext
        number = 2
        while candidate.lower() in seen:
            candidate = f"{base} ({number}){ext}"
            number += 1
        seen.add(candidate.lower())
        return candidate


def relpath_budget(root: str, parts: list[str], limit=240) -> list[str]:
    """Shorten longest components to fit, without modifying the input list.

    Ties are resolved by component order. Every shortened component keeps
    a checksum of its original value and needs at least nine characters.
    """
    result = list(parts)
    while len(os.path.join(root, *result)) > limit:
        eligible = [i for i, part in enumerate(result) if len(part) > 9]
        if not eligible:
            raise ValueError("Path cannot fit within the requested limit")
        index = max(eligible, key=lambda i: len(result[i]))
        result[index] = _shorten(
            parts[index], len(result[index]) - 1, parts[index]
        )
    return result


def rfa_target(root: str, category: str, name: str, limit=240):
    """Return (category dir name, family stem) so root/families/<cat>/<stem> (~NN) .rfa stays under the Windows path limit."""
    cat, stem = safe_name(category), safe_name(name)
    reserve = len(' (99).rfa')
    try: cat, stem = relpath_budget(os.path.join(root, 'families'), [cat, stem], limit - reserve)
    except ValueError: pass      # output root alone is too long: keep the 120-char names rather than fail every family
    return cat, stem


def stale_rfa(out, families):
    """relative paths of .rfa files under out/families that this run's manifest entries do not list (left by an earlier run in the same --out)"""
    import os
    listed = {os.path.normpath(os.path.join(out, (e.get('rfa') or {}).get('file', ''))) for e in families if e.get('rfa')}
    return sorted(os.path.relpath(os.path.join(dp, f), out) for dp, _, fs in os.walk(os.path.join(out, 'families')) for f in fs if f.endswith('.rfa') and os.path.normpath(os.path.join(dp, f)) not in listed)


INCOMPLETE = os.path.join('families', 'INCOMPLETE')


def mark_incomplete(out):
    """Create families/INCOMPLETE; it is removed only after the final manifest is written (a killed run leaves it, plus a checkpoint manifest at most one family behind)."""
    os.makedirs(os.path.join(out, 'families'), exist_ok=True)
    open(os.path.join(out, INCOMPLETE), 'w').write('extraction started; absent when the run finished. .rfa files without a manifest entry may exist.\n')


def clear_incomplete(out):
    try: os.unlink(os.path.join(out, INCOMPLETE))
    except FileNotFoundError: pass
