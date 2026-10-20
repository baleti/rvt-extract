"""Read, write, and merge Revit shared parameter text using only the stdlib."""

import re
import uuid


_PARAM_HEADER = (
    "*PARAM\tGUID\tNAME\tDATATYPE\tDATACATEGORY\tGROUP\tVISIBLE"
    "\tDESCRIPTION\tUSERMODIFIABLE\tHIDEWHENNOVALUE"
)


def _clean(value):
    return re.sub(r"[\t\r\n]+", " ", value)


def _guid(value):
    return str(uuid.UUID(value))


def write(groups, params):
    """Return deterministic tab-separated text with CRLF line endings."""
    groups = sorted(groups, key=lambda group: group[0])
    group_ids = {group_id for group_id, _ in groups}
    normalized = []
    for param in params:
        param = dict(param)
        param["guid"] = _guid(param["guid"])
        if param["group"] not in group_ids:
            raise ValueError("Undeclared parameter group: %r" % param["group"])
        normalized.append(param)
    normalized.sort(key=lambda p: (p["group"], p["name"].lower(), p["guid"]))
    lines = [
        "# This is a Revit shared parameter file.",
        "# Do not edit manually.",
        "*META\tVERSION\tMINVERSION",
        "META\t2\t1",
        "*GROUP\tID\tNAME",
        "# Parameter groups",
    ]
    lines.extend("GROUP\t%d\t%s" % (gid, _clean(name)) for gid, name in groups)
    lines.append(_PARAM_HEADER)
    for param in normalized:
        lines.append("\t".join([
            "PARAM", param["guid"], _clean(param["name"]), param["datatype"],
            param.get("datacategory", ""), str(param["group"]),
            "1" if param.get("visible", True) else "0",
            _clean(param.get("description", "")),
            "1" if param.get("usermodifiable", True) else "0",
            "1" if param.get("hidewhennovalue", False) else "0",
        ]))
    return "\r\n".join(lines) + "\r\n"


def _boolean(value):
    if value not in ("0", "1"):
        raise ValueError("Expected a boolean column containing 0 or 1")
    return value == "1"


def parse(text):
    """Parse text, tolerating comments, unknown records and omitted suffixes."""
    groups, params = [], []
    for line in text.lstrip("\ufeff").splitlines():
        columns = line.split("\t")
        if columns[0] == "GROUP":
            if len(columns) < 3:
                raise ValueError("GROUP requires an ID and name")
            groups.append((int(columns[1]), columns[2]))
        elif columns[0] == "PARAM":
            if len(columns) < 6:
                raise ValueError("PARAM requires GUID, name, datatype, category and group")
            # Optional trailing columns: visible, description, modifiable, hide.
            defaults = ["1", "", "1", "0"]
            columns += defaults[max(0, len(columns) - 6):]
            params.append({
                "guid": _guid(columns[1]),
                "name": columns[2],
                "datatype": columns[3],
                "datacategory": columns[4],
                "group": int(columns[5]),
                "visible": _boolean(columns[6]),
                "description": columns[7],
                "usermodifiable": _boolean(columns[8]),
                "hidewhennovalue": _boolean(columns[9]),
            })
    group_ids = {gid for gid, _ in groups}
    for param in params:
        if param["group"] not in group_ids:
            raise ValueError("Undeclared parameter group: %r" % param["group"])
    return groups, params


def merge(*files):
    """Merge in input order, retaining the first occurrence of each UUID.

    Group names match exactly. If distinct names use the same ID, assign the
    later group a fresh ID above all input IDs. Inputs are never modified.
    """
    files = [(list(groups), list(params)) for groups, params in files]
    next_id = max((gid for groups, _ in files for gid, _ in groups), default=0) + 1
    groups, params = [], []
    name_to_id, used_ids, seen_guids = {}, set(), set()
    for source_groups, source_params in files:
        remap = {}
        for gid, name in source_groups:
            if name not in name_to_id:
                target_id = gid
                if target_id in used_ids:
                    target_id = next_id
                    next_id += 1
                name_to_id[name] = target_id
                used_ids.add(target_id)
                groups.append((target_id, name))
            remap[gid] = name_to_id[name]
        for param in source_params:
            guid = _guid(param["guid"])
            if param["group"] not in remap:
                raise ValueError("Undeclared parameter group: %r" % param["group"])
            if guid not in seen_guids:
                copied = dict(param)
                copied.update(guid=guid, group=remap[param["group"]])
                params.append(copied)
                seen_guids.add(guid)
    return groups, params
