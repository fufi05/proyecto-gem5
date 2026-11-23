#!/usr/bin/env python3
"""parse_stats.py <dir_resultados> > salida.csv
Lee <dir>/*/meta.txt y <dir>/*/stats.txt (primer bloque = region de interes)."""
import csv
import pathlib
import re
import sys

SEP = "---------- Begin Simulation Statistics ----------"


def first_block(path):
    blocks = [b for b in open(path).read().split(SEP) if b.strip()]
    return blocks[0]


def grab(block, pat):
    total, found = 0.0, False
    for line in block.splitlines():
        t = line.split()
        if len(t) >= 2 and re.search(pat, t[0]):
            try:
                total += float(t[1])
                found = True
            except ValueError:
                pass
    return total if found else float("nan")


def div(a, b):
    return a / b if b else float("nan")


rows = []
for m in sorted(pathlib.Path(sys.argv[1]).glob("*/meta.txt")):
    meta = dict(kv.split("=") for kv in m.read_text().split())
    b = first_block(m.parent / "stats.txt")
    cyc = grab(b, r"\.numCycles$")
    ins = grab(b, r"^simInsts$")
    rows.append(dict(
        meta, cycles=cyc, insts=ins, ipc=div(ins, cyc),
        l1d_miss=div(grab(b, r"l1d.*\.overallMisses::total$"),
                     grab(b, r"l1d.*\.overallAccesses::total$")),
        l2_miss=div(grab(b, r"l2.*\.overallMisses::total$"),
                    grab(b, r"l2.*\.overallAccesses::total$")),
    ))

if not rows:
    sys.exit("No se encontraron corridas con meta.txt en " + sys.argv[1])
w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]))
w.writeheader()
w.writerows(rows)