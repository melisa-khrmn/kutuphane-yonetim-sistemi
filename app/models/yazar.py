"""Yazar sınıfı."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.veritabani import Base
from app.models.kitap import kitap_yazar

if TYPE_CHECKING:
    from app.models.kitap import Kitap


class Yazar(Base):
    __tablename__ = "yazarlar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ad: Mapped[str] = mapped_column(String(50))
    soyad: Mapped[str] = mapped_column(String(50))
    biyografi: Mapped[str | None] = mapped_column(Text, nullable=True)
    dogum_yili: Mapped[int | None] = mapped_column(Integer, nullable=True)

    kitaplar: Mapped[list[Kitap]] = relationship(secondary=kitap_yazar, back_populates="yazarlar")

    @property
    def tam_ad(self) -> str:
        return f"{self.ad} {self.soyad}"

    def kitabi_var_mi(self) -> bool:
        return len(self.kitaplar) > 0
