
import streamlit as st
from db import get_db_connection, init_db
from utils import navigate_to
from streamlit_cookies_controller import CookieController
import time
import os
import shutil

from views.admin import admin_panel
from views.browse_opportunities import browse_opportunities
from views.chat import chat_page
from views.landing import landing_page
from views.login import login_page
from views.manage_applications import manage_applications
from views.user_applications import user_applications
from views.opp_details import opp_details
from views.org_dashboard import org_dashboard
from views.org_opps import org_opps
from views.post_opportunity import post_opportunity
from views.reflections import reflections_page
from views.register import register_page
from views.user_dashboard import user_dashboard

def main():
    if 'current_page' not in st.session_state or st.session_state.current_page is None:
        st.session_state.current_page = "landing"

    if st.session_state.current_page == "landing" or st.session_state.current_page == "login" or st.session_state.current_page == "register":
        st.set_page_config(
            page_title="VolunTree",
            page_icon="🤝",
            layout="centered",
            initial_sidebar_state="collapsed"
        )
    else:
        st.set_page_config(
            page_title="VolunTree",
            page_icon="🤝",
            layout="wide",
            initial_sidebar_state="expanded"
        )

    conn = get_db_connection("./voluntree_1000.db")
    init_db(conn)

    controller = CookieController()
    try:
        if controller.get("user_id"):
            st.session_state.logged_in = True
            st.session_state.user_id = controller.get("user_id")
            st.session_state.user_type = controller.get("user_type")
            st.session_state.user_email = controller.get("user_email")
            if st.session_state.current_page in [None, "landing"]:
                if st.session_state.user_type == "individual":
                    st.session_state.current_page = "user_dashboard"
                    st.rerun()
                else:
                    st.session_state.current_page = "org_dashboard"
                    st.rerun()
        else:
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.user_type = None
            st.session_state.user_email = None
            if st.session_state.current_page is None:
                st.session_state.current_page = "landing"

    except Exception as e:
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_type = None
        st.session_state.user_email = None
        st.rerun()

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

    st.markdown(
    """
    <style>
    [aria-label="Sidebar"] div.stButton > button {
        border: none; /* Remove border */
        font-size: 14px !important; /* Reduce font size */
        padding: 8px 15px !important; /* Adjust padding */
        margin: 3px 0 !important; /* Reduce spacing */
        width: 100%; /* Full width for alignment */
        border-radius: 8px; /* Optional: Rounded corners */
        background-color: #222; /* Dark button background */
        color: white; /* White text */
        transition: background-color 0.3s ease-in-out;
    }

    [aria-label="Sidebar"] div.stButton > button:hover {
        background-color: #444 !important; /* Lighter gray on hover */
        color: white !important;
    }

    [aria-label="Sidebar"] div[data-testid="column"] {
        padding: 0px !important;
    }

    [aria-label="Sidebar"] button[data-baseweb="tab"] {
        font-size: 16px !important; /* Reduce tab text size */
        margin: 0 !important;
        padding: 5px !important;
        width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
    if 'temp_chat_title' not in st.session_state:
        st.session_state.temp_chat_title = None
    if 'temp_chat_location' not in st.session_state:
        st.session_state.temp_chat_location = None
    if 'opp_max_applicants' not in st.session_state:
        st.session_state.opp_max_applicants = 0
    if 'rating_user_name'not in st.session_state:
        st.session_state.rating_user_name = None
    if 'rating_opp_title'not in st.session_state:
        st.session_state.rating_opp_title = None
    if 'rating_user_id' not in st.session_state:
        st.session_state.rating_user_id = 0
    if 'rating_org_id' not in st.session_state:
        st.session_state.rating_org_id = 0
    if 'temp_opp_id_reflection' not in st.session_state:
        st.session_state.temp_opp_id_reflection = 0
    if 'edit_opp'not in st.session_state:
        st.session_state.edit_opp = 0

    st.markdown(
        """
        <style>
        /* Target only the button whose aria-label is "Dashboard" */
        div.stButton > button[aria-label="Dashboard"] {
            display: flex !important;
            justify-content: flex-start !important;
            width: 100% !important;
            padding-left: 1rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True
        )

    with st.sidebar:
        st.title("VolunTree")
        st.text("")
        st.text("")
        if st.session_state.logged_in:
            st.write(f"User {st.session_state.user_email}")
            st.write(f"Account Type **{st.session_state.user_type.capitalize()}**")
            st.divider()
            
            if st.session_state.user_type == "individual":
                if st.button("Dashboard", use_container_width=True, icon=":material/dashboard:", key="dashboard-btn"):
                    navigate_to("user_dashboard")
                if st.button("Find Opportunities", use_container_width=True, icon=":material/explore:"):
                    navigate_to("browse_opportunities")
                if st.button("My Applications", use_container_width=True, icon=":material/rule:"):
                    navigate_to("user_applications")
                if st.button("Chat Messages", use_container_width=True, icon=":material/chat:"):
                    navigate_to("chat")
                if st.button("My Reflections", use_container_width=True, icon=":material/thumbs_up_down:"):
                    navigate_to("reflections")
                if st.session_state.user_email == "egeguvener0808@gmail.com":
                    if st.button("Admin Panel", use_container_width=True, icon=":material/admin_panel_settings:"):
                        navigate_to("admin")
            
            elif st.session_state.user_type == "organisation":
                if st.button("My Dashboard", use_container_width=True, icon=":material/dashboard:"):
                    navigate_to("org_dashboard")
                if st.button("Post Opportunity", use_container_width=True, icon=":material/add_2:"):
                    navigate_to("post_opportunity")
                if st.button("Manage Applications", use_container_width=True, icon=":material/rule:"):
                    navigate_to("manage_applications")
                if st.button("My Opportunities & Ratings", use_container_width=True, icon=":material/assignment:"):
                    navigate_to("org_opps")
                if st.button("Chat Messages", use_container_width=True, icon=":material/chat:"):
                    navigate_to("chat")
            
            if st.button("Logout", use_container_width=True, icon=":material/logout:"):
                with st.spinner("Logging out..."):
                    st.session_state.logged_in = False
                    st.session_state.user_id = None
                    st.session_state.user_type = None
                    st.session_state.user_email = None
                    st.session_state.current_page = "landing"  # <-- Add this line
                    controller.remove("user_id")
                    controller.remove("user_type")
                    controller.remove("user_email")
                    time.sleep(2)
                st.rerun()

    if st.session_state.current_page == "landing":
        landing_page()
    elif st.session_state.current_page == "login":
        login_page(conn)
    elif st.session_state.current_page == "register":
        register_page(conn)
    elif st.session_state.current_page == "user_dashboard":
        user_dashboard(conn)
    elif st.session_state.current_page == "org_dashboard":
        org_dashboard(conn)
    elif st.session_state.current_page == "browse_opportunities":
        browse_opportunities(conn)
    elif st.session_state.current_page == "post_opportunity":
        post_opportunity(conn)
    elif st.session_state.current_page == "user_applications":
        user_applications(conn)
    elif st.session_state.current_page == "manage_applications":
        manage_applications(conn)
    elif st.session_state.current_page == "chat":
        chat_page(conn)
    elif st.session_state.current_page == "reflections":
        reflections_page(conn)
    elif st.session_state.current_page == "org_opps":
        org_opps(conn)
    elif st.session_state.current_page == "admin":
        admin_panel(conn)
    elif st.session_state.current_page == "opp_details":
        opp_details(conn)
    else:
        st.error("Page not found!")

if __name__ == "__main__":
    main()
