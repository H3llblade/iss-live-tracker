import streamlit as st
import requests
import pydeck as pdk
import math
from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

st.set_page_config(layout="wide", page_title="NASA ISS Tracker - Fluido")

st.title("🛰️ NASA ISS Tracker - PyDeck Fluido")

# ----------------------
# SESSION STATE
# ----------------------
if "track" not in st.session_state:
    st.session_state.track = []

if "last" not in st.session_state:
    st.session_state.last = None

# ----------------------
# FUNZIONI
# ----------------------
def get_iss():
    try:
        data = requests.get("http://api.open-notify.org/iss-now.json", timeout=5).json()
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
    get_color=[255, 165, 0],
    get_radius=250000,
)

# TRAIETTORIA
path_layer = pdk.Layer(
    "PathLayer",
    data=[{"path": st.session_state.track}],
    get_path="path",
    get_color=[0, 255, 255],
    width_scale=20,
    width_min_pixels=2,
)

# VIEW
view_state = pdk.ViewState(
    latitude=lat,
    longitude=lon,
    zoom=2,
    pitch=45,
)

deck = pdk.Deck(
    layers=[path_layer, iss_layer],
    initial_view_state=view_state,
    map_style="https://basemaps.cartocdn.com/gl/positron/{z}/{x}/{y}{r}.png",
    tooltip={"text": "ISS Position\nLat: {lat}\nLon: {lon}"}
)

st.pydeck_chart(deck)

# ----------------------
# TELEMETRIA
# ----------------------
st.subheader("📡 Telemetria ISS")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Latitudine", f"{lat:.4f}°")
col2.metric("Longitudine", f"{lon:.4f}°")
col3.metric("Velocità", f"{speed:.0f} km/h")
col4.metric("Aggiornamento", datetime.utcnow().strftime("%H:%M:%S"))

# ----------------------
# CITTÀ SORVOLATA
st.subheader("🏙️ Città sorvolata")
city, tz_name, local_time = get_city_and_time(lat, lon)
col_city, col_tz, col_time = st.columns(3)
col_city.metric("Città più vicina", city)
col_tz.metric("Fuso orario", tz_name)
col_time.metric("Orario locale", local_time)
