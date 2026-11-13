import pandas as pd, json, re, sys
d = pd.read_csv("data/obvestila_sklopi.csv", low_memory=False)
d = d[d.status_oddaje == 2].copy()
d["postopek"] = d["postopek"].astype(str).replace({"9": "Neznano (šifra 9)"})
def kratko(s):
    s = re.split(r",|\sd\.o\.o|\sd\.d\.|\sGmbH|\sAG\b", s.strip())[0].strip()
    return s.upper()
rows = []
for r in d.itertuples():
    izv = [x.strip() for x in str(r.izvajalec).split("|")] if pd.notna(r.izvajalec) else []
    rows.append([int(r.id_obvestila), str(r.datum_pogodbe)[:10] if pd.notna(r.datum_pogodbe) else "",
        r.narocnik, str(r.naslov_sklopa) if pd.notna(r.naslov_sklopa) else "", r.postopek,
        None if pd.isna(r.ocenjena_sklop) else round(r.ocenjena_sklop),
        None if pd.isna(r.izbrana) else round(r.izbrana),
        None if pd.isna(r.st_ponudb) else int(r.st_ponudb),
        sorted({kratko(x) for x in izv}), str(r.razlog_brez_objave) if pd.notna(r.razlog_brez_objave) else ""])
data = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
html = open("scripts/iskalnik_template.html", encoding="utf-8").read().replace("__DATA__", data)
open("docs/iskalnik.html", "w", encoding="utf-8").write(html)
print(len(rows), "sklopov,", round(len(html)/1e6, 1), "MB")
