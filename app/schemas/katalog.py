"""Kitap, Yazar ve Kategori şemaları."""
from pydantic import BaseModel, ConfigDict, Field

from app.models import Kategori, Kitap, Yazar


# ---------- Kategori ----------
class KategoriOlustur(BaseModel):
    ad: str = Field(min_length=2, max_length=60, examples=["Bilim Kurgu"])


class KategoriGuncelle(KategoriOlustur):
    pass


class KategoriKisa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ad: str


class KategoriYanit(KategoriKisa):
    kitap_sayisi: int = 0

    @classmethod
    def nesneden(cls, k: Kategori) -> "KategoriYanit":
        return cls(id=k.id, ad=k.ad, kitap_sayisi=k.kitap_sayisi())


# ---------- Yazar ----------
class YazarOlustur(BaseModel):
    ad: str = Field(min_length=1, max_length=50, examples=["Orhan"])
    soyad: str = Field(min_length=1, max_length=50, examples=["Pamuk"])
    biyografi: str | None = Field(default=None, examples=["Nobel ödüllü Türk yazar."])
    dogum_yili: int | None = Field(default=None, ge=0, le=2100, examples=[1952])


class YazarGuncelle(BaseModel):
    ad: str | None = Field(default=None, min_length=1, max_length=50)
    soyad: str | None = Field(default=None, min_length=1, max_length=50)
    biyografi: str | None = None
    dogum_yili: int | None = Field(default=None, ge=0, le=2100)


class YazarKisa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ad: str
    soyad: str


class KitapKisa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    baslik: str
    isbn: str
    mevcut_adet: int
    kapak_url: str | None = None


class YazarYanit(YazarKisa):
    biyografi: str | None = None
    dogum_yili: int | None = None
    kitap_sayisi: int = 0
    kitaplar: list[KitapKisa] = []

    @classmethod
    def nesneden(cls, y: Yazar, kitaplarla: bool = False) -> "YazarYanit":
        return cls(
            id=y.id, ad=y.ad, soyad=y.soyad, biyografi=y.biyografi, dogum_yili=y.dogum_yili,
            kitap_sayisi=len(y.kitaplar),
            kitaplar=[KitapKisa.model_validate(k) for k in y.kitaplar] if kitaplarla else [],
        )


# ---------- Kitap ----------
class KitapTemel(BaseModel):
    baslik: str = Field(min_length=1, max_length=200, examples=["Kürk Mantolu Madonna"])
    isbn: str = Field(min_length=10, max_length=20, examples=["9789753638029"])
    yayin_yili: int | None = Field(default=None, ge=0, le=2100, examples=[1943])
    yayinevi: str | None = Field(default=None, max_length=100, examples=["Yapı Kredi Yayınları"])
    sayfa_sayisi: int | None = Field(default=None, ge=1, examples=[160])
    dil: str = Field(default="Türkçe", max_length=30)
    raf_kodu: str | None = Field(default=None, max_length=20, examples=["TR-ROM-01"])
    toplam_adet: int = Field(default=1, ge=1, le=1000)
    kapak_url: str | None = Field(default=None, max_length=500)
    ozet: str | None = None
    kategori_id: int | None = None


class KitapOlustur(KitapTemel):
    yazar_idleri: list[int] = Field(default_factory=list, examples=[[1]])


class KitapGuncelle(BaseModel):
    baslik: str | None = Field(default=None, min_length=1, max_length=200)
    isbn: str | None = Field(default=None, min_length=10, max_length=20)
    yayin_yili: int | None = Field(default=None, ge=0, le=2100)
    yayinevi: str | None = None
    sayfa_sayisi: int | None = Field(default=None, ge=1)
    dil: str | None = None
    raf_kodu: str | None = None
    toplam_adet: int | None = Field(default=None, ge=1, le=1000)
    kapak_url: str | None = None
    ozet: str | None = None
    kategori_id: int | None = None
    yazar_idleri: list[int] | None = None


class KitapYanit(KitapTemel):
    id: int
    mevcut_adet: int
    musait: bool
    kategori: KategoriKisa | None = None
    yazarlar: list[YazarKisa] = []
    bekleyen_rezervasyon: int = 0

    @classmethod
    def nesneden(cls, k: Kitap) -> "KitapYanit":
        return cls(
            id=k.id, baslik=k.baslik, isbn=k.isbn, yayin_yili=k.yayin_yili, yayinevi=k.yayinevi,
            sayfa_sayisi=k.sayfa_sayisi, dil=k.dil, raf_kodu=k.raf_kodu, toplam_adet=k.toplam_adet,
            mevcut_adet=k.mevcut_adet, kapak_url=k.kapak_url, ozet=k.ozet, kategori_id=k.kategori_id,
            musait=k.musait_mi(),
            kategori=KategoriKisa.model_validate(k.kategori) if k.kategori else None,
            yazarlar=[YazarKisa.model_validate(y) for y in k.yazarlar],
            bekleyen_rezervasyon=sum(1 for r in k.rezervasyonlar if r.bekliyor_mu()),
        )


class KitapListeYanit(BaseModel):
    kayitlar: list[KitapYanit]
    toplam: int
    sayfa: int
    boyut: int
    toplam_sayfa: int
