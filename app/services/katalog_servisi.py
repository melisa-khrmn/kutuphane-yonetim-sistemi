"""Kitap, Yazar ve Kategori iş mantığı."""
import math

from sqlalchemy.orm import Session

from app.core.istisnalar import BulunamadiHatasi, CakismaHatasi, IsKuraliHatasi
from app.models import Kategori, Kitap, Yazar
from app.repositories import KategoriRepository, KitapRepository, YazarRepository
from app.schemas import (
    KategoriGuncelle, KategoriOlustur, KitapGuncelle, KitapOlustur, YazarGuncelle, YazarOlustur,
)


class KitapServisi:
    def __init__(self, db: Session):
        self.repo = KitapRepository(db)
        self.yazar_repo = YazarRepository(db)
        self.kategori_repo = KategoriRepository(db)

    def ara(self, **filtreler) -> tuple[list[Kitap], int, int]:
        kitaplar, toplam = self.repo.ara(**filtreler)
        toplam_sayfa = max(1, math.ceil(toplam / filtreler.get("boyut", 12)))
        return kitaplar, toplam, toplam_sayfa

    def getir(self, kitap_id: int) -> Kitap:
        kitap = self.repo.getir(kitap_id)
        if not kitap:
            raise BulunamadiHatasi("Kitap bulunamadı.")
        return kitap

    def _yazarlari_coz(self, idler: list[int]) -> list[Yazar]:
        yazarlar = self.yazar_repo.id_listesi_ile(idler)
        if len(yazarlar) != len(set(idler)):
            raise BulunamadiHatasi("Seçilen yazarlardan biri bulunamadı.")
        return yazarlar

    def _kategori_kontrol(self, kategori_id: int | None) -> None:
        if kategori_id is not None and not self.kategori_repo.getir(kategori_id):
            raise BulunamadiHatasi("Kategori bulunamadı.")

    def olustur(self, veri: KitapOlustur) -> Kitap:
        if self.repo.isbn_ile(veri.isbn):
            raise CakismaHatasi("Bu ISBN ile kayıtlı bir kitap zaten var.")
        self._kategori_kontrol(veri.kategori_id)
        alanlar = veri.model_dump(exclude={"yazar_idleri"})
        kitap = Kitap(**alanlar, mevcut_adet=veri.toplam_adet)
        kitap.yazarlar = self._yazarlari_coz(veri.yazar_idleri)
        self.repo.ekle(kitap)
        self.repo.kaydet()
        return kitap

    def guncelle(self, kitap_id: int, veri: KitapGuncelle) -> Kitap:
        kitap = self.getir(kitap_id)
        degisen = veri.model_dump(exclude_unset=True)
        if "isbn" in degisen and degisen["isbn"] != kitap.isbn and self.repo.isbn_ile(degisen["isbn"]):
            raise CakismaHatasi("Bu ISBN ile kayıtlı başka bir kitap var.")
        if "kategori_id" in degisen:
            self._kategori_kontrol(degisen["kategori_id"])
        if "yazar_idleri" in degisen:
            kitap.yazarlar = self._yazarlari_coz(degisen.pop("yazar_idleri") or [])
        if "toplam_adet" in degisen:
            yeni_toplam = degisen.pop("toplam_adet")
            oduncte = kitap.toplam_adet - kitap.mevcut_adet
            if yeni_toplam < oduncte:
                raise IsKuraliHatasi(f"Toplam adet, ödünçteki adetten ({oduncte}) az olamaz.")
            kitap.toplam_adet = yeni_toplam
            kitap.mevcut_adet = yeni_toplam - oduncte
        for alan, deger in degisen.items():
            setattr(kitap, alan, deger)
        self.repo.kaydet()
        return kitap

    def sil(self, kitap_id: int) -> None:
        kitap = self.getir(kitap_id)
        if kitap.aktif_odunc_var_mi():
            raise IsKuraliHatasi("Bu kitabın aktif ödüncü var; silinemez.")
        self.repo.sil(kitap)
        self.repo.kaydet()


class YazarServisi:
    def __init__(self, db: Session):
        self.repo = YazarRepository(db)

    def listele(self, arama: str | None = None) -> list[Yazar]:
        return self.repo.ara(arama)

    def getir(self, yazar_id: int) -> Yazar:
        yazar = self.repo.getir(yazar_id)
        if not yazar:
            raise BulunamadiHatasi("Yazar bulunamadı.")
        return yazar

    def olustur(self, veri: YazarOlustur) -> Yazar:
        yazar = self.repo.ekle(Yazar(**veri.model_dump()))
        self.repo.kaydet()
        return yazar

    def guncelle(self, yazar_id: int, veri: YazarGuncelle) -> Yazar:
        yazar = self.getir(yazar_id)
        for alan, deger in veri.model_dump(exclude_unset=True).items():
            setattr(yazar, alan, deger)
        self.repo.kaydet()
        return yazar

    def sil(self, yazar_id: int) -> None:
        yazar = self.getir(yazar_id)
        if yazar.kitabi_var_mi():
            raise IsKuraliHatasi("Yazarın kayıtlı kitapları var; önce kitapları silin veya yazarı kitaplardan çıkarın.")
        self.repo.sil(yazar)
        self.repo.kaydet()


class KategoriServisi:
    def __init__(self, db: Session):
        self.repo = KategoriRepository(db)

    def listele(self) -> list[Kategori]:
        return self.repo.tumu()

    def getir(self, kategori_id: int) -> Kategori:
        kategori = self.repo.getir(kategori_id)
        if not kategori:
            raise BulunamadiHatasi("Kategori bulunamadı.")
        return kategori

    def olustur(self, veri: KategoriOlustur) -> Kategori:
        if self.repo.ad_ile(veri.ad):
            raise CakismaHatasi("Bu adla bir kategori zaten var.")
        kategori = self.repo.ekle(Kategori(ad=veri.ad.strip()))
        self.repo.kaydet()
        return kategori

    def guncelle(self, kategori_id: int, veri: KategoriGuncelle) -> Kategori:
        kategori = self.getir(kategori_id)
        mevcut = self.repo.ad_ile(veri.ad)
        if mevcut and mevcut.id != kategori_id:
            raise CakismaHatasi("Bu adla bir kategori zaten var.")
        kategori.ad = veri.ad.strip()
        self.repo.kaydet()
        return kategori

    def sil(self, kategori_id: int) -> None:
        kategori = self.getir(kategori_id)
        if kategori.kitap_sayisi() > 0:
            raise IsKuraliHatasi("Bu kategoride kitaplar var; önce kitapları başka kategoriye taşıyın.")
        self.repo.sil(kategori)
        self.repo.kaydet()
