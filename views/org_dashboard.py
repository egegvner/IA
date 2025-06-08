import streamlit as st
from utils import navigate_to
from datetime import datetime

def org_dashboard(conn):
    st.markdown("""
    <style>
    /* Header */
    .org-dashboard-header {
        border-radius: 12px;
        background: #4a90e2;
        color: white;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .org-dashboard-header h1 {
        margin: 0;
        font-size: 2em;
    }

    /* Metric cards */
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 16px;
    }
    .metric-card h3 {
        margin: 0;
        font-size: 1.6em;
        color: #333;
    }
    .metric-card p {
        margin: 4px 0 0 0;
        color: #666;
    }

    /* Opportunity grid */
    .opp-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 16px;
        margin-top: 16px;
    }
    .opp-card {
        background-color: #fafafa;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .opp-card h4 {
        margin: 0 0 8px 0;
        font-size: 1.2em;
        color: #2c3e50;
    }
    .opp-card .details {
        font-size: 0.9em;
        color: #555;
        margin-bottom: 12px;
    }
    .opp-card .posted {
        font-size: 0.8em;
        color: #888;
        margin-bottom: 12px;
    }
    .opp-card button {
        width: 100%;
    }

    /* Recent applications grid */
    .app-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 16px;
        margin-top: 16px;
    }
    .app-card {
        background-color: #fff;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .app-card h4 {
        margin: 0 0 8px 0;
        font-size: 1.1em;
        color: #2c3e50;
    }
    .app-card .sub {
        font-size: 0.9em;
        color: #666;
        margin-bottom: 8px;
    }
    .app-card .status {
        margin-bottom: 12px;
    }
    .app-card button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

    c = conn.cursor()
    org_name = c.execute(
        "SELECT name FROM organisations WHERE id = ?",
        (st.session_state.user_id,)
    ).fetchone()[0]

    st.markdown(f"""
    <div class="org-dashboard-header">
      <h1>{org_name} Dashboard</h1>
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

    cols = st.columns(3)
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
            html = '<div class="opp-grid">'
            for opp_id, title, loc, date_str, created in opps:
                posted = datetime.strptime(created, "%Y-%m-%d %H:%M:%S")\
                        .strftime("%b %d, %Y")
                html += f"""
                <div class="opp-card">
                <h3 style="font-family: 'Inter';">{title}</h3>
                <div class="details">
                    📍 {loc}<br>
                    🗓 {date_str}
                </div>
                <div class="posted">Posted on {posted}</div>
                    
                """
            st.markdown(html, unsafe_allow_html=True)

            for opp_id, *_ in opps:
                if st.session_state.get(f"view_{opp_id}", False):
                    st.session_state.temp_opp_id = opp_id
                    navigate_to("manage_applications")
        else:
            st.info("You haven't posted any opportunities yet.")

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
                html += f"""
                <div class="app-card">
                <h3 style="font-family: 'Inter';">👤 {student}</h3>
                <div class="sub">{opp_title}</div>
                <div class="status" style="color:{color};">
                    Status: <b>{status.capitalize()}</b>
                </div>
                <div class="sub">Applied on: {appl_date}</div>
                """
            st.markdown(html, unsafe_allow_html=True)

            for app_id, *_ in recent:
                if st.session_state.get(f"review_{app_id}", False):
                    st.session_state.temp_app_id = app_id
                    navigate_to("manage_applications")
        else:
            st.info("You haven't received any applications yet.")
