"""Ödünç ve Rezervasyon iş mantığı (tüm iş kuralları burada)."""
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.ayarlar import ayarlar
from app.core.istisnalar import BulunamadiHatasi, CakismaHatasi, IsKuraliHatasi, YetkiHatasi
from app.models import Kullanici, Odunc, OduncDurumu, Rezervasyon, RezervasyonDurumu, Uye
from app.repositories import KitapRepository, OduncRepository, RezervasyonRepository, UyeRepository


class OduncServisi:
    def __init__(self, db: Session):
        self.repo = OduncRepository(db)
        self.kitap_repo = KitapRepository(db)
        self.uye_repo = UyeRepository(db)
        self.rez_repo = RezervasyonRepository(db)

    def getir(self, odunc_id: int) -> Odunc:
        odunc = self.repo.getir(odunc_id)
        if not odunc:
            raise BulunamadiHatasi("Ödünç kaydı bulunamadı.")
        return odunc

    @staticmethod
    def _yetki_kontrol(odunc: Odunc, istek_yapan: Kullanici) -> None:
        if not istek_yapan.yonetici_mi() and odunc.uye_id != istek_yapan.id:
            raise YetkiHatasi("Bu ödünç kaydı size ait değil.")

    def odunc_ver(self, uye_id: int, kitap_id: int, bugun: date | None = None) -> Odunc:
        bugun = bugun or date.today()
        uye = self.uye_repo.getir(uye_id)
        if not uye:
            raise BulunamadiHatasi("Üye bulunamadı.")
        if not uye.aktif_mi:
            raise IsKuraliHatasi("Üye hesabı pasif; ödünç verilemez.")
        kitap = self.kitap_repo.getir(kitap_id)
        if not kitap:
            raise BulunamadiHatasi("Kitap bulunamadı.")

        # İş kuralları
        if self.repo.aktif_odunc_var_mi(uye.id, kitap.id):
            raise CakismaHatasi("Bu kitap zaten üyede ödünçte; aynı kitap iki kez verilemez.")
        if any(o.gecikmis_mi(bugun) for o in uye.aktif_oduncler()):
            raise IsKuraliHatasi("Gecikmiş kitabı olan üye yeni ödünç alamaz. Önce gecikmiş kitabı iade edin.")
        if uye.aktif_odunc_sayisi() >= ayarlar.max_aktif_odunc:
            raise IsKuraliHatasi(f"Aynı anda en fazla {ayarlar.max_aktif_odunc} kitap ödünç alınabilir.")
        if not kitap.musait_mi():
            raise IsKuraliHatasi("Kitabın mevcut adedi kalmadı. Rezervasyon yapabilirsiniz.")

        odunc = Odunc(
            uye=uye, kitap=kitap, alis_tarihi=bugun,
            son_iade_tarihi=bugun + timedelta(days=ayarlar.odunc_suresi_gun),
            durum=OduncDurumu.AKTIF, gecikme_gunu=0, ceza_tutari=0.0, uzatma_sayisi=0,
        )
        kitap.stok_azalt()
        # Üyenin bu kitap için bekleyen rezervasyonu varsa karşılandı say
        rez = self.rez_repo.bekleyen_var_mi(uye.id, kitap.id)
        if rez:
            rez.karsila()
        self.repo.ekle(odunc)
        self.repo.kaydet()
        return odunc

    def iade_al(
        self, odunc_id: int, istek_yapan: Kullanici, bugun: date | None = None
    ) -> tuple[Odunc, Rezervasyon | None]:
        odunc = self.getir(odunc_id)
        self._yetki_kontrol(odunc, istek_yapan)
        odunc.iade_et(bugun or date.today())
        odunc.uye.ceza_puani += odunc.gecikme_gunu
        odunc.kitap.stok_artir()
        # Bekleyen ilk rezervasyonu karşıla
        siradaki = self.rez_repo.siradaki(odunc.kitap_id)
        if siradaki:
            siradaki.karsila()
        self.repo.kaydet()
        return odunc, siradaki

    def uzat(self, odunc_id: int, istek_yapan: Kullanici, bugun: date | None = None) -> Odunc:
        odunc = self.getir(odunc_id)
        self._yetki_kontrol(odunc, istek_yapan)
        if self.rez_repo.siradaki(odunc.kitap_id) and odunc.kitap.mevcut_adet == 0:
            raise IsKuraliHatasi("Bu kitap için bekleyen rezervasyon var; uzatma yapılamaz.")
        odunc.uzat(bugun or date.today())
        self.repo.kaydet()
        return odunc

    def uyenin_oduncleri(self, uye_id: int) -> list[Odunc]:
        return self.repo.uyenin(uye_id)

    def filtrele(self, durum: OduncDurumu | None, uye_id: int | None, kitap_id: int | None) -> list[Odunc]:
        return self.repo.filtrele(durum, uye_id, kitap_id)


class RezervasyonServisi:
    def __init__(self, db: Session):
        self.repo = RezervasyonRepository(db)
        self.kitap_repo = KitapRepository(db)
        self.uye_repo = UyeRepository(db)
        self.odunc_repo = OduncRepository(db)

    def olustur(self, uye_id: int, kitap_id: int) -> Rezervasyon:
        uye: Uye | None = self.uye_repo.getir(uye_id)
        if not uye:
            raise BulunamadiHatasi("Üye bulunamadı.")
        kitap = self.kitap_repo.getir(kitap_id)
        if not kitap:
            raise BulunamadiHatasi("Kitap bulunamadı.")
        if kitap.musait_mi():
            raise IsKuraliHatasi("Kitap şu an rafta mevcut; rezervasyon yerine doğrudan ödünç alabilirsiniz.")
        if self.odunc_repo.aktif_odunc_var_mi(uye_id, kitap_id):
            raise CakismaHatasi("Bu kitap zaten sizde ödünçte.")
        if self.repo.bekleyen_var_mi(uye_id, kitap_id):
            raise CakismaHatasi("Bu kitap için zaten bekleyen bir rezervasyonunuz var.")
        rez = Rezervasyon(uye=uye, kitap=kitap, tarih=datetime.now(), durum=RezervasyonDurumu.BEKLIYOR)
        self.repo.ekle(rez)
        self.repo.kaydet()
        return rez

    def uyenin(self, uye_id: int) -> list[Rezervasyon]:
        return self.repo.uyenin(uye_id)

    def sira(self, rez: Rezervasyon) -> int | None:
        return self.repo.sira_numarasi(rez) if rez.bekliyor_mu() else None

    def tumu(self, durum: RezervasyonDurumu | None = None) -> list[Rezervasyon]:
        return self.repo.tumu_filtreli(durum)

    def iptal_et(self, rez_id: int, istek_yapan: Kullanici) -> Rezervasyon:
        rez = self.repo.getir(rez_id)
        if not rez:
            raise BulunamadiHatasi("Rezervasyon bulunamadı.")
        if not istek_yapan.yonetici_mi() and rez.uye_id != istek_yapan.id:
            raise YetkiHatasi("Bu rezervasyon size ait değil.")
        rez.iptal_et()
        self.repo.kaydet()
        return rez
