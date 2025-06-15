# 🗺️ Smart Njira – Global Route Planner

Smart Njira is a Streamlit web app that allows you to plan routes anywhere in the world using OpenRouteService and OpenStreetMap data. It supports multiple travel modes like driving, walking, and biking, and displays the route on an interactive map powered by Folium.

---

## Features

- **Plan Routes:** Input origin and destination locations globally and get driving, walking, or biking directions.
- **Interactive Map:** View your route on an embedded Folium map with zoom, fullscreen, and minimap support.
- **Route Details:** See estimated distance and travel time for your selected route.
- **Route History:** Keep track of your last 10 searched routes and clear history as needed.
- **Download Map:** Save your route map as an HTML file for offline use or sharing.

---

## How to Use

1. Enter origin and destination locations (e.g., `Lilongwe, Malawi` or `Cape Town, South Africa`).
2. Select your preferred travel mode: Car, Walk, or Bike.
3. Click **Get Directions** to view the route on the map along with distance and estimated time.
4. Download the route map as an HTML file if you want to save it.
5. Switch to the **Route History** tab to view your recent searches.

---

## Requirements

- Python 3.7+
- Streamlit
- Folium
- streamlit-folium
- Requests

Install dependencies with:

```bash
pip install streamlit folium streamlit-folium requests
