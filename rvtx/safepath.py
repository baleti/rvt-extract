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


def safe_name(s: str | None, maxlen=120) -> str:
    """Sanitize a name, preserving NFC Unicode and hashing truncations.

    The checksum covers the entire original input, before sanitization.
    A length below nine is supported only when no truncation is needed.
    """
    original = s or ""
    normalized = unicodedata.normalize("NFC", original)
    name = "".join(
        "_" if char in _FORBIDDEN or unicodedata.category(char) == "Cc"
        else char
        for char in normalized
    ).strip(" .") or "Unnamed"
    if _DEVICE.fullmatch(name.split(".", 1)[0]):
        name += "_"
    return _shorten(name, maxlen, original)


class Namer:
    """Allocate names in memory, with independent state per directory key."""

    def __init__(self):
        self._seen: dict[str, set[str]] = {}

    def take(self, directory: str, name: str, ext: str = "") -> str:
        """Return an unused sanitized name, preserving the supplied extension."""
        seen = self._seen.setdefault(directory, set())
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
