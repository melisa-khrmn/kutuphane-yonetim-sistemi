"""Alan enum'ları."""
import enum


class Rol(str, enum.Enum):
    UYE = "UYE"
    YONETICI = "YONETICI"


class OduncDurumu(str, enum.Enum):
    AKTIF = "AKTIF"
    IADE_EDILDI = "IADE_EDILDI"
    GECIKMIS = "GECIKMIS"


class RezervasyonDurumu(str, enum.Enum):
    BEKLIYOR = "BEKLIYOR"
    KARSILANDI = "KARSILANDI"
    IPTAL = "IPTAL"
