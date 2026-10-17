"""Ortak CRUD işlemlerini sağlayan temel repository."""
from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.veritabani import Base

T = TypeVar("T", bound=Base)


class TemelRepository(Generic[T]):
    model: type[T]

    def __init__(self, db: Session):
        self.db = db

    def getir(self, id: int) -> T | None:
        return self.db.get(self.model, id)

    def tumu(self) -> list[T]:
        return list(self.db.scalars(select(self.model).order_by(self.model.id)))

    def sayi(self) -> int:
        return self.db.scalar(select(func.count()).select_from(self.model)) or 0

    def ekle(self, nesne: T) -> T:
        self.db.add(nesne)
        self.db.flush()
        return nesne

    def sil(self, nesne: T) -> None:
        self.db.delete(nesne)
        self.db.flush()

    def kaydet(self) -> None:
        """İşlemi kalıcı hale getirir (commit)."""
        self.db.commit()

    def geri_al(self) -> None:
        self.db.rollback()

    def yenile(self, nesne: T) -> T:
        self.db.refresh(nesne)
        return nesne
