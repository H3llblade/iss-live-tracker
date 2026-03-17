import streamlit as st
import requests
import folium
import time
from streamlit_folium import st_folium
from datetime import datetime
import math

# Config pagina
st.set_page_config(
    page_title="ISS Tracker Live",
    layout="wide"
)

st.title("🛰️ ISS Live Tracker")
st.markdown("Tracking in tempo reale della Stazione Spaziale Internazionale")

URL = "http://api.open-notify.org/iss-now.json"

# Funzione per ottenere dati ISS
def get_iss_position():
    response = requests.get(URL)
    data = response.json()

    lat = float(data['iss_position']['latitude'])
    lon = float(data['iss_position']['longitude'])

    return lat, lon

# Calcolo distanza (Haversine)
def distanza(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

# Stato Italia
def sopra_italia(lat, lon):
    return 36 < lat < 47 and 6 < lon < 19

# Stato sessione
if "percorso" not in st.session_state:
    st.session_state.percorso = []

if "last_pos" not in st.session_state:
    st.session_state.last_pos = None

# Aggiornamento automatico
REFRESH_RATE = 30

# Bottone manuale
if st.button("🔄 Aggiorna ora"):
    st.rerun()

# Dati ISS
lat, lon = get_iss_position()
st.session_state.percorso.append([lat, lon])

# Metriche
col1, col2, col3, col4 = st.columns(4)

col1.metric("Latitudine", f"{lat:.4f}")
col2.metric("Longitudine", f"{lon:.4f}")

# Velocità stimata
velocita = 0
if st.session_state.last_pos:
    lat1, lon1 = st.session_state.last_pos
    dist = distanza(lat1, lon1, lat, lon)
    velocita = dist / (REFRESH_RATE / 3600)

col3.metric("Velocità (km/h)", f"{velocita:.0f}")

# Stato Italia
stato = "🇮🇹 Sopra Italia" if sopra_italia(lat, lon) else "🌍 Altrove"
col4.metric("Posizione", stato)

# Salva ultima posizione
st.session_state.last_pos = (lat, lon)

# Mappa
mappa = folium.Map(location=[lat, lon], zoom_start=3)

# Marker
folium.Marker(
    [lat, lon],
    tooltip="ISS",
    icon=folium.Icon(color="red")
).add_to(mappa)

# Percorso
if len(st.session_state.percorso) > 1:
    folium.PolyLine(
        st.session_state.percorso,
        color="red",
        weight=2
    ).add_to(mappa)

st_folium(mappa, width=1000, height=500)

# Timeline
st.subheader("📍 Storico posizioni")

for i, pos in enumerate(st.session_state.percorso[-10:][::-1]):
    st.write(f"{i+1}. {pos}")

# Timestamp
st.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}")

# Auto-refresh
time.sleep(REFRESH_RATE)
st.rerun()
