#!/usr/bin/env python3
"""euc_scan - list EUC-JP strings (NUL-terminated, >= 1 double-byte char) in a binary range.
  euc_scan.py <file> <start> <end> [ram_base] > out.tsv     columns: offset, ram, bytes, text
"""
import re, sys
f, a, b = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
ram = int(sys.argv[4], 0) if len(sys.argv) > 4 else None
d = open(f, 'rb').read()[a:b]
pat = re.compile(rb'(?:[\xa1-\xfe][\xa1-\xfe]|[\x20-\x7e]|\x8e[\xa1-\xdf]|\n)+\x00')
for m in pat.finditer(d):
    s = m.group()[:-1]
    if not re.search(rb'[\xa1-\xfe][\xa1-\xfe]', s):
        continue
    try:
        t = s.decode('euc_jp')
    except UnicodeDecodeError:
        continue
    jp = sum(1 for c in t if ord(c) > 0x3000)
    if jp < 2 or jp < len(t) * 0.25:
        continue
    o = a + m.start()
    print('%08x\t%s\t%d\t%s' % (o, '%08x' % (o - a + ram) if ram is not None else '-', len(s), t.replace('\n', '\\n')))
