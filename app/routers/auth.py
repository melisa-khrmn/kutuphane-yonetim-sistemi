"""Kimlik doğrulama uçları."""
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.bagimliliklar import aktif_kullanici
from app.core.veritabani import oturum_al
from app.models import Kullanici
from app.schemas import GirisIstek, KayitIstek, KullaniciYanit, TokenYanit
from app.services import AuthServisi

router = APIRouter(prefix="/auth", tags=["Kimlik Doğrulama"])


@router.post("/kayit", response_model=KullaniciYanit, status_code=status.HTTP_201_CREATED,
             summary="Üye kaydı oluştur",
             description="Yeni bir öğrenci üye hesabı açar. E-posta ve öğrenci numarası benzersiz olmalıdır.")
def kayit(istek: KayitIstek, db: Session = Depends(oturum_al)):
    return KullaniciYanit.nesneden(AuthServisi(db).kayit_ol(istek))


@router.post("/giris", response_model=TokenYanit, summary="Giriş yap",
             description="E-posta ve şifre ile giriş yapar; JWT erişim anahtarı döndürür.")
def giris(istek: GirisIstek, db: Session = Depends(oturum_al)):
    token, kullanici = AuthServisi(db).giris_yap(istek.email, istek.sifre)
    return TokenYanit(access_token=token, kullanici=KullaniciYanit.nesneden(kullanici))


@router.post("/token", response_model=TokenYanit, summary="Swagger için form tabanlı giriş",
             description="Swagger 'Authorize' düğmesi tarafından kullanılır. **username** alanına e-posta yazın.")
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(oturum_al)):
    erisim, kullanici = AuthServisi(db).giris_yap(form.username, form.password)
    return TokenYanit(access_token=erisim, kullanici=KullaniciYanit.nesneden(kullanici))


@router.get("/ben", response_model=KullaniciYanit, summary="Oturumdaki kullanıcı",
            description="Giriş yapmış kullanıcının profil bilgilerini döndürür.")
def ben(kullanici: Kullanici = Depends(aktif_kullanici)):
    return KullaniciYanit.nesneden(kullanici)
