"""Kitap sınıfı ve Kitap–Yazar ara tablosu."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.istisnalar import IsKuraliHatasi
from app.core.veritabani import Base
from app.models.enumlar import OduncDurumu, RezervasyonDurumu

if TYPE_CHECKING:
    from app.models.kategori import Kategori
    from app.models.odunc import Odunc
    from app.models.rezervasyon import Rezervasyon
    from app.models.yazar import Yazar

# Çoktan çoğa ara tablo
kitap_yazar = Table(
    "kitap_yazar",
    Base.metadata,
    Column("kitap_id", ForeignKey("kitaplar.id", ondelete="CASCADE"), primary_key=True),
    Column("yazar_id", ForeignKey("yazarlar.id", ondelete="RESTRICT"), primary_key=True),
)


class Kitap(Base):
    __tablename__ = "kitaplar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    baslik: Mapped[str] = mapped_column(String(200), index=True)
    isbn: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    yayin_yili: Mapped[int | None] = mapped_column(Integer, nullable=True)
    yayinevi: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sayfa_sayisi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dil: Mapped[str] = mapped_column(String(30), default="Türkçe")
    raf_kodu: Mapped[str | None] = mapped_column(String(20), nullable=True)
    toplam_adet: Mapped[int] = mapped_column(Integer, default=1)
    mevcut_adet: Mapped[int] = mapped_column(Integer, default=1)
    kapak_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ozet: Mapped[str | None] = mapped_column(Text, nullable=True)
    kategori_id: Mapped[int | None] = mapped_column(ForeignKey("kategoriler.id", ondelete="SET NULL"), nullable=True)

    kategori: Mapped[Kategori | None] = relationship(back_populates="kitaplar")
    yazarlar: Mapped[list[Yazar]] = relationship(secondary=kitap_yazar, back_populates="kitaplar")
    oduncler: Mapped[list[Odunc]] = relationship(back_populates="kitap", cascade="all, delete-orphan")
    rezervasyonlar: Mapped[list[Rezervasyon]] = relationship(
        back_populates="kitap", cascade="all, delete-orphan", order_by="Rezervasyon.tarih"
    )

    def musait_mi(self) -> bool:
        return self.mevcut_adet > 0

    def stok_azalt(self) -> None:
        if self.mevcut_adet <= 0:
            raise IsKuraliHatasi("Kitabın mevcut adedi yok.")
        self.mevcut_adet -= 1

    def stok_artir(self) -> None:
        if self.mevcut_adet < self.toplam_adet:
            self.mevcut_adet += 1

    def aktif_odunc_var_mi(self) -> bool:
        return any(o.durum != OduncDurumu.IADE_EDILDI for o in self.oduncler)

    def siradaki_rezervasyon(self) -> Rezervasyon | None:
        bekleyenler = [r for r in self.rezervasyonlar if r.durum == RezervasyonDurumu.BEKLIYOR]
        return min(bekleyenler, key=lambda r: r.tarih) if bekleyenler else None

    @property
    def yazar_adlari(self) -> str:
        return ", ".join(y.tam_ad for y in self.yazarlar)
