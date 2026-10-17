"""Şifre hash ve JWT işlemleri."""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.ayarlar import ayarlar

_sifre_baglami = CryptContext(schemes=["bcrypt"], deprecated="auto")


def sifre_hashle(sifre: str) -> str:
    return _sifre_baglami.hash(sifre)


def sifre_dogrula(sifre: str, sifre_hash: str) -> bool:
    try:
        return _sifre_baglami.verify(sifre, sifre_hash)
    except ValueError:
        return False


def token_olustur(kullanici_id: int, rol: str) -> str:
    bitis = datetime.now(timezone.utc) + timedelta(minutes=ayarlar.token_sure_dakika)
    veri = {"sub": str(kullanici_id), "rol": rol, "exp": bitis}
    return jwt.encode(veri, ayarlar.gizli_anahtar, algorithm=ayarlar.jwt_algoritma)


def token_coz(token: str) -> dict | None:
    try:
        return jwt.decode(token, ayarlar.gizli_anahtar, algorithms=[ayarlar.jwt_algoritma])
    except JWTError:
        return None
