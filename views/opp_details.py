import streamlit as st
import pydeck as pdk
from datetime import datetime
from utils import navigate_to, get_distance_km
import pandas as pd
import base64
import time

def opp_details(conn):
    st.markdown("""
    <style>
    .opp-header {
        border-radius: 12px;
        background-color: rgb(100, 100, 255);
        color: white;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .opp-header h1 {
        margin: 0;
        font-size: 2em;
    }

    .section-title {
        font-size: 1.4em;
        margin: 24px 0 8px 0;
        color: #333;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 4px;
    }

    .image-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 8px;
        margin-bottom: 16px;
    }

    .reflection-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 16px;
        margin-top: 16px;
    }
    .reflection-card {
        background-color: #fafafa;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .reflection-card h4 {
        margin: 0 0 8px 0;
        font-size: 1.1em;
        color: #2c3e50;
    }
    .reflection-card .stars {
        color: #f39c12;
        margin-bottom: 8px;
    }
    .reflection-card .text {
        flex-grow: 1;
        color: #444;
        margin-bottom: 8px;
        overflow-wrap: break-word;
    }
    .reflection-card .meta {
        font-size: 0.8em;
        color: #888;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

    c = conn.cursor()
    opp_id = st.session_state.get("temp_opp_id")
    if not opp_id:
        st.error("No opportunity selected.")
        return
    
    user_lat, user_lon = c.execute("""
        SELECT latitude, longitude FROM individuals
        WHERE id = ?
    """, (st.session_state.user_id,)).fetchone()

    c.execute("""
        SELECT o.title, o.description, o.requirements, o.location, o.event_date,
               o.latitude, o.longitude, u.id AS org_id, u.name, u.email
        FROM opportunities o
        JOIN organisations u ON o.org_id = u.id
        WHERE o.id = ?
    """, (opp_id,))
    row = c.fetchone()
    if not row:
        st.error("Opportunity not found.")
        return

    (title, description, requirements, location, event_date,
     lat, lon, org_id, org_name, org_email) = row

    c.execute("""
        SELECT AVG(r.rating)
        FROM ratings r
        WHERE r.org_id = ?
    """, (org_id,))
    avg_rating = c.fetchone()[0]
    avg_rating = f"{avg_rating:.2f} ⭐" if avg_rating else "No ratings yet"

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="opp-header">
            <h1>{title}</h1>
            <p>📍 {location} &nbsp; | &nbsp; 🗓 {event_date} &nbsp; | &nbsp; 🚩 {get_distance_km(user_lat, user_lon, row[5], row[6])} km</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"<div class='section-title'>Description</div>", unsafe_allow_html=True)
        st.write(description)

        st.markdown(f"<div class='section-title'>Requirements</div>", unsafe_allow_html=True)
        st.write(requirements or "No specific requirements.")

        st.markdown(f"<div class='section-title'>Organizer</div>", unsafe_allow_html=True)
        st.write(f"**{org_name}**")
        st.write(f"✉️ {org_email}")
        st.write(f"Average Rating: **{avg_rating}**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💬 Chat with Organizer", use_container_width=True):
                c.execute("""
                    SELECT id FROM chats
                    WHERE student_id = ? AND opportunity_id = ? AND org_id = ?
                """, (st.session_state.user_id, opp_id, org_id))
                chat = c.fetchone()
                if not chat:
                    c.execute("""
                        INSERT INTO chats (student_id, org_id, opportunity_id)
                        VALUES (?, ?, ?)
                    """, (st.session_state.user_id, org_id, opp_id))
                    conn.commit()
                    chat_id = c.lastrowid
                else:
                    chat_id = chat[0]
                st.session_state.active_chat = chat_id
                navigate_to("chat")
        with col2:
            c.execute("""
                SELECT id, status FROM applications
                WHERE student_id = ? AND opportunity_id = ?
            """, (st.session_state.user_id, opp_id))
            appl = c.fetchone()
            if appl:
                if appl[0] and appl[1] == "accepted":
                    st.success("✅ Already Applied")
                elif appl[0] and appl[1] == "rejected":
                    st.error("❌ Application Rejected")
                elif appl[0] and appl[1] == "pending":
                    st.warning("⏳ Application Pending")
            else:
                if st.button("✋ Apply Now", use_container_width=True, type="primary"):
                    with st.spinner("Submitting application..."):
                        c.execute("""
                            INSERT INTO applications
                            (student_id, opportunity_id, status, application_date)
                            VALUES (?, ?, 'pending', datetime('now'))
                        """, (st.session_state.user_id, opp_id))
                        conn.commit()
                        time.sleep(4)

                    st.success("Application submitted!")
                    st.rerun()

        st.markdown(f"<div class='section-title'>Student Reflections</div>", unsafe_allow_html=True)
        c.execute("""
            SELECT r.rating, r.reflection, r.created_at, u.name
            FROM ratings r
            JOIN individuals u ON r.student_id = u.id
            WHERE r.opportunity_id = ?
            ORDER BY r.created_at DESC
            LIMIT 6
        """, (opp_id,))
        reflections = c.fetchall()
        if reflections:
            html = '<div class="reflection-grid">'
            for rating, text, created_at, student in reflections:
                stars = "★" * rating + "☆" * (5 - rating)
                date_str = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")\
                                .strftime("%b %d, %Y")
                html += f"""
                <div class="reflection-card">
                <h4>{student}</h4>
                <div class="stars">{stars}</div>
                <div class="text">{text}</div>
                <div class="meta">{date_str}</div>
                </div>
                """
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("No reflections yet for this opportunity.")
    
    with c2:
        st.markdown("<h2 style='font-family: Inter;'>📍 Opportunity Location</h2>", unsafe_allow_html=True)

        map_df = pd.DataFrame([{
            "LAT": lat,
            "LON": lon,
            "Color": [0, 255, 0],
            "Title": title,
            "Organizer": org_name,
            "Rating": avg_rating,
            "Location": location,
        }])

        st.pydeck_chart(pdk.Deck(
            map_style="light",
            height=400,
            layers=[
                pdk.Layer(
                    "PointCloudLayer",
                    data=map_df,
                    get_position=["LON", "LAT"],
                    get_color="Color",
                    pickable=True,
                    pointSize=5,
                    
                )
            ],
            initial_view_state=pdk.ViewState(
                latitude=lat or 0,
                longitude=lon or 0,
                zoom=12,
                pitch=40,
            ),
            tooltip={
                "html": """
                    <div style='font-family: Inter;'>
                        <span style="color: white;"><b>{Title}</b></span><br/><hr>
                        <span style="color: white;">📍 Location:</span> <span style="color: gold;">{Location}</span><br/>
                        <span style="color: white;">🧑‍💼 Organizer:</span> <span style="color: skyblue;">{Organizer}</span><br/>
                        <span style="color: white;">⭐ Avg. Rating:</span> <span style="color: lime;">{Rating}</span>
                    </div>
                """,
                "style": {
                    "backgroundColor": "black",
                    "color": "white",
                    "border": "1px solid white"
                }
            }
        ))
        st.markdown("<h2 style='font-family: Inter;'>🖼️ Images</h2>", unsafe_allow_html=True)

        c.execute("SELECT image_blob FROM opportunity_images WHERE opportunity_id = ?", (opp_id,))
        images = c.fetchall()

        st.markdown("""
        <style>
        .image-scroll {
            white-space: nowrap;
            overflow-x: auto;
            padding-bottom: 8px;
            margin-bottom: 16px;
        }
        .image-scroll img {
            display: inline-block;
            height: 180px;
            margin-right: 8px;
            border-radius: 8px;
        }
        </style>
        """, unsafe_allow_html=True)

        if images:
            html = '<div class="image-scroll">'
            for (blob,) in images:
                b64 = base64.b64encode(blob).decode("utf-8")
                html += f'<img src="data:image/png;base64,{b64}" />'
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("No images for this opportunity.")
