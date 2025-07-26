import json
import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from shapely.geometry import shape

from geoalchemy2 import WKTElement

from model import SpatialRecord, Base

# ———————————————— Configure & connect to PostGIS
st.set_page_config(
    page_title="PostGIS Explorer",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Initialize session state
if 'geometries' not in st.session_state:
    st.session_state['geometries'] = []
if 'center' not in st.session_state:
    st.session_state['center'] = [20, 0]  # Default center
if 'zoom' not in st.session_state:
    st.session_state['zoom'] = 2  # Default zoom level

DB_URL = st.secrets.get(
    "DATABASE_URL", "postgresql://streamlit:password@localhost:5432/db"
)


@st.cache_resource
def init_db_session():
    engine = create_engine(DB_URL)
    Base.metadata.create_all(engine, checkfirst=True)
    with Session(engine) as session:
        session.query(SpatialRecord).delete()
        session.commit()
        print("Database initialized and existing records cleared.")
        return session

### ————————————————
status_bar = st.container()
st.title("🗺️ PostGIS Explorer")
st.markdown("""
Draw points or polygons on the map below, then enter any PostGIS‑SQL 
in the box and hit **Apply** to see the transformed geometry.
""")

# Sidebar for SQL input
sql_input = st.sidebar.text_area(
    "SQL",
    value="SELECT ST_ConvexHull(ST_Collect(geom)) AS geom \nFROM spatial_elements",
)
sql_input = sql_input.replace(";", "")
apply = st.sidebar.button("Apply SQL")

session = init_db_session()
fg = folium.FeatureGroup(name="Geometries")

# apply SQL
transformed_geometries = []
if apply:
    try:
        sql = f"""WITH input as ({sql_input})
         SELECT ST_AsGeoJson(geom) from input"""
        res = session.execute(
            text(sql)
        ).all()  # TODO: replace table with output of this query
        transformed_geometries = [json.loads(row[0]) for row in res]
        print("sql output", transformed_geometries)
        
    except Exception as e:
        session.rollback()
        status_bar.error(f"❌ SQL error: {e}")

fg_drawn = folium.FeatureGroup(name="Drawn")

## redraw map
if transformed_geometries:
    st.sidebar.markdown("**Transformed geometries:**")
    st.session_state["geometries"] = []  # Clear previous geometries
    for geom in transformed_geometries:
        st.sidebar.info(shape(geom).wkt)
        # Add transformed geometries to the map
        st.session_state["geometries"] += [folium.GeoJson(data=shape(geom))]
        fg_drawn._children.clear()

### Display map 
m = folium.Map(
    location=st.session_state['center'],
    zoom_start=st.session_state['zoom'],
)
print(f"Adding {len(st.session_state['geometries'])} geometries from session_state.")
for geom in st.session_state["geometries"]: 
    fg.add_child(geom)


Draw(
    export=False,
    # feature_group=fg,
    draw_options={
        "marker": True,
        "polyline": True,
        "polygon": True,
        "rectangle": True,
        "circle": False,
        "circlemarker": False,
    },
).add_to(m)


map_data = st_folium(
    m,
    width=700,
    height=500,
    feature_group_to_add=fg,
    center=st.session_state['center'],
    zoom=st.session_state['zoom'],
)
#TODO: on_change= set_session_state
# st.session_state.center = (map_data["center"]['lng'], map_data["center"]['lat'])
# st.session_state.zoom = map_data["zoom"]
# print("Map data:", map_data)

### EVENT LOOP

all_drawings = map_data.get("all_drawings", [])
# Show shapes in sidebar
if all_drawings:
    st.sidebar.markdown("**Drawn shapes (GeoJSON):**")
    st.sidebar.info([shape(feat["geometry"]).wkt for feat in all_drawings])

    # Insert all features
    session.query(SpatialRecord).delete()
    print("Refreshing existing records in the database.")
    for feature in all_drawings:
        geom = WKTElement(shape(feature["geometry"]).wkt, srid=4326)
        record = SpatialRecord(geom=geom)
        session.add(record)
    session.commit()
    status_bar.success(f"✅ {len(all_drawings)} features synced to the database.")
