import streamlit as st
import requests
import plotly.graph_objects as go
import math
from streamlit_autorefresh import st_autorefresh

# ----------------------
# CONFIG
# ----------------------
st.set_page_config(layout="wide")
st.title("🛰️ ISS ORBITAL TRACKER — SPACE MODE")

# Auto refresh ogni 5 secondi (più fluido)
st_autorefresh(interval=5000, key="refresh")

URL = "http://api.open-notify.org/iss-now.json"

# ----------------------
# FUNZIONE DATI
# ----------------------
def get_iss():
    data = requests.get(URL).json()
    lat = float(data['iss_position']['latitude'])
    lon = float(data['iss_position']['longitude'])
    return lat, lon

# ----------------------
# CONVERSIONE LAT/LON → 3D
# ----------------------
def latlon_to_xyz(lat, lon, r=1):
    lat = math.radians(lat)
    lon = math.radians(lon)

    x = r * math.cos(lat) * math.cos(lon)
    y = r * math.cos(lat) * math.sin(lon)
    z = r * math.sin(lat)

    return x, y, z

# ----------------------
# SESSION STATE
# ----------------------
if "track" not in st.session_state:
    st.session_state.track = []

# ----------------------
# DATI
# ----------------------
lat, lon = get_iss()
st.session_state.track.append((lat, lon))

# Limita punti (performance)
if len(st.session_state.track) > 100:
    st.session_state.track.pop(0)

# ----------------------
# CONVERSIONE TRACK
# ----------------------
xs, ys, zs = [], [], []

for lat_i, lon_i in st.session_state.track:
    x, y, z = latlon_to_xyz(lat_i, lon_i)
    xs.append(x)
    ys.append(y)
    zs.append(z)

# posizione attuale
x, y, z = latlon_to_xyz(lat, lon)

# ----------------------
# GLOBO TERRA
# ----------------------
sphere = go.Surface(
    x=[[math.cos(u)*math.sin(v) for u in [i*0.1 for i in range(63)]] for v in [i*0.1 for i in range(63)]],
    y=[[math.sin(u)*math.sin(v) for u in [i*0.1 for i in range(63)]] for v in [i*0.1 for i in range(63)]],
    z=[[math.cos(v) for u in [i*0.1 for i in range(63)]] for v in [i*0.1 for i in range(63)]],
    colorscale="Blues",
    showscale=False,
    opacity=0.6
)

# ----------------------
# ISS TRACK
# ----------------------
track_line = go.Scatter3d(
    x=xs,
    y=ys,
    z=zs,
    mode='lines',
    line=dict(color='cyan', width=4),
    name="Orbita"
)

# ----------------------
# ISS PUNTO
# ----------------------
iss_point = go.Scatter3d(
    x=[x],
    y=[y],
    z=[z],
    mode='markers',
    marker=dict(size=6, color='red'),
    name="ISS"
)

# ----------------------
# FIGURA
# ----------------------
fig = go.Figure(data=[sphere, track_line, iss_point])

fig.update_layout(
    scene=dict(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        zaxis=dict(visible=False),
        bgcolor="black"
    ),
    margin=dict(l=0, r=0, t=0, b=0)
)

# ----------------------
# OUTPUT
# ----------------------
st.plotly_chart(fig, use_container_width=True)

# ----------------------
# DATI LIVE
# ----------------------
st.subheader("📡 Telemetria")

col1, col2 = st.columns(2)
col1.metric("Latitudine", f"{lat:.4f}")
col2.metric("Longitudine", f"{lon:.4f}")
