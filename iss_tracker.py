import streamlit as st
import requests
import pydeck as pdk
from streamlit_autorefresh import st_autorefresh
import math
from datetime import datetime

# ----------------------
# CONFIG
# ----------------------
st.set_page_config(layout="wide", page_title="NASA ISS Globe Tracker")
st.title("🛰️ NASA ISS Tracker - Globe 3D")

# Refresh automatico ogni 10 secondi
st_autorefresh(interval=10000, key="refresh")

URL = "http://api.open-notify.org/iss-now.json"

# ----------------------
# TOGGLE LIGHT/DARK
# ----------------------
col1, col2 = st.columns(2)
with col1:
    light_mode = st.checkbox("🌕 Light Mode", value=False)
with col2:
    dark_mode = st.checkbox("🌑 Dark Mode", value=not light_mode)

map_style = "light" if light_mode else "dark"

# ----------------------
# FUNZIONI
# ----------------------
def get_iss():
    try:
        data = requests.get(URL, timeout=5).json()
        lat = float(data['iss_position']['latitude'])
        lon = float(data['iss_position']['longitude'])
        return lat, lon
    except:
        return None, None

def distanza(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ----------------------
# SESSION STATE
# ----------------------
if "track" not in st.session_state:
    st.session_state.track = []

if "last" not in st.session_state:
    st.session_state.last = None

if "altitude" not in st.session_state:
    st.session_state.altitude = 420

# ----------------------
# DATI ISS
# ----------------------
lat, lon = get_iss()
if lat is None:
    st.error("Impossibile ottenere i dati ISS")
    st.stop()

st.session_state.track.append([lon, lat])
if len(st.session_state.track) > 300:
    st.session_state.track.pop(0)

# ----------------------
# VELOCITÀ ISTANTANEA
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
    get_color=[255, 215, 0],
    get_radius=250000,
    pickable=True,
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
# GLOBO 3D
# ----------------------
view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=1, pitch=30, bearing=0)
deck = pdk.Deck(
    layers=[path_layer, iss_layer],
    initial_view_state=view_state,
    map_style=f"mapbox://styles/mapbox/{map_style}-v10",
    views=[pdk.GlobeView()],
    tooltip={"text": "ISS Position\nLat: {lat}\nLon: {lon}"}
)

st.pydeck_chart(deck)

# ----------------------
# TELEMETRIA ISS
# ----------------------
st.subheader("📡 Telemetria ISS")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Latitudine", f"{lat:.4f}°")
col2.metric("Longitudine", f"{lon:.4f}°")
col3.metric("Velocità", f"{speed:.0f} km/h")
col4.metric("Altitudine stimata", f"{st.session_state.altitude} km")
col5.metric("Aggiornamento", datetime.now().strftime("%H:%M:%S"))
