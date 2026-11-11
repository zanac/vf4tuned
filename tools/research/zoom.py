#!/usr/bin/env python3
"""zoom.py - magnified crop of a texture with a coordinate grid.

    zoom.py <texture.png> <x0> <y0> <x1> <y1> <scale> <out.png>

Draws the crop on magenta (to see the alpha) with a tick every 8 px and a label every 32 px, to
read exact pixel coordinates for the boxes of text/gfx_spec.py.
"""
import sys
from PIL import Image, ImageDraw
p,x0,y0,x1,y1,sc,out=sys.argv[1],*map(int,sys.argv[2:7]),sys.argv[7]
im=Image.open(p).convert('RGBA').crop((x0,y0,x1,y1)); bg=Image.new('RGBA',im.size,(255,0,255,255)); bg.alpha_composite(im)
big=bg.convert('RGB').resize((im.width*sc,im.height*sc),Image.NEAREST); dr=ImageDraw.Draw(big)
for x in range((x0+7)//8*8,x1,8):
    X=(x-x0)*sc; dr.line((X,0,X,6),fill=(0,255,0)); dr.text((X+1,0),str(x),fill=(0,255,0)) if x%32==0 else None
for y in range((y0+7)//8*8,y1,8):
    Y=(y-y0)*sc; dr.line((0,Y,6,Y),fill=(0,255,0)); dr.text((0,Y+1),str(y),fill=(0,255,0)) if y%32==0 else None
big.save(out)
