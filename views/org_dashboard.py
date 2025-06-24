import streamlit as st
from utils import navigate_to
from datetime import datetime

def org_dashboard(conn):
    st.markdown("""
    <style>
    .org-dashboard-header {
        border-radius: 20px;
        background: linear-gradient(
            to right,
            #a0d8f1,
            #4a90e2
        );
        color: white;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 0px 12px rgba(0,0,0,0.15);
    }
    .org-dashboard-header .header-content {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
    }
    .org-dashboard-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: bold;
        font-family: 'Inter', sans-serif;
    }
    .header-stats {
        display: flex;
        gap: 40px;
        margin-top: 16px;
    }
    .stat-item {
        text-align: center;
    }
    .stat-item .stat-value {
        font-size: 1.5rem;
        font-weight: bold;
        margin: 0;
        line-height: 1;
    }
    .stat-item .stat-label {
        font-size: 0.9rem;
        margin: 4px 0 0;
        opacity: 0.5;
    }
    .metric-card {
        text-align: center;
        padding: 1rem;
        margin: 0.5rem;
        background-color: #ffffff !important;
        border-radius: 20px !important;
        box-shadow: 0 0px 10px rgba(0,0,0,0.2) !important;
    }
    .metric-card h3 {
        margin: 0;
        font-size: 3rem !important;
        line-height: 1;
        font-weight: bold;
    }
    .metric-card p {
        margin: 4px 0 0 0;
        font-size: 1.01rem !important;
        color: gray;
        opacity: 0.7;
    }
    @media (max-width: 600px) {
        .org-dashboard-header .header-content {
            flex-direction: column;
            align-items: flex-start;
        }
        .header-stats {
            width: 100%;
            justify-content: space-between;
            margin-top: 12px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    c = conn.cursor()
    org_row = c.execute(
        "SELECT name, registration_date FROM organisations WHERE id = ?",
        (st.session_state.user_id,)
    ).fetchone()
    org_name, reg_date_raw = org_row
    reg_date = datetime.fromisoformat(reg_date_raw).strftime("%b %d, %Y")

    avg_rating = c.execute(
        "SELECT AVG(rating) FROM ratings WHERE org_id = ?",
        (st.session_state.user_id,)
    ).fetchone()[0] or 0
    avg_rating = f"{avg_rating:.1f}"

    st.markdown(f"""
    <div class="org-dashboard-header">
      <div class="header-content">
        <h1>{org_name}</h1>
        <div class="header-stats">
          <div class="stat-item">
            <p class="stat-value">{reg_date}</p>
            <p class="stat-label">Member Since</p>
          </div>
          <div class="stat-item">
            <p class="stat-value">⭐ {avg_rating}</p>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    total_opps = c.execute(
        "SELECT COUNT(*) FROM opportunities WHERE org_id = ?",
        (st.session_state.user_id,)
    ).fetchone()[0]
    total_apps = c.execute("""
        SELECT COUNT(*) FROM applications a
        JOIN opportunities o ON a.opportunity_id = o.id
        WHERE o.org_id = ?
    """, (st.session_state.user_id,)).fetchone()[0]
    pending_apps = c.execute("""
        SELECT COUNT(*) FROM applications a
        JOIN opportunities o ON a.opportunity_id = o.id
        WHERE o.org_id = ? AND a.status = 'pending'
    """, (st.session_state.user_id,)).fetchone()[0]

    cols = st.columns(3, gap="small")
    metrics = [
        ("Total Opportunities", total_opps),
        ("Total Applications", total_apps),
        ("Pending Applications", pending_apps)
    ]
    for col, (label, val) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <h3>{val}</h3>
              <p>{label}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.text("")
    st.text("")
    st.text("")

    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.subheader("Posted Opportunities")
        opps = c.execute("""
            SELECT id, title, location, event_date, created_at
            FROM opportunities
            WHERE org_id = ?
            ORDER BY created_at DESC
            LIMIT 6
        """, (st.session_state.user_id,)).fetchall()

        if opps:
            # Start the grid
            html = '<div class="opp-grid" style="padding: 8px;">\n'

            for opp_id, title, loc, date_str, created in opps:
                posted = datetime.strptime(created, "%Y-%m-%d %H:%M:%S") \
                                .strftime("%b %d, %Y")
                # Notice the f-string is flush with the left margin, and we only close .opp-card here
                html += f"""
        <div class="opp-card">
        <h3 style="font-family: 'Inter'; margin-bottom: 8px;">{title}</h3>
        <div class="details" style="margin-bottom: 12px;">
            📍 {loc}<br>
            🗓 {date_str}
        </div>
        <div class="posted" style="font-size:0.8em; color:#666; margin-bottom: 8px;">
            Posted on {posted}
        </div>
        </div>
        """

            # **Close the grid container once** after the loop
            html += "</div>"

            st.markdown(html, unsafe_allow_html=True)
        else:
            st.markdown("""
        <div style="
            background: #f9f9f9;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            color: #888;
            font-family: Inter;
        ">
            No recent opportunities found.
        </div>
        """, unsafe_allow_html=True)



    with c2:
        st.subheader("Recent Applications")
        recent = c.execute("""
            SELECT a.id, u.name, o.title, a.status, a.application_date
            FROM applications a
            JOIN individuals u ON a.student_id = u.id
            JOIN opportunities o ON a.opportunity_id = o.id
            WHERE o.org_id = ?
            ORDER BY a.application_date DESC
            LIMIT 6
        """, (st.session_state.user_id,)).fetchall()

        if recent:
            html = '<div class="app-grid">'
            for app_id, student, opp_title, status, appl_date in recent:
                color = ("green" if status=="accepted" else
                        "red" if status=="rejected" else "#FFA500")
                html += f'''
                <div class="app-card">
                <h3 style="font-family: 'Inter';">👤 {student}</h3>
                <div class="sub">{opp_title}</div>
                <div class="status" style="color:{color};">Status: <b>{status.capitalize()}</b></div>
                <div class="sub">Applied on: {appl_date}</div>
                
                '''
            st.markdown(html, unsafe_allow_html=True)

            for app_id, *_ in recent:
                if st.session_state.get(f"review_{app_id}", False):
                    st.session_state.temp_app_id = app_id
                    navigate_to("manage_applications")
        else:
            st.info("You haven't received any applications yet.")
