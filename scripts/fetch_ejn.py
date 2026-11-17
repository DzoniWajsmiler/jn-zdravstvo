"""Poskusni prenos strani z ejn.gov.si (odprta naročila in pregled ponudnikov).
Shrani surov HTML, da lahko preverimo strukturo. Redke zahteve, upošteva robots.txt."""
import argparse, csv, sys, time, pathlib, urllib.robotparser, requests
B = "https://ejn.gov.si/ponudba/pages"
URLS = {"podrobno": B + "/aktualno/aktualno_jnc_podrobno.xhtml?zadevaId={}",
        "ponudniki": B + "/javno/javni_pregled_ponudnikov.xhtml?zadevaId={}"}
ap = argparse.ArgumentParser()
ap.add_argument("od", type=int); ap.add_argument("do", type=int)
ap.add_argument("--out", default="cache_ejn"); ap.add_argument("--delay", type=float, default=1.5)
a = ap.parse_args()
out = pathlib.Path(a.out); out.mkdir(exist_ok=True)
s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0 (compatible; jn-zdravstvo-research)", "Accept-Language": "sl"})
rp = urllib.robotparser.RobotFileParser("https://ejn.gov.si/robots.txt")
robots_ok = False
try: rp.read(); robots_ok = True; print("robots.txt prebran")
except Exception as e: print("robots.txt ni dosegljiv:", e)
rows, fails = [], 0
for zid in range(a.od, a.do + 1):
    for kind, tpl in URLS.items():
        url = tpl.format(zid)
        if robots_ok and not rp.can_fetch("*", url):
            print("robots prepoveduje", url); rows.append([zid, kind, "robots", 0]); continue
        try:
            r = s.get(url, timeout=30)
        except Exception as e:
            print("napaka", zid, kind, e); fails += 1; rows.append([zid, kind, "exc", 0])
            if fails >= 5: sys.exit("preveč napak zaporedoma")
            time.sleep(a.delay); continue
        if r.status_code in (429, 503): print("status", r.status_code, "ustavljam"); sys.exit(1)
        fails = 0
        (out / f"{kind}_{zid}.html").write_text(r.text, encoding="utf-8")
        rows.append([zid, kind, r.status_code, len(r.text)]); print(zid, kind, r.status_code, len(r.text))
        time.sleep(a.delay)
with open(out / "index.csv", "w", newline="") as f: csv.writer(f).writerows([["zadevaId", "vrsta", "status", "dolzina"]] + rows)
