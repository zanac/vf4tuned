#!/bin/sh
# Build the English VF4 Final Tuned GD-ROM from the original Japanese one.
#
#   ./build.sh <gds-0036f.chd> <vf4tuned.zip | 317-0387-com.pic> <patch.vfp> <output.chd>
#
# Needs: python3, chdman (MAME tools), a C/C++ compiler,
# unzip (only when a zip is given). Temporary files go to $TMPDIR (default /tmp), ~1.6 GB.
set -e
[ $# -eq 4 ] || { sed -n '2,8p' "$0"; exit 2; }
CHD=$1; PIC=$2; PATCH=$3; OUT=$4
HERE=$(cd "$(dirname "$0")" && pwd)
T=$(mktemp -d "${TMPDIR:-/tmp}/vf4ft.XXXXXX")
trap 'rm -rf "$T"' EXIT

command -v chdman >/dev/null || { echo "chdman not found (install MAME tools)"; exit 1; }
"$HERE/tools/build_tools.sh" "$T/bin" >/dev/null

case "$PIC" in
  *.zip) unzip -q -o "$PIC" 317-0387-com.pic -d "$T" && PIC="$T/317-0387-com.pic" ;;
esac

echo "[1/5] extracting $CHD"
chdman extractcd -i "$CHD" -o "$T/disc.gdi" >/dev/null 2>&1
echo "[2/5] decrypting VF41_S.BIN"
python3 "$HERE/tools/gdtool.py" extract "$T/disc.gdi" VF41_S.BIN "$T/VF41_S.enc" >/dev/null
"$T/bin/naomigd_des" dec "$PIC" "$T/VF41_S.enc" "$T/VF41_S.dec" 2>/dev/null
echo "[3/5] applying $PATCH"
python3 "$HERE/tools/vfpatch.py" apply "$T/VF41_S.dec" "$PATCH"
echo "[4/5] encrypting and writing both game files"
"$T/bin/naomigd_des" enc "$PIC" "$T/VF41_S.dec" "$T/VF41_S.enc" 2>/dev/null
CDECC="$T/bin/cdecc" python3 "$HERE/tools/gdtool.py" inject "$T/disc.gdi" VF41_S.BIN  "$T/VF41_S.enc" >/dev/null
CDECC="$T/bin/cdecc" python3 "$HERE/tools/gdtool.py" inject "$T/disc.gdi" VF41_S2.BIN "$T/VF41_S.enc" >/dev/null
echo "[5/5] creating $OUT"
chdman createcd -f -i "$T/disc.gdi" -o "$OUT" >/dev/null 2>&1
echo "done: $OUT"
