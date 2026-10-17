"""Router katmanı: REST API uçları."""
from fastapi import APIRouter

from app.routers.auth import router as auth_router
from app.routers.islemler import odunc_router, rapor_router, rez_router, uye_router
from app.routers.katalog import kategori_router, kitap_router, yazar_router

api_router = APIRouter(prefix="/api")
for r in (auth_router, kitap_router, yazar_router, kategori_router, uye_router, odunc_router, rez_router, rapor_router):
    api_router.include_router(r)
