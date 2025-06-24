import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
import altair as alt
import pydeck as pdk
from utils import navigate_to, CATEGORY_COLORS
import time

def student_dashboard(conn):
    st.markdown("""
                <style>
                .card {
                    background-color: white;
                    border-radius: 12px;
                    padding: 16px;
                    margin-bottom: 16px;
                    box-shadow: 0 0px 8px rgba(0, 0, 0, 0.2);
                }
                .student-stat-card {
                    background: #ffffff;
                    border-radius: 20px;
                    padding: 15px;
                    text-align: center;
                    box-shadow: 0 0px 10px rgba(0,0,0,0.1);
                    position: relative;
                    margin-bottom: 16px;
                }
                .student-stat-card .value {
                    font-size: 2.5rem;
                    font-weight: bold;
                    margin: 0;
                    line-height: 1;
                }
                .student-stat-card .label {
                    font-size: 0.9rem;
                    color: #666;
                    margin: 10px 0 0;
                }
                .student-stat-card.completed::before,
                .student-stat-card.accepted::before,
                .student-stat-card.rejected::before,
                .student-stat-card.rating::before {
                    content: "";
                    position: absolute;
                    top: 0;
                    left: 0;
                    height: 10px;
                    width: 100%;
                    border-top-left-radius: 20px;
                    border-top-right-radius: 20px;
                }
                .student-stat-card.completed::before { background: #9EC79F; }
                .student-stat-card.accepted::before  { background: #91ACC9; }
                .student-stat-card.rejected::before  { background: #E99493; }
                .student-stat-card.rating::before  { background: #EBB73F; }

                @media (max-width: 600px) {
                    .stColumns > div { width: 100% !important; }
                }
                    </style>
                    """, unsafe_allow_html=True)
    c = conn.cursor()
    student_name = c.execute(
        "SELECT name FROM individuals WHERE id = ?", 
        (st.session_state.user_id,)
    ).fetchone()[0]

    total_apps = c.execute(
        "SELECT COUNT(*) FROM applications WHERE student_id = ?", (st.session_state.user_id,)
    ).fetchone()[0]
    accepted_apps = c.execute(
        "SELECT COUNT(*) FROM applications WHERE student_id = ? AND status = 'accepted'", (st.session_state.user_id,)
    ).fetchone()[0]
    rejected_apps = c.execute(
        "SELECT COUNT(*) FROM applications WHERE student_id = ? AND status = 'rejected'", (st.session_state.user_id,)
    ).fetchone()[0]
    completed_ops = c.execute(
        "SELECT COUNT(*) FROM ratings WHERE student_id = ?", (st.session_state.user_id,)
    ).fetchone()[0]
    rating = c.execute(
        "SELECT AVG(rating) FROM student_ratings WHERE student_id = ?", (st.session_state.user_id,)
    ).fetchone()[0]

    rating = round(rating, 2) if rating is not None else 0.0
    
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        greeting = "☀️ Good morning"
    elif 12 <= current_hour < 17:
        greeting = "⭐️ Good afternoon"
    else:
        greeting = "🌙 Good evening"

    st.markdown(
        f"<h1 style='font-family: Inter;'>{greeting}, {student_name.split(' ')[0]}!</h1>",
        unsafe_allow_html=True
    )
    for i in range(5):
        st.text("")

    col1, col2, col3, col4 = st.columns(4, gap="small")

    with col1:
        st.markdown(f"""
        <div class="student-stat-card completed">
          <p class="value">{completed_ops}</p>
          <p class="label">Completed</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="student-stat-card accepted">
          <p class="value">{accepted_apps}</p>
          <p class="label">Accepted</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="student-stat-card rejected">
          <p class="value">{rejected_apps}</p>
          <p class="label">Rejected</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="student-stat-card rating">
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
        c1, c2 = st.columns([3,2])
        with c1:
            recent_opps = c.execute("""
                SELECT o.id, o.title, o.location, o.event_date, u.name, o.category, a.status
                FROM applications a
                JOIN opportunities o ON a.opportunity_id = o.id
                JOIN organisations u ON o.org_id = u.id
                WHERE a.student_id = ?
                ORDER BY o.created_at DESC
                LIMIT 5
        """, (st.session_state.user_id,)).fetchall()

            st.markdown("<h2 style='font-family: Inter;'>Recent Opportunities</h2>", unsafe_allow_html=True)
            with st.container():
                if recent_opps:
                    for opp in recent_opps:
                        opp_id, title, location, event_date, org_name, category, status = opp

                        color = CATEGORY_COLORS.get(category, "#90A4AE")  # fallback gray-blue
                        category_html = f'''
                            <div style="
                                display: inline-block;
                                background-color: {color};
                                color: white;
                                padding: 5px 10px;
                                border-radius: 20px;
                                font-size: 0.8em;
                                margin-top: 5px;
                                font-weight: 500;
                            ">
                                {category}
                            </div>
                        ''' if category else ""

                        with st.container(border=True):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(
                                    f"<h4 style='font-family: Inter;'>{title}</h4>",
                                    unsafe_allow_html=True
                                )
                                st.markdown(category_html, unsafe_allow_html=True)
                                st.text("")
                                st.write(f"Location -- **{location}**")
                                st.write(f"Organiser -- **{org_name}**")
                                st.caption(f"{event_date}")
                            with col2:
                                if st.button("Details", key=f"home_view_{opp_id}", use_container_width=True, type="primary"):
                                    with st.spinner(""):
                                        st.session_state.temp_opp_id = opp_id
                                        st.session_state.temp_opp_details = True
                                        time.sleep(1)
                                    st.rerun()
                else:
                    st.info("No recent opportunities available.")

        with c2:
            today_str = date.today().strftime("%Y-%m-%d")
            upcoming = c.execute("""
                SELECT o.id, o.title, o.location, o.event_date, u.name
                FROM applications a
                JOIN opportunities o ON a.opportunity_id = o.id
                JOIN organisations u ON o.org_id = u.id
                WHERE a.student_id = ? AND a.status = 'accepted' 
                AND o.event_date >= ?
                ORDER BY o.event_date ASC
                LIMIT 5
            """, (st.session_state.user_id, today_str)).fetchall()

            st.markdown("<h2 style='font-family: Inter;'>Upcoming</h2>", unsafe_allow_html=True)
            with st.container():
                if upcoming:
                    for opp in upcoming:
                        opp_id, title, location, event_date, org_name = opp
                        with st.container(border=True):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(
                                    f"<h4 style='font-family: Inter;'>{title}</h4>",
                                    unsafe_allow_html=True
                                )
                                st.write(f"Location -- **{location}**")
                                st.write(f"Organiser -- **{org_name}**")
                                st.text("")
                                st.caption(f"{event_date}")
                            with col2:
                                if st.button("View Event", key=f"upcoming_{opp_id}", use_container_width=True):
                                    st.session_state.temp_opp_id = opp_id
                                    st.session_state.temp_opp_details = True
                                    navigate_to("opp_details")
                else:
                    st.info("No upcoming events found.")

    with analytics_tab:
        st.markdown("<h2 style='font-family: Inter;'>Analytics</h2>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([4,0.4,3])
        with c3:
            df_lifetime = pd.DataFrame(
                c.execute("""
                    SELECT o.category, COUNT(*) as count
                    FROM ratings r
                    JOIN opportunities o ON r.opportunity_id = o.id
                    WHERE r.student_id = ?
                    GROUP BY o.category
                """, (st.session_state.user_id,)).fetchall(),
                columns=["Category", "Count"]
            )
            if not df_lifetime.empty:
                pie_chart = alt.Chart(df_lifetime).mark_arc().encode(
                    theta=alt.Theta(field="Count", type="quantitative"),
                    color=alt.Color(field="Category", type="nominal"),
                    tooltip=["Category", "Count"]
                )
                st.altair_chart(pie_chart, use_container_width=True)
            else:
                st.info("No completed experiences to show.")
        with c3:
            st.text("")
        with c1:
            today = date.today()
            week_ago = today - timedelta(days=6)
            df_weekly = pd.DataFrame(
                c.execute("""
                    SELECT o.event_date, COUNT(*) as count
                    FROM ratings r
                    JOIN opportunities o ON r.opportunity_id = o.id
                    WHERE r.student_id = ?
                    AND o.event_date BETWEEN ? AND ?
                    GROUP BY o.event_date
                """, (st.session_state.user_id, week_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))).fetchall(),
                columns=["event_date", "count"]
            )
            all_dates = pd.DataFrame({
                "event_date": [(week_ago + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
            })
            if not df_weekly.empty:
                df_weekly = all_dates.merge(df_weekly, on="event_date", how="left").fillna(0)
                df_weekly["event_date"] = pd.to_datetime(df_weekly["event_date"])
                bar_weekly = alt.Chart(df_weekly).mark_bar().encode(
                    x=alt.X("event_date:T", title="Date"),
                    y=alt.Y("count:Q", title="Completed"),
                    tooltip=[alt.Tooltip("event_date:T", title="Date"), alt.Tooltip("count:Q", title="Count")]
                ).properties(height=300)
                st.markdown("<h4 style='font-family: Inter;'>Last 7 Days</h4>", unsafe_allow_html=True)
                st.altair_chart(bar_weekly, use_container_width=True)
            else:
                st.info("No experiences this week.")

            st.text("")

        month_ago = today - timedelta(days=29)
        df_monthly = pd.DataFrame(
            c.execute("""
                SELECT o.event_date, COUNT(*) as count
                FROM ratings r
                JOIN opportunities o ON r.opportunity_id = o.id
                WHERE r.student_id = ?
                  AND o.event_date BETWEEN ? AND ?
                GROUP BY o.event_date
            """, (st.session_state.user_id, month_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))).fetchall(),
            columns=["event_date", "count"]
        )
        all_month_dates = pd.DataFrame({
            "event_date": [(month_ago + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
        })
        if not df_monthly.empty:
            df_monthly = all_month_dates.merge(df_monthly, on="event_date", how="left").fillna(0)
            df_monthly["event_date"] = pd.to_datetime(df_monthly["event_date"])
            bar_monthly = alt.Chart(df_monthly).mark_bar().encode(
                x=alt.X("event_date:T", title="Date"),
                y=alt.Y("count:Q", title="Completed"),
                tooltip=[alt.Tooltip("event_date:T", title="Date"), alt.Tooltip("count:Q", title="Count")]
            ).properties(height=300)
            st.markdown("<h4 style='font-family: Inter;'>Last 30 Days</h4>", unsafe_allow_html=True)
            st.altair_chart(bar_monthly, use_container_width=True)
        else:
            st.info("No experiences this month.")

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
                WHERE student_id = ? AND opportunity_id = ?
            """, (st.session_state.user_id, opp_id))
            app = c.fetchone()
            
            if app:
                status = app[0].lower()
                if status == "accepted":
                    scatter_color = [0, 200, 0]
                    text_color = "#008000"  # green
                elif status == "rejected":
                    scatter_color = [200, 0, 0]
                    text_color = "#B50000"  # red
                else:
                    scatter_color = [255, 165, 0]
                    text_color = "#FFA500"  # orange
            else:
                status = "available"
                scatter_color = [0, 100, 255]
                text_color = "#3AA6FF"      # blue

            c.execute("""
                SELECT AVG(rating) FROM ratings
                WHERE org_id = ?
            """, (org_id,))

            avg = c.fetchone()[0] or 0
            avg_rating = f"{avg:.1f}"

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
                "status_color": text_color
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
                id="scatter-layer"
            )

            deck = pdk.Deck(
                map_style="light",
                initial_view_state=pdk.ViewState(
                    latitude=df_map["lat"].mean(),
                    longitude=df_map["lon"].mean(),
                    zoom=10,
                    pitch=40,
                ),
                layers=[layer],
                tooltip={
                "html": """
                    <div style="font-family: Inter; font-size:12px; min-width:150px;">
                      <b style="font-size:16px;">{title}</b><hr style="margin:4px 0;">
                        {location}<br>
                        By <b>{org_name}</b><br>
                        <span style="font-size:1em;">
                        <b>{avg_rating}</b> ⭐
                        </span><br>
                        <b style="color:{status_color};">{status}</b>
                    </div>
                """,
                "style": {
                    "backgroundColor": "white",
                    "color": "black",
                    "padding": "15px",
                    "borderRadius": "15px",
                    "minWidth": "200px",
                    "maxWidth": "300px",
                    "width": "auto",
                    "minHeight": "100px",
                    "maxHeight": "150px",
                    "textAlign": "left",
                    "height": "auto",
                    "fontFamily": "Inter, sans-serif",
                    "boxShadow": "0 0 10px rgba(0,0,0,0.2)"
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
