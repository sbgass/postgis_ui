import json
from shapely import from_wkt
import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from shapely.geometry import shape

from geoalchemy2 import WKTElement
from geoalchemy2.functions import ST_AsGeoJSON
from model import SpatialRecord, Base

# ———————————————— Configure & connect to PostGIS
st.set_page_config(
    page_title="PostGIS Sandbox",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Initialize session state
if "center" not in st.session_state:
    st.session_state["center"] = [20, 0]  # Default center
if "zoom" not in st.session_state:
    st.session_state["zoom"] = 2  # Default zoom level

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
st.title("🗺️ PostGIS Sandbox")
st.markdown("""
Draw points or polygons on the map below, then enter any PostGIS‑SQL 
in the box and hit **Apply** to see the transformed geometry.
""")


style_red = {
    "color": "#ff3939",
    "fillOpacity": 0.13,
    "weight": 3,
    "opacity": 1,
}

# Sidebar for SQL input
sql_input = st.sidebar.text_area(
    "SQL",
    value="SELECT ST_ConvexHull(ST_Collect(geom)) AS geom \nFROM spatial_elements",
)
sql_input = sql_input.replace(";", "")
apply = st.sidebar.button("Apply SQL")
sql_results_title = st.sidebar.container()
sql_results = st.sidebar.container()

session = init_db_session()
fg_res = folium.FeatureGroup(name="Results")

# apply SQL
transformed_geometries = []
if apply:
    try:
        sql = f"""WITH input as ({sql_input})
         SELECT ST_AsGeoJSON(geom) from input"""
        res = session.execute(
            text(sql)
        ).all()  # TODO: replace table with output of this query
        transformed_geometries = [json.loads(row[0]) for row in res]
    except Exception as e:
        session.rollback()
        status_bar.error(f"❌ SQL error: {e}")

## redraw map
if transformed_geometries:
    sql_results_title.markdown("**Transformed geometry:**")
    for geom in transformed_geometries:
        sql_results.info(shape(geom).wkt)
        # Add transformed geometries to the map
        fg_res.add_child(
            folium.GeoJson(
                data=geom,
                style_function=lambda x: style_red,
                name="Transformed",
            )
        )


wkt_input = st.sidebar.text_area(
    "**WKT**",
    value="POLYGON ((-110.390625 21.943046, -151.171875 42.293564, -139.570313 56.170023, -45.703125 52.268157, 8.4375 34.307144, 8.4375 31.653381, -110.390625 21.943046))",
)
draw_wkt = st.sidebar.button("Add WKT")

if draw_wkt:
    try:
        fg_res.add_child(
            folium.GeoJson(
                data=from_wkt(wkt_input),
                name="WKT",
            )
        )
    except Exception as e:
        status_bar.error(f"❌ Error adding geometry: {e}")

### Display map
m = folium.Map(
    location=st.session_state["center"],
    zoom_start=st.session_state["zoom"],
)

### There's a bug that's preventing Draw Featuregroups, and radiobuttons only work with Featuregroups :(
Draw(
    export=False,
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
    feature_group_to_add=fg_res,
    center=st.session_state["center"],
    zoom=st.session_state["zoom"],
)


### EVENT LOOP

last_active_drawing = map_data.get("last_active_drawing", None)
if last_active_drawing:
    # print("Last active drawing:", last_active_drawing)
    geom = shape(last_active_drawing["geometry"])
    # Add to database
    geom_wkt = WKTElement(geom.wkt, srid=4326)
    record = SpatialRecord(geom=geom_wkt)
    session.add(record)
    session.commit()
    status_bar.success("✅ Geometry added to the database.")
