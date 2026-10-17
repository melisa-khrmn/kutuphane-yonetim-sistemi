"""Üye yönetimi iş mantığı."""
from sqlalchemy.orm import Session

from app.core.istisnalar import BulunamadiHatasi, CakismaHatasi, IsKuraliHatasi
from app.models import Uye
from app.repositories import KullaniciRepository, UyeRepository
from app.schemas import UyeGuncelle


class UyeServisi:
    def __init__(self, db: Session):
        self.repo = UyeRepository(db)
        self.kullanici_repo = KullaniciRepository(db)

    def listele(self, arama: str | None = None, aktif_mi: bool | None = None) -> list[Uye]:
        return self.repo.ara(arama, aktif_mi)

    def getir(self, uye_id: int) -> Uye:
        uye = self.repo.getir(uye_id)
        if not uye:
            raise BulunamadiHatasi("Üye bulunamadı.")
        return uye

    def guncelle(self, uye_id: int, veri: UyeGuncelle) -> Uye:
        uye = self.getir(uye_id)
        degisen = veri.model_dump(exclude_unset=True)
        if "email" in degisen:
            mevcut = self.kullanici_repo.email_ile(degisen["email"])
            if mevcut and mevcut.id != uye_id:
                raise CakismaHatasi("Bu e-posta başka bir kullanıcıya ait.")
            degisen["email"] = degisen["email"].lower()
        if "ogrenci_no" in degisen:
            mevcut = self.repo.ogrenci_no_ile(degisen["ogrenci_no"])
            if mevcut and mevcut.id != uye_id:
                raise CakismaHatasi("Bu öğrenci numarası başka bir üyeye ait.")
        for alan, deger in degisen.items():
            setattr(uye, alan, deger)
        self.repo.kaydet()
        return uye

    def aktiflik_degistir(self, uye_id: int, aktif_mi: bool) -> Uye:
        uye = self.getir(uye_id)
        uye.aktif_mi = aktif_mi
        self.repo.kaydet()
        return uye

    def sil(self, uye_id: int) -> None:
        uye = self.getir(uye_id)
        if uye.aktif_odunc_sayisi() > 0:
            raise IsKuraliHatasi("Üyenin iade etmediği kitaplar var; silinemez.")
        self.repo.sil(uye)
        self.repo.kaydet()
