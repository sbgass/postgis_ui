# PostGIS Sandbox

**PostGIS Sandbox** is a simple `streamlit` web application for visualizing and transforming geospatial data on an interactive dashboard. It uses a PostGIS backend provisioned by `docker-compose` for executing the geospatial functions, and streamlit with streamlit-folium for a simple UI and map rendering. The Python dependencies are managed with `uv`.  

---

## Motivation

Some PostGIS functions can be counter-intuitive, and their documentation lacking, so it's helpful to visualize certain transformations on a map. This app lets you draw your own geometries and write the sql query to see the transformation that the geospatial function performs. 

### How To: 
- Draw or paste geometries (points, polygons, etc.) on the map to add them to the database. 
- Write and run a PostGIS SQL query to transform these geometries 
- The query results are visualized directly on the same map (in red)
- Great for rapidly prototyping and debuging spatial SQL functions

---

## Quick Start

### Prerequisites

- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) or podman and podman compose to run the PostGIS database. 
- [uv](https://lukeautry.com/uv/) to run the streamlit application. 

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/postgis_ui.git
cd postgis_ui
```

### 2. Start the PostGIS database

```bash
docker compose up -d
```


### 3. Run the streamlit application with uv 

```bash
cd ui/ 
uv run streamlit run main.py
```
- The dashboard should automatically open in your broswer at [http://localhost:8501](http://localhost:8501).

---

## How to Use the Dashboard

1. **Draw or Paste Geometry**: Use the map tools to draw points, lines, or polygons, or paste WKT in the sidebar.
2. **Write SQL**: Enter any valid PostGIS SQL in the sidebar. Example:
   ```sql
   SELECT ST_ConvexHull(ST_Collect(geom)) AS geom FROM spatial_elements
   ```
3. **Apply**: Click "Apply SQL" to run your query. The transformed geometry will appear on the map and in WKT form.
4. **Inspect Results**: View the output geometry and its WKT representation in the sidebar.

---

## TechStack

### Streamlit

[Streamlit](https://streamlit.io/) is a Python framework for building interactive web apps. It's a simple tool for doing simple dashboards. 

### Streamlit-Folium

[streamlit-folium](https://github.com/randyzwitch/streamlit-folium) integrates [Folium](https://python-visualization.github.io/folium/) maps into Streamlit apps, allowing for interactive map drawing and visualization.

### PostGIS

[PostGIS](https://postgis.net/) is a spatial database extender for PostgreSQL. It adds support for geographic objects, enabling location queries to be run in SQL.

### uv

[uv](https://lukeautry.com/uv/) is an extremely fast Python package installer and runner. I use it for all my python projects.

---

## Project Structure

```
postgis_ui/
├── docker-compose.yml
├── ui/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── .streamlit/
│   │   ├── config.toml
│   │   └── secrets.toml
│   ├── main.py
│   └── model.py
└── README.md
```