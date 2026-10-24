"""Summarize tab-separated file-open check results."""


def parse(text):
    """Return open and failure entries in their original order."""
    entries = []
    for line in text.splitlines():
        columns = line.split("\t")
        if len(columns) < 2:
            continue
        kind, filename = columns[:2]
        if kind == "OPEN":
            entries.append(("open", filename, ""))
        elif kind == "OPENFAIL":
            detail = columns[2].split(":", 1)[0].strip() if len(columns) > 2 else ""
            entries.append(("fail", filename, detail))
    return entries


def merge(results_list):
    """Combine chronological results, retaining the last entry per file."""
    return {
        filename: (status, detail)
        for results in results_list
        for status, filename, detail in results
    }


def _category(filename):
    if "__" in filename:
        return filename.split("__", 1)[0]
    return filename[:-4] if filename.endswith(".xfa") else filename


def by_category(merged):
    """Count final open and failure statuses by sorted category."""
    counts = {}
    for filename, (status, _) in merged.items():
        category = _category(filename)
        counts.setdefault(category, {"open": 0, "fail": 0})[status] += 1
    return {category: counts[category] for category in sorted(counts)}


def missing(merged, expected):
    """Return distinct expected file names that have no result, sorted."""
    return sorted(set(expected).difference(merged))


def table(merged, expected=None):
    """Render category counts, including missing-only categories and totals."""
    counts = by_category(merged)
    absent = {}
    for filename in missing(merged, expected) if expected is not None else ():
        category = _category(filename)
        absent[category] = absent.get(category, 0) + 1
    rows = []
    for category in sorted(counts.keys() | absent.keys()):
        count = counts.get(category, {"open": 0, "fail": 0})
        rows.append((category, count["open"], count["fail"], absent.get(category, 0)))
    totals = tuple(sum(row[index] for row in rows) for index in range(1, 4))
    rows.append(("TOTAL", *totals))
    headings = ("category", "open", "fail", "missing")
    widths = [
        max(len(headings[index]), *(len(str(row[index])) for row in rows))
        for index in range(4)
    ]
    lines = ["category  open  fail  missing"]
    for row in rows:
        lines.append("  ".join([
            row[0].ljust(widths[0]),
            *(str(row[index]).rjust(widths[index]) for index in range(1, 4)),
        ]))
    return "\n".join(lines)
