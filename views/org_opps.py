import streamlit as st
from datetime import datetime
from dialogs import show_reflections_dialog, edit_opportunity_dialog

def org_opps(conn):
    c = conn.cursor()
    org_id = st.session_state.user_id

    st.markdown("<h1 style='font-family: Inter;'>Manage Your Opportunities</h1>", unsafe_allow_html=True)
    st.write("Here you can edit, delete, or view reflections on each of your posted opportunities.")
    st.write("\n")

    c.execute("""
        SELECT id, title, location, event_date, duration, category, min_required_rating
        FROM opportunities
        WHERE org_id = ?
        ORDER BY created_at DESC
    """, (org_id,))
    opps = c.fetchall()

    if not opps:
        st.info("You haven’t posted any opportunities yet.")
        return

    st.markdown("""
    <style>
    .opp-card { 
        border:none; 
        border-radius:20px; 
        padding:20px; 
        margin:10px; 
        box-shadow:0px 0px 30px 1px rgba(0,0,0,0.1); 
        transition: transform 0.2s cubic-bezier(0.4,0,0.2,1), box-shadow 0.2s cubic-bezier(0.4,0,0.2,1);
    }
    .opp-card:hover { 
        transform: translateY(-5px) scale(1.02); 
        box-shadow:0px 8px 40px 4px rgba(44,62,80,0.18);
    }
    .opp-title { font-weight:bold; font-size:1.6em; margin-bottom:12px; color:#2c3e50; }
    .opp-row { display:flex; justify-content:space-between; font-size:0.95em; margin:2px 0; }
    .label { font-weight:bold; color:#333; }
    .value { color:#444; }
    </style>
    """, unsafe_allow_html=True)

    for opp in opps:
        opp_id, title, location, event_date, duration, category, min_rating = opp

        with st.container():
            st.markdown(f"""
            <div class="opp-card">
              <div class="opp-title">{title}</div>
              <div class="opp-row"><span class="label">Location:</span><span class="value">{location}</span></div>
              <div class="opp-row"><span class="label">Date:</span><span class="value">{event_date}</span></div>
              <div class="opp-row"><span class="label">Duration:</span><span class="value">{duration}</span></div>
              <div class="opp-row"><span class="label">Category:</span><span class="value">{category or "—"}</span></div>
              <div class="opp-row"><span class="label">Min Rating:</span><span class="value">⭐️ {min_rating}</span></div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                if st.button("Edit", key=f"edit_{opp_id}", use_container_width=True, icon="✏️"):
                    st.session_state.edit_opp = opp_id
                    edit_opportunity_dialog(conn)
            with col2:
                if st.button("Delete", key=f"del_{opp_id}", use_container_width=True, icon="🗑️"):
                    st.warning(f"Are you sure you want to delete opportunity #{opp_id}? This action cannot be undone.")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Yes, delete"):
                            c.execute("DELETE FROM opportunities WHERE id = ?", (opp_id,))
                            conn.commit()
                            st.toast("Opportunity deleted.")
                            del st.session_state["del_opp"]
                            st.rerun()
                    with c2:
                        if st.button("Cancel"):
                            del st.session_state["del_opp"]
                            st.rerun()
            with col3:
                if st.button("Reflections", key=f"ref_{opp_id}", use_container_width=True, icon="💬"):
                    st.session_state.temp_opp_id_reflection = opp_id
                    show_reflections_dialog(conn)

            st.write("\n")
