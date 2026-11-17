"""Pregleda zadevaId na ejn.gov.si, posodobi data/ejn_state.json.
Uporablja redke zahteve (privzeto 1 s), preskoči že končana naročila in znane neobstoječe številke."""
import argparse, json, sys, time, datetime, pathlib, urllib.robotparser, requests
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from ejn_lib import parse_podrobno, parse_ponudniki
ap = argparse.ArgumentParser()
ap.add_argument("--lo", type=int, default=77500)
ap.add_argument("--delay", type=float, default=1.0)
ap.add_argument("--max-miss", type=int, default=80)
ap.add_argument("--state", default="data/ejn_state.json")
a = ap.parse_args()
B = "https://ejn.gov.si/ponudba/pages"
PJN = "https://www.enarocanje.si"
HDR = {"User-Agent": "Mozilla/5.0 (compatible; jn-zdravstvo-research)", "Accept-Language": "sl"}
s = requests.Session(); s.headers.update(HDR)
FINAL = {"Zaključeno javno naročilo", "Ustavljeno"}
OPEN_STATES = {"Javno odpiranje ponudb", "Zaključeno zbiranje ponudb/prijav"}
sp = pathlib.Path(a.state)
st = json.load(open(sp, encoding="utf-8")) if sp.exists() else {"zapisi": {}, "ni": [], "cpv": {}}
zap, ni, cpvc = st["zapisi"], set(st["ni"]), st["cpv"]
rp = urllib.robotparser.RobotFileParser("https://ejn.gov.si/robots.txt")
robots = False
try: rp.read(); robots = True
except Exception as e: print("robots.txt ni dosegljiv:", e)

def get(url, tries=3):
    if robots and not rp.can_fetch("*", url): print("robots prepoveduje", url); return None
    for i in range(tries):
        try: r = s.get(url, timeout=40)
        except requests.RequestException as e: print("  napaka", e); time.sleep(5 * (i + 1)); continue
        if r.status_code in (429, 503): print("  status", r.status_code, "- ustavim"); raise SystemExit(2)
        return r
    return None

cpv_map = {}
try:
    r = requests.get(PJN + "/api/sifObrazec/sifCpvGridGetList", headers={**HDR, "Accept": "application/json"}, timeout=40)
    for x in r.json(): cpv_map[x["id"]] = x["label"].partition(" - ")[0]
    print("CPV seznam:", len(cpv_map))
except Exception as e: print("CPV seznam ni na voljo:", e)

def collect(o, acc):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "idSifCpv" and isinstance(v, int): acc.add(v)
            else: collect(v, acc)
    elif isinstance(o, list):
        for v in o: collect(v, acc)

def cpv_for(pjn_id):
    if pjn_id in cpvc: return cpvc[pjn_id]
    try:
        r = requests.get(f"{PJN}/api/obrazec/objava/obrazecGet?id={pjn_id}", headers={**HDR, "Accept": "application/json"}, timeout=40)
        ids = set(); collect(r.json(), ids)
        codes = sorted({cpv_map[i] for i in ids if i in cpv_map}); cpvc[pjn_id] = codes; time.sleep(0.5); return codes
    except Exception as e:
        print("  CPV ni na voljo za", pjn_id, e); return None

hi = max([int(k) for k in zap] + [a.lo]); cur, miss, n = a.lo, 0, 0
while True:
    if cur > hi and miss >= a.max_miss: break
    k = str(cur); rec = zap.get(k)
    if rec and rec["stanje"] in FINAL: cur += 1; continue
    if cur in ni and cur < hi - 200: cur += 1; continue
    r = get(f"{B}/aktualno/aktualno_jnc_podrobno.xhtml?zadevaId={cur}"); time.sleep(a.delay)
    p = parse_podrobno(r.text) if r is not None and r.status_code == 200 else None
    if p is None: ni.add(cur); miss += 1; cur += 1; continue
    miss = 0; hi = max(hi, cur); new = rec is None
    old_b = (rec or {}).get("ponudbe", [])
    p["ponudbe"] = old_b
    if p["stanje"] in OPEN_STATES:
        r2 = get(f"{B}/javno/javni_pregled_ponudnikov.xhtml?zadevaId={cur}"); time.sleep(a.delay)
        if r2 is not None and r2.status_code == 200:
            b = parse_ponudniki(r2.text)
            if b: p["ponudbe"] = b
    if p["pjn_id"]:
        p["cpv"] = cpv_for(p["pjn_id"]); 
    else: p["cpv"] = None
    p["zdravstvo"] = bool(p["cpv"]) and any(c.startswith("33") for c in p["cpv"])
    p["zadevaId"] = cur; p["posodobljeno"] = datetime.date.today().isoformat()
    zap[k] = p; n += 1; cur += 1
    if n % 50 == 0:
        st.update({"zapisi": zap, "ni": sorted(ni), "cpv": cpvc}); json.dump(st, open(sp, "w", encoding="utf-8"), ensure_ascii=False); print("shranjeno", n, "do", cur)
st.update({"zapisi": zap, "ni": sorted(ni), "cpv": cpvc})
sp.parent.mkdir(exist_ok=True); json.dump(st, open(sp, "w", encoding="utf-8"), ensure_ascii=False)
print("končano: obdelanih", n, "zapisov skupaj", len(zap), "zdravstvo", sum(1 for z in zap.values() if z.get("zdravstvo")))
