"""Kitap, Yazar ve Kategori veri erişimi."""
from sqlalchemy import asc, desc, func, or_, select

from app.models import Kategori, Kitap, Yazar
from app.repositories.temel_repository import TemelRepository

SIRALANABILIR = {
    "baslik": Kitap.baslik,
    "yayin_yili": Kitap.yayin_yili,
    "mevcut_adet": Kitap.mevcut_adet,
    "id": Kitap.id,
}


class KitapRepository(TemelRepository[Kitap]):
    model = Kitap

    def isbn_ile(self, isbn: str) -> Kitap | None:
        return self.db.scalar(select(Kitap).where(Kitap.isbn == isbn))

    def ara(
        self,
        baslik: str | None = None,
        yazar: str | None = None,
        isbn: str | None = None,
        kategori_id: int | None = None,
        sadece_musait: bool = False,
        sayfa: int = 1,
        boyut: int = 12,
        sirala: str = "baslik",
        yon: str = "artan",
    ) -> tuple[list[Kitap], int]:
        sorgu = select(Kitap)
        if baslik:
            sorgu = sorgu.where(Kitap.baslik.ilike(f"%{baslik}%"))
        if isbn:
            sorgu = sorgu.where(Kitap.isbn.ilike(f"%{isbn}%"))
        if kategori_id:
            sorgu = sorgu.where(Kitap.kategori_id == kategori_id)
        if sadece_musait:
            sorgu = sorgu.where(Kitap.mevcut_adet > 0)
        if yazar:
            desen = f"%{yazar}%"
            sorgu = sorgu.where(
                Kitap.yazarlar.any(
                    or_(Yazar.ad.ilike(desen), Yazar.soyad.ilike(desen), (Yazar.ad + " " + Yazar.soyad).ilike(desen))
                )
            )
        toplam = self.db.scalar(select(func.count()).select_from(sorgu.subquery())) or 0
        kolon = SIRALANABILIR.get(sirala, Kitap.baslik)
        sorgu = sorgu.order_by(desc(kolon) if yon == "azalan" else asc(kolon), Kitap.id)
        sorgu = sorgu.offset((sayfa - 1) * boyut).limit(boyut)
        return list(self.db.scalars(sorgu)), toplam

    def az_stoklu(self, esik: int) -> list[Kitap]:
        return list(self.db.scalars(select(Kitap).where(Kitap.mevcut_adet <= esik).order_by(Kitap.mevcut_adet, Kitap.baslik)))

    def toplam_adet(self) -> int:
        return self.db.scalar(select(func.coalesce(func.sum(Kitap.toplam_adet), 0))) or 0


class YazarRepository(TemelRepository[Yazar]):
    model = Yazar

    def id_listesi_ile(self, idler: list[int]) -> list[Yazar]:
        if not idler:
            return []
        return list(self.db.scalars(select(Yazar).where(Yazar.id.in_(idler))))

    def ara(self, arama: str | None = None) -> list[Yazar]:
        sorgu = select(Yazar)
        if arama:
            desen = f"%{arama}%"
            sorgu = sorgu.where(or_(Yazar.ad.ilike(desen), Yazar.soyad.ilike(desen)))
        return list(self.db.scalars(sorgu.order_by(Yazar.soyad, Yazar.ad)))


class KategoriRepository(TemelRepository[Kategori]):
    model = Kategori

    def ad_ile(self, ad: str) -> Kategori | None:
        return self.db.scalar(select(Kategori).where(func.lower(Kategori.ad) == ad.lower()))

    def tumu(self) -> list[Kategori]:
        return list(self.db.scalars(select(Kategori).order_by(Kategori.ad)))
