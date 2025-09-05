import streamlit as st
from utils import navigate_to
from dialogs import rate_user_dialog
import time
import base64

def manage_applications(conn):
    st.markdown("<h1 style='font-family: Inter;'>Manage Applications</h1>", unsafe_allow_html=True)
    st.text("")
    st.text("")
    st.text("")
    
    c = conn.cursor()
    
    opportunities = c.execute("""
    SELECT id, title, location FROM opportunities
    WHERE org_id = ? ORDER BY created_at DESC
    """, (st.session_state.user_id,)).fetchall()
        
    if not opportunities:
        st.info("You haven't posted any opportunities yet.")
        if st.button("Post Your First Opportunity"):
            navigate_to("post_opportunity")
        return
    
    opp_titles = [f"{opp[1]} ({opp[2]}) [ID: {opp[0]}]" for opp in opportunities]
    c1, c2, c3 = st.columns([3, 3, 0.8], vertical_alignment="center", gap="small")

    selected_opp_title = c1.selectbox("Show Applications For", opp_titles)
    selected_opp_id = int(selected_opp_title.split("ID: ")[1].strip("]"))
    status_filter = c2.selectbox("Filter by Status", ["All", "Pending", "Accepted", "Rejected", "Completed"])
    
    if c3.button("Refresh", use_container_width=True, icon=":material/autorenew:", type="primary"):
        st.rerun()

    query = """
    SELECT a.id, u.name as user_name, u.email as user_email,
           a.status, a.application_date, u.user_id as user_id
    FROM applications a
    JOIN users u ON a.user_id = u.user_id
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

    st.text("")
    st.text("")

    st.markdown(f"<h2 style='font-family: Inter;'>Applicants for {opp_details[0]} at {opp_details[1]}</h2>", unsafe_allow_html=True)
    st.divider()
    if applications:
        for app in applications:
            app_id, user_name, user_email, status, app_date, user_id = app
            user_rating = c.execute("SELECT AVG(rating) from user_ratings WHERE user_id = ?",
                                     (user_id,)).fetchone()[0]
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1], gap="large")
                with col1:
                    # Get user profile picture if available
                    user_profile = c.execute("SELECT profile_picture FROM users WHERE user_id = ?", (user_id,)).fetchone()
                    if user_profile and user_profile[0]:
                        # Insert custom CSS for circle profile picture (only once)
                        st.markdown("""
                        <style>
                        .profile-picture-circle {
                            border-radius: 50%;
                            object-fit: cover;
                            width: 150px;
                            height: 150px;
                            border: 3px solid #fff;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.15), 0 0 0 1px rgba(0,0,0,0.05);
                            transition: all 0.3s ease-in-out;
                        }
                        .profile-picture-container {
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            margin-bottom: 10px;
                            position: relative;
                            padding: 5px;
                        }
                        </style>
                        """, unsafe_allow_html=True)

                        def detect_image_mime_type(img_bytes):
                            if not img_bytes or len(img_bytes) < 10:
                                return None
                            if img_bytes.startswith(b'\xff\xd8\xff'):
                                return 'image/jpeg'
                            elif img_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
                                return 'image/png'
                            elif img_bytes.startswith(b'GIF87a') or img_bytes.startswith(b'GIF89a'):
                                return 'image/gif'
                            else:
                                return 'image/png'

                        img_bytes = user_profile[0]
                        img_base64 = base64.b64encode(img_bytes).decode()
                        mime_type = detect_image_mime_type(img_bytes)
                        if mime_type:
                            st.markdown(f"""
                            <div class="profile-picture-container">
                                <img src="data:{mime_type};base64,{img_base64}" class="profile-picture-circle" alt="Profile Picture">
                            </div>
                            <div style="text-align:center; font-size:0.9rem; color:#888;">Member since 2025/09/02</div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class="profile-picture-container">
                                <img src="data:image/png;base64,{img_base64}" class="profile-picture-circle" alt="Profile Picture">
                            </div>
                            <div style="text-align:center; font-size:0.9rem; color:#888;">Member since 2025/09/02</div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="profile-picture-container">
                            <img src="user.png" class="profile-picture-circle" alt="Default Profile Picture">
                        </div>
                        <div style="text-align:center; font-size:0.9rem; color:#888;">Member since 2025/09/02</div>
                        """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                        <div style="
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            font-family: Inter, sans-serif;
                        ">
                        <div style="font-size:1.8rem; font-weight:600;">{user_name}</div>
                        <div style="font-size:1.3rem; font-weight:600;">⭐️ {round(user_rating if user_rating else 0.0, 2)}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.text("")
                    st.text("")
                    st.write(f"{user_email}")
                    st.write(f"**Applied on:** {app_date}")
                    
                    if status == "accepted":
                        st.info(f"{status.capitalize()}")
                    elif status == "rejected":
                        st.error(f"{status.capitalize()}")
                    elif status == "completed":
                        st.success(f"{status.capitalize()}")

                chat = c.execute("""
                        SELECT id FROM chats
                        WHERE user_id = ? AND org_id = ? AND opportunity_id = ?
                        """, (user_id, st.session_state.user_id, selected_opp_id)).fetchone()
                
                with col3:
                    if status == "pending":
                        if st.button("Accept", key=f"accept_{app_id}", use_container_width=True, type="primary"):
                            with st.spinner(""):
                                c.execute("UPDATE applications SET status = 'accepted', status_updated = 1 WHERE id = ?", (app_id,))
                                                            
                                c.execute("""
                                INSERT OR IGNORE INTO chats (user_id, org_id, opportunity_id)
                                VALUES (?, ?, ?)
                                """, (user_id, st.session_state.user_id, selected_opp_id))
                                
                                conn.commit()
                                time.sleep(2)
                            st.rerun()
                        
                        if st.button("Reject", key=f"reject_{app_id}", use_container_width=True):
                            with st.spinner(""):
                                c.execute("UPDATE applications SET status = 'rejected', status_updated = 1 WHERE id = ?", (app_id,))
                                conn.commit()
                                time.sleep(2)
                            st.rerun()

                        if st.button("Open Chat", key=f"open_chat_{app_id}", use_container_width=True):
                            c.execute("""
                                SELECT id FROM chats
                                WHERE user_id = ? AND org_id = ? AND opportunity_id = ?
                            """, (user_id, st.session_state.user_id, selected_opp_id))
                            chat = c.fetchone()
                            if not chat:
                                c.execute("""
                                    INSERT INTO chats (user_id, org_id, opportunity_id)
                                    VALUES (?, ?, ?)
                                """, (user_id, st.session_state.user_id, selected_opp_id))
                                conn.commit()
                                c.execute("""
                                    SELECT id FROM chats
                                    WHERE user_id = ? AND org_id = ? AND opportunity_id = ?
                                """, (user_id, st.session_state.user_id, selected_opp_id))
                                chat = c.fetchone()
                            if chat:
                                st.session_state.active_chat = chat[0]
                                navigate_to("chat")
                    
                    elif status == "accepted":
                        already_completed = c.execute("""
                            SELECT 1 FROM applications
                            WHERE id = ? AND status = 'completed'
                        """, (app_id,)).fetchone()

                        if not already_completed:
                            if st.button("Mark as Completed", key=f"complete_{app_id}", use_container_width=True, type="primary"):
                                with st.spinner(""):
                                    c.execute("UPDATE applications SET status = 'completed', status_updated = 1 WHERE id = ?", (app_id,))
                                    conn.commit()
                                    time.sleep(2)
                                st.rerun()

                    elif status == "completed":
                         already_rated = c.execute("""
                        SELECT 1 FROM user_ratings
                        WHERE user_id = ? AND org_id = ? AND opportunity_id = ?
                        """, (user_id, st.session_state.user_id, selected_opp_id)).fetchall()
                    
                    if not already_rated:
                        with st.popover("Rate this user", use_container_width=True, icon=":material/star_rate:"):
                            st.markdown("<h3 style='font-family: Inter;'>Rate User</h3>", unsafe_allow_html=True)
                            rating = st.slider("Rate this user (1 = worst, 5 = best):", 1, 5, 3, key="rating_slider")
                            col1, col2 = st.columns(2)
                            with col2:
                                if st.button("Submit", use_container_width=True, type="primary"):
                                    with st.spinner(""):
                                        c.execute("""
                                        INSERT INTO user_ratings (user_id, org_id, opportunity_id, rating, created_at)
                                        VALUES (?, ?, ?, ?, datetime('now'))
                                        """, (
                                            user_id,
                                            st.session_state.user_id,
                                            selected_opp_id,
                                            rating,
                                        ))
                                        conn.commit()
                                        st.session_state.show_rating_dialog = False
                                        st.session_state.rating_user_id = None
                                        st.session_state.rating_opp_id = None
                                        st.session_state.rating_org_id = None
                                        st.session_state.rating_user_name = None
                                        st.session_state.rating_opp_title = None
                                    time.sleep(1)
                                    st.rerun()
                            with col1:
                                if st.button("Cancel", use_container_width=True):
                                    st.session_state.show_rating_dialog = False
                                    st.rerun()
                         
                    elif status == "rejected":
                        if st.button("Undo Rejection", use_container_width=True):
                            with st.spinner(""):
                                c.execute("UPDATE applications SET status = 'pending', status_updated = 1 WHERE id = ?", (app_id,))
                                conn.commit()
                                time.sleep(2)
                            st.rerun()

                st.markdown("---")
    else:
        st.info("No applications found for this opportunity with the selected status.")

