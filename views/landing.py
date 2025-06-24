import streamlit as st
from utils import navigate_to
import time

def landing_page():
    st.markdown('''
    <style>
            [data-testid="stAppViewContainer"] {
            background: linear-gradient(90deg, #ffffff, #cfe6ff)
                }
            [data-testid="stHeader"]{
            background: linear-gradient(90deg, #ffffff, #cfe6ff)
                }
    </style>
    ''', unsafe_allow_html=True)
    
    st.markdown("<h1 style='font-family: Inter;'>CommiUnity</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-family: Inter;'>Unite. Engage. Transform.</p>", unsafe_allow_html=True)
    
    for i in range(7):
        st.text("")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<h3 style='font-family: Inter;'>Own an Account?</h3>", unsafe_allow_html=True)
        st.text("")
        if st.button("Login", key="login_button", use_container_width=True, type="primary", icon=":material/arrow_forward:"):
            with st.spinner(""):
                time.sleep(1)
            navigate_to("login")

    with col2:
        st.markdown("<h3 style='font-family: Inter;'>New to the App?</h3>", unsafe_allow_html=True)
        st.text("")
        if st.button("Register", key="register_button", use_container_width=True, type="primary", icon=":material/arrow_forward:"):
            with st.spinner(""):
                time.sleep(1)
            navigate_to("register")
    
    for i in range(5):
        st.text("")
    st.divider()
    
    st.markdown("<h3 style='font-family: Inter;'>About this app</h3>", unsafe_allow_html=True)
    st.markdown("""<p style='font-family: Inter;'>
    CommiUnity connects students with volunteer opportunities 
    and organizations seeking volunteers. Browse opportunities, apply to events, and track 
    your volunteering journey all in one place.
    </p>""", unsafe_allow_html=True)

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
