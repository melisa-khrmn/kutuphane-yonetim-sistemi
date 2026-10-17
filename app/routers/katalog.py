"""Kitap, Yazar ve Kategori uçları."""
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.bagimliliklar import yonetici_gerekli
from app.core.veritabani import oturum_al
from app.schemas import (
    KategoriGuncelle, KategoriOlustur, KategoriYanit, KitapGuncelle, KitapListeYanit, KitapOlustur,
    KitapYanit, MesajYanit, YazarGuncelle, YazarOlustur, YazarYanit,
)
from app.services import KategoriServisi, KitapServisi, YazarServisi

YONETICI = [Depends(yonetici_gerekli)]

# ---------------- Kitaplar ----------------
kitap_router = APIRouter(prefix="/kitaplar", tags=["Kitaplar"])


@kitap_router.get("", response_model=KitapListeYanit, summary="Kitap ara / listele",
                  description="Başlık, yazar, ISBN ve kategoriye göre arama; sayfalama ve sıralama destekler. Herkese açıktır.")
def kitap_listele(
    baslik: str | None = Query(None, description="Başlıkta geçen ifade"),
    yazar: str | None = Query(None, description="Yazar adı/soyadı"),
    isbn: str | None = Query(None, description="ISBN (kısmi)"),
    kategori: int | None = Query(None, description="Kategori kimliği"),
    sadece_musait: bool = Query(False, description="Yalnızca rafta mevcut olanlar"),
    sayfa: int = Query(1, ge=1, description="Sayfa numarası"),
    boyut: int = Query(12, ge=1, le=100, description="Sayfa başına kayıt"),
    sirala: Literal["baslik", "yayin_yili", "mevcut_adet", "id"] = Query("baslik", description="Sıralama alanı"),
    yon: Literal["artan", "azalan"] = Query("artan", description="Sıralama yönü"),
    db: Session = Depends(oturum_al),
):
    kitaplar, toplam, toplam_sayfa = KitapServisi(db).ara(
        baslik=baslik, yazar=yazar, isbn=isbn, kategori_id=kategori, sadece_musait=sadece_musait,
        sayfa=sayfa, boyut=boyut, sirala=sirala, yon=yon,
    )
    return KitapListeYanit(kayitlar=[KitapYanit.nesneden(k) for k in kitaplar], toplam=toplam,
                           sayfa=sayfa, boyut=boyut, toplam_sayfa=toplam_sayfa)


@kitap_router.get("/{kitap_id}", response_model=KitapYanit, summary="Kitap detayı")
def kitap_getir(kitap_id: int, db: Session = Depends(oturum_al)):
    return KitapYanit.nesneden(KitapServisi(db).getir(kitap_id))


@kitap_router.post("", response_model=KitapYanit, status_code=status.HTTP_201_CREATED, dependencies=YONETICI,
                   summary="Kitap ekle (yönetici)", description="Yeni kitap ekler. Mevcut adet, toplam adede eşitlenir.")
def kitap_ekle(veri: KitapOlustur, db: Session = Depends(oturum_al)):
    return KitapYanit.nesneden(KitapServisi(db).olustur(veri))


@kitap_router.put("/{kitap_id}", response_model=KitapYanit, dependencies=YONETICI, summary="Kitap güncelle (yönetici)",
                  description="Gönderilen alanları günceller. Toplam adet değişirse mevcut adet ödünçtekilere göre ayarlanır.")
def kitap_guncelle(kitap_id: int, veri: KitapGuncelle, db: Session = Depends(oturum_al)):
    return KitapYanit.nesneden(KitapServisi(db).guncelle(kitap_id, veri))


@kitap_router.delete("/{kitap_id}", response_model=MesajYanit, dependencies=YONETICI, summary="Kitap sil (yönetici)",
                     description="Aktif ödüncü olan kitap silinemez.")
def kitap_sil(kitap_id: int, db: Session = Depends(oturum_al)):
    KitapServisi(db).sil(kitap_id)
    return MesajYanit(mesaj="Kitap silindi.")


# ---------------- Yazarlar ----------------
yazar_router = APIRouter(prefix="/yazarlar", tags=["Yazarlar"])


@yazar_router.get("", response_model=list[YazarYanit], summary="Yazarları listele")
def yazar_listele(arama: str | None = Query(None, description="Ad/soyad araması"), db: Session = Depends(oturum_al)):
    return [YazarYanit.nesneden(y) for y in YazarServisi(db).listele(arama)]


@yazar_router.get("/{yazar_id}", response_model=YazarYanit, summary="Yazar detayı (kitaplarıyla)")
def yazar_getir(yazar_id: int, db: Session = Depends(oturum_al)):
    return YazarYanit.nesneden(YazarServisi(db).getir(yazar_id), kitaplarla=True)


@yazar_router.post("", response_model=YazarYanit, status_code=status.HTTP_201_CREATED, dependencies=YONETICI,
                   summary="Yazar ekle (yönetici)")
def yazar_ekle(veri: YazarOlustur, db: Session = Depends(oturum_al)):
    return YazarYanit.nesneden(YazarServisi(db).olustur(veri))


@yazar_router.put("/{yazar_id}", response_model=YazarYanit, dependencies=YONETICI, summary="Yazar güncelle (yönetici)")
def yazar_guncelle(yazar_id: int, veri: YazarGuncelle, db: Session = Depends(oturum_al)):
    return YazarYanit.nesneden(YazarServisi(db).guncelle(yazar_id, veri))


@yazar_router.delete("/{yazar_id}", response_model=MesajYanit, dependencies=YONETICI, summary="Yazar sil (yönetici)",
                     description="Kayıtlı kitabı olan yazar silinemez.")
def yazar_sil(yazar_id: int, db: Session = Depends(oturum_al)):
    YazarServisi(db).sil(yazar_id)
    return MesajYanit(mesaj="Yazar silindi.")


# ---------------- Kategoriler ----------------
kategori_router = APIRouter(prefix="/kategoriler", tags=["Kategoriler"])


@kategori_router.get("", response_model=list[KategoriYanit], summary="Kategorileri listele")
def kategori_listele(db: Session = Depends(oturum_al)):
    return [KategoriYanit.nesneden(k) for k in KategoriServisi(db).listele()]


@kategori_router.get("/{kategori_id}", response_model=KategoriYanit, summary="Kategori detayı")
def kategori_getir(kategori_id: int, db: Session = Depends(oturum_al)):
    return KategoriYanit.nesneden(KategoriServisi(db).getir(kategori_id))


@kategori_router.post("", response_model=KategoriYanit, status_code=status.HTTP_201_CREATED, dependencies=YONETICI,
                      summary="Kategori ekle (yönetici)")
def kategori_ekle(veri: KategoriOlustur, db: Session = Depends(oturum_al)):
    return KategoriYanit.nesneden(KategoriServisi(db).olustur(veri))


@kategori_router.put("/{kategori_id}", response_model=KategoriYanit, dependencies=YONETICI,
                     summary="Kategori güncelle (yönetici)")
def kategori_guncelle(kategori_id: int, veri: KategoriGuncelle, db: Session = Depends(oturum_al)):
    return KategoriYanit.nesneden(KategoriServisi(db).guncelle(kategori_id, veri))


@kategori_router.delete("/{kategori_id}", response_model=MesajYanit, dependencies=YONETICI,
                        summary="Kategori sil (yönetici)", description="İçinde kitap bulunan kategori silinemez.")
def kategori_sil(kategori_id: int, db: Session = Depends(oturum_al)):
    KategoriServisi(db).sil(kategori_id)
    return MesajYanit(mesaj="Kategori silindi.")
