import streamlit as st
import folium
from streamlit_folium import st_folium
from dialogs import confirm_post_opportunity  # if you still want a confirmation dialog
from datetime import datetime

def post_opportunity(conn):
    c = conn.cursor()

    # ─── Page Header ─────────────────────────────────────────────────────────
    st.markdown("<h1 style='font-family: Inter;'>Post New Opportunity</h1>", unsafe_allow_html=True)
    st.write("Fill in the details below to post a new opportunity.")
    st.write("")  # spacing

    # ─── Left Column: Form Fields ─────────────────────────────────────────────
    c1, c2 = st.columns(2, gap="small")
    with c1:
        title = st.text_input("Opportunity Title *")
        col1, col2 = st.columns(2, gap="small")
        location = col1.text_input("Location / Address *")
        category = col2.selectbox("Category *", [
            "Education", "Environment", "Health", "Arts & Culture", 
            "Community Service", "Animal Welfare", "Disaster Relief", "Other"
        ])
        col3, col4 = st.columns(2, gap="small")
        event_date = col3.date_input("Event Date *")
        duration = col4.text_input("Duration (e.g. '2 hours', '3 days') *")
        description = st.text_area("Opportunity Description *", height=120)
        requirements = st.text_area("Requirements (optional)", height=100)

        st.write("")

        if "temp_images" not in st.session_state:
            st.session_state.temp_images = []

        uploaded = st.file_uploader(
            "Upload up to 5 images (optional)",
            type=["png","jpg","jpeg"],
            accept_multiple_files=True,
            key="file_uploader"
        )
        if uploaded:
            st.session_state.temp_images = uploaded[:5]
        if st.session_state.temp_images:
            st.markdown("**Preview:**")
            cols = st.columns(len(st.session_state.temp_images))
            for file, col in zip(st.session_state.temp_images, cols):
                img_bytes = file.read()
                col.image(img_bytes, use_container_width=True, caption=file.name)
                file.seek(0)

    with c2:
        DEFAULT_LAT, DEFAULT_LON = 39.9042, 116.4074
        st.markdown("### 📍 Pick a location on the map")
        m = folium.Map(location=[DEFAULT_LAT, DEFAULT_LON], zoom_start=12, tiles="CartoDB.Positron")
        folium.LatLngPopup().add_to(m)
        map_data = st_folium(m, width=700, height=400)

        if map_data and map_data.get("last_clicked"):
            lat = map_data["last_clicked"]["lat"]
            lon = map_data["last_clicked"]["lng"]
            st.session_state.picked_lat = lat
            st.session_state.picked_lon = lon
            st.success(f"Selected location: {lat:.5f}, {lon:.5f}")
        else:
            st.info("Click on the map to pick latitude & longitude")

    if st.button("📌 Post Opportunity", type="primary", use_container_width=True):
        if not all([title, location, description, duration]):
            st.error("Please fill in all required fields (*)")
            return
        if len(title) < 5:
            st.error("Title must be ≥ 5 characters")
            return
        if len(description) < 20:
            st.error("Description must be ≥ 20 characters")
            return
        if category == "Other" and not requirements:
            st.error("Please provide requirements for 'Other'")
            return
        
        st.session_state.opportunity_title = title
        st.session_state.opportunity_location = location
        st.session_state.opportunity_category = category
        st.session_state.opportunity_event_date = event_date
        st.session_state.opportunity_duration = duration
        st.session_state.opportunity_description = description
        st.session_state.opportunity_requirements = requirements
        st.session_state.opportunity_latitude = lat if 'picked_lat' in st.session_state else DEFAULT_LAT
        st.session_state.opportunity_longitude = lon if 'picked_lon' in st.session_state else DEFAULT_LON
        st.session_state.temp_images = st.session_state.get("temp_images", [])

        confirm_post_opportunity(conn)