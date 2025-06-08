# dialogs.py
import streamlit as st
import sqlite3
import time
from datetime import datetime
from utils import hash_password, CATEGORY_COLORS
from utils import navigate_to

@st.dialog(" ")
def confirm_org_creation(conn, name, description, email, password):
    c = conn.cursor()
    st.markdown("<h1 style='font-family: Inter;'>Confirm Organisation Application Request</h1>", unsafe_allow_html=True)
    st.write("Please confirm the details below before creating your organisation account.")
    st.divider()
    st.write("Name: ", name)
    st.write("Description:", description)
    st.write("Email:", email)
    st.write("Password:", "*" * len(password))
    st.divider()
    checkbox = st.checkbox("I confirm the details above are correct and aware that **I cannot change** them later.")
    if st.button("Request Application", key="confirm_org", type="primary", use_container_width=True, disabled=not checkbox):
        with st.spinner("Processing..."):
            c.execute("INSERT INTO pending_organisations (name, description, email, password) VALUES (?, ?, ?, ?)",
                    (name, description, email, hash_password(password)))
            conn.commit()
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
    description = st.session_state.opportunity_description
    requirements = st.session_state.opportunity_requirements
    category = st.session_state.opportunity_category
    latitude = st.session_state.opportunity_latitude
    longitude = st.session_state.opportunity_longitude

    st.divider()
    st.write(f"**Title:** {title}")
    st.write(f"**Location:** {location}")
    st.write(f"**Event Date:** {event_date}")
    st.write(f"**Duration:** {duration}")
    st.write(f"**Description:** {description}")
    
    if requirements:
        st.write(f"**Requirements:** {requirements}")
    
    if category:
        st.write(f"**Category:** {category}")
    
    checkbox = st.checkbox("I confirm the details above are correct and aware that **I cannot change** them later.")
    
    if st.button("Publish", key="confirm_post", type="primary", use_container_width=True, disabled=not checkbox):
        with st.spinner("Publishing..."):
            lat = st.session_state.get("picked_lat")
            lon = st.session_state.get("picked_lon")
            c.execute("""
                INSERT INTO opportunities
                (org_id, title, location, latitude, longitude, event_date, duration, description, requirements, category, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                st.session_state.user_id,
                title,
                location,
                lat,
                lon,
                event_date.strftime("%Y-%m-%d"),
                duration,
                description,
                requirements or "None",
                category
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
            time.sleep(6)
        st.success(f"Opportunity posted successfully with ID {new_opp_id}! 🎉")
        st.session_state.temp_images = []
        time.sleep(1.5)
        navigate_to("org_dashboard")
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
            INSERT INTO ratings (student_id, org_id, opportunity_id, rating, reflection, created_at)
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