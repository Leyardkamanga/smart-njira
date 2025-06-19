import folium
import streamlit as st
from streamlit_folium import folium_static
from folium.plugins import (
    MiniMap, MousePosition, Fullscreen, MeasureControl, Draw, LocateControl
)
import requests
import re

# --- Page Setup ---
st.set_page_config(page_title='Smart Njira', layout='centered')
st.title('🗺️ Smart Njira – Global Route Planner')

st.markdown("""
Plan your route between any two places in the world using 
[OpenRouteService](https://openrouteservice.org/) and OpenStreetMap data.
""")

# --- Session State for History ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- API Key ---
ORS_API_KEY = st.secrets.get('ORS_API_KEY')
if not ORS_API_KEY:
    st.error("Missing OpenRouteService API key in secrets.")
    st.stop()

# --- Parse coordinates or place name ---
def parse_location(text):
    pattern = r'^\s*(-?\d+\.?\d*),\s*(-?\d+\.?\d*)\s*$'
    match = re.match(pattern, text)
    if match:
        return float(match.group(1)), float(match.group(2))
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
        route_xy = [(y, x) for x, y in route]
        summary = data['features'][0]['properties']['summary']
        distance_km = round(summary['distance'] / 1000, 2)
        duration_min = round(summary['duration'] / 60)
        tooltip = f"Distance: {distance_km} km | Duration: {duration_min // 60}h {duration_min % 60}m"
        return route_xy, tooltip, distance_km, duration_min
    else:
        st.error(f"Routing failed: {r.status_code} – {r.text}")
        return [], "", 0, 0

# --- Tabs ---
tab1, tab2 = st.tabs(["📍 Plan Route", "🕘 Route History"])

# --- TAB 1: Planner ---
with tab1:
    origin = st.text_input('🟢 Origin (e.g., Lilongwe or -14.0, 33.8)')
    destination = st.text_input('🔴 Destination (e.g., Blantyre or -15.8, 35.0)')
    mode = st.selectbox('Travel Mode', ['Car', 'Walk', 'Bike'])
    button = st.button('🧭 Get Directions')
    placeholder = st.empty()

    # Map setup
    m = folium.Map(location=[0, 0], zoom_start=2)
    Fullscreen().add_to(m)
    MiniMap(toggle_display=True).add_to(m)
    MousePosition().add_to(m)
    MeasureControl(primary_length_unit='kilometers').add_to(m)
    LocateControl().add_to(m)
    Draw(export=True).add_to(m)
    folium.LatLngPopup().add_to(m)

    # Tile layers with attribution
    folium.TileLayer(
        'OpenStreetMap',
        attr='© OpenStreetMap contributors'
    ).add_to(m)
    folium.TileLayer(
        'Stamen Terrain',
        attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
    ).add_to(m)
    folium.TileLayer(
        'CartoDB positron',
        attr='Tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
    ).add_to(m)
    folium.TileLayer(
        'CartoDB dark_matter',
        attr='Tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
    ).add_to(m)
    folium.LayerControl().add_to(m)

    # Geocoding
    origin_coords = parse_location(origin) if origin else None
    dest_coords = parse_location(destination) if destination else None

    if origin_coords:
        folium.Marker(origin_coords, popup=origin, icon=folium.Icon(color='green')).add_to(m)
    if dest_coords:
        folium.Marker(dest_coords, popup=destination, icon=folium.Icon(color='red')).add_to(m)

    if origin_coords and dest_coords:
        m.fit_bounds([origin_coords, dest_coords])

    # Get route
    if button and origin_coords and dest_coords:
        route_xy, tooltip, distance_km, duration_min = get_directions(origin_coords, dest_coords, mode)
        if route_xy:
            st.success(
                f"From **{origin}** to **{destination}**: **{distance_km} km**, "
                f"est. time: **{duration_min // 60}h {duration_min % 60}m** by {mode.lower()}."
            )
            folium.PolyLine(route_xy, tooltip=tooltip, color='blue', weight=5).add_to(m)

            # Save and download
            m.save('directions.html')
            with open('directions.html', 'rb') as file:
                placeholder.download_button('⬇️ Download Route Map (HTML)', file, 'directions.html')

            st.session_state.history.append({
                'origin': origin,
                'destination': destination,
                'mode': mode,
                'distance': distance_km,
                'duration': duration_min
            })

    folium_static(m, width=800)

# --- TAB 2: History ---
with tab2:
    st.subheader("🕘 Last 5 Routes")
    if st.session_state.history:
        for i, h in enumerate(reversed(st.session_state.history[-5:]), 1):
            d = h['duration']
            st.markdown(
                f"**{i}.** {h['origin']} ➡️ {h['destination']} "
                f"({h['mode']}) — {h['distance']} km, {d // 60}h {d % 60}m"
            )
        if st.button("🧹 Clear History"):
            st.session_state.history = []
            st.success("History cleared.")
    else:
        st.info("No routes saved yet.")
