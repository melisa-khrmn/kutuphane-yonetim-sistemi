"""Kimlik doğrulama servisi."""
from sqlalchemy.orm import Session

from app.core.guvenlik import sifre_dogrula, sifre_hashle, token_coz, token_olustur
from app.core.istisnalar import CakismaHatasi, KimlikHatasi
from app.models import Kullanici, Uye
from app.repositories import KullaniciRepository, UyeRepository
from app.schemas import KayitIstek


class AuthServisi:
    def __init__(self, db: Session):
        self.kullanici_repo = KullaniciRepository(db)
        self.uye_repo = UyeRepository(db)

    def kayit_ol(self, istek: KayitIstek) -> Uye:
        if self.kullanici_repo.email_ile(istek.email):
            raise CakismaHatasi("Bu e-posta adresi zaten kayıtlı.")
        if self.uye_repo.ogrenci_no_ile(istek.ogrenci_no):
            raise CakismaHatasi("Bu öğrenci numarası zaten kayıtlı.")
        uye = Uye(
            ad=istek.ad.strip(), soyad=istek.soyad.strip(), email=istek.email.lower(),
            sifre_hash=sifre_hashle(istek.sifre), ogrenci_no=istek.ogrenci_no.strip(),
            bolum=istek.bolum.strip(), telefon=istek.telefon, ceza_puani=0, aktif_mi=True,
        )
        self.uye_repo.ekle(uye)
        self.uye_repo.kaydet()
        return uye

    def giris_yap(self, email: str, sifre: str) -> tuple[str, Kullanici]:
        kullanici = self.kullanici_repo.email_ile(email)
        if not kullanici or not sifre_dogrula(sifre, kullanici.sifre_hash):
            raise KimlikHatasi("E-posta veya şifre hatalı.")
        if not kullanici.aktif_mi:
            raise KimlikHatasi("Hesabınız pasif durumda. Lütfen kütüphane yönetimiyle iletişime geçin.")
        return token_olustur(kullanici.id, kullanici.rol.value), kullanici

    def token_ile_kullanici(self, token: str) -> Kullanici:
        veri = token_coz(token)
        if not veri or "sub" not in veri:
            raise KimlikHatasi("Geçersiz veya süresi dolmuş oturum.")
        kullanici = self.kullanici_repo.getir(int(veri["sub"]))
        if not kullanici or not kullanici.aktif_mi:
            raise KimlikHatasi("Kullanıcı bulunamadı veya pasif.")
        return kullanici
