"""İlk açılışta örnek verileri oluşturan seed servisi."""
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.ayarlar import ayarlar
from app.core.guvenlik import sifre_hashle
from app.models import Kategori, Kitap, Odunc, OduncDurumu, Rezervasyon, RezervasyonDurumu, Uye, Yazar, Yonetici
from app.repositories import KullaniciRepository
from app.services.rapor_servisi import gecikmeleri_guncelle

KATEGORILER = ["Türk Edebiyatı", "Dünya Klasikleri", "Bilim Kurgu", "Fantastik", "Distopya", "Tarih ve Bilim"]

YAZARLAR = [
    ("Sabahattin", "Ali", 1907, "Türk edebiyatının önemli öykü ve roman yazarlarından."),
    ("Orhan", "Pamuk", 1952, "2006 Nobel Edebiyat Ödülü sahibi Türk romancı."),
    ("Yaşar", "Kemal", 1923, "Çukurova'yı anlatan destansı romanlarıyla tanınır."),
    ("Ahmet Hamdi", "Tanpınar", 1901, "Şair, romancı ve edebiyat tarihçisi."),
    ("Oğuz", "Atay", 1934, "Türk edebiyatında modernist romanın öncüsü."),
    ("George", "Orwell", 1903, "İngiliz yazar ve gazeteci; distopya türünün ustası."),
    ("Fyodor", "Dostoyevski", 1821, "Rus edebiyatının psikolojik roman ustası."),
    ("J.R.R.", "Tolkien", 1892, "Modern fantastik edebiyatın babası sayılan İngiliz yazar."),
    ("Isaac", "Asimov", 1920, "Bilim kurgu ve popüler bilim alanında yüzlerce eser veren yazar."),
    ("Yuval Noah", "Harari", 1976, "İsrailli tarihçi; insanlık tarihi üzerine çok satan kitapları var."),
]

# (başlık, isbn, yıl, yayınevi, sayfa, dil, kategori_idx, yazar_idx, adet, özet)
KITAPLAR = [
    ("Kürk Mantolu Madonna", "9789753638029", 1943, "Yapı Kredi Yayınları", 160, "Türkçe", 0, 0, 1,
     "Raif Efendi'nin Berlin'de tanıştığı Maria Puder'e duyduğu sessiz ve derin aşkın hikâyesi."),
    ("İçimizdeki Şeytan", "9789753638036", 1940, "Yapı Kredi Yayınları", 272, "Türkçe", 0, 0, 2,
     "Ömer'in kendi zaaflarını 'içindeki şeytana' yüklemesini konu alan psikolojik roman."),
    ("Kuyucaklı Yusuf", "9789753638043", 1937, "Yapı Kredi Yayınları", 224, "Türkçe", 0, 0, 2,
     "Taşra kasabasında Yusuf ile Muazzez'in trajik aşkı."),
    ("Benim Adım Kırmızı", "9789750806544", 1998, "Yapı Kredi Yayınları", 472, "Türkçe", 0, 1, 3,
     "16. yüzyıl İstanbul'unda nakkaşlar arasında geçen polisiye ve sanat romanı."),
    ("Masumiyet Müzesi", "9789750816123", 2008, "Yapı Kredi Yayınları", 592, "Türkçe", 0, 1, 2,
     "Kemal'in Füsun'a olan takıntılı aşkını eşyalar üzerinden anlatan roman."),
    ("Kar", "9789750806209", 2002, "İletişim Yayınları", 432, "Türkçe", 0, 1, 2,
     "Kars'ta karla kapanan günlerde siyaset, din ve aşk üzerine bir roman."),
    ("İnce Memed", "9789750807145", 1955, "Yapı Kredi Yayınları", 436, "Türkçe", 0, 2, 3,
     "Ağaların zulmüne başkaldıran eşkıya Memed'in destansı öyküsü."),
    ("Yer Demir Gök Bakır", "9789750807152", 1963, "Yapı Kredi Yayınları", 384, "Türkçe", 0, 2, 1,
     "Toroslarda bir köyün borç, yoksulluk ve efsane yaratma sürecini anlatır."),
    ("Saatleri Ayarlama Enstitüsü", "9789759952129", 1961, "Dergâh Yayınları", 384, "Türkçe", 0, 3, 2,
     "Doğu-Batı ikilemini ironik bir dille ele alan kült roman."),
    ("Huzur", "9789759952136", 1949, "Dergâh Yayınları", 400, "Türkçe", 0, 3, 1,
     "Mümtaz ile Nuran'ın İstanbul'da geçen aşkı ve iç huzur arayışı."),
    ("Tutunamayanlar", "9789754700114", 1972, "İletişim Yayınları", 724, "Türkçe", 0, 4, 2,
     "Selim Işık'ın intiharının ardından Turgut Özben'in arayışı."),
    ("Tehlikeli Oyunlar", "9789754700121", 1973, "İletişim Yayınları", 488, "Türkçe", 0, 4, 1,
     "Hikmet Benol'un hayal ile gerçek arasında gidip gelen iç dünyası."),
    ("1984", "9789750718533", 1949, "Can Yayınları", 352, "Türkçe", 4, 5, 4,
     "Büyük Birader'in her şeyi gözetlediği totaliter bir dünyada Winston Smith'in başkaldırısı."),
    ("Hayvan Çiftliği", "9789750719387", 1945, "Can Yayınları", 152, "Türkçe", 4, 5, 3,
     "Devrimin nasıl yozlaştığını hayvanlar üzerinden anlatan alegorik roman."),
    ("Suç ve Ceza", "9789754587111", 1866, "İş Bankası Kültür Yayınları", 687, "Türkçe", 1, 6, 3,
     "Raskolnikov'un işlediği cinayet sonrası vicdani hesaplaşması."),
    ("Karamazov Kardeşler", "9789754587128", 1880, "İş Bankası Kültür Yayınları", 1016, "Türkçe", 1, 6, 2,
     "İnanç, ahlak ve özgür irade üzerine bir aile trajedisi."),
    ("Yeraltından Notlar", "9789754587135", 1864, "İş Bankası Kültür Yayınları", 160, "Türkçe", 1, 6, 2,
     "Toplumdan kopmuş bir adamın acı ve ironik itirafları."),
    ("Hobbit", "9789753421652", 1937, "İthaki Yayınları", 384, "Türkçe", 3, 7, 3,
     "Bilbo Baggins'in cüceler ve Gandalf ile çıktığı beklenmedik yolculuk."),
    ("Yüzüklerin Efendisi: Yüzük Kardeşliği", "9789753421669", 1954, "Metis Yayınları", 576, "Türkçe", 3, 7, 2,
     "Frodo ve arkadaşlarının Tek Yüzük'ü yok etmek için başlattığı yolculuk."),
    ("Vakıf", "9786053757818", 1951, "İthaki Yayınları", 288, "Türkçe", 2, 8, 2,
     "Galaktik İmparatorluğun çöküşünü öngören Hari Seldon ve psikotarih."),
    ("Ben, Robot", "9786053757825", 1950, "İthaki Yayınları", 304, "Türkçe", 2, 8, 2,
     "Robotiğin üç yasası etrafında kurgulanmış öyküler."),
    ("The Naked Sun", "9780553293395", 1957, "Bantam Spectra", 272, "İngilizce", 2, 8, 1,
     "Dedektif Elijah Baley ve robot R. Daneel Olivaw'ın Solaria'daki cinayet soruşturması."),
    ("Sapiens: Hayvanlardan Tanrılara", "9786055029371", 2011, "Kolektif Kitap", 412, "Türkçe", 5, 9, 3,
     "İnsan türünün bilişsel devrimden bugüne kısa tarihi."),
    ("Homo Deus: Yarının Kısa Bir Tarihi", "9786055029388", 2015, "Kolektif Kitap", 448, "Türkçe", 5, 9, 2,
     "İnsanlığın gelecekte ölümsüzlük, mutluluk ve tanrısallık arayışı."),
    ("21 Lessons for the 21st Century", "9780525512172", 2018, "Spiegel & Grau", 372, "İngilizce", 5, 9, 1,
     "Günümüzün en acil sorunları üzerine 21 deneme."),
]

RAF_ON_EKLERI = ["TR", "DK", "BK", "FN", "DS", "TB"]


def seed_olustur(db: Session) -> bool:
    """Veritabanı boşsa örnek verileri ekler. Ekleme yapıldıysa True döner."""
    if KullaniciRepository(db).sayi() > 0:
        return False

    bugun = date.today()
    db.add(Yonetici(
        ad="Sistem", soyad="Yöneticisi", email="admin@kutuphane.com", sifre_hash=sifre_hashle("Admin123!"),
        sicil_no="Y-0001", aktif_mi=True,
    ))
    uye_sifre = sifre_hashle("Uye123!")
    ahmet = Uye(ad="Ahmet", soyad="Yılmaz", email="ahmet@ogr.edu.tr", sifre_hash=uye_sifre,
                ogrenci_no="20230001", bolum="Bilgisayar Mühendisliği", telefon="05551112233", ceza_puani=0)
    ayse = Uye(ad="Ayşe", soyad="Demir", email="ayse@ogr.edu.tr", sifre_hash=uye_sifre,
               ogrenci_no="20230002", bolum="Türk Dili ve Edebiyatı", telefon="05552223344", ceza_puani=0)
    mehmet = Uye(ad="Mehmet", soyad="Kaya", email="mehmet@ogr.edu.tr", sifre_hash=uye_sifre,
                 ogrenci_no="20230003", bolum="Tarih", telefon="05553334455", ceza_puani=0)
    db.add_all([ahmet, ayse, mehmet])

    kategoriler = [Kategori(ad=ad) for ad in KATEGORILER]
    yazarlar = [Yazar(ad=a, soyad=s, dogum_yili=y, biyografi=b) for a, s, y, b in YAZARLAR]
    db.add_all(kategoriler + yazarlar)

    kitaplar: dict[str, Kitap] = {}
    for i, (baslik, isbn, yil, yayinevi, sayfa, dil, k_idx, y_idx, adet, ozet) in enumerate(KITAPLAR, start=1):
        kitap = Kitap(
            baslik=baslik, isbn=isbn, yayin_yili=yil, yayinevi=yayinevi, sayfa_sayisi=sayfa, dil=dil,
            raf_kodu=f"{RAF_ON_EKLERI[k_idx]}-{i:03d}", toplam_adet=adet, mevcut_adet=adet, ozet=ozet,
            kategori=kategoriler[k_idx], yazarlar=[yazarlar[y_idx]],
        )
        kitaplar[baslik] = kitap
        db.add(kitap)

    def odunc(uye: Uye, baslik: str, alis_once: int, iade_once: int | None = None) -> None:
        kitap = kitaplar[baslik]
        alis = bugun - timedelta(days=alis_once)
        son = alis + timedelta(days=ayarlar.odunc_suresi_gun)
        o = Odunc(uye=uye, kitap=kitap, alis_tarihi=alis, son_iade_tarihi=son,
                  durum=OduncDurumu.AKTIF, gecikme_gunu=0, ceza_tutari=0.0, uzatma_sayisi=0)
        if iade_once is None:
            kitap.mevcut_adet -= 1
        else:
            o.iade_et(bugun - timedelta(days=iade_once))
            uye.ceza_puani += o.gecikme_gunu
        db.add(o)

    # Aktif ödünçler
    odunc(ahmet, "1984", 5)
    odunc(ahmet, "Sapiens: Hayvanlardan Tanrılara", 10)
    odunc(ayse, "Tutunamayanlar", 3)
    # Gecikmiş ödünçler
    odunc(ayse, "Kürk Mantolu Madonna", 20)
    odunc(mehmet, "Vakıf", 25)
    # İade edilmiş ödünçler (biri gecikmeli → ceza)
    odunc(ahmet, "Suç ve Ceza", 40, iade_once=28)
    odunc(ahmet, "Hobbit", 50, iade_once=30)
    odunc(mehmet, "Benim Adım Kırmızı", 30, iade_once=18)
    odunc(ayse, "1984", 60, iade_once=47)
    odunc(mehmet, "1984", 45, iade_once=33)

    # Stokta olmayan kitap için bekleyen rezervasyon
    db.add(Rezervasyon(uye=mehmet, kitap=kitaplar["Kürk Mantolu Madonna"],
                       tarih=datetime.now() - timedelta(days=2), durum=RezervasyonDurumu.BEKLIYOR))
    db.commit()
    gecikmeleri_guncelle(db)
    return True
