import streamlit as st
from db import connect_database, init_db
from utils import navigate_to

from views.admin import admin_panel
from views.browse_opportunities import browse_opportunities
from views.chat import chat_page
from views.landing import landing_page
from views.login import login_page
from views.manage_applications import manage_applications
from views.my_applications import my_applications
from views.opp_details import opp_details
from views.org_dashboard import org_dashboard
from views.org_profile import org_profile
from views.post_opportunity import post_opportunity
from views.reflections import reflections_page
from views.register import register_page
from views.student_dashboard import student_dashboard

if 'current_page' not in st.session_state:
    st.session_state.current_page = "landing"
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'notifications' not in st.session_state:
    st.session_state.notifications = []
if 'active_chat' not in st.session_state:
    st.session_state.active_chat = None
if 'show_reflection_dialog' not in st.session_state:
    st.session_state.show_reflection_dialog = False
if 'reflection_opp_id' not in st.session_state:
    st.session_state.reflection_opp_id = None
if 'reflection_org_id' not in st.session_state:
    st.session_state.reflection_org_id = None
if 'reflection_title' not in st.session_state:
    st.session_state.reflection_title = None
if 'chat_partner_name' not in st.session_state:
    st.session_state.chat_partner_name = None
if 'chat_opportunity_title' not in st.session_state:
    st.session_state.chat_opportunity_title = None
if 'opportunity_title' not in st.session_state:
    st.session_state.opportunity_title = None
if 'opportunity_description' not in st.session_state:
    st.session_state.opportunity_description = None
if 'opportunity_requirements' not in st.session_state:
    st.session_state.opportunity_requirements = None
if 'opportunity_event_date' not in st.session_state:    
    st.session_state.opportunity_event_date = None
if 'opportunity_location' not in st.session_state:
    st.session_state.opportunity_location = None
if 'opportunity_latitude' not in st.session_state:
    st.session_state.opportunity_latitude = None
if 'opportunity_longitude' not in st.session_state:
    st.session_state.opportunity_longitude = None
if 'opportunity_duration' not in st.session_state:
    st.session_state.opportunity_duration = None
if 'opportunity_category' not in st.session_state:
    st.session_state.opportunity_category = None
if 'temp_opp_id' not in st.session_state:
    st.session_state.temp_opp_id = None
if 'temp_opp_details' not in st.session_state:
    st.session_state.temp_opp_details = False
if 'temp_images' not in st.session_state:
    st.session_state.temp_images = []
if 'temp_opp_category' not in st.session_state:
    st.session_state.temp_opp_category = None
if 'pydeck_selected_point' not in st.session_state:
    st.session_state.pydeck_selected_point = None
if 'register_lat' not in st.session_state:
    st.session_state.register_lat = None
if 'register_lon' not in st.session_state:
    st.session_state.register_lon = None
if 'picked_lat' not in st.session_state:
    st.session_state.picked_lat = None
if 'picked_lon' not in st.session_state:
    st.session_state.picked_lon = None
if 'opportunity_min_required_rating' not in st.session_state:
    st.session_state.opportunity_min_required_rating = 0.0

st.set_page_config(
    page_title="CommiUnity",
    page_icon="🤝",
    layout="centered" if st.session_state.current_page in ["login", "landing", "register"] else "wide",
    initial_sidebar_state="collapsed" if st.session_state.current_page in ["landing", "login", "register"] else "expanded"
)

def main(conn):
    with st.sidebar:
        st.title("Community Connect™")
        st.text("")
        st.text("")
        if st.session_state.logged_in:
            st.write(f"User {st.session_state.user_email}")
            st.write(f"Account Type **{st.session_state.user_type.capitalize()}**")
            st.divider()
            
            if st.session_state.user_type == "individual":
                if st.button("Dashboard", use_container_width=True):
                    navigate_to("individual_dashboard")
                if st.button("Find Opportunities", use_container_width=True):
                    navigate_to("browse_opportunities")
                if st.button("My Applications", use_container_width=True):
                    navigate_to("my_applications")
                if st.button("Chat Messages", use_container_width=True):
                    navigate_to("chat")
                if st.button("My Reflections", use_container_width=True):
                    navigate_to("reflections")
                if st.session_state.user_email == "egeguvener0808@gmail.com":
                    if st.button("Admin Panel", use_container_width=True):
                        navigate_to("admin")
            
            elif st.session_state.user_type == "organisation":
                if st.button("My Dashboard", use_container_width=True):
                    navigate_to("org_dashboard")
                if st.button("Post Opportunity", use_container_width=True):
                    navigate_to("post_opportunity")
                if st.button("Manage Applications", use_container_width=True):
                    navigate_to("manage_applications")
                if st.button("Chat Messages", use_container_width=True):
                    navigate_to("chat")
                if st.button("Organization Profile", use_container_width=True):
                    navigate_to("org_profile")
            
            if st.button("Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.user_type = None
                st.session_state.user_email = None
                navigate_to("landing")
                st.rerun()

    if st.session_state.current_page == "landing":
        landing_page()
    elif st.session_state.current_page == "login":
        login_page(conn)
    elif st.session_state.current_page == "register":
        register_page(conn)
    elif st.session_state.current_page == "individual_dashboard":
        student_dashboard(conn)
    elif st.session_state.current_page == "org_dashboard":
        org_dashboard(conn)
    elif st.session_state.current_page == "browse_opportunities":
        browse_opportunities(conn)
    elif st.session_state.current_page == "post_opportunity":
        post_opportunity(conn)
    elif st.session_state.current_page == "my_applications":
        my_applications(conn)
    elif st.session_state.current_page == "manage_applications":
        manage_applications(conn)
    elif st.session_state.current_page == "chat":
        chat_page(conn)
    elif st.session_state.current_page == "reflections":
        reflections_page(conn)
    elif st.session_state.current_page == "org_profile":
        org_profile(conn)
    elif st.session_state.current_page == "admin":
        admin_panel(conn)
    elif st.session_state.current_page == "opp_details":
        opp_details(conn)
    else:
        st.error("Page not found!")

if __name__ == "__main__":
    conn = connect_database()
    init_db(conn)
    # conn.cursor().execute("ALTER TABLE opportunities ADD COLUMN min_required_rating REAL NOT NULL DEFAULT 0.0")
    conn.commit()    
    st.markdown("""<style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
                * { font-family: 'Inter', sans-serif; }
                html, body, [class*="st-"] { font-size: 13px !important; }
                </style>""", unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    .stButton>button:first-child {
        padding: 10px 10px !important;
        transition: all 0.1s ease-in-out;
        border-radius: 10px
    </style>
    """, unsafe_allow_html=True)
    
    main(conn)
    
