#!/usr/bin/env python3
"""comps.py - connected components of a texture, to locate glyphs in an atlas.

    comps.py <texture.png> <out.png> [gap]

Labels the opaque areas (alpha > 20, dilated by gap pixels, default 2, so the strokes of one
kanji join), prints index and bounding box (x0, y0, x1, y1) of each one and writes a 2x view with
the boxes drawn and numbered. Needs scipy.
"""
import sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
png, out = sys.argv[1], sys.argv[2]
gap = int(sys.argv[3]) if len(sys.argv) > 3 else 2
im = Image.open(png).convert('RGBA'); a = np.asarray(im)
m = a[..., 3] > 20
m2 = ndimage.binary_dilation(m, iterations=gap)
lab, n = ndimage.label(m2)
boxes = ndimage.find_objects(lab)
bg = Image.new('RGBA', im.size, (40, 40, 90, 255)); bg.alpha_composite(im)
sc = 2
big = bg.convert('RGB').resize((im.width * sc, im.height * sc), Image.NEAREST); dr = ImageDraw.Draw(big)
for i, b in enumerate(boxes):
    y0, y1, x0, x1 = b[0].start, b[0].stop, b[1].start, b[1].stop
    dr.rectangle((x0 * sc, y0 * sc, x1 * sc - 1, y1 * sc - 1), outline=(255, 0, 255))
    dr.text((x0 * sc + 1, y0 * sc), str(i), fill=(0, 255, 0))
    print(i, (x0, y0, x1, y1))
big.save(out)
