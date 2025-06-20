Smart Njira

**Smart Njira** is an open-source geospatial web app for global route planning using coordinates or place names. Built with **Python**, **Streamlit**, and **Folium**, it provides a simple UI for distance and time estimation, interactive map visualization, real-time location tracking, and more — powered by the OpenRouteService and OpenStreetMap APIs.

The app supports routing for walking, driving, and biking, and is suitable for field mapping, exploration, planning logistics, or educational purposes.

---

## Usage

Smart Njira is designed for ease of use and flexibility. You can input either **place names** (e.g., `"Lilongwe"`) or **latitude/longitude coordinates** (e.g., `-14.0, 34.0`) to define your origin and destination.

### Example 1 – Basic route between two place names

```python
# Example input in app interface
Origin: Mzuzu
Destination: Lilongwe
Mode: Car

Result: The app fetches the best available route, displays it on the map, and estimates distance and travel time.

Example 2 – Using coordinates for precise points

Origin: -14.123, 33.456
Destination: -13.987, 33.765
Mode: Walk

Result: A walking route is calculated between the given GPS points. Coordinates can also be copied from the map by clicking.

Example 3 – Real-time interaction tools

After generating a route, the app also lets you:

View real-time location

Add custom markers

Measure distances or areas

Draw polygons or lines

Switch map basemaps (light, terrain, dark)


Example 4 – Export and share

After route generation:

You can download an HTML map file with the route

View search history

Clear previous sessions



---

Note

The app uses OpenRouteService's free API tier, so usage is limited by daily quota.

You need an internet connection to use the app — it fetches data in real time from OSM and ORS.

Location data and map tiles are based on WGS 84 (EPSG:4326).



---

Installation

Clone the repository and install dependencies:

git clone https://github.com/Leyardkamanga/smart-njira.git
cd smart-njira
pip install -r requirements.txt

Add your API key to .streamlit/secrets.toml:

# .streamlit/secrets.toml
ORS_API_KEY = "your_api_key_here"

Launch the app locally:

streamlit run app.py


---

Functionality Overview

Feature	Description

Global Routing	Plan routes using names or coordinates
Travel Modes	Car, Walk, Bike
Coordinate Input Support	Accepts both decimal degrees and text inputs
Downloadable Maps	Export HTML route maps
Real-Time Location	Locate user via GPS/browser
Layer Control	Switch between dark, terrain, light tiles
Measurement Tools	Area, distance, marker, drawing tools
Route History	Tracks and clears past routes



---

Credits

Developer: Leyard Kamanga
Email: kamangaleyard68@gmail.com
GitHub: @Leyardkamanga
Map data: OpenStreetMap
Routing engine: OpenRouteService


---

References

[1] OpenStreetMap contributors. (n.d.). OpenStreetMap. Retrieved from https://www.openstreetmap.org

[2] OpenRouteService. (n.d.). Location-based services by HeiGIT. Retrieved from https://openrouteservice.org



