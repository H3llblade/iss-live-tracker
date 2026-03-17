import streamlit as st
import requests
import pydeck as pdk
from streamlit_autorefresh import st_autorefresh
import math
from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

# ----------------------
# CONFIG
# ----------------------
st.set_page_config(layout="wide", page_title="NASA ISS TRACKER")
st.title("🛰️ NASA ISS TRACKER")

# Refresh automatico ogni 10 secondi
st_autorefresh(interval=30000, key="refresh")

URL = "http://api.open-notify.org/iss-now.json"

# ----------------------
# SELEZIONE LIGHT/DARK CON DUE CHECKBOX
# ----------------------
# Stato iniziale
if "light_mode" not in st.session_state:
    st.session_state.light_mode = False
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

def toggle_light():
    st.session_state.dark_mode = not st.session_state.light_mode

def toggle_dark():
    st.session_state.light_mode = not st.session_state.dark_mode

col1, col2 = st.columns(2)
with col1:
    st.checkbox("🌕 Light Mode", value=st.session_state.light_mode, key="light_mode", on_change=toggle_light)
with col2:
    st.checkbox("🌑 Dark Mode", value=st.session_state.dark_mode, key="dark_mode", on_change=toggle_dark)

map_style = "light" if st.session_state.light_mode else "dark"

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

def get_city_and_time(lat, lon):
    try:
        geolocator = Nominatim(user_agent="iss_tracker")
        location = geolocator.reverse((lat, lon), language="en", zoom=10)
        city = location.raw.get('address', {}).get('city') or location.raw.get('address', {}).get('town') or location.raw.get('address', {}).get('village') or "Sconosciuta"
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        tz = pytz.timezone(tz_name) if tz_name else pytz.utc
        local_time = datetime.now(tz).strftime("%H:%M:%S")
        return city, tz_name, local_time
    except:
        return "Sconosciuta", "UTC", datetime.utcnow().strftime("%H:%M:%S")

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
# ICONA ISS
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
# MAPPA 3D GLOBO
# ----------------------
view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=1.5, pitch=45, bearing=0)
deck = pdk.Deck(
    layers=[path_layer, iss_layer],
    initial_view_state=view_state,
    map_style=map_style,
    tooltip={"text": "ISS Position\nLat: {lat}\nLon: {lon}"}
)
st.pydeck_chart(deck)

# ----------------------
# TELEMETRIA IN BOX
# ----------------------
st.subheader("📡 Telemetria ISS")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Latitudine", f"{lat:.4f}°")
col2.metric("Longitudine", f"{lon:.4f}°")
col3.metric("Velocità", f"{speed:.0f} km/h")
col4.metric("Altitudine stimata", f"{st.session_state.altitude} km")
col5.metric("Aggiornamento", datetime.now().strftime("%H:%M:%S"))

# ----------------------
# FUNZIONE PER STATO/REGIONE E ORARIO LOCALE
# ----------------------
def get_location_and_time(lat, lon):
    try:
        geolocator = Nominatim(user_agent="iss_tracker")
        location = geolocator.reverse((lat, lon), language="en", zoom=5)
        address = location.raw.get('address', {})
        # Stato e regione/provincia
        state = address.get('state') or address.get('region') or address.get('country')
        region = address.get('county') or address.get('state_district') or ""
        if not state:
            return "Over Ocean", "", "UTC", datetime.utcnow().strftime("%H:%M:%S")
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        tz = pytz.timezone(tz_name) if tz_name else pytz.utc
        local_time = datetime.now(tz).strftime("%H:%M:%S")
        return state, region, tz_name, local_time
    except:
        return "Sconosciuto", "", "UTC", datetime.utcnow().strftime("%H:%M:%S")

# ----------------------
# CITTÀ/STATO SORVOLATO E ORARIO LOCALE
# ----------------------
st.subheader("🗺️ Posizione sorvolata")
state, region, tz_name, local_time = get_location_and_time(lat, lon)
col_state, col_region, col_tz, col_time = st.columns(4)
col_state.metric("Stato", state)
col_region.metric("Regione/Provincia", region)
col_tz.metric("Fuso orario", tz_name)
col_time.metric("Orario locale", local_time)
