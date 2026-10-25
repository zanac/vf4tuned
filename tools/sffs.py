#!/usr/bin/env python3
"""sffs - reader for the "SimpleFlashFS" found in the VF4 Final Tuned DIMM image.

  sffs.py list    <image.dec> [base=0x800000]
  sffs.py extract <image.dec> <outdir> [base]      (.gz files are also gunzipped)

Layout (reverse engineered): 0x40-byte volume header at base, files start at
base+0x1000, each file = 0x100-byte entry header + data, aligned to 0x1000.
Entry: +0x00 remaining space, +0x04 allocated bytes (header+data, 4K multiple), +0x0c data size,
+0x14 mtime, +0x18 unix mode, +0x80 file name (NUL terminated).
"""
import os, struct, sys, zlib, time

def entries(d, base=0x800000):
    assert d[base:base + 13] == b"SimpleFlashFS", "no SimpleFlashFS at %x" % base
    p = base + 0x1000
    while p + 0x100 <= len(d):
        rem, bs, _, size = struct.unpack_from("<IIII", d, p)
        if rem == 0xFFFFFFFF or bs == 0 or bs & 0xFFF:
            break
        mtime, mode = struct.unpack_from("<II", d, p + 0x14)
        name = d[p + 0x80:d.index(b"\0", p + 0x80)].decode("latin1")
        yield dict(off=p, data=p + 0x100, size=size, mtime=mtime, mode=mode, name=name)
        p += bs                     # +0x04 = bytes allocated to this entry

def main(a):
    if len(a) < 2: raise SystemExit(__doc__)
    d = open(a[1], "rb").read()
    base = int(a[3 if a[0] == "extract" else 2], 0) if len(a) > (3 if a[0] == "extract" else 2) else 0x800000
    es = list(entries(d, base))
    if a[0] == "list":
        for e in es:
            print("%08x %9d %s %s" % (e["data"], e["size"], time.strftime("%Y-%m-%d", time.gmtime(e["mtime"])), e["name"]))
        last = es[-1]
        print("%d files, last data ends at %x" % (len(es), last["data"] + last["size"]), file=sys.stderr)
    elif a[0] == "extract":
        os.makedirs(a[2], exist_ok=True)
        for e in es:
            raw = d[e["data"]:e["data"] + e["size"]]
            name = e["name"]
            if name.endswith(".gz") and e["size"]:          # 3 empty test files have size 0
                z = zlib.decompressobj(31)                  # data size may include padding
                raw, name = z.decompress(raw), name[:-3]
            open(os.path.join(a[2], name), "wb").write(raw)
        print("%d files extracted" % len(es))
    else:
        raise SystemExit(__doc__)

if __name__ == "__main__":
    main(sys.argv[1:])
