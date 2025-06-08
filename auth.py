import streamlit as st
import bcrypt
import time

ADMIN_EMAILS = ["egeguvener0808@gmail.com"]

def login_if_needed(conn):
    if "user_id" not in st.session_state:
        show_login(conn)

def check_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

def show_login(conn):
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
    st.write("Log into your personalised account to benefit from the platform's features.")

    for _ in range(5): st.text("")
    email = st.text_input("Email", label_visibility="collapsed", placeholder="Email")
    st.text("")
    password = st.text_input("Password", label_visibility="collapsed", type="password", placeholder="Password")
    for _ in range(3): st.text("")

    if st.button("Log In", key="login_submit", use_container_width=True, type="primary"):
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
                st.rerun()
            else:
                st.error("Invalid email or password")

    if st.button("Back", icon=":material/arrow_back:", use_container_width=True):
        st.session_state.pop("user_id", None)
        st.rerun()

    col1, col2, col3 = st.columns([1.1, 1.3, 1])
    with col2:
        if st.button("Create a new account instead!", type="tertiary"):
            st.session_state.auth_mode = "register"
            st.rerun()

    st.markdown("""
            <style>
            .footer {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                background-color: #f8f9fa;
                text-align: center;
                padding: 10px 0;
                font-size: 8px;
                color: gray;
                border-top: 1px solid #e9ecef;
            }
            </style>
            <div class="footer">
                © 2025 CommiUnity, entirely by Ege Güvener.
            </div>
        """, unsafe_allow_html=True)