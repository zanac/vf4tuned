#!/usr/bin/env python3
"""sprtool - export / import VF4 Final Tuned sprite textures as upright PNGs.

  sprtool.py sets   <image.dec>                              list sprite sets present on disc
  sprtool.py export <image.dec> <set> <outdir>               one PNG per texture + manifest.json
  sprtool.py import <image.dec> <pngdir> [<out.dec>]          re-encode every PNG listed in the
                                                             manifests found in pngdir and write
                                                             them into the image (in place if no out)

<set> is the sprite set file name as in the program table, e.g. spr_mode_sel.bin or spr_asc.bin.gz.
PNG names: <set-base>_<NN>.png. Sprite art is stored rotated 90 degrees; PNGs are exported upright
and rotated back on import, so edit them as they look on screen.

Import only touches textures whose PNG differs from what the image currently holds, rewrites the
SimpleFlashFS entry (size, data CRC-16/XMODEM at +0x10) and, for .gz entries, recompresses the file
(must still fit the entry's allocated 4 KB blocks).
"""
import binascii, gzip, io, json, os, struct, sys, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pvrtex, sffs, spr_sheets
from PIL import Image

UPRIGHT = Image.Transpose.ROTATE_90      # stored -> screen
STORED = Image.Transpose.ROTATE_270      # screen -> stored


def find_entry(d, name):
    for e in sffs.entries(d):
        if e["name"] == name:
            return e
    raise SystemExit("set %s not found in the filesystem" % name)


def file_bytes(d, e):
    raw = bytes(d[e["data"]:e["data"] + e["size"]])
    return zlib.decompressobj(31).decompress(raw) if e["name"].endswith(".gz") else raw


def write_file(d, e, content):
    """write new content for entry e (recompressing .gz), update size and data CRC."""
    if e["name"].endswith(".gz"):
        hdr = bytes(d[e["data"]:e["data"] + 10])
        mtime = struct.unpack_from("<I", hdr, 4)[0]
        buf = io.BytesIO()
        with gzip.GzipFile(filename=e["name"][:-3], mode="wb", fileobj=buf, compresslevel=9, mtime=mtime) as g:
            g.write(content)
        data = buf.getvalue()
    else:
        data = content
    alloc = struct.unpack_from("<I", d, e["off"] + 4)[0] - 0x100
    if len(data) > alloc:
        raise SystemExit("%s: new data %d bytes exceeds allocated %d" % (e["name"], len(data), alloc))
    d[e["data"]:e["data"] + alloc] = data + b"\xff" * (alloc - len(data))
    struct.pack_into("<I", d, e["off"] + 0x0c, len(data))
    struct.pack_into("<I", d, e["off"] + 0x10, binascii.crc_hqx(data, 0))
    e["size"] = len(data)


def sets_on_disc(d):
    names = {e["name"] for e in sffs.entries(d)}
    return [(n, r) for n, v, r in spr_sheets.sprite_sets(d) if n in names]


def cmd_export(d, setname, outdir):
    recs = dict(sets_on_disc(d))[setname]
    content = file_bytes(d, find_entry(d, setname))
    os.makedirs(outdir, exist_ok=True)
    base = setname.split(".")[0]
    man = {"set": setname, "textures": []}
    for i, (w, h, f, o) in enumerate(recs):
        png = "%s_%02d.png" % (base, i)
        pvrtex.decode_rec(content, w, h, f, o).transpose(UPRIGHT).save(os.path.join(outdir, png))
        man["textures"].append({"png": png, "index": i, "w": w, "h": h, "fmt": "%#x" % f, "offset": "%#x" % o})
    with open(os.path.join(outdir, base + ".json"), "w") as fh:
        json.dump(man, fh, indent=1)
    print("%s: %d textures exported to %s" % (setname, len(recs), outdir))


def cmd_import(d, pngdir):
    sets = dict(sets_on_disc(d))
    total = 0
    for jf in sorted(f for f in os.listdir(pngdir) if f.endswith(".json")):
        man = json.load(open(os.path.join(pngdir, jf)))
        setname = man["set"]
        e = find_entry(d, setname)
        content = bytearray(file_bytes(d, e))
        changed = []
        for t in man["textures"]:
            p = os.path.join(pngdir, t["png"])
            if not os.path.exists(p):
                continue
            w, h, f, o = sets[setname][t["index"]]
            img = Image.open(p).convert("RGBA").transpose(STORED)
            if img.size != (w, h):
                raise SystemExit("%s: size %s, expected %dx%d (upright %dx%d)" % (t["png"], img.size, w, h, h, w))
            cur = pvrtex.decode_rec(content, w, h, f, o)
            if cur.tobytes() == img.tobytes():        # (ImageChops.difference ignores RGB when alpha is equal)
                continue
            enc = pvrtex.encode_rec(img, w, h, f)
            content[o:o + len(enc)] = enc
            changed.append(t["index"])
        if changed:
            write_file(d, e, bytes(content))
            print("%s: textures %s re-encoded" % (setname, changed))
            total += len(changed)
    print("%d textures written" % total)


def main(a):
    if len(a) < 2:
        raise SystemExit(__doc__)
    d = bytearray(open(a[1], "rb").read())
    if a[0] == "sets":
        for n, r in sets_on_disc(d):
            print("%-24s %3d textures" % (n, len(r)))
    elif a[0] == "export" and len(a) == 4:
        cmd_export(d, a[2], a[3])
    elif a[0] == "import" and len(a) in (3, 4):
        cmd_import(d, a[2])
        open(a[3] if len(a) == 4 else a[1], "wb").write(d)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
