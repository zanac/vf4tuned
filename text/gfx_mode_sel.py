# spr_mode_sel #0/#2: katakana captions -> CHALLENGE MODE / NORMAL MODE.  usage: gfx_mode_sel.py <export_dir> <out_dir>
# Test edit: replace the katakana captions of spr_mode_sel with English, in the original style.
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def caption(text, size=15):
    f = ImageFont.truetype(FONT, size)
    tmp = Image.new('RGBA', (300, 40), (0, 0, 0, 0)); dr = ImageDraw.Draw(tmp)
    dr.text((10, 8), text, font=f, fill=(255, 255, 255, 255), stroke_width=1, stroke_fill=(0, 0, 0, 255))
    tmp = tmp.crop(tmp.getbbox())
    sh = 0.3                                   # faux italic like the original
    w, h = tmp.size
    return tmp.transform((w + int(h * sh) + 1, h), Image.AFFINE, (1, sh, -h * sh, 0, 1, 0), Image.BICUBIC)
def fix(path, text, out):
    im = Image.open(path).convert('RGBA'); a = np.asarray(im).copy()
    lum = a[..., :3].mean(2); al = a[..., 3]
    y = np.arange(a.shape[0])[:, None] * np.ones((1, a.shape[1]))
    kat_core = (y <= 31) & (al >= 240) & ((lum > 200) | (lum < 70))
    # grow by one pixel (antialiased edge of the katakana outline)
    g = kat_core.copy()
    g[1:] |= kat_core[:-1]; g[:-1] |= kat_core[1:]; g[:, 1:] |= kat_core[:, :-1]; g[:, :-1] |= kat_core[:, 1:]
    kat = (y <= 24) | (g & (y <= 31))
    a[kat & (y <= 24)] = 0
    hole = kat & (y > 24)                      # overlaps the logo glow: inpaint from neighbours
    f = a.astype(np.float32); f[..., :3] *= f[..., 3:4] / 255; f[hole] = 0
    known = ~hole
    for _ in range(40):
        acc = np.zeros_like(f); cnt = np.zeros(hole.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(np.roll(f, dy, 0), dx, 1); k = np.roll(np.roll(known, dy, 0), dx, 1)
            acc += sh * k[..., None]; cnt += k
        upd = hole & (cnt > 0) & ~known
        f[upd] = acc[upd] / cnt[upd, None]; known |= upd
    al2 = np.clip(f[..., 3:4], 1e-3, None)
    f[..., :3] = np.where(f[..., 3:4] > 0, f[..., :3] * 255 / al2, 0)
    a = np.clip(np.rint(f), 0, 255).astype(np.uint8)
    base = Image.fromarray(a)
    cap = caption(text)
    if cap.width > 250: cap = cap.resize((250, cap.height), Image.LANCZOS)
    cx = (base.width - cap.width) // 2 + 6
    base.alpha_composite(cap, (cx, 12))
    base.save(out)
src, dst = sys.argv[1], sys.argv[2]
import os, shutil
os.makedirs(dst, exist_ok=True)
shutil.copy(os.path.join(src, 'spr_mode_sel.json'), dst)
fix(os.path.join(src, 'spr_mode_sel_00.png'), 'CHALLENGE MODE', os.path.join(dst, 'spr_mode_sel_00.png'))
fix(os.path.join(src, 'spr_mode_sel_02.png'), 'NORMAL MODE', os.path.join(dst, 'spr_mode_sel_02.png'))
