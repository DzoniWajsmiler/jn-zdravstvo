import sys, pandas as pd, numpy as np, warnings
warnings.filterwarnings("ignore")
df = pd.read_excel(sys.argv[1], header=0).dropna(subset=["Naročnik"])
df["leto"] = pd.to_datetime(df["Datum oddaje naročila"], format="%d.%m.%Y").dt.year
v = df["Vrednost brez DDV"]
df["nekonk"] = df["Vrsta postopka"].str.contains("brez predhodne objave|brez predhodnega", case=False, na=False)
print("Skupaj mio:", round(v.sum()/1e6), " nekonkurenčni mio:", round(v[df.nekonk].sum()/1e6,1),
      " delež vrednost %:", round(100*v[df.nekonk].sum()/v.sum(),2), " število:", int(df.nekonk.sum()))
y = df.groupby("leto").apply(lambda g: pd.Series({"n":len(g),"mio":g["Vrednost brez DDV"].sum()/1e6,
    "nekonk_n":g.nekonk.sum(),"nekonk_mio":g.loc[g.nekonk,"Vrednost brez DDV"].sum()/1e6}))
print(y.round(1))
nk = df[df.nekonk].groupby("Naročnik")["Vrednost brez DDV"].agg(["count","sum"]).sort_values("sum",ascending=False).head(12)
print("\nNekonkurenčna po naročniku:\n", nk)
# prag 20.000: histogram v 1.000 EUR košarah pri naročilih male vrednosti
mv = df[df["Vrsta postopka"]=="Naročilo male vrednosti"]["Vrednost brez DDV"]
bins = list(range(10000, 30001, 2000))
print("\nMale vrednosti, histogram (EUR):\n", pd.cut(mv, bins).value_counts().sort_index())
band = df[(v>=17000)&(v<20000)]
sp = band.groupby(["Naročnik","Izvajalec","leto"]).size().reset_index(name="n")
sp = sp[sp.n>=3].sort_values("n",ascending=False)
print("\nTrojice naročnik/izvajalec/leto z >=3 naročili 17.000-19.999 EUR:", len(sp))
print(sp.head(10).to_string())
sp.to_csv("data/mozno_drobljenje.csv", index=False)
# koncentracija pri največjih naročnikih
big = df.groupby("Naročnik")["Vrednost brez DDV"].sum().sort_values(ascending=False).head(12).index
rows=[]
for n in big:
    g = df[df.Naročnik==n].groupby("Izvajalec")["Vrednost brez DDV"].sum().sort_values(ascending=False)
    rows.append((n[:45], round(g.sum()/1e6,1), g.index[0][:30], round(100*g.iloc[0]/g.sum(),1), round(100*g.head(3).sum()/g.sum(),1)))
print("\nKoncentracija:\n", pd.DataFrame(rows, columns=["naročnik","mio","top izvajalec","top1 %","top3 %"]).to_string(index=False))
print("\nNaročniki, ki niso bolnišnice (grosisti):", [n for n in df.Naročnik.unique() if "GROSIST" in n.upper() or "VELETRG" in n.upper()][:5])
