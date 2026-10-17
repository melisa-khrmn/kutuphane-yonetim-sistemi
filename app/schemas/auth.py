"""Kimlik doğrulama ve kullanıcı şemaları."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Kullanici, Rol, Uye, Yonetici


class KayitIstek(BaseModel):
    ad: str = Field(min_length=2, max_length=50, examples=["Ahmet"])
    soyad: str = Field(min_length=2, max_length=50, examples=["Yılmaz"])
    email: EmailStr = Field(examples=["ahmet@ogr.edu.tr"])
    sifre: str = Field(min_length=6, max_length=64, examples=["Sifre123!"])
    ogrenci_no: str = Field(min_length=3, max_length=20, examples=["20230001"])
    bolum: str = Field(min_length=2, max_length=100, examples=["Bilgisayar Mühendisliği"])
    telefon: str | None = Field(default=None, max_length=20, examples=["05551112233"])


class GirisIstek(BaseModel):
    email: EmailStr = Field(examples=["admin@kutuphane.com"])
    sifre: str = Field(examples=["Admin123!"])


class KullaniciYanit(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ad: str
    soyad: str
    email: str
    rol: Rol
    aktif_mi: bool
    kayit_tarihi: datetime | None = None
    ogrenci_no: str | None = None
    bolum: str | None = None
    telefon: str | None = None
    ceza_puani: int | None = None
    sicil_no: str | None = None

    @classmethod
    def nesneden(cls, k: Kullanici) -> "KullaniciYanit":
        veri = {
            "id": k.id, "ad": k.ad, "soyad": k.soyad, "email": k.email, "rol": k.rol,
            "aktif_mi": k.aktif_mi, "kayit_tarihi": k.kayit_tarihi,
        }
        if isinstance(k, Uye):
            veri |= {"ogrenci_no": k.ogrenci_no, "bolum": k.bolum, "telefon": k.telefon, "ceza_puani": k.ceza_puani}
        if isinstance(k, Yonetici):
            veri["sicil_no"] = k.sicil_no
        return cls(**veri)


class TokenYanit(BaseModel):
    access_token: str
    token_type: str = "bearer"
    kullanici: KullaniciYanit
