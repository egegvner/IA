import streamlit as st
from datetime import datetime
from dialogs import show_reflections_dialog, edit_opportunity_dialog, delete_opportunity_dialog
from constants import CATEGORY_COLORS

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
        transition: transform 0.2s cubic-bezier(0.2,0,0.2,1), box-shadow 0.2s cubic-bezier(0.2,0,0.2,1);
    }
    .opp-card:hover { 
        transform: translateY(-5px) scale(1.01); 
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

        num_accepted = c.execute("""
            SELECT COUNT(*)
            FROM applications
            WHERE opportunity_id = ? AND status = 'accepted'
        """, (opp_id,)).fetchone()[0]

        num_rejected = c.execute("""
            SELECT COUNT(*)
            FROM applications
            WHERE opportunity_id = ? AND status = 'rejected'
        """, (opp_id,)).fetchone()[0]

        num_pending = c.execute("""
            SELECT COUNT(*)
            FROM applications
            WHERE opportunity_id = ? AND status = 'pending'
        """, (opp_id,)).fetchone()[0]
        
        rating = c.execute("""
            SELECT AVG(rating)
            FROM ratings
            WHERE opportunity_id = ?
        """, (opp_id,)).fetchone()[0]

        with st.container():
            st.markdown(f"""
            <div class="opp-card" style="display:flex;align-items:stretch;">
                <div style="width:7px;border-radius:50px;background:{color};margin-right:18px;"></div>
                <div style="flex:1;">
                    <div class="opp-title" style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center;">
                            <span>{title}</span>
                            <span style="margin-left: 10px; display: inline-block; vertical-align: middle; font-size: 1.1rem;">{category_html}</span>
                        </div>
                        <div style="text-align: right; min-width: 180px; font-weight: 500;">
                            <span style="background: #eafaf1; color: #27ae60; border-radius: 12px; padding: 8px 10px; margin-right: 4px; font-size: 0.7em;">{num_accepted}</span>
                            <span style="background: #fbeee6; color: #e67e22; border-radius: 12px; padding: 8px 10px; margin-right: 4px; font-size: 0.7em;">{num_pending}</span>
                            <span style="background: #fdeaea; color: #e74c3c; border-radius: 12px; padding: 8px 10px; margin-right: 4px; font-size: 0.7em;">{num_rejected}</span>
                            <span style="background: #f4f8fb; color: #2980b9; border-radius: 12px; padding: 8px 10px; font-size: 0.7em;">
                                ⭐️ {rating if rating else "&nbsp-"}
                            </span>
                        </div>
                    </div>
                    <div class="opp-row"><span class="label">Location:</span><span class="value">{location}</span></div>
                    <div class="opp-row"><span class="label">Date:</span><span class="value">{event_date}</span></div>
                    <div class="opp-row"><span class="label">Duration:</span><span class="value">{duration}</span></div>
                    <div class="opp-row"><span class="label">Category:</span><span class="value">{category or "—"}</span></div>
                    <div class="opp-row"><span class="label">Minimum Rating Required:</span><span class="value">⭐️ {min_rating}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                if st.button("Edit", key=f"edit_{opp_id}", use_container_width=True, icon="✏️"):
                    st.session_state.edit_opp = opp_id
                    edit_opportunity_dialog(conn)
            with col2:
                if st.button("Delete", key=f"del_{opp_id}", use_container_width=True, icon="🗑️"):
                    delete_opportunity_dialog(conn, opp_id)
            with col3:
                if st.button("Reflections", key=f"ref_{opp_id}", use_container_width=True, icon="💬"):
                    st.session_state.temp_opp_id_reflection = opp_id
                    show_reflections_dialog(conn)

            st.write("\n")
