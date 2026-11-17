"""Razčlenjevanje strani ejn.gov.si (podrobnosti naročila in pregled ponudnikov)."""
import re, html

def _lines(s):
    s = re.sub(r"(?s)<(script|style).*?</\1>", "", s)
    s = re.sub(r"<[^>]+>", "\n", s)
    return [l.strip() for l in html.unescape(s).split("\n") if l.strip()]

def _after(t, k):
    return t[t.index(k) + 1] if k in t and t.index(k) + 1 < len(t) else ""

def _num(x):
    x = re.sub(r"[^\d,.\-]", "", x or "")
    try: return float(x.replace(".", "").replace(",", "."))
    except ValueError: return None

def parse_podrobno(s):
    """Vrne slovar ali None, če naročilo ne obstaja."""
    t = _lines(s)
    if "Osnovni podatki javnega naročila" not in t: return None
    m = re.search(r"pregled-objav/(\d+)", s)
    return {"oznaka": _after(t, "Oznaka javnega naročila"), "pjn_st": _after(t, "Številka na PJN"),
            "postopek": _after(t, "Vrsta postopka"), "naziv": _after(t, "Naziv"),
            "predmet": _after(t, "Predmet naročila"), "narocnik": _after(t, "Naročnik"),
            "rok": _after(t, "Rok za oddajo ponudbe"), "odpiranje": _after(t, "Datum in ura javnega odpiranja ponudb"),
            "stanje": _after(t, "Stanje"), "pjn_id": m.group(1) if m else None}

def parse_ponudniki(s):
    """Vrne seznam sklopov [{sklop, stevilo, ponudniki:[{ime, brez_ddv}]}]; prazen seznam, če ponudbe niso vidne."""
    t = _lines(s)
    if any("ni v fazi javnega odpiranja" in x for x in t): return []
    out = []
    k = s.find("Seznam prejetih ponudb"); k = s.find("Seznam prejetih ponudb", k + 10)
    if k < 0: return []
    body = s[k:]
    parts = re.split(r"(?s)(?=<h3>\s*Sklop)", body) if "<h3> Sklop" in body or re.search(r"<h3>\s*Sklop", body) else [body]
    for p in parts:
        mh = re.match(r"(?s)<h3>\s*(Sklop[^<]*?)\s*</h3>", p)
        ms = re.search(r"Število prejetih ponudb</label>.*?>\s*(\d+)\s*<", p, re.S)
        rows = []
        for tr in re.findall(r'(?s)<tr data-ri="\d+".*?</tr>', p):
            tds = re.findall(r"(?s)<td[^>]*>(.*?)</td>", tr)
            if len(tds) >= 2:
                ime = html.unescape(re.sub(r"<[^>]+>", "", tds[0])).strip()
                rows.append({"ime": ime, "brez_ddv": _num(re.sub(r"<[^>]+>", "", tds[1]))})
        if ms or rows:
            out.append({"sklop": html.unescape(mh.group(1)).strip() if mh else "", "stevilo": int(ms.group(1)) if ms else len(rows), "ponudniki": rows})
    return out
