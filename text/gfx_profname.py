# spr_sel_profname #0-#14: remove the Japanese fighting-style names, keep the English ones.
# usage: gfx_profname.py <export_dir> <out_dir>
#
# OPTIONAL - not used by make_patch.sh. The character profile cards show each fighting style in
# Japanese (八極拳, 柔道, ...) and in English; the release keeps both, as the arcade did. To drop the
# Japanese names, export the set and run this script before the import step of make_patch.sh:
#   python3 tools/sprtool.py export "$T/VF41_S.dec" spr_sel_profname.bin "$T/exp/spr_sel_profname"
#   python3 text/gfx_profname.py "$T/exp/spr_sel_profname" "$T/edit/spr_sel_profname"
#
# Each entry: texture, region (upright x0,y0,x1,y1) holding the style name, layout.
#   "top"   : Japanese line above the English line  -> erase the rows above the first empty row
#   "right" : vertical Japanese column right of the English column -> erase the columns right of
#             the last empty column
import json, os, shutil, sys
import numpy as np
from PIL import Image

STYLES = [
    (0, (104, 162, 214, 211), "top"),     # 八極拳 Hakkyoku-Ken
    (1, (143, 74, 237, 121), "top"),      # 合気柔術 Aiki Ju-Jutsu
    (2, (207, 0, 254, 144), "right"),     # キックボクシング Kick Boxing
    (3, (171, 106, 221, 152), "top"),     # 柔道 Judo
    (4, (132, 0, 234, 45), "top"),        # 截拳道 Jeet Kune Do
    (5, (192, 0, 234, 98), "right"),      # パンクラチオン Pancratium
    (6, (0, 162, 154, 210), "top"),       # 葉隠流柔術 Hagakure-ryu Ju-Jutsu
    (7, (0, 162, 75, 208), "top"),        # 虎燕拳 Koen-Ken
    (8, (118, 60, 246, 112), "top"),      # 少林拳 Shaolin Kung-Fu
    (9, (112, 162, 201, 208), "top"),     # 蟷螂拳 Tourou-Ken
    (10, (0, 160, 116, 209), "top"),      # 燕青拳 Ensei-Ken
    (11, (147, 0, 190, 139), "right"),    # マーシャルアーツ Martial Arts
    (12, (0, 160, 135, 211), "top"),      # 酔拳 Drunken Kung-Fu
    (13, (206, 0, 250, 132), "right"),    # バーリトゥード Vale Tudo
    (14, (211, 132, 256, 234), "right"),  # プロレス Pro-Wrestling
]


def split(ink_strict, axis):
    """index of the emptiest line between the two text blocks along axis (0 = rows, 1 = cols)."""
    prof = ink_strict.sum(1 - axis)
    idx = np.nonzero(prof)[0]
    a, b = idx[0], idx[-1]
    inner = prof[a:b + 1]
    # longest run of minimum values inside the inked span: middle of that run
    m = inner.min()
    best, cur, start, bs = 0, 0, 0, 0
    for k, v in enumerate(inner):
        if v == m:
            if cur == 0:
                start = k
            cur += 1
            if cur > best:
                best, bs = cur, start
        else:
            cur = 0
    return a + bs + best // 2


def main(src, dst):
    os.makedirs(dst, exist_ok=True)
    shutil.copy(os.path.join(src, "spr_sel_profname.json"), dst)
    for tex, region, layout in STYLES:
        name = "spr_sel_profname_%02d.png" % tex
        img = Image.open(os.path.join(src, name)).convert("RGBA")
        a = np.asarray(img).copy()
        x0, y0, x1, y1 = region
        reg = a[y0:y1, x0:x1]
        strict = (reg[..., 3] > 200) & (reg[..., :3].mean(2) > 200)   # glyph body, no shadow
        if layout == "top":
            cut = split(strict, 0)
            a[y0:y0 + cut, x0:x1, 3] = 0
            box = (x0, y0, x1, y0 + cut)
        else:
            cut = split(strict, 1)
            a[y0:y1, x0 + cut:x1, 3] = 0
            box = (x0 + cut, y0, x1, y1)
        Image.fromarray(a).save(os.path.join(dst, name))
        print("tex %2d: erased %s" % (tex, box))


if __name__ == "__main__":
    main(*sys.argv[1:3])
