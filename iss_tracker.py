import requests
import folium
import time
from IPython.display import display, clear_output

# URL API ISS
URL = "http://api.open-notify.org/iss-now.json"

# Lista per salvare il percorso
percorso = []

# Numero aggiornamenti (puoi aumentarlo)
UPDATE_COUNT = 2000000

# Intervallo aggiornamento (secondi)
INTERVAL = 30


def get_iss_position():
    response = requests.get(URL)
    data = response.json()

    lat = float(data['iss_position']['latitude'])
    lon = float(data['iss_position']['longitude'])

    return lat, lon


def is_over_italy(lat, lon):
    # Bounding box Italia (approssimato)
    return 36 < lat < 47 and 6 < lon < 19


def create_map(percorso, lat, lon):
    mappa = folium.Map(
        location=[lat, lon],
        zoom_start=3,
        tiles="OpenStreetMap"
    )

    # Marker ISS
    folium.Marker(
        [lat, lon],
        tooltip="ISS - posizione attuale",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(mappa)

    # Percorso tracciato
    if len(percorso) > 1:
        folium.PolyLine(
            percorso,
            color="red",
            weight=2
        ).add_to(mappa)

    return mappa


def main():
    print("🚀 Avvio ISS Tracker...\n")

    for i in range(UPDATE_COUNT):
        lat, lon = get_iss_position()

        percorso.append([lat, lon])

        # Pulizia output per effetto live
        clear_output(wait=True)

        print(f"🛰️ Aggiornamento #{i+1}")
        print(f"Latitudine: {lat}")
        print(f"Longitudine: {lon}")

        # Controllo Italia
        if is_over_italy(lat, lon):
            print("🇮🇹 ISS sopra l'Italia!")

        # Creazione mappa
        mappa = create_map(percorso, lat, lon)

        display(mappa)

        # Attesa
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()