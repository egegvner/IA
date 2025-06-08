import streamlit as st

def admin_panel(conn):
    if st.session_state.user_email != "egeguvener0808@gmail.com":
        st.error("Access denied.")
        return
    
    st.title("Admin Panel - Pending Organisation Approvals")
    c = conn.cursor()
    c.execute("SELECT id, name, description, email, request_date FROM pending_organisations")
    pending_orgs = c.fetchall()
    
    if not pending_orgs:
        st.info("No pending organisation requests.")
        return
    
    for org in pending_orgs:
        org_id, name, description, email, request_date = org
        with st.container():
            st.subheader(name)
            st.write(f"**Description:** {description}")
            st.write(f"**Email:** {email}")
            st.write(f"**Requested on:** {request_date}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Approve", key=f"approve_{org_id}"):
                    c.execute("INSERT INTO organisations (name, description, email, password) SELECT name, description, email, password FROM pending_organisations WHERE id = ?", (org_id,))
                    c.execute("DELETE FROM pending_organisations WHERE id = ?", (org_id,))
                    conn.commit()
                    st.success(f"Approved {name}")
                    st.rerun()
            with col2:
                if st.button("Reject", key=f"reject_{org_id}"):
                    c.execute("DELETE FROM pending_organisations WHERE id = ?", (org_id,))
                    conn.commit()
                    st.warning(f"Rejected {name}")
                    st.rerun()