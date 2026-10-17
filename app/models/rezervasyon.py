"""Rezervasyon sınıfı."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.istisnalar import IsKuraliHatasi
from app.core.veritabani import Base
from app.models.enumlar import RezervasyonDurumu

if TYPE_CHECKING:
    from app.models.kitap import Kitap
    from app.models.kullanici import Uye


class Rezervasyon(Base):
    __tablename__ = "rezervasyonlar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uye_id: Mapped[int] = mapped_column(ForeignKey("uyeler.id", ondelete="CASCADE"), index=True)
    kitap_id: Mapped[int] = mapped_column(ForeignKey("kitaplar.id", ondelete="CASCADE"), index=True)
    tarih: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    durum: Mapped[RezervasyonDurumu] = mapped_column(
        Enum(RezervasyonDurumu, native_enum=False, length=20), default=RezervasyonDurumu.BEKLIYOR
    )

    uye: Mapped[Uye] = relationship(back_populates="rezervasyonlar")
    kitap: Mapped[Kitap] = relationship(back_populates="rezervasyonlar")

    def bekliyor_mu(self) -> bool:
        return self.durum == RezervasyonDurumu.BEKLIYOR

    def karsila(self) -> None:
        if not self.bekliyor_mu():
            raise IsKuraliHatasi("Sadece bekleyen rezervasyon karşılanabilir.")
        self.durum = RezervasyonDurumu.KARSILANDI

    def iptal_et(self) -> None:
        if not self.bekliyor_mu():
            raise IsKuraliHatasi("Sadece bekleyen rezervasyon iptal edilebilir.")
        self.durum = RezervasyonDurumu.IPTAL
