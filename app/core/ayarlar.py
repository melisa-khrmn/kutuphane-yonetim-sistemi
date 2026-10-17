"""Uygulama ayarları (ortam değişkenleriyle ezilebilir)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Ayarlar(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KUTUPHANE_", env_file=".env", extra="ignore")

    uygulama_adi: str = "Online Kütüphane Yönetim Sistemi"
    veritabani_url: str = "sqlite:///./kutuphane.db"
    gizli_anahtar: str = "gelistirme-icin-gizli-anahtar-uretimde-degistirin"
    jwt_algoritma: str = "HS256"
    token_sure_dakika: int = 60 * 8

    # İş kuralı sabitleri
    odunc_suresi_gun: int = 14
    uzatma_suresi_gun: int = 7
    max_uzatma_sayisi: int = 1
    max_aktif_odunc: int = 5
    gunluk_ceza_tl: float = 2.0
    az_stok_esigi: int = 1

    seed_calistir: bool = True


ayarlar = Ayarlar()
