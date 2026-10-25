#!/usr/bin/env python3
"""spr_sheets - render every VF4FT sprite set (table in the main program) to PNG contact sheets.

  spr_sheets.py <image.dec> <files_dir> <out_dir>
"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pvrtex
from PIL import Image, ImageDraw

TABLE = 0x322154          # program table: {name*, vram, records*} x N  (RAM 0x0c322154 - 0x0c000000)
RAM2ROM = lambda a: a - 0x0c020000 + 0x20000

def sprite_sets(d):
    p = TABLE
    while True:
        n, vram, a = struct.unpack_from("<III", d, p)
        if n >> 24 != 0x0c or a >> 24 != 0x0c:
            return
        name = d[RAM2ROM(n):d.index(b"\0", RAM2ROM(n))].decode("latin1")
        if not name.startswith("spr_"):
            return
        recs, q = [], RAM2ROM(a)
        while True:
            wh, fmt, off, fl = struct.unpack_from("<4I", d, q)
            if wh == 0xFFFFFFFF:
                break
            recs.append((wh >> 16, wh & 0xFFFF, fmt, off))   # field is (h << 16) | w swapped: width in high half
            q += 16
        yield name, vram, recs
        p += 12

def main(img, fdir, out):
    d = open(img, "rb").read()
    os.makedirs(out, exist_ok=True)
    for name, vram, recs in sprite_sets(d):
        fn = os.path.join(fdir, name[:-3] if name.endswith(".gz") else name)
        if not os.path.exists(fn):
            print("missing", name); continue
        data = open(fn, "rb").read()
        tiles = []
        for i, (w, h, fmt, off) in enumerate(recs):
            try:
                im = pvrtex.decode_rec(data, w, h, fmt, off)
            except Exception as e:
                print("  %s #%d %dx%d fmt %x: %s" % (name, i, w, h, fmt, e)); continue
            bg = Image.new("RGBA", im.size, (40, 40, 90, 255)); bg.alpha_composite(im)
            tiles.append((i, bg.convert("RGB")))
        if not tiles:
            continue
        cols = 4; cw = max(t.width for _, t in tiles); ch = max(t.height for _, t in tiles) + 14
        sheet = Image.new("RGB", (cols * cw, ((len(tiles) + cols - 1) // cols) * ch), (20, 20, 20))
        dr = ImageDraw.Draw(sheet)
        for k, (i, t) in enumerate(tiles):
            x, y = (k % cols) * cw, (k // cols) * ch
            sheet.paste(t, (x, y + 14)); dr.text((x + 2, y + 1), "#%d %dx%d" % (i, t.width, t.height), fill=(255, 255, 0))
        base = name.replace(".bin", "").replace(".gz", "")
        sheet.save(os.path.join(out, base + ".png"))
        print("%-26s %3d textures" % (name, len(tiles)))

if __name__ == "__main__":
    if len(sys.argv) != 4: raise SystemExit(__doc__)
    main(*sys.argv[1:])
