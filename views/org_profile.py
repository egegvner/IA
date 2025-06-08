import streamlit as st
from datetime import datetime

def org_profile(conn):
    # ─── Inject Global CSS ─────────────────────────────────────────────────────
    st.markdown("""
    <style>
    /* Profile header card */
    .org-header {
        border-radius: 12px;
        background: linear-gradient(135deg, #6C63FF 0%, #3F3D56 100%);
        color: white;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .org-header h1 {
        margin: 0;
        font-size: 2.2em;
    }
    .org-header p {
        margin: 4px 0;
        opacity: 0.9;
    }

    /* Metric cards */
    .metric-card {
        border-radius: 10px;
        background-color: #ffffff;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 16px;
    }
    .metric-card h3 {
        margin: 0;
        font-size: 1.5em;
        color: #333;
    }
    .metric-card p {
        margin: 4px 0 0 0;
        font-size: 0.9em;
        color: #666;
    }

    /* Ratings grid */
    .ratings-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 16px;
        margin-top: 16px;
    }
    .rating-card {
        border-radius: 12px;
        background-color: #fafafa;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .rating-card h4 {
        margin: 0 0 8px 0;
        font-size: 1.2em;
        color: #2c3e50;
    }
    .rating-card .stars {
        color: #f39c12;
        margin-bottom: 8px;
    }
    .rating-card .reflection {
        flex-grow: 1;
        margin-bottom: 8px;
        color: #444;
        overflow-wrap: break-word;
    }
    .rating-card .date {
        font-size: 0.8em;
        color: #888;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

    # ─── Fetch Organisation Info ──────────────────────────────────────────────
    c = conn.cursor()
    c.execute(
        "SELECT name, email, registration_date FROM organisations WHERE id = ?",
        (st.session_state.user_id,)
    )
    org_info = c.fetchone()
    if not org_info:
        st.error("Organization information not found.")
        return
    name, email, reg_date = org_info

    # ─── Header Card ─────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="org-header">
        <h1>{name}</h1>
        <p>📧 {email}</p>
        <p>🗓 Member since {datetime.strptime(reg_date, '%Y-%m-%d %H:%M:%S').strftime('%b %Y')}</p>
    </div>
    """, unsafe_allow_html=True)

    # ─── Statistics Metrics ──────────────────────────────────────────────────
    st.subheader("Statistics")
    total_opps = c.execute(
        "SELECT COUNT(*) FROM opportunities WHERE org_id = ?",
        (st.session_state.user_id,)
    ).fetchone()[0]
    total_apps = c.execute("""
        SELECT COUNT(*) FROM applications a
        JOIN opportunities o ON a.opportunity_id = o.id
        WHERE o.org_id = ?
    """, (st.session_state.user_id,)).fetchone()[0]
    total_ratings = c.execute("""
        SELECT COUNT(*) FROM ratings r
        JOIN opportunities o ON r.opportunity_id = o.id
        WHERE o.org_id = ?
    """, (st.session_state.user_id,)).fetchone()[0]
    avg_rating = c.execute("""
        SELECT AVG(rating) FROM ratings r
        JOIN opportunities o ON r.opportunity_id = o.id
        WHERE o.org_id = ?
    """, (st.session_state.user_id,)).fetchone()[0]

    # Render metric cards in three columns
    cols = st.columns(3)
    metrics = [
        ("Total Opportunities", total_opps),
        ("Total Applications", total_apps),
        ("Total Ratings", total_ratings),
    ]
    # Add average rating as a fourth metric if needed
    if avg_rating is not None:
        metrics.append(("Average Rating", f"{avg_rating:.2f}"))
    else:
        metrics.append(("Average Rating", "N/A"))

    for col, (label, value) in zip(cols + st.columns(len(metrics) - 3), metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{value}</h3>
                <p>{label}</p>
            </div>
            """, unsafe_allow_html=True)

    # ─── Recent Ratings Grid ─────────────────────────────────────────────────
    st.subheader("Recent Ratings")
    c.execute("""
        SELECT r.rating, r.reflection, r.created_at, u.name AS student_name, o.title AS opp_title
        FROM ratings r
        JOIN individuals u ON r.student_id = u.id
        JOIN opportunities o ON r.opportunity_id = o.id
        WHERE o.org_id = ?
        ORDER BY r.created_at DESC
        LIMIT 6
    """, (st.session_state.user_id,))
    recent = c.fetchall()

    if recent:
        # Build a grid of rating cards
        html = '<div class="ratings-grid">'
        for rating, reflection, created_at, student, opp_title in recent:
            stars = "★" * rating + "☆" * (5 - rating)
            date_str = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')\
                        .strftime('%b %d, %Y')
            html += f"""
            <div class="rating-card">
                <h4>{opp_title}</h4>
                <div class="stars">{stars}</div>
                <div class="reflection">{reflection}</div>
                <div class="date">— {student}, {date_str}</div>
            </div>
            """
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("No ratings available yet.")
