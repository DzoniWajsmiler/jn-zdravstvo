#!/usr/bin/env python3
"""Prenese obvestila neposredno iz javnega API-ja enarocanje.si (brez brskalnika).

Endpoint, ki ga uporablja sama stran:
  https://www.enarocanje.si/api/obrazec/objava/obrazecGet?id=<ID obvestila>
Za vsak ID shrani surovi JSON v cache_api/<id>.json. Nadaljuje po prekinitvi.
Najprej enkrat prenese tudi seznam CPV (cpv.json).
"""
import argparse, random, re, sys, time, json
from pathlib import Path
import pandas as pd, requests

ap = argparse.ArgumentParser()
ap.add_argument("xlsx", nargs="?")
ap.add_argument("--ids", default="")
ap.add_argument("--out", default="cache_api")
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--shard", default="")
ap.add_argument("--delay", type=float, default=0.8)
a = ap.parse_args()

BASE = "https://www.enarocanje.si"
out = Path(a.out); out.mkdir(exist_ok=True)
s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "sl-SI,sl;q=0.9",
    "Referer": BASE + "/",
})

def get(path, tries=4):
    for i in range(tries):
        try:
            r = s.get(BASE + path, timeout=40)
        except requests.RequestException as e:
            print("  omrezna napaka:", e, file=sys.stderr); time.sleep(5 * (i + 1)); continue
        if r.status_code == 200 and r.text.lstrip().startswith(("{", "[")):
            return r
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(10 * (i + 1)); continue
        print(f"  HTTP {r.status_code} za {path}: {r.text[:200]!r}", file=sys.stderr)
        return None
    return None

cpv = out / "cpv.json"
if not cpv.exists():
    r = get("/api/sifObrazec/sifCpvGridGetList")
    if r is None:
        sys.exit("Ne morem prenesti seznama CPV. API morda zahteva drugacne glave ali blokira ta naslov.")
    cpv.write_text(r.text, encoding="utf-8")
    print("cpv.json:", len(r.text), "znakov")

def _id(u):
    m = re.search(r"(?:/|id_obrazec=)(\d+)\s*$", str(u))
    return m.group(1) if m else None
if a.ids:
    ids = [l.strip() for l in open(a.ids) if l.strip()]
else:
    df = pd.read_excel(a.xlsx).dropna(subset=["Povezava do objave"])
    ids = [i for i in dict.fromkeys(_id(u) for u in df["Povezava do objave"]) if i]
if a.shard:
    k, n = map(int, a.shard.split("/")); ids = ids[k::n]
if a.limit: ids = ids[:a.limit]

fails = consecutive = done = 0
for i, nid in enumerate(ids, 1):
    f = out / f"{nid}.json"
    if f.exists(): continue
    r = get(f"/api/obrazec/objava/obrazecGet?id={nid}")
    if r is None:
        fails += 1; consecutive += 1
        (out / "failed.txt").open("a").write(nid + "\n")
        if consecutive >= 5:
            sys.exit("5 zaporednih napak, ustavljam (verjetno blokada ali sprememba API-ja).")
    else:
        consecutive = 0; done += 1
        f.write_text(r.text, encoding="utf-8")
        if i % 50 == 0 or i <= 5: print(f"[{i}/{len(ids)}] {nid} ok ({len(r.text)} znakov)")
    time.sleep(max(0.3, random.gauss(a.delay, 0.2)))
print(f"preneseno: {done}, napak: {fails}")
