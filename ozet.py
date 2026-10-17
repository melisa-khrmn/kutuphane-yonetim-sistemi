"""Projedeki API uçlarını ve veritabanı sınıflarını ozet.txt dosyasına döker.
Proje ana klasöründe çalıştır:  python ozet.py
Veritabanına yazmaz, sadece okur."""
import io
import sys

from app.main import app

satirlar = []
yaz = satirlar.append

sema = app.openapi()
bilesenler = sema.get("components", {}).get("schemas", {})


def ad(s):
    if not s:
        return "-"
    if "$ref" in s:
        return s["$ref"].split("/")[-1]
    for anahtar in ("anyOf", "oneOf", "allOf"):
        if anahtar in s:
            return "|".join(ad(x) for x in s[anahtar])
    if s.get("type") == "array":
        return "[" + ad(s.get("items")) + "]"
    return s.get("type", "?")


def alanlar(isim):
    c = bilesenler.get(isim, {})
    zorunlu = set(c.get("required", []))
    return ", ".join(
        f"{k}{'*' if k in zorunlu else ''}:{ad(v)}" for k, v in c.get("properties", {}).items()
    )


def govde(op):
    icerik = op.get("requestBody", {}).get("content", {})
    if not icerik:
        return ""
    tur, s = next(iter(icerik.items()))
    isim = ad(s.get("schema"))
    return f" | GOVDE({tur.split('/')[-1]}) {isim}{{{alanlar(isim)}}}"


def cevap(op):
    for kod, c in op.get("responses", {}).items():
        if kod.startswith("2"):
            s = next(iter(c.get("content", {}).values()), {}).get("schema")
            isim = ad(s)
            ic = isim.strip("[]")
            return f" | CEVAP {kod} {isim}{{{alanlar(ic)}}}"
    return ""


yaz("===== API UCLARI (* = zorunlu alan) =====")
for yol, metotlar in sema["paths"].items():
    for metot, op in metotlar.items():
        if metot not in ("get", "post", "put", "patch", "delete"):
            continue
        prm = ", ".join(
            f"{p['in']}:{p['name']}" for p in op.get("parameters", [])
        )
        yaz(f"{metot.upper():6} {yol}" + (f" | PARAM {prm}" if prm else "") + govde(op) + cevap(op))

yaz("")
yaz("===== VERITABANI SINIFLARI =====")
model_baslangic = len(satirlar) - 1
try:
    from sqlalchemy.orm import DeclarativeBase

    gorulen = set()
    for taban in DeclarativeBase.__subclasses__():
        for m in taban.registry.mappers:
            if m.class_ in gorulen:
                continue
            gorulen.add(m.class_)
            ust = m.inherits.class_.__name__ if m.inherits else None
            yaz(f"\n{m.class_.__name__}" + (f"  (miras: {ust})" if ust else "") + f"  tablo={m.local_table.name}")
            yaz("  alanlar: " + ", ".join(f"{c.key}:{c.columns[0].type}" for c in m.column_attrs))
            for r in m.relationships:
                yaz(f"  iliski: {r.key} -> {r.mapper.class_.__name__} ({r.direction.name})")
            metotlar = [n for n, v in vars(m.class_).items() if callable(v) and not n.startswith("_")]
            if metotlar:
                yaz("  metotlar: " + ", ".join(metotlar))
except Exception as e:  # modeller okunamazsa API özeti yine de çıkar
    yaz(f"(Model bilgisi okunamadi: {e})")

metin = "\n".join(satirlar)
with io.open("ozet.txt", "w", encoding="utf-8") as f:
    f.write(metin)
sys.stdout.reconfigure(encoding="utf-8")
print("\n".join(satirlar[model_baslangic:]))
print("\n>>> ozet.txt dosyasi olusturuldu. Yukaridaki model listesini sohbete yapistir.")
