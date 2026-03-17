import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime
import math
from streamlit_autorefresh import st_autorefresh

# ----------------------
# CONFIG PAGINA
# ----------------------
st.set_page_config(
    page_title="ISS Mission Control",
    layout="wide"
)

# ----------------------
# AUTO REFRESH (30s)
# ----------------------
st_autorefresh(interval=30000, key="iss_refresh")

# ----------------------
# STILE DARK NASA
# ----------------------
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0f1a;
        color: white;
    }
    h1, h2, h3 {
        color: #00e6ff;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------
# HEADER
# ----------------------
st.title("🛰️ ISS MISSION CONTROL")
st.caption("Live tracking della Stazione Spaziale Internazionale")

# ----------------------
# API
# ----------------------
URL = "http://api.open-notify.org/iss-now.json"

def get_iss_position():
    response = requests.get(URL)
    data = response.json()
    return float(data['iss_position']['latitude']), float(data['iss_position']['longitude'])

# ----------------------
# DISTANZA (Haversine)
# ----------------------
def distanza(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

# ----------------------
# CHECK ITALIA
# ----------------------
def sopra_italia(lat, lon):
    return 36 < lat < 47 and 6 < lon < 19

# ----------------------
# SESSION STATE
# ----------------------
if "percorso" not in st.session_state:
    st.session_state.percorso = []

if "last_pos" not in st.session_state:
    st.session_state.last_pos = None

# ----------------------
# DATI ISS
# ----------------------
lat, lon = get_iss_position()
st.session_state.percorso.append([lat, lon])

# ----------------------
# METRICHE
# ----------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("🌍 Latitudine", f"{lat:.4f}")
col2.metric("🌍 Longitudine", f"{lon:.4f}")

velocita = 0
if st.session_state.last_pos:
    lat1, lon1 = st.session_state.last_pos
    dist = distanza(lat1, lon1, lat, lon)
    velocita = dist / (30 / 3600)

col3.metric("🚀 Velocità km/h", f"{velocita:.0f}")

stato = "🇮🇹 SOPRA ITALIA" if sopra_italia(lat, lon) else "🌌 IN ORBITA"
col4.metric("📡 Stato", stato)

st.session_state.last_pos = (lat, lon)

# ----------------------
# MAPPA DARK
# ----------------------
mappa = folium.Map(
    location=[lat, lon],
    zoom_start=3,
    tiles="CartoDB dark_matter"
)

# Marker ISS
folium.CircleMarker(
    location=[lat, lon],
    radius=8,
    color="cyan",
    fill=True,
    fill_color="cyan"
).add_to(mappa)

# Percorso
if len(st.session_state.percorso) > 1:
    folium.PolyLine(
        st.session_state.percorso,
        color="cyan",
        weight=2
    ).add_to(mappa)

st_folium(mappa, width=1200, height=500, key="map")

# ----------------------
# STORICO
# ----------------------
st.subheader("📍 Traiettoria recente")

for i, pos in enumerate(st.session_state.percorso[-10:][::-1]):
    st.write(f"{i+1}. Lat: {pos[0]:.4f}, Lon: {pos[1]:.4f}")

# ----------------------
# FOOTER
# ----------------------
st.markdown("---")
st.caption(f"🕒 Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}")
