import streamlit as st
from utils import CATEGORY_COLORS, get_distance_km
import time
from datetime import datetime

def browse_opportunities(conn):
    c = conn.cursor()
    st.markdown("<h1 style='font-family: Inter;'>Browse Nearby Opportunities</h1>", unsafe_allow_html=True)
    st.text("")
    st.text("")
    st.text("")

    c1, c2, c3 = st.columns([3, 3, 1], vertical_alignment="center", gap="small")
    with c1:
        search_term = st.text_input("", placeholder="🔍 Search by title or description", label_visibility="collapsed")
    with c2:
        with st.popover("Options", icon=":material/discover_tune:", use_container_width=True):
            c.execute("SELECT DISTINCT category FROM opportunities WHERE category IS NOT NULL")
            categories = [cat[0] for cat in c.fetchall()]
            category_filter = st.selectbox("Filter by Category", ["All"] + categories)

            c.execute("SELECT DISTINCT u.name FROM opportunities o JOIN organisations u ON o.org_id = u.id")
            organisations = [org[0] for org in c.fetchall()]
            organisation_filter = st.selectbox("Filter by Organisation", ["All"] + organisations)
            st.divider()
            sort_field = st.selectbox(
                "Sort by",
                ["Date", "Duration", "Rating", "Distance"]
            )
            sort_order = st.selectbox(
                "Order",
                ["Ascending", "Descending"]
            )

    with c3:
        if st.button("Refresh", use_container_width=True, icon=":material/autorenew:", type="primary"):
            st.rerun()

    user_coords = c.execute(
        "SELECT latitude, longitude FROM users WHERE user_id = ?",
        (st.session_state.user_id,)
    ).fetchone()

    query = """
    SELECT o.id, o.title, o.description, o.location, o.event_date, o.duration,
           o.requirements, o.category, u.name as org_name,
           o.latitude, o.longitude, o.min_required_rating,
           IFNULL(AVG(r.rating), 0) as avg_rating,
           COUNT(r.id) as num_reflections
    FROM opportunities o
    JOIN organisations u ON o.org_id = u.id
    LEFT JOIN ratings r ON r.opportunity_id = o.id
    WHERE 1=1
    """
    params = []
    if search_term:
        query += " AND (o.title LIKE ? OR o.description LIKE ?)"
        params += [f"%{search_term}%", f"%{search_term}%"]
    if category_filter and category_filter != "All":
        query += " AND o.category = ?"
        params.append(category_filter)
    if organisation_filter and organisation_filter != "All":
        query += " AND u.name = ?"
        params.append(organisation_filter)
    query += " GROUP BY o.id"

    c.execute(query, params)
    raw_rows = c.fetchall()

    opp_list = []
    for row in raw_rows:
        (opp_id, title, description, location, event_date,
         duration, requirements, category, org_name,
         lat, lon, min_rating, avg_rating, num_reflections) = row

        try:
            ev_dt = datetime.strptime(event_date, "%Y-%m-%d")
        except Exception:
            ev_dt = datetime.min

        if user_coords and None not in user_coords:
            dist = get_distance_km(user_coords[0], user_coords[1], lat, lon)
        else:
            dist = float('inf')

        opp_list.append({
            "id": opp_id,
            "title": title,
            "description": description,
            "location": location,
            "event_date": ev_dt,
            "event_date_str": event_date,
            "duration": duration,
            "requirements": requirements,
            "category": category,
            "org_name": org_name,
            "latitude": lat,
            "longitude": lon,
            "distance": dist,
            "min_rating": min_rating,
            "avg_rating": avg_rating,
            "num_reflections": num_reflections
        })

    reverse = (sort_order == "Descending")
    if sort_field == "Date":
        opp_list.sort(key=lambda x: x["event_date"], reverse=reverse)
    elif sort_field == "Duration":
        opp_list.sort(key=lambda x: x["duration"], reverse=reverse)
    elif sort_field == "Rating":
        opp_list.sort(key=lambda x: x["min_rating"], reverse=reverse)
    elif sort_field == "Distance":
        opp_list.sort(key=lambda x: x["distance"], reverse=reverse)

    if opp_list:
        num_opps = len(opp_list)
        num_rows = (num_opps + 2) // 3

        st.markdown("""
        <style>
        .opp-row { display: flex; justify-content: space-between; font-size: 0.95em; margin: 2px 0; }
        .label { font-weight: bold; color: #333; margin-right: 10px; }
        .value { text-align: right; color: #444; }
        .opp-card {
            border: none; border-radius: 20px; padding: 20px; margin: 10px;
            height: 100%; background-color: #fffff;
            transition: transform 0.3s;
            box-shadow: 0px 0px 30px 1px rgba(0,0,0,0.1);
        }
        .opp-card:hover {
            transform: translateY(-5px);
            box-shadow: 0px 0px 30px 2px rgba(0,0,0,0.1);
        }
        .opp-title { font-weight: bold; font-size: 1.6em; margin-bottom: 12px; color: #2c3e50; }
        .opp-details { font-size: 0.95em; margin-bottom: 15px; }
        .opp-description { font-size: 0.9em; margin: 20px 0; color: #555; line-height: 1.4; }
        .opp-requirements {
            font-size: 0.9em; margin: 15px 0; color: #555; background-color: #f5f5f5;
            padding: 8px; border-left: 3px solid #3498db;
        }
        .opp-category {
            display: inline-block; background-color: #e0f7fa; color: #00838f;
            padding: 3px 8px; border-radius: 12px; font-size: 0.8em; margin-top: 5px;
        }
        .opp-divider { height: 1px; background-color: #eee; margin: 15px 0; }
        </style>
        """, unsafe_allow_html=True)

        for row_idx in range(num_rows):
            cols = st.columns(3)
            for col_idx in range(3):
                idx = row_idx * 3 + col_idx
                if idx >= num_opps:
                    continue

                opp = opp_list[idx]
                with cols[col_idx]:
                    with st.container():
                        if user_coords and user_coords[0] is not None and user_coords[1] is not None:
                            dist = round(get_distance_km(user_coords[0], user_coords[1], opp["latitude"], opp["longitude"]), 1)
                            distance_html = f"<div class='opp-row'><span class='value'><b>{dist} km</b></span></div>"
                        else:
                            distance_html = "<div class='opp-row'><span class='value'>Unknown</span></div>"

                        color = CATEGORY_COLORS.get(opp["category"], "#90A4AE")
                        category_html = f'''
                        <div style="
                            display: inline-block;
                            background-color: {color};
                            color: white;
                            padding: 5px 20px;
                            border-radius: 20px;
                            font-size: 0.8em;
                            margin-top: 5px;
                            font-weight: 500;
                        ">
                            {opp["category"]}
                        </div>
                        ''' if opp["category"] else ''

                        c.execute("""
                        SELECT id, status FROM applications 
                        WHERE user_id = ? AND opportunity_id = ?
                        """, (st.session_state.user_id, opp["id"]))

                        existing_application = c.fetchone()

                        title = opp["title"]
                        if existing_application:
                            status = existing_application[1]
                            if status == "accepted":
                                title = f"{title} - <span style='color:green;'>Accepted</span>"
                            elif status == "rejected":
                                title = f"{title} - <span style='color:red;'>Rejected</span>"
                            else:
                                title = f"{title} - <span style='color:orange;'>Pending</span>"

                        st.markdown(f"""
                            <div class="opp-card">
                                <div class="opp-title">{title}</div>
                                {category_html}&nbsp;<br><br>
                                <div class="opp-details">
                                    <div class="opp-row"><span class="label"> </span> <span class="value"></span></div>
                                    <div class="opp-row"><span class="label">Organisation:</span> <span class="value">{opp["org_name"]}</span></div>
                                    <div class="opp-row"><span class="label">Location:</span> <span class="value">{opp["location"]}</span></div>
                                    <div class="opp-row"><span class="label">Date:</span> <span class="value">{opp["event_date_str"]}</span></div>
                                    <div class="opp-row"><span class="label">Duration:</span> <span class="value">{opp["duration"]}</span></div>
                                    <div class="opp-row"><span class="label">Distance:</span> <span class="value">{distance_html}</span></div>
                                    <div class="opp-row"><span class="label">Minimum Rating Required:</span> <span class="value">{f"⭐️ {opp['min_rating']}" if opp['min_rating'] else "None!"}</span></div>
                                </div>
                                <div><div style="display: flex; align-items: center; margin: 12px 0;">
                                    <div style="flex: 1; height: 1px; background: #eee;"></div>
                                    <span style="padding: 0 12px; font-weight: 500; color: #888;">
                                        ⭐️ {opp['avg_rating']} &nbsp;&nbsp;•&nbsp;&nbsp; 💬 {opp['num_reflections']}
                                    </span>
                                    <div style="flex: 1; height: 1px; background: #eee;"></div>
                                    </div>
                                    <div class="opp-description">
                                        <strong>Description</strong><br>
                                        {opp["description"]}
                                    </div>
                                    <div class="opp-requirements">
                                        <strong>Requirements:</strong><br>
                                        {opp["requirements"][:50]}{'...' if len(opp["requirements"]) > 100 else ''}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        if st.button("View Details", key=f"view_{opp['id']}", use_container_width=True):
                            with st.spinner(""):
                                st.session_state.temp_opp_id = opp["id"]
                                st.session_state.temp_opp_details = True
                                time.sleep(1)
                            st.rerun()
                                
    else:
        st.info("No opportunities found matching your criteria.")
    
    if 'temp_opp_details' in st.session_state and st.session_state.temp_opp_details and 'temp_opp_id' in st.session_state:
        st.session_state.current_page = "opp_details"
        st.rerun()
