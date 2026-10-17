"""Veritabanı bağlantısı, oturum ve Base sınıfı."""
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.ayarlar import ayarlar


class Base(DeclarativeBase):
    """Tüm ORM modellerinin temel sınıfı."""


def motor_olustur(url: str):
    baglanti_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    motor = create_engine(url, connect_args=baglanti_args)
    if url.startswith("sqlite"):
        # SQLite'ta yabancı anahtar kısıtlarını aç
        @event.listens_for(motor, "connect")
        def _fk_ac(dbapi_conn, _):
            imlec = dbapi_conn.cursor()
            imlec.execute("PRAGMA foreign_keys=ON")
            imlec.close()
    return motor


motor = motor_olustur(ayarlar.veritabani_url)
OturumYerel = sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)


def oturum_al() -> Generator[Session, None, None]:
    """İstek başına veritabanı oturumu sağlar."""
    db = OturumYerel()
    try:
        yield db
    finally:
        db.close()
