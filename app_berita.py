import base64
from collections import Counter
from datetime import datetime, timedelta, timezone
import glob
import random
import re
from time import mktime
import feedparser
import google.generativeai as genai
import streamlit as st

st.set_page_config(
    page_title="Nortisce Gaming News Database", page_icon="🎮", layout="wide"
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
        mime = (
            "image/png"
            if file.lower().endswith(".png")
            else (
                "image/webp" if file.lower().endswith(".webp") else "image/jpeg"
            )
        )
        with open(file, "rb") as img_file:
          return base64.b64encode(img_file.read()).decode(), mime
  return "", ""


sidebar_bg_base64, img_mime = get_chunli_bg()

if sidebar_bg_base64:
  sidebar_css = (
      '[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {'
      f' background-image: linear-gradient(rgba(10, 15, 30, 0.70), rgba(10, 15, 30, 0.85)), url("data:{img_mime};base64,{sidebar_bg_base64}") !important;'
      " background-size: cover !important; background-position: center 15%"
      " !important; background-repeat: no-repeat !important;"
      "}"
  )
else:
  sidebar_css = (
      '[data-testid="stSidebar"] { background-color: rgba(15, 20, 35, 0.95)'
      " !important; }"
  )

# Cek status buka/tutup sidebar via session_state
if "sidebar_open" not in st.session_state:
  st.session_state.sidebar_open = False

# Tangkap parameter URL query untuk buka/tutup sidebar
query_params = st.query_params
if "toggle_sidebar" in query_params:
  val = query_params["toggle_sidebar"]
  st.session_state.sidebar_open = val == "1"
  st.rerun()

sidebar_left_pos = "0px" if st.session_state.sidebar_open else "-300px"

# --- CLEAN GAMING UI CSS + PC CLICK-OUTSIDE OVERLAY ---
custom_ui = (
    "<style>"
    ".stApp { background-image:"
    " linear-gradient(rgba(8, 12, 20, 0.85), rgba(8, 12, 20, 0.92)),"
    ' url("https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1920&auto=format&fit=crop");'
    " background-size: cover; background-position: center;"
    " background-attachment: fixed; }"
    + sidebar_css
    + 'header[data-testid="stHeader"] { background-color: transparent'
    " !important; }"
    # --- POSISI & ANIMASI SIDEBAR ---
    '[data-testid="stSidebar"] {'
    " position: fixed !important;"
    " top: 0 !important;"
    f" left: {sidebar_left_pos} !important;"
    " width: 300px !important;"
    " height: 100vh !important;"
    " z-index: 999999 !important;"
    " transition: left 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;"
    " box-shadow: 5px 0 25px rgba(0, 0, 0, 0.8) !important;"
    " border-right: 1px solid rgba(56, 189, 248, 0.4) !important;"
    "}"
    # --- LAPISAN OVERLAY KHUSUS PC (DI LUAR 300px SIDEBAR) ---
    + (
        "\n@media (min-width: 768px) {\n"
        " .pc-sidebar-overlay {\n"
        " position: fixed;\n"
        " top: 0;\n"
        " left: 300px;\n"
        " width: calc(100vw - 300px);\n"
        " height: 100vh;\n"
        " z-index: 999995;\n"
        " background: transparent;\n"
        " }\n"
        "}\n"
        if st.session_state.sidebar_open
        else ""
    )
    + "# Metal Slug Runner Animation Banner"
    ".metal-slug-banner { position: fixed; top: 0; left: 0; width: 100%; height:"
    " 50px; overflow: hidden; pointer-events: none; z-index: 999990; }"
    "@keyframes patrolShoot { 0% { left: -60px; transform: scaleX(1); } 47% {"
    " left: calc(100% - 210px); transform: scaleX(1); } 50% { left: calc(100%"
    " - 210px); transform: scaleX(-1); } 97% { left: -60px; transform:"
    " scaleX(-1); } 100% { left: -60px; transform: scaleX(1); } }"
    "@keyframes runBounce { 0%, 100% { transform: translateY(0px); } 50% {"
    " transform: translateY(-3px); } }"
    "@keyframes legLeft { 0%, 100% { transform: translateX(0px); } 50% {"
    " transform: translateX(3px); } }"
    "@keyframes legRight { 0%, 100% { transform: translateX(0px); } 50% {"
    " transform: translateX(-3px); } }"
    "@keyframes muzzleFlash { 0%, 100% { opacity: 0; } 50% { opacity: 1; } }"
    ".metal-slug-runner { position: absolute; top: 4px; width: 60px; height:"
    " 45px; animation: patrolShoot 14s linear infinite; }"
    ".sprite-body { width: 100%; height: 100%; animation: runBounce 0.2s"
    " infinite; }"
    ".leg-l { animation: legLeft 0.2s infinite; } .leg-r { animation: legRight"
    " 0.2s infinite; } .flash { animation: muzzleFlash 0.12s infinite; }"
    "@keyframes bulletStream1 { 0% { opacity: 1; transform: translateX(0px); }"
    " 100% { opacity: 0; transform: translateX(260px); } }"
    "@keyframes bulletStream2 { 0% { opacity: 0; transform: translateX(0px);"
    " } 40% { opacity: 1; transform: translateX(80px); } 100% { opacity: 0;"
    " transform: translateX(260px); } }"
    ".bullet-1, .bullet-2 { position: absolute; top: 20px; left: 44px; width:"
    " 14px; height: 2px; background: #38bdf8; box-shadow: 0 0 6px #0284c7, 0 0"
    " 10px #38bdf8; border-radius: 2px; }"
    ".bullet-1 { animation: bulletStream1 0.3s linear infinite; } .bullet-2 {"
    " animation: bulletStream2 0.3s linear infinite; }"
    # Kartu Berita Clean
    "div.stContainer { background-color: rgba(15, 23, 42, 0.45);"
    " backdrop-filter: blur(8px); padding: 15px; border-radius: 12px; border:"
    " 1px solid rgba(56, 189, 248, 0.25); margin-bottom: 12px; }"
    # Tombol Transparan
    'div.stButton > button, button[kind="secondary"] {'
    " background-color: transparent !important;"
    " border: 1px solid rgba(56, 189, 248, 0.45) !important;"
    " color: #f8fafc !important;"
    " border-radius: 8px !important;"
    "}"
    'div.stButton > button:hover, button[kind="secondary"]:hover {'
    " background-color: rgba(56, 189, 248, 0.15) !important;"
    " border-color: #38bdf8 !important;"
    "}"
    # Dropdown & Input Transparan Penuh
    'div[data-baseweb="select"],'
    'div[data-baseweb="select"] > div,'
    'div[data-baseweb="select"] > div > div,'
    'div[data-baseweb="input"],'
    'div[data-baseweb="input"] > div,'
    'div[data-baseweb="base-input"],'
    '.stSelectbox div[data-baseweb="select"] > div,'
    '.stTextInput div[data-baseweb="input"] {'
    " background-color: transparent !important;"
    " background: transparent !important;"
    " color: #f8fafc !important;"
    "}"
    'div[data-baseweb="select"] > div,'
    'div[data-baseweb="base-input"] {'
    " border: 1px solid rgba(56, 189, 248, 0.45) !important;"
    " border-radius: 8px !important;"
    "}"
    'div[data-baseweb="select"] > div:hover,'
    'div[data-baseweb="base-input"]:hover {'
    " border-color: #38bdf8 !important;"
    "}"
    'div[data-baseweb="input"] input {'
    " background-color: transparent !important;"
    " color: #f8fafc !important;"
    "}"
    'ul[role="listbox"], div[data-baseweb="popover"] > div, li[role="option"] {'
    " background-color: rgba(10, 15, 28, 0.92) !important;"
    " backdrop-filter: blur(12px) !important;"
    " color: #f8fafc !important;"
    "}"
    'li[role="option"]:hover {'
    " background-color: rgba(56, 189, 248, 0.25) !important;"
    "}"
    "</style>"
    # Render overlay klik khusus PC di luar sidebar jika sidebar sedang terbuka
    + (
        '<a href="?toggle_sidebar=0" class="pc-sidebar-overlay" title="Tutup'
        ' Menu"></a>'
        if st.session_state.sidebar_open
        else ""
    )
    + '<div class="metal-slug-banner"><div class="metal-slug-runner"><div'
    ' class="sprite-body">'
    '<svg viewBox="0 0 16 16" width="40" height="40"'
    ' shape-rendering="crispEdges">'
    '<rect x="4" y="1" width="6" height="2" fill="#8B4513"/><rect x="4" y="3"'
    ' width="7" height="1" fill="#FF0000"/><rect x="2" y="3" width="2"'
    ' height="2" fill="#FF0000"/>'
    '<rect x="5" y="4" width="5" height="3" fill="#FFCC99"/><rect x="8" y="4"'
    ' width="1" height="1" fill="#000000"/><rect x="4" y="7" width="6"'
    ' height="4" fill="#F0F0F0"/>'
    '<rect x="5" y="7" width="4" height="4" fill="#3A5F0B"/><rect x="6" y="8"'
    ' width="8" height="2" fill="#222222"/><rect x="7" y="9" width="2"'
    ' height="2" fill="#555555"/>'
    '<polygon class="flash" points="14,7 16,9 14,11" fill="#38bdf8"/>'
    '<g class="leg-l"><rect x="4" y="11" width="2" height="3"'
    ' fill="#2F4F4F"/><rect x="3" y="14" width="3" height="2"'
    ' fill="#4A2E1B"/></g>'
    '<g class="leg-r"><rect x="8" y="11" width="2" height="3"'
    ' fill="#2F4F4F"/><rect x="8" y="14" width="3" height="2"'
    ' fill="#4A2E1B"/></g>'
    '</svg></div><div class="bullet-1"></div><div'
    ' class="bullet-2"></div></div></div>'
)
st.markdown(custom_ui, unsafe_allow_html=True)

st.title("🎮 Nortisce Gaming News Database")
st.markdown(
    "Database berita game terkini dari **20 kanal global + 8 kanal lokal"
    " terbaik** lengkap dengan thumbnail, filter, dan analisis AI Gemini."
)

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
    "IDN Times Game": (
        "https://news.google.com/rss/search?q=site:idntimes.com+game&hl=id&gl=ID&ceid=ID:id"
    ),
    "GGWP ID": (
        "https://news.google.com/rss/search?q=site:ggwp.id+game&hl=id&gl=ID&ceid=ID:id"
    ),
    "Hybrid Indonesia": (
        "https://news.google.com/rss/search?q=site:hybrid.co.id+game&hl=id&gl=ID&ceid=ID:id"
    ),
    "Jagat Play": (
        "https://news.google.com/rss/search?q=site:jagatplay.com+game&hl=id&gl=ID&ceid=ID:id"
    ),
    "KotakGame": (
        "https://news.google.com/rss/search?q=site:kotakgame.com+game&hl=id&gl=ID&ceid=ID:id"
    ),
    "Kincir Game": (
        "https://news.google.com/rss/search?q=site:kincir.com+game&hl=id&gl=ID&ceid=ID:id"
    ),
    "Indogamers": (
        "https://news.google.com/rss/search?q=site:indogamers.com+game&hl=id&gl=ID&ceid=ID:id"
    ),
    "RevivalTV": (
        "https://news.google.com/rss/search?q=site:revivaltv.id+game&hl=id&gl=ID&ceid=ID:id"
    ),
}


def bersihkan_html(teks):
  teks_bersih = re.sub(r"<[^>]+>", " ", teks)
  return re.sub(r"\s+", " ", teks_bersih).strip()[:600]


def ambil_thumbnail(entry):
  fallback_game_images = [
      (
          "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=600&auto=format&fit=crop"
      ),
      (
          "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?q=80&w=600&auto=format&fit=crop"
      ),
      (
          "https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=600&auto=format&fit=crop"
      ),
      (
          "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=600&auto=format&fit=crop"
      ),
      (
          "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=600&auto=format&fit=crop"
      ),
  ]

  candi_url = ""
  if hasattr(entry, "media_content") and entry.media_content:
    for m in entry.media_content:
      if "url" in m:
        candi_url = m["url"]
        break
  if not candi_url and hasattr(entry, "links") and entry.links:
    for l in entry.links:
      if "type" in l and "image" in l["type"]:
        candi_url = l["href"]
        break
  if not candi_url:
    raw_html = getattr(entry, "summary", "") + getattr(
        entry, "content", [{"value": ""}]
    )[0].get("value", "")
    match = re.search(
        r'src=["\'](https?://[^"\']+\.(?:jpg|jpeg|png|webp))["\']',
        raw_html,
        re.IGNORECASE,
    )
    if match:
      candi_url = match.group(1)

  if not candi_url or any(
      bad in candi_url.lower()
      for bad in [
          "purexbox.com",
          "nintendolife.com",
          "pushsquare.com",
          "kickstarter",
          "ads",
      ]
  ):
    return random.choice(fallback_game_images)

  return candi_url


@st.cache_data(ttl=3600)
def muat_data_berita():
  semua_berita = []
  sekarang_utc = datetime.now(timezone.utc)
  batas_waktu = sekarang_utc - timedelta(days=7)

  for nama_web, u in RSS_SOURCES.items():
    try:
      feed = feedparser.parse(u)
      for entry in feed.entries:
        raw_desc = getattr(entry, "summary", entry.title)
        clean_desc = bersihkan_html(raw_desc)
        thumb_url = ambil_thumbnail(entry)
        if hasattr(entry, "published_parsed") and entry.published_parsed:
          pub_dt = datetime.fromtimestamp(
              mktime(entry.published_parsed), timezone.utc
          )
          if pub_dt >= batas_waktu:
            selisih_jam = (sekarang_utc - pub_dt).total_seconds() / 3600
            selisih_hari = int(selisih_jam // 24)
            label_waktu = (
                "Today (Hari Ini)"
                if selisih_jam < 24
                else (
                    "1 Day Ago (Kemarin)"
                    if selisih_hari == 1
                    else f"{selisih_hari} Days Ago"
                )
            )
            info = {
                "judul": entry.title,
                "link": entry.link,
                "sumber": nama_web,
                "tanggal": pub_dt.strftime("%d %b %Y, %H:%M"),
                "rentang_waktu": label_waktu,
                "selisih_hari": selisih_hari,
                "selisih_jam": selisih_jam,
                "deskripsi": clean_desc,
                "thumbnail": thumb_url,
                "datetime_obj": pub_dt,
            }
            if info not in semua_berita:
              semua_berita.append(info)
    except Exception:
      pass

  # Algoritma Hype & Engagement Scoring
  kata_penting = []
  for item in semua_berita:
    kata2 = [
        w.lower()
        for w in re.findall(r"\b[A-Za-z]{4,}\b", item["judul"])
        if w.lower() not in ["with", "from", "this", "that", "have", "will", "your"]
    ]
    kata_penting.extend(kata2)

  frekuensi_topik = Counter(kata_penting)
  hype_keywords = [
      "gta",
      "grand theft auto",
      "release",
      "trailer",
      "leak",
      "rumor",
      "ps5",
      "switch 2",
      "remake",
      "update",
      "dlc",
      "free",
      "xbox",
      "nintendo",
  ]

  for item in semua_berita:
    skor_hype = 0
    judul_lc = item["judul"].lower()
    for hk in hype_keywords:
      if hk in judul_lc:
        skor_hype += 15
    for kata in set(re.findall(r"\b[A-Za-z]{4,}\b", item["judul"])):
      if frekuensi_topik[kata.lower()] > 1:
        skor_hype += frekuensi_topik[kata.lower()] * 5
    jam_lalu = item["selisih_jam"]
    if jam_lalu <= 24:
      skor_hype += max(0, int(50 - (jam_lalu * 1.5)))
    elif jam_lalu <= 72:
      skor_hype += 15
    item["skor_engagement"] = skor_hype

  semua_berita.sort(key=lambda x: x["skor_engagement"], reverse=True)
  return semua_berita


@st.cache_data(show_spinner=False)
def analisis_gemini_multi_key(keys_tuple, mode, judul, sumber, deskripsi):
  if mode == "ringkas":
    prompt = (
        f"Sebagai analis industri game, bedah esensi berita dari {sumber}"
        " berikut secara tajam, unik, dan mendalam dalam 3 kalimat bahasa"
        f" Indonesia (tanpa basa-basi pembuka):\nJudul: {judul}\nKonteks:"
        f" {deskripsi}"
    )
  else:
    prompt = (
        "As a gaming community observer, determine public sentiment (Positive"
        " / Negative / Neutral) and its sharp reasoning in 2-3 sentences of"
        f" Indonesian for this news:\nTitle: {judul}\nContext: {deskripsi}"
    )

  catatan_error = []
  for idx, key in enumerate(keys_tuple, start=1):
    if not key or not key.strip():
      continue
    try:
      genai.configure(api_key=key.strip())
      model = genai.GenerativeModel("gemini-3.8-flash")
      response = model.generate_content(prompt)
      return response.text
    except Exception as e:
      catatan_error.append(f"Key #{idx}: {e}")
      continue

  raise Exception(
      " | ".join(catatan_error)
      if catatan_error
      else "Daftar API Key kosong"
  )


# --- LOGIKA GAME TIC-TAC-TOE ---
def cek_pemenang_ttt(papan):
  pola_menang = [
      (0, 1, 2),
      (3, 4, 5),
      (6, 7, 8),
      (0, 3, 6),
      (1, 4, 7),
      (2, 5, 8),
      (0, 4, 8),
      (2, 4, 6),
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


if st.sidebar.button("🔄 Refresh Cache Berita", use_container_width=True):
  st.cache_data.clear()
  st.rerun()

with st.spinner(
    "⏳ Menyerok berita, menganalisis hype & thumbnail dari 28 server..."
):
  semua_berita = muat_data_berita()

st.success(
    f"Berhasil mengumpulkan {len(semua_berita)} berita segar dalam 7 hari"
    " terakhir! (28 Kanal Media)"
)

st.sidebar.header("🎛️ Panel Filter")
search_keyword = st.sidebar.text_input("🔍 Cari Judul / Game:", "").lower()

pilih_kategori = st.sidebar.selectbox(
    "📂 Kategori Berita:",
    [
        "Semua Kategori",
        "🎮 Game Releases & Updates",
        "🛠️ Tech, Hardware & Performance",
        "🏢 Industry & Business",
        "🏆 Esports & Competitive",
        "🍿 Pop Culture, Media & Leaks",
        "📌 Lainnya",
    ],
)

pilih_web = st.sidebar.selectbox(
    "🌐 Sumber Website:", ["Semua Website (28 Media)"] + list(RSS_SOURCES.keys())
)
pilih_waktu = st.sidebar.selectbox(
    "⏰ Rentang Waktu:",
    [
        "Semua Rentang Waktu (7 Hari Terakhir)",
        "Today (Hari Ini)",
        "1 Day Ago (Kemarin)",
        "2 Days Ago",
        "3 Days Ago",
        "4-7 Days Ago",
    ],
)

# --- SIDEBAR: UPCOMING GAMES RELEASE ---
st.sidebar.markdown("---")
st.sidebar.markdown(
    "[🎮 Upcoming Games Release](https://www.ign.com/upcoming/games)",
    unsafe_allow_html=True,
)

# --- MINI-GAME TIC-TAC-TOE ---
st.sidebar.markdown("---")
st.sidebar.subheader("🕹️ Tic-Tac-Toe")
st.sidebar.caption("Kamu (**❌**) vs Bot (**⭕**)")

if "ttt_board" not in st.session_state:
  st.session_state.ttt_board = [""] * 9
if "ttt_winner" not in st.session_state:
  st.session_state.ttt_winner = None


def klik_kotak_ttt(idx):
  if (
      st.session_state.ttt_board[idx] == ""
      and st.session_state.ttt_winner is None
  ):
    st.session_state.ttt_board[idx] = "X"
    hasil = cek_pemenang_ttt(st.session_state.ttt_board)
    if hasil:
      st.session_state.ttt_winner = hasil
    else:
      bot_idx = langkah_bot_ttt(st.session_state.ttt_board)
      if bot_idx is not None:
        st.session_state.ttt_board[bot_idx] = "O"
        st.session_state.ttt_winner = cek_pemenang_ttt(
            st.session_state.ttt_board
        )


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
        disabled=(val != "" or st.session_state.ttt_winner is not None),
    )

if st.session_state.ttt_winner == "X":
  st.sidebar.success("🎉 Kamu Menang!")
elif st.session_state.ttt_winner == "O":
  st.sidebar.error("🤖 Bot Menang!")
elif st.session_state.ttt_winner == "Seri":
  st.sidebar.warning("🤝 Seri!")

if st.sidebar.button("🔁 Reset Game", use_container_width=True):
  st.session_state.ttt_board = [""] * 9
  st.session_state.ttt_winner = None
  st.rerun()

# --- FILTER & KATEGORISASI BERITA ---
kategori = {
    k: []
    for k in [
        "🎮 Game Releases & Updates",
        "🛠️ Tech, Hardware & Performance",
        "🏢 Industry & Business",
        "🏆 Esports & Competitive",
        "🍿 Pop Culture, Media & Leaks",
        "📌 Lainnya",
    ]
}
keywords = {
    "🎮 Game Releases & Updates": [
        "release",
        "launch",
        "update",
        "patch",
        "dlc",
        "expansion",
        "out now",
        "beta",
        "season",
        "gameplay",
        "review",
    ],
    "🛠️ Tech, Hardware & Performance": [
        "rtx",
        "gtx",
        "gpu",
        "cpu",
        "amd",
        "nvidia",
        "intel",
        "ps5 pro",
        "switch 2",
        "hardware",
        "monitor",
        "fps",
        "steam deck",
    ],
    "🏢 Industry & Business": [
        "acquire",
        "acquisition",
        "layoffs",
        "studio",
        "sales",
        "revenue",
        "sony",
        "nintendo",
        "microsoft",
        "xbox",
        "epic games",
        "valve",
    ],
    "🏆 Esports & Competitive": [
        "esports",
        "tournament",
        "championship",
        "valorant",
        "pro player",
        "meta",
        "nerf",
        "buff",
    ],
    "🍿 Pop Culture, Media & Leaks": [
        "movie",
        "series",
        "adaption",
        "trailer",
        "leak",
        "rumor",
        "hbo",
        "netflix",
    ],
}

berita_terfilter = []
for item in semua_berita:
  sw = item["selisih_hari"]
  waktu_cocok = (
      pilih_waktu == "Semua Rentang Waktu (7 Hari Terakhir)"
      or (
          pilih_waktu == "Today (Hari Ini)"
          and item["rentang_waktu"] == "Today (Hari Ini)"
      )
      or (
          pilih_waktu == "1 Day Ago (Kemarin)"
          and item["rentang_waktu"] == "1 Day Ago (Kemarin)"
      )
      or (pilih_waktu == "2 Days Ago" and sw == 2)
      or (pilih_waktu == "3 Days Ago" and sw == 3)
      or (pilih_waktu == "4-7 Days Ago" and (4 <= sw <= 7))
  )
  web_cocok = (pilih_web == "Semua Website (28 Media)") or (
      item["sumber"] == pilih_web
  )
  search_cocok = (
      (search_keyword in item["judul"].lower())
      or (search_keyword in item["sumber"].lower())
      if search_keyword
      else True
  )

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

target_tampil = (
    kategori.items()
    if pilih_kategori == "Semua Kategori"
    else [(pilih_kategori, kategori[pilih_kategori])]
)

st.markdown("---")
total_ditampilkan = sum(len(daftar) for _, daftar in target_tampil)
st.info(
    f"Menampilkan total **{total_ditampilkan} berita** tersaring (Diurutkan"
    f" berdasarkan Engagement & Hype Tertinggi) | Kategori:"
    f" **{pilih_kategori}** | Sumber: **{pilih_web}**"
)

# --- SISTEM PAGINASI TERSINKRONISASI SEMPURNA (ATAS & BAWAH) ---
semua_berita_flat = []
for kat, daftar in target_tampil:
  for b in daftar:
    b["kategori_asal"] = kat
    semua_berita_flat.append(b)

items_per_page = 10
total_pages = max(
    1, (len(semua_berita_flat) + items_per_page - 1) // items_per_page
)

if "halaman_aktif" not in st.session_state:
  st.session_state.halaman_aktif = 1
if st.session_state.halaman_aktif > total_pages:
  st.session_state.halaman_aktif = 1

st.session_state.top_pagination = st.session_state.halaman_aktif
st.session_state.bottom_pagination = st.session_state.halaman_aktif


def ubah_halaman_atas():
  st.session_state.halaman_aktif = st.session_state.top_pagination
  st.session_state.bottom_pagination = st.session_state.top_pagination


def ubah_halaman_bawah():
  st.session_state.halaman_aktif = st.session_state.bottom_pagination
  st.session_state.top_pagination = st.session_state.bottom_pagination


# Paginasi Bagian Atas
if total_pages > 1:
  st.selectbox(
      f"📄 Pilih Halaman (Total {total_pages} Page Tersedia):",
      range(1, total_pages + 1),
      format_func=lambda x: (
          f"Page {x} dari {total_pages} (Menampilkan 10 Berita)"
      ),
      key="top_pagination",
      on_change=ubah_halaman_atas,
  )

current_page = st.session_state.halaman_aktif
start_idx = (current_page - 1) * items_per_page
end_idx = start_idx + items_per_page
berita_paginasi = semua_berita_flat[start_idx:end_idx]

st.markdown(
    f"### 📑 Menampilkan Berita Halaman {current_page} dari {total_pages}"
    f" ({len(berita_paginasi)} Berita di Halaman Ini)"
)

for idx, b in enumerate(berita_paginasi):
  with st.container():
    col_img, col_txt = st.columns([1, 4])

    with col_img:
      # Diperbarui menggunakan use_container_width agar tidak error deprecated di Streamlit versi baru
      st.image(b["thumbnail"], use_container_width=True)

    with col_txt:
      st.markdown(f"**[{b['judul']}]({b['link']})**")
      st.caption(
          f"📂 *{b['kategori_asal']}* | 🌐 **{b['sumber']}** | 📅 {b['tanggal']}"
          f" ({b['rentang_waktu']})"
      )

    expander_key = f"exp_page_{current_page}_{idx}_{b['judul'][:10]}"
    with st.expander("✨ Ringkasan AI & Analisis Sentimen Publik"):
      col_btn1, col_btn2 = st.columns(2)

      if col_btn1.button("📝 Ringkas Artikel", key=f"btn_sum_{expander_key}"):
        if not daftar_api_keys:
          st.warning("⚠️ API Key belum dikonfigurasi di Streamlit Secrets.")
        else:
          with st.spinner("Menganalisis..."):
            try:
              hasil = analisis_gemini_multi_key(
                  tuple(daftar_api_keys),
                  "ringkas",
                  b["judul"],
                  b["sumber"],
                  b["deskripsi"],
              )
              st.success(hasil)
            except Exception as e:
              st.error(f"Detail kendala: {e}")

      if col_btn2.button(
          "📊 Cek Sentimen Publik", key=f"btn_sent_{expander_key}"
      ):
        if not daftar_api_keys:
          st.warning("⚠️ API Key belum dikonfigurasi di Streamlit Secrets.")
        else:
          with st.spinner("Memindai sentimen..."):
            try:
              hasil = analisis_gemini_multi_key(
                  tuple(daftar_api_keys),
                  "sentimen",
                  b["judul"],
                  b["sumber"],
                  b["deskripsi"],
              )
              st.info(hasil)
            except Exception as e:
              st.error(f"Detail kendala: {e}")

# --- Paginasi Bagian Bawah (Tersinkronisasi otomatis dengan atas) ---
if total_pages > 1:
  st.markdown("---")
  st.selectbox(
      f"📄 Navigasi Halaman Bawah (Total {total_pages} Page):",
      range(1, total_pages + 1),
      format_func=lambda x: f"Page {x} dari {total_pages}",
      key="bottom_pagination",
      on_change=ubah_halaman_bawah,
  )
