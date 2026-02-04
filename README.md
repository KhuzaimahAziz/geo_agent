# Peru Mining Concessions Buffer Tool

**Interactive Geospatial Analysis of Mining Concessions in Peru**  

This project allows users to query Peruvian provinces or cities using natural language, create circular buffers around them, filter mining concessions intersecting the buffer, and generate an interactive Folium map with results. All outputs are saved as JSON and HTML for easy access.  

---

## Features

- Geocode provinces or cities in Peru using a dataset and Geopy for coordinate mapping.  
- Automatically extract **place names** and **radius** from natural language queries.  
- Generate **true circular buffers** using Azimuthal Equidistant projections.  
- Filter mining concessions that intersect the buffer and take out Concessions and Area to display them on the Map.  
- Generate interactive **Folium maps** showing center, buffer, and filtered concessions.  
- Save outputs for each step as JSON and HTML files.  

---

## Dataset

- Dataset of CatastroMinero was used in this project from https://geocatmin.ingemmet.gob.pe/geocatmin/ 

## Challenges

- Tried doing everything locally by setting up Ollama model with 3B parameters. But the outputs were not ideal so switched to OPENAI gpt4mini.

## Gaps

- The output concessions from the agent are of good quality but it is missing some of the mines still which needs further investigation.
- It is not using MCP Server at the moment but it can be integrated with MCP in future.
- The output jsons and maps saving function is not ideal at the moment and need to be more efficient.
- Ideally all the variables should be in pydantic format.
- query should be accepted from the CLI rather then hardcoding in the codebase


## Project Structure

geo_agent/
├─ src/
│ ├─ tools.py # All CrewAI tools (geocode, buffer, filter, render map)
│ ├─ tasks.py # CrewAI tasks and agents
│ ├─ main.py # Command line interface entry point
│ ├─ data/ # Dataset (e.g., mining concessions shapefile)
│ └─ output/ # Output folder for JSON & HTML
├─ pyproject.toml
└─ README.md

Crew_AI Setup:

1. Open API Model setup is needed in enviornment variables to run this project.
## Installation

1. Clone the repository.
2. pip install -e .
3. Run in command line by writing "geo_agent".
4. Change the query in the main.py file.

