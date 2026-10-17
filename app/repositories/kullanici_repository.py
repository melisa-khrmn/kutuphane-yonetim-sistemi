"""Kullanıcı / Üye / Yönetici veri erişimi."""
from sqlalchemy import func, or_, select

from app.models import Kullanici, Uye, Yonetici
from app.repositories.temel_repository import TemelRepository


class KullaniciRepository(TemelRepository[Kullanici]):
    model = Kullanici

    def email_ile(self, email: str) -> Kullanici | None:
        return self.db.scalar(select(Kullanici).where(func.lower(Kullanici.email) == email.lower()))


class UyeRepository(TemelRepository[Uye]):
    model = Uye

    def ogrenci_no_ile(self, ogrenci_no: str) -> Uye | None:
        return self.db.scalar(select(Uye).where(Uye.ogrenci_no == ogrenci_no))

    def ara(self, arama: str | None = None, aktif_mi: bool | None = None) -> list[Uye]:
        sorgu = select(Uye)
        if arama:
            desen = f"%{arama}%"
            sorgu = sorgu.where(
                or_(Uye.ad.ilike(desen), Uye.soyad.ilike(desen), Uye.email.ilike(desen), Uye.ogrenci_no.ilike(desen))
            )
        if aktif_mi is not None:
            sorgu = sorgu.where(Uye.aktif_mi == aktif_mi)
        return list(self.db.scalars(sorgu.order_by(Uye.id)))


class YoneticiRepository(TemelRepository[Yonetici]):
    model = Yonetici
