"""İş kuralı ve erişim istisnaları (HTTP'den bağımsız)."""


class IsKuraliHatasi(Exception):
    """Genel iş kuralı ihlali (HTTP 400)."""

    durum_kodu = 400

    def __init__(self, mesaj: str):
        super().__init__(mesaj)
        self.mesaj = mesaj


class BulunamadiHatasi(IsKuraliHatasi):
    durum_kodu = 404


class CakismaHatasi(IsKuraliHatasi):
    durum_kodu = 409


class YetkiHatasi(IsKuraliHatasi):
    durum_kodu = 403


class KimlikHatasi(IsKuraliHatasi):
    durum_kodu = 401
