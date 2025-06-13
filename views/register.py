import streamlit as st
import time
from utils import navigate_to, hash_password, validate_email
from dialogs import confirm_org_creation, map_location_dialog

def register_page(conn):
    c = conn.cursor()
    
    st.markdown("<h1 style='font-family: Inter;'>Create Your Account</h1>", unsafe_allow_html=True)
    for i in range(3):
        st.text("")
    tab1, tab2 = st.tabs(["I'm a Student / Individual", "I'm an Organisation"])
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
        email = st.text_input("", label_visibility="collapsed", placeholder="Email (Preferably own email, non-school)", key="ind_email")
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

        if st.button("Include my location", use_container_width=True, key="include_location", type="secondary", help="You may add your location to find opportunities near you."):
            map_location_dialog()

        if st.button("Register Now", use_container_width=True, key="register_submit", type="primary"):
            if not name or not email or not age or not password or not confirm_password:
                st.toast("Please fill in all fields")
                return
            
            if not validate_email(email):
                st.toast("Please enter a valid email address")
                return
            
            if password != confirm_password:
                st.toast("Passwords do not match")
                return
            
            if len(password) < 8:
                st.error("Password must be at least 6 characters long")
                return
            
            try:
                age_int = int(age)
            except ValueError:
                st.toast("Age must be a number")
                return
                        
            c.execute("SELECT id FROM individuals WHERE email = ?", (email,))
            existing_user = c.fetchone()
            
            if not existing_user:
                c.execute("SELECT id FROM organisations WHERE email = ?", (email,))
                existing_user = c.fetchone()
            
            if existing_user:
                st.error("Email is already registered")
                time.sleep(2.5)
                st.rerun()

            with st.spinner("Processing..."):
                hashed_password = hash_password(password)
                c.execute(
                    "INSERT INTO individuals (name, age, email, password, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, age_int, email, hashed_password, st.session_state.register_lat, st.session_state.register_lon)
                )
                conn.commit()
                
                c.execute("SELECT id FROM individuals WHERE email = ?", (email,))
                new_user_id = c.fetchone()[0]
                
                st.session_state.logged_in = True
                st.session_state.user_id = new_user_id
                st.session_state.user_email = email
                st.session_state.user_type = "individual"
                
                time.sleep(5)
                st.success("Registration successful!")
                time.sleep(2)
                st.session_state.logged_in = True
                st.session_state.user_id = new_user_id
                st.session_state.user_email = email
                st.session_state.user_type = "individual"

            navigate_to("individual_dashboard")
    
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

        if st.button("Register Organisation", use_container_width=True, key="register_org_submit", type="primary"):
            if not org_name or not org_description or not work_email or not org_password or not org_confirm_password:
                st.error("Please fill in all fields")
                return
            
            if not validate_email(work_email):
                st.error("Please enter a valid email address")
                return
            
            if org_password != org_confirm_password:
                st.error("Passwords do not match")
                return
            
            if len(org_password) < 8:
                st.error("Password must be at least 6 characters long")
                return
                        
            confirm_org_creation(conn, org_name, org_description, work_email, org_password)
    
    st.text("")
    if st.button("Back to Home", use_container_width=True, icon=":material/arrow_back:"):
        navigate_to("landing")
