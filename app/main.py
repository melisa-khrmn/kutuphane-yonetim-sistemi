"""Uygulama giriş noktası: uvicorn app.main:app --reload"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.ayarlar import ayarlar
from app.core.istisnalar import IsKuraliHatasi
from app.core.veritabani import Base, OturumYerel, motor
from app.routers import api_router
from app.services import gecikmeleri_guncelle
from app.services.seed_servisi import seed_olustur

STATIK = Path(__file__).parent / "static"

ETIKETLER = [
    {"name": "Kimlik Doğrulama", "description": "Kayıt, giriş ve oturum bilgisi."},
    {"name": "Kitaplar", "description": "Kitap arama ve kitap yönetimi (CRUD)."},
    {"name": "Yazarlar", "description": "Yazar yönetimi (CRUD)."},
    {"name": "Kategoriler", "description": "Kategori yönetimi (CRUD)."},
    {"name": "Üye Yönetimi", "description": "Yönetici için üye işlemleri."},
    {"name": "Ödünç İşlemleri", "description": "Ödünç alma, iade, uzatma ve listeleme."},
    {"name": "Rezervasyonlar", "description": "Stokta olmayan kitaplar için rezervasyon."},
    {"name": "Raporlar", "description": "Yönetici raporları ve özet istatistikler."},
]


@asynccontextmanager
async def yasam_dongusu(_: FastAPI):
    # Açılışta tabloları oluştur, seed'i çalıştır, gecikmeleri güncelle
    Base.metadata.create_all(bind=motor)
    with OturumYerel() as db:
        if ayarlar.seed_calistir:
            seed_olustur(db)
        gecikmeleri_guncelle(db)
    yield


app = FastAPI(
    title=ayarlar.uygulama_adi,
    description=(
        "Üniversite kütüphanesi için ödünç, rezervasyon ve katalog yönetimi API'si.\n\n"
        "**Giriş:** Sağ üstteki *Authorize* düğmesine `admin@kutuphane.com` / `Admin123!` yazın "
        "(username alanına e-posta)."
    ),
    version="1.0.0",
    openapi_tags=ETIKETLER,
    lifespan=yasam_dongusu,
)


@app.exception_handler(IsKuraliHatasi)
async def is_kurali_isleyici(_: Request, hata: IsKuraliHatasi):
    basliklar = {"WWW-Authenticate": "Bearer"} if hata.durum_kodu == 401 else None
    return JSONResponse(status_code=hata.durum_kodu, content={"detail": hata.mesaj}, headers=basliklar)


@app.exception_handler(RequestValidationError)
async def dogrulama_isleyici(_: Request, hata: RequestValidationError):
    mesajlar = []
    for e in hata.errors():
        alan = ".".join(str(p) for p in e.get("loc", []) if p not in ("body", "query", "path"))
        mesajlar.append(f"{alan}: {e.get('msg')}" if alan else e.get("msg"))
    return JSONResponse(status_code=422, content={"detail": "Geçersiz veri — " + "; ".join(mesajlar)})


app.include_router(api_router)
app.mount("/static", StaticFiles(directory=STATIK), name="static")


@app.get("/", include_in_schema=False)
def ana_sayfa():
    return FileResponse(STATIK / "index.html")
