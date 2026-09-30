#!/usr/bin/env python3
import gzip
import re
import sys
from pathlib import Path

SRC = Path(__file__).parent / "curly-hair.pbrt.gz"
DST = Path(__file__).parent / "curly-hair-left.pbrt.gz"

P_RE = re.compile(r'"point3 P"\s*\[\s*([-+0-9.eE\s]+?)\s*\]')


def parse_xs(line):
    m = P_RE.search(line)
    if not m:
        return None
    floats = m.group(1).split()
    if len(floats) != 12:
        return None
    return [float(floats[0]), float(floats[3]), float(floats[6]), float(floats[9])]


def main():
    print(f"Reading {SRC}...", file=sys.stderr)
    lines = []
    all_xs = []
    with gzip.open(SRC, "rt") as f:
        for line in f:
            xs = parse_xs(line)
            if xs is None:
                continue
            lines.append((line, xs))
            all_xs.extend(xs)

    if not all_xs:
        print("No point3 P entries found.", file=sys.stderr)
        sys.exit(1)

    all_xs.sort()
    threshold = all_xs[len(all_xs) // 10]
    print(f"Total points: {len(all_xs)}, x range [{all_xs[0]}, {all_xs[-1]}], "
          f"10th-percentile threshold: {threshold}", file=sys.stderr)

    kept = 0
    with gzip.open(DST, "wt") as out:
        for line, xs in lines:
            if all(x <= threshold for x in xs):
                out.write(line)
                kept += 1

    print(f"Kept {kept} / {len(lines)} curves -> {DST}", file=sys.stderr)


if __name__ == "__main__":
    main()
