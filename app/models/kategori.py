"""Kategori sınıfı."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.veritabani import Base

if TYPE_CHECKING:
    from app.models.kitap import Kitap


class Kategori(Base):
    __tablename__ = "kategoriler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ad: Mapped[str] = mapped_column(String(60), unique=True)

    kitaplar: Mapped[list[Kitap]] = relationship(back_populates="kategori")

    def kitap_sayisi(self) -> int:
        return len(self.kitaplar)
