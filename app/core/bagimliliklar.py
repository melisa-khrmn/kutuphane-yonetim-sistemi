"""FastAPI bağımlılıkları: oturum, aktif kullanıcı, rol kontrolü."""
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.istisnalar import KimlikHatasi, YetkiHatasi
from app.core.veritabani import oturum_al
from app.models import Kullanici, Uye

oauth2_semasi = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


def aktif_kullanici(token: str | None = Depends(oauth2_semasi), db: Session = Depends(oturum_al)) -> Kullanici:
    """Bearer token'dan giriş yapmış kullanıcıyı çözer."""
    from app.services.auth_servisi import AuthServisi  # döngüsel içe aktarmayı önler

    if not token:
        raise KimlikHatasi("Bu işlem için giriş yapmalısınız.")
    return AuthServisi(db).token_ile_kullanici(token)


def yonetici_gerekli(kullanici: Kullanici = Depends(aktif_kullanici)) -> Kullanici:
    if not kullanici.yonetici_mi():
        raise YetkiHatasi("Bu işlem yalnızca yöneticiler içindir.")
    return kullanici


def uye_gerekli(kullanici: Kullanici = Depends(aktif_kullanici)) -> Uye:
    if not isinstance(kullanici, Uye):
        raise YetkiHatasi("Bu işlem yalnızca üyeler içindir.")
    return kullanici
