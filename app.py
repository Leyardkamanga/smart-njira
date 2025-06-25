import streamlit as st
import folium
from streamlit_folium import folium_static
from folium.plugins import Fullscreen, MiniMap, MeasureControl, Draw, LocateControl, MousePosition
import requests
import re
import json
import pandas as pd
import io
import zipfile

# --- Setup ---
st.set_page_config(page_title='Smart Njira', layout='centered', page_icon="🗺️")
st.title('🗺️ Smart Njira')

# --- Session State Init ---
for key in ['token', 'username', 'history', 'registered', 'route_geojson', 'route_html']:
    if key not in st.session_state:
        st.session_state[key] = None if key != 'history' else []

BASE_URL = "http://127.0.0.1:8000"
ORS_API_KEY = st.secrets.get('ORS_API_KEY')

# --- Parse coords or location name ---
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

# --- Directions API ---
def get_directions(origin_coords, dest_coords, mode):
    mode_dict = {'Car': 'driving-car', 'Walk': 'foot-walking', 'Bike': 'cycling-regular'}
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
        tooltip = f"📏 {distance_km} km | ⏱️ {duration_min // 60}h {duration_min % 60}m"
        geojson = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": route},
            "properties": {
                "mode": mode,
                "distance_km": distance_km,
                "duration_min": duration_min
            }
        }
        return route_xy, tooltip, distance_km, duration_min, geojson
    else:
        st.error(f"Routing failed: {r.status_code} – {r.text}")
        return [], "", 0, 0, None

# --- Save Route to Backend ---
def save_route_to_api(origin, destination, mode, distance_km, duration_min, route_xy):
    if not st.session_state.token:
        st.warning("🔐 Please login to save routes.")
        return
    geojson_route = {
        "type": "LineString",
        "coordinates": [[x, y] for (y, x) in route_xy]
    }
    payload = {
        "origin_name": origin,
        "destination_name": destination,
        "travel_mode": mode,
        "distance_km": distance_km,
        "duration_min": duration_min,
        "geometry": geojson_route
    }
    headers = {"Authorization": f"Token {st.session_state.token}"}
    try:
        response = requests.post(f"{BASE_URL}/api/routes/", json=payload, headers=headers)
        if response.status_code != 201:
            st.warning(f"⚠️ Backend error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"❌ Could not connect to backend: {e}")

# --- MAIN APP ---
if not st.session_state.token:
    # --- LOGIN / REGISTER TAB ---
    tab_login = st.tabs(["🔐 Login / Register"])[0]
    with tab_login:
        auth_mode = st.radio("Choose an action", ["Login", "Register"], horizontal=True)

        if auth_mode == "Login" or st.session_state.registered:
            st.subheader("🔐 Login")
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login"):
                r = requests.post(f"{BASE_URL}/api/auth/token/login/", data={"username": username, "password": password})
                if r.status_code == 200:
                    st.session_state.token = r.json().get("token")
                    st.session_state.username = username
                    st.success(f"✅ Logged in as {username}")
                    st.rerun()
                else:
                    st.error(f"Login failed: {r.text}")

        elif auth_mode == "Register" and not st.session_state.registered:
            st.subheader("👤 Register")
            new_username = st.text_input("New Username", key="reg_user")
            new_password = st.text_input("New Password", type="password", key="reg_pass")
            if st.button("Create Account"):
                r = requests.post(f"{BASE_URL}/api/auth/register/", json={"username": new_username, "password": new_password})
                if r.status_code == 201:
                    st.success("✅ Account created. Please log in.")
                    st.session_state.registered = True
                else:
                    st.error(f"Registration failed: {r.text}")

else:
    # --- ROUTE PLANNER + HISTORY TABS ---
    tab_plan, tab_history = st.tabs(["📍 Plan Route", "📜 Route History"])

    with tab_plan:
        origin = st.text_input('🟢 Origin (e.g., Lilongwe or -14.0, 33.8)')
        destination = st.text_input('🔴 Destination (e.g., Blantyre or -15.8, 35.0)')
        mode = st.selectbox('🚗 Travel Mode', ['Car', 'Walk', 'Bike'])
        button = st.button('🧭 Get Directions')

        m = folium.Map(location=[-13.9, 33.8], zoom_start=6)
        for plugin in [Fullscreen(), MiniMap(), MousePosition(), MeasureControl(), LocateControl(), Draw()]:
            plugin.add_to(m)

        folium.TileLayer('OpenStreetMap', attr='OpenStreetMap').add_to(m)
        folium.TileLayer('CartoDB positron', attr='CartoDB & OSM').add_to(m)
        folium.TileLayer('CartoDB dark_matter', attr='CartoDB & OSM').add_to(m)
        folium.LayerControl().add_to(m)

        origin_coords = parse_location(origin) if origin else None
        dest_coords = parse_location(destination) if destination else None

        if origin_coords:
            folium.Marker(origin_coords, tooltip=origin, icon=folium.Icon(color='green')).add_to(m)
        if dest_coords:
            folium.Marker(dest_coords, tooltip=destination, icon=folium.Icon(color='red')).add_to(m)
        if origin_coords and dest_coords:
            m.fit_bounds([origin_coords, dest_coords])

        if button and origin_coords and dest_coords:
            route_xy, tooltip, distance_km, duration_min, geojson = get_directions(origin_coords, dest_coords, mode)
            if route_xy:
                folium.PolyLine(route_xy, tooltip=tooltip, color='blue', weight=5).add_to(m)
                st.success(f"📍 **{origin} → {destination}**: {distance_km} km, {duration_min // 60}h {duration_min % 60}m by {mode.lower()}")
                save_route_to_api(origin, destination, mode, distance_km, duration_min, route_xy)

                st.session_state.route_geojson = geojson
                st.session_state.route_html = m.get_root().render()

                st.session_state.history.append({
                    'origin': origin,
                    'destination': destination,
                    'mode': mode,
                    'distance': distance_km,
                    'duration': duration_min
                })

        folium_static(m, width=800)

        # --- Download Options ---
        if st.session_state.route_geojson and st.session_state.route_html:
            geojson_data = json.dumps(st.session_state.route_geojson, indent=2)
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr("route.geojson", geojson_data)
                zipf.writestr("route_map.html", st.session_state.route_html)
            zip_buffer.seek(0)
            st.download_button("⬇️ Download GeoJSON + Map (ZIP)", data=zip_buffer, file_name="smart_njira_route.zip", mime="application/zip")

    with tab_history:
        st.subheader("📜 Last 5 Routes (Session History)")
        if st.session_state.history:
            for i, h in enumerate(reversed(st.session_state.history[-5:]), 1):
                d = h['duration']
                st.markdown(f"**{i}.** {h['origin']} ➡️ {h['destination']} ({h['mode']}) — {h['distance']} km, {d // 60}h {d % 60}m")

            if st.button("⬇️ Export History as CSV"):
                df = pd.DataFrame(st.session_state.history)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", data=csv, file_name="route_history.csv", mime="text/csv")

            if st.button("🧹 Clear History"):
                st.session_state.history = []
                st.success("🗑️ History cleared.")
        else:
            st.info("🕐 No routes saved yet.")

    # --- Sidebar Logout ---
    with st.sidebar:
        st.markdown(f"👤 Logged in as **{st.session_state.username}**")
        if st.button("🔓 Logout"):
            for key in ['token', 'username', 'route_geojson', 'route_html']:
                st.session_state[key] = None
            st.success("✅ Logged out.")
            st.rerun()
