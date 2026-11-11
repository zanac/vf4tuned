#!/usr/bin/env python3
"""glyph_id.py - identify the characters of the spr_asc 16x16 font by template matching.

    glyph_id.py <VF41_S.dec> <font.ttf> [orientation] [textures] [out.pkl]

  VF41_S.dec   decrypted game file
  font.ttf     a Japanese font to render the reference glyphs (e.g. a Noto Sans CJK / IPA gothic)
  orientation  extra transpose applied to the upright cells before matching, as a PIL
               Image.Transpose name (FLIP_LEFT_RIGHT, ROTATE_180, ...) or "none" (default)
  textures     comma separated texture indexes of spr_asc to scan (default: all 31)
  out.pkl      result, default glyphs.pkl: {(texture, cell): (char, score) or None}

Every defined cp932 double-byte character is rendered at 16x16, blurred and normalised; each
non-empty 16x16 cell of the font textures is matched to the best one (cosine similarity). The
printout shows the first 32 cells of each texture and the mean score. This is how the font was
found to follow Shift-JIS order (190 codes per lead byte, trail bytes 0x40-0xFC without 0x7F).
Needs numpy and Pillow.
"""
import os, pickle, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pvrtex, spr_sheets, sprtool

if len(sys.argv) < 3:
    raise SystemExit(__doc__)
DEC, FONT = sys.argv[1], sys.argv[2]
ORIENT = None if len(sys.argv) < 4 or sys.argv[3] == "none" else getattr(Image.Transpose, sys.argv[3])
ONLY = [int(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 and sys.argv[4] else None
OUT = sys.argv[5] if len(sys.argv) > 5 else "glyphs.pkl"

d = open(DEC, "rb").read()
recs = [r for n, v, r in spr_sheets.sprite_sets(d) if n == "spr_asc.bin.gz"][0]
data = sprtool.file_bytes(d, sprtool.find_entry(d, "spr_asc.bin.gz"))


def norm(a):
    a = a.astype(np.float32); a -= a.mean(); n = np.linalg.norm(a)
    return a / n if n > 0 else a


def prep(img):          # 16x16 'L' -> blurred, normalised vector
    return norm(np.asarray(img.filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float32).ravel())


chars = []
for lead in list(range(0x81, 0xA0)) + list(range(0xE0, 0xF0)):
    for tr in range(0x40, 0xFD):
        if tr == 0x7F:
            continue
        try:
            chars.append(bytes([lead, tr]).decode("cp932"))
        except UnicodeDecodeError:
            pass
chars = sorted(set(c for c in chars if c.strip()))
font = ImageFont.truetype(FONT, 16)
refs = []
for c in chars:
    im = Image.new("L", (16, 16), 0); dr = ImageDraw.Draw(im)
    bb = dr.textbbox((0, 0), c, font=font)
    dr.text(((16 - (bb[2] - bb[0])) // 2 - bb[0], (16 - (bb[3] - bb[1])) // 2 - bb[1]), c, fill=255, font=font)
    refs.append(prep(im))
R = np.stack(refs)

res = {}
for t, (w, h, f, o) in enumerate(recs):
    if ONLY and t not in ONLY:
        continue
    im = pvrtex.decode_rec(data, w, h, f, o).transpose(sprtool.UPRIGHT)
    if ORIENT is not None:
        im = im.transpose(ORIENT)
    w, h = im.size
    a = im.split()[3]                                   # alpha = glyph
    for cy in range(h // 16):
        for cx in range(w // 16):
            cell = a.crop((cx * 16, cy * 16, cx * 16 + 16, cy * 16 + 16))
            k = cy * (w // 16) + cx
            if np.asarray(cell).max() < 64:
                res[(t, k)] = None
                continue
            s = R @ prep(cell); i = int(s.argmax())
            res[(t, k)] = (chars[i], float(s[i]))
pickle.dump(res, open(OUT, "wb"))
for t in (ONLY or range(len(recs))):
    row = "".join(res[(t, k)][0] if res.get((t, k)) else "·" for k in range(32))
    sc = [v[1] for (tt, _), v in res.items() if tt == t and v]
    print("%2d %.2f %s" % (t, np.mean(sc) if sc else 0, row))
