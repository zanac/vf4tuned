#!/usr/bin/env python3
"""vfpatch - tiny binary patch format for the decrypted VF41_S.BIN image.

  vfpatch.py make  <original.dec> <modified.dec> <out.vfp>
  vfpatch.py apply <image.dec> <patch.vfp>            (in place; checks the source hash first)

Format: b"VF4P" u32 version(1), 20-byte SHA1 of the source image, 20-byte SHA1 of the result,
u32 record count, then records {u32 offset, u32 length, bytes}. Little endian.
"""
import hashlib, struct, sys

MAGIC = b"VF4P"


def make(a, b, out):
    A, B = open(a, "rb").read(), open(b, "rb").read()
    if len(A) != len(B):
        raise SystemExit("images differ in size")
    recs, i, n = [], 0, len(A)
    while i < n:
        if A[i] == B[i]:
            i += 1
            continue
        j = i
        while j < n and (A[j] != B[j] or A[j:j + 16] != B[j:j + 16]):   # merge gaps < 16 bytes
            j += 1
        recs.append((i, B[i:j]))
        i = j
    with open(out, "wb") as f:
        f.write(MAGIC + struct.pack("<I", 1) + hashlib.sha1(A).digest() + hashlib.sha1(B).digest())
        f.write(struct.pack("<I", len(recs)))
        for off, data in recs:
            f.write(struct.pack("<II", off, len(data)) + data)
    print("%d records, %d bytes changed" % (len(recs), sum(len(r[1]) for r in recs)))


def apply(img, patch):
    p = open(patch, "rb").read()
    if p[:4] != MAGIC:
        raise SystemExit("not a VF4P patch")
    src, dst = p[8:28], p[28:48]
    d = bytearray(open(img, "rb").read())
    h = hashlib.sha1(d).digest()
    if h == dst:
        print("already patched")
        return
    if h != src:
        raise SystemExit("source image SHA1 mismatch: is this the decrypted VF41_S.BIN of gds-0036f?")
    count, pos = struct.unpack_from("<I", p, 48)[0], 52
    for _ in range(count):
        off, ln = struct.unpack_from("<II", p, pos)
        d[off:off + ln] = p[pos + 8:pos + 8 + ln]
        pos += 8 + ln
    if hashlib.sha1(d).digest() != dst:
        raise SystemExit("result SHA1 mismatch")
    open(img, "wb").write(d)
    print("patch applied (%d records)" % count)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 4 and a[0] == "make":
        make(*a[1:])
    elif len(a) == 3 and a[0] == "apply":
        apply(*a[1:])
    else:
        raise SystemExit(__doc__)
