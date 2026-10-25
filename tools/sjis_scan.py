#!/usr/bin/env python3
"""sjis_scan - find Shift-JIS text runs in a binary and dump them as TSV.

  sjis_scan.py <file> [min_chars=3] [out.tsv]

A run is a sequence of valid SJIS characters (double-byte JIS X 0208 plus
printable ASCII / half-width katakana) containing at least one double-byte
kana or kanji, terminated by NUL or by an invalid byte. Columns:
offset(hex)  bytes  fullwidth_chars  terminator  text
"""
import sys


def is_lead(b):
    return 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xEF


def is_trail(b):
    return 0x40 <= b <= 0xFC and b != 0x7F


def scan(data, min_chars):
    i, n = 0, len(data)
    while i < n:
        start, chars, wide, j = i, 0, 0, i
        while j < n:
            b = data[j]
            if is_lead(b) and j + 1 < n and is_trail(data[j + 1]):
                try:
                    data[j:j + 2].decode("cp932")
                except UnicodeDecodeError:
                    break
                j += 2
                chars += 1
                wide += 1
            elif 0x20 <= b <= 0x7E or 0xA1 <= b <= 0xDF or b in (0x0A, 0x0D):
                j += 1
                chars += 1
            else:
                break
        if wide >= 1 and chars >= min_chars:
            term = data[j] if j < n else -1
            text = data[start:j].decode("cp932", "replace").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")
            yield start, j - start, wide, term, text
            i = j + 1
        else:
            i = max(j, i + 1) if j > i else i + 1


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    data = open(sys.argv[1], "rb").read()
    mn = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    out = open(sys.argv[3], "w", encoding="utf-8") if len(sys.argv) > 3 else sys.stdout
    count = 0
    for off, ln, wide, term, text in scan(data, mn):
        out.write("%08x\t%d\t%d\t%s\t%s\n" % (off, ln, wide, "NUL" if term == 0 else "%02x" % term if term >= 0 else "EOF", text))
        count += 1
    sys.stderr.write("%d runs\n" % count)


if __name__ == "__main__":
    main()
