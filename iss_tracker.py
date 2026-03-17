import streamlit as st
import requests
from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import folium
from streamlit.components.v1 import html

st.set_page_config(layout="wide", page_title="NASA ISS Tracker - OSM")

st.title("🛰️ NASA ISS Tracker - OpenStreetMap")

# ----------------------
# SESSION STATE
# ----------------------
if "track" not in st.session_state:
    st.session_state.track = []

# ----------------------
# SELEZIONE TEMA
# ----------------------
theme = st.selectbox("Seleziona tema mappa", ["Light", "Dark"])
tile_style = "OpenStreetMap" if theme == "Light" else "CartoDB dark_matter"

# ----------------------
# FUNZIONI
# ----------------------
def get_iss():
    try:
        data = requests.get("https://api.wheretheiss.at/v1/satellites/25544", timeout=5).json()
        lat = float(data['latitude'])
        lon = float(data['longitude'])
        altitude = float(data.get('altitude', 420))  # km
        speed = float(data.get('velocity', 27600))   # km/h
        return lat, lon, altitude, speed
    except:
        return None, None, None, None

def get_city_and_time(lat, lon):
    try:
        geolocator = Nominatim(user_agent="iss_tracker")
        location = geolocator.reverse((lat, lon), language="en", zoom=10)
        address = location.raw.get('address', {})
        city = address.get('city') or address.get('town') or address.get('village')
        if not city:
            return "Over Ocean", "UTC", datetime.utcnow().strftime("%H:%M:%S")
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        tz = pytz.timezone(tz_name) if tz_name else pytz.utc
        local_time = datetime.now(tz).strftime("%H:%M:%S")
        return city, tz_name, local_time
    except:
        return "Sconosciuta", "UTC", datetime.utcnow().strftime("%H:%M:%S")

# ----------------------
# OTTIENI DATI ISS
# ----------------------
lat, lon, altitude, speed = get_iss()
if lat is None:
    st.error("Impossibile ottenere i dati ISS")
    st.stop()

# Aggiorna traiettoria
st.session_state.track.append([lat, lon])
if len(st.session_state.track) > 300:
    st.session_state.track.pop(0)

# ----------------------
# CREA MAPPA
# ----------------------
m = folium.Map(location=[lat, lon], zoom_start=2, tiles=tile_style)

# Traiettoria
if len(st.session_state.track) > 1:
    folium.PolyLine(st.session_state.track, color="cyan", weight=2.5, opacity=0.8).add_to(m)

# Pallino arancione ISS
folium.CircleMarker(
    location=[lat, lon],
    radius=8,
    color="orange",
    fill=True,
    fill_color="orange",
).add_to(m)

# Visualizza mappa su Streamlit
html(m._repr_html_(), height=500)

# ----------------------
# TELEMETRIA ISS
# ----------------------
st.subheader("📡 Telemetria ISS")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Latitudine", f"{lat:.4f}°")
col2.metric("Longitudine", f"{lon:.4f}°")
col3.metric("Velocità", f"{speed:.0f} km/h")
col4.metric("Altitudine stimata", f"{altitude:.0f} km")

# ----------------------
# CITTÀ SORVOLATA
st.subheader("🏙️ Città sorvolata")
city, tz_name, local_time = get_city_and_time(lat, lon)
col_city, col_tz, col_time = st.columns(3)
col_city.metric("Città più vicina", city)
col_tz.metric("Fuso orario", tz_name)
col_time.metric("Orario locale", local_time)
