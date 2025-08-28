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
            ["All", "Pending", "Accepted", "Rejected, Completed"],
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
                status_color = "#f39c12"
            elif status.lower() == "accepted":
                status_color = "#2980b9"
            elif status.lower() == "rejected":
                status_color = "#e74c3c"
            elif status.lower() == "completed":
                status_color = "#27ae60"
            else:
                status_color = "#7f8c8d"

            color = CATEGORY_COLORS.get(category, "#90A4AE")
            category_html = f'''
            <div style="
                display: inline-block;
                background-color: {color};
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: 500;
            ">
                {category}
            </div>
            ''' if category else ''

            st.markdown("""
            <style>
            .app-card { 
                border:none; 
                border-radius:20px; 
                padding:20px; 
                margin:10px 0; 
                box-shadow:0px 0px 30px 1px rgba(0,0,0,0.09);
                transition: transform 0.2s cubic-bezier(0.2,0,0.2,1), box-shadow 0.2s cubic-bezier(0.2,0,0.2,1);
            }
            .app-card:hover { 
                transform: translateY(-5px) scale(1.01); 
                box-shadow:0px 8px 40px 4px rgba(44,62,80,0.13);
            }
            .app-title { font-weight:bold; font-size:1.35em; margin-bottom:10px; color:#2c3e50; }
            .app-row { display:flex; justify-content:space-between; font-size:0.97em; margin:2px 0; }
            .label { font-weight:bold; color:#333; }
            .value { color:#444; }
            </style>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="app-card" style="display:flex;align-items:stretch;">
                <div style="width:7px;border-radius:50px;background:{accent_color};margin-right:18px;"></div>
                <div style="flex:1;">
                    <div class="app-title" style="display: flex; align-items: center">
                        <div style="display: flex; align-items: center;">
                            <span>{title}</span>
                            <span style="margin-left: 10px; display: inline-block; vertical-align: middle; font-size: 0.9rem;">&nbsp;&nbsp;{category_html}</span>
                        </div>
                        <div style="min-width: 120px; font-weight: 500;">
                            <span style="background: {status_color}22; color: {status_color}; border-radius: 20px; display: inline-block; font-size: 0.9rem; padding: 5px 15px; margin-left: 20px; font-size: 0.7em;">{status.capitalize()}</span>
                        </div>
                    </div>
                    <div class="app-row" style="background-color: #f7f7f9; border-radius: 6px; padding-left: 10px; padding-right: 10px; margin-top: 5px;">
                        <span class="label">Organization:</span><span class="value">{org_name}</span>
                    </div>
                    <div class="app-row" style="background-color: #ffffff; border-radius: 6px; padding-left: 10px; padding-right: 10px; margin-top: 5px;">
                        <span class="label">Location:</span><span class="value">{location}</span>
                    </div>
                    <div class="app-row" style="background-color: #f7f7f9; border-radius: 6px; padding-left: 10px; padding-right: 10px; margin-top: 5px;">
                        <span class="label">Date:</span><span class="value">{event_date}</span>
                    </div>
                    <div class="app-row" style="background-color: #ffffff; border-radius: 6px; padding-left: 10px; padding-right: 10px; margin-top: 5px;">
                        <span class="label">Applied:</span><span class="value">{app_date}</span>
                    </div>
                    <div class="app-row" style="background-color: #f7f7f9; border-radius: 6px; padding-left: 10px; padding-right: 10px; margin-top: 5px;">
                        <span class="label">Status:</span>
                        <span class="value" style="color: {status_color}; font-weight: 600;">{status.capitalize()}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2= st.columns(2)

            if status.lower() == "accepted" or status.lower() == "completed":
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
