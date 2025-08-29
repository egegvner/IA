import streamlit as st
import time
from utils import navigate_to, hash_password, validate_email, generate_unique_id
from dialogs import confirm_user_creation, confirm_org_creation, map_location_dialog

def register_page(conn):
    c = conn.cursor()
    
    st.markdown("<h1 style='font-family: Inter;'>Create Your Account</h1>", unsafe_allow_html=True)
    for i in range(3):
        st.text("")
    tab1, tab2 = st.tabs(["I'm an Individual", "I'm an Organisation"])
    st.markdown('''
        <style>
            button[data-baseweb="tab"] {
                font-size: 24px;
                margin: 0;
                width: 100%;
            }
        </style>
            ''''', unsafe_allow_html=True)
    
    with tab1:
        st.write("")
        st.write("")
        
        name = st.text_input("", label_visibility="collapsed", placeholder="First & Last name", key="ind_name")
        email = st.text_input("", label_visibility="collapsed", placeholder="Personal email", key="ind_email")
        age = st.text_input("", label_visibility="collapsed", placeholder="Age", key="ind_age")
        password = st.text_input("", label_visibility="collapsed", placeholder="Create a password", type="password", key="ind_pass")
        confirm_password = st.text_input("", label_visibility="collapsed", placeholder="Confirm password", type="password", key="ind_conf_pass")
        st.write("")
        st.write("")
        if st.session_state.register_lat and st.session_state.register_lon:
            c1, c2 = st.columns(2, gap="small")
            c1.write("**Your location is set.**")
            if c2.button("Remove my location", use_container_width=True):
                st.session_state.register_lat = None
                st.session_state.register_lon = None
                st.rerun()

        if not st.session_state.register_lat or not st.session_state.register_lon:
            if st.button("Include a location", use_container_width=True, key="include_location", type="tertiary", help="You may add a home location to find opportunities near you."):
                map_location_dialog()

        col1, col2 = st.columns([1, 3])
        if col1.button("Back to Home", use_container_width=True, icon=":material/arrow_back:"):
            navigate_to("landing")

        if col2.button("Register Now", use_container_width=True, icon=":material/arrow_forward:", key="register_submit", type="primary"):
            if name and email and age and password and confirm_password:
                if "'" in name or '"' in name or ";" in name or "--" in name:
                    st.error("Invalid characters in name")
                    return
                elif "'" in email or '"' in email or ";" in email or "--" in email:
                    st.error("Invalid characters in email")
                    return
                elif "'" in password or '"' in password or ";" in password or "--" in password:
                    st.error("Invalid characters in password")
                    return
                elif "'" in confirm_password or '"' in confirm_password or ";" in confirm_password or "--" in confirm_password:
                    st.error("Invalid characters in password confirmation")
                    return
                else:
                    if not validate_email(email):
                        st.error("Please enter a valid email address")
                        return
                    
                    if password != confirm_password:
                        st.error("Passwords do not match")
                        return
                    
                    if len(password) < 8:
                        st.error("Password must be at least 6 characters long")
                        return
                    
                    try:
                        age = int(age)
                    except ValueError:
                        st.error("Age must be a number")
                        return
                                
                    c.execute("SELECT user_id FROM users WHERE email = ?", (email,))
                    existing_user = c.fetchone()
                    
                    if not existing_user:
                        c.execute("SELECT id FROM organisations WHERE email = ?", (email,))
                        existing_user = c.fetchone()
                    
                    if existing_user:
                        st.error("An user with this email already exists.")
                        return

                    confirm_user_creation(conn, generate_unique_id(conn), name, age, email, password, st.session_state.register_lat if st.session_state.register_lat else None, st.session_state.register_lon if st.session_state.register_lon else None)
            else:
                st.error("Please fill in all fields")
                return
            
    with tab2:
        st.write("")
        st.write("")
        
        org_name = st.text_input("", label_visibility="collapsed", placeholder="Organisation name", key="org_name")
        org_description = st.text_input("", label_visibility="collapsed", placeholder="Short description", key="org_desc")
        work_email = st.text_input("", label_visibility="collapsed", placeholder="Work email", key="org_email")
        org_password = st.text_input("", label_visibility="collapsed", placeholder="Create a strong password", type="password", key="org_pass")
        org_confirm_password = st.text_input("", label_visibility="collapsed", placeholder="Confirm pass", type="password", key="org_conf_pass")
         
        st.write("")
        st.write("")
        st.write("")
        st.info("We will need to verify your organisation via an administrator.")
        colu1, colu2 = st.columns([1, 3])
        if colu1.button("Back to Home", use_container_width=True, icon=":material/arrow_back:", key="back_to_home_org"):
            navigate_to("landing")
        if colu2.button("Register Organisation", use_container_width=True, key="register_org_submit", type="primary", icon=":material/arrow_forward:"):
            if not org_name or not org_description or not work_email or not org_password or not org_confirm_password:
                st.toast("Please fill in all fields")
                return
            
            if not validate_email(work_email):
                st.toast("Please enter a valid email address")
                return
            
            if c.execute("SELECT 1 FROM organisations WHERE email = ?", (email,)).fetchone():
                st.toast("This email already exists!")
                return

            if org_password != org_confirm_password:
                st.toast("Passwords do not match")
                return
            
            if len(org_password) < 8:
                st.toast("Password must be at least 6 characters long")
                return
            
            confirm_org_creation(conn, generate_unique_id(conn), org_name, org_description, work_email, org_password)
    
    st.text("")
