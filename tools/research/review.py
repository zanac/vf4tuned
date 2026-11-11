#!/usr/bin/env python3
"""review.py - before/after sheet of the graphics edits.

    review.py <spec.py> <export_dir> <edited_dir> <out.png>

For every texture touched by the spec (text/gfx_spec.py: EDITS entries with set, tex, box) it
crops the union of the edited boxes from the original export and from the redrawn texture and
places them side by side (2x when narrow). This is how screenshots/graphics_before_after.png
was made.
"""
import sys, importlib.util
from PIL import Image, ImageDraw
spec=importlib.util.spec_from_file_location('s',sys.argv[1]); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
src,dst,out=sys.argv[2],sys.argv[3],sys.argv[4]
groups={}
for e in m.EDITS: groups.setdefault((e['set'],e['tex']),[]).append(e['box'])
tiles=[]
for (s,t),boxes in groups.items():
    x0=min(b[0] for b in boxes)-2; y0=min(b[1] for b in boxes)-2; x1=max(b[2] for b in boxes)+2; y1=max(b[3] for b in boxes)+2
    a=Image.open('%s/%s/%s_%02d.png'%(src,s,s,t)); b=Image.open('%s/%s/%s_%02d.png'%(dst,s,s,t))
    x0=max(0,x0);y0=max(0,y0);x1=min(a.width,x1);y1=min(a.height,y1)
    sc=2 if (x1-x0)<=300 else 1
    def prep(im):
        im=im.crop((x0,y0,x1,y1)); bg=Image.new('RGBA',im.size,(60,40,110,255)); bg.alpha_composite(im); return bg.convert('RGB').resize((im.width*sc,im.height*sc),Image.NEAREST)
    pa,pb=prep(a),prep(b)
    tile=Image.new('RGB',(pa.width*2+12,pa.height+14),(0,0,0)); tile.paste(pa,(0,14)); tile.paste(pb,(pa.width+12,14))
    ImageDraw.Draw(tile).text((2,1),'%s #%d'%(s,t),fill=(255,255,0)); tiles.append(tile)
W=max(t.width for t in tiles); H=sum(t.height+6 for t in tiles)
o=Image.new('RGB',(W,H)); y=0
for t in tiles: o.paste(t,(0,y)); y+=t.height+6
o.save(out); print(o.size)
