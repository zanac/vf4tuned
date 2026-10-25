#!/usr/bin/env python3
"""apply_text - write the English text table into the decrypted VF4 FT image, in place.

  apply_text.py <image.dec> <translations.py> <strings_cap.tsv> [--check]

Every translated string must fit its slot (original bytes + the NUL padding up to the next string);
the rest of the slot is zero-filled. Strings that still contain Japanese afterwards are listed.
"""
import importlib.util, re, sys


def load(path):
    spec = importlib.util.spec_from_file_location("tr", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main(a):
    check = "--check" in a
    a = [x for x in a if x != "--check"]
    img, trp, capp = a
    tr = load(trp)
    d = bytearray(open(img, "rb").read())
    slots = {}
    for line in open(capp, encoding="utf-8"):
        o, ln, cap, _ = line.rstrip("\n").split("\t", 3)
        slots[int(o, 16)] = (int(ln), int(cap))
    errors, done, left = [], 0, []
    for o, (ln, cap) in sorted(slots.items()):
        cur = bytes(d[o:o + ln]).decode("euc_jp")
        if o in tr.T:
            new = tr.T[o]
        else:
            new = cur
            for jp, en in tr.SUBST:
                new = new.replace(jp, en)
            if new == cur:
                if re.search(r"[぀-ヿ一-鿿]", cur):
                    left.append((o, cur))
                continue
        if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", new):
            errors.append("%x: Japanese left in translation %r" % (o, new))
            continue
        b = new.encode("euc_jp")          # ASCII, plus symbols such as the -> arrow kept from the original
        if len(b) > cap:
            errors.append("%x: %d bytes > slot %d: %r" % (o, len(b), cap, new))
            continue
        if not check:
            d[o:o + cap + 1] = b + b"\0" * (cap + 1 - len(b))
        done += 1
    unknown = [o for o in tr.T if o not in slots]
    for o in unknown:
        errors.append("%x: offset not in the string list" % o)
    print("%d strings %s, %d errors" % (done, "checked" if check else "written", len(errors)))
    for e in errors:
        print("  ERROR", e)
    print("%d strings left in Japanese" % len(left))
    if errors:
        sys.exit(1)
    if not check:
        open(img, "wb").write(d)
    return left


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    left = main(sys.argv[1:])
