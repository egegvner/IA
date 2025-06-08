import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

def chat_page(conn):
    st_autorefresh(interval=5000)
    st.markdown("<h1 style='font-family: Inter;'>Chats</h1>", unsafe_allow_html=True)
    st.divider()
    
    c = conn.cursor()
    
    if st.session_state.user_type == "individual":
        c.execute("""
        SELECT c.id, u.name as org_name, o.title, c.created_at, o.id as opp_id, u.id as org_id
        FROM chats c
        JOIN organisations u ON c.org_id = u.id
        JOIN opportunities o ON c.opportunity_id = o.id
        WHERE c.student_id = ?
        ORDER BY c.created_at DESC
        """, (st.session_state.user_id,))
    else:
        c.execute("""
        SELECT c.id, u.name as student_name, o.title, c.created_at, o.id as opp_id, u.id as student_id
        FROM chats c
        JOIN individuals u ON c.student_id = u.id
        JOIN opportunities o ON c.opportunity_id = o.id
        WHERE c.org_id = ?
        ORDER BY c.created_at DESC
        """, (st.session_state.user_id,))
    
    chats = c.fetchall()
    
    if not chats:
        st.info("No active chats available.")
        return
    
    c1, c2 = st.columns([1, 3], gap="large")
    with c1:
        st.markdown("<h3 style='font-family: Inter;'>Available Chats</h3>", unsafe_allow_html=True)
        st.text("")
        for chat in chats:
            chat_id, other_name, opp_title, chat_date, opp_id, other_id = chat
            if st.button(f"{other_name} - {opp_title}", key=f"chat_btn_{chat_id}", use_container_width=True):
                st.session_state.active_chat = chat_id
                st.rerun()
    
    with c2:
        if st.session_state.active_chat:
            # Get participant names for THIS chat
            if st.session_state.user_type == "individual":
                c.execute("""
                SELECT o.name 
                FROM chats
                JOIN organisations o ON org_id = o.id
                WHERE chats.id = ?
                """, (st.session_state.active_chat,))
                other_name = c.fetchone()[0]
            else:
                c.execute("""
                SELECT i.name 
                FROM chats
                JOIN individuals i ON student_id = i.id
                WHERE chats.id = ?
                """, (st.session_state.active_chat,))
                other_name = c.fetchone()[0]

            # Fetch messages
            c.execute("SELECT sender_id, content, timestamp FROM messages WHERE chat_id = ? ORDER BY timestamp ASC", 
                      (st.session_state.active_chat,))
            messages = c.fetchall()
            
            # Display chat header
            st.markdown(f"<h3>Chat with {other_name}</h3>", unsafe_allow_html=True)
            
            # Display messages
            with st.container(height=400, border=False):
                for msg in messages:
                    sender_id, content, timestamp = msg
                    # Determine display name
                    display_name = "You" if sender_id == st.session_state.user_id else other_name
                    
                    with st.chat_message(name="human" if sender_id == st.session_state.user_id else "ai"):
                        st.write(f"**{display_name} ({datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%H:%M')}):** {content}")
            
            # Message input
            new_message = st.chat_input("Type your message here...")
            if new_message:
                c.execute("INSERT INTO messages (chat_id, sender_id, content) VALUES (?, ?, ?)",
                          (st.session_state.active_chat, st.session_state.user_id, new_message))
                conn.commit()
                st.rerun()