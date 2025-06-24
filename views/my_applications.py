import streamlit as st
from utils import navigate_to
from dialogs import reflection_dialog
import time

def my_applications(conn):
    st.markdown(
        "<h1 style='font-family: Inter;'>📄 My Applications</h1>",
        unsafe_allow_html=True
    )

    c = conn.cursor()
    uid = st.session_state.user_id

    c.execute("""
        SELECT a.id, o.title, u.name as org_name, o.location, o.event_date, 
               a.status, a.application_date, o.id as opp_id, u.id as org_id
        FROM applications a
        JOIN opportunities o ON a.opportunity_id = o.id
        JOIN organisations u ON o.org_id = u.id
        WHERE a.student_id = ?
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
             opp_id, org_id) = app

            st.markdown(f"""
            <div style='
                background-color: #ffffff;
                border-radius: 20px;
                padding-left: 30px;
                padding-top: 15px;
                padding-bottom: 15px;
                margin: 10px 0;
                box-shadow: 0px 0px 30px 2px rgba(0,0,0,0.1);
                '>
                <h4 style='margin-bottom: 0.2em; font-size: 2em;'><b>{title}</b></h4>
                <p style='margin: 0;'><strong>Organization:</strong> {org_name}</p>
                <p style='margin: 0;'><strong>Location:</strong> {location}</p>
                <p style='margin: 0;'><strong>Date:</strong> {event_date}</p>
                <p style='margin: 0;'><strong>Applied:</strong> {app_date}</p>
                <p style='margin: 0.5em 0;'><strong>Status:</strong> 
                    <span style='color: {"green" if status=="accepted" else "red" if status=="rejected" else "#F1A900"};'>
                        <b>{status.capitalize()}</b>
                    </span>
                </p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2= st.columns(2)

            if status.lower() == "accepted":
                chat = c.execute("""
                    SELECT id FROM chats
                    WHERE student_id = ? AND opportunity_id = ?
                """, (uid, opp_id)).fetchone()
                with col1:
                    if chat and st.button(
                        "💬 Open Chat",
                        key=f"chat_{app_id}",
                        use_container_width=True
                    ):
                        st.session_state.active_chat = chat[0]
                        navigate_to("chat")

                with col2:
                    c.execute("""
                        SELECT id FROM ratings
                        WHERE student_id = ? AND opportunity_id = ?
                    """, (uid, opp_id))
                    rating = c.fetchone()

                    if not rating:
                        if st.button(
                            "✍️ Submit Reflection",
                            key=f"reflect_{app_id}",
                            use_container_width=True
                        ):
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

            else:
                with col1:
                    st.write("🙁 This application was not accepted.")
            st.divider()

    else:
        st.info("No applications found with the selected filters.")
        if st.button("🔍 Browse Opportunities"):
            navigate_to("browse_opportunities")
