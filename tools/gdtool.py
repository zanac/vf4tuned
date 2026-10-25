#!/usr/bin/env python3
"""gdtool - minimal NAOMI GD-ROM image helper working on a GDI dump (chdman extractcd).

  gdtool.py info    <disc.gdi>
  gdtool.py ls      <disc.gdi>                    list root directory of the HD-area ISO9660
  gdtool.py extract <disc.gdi> <NAME> <out>       copy a file out (raw, still encrypted)
  gdtool.py inject  <disc.gdi> <NAME> <in>        overwrite a file in place (must fit its sectors)

The HD area of a NAOMI GD starts at LBA 45000; the PVD is at 45000+16.
"""
import os
import struct
import subprocess
import sys

HD_LBA = 45000


class Gdi:
    def __init__(self, path):
        self.dir = os.path.dirname(os.path.abspath(path))
        self.tracks = []
        with open(path) as f:
            lines = [l.split() for l in f if l.strip()]
        for t in lines[1:1 + int(lines[0][0])]:
            # num lba type sectorsize file offset (file may be quoted)
            num, lba, typ, ssize = int(t[0]), int(t[1]), int(t[2]), int(t[3])
            fname = " ".join(t[4:-1]).strip('"')
            path_t = os.path.join(self.dir, fname)
            self.tracks.append(dict(num=num, lba=lba, type=typ, ssize=ssize, file=path_t,
                                    sectors=os.path.getsize(path_t) // ssize))

    def track_for(self, lba):
        best = None
        for t in self.tracks:
            if t["type"] == 4 and t["lba"] <= lba < t["lba"] + t["sectors"]:
                best = t
        if best is None:
            raise ValueError("LBA %d not in any data track" % lba)
        return best

    def _loc(self, lba):
        t = self.track_for(lba)
        off = (lba - t["lba"]) * t["ssize"] + (16 if t["ssize"] == 2352 else 0)
        return t, off

    def read(self, lba, count=1):
        out = bytearray()
        for i in range(count):
            t, off = self._loc(lba + i)
            with open(t["file"], "rb") as f:
                f.seek(off)
                out += f.read(2048)
        return bytes(out)

    def write(self, lba, data):
        """Write user data; for 2352-byte tracks EDC/ECC is regenerated with tools/cdecc."""
        assert len(data) % 2048 == 0
        n = len(data) // 2048
        t, _ = self._loc(lba)
        if lba + n > t["lba"] + t["sectors"]:
            raise SystemExit("write crosses track boundary")
        with open(t["file"], "r+b") as f:
            for i in range(n):
                f.seek((lba + i - t["lba"]) * t["ssize"] + (16 if t["ssize"] == 2352 else 0))
                f.write(data[i * 2048:(i + 1) * 2048])
        if t["ssize"] == 2352:
            cdecc = os.environ.get("CDECC") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "cdecc")
            subprocess.run([cdecc, t["file"], str(lba - t["lba"]), str(n)], check=True)


def root_entries(g):
    pvd = g.read(HD_LBA + 16)
    if pvd[1:6] != b"CD001":
        raise SystemExit("no ISO9660 PVD at LBA %d" % (HD_LBA + 16))
    rlba, rsize = struct.unpack_from("<I", pvd, 156 + 2)[0], struct.unpack_from("<I", pvd, 156 + 10)[0]
    data = g.read(rlba, (rsize + 2047) // 2048)
    ents, pos = [], 0
    while pos < len(data):
        ln = data[pos]
        if ln == 0:
            pos = (pos // 2048 + 1) * 2048
            continue
        lba, size, flags = struct.unpack_from("<I", data, pos + 2)[0], struct.unpack_from("<I", data, pos + 10)[0], data[pos + 25]
        name = data[pos + 33:pos + 33 + data[pos + 32]].decode("ascii", "replace").split(";")[0]
        if name not in ("\x00", "\x01"):
            ents.append(dict(name=name, lba=lba, size=size, dir=bool(flags & 2)))
        pos += ln
    return pvd, ents


def find(g, name):
    for e in root_entries(g)[1]:
        if e["name"].upper() == name.upper():
            return e
    raise SystemExit("file %s not found" % name)


def main(a):
    if len(a) < 2:
        raise SystemExit(__doc__)
    g = Gdi(a[1])
    if a[0] == "info":
        for t in g.tracks:
            print("track %(num)d lba %(lba)d type %(type)d ssize %(ssize)d sectors %(sectors)d" % t)
        pvd, _ = root_entries(g)
        print("volume id:", pvd[40:72].decode("ascii", "replace").strip())
    elif a[0] == "ls":
        for e in root_entries(g)[1]:
            print("%-24s lba %8d size %10d%s" % (e["name"], e["lba"], e["size"], " <DIR>" if e["dir"] else ""))
    elif a[0] == "extract":
        e = find(g, a[2])
        with open(a[3], "wb") as f:
            f.write(g.read(e["lba"], (e["size"] + 2047) // 2048)[:e["size"]])
        print("extracted %s: %d bytes" % (e["name"], e["size"]))
    elif a[0] == "inject":
        e = find(g, a[2])
        data = open(a[3], "rb").read()
        if len(data) > ((e["size"] + 2047) // 2048) * 2048:
            raise SystemExit("new file (%d) larger than allocated sectors of %s (%d)" % (len(data), e["name"], e["size"]))
        if len(data) != e["size"]:
            raise SystemExit("size change not supported yet (%d -> %d)" % (e["size"], len(data)))
        nsec = (e["size"] + 2047) // 2048
        orig = g.read(e["lba"], nsec)          # keep original tail padding of the last sector
        g.write(e["lba"], data + orig[len(data):])
        print("injected %s: %d bytes" % (e["name"], e["size"]))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
