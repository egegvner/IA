import streamlit as st
import folium
from streamlit_folium import st_folium
from dialogs import confirm_post_opportunity
from constants import CATEGORY_COLORS

def post_opportunity(conn):
    c = conn.cursor()

    st.markdown("<h1 style='font-family: Inter;'>Post New Opportunity</h1>", unsafe_allow_html=True)
    st.write("")

    c1, c2 = st.columns(2, gap="large")
    with c1:
        title = st.text_input("Opportunity Title *")
        col1, col2, col3 = st.columns(3, gap="medium")
        location = col1.text_input("Location / Address *")
        category = col2.selectbox(
            "Category *",
            options=list(CATEGORY_COLORS.keys()),
        )
        max_applicants = col3.number_input("Max Applicants", 
        min_value=0, step=1, help="Maximum number of users that can apply for this opportunity. Leave '0' for no any limit.")
        col3, col4, col5 = st.columns(3, gap="medium")
        event_date = col3.date_input("Event Date *")
        duration = col4.text_input("Duration (e.g. '1 hour') *")
        min_required_rating = col5.number_input("Minimum Rating ⭐️ *", min_value = 0.0, max_value = 5.0, step = 0.1, help="Minimum self-rating required for applicants to be eligible for application for this opportunity. Leave 0 for no minimum rating requirement.")
        description = st.text_area("Opportunity Description *", height=120, placeholder="Describe the opportunity in detail. Include what volunteers will do, who can apply, and any other relevant information.")
        requirements = st.text_area("Requirements (optional)", height=80, placeholder="List any specific requirements or qualifications needed for this opportunity, e.g. 'Must be 18+, First Aid Certification'. If 'Other' is selected as category, please provide requirements.")

        st.text("")

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

        st.text("")

        if st.button("Post Opportunity", type="primary", use_container_width=True):
            if not all([title, location, description, duration]):
                st.error("Please fill in all required fields (*)")
            elif len(title) < 5:
                st.error("Title must be ≥ 5 characters")
            elif len(description) < 20:
                st.error("Description must be ≥ 20 characters")
            elif category == "Other" and not requirements:
                st.error("Please provide requirements for 'Other'")
            elif st.session_state.picked_lat == None or st.session_state.picked_lon == None:
                st.warning("Please select a location on the map")
            else:
                st.session_state.opportunity_title = title
                st.session_state.opportunity_location = location
                st.session_state.opportunity_category = category
                st.session_state.opportunity_event_date = event_date
                st.session_state.opportunity_duration = duration
                st.session_state.opportunity_min_required_rating = min_required_rating
                st.session_state.opportunity_description = description
                st.session_state.opportunity_requirements = requirements
                st.session_state.max_num_applicants = max_applicants
                st.session_state.temp_images = st.session_state.get("temp_images", [])

                confirm_post_opportunity(conn)

    with c2:
        DEFAULT_LAT, DEFAULT_LON = 39.9042, 116.4074
        st.markdown("### 📍 Pick a Location on the Map")
        m = folium.Map(location=[DEFAULT_LAT, DEFAULT_LON], zoom_start=12, tiles="CartoDB.Positron")
        folium.LatLngPopup().add_to(m)
        map_data = st_folium(m)

        if map_data and map_data.get("last_clicked"):
            lat = map_data["last_clicked"]["lat"]
            lon = map_data["last_clicked"]["lng"]
            st.session_state.picked_lat = lat
            st.session_state.picked_lon = lon
            st.success(f"Selected location: {lat:.5f}, {lon:.5f}")
        else:
            st.info("Click on the map to pick latitude & longitude")
