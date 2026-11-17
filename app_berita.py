import streamlit as st
import feedparser
import base64
import glob
import re
import random
from datetime import datetime, timedelta, timezone
from time import mktime
import google.generativeai as genai

st.set_page_config(
    page_title="Nortisce Gaming News Database",
    page_icon="🎮",
    layout="wide"
)

# Mengambil daftar banyak API Key dari Streamlit Secrets
daftar_api_keys = []
if "GEMINI_API_KEYS" in st.secrets:
    daftar_api_keys = list(st.secrets["GEMINI_API_KEYS"])
elif "GEMINI_API_KEY" in st.secrets:
    daftar_api_keys = [st.secrets["GEMINI_API_KEY"]]

def get_chunli_bg():
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
        for file in glob.glob(ext):
            if "chunli" in file.lower():
                mime = "image/png" if file.lower().endswith(".png") else ("image/webp" if file.lower().endswith(".webp") else "image/jpeg")
                with open(file, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode(), mime
    return "", ""

sidebar_bg_base64, img_mime = get_chunli_bg()

if sidebar_bg_base64:
    sidebar_css = (
        '[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {'
        f'    background-image: linear-gradient(rgba(10, 15, 30, 0.55), rgba(10, 15, 30, 0.75)), url("data:{img_mime};base64,{sidebar_bg_base64}") !important;'
        '    background-size: cover !important; background-position: center 15% !important; background-repeat: no-repeat !important;'
        '}'
    )
else:
    sidebar_css = '[data-testid="stSidebar"] { background-color: rgba(15, 20, 35, 0.9) !important; }'

custom_ui = (
    '<style>'
    '.stApp { background-image: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), url("https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1920&auto=format&fit=crop"); background-size: cover; background-position: center; background-attachment: fixed; }'
    + sidebar_css +
    'header[data-testid="stHeader"] { background-color: transparent !important; }'
    '.metal-slug-banner { position: fixed; top: 0; left: 0; width: 100%; height: 60px; overflow: hidden; pointer-events: none; z-index: 999990; }'
    '@keyframes patrolShoot { 0% { left: -60px; transform: scaleX(1); } 47% { left: calc(100% - 210px); transform: scaleX(1); } 50% { left: calc(100% - 210px); transform: scaleX(-1); } 97% { left: -60px; transform: scaleX(-1); } 100% { left: -60px; transform: scaleX(1); } }'
    '@keyframes runBounce { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-3px); } }'
    '@keyframes legLeft { 0%, 100% { transform: translateX(0px); } 50% { transform: translateX(3px); } }'
    '@keyframes legRight { 0%, 100% { transform: translateX(0px); } 50% { transform: translateX(-3px); } }'
    '@keyframes muzzleFlash { 0%, 100% { opacity: 0; } 50% { opacity: 1; } }'
    '.metal-slug-runner { position: absolute; top: 6px; width: 60px; height: 50px; animation: patrolShoot 12s linear infinite; }'
    '.sprite-body { width: 100%; height: 100%; animation: runBounce 0.2s infinite; }'
    '.leg-l { animation: legLeft 0.2s infinite; } .leg-r { animation: legRight 0.2s infinite; } .flash { animation: muzzleFlash 0.12s infinite; }'
    '@keyframes bulletStream1 { 0% { opacity: 1; transform: translateX(0px); } 100% { opacity: 0; transform: translateX(260px); } }'
    '@keyframes bulletStream2 { 0% { opacity: 0; transform: translateX(0px); } 40% { opacity: 1; transform: translateX(80px); } 100% { opacity: 0; transform: translateX(260px); } }'
    '.bullet-1, .bullet-2 { position: absolute; top: 23px; left: 44px; width: 16px; height: 3px; background: #fff200; box-shadow: 0 0 6px #ff6600, 0 0 10px #ff0000; border-radius: 2px; }'
    '.bullet-1 { animation: bulletStream1 0.3s linear infinite; } .bullet-2 { animation: bulletStream2 0.3s linear infinite; }'
    'div.stContainer { background-color: rgba(15, 20, 35, 0.75); padding: 15px; border-radius: 10px; border: 1px solid rgba(255, 120, 0, 0.3); margin-bottom: 10px; }'
    '</style>'
    '<div class="metal-slug-banner"><div class="metal-slug-runner"><div class="sprite-body">'
    '<svg viewBox="0 0 16 16" width="46" height="46" shape-rendering="crispEdges">'
    '<rect x="4" y="1" width="6" height="2" fill="#8B4513"/><rect x="4" y="3" width="7" height="1" fill="#FF0000"/><rect x="2" y="3" width="2" height="2" fill="#FF0000"/>'
    '<rect x="5" y="4" width="5" height="3" fill="#FFCC99"/><rect x="8" y="4" width="1" height="1" fill="#000000"/><rect x="4" y="7" width="6" height="4" fill="#F0F0F0"/>'
    '<rect x="5" y="7" width="4" height="4" fill="#3A5F0B"/><rect x="6" y="8" width="8" height="2" fill="#222222"/><rect x="7" y="9" width="2" height="2" fill="#555555"/>'
    '<polygon class="flash" points="14,7 16,9 14,11" fill="#FFAA00"/>'
    '<g class="leg-l"><rect x="4" y="11" width="2" height="3" fill="#2F4F4F"/><rect x="3" y="14" width="3" height="2" fill="#4A2E1B"/></g>'
    '<g class="leg-r"><rect x="8" y="11" width="2" height="3" fill="#2F4F4F"/><rect x="8" y="14" width="3" height="2" fill="#4A2E1B"/></g>'
    '</svg></div><div class="bullet-1"></div><div class="bullet-2"></div></div></div>'
)
st.markdown(custom_ui, unsafe_allow_html=True)

st.title("🎮 Nortisce Gaming News Database")
st.markdown("Database berita game terkini dari **20 kanal global + 8 kanal lokal terbaik** lengkap dengan filter, pencarian, dan analisis AI Gemini.")

RSS_SOURCES = {
    # --- 20 Kanal Global ---
    "IGN": "https://feeds.feedburner.com/ign/games-all",
    "GameSpot": "https://www.gamespot.com/feeds/news/",
    "Gematsu": "https://www.gematsu.com/feed",
    "Nintendo Life": "https://nintendolive.com/feed",
    "Eurogamer": "https://www.eurogamer.net/feed",
    "PC Gamer": "https://www.pcgamer.com/rss/",
    "Destructoid": "https://www.destructoid.com/feed/",
    "Kotaku": "https://kotaku.com/feed",
    "Polygon": "https://www.polygon.com/rss/index.xml",
    "Push Square": "https://www.pushsquare.com/feed",
    "Pure Xbox": "https://www.purexbox.com/feed",
    "GamesIndustry.biz": "https://www.gamesindustry.biz/feed",
    "VG247": "https://www.vg247.com/feed",
    "Pocket Gamer": "https://www.pocketgamer.com/rss/news.xml",
    "TouchArcade": "https://toucharcade.com/feed/",
    "Anime Senpai": "https://animesenpai.com/feed/",
    "ResetEra": "https://www.resetera.com/index.rss",
    "DualShockers": "https://www.dualshockers.com/feed/",
    "Wccftech": "https://wccftech.com/feed",
    "Rock Paper Shotgun": "https://www.rockpapershotgun.com/feed",

    # --- 8 Kanal Lokal Indonesia ---
    "IDN Times Game": "https://news.google.com/rss/search?q=site:idntimes.com+game&hl=id&gl=ID&ceid=ID:id",
    "GGWP ID": "https://news.google.com/rss/search?q=site:ggwp.id+game&hl=id&gl=ID&ceid=ID:id",
    "Hybrid Indonesia": "https://news.google.com/rss/search?q=site:hybrid.co.id+game&hl=id&gl=ID&ceid=ID:id",
    "Jagat Play": "https://news.google.com/rss/search?q=site:jagatplay.com+game&hl=id&gl=ID&ceid=ID:id",
    "KotakGame": "https://news.google.com/rss/search?q=site:kotakgame.com+game&hl=id&gl=ID&ceid=ID:id",
    "Kincir Game": "https://news.google.com/rss/search?q=site:kincir.com+game&hl=id&gl=ID&ceid=ID:id",
    "Indogamers": "https://news.google.com/rss/search?q=site:indogamers.com+game&hl=id&gl=ID&ceid=ID:id",
    "RevivalTV": "https://news.google.com/rss/search?q=site:revivaltv.id+game&hl=id&gl=ID&ceid=ID:id"
}

def bersihkan_html(teks):
    teks_bersih = re.sub(r'<[^>]+>', ' ', teks)
    return re.sub(r'\s+', ' ', teks_bersih).strip()[:600]

@st.cache_data(ttl=3600)
def muat_data_berita():
    semua_berita = []
    sekarang_utc = datetime.now(timezone.utc)
    batas_waktu = sekarang_utc - timedelta(days=7)

    for nama_web, u in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(u)
            for entry in feed.entries:
                raw_desc = getattr(entry, 'summary', entry.title)
                clean_desc = bersihkan_html(raw_desc)
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_dt = datetime.fromtimestamp(mktime(entry.published_parsed), timezone.utc)
                    if pub_dt >= batas_waktu:
                        selisih_jam = (sekarang_utc - pub_dt).total_seconds() / 3600
                        selisih_hari = int(selisih_jam // 24)
                        label_waktu = "Today (Hari Ini)" if selisih_jam < 24 else ("1 Day Ago (Kemarin)" if selisih_hari == 1 else f"{selisih_hari} Days Ago")
                        info = {
                            "judul": entry.title, "link": entry.link, "sumber": nama_web,
                            "tanggal": pub_dt.strftime("%d %b %Y, %H:%M"),
                            "rentang_waktu": label_waktu, "selisih_hari": selisih_hari,
                            "deskripsi": clean_desc
                        }
                        if info not in semua_berita:
                            semua_berita.append(info)
        except Exception:
            pass
    return semua_berita

@st.cache_data(show_spinner=False)
def analisis_gemini_multi_key(keys_tuple, mode, judul, sumber, deskripsi):
    if mode == "ringkas":
        prompt = (
            f"Sebagai analis industri game, bedah esensi berita dari {sumber} berikut secara tajam, unik, dan mendalam dalam 3 kalimat bahasa Indonesia (tanpa basa-basi pembuka):\n"
            f"Judul: {judul}\nKonteks: {deskripsi}"
        )
    else:
        prompt = (
            f"As a gaming community observer, determine public sentiment (Positive / Negative / Neutral) and its sharp reasoning in 2-3 sentences of Indonesian for this news:\n"
            f"Title: {judul}\nContext: {deskripsi}"
        )

    catatan_error = []
    for idx, key in enumerate(keys_tuple, start=1):
        if not key or not key.strip():
            continue
        try:
            genai.configure(api_key=key.strip())
            model = genai.GenerativeModel('gemini-3.8-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            catatan_error.append(f"Key #{idx}: {e}")
            continue

    raise Exception(" | ".join(catatan_error) if catatan_error else "Daftar API Key kosong")

# --- LOGIKA GAME TIC-TAC-TOE ---
def cek_pemenang_ttt(papan):
    pola_menang = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]
    for a, b, c in pola_menang:
        if papan[a] != "" and papan[a] == papan[b] == papan[c]:
            return papan[a]
    if "" not in papan:
        return "Seri"
    return None

def langkah_bot_ttt(papan):
    kosong = [i for i, v in enumerate(papan) if v == ""]
    if not kosong:
        return None
    for i in kosong:
        salinan = papan.copy()
        salinan[i] = "O"
        if cek_pemenang_ttt(salinan) == "O":
            return i
    for i in kosong:
        salinan = papan.copy()
        salinan[i] = "X"
        if cek_pemenang_ttt(salinan) == "X":
            return i
    if 4 in kosong:
        return 4
    return random.choice(kosong)

if st.sidebar.button("🔄 Refresh / Bersihkan Cache Berita"):
    st.cache_data.clear()
    st.rerun()

with st.spinner("⏳ Menyerok berita dari 28 server (Global & Lokal)..."):
    semua_berita = muat_data_berita()

st.success(f"Berhasil mengumpulkan {len(semua_berita)} berita segar dalam 7 hari terakhir! (28 Kanal Media)")

st.sidebar.header("🎛️ Panel Filter Konten")
search_keyword = st.sidebar.text_input("🔍 Cari Judul / Topik Game:", "").lower()

pilih_kategori = st.sidebar.selectbox(
    "📂 Pilih Kategori Berita:",
    ["Semua Kategori", "🎮 Game Releases & Updates", "🛠️ Tech, Hardware & Performance", "🏢 Industry & Business", "🏆 Esports & Competitive", "🍿 Pop Culture, Media & Leaks", "📌 Lainnya"]
)

pilih_web = st.sidebar.selectbox("🌐 Pilih Sumber Website:", ["Semua Website (28 Media)"] + list(RSS_SOURCES.keys()))
pilih_waktu = st.sidebar.selectbox("⏰ Pilih Rentang Waktu:", ["Semua Rentang Waktu (7 Hari Terakhir)", "Today (Hari Ini)", "1 Day Ago (Kemarin)", "2 Days Ago", "3 Days Ago", "4-7 Days Ago"])

# --- MINI-GAME TIC-TAC-TOE ---
st.sidebar.markdown("---")
st.sidebar.subheader("🕹️ Mini-Game: Tic-Tac-Toe")
st.sidebar.caption("Kamu (**❌**) vs Bot (**⭕**)")

if "ttt_board" not in st.session_state:
    st.session_state.ttt_board = [""] * 9
if "ttt_winner" not in st.session_state:
    st.session_state.ttt_winner = None

def klik_kotak_ttt(idx):
    if st.session_state.ttt_board[idx] == "" and st.session_state.ttt_winner is None:
        st.session_state.ttt_board[idx] = "X"
        hasil = cek_pemenang_ttt(st.session_state.ttt_board)
        if hasil:
            st.session_state.ttt_winner = hasil
        else:
            bot_idx = langkah_bot_ttt(st.session_state.ttt_board)
            if bot_idx is not None:
                st.session_state.ttt_board[bot_idx] = "O"
                st.session_state.ttt_winner = cek_pemenang_ttt(st.session_state.ttt_board)

for row in range(3):
    cols = st.sidebar.columns(3)
    for col in range(3):
        idx = row * 3 + col
        val = st.session_state.ttt_board[idx]
        label = "❌" if val == "X" else ("⭕" if val == "O" else " ")
        cols[col].button(
            label,
            key=f"ttt_cell_{idx}",
            on_click=klik_kotak_ttt,
            args=(idx,),
            use_container_width=True,
            disabled=(val != "" or st.session_state.ttt_winner is not None)
        )

if st.session_state.ttt_winner == "X":
    st.sidebar.success("🎉 Mantap! Kamu Menang!")
elif st.session_state.ttt_winner == "O":
    st.sidebar.error("🤖 Bot Menang! Coba lagi!")
elif st.session_state.ttt_winner == "Seri":
    st.sidebar.warning("🤝 Hasil Seri!")

if st.sidebar.button("🔁 Main Ulang Tic-Tac-Toe", use_container_width=True):
    st.session_state.ttt_board = [""] * 9
    st.session_state.ttt_winner = None
    st.rerun()

# --- FILTER & TAMPILAN BERITA ---
kategori = {k: [] for k in ["🎮 Game Releases & Updates", "🛠️ Tech, Hardware & Performance", "🏢 Industry & Business", "🏆 Esports & Competitive", "🍿 Pop Culture, Media & Leaks", "📌 Lainnya"]}
keywords = {
    "🎮 Game Releases & Updates": ["release", "launch", "update", "patch", "dlc", "expansion", "out now", "beta", "season", "gameplay", "review"],
    "🛠️ Tech, Hardware & Performance": ["rtx", "gtx", "gpu", "cpu", "amd", "nvidia", "intel", "ps5 pro", "switch 2", "hardware", "monitor", "fps", "steam deck"],
    "🏢 Industry & Business": ["acquire", "acquisition", "layoffs", "studio", "sales", "revenue", "sony", "nintendo", "microsoft", "xbox", "epic games", "valve"],
    "🏆 Esports & Competitive": ["esports", "tournament", "championship", "valorant", "pro player", "meta", "nerf", "buff"],
    "🍿 Pop Culture, Media & Leaks": ["movie", "series", "adaption", "trailer", "leak", "rumor", "hbo", "netflix"]
}

berita_terfilter = []
for item in semua_berita:
    sw = item["selisih_hari"]
    waktu_cocok = (
        pilih_waktu == "Semua Rentang Waktu (7 Hari Terakhir)" or
        (pilih_waktu == "Today (Hari Ini)" and item["rentang_waktu"] == "Today (Hari Ini)") or
        (pilih_waktu == "1 Day Ago (Kemarin)" and item["rentang_waktu"] == "1 Day Ago (Kemarin)") or
        (pilih_waktu == "2 Days Ago" and sw == 2) or
        (pilih_waktu == "3 Days Ago" and sw == 3) or
        (pilih_waktu == "4-7 Days Ago" and (4 <= sw <= 7))
    )
    web_cocok = (pilih_web == "Semua Website (28 Media)") or (item["sumber"] == pilih_web)
    search_cocok = (search_keyword in item["judul"].lower()) or (search_keyword in item["sumber"].lower()) if search_keyword else True

    if waktu_cocok and web_cocok and search_cocok:
        berita_terfilter.append(item)

for item in berita_terfilter:
    judul_lower = item["judul"].lower()
    masuk = False
    for kat, keys in keywords.items():
        if any(k in judul_lower for k in keys):
            kategori[kat].append(item)
            masuk = True
            break
    if not masuk:
        kategori["📌 Lainnya"].append(item)

target_tampil = kategori.items() if pilih_kategori == "Semua Kategori" else [(pilih_kategori, kategori[pilih_kategori])]

st.markdown("---")
total_ditampilkan = sum(len(daftar) for _, daftar in target_tampil)
st.info(f"Menampilkan **{total_ditampilkan} berita** | Kategori: **{pilih_kategori}** | Sumber: **{pilih_web}**")

for kat, daftar in target_tampil:
    if daftar:
        st.markdown(f"### {kat} ({len(daftar)} Berita)")
        for idx, b in enumerate(daftar):
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{b['judul']}**")
                    st.caption(f"🌐 **{b['sumber']}** | 📅 {b['tanggal']} ({b['rentang_waktu']})")
                with col2:
                    st.markdown(f"[🔗 Buka Berita]({b['link']})")
                
                expander_key = f"exp_{kat}_{idx}_{b['judul'][:15]}"
                with st.expander("✨ Ringkasan AI & Analisis Sentimen Publik"):
                    col_btn1, col_btn2 = st.columns(2)
                    
                    if col_btn1.button("📝 Ringkas Artikel", key=f"btn_sum_{expander_key}"):
                        if not daftar_api_keys:
                            st.warning("⚠️ API Key belum dikonfigurasi di Streamlit Secrets.")
                        else:
                            with st.spinner("Menganalisis..."):
                                try:
                                    hasil = analisis_gemini_multi_key(tuple(daftar_api_keys), "ringkas", b['judul'], b['sumber'], b['deskripsi'])
                                    st.success(hasil)
                                except Exception as e:
                                    st.error(f"Detail kendala: {e}")
                            
                    if col_btn2.button("📊 Cek Sentimen Publik", key=f"btn_sent_{expander_key}"):
                        if not daftar_api_keys:
                            st.warning("⚠️ API Key belum dikonfigurasi di Streamlit Secrets.")
                        else:
                            with st.spinner("Memindai sentimen..."):
                                try:
                                    hasil = analisis_gemini_multi_key(tuple(daftar_api_keys), "sentimen", b['judul'], b['sumber'], b['deskripsi'])
                                    st.info(hasil)
                                except Exception as e:
                                    st.error(f"Detail kendala: {e}")
