import streamlit as st
import sqlite3
import time
from datetime import datetime
from utils import hash_password, navigate_to, reverse_geocode_location, encrypt_coordinate
import folium
import random
from streamlit_folium import st_folium
from streamlit_cookies_controller import CookieController

@st.dialog(" ")
def confirm_user_creation(conn, user_id, name, age, email, password, latitude, longitude):
    controller = CookieController()
    c = conn.cursor()
    st.markdown("<h1 style='font-family: Inter;'>Confirm user Registration</h1>", unsafe_allow_html=True)
    st.write("Please confirm the details below before creating your user account.")
    st.divider()
    st.write("**Name:**", name)
    st.write("**Date of Birth:**", f"{int(str(datetime.date(datetime.today())).split("-")[0]) - age}")
    st.write("**Email:**", email)
    st.write("**Password:**", "*" * len(password))
    with st.spinner("Loading..."):
        try:
            geocode = reverse_geocode_location(latitude, longitude)
        except:
            geocode = 'Not available at the moment.'
    st.write("**City / Province:**", geocode)
    st.markdown(f"<span style='font-size: 11px; color: #d6d6d6; font-family: Inter;'>ID {user_id}</span>", unsafe_allow_html=True)
    st.divider()
    checkbox = st.checkbox("I confirm the details above are correct and aware that **I cannot change** them later.")
    if st.button("Register", key="confirm_user", type="primary", use_container_width=True, disabled=not checkbox):
        with st.spinner("Processing..."):
            c.execute("INSERT INTO users (user_id, name, age, email, password, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (user_id, name, age, email, hash_password(password), encrypt_coordinate(latitude), encrypt_coordinate(longitude)))
            conn.commit()
            time.sleep(4)
        st.session_state.logged_in = True
        st.session_state.user_id = user_id
        st.session_state.user_email = email
        st.session_state.user_type = "individual"
        controller.set("user_id", user_id)
        controller.set("user_email", email)
        controller.set("user_type", "individual")
        st.balloons()
        time.sleep(3)
        navigate_to("user_dashboard")

@st.dialog(" ")
def confirm_org_creation(conn, org_id, name, description, email, password):
    c = conn.cursor()
    st.markdown("<h1 style='font-family: Inter;'>Confirm Organisation Application Request</h1>", unsafe_allow_html=True)
    st.write("Please confirm the details below before creating your organisation account.")
    st.divider()
    st.write("**Name:**", name)
    st.write("**Description:**", description)
    st.write("**Email:**", email)
    st.write("**Password:**", "*" * len(password))
    st.markdown(f"<span style='font-size: 11px; color: #d6d6d6; font-family: Inter;'>ID {org_id}</span>", unsafe_allow_html=True)
    st.divider()
    checkbox = st.checkbox("I confirm the details above are correct and aware that **I cannot change** them later.")
    if st.button("Request Application", key="confirm_org", type="primary", use_container_width=True, disabled=not checkbox):
        with st.spinner("Processing..."):
            try:
                c.execute("INSERT INTO pending_organisations (name, description, email, password) VALUES (?, ?, ?, ?)",
                        (name, description, email, hash_password(password)))
                conn.commit()
            except sqlite3.InterfaceError:
                st.error("dee")
                return
            time.sleep(2)
        st.success("Your registration request has been submitted. Awaiting admin approval.")
        time.sleep(3)
        st.rerun()

@st.dialog(" ")
def confirm_post_opportunity(conn):
    c = conn.cursor()
    st.markdown("<h1 style='font-family: Inter;'>Confirm Opportunity Details</h1>", unsafe_allow_html=True)
    st.write("Please review the details below before posting your opportunity.")
    
    title = st.session_state.opportunity_title
    location = st.session_state.opportunity_location
    event_date = st.session_state.opportunity_event_date
    duration = st.session_state.opportunity_duration
    min_required_rating = st.session_state.opportunity_min_required_rating
    description = st.session_state.opportunity_description
    requirements = st.session_state.opportunity_requirements
    category = st.session_state.opportunity_category
    latitude = st.session_state.picked_lat
    longitude = st.session_state.picked_lon
    max_applicants = st.session_state.opp_max_applicants
    
    try:
        loc = reverse_geocode_location(latitude, longitude)
    except:
        loc = ''
    st.divider()
    st.write(f"**Title:** {title}")
    st.write(f"**Location:** {location} ({loc})")
    st.write(f"**Event Date:** {event_date}")
    st.write(f"**Duration:** {duration}")
    st.write(f"**Minimum Required Rating:** {min_required_rating} ⭐️")
    st.write(f"**Description:** {description}")
    st.write(f"**Max. Number of Applicants:** {max_applicants if max_applicants else "No Limit"}")
    
    if requirements:
        st.write(f"**Requirements:** {requirements}")
    
    if category:
        st.write(f"**Category:** {category}")
    
    st.divider()
    checkbox = st.checkbox("I confirm the details above are correct and aware that **I cannot change** them later.")
    
    if st.button("Publish", key="confirm_post", type="primary", use_container_width=True, disabled=not checkbox):
        with st.spinner("Publishing..."):
            bar = st.progress(0, "Publishing")
            c.execute("""
                INSERT INTO opportunities
                (org_id, title, location, latitude, longitude, event_date, duration, description, requirements, category, min_required_rating, max_applicants, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                st.session_state.user_id,
                title,
                location,
                latitude,
                longitude,
                event_date.strftime("%Y-%m-%d"),
                duration,
                description,
                requirements or "None",
                category,
                max_applicants,
                min_required_rating
            ))
            conn.commit()
            new_opp_id = c.lastrowid

            imgs = st.session_state.temp_images
            if imgs:
                for file in imgs:
                    img_blob = file.read()
                    c.execute("""
                        INSERT INTO opportunity_images
                        (opportunity_id, image_blob, filename, uploaded_at)
                        VALUES (?, ?, ?, datetime('now'))
                    """, (new_opp_id, img_blob, file.name))
                conn.commit()

            time.sleep(5)
            for percent_complete in range(100):
                time.sleep(0.02)
                bar.progress(percent_complete + 1, "Loading")
            
        st.success(f"Opportunity posted successfully with ID {new_opp_id}! 🎉")
        st.session_state.temp_images = []
        time.sleep(1.5)
        navigate_to("org_dashboard")
        st.rerun()

@st.dialog(" ")
def confirm_apply_opportunity(conn):
    c = conn.cursor()
    st.markdown("<h1 style='font-family: Inter;'>Confirm Application</h1>", unsafe_allow_html=True)
    st.write("Please review the opportunity details before applying.")

    title = st.session_state.apply_opp_title
    org_name = st.session_state.apply_opp_org_name
    event_date = st.session_state.apply_opp_event_date
    location = st.session_state.apply_opp_location
    description = st.session_state.apply_opp_description

    st.divider()
    st.write(f"**Title:** {title}")
    st.write(f"**Organisation:** {org_name}")
    st.write(f"**Event Date:** {event_date}")
    st.write(f"**Location:** {location}")
    st.write(f"**Description:** {description}")
    st.divider()

    checkbox = st.checkbox("I confirm I want to apply for this opportunity and my details will be shared with the organisation.")

    if st.button("Apply", key="confirm_apply", type="primary", use_container_width=True, disabled=not checkbox):
        with st.spinner("Submitting application..."):
            c.execute("""
                INSERT INTO applications (user_id, opportunity_id, org_id, applied_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (
                st.session_state.user_id,
                st.session_state.apply_opp_id,
                st.session_state.apply_opp_org_id
            ))
            conn.commit()
            time.sleep(2)
        st.success("Application submitted successfully! 🎉")
        st.session_state.show_apply_dialog = False
        st.rerun()

@st.dialog("📝 Reflection Dialog")
def reflection_dialog(conn):
    c = conn.cursor()
    st.markdown("### Share your experience")
    rating = st.slider("Rate your experience (1 = worst, 5 = best):", 1, 5, 3, key="reflection_rating")
    reflection_text = st.text_area("Write your reflection here:", key="reflection_text")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Submit", use_container_width=True):
            c.execute("""
            INSERT INTO ratings (user_id, org_id, opportunity_id, rating, reflection, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (
                st.session_state.user_id,
                st.session_state.reflection_org_id,
                st.session_state.reflection_opp_id,
                rating,
                reflection_text
            ))
            conn.commit()

            st.success("Your reflection has been submitted ✅")

            st.session_state.show_reflection_dialog = False
            st.session_state.reflection_opp_id = None
            st.session_state.reflection_org_id = None
            st.session_state.reflection_title = None

            st.rerun()

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_reflection_dialog = False
            st.rerun()

@st.dialog(" ", width="large")
def show_reflections_dialog(conn):
    c = conn.cursor()
    temp_opp_id_reflection = st.session_state.temp_opp_id_reflection
    c.execute("""
        SELECT r.rating, r.reflection, r.created_at, u.name
        FROM ratings r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.opportunity_id = ?
        ORDER BY r.created_at DESC
    """, (temp_opp_id_reflection,))
    reflections = c.fetchall()

    st.markdown("<h1 style='font-family: Inter;'>Reflections</h1>", unsafe_allow_html=True)
    if not reflections:
        st.info("No reflections have been submitted for this opportunity yet.")
    else:
        for rating, reflection_text, created_at, author in reflections:
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #e0e0e0;
                    border-radius: 10px;
                    padding: 16px;
                    margin-bottom: 18px;
                    background: #fafbfc;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
                    font-family: Inter, sans-serif;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: #333;">{author}</span>
                        <span style="font-size: 15px; color: #f0ba1a; font-weight:600;">⭐️ {rating:.1f}</span>
                    </div><br>
                    <div style="font-size: 15px; color: #222;">{reflection_text}</div><br>
                    <div style="font-size: 10px; color: lightgray; margin-bottom: 8px;">{created_at}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    if st.button("Close", use_container_width=True):
        st.rerun()

@st.dialog(" ", width="large")
def edit_opportunity_dialog(conn):
    c = conn.cursor()
    st.markdown("<h1 style='font-family: Inter;'>Edit Opportunity</h1>", unsafe_allow_html=True)
    eid = st.session_state.edit_opp
    c.execute("""
      SELECT title, location, event_date, duration,
             description, requirements, category, min_required_rating, max_applicants, latitude, longitude
      FROM opportunities
      WHERE id = ?
    """, (eid,))
    (t, loc, ev, dur, desc, reqs, cat, min_rt, max_applicants, latitude, longitude) = c.fetchone()

    with st.container():
        c1, c2 = st.columns(2)
        title_in = c1.text_input("Title", t)
        loc_in   = c2.text_input("Location", loc)
        c3, c4 = st.columns(2)
        date_in  = c3.date_input("Date", datetime.strptime(ev, "%Y-%m-%d"))
        dur_in   = c4.text_input("Duration", dur)
        c5, c6, c7 = st.columns(3)
        cat_in   = c5.text_input("Category", cat or "")
        minrt_in = c6.number_input("Min Rating", min_value=0.0, max_value=5.0, value=min_rt, step=0.1)
        max_applicants = c7.number_input("Max Applicants", min_value=1, step=1, value=max_applicants if max_applicants else 1)
        desc_in  = st.text_area("Description", desc)
        reqs_in  = st.text_area("Requirements", reqs)
        if st.checkbox("Update Map Location"):
            DEFAULT_LAT, DEFAULT_LON = 39.9042, 116.4074
            st.markdown("### 📍 Pick a Location on the Map")
            m = folium.Map(width='100%', height='322%', location=[DEFAULT_LAT, DEFAULT_LON], zoom_start=12, tiles="CartoDB.Positron")
            folium.LatLngPopup().add_to(m)
            map_data = st_folium(m)

            if map_data and map_data.get("last_clicked"):
                lat = map_data["last_clicked"]["lat"]
                lon = map_data["last_clicked"]["lng"]
                st.session_state.picked_lat = lat
                st.session_state.picked_lon = lon
                st.success(f"Selected location: {lat:.5f}, {lon:.5f} ()")
            else:
                st.info("Click on the map to pick latitude & longitude")
        c8, c9 = st.columns(2)
        if c8.button("Cancel", use_container_width=True):
            del st.session_state["edit_opp"]
            st.rerun()
        if c9.button("Save Changes", use_container_width=True, type="primary"):
            if not st.session_state.picked_lat or not st.session_state.picked_lon:
                st.error("Please select a location on the map.")
            else:
                with st.spinner():
                    c.execute("""
                    UPDATE opportunities
                    SET title=?, location=?, event_date=?, duration=?,
                        description=?, requirements=?, category=?, min_required_rating=?, max_applicants=?, latitude=?, longitude=?
                    WHERE id=?
                    """, (
                        title_in,
                        loc_in,
                        date_in.strftime("%Y-%m-%d"),
                        dur_in,
                        desc_in,
                        reqs_in,
                        cat_in or None,
                        minrt_in,
                        max_applicants,
                        st.session_state.picked_lat if st.session_state.picked_lat else latitude,
                        st.session_state.picked_lon if st.session_state.picked_lon else longitude,
                        eid
                    ))
                    conn.commit()
                    del st.session_state["edit_opp"]
                    time.sleep(2)
                st.rerun()        

@st.dialog(" ", width="large")
def delete_opportunity_dialog(conn, opp_id):
    c = conn.cursor()
    st.markdown("<h1 style='font-family: Inter;'>Delete Opportunity</h1>", unsafe_allow_html=True)
    st.text("")
    st.write(f"Are you sure you want to delete the opportunity? **This action cannot be undone.**")
    st.text("")
    st.text("")
    confirm = st.checkbox("I confirm that I want to delete this opportunity.", value=False, key="confirm_delete_opp")
    
    col1, col2 = st.columns(2)
    
    if col1.button("Cancel", use_container_width=True):
        st.session_state.show_delete_dialog = False
        st.rerun()

    if col2.button("Yes, Delete", use_container_width=True, type="primary", disabled=not confirm):
        c.execute("DELETE FROM opportunities WHERE id = ?", (opp_id,))
        conn.commit()
        st.session_state.show_delete_dialog = False
        st.rerun()

@st.dialog(" ", width="large")
def map_location_dialog():
    DEFAULT_LAT, DEFAULT_LON = 39.9042, 116.4074
    st.markdown("<h1 style='font-family: Inter;'>Select Location</h1>", unsafe_allow_html=True)
    m = folium.Map(location=[DEFAULT_LAT, DEFAULT_LON], zoom_start=7, tiles="CartoDB.Positron")
    folium.LatLngPopup().add_to(m)
    map_data = st_folium(m, width=700, height=400)
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.session_state.picked_lat = lat
        st.session_state.picked_lon = lon
        st.markdown(f"<div style='font-size:0.8em;color:gray;'>{encrypt_coordinate(lat)}<br>{encrypt_coordinate(lon)}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.success(f"Location set.")
        if c2.button("Remove", use_container_width=True):
            st.session_state.picked_lat = None
            st.session_state.picked_lon = None
            st.rerun()

    st.write("This location will only be used to show opportunities and experiences near you, never shared or used for any other purpose. This can be removed at any time. Coordinates are encrypted using AES-GCM symmetric encryption.")
    if st.button("**Confirm**", type="primary", use_container_width=True):
        if 'picked_lat' in st.session_state and 'picked_lon' in st.session_state:
            st.session_state.register_lat = st.session_state.picked_lat
            st.session_state.register_lon = st.session_state.picked_lon
            st.rerun()
        else:
            st.error("Please select a location on the map first.")

@st.dialog(" ")
def rate_user_dialog(conn):
    c = conn.cursor()
    st.markdown("<h1 style='font-family: Inter;'>Rate User</h1>", unsafe_allow_html=True)
    
    user_name = st.session_state.rating_user_name
    opp_title = st.session_state.rating_opp_title
    rating = st.slider("Rate this user (1 = worst, 5 = best):", 1, 5, 3, key="rating_slider")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Submit", use_container_width=True):
            c.execute("""
            INSERT INTO user_ratings (user_id, org_id, rating, created_at)
            VALUES (?, ?, ?, datetime('now'))
            """, (
                st.session_state.rating_user_id,
                st.session_state.rating_org_id,
                rating,
            ))
            conn.commit()

            st.success(f"Rating for {user_name} on '{opp_title}' submitted successfully! ✅")

            st.session_state.show_rating_dialog = False
            st.session_state.rating_user_id = None
            st.session_state.rating_opp_id = None
            st.session_state.rating_org_id = None
            st.session_state.rating_user_name = None
            st.session_state.rating_opp_title = None

            st.rerun()

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_rating_dialog = False
            st.rerun()
