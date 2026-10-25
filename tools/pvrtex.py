#!/usr/bin/env python3
"""pvrtex - decode/encode PowerVR2 (Dreamcast/NAOMI) textures used by VF4 FT sprite sets.

Library + CLI. Supported: 16-bit twiddled, 16-bit linear (stride = width), VQ twiddled.
Pixel formats: 1555, 565, 4444.
"""
import struct
from PIL import Image


def _untwiddle_table(n):
    # morton: x bits on odd positions, y bits on even positions (PVR twiddling: y is the low bit)
    t = []
    for i in range(n):
        v, b = 0, 0
        while i >> b:
            v |= ((i >> b) & 1) << (2 * b)
            b += 1
        t.append(v)
    return t


_TW = _untwiddle_table(1024)


def twidx(x, y, w, h):
    """index of texel (x,y) in a twiddled w*h texture (handles rectangular textures)."""
    m = min(w, h)
    if w == h:
        return (_TW[y] << 1) | _TW[x]
    if w > h:      # stacked squares horizontally
        return (x // m) * m * m + ((_TW[y] << 1) | _TW[x % m])
    return (y // m) * m * m + ((_TW[y % m] << 1) | _TW[x])


def px(v, fmt):
    if fmt == "4444":
        return (((v >> 8) & 15) * 17, ((v >> 4) & 15) * 17, (v & 15) * 17, (v >> 12) * 17)
    if fmt == "565":
        return (((v >> 11) & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31, 255)
    return (((v >> 10) & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, (v & 31) * 255 // 31, 255 if v >> 15 else 0)


def decode(data, off, w, h, fmt, kind):
    img = Image.new("RGBA", (w, h))
    out = img.load()
    if kind == "vq":
        cb = struct.unpack_from("<1024H", data, off)
        idx = data[off + 2048:off + 2048 + (w * h) // 4]
        for y in range(0, h, 2):
            for x in range(0, w, 2):
                i = idx[twidx(x // 2, y // 2, w // 2, h // 2)]
                # each code = 2x2 texels, twiddled order (x low bit first)
                for k, (dx, dy) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
                    out[x + dx, y + dy] = px(cb[i * 4 + k], fmt)
    else:
        n = w * h
        vals = struct.unpack_from("<%dH" % n, data, off)
        for y in range(h):
            for x in range(w):
                v = vals[twidx(x, y, w, h)] if kind == "tw" else vals[y * w + x]
                out[x, y] = px(v, fmt)
    return img


def size_of(w, h, kind):
    return 2048 + w * h // 4 if kind == "vq" else w * h * 2


PIXFMT = {0: "1555", 1: "565", 2: "4444"}
KIND = {0x1: "tw", 0x3: "vq", 0xd: "tw"}   # 0xd = twiddled rectangle


def decode_rec(data, w, h, fmtword, off):
    """decode one VF4FT sprite texture record: fmtword = (kind << 8) | pixel format."""
    return decode(data, off, w, h, PIXFMT[fmtword & 0xff], KIND[(fmtword >> 8) & 0xff])


# ---------------------------------------------------------------- encoding

def _pack(rgba, fmt):
    """rgba: (..., 4) uint8 numpy array -> uint16 array in pixel format fmt."""
    import numpy as np
    r, g, b, a = [rgba[..., i].astype(np.uint32) for i in range(4)]
    if fmt == "4444":
        q = lambda c: (c * 15 + 127) // 255
        return ((q(a) << 12) | (q(r) << 8) | (q(g) << 4) | q(b)).astype(np.uint16)
    if fmt == "565":
        return ((((r * 31 + 127) // 255) << 11) | (((g * 63 + 127) // 255) << 5) | ((b * 31 + 127) // 255)).astype(np.uint16)
    return (((a >= 128).astype(np.uint32) << 15) | (((r * 31 + 127) // 255) << 10)
            | (((g * 31 + 127) // 255) << 5) | ((b * 31 + 127) // 255)).astype(np.uint16)


def _unpack(v, fmt):
    import numpy as np
    return np.array([px(int(x), fmt) for x in v], dtype=np.float32)


def _tw_order(w, h):
    """flat list: position p in the stored stream -> (x, y)."""
    import numpy as np
    order = np.zeros((w * h, 2), dtype=np.int32)
    for y in range(h):
        for x in range(w):
            order[twidx(x, y, w, h)] = (x, y)
    return order


def encode(img, w, h, fmt, kind, seed=1):
    """PIL image (w x h, any mode) -> texture bytes for the given kind ('tw', 'lin', 'vq')."""
    import numpy as np
    a = np.asarray(img.convert("RGBA").resize((w, h)) if img.size != (w, h) else img.convert("RGBA"), dtype=np.uint8)
    if kind in ("tw", "lin"):
        v = _pack(a, fmt)
        if kind == "lin":
            return v.astype("<u2").tobytes()
        o = _tw_order(w, h)
        return v[o[:, 1], o[:, 0]].astype("<u2").tobytes()
    # VQ: 2x2 blocks in twiddled order, codebook of 256 x 4 texels (block order (0,0),(1,0),(0,1),(1,1))
    o = _tw_order(w // 2, h // 2)
    blocks = np.stack([a[o[:, 1] * 2 + dy, o[:, 0] * 2 + dx] for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))], 1)
    X = blocks.reshape(len(o), 16).astype(np.float32)
    uniq, inv = np.unique(X, axis=0, return_inverse=True)
    inv = inv.ravel()
    if len(uniq) <= 256:
        centers, labels = uniq, inv
    else:
        rng = np.random.default_rng(seed)
        cnt = np.bincount(inv).astype(np.float32)
        # k-means++ on unique blocks weighted by frequency
        centers = [uniq[rng.choice(len(uniq), p=cnt / cnt.sum())]]
        d2 = ((uniq - centers[0]) ** 2).sum(1)
        for _ in range(255):
            p = d2 * cnt; centers.append(uniq[rng.choice(len(uniq), p=p / p.sum())])
            d2 = np.minimum(d2, ((uniq - centers[-1]) ** 2).sum(1))
        centers = np.array(centers)
        for _ in range(25):
            dist = ((uniq[:, None, :] - centers[None]) ** 2).sum(2)
            lab = dist.argmin(1)
            for k in range(256):
                m = lab == k
                if m.any():
                    centers[k] = (uniq[m] * cnt[m, None]).sum(0) / cnt[m].sum()
        labels = lab[inv]
    cb = np.zeros((256, 4), dtype=np.uint16)
    cq = _pack(np.clip(np.rint(centers.reshape(-1, 4, 4)), 0, 255).astype(np.uint8), fmt)
    cb[:len(cq)] = cq
    return cb.astype("<u2").tobytes() + labels.astype(np.uint8).tobytes()


def encode_rec(img, w, h, fmtword):
    return encode(img, w, h, PIXFMT[fmtword & 0xff], KIND[(fmtword >> 8) & 0xff])
