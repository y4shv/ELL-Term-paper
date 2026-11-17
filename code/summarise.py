#!/usr/bin/env python3
"""Summarise litmus results by test and skew.

Reports the hit fraction across runs: median, range, mean and sample
standard deviation. Also prints the 3/N bound when there are no hits.
"""
import csv
import statistics as st
from collections import defaultdict

TARGET = {"sb": "c00", "sb_mfence": "c00", "mp": "c10"}
NAME = {"sb": "SB (0,0)", "sb_mfence": "SB+mfence (0,0)", "mp": "MP (1,0)"}

rows = defaultdict(list)
with open("../results/litmus_raw.csv") as f:
    for r in csv.DictReader(f):
        rows[(r["test"], int(r["skew"]))].append(r)

print("%-17s %5s %4s %10s %10s %10s %10s %10s %9s %s" % (
    "test", "skew", "runs", "total N", "median", "min", "max", "mean",
    "sd", "hits"))

for (test, skew), rs in rows.items():
    key = TARGET[test]
    fr = [int(r[key]) / int(r["iterations"]) for r in rs]
    hits = sum(int(r[key]) for r in rs)
    total = sum(int(r["iterations"]) for r in rs)

    print("%-17s %5d %4d %10d %10.5f %10.5f %10.5f %10.5f %9.5f %d" % (
        NAME[test], skew, len(rs), total, st.median(fr), min(fr), max(fr),
        st.mean(fr), st.stdev(fr), hits), end="")
    
    if hits == 0:
        print("   rule of three: p < %.1e" % (3 / total), end="")
    print()

print("\nAll four outcomes, summed over the repeats, skew 0")

for test in ["sb", "sb_mfence", "mp"]:
    rs = rows[(test, 0)]
    s = {k: sum(int(r[k]) for r in rs) for k in ["c00", "c01", "c10", "c11"]}

    
    print("  %-10s (0,0)=%d (0,1)=%d (1,0)=%d (1,1)=%d" % (
        test, s["c00"], s["c01"], s["c10"], s["c11"]))
