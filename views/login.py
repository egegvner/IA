import streamlit as st
from utils import navigate_to, check_password
import time
from streamlit_cookies_controller import CookieController

def login_page(conn):
    c = conn.cursor()
    controller = CookieController()
    st.markdown('''
    <style>
            [data-testid="stTextInputRootElement"] {
            border-radius: 13px;
            color: white;
            padding-left: 10px;
            height: 40px;
            }
    </style>
    ''', unsafe_allow_html=True)
    
    st.markdown("<h1 style='font-family: Inter;'>Login to VolunTree</h1>", unsafe_allow_html=True)
    st.write("Log into your personalised account to benefit from VolunTree's features.")
    
    for i in range(5):
        st.text("")

    email = st.text_input("Email", label_visibility="collapsed", placeholder="Email")
    st.text("")
    password = st.text_input("Password", label_visibility="collapsed", type="password", placeholder="Password")
    
    for i in range(3):
        st.text("")
    
    c1, c2 = st.columns([1, 3])
    if c1.button("Back", icon=":material/arrow_back:", use_container_width=True):
        navigate_to("landing")

    if c2.button("Log In", icon=":material/arrow_forward:", use_container_width=True, type="primary"):
        if "'" in email or "'" in email or ";" in email or "--" in email:
            st.error("Invalid characters in email")
            return
        elif "'" in password or '"' in password or ";" in password or "--" in password:
            st.error("Invalid characters in password")
            return
        else:
            if not email or not password:
                st.error("Please enter both email and password")
                return                
            try:
                user = c.execute("SELECT user_id, password FROM users WHERE email = ?", (email,)).fetchone()
                user_type = "individual"
                
                if not user:
                    user = c.execute("SELECT id, password FROM organisations WHERE email = ?", (email,)).fetchone()
                    user_type = "organisation"
                
                if user and check_password(password, user[1]):
                    with st.spinner("Logging you in..."):
                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.session_state.user_email = email
                        st.session_state.user_type = user_type
                        
                        controller.set("user_id", user[0])
                        controller.set("user_email", email)
                        controller.set("user_type", user_type)
                        
                        time.sleep(2)
                        
                        if user_type == "individual":
                            navigate_to("user_dashboard")
                        else:
                            navigate_to("org_dashboard")
                else:
                    st.error("Invalid email or password")
            except Exception as e:
                st.error(f"Database error: {str(e)}")
    
    col1, col2, col3 = st.columns([1.1, 1.3, 1])
    with col2:
        if st.button("Create a new account instead!", type="tertiary"):
            with st.spinner(""):
                time.sleep(0.5)
            navigate_to("register")
