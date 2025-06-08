import streamlit as st
from utils import navigate_to
from dialogs import reflection_dialog

def my_applications(conn):
    """Page for students to view and manage their applications"""
    st.markdown("<h1 style='font-family: Inter;'>📄 My Applications</h1>", unsafe_allow_html=True)
    c = conn.cursor()

    c.execute("""
    SELECT a.id, o.title, u.name as org_name, o.location, o.event_date, 
           a.status, a.application_date, o.id as opp_id, u.id as org_id
    FROM applications a
    JOIN opportunities o ON a.opportunity_id = o.id
    JOIN organisations u ON o.org_id = u.id
    WHERE a.student_id = ?
    ORDER BY a.application_date DESC
    """, (st.session_state.user_id,))

    applications = c.fetchall()
    st.text("")
    st.text("")

    status_filter = st.selectbox("🔍 Filter by Status", ["All", "Pending", "Accepted", "Rejected"])

    if status_filter != "All":
        applications = [app for app in applications if app[5].lower() == status_filter.lower()]
    
    st.text("")
    st.text("")

    if applications:
        for app in applications:
            app_id, title, org_name, location, event_date, status, app_date, opp_id, org_id = app

            with st.container():
                st.markdown(f"""
                <div style='
                    border: none;
                    border-radius: 15px;
                    padding: 15px;
                    margin: 8px;
                    height: 100%;
                    background-color: #fffff;
                    transition: transform 0.3s;
                    box-shadow: 0px 0px 30px 2px rgba(0,0,0,0.1);
                '>
                    <h4 style='margin-bottom: 0.2em;'>{title}</h4>
                    <p style='margin: 0;'><strong>Organization:</strong> {org_name}</p>
                    <p style='margin: 0;'><strong>Location:</strong> {location}</p>
                    <p style='margin: 0;'><strong>Event Date:</strong> {event_date}</p>
                    <p style='margin: 0;'><strong>Applied On:</strong> {app_date}</p>
                    <p style='margin: 0.5em 0;'><strong>Status:</strong> 
                        <span style='color: {"green" if status == "accepted" else "red" if status == "rejected" else "#F1A900"};'>
                            <b>{status.capitalize()}</b>
                        </span>
                    </p>
                </div>
                """, unsafe_allow_html=True)

                col1, col2, col3 = st.columns(3)
                
                if status.lower() == "accepted":
                    c.execute("""
                        SELECT id FROM chats
                        WHERE student_id = ? AND opportunity_id = ?
                    """, (st.session_state.user_id, opp_id))
                    chat = c.fetchone()

                    with col1:
                        if chat and st.button("💬 Open Chat", key=f"chat_{app_id}", use_container_width=True):
                            st.session_state.active_chat = chat[0]
                            navigate_to("chat")

                    with col2:
                        c.execute("""
                            SELECT id FROM ratings
                            WHERE student_id = ? AND opportunity_id = ?
                        """, (st.session_state.user_id, opp_id))
                        rating = c.fetchone()

                        if not rating:
                            if st.button("✍️ Submit Reflection", key=f"reflect_{app_id}", use_container_width=True):
                                st.session_state.show_reflection_dialog = True
                                st.session_state.reflection_opp_id = opp_id
                                st.session_state.reflection_org_id = org_id
                                st.session_state.reflection_title = title
                                reflection_dialog(conn)
                                
                        else:
                            if st.button("📄 View Reflection", key=f"view_reflect_{app_id}", use_container_width=True):
                                navigate_to("reflections")

                elif status.lower() == "pending":
                    with col1:
                        if st.button("❌ Withdraw Application", key=f"withdraw_{app_id}", use_container_width=True):
                            c.execute("DELETE FROM applications WHERE id = ?", (app_id,))
                            conn.commit()
                            st.success("Application withdrawn successfully ✅")
                            st.rerun()

                elif status.lower() == "rejected":
                    with col1:
                        st.write("🙁 This application was not accepted.")

            st.markdown("---")
    else:
        st.info("No applications found with the selected status.")
        if st.button("🔍 Browse Opportunities"):
            navigate_to("browse_opportunities")