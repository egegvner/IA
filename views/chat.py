import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

def chat_page(conn):
    st_autorefresh(interval=2000)
    st.markdown("<h1 style='font-family: Inter;'>Private Messages</h1>", unsafe_allow_html=True)
    st.divider()
    
    c = conn.cursor()
    
    user_id   = st.session_state.user_id
    user_type = st.session_state.user_type
    other_col = "org_id" if user_type == "individual" else "user_id"

    if user_type == "individual":
        chats = c.execute("""
        SELECT c.id, o.title, org.name, c.created_at, o.location
        FROM chats c
        JOIN organisations org ON c.org_id = org.id
        JOIN opportunities o ON c.opportunity_id = o.id
        WHERE c.user_id = ?
        ORDER BY c.created_at DESC
        """, (user_id,)).fetchall()
    else:
        chats = c.execute("""
        SELECT c.id, o.title, u.name, c.created_at, o.location
        FROM chats c
        JOIN users u ON c.user_id = u.user_id
        JOIN opportunities o ON c.opportunity_id = o.id
        WHERE c.org_id = ?
        ORDER BY c.created_at DESC
        """, (user_id,)).fetchall()
        
    if not chats:
        st.info("No active chats available.")
        return
    
    c1, c2 = st.columns([1, 3], gap="large")
    with c1:
        st.markdown("<h3 style='font-family: Inter;'>Available Chats</h3>", unsafe_allow_html=True)
        st.write("")
        for chat_id, opp_title, other_name, created_at, location in chats:
            lr = c.execute(
                "SELECT last_read FROM chat_reads WHERE chat_id = ? AND user_id = ?",
                (chat_id, user_id)
            ).fetchone()
            last_read = lr[0] if lr else created_at

            unread = c.execute("""
                SELECT COUNT(*) FROM messages
                WHERE chat_id = ? 
                  AND sender_id != ?
                  AND timestamp > ?
            """, (chat_id, user_id, last_read)).fetchone()[0]

            label = f"{other_name} – [{opp_title}]"
            if unread:
                label += f" 🟢 {unread}"
            
            if st.button(label, key=f"chat_btn_{chat_id}", use_container_width=True):
                st.session_state.active_chat = chat_id
                st.session_state.temp_chat_title = opp_title
                st.session_state.temp_chat_location = location
                st.rerun()

    with c2:
        active = st.session_state.get("active_chat")
        if not active:
            st.info("Please select an active chat on the left side.")
            return

        if user_type == "individual":
            row = c.execute("""
                SELECT org.id, org.name, u.user_id, u.name
                FROM chats c
                JOIN organisations org ON c.org_id = org.id
                JOIN users u ON c.user_id = u.user_id
                WHERE c.id = ?
            """, (active,)).fetchone()
            org_id, org_name, user_id_db, user_name = row
            self_id = user_id_db
            self_name = user_name
            other_id = org_id
            other_name = org_name
        else:
            row = c.execute("""
                SELECT org.id, org.name, u.user_id, u.name
                FROM chats c
                JOIN organisations org ON c.org_id = org.id
                JOIN users u ON c.user_id = u.user_id
                WHERE c.id = ?
            """, (active,)).fetchone()
            org_id, org_name, user_id_db, user_name = row
            self_id = org_id
            self_name = org_name
            other_id = user_id_db
            other_name = user_name

        msgs = c.execute("""
            SELECT sender_id, content, timestamp
            FROM messages
            WHERE chat_id = ?
            ORDER BY timestamp ASC
        """, (active,)).fetchall()

        st.markdown(
            f"<h3 style='font-family: Inter;'>Chat with <b>{other_name}</b> ({st.session_state.temp_chat_title} at {st.session_state.temp_chat_location})</h3>",
            unsafe_allow_html=True
        )
        with st.container(height=400, border=False):
            for sender, content, ts in msgs:
                if str(sender) == str(self_id):
                    who = "Me"
                elif str(sender) == str(other_id):
                    who = other_name
                else:
                    who = "Unknown"
                try:
                    time_str = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
                except Exception:
                    time_str = ts
                with st.chat_message(name=("ai" if str(sender) == str(self_id) else "human")):
                    st.write(f"[{time_str}] **{who}:** {content}")

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute(
                """
                INSERT INTO chat_reads (chat_id, user_id, last_read)
                VALUES (?, ?, ?)
                ON CONFLICT(chat_id, user_id) DO UPDATE SET last_read=excluded.last_read
                """,
                (active, self_id, now)
            )
            conn.commit()

        st.write("")
        new_message = st.chat_input("Type your message...", key="chat_input")
        if new_message:
            c.execute(
                "INSERT INTO messages (chat_id, sender_id, content, timestamp) VALUES (?, ?, ?, ?)",
                (active, self_id, new_message.strip(), now)
            )
            st.rerun()
