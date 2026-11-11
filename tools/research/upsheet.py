#!/usr/bin/env python3
"""upsheet.py - contact sheet of an exported sprite set.

    upsheet.py <export_dir/set_name> <out.png> [max_width]

Reads the manifest (<set_name>.json) written by "tools/sprtool.py export" and lays out every
texture on a dark background with its index (#N), rows up to max_width (default 1024) px.
Used to find which texture of a set holds a given caption.
"""
import sys, os, json
from PIL import Image, ImageDraw
d=sys.argv[1]; out=sys.argv[2]; maxw=int(sys.argv[3]) if len(sys.argv)>3 else 1024
base=os.path.basename(d.rstrip('/'))
man=json.load(open(os.path.join(d,base+'.json')))
tiles=[]
for t in man['textures']:
    im=Image.open(os.path.join(d,t['png'])); bg=Image.new('RGBA',im.size,(40,40,90,255)); bg.alpha_composite(im); tiles.append((t['index'],bg.convert('RGB')))
x=y=rowh=0; pos=[]
for i,t in tiles:
    if x+t.width>maxw and x>0: x=0; y+=rowh+14; rowh=0
    pos.append((i,t,x,y)); x+=t.width+4; rowh=max(rowh,t.height)
H=y+rowh+14
sheet=Image.new('RGB',(maxw,H),(10,10,10)); dr=ImageDraw.Draw(sheet)
for i,t,x,y in pos: sheet.paste(t,(x,y+14)); dr.text((x+2,y+1),'#%d'%i,fill=(255,255,0))
sheet.save(out); print(base,len(tiles),sheet.size)
