import pandas as pd, json, re, sys
d = pd.read_csv("data/obvestila_sklopi.csv", low_memory=False)
d = d[d.status_oddaje == 2].copy()
d["postopek"] = d["postopek"].astype(str).replace({"9": "Neznano (šifra 9)"})
def kratko(s):
    s = re.split(r",|\sd\.o\.o|\sd\.d\.|\sGmbH|\sAG\b", s.strip())[0].strip()
    return s.upper()
rows = []
d["_one"] = d.st_ponudb == 1
g = d.groupby("id_obvestila")._one.agg(["size", "all"])
vse1 = set(g[(g["size"] >= 3) & g["all"]].index)
SK = {"zdravstvo": "z", "ministrstvo": "m", "kandidat": "k"}
for r in d.itertuples():
    izv = [x.strip() for x in str(r.izvajalec).split("|")] if pd.notna(r.izvajalec) else []
    rows.append([int(r.id_obvestila), str(r.datum_pogodbe)[:10] if pd.notna(r.datum_pogodbe) else "",
        r.narocnik, str(r.naslov_sklopa) if pd.notna(r.naslov_sklopa) else "", r.postopek,
        None if pd.isna(r.ocenjena_sklop) else round(r.ocenjena_sklop),
        None if pd.isna(r.izbrana) else round(r.izbrana),
        None if pd.isna(r.st_ponudb) else int(r.st_ponudb),
        sorted({kratko(x) for x in izv}), str(r.razlog_brez_objave) if pd.notna(r.razlog_brez_objave) else "",
        SK.get(r.skupina, "z"),
        ("A" if r.id_obvestila in vse1 else "") + ("B" if pd.notna(r.ocenjena_sklop) and pd.notna(r.izbrana) and r.ocenjena_sklop > 0 and r.izbrana >= 10000 and 0.98 <= r.izbrana / r.ocenjena_sklop <= 1.0 else "")])
import os
odp = []; osv = ""
if os.path.exists("data/ejn_state.json"):
    st = json.load(open("data/ejn_state.json", encoding="utf-8"))
    for z in st["zapisi"].values():
        pb = [[x["sklop"], q["ime"], q["brez_ddv"]] for x in z.get("ponudbe", []) for q in x["ponudniki"]]
        n = sum(x["stevilo"] for x in z.get("ponudbe", [])) if z.get("ponudbe") else None
        odp.append([z["zadevaId"], z["narocnik"], z["naziv"], z["postopek"], z["stanje"], z["rok"], z["odpiranje"], bool(z.get("zdravstvo")), z.get("pjn_id"), pb, n])
        osv = max(osv, z.get("posodobljeno", ""))
odprta = json.dumps(odp, ensure_ascii=False).replace("</", "<\\/")
data = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
html = open("scripts/iskalnik_template.html", encoding="utf-8").read().replace("__DATA__", data).replace("__ODPRTA__", odprta).replace("OSVEZENO", json.dumps(osv))
open("docs/iskalnik.html", "w", encoding="utf-8").write(html)
print(len(rows), "sklopov,", round(len(html)/1e6, 1), "MB")
