"""Kütüphane API testleri (demo verisi üzerinde çalışır)."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

ADMIN = ("admin@kutuphane.com", "Admin123!")
AHMET = ("ahmet@ogr.edu.tr", "Uye123!")
AYSE = ("ayse@ogr.edu.tr", "Uye123!")  # gecikmiş kitabı olan üye


@pytest.fixture(scope="module")
def istemci():
    with TestClient(app) as c:
        yield c


def giris(istemci, kimlik):
    r = istemci.post("/api/auth/token", data={"username": kimlik[0], "password": kimlik[1]})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def liste(veri):
    """API düz liste ya da sayfalı nesne dönebilir; ilk listeyi bulur."""
    if isinstance(veri, list):
        return veri
    return next((v for v in veri.values() if isinstance(v, list)), [])


def kitaplar(istemci):
    """Sayfalı /api/kitaplar cevabının tüm sayfalarını birleştirir."""
    sonuc, sayfa = [], 1
    while True:
        v = istemci.get("/api/kitaplar", params={"sayfa": sayfa}).json()
        sonuc += v["kayitlar"]
        if sayfa >= v["toplam_sayfa"]:
            return sonuc
        sayfa += 1


def test_admin_giris_basarili(istemci):
    assert "Authorization" in giris(istemci, ADMIN)


def test_yanlis_sifre_reddedilir(istemci):
    r = istemci.post("/api/auth/token", data={"username": ADMIN[0], "password": "yanlis"})
    assert r.status_code in (400, 401)


def test_kitap_listesi_dolu(istemci):
    assert len(kitaplar(istemci)) > 0


def test_uye_kitap_ekleyemez(istemci):
    baslik = giris(istemci, AHMET)
    r = istemci.post("/api/kitaplar", headers=baslik, json={"baslik": "Yetkisiz", "isbn": "0000000000000", "toplam_adet": 1})
    assert r.status_code in (401, 403)


def test_odunc_al_ve_iade_et(istemci):
    h = giris(istemci, AHMET)
    aktifler = {o["kitap_id"] for o in liste(istemci.get("/api/oduncler/benim", headers=h).json())
                if o["durum"] in ("AKTIF", "GECIKMIS")}
    kitap = next((k for k in kitaplar(istemci) if k["mevcut_adet"] > 0 and k["id"] not in aktifler), None)
    if kitap is None:
        pytest.skip("Ödünç verilebilir kitap bulunamadı")

    r = istemci.post("/api/oduncler", headers=h, json={"kitap_id": kitap["id"]})
    assert r.status_code in (200, 201), r.text
    odunc = r.json()

    stok = istemci.get(f"/api/kitaplar/{kitap['id']}").json()["mevcut_adet"]
    assert stok == kitap["mevcut_adet"] - 1  # ödünç alınca stok düşer

    r = istemci.put(f"/api/oduncler/{odunc['id']}/iade", headers=h)
    assert r.status_code == 200, r.text
    stok = istemci.get(f"/api/kitaplar/{kitap['id']}").json()["mevcut_adet"]
    assert stok == kitap["mevcut_adet"]  # iade edince stok geri artar


def test_ayni_kitap_iki_kez_alinamaz(istemci):
    h = giris(istemci, AHMET)
    aktifler = {o["kitap_id"] for o in liste(istemci.get("/api/oduncler/benim", headers=h).json())
                if o["durum"] in ("AKTIF", "GECIKMIS")}
    kitap = next((k for k in kitaplar(istemci) if k["mevcut_adet"] > 1 and k["id"] not in aktifler), None)
    if kitap is None:
        pytest.skip("Uygun kitap bulunamadı")

    ilk = istemci.post("/api/oduncler", headers=h, json={"kitap_id": kitap["id"]})
    assert ilk.status_code in (200, 201), ilk.text
    try:
        ikinci = istemci.post("/api/oduncler", headers=h, json={"kitap_id": kitap["id"]})
        assert 400 <= ikinci.status_code < 500
    finally:
        istemci.put(f"/api/oduncler/{ilk.json()['id']}/iade", headers=h)  # temizlik


def test_stok_sifirsa_odunc_verilmez(istemci):
    h = giris(istemci, AHMET)
    kitap = next((k for k in kitaplar(istemci) if k["mevcut_adet"] == 0), None)
    if kitap is None:
        pytest.skip("Stoğu 0 olan kitap bulunamadı")
    r = istemci.post("/api/oduncler", headers=h, json={"kitap_id": kitap["id"]})
    assert 400 <= r.status_code < 500


def test_gecikmisi_olan_uye_odunc_alamaz(istemci):
    h = giris(istemci, AYSE)
    kitap = next((k for k in kitaplar(istemci) if k["mevcut_adet"] > 0), None)
    if kitap is None:
        pytest.skip("Müsait kitap yok")
    r = istemci.post("/api/oduncler", headers=h, json={"kitap_id": kitap["id"]})
    assert 400 <= r.status_code < 500


def test_gecikme_cezasi_raporda_gorunur(istemci):
    h = giris(istemci, ADMIN)
    r = istemci.get("/api/raporlar/gecikmeler", headers=h)
    assert r.status_code == 200
    assert len(liste(r.json())) > 0


def test_uye_yonetici_raporuna_erisemez(istemci):
    r = istemci.get("/api/raporlar/gecikmeler", headers=giris(istemci, AHMET))
    assert r.status_code in (401, 403)
