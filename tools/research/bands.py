#!/usr/bin/env python3
"""bands.py - text line and glyph layout inside a region of a texture.

    bands.py <texture.png> <x0> <y0> <x1> <y1>

Prints the row bands of opaque pixels (alpha > 20) inside the region and, for each band, the
column segments (gaps narrower than 4 px are bridged). Used to find the boxes of the Japanese
lines and words before writing an entry of text/gfx_spec.py. Coordinates are upright, as the
PNGs exported by tools/sprtool.py.
"""
import sys, numpy as np
from PIL import Image
p,x0,y0,x1,y1=sys.argv[1],*map(int,sys.argv[2:6])
a=np.asarray(Image.open(p).convert('RGBA'))[y0:y1,x0:x1,3]>20
rows=a.any(1); y=0; bands=[]
while y<len(rows):
    if rows[y]:
        s=y
        while y<len(rows) and rows[y]: y+=1
        bands.append((s+y0,y+y0))
    y+=1
for b0,b1 in bands:
    cols=a[b0-y0:b1-y0].any(0); x=0; segs=[]
    while x<len(cols):
        if cols[x]:
            s=x
            while x<len(cols) and cols[x:x+4].any(): x+=1
            segs.append((s+x0,x+x0))
        x+=1
    print('rows',b0,b1,'segs',segs)
