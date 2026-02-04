import json
import os
import geopandas as gpd
from shapely.geometry import Point, mapping, shape
from shapely.ops import transform
import folium
from geopy.geocoders import Nominatim
from crewai.tools import tool
from datetime import datetime

DATASET_PATH = "data\CMI_WGS84_17S\CatastroMinero_WGS84_17S_300126.shp"  
dataset_gdf = gpd.read_file(DATASET_PATH)  



@tool
def geocode_from_dataset_tool(user_input: str, radius_km: float = 10.0) -> str:
    """
    Geocode a Peruvian province or city name taken from the user query using a reference dataset and Geopy.

    Steps:
    1. Match the user-provided place name against the 'PROVI' column of the dataset.
    2. If a match is found, use Geopy (Nominatim) to retrieve WGS84 coordinates.
    3. Attach the user-provided radius in kilometers.

    Parameters:
    - user_input (str): Name of a Peruvian province or city.
    - radius_km (float, optional): Radius in kilometers to be used for buffering.

    Returns:
    - str: A JSON string containing:
        {
            "latitude": float,
            "longitude": float,
            "display_name": str,
            "address": str,
            "radius_km": float
        }

    If the location cannot be matched or geocoded, returns a JSON error object.
    """
    match = dataset_gdf[dataset_gdf['PROVI'].str.upper() == user_input.strip().upper()]
    if match.empty:
        return json.dumps({"error": f"No matching province for '{user_input}'"}, ensure_ascii=False)

    province_name = match.iloc[0]['PROVI']
    geolocator = Nominatim(user_agent="peru_buffer_agent")
    location = geolocator.geocode(f"{province_name}, Peru")
    if location is None:
        return json.dumps({"error": f"Geocoding failed for '{province_name}'"}, ensure_ascii=False)

    result = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "display_name": location.address,
        "address": province_name,
        "radius_km": float(radius_km)
    }
    return json.dumps(result, ensure_ascii=False)


@tool
def buffer_point_tool(geocode_json: str) -> dict:
    """
    Create a true circular geographic buffer around a point.

    The function expects a JSON string produced by the geocoding tool containing
    latitude, longitude, and radius_km. It generates a circular buffer using an
    Azimuthal Equidistant projection to ensure metric accuracy.

    Parameters:
    - geocode_json (str): JSON string with:
        {
            "latitude": float,
            "longitude": float,
            "radius_km": float
        }

    Returns:
    - str: A GeoJSON FeatureCollection (JSON string) representing the circular buffer polygon.
    """
    import json
    from shapely.geometry import Point, mapping
    from shapely.ops import transform
    import pyproj

    geocode = json.loads(geocode_json)
    lat = float(geocode["latitude"])
    lon = float(geocode["longitude"])
    radius_km = float(geocode["radius_km"])

    point = Point(lon, lat)

    project = pyproj.Transformer.from_crs(
        "EPSG:4326",
        f"+proj=aeqd +lat_0={lat} +lon_0={lon} +units=m",
        always_xy=True
    ).transform
    project_back = pyproj.Transformer.from_crs(
        f"+proj=aeqd +lat_0={lat} +lon_0={lon} +units=m",
        "EPSG:4326",
        always_xy=True
    ).transform

    buffer = transform(project_back, transform(project, point).buffer(radius_km * 1000))
    buffer = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"radius_km": radius_km}, "geometry": mapping(buffer)}]}
    return json.dumps(buffer, ensure_ascii=False)



@tool
def filter_dataset_tool(json_buffer: str):
    """
    Filter mining concessions that spatially intersect a buffer polygon.

    The function takes a buffer GeoJSON (as a JSON string), converts it to a
    GeoDataFrame, and filters the mining concessions dataset to include only
    features that intersect the buffer geometry.

    Parameters:
    - json_buffer (str): GeoJSON FeatureCollection (JSON string) representing the buffer.

    Returns:
    - str: GeoJSON FeatureCollection (JSON string) of intersecting mining concessions.

    If filtering fails, returns a JSON error object.
    """
    try:

            # Parse buffer GeoJSON string
            buffer_geojson = json.loads(json_buffer)

            # Convert buffer to GeoDataFrame
            buffer_geom = shape(buffer_geojson["features"][0]["geometry"])
            buffer_gdf = gpd.GeoDataFrame(
                geometry=[buffer_geom],
                crs="EPSG:4326"
            )

            # Ensure dataset CRS matches
            if dataset_gdf.crs != "EPSG:4326":
                dataset = dataset_gdf.to_crs("EPSG:4326")
            else:
                dataset = dataset_gdf

            # Spatial intersection
            filtered = dataset[dataset.geometry.intersects(buffer_gdf.geometry.iloc[0])]

            # Convert all non-geometry columns to string (GeoJSON-safe)
            for col in filtered.columns:
                if col != "geometry":
                    filtered[col] = filtered[col].astype(str)

            # Return GeoJSON
            return filtered.to_json()

    except Exception as e:
            return json.dumps({"error": str(e)})

@tool
def render_map_tool(
    geocode_json: str,
    buffer_geojson: str,
    matches_geojson: str,
    output_dir: str = "output/maps"
) -> str:
    """
    Create and save an interactive Folium map showing:
    - Center point
    - Buffer polygon
    - Filtered mining concessions

    The map is automatically named based on the location
    (e.g., 'Santa' → santa_map.html).

    Returns:
    - str: Path to the saved HTML file
    """
    import json
    import os
    import folium

    # Parse inputs
    center = json.loads(geocode_json, strict=False)
    buffer_fc = json.loads(buffer_geojson, strict=False)
    matches_fc = json.loads(matches_geojson, strict=False)

    lat = float(center["latitude"])
    lon = float(center["longitude"])

    # ---- filename logic (NEW) ----
    place_name = center.get("display_name", "map")
    safe_name = place_name.lower().replace(" ", "_")
    filename = f"{safe_name}_map.html"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, filename)
    # --------------------------------

    # Initialize map
    m = folium.Map(location=[lat, lon], zoom_start=8)

    # Center marker
    folium.Marker(
        location=[lat, lon],
        popup=place_name,
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(m)

    # Buffer layer
    folium.GeoJson(
        buffer_fc,
        name="Search Buffer",
        style_function=lambda _: {
            "color": "blue",
            "fillOpacity": 0.15,
            "weight": 2,
        },
    ).add_to(m)

    # Mining concessions layer (only if present)
    if matches_fc.get("features"):
        folium.GeoJson(
            matches_fc,
            name="Mining Concessions",
            tooltip=folium.GeoJsonTooltip(
                fields=["CONCESION", "HASDATUM"],
                aliases=["Concession", "Area (ha)"],
            ),
            style_function=lambda _: {
                "color": "green",
                "fillColor": "green",
                "fillOpacity": 0.5,
                "weight": 2,
            },
        ).add_to(m)

    folium.LayerControl().add_to(m)

    m.save(output_file)
    return output_file


