import pandas as pd, numpy as np, re, warnings
warnings.filterwarnings("ignore")
x = pd.read_excel("data/skrinja_cpv33_2021_2025.xlsx").dropna(subset=["Naročnik"])
x["id"] = x["Povezava do objave"].astype(str).str.extract(r"(?:/|id_obrazec=)(\d+)\s*$")[0].astype(float)
x["format"] = np.where(x["id"] >= 600000, "novo", "staro")
x["d"] = pd.to_datetime(x["Datum oddaje naročila"], format="%d.%m.%Y", errors="coerce")
print("=== Pokritost po formatu obvestila (izvoz Skrinje) ===")
print(x.groupby("format").agg(vrstic=("id", "size"), obvestil=("id", "nunique"), mio=("Vrednost brez DDV", lambda s: s.sum()/1e6),
      od=("d", "min"), do=("d", "max")).round(1))
x.groupby([x.d.dt.year, "format"])["Vrednost brez DDV"].agg(["size", lambda s: s.sum()/1e6]).round(0).to_csv("data/pokritost_po_letih.csv")

d = pd.read_csv("data/obvestila_sklopi.csv", low_memory=False)
d["datum"] = pd.to_datetime(d["datum_pogodbe"], errors="coerce")
d = d[d.status_oddaje == 2].copy()   # samo oddana
d["cpv2"] = d["cpv_dodatni"].fillna("").str.split(";").str[0].where(d["cpv_dodatni"].notna() & (d["cpv_dodatni"] != ""), d["cpv_glavni"].astype(str))
d["zdravila"] = d["cpv2"].astype(str).str.startswith("336")
d["ena_ponudba"] = d.st_ponudb == 1
d["pod_oc"] = (d.ocenjena_sklop - d.izbrana) / d.ocenjena_sklop
print("\n=== Sklopi z oddajo (novi format):", len(d), " obvestil:", d.id_obvestila.nunique(), " mio izbrana:", round(d.izbrana.sum()/1e6))
v = d[d.st_ponudb.notna()]
print("ponudb mediana/povp:", v.st_ponudb.median(), round(v.st_ponudb.mean(), 2))
print("\nDelež sklopov z eno ponudbo (po številu / po vrednosti izbrane):")
def tab(g):
    return pd.Series({"sklopov": len(g), "ena_ponudba_%": 100*g.ena_ponudba.mean(), "ena_ponudba_vrednost_%": 100*g.loc[g.ena_ponudba, "izbrana"].sum()/g.izbrana.sum() if g.izbrana.sum() else np.nan, "mio": g.izbrana.sum()/1e6})
print(v.groupby("postopek").apply(tab).round(1).sort_values("mio", ascending=False).to_string())
print("\nZdravila vs ostalo (336 po CPV):"); print(v.groupby("zdravila").apply(tab).round(1).to_string())
print("\nTop naročniki po vrednosti, delež eno-ponudbenih:")
big = v.groupby("narocnik").apply(tab); print(big.sort_values("mio", ascending=False).head(15).round(1).to_string())
big.sort_values("mio", ascending=False).round(2).to_csv("data/narocniki_ena_ponudba.csv")
r = v[v.ocenjena_sklop > 0].copy()
print("\nIzbrana cena glede na ocenjeno vrednost (sklopi z obema):", len(r))
print(r.pod_oc.describe(percentiles=[.1,.25,.5,.75,.9]).round(3).to_string())
print("nad ocenjeno: %.1f%% sklopov; pod ocenjeno >5%%: %.1f%%; do 1%% pod ocenjeno: %.1f%%" % (100*(r.pod_oc < 0).mean(), 100*(r.pod_oc > .05).mean(), 100*r.pod_oc.between(0, .01).mean()))
print("Ena ponudba: mediana pod ocenjeno %.3f; več ponudb: %.3f" % (r[r.ena_ponudba].pod_oc.median(), r[~r.ena_ponudba].pod_oc.median()))
print("Skupaj ocenjeno %.0f mio, izbrano %.0f mio, razlika %.0f mio (sklopi z obema)" % (r.ocenjena_sklop.sum()/1e6, r.izbrana.sum()/1e6, (r.ocenjena_sklop.sum()-r.izbrana.sum())/1e6))
print("\nDatumi pogodb novi format:", d.datum.min(), d.datum.max())
