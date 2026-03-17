import streamlit as st
import requests
import pydeck as pdk
from streamlit_autorefresh import st_autorefresh
import math
from datetime import datetime

# ----------------------
# CONFIG
# ----------------------
st.set_page_config(layout="wide", page_title="NASA ISS Mission Control")
st.title("🛰️ NASA ISS MISSION CONTROL - Versione Avanzata")

# Refresh automatico ogni 10 secondi
st_autorefresh(interval=10000, key="refresh")

URL = "http://api.open-notify.org/iss-now.json"

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
        return 0, 0

def distanza(lat1, lon1, lat2, lon2):
    R = 6371  # raggio Terra km
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

if "altitude" not in st.session_state:
    st.session_state.altitude = 420  # km circa ISS

# ----------------------
# DATI NUOVI
# ----------------------
lat, lon = get_iss()
st.session_state.track.append([lon, lat])

# limita storico a 300 punti
if len(st.session_state.track) > 300:
    st.session_state.track.pop(0)

# ----------------------
# VELOCITÀ ISTANTANEA
# ----------------------
speed = 0
if st.session_state.last:
    lat1, lon1 = st.session_state.last
    dist = distanza(lat1, lon1, lat, lon)
    speed = dist / (10 / 3600)  # km/h

st.session_state.last = (lat, lon)

# ----------------------
# LAYER ISS CON ICONA PERSONALIZZATA
# ----------------------
iss_layer = pdk.Layer(
    "IconLayer",
    data=[{"position": [lon, lat], "icon_data": "iss"}],
    get_icon="icon_data",
    get_size=4,
    size_scale=15,
    get_position="position",
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
# MAPPA - GLOBO 3D
# ----------------------
view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=2, pitch=45)

deck = pdk.Deck(
    layers=[path_layer, iss_layer],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/satellite-v9"  # mappa terrestre realistica
)

st.pydeck_chart(deck)

# ----------------------
# BOX METRICHE
# ----------------------
st.subheader("📡 Telemetria ISS")
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Latitudine", f"{lat:.4f}°")
col2.metric("Longitudine", f"{lon:.4f}°")
col3.metric("Velocità", f"{speed:.0f} km/h")
col4.metric("Altitudine stimata", f"{st.session_state.altitude} km")
col5.metric("Aggiornamento", datetime.now().strftime("%H:%M:%S"))
