#!/bin/sh
# Rebuild vf4ft_en.vfp from the sources (text table + graphics specs) and the original disc.
#
#   ./make_patch.sh <gds-0036f.chd> <vf4tuned.zip | 317-0387-com.pic> [out.vfp]   (default: patch/vf4ft_en.vfp)
#
# Needs: python3 + Pillow + numpy + scipy, chdman, a C/C++ compiler, DejaVu fonts
# (/usr/share/fonts/truetype/dejavu). Temporary files go to $TMPDIR (default /tmp), ~1.7 GB.
set -e
[ $# -ge 2 ] || { sed -n '2,7p' "$0"; exit 2; }
CHD=$1; PIC=$2; OUT=${3:-$(cd "$(dirname "$0")" && pwd)/patch/vf4ft_en.vfp}
HERE=$(cd "$(dirname "$0")" && pwd)
T=$(mktemp -d "${TMPDIR:-/tmp}/vf4ftp.XXXXXX")
trap 'rm -rf "$T"' EXIT
"$HERE/tools/build_tools.sh" "$T/bin" >/dev/null
case "$PIC" in *.zip) unzip -q -o "$PIC" 317-0387-com.pic -d "$T" && PIC="$T/317-0387-com.pic" ;; esac

echo "[1/5] extracting and decrypting the original game file"
chdman extractcd -i "$CHD" -o "$T/disc.gdi" >/dev/null 2>&1
python3 "$HERE/tools/gdtool.py" extract "$T/disc.gdi" VF41_S.BIN "$T/VF41_S.enc" >/dev/null
"$T/bin/naomigd_des" dec "$PIC" "$T/VF41_S.enc" "$T/orig.dec" 2>/dev/null
rm -rf "$T/disc.gdi" "$T"/disc0* "$T/VF41_S.enc"
cp "$T/orig.dec" "$T/en.dec"

echo "[2/5] exporting the sprite sets that get edited"
for s in spr_card.bin spr_comm.bin.gz spr_sel_ft.bin spr_chlg.bin spr_game.bin spr_staff.bin spr_mode_sel.bin spr_cmn_skill.bin; do
  python3 "$HERE/tools/sprtool.py" export "$T/orig.dec" "$s" "$T/exp/${s%%.*}" >/dev/null
done

echo "[3/5] redrawing graphics"
python3 "$HERE/tools/redraw.py" "$HERE/text/gfx_spec.py" "$T/exp" "$T/edit" 2>/dev/null
python3 "$HERE/text/gfx_mode_sel.py" "$T/exp/spr_mode_sel" "$T/edit/spr_mode_sel"
python3 "$HERE/text/gfx_sel_ft.py" "$T/exp/spr_sel_ft" "$T/edit/spr_sel_ft"   # texture 1 (gfx_spec edits texture 0)
python3 "$HERE/text/gfx_skill_icon.py" "$T/exp/spr_cmn_skill" "$T/edit/spr_cmn_skill"

echo "[4/5] writing text and graphics"
python3 "$HERE/tools/apply_text.py" "$T/en.dec" "$HERE/text/translations.py" "$HERE/text/strings_cap.tsv"
for d in "$T"/edit/*; do python3 "$HERE/tools/sprtool.py" import "$T/en.dec" "$d" | grep -v '^0 textures' || true; done

echo "[5/5] making $OUT"
python3 "$HERE/tools/vfpatch.py" make "$T/orig.dec" "$T/en.dec" "$OUT"
