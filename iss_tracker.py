import streamlit as st
import requests
import math
from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import folium
from streamlit_folium import st_folium

# ----------------------
# CONFIG
# ----------------------
st.set_page_config(layout="wide", page_title="NASA ISS Tracker")
st.title("🛰️ NASA ISS Tracker - Folium OpenStreetMap")

# Refresh automatico ogni 10 secondi
st_autorefresh(interval=10000, key="refresh")

URL = "http://api.open-notify.org/iss-now.json"

# ----------------------
# LIGHT/DARK TOGGLE
# ----------------------
if "light_mode" not in st.session_state:
    st.session_state.light_mode = True

st.checkbox("🌕 Light Mode / 🌑 Dark Mode", value=st.session_state.light_mode,
            key="light_mode", on_change=lambda: st.session_state.update({"light_mode": not st.session_state.light_mode}))

tile_style = "OpenStreetMap" if st.session_state.light_mode else "CartoDB dark_matter"

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
    """Restituisce città e ora locale corretta"""
    try:
        geolocator = Nominatim(user_agent="iss_tracker")
        location = geolocator.reverse((lat, lon), language="en", zoom=10)
        city = location.raw.get('address', {}).get('city') \
               or location.raw.get('address', {}).get('town') \
               or location.raw.get('address', {}).get('village') \
               or "Sconosciuta"
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        tz = pytz.timezone(tz_name) if tz_name else pytz.utc
        local_time = datetime.now(tz).strftime("%H:%M:%S")
        return city, tz_name, local_time
    except:
        return "Sconosciuta", "UTC", datetime.utcnow().strftime("%H:%M:%S")

# ----------------------
# DATI ISS
# ----------------------
lat, lon = get_iss()
if lat is None:
    st.error("Impossibile ottenere i dati ISS")
    st.stop()

st.session_state.track.append([lat, lon])
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
# MAPPA FOLIUM
# ----------------------
m = folium.Map(location=[lat, lon], zoom_start=2, tiles=tile_style)

# Traiettoria
if len(st.session_state.track) > 1:
    folium.PolyLine(st.session_state.track, color="cyan", weight=2.5, opacity=0.8).add_to(m)

# ISS come pallino arancione
folium.CircleMarker(
    location=[lat, lon],
    radius=8,
    color="orange",
    fill=True,
    fill_color="orange",
).add_to(m)

# Visualizza la mappa su Streamlit
st_data = st_folium(m, width=900, height=500)

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

# ----------------------
# CITTÀ SORVOLATA E ORARIO LOCALE
# ----------------------
st.subheader("🏙️ Città sorvolata")
city, tz_name, local_time = get_city_and_time(lat, lon)
col_city, col_tz, col_time = st.columns(3)
col_city.metric("Città più vicina", city)
col_tz.metric("Fuso orario", tz_name)
col_time.metric("Orario locale", local_time)
