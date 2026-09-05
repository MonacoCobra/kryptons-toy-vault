#!/usr/bin/env python3
"""Image Comics densify: Spawn, Walking Dead, Saga + select majors. Floor 1980."""
from __future__ import annotations
import json
from pathlib import Path
from comic_backlog_common import (
    FLOOR, BatchBuilder, load_blocklists, cover, interp_date, BACKLOG,
)

PUB = "Image Comics"
PAL_SPAWN = "111827,166534,dc2626"
PAL_TWD = "1f2937,9ca3af,7f1d1d"
PAL_SAGA = "7c2d12,1e3a8a,fbbf24"
PAL_SD = "166534,fbbf24,111827"
PAL_ELSE = "1e3a8a,dc2626,f8fafc"

EXISTING_IDS, EXISTING_KEYS = load_blocklists()
b = BatchBuilder(PUB, PAL_SPAWN, EXISTING_IDS, EXISTING_KEYS, target_min=1, target_max=20000)

def msrp_era(y):
    if y < 1996: return 1.95
    if y < 2000: return 2.50
    if y < 2006: return 2.95
    if y < 2012: return 2.99
    if y < 2018: return 3.99
    return 3.99

def date_msrp(cd): return msrp_era(int(cd[:4]))

def anchor_date(n, anchors):
    if n <= anchors[0][0]: return cover(anchors[0][1], anchors[0][2])
    if n >= anchors[-1][0]: return cover(anchors[-1][1], anchors[-1][2])
    for i in range(len(anchors)-1):
        n0,y0,m0=anchors[i]; n1,y1,m1=anchors[i+1]
        if n0 <= n <= n1: return interp_date(n,n0,y0,m0,n1,y1,m1)
    return cover(anchors[-1][1], anchors[-1][2])

# Spawn #1–350 (ongoing; archive has sparse)
SPAWN_A = [(1,1992,5),(50,1996,6),(100,2000,11),(150,2005,9),(200,2010,12),
           (250,2015,3),(300,2019,9),(350,2024,1)]
SPAWN_KEYS = {1,8,9,16,50,100,150,200,250,300,350}
for n in range(1, 351):
    cd = anchor_date(n, SPAWN_A)
    w = "Todd McFarlane" if n < 30 else ("Various" if n < 200 else "Todd McFarlane / Various")
    a = "Todd McFarlane" if n < 20 else "Various"
    b.try_add(f"im-spawn-{n}", "Spawn", n, cd, w, a,
              ("Spawn #1 — Image launch cornerstone." if n==1 else f"Spawn #{n}."),
              date_msrp(cd), demand=2.5 if n==1 else (1.2 if n in SPAWN_KEYS else 0.4),
              key=1 if n in SPAWN_KEYS else 0, palette=PAL_SPAWN)

print("SPAWN", len(b.rows))

# The Walking Dead #1–193
TWD_A = [(1,2003,10),(24,2005,11),(48,2008,4),(72,2010,5),(100,2012,7),
         (127,2014,5),(150,2016,1),(167,2017,5),(193,2019,7)]
TWD_KEYS = {1,7,8,19,27,48,100,127,150,167,193}
for n in range(1, 194):
    cd = anchor_date(n, TWD_A)
    b.try_add(f"im-twd-{n}", "The Walking Dead", n, cd, "Robert Kirkman", "Tony Moore" if n<=6 else "Charlie Adlard",
              ("The Walking Dead #1." if n==1 else ("Final issue — The Walking Dead #193." if n==193 else f"The Walking Dead #{n}.")),
              date_msrp(cd), demand=2.5 if n==1 else (1.3 if n in TWD_KEYS else 0.45),
              key=1 if n in TWD_KEYS else 0, palette=PAL_TWD)

print("TWD", len(b.rows))

# Saga #1–72+ (ongoing; archive sparse) — fill 1–72 densely, then 73–78 recent
for n in range(1, 79):
    # hiatus after 54 (~2018), resumed 2022
    if n <= 54:
        cd = interp_date(n, 1, 2012, 3, 54, 2018, 1)
    else:
        cd = interp_date(n, 55, 2022, 1, 78, 2026, 8)
    b.try_add(f"im-saga-{n}", "Saga", n, cd, "Brian K. Vaughan", "Fiona Staples",
              ("Saga #1 begins." if n==1 else f"Saga #{n}."),
              2.99 if n < 20 else 3.99, demand=2.0 if n==1 else 0.5,
              key=1 if n in (1,18,54,55) else 0, palette=PAL_SAGA)

# Savage Dragon #1–260 sample densify (long ongoing)
for n in range(1, 261):
    cd = interp_date(n, 1, 1993, 7, 260, 2024, 6)
    b.try_add(f"im-sd-{n}", "Savage Dragon", n, cd, "Erik Larsen", "Erik Larsen",
              ("Savage Dragon #1." if n==1 else f"Savage Dragon #{n}."),
              date_msrp(cd), demand=1.3 if n==1 else 0.3,
              key=1 if n in (1,50,100,200) else 0, palette=PAL_SD)

# Youngblood #1–10 early; WildC.A.T.s #1–50; Witchblade #1–50 densify starters
for n in range(1, 11):
    cd = interp_date(n, 1, 1992, 4, 10, 1993, 6)
    b.try_add(f"im-yb-{n}", "Youngblood", n, cd, "Rob Liefeld", "Rob Liefeld",
              ("Youngblood #1 — Image #1." if n==1 else f"Youngblood #{n}."),
              1.95, demand=1.5 if n==1 else 0.4, key=1 if n==1 else 0, palette=PAL_ELSE)
for n in range(1, 51):
    cd = interp_date(n, 1, 1992, 8, 50, 1998, 6)
    b.try_add(f"im-wildcats-{n}", "WildC.A.T.s", n, cd, "Brandon Choi / Jim Lee", "Jim Lee" if n<=10 else "Various",
              ("WildC.A.T.s #1." if n==1 else f"WildC.A.T.s #{n}."),
              date_msrp(cd), demand=1.4 if n==1 else 0.35, key=1 if n in (1,2) else 0, palette=PAL_ELSE)
for n in range(1, 51):
    cd = interp_date(n, 1, 1995, 11, 50, 2002, 3)
    # Top Cow imprint often Image / Top Cow
    b.pub = "Image / Top Cow"
    b.try_add(f"im-witchblade-{n}", "Witchblade", n, cd, "Various", "Michael Turner" if n<=12 else "Various",
              ("Witchblade #1." if n==1 else f"Witchblade #{n}."),
              date_msrp(cd), demand=1.3 if n==1 else 0.35, key=1 if n==1 else 0, palette=PAL_ELSE)
b.pub = PUB

# East of West #2–45; Paper Girls #2–30; Descender #2–32; Deadly Class #2–45
for n in range(2, 46):
    cd = interp_date(n, 1, 2013, 3, 45, 2019, 7)
    b.try_add(f"im-eow-{n}", "East of West", n, cd, "Jonathan Hickman", "Nick Dragotta",
              f"East of West #{n}.", 3.99, demand=0.5, key=0, palette=PAL_ELSE)
for n in range(2, 31):
    cd = interp_date(n, 1, 2015, 10, 30, 2019, 4)
    b.try_add(f"im-pg-{n}", "Paper Girls", n, cd, "Brian K. Vaughan", "Cliff Chiang",
              f"Paper Girls #{n}.", 3.99, demand=0.5, key=0, palette=PAL_ELSE)
for n in range(2, 33):
    cd = interp_date(n, 1, 2015, 3, 32, 2018, 5)
    b.try_add(f"im-desc-{n}", "Descender", n, cd, "Jeff Lemire", "Dustin Nguyen",
              f"Descender #{n}.", 3.99, demand=0.45, key=0, palette=PAL_ELSE)
for n in range(2, 46):
    cd = interp_date(n, 1, 2014, 1, 45, 2019, 11)
    b.try_add(f"im-dc-{n}", "Deadly Class", n, cd, "Rick Remender", "Wes Craig",
              f"Deadly Class #{n}.", 3.99, demand=0.45, key=0, palette=PAL_ELSE)

# Radiant Black #2–30; Ice Cream Man #2–40 densify
for n in range(2, 31):
    cd = interp_date(n, 1, 2021, 2, 30, 2024, 6)
    b.try_add(f"im-rb-{n}", "Radiant Black", n, cd, "Kyle Higgins", "Various",
              f"Radiant Black #{n}.", 3.99, demand=0.4, key=0, palette=PAL_ELSE)
for n in range(2, 41):
    cd = interp_date(n, 1, 2018, 1, 40, 2024, 8)
    b.try_add(f"im-icm-{n}", "Ice Cream Man", n, cd, "W. Maxwell Prince", "Martín Morazzo",
              f"Ice Cream Man #{n}.", 3.99, demand=0.45, key=0, palette=PAL_ELSE)

print("IMAGE_DONE", len(b.rows))
# relax finalize pub assert for Image / Top Cow — patch by temporarily allowing
# BatchBuilder.finalize asserts pub == self.pub or DC — we changed b.pub back to Image
# Witchblade rows have Image / Top Cow — finalize will fail. Fix: override finalize check.
# Quick fix: set self.pub check — call finalize after monkeypatch

_orig_finalize = b.finalize
def _finalize(priority_series=None):
    priority_series = priority_series or set()
    while len(b.rows) > b.target_max:
        cands = [i for i, r in enumerate(b.rows) if r[1] not in priority_series and r[11] == 0]
        if not cands:
            cands = [i for i, r in enumerate(b.rows) if r[11] == 0]
        if not cands: break
        drop_i = min(cands, key=lambda i: b.rows[i][4])
        b.skipped.append({"reason": "cap", "id": b.rows[drop_i][0], "series": b.rows[drop_i][1], "issue": b.rows[drop_i][2]})
        b.rows.pop(drop_i)
    import re
    b.rows.sort(key=lambda r: (r[4], r[1], int(re.sub(r"\D", "", str(r[2])) or 0)), reverse=True)
    assert len({r[0] for r in b.rows}) == len(b.rows)
    for r in b.rows:
        assert r[0] not in b.existing_ids
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", r[4])
        assert r[4] >= FLOOR
        assert r[9] in ("single", "facsimile", "tpb", "hardcover", "omnibus")
        assert r[3] == PUB or r[3].startswith("Image")
_finalize()
report = b.report()
out = b.write(
    "batch-008",
    "Image Comics densify — Spawn / Walking Dead / Saga / Savage Dragon + select majors",
    "Image permanent archive densify; floor 1980-01-01",
)
Path("/tmp/batch-008-report.json").write_text(json.dumps({
    "count": report["count"], "date_max": report["date_max"], "date_min": report["date_min"],
    "archive_skipped": report["archive_skipped"], "breakdown": report["breakdown"][:40], "floor": FLOOR,
}, indent=2))
print("WROTE", out)
