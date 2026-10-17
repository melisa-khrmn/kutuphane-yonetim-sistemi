"""Kullanici, Uye ve Yonetici sınıfları (joined-table inheritance)."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ayarlar import ayarlar
from app.core.veritabani import Base
from app.models.enumlar import OduncDurumu, RezervasyonDurumu, Rol

if TYPE_CHECKING:
    from app.models.odunc import Odunc
    from app.models.rezervasyon import Rezervasyon


class Kullanici(Base):
    __tablename__ = "kullanicilar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ad: Mapped[str] = mapped_column(String(50))
    soyad: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    sifre_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[Rol] = mapped_column(Enum(Rol, native_enum=False, length=20))
    aktif_mi: Mapped[bool] = mapped_column(Boolean, default=True)
    kayit_tarihi: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __mapper_args__ = {"polymorphic_on": "rol"}

    @property
    def tam_ad(self) -> str:
        return f"{self.ad} {self.soyad}"

    def yonetici_mi(self) -> bool:
        return self.rol == Rol.YONETICI


class Uye(Kullanici):
    __tablename__ = "uyeler"

    id: Mapped[int] = mapped_column(ForeignKey("kullanicilar.id", ondelete="CASCADE"), primary_key=True)
    ogrenci_no: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    bolum: Mapped[str] = mapped_column(String(100))
    telefon: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ceza_puani: Mapped[int] = mapped_column(Integer, default=0)

    oduncler: Mapped[list[Odunc]] = relationship(back_populates="uye", cascade="all, delete-orphan")
    rezervasyonlar: Mapped[list[Rezervasyon]] = relationship(back_populates="uye", cascade="all, delete-orphan")

    __mapper_args__ = {"polymorphic_identity": Rol.UYE}

    def aktif_oduncler(self) -> list[Odunc]:
        """İade edilmemiş (AKTIF veya GECIKMIS) ödünçler."""
        return [o for o in self.oduncler if o.durum != OduncDurumu.IADE_EDILDI]

    def aktif_odunc_sayisi(self) -> int:
        return len(self.aktif_oduncler())

    def gecikmis_odunc_var_mi(self) -> bool:
        return any(o.gecikmis_mi() for o in self.aktif_oduncler())

    def odunc_alabilir_mi(self) -> bool:
        return (
            self.aktif_mi
            and self.aktif_odunc_sayisi() < ayarlar.max_aktif_odunc
            and not self.gecikmis_odunc_var_mi()
        )

    def bekleyen_rezervasyonlar(self) -> list[Rezervasyon]:
        return [r for r in self.rezervasyonlar if r.durum == RezervasyonDurumu.BEKLIYOR]

    def toplam_ceza(self) -> float:
        return round(sum(o.ceza_tutari for o in self.oduncler), 2)


class Yonetici(Kullanici):
    __tablename__ = "yoneticiler"

    id: Mapped[int] = mapped_column(ForeignKey("kullanicilar.id", ondelete="CASCADE"), primary_key=True)
    sicil_no: Mapped[str] = mapped_column(String(20), unique=True)

    __mapper_args__ = {"polymorphic_identity": Rol.YONETICI}
