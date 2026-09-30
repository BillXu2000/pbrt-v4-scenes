#!/bin/bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <n>" >&2
    exit 1
fi

n="$1"
src="curly-hair.pbrt.gz"
dst="curly-hair-${n}.pbrt.gz"

cd "$(dirname "$0")"
zcat "$src" | head -n "$n" | gzip > "$dst"
echo "Wrote $dst"
