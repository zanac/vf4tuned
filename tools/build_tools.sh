#!/bin/sh
# Build the native helpers. Usage: tools/build_tools.sh [output_dir]   (default: directory of this script)
set -e
SRC=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-$SRC}
mkdir -p "$OUT"
${CXX:-g++} -O2 -std=c++17 -o "$OUT/naomigd_des" "$SRC/naomigd_des.cpp"
${CC:-gcc}  -O2 -o "$OUT/cdecc" "$SRC/cdecc.c"
echo "built: $OUT/naomigd_des $OUT/cdecc"
