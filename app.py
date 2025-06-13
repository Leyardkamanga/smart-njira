import streamlit as st
import folium
import requests
from streamlit_folium import folium_static
from folium.plugins import MiniMap, MousePosition, Fullscreen

# --- Setup ---
st.set_page_config(page_title='Smart Njira', layout='centered')
st.title('🗺️ Smart Njira – Global Route Planner')

# --- Tabs ---
tab1, tab2 = st.tabs(["📍 Plan Route", "🕘 Route History"])

# --- Load API Key ---
try:
    ORS_API_KEY = st.secrets['ORS_API_KEY']
except KeyError:
    st.error("🔑 ORS_API_KEY not found in secrets. Please configure it.")
    st.stop()

# --- Session State for Route History ---
if 'route_history' not in st.session_state:
    st.session_state.route_history = []

# --- Utility: Format time ---
def format_time(minutes):
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours}h {mins}m" if hours else f"{mins}m"

# --- Utility: Geocode Location ---
@st.cache_data
def geocode(query):
    params = {'api_key': ORS_API_KEY, 'text': query}
    r = requests.get('https://api.openrouteservice.org/geocode/search', params=params)
    if r.status_code == 200:
        data = r.json()
        if data['features']:
            x, y = data['features'][0]['geometry']['coordinates']
            return (y, x)
        else:
            st.error(f"❌ No results for: {query}")
    else:
        st.error("❌ Geocoding failed.")
    return None

# --- Utility: Get Directions ---
def get_directions(origin_name, destination_name, mode):
    origin_coords = geocode(origin_name)
    destination_coords = geocode(destination_name)

    if not origin_coords or not destination_coords:
        return [], None, 0, 0

    url = f"https://api.openrouteservice.org/v2/directions/{mode}"
    params = {
        "api_key": ORS_API_KEY,
        "start": f"{origin_coords[1]},{origin_coords[0]}",
        "end": f"{destination_coords[1]},{destination_coords[0]}"
    }
    r = requests.get(url, params=params)

    if r.status_code == 200:
        data = r.json()
        route = data['features'][0]['geometry']['coordinates']
        summary = data['features'][0]['properties']['summary']
        route_xy = [(y, x) for x, y in route]
        distance_km = round(summary['distance'] / 1000, 2)
        duration_min = round(summary['duration'] / 60, 2)
        tooltip = f'{distance_km} km | {format_time(duration_min)}'
        return route_xy, tooltip, distance_km, duration_min
    else:
        st.error("❌ Routing failed.")
        return [], None, 0, 0

# --- Tab 1: Route Planner ---
with tab1:
    st.markdown("Plan your route using [OpenRouteService](https://openrouteservice.org/) and OpenStreetMap.")

    # Input Fields
    origin = st.text_input('🟢 Origin (e.g., Lilongwe, Malawi)')
    destination = st.text_input('🔴 Destination (e.g., Cape Town, South Africa)')
    mode_label = st.selectbox('Travel Mode', ['Car', 'Walk', 'Bike'])
    button = st.button('🧭 Get Directions')
    placeholder = st.empty()

    # Convert to ORS format
    mode_dict = {
        'Car': 'driving-car',
        'Walk': 'foot-walking',
        'Bike': 'cycling-regular'
    }
    selected_mode = mode_dict[mode_label]

    # Setup base map
    m = folium.Map(location=[0, 0], zoom_start=2, tiles='OpenStreetMap')
    MiniMap(toggle_display=True).add_to(m)
    Fullscreen().add_to(m)
    MousePosition().add_to(m)

    # Add Markers if input provided
    origin_coords = geocode(origin) if origin else None
    destination_coords = geocode(destination) if destination else None

    if origin_coords:
        folium.Marker(origin_coords, popup=origin,
                      icon=folium.Icon(color='green', icon='play')).add_to(m)
    if destination_coords:
        folium.Marker(destination_coords, popup=destination,
                      icon=folium.Icon(color='red', icon='flag')).add_to(m)
    if origin_coords and destination_coords:
        m.fit_bounds([origin_coords, destination_coords])

    # Button Logic
    if button:
        route_xy, tooltip, distance_km, duration_min = get_directions(origin, destination, selected_mode)

        if route_xy:
            folium.PolyLine(route_xy, tooltip=tooltip, color='blue', weight=5).add_to(m)

            st.success(
                f"Distance from **{origin}** to **{destination}** is **{distance_km} km**, estimated time: **{format_time(duration_min)}** by {mode_label.lower()}."
            )

            # Save to history
            st.session_state.route_history.append({
                "origin": origin,
                "destination": destination,
                "mode": mode_label,
                "distance": distance_km,
                "duration": format_time(duration_min)
            })

            # Save map and offer download
            m.save('directions.html')
            with open('directions.html', 'rb') as f:
                placeholder.download_button("⬇️ Download Map", data=f, file_name="directions.html")

    # Display map
    folium_static(m, width=800)

# --- Tab 2: History ---
with tab2:
    st.subheader("📌 Previous Routes")

    if st.session_state.route_history:
        for i, h in enumerate(reversed(st.session_state.route_history[-10:]), 1):
            st.markdown(
                f"**{i}.** {h['origin']} ➡️ {h['destination']} via *{h['mode']}* — "
                f"{h['distance']} km, {h['duration']}"
            )
        if st.button("🧹 Clear History"):
            st.session_state.route_history = []
            st.success("History cleared.")
    else:
        st.info("No routes searched yet.")
