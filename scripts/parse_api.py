#!/usr/bin/env python3
"""Iz cache_api/<id>.json naredi eno vrstico na oddajo po sklopih (lot).
Izhod: data/obvestila_sklopi.csv
"""
import json, sys, csv
from pathlib import Path
cache = Path(sys.argv[1] if len(sys.argv) > 1 else "cache_api")
POSTOPEK = {1: "Odprti postopek", 2: "Omejeni postopek", 3: "Konkurenčni postopek s pogajanji",
            4: "Konkurenčni dialog", 5: "Partnerstvo za inovacije", 6: "Oddaja brez predhodne objave",
            7: "Naročilo male vrednosti (po obrazcu SL2)", 8: "Drugo"}
cpv = {}
cf = cache / "cpv.json"
if cf.exists():
    for r in json.load(open(cf, encoding="utf-8")):
        code, _, name = r["label"].partition(" - ")
        cpv[r["id"]] = (code, name)
def c(i):
    return cpv.get(int(i), ("", ""))[0] if i not in (None, "None") else ""
def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

rows = []
for f in sorted(cache.glob("[0-9]*.json")):
    try: j = json.load(open(f, encoding="utf-8"))
    except Exception: continue
    nar = (j.get("narocnik") or [{}])[0]
    sklopi = {s["id"]: s for s in j.get("obrazecSklop", [])}
    pogodbe = j.get("obrazecPogodba") or []
    datum_pogodbe = next((p.get("datumSklenitev") for p in pogodbe if p.get("datumSklenitev")), None)
    for od in j.get("obrazecOddaja", []):
        sk = sklopi.get(od.get("idObrazecSklop"), {})
        dodatni = [c(x.get("id")) for x in sk.get("obrazecSklopCpv", [])]
        subj = [x.get("naziv") for x in od.get("obrazecOddajaSubjekt", []) if x.get("naziv")]
        rows.append({
            "id_obvestila": f.stem, "objava": j.get("objavaIdent"), "obrazec": j.get("sifObrazecNaziv"),
            "postopek": POSTOPEK.get(j.get("idSifPostopekVrsta"), j.get("idSifPostopekVrsta")),
            "razlog_brez_objave": j.get("razlogOddajeBrezObjave"),
            "narocnik": nar.get("naziv"), "maticna": nar.get("maticna"),
            "naslov_sklopa": sk.get("naslov") or j.get("naslov"),
            "cpv_glavni": c(sk.get("idSifCpv") or j.get("idSifCpv")), "cpv_dodatni": ";".join(x for x in dodatni if x),
            "ocenjena_sklop": num(sk.get("vrednostOcenjenaBrezDDV")),
            "status_oddaje": od.get("idSifOddajaStatus"),
            "st_ponudb": num(od.get("steviloPonudbe")), "st_dopustnih": num(od.get("steviloDopustno")),
            "min_dopustna": num(od.get("vrednostMinDopustna")), "max_dopustna": num(od.get("vrednostMaxDopustna")),
            "izbrana": num(od.get("vrednostIzbrana")),
            "izvajalec": " | ".join(subj), "datum_pogodbe": datum_pogodbe,
        })
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "data/obvestila_sklopi.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)
if rows:
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), "vrstic (sklop/oddaja) iz", len(set(r["id_obvestila"] for r in rows)), "obvestil")
