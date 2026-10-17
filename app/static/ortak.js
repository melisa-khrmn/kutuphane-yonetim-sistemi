// Ortak yardımcılar: API istemcisi, oturum, toast, gezinme çubuğu
const API = "/api";

const Oturum = {
  token: () => localStorage.getItem("token"),
  kullanici: () => JSON.parse(localStorage.getItem("kullanici") || "null"),
  kaydet(token, kullanici) {
    localStorage.setItem("token", token);
    localStorage.setItem("kullanici", JSON.stringify(kullanici));
  },
  cikis() {
    localStorage.removeItem("token");
    localStorage.removeItem("kullanici");
    location.href = "/";
  },
  yoneticiMi: () => Oturum.kullanici()?.rol === "YONETICI",
  uyeMi: () => Oturum.kullanici()?.rol === "UYE",
};

// Fetch sarmalayıcı: JSON gönderir, hata mesajını Türkçe fırlatır
async function api(yol, { method = "GET", govde, sessiz = false } = {}) {
  const basliklar = { "Content-Type": "application/json" };
  if (Oturum.token()) basliklar["Authorization"] = "Bearer " + Oturum.token();
  let yanit;
  try {
    yanit = await fetch(API + yol, { method, headers: basliklar, body: govde ? JSON.stringify(govde) : undefined });
  } catch (e) {
    throw new Error("Sunucuya ulaşılamadı.");
  }
  let veri = null;
  try { veri = await yanit.json(); } catch (_) {}
  if (!yanit.ok) {
    if (yanit.status === 401 && Oturum.token()) {
      toast("Oturumunuzun süresi doldu, lütfen tekrar giriş yapın.", "hata");
      setTimeout(Oturum.cikis, 1200);
    }
    const mesaj = typeof veri?.detail === "string" ? veri.detail : "İşlem başarısız (" + yanit.status + ")";
    throw new Error(mesaj);
  }
  return veri;
}

function toast(mesaj, tur = "basari") {
  let kutu = document.getElementById("toast-kutusu");
  if (!kutu) {
    kutu = document.createElement("div");
    kutu.id = "toast-kutusu";
    document.body.appendChild(kutu);
  }
  const t = document.createElement("div");
  t.className = "toast toast-" + tur;
  t.textContent = mesaj;
  kutu.appendChild(t);
  setTimeout(() => { t.style.opacity = "0"; t.style.transition = "opacity .3s"; }, 3500);
  setTimeout(() => t.remove(), 3900);
}

// Hata yakalayan kısa yardımcı
async function dene(fn, basariMesaji) {
  try {
    const sonuc = await fn();
    if (basariMesaji) toast(typeof basariMesaji === "function" ? basariMesaji(sonuc) : basariMesaji, "basari");
    return sonuc;
  } catch (e) {
    toast(e.message, "hata");
    return null;
  }
}

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function tarih(t) {
  if (!t) return "—";
  const d = new Date(t.length <= 10 ? t + "T00:00:00" : t);
  return d.toLocaleDateString("tr-TR", { day: "2-digit", month: "short", year: "numeric" });
}

const TL = (n) => (n || 0).toLocaleString("tr-TR", { style: "currency", currency: "TRY" });

const RENKLER = [
  ["#6366f1", "#8b5cf6"], ["#0ea5e9", "#2563eb"], ["#f59e0b", "#ef4444"], ["#10b981", "#0d9488"],
  ["#ec4899", "#8b5cf6"], ["#64748b", "#334155"], ["#f97316", "#db2777"], ["#14b8a6", "#6366f1"],
];

function kapakHtml(kitap, ekSinif = "") {
  if (kitap.kapak_url) {
    return `<div class="kapak ${ekSinif}" style="background-image:url('${esc(kitap.kapak_url)}')"></div>`;
  }
  const [a, b] = RENKLER[kitap.id % RENKLER.length];
  return `<div class="kapak ${ekSinif}" style="background:linear-gradient(135deg, ${a}, ${b})">
            <span class="text-sm">${esc(kitap.baslik)}</span></div>`;
}

function musaitlikRozeti(k) {
  if (k.mevcut_adet > 0) return `<span class="rozet rozet-yesil">● Müsait (${k.mevcut_adet}/${k.toplam_adet})</span>`;
  return `<span class="rozet rozet-kirmizi">● Tükendi${k.bekleyen_rezervasyon ? " · " + k.bekleyen_rezervasyon + " rezervasyon" : ""}</span>`;
}

const DURUM_ROZET = {
  AKTIF: '<span class="rozet rozet-mavi">Aktif</span>',
  GECIKMIS: '<span class="rozet rozet-kirmizi">Gecikmiş</span>',
  IADE_EDILDI: '<span class="rozet rozet-gri">İade edildi</span>',
  BEKLIYOR: '<span class="rozet rozet-sari">Bekliyor</span>',
  KARSILANDI: '<span class="rozet rozet-yesil">Karşılandı</span>',
  IPTAL: '<span class="rozet rozet-gri">İptal</span>',
};

function navbarCiz(aktif) {
  const k = Oturum.kullanici();
  const link = (href, ad, anahtar) =>
    `<a href="${href}" class="px-3 py-2 rounded-md text-sm font-medium ${aktif === anahtar ? "bg-indigo-700 text-white" : "text-indigo-100 hover:bg-indigo-500"}">${ad}</a>`;
  let linkler = link("/static/kitaplar.html", "📚 Katalog", "katalog");
  if (k?.rol === "UYE") linkler += link("/static/uye.html", "👤 Panelim", "uye");
  if (k?.rol === "YONETICI") linkler += link("/static/yonetici.html", "🛠️ Yönetim", "yonetici");
  const sag = k
    ? `<span class="hidden sm:inline text-indigo-100 text-sm">${esc(k.ad)} ${esc(k.soyad)} <span class="rozet bg-indigo-800 text-indigo-100 ml-1">${k.rol === "YONETICI" ? "Yönetici" : "Üye"}</span></span>
       <button onclick="Oturum.cikis()" class="btn btn-kucuk bg-white/10 text-white hover:bg-white/20">Çıkış</button>`
    : `<a href="/" class="btn btn-kucuk bg-white text-indigo-700">Giriş Yap</a>`;
  const nav = document.createElement("nav");
  nav.className = "bg-indigo-600 shadow";
  nav.innerHTML = `
    <div class="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-3">
      <a href="/static/kitaplar.html" class="flex items-center gap-2 text-white font-bold text-lg">🏛️ <span>Üniversite Kütüphanesi</span></a>
      <div class="flex items-center gap-1 flex-wrap">${linkler}</div>
      <div class="flex items-center gap-3">${sag}</div>
    </div>`;
  document.body.prepend(nav);
}

// Sayfa erişim koruması
function korumaGerekli(rol) {
  const k = Oturum.kullanici();
  if (!k || !Oturum.token()) { location.href = "/"; return false; }
  if (rol && k.rol !== rol) { location.href = k.rol === "YONETICI" ? "/static/yonetici.html" : "/static/uye.html"; return false; }
  return true;
}

// Basit modal
function modalAc(baslik, icerikHtml, kaydetFn, kaydetMetni = "Kaydet") {
  const arka = document.createElement("div");
  arka.className = "modal-arka";
  arka.innerHTML = `
    <div class="kart w-full max-w-2xl max-h-[90vh] overflow-y-auto">
      <div class="flex items-center justify-between px-5 py-4 border-b">
        <h3 class="font-bold text-lg">${baslik}</h3>
        <button class="text-slate-400 hover:text-slate-700 text-2xl leading-none" data-kapat>&times;</button>
      </div>
      <form class="p-5 space-y-4">${icerikHtml}
        <div class="flex justify-end gap-2 pt-2">
          <button type="button" class="btn btn-ikincil" data-kapat>Vazgeç</button>
          <button type="submit" class="btn btn-ana">${kaydetMetni}</button>
        </div>
      </form>
    </div>`;
  const kapat = () => arka.remove();
  arka.querySelectorAll("[data-kapat]").forEach((b) => (b.onclick = kapat));
  arka.addEventListener("click", (e) => { if (e.target === arka) kapat(); });
  arka.querySelector("form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.submitter; if (btn) btn.disabled = true;
    const ok = await kaydetFn(new FormData(e.target), e.target);
    if (btn) btn.disabled = false;
    if (ok !== false) kapat();
  });
  document.body.appendChild(arka);
  arka.querySelector("input,select,textarea")?.focus();
  return arka;
}

function onayla(mesaj) { return window.confirm(mesaj); }

// Katalog işlemleri (katalog ve detay sayfası ortak)
async function oduncAl(kitapId, sonra) {
  if (!Oturum.token()) { toast("Ödünç almak için giriş yapın.", "bilgi"); setTimeout(() => (location.href = "/"), 900); return; }
  const r = await dene(() => api("/oduncler", { method: "POST", govde: { kitap_id: kitapId } }),
    (o) => `"${o.kitap_baslik}" ödünç alındı. Son iade: ${tarih(o.son_iade_tarihi)}`);
  if (r && sonra) sonra();
}

async function rezerveEt(kitapId, sonra) {
  if (!Oturum.token()) { toast("Rezervasyon için giriş yapın.", "bilgi"); setTimeout(() => (location.href = "/"), 900); return; }
  const r = await dene(() => api("/rezervasyonlar", { method: "POST", govde: { kitap_id: kitapId } }),
    (x) => `Rezervasyon oluşturuldu. Sıranız: ${x.sira}`);
  if (r && sonra) sonra();
}
