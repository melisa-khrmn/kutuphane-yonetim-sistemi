"""Üye, Ödünç, Rezervasyon ve Rapor şemaları."""
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.core.ayarlar import ayarlar
from app.models import Odunc, OduncDurumu, Rezervasyon, RezervasyonDurumu, Uye


# ---------- Üye ----------
class UyeGuncelle(BaseModel):
    ad: str | None = Field(default=None, min_length=2, max_length=50)
    soyad: str | None = Field(default=None, min_length=2, max_length=50)
    email: str | None = None
    ogrenci_no: str | None = Field(default=None, min_length=3, max_length=20)
    bolum: str | None = None
    telefon: str | None = None
    ceza_puani: int | None = Field(default=None, ge=0)


class AktiflikIstek(BaseModel):
    aktif_mi: bool


class UyeYanit(BaseModel):
    id: int
    ad: str
    soyad: str
    email: str
    ogrenci_no: str
    bolum: str
    telefon: str | None
    ceza_puani: int
    aktif_mi: bool
    kayit_tarihi: datetime | None
    aktif_odunc_sayisi: int
    gecikmis_var: bool
    toplam_ceza: float

    @classmethod
    def nesneden(cls, u: Uye) -> "UyeYanit":
        return cls(
            id=u.id, ad=u.ad, soyad=u.soyad, email=u.email, ogrenci_no=u.ogrenci_no, bolum=u.bolum,
            telefon=u.telefon, ceza_puani=u.ceza_puani, aktif_mi=u.aktif_mi, kayit_tarihi=u.kayit_tarihi,
            aktif_odunc_sayisi=u.aktif_odunc_sayisi(), gecikmis_var=u.gecikmis_odunc_var_mi(),
            toplam_ceza=u.toplam_ceza(),
        )


# ---------- Ödünç ----------
class OduncOlustur(BaseModel):
    kitap_id: int = Field(examples=[1])
    uye_id: int | None = Field(default=None, description="Sadece yönetici: başka üye adına ödünç verir.")


class OduncYanit(BaseModel):
    id: int
    uye_id: int
    uye_ad: str
    ogrenci_no: str
    kitap_id: int
    kitap_baslik: str
    alis_tarihi: date
    son_iade_tarihi: date
    iade_tarihi: date | None
    durum: OduncDurumu
    gecikme_gunu: int
    ceza_tutari: float
    uzatma_sayisi: int
    kalan_gun: int | None
    uzatilabilir: bool

    @classmethod
    def nesneden(cls, o: Odunc) -> "OduncYanit":
        aktif = not o.iade_edildi_mi()
        return cls(
            id=o.id, uye_id=o.uye_id, uye_ad=o.uye.tam_ad, ogrenci_no=o.uye.ogrenci_no,
            kitap_id=o.kitap_id, kitap_baslik=o.kitap.baslik,
            alis_tarihi=o.alis_tarihi, son_iade_tarihi=o.son_iade_tarihi, iade_tarihi=o.iade_tarihi,
            durum=o.durum, gecikme_gunu=o.gecikme_gunu, ceza_tutari=o.ceza_tutari,
            uzatma_sayisi=o.uzatma_sayisi,
            kalan_gun=o.kalan_gun() if aktif else None,
            uzatilabilir=aktif and not o.gecikmis_mi() and o.uzatma_sayisi < ayarlar.max_uzatma_sayisi,
        )


# ---------- Rezervasyon ----------
class RezervasyonOlustur(BaseModel):
    kitap_id: int = Field(examples=[1])
    uye_id: int | None = Field(default=None, description="Sadece yönetici: başka üye adına rezervasyon.")


class RezervasyonYanit(BaseModel):
    id: int
    uye_id: int
    uye_ad: str
    kitap_id: int
    kitap_baslik: str
    tarih: datetime
    durum: RezervasyonDurumu
    sira: int | None = None

    @classmethod
    def nesneden(cls, r: Rezervasyon, sira: int | None = None) -> "RezervasyonYanit":
        return cls(
            id=r.id, uye_id=r.uye_id, uye_ad=r.uye.tam_ad, kitap_id=r.kitap_id,
            kitap_baslik=r.kitap.baslik, tarih=r.tarih, durum=r.durum, sira=sira,
        )


class IadeYanit(BaseModel):
    mesaj: str
    odunc: OduncYanit
    ceza_tutari: float
    karsilanan_rezervasyon: RezervasyonYanit | None = None


class UyeDetayYanit(UyeYanit):
    oduncler: list[OduncYanit] = []
    rezervasyonlar: list[RezervasyonYanit] = []


# ---------- Rapor ----------
class OzetRapor(BaseModel):
    toplam_kitap: int
    toplam_kopya: int
    mevcut_kopya: int
    toplam_uye: int
    aktif_uye: int
    aktif_odunc: int
    geciken: int
    bekleyen_rezervasyon: int
    toplam_ceza: float


class StokSatiri(BaseModel):
    id: int
    baslik: str
    isbn: str
    raf_kodu: str | None
    toplam_adet: int
    mevcut_adet: int
    bekleyen_rezervasyon: int


class EnCokOkunanSatiri(BaseModel):
    id: int
    baslik: str
    yazarlar: str
    odunc_sayisi: int
