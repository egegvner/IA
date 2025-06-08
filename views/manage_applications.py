import streamlit as st
from utils import navigate_to

def manage_applications(conn):
    st.markdown("<h1 style='font-family: Inter;'>Manage Applications</h1>", unsafe_allow_html=True)
    c = conn.cursor()
    
    c.execute("""
    SELECT id, title FROM opportunities
    WHERE org_id = ? ORDER BY created_at DESC
    """, (st.session_state.user_id,))
    
    opportunities = c.fetchall()
    
    if not opportunities:
        st.info("You haven't posted any opportunities yet.")
        if st.button("Post Your First Opportunity"):
            navigate_to("post_opportunity")
        return
    
    opp_titles = [f"{opp[1]} (ID: {opp[0]})" for opp in opportunities]
    selected_opp_title = st.selectbox("Select Opportunity", opp_titles)
    selected_opp_id = int(selected_opp_title.split("ID: ")[1].strip(")"))
    
    status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Accepted", "Rejected"])
    
    query = """
    SELECT a.id, u.name as student_name, u.email as student_email, 
           a.status, a.application_date, u.id as student_id
    FROM applications a
    JOIN individuals u ON a.student_id = u.id
    WHERE a.opportunity_id = ?
    """
    
    params = [selected_opp_id]
    
    if status_filter != "All":
        query += " AND a.status = ?"
        params.append(status_filter.lower())
    
    query += " ORDER BY a.application_date DESC"
    
    c.execute(query, params)
    applications = c.fetchall()
    
    c.execute("SELECT title, location, event_date FROM opportunities WHERE id = ?", (selected_opp_id,))
    opp_details = c.fetchone()
    st.divider()
    
    st.subheader(f"Applications for: {opp_details[0]}")
    st.write(f"Location: {opp_details[1]} | Date: {opp_details[2]}")
    
    if applications:
        for app in applications:
            app_id, student_name, student_email, status, app_date, student_id = app
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Student:** {student_name}")
                    st.write(f"**Email:** {student_email}")
                    st.write(f"**Applied on:** {app_date}")
                    
                    if status == "accepted":
                        st.success(f"Status: {status.capitalize()}")
                    elif status == "rejected":
                        st.error(f"Status: {status.capitalize()}")
                    else:
                        st.info(f"Status: {status.capitalize()}")
                
                with col2:
                    if status == "pending":
                        if st.button("Accept", key=f"accept_{app_id}", use_container_width=True, type="primary"):
                            c.execute("UPDATE applications SET status = 'accepted' WHERE id = ?", (app_id,))
                                                        
                            c.execute("""
                            INSERT OR IGNORE INTO chats (student_id, org_id, opportunity_id)
                            VALUES (?, ?, ?)
                            """, (student_id, st.session_state.user_id, selected_opp_id))
                            
                            conn.commit()
                            st.success("Application accepted. A chat channel has been created.")
                            st.rerun()
                        
                        if st.button("Reject", key=f"reject_{app_id}", use_container_width=True):
                            c.execute("UPDATE applications SET status = 'rejected' WHERE id = ?", (app_id,))
                            conn.commit()
                            st.success("Application rejected.")
                            st.rerun()
                    
                    elif status == "accepted":
                        c.execute("""
                        SELECT id FROM chats
                        WHERE student_id = ? AND org_id = ? AND opportunity_id = ?
                        """, (student_id, st.session_state.user_id, selected_opp_id))
                        
                        chat = c.fetchone()
                        
                        if chat and st.button("Open Chat", key=f"chat_{app_id}"):
                            st.session_state.active_chat = chat[0]
                            navigate_to("chat")
                
                st.markdown("---")
    else:
        st.info("No applications found for this opportunity with the selected status.")