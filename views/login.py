import streamlit as st
from utils import navigate_to, check_password
import time

def login_page(conn):
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
    
    st.markdown("<h1 style='font-family: Inter;'>Login to Your Account</h1>", unsafe_allow_html=True)
    st.write("Log into your personalised account to benefit from CommiUnity's features.")
    
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
    if c2.button("Log In", icon=":material/arrow_forward:", key="login_submit", use_container_width=True, type="primary"):
        with st.spinner("Logging you in..."):
            if not email or not password:
                st.error("Please enter both email and password")
                return
            
            c = conn.cursor()
            
            c.execute("SELECT id, password FROM individuals WHERE email = ?", (email,))
            user = c.fetchone()
            user_type = "individual"
            
            if not user:
                c.execute("SELECT id, password FROM organisations WHERE email = ?", (email,))
                user = c.fetchone()
                user_type = "organisation"
            
            if user and check_password(password, user[1]):
                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.session_state.user_email = email
                st.session_state.user_type = user_type
                time.sleep(2)
                
                if user_type == "individual":
                    navigate_to("individual_dashboard")
                else:
                    navigate_to("org_dashboard")
                st.rerun()
            else:
                st.error("Invalid email or password")
    
    col1, col2, col3 = st.columns([1.1, 1.3, 1])
    with col2:
        if st.button("Create a new account instead!", type="tertiary"):
            navigate_to("register")
