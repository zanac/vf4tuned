#!/usr/bin/env python3
"""redraw - replace Japanese text areas of exported sprite textures with English.

  redraw.py <spec.py> <export_root> <out_root>

<export_root>/<set>/ holds the upright PNGs + manifest written by `sprtool.py export`.
For every texture touched by the spec, the edited PNG and the manifest are written to <out_root>/<set>/,
ready for `sprtool.py import`.

spec.py defines EDITS = [dict(...)], keys:
  set, tex          sprite set directory name (e.g. "spr_card") and texture index
  box               (x0, y0, x1, y1) upright pixel box; the text is fitted inside it
  text              English text ("\\n" for several lines)
  clear             optional box to erase (default: box); list of boxes allowed
  font              "sans" (default), "serif", "mono" or a .ttf path
  fill / outline    RGB tuple, "auto" (sampled from the original pixels in box) or None
  shear             italic shear (0 = upright)
  align             "center" (default), "left" or "right"
  shadow            soft drop shadow (bool)
  stroke            outline width in px (default 1 if an outline colour is used)
  gradient          (rgb_left, rgb_mid, rgb_right) horizontal gradient fill instead of `fill`
  bg                erase by filling the box with the median non-text colour (text on a translucent bar)
  blur              gaussian radius applied to the rendered text (glowing / blurred copies)
"""
import importlib.util, json, os, shutil, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = {
    "sans": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "sanscond": "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
    "serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "sansreg": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
}


def sample_style(img, box):
    """dominant text colour (bright, opaque) and outline colour (dark, opaque) inside box."""
    a = np.asarray(img.crop(box)).reshape(-1, 4).astype(np.float32)
    op = a[a[:, 3] > 200]
    if len(op) == 0:
        return (255, 255, 255), None
    lum = op[:, :3].mean(1)
    bright = op[lum >= np.percentile(lum, 70)]
    fill = tuple(int(v) for v in np.median(bright[:, :3], 0))
    dark = op[lum < 70]
    outline = tuple(int(v) for v in np.median(dark[:, :3], 0)) if len(dark) > len(op) * 0.08 else None
    return fill, outline


def render(e, w, h, fill, outline):
    path = FONTS.get(e.get("font", "sans"), e.get("font", "sans"))
    stroke = e.get("stroke", 1 if outline else 0)
    lines = e["text"].split("\n")
    size = 64                                   # render big, then downscale to fit
    f = ImageFont.truetype(path, size)
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lh = size + 2 * stroke + int(size * 0.08)
    lw = [dummy.textlength(l, font=f) + 2 * stroke for l in lines]
    W, H = int(max(lw)) + 8, lh * len(lines) + 8
    t = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(t)
    for i, l in enumerate(lines):
        x = {"left": 4, "right": W - 4 - lw[i]}.get(e.get("align", "center"), (W - lw[i]) / 2)
        dr.text((x + stroke, 4 + i * lh + stroke), l, font=f, fill=fill + (255,),
                stroke_width=stroke * 6 if stroke else 0, stroke_fill=(outline or (0, 0, 0)) + (255,))
    if e.get("gradient"):
        g = np.asarray(t).astype(np.float32)
        cl, cm, cr = [np.array(c, np.float32) for c in e["gradient"]]
        xs = np.linspace(0, 1, W)[:, None]
        col = np.where(xs < .5, cl + (cm - cl) * (xs / .5), cm + (cr - cm) * ((xs - .5) / .5))
        inner = g[..., :3].mean(2) > 128
        g[..., :3] = np.where(inner[..., None], col[None, :, :], g[..., :3])
        t = Image.fromarray(g.astype(np.uint8))
    t = t.crop(t.getbbox())
    sh = e.get("shear", 0)
    if sh:
        tw, th = t.size
        t = t.transform((tw + int(th * sh) + 1, th), Image.AFFINE, (1, sh, -th * sh, 0, 1, 0), Image.BICUBIC)
    pad = 2 if e.get("shadow") else 0
    sc = min((w - pad) / t.width, (h - pad) / t.height)
    if e.get("max_scale"):
        sc = min(sc, e["max_scale"])
    if e.get("max_h"):                           # common text height across a group of labels
        sc = min(sc, e["max_h"] / t.height)
    nt = t.resize((max(1, round(t.width * sc)), max(1, round(t.height * sc))), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = {"left": 0, "right": w - nt.width - pad}.get(e.get("align", "center"), (w - pad - nt.width) // 2)
    y = (h - pad - nt.height) // 2
    if e.get("shadow"):
        s = Image.new("RGBA", nt.size, (0, 0, 0, 0))
        s.putalpha(nt.split()[3].filter(ImageFilter.GaussianBlur(1)).point(lambda v: int(v * .7)))
        out.alpha_composite(s, (x + 2, y + 2))
    out.alpha_composite(nt, (x, y))
    if e.get("blur"):
        out = out.filter(ImageFilter.GaussianBlur(e["blur"]))
    return out


def main(spec_path, src, dst):
    spec = importlib.util.spec_from_file_location("spec", spec_path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    imgs = {}
    for e in m.EDITS:
        key = (e["set"], e["tex"])
        if key not in imgs:
            imgs[key] = Image.open(os.path.join(src, e["set"], "%s_%02d.png" % key)).convert("RGBA")
        img = imgs[key]
        box = tuple(e["box"])
        fill, outline = sample_style(img, box)
        if e.get("fill", "auto") != "auto":
            fill = e["fill"]
        if e.get("outline", "auto") != "auto":
            outline = e["outline"]
        clears = e.get("clear", box)
        clears = clears if isinstance(clears[0], (list, tuple)) else [clears]
        for c in clears:
            if e.get("bg"):
                # glyph on a translucent bar: repaint every visible pixel of the box with the bar colour,
                # keeping the (lower) alpha of the bar's antialiased edges
                a = np.asarray(img).copy()
                reg = a[c[1]:c[3], c[0]:c[2]]
                vis = reg[..., 3] > 0
                al = reg[..., 3]
                # bar = most frequent (lower) alpha among visible pixels; glyph pixels are more opaque
                low = al[vis & (al < 160)]
                bar_a = np.bincount(low).argmax() if len(low) else 0
                pool = reg[vis & (al == bar_a)]
                bar_rgb = np.median(pool[:, :3], 0).astype(np.uint8) if len(pool) else np.array([255, 255, 255], np.uint8)
                # rebuild each row: bar span (from the bar-alpha pixels of that row, or of the rows
                # around it when the glyph covers the whole row) gets the bar, the rest becomes empty
                isbar = np.abs(al.astype(int) - int(bar_a)) <= 12
                H = reg.shape[0]
                spans = []
                for y in range(H):
                    xs = np.where(isbar[y])[0]
                    spans.append((xs.min(), xs.max()) if len(xs) else None)
                for y in range(H):
                    sp = spans[y]
                    if sp is None:          # take the nearest rows that do show the bar
                        up = next((spans[k] for k in range(y - 1, -1, -1) if spans[k]), None)
                        dn = next((spans[k] for k in range(y + 1, H) if spans[k]), None)
                        sp = (up and dn) and (min(up[0], dn[0]), max(up[1], dn[1]))
                    hot = vis[y] & (al[y] >= bar_a * 0.5)
                    if sp:
                        inside = np.zeros(reg.shape[1], bool); inside[sp[0]:sp[1] + 1] = True
                        reg[y, hot & inside, :3] = bar_rgb
                        reg[y, hot & inside, 3] = bar_a
                        reg[y, hot & ~inside, 3] = 0
                    else:
                        reg[y, hot, 3] = 0
                a[c[1]:c[3], c[0]:c[2]] = reg
                img.paste(Image.fromarray(a), (0, 0))
                continue
            img.paste(Image.new("RGBA", (c[2] - c[0], c[3] - c[1]), (0, 0, 0, 0)), (c[0], c[1]))
        if e["text"].strip():              # blank text: erase only
            img.alpha_composite(render(e, box[2] - box[0], box[3] - box[1], tuple(fill), outline and tuple(outline)),
                                (box[0], box[1]))
    for (s, t), img in imgs.items():
        os.makedirs(os.path.join(dst, s), exist_ok=True)
        img.save(os.path.join(dst, s, "%s_%02d.png" % (s, t)))
        shutil.copy(os.path.join(src, s, s + ".json"), os.path.join(dst, s, s + ".json"))
    print("%d edits on %d textures" % (len(m.EDITS), len(imgs)))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
