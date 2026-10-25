# spr_sel_ft #1: replace the katakana mode captions with English, inside the original atlas rects.
import os, shutil, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def render(text, box_w, box_h, fill, size=18, shear=0.28):
    """white/gradient italic text with dark outline + soft shadow, fitted into box_w x box_h."""
    f = ImageFont.truetype(FONT, size)
    pad = 8
    tmp = Image.new('RGBA', (box_w * 3, box_h * 3), (0, 0, 0, 0))
    dr = ImageDraw.Draw(tmp)
    dr.text((pad, pad), text, font=f, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(20, 20, 20, 255))
    tmp = tmp.crop(tmp.getbbox())
    # fill colour: recolour the light (inner) pixels
    a = np.asarray(tmp).astype(np.float32)
    lum = a[..., :3].mean(2)
    w = a.shape[1]
    if fill == 'gradient':     # original: green -> yellow -> orange along the word
        t = np.linspace(0, 1, w)[None, :]
        col = np.stack([np.interp(t, [0, .45, 1], [60, 255, 255]), np.interp(t, [0, .45, 1], [220, 240, 120]),
                        np.interp(t, [0, .45, 1], [20, 20, 0])], -1)
        inner = (lum > 128)[..., None]
        a[..., :3] = np.where(inner, col * (lum[..., None] / 255), a[..., :3])
    tmp = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    tw, th = tmp.size
    tmp = tmp.transform((tw + int(th * shear) + 1, th), Image.AFFINE, (1, shear, -th * shear, 0, 1, 0), Image.BICUBIC)
    # fit into the box (keep 2px for the shadow)
    sc = min((box_w - 3) / tmp.width, (box_h - 3) / tmp.height, 1.0)
    tmp = tmp.resize((max(1, int(tmp.width * sc)), max(1, int(tmp.height * sc))), Image.LANCZOS)
    out = Image.new('RGBA', (box_w, box_h), (0, 0, 0, 0))
    sh = tmp.split()[3].filter(ImageFilter.GaussianBlur(1.2))
    shadow = Image.new('RGBA', tmp.size, (0, 0, 0, 0)); shadow.putalpha(sh.point(lambda v: v * 0.7))
    x, y = (box_w - tmp.width) // 2, (box_h - tmp.height) // 2
    out.alpha_composite(shadow, (min(x + 2, box_w - tmp.width), min(y + 2, box_h - tmp.height)))
    out.alpha_composite(tmp, (x, y))
    return out


BOXES = [  # (x0, y0, x1, y1) in the upright 512x512 atlas, text, fill
    ((132, 379, 287, 405), 'CHALLENGE MODE', 'gradient'),
    ((294, 379, 446, 405), 'CHALLENGE MODE', 'white'),
    ((132, 409, 279, 437), 'NORMAL MODE', 'white'),
]

src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)
shutil.copy(os.path.join(src, 'spr_sel_ft.json'), dst)
im = Image.open(os.path.join(src, 'spr_sel_ft_01.png')).convert('RGBA')
for (x0, y0, x1, y1), text, fill in BOXES:
    clear_y1 = 408 if y1 <= 405 else y1          # katakana descenders reach row 407
    im.paste(Image.new('RGBA', (x1 - x0, clear_y1 - y0), (0, 0, 0, 0)), (x0, y0))
    im.alpha_composite(render(text, x1 - x0, y1 - y0, fill), (x0, y0))
im.save(os.path.join(dst, 'spr_sel_ft_01.png'))
