import streamlit as st
import folium
from streamlit_folium import st_folium
from phase3_llm_extraction import extract_and_clean_address
from phase2_geocode import get_coords_with_fallback 
from phase2_geocode import add_coordinates   # reuse your existing geocoding function
from phase4_ranking import get_road_distance, rank_nearest_vehicles_two_stage

@st.cache_data
def load_off_vehicles():
    df = add_coordinates()
    return df.dropna(subset=["off_lat", "off_lon"]).reset_index(drop=True)

def build_dispatch_map(incident_lat, incident_lon, ranked_vehicles_df):
    m = folium.Map(location=[incident_lat, incident_lon], zoom_start=13)

    folium.Marker(
        [incident_lat, incident_lon],
        popup="Incident Location",
        icon=folium.Icon(color="red", icon="exclamation-sign")
    ).add_to(m)

    for _, row in ranked_vehicles_df.iterrows():
        folium.Marker(
            [row["off_lat"], row["off_lon"]],
            popup=f"{row['Grouping']} — {row['distance_km']:.2f} km, ETA {row['eta_min_adjusted']:.0f} min",
            icon=folium.Icon(color="green", icon="ambulance", prefix="fa")
        ).add_to(m)

        # Get the actual road route for this vehicle -> incident
        _, _, route_coords = get_road_distance(incident_lat, incident_lon, row["off_lat"], row["off_lon"])

        if route_coords:
            folium.PolyLine(locations=route_coords, color="blue", weight=3, opacity=0.7).add_to(m)
        else:
            # fallback to straight line if routing fails for this pair
            folium.PolyLine(
                locations=[[incident_lat, incident_lon], [row["off_lat"], row["off_lon"]]],
                color="gray", weight=2, opacity=0.5, dash_array="5"
            ).add_to(m)

    return m

off_vehicles = load_off_vehicles()
st.set_page_config(page_title="Emergency Call Form", layout="wide")
st.title("Emergency Call Form")

col1, col2 = st.columns(2)
with col1:
    address = st.text_input("Address of the Emergency")
    landmark = st.text_input("Land Mark (optional)")
    age = st.number_input("Age", min_value=0, max_value=120)
with col2:
    chief_complaint = st.selectbox("Chief Complaint", ["Cardiac", "RTA", "Breathing Difficulty", "Trauma", "Other"])
    priority = st.selectbox("Priority", ["Emergency", "Urgent", "Non-Urgent"])
    gender = st.selectbox("Gender", ["Male", "Female"])

if "result" not in st.session_state:
    st.session_state.result = None

if st.button("Submit"):
    cleaned_address = extract_and_clean_address(address, landmark)
    lat, lon = get_coords_with_fallback(cleaned_address)

    if lat is not None and lon is not None:
        ranked = rank_nearest_vehicles_two_stage(lat, lon, off_vehicles)
        st.session_state.result = {
            "address": address,
            "landmark": landmark,
            "cleaned_address": cleaned_address,
            "lat": lat,
            "lon": lon,
            "ranked": ranked,
            "chief_complaint": chief_complaint,
            "priority": priority,
            "age": age,
            "gender": gender,
        }
    else:
        st.session_state.result = None
        st.error("Could not determine coordinates for this address.")

# --- Everything below runs on EVERY rerun, showing whatever's currently stored ---
if st.session_state.result:
    r = st.session_state.result

    st.write("Cleaned address:", r["cleaned_address"])
    st.write("Coordinates:", r["lat"], r["lon"])

    st.subheader("Nearest Available Vehicles")
    st.dataframe(r["ranked"])

    dispatch_map = build_dispatch_map(r["lat"], r["lon"], r["ranked"])
    st_folium(dispatch_map, width=700, height=500, key="dispatch_map")

    st.json({
        "address": r["address"],
        "landmark": r["landmark"],
        "cleaned_address": r["cleaned_address"],
        "lat": r["lat"],
        "lon": r["lon"],
        "chief_complaint": r["chief_complaint"],
        "priority": r["priority"],
        "age": r["age"],
        "gender": r["gender"],
    })