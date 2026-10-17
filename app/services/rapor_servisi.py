"""Raporlama servisi ve gecikme güncelleme yardımcı fonksiyonu."""
from datetime import date

from sqlalchemy.orm import Session

from app.core.ayarlar import ayarlar
from app.models import Kitap, Odunc, OduncDurumu, RezervasyonDurumu
from app.repositories import KitapRepository, OduncRepository, RezervasyonRepository, UyeRepository


def gecikmeleri_guncelle(db: Session, bugun: date | None = None) -> int:
    """İade edilmemiş ödünçleri tarar; süresi geçenleri GECIKMIS yapar ve anlık cezayı yazar.

    Uygulama açılışında ve rapor çağrılarında çalışır. Güncellenen kayıt sayısını döndürür.
    """
    repo = OduncRepository(db)
    guncellenen = sum(1 for o in repo.iade_edilmemisler() if o.durumu_guncelle(bugun))
    if guncellenen:
        repo.kaydet()
    return guncellenen


class RaporServisi:
    def __init__(self, db: Session):
        self.db = db
        self.odunc_repo = OduncRepository(db)
        self.kitap_repo = KitapRepository(db)
        self.uye_repo = UyeRepository(db)
        self.rez_repo = RezervasyonRepository(db)

    def gecikmeler(self) -> list[Odunc]:
        gecikmeleri_guncelle(self.db)
        return self.odunc_repo.gecikmisler()

    def stok(self, esik: int | None = None) -> list[Kitap]:
        return self.kitap_repo.az_stoklu(ayarlar.az_stok_esigi if esik is None else esik)

    def en_cok_okunanlar(self, limit: int = 10) -> list[tuple[Kitap, int]]:
        return self.odunc_repo.en_cok_okunanlar(limit)

    def ozet(self) -> dict:
        gecikmeleri_guncelle(self.db)
        kitaplar = self.kitap_repo.tumu()
        uyeler = self.uye_repo.tumu()
        return {
            "toplam_kitap": len(kitaplar),
            "toplam_kopya": sum(k.toplam_adet for k in kitaplar),
            "mevcut_kopya": sum(k.mevcut_adet for k in kitaplar),
            "toplam_uye": len(uyeler),
            "aktif_uye": sum(1 for u in uyeler if u.aktif_mi),
            "aktif_odunc": self.odunc_repo.durum_sayisi(OduncDurumu.AKTIF, OduncDurumu.GECIKMIS),
            "geciken": self.odunc_repo.durum_sayisi(OduncDurumu.GECIKMIS),
            "bekleyen_rezervasyon": len(self.rez_repo.tumu_filtreli(RezervasyonDurumu.BEKLIYOR)),
            "toplam_ceza": round(self.odunc_repo.toplam_ceza(), 2),
        }
