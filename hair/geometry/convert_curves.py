#!/usr/bin/env python3
"""
Convert a pbrt curve file (e.g. geometry/curly-hair.pbrt.gz) to a flat binary
file that C++ can mmap. The output path is automatically derived from the
input by appending ".bin":

    geometry/curly-hair.pbrt.gz  ->  geometry/curly-hair.pbrt.gz.bin

Each line in the source is a `Shape "curve"` declaration of the form:
    Shape "curve" "string type" [ "cylinder" ]
                  "point3 P" [ x0 y0 z0 x1 y1 z1 x2 y2 z2 x3 y3 z3 ]
                  "float width0" [ w0 ] "float width1" [ w1 ]

We emit:
    Header (32 bytes, little-endian, packed):
        magic     [4] = b"CURV"
        version    u32 = 1
        num_curves u64
        curve_type u32 (0=cylinder, 1=flat, 2=ribbon)
        record_size u32 = 56  (sanity)
        reserved   u32 = 0    (padding to align records to 8 bytes)
    Records (56 bytes each):
        P        : 12 * float32  (4 control points x,y,z)
        width0   :      float32
        width1   :      float32

Total file size = 32 + num_curves * 56.
"""

import argparse
import gzip
import re
import struct
import sys
import time

CURVE_TYPE = {'cylinder': 0, 'flat': 1, 'ribbon': 2}
RECORD_SIZE = 14 * 4
HEADER_SIZE = 32

LINE_RE = re.compile(
    r'Shape\s+"curve"\s+'
    r'"string\s+type"\s+\[\s+"(?P<type>[a-z]+)"\s+\]\s+'
    r'"point3\s+P"\s+\[\s+'
    r'(?P<P>[-\d.eE+ \t]+?)'
    r'\]\s+'
    r'"float\s+width0"\s+\[\s+(?P<w0>[-\d.eE+]+)\s+\]\s+'
    r'"float\s+width1"\s+\[\s+(?P<w1>[-\d.eE+]+)\s+\]'
)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('source', help='input .pbrt or .pbrt.gz file of curves')
    args = ap.parse_args()

    dest = args.source + '.bin'

    open_fn = gzip.open if args.source.endswith('.gz') else open
    record = struct.Struct('<14f')

    t0 = time.time()
    n = 0
    curve_type_id = None
    with open_fn(args.source, 'rt') as fin, open(dest, 'wb') as fout:
        fout.write(b'\0' * HEADER_SIZE)

        for raw in fin:
            line = raw.strip()
            if not line:
                continue
            m = LINE_RE.match(line)
            if not m:
                continue
            t = m.group('type')
            if curve_type_id is None:
                curve_type_id = CURVE_TYPE.get(t, 0)
            P_tokens = m.group('P').split()
            if len(P_tokens) != 12:
                raise ValueError(
                    f'curve {n}: expected 12 P values, got {len(P_tokens)}')
            P_vals = [float(x) for x in P_tokens]
            w0 = float(m.group('w0'))
            w1 = float(m.group('w1'))
            fout.write(record.pack(*P_vals, w0, w1))
            n += 1
            if n % 200_000 == 0:
                dt = time.time() - t0
                print(f'  ... {n:>10,} curves in {dt:6.1f}s '
                      f'({n / dt / 1e3:.0f}k/s)', file=sys.stderr)

        fout.seek(0)
        fout.write(b'CURV')
        fout.write(struct.pack('<I', 1))
        fout.write(struct.pack('<Q', n))
        fout.write(struct.pack('<I', curve_type_id or 0))
        fout.write(struct.pack('<I', RECORD_SIZE))
        fout.write(struct.pack('<I', 0))

    dt = time.time() - t0
    print(f'wrote {n:,} curves to {dest} in {dt:.1f}s')


if __name__ == '__main__':
    main()
