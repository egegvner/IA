import streamlit as st
from utils import navigate_to
from constants import CATEGORY_COLORS
from dialogs import reflection_dialog
import time

def user_applications(conn):
    st.markdown(
        "<h1 style='font-family: Inter;'>📄 My Applications</h1>",
        unsafe_allow_html=True
    )

    c = conn.cursor()
    uid = st.session_state.user_id

    c.execute("""
        SELECT a.id, o.title, u.name as org_name, o.location, o.event_date, 
               a.status, a.application_date, o.id as opp_id, u.id as org_id, o.category
        FROM applications a
        JOIN opportunities o ON a.opportunity_id = o.id
        JOIN organisations u ON o.org_id = u.id
        WHERE a.user_id = ?
        ORDER BY a.application_date DESC
    """, (uid,))
    applications = c.fetchall()

    col_filter, col_search = st.columns([1, 2], gap="small")
    with col_filter:
        status_filter = st.selectbox(
            "🔍 Filter by Status",
            ["All", "Pending", "Accepted", "Rejected"],
            key="status_filter"
        )
    with col_search:
        search_query = st.text_input(
            "🔎 Search Title or Org",
            placeholder="Type to filter…",
            key="search_query"
        )

    if status_filter != "All":
        applications = [
            app for app in applications
            if app[5].lower() == status_filter.lower()
        ]

    if search_query:
        q = search_query.lower()
        applications = [
            app for app in applications
            if q in app[1].lower() or q in app[2].lower()
        ]

    st.write("")

    if applications:
        for app in applications:
            (app_id, title, org_name, location,
             event_date, status, app_date,
             opp_id, org_id, category) = app

            accent_color = CATEGORY_COLORS.get(category, "Other")
            if status.lower() == "pending":
                status_color = "#f39c12"  # orange
            elif status.lower() == "accepted":
                status_color = "#27ae60"  # green
            elif status.lower() == "rejected":
                status_color = "#e74c3c"  # red
            else:
                status_color = "#7f8c8d"  # gray

            # Category badge HTML
            color = CATEGORY_COLORS.get(category, "#90A4AE")
            category_html = f'''
            <div style="
                display: inline-block;
                background-color: {color};
                color: white;
                padding: 5px 20px;
                border-radius: 20px;
                font-size: 0.9em;
                margin-top: 5px;
                font-weight: 500;
            ">
                {category}
            </div>
            ''' if category else ''

            st.markdown(f"""
            <div style='
                width: 100%;
                max-width: 100%;
                background: #fff;
                border-radius: 15px;
                padding: 1rem 2rem 1rem 2rem;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                border-left: 10px solid {accent_color};
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                margin-bottom: 1rem;
            ' 
            onmouseover="this.style.transform='translateY(-4px)';this.style.boxShadow='0 8px 20px rgba(0,0,0,0.12)';"
            onmouseout="this.style.transform='';this.style.boxShadow='0 2px 6px rgba(0,0,0,0.1)';"
            >
                <div style='display: flex; align-items: center; justify-content: space-between; gap: 1rem;'>
                    <h4 style='margin: 0 0 0.5rem 0; font-size: 2rem; font-family: Inter; color: #2c3e50;'><b>{title}</b></h4>
                    {category_html} \
                </div>
                <div class='card-meta' style='font-size: 0.9rem; color: #555; display: flex; justify-content: space-between;'>
                    <span><strong>💼 &nbsp; Organization &nbsp;&nbsp; </strong> {org_name}</span><br>
                    <span><strong>Location &nbsp;&nbsp; </strong> {location} &nbsp; 📍</span>
                </div>
                <div class='card-meta' style='font-size: 0.9rem; color: #555; display: flex; justify-content: space-between;'>
                    <span><strong>📅 &nbsp; Date &nbsp;&nbsp; </strong> {event_date}</span><br>
                    <span><strong>Applied &nbsp;&nbsp; </strong> {app_date} &nbsp; 📥 </span>
                </div>
                <p style='margin: 0.5em 0;'><strong>Status:</strong> 
                    <span style='color: {status_color};'>
                        <b>{status.capitalize()}</b>
                    </span>
                </p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2= st.columns(2)

            if status.lower() == "accepted":
                chat = c.execute("""
                    SELECT id FROM chats
                    WHERE user_id = ? AND opportunity_id = ?
                """, (uid, opp_id)).fetchone()
                with col1:
                    if chat and st.button("💬 Open Chat", key=f"chat_{app_id}", use_container_width=True, type="primary"):
                        st.session_state.active_chat = chat[0]
                        navigate_to("chat")

                with col2:
                    c.execute("""
                        SELECT id FROM ratings
                        WHERE user_id = ? AND opportunity_id = ?
                    """, (uid, opp_id))
                    rating = c.fetchone()

                    if not rating:
                        if st.button("✍️ Submit Reflection", key=f"reflect_{app_id}", use_container_width=True):
                            st.session_state.show_reflection_dialog = True
                            st.session_state.reflection_opp_id = opp_id
                            st.session_state.reflection_org_id = org_id
                            st.session_state.reflection_title = title
                            reflection_dialog(conn)
                    else:
                        if st.button(
                            "📄 View Reflection",
                            key=f"view_reflect_{app_id}",
                            use_container_width=True
                        ):
                            navigate_to("reflections")

            elif status.lower() == "pending":
                if st.button(
                    "❌ Withdraw Application",
                    key=f"withdraw_{app_id}",
                    use_container_width=True):
                    with st.spinner(""):
                        c = conn.cursor()
                        c.execute(
                            "DELETE FROM applications WHERE id = ?",
                            (app_id,)
                        )
                        conn.commit()
                        time.sleep(3)
                    st.rerun()

            st.divider()

    else:
        st.info("No applications found with the selected filters.")
        if st.button("🔍 Browse Opportunities"):
            navigate_to("browse_opportunities")
