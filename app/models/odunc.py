"""Odunc (ödünç) sınıfı."""
from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ayarlar import ayarlar
from app.core.istisnalar import IsKuraliHatasi
from app.core.veritabani import Base
from app.models.enumlar import OduncDurumu

if TYPE_CHECKING:
    from app.models.kitap import Kitap
    from app.models.kullanici import Uye


class Odunc(Base):
    __tablename__ = "oduncler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uye_id: Mapped[int] = mapped_column(ForeignKey("uyeler.id", ondelete="CASCADE"), index=True)
    kitap_id: Mapped[int] = mapped_column(ForeignKey("kitaplar.id", ondelete="CASCADE"), index=True)
    alis_tarihi: Mapped[date] = mapped_column(Date)
    son_iade_tarihi: Mapped[date] = mapped_column(Date)
    iade_tarihi: Mapped[date | None] = mapped_column(Date, nullable=True)
    durum: Mapped[OduncDurumu] = mapped_column(
        Enum(OduncDurumu, native_enum=False, length=20), default=OduncDurumu.AKTIF, index=True
    )
    gecikme_gunu: Mapped[int] = mapped_column(Integer, default=0)
    ceza_tutari: Mapped[float] = mapped_column(Float, default=0.0)
    uzatma_sayisi: Mapped[int] = mapped_column(Integer, default=0)

    uye: Mapped[Uye] = relationship(back_populates="oduncler")
    kitap: Mapped[Kitap] = relationship(back_populates="oduncler")

    # --- Domain metotları ---
    def iade_edildi_mi(self) -> bool:
        return self.durum == OduncDurumu.IADE_EDILDI

    def gecikme_gunu_hesapla(self, bugun: date | None = None) -> int:
        referans = self.iade_tarihi or bugun or date.today()
        return max(0, (referans - self.son_iade_tarihi).days)

    def ceza_hesapla(self, bugun: date | None = None) -> float:
        return round(self.gecikme_gunu_hesapla(bugun) * ayarlar.gunluk_ceza_tl, 2)

    def gecikmis_mi(self, bugun: date | None = None) -> bool:
        return not self.iade_edildi_mi() and self.gecikme_gunu_hesapla(bugun) > 0

    def kalan_gun(self, bugun: date | None = None) -> int:
        return (self.son_iade_tarihi - (bugun or date.today())).days

    def durumu_guncelle(self, bugun: date | None = None) -> bool:
        """Gecikmeyi işaretler, anlık cezayı yansıtır. Değişiklik olduysa True döner."""
        if self.iade_edildi_mi():
            return False
        gun = self.gecikme_gunu_hesapla(bugun)
        yeni_durum = OduncDurumu.GECIKMIS if gun > 0 else OduncDurumu.AKTIF
        yeni_ceza = round(gun * ayarlar.gunluk_ceza_tl, 2)
        degisti = (self.durum, self.gecikme_gunu, self.ceza_tutari) != (yeni_durum, gun, yeni_ceza)
        self.durum, self.gecikme_gunu, self.ceza_tutari = yeni_durum, gun, yeni_ceza
        return degisti

    def uzat(self, bugun: date | None = None) -> None:
        if self.iade_edildi_mi():
            raise IsKuraliHatasi("İade edilmiş ödünç uzatılamaz.")
        if self.gecikmis_mi(bugun):
            raise IsKuraliHatasi("Gecikmiş ödünç uzatılamaz; lütfen kitabı iade edin.")
        if self.uzatma_sayisi >= ayarlar.max_uzatma_sayisi:
            raise IsKuraliHatasi(f"Bir ödünç en fazla {ayarlar.max_uzatma_sayisi} kez uzatılabilir.")
        self.son_iade_tarihi += timedelta(days=ayarlar.uzatma_suresi_gun)
        self.uzatma_sayisi += 1

    def iade_et(self, bugun: date | None = None) -> float:
        """Kitabı iade eder, gecikme cezasını hesaplar ve döndürür."""
        if self.iade_edildi_mi():
            raise IsKuraliHatasi("Bu ödünç zaten iade edilmiş.")
        self.iade_tarihi = bugun or date.today()
        self.gecikme_gunu = self.gecikme_gunu_hesapla()
        self.ceza_tutari = round(self.gecikme_gunu * ayarlar.gunluk_ceza_tl, 2)
        self.durum = OduncDurumu.IADE_EDILDI
        return self.ceza_tutari
