#!/usr/bin/env python3
"""Compare two family manifests from a source checkout."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rvtx.mdiff import diff, render_md, render_text


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("a", metavar="A.json")
    parser.add_argument("b", metavar="B.json")
    parser.add_argument("--format", choices=("text", "json", "md"), default="text")
    args = parser.parse_args(argv)
    try:
        with open(args.a, encoding="utf-8") as stream:
            a = json.load(stream)
        with open(args.b, encoding="utf-8") as stream:
            b = json.load(stream)
        result = diff(a, b)
        if args.format == "json":
            output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        else:
            output = (render_md if args.format == "md" else render_text)(result)
        sys.stdout.write(output)
    except (OSError, ValueError) as exc:
        print("manifest_diff: %s" % exc, file=sys.stderr)
        return 2
    return int(bool(result["only_a"] or result["only_b"] or result["changed"]))


if __name__ == "__main__":
    sys.exit(main())
