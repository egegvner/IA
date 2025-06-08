import streamlit as st
from utils import navigate_to

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
    
    for i in range(6):
        st.text("")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<h3 style='font-family: Inter;'>Own an Account?</h3>", unsafe_allow_html=True)
        st.text("")
        if st.button("Login", key="login_button", use_container_width=True, type="primary", icon=":material/arrow_forward:"):
            navigate_to("login")
    
    with col2:
        st.markdown("<h3 style='font-family: Inter;'>New to the App?</h3>", unsafe_allow_html=True)
        st.text("")
        if st.button("Register", key="register_button", use_container_width=True, type="primary", icon=":material/arrow_forward:"):
            navigate_to("register")
    
    for i in range(4):
        st.text("")
    st.divider()
    
    st.markdown("<h3 style='font-family: Inter;'>About this app</h3>", unsafe_allow_html=True)
    st.markdown("""<p style='font-family: Inter;'>
    CommiUnity connects students with volunteer opportunities 
    and organizations seeking volunteers. Browse opportunities, apply to events, and track 
    your volunteering journey all in one place.
    </p>""", unsafe_allow_html=True)