#!/usr/bin/env python3
"""Prenese obvestila o oddaji z enarocanje.si za povezave iz izvoza Odprte skrinje.

Zazene se na TVOJEM racunalniku (iz delovnega okolja Claude do portala ni dostopa).
Stran je SPA, zato uporabimo Playwright. Za vsako obvestilo shrani:
  cache/<id>.txt   vidno besedilo strani
  cache/<id>.json  vsi JSON odgovori, ki jih je stran prenesla (da najdemo API)
Ponovni zagon nadaljuje tam, kjer se je ustavil.

Namestitev:  pip install playwright pandas openpyxl && playwright install chromium
Poskus:      python fetch_notices.py data/skrinja_cpv33_2021_2025.xlsx --limit 5 --headed
Polni zagon: python fetch_notices.py data/skrinja_cpv33_2021_2025.xlsx
"""
import argparse, json, random, re, sys, time
from pathlib import Path
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ap = argparse.ArgumentParser()
ap.add_argument("xlsx")
ap.add_argument("--out", default="cache")
ap.add_argument("--limit", type=int, default=0, help="samo prvih N obvestil (poskus)")
ap.add_argument("--delay", type=float, default=3.0, help="povprecna pavza med stranmi (s)")
ap.add_argument("--headed", action="store_true", help="pokazi okno brskalnika")
a = ap.parse_args()

out = Path(a.out); out.mkdir(exist_ok=True)
df = pd.read_excel(a.xlsx).dropna(subset=["Povezava do objave"])
urls = list(dict.fromkeys(df["Povezava do objave"]))
if a.limit: urls = urls[:a.limit]
failed = out / "failed.txt"

def nid(u): return re.search(r"/(\d+)\s*$", u).group(1)

with sync_playwright() as p:
    br = p.chromium.launch(headless=not a.headed)
    ctx = br.new_context(locale="sl-SI")
    page = ctx.new_page()
    bodies = []
    def on_resp(r):
        try:
            if "json" in (r.headers.get("content-type") or "") and "enarocanje" in r.url:
                bodies.append({"url": r.url, "status": r.status, "body": r.text()[:200000]})
        except Exception:
            pass
    page.on("response", on_resp)
    done = 0
    for i, u in enumerate(urls, 1):
        i_d = nid(u)
        if (out / f"{i_d}.txt").exists():
            continue
        bodies.clear()
        try:
            page.goto(u, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(1500)
            txt = page.inner_text("body")
            if len(txt) < 200:
                raise RuntimeError("prekratko besedilo")
            (out / f"{i_d}.txt").write_text(txt, encoding="utf-8")
            (out / f"{i_d}.json").write_text(json.dumps(bodies, ensure_ascii=False), encoding="utf-8")
            done += 1
            print(f"[{i}/{len(urls)}] {i_d} ok ({len(txt)} znakov, {len(bodies)} json)")
        except (PWTimeout, RuntimeError) as e:
            failed.open("a").write(f"{u}\t{e}\n")
            print(f"[{i}/{len(urls)}] {i_d} NAPAKA {e}", file=sys.stderr)
        time.sleep(max(1.0, random.gauss(a.delay, 0.7)))
    br.close()
print("preneseno v tem zagonu:", done)
