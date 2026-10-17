"""Üye yönetimi, ödünç, rezervasyon ve rapor uçları."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.bagimliliklar import aktif_kullanici, uye_gerekli, yonetici_gerekli
from app.core.istisnalar import IsKuraliHatasi
from app.core.veritabani import oturum_al
from app.models import Kullanici, OduncDurumu, RezervasyonDurumu, Uye
from app.schemas import (
    AktiflikIstek, EnCokOkunanSatiri, IadeYanit, MesajYanit, OduncOlustur, OduncYanit, OzetRapor,
    RezervasyonOlustur, RezervasyonYanit, StokSatiri, UyeDetayYanit, UyeGuncelle, UyeYanit,
)
from app.services import OduncServisi, RaporServisi, RezervasyonServisi, UyeServisi

YONETICI = [Depends(yonetici_gerekli)]


def _hedef_uye_id(kullanici: Kullanici, istenen: int | None) -> int:
    """Üye kendi adına, yönetici seçtiği üye adına işlem yapar."""
    if kullanici.yonetici_mi():
        if not istenen:
            raise IsKuraliHatasi("Yönetici olarak işlem yaparken uye_id belirtmelisiniz.")
        return istenen
    return kullanici.id


# ---------------- Üyeler ----------------
uye_router = APIRouter(prefix="/uyeler", tags=["Üye Yönetimi"], dependencies=YONETICI)


@uye_router.get("", response_model=list[UyeYanit], summary="Üyeleri listele (yönetici)")
def uye_listele(arama: str | None = Query(None, description="Ad, soyad, e-posta veya öğrenci no"),
                aktif_mi: bool | None = Query(None, description="Aktif/pasif filtresi"),
                db: Session = Depends(oturum_al)):
    return [UyeYanit.nesneden(u) for u in UyeServisi(db).listele(arama, aktif_mi)]


@uye_router.get("/{uye_id}", response_model=UyeDetayYanit, summary="Üye detayı (yönetici)",
                description="Üye bilgileri ile ödünç ve rezervasyon geçmişini döndürür.")
def uye_getir(uye_id: int, db: Session = Depends(oturum_al)):
    uye = UyeServisi(db).getir(uye_id)
    return UyeDetayYanit(
        **UyeYanit.nesneden(uye).model_dump(),
        oduncler=[OduncYanit.nesneden(o) for o in OduncServisi(db).uyenin_oduncleri(uye_id)],
        rezervasyonlar=[RezervasyonYanit.nesneden(r) for r in RezervasyonServisi(db).uyenin(uye_id)],
    )


@uye_router.put("/{uye_id}", response_model=UyeYanit, summary="Üye güncelle (yönetici)")
def uye_guncelle(uye_id: int, veri: UyeGuncelle, db: Session = Depends(oturum_al)):
    return UyeYanit.nesneden(UyeServisi(db).guncelle(uye_id, veri))


@uye_router.put("/{uye_id}/aktiflik", response_model=UyeYanit, summary="Üyeyi aktif/pasif yap (yönetici)",
                description="Pasif üye giriş yapamaz ve ödünç alamaz.")
def uye_aktiflik(uye_id: int, veri: AktiflikIstek, db: Session = Depends(oturum_al)):
    return UyeYanit.nesneden(UyeServisi(db).aktiflik_degistir(uye_id, veri.aktif_mi))


@uye_router.delete("/{uye_id}", response_model=MesajYanit, summary="Üye sil (yönetici)",
                   description="İade etmediği kitabı olan üye silinemez.")
def uye_sil(uye_id: int, db: Session = Depends(oturum_al)):
    UyeServisi(db).sil(uye_id)
    return MesajYanit(mesaj="Üye silindi.")


# ---------------- Ödünçler ----------------
odunc_router = APIRouter(prefix="/oduncler", tags=["Ödünç İşlemleri"])


@odunc_router.post("", response_model=OduncYanit, status_code=status.HTTP_201_CREATED, summary="Ödünç al / ver",
                   description=(
                       "Üye kendi adına ödünç alır; yönetici `uye_id` vererek ödünç verir.\n\n"
                       "Kurallar: stok 0 ise verilmez, en fazla 5 aktif ödünç, gecikmiş kitabı olan alamaz, "
                       "aynı kitap aynı üyeye aktif olarak iki kez verilemez. Süre 14 gündür."
                   ))
def odunc_ver(veri: OduncOlustur, kullanici: Kullanici = Depends(aktif_kullanici), db: Session = Depends(oturum_al)):
    uye_id = _hedef_uye_id(kullanici, veri.uye_id)
    return OduncYanit.nesneden(OduncServisi(db).odunc_ver(uye_id, veri.kitap_id))


@odunc_router.put("/{odunc_id}/iade", response_model=IadeYanit, summary="Kitabı iade et",
                  description="İade tarihi bugün olarak işlenir; gecikme varsa günlük 2 TL ceza hesaplanır. "
                              "Bekleyen ilk rezervasyon 'KARSILANDI' olarak işaretlenir.")
def iade(odunc_id: int, kullanici: Kullanici = Depends(aktif_kullanici), db: Session = Depends(oturum_al)):
    odunc, rez = OduncServisi(db).iade_al(odunc_id, kullanici)
    mesaj = "Kitap iade alındı."
    if odunc.ceza_tutari:
        mesaj += f" {odunc.gecikme_gunu} gün gecikme: {odunc.ceza_tutari:.2f} TL ceza."
    if rez:
        mesaj += f" Rezervasyon sırasındaki {rez.uye.tam_ad} için ayrıldı."
    return IadeYanit(mesaj=mesaj, odunc=OduncYanit.nesneden(odunc), ceza_tutari=odunc.ceza_tutari,
                     karsilanan_rezervasyon=RezervasyonYanit.nesneden(rez) if rez else None)


@odunc_router.put("/{odunc_id}/uzat", response_model=OduncYanit, summary="Ödünç süresini uzat",
                  description="Süre 7 gün uzatılır. Her ödünç yalnızca 1 kez uzatılabilir; gecikmiş ödünç uzatılamaz.")
def uzat(odunc_id: int, kullanici: Kullanici = Depends(aktif_kullanici), db: Session = Depends(oturum_al)):
    return OduncYanit.nesneden(OduncServisi(db).uzat(odunc_id, kullanici))


@odunc_router.get("/benim", response_model=list[OduncYanit], summary="Ödünçlerim (üye)")
def benim_oduncler(uye: Uye = Depends(uye_gerekli), db: Session = Depends(oturum_al)):
    return [OduncYanit.nesneden(o) for o in OduncServisi(db).uyenin_oduncleri(uye.id)]


@odunc_router.get("", response_model=list[OduncYanit], dependencies=YONETICI, summary="Tüm ödünçler (yönetici)",
                  description="Durum, üye ve kitaba göre filtrelenebilir.")
def odunc_listele(durum: OduncDurumu | None = Query(None, description="AKTIF / IADE_EDILDI / GECIKMIS"),
                  uye_id: int | None = Query(None), kitap_id: int | None = Query(None),
                  db: Session = Depends(oturum_al)):
    return [OduncYanit.nesneden(o) for o in OduncServisi(db).filtrele(durum, uye_id, kitap_id)]


# ---------------- Rezervasyonlar ----------------
rez_router = APIRouter(prefix="/rezervasyonlar", tags=["Rezervasyonlar"])


@rez_router.post("", response_model=RezervasyonYanit, status_code=status.HTTP_201_CREATED,
                 summary="Rezervasyon yap", description="Yalnızca stokta olmayan kitaplar rezerve edilebilir.")
def rez_olustur(veri: RezervasyonOlustur, kullanici: Kullanici = Depends(aktif_kullanici),
                db: Session = Depends(oturum_al)):
    servis = RezervasyonServisi(db)
    rez = servis.olustur(_hedef_uye_id(kullanici, veri.uye_id), veri.kitap_id)
    return RezervasyonYanit.nesneden(rez, servis.sira(rez))


@rez_router.get("/benim", response_model=list[RezervasyonYanit], summary="Rezervasyonlarım (üye)")
def rez_benim(uye: Uye = Depends(uye_gerekli), db: Session = Depends(oturum_al)):
    servis = RezervasyonServisi(db)
    return [RezervasyonYanit.nesneden(r, servis.sira(r)) for r in servis.uyenin(uye.id)]


@rez_router.get("", response_model=list[RezervasyonYanit], dependencies=YONETICI,
                summary="Tüm rezervasyonlar (yönetici)")
def rez_listele(durum: RezervasyonDurumu | None = Query(None), db: Session = Depends(oturum_al)):
    servis = RezervasyonServisi(db)
    return [RezervasyonYanit.nesneden(r, servis.sira(r)) for r in servis.tumu(durum)]


@rez_router.delete("/{rez_id}", response_model=RezervasyonYanit, summary="Rezervasyonu iptal et",
                   description="Üye kendi bekleyen rezervasyonunu, yönetici herhangi birini iptal edebilir.")
def rez_iptal(rez_id: int, kullanici: Kullanici = Depends(aktif_kullanici), db: Session = Depends(oturum_al)):
    return RezervasyonYanit.nesneden(RezervasyonServisi(db).iptal_et(rez_id, kullanici))


# ---------------- Raporlar ----------------
rapor_router = APIRouter(prefix="/raporlar", tags=["Raporlar"], dependencies=YONETICI)


@rapor_router.get("/gecikmeler", response_model=list[OduncYanit], summary="Geciken ödünçler",
                  description="Çağrıldığında gecikme durumları güncellenir.")
def rapor_gecikmeler(db: Session = Depends(oturum_al)):
    return [OduncYanit.nesneden(o) for o in RaporServisi(db).gecikmeler()]


@rapor_router.get("/stok", response_model=list[StokSatiri], summary="Az kalan kitaplar",
                  description="Mevcut adedi eşik değerin altında/eşit olan kitaplar.")
def rapor_stok(esik: int = Query(1, ge=0, description="Mevcut adet eşiği"), db: Session = Depends(oturum_al)):
    return [
        StokSatiri(id=k.id, baslik=k.baslik, isbn=k.isbn, raf_kodu=k.raf_kodu, toplam_adet=k.toplam_adet,
                   mevcut_adet=k.mevcut_adet, bekleyen_rezervasyon=sum(1 for r in k.rezervasyonlar if r.bekliyor_mu()))
        for k in RaporServisi(db).stok(esik)
    ]


@rapor_router.get("/en-cok-okunanlar", response_model=list[EnCokOkunanSatiri], summary="En çok okunan kitaplar")
def rapor_en_cok(limit: int = Query(10, ge=1, le=50), db: Session = Depends(oturum_al)):
    return [EnCokOkunanSatiri(id=k.id, baslik=k.baslik, yazarlar=k.yazar_adlari, odunc_sayisi=s)
            for k, s in RaporServisi(db).en_cok_okunanlar(limit)]


@rapor_router.get("/ozet", response_model=OzetRapor, summary="Özet istatistikler",
                  description="Toplam kitap, üye, aktif ödünç ve geciken sayısı gibi dashboard verileri.")
def rapor_ozet(db: Session = Depends(oturum_al)):
    return OzetRapor(**RaporServisi(db).ozet())
