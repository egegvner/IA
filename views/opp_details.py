import streamlit as st
import pydeck as pdk
from datetime import datetime
from utils import navigate_to, get_distance_km, reverse_geocode_location
import pandas as pd
import base64
import time

def opp_details(conn):
    CATEGORY_COLORS = {
    "Environment": "#09AD11",
    "Education": "#3AA6FF",
    "Health": "#B50000",
    "Animal Welfare": "#FFAA00",
    "Community Service": "#E456FD",
    "Sports": "#00FFE5",
    "Arts & Culture": "#440FCA",
    "Disaster Relief": "#5C5C5C",
    "Other": "#000000"
}
    st.markdown("""
    <style>
    .opp-header {
        border-radius: 20px;
        background: linear-gradient(
            to right,
            #a0d8f1,
            #4a90e2
        );
        color: white;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 0px 12px rgba(0,0,0,0.2);
    }
    .opp-header h1 {
        margin: 0;
        font-size: 3em;
    }
    .section-title {
        font-size: 1.8em;
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
        background-color: #fffff;
        border-radius: 20px;
        padding: 16px;
        box-shadow: 0 0px 10px rgba(0,0,0,0.1);
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
    user_rating = c.execute(
        "SELECT AVG(rating) FROM user_ratings WHERE user_id = ?", (st.session_state.user_id,)
    ).fetchone()[0]

    user_rating = user_rating if user_rating else 0

    opp_id = st.session_state.temp_opp_id
    if not opp_id:
        st.error("No opportunity selected.")
        return
    
    user_lat, user_lon = c.execute("""
        SELECT latitude, longitude FROM users
        WHERE user_id = ?
    """, (st.session_state.user_id,)).fetchone()

    c.execute("""
        SELECT o.title, o.description, o.requirements, o.location, o.event_date,
               o.latitude, o.longitude, o.min_required_rating, u.id AS org_id, u.name, u.email
        FROM opportunities o
        JOIN organisations u ON o.org_id = u.id
        WHERE o.id = ?
    """, (opp_id,))
    row = c.fetchone()
    if not row:
        st.error("Opportunity not found.")
        return

    (title, description, requirements, location, event_date,
     lat, lon, min_requred_rating, org_id, org_name, org_email) = row

    avg_rating = c.execute("""
        SELECT AVG(r.rating)
        FROM ratings r
        WHERE r.org_id = ?
    """, (org_id,)).fetchone()[0]
    avg_rating = f"{avg_rating:.2f}" if avg_rating else "No ratings yet"
    c1, c2 = st.columns(2, gap="large")
    with c1:
        c.execute("SELECT category FROM opportunities WHERE id = ?", (opp_id,))
        category_row = c.fetchone()
        category = category_row[0] if category_row else "Other"
        base_color = CATEGORY_COLORS.get(category, CATEGORY_COLORS["Other"])
        def lighten(hex_color, factor=0.6):
            hex_color = hex_color.lstrip("#")
            rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
            light_rgb = [int(c + (255 - c) * factor) for c in rgb]
            return f"#{''.join(f'{v:02X}' for v in light_rgb)}"
        gradient_start = lighten(base_color, 0.4)
        gradient_end = base_color

        with st.spinner(""):
            try:
                @st.cache_data(show_spinner=False)
                def get_location(lat, lon):
                    return reverse_geocode_location(lat, lon)
                loc = get_location(lat, lon)
            except:
                loc = ''
        st.markdown(f"""
        <div class="opp-header" style="background: linear-gradient(to right, {gradient_start}, {gradient_end});">
            <h1 style="font-family:Inter;">{title}</h1>
            <span style="font-size:1em; color:rgba(255,255,255,0.6);">{loc}</span><br><br>
            <span style="font-size:1em; color:rgba(255,255,255,0.8);">
            📍 {location} &nbsp; | &nbsp;  {event_date} &nbsp; | &nbsp; 📌 {round(get_distance_km(user_lat, user_lon, lat, lon), 1) if user_lat or user_lon else None} km &nbsp; | &nbsp; ⭐️ {avg_rating[:3]}
            </span></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"<div class='section-title'><b>Details</b></div>", unsafe_allow_html=True)
        st.write(description)

        st.markdown(f"<div class='section-title'><b>Requirements</b>", unsafe_allow_html=True)
        st.write(requirements or "No specific requirements.")
        with st.container(border=True):
            st.write(f"Minimum Required Self-Rating: {f"⭐️ {min_requred_rating}" if min_requred_rating else "**None!**"}")

        st.markdown(f"<div class='section-title'><b>Organizer</b></div>", unsafe_allow_html=True)
        st.write(f"##### **{org_name}** ⭐️ {avg_rating}")
        st.write(f"✉️ {org_email}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💬 Chat with Organizer", use_container_width=True):
                with st.spinner(""):
                    c.execute("""
                        SELECT id FROM chats
                        WHERE user_id = ? AND opportunity_id = ? AND org_id = ?
                    """, (st.session_state.user_id, opp_id, org_id))
                    chat = c.fetchone()
                    if not chat:
                        c.execute("""
                            INSERT INTO chats (user_id, org_id, opportunity_id)
                            VALUES (?, ?, ?)
                        """, (st.session_state.user_id, org_id, opp_id))
                        conn.commit()
                        chat_id = c.lastrowid
                    else:
                        chat_id = chat[0]
                    st.session_state.active_chat = chat_id
                    time.sleep(1)
                navigate_to("chat")
        with col2:
            c.execute("""
                SELECT id, status FROM applications
                WHERE user_id = ? AND opportunity_id = ?
            """, (st.session_state.user_id, opp_id))
            appl = c.fetchone()
            if appl:
                if appl[0] and appl[1] == "accepted":
                    st.info("✅ Accepted")
                elif appl[0] and appl[1] == "rejected":
                    st.error("❌ Application Rejected")
                elif appl[0] and appl[1] == "pending":
                    st.warning("⏳ Application Pending")
            else:
                if st.button("✋ Apply Now", use_container_width=True, type="primary", disabled=(user_rating < min_requred_rating), help="Your self-rating is too low to apply." if user_rating < min_requred_rating else None):
                    with st.spinner("Submitting application..."):
                        c.execute("""
                            INSERT INTO applications
                            (user_id, opportunity_id, status, application_date)
                            VALUES (?, ?, 'pending', datetime('now'))
                        """, (st.session_state.user_id, opp_id))
                        conn.commit()
                        time.sleep(4)
                    st.rerun()

        st.markdown(f"<div class='section-title'><b>User Reflections ({c.execute("SELECT COUNT(reflection) FROM ratings WHERE opportunity_id = ?", (opp_id,)).fetchone()[0]})</b></div>", unsafe_allow_html=True)
        c.execute("""
            SELECT r.rating, r.reflection, r.created_at, u.name
            FROM ratings r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.opportunity_id = ?
            ORDER BY r.created_at DESC
            LIMIT 6
        """, (opp_id,))
        reflections = c.fetchall()
        if reflections:
            html = '<div class="reflection-grid">'
            for rating, text, created_at, user in reflections:
                stars = "★" * rating + "☆" * (5 - rating)
                date_str = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")\
                                .strftime("%b %d, %Y")
                html += f"""
                <div class="reflection-card">
                <h4>{user}</h4>
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
        st.markdown("<h2 style='font-family: Inter;'>Location</h2>", unsafe_allow_html=True)

        map_df = pd.DataFrame([{
            "LAT": lat,
            "LON": lon,
            "Color": [0, 255, 0],
            "Title": title,
            "Organizer": org_name,
            "Rating": avg_rating[:3],
            "Location": location,
            "Dist": round(get_distance_km(user_lat, user_lon, lat, lon), 1) if user_lat or user_lon else None
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
            zoom=15,
            pitch=40,
            ),
            tooltip={
            "html": """
                <div style='font-family: Inter;'>
                <span style='font-size: 1.4em; font-weight: bold;'><b>{Title}</b></span><br/><hr>
                <span>📍 {Location}</span><br>
                <span>🏢 {Organizer}</span><br>
                <span>⭐ {Rating}</span><br>
                <span>📌 {Dist} km</span>
                </div>
            """,
            "style": {
                "backgroundColor": "white",
                "color": "black",
                "padding-left": "20px",
                "padding-right": "20px",
                "padding-top": "15px",
                "padding-bottom": "15px",
                "borderRadius": "15px",
                "fontSize": "14px",
                "fontFamily": "Inter, sans-serif",
                "box-shadow": "0 0px 10px rgba(0,0,0,0.1)",
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
