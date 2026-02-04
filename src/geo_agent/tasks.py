from crewai import Task, Agent
from .tools import (
    geocode_from_dataset_tool,
    buffer_point_tool,
    filter_dataset_tool,
    render_map_tool
)
import os

os.makedirs("output", exist_ok=True)

geo_agent = Agent(
    role="Geospatial & Mining Expert",
    goal=(
        "Given a Peruvian province/city and radius, geocode, create buffer, "
        "filter mining concessions, and generate an interactive map with summary."
    ),
    backstory="Expert in geospatial analysis for Peru and mining concessions.",
    tools=[
        geocode_from_dataset_tool,
        buffer_point_tool,
        filter_dataset_tool,
        render_map_tool
    ],
    tool_dependencies={
        "buffer_point_tool": "geocode_from_dataset_tool",
        "filter_dataset_tool": "buffer_point_tool",
        "render_map_tool": "filter_dataset_tool"
    },
    verbose=True
)

task_geocode = Task(
    description=(
        "Geocode a Peruvian province or city mentioned in the user {query} "
        "and include the provided radius in km. "
        "Return only the JSON result containing latitude, longitude, display_name, address, and radius_km."
    ),
    expected_output="Valid JSON with 'latitude', 'longitude', 'display_name', 'address', and 'radius_km' fields",
    output_file="output/jsons/geocode_result.json",
    agent=geo_agent,  #
)

task_buffer = Task(
    description=(
        "Create a circular buffer around the point from the geocode step "
        "using the provided radius in km. "
        "Return only the GeoJSON of the buffer."
    ),
    expected_output="GeoJSON FeatureCollection of a true circular buffer",
    input_file="output/jsons/geocode_result.json",
    output_file="output/jsons/buffer_geojson.json",
    agent=geo_agent,  # uses buffer_point_tool
)

task_filter = Task(
    description=(
        "Filter mining concessions that intersect the buffer GeoJSON from the previous step. "
        "Return ONLY the resulting GeoJSON."
    ),
    expected_output="GeoJSON FeatureCollection of matching mining concessions",
    input_file="output/jsons/buffer_geojson.json",
    output_file="output/jsons/filtered_concessions.json",
    agent=geo_agent,  # uses filter_dataset_tool
    context=[task_geocode, task_buffer]
)


task_render_map = Task(
    description=(
        "Create a final interactive Folium map showing:\n"
        "- The center point\n"
        "- The circular buffer\n"
        "- Filtered mining concessions\n\n"
        "Save the map as an HTML file and return ONLY the file path."
    ),
    expected_output="Path to the saved interactive HTML map",
    agent=geo_agent,  # agent that owns render_map_tool
    context=[task_geocode, task_buffer, task_filter],
)
