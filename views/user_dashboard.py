import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
import altair as alt
import pydeck as pdk
import base64
from utils import navigate_to, get_distance_km
import time
from constants import CATEGORY_COLORS
from streamlit_cookies_controller import CookieController

def detect_image_mime_type(img_bytes):
    """Detect MIME type from image bytes"""
    try:
        # Check if the bytes are valid image data
        if not img_bytes or len(img_bytes) < 10:
            return None
            
        # Check for common image file signatures
        if img_bytes.startswith(b'\xff\xd8\xff'):  # JPEG
            return 'image/jpeg'
        elif img_bytes.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
            return 'image/png'
        elif img_bytes.startswith(b'GIF87a') or img_bytes.startswith(b'GIF89a'):  # GIF
            return 'image/gif'
        else:
            return 'image/png'  # Default fallback
    except:
        return None

def user_dashboard(conn):
    st.markdown("""
                <style>
                .card {
                    background-color: white;
                    border-radius: 12px;
                    padding: 16px;
                    margin-bottom: 16px;
                    box-shadow: 0 0px 8px rgba(0, 0, 0, 0.2);
                }
                
                .profile-picture-circle {
                    border-radius: 50%;
                    object-fit: cover;
                    width: 80px;
                    height: 80px;
                    border: 3px solid #ffffff;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15), 0 0 0 1px rgba(0,0,0,0.05);
                    transition: all 0.3s ease-in-out;
                    cursor: pointer;
                }
                .profile-picture-circle:hover {
                    transform: scale(1.05);
                    box-shadow: 0 8px 20px rgba(0,0,0,0.2), 0 0 0 1px rgba(0,0,0,0.1);
                    border-color: #f8f9fa;
                }
                .profile-picture-container {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin-bottom: 10px;
                    position: relative;
                    padding: 5px;
                }
                .profile-picture-container::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    z-index: -1;
                    opacity: 0.8;
                }
                
                .dashboard-profile-picture {
                    margin: 0 auto;
                    display: block;
                }
                .user-stat-card {
                    background: #ffffff;
                    border-radius: 20px;
                    padding: 15px;
                    text-align: center;
                    box-shadow: 0 0px 10px rgba(0,0,0,0.07);
                    position: relative;
                    margin-bottom: 16px;
                }
                .user-stat-card .value {
                    font-size: 2.5rem;
                    font-weight: bold;
                    margin-top: 10px;
                    line-height: 1;
                }
                .user-stat-card .label {
                    font-size: 0.9rem;
                    color: #666;
                    margin: 10px 0 0;
                }
                .user-stat-card.completed::before,
                .user-stat-card.accepted::before,
                .user-stat-card.rejected::before,
                .user-stat-card.rating::before {
                    content: "";
                    position: absolute;
                    top: 0;
                    left: 0;
                    height: 10px;
                    width: 100%;
                    border-top-left-radius: 20px;
                    border-top-right-radius: 20px;
                }
                .user-stat-card.completed::before { background: #9EC79F; }
                .user-stat-card.accepted::before  { background: #91ACC9; }
                .user-stat-card.rejected::before  { background: #E99493; }
                .user-stat-card.rating::before  { 
                    background: repeating-linear-gradient(
                        135deg,
                        #ffe066,
                        #ffe066 10px,
                        #fffbe6 10px,
                        #fffbe6 20px
                    ),
                    url("data:image/svg+xml;utf8,<svg width='40' height='10' xmlns='http://www.w3.org/2000/svg'><text x='0' y='9' font-size='10' font-family='Arial' fill='%23FFD700'>★</text><text x='20' y='9' font-size='10' font-family='Arial' fill='%23FFD700'>★</text></svg>");
                    background-repeat: repeat;
                    background-size: 40px 10px;
                }

                .card-row {
                display: flex;
                gap: 1rem;
                overflow-x: auto;
                padding: 0.5rem;
                margin-bottom: 1rem;
                }

                .card-item {
                flex: 0 0 250px;
                background: #fff;
                border-radius: 15px;
                padding: 1rem;
                padding-right:2rem;
                padding-bottom:1.2rem;
                margin-bottom:1.5rem;
                height: auto;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                transition: transform 0.2s cubic-bezier(0.4,0,0.2,1), box-shadow 0.2s cubic-bezier(0.4,0,0.2,1);
                border-left: 8px solid var(--accent-color);
                }

                .card-item:hover {
                transform: translateY(-5px) scale(1.01); 
                box-shadow:0px 8px 40px 4px rgba(44,62,80,0.18);
                }

                .card-item h4 {
                margin: 0 0 0.5rem;
                font-size: 1.0rem;
                font-family: Inter;
                color: #2c3e50;
                }

                .card-meta {
                font-size: 0.9rem;
                color: #555;
                display: flex;
                justify-content: space-between;
                }

                @media (max-width: 600px) {
                    .stColumns > div { width: 100% !important; }
                }
                    </style>
                    """, unsafe_allow_html=True)
    
    c = conn.cursor()

    try:
        user_data = c.execute(
            "SELECT name, profile_picture FROM users WHERE user_id = ?", 
            (st.session_state.user_id,)
        ).fetchone()
        user_name = user_data[0]
        profile_picture = user_data[1]
    except:
        CookieController().remove("user_id")
        CookieController().remove("user_email")
        CookieController().remove("user_type")
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.user_type = None
        navigate_to("login")

    unread_info = c.execute("""
        SELECT o.name, COUNT(*) as unread_count
        FROM messages m
        JOIN chats ch ON m.chat_id = ch.id
        LEFT JOIN chat_reads r ON m.chat_id = r.chat_id AND r.user_id = ?
        JOIN organisations o ON m.sender_id = o.id
        WHERE ch.user_id = ?
        AND (r.last_read IS NULL OR m.timestamp > r.last_read)
        AND m.sender_id != ?
        GROUP BY o.id
    """, (st.session_state.user_id, 
          st.session_state.user_id, 
          st.session_state.user_id)).fetchall()

    status_changes = c.execute("""
        SELECT o.title, a.status
        FROM applications a
        JOIN opportunities o ON a.opportunity_id = o.id
        WHERE a.user_id = ?
        AND a.status_updated = 1
    """, (st.session_state.user_id,)).fetchall()
    
    if status_changes:
        for title, status in status_changes:
            st.toast(
                f"Status update: Your application for **{title}** is now **{status.capitalize()}**.",
                icon="🔔"
            )
        c.execute("""
            UPDATE applications SET status_updated = 0
            WHERE user_id = ? AND status_updated = 1
        """, (st.session_state.user_id,))
        conn.commit()

    total_unread = sum(row[1] for row in unread_info)
    unread_orgs = len(unread_info)
    if total_unread > 0:
        names = [f"**{row[0].split()[0]}**" for row in unread_info]
        if unread_orgs == 2:
            names_str = " and ".join(names)
        elif unread_orgs <= 3:
            names_str = ", ".join(names)
        if unread_orgs <= 3:
            st.toast(f"You have 🟢 **{total_unread}** unread message{'s' if total_unread > 1 else ''} from {names_str}", icon="💬")
        else:
            st.toast(f"You have 🟢 **{total_unread}** unread messages from *{unread_orgs}* organisations!", icon="💬")

    total_apps = c.execute(
        "SELECT COUNT(*) FROM applications WHERE user_id = ?", (st.session_state.user_id,)
    ).fetchone()[0]
    accepted_apps = c.execute(
        "SELECT COUNT(*) FROM applications WHERE user_id = ? AND status = 'accepted'", (st.session_state.user_id,)
    ).fetchone()[0]
    rejected_apps = c.execute(
        "SELECT COUNT(*) FROM applications WHERE user_id = ? AND status = 'rejected'", (st.session_state.user_id,)
    ).fetchone()[0]
    completed_ops = c.execute(
        "SELECT COUNT(*) FROM ratings WHERE user_id = ?", (st.session_state.user_id,)
    ).fetchone()[0]
    rating = c.execute(
        "SELECT AVG(rating) FROM user_ratings WHERE user_id = ?", (st.session_state.user_id,)
    ).fetchone()[0]

    rating = round(rating, 2) if rating is not None else 0.0
    
    current_hour = time.localtime().tm_hour
    if 5 <= current_hour < 12:
        greeting = "Good morning"
    elif 12 <= current_hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    col1, col2 = st.columns([1, 4])
    
    with col1:
        if profile_picture:
            img_base64 = base64.b64encode(profile_picture).decode()
            
            mime_type = detect_image_mime_type(profile_picture)
            
            if mime_type:
                st.markdown(f"""
                <div class="profile-picture-container">
                    <img src="data:{mime_type};base64,{img_base64}" class="profile-picture-circle" alt="Profile Picture">
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="profile-picture-container">
                    <img src="data:image/png;base64,{img_base64}" class="profile-picture-circle" alt="Profile Picture">
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="profile-picture-container">
                <img src="user.png" class="profile-picture-circle" alt="Default Profile Picture">
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(
            f"<h1 style='font-family: Inter;'>{greeting}, {user_name.split(' ')[0]}!</h1>",
            unsafe_allow_html=True
        )
    
    for i in range(3):
        st.text("")

    col1, col2, col3, col4 = st.columns(4, gap="small")

    with col1:
        st.markdown(f"""
        <div class="user-stat-card completed">
          <p class="value">{completed_ops}</p>
          <p class="label">Completed</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="user-stat-card accepted">
          <p class="value">{accepted_apps}</p>
          <p class="label">Accepted</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="user-stat-card rejected">
          <p class="value">{rejected_apps}</p>
          <p class="label">Rejected</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="user-stat-card rating">
          <p class="value">{rating}</p>
          <p class="label">Self-Rating</p>
        </div>
        """, unsafe_allow_html=True)

    st.text("")
    st.text("")

    home_tab, analytics_tab, explore_tab = st.tabs(["Home", "Analytics", "Explore"])
    st.markdown('''<style>
                        button[data-baseweb="tab"] {
                        font-size: 24px;
                        margin: 0;
                        width: 100%;
                        }
                        </style>
                ''', unsafe_allow_html=True)

    with home_tab:
        st.text("")
        st.text("")
        c1, c2 = st.columns([3, 2], gap="large")

        with c1:
            st.markdown("<span style='font-family:Inter; font-size:2em; font-weight:700;'>Recent</span>", unsafe_allow_html=True)
            recent_opps = c.execute("""
                SELECT o.id, o.title, o.location, o.event_date, u.name AS org_name, o.category,
                (SELECT ROUND(AVG(rating), 1) FROM ratings WHERE opportunity_id = o.id) AS avg_rating
                FROM applications a
                JOIN opportunities o ON a.opportunity_id = o.id
                JOIN organisations u ON o.org_id = u.id
                WHERE a.user_id = ?
                ORDER BY o.created_at DESC
            """, (st.session_state.user_id,)).fetchall()

            if recent_opps:
                st.markdown('<div class="card-row">', unsafe_allow_html=True)
                for opp_id, title, location, event_date, org_name, category, rating in recent_opps:
                    color = CATEGORY_COLORS.get(category, "#FF9500")
                    category_html = f'''
                    <div style="
                        display: inline-block;
                        background-color: {color};
                        color: white;
                        padding: 5px 15px;
                        border-radius: 20px;
                        font-size: 0.7em;
                        font-weight: 500;
                    ">
                        {category}
                    </div>
                    ''' if category else ''

                    duration_row = c.execute(
                        "SELECT duration FROM opportunities WHERE id = ?", (opp_id,)
                    ).fetchone()
                    duration = duration_row[0] if duration_row and duration_row[0] else "—"

                    st.markdown(f"""
                    <div class="card-item" style="border-left: 20px solid {color}; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 18px; background: white; box-shadow:0px 0px 30px 1px rgba(0,0,0,0.07); border-radius: 15px; padding: 20px 20px; min-height: 140px;">
                        <div style="width:7px;border-radius:50px;background:{color};margin-right:18px;"></div>
                        <div style="flex:1;">
                            <div class="opp-title" style="display: flex; align-items: center; justify-content: space-between;">
                                <div style="display: flex; flex-direction: column;">
                                    <span style="font-family:Inter;font-size:1.8em;font-weight:900;">{title}</span>
                                    <span style="margin-top: 8px;">{category_html}</span>
                                </div>
                                <div style="text-align: right; min-width: 180px; font-weight: 500;">
                                    <span style="background: #f4f8fb; border-radius: 20px; padding: 8px 10px; font-size: 0.9em;">
                                        ⭐️ <b>{rating if rating else "&nbsp-"}</b>
                                    </span>
                                </div>
                            </div><br>
                            <div class="opp-row" style="background-color: #f7f7f9; border-radius: 6px; padding-left: 10px; padding-right: 10px; margin-top: 5px; display: flex; justify-content: space-between;">
                                <span class="label" style="color: #888;">Location:</span>
                                <span class="value">{location}</span>
                            </div>
                            <div class="opp-row" style="background-color: #ffffff; border-radius: 6px; padding-left: 10px; padding-right: 10px; margin-top: 5px; display: flex; justify-content: space-between;">
                                <span class="label" style="color: #888;">Date:</span>
                                <span class="value">{event_date}</span>
                            </div>
                            <div class="opp-row" style="background-color: #f7f7f9; border-radius: 6px; padding-left: 10px; padding-right: 10px; margin-top: 5px; display: flex; justify-content: space-between;">
                                <span class="label" style="color: #888;">Duration:</span>
                                <span class="value">{duration}</span>
                            </div>
                            <div class="opp-row" style="background-color: #ffffff; border-radius: 6px; padding-left: 10px; padding-right: 10px; margin-top: 5px; display: flex; justify-content: space-between;">
                                <span class="label" style="color: #888;">Category:</span>
                                <span class="value">{category or "—"}</span>
                            </div>
                            <div class="opp-row" style="background-color: #f7f7f9; border-radius: 6px; padding-left: 10px; padding-right: 10px; margin-top: 5px; display: flex; justify-content: space-between;">
                                <span class="label" style="color: #888;">Minimum Rating Required:</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            else:
                st.info("No recent opportunities available.")

        with c2:
            st.markdown("<span style='font-family:Inter; font-size:2em; font-weight:700;'>Upcoming</span>", unsafe_allow_html=True)
            today_str = date.today().strftime("%Y-%m-%d")
            upcoming = c.execute("""
                SELECT o.id, o.title, o.location, o.event_date, u.name AS org_name, o.category,
                (SELECT ROUND(AVG(rating), 1) FROM ratings WHERE opportunity_id = o.id) AS avg_rating
                FROM applications a
                JOIN opportunities o ON a.opportunity_id = o.id
                JOIN organisations u ON o.org_id = u.id
                WHERE a.user_id = ? AND a.status = 'accepted'
                AND o.event_date >= ?
                ORDER BY o.event_date ASC
            """, (st.session_state.user_id, today_str)).fetchall()

            if upcoming:
                st.markdown('<div class="card-row">', unsafe_allow_html=True)
                for opp_id, title, location, event_date, org_name, category, rating in upcoming:
                    color = CATEGORY_COLORS.get(category, "#FF9500")
                    category_html = f'''
                    <div style="
                        display: inline-block;
                        background-color: {color};
                        color: white;
                        padding: 5px 15px;
                        border-radius: 20px;
                        font-size: 0.7em;
                        font-weight: 500;
                    ">
                        {category}
                    </div>
                    ''' if category else ''

                    duration_row = c.execute(
                        "SELECT duration FROM opportunities WHERE id = ?", (opp_id,)
                    ).fetchone()
                    duration = duration_row[0] if duration_row and duration_row[0] else "—"

                    min_required_rating_row = c.execute(
                        "SELECT min_required_rating FROM opportunities WHERE id = ?", (opp_id,)
                    ).fetchone()
                    min_required_rating = min_required_rating_row[0] if min_required_rating_row and min_required_rating_row[0] else "—"

                    st.markdown(f"""
                    <div class="card-item"; style="box-shadow:0px 0px 30px 1px rgba(0,0,0,0.07);">
                        <div style="display:flex;align-items:stretch;">
                            <div style="flex:1;">
                                <div class="opp-title" style="display: flex; align-items: center; justify-content: space-between;">
                                    <div style="display: flex; flex-direction: column;">
                                        <span style="font-family:Inter;font-size:1.8em;font-weight:900;">{title}</span>
                                        <span style="margin-top: 8px;">{category_html}</span>
                                    </div>
                                    <div style="text-align: right; min-width: 180px; font-weight: 500;">
                                        <span style="background: #f4f8fb; border-radius: 20px; padding: 8px 10px; font-size: 0.7em;">
                                            ⭐️ <b>{rating if rating else "&nbsp-"}</b>
                                        </span>
                                    </div>
                                </div><br>
                                <div class="opp-row" style="background-color: #f7f7f9; border-radius: 6px; padding-left: 10px; padding-right: 10px; margin-top: 5px; display: flex; justify-content: space-between;">
                                    <span class="label" style="color: #888;">Location:</span>
                                    <span class="value">{location}</span>
                                </div>
                                <div class="opp-row" style="background-color: #ffffff; border-radius: 6px; padding-left: 10px; padding-right: 10px; margin-top: 5px; display: flex; justify-content: space-between;">
                                    <span class="label" style="color: #888;">Date:</span>
                                    <span class="value">{event_date}</span>
                                </div>
                                <div class="opp-row" style="background-color: #f7f7f9; border-radius: 6px; padding-left: 10px; padding-right: 10px; margin-top: 5px; display: flex; justify-content: space-between;">
                                    <span class="label" style="color: #888;">Duration:</span>
                                    <span class="value">{duration}</span>
                                </div>
                                <div class="opp-row" style="background-color: #ffffff; border-radius: 6px; padding-left: 10px; padding-right: 10px; margin-top: 5px; display: flex; justify-content: space-between;">
                                    <span class="label" style="color: #888;">Category:</span>
                                    <span class="value">{category or "—"}</span>
                                </div>
                                <div class="opp-row" style="background-color: #f7f7f9; border-radius: 6px; padding-left: 10px; padding-right: 10px; margin-top: 5px; display: flex; justify-content: space-between;">
                                    <span class="label" style="color: #888;">Minimum Rating Required:</span>
                                    <span class="value">{min_required_rating}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            else:
                st.info("No upcoming events found.")

    with analytics_tab:
        st.markdown("<h2 style='font-family: Inter;'>Analytics</h2>", unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="large")
        with c1:
            time_ranges = {
                "Last 7 days": 7,
                "Last 30 days": 30,
                "Last 90 days": 90,
                "All time": 99999
            }
            selected_range = st.radio(
                "Select time range:",
                list(time_ranges.keys()),
                horizontal=True
            )

            days = time_ranges[selected_range]
            today = date.today()
            if days:
                start_date = today - timedelta(days=days)
                start_date_str = start_date.strftime("%Y-%m-%d")
            else:
                start_date_str = None

            if start_date_str:
                rows = c.execute("""
                    SELECT o.category, o.event_date
                    FROM applications a
                    JOIN opportunities o ON a.opportunity_id = o.id
                    WHERE a.user_id = ? AND a.status = 'accepted' OR a.status = 'completed'
                    AND o.event_date >= ?
                    ORDER BY o.event_date ASC
                """, (st.session_state.user_id, start_date_str)).fetchall()
            else:
                rows = c.execute("""
                    SELECT o.category, o.event_date
                    FROM applications a
                    JOIN opportunities o ON a.opportunity_id = o.id
                    WHERE a.user_id = ? AND a.status = 'accepted'
                    ORDER BY o.event_date ASC
                """, (st.session_state.user_id,)).fetchall()

            if rows:
                df = pd.DataFrame(rows, columns=["Category", "Date"])
                df["Date"] = pd.to_datetime(df["Date"])
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X("Date:T", title="Date"),
                    y=alt.Y("count():Q", title="Accepted Opportunities"),
                    color=alt.Color("Category:N", scale=alt.Scale(domain=list(CATEGORY_COLORS.keys()), range=list(CATEGORY_COLORS.values())), legend=None),
                    tooltip=["Category", "Date"]
                ).properties(
                    width=500,
                    height=350,
                    title="Accepted Opportunities by Category and Date"
                )
                c1.altair_chart(chart, use_container_width=True)
            else:
                c1.info("No accepted opportunities in this time range.")

        with c2:
            pie_rows = c.execute("""
                SELECT o.category
                FROM applications a
                JOIN opportunities o ON a.opportunity_id = o.id
                WHERE a.user_id = ? AND (a.status = 'accepted' OR a.status = 'completed')
            """, (st.session_state.user_id,)).fetchall()

            if pie_rows:
                pie_df = pd.DataFrame(pie_rows, columns=["Category"])
                pie_data = pie_df["Category"].value_counts().reset_index()
                pie_data.columns = ["Category", "Count"]

                pie_chart = alt.Chart(pie_data).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta("Count:Q", stack=True),
                    color=alt.Color("Category:N", scale=alt.Scale(domain=list(CATEGORY_COLORS.keys()), range=list(CATEGORY_COLORS.values()))),
                    tooltip=["Category", "Count"]
                ).properties(
                    width=350,
                    height=350,
                    title="Accepted/Completed Opportunities by Category"
                )
                c2.altair_chart(pie_chart, use_container_width=True)
            else:
                c2.info("No accepted or completed opportunities for pie chart.")

    with explore_tab:
        st.markdown("<h2 style='font-family: Inter;'>Explore Opportunities</h2>", unsafe_allow_html=True)

        c.execute("""
            SELECT o.id, o.title, u.id AS org_id, u.name AS org_name,
                   o.latitude, o.longitude, o.location
            FROM opportunities o
            JOIN organisations u ON o.org_id = u.id
            WHERE o.latitude IS NOT NULL AND o.longitude IS NOT NULL
        """)
        opps = c.fetchall()

        data = []
        for opp_id, title, org_id, org_name, lat, lon, location in opps:
            c.execute("""
                SELECT status FROM applications
                WHERE user_id = ? AND opportunity_id = ?
            """, (st.session_state.user_id, opp_id))
            app = c.fetchone()
            
            c.execute("""
                SELECT category FROM opportunities WHERE id = ?
            """, (opp_id,))
            category_row = c.fetchone()
            category = category_row[0] if category_row else "Other"

            color_hex = CATEGORY_COLORS.get(category, "#90A4AE")

            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

            scatter_color = hex_to_rgb(color_hex)
            category_text_color = color_hex
            if app:
                status = app[0].lower()
                if status == "accepted":
                    text_color = "#09AD11"  # Green
                elif status == "rejected":
                    text_color = "#B50000"  # Red
                else:
                    text_color = "#3AA6FF"  # Blue for pending/other
            else:
                status = "available"
                text_color = "#3AA6FF"  # Blue for available

            if app:
                status = app[0].lower()
            else:
                status = "available"

            c.execute("""
                SELECT AVG(rating) FROM ratings
                WHERE opportunity_id = ?
            """, (opp_id,))

            avg = c.fetchone()[0] or 0
            avg_rating = f"{avg:.1f}"

            user_lat, user_lon = c.execute("SELECT latitude, longitude FROM users WHERE user_id = ?", (st.session_state.user_id,)).fetchone()
            min_required_rating = c.execute("SELECT min_required_rating FROM opportunities WHERE id = ?", (opp_id,)).fetchone()[0] if c.execute("SELECT min_required_rating FROM opportunities WHERE id = ?", (opp_id,)).fetchone()[0] else "None!"
            
            accepted_users = c.execute("""
                SELECT COUNT(*) FROM applications
                WHERE opportunity_id = ? AND status = 'accepted'
            """, (opp_id,)).fetchone()[0]

            rejected_users = c.execute("""
                SELECT COUNT(*) FROM applications
                WHERE opportunity_id = ? AND status = 'rejected'
            """, (opp_id,)).fetchone()[0]

            if user_lat is not None and user_lon is not None:
                # user_lat and user_lon are already plain numbers, no need to decrypt
                distance = get_distance_km(user_lat, user_lon, lat, lon)
            else:
                distance = "-"
            data.append({
                "opp_id": opp_id,
                "title": title,
                "org_name": org_name,
                "avg_rating": avg_rating,
                "status": status.capitalize(),
                "lat": lat,
                "lon": lon,
                "location": location,
                "color": scatter_color,
                "status_color": text_color,
                "category": category,
                "category_text_color": category_text_color,
                "distance": distance,
                "num_reflections": c.execute("SELECT COUNT(id) FROM RATINGS WHERE opportunity_id = ?", (opp_id,)).fetchone(),
                "min_required_rating": min_required_rating,
                "accepted_users": accepted_users,
                "rejected_users": rejected_users
            })

        if data:
            df_map = pd.DataFrame(data)
            
            layer = pdk.Layer(
                "ScatterplotLayer",
                df_map,
                get_position=["lon", "lat"],
                get_fill_color="color",
                pickable=True,
                auto_highlight=True,
                radius_scale=20,
                radius_min_pixels=5,
                radius_max_pixels=20,
                id="scatter-layer",
            )

            deck = pdk.Deck(
                map_style="light",
                initial_view_state=pdk.ViewState(
                    latitude=df_map["lat"].mean(),
                    longitude=df_map["lon"].mean(),
                    zoom=5,
                    pitch=40,
                ),
                layers=[layer],
                tooltip={
                    "html": """
                        <div style='font-family: Inter; line-height: 1.8;'>
                            <span style='font-size: 1.2em; font-weight: bold;'><b>{title}</b></span><br/><hr>
                            <div style="display: flex; flex-direction: row; justify-content: center; align-items: center; margin-bottom: 4px;">
                                <span style="font-size:1em; text-align: center;">
                                    <span style="
                                        display: inline-block;
                                        background-color: {category_text_color};
                                        color: white;
                                        padding: 3px 12px;
                                        border-radius: 20px;
                                        font-size: 10px;
                                        font-weight: 500;
                                        margin-left: 4px;
                                        margin-top: 15px;
                                        margin-bottom: 15px;
                                        vertical-align: middle;
                                    ">
                                        {category}
                                    </span>
                                    • ⭐ {avg_rating} • 💬 {num_reflections}
                                </span>
                            </div>
                            <span style = "font-size:0.8em;">
                            <div style="background-color: #f7f7f9; display: flex; flex-direction: row; justify-content: space-between; margin-bottom: 8px; border-radius: 6px; padding: 0 8px;">
                                <span style="color:gray;">Location</span>
                                <span style="margin-left:auto; font-weight: 500;">{location}</span>
                            </div>
                            <div style="background-color: #ffffff; display: flex; flex-direction: row; justify-content: space-between; margin-bottom: 8px; border-radius: 6px; padding: 0 8px;">
                                <span style="color:gray;">Organiser</span>
                                <span style="margin-left:auto; font-weight: 500;">{org_name}</span>
                            </div>
                            <div style="background-color: #f7f7f9; display: flex; flex-direction: row; justify-content: space-between; margin-bottom: 8px; border-radius: 6px; padding: 0 8px;">
                                <span style="color:gray;">Distance</span>
                                <span style="margin-left:auto; font-weight: 500;">{distance} km</span>
                            </div>
                            <div style="background-color: #ffffff; display: flex; flex-direction: row; justify-content: space-between; margin-bottom: 8px; border-radius: 6px; padding: 0 8px;">
                                <span style="color:gray;">Minimum Required Rating</span>
                                <span style="margin-left:auto; font-weight: 500;">{min_required_rating}</span>
                            </div>
                            <div style="display: flex; flex-direction: row; justify-content: center; align-items: center; gap: 18px; margin-top: 10px;">
                                <span style="display: flex; align-items: center; font-size: 1em;">
                                    <span style="font-size: 1.2em; margin-right: 5px;">👥</span>
                                    <span style="color:gray;">{accepted_users}</span>
                                </span>
                            </div>
                            </span>
                        </div>
                    """,
                    "style": {
                        "width": "auto",
                        "minWidth": "250px",
                        "backgroundColor": "white",
                        "color": "black",
                        "padding-left": "20px",
                        "padding-right": "20px",
                        "padding-top": "15px",
                        "padding-bottom": "5px",
                        "borderRadius": "20px",
                        "fontSize": "14px",
                        "fontFamily": "Inter, sans-serif",
                        "box-shadow": "0 0px 20px rgba(0,0,0,0.2)",
                    }
                }
            )

            if "map_select" not in st.session_state:
                st.session_state.map_select = {}

            def on_select():
                sel = st.session_state.map_select.get("selection", {})
                objs = sel.get("objects", {}).get("scatter-layer", [])
                if not objs:
                    return
                info = objs[0]
                idx = info.get("index")
                if idx is None:
                    return
                opp_id = int(df_map.iloc[idx]["opp_id"])
                st.session_state.temp_opp_id = opp_id
                navigate_to("opp_details")

            st.session_state.map_select = st.pydeck_chart(
                deck,
                on_select=on_select,
                selection_mode="single-object"
            )

        else:
            st.info("No opportunities with location data.")
