import folium
import streamlit as st
from streamlit_folium import folium_static
from folium.plugins import (
    MiniMap, MousePosition, Fullscreen, MeasureControl, Draw, LocateControl
)
import requests
import re
import time
import zipfile
import io
import json
from pyproj import Transformer

# --- Streamlit Page Setup ---
st.set_page_config(page_title='Smart Njira', layout='centered')
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(to right, #e0eafc, #cfdef3);
    }

    .route-card {
        background: rgba(255, 255, 255, 0.85);
        border-radius: 10px;
        padding: 12px;
        margin: 10px 0;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }

    .gradient-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
        -webkit-background-clip: text;
        color: transparent;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="gradient-header">Smart Njira 🌍</h1>', unsafe_allow_html=True)
st.caption("Plan routes using coordinates or place names. Built with OpenRouteService & OSM.")

# --- Session State for History ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- API Key ---
ORS_API_KEY = st.secrets.get('ORS_API_KEY')
if not ORS_API_KEY:
    st.error("Missing OpenRouteService API key.")
    st.stop()

# --- Coordinate System ---
crs_choice = st.selectbox("📐 Coordinate System", ["WGS 84 (Lat/Lon)", "UTM Zone 36S"])
crs_code = "EPSG:4326" if "WGS" in crs_choice else "EPSG:32736"

# --- Parse input as coords or name ---
def parse_location(text):
    pattern = r'^\s*(-?\d+\.?\d*),\s*(-?\d+\.?\d*)\s*$'
    match = re.match(pattern, text)
    if match:
        x, y = float(match.group(1)), float(match.group(2))
        if crs_code != "EPSG:4326":
            transformer = Transformer.from_crs(crs_code, "EPSG:4326", always_xy=True)
            x, y = transformer.transform(x, y)
        return y, x
    else:
        params = {'api_key': ORS_API_KEY, 'text': text}
        r = requests.get('https://api.openrouteservice.org/geocode/search', params=params)
        if r.status_code == 200 and r.json().get('features'):
            x, y = r.json()['features'][0]['geometry']['coordinates']
            return (y, x)
    return None

# --- Get Directions ---
def get_directions(origin_coords, dest_coords, mode):
    mode_dict = {
        'Car': 'driving-car',
        'Walk': 'foot-walking',
        'Bike': 'cycling-regular'
    }
    url = f"https://api.openrouteservice.org/v2/directions/{mode_dict[mode]}"
    params = {
        'api_key': ORS_API_KEY,
        'start': f"{origin_coords[1]},{origin_coords[0]}",
        'end': f"{dest_coords[1]},{dest_coords[0]}"
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        data = r.json()
        route = data['features'][0]['geometry']['coordinates']
        geojson = data['features'][0]
        route_xy = [(y, x) for x, y in route]
        summary = data['features'][0]['properties']['summary']
        distance_km = round(summary['distance'] / 1000, 2)
        duration_min = round(summary['duration'] / 60)
        tooltip = f"Distance: {distance_km} km | Duration: {duration_min // 60}h {duration_min % 60}m"
        return route_xy, tooltip, distance_km, duration_min, geojson
    else:
        st.error(f"Routing failed: {r.status_code} – {r.text}")
        return [], "", 0, 0, {}

# --- Tabs ---
tab1, tab2 = st.tabs(["🧭 Plan Route", "📜 History"])

with tab1:
    st.markdown("### 🗺️ Enter Route Details")

    origin = st.text_input("🟢 Origin", placeholder="Lilongwe or -14.0, 33.8")
    destination = st.text_input("🔴 Destination", placeholder="Blantyre or -15.8, 35.0")
    mode = st.selectbox("🚗 Mode of Travel", ["Car", "Walk", "Bike"])
    go = st.button("✨ Get Route")
    placeholder = st.empty()

    # --- Create Map ---
    m = folium.Map(location=[-13.5, 34.0], zoom_start=6, tiles=None)
    folium.TileLayer('OpenStreetMap', attr='© OpenStreetMap contributors').add_to(m)
    folium.TileLayer('CartoDB positron', attr='CartoDB').add_to(m)
    folium.TileLayer('CartoDB dark_matter', attr='CartoDB').add_to(m)
    folium.LayerControl().add_to(m)

    Fullscreen().add_to(m)
    MiniMap(toggle_display=True).add_to(m)
    MeasureControl(primary_length_unit='kilometers').add_to(m)
    MousePosition().add_to(m)
    LocateControl().add_to(m)
    Draw(export=True).add_to(m)
    folium.LatLngPopup().add_to(m)

    origin_coords = parse_location(origin) if origin else None
    dest_coords = parse_location(destination) if destination else None

    if origin_coords:
        folium.Marker(origin_coords, icon=folium.Icon(color='green', icon='play', prefix='fa')).add_to(m)
    if dest_coords:
        folium.Marker(dest_coords, icon=folium.Icon(color='red', icon='flag', prefix='fa')).add_to(m)

    if origin_coords and dest_coords:
        m.fit_bounds([origin_coords, dest_coords])

    if go and origin_coords and dest_coords:
        with st.spinner("Calculating route..."):
            time.sleep(1.5)
            route_xy, tooltip, distance_km, duration_min, geojson = get_directions(origin_coords, dest_coords, mode)

        if route_xy:
            st.success(
                f"**{distance_km} km**, approx **{duration_min // 60}h {duration_min % 60}m** by {mode.lower()}"
            )

            folium.PolyLine(route_xy, tooltip=tooltip, color="#3399ff", weight=6, opacity=0.8).add_to(m)

            m.save("directions.html")
            geojson_data = json.dumps({
                "type": "FeatureCollection",
                "features": [geojson]
            }, indent=2)
            with open("route.geojson", "w") as gj:
                gj.write(geojson_data)

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                zip_file.write("directions.html")
                zip_file.writestr("route.geojson", geojson_data)
            zip_buffer.seek(0)

            st.download_button("⬇️ Download HTML Map", open("directions.html", "rb"), "directions.html")
            st.download_button("⬇️ Download Route (.zip)", zip_buffer, "route_files.zip")

            st.session_state.history.append({
                'origin': origin,
                'destination': destination,
                'mode': mode,
                'distance': distance_km,
                'duration': duration_min
            })

    folium_static(m, width=800, height=600)

# --- TAB 2: History ---
with tab2:
    st.subheader("🕘 Last 5 Routes")
    if st.session_state.history:
        for i, h in enumerate(reversed(st.session_state.history[-5:]), 1):
            d = h['duration']
            st.markdown(
                f"""<div class='route-card'>
                    <strong>{i}. {h['origin']} ➡️ {h['destination']}</strong><br>
                    Mode: {h['mode']}<br>
                    Distance: {h['distance']} km<br>
                    Time: {d // 60}h {d % 60}m
                </div>""", unsafe_allow_html=True
            )
        if st.button("🧹 Clear History"):
            st.session_state.history = []
            st.success("History cleared.")
    else:
        st.info("No routes yet.")

# --- Branding Footer ---
st.markdown("""
<div style='text-align:center; margin-top: 40px; color: #666; font-size: 14px;'>
    🚀 Built by <strong>Leyard Kamanga</strong> | Powered by Streamlit & OSM
</div>
""", unsafe_allow_html=True)
