import streamlit as st
import requests
import pydeck as pdk
from streamlit_autorefresh import st_autorefresh
import math
from datetime import datetime

# ----------------------
# CONFIG
# ----------------------
st.set_page_config(layout="wide")
st.title("🛰️ NASA ISS MISSION CONTROL")

# Refresh fluido (10 secondi)
st_autorefresh(interval=10000, key="refresh")

URL = "http://api.open-notify.org/iss-now.json"

# ----------------------
# DATI ISS
# ----------------------
def get_iss():
    data = requests.get(URL).json()
    lat = float(data['iss_position']['latitude'])
    lon = float(data['iss_position']['longitude'])
    return lat, lon

# ----------------------
# DISTANZA (velocità)
# ----------------------
def distanza(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

# ----------------------
# SESSION STATE
# ----------------------
if "track" not in st.session_state:
    st.session_state.track = []

if "last" not in st.session_state:
    st.session_state.last = None

# ----------------------
# NUOVI DATI
# ----------------------
lat, lon = get_iss()
st.session_state.track.append([lon, lat])  # pydeck usa [lon, lat]

# limita storico
if len(st.session_state.track) > 200:
    st.session_state.track.pop(0)

# ----------------------
# VELOCITÀ REALE
# ----------------------
speed = 0
if st.session_state.last:
    lat1, lon1 = st.session_state.last
    dist = distanza(lat1, lon1, lat, lon)
    speed = dist / (10 / 3600)

st.session_state.last = (lat, lon)

# ----------------------
# LAYER ISS
# ----------------------
iss_layer = pdk.Layer(
    "ScatterplotLayer",
    data=[{"position": [lon, lat]}],
    get_position="position",
    get_color=[255, 0, 0],
    get_radius=200000,
)

# ----------------------
# TRAIETTORIA
# ----------------------
path_layer = pdk.Layer(
    "PathLayer",
    data=[{"path": st.session_state.track}],
    get_path="path",
    get_color=[0, 255, 255],
    width_scale=20,
    width_min_pixels=2,
)

# ----------------------
# VIEW
# ----------------------
view_state = pdk.ViewState(
    latitude=lat,
    longitude=lon,
    zoom=2,
    pitch=45,
)

# ----------------------
# MAPPA (STILE NASA)
# ----------------------
deck = pdk.Deck(
    layers=[path_layer, iss_layer],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/dark-v10"
)

st.pydeck_chart(deck)

# ----------------------
# TELEMETRIA
# ----------------------
st.subheader("📡 Telemetria ISS")

col1, col2, col3 = st.columns(3)

col1.metric("Latitudine", f"{lat:.4f}")
col2.metric("Longitudine", f"{lon:.4f}")
col3.metric("Velocità km/h", f"{speed:.0f}")

# ----------------------
# INFO EXTRA
# ----------------------
st.markdown("---")
st.caption(f"🕒 Aggiornamento: {datetime.now().strftime('%H:%M:%S')}")
