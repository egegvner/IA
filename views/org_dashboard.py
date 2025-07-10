import streamlit as st
from utils import navigate_to
from datetime import datetime
import streamlit.components.v1 as components
from constants import CATEGORY_COLORS
from streamlit_cookies_controller import CookieController

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
                
    .metric-card {
        background: #ffffff;
        border-radius: 20px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 0px 10px rgba(0,0,0,0.07);
        position: relative;
        margin-bottom: 16px;
    }
                
    .org-stat-card .value {
        font-size: 2.5rem;
        font-weight: bold;
        margin-top: 10px;
        line-height: 1;
    }
                
    .org-stat-card .label {
        font-size: 0.9rem;
        color: #666;
        margin: 10px 0 0;
    }
                
    .org-stat-card.opps::before,
    .org-stat-card.total_applications::before,
    .org-stat-card.pending_applications::before,
    .org-stat-card.rating::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        height: 10px;
        width: 100%;
        border-top-left-radius: 20px;
        border-top-right-radius: 20px;
    }
                
    .org-stat-card.opps::before { background: #9EC79F; }
    .org-stat-card.total_applications::before  { background: #91ACC9; }
    .org-stat-card.pending_applications::before  { background: #EBB73F; }
    .org-stat-card.rating::before  { 
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

    @media (max-width: 600px) {
        .stColumns > div { width: 100% !important; }
    }
                
    .opp-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
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

    unread_info = c.execute("""
        SELECT u.name, COUNT(*) as unread_count
        FROM messages m
        JOIN chats c ON m.chat_id = c.id
        LEFT JOIN chat_reads r ON m.chat_id = r.chat_id AND r.user_id = ?
        JOIN users u ON m.sender_id = u.user_id
        WHERE c.org_id = ?
        AND (r.last_read IS NULL OR m.timestamp > r.last_read)
        AND m.sender_id != ?
        GROUP BY u.user_id
    """, (st.session_state.user_id, st.session_state.user_id, st.session_state.user_id)).fetchall()
    total_unread = sum(row[1] for row in unread_info)
    unread_users = len(unread_info)
    if total_unread > 0:
        names = [f"**{row[0].split()[0]}**" for row in unread_info]
        if unread_users == 2:
            names_str = " and ".join(names)
        elif unread_users <= 3:
            names_str = ", ".join(names)
        if unread_users <= 3:
            st.toast(f"You have 🟢 **{total_unread}** unread message{'s' if total_unread > 1 else ''} from {names_str}", icon="💬")
        else:
            st.toast(f"You have 🟢 **{total_unread}** unread messages from *{unread_users}*!", icon="💬")

    pending_apps_info = c.execute("""
        SELECT u.name, COUNT(*) as pending_count
        FROM applications a
        JOIN users u ON a.user_id = u.user_id
        JOIN opportunities o ON a.opportunity_id = o.id
        WHERE o.org_id = ? AND a.status = 'pending'
        GROUP BY u.user_id
    """, (st.session_state.user_id,)).fetchall()

    total_pending = sum(row[1] for row in pending_apps_info)
    pending_users = len(pending_apps_info)

    if total_pending > 0:
        names = [f"**{row[0].split()[0]}**" for row in pending_apps_info]
        if pending_users == 2:
            names_str = " and ".join(names)
        elif pending_users <= 3:
            names_str = ", ".join(names)
        if pending_users <= 3:
            st.toast(
                f"You have 🟡 **{total_pending}** pending application{'s' if total_pending > 1 else ''} from {names_str}",
                icon="📥"
            )
        else:
            st.toast(
                f"You have 🟡 **{total_pending}** pending applications from *{pending_users}* applicants!",
                icon="📥"
            )
    try:
        org_row = c.execute(
            "SELECT name, registration_date FROM organisations WHERE id = ?",
            (st.session_state.user_id,)

        ).fetchone()
    except:
        CookieController().remove("user_id")
        CookieController().remove("user_email")
        CookieController().remove("user_type")
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.user_type = None
        navigate_to("login")

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

    cols = st.columns(4, gap="small")
    metrics = [
        ("Total Opportunities", total_opps),
        ("Total Applications", total_apps),
        ("Pending Applications", pending_apps),
        ("Rating", avg_rating)
    ]
    for i, (label, value) in enumerate(metrics):
        card_class = ["org-stat-card", "metric-card"]
        if i == 0:
            card_class.append("opps")
        elif i == 1:
            card_class.append("total_applications")
        elif i == 2:
            card_class.append("pending_applications")
        elif i == 3:
            card_class.append("rating")
        with cols[i]:
            st.markdown(
                f"""
                <div class="{' '.join(card_class)}">
                    <div class="value">{value}</div>
                    <div class="label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    st.text("")
    st.text("")
    st.text("")

    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown("<span style='font-family:Inter; font-size:2em; font-weight:700;'>Posted Opportunities</span>", unsafe_allow_html=True)
        opps = c.execute("""
            SELECT id, title, location, event_date, created_at, category
            FROM opportunities
            WHERE org_id = ?
            ORDER BY created_at DESC
            LIMIT 6
        """, (st.session_state.user_id,)).fetchall()

        if opps:
            st.markdown('<div class="card-row">', unsafe_allow_html=True)
            for opp_id, title, location, event_date, created_at, category in opps:
                color = CATEGORY_COLORS.get(category, "#FF9500")
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
                ''' if category else ''
                event_str = datetime.fromisoformat(event_date).strftime("%b %d, %Y") if event_date else "N/A"
                created_str = datetime.fromisoformat(created_at).strftime("%b %d, %Y")

                total_applicants = c.execute(
                    "SELECT COUNT(*) FROM applications WHERE opportunity_id = ?", (opp_id,)
                ).fetchone()[0]
                accepted_applicants = c.execute(
                    "SELECT COUNT(*) FROM applications WHERE opportunity_id = ? AND status = 'accepted'", (opp_id,)
                ).fetchone()[0]
                pending_applicants = c.execute(
                    "SELECT COUNT(*) FROM applications WHERE opportunity_id = ? AND status = 'pending'", (opp_id,)
                ).fetchone()[0]
                rejected_applicants = c.execute(
                    "SELECT COUNT(*) FROM applications WHERE opportunity_id = ? AND status = 'rejected'", (opp_id,)
                ).fetchone()[0]

                rating = c.execute(
                    "SELECT AVG(rating) FROM ratings WHERE opportunity_id = ?",
                    (opp_id,)
                ).fetchone()[0]

                st.markdown(f'''
                    <div class="card-item" style="border-left: 8px solid {color}; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 18px; background: white; box-shadow: 0 5px 10px rgba(0,0,0,0.1); border-radius: 20px; padding: 18px 16px; min-height: 140px;">
                        <div style="display: flex; flex-direction: row; align-items: center; justify-content: space-between; width: 100%;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="font-family:Inter;font-size:1.1em;font-weight:900; display: inline-block; vertical-align: middle;">{title}</span>
                                {category_html}<j>
                            </div>
                            <div style="display: flex; align-items: center; gap: 6px;">
                                <span style="background: #eafaf1; color: #27ae60; border-radius: 100px; padding: 8px 10px; font-size: 0.8em;" title="Accepted">{accepted_applicants}</span>&nbsp;
                                <span style="background: #fbeee6; color: #e67e22; border-radius: 100px; padding: 8px 10px; font-size: 0.8em;" title="Pending">{pending_applicants}</span>&nbsp;
                                <span style="background: #fdeaea; color: #e74c3c; border-radius: 100px; padding: 8px 10px; font-size: 0.8em;" title="Rejected">{rejected_applicants}</span>&nbsp;
                                <span style="background: #f4f8fb; color: #2980b9; border-radius: 100px; padding: 8px 10px; font-size: 0.8em;" title="Average Rating">
                                    ⭐️ {rating if rating else "&nbsp;-"}
                                </span>
                            </div>
                        </div>
                        <div class="card-meta" style="display: flex; flex-direction: row; justify-content: space-between; align-items: center; width: 100%; margin-top: 18px;">
                            <span style="flex:1; text-align:left;">📍 &nbsp; {location}</span>
                            <span style="flex:1; text-align:center;">📅 &nbsp; {event_str}</span>
                            <span style="flex:1; text-align:right; color:#888;">Posted &nbsp; {created_str}</span>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("You haven't posted any opportunities yet.")

    with c2:
        st.markdown("<span style='font-family:Inter; font-size:2em; font-weight:700;'>Recent Applications</span>", unsafe_allow_html=True)
        recent = c.execute("""
            SELECT a.id, u.name, o.title, a.status, a.application_date, o.category
            FROM applications a
            JOIN users u ON a.user_id = u.user_id
            JOIN opportunities o ON a.opportunity_id = o.id
            WHERE o.org_id = ?
            ORDER BY a.application_date DESC
            LIMIT 6
        """, (st.session_state.user_id,)).fetchall()

        if recent:
            st.markdown('<div class="card-row">', unsafe_allow_html=True)
            for app_id, user, opp_title, status, appl_date, category in recent:
                color = CATEGORY_COLORS.get(category)
                category_color = CATEGORY_COLORS.get(category, "#FF9500")
                category_html = f'''
                <div style="
                    display: inline-block;
                    background-color: {category_color};
                    color: white;
                    padding: 5px 10px;
                    border-radius: 20px;
                    font-size: 0.8em;
                    margin-top: 5px;
                    font-weight: 500;
                ">
                    {category}
                </div>
                ''' if category else ''
                # Define status color mapping
                STATUS_COLORS = {
                    "pending": "#EBB73F",
                    "accepted": "#27ae60",
                    "rejected": "#e74c3c"
                }
                status_color = STATUS_COLORS.get(status.lower(), "#888")
                if status.lower() == "pending":
                    sign = "🟡"
                elif status.lower() == "accepted":
                    sign = "🟢"
                elif status.lower() == "rejected":
                    sign = "🔴"
                status = f'<span style="color: {status_color}; font-weight: 500; font-size: 1.1em;">{sign}&nbsp;{status.capitalize()}</span>'
                st.markdown(f'''
                <div class="card-item" style="border-left: 8px solid {color}; display: flex; flex-direction: column; justify-content: center; margin-bottom: 18px; background: white; box-shadow: 0 5px 10px rgba(0,0,0,0.1); border-radius: 20px; padding: 18px 16px; position: relative; min-height: 120px;">
                    <div style="display: flex; flex-direction: row; align-items: center; justify-content: flex-start; min-height: 48px;">
                        <span style="font-family:Inter;font-size:1.6em;font-weight:900; display: inline-block; vertical-align: middle;">👤 &nbsp; {user}</span>
                        <span style="margin-left: 10px; display: inline-block; vertical-align: middle;">
                            &nbsp;{category_html} &nbsp; &nbsp
                            {status.replace("{status_color}", status_color)}
                        </span>
                    </div><br>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="font-size:0.85em; opacity:0.6;">Applied for</span>
                        <span style="font-size:1em;">{opp_title} at {location}</span>
                    </div>
                    <div class="card-meta" style="position: absolute; bottom: 10px; right: 18px;">
                        <span style="color:#888; font-size:0.85em;">Applied &nbsp; {appl_date}</span>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("You haven't received any applications yet.")
