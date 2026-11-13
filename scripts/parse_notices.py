#!/usr/bin/env python3
"""Iz cache/*.txt izlusci CPV, stevilo ponudb in ocenjeno vrednost.
Regexi so ugibani (strani nisem videl), zato izpise tudi surove najdbe.
Po prvem poskusu (--limit 5) jih je treba uskladiti z dejanskim besedilom."""
import re, sys, csv
from pathlib import Path
cache = Path(sys.argv[1] if len(sys.argv) > 1 else "cache")
rows = []
for f in sorted(cache.glob("*.txt")):
    t = f.read_text(encoding="utf-8")
    cpv = sorted(set(re.findall(r"\b(\d{8})(?:-\d)?\b", t)))
    ponudbe = re.findall(r"(?:Število|Stevilo)\s+prejetih\s+ponudb[^\d\n]{0,80}(\d+)", t, flags=re.I)
    ocen = re.findall(r"Ocenjena\s+vrednost[^\d\n]{0,80}([\d\.\s]+(?:,\d+)?)", t, flags=re.I)
    rows.append({"id": f.stem, "cpv": ";".join(cpv), "ponudbe": ";".join(ponudbe), "ocenjena": ";".join(o.strip() for o in ocen)})
with open("data/obvestila_razclenjena.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["id", "cpv", "ponudbe", "ocenjena"]); w.writeheader(); w.writerows(rows)
print(len(rows), "obvestil;", sum(1 for r in rows if r["ponudbe"]), "s stevilom ponudb;", sum(1 for r in rows if r["cpv"]), "s CPV")
