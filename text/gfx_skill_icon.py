# spr_cmn_skill #0: replace the 技 (technique) kanji in the blue (1P) and red (2P) skill icons with "T".
# usage: gfx_skill_icon.py <export_dir> <out_dir>
#
# The kanji is dark engraving inside a ~17 px disc at the left of each icon. The disc is refilled
# row by row with the icon's own shading (taken from the bright, kanji-free pixels of the same row),
# then a white "T" is drawn with a 1 px shadow in the darkest colour of the original glyph.
import os, shutil, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
DISCS = [(1, 1, 18, 21), (1, 29, 18, 49)]          # upright x0, y0, x1, y1 of the two discs


def fix_disc(a, box):
    x0, y0, x1, y1 = box
    reg = a[y0:y1, x0:x1].astype(np.float32)
    vis = reg[..., 3] > 128
    lum = reg[..., :3].mean(2)
    ink = vis & (lum < np.percentile(lum[vis], 45))                      # kanji strokes
    dark = np.median(reg[ink][:, :3], 0)
    for y in range(reg.shape[0]):
        row = vis[y] & ~ink[y]
        if not row.any():
            continue
        xs = np.nonzero(row)[0]
        cols = reg[y, xs, :3]
        for x in np.nonzero(ink[y])[0]:                                   # interpolate along the row
            reg[y, x, :3] = [np.interp(x, xs, cols[:, c]) for c in range(3)]
    # vertical smoothing pass for rows that were almost entirely kanji
    for x in range(reg.shape[1]):
        col = vis[:, x] & ~ink[:, x]
        if col.sum() >= 2:
            ys = np.nonzero(col)[0]
            for y in np.nonzero(ink[:, x])[0]:
                v = [np.interp(y, ys, reg[ys, x, c]) for c in range(3)]
                reg[y, x, :3] = (reg[y, x, :3] + np.array(v)) / 2
    out = Image.fromarray(np.clip(reg, 0, 255).astype(np.uint8))
    # engraved "T", centred on the disc
    w, h = x1 - x0, y1 - y0
    t = Image.new("L", (w * 4, h * 4), 0)
    d = ImageDraw.Draw(t)
    f = ImageFont.truetype(FONT, int(h * 4 * 0.78))
    bb = d.textbbox((0, 0), "T", font=f)
    d.text(((w * 4 - (bb[2] - bb[0])) / 2 - bb[0], (h * 4 - (bb[3] - bb[1])) / 2 - bb[1]), "T", fill=255, font=f)
    m = np.asarray(t.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255
    sh = np.zeros_like(m); sh[1:, 1:] = m[:-1, :-1]                       # 1 px drop shadow
    o = np.asarray(out).astype(np.float32)
    o[..., :3] = o[..., :3] * (1 - sh[..., None] * 0.8) + dark * sh[..., None] * 0.8
    o[..., :3] = o[..., :3] * (1 - m[..., None]) + 255 * m[..., None]     # white T
    o[..., 3] = reg[..., 3]
    a[y0:y1, x0:x1] = np.clip(o, 0, 255).astype(np.uint8)


def main(src, dst):
    os.makedirs(dst, exist_ok=True)
    shutil.copy(os.path.join(src, "spr_cmn_skill.json"), dst)
    p = "spr_cmn_skill_00.png"
    a = np.asarray(Image.open(os.path.join(src, p)).convert("RGBA")).copy()
    for box in DISCS:
        fix_disc(a, box)
    Image.fromarray(a).save(os.path.join(dst, p))


if __name__ == "__main__":
    main(*sys.argv[1:3])
