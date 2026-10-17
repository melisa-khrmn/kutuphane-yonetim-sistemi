"""Şema katmanı: Pydantic istek/yanıt modelleri."""
from app.schemas.auth import GirisIstek, KayitIstek, KullaniciYanit, TokenYanit
from app.schemas.islem import (
    AktiflikIstek, EnCokOkunanSatiri, IadeYanit, OduncOlustur, OduncYanit, OzetRapor,
    RezervasyonOlustur, RezervasyonYanit, StokSatiri, UyeDetayYanit, UyeGuncelle, UyeYanit,
)
from app.schemas.katalog import (
    KategoriGuncelle, KategoriOlustur, KategoriYanit, KitapGuncelle, KitapListeYanit, KitapOlustur,
    KitapYanit, YazarGuncelle, YazarOlustur, YazarYanit,
)


from pydantic import BaseModel


class MesajYanit(BaseModel):
    mesaj: str
