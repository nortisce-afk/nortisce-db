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

# Inisialisasi status buka/tutup sidebar
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True

# Ambil API Key dari Streamlit Secrets secara aman & sederhana
api_key = st.secrets.get("GEMINI_API_KEY", "")
if api_key:
    genai.configure(api_key=api_key)


def get_chunli_bg():
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
        for file in glob.glob(ext):
            if "chunli" in file.lower():
                mime = (
                    "image/png"
                    if file.lower().endswith(".png")
                    else (
                        "image/webp"
                        if file.lower().endswith(".webp")
                        else "image/jpeg"
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

sidebar_left_pos = "0px" if st.session_state.sidebar_open else "-300px"

# --- CLEAN GAMING UI CSS + CUSTOM ARROW TOGGLE DI POJOK KIRI ATAS ---
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
    ".floating-sidebar-toggle {"
    " position: fixed;"
    " top: 12px;"
    f" left: {'265px' if st.session_state.sidebar_open else '15px'};"
    " z-index: 1000000;"
    " background: rgba(15, 23, 42, 0.8);"
    " border: 1px solid rgba(56, 189, 248, 0.5);"
    " color: #38bdf8;"
    " width: 36px;"
    " height: 36px;"
    " border-radius: 8px;"
    " display: flex;"
    " align-items: center;"
    " justify-content: center;"
    " text-decoration: none;"
    " font-size: 18px;"
    " font-weight: bold;"
    " transition: all 0.3s ease;"
    " backdrop-filter: blur(4px);"
    "}"
    ".floating-sidebar-toggle:hover {"
    " background: rgba(56, 189, 248, 0.25);"
    " color: #ffffff;"
    " border-color: #38bdf8;"
    "}"
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
    + ".metal-slug-banner { position: fixed; top: 0; left: 0; width: 100%; height:"
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
    "div.stContainer { background-color: rgba(15, 23, 42, 0.45);"
    " backdrop-filter: blur(8px); padding: 15px; border-radius: 12px; border:"
    " 1px solid rgba(56, 189, 248, 0.25); margin-bottom: 12px; }"
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
    + (
        '<div onclick="window.location.href=\'?toggle_sidebar=0\'"'
        ' class="pc-sidebar-overlay" title="Tutup Menu"></div>'
        if st.session_state.sidebar_open
        else ""
    )
    + f'<a href="?toggle_sidebar={0 if st.session_state.sidebar_open else 1}"'
    ' class="floating-sidebar-toggle"'
    f' title="{"Tutup Menu" if st.session_state.sidebar_open else "Buka Menu"}">'
    f'{"❮" if st.session_state.sidebar_open else "❯"}</a>'
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
    " terbaik** lengkap dengan thumbnail asli, filter, dan analisis AI Gemini."
)

RSS_SOURCES = {
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
        "
