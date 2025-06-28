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

# =============================================
# 🚀 INVESTOR-GRADE UI CONFIGURATION
# =============================================
st.set_page_config(
    page_title='Smart Njira | Geospatial AI',
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 💎 Premium Geospatial UI Styling
st.markdown(f"""
<style>
    /* 🌍 Global Geospatial Theme */
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(145deg, #000428 0%, #004e92 100%);
    }}
    
    /* 🛰️ Professional Sidebar */
    [data-testid="stSidebar"] {{
        background: rgba(0,20,40,0.9) !important;
        backdrop-filter: blur(5px);
        border-right: 1px solid rgba(0,150,255,0.2);
    }}
    
    /* 🏙️ Urban Typography */
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Montserrat', sans-serif;
        color: #ffffff !important;
        letter-spacing: 0.5px;
    }}
    
    /* 🛣️ Input Fields */
    .stTextInput>div>div>input {{
        background: rgba(0,30,60,0.7) !important;
        color: white !important;
        border: 1px solid rgba(0,150,255,0.3) !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }}
    
    /* 🚦 Action Buttons */
    .stButton>button {{
        background: linear-gradient(45deg, #00b4db, #0083b0) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(0,180,219,0.3);
        transition: all 0.3s !important;
    }}
    
    .stButton>button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0,180,219,0.4) !important;
    }}
    
    /* 🗺️ Map Container */
    .folium-map {{
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        border: 1px solid rgba(0,150,255,0.2);
    }}
    
    /* 📊 Data Cards */
    .route-card {{
        background: rgba(0,40,80,0.7) !important;
        border-radius: 10px !important;
        padding: 16px !important;
        margin: 12px 0 !important;
        border-left: 4px solid #00b4db !important;
        backdrop-filter: blur(5px);
    }}
    
    /* 🏢 Modern Tabs */
    [data-baseweb="tab-list"] {{
        gap: 5px !important;
    }}
    
    [data-baseweb="tab"] {{
        background: rgba(0,40,80,0.5) !important;
        color: rgba(255,255,255,0.7) !important;
        padding: 10px 20px !important;
        border-radius: 8px 8px 0 0 !important;
        border: none !important;
        transition: all 0.3s !important;
    }}
    
    [aria-selected="true"] {{
        background: linear-gradient(90deg, #00b4db, #0083b0) !important;
        color: white !important;
    }}
    
    /* 🚀 Floating Elements */
    .floating-card {{
        box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0,150,255,0.2);
    }}
</style>

<link href='https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap' rel='stylesheet'>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
""", unsafe_allow_html=True)

# =============================================
# 🛰️ SIDEBAR - CONTROL CENTER
# =============================================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h2 style="margin-bottom: 5px; color: #00b4db;">SMART NJIRA</h2>
        <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Geospatial Route Intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎛️ SYSTEM CONTROLS")
    crs_choice = st.selectbox(
        "Coordinate Reference System",
        ["WGS 84 (Lat/Lon)", "UTM Zone 36S"],
        key="coord_system"
    )
    crs_code = "EPSG:4326" if "WGS" in crs_choice else "EPSG:32736"
    
    st.markdown("---")
    st.markdown("### 📡 REAL-TIME DATA")
    st.markdown("""
    <div style="background: rgba(0,60,120,0.3); padding: 15px; border-radius: 8px;">
        <p style="color: rgba(255,255,255,0.8); margin-bottom: 5px;">
        <i class="fas fa-satellite" style="margin-right: 8px; color: #00b4db;"></i> 
        <strong>LIVE FEEDS:</strong></p>
        <p style="color: rgba(255,255,255,0.6); font-size: 0.9rem;">
        • OpenRouteService API<br>
        • OSM Vector Tiles<br>
        • Satellite Positioning
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: rgba(255,255,255,0.5); font-size: 0.8rem;">
        
    </div>
    """, unsafe_allow_html=True)

# =============================================
# 🧠 CORE FUNCTIONALITY (UNCHANGED)
# =============================================
if 'history' not in st.session_state:
    st.session_state.history = []

ORS_API_KEY = st.secrets.get('ORS_API_KEY')
if not ORS_API_KEY:
    st.error("Missing OpenRouteService API key.")
    st.stop()

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

# =============================================
# 🖥️ MAIN INTERFACE - INVESTOR READY
# =============================================
tab1, tab2 = st.tabs(["🌐 ROUTE OPTIMIZER", "📊 JOURNEY ANALYTICS"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🚦 NAVIGATION PARAMETERS")
        
        with st.container():
            st.markdown("#### 🟢 ORIGIN POINT")
            origin = st.text_input(
                "Enter start location",
                placeholder="Lilongwe or -14.0, 33.8",
                key="origin",
                label_visibility="collapsed"
            )
            
            st.markdown("#### 🔴 DESTINATION")
            destination = st.text_input(
                "Enter end location",
                placeholder="Blantyre or -15.8, 35.0",
                key="destination",
                label_visibility="collapsed"
            )
            
            st.markdown("#### 🚙 TRANSPORT MODE")
            mode = st.selectbox(
                "Select travel method",
                ["Car", "Walk", "Bike"],
                key="travel_mode",
                label_visibility="collapsed"
            )
            
            if st.button("🚀 CALCULATE OPTIMAL ROUTE", key="calculate"):
                st.session_state.calculate_route = True
    
    with col2:
        st.markdown("### 🗺️ INTERACTIVE GEOSPATIAL VIEW")
        
        # 🌟 Premium Map Configuration
        m = folium.Map(location=[-13.5, 34.0], zoom_start=6, tiles=None)
        
        # 🏙️ Professional Tile Layers
        folium.TileLayer(
            'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
            attr='CartoDB.DarkMatter',
            name='Night Mode',
            max_zoom=19
        ).add_to(m)
        
        folium.TileLayer(
            'OpenStreetMap',
            attr='OpenStreetMap',
            name='Street View'
        ).add_to(m)
        
        folium.TileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri.WorldImagery',
            name='Satellite'
        ).add_to(m)
        
        # 🛠️ Professional Plugins
        Fullscreen().add_to(m)
        MiniMap(toggle_display=True, position="bottomleft").add_to(m)
        MeasureControl(position="topright", primary_length_unit='kilometers').add_to(m)
        MousePosition(position="bottomright").add_to(m)
        LocateControl(position="topleft").add_to(m)
        Draw(export=True, position="topright").add_to(m)
        
        # 🏁 Layer Control with Style
        folium.LayerControl(position="topright", collapsed=False).add_to(m)
        
        # Process locations
        origin_coords = parse_location(origin) if origin else None
        dest_coords = parse_location(destination) if destination else None
        
        # 🎯 Markers with Professional Icons
        if origin_coords:
            folium.Marker(
                origin_coords,
                icon=folium.Icon(color='green', icon='location-dot', prefix='fa'),
                popup=f"<b>ORIGIN:</b> {origin}",
                tooltip="Start Point"
            ).add_to(m)
        
        if dest_coords:
            folium.Marker(
                dest_coords,
                icon=folium.Icon(color='red', icon='flag-checkered', prefix='fa'),
                popup=f"<b>DESTINATION:</b> {destination}",
                tooltip="End Point"
            ).add_to(m)
        
        if origin_coords and dest_coords:
            m.fit_bounds([origin_coords, dest_coords])
        
        if hasattr(st.session_state, 'calculate_route') and origin_coords and dest_coords:
            with st.spinner("ANALYZING OPTIMAL PATH..."):
                time.sleep(1.5)
                route_xy, tooltip, distance_km, duration_min, geojson = get_directions(
                    origin_coords, dest_coords, mode
                )
            
            if route_xy:
                with st.container():
                    st.markdown(f"""
                    <div class="floating-card" style="padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                        <h3 style="margin-top: 0; color: #00b4db;">ROUTE ANALYSIS COMPLETE</h3>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                            <div>
                                <p style="color: rgba(255,255,255,0.7); margin-bottom: 5px;">DISTANCE</p>
                                <h4 style="margin-top: 0; color: white;">{distance_km} km</h4>
                            </div>
                            <div>
                                <p style="color: rgba(255,255,255,0.7); margin-bottom: 5px;">DURATION</p>
                                <h4 style="margin-top: 0; color: white;">{duration_min // 60}h {duration_min % 60}m</h4>
                            </div>
                            <div>
                                <p style="color: rgba(255,255,255,0.7); margin-bottom: 5px;">MODE</p>
                                <h4 style="margin-top: 0; color: white;">{mode.upper()}</h4>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # 🛣️ Route Visualization
                folium.PolyLine(
                    route_xy,
                    tooltip=tooltip,
                    color="#00b4db",
                    weight=5,
                    opacity=0.9,
                    line_cap='round'
                ).add_to(m)
                
                # 💾 Export Functionality
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
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "💾 DOWNLOAD MAP VISUALIZATION",
                        open("directions.html", "rb"),
                        "smartnjira_route.html",
                        key="dl_html"
                    )
                with col2:
                    st.download_button(
                        "📦 EXPORT GEOSPATIAL DATA",
                        zip_buffer,
                        "smartnjira_data_package.zip",
                        key="dl_zip"
                    )
                
                st.session_state.history.append({
                    'origin': origin,
                    'destination': destination,
                    'mode': mode,
                    'distance': distance_km,
                    'duration': duration_min
                })
        
        folium_static(m, width=900, height=600)

with tab2:
    st.markdown("### 📈 ROUTE ANALYTICS")
    
    if st.session_state.history:
        for i, h in enumerate(reversed(st.session_state.history[-5:]), 1):
            d = h['duration']
            st.markdown(f"""
            <div class="route-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin-bottom: 5px; color: white;">ROUTE #{i}</h4>
                        <p style="color: rgba(255,255,255,0.7); margin-bottom: 5px;">
                        <i class="fas fa-route" style="margin-right: 8px; color: #00b4db;"></i>
                        {h['origin']} → {h['destination']}
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <p style="color: rgba(255,255,255,0.7); margin-bottom: 0;">
                        <i class="fas fa-{h['mode'].lower()}" style="margin-right: 5px;"></i> {h['distance']} km
                        </p>
                        <p style="color: rgba(255,255,255,0.7); margin-bottom: 0;">
                        <i class="fas fa-clock" style="margin-right: 5px;"></i> {d // 60}h {d % 60}m
                        </p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🧹 CLEAR HISTORY", key="clear_history"):
            st.session_state.history = []
            st.success("Analytics data cleared.")
    else:
        st.markdown("""
        <div style="background: rgba(0,60,120,0.3); padding: 40px; border-radius: 12px; text-align: center;">
            <i class="fas fa-route" style="font-size: 2.5rem; color: rgba(0,180,219,0.3); margin-bottom: 20px;"></i>
            <h4 style="color: rgba(255,255,255,0.5);">NO ROUTE DATA AVAILABLE</h4>
            <p style="color: rgba(255,255,255,0.3);">Calculated routes will appear here</p>
        </div>
        """, unsafe_allow_html=True)

# =============================================
# 🚀 SYSTEM STATUS BAR
# =============================================
st.markdown("""
<div style="position: fixed; bottom: 0; left: 0; right: 0; background: rgba(0,20,40,0.9); padding: 10px 20px; text-align: center; border-top: 1px solid rgba(0,150,255,0.2); z-index: 999;">
    <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 0.8rem; letter-spacing: 0.5px;">
    <i class="fas fa-satellite-dish" style="margin-right: 8px;"></i> BUILT BY LEYARD BOKOLA KAMANGA
    </p>
</div>
""", unsafe_allow_html=True)