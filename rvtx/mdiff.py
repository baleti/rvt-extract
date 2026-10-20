"""Deterministic comparisons and reports for family manifests (stdlib only)."""

import json


_FIELDS = ("datatype", "formula", "shared")


def _index(manifest):
    """Validate the manifest and index families; later duplicates win."""
    if not isinstance(manifest, list):
        raise ValueError("manifest must be a JSON list")
    indexed = {}
    for family in manifest:
        if not isinstance(family, dict):
            raise ValueError("each family must be an object")
        for field in ("category", "name"):
            if not isinstance(family.get(field), str):
                raise ValueError("family %s must be a string" % field)
        types = family.get("types")
        if not isinstance(types, list) or any(not isinstance(t, str) for t in types):
            raise ValueError("family types must be a list of strings")
        params = family.get("parameters")
        if not isinstance(params, list):
            raise ValueError("family parameters must be a list")
        for param in params:
            if not isinstance(param, dict) or not isinstance(param.get("name"), str):
                raise ValueError("each parameter must have a string name")
            for field, kind in (("datatype", str), ("shared", bool), ("formula", str)):
                if field in param and not (
                    field == "formula" and param[field] is None
                ) and not isinstance(param[field], kind):
                    raise ValueError("invalid parameter %s" % field)
        if type(family.get("embedded_records")) is not int:
            raise ValueError("family embedded_records must be an integer")
        indexed[(family["category"], family["name"])] = family
    return indexed


def diff(a: list, b: list) -> dict:
    """Compare known fields only, without modifying either input.

    Type order and repetitions are ignored. Parameters are keyed by name,
    with later duplicates winning. Missing optional fields compare as None.
    """
    a, b = _index(a), _index(b)
    result = {
        "only_a": [list(k) for k in sorted(a.keys() - b.keys())],
        "only_b": [list(k) for k in sorted(b.keys() - a.keys())],
        "changed": [],
        "same": 0,
    }
    for category, name in sorted(a.keys() & b.keys()):
        left, right = a[(category, name)], b[(category, name)]
        ta, tb = set(left["types"]), set(right["types"])
        pa = {p["name"]: p for p in left["parameters"]}
        pb = {p["name"]: p for p in right["parameters"]}
        changes = [
            {"name": pname, "field": field, "a": pa[pname].get(field),
             "b": pb[pname].get(field)}
            for pname in sorted(pa.keys() & pb.keys())
            for field in _FIELDS
            if pa[pname].get(field) != pb[pname].get(field)
        ]
        counts = [left["embedded_records"], right["embedded_records"]]
        item = {
            "category": category, "name": name,
            "types_added": sorted(tb - ta), "types_removed": sorted(ta - tb),
            "params_added": sorted(pb.keys() - pa.keys()),
            "params_removed": sorted(pa.keys() - pb.keys()),
            "params_changed": changes,
            "records": counts if counts[0] != counts[1] else None,
        }
        if any(item[k] for k in (
            "types_added", "types_removed", "params_added", "params_removed",
            "params_changed", "records",
        )):
            result["changed"].append(item)
        else:
            result["same"] += 1
    return result


def _summary(d):
    return "%d same, %d changed, %d only in A, %d only in B" % (
        d["same"], len(d["changed"]), len(d["only_a"]), len(d["only_b"]),
    )


def _details(item):
    for field, label in (
        ("types_added", "type added"), ("types_removed", "type removed"),
        ("params_added", "parameter added"), ("params_removed", "parameter removed"),
    ):
        for name in item[field]:
            yield "%s: %s" % (label, json.dumps(name, ensure_ascii=False))
    for change in item["params_changed"]:
        yield "parameter %s %s: %s -> %s" % (
            json.dumps(change["name"], ensure_ascii=False), change["field"],
            json.dumps(change["a"], ensure_ascii=False),
            json.dumps(change["b"], ensure_ascii=False),
        )
    if item["records"] is not None:
        yield "records: %s -> %s" % tuple(item["records"])


def _line(value):
    return str(value).replace("\r", "\\r").replace("\n", "\\n")


def render_text(d):
    """Render one line per family, followed by a summary."""
    lines = []
    for key, marker, side in (("only_a", "-", "A"), ("only_b", "+", "B")):
        for category, name in d[key]:
            lines.append("%s %s / %s  (only in %s)" % (
                marker, _line(category), _line(name), side,
            ))
    for item in d["changed"]:
        lines.append("~ %s / %s  %s" % (
            _line(item["category"]), _line(item["name"]),
            "; ".join(_details(item)),
        ))
    return "\n".join(lines + [_summary(d)]) + "\n"


def _cell(value):
    return (_line(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace("\\", "&#92;").replace("|", "&#124;"))


def render_md(d):
    """Render a Markdown table for each difference section."""
    lines = []
    for key, title in (("only_a", "Only in A"), ("only_b", "Only in B")):
        lines.extend(["## " + title, "", "| Category | Name |", "| --- | --- |"])
        for category, name in d[key]:
            lines.append("| %s | %s |" % (_cell(category), _cell(name)))
        lines.append("")
    lines.extend(["## Changed", "", "| Category | Name | Changes |",
                  "| --- | --- | --- |"])
    for item in d["changed"]:
        lines.append("| %s | %s | %s |" % (
            _cell(item["category"]), _cell(item["name"]),
            "<br>".join(_cell(detail) for detail in _details(item)),
        ))
    return "\n".join(lines + ["", _summary(d)]) + "\n"
