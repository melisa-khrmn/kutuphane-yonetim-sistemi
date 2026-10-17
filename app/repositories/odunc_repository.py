"""Ödünç ve Rezervasyon veri erişimi."""
from sqlalchemy import desc, func, select

from app.models import Kitap, Odunc, OduncDurumu, Rezervasyon, RezervasyonDurumu
from app.repositories.temel_repository import TemelRepository

AKTIF_DURUMLAR = (OduncDurumu.AKTIF, OduncDurumu.GECIKMIS)


class OduncRepository(TemelRepository[Odunc]):
    model = Odunc

    def aktif_odunc_var_mi(self, uye_id: int, kitap_id: int) -> bool:
        sorgu = select(Odunc.id).where(
            Odunc.uye_id == uye_id, Odunc.kitap_id == kitap_id, Odunc.durum.in_(AKTIF_DURUMLAR)
        )
        return self.db.scalar(sorgu) is not None

    def iade_edilmemisler(self) -> list[Odunc]:
        return list(self.db.scalars(select(Odunc).where(Odunc.durum.in_(AKTIF_DURUMLAR))))

    def gecikmisler(self) -> list[Odunc]:
        sorgu = select(Odunc).where(Odunc.durum == OduncDurumu.GECIKMIS).order_by(Odunc.son_iade_tarihi)
        return list(self.db.scalars(sorgu))

    def uyenin(self, uye_id: int) -> list[Odunc]:
        sorgu = select(Odunc).where(Odunc.uye_id == uye_id).order_by(desc(Odunc.alis_tarihi), desc(Odunc.id))
        return list(self.db.scalars(sorgu))

    def filtrele(
        self, durum: OduncDurumu | None = None, uye_id: int | None = None, kitap_id: int | None = None
    ) -> list[Odunc]:
        sorgu = select(Odunc)
        if durum:
            sorgu = sorgu.where(Odunc.durum == durum)
        if uye_id:
            sorgu = sorgu.where(Odunc.uye_id == uye_id)
        if kitap_id:
            sorgu = sorgu.where(Odunc.kitap_id == kitap_id)
        return list(self.db.scalars(sorgu.order_by(desc(Odunc.alis_tarihi), desc(Odunc.id))))

    def durum_sayisi(self, *durumlar: OduncDurumu) -> int:
        return self.db.scalar(select(func.count(Odunc.id)).where(Odunc.durum.in_(durumlar))) or 0

    def en_cok_okunanlar(self, limit: int = 10) -> list[tuple[Kitap, int]]:
        sayi = func.count(Odunc.id).label("sayi")
        sorgu = (
            select(Kitap, sayi)
            .join(Odunc, Odunc.kitap_id == Kitap.id)
            .group_by(Kitap.id)
            .order_by(desc(sayi), Kitap.baslik)
            .limit(limit)
        )
        return [(k, s) for k, s in self.db.execute(sorgu).all()]

    def toplam_ceza(self) -> float:
        return float(self.db.scalar(select(func.coalesce(func.sum(Odunc.ceza_tutari), 0.0))) or 0.0)


class RezervasyonRepository(TemelRepository[Rezervasyon]):
    model = Rezervasyon

    def bekleyen_var_mi(self, uye_id: int, kitap_id: int) -> Rezervasyon | None:
        return self.db.scalar(
            select(Rezervasyon).where(
                Rezervasyon.uye_id == uye_id,
                Rezervasyon.kitap_id == kitap_id,
                Rezervasyon.durum == RezervasyonDurumu.BEKLIYOR,
            )
        )

    def uyenin(self, uye_id: int) -> list[Rezervasyon]:
        sorgu = select(Rezervasyon).where(Rezervasyon.uye_id == uye_id).order_by(desc(Rezervasyon.tarih))
        return list(self.db.scalars(sorgu))

    def siradaki(self, kitap_id: int) -> Rezervasyon | None:
        return self.db.scalar(
            select(Rezervasyon)
            .where(Rezervasyon.kitap_id == kitap_id, Rezervasyon.durum == RezervasyonDurumu.BEKLIYOR)
            .order_by(Rezervasyon.tarih, Rezervasyon.id)
        )

    def sira_numarasi(self, rezervasyon: Rezervasyon) -> int:
        return (
            self.db.scalar(
                select(func.count(Rezervasyon.id)).where(
                    Rezervasyon.kitap_id == rezervasyon.kitap_id,
                    Rezervasyon.durum == RezervasyonDurumu.BEKLIYOR,
                    Rezervasyon.tarih <= rezervasyon.tarih,
                )
            )
            or 0
        )

    def tumu_filtreli(self, durum: RezervasyonDurumu | None = None) -> list[Rezervasyon]:
        sorgu = select(Rezervasyon)
        if durum:
            sorgu = sorgu.where(Rezervasyon.durum == durum)
        return list(self.db.scalars(sorgu.order_by(desc(Rezervasyon.tarih))))
