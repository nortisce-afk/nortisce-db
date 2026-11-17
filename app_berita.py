import feedparser
import streamlit as st

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Nortisce News Aggregator", page_icon="🎮", layout="wide"
)

# --- DAFTAR SUMBER BERITA (30 KANAL: 20 GLOBAL + 10 LOKAL) ---
RSS_SOURCES = [
    # --- 20 MEDIA GLOBAL ---
    {
        "name": "IGN",
        "url": "https://feeds.feedburner.com/ign/games-all",
        "region": "Global",
    },
    {
        "name": "GameSpot",
        "url": "https://www.gamespot.com/feeds/mashup/",
        "region": "Global",
    },
    {"name": "Kotaku", "url": "https://kotaku.com/rss", "region": "Global"},
    {
        "name": "Polygon",
        "url": "https://www.polygon.com/rss/index.xml",
        "region": "Global",
    },
    {
        "name": "PC Gamer",
        "url": "https://www.pcgamer.com/rss/",
        "region": "Global",
    },
    {
        "name": "Eurogamer",
        "url": "https://www.eurogamer.net/feed",
        "region": "Global",
    },
    {
        "name": "Rock Paper Shotgun",
        "url": "https://www.rockpapershotgun.com/feed",
        "region": "Global",
    },
    {
        "name": "GamesRadar+",
        "url": "https://www.gamesradar.com/rss/",
        "region": "Global",
    },
    {
        "name": "Destructoid",
        "url": "https://www.destructoid.com/feed/",
        "region": "Global",
    },
    {
        "name": "Game Informer",
        "url": "https://www.gameinformer.com/feed.xml",
        "region": "Global",
    },
    {
        "name": "Gematsu",
        "url": "https://www.gematsu.com/feed",
        "region": "Global",
    },
    {
        "name": "VGC (Video Games Chronicle)",
        "url": "https://www.videogameschronicle.com/feed/",
        "region": "Global",
    },
    {
        "name": "Push Square",
        "url": "https://www.pushsquare.com/feed",
        "region": "Global",
    },
    {
        "name": "Nintendo Life",
        "url": "https://www.nintendolife.com/feed",
        "region": "Global",
    },
    {
        "name": "Pocket Gamer",
        "url": "https://www.pocketgamer.com/rss/",
        "region": "Global",
    },
    {
        "name": "PCGamesN",
        "url": "https://www.pcgamesn.com/feed",
        "region": "Global",
    },
    {
        "name": "Siliconera",
        "url": "https://www.siliconera.com/feed/",
        "region": "Global",
    },
    {
        "name": "Twoset / RPG Site",
        "url": "https://www.rpgsite.net/rss",
        "region": "Global",
    },
    {
        "name": "Shacknews",
        "url": "https://www.shacknews.com/rss?format=rss",
        "region": "Global",
    },
    {
        "name": "DualShockers",
        "url": "https://www.dualshockers.com/feed/",
        "region": "Global",
    },
    # --- 10 MEDIA LOKAL (INDONESIA) ---
    {"name": "Jagat Play", "url": "https://jagatplay.com/feed/", "region": "Lokal"},
    {"name": "Gamebrott", "url": "https://gamebrott.com/feed/", "region": "Lokal"},
    {
        "name": "Duniaku.com",
        "url": "https://duniaku.idntimes.com/feed",
        "region": "Lokal",
    },
    {
        "name": "KotakGame",
        "url": "https://www.kotakgame.com/rss/news.xml",
        "region": "Lokal",
    },
    {
        "name": "ONE Esports ID",
        "url": "https://www.oneesports.id/feed/",
        "region": "Lokal",
    },
    {"name": "RevivaLTV", "url": "https://revivaltv.id/feed/", "region": "Lokal"},
    {"name": "Spin Esports", "url": "https://esports.id/feed", "region": "Lokal"},
    {"name": "GGWP.ID", "url": "https://ggwp.id/feed", "region": "Lokal"},
    {
        "name": "Kincir (Game)",
        "url": "https://kincir.com/game/feed/",
        "region": "Lokal",
    },
    {
        "name": "Hybrid.co.id",
        "url": "https://hybrid.co.id/feed/",
        "region": "Lokal",
    },
]

st.title("🎮 Nortisce News Aggregator")
st.markdown("Portal berita game pilihan (30 Kanal: 20 Global + 10 Lokal)")

# --- SIDEBAR FILTER ---
st.sidebar.header("Pengaturan Konten")

selected_region = st.sidebar.selectbox(
    "🌍 Pilih Wilayah Media:",
    ["Semua Wilayah (30 Media)", "Global (20 Media)", "Lokal Indonesia (10 Media)"],
)

if selected_region == "Global (20 Media)":
  active_sources = [s for s in RSS_SOURCES if s["region"] == "Global"]
elif selected_region == "Lokal Indonesia (10 Media)":
  active_sources = [s for s in RSS_SOURCES if s["region"] == "Lokal"]
else:
  active_sources = RSS_SOURCES

source_names = [s["name"] for s in active_sources]
selected_source = st.sidebar.selectbox(
    "🌐 Pilih Sumber Website:", ["Semua Website"] + source_names
)


# --- FUNGSI AMBIL BERITA ---
@st.cache_data(ttl=600)
def fetch_news(sources):
  articles = []
  for source in sources:
    try:
      feed = feedparser.parse(source["url"])
      for entry in feed.entries:
        articles.append({
            "title": entry.get("title", "Tanpa Judul"),
            "link": entry.get("link", "#"),
            "published": entry.get(
                "published", entry.get("updated", "Baru saja")
            ),
            "source": source["name"],
            "region": source["region"],
        })
    except Exception:
      pass
  return articles


# --- EKsekusi PENGAMBILAN DATA ---
target_sources = (
    active_sources
    if selected_source == "Semua Website"
    else [s for s in active_sources if s["name"] == selected_source]
)

with st.spinner("Mengambil berita terbaru..."):
  news_list = fetch_news(target_sources)

# --- TAMPILKAN BERITA ---
if not news_list:
  st.warning(
      "Belum ada berita yang berhasil dimuat. Coba periksa koneksi atau"
      " pilih sumber lain."
  )
else:
  st.success(f"Berhasil memuat {len(news_list)} artikel!")
  for item in news_list:
    with st.container():
      st.markdown(f"### [{item['title']}]({item['link']})")
      st.caption(
          f"Sumber: **{item['source']}** | Wilayah: `{item['region']}` | Dipublikasikan:"
          f" {item['published']}"
      )
      st.divider()
