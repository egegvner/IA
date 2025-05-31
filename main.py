import streamlit as st
import sqlite3
import bcrypt
import pandas as pd
import re
from datetime import datetime
import os
import json
import time
from streamlit_autorefresh import st_autorefresh

if 'current_page' not in st.session_state:
    st.session_state.current_page = "landing"

st.set_page_config(
    page_title="Community Engagement Platform",
    page_icon="🤝",
    layout="centered" if st.session_state.current_page == "login" or st.session_state.current_page == "landing" or st.session_state.current_page == "register" else "wide",
    initial_sidebar_state="collapsed" if st.session_state.current_page == "landing" or st.session_state.current_page == "login" or st.session_state.current_page == "register" else "expanded"
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

@st.cache_resource
def connect_database():
    conn = sqlite3.connect("community_platform4.db", check_same_thread=False)
    return conn

def init_db(conn):
    c = conn.cursor()
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS individuals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS organisations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS pending_organisations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        location TEXT NOT NULL,
        event_date TEXT NOT NULL,
        duration TEXT NOT NULL,
        description TEXT NOT NULL,
        requirements TEXT,
        category TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (org_id) REFERENCES organisations (id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        opportunity_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES individuals (id),
        FOREIGN KEY (opportunity_id) REFERENCES opportunities (id),
        UNIQUE(student_id, opportunity_id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        org_id INTEGER NOT NULL,
        opportunity_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        reflection TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES individuals (id),
        FOREIGN KEY (org_id) REFERENCES organisations (id),
        FOREIGN KEY (opportunity_id) REFERENCES opportunities (id),
        UNIQUE(student_id, opportunity_id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        org_id INTEGER NOT NULL,
        opportunity_id INTEGER NOT NULL,
        supabase_channel TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES individuals (id),
        FOREIGN KEY (org_id) REFERENCES organisations (id),
        FOREIGN KEY (opportunity_id) REFERENCES opportunities (id),
        UNIQUE(student_id, org_id, opportunity_id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        sender_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chat_id) REFERENCES chats (id),
        FOREIGN KEY (sender_id) REFERENCES individuals (id)
    )
    ''')
    
    conn.commit()

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(provided_password, stored_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

def validate_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def navigate_to(page):
    st.session_state.current_page = page
    for key in list(st.session_state.keys()):
        if key.startswith('temp_'):
            del st.session_state[key]

    st.rerun()

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
                if st.session_state.user_email == "ege_guvener@britishschool.org.cn":
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
    else:
        st.error("Page not found!")

def register_organisation(conn, name, description, email, password):
    c = conn.cursor()
    with st.spinner("Processing..."):
        c.execute("INSERT INTO pending_organisations (name, description, email, password) VALUES (?, ?, ?, ?)",
                (name, description, email, hash_password(password)))
        conn.commit()
        time.sleep(2)
    st.success("Your registration request has been submitted. Awaiting admin approval.")
    time.sleep(3)
    st.rerun()

def admin_panel(conn):
    if st.session_state.user_email != "ege_guvener@britishschool.org.cn":
        st.error("Access denied.")
        return
    
    st.title("Admin Panel - Pending Organisation Approvals")
    c = conn.cursor()
    c.execute("SELECT id, name, description, email, request_date FROM pending_organisations")
    pending_orgs = c.fetchall()
    
    if not pending_orgs:
        st.info("No pending organisation requests.")
        return
    
    for org in pending_orgs:
        org_id, name, description, email, request_date = org
        with st.container():
            st.subheader(name)
            st.write(f"**Description:** {description}")
            st.write(f"**Email:** {email}")
            st.write(f"**Requested on:** {request_date}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Approve", key=f"approve_{org_id}"):
                    c.execute("INSERT INTO organisations (name, description, email, password) SELECT name, description, email, password FROM pending_organisations WHERE id = ?", (org_id,))
                    c.execute("DELETE FROM pending_organisations WHERE id = ?", (org_id,))
                    conn.commit()
                    st.success(f"Approved {name}")
                    st.rerun()
            with col2:
                if st.button("Reject", key=f"reject_{org_id}"):
                    c.execute("DELETE FROM pending_organisations WHERE id = ?", (org_id,))
                    conn.commit()
                    st.warning(f"Rejected {name}")
                    st.rerun()

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
    st.markdown("<h1 style='font-family: Inter;'>Community Connect™</h1>", unsafe_allow_html=True)
    st.write("Connects students with volunteering opportunities.")
    for i in range(4):
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
    
    st.markdown("---")
    st.header("About this Platform")
    st.write("""
    The Community Engagement Platform connects students with volunteer opportunities 
    and organizations seeking volunteers. Browse opportunities, apply to events, and track 
    your volunteering journey all in one place.
    """)

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
    st.write("Log into your personalised account to benefit from the platform's features.")
    for i in range(5):
        st.text("")
    email = st.text_input("Email", label_visibility="collapsed", placeholder="Email")
    st.text("")
    password = st.text_input("Password", label_visibility="collapsed", type="password", placeholder="Password")
    for i in range(3):
        st.text("")
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
                
                if user_type == "individual":
                    navigate_to("individual_dashboard")
                else:
                    navigate_to("org_dashboard")
                st.rerun()
            else:
                st.error("Invalid email or password")

    if st.button("Back", icon=":material/arrow_back:", use_container_width=True):
        navigate_to("landing")
    
    col1, col2, col3 = st.columns([1.1, 1.3, 1])
    with col2:
        if st.button("Create a new account instead!", type="tertiary"):
                navigate_to("register")

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
                font-size: 10px;
                color: gray;
                border-top: 1px solid #e9ecef;
            }
            </style>
            <div class="footer">
                © 2025 Community Engagement Platform by Ege Güvener.
            </div>
        """, unsafe_allow_html=True)

@st.dialog(" ")
def confirm_org_creation(conn, name, description, email, password):
    c = conn.cursor()
    st.markdown("<h1 style='font-family: Inter;'>Confirm Organisation Application Request</h1>", unsafe_allow_html=True)
    st.write("Please confirm the details below before creating your organisation account.")
    st.divider()
    st.write("Name: ", name)
    st.write("Description:", description)
    st.write("Email:", email)
    st.write("Password:", "*" * len(password))
    st.divider()
    checkbox = st.checkbox("I confirm the details above are correct and aware that **I cannot change** them later.")
    if st.button("Request Application", key="confirm_org", type="primary", use_container_width=True, disabled=not checkbox):
        register_organisation(conn, name, description, email, password)
        
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
        st.write("")

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
                    "INSERT INTO individuals (name, age, email, password) VALUES (?, ?, ?, ?)",
                    (name, age_int, email, hashed_password)
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
    
    if st.button("Back to Home", use_container_width=True, icon=":material/arrow_back:"):
        navigate_to("landing")

def student_dashboard(conn):
    c = conn.cursor()

    student_name = c.execute("SELECT name FROM individuals WHERE id = ?", (st.session_state.user_id,)).fetchone()[0]
    current_hour = datetime.now().hour

    if 5 <= current_hour < 12:
        greeting = "Good morning"
    elif 12 <= current_hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    st.markdown(f"<h1 style='font-family: Inter;'>{greeting}, {student_name.split(" ")[0]}!</h1>", unsafe_allow_html=True)
    st.text("")
    st.text("")
    st.text("")
    st.text("")
    col1, col2, col3 = st.columns(3)
    
    total_applications = c.execute("SELECT COUNT(*) FROM applications WHERE student_id = ?", (st.session_state.user_id,)).fetchone()[0]
    accepted_applications = c.execute("SELECT COUNT(*) FROM applications WHERE student_id = ? AND status = 'accepted'", (st.session_state.user_id,)).fetchone()[0]
    rejected_applications = c.execute("SELECT COUNT(*) FROM applications WHERE student_id = ? AND status = 'rejected'", (st.session_state.user_id,)).fetchone()[0]
    completed_opportunities = c.execute("SELECT COUNT(*) FROM ratings WHERE student_id = ?", (st.session_state.user_id,)).fetchone()[0]
    with col1:
        st.markdown(f"<h6 style='font-family: Inter;color:rgb(168, 209, 169)'>Completed</h6>", unsafe_allow_html=True)
        st.success(f"##### {completed_opportunities}")
    
    with col2:
        st.markdown(f"<h6 style='font-family: Inter;color:rgb(165, 192, 221)'>Accepted</h6>", unsafe_allow_html=True)
        st.info(f"##### {accepted_applications}")

    with col3:
        st.markdown(f"<h6 style='font-family: Inter;color:rgb(223, 168, 167)'>Rejected</h6>", unsafe_allow_html=True)
        st.error(f"##### {rejected_applications}")
        
    st.header("", divider="gray")
    
    recent_opps = c.execute("""
    SELECT o.id, o.title, o.location, o.event_date, u.name
    FROM opportunities o
    JOIN organisations u ON o.org_id = u.id
    ORDER BY o.created_at DESC
    LIMIT 5
    """).fetchall()

    recent_apps = c.execute("""
    SELECT a.id, o.title, u.name as org_name, a.status, a.application_date
    FROM applications a
    JOIN opportunities o ON a.opportunity_id = o.id
    JOIN organisations u ON o.org_id = u.id
    WHERE a.student_id = ?
    ORDER BY a.application_date DESC
    LIMIT 5
    """, (st.session_state.user_id,)).fetchall()
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<h2 style='font-family: Inter;'>Recent Opportunities</h2>", unsafe_allow_html=True)
        with st.container(border=True):
            if recent_opps:
                for opp in recent_opps:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"<h4 style='font-family: Inter;'>{opp[1]} at {opp[4]}</h4>", unsafe_allow_html=True)
                            st.write(f"Location -- **{opp[2]}**")
                            st.caption(f"{opp[3]}")
                        with col2:
                            if st.button("Details", key=f"view_{opp[0]}", use_container_width=True):
                                st.session_state.temp_opp_id = opp[0]
                                navigate_to("browse_opportunities")
                        st.divider()
            else:
                st.info("No recent opportunities available.")
    
    with c2:
        st.markdown("<h2 style='font-family: Inter;'>Recent Applications</h2>", unsafe_allow_html=True)
        with st.container(border=True):
            if recent_apps:
                for app in recent_apps:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"<h3 style='font-family: Inter;'>{app[1]}</h3>", unsafe_allow_html=True)
                            st.write(f"Organisation -- **{app[2]}**")
                            
                            status = app[3]
                            if status == "accepted":
                                st.success(f"Status -- **{status.capitalize()}**")
                            elif status == "rejected":
                                st.error(f"Status -- **{status.capitalize()}**")
                            else:
                                st.info(f"Status -- **{status.capitalize()}**")
                            
                            st.caption(f"Applied on {app[4]}")
                        with col2:
                            if st.button("Details", key=f"app_{app[0]}", use_container_width=True):
                                st.session_state.temp_app_id = app[0]
                                navigate_to("my_applications")
                        st.divider()
            else:
                st.info("No pending applications.")
        
def org_dashboard(conn):
    c = conn.cursor()
    org_name = c.execute("SELECT name FROM organisations WHERE id = ?", (st.session_state.user_id,)).fetchone()[0]
    st.title(f"{org_name}")

    if "temp_opp_id" not in st.session_state:
        st.session_state.temp_opp_id = None
    
    col1, col2, col3 = st.columns(3)
    
    total_opportunities = c.execute("SELECT COUNT(*) FROM opportunities WHERE org_id = ?", (st.session_state.user_id,)).fetchone()[0]
    
    total_applications = c.execute("""
    SELECT COUNT(*) FROM applications a
    JOIN opportunities o ON a.opportunity_id = o.id
    WHERE o.org_id = ?
    """, (st.session_state.user_id,)).fetchone()[0]
    
    pending_applications = c.execute("""
    SELECT COUNT(*) FROM applications a
    JOIN opportunities o ON a.opportunity_id = o.id
    WHERE o.org_id = ? AND a.status = 'pending'
    """, (st.session_state.user_id,)).fetchone()[0]
    
    with col1:
        st.metric("Total Opportunities", total_opportunities)
    
    with col2:
        st.metric("Total Applications", total_applications)
    
    with col3:
        st.metric("Pending Applications", pending_applications)
    
    st.text("")
    st.text("")
    st.text("")
    st.subheader("Posted Opportunities", divider="gray")
    
    opps = c.execute("""
    SELECT id, title, location, event_date, created_at
    FROM opportunities
    WHERE org_id = ?
    ORDER BY created_at DESC
    LIMIT 5
    """, (st.session_state.user_id,)).fetchall()
    
    if opps:
        st.markdown("""
        <style>
        .opp-card {
            border: none;
            border-radius: 10px;
            padding: 15px;
            margin: 8px;
            height: 100%;
            background-color: #fffff;
            transition: transform 0.3s;
            box-shadow: 0px 0px 30px 2px rgba(0,0,0,0.1);
        }
        .opp-card:hover {
            transform: translateY(-5px);
            box-shadow: 0px 0px 30px 2px rgba(0,0,0,0.1);
        }
        .opp-title {
            font-weight: bold;
            font-size: 1.3em;
            margin-bottom: 12px;
            color: #2c3e50;
        }
        .opp-details {
            font-size: 0.95em;
            margin-bottom: 15px;
        }
        .opp-description {
            font-size: 0.9em;
            margin: 15px 0;
            color: #555;
            line-height: 1.4;
        }
        .opp-requirements {
            font-size: 0.9em;
            margin: 15px 0;
            color: #555;
            background-color: #f5f5f5;
            padding: 8px;
            border-left: 3px solid #3498db;
        }
        .opp-category {
            display: inline-block;
            background-color: #e0f7fa;
            color: #00838f;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin-top: 5px;
        }
        .opp-divider {
            height: 1px;
            background-color: #eee;
            margin: 15px 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        num_opps = len(opps)
        num_rows = (num_opps + 2) // 3
        
        for row_idx in range(num_rows):
            cols = st.columns(3)
            
            for col_idx in range(3):
                opp_idx = row_idx * 3 + col_idx
                
                if opp_idx < num_opps:
                    opp = opps[opp_idx]
                    opp_id, title, location, event_date, created_at = opp
                    
                    with cols[col_idx]:
                        with st.container():
                            st.markdown(f"""
                            <div class="opp-card">
                                <div class="opp-title">{title}</div>
                                <div class="opp-details">
                                    <strong>Location:</strong> {location}<br>
                                    <strong>Date:</strong> {event_date}
                                </div>
                                <div class="opp-divider"></div>
                                <div class="opp-description">
                                    <strong>Posted on:</strong> {created_at}
                                </div>
                            """, unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            with st.container():
                                if st.button("View Applications", key=f"view_apps_{opp_id}", use_container_width=True):
                                    st.session_state.temp_opp_id = opp_id
                                    navigate_to("manage_applications")
    else:
        st.info("You haven't posted any opportunities yet.")
    
    st.subheader("Recent Applications")
    recent_apps = c.execute("""
                    SELECT a.id, u.name as student_name, o.title, a.status, a.application_date
                    FROM applications a
                    JOIN individuals u ON a.student_id = u.id
                    JOIN opportunities o ON a.opportunity_id = o.id
                    WHERE o.org_id = ?
                    ORDER BY a.application_date DESC
                    LIMIT 5
                    """, (st.session_state.user_id,)).fetchall()
        
    if recent_apps:
        for app in recent_apps:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{app[2]}**")
                    st.write(f"Student: {app[1]}")
                    
                    status = app[3]
                    if status == "accepted":
                        st.success(f"Status: {status.capitalize()}")
                    elif status == "rejected":
                        st.error(f"Status: {status.capitalize()}")
                    else:
                        st.info(f"Status: {status.capitalize()}")
                    
                    st.write(f"Applied on: {app[4]}")
                with col2:
                    if st.button("Review", key=f"review_{app[0]}"):
                        st.session_state.temp_app_id = app[0]
                        navigate_to("manage_applications")
                st.markdown("---")
    else:
        st.info("You haven't received any applications yet.")
    
@st.dialog(" ", width="large")
def opp_details_dialog(conn):
    c = conn.cursor()
    opp_id = st.session_state.temp_opp_id

    opp_details = c.execute("""
    SELECT o.title, o.description, o.location, o.event_date, o.duration, 
           o.requirements, o.category, u.name as org_name
    FROM opportunities o
    JOIN organisations u ON o.org_id = u.id
    WHERE o.id = ?
    """, (opp_id,)).fetchone()
    
    if opp_details:
        title, description, location, event_date, duration, requirements, category, org_name = opp_details
        st.title("**Opportunity Details**")
        st.header(" ", divider="gray")
        st.title(f"**{title}**")
        st.write(f"**Organization:** {org_name}")
        st.write(f"**Location:** {location}")
        st.write(f"**Date:** {event_date}")
        st.write(f"**Duration:** {duration}")
        
        if category:
            st.write(f"**Category:** {category}")
        
        st.header("Description")
        with st.container():
            st.write(description)
        
        if requirements:
            st.subheader("Requirements")
            st.write(requirements)

        c.execute("""
        SELECT status FROM applications 
        WHERE student_id = ? AND opportunity_id = ?
        """, (st.session_state.user_id, opp_id))
        
        existing_application = c.fetchone()
        apply_disabled = False
        apply_message = ""

        if existing_application:
            status = existing_application[0]
            if status == "pending":
                apply_disabled = True
                apply_message = "You have already applied for this opportunity. Application pending."
            elif status == "accepted":
                apply_disabled = True
                apply_message = "You have been accepted for this opportunity!"
            elif status == "rejected":
                apply_message = "Your previous application was rejected. You can reapply."

        c1, c2 = st.columns(2)

        if c1.button("Close Details", use_container_width=True):
            st.session_state.temp_opp_details = False
            st.rerun()

        if apply_message:
            st.info(apply_message)

        if c2.button("Apply", key=f"apply_{opp_id}", use_container_width=True, disabled=apply_disabled, type="primary"):
            with st.spinner("Sending application request..."):
                c.execute("""
                INSERT INTO applications (student_id, opportunity_id, status)
                VALUES (?, ?, 'pending')
                """, (st.session_state.user_id, opp_id))

                conn.commit()
                time.sleep(3)
            st.success("Application submitted successfully!")
            time.sleep(3)
            st.rerun()

def browse_opportunities(conn):
    CATEGORY_COLORS = {
    "Environment": "#09AD11",      # green
    "Education": "#3AA6FF",        # blue
    "Health": "#B50000",           # red
    "Animal Welfare": "#FFAA00",      # yellow
    "Community Service": "#E456FD",        # purple
    "Sports": "#00FFE5",           # teal
    "Arts & Culture": "#440FCA",           # teal
    "Disaster Relief": "#5C5C5C",           # teal
    "Other": "#000000"             # brown/neutral
    }
    st.markdown("<h1 style='font-family: Inter;'>Browse Nearby Opportunities</h1>", unsafe_allow_html=True)
    c = conn.cursor()
    with st.expander("Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input("Search by title or description")
        
        with col2:
            c.execute("SELECT DISTINCT category FROM opportunities WHERE category IS NOT NULL")
            categories = [cat[0] for cat in c.fetchall()]
            
            c.execute("SELECT DISTINCT u.name FROM opportunities o JOIN organisations u ON o.org_id = u.id")
            organisations = [org[0] for org in c.fetchall()]
            
            category_filter = st.selectbox("Filter by Category", ["All"] + categories)
            organisation_filter = st.selectbox("Filter by Organisation", ["All"] + organisations)
    
    query = """
    SELECT o.id, o.title, o.description, o.location, o.event_date, o.duration, 
           o.requirements, o.category, u.name as org_name
    FROM opportunities o
    JOIN organisations u ON o.org_id = u.id
    WHERE 1=1
    """
    params = []
    
    if search_term:
        query += " AND (o.title LIKE ? OR o.description LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    
    if category_filter != "All":
        query += " AND o.category = ?"
        params.append(category_filter)
    
    if organisation_filter != "All":
        query += " AND u.name = ?"
        params.append(organisation_filter)
    
    query += " ORDER BY o.created_at DESC"
    
    c.execute(query, params)
    opportunities = c.fetchall()
    
    if opportunities:
        num_opps = len(opportunities)
        num_rows = (num_opps + 2) // 3
        
        st.markdown("""
        <style>
        .opp-row {
            display: flex;
            justify-content: space-between;
            font-size: 0.95em;
            margin: 2px 0;
        }

        .label {
            font-weight: bold;
            color: #333;
            margin-right: 10px;
        }

        .value {
            text-align: right;
            color: #444;
        }
        .opp-card {
            border: none;
            border-radius: 15px;
            padding: 15px;
            margin: 8px;
            height: 100%;
            background-color: #fffff;
            transition: transform 0.3s;
            box-shadow: 0px 0px 30px 2px rgba(0,0,0,0.1);
        }
        .opp-card:hover {
            transform: translateY(-5px);
            box-shadow: 0px 0px 30px 2px rgba(0,0,0,0.1);
        }
        .opp-title {
            font-weight: bold;
            font-size: 1.6em;
            margin-bottom: 12px;
            color: #2c3e50;
        }
        .opp-details {
            font-size: 0.95em;
            margin-bottom: 15px;
        }
        .opp-description {
            font-size: 0.9em;
            margin: 20px 0;
            color: #555;
            line-height: 1.4;
            
        }
        .opp-requirements {
            font-size: 0.9em;
            margin: 15px 0;
            color: #555;
            background-color: #f5f5f5;
            padding: 8px;
            border-left: 3px solid #3498db;
        }
        .opp-category {
            display: inline-block;
            background-color: #e0f7fa;
            color: #00838f;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin-top: 5px;
        }
        .opp-divider {
            height: 1px;
            background-color: #eee;
            margin: 15px 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        for row_idx in range(num_rows):
            cols = st.columns(3)
            
            for col_idx in range(3):
                opp_idx = row_idx * 3 + col_idx
                
                if opp_idx < num_opps:
                    opp = opportunities[opp_idx]
                    opp_id, title, description, location, event_date, duration, requirements, category, org_name = opp
                    
                    with cols[col_idx]:
                        with st.container():
                            color = CATEGORY_COLORS.get(category, "#90A4AE")  # default gray-blue
                            category_html = f'''
                            <div style="
                                display: inline-block;
                                background-color: {color};
                                color: white;
                                padding: 5px 10px;
                                border-radius: 20px;
                                font-size: 0.8em;
                                margin-top: 5px;
                                font-weight: 500;
                            ">
                                {category}
                            </div>
                            ''' if category else ''

                            
                            c.execute("""
                            SELECT id, status FROM applications 
                            WHERE student_id = ? AND opportunity_id = ?
                            """, (st.session_state.user_id, opp_id))
                            
                            existing_application = c.fetchone()
                            
                            if existing_application:
                                app_id, status = existing_application
                                if status == "accepted":
                                    title = f"{title} - <span style='color:green;'>Accepted</span>"
                                elif status == "rejected":
                                    title = f"{title} - <span style='color:red;'>Rejected</span>"
                                else:
                                    title = f"{title} - <span style='color:darkblue;'>Pending</span>"
                            else:
                                title = f"{title}"

                            st.markdown(f"""
                            <div class="opp-card">
                                <div class="opp-title">{title}</div>
                                {category_html}<-
                                <div class="opp-details">
                                    <div class="opp-row"><span class="label"> </span> <span class="value">.</span></div>
                                    <div class="opp-row"><span class="label">Organisation:</span> <span class="value">{org_name}</span></div>
                                    <div class="opp-row"><span class="label">Location:</span> <span class="value">{location}</span></div>
                                    <div class="opp-row"><span class="label">Date:</span> <span class="value">{event_date}</span></div>
                                    <div class="opp-row"><span class="label">Duration:</span> <span class="value">{duration}</span></div>
                                </div>
                                <div>
                                    <div class="opp-divider"></div>
                                    <div class="opp-description">
                                        <strong>Description</strong><br>
                                        {description[:50]}{'...' if len(description) > 150 else ''}
                                    </div>
                                    <div class="opp-requirements">
                                        <strong>Requirements:</strong><br>
                                        {requirements[:50]}{'...' if len(requirements) > 100 else ''}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            if st.button("View Details", key=f"view_{opp_id}", use_container_width=True):
                                st.session_state.temp_opp_id = opp_id
                                st.session_state.temp_opp_details = True

    else:
        st.info("No opportunities found matching your criteria.")
    
    if 'temp_opp_details' in st.session_state and st.session_state.temp_opp_details and 'temp_opp_id' in st.session_state:
        opp_details_dialog(conn)

def set_active_chat_and_navigate(chat_id):
    st.session_state.active_chat = chat_id
    navigate_to("chat")

@st.dialog("f")
def confirm_post_opportunity(conn):
    c = conn.cursor()
    st.markdown("<h1 style='font-family: Inter;'>Confirm Opportunity Details</h1>", unsafe_allow_html=True)
    st.write("Please review the details below before posting your opportunity.")
    
    title = st.session_state.opportunity_title
    location = st.session_state.opportunity_location
    event_date = st.session_state.opportunity_event_date
    duration = st.session_state.opportunity_duration
    description = st.session_state.opportunity_description
    requirements = st.session_state.opportunity_requirements
    category = st.session_state.opportunity_category
    
    st.divider()
    st.write(f"**Title:** {title}")
    st.write(f"**Location:** {location}")
    st.write(f"**Event Date:** {event_date}")
    st.write(f"**Duration:** {duration}")
    st.write(f"**Description:** {description}")
    
    if requirements:
        st.write(f"**Requirements:** {requirements}")
    
    if category:
        st.write(f"**Category:** {category}")
    
    checkbox = st.checkbox("I confirm the details above are correct and aware that **I cannot change** them later.")
    
    if st.button("Post Opportunity", key="confirm_post", type="primary", use_container_width=True, disabled=not checkbox):
        post_opportunity(conn)

def post_opportunity(conn):
    c = conn.cursor()
    st.markdown("<h1 style='font-family: Inter;'>Post New Opportunity</h1>", unsafe_allow_html=True)
    st.write("Fill in the details below to post a new opportunity.")

    for i in range(3):
        st.text("")
    with st.container(border=True):
        title = st.text_input("Opportunity Title *")
        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input("Location / Address *")
        with col2:
            category = st.selectbox("Category *", [
                "Education", "Environment", "Health", "Arts & Culture", 
                "Community Service", "Animal Welfare", "Disaster Relief", "Other"
            ])
        
        col1, col2 = st.columns(2)
        with col1:
            event_date = st.date_input("Event Date *")
        with col2:
            duration = st.text_input("Duration (e.g. '2 hours', '3 days') *")
        
        description = st.text_area("Opportunity Description *", height=100)
        requirements = st.text_area("Requirements (Skills, experience, ability etc.) - **Optional**", height=100)

        st.text("")
        st.text("")
        st.text("")

        if st.button("Post Opportunity", type="primary", use_container_width=True):
            if not title or not location or not event_date or not duration or not description:
                st.error("Please fill in all required fields marked with *")
                return
            
            if len(title) < 5:
                st.error("Title must be at least 5 characters long")
                return
            
            if len(location) < 5:
                st.error("Location must be at least 5 characters long")
                return
            
            if len(description) < 20:
                st.error("Description must be at least 20 characters long")
                return
            
            if category == "Other" and not requirements:
                st.error("Please provide requirements for 'Other' category")
                return
            
            st.session_state.opportunity_title = title
            st.session_state.opportunity_location = location
            st.session_state.opportunity_event_date = event_date
            st.session_state.opportunity_duration = duration
            st.session_state.opportunity_description = description
            st.session_state.opportunity_requirements = requirements
            st.session_state.opportunity_category = category
            
            confirm_post_opportunity(conn)

def my_applications(conn):
    """Page for students to view and manage their applications"""
    st.title("My Applications")
    
    c = conn.cursor()
    
    c.execute("""
    SELECT a.id, o.title, u.name as org_name, o.location, o.event_date, 
           a.status, a.application_date, o.id as opp_id, u.id as org_id
    FROM applications a
    JOIN opportunities o ON a.opportunity_id = o.id
    JOIN organisations u ON o.org_id = u.id
    WHERE a.student_id = ?
    ORDER BY a.application_date DESC
    """, (st.session_state.user_id,))
    
    applications = c.fetchall()
    
    status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Accepted", "Rejected"])
    
    filtered_applications = applications
    if status_filter != "All":
        filtered_applications = [app for app in applications if app[5].lower() == status_filter.lower()]
    if st.session_state.show_reflection_dialog:
        with st.container():
            st.markdown("""
            <style>
            .reflection-dialog {
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 0px 10px rgba(0,0,0,0.2);
                margin: 10px 0;
                border: 1px solid #ddd;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown(f'<div class="reflection-dialog">', unsafe_allow_html=True)
            st.subheader(f"Reflection for: {st.session_state.reflection_title}")
            
            with st.form("reflection_dialog_form"):
                reflection = st.text_area("Your Reflection", height=200, 
                                         placeholder="Share your experience, what you learned, and how this opportunity impacted you...")
                
                st.write("Rate your experience (1-5 stars):")
                rating = st.slider("Rating", 1, 5, 3)
                
                col1, col2 = st.columns(2)
                with col1:
                    submit_button = st.form_submit_button("Submit Reflection")
                with col2:
                    cancel_button = st.form_submit_button("Cancel")
            
            if submit_button:
                if not reflection:
                    st.error("Please write a reflection before submitting.")
                else:
                    c.execute("""
                    SELECT id FROM ratings 
                    WHERE student_id = ? AND opportunity_id = ?
                    """, (st.session_state.user_id, st.session_state.reflection_opp_id))
                    
                    existing_reflection = c.fetchone()
                    
                    if existing_reflection:
                        st.warning("You've already submitted a reflection for this opportunity.")
                    else:
                        try:
                            c.execute("""
                            INSERT INTO ratings (student_id, org_id, opportunity_id, rating, reflection)
                            VALUES (?, ?, ?, ?, ?)
                            """, (st.session_state.user_id, st.session_state.reflection_org_id, 
                                 st.session_state.reflection_opp_id, rating, reflection))
                            
                            conn.commit()
                            st.success("Reflection submitted successfully!")
                            
                            st.session_state.show_reflection_dialog = False
                            st.session_state.reflection_opp_id = None
                            st.session_state.reflection_org_id = None
                            st.session_state.reflection_title = None
                            
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.warning("You've already submitted a reflection for this opportunity.")
            
            if cancel_button:
                st.session_state.show_reflection_dialog = False
                st.session_state.reflection_opp_id = None
                st.session_state.reflection_org_id = None
                st.session_state.reflection_title = None
                st.rerun()
    
    if filtered_applications:
        for app in filtered_applications:
            app_id, title, org_name, location, event_date, status, app_date, opp_id, org_id = app
            
            with st.container():
                st.subheader(title)
                st.write(f"**Organization:** {org_name}")
                st.write(f"**Location:** {location}")
                st.write(f"**Event Date:** {event_date}")
                st.write(f"**Applied on:** {app_date}")
                
                if status.lower() == "accepted":
                    st.success(f"Status: {status.capitalize()}")
                    
                    c.execute("""
                    SELECT id FROM chats
                    WHERE student_id = ? AND opportunity_id = ?
                    """, (st.session_state.user_id, opp_id))
                    
                    chat = c.fetchone()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if chat and st.button("Open Chat", key=f"chat_{app_id}", use_container_width=True):
                            st.session_state.active_chat = chat[0]
                            navigate_to("chat")
                    
                    with col2:
                        c.execute("""
                        SELECT id FROM ratings
                        WHERE student_id = ? AND opportunity_id = ?
                        """, (st.session_state.user_id, opp_id))
                        
                        rating = c.fetchone()
                        
                        if not rating:
                            if st.button("Submit Reflection", key=f"reflect_{app_id}", use_container_width=True):
                                st.session_state.show_reflection_dialog = True
                                st.session_state.reflection_opp_id = opp_id
                                st.session_state.reflection_org_id = org_id
                                st.session_state.reflection_title = title
                                st.rerun()
                        else:
                            st.button("View Reflections", key=f"view_reflect_{app_id}", on_click=lambda: navigate_to("reflections"))
                    
                elif status.lower() == "rejected":
                    st.error(f"Status: {status.capitalize()}")
                else:
                    st.info(f"Status: {status.capitalize()}")
                    
                    if st.button("Withdraw Application", key=f"withdraw_{app_id}"):
                        c.execute("DELETE FROM applications WHERE id = ?", (app_id,))
                        conn.commit()
                        st.success("Application withdrawn successfully.")
                        st.rerun()
            
            st.markdown("---")
    else:
        st.info("No applications found with the selected status.")
        
        if status_filter != "All":
            if st.button("View All Applications"):
                st.session_state.status_filter = "All"
                st.rerun()
        else:
            st.write("You haven't applied to any opportunities yet.")
            if st.button("Browse Opportunities"):
                navigate_to("browse_opportunities")
    
def manage_applications(conn):
    st.markdown("<h1 style='font-family: Inter;'>Manage Applications</h1>", unsafe_allow_html=True)
    c = conn.cursor()
    
    c.execute("""
    SELECT id, title FROM opportunities
    WHERE org_id = ? ORDER BY created_at DESC
    """, (st.session_state.user_id,))
    
    opportunities = c.fetchall()
    
    if not opportunities:
        st.info("You haven't posted any opportunities yet.")
        if st.button("Post Your First Opportunity"):
            navigate_to("post_opportunity")
        return
    
    opp_titles = [f"{opp[1]} (ID: {opp[0]})" for opp in opportunities]
    selected_opp_title = st.selectbox("Select Opportunity", opp_titles)
    selected_opp_id = int(selected_opp_title.split("ID: ")[1].strip(")"))
    
    status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Accepted", "Rejected"])
    
    query = """
    SELECT a.id, u.name as student_name, u.email as student_email, 
           a.status, a.application_date, u.id as student_id
    FROM applications a
    JOIN individuals u ON a.student_id = u.id
    WHERE a.opportunity_id = ?
    """
    
    params = [selected_opp_id]
    
    if status_filter != "All":
        query += " AND a.status = ?"
        params.append(status_filter.lower())
    
    query += " ORDER BY a.application_date DESC"
    
    c.execute(query, params)
    applications = c.fetchall()
    
    c.execute("SELECT title, location, event_date FROM opportunities WHERE id = ?", (selected_opp_id,))
    opp_details = c.fetchone()
    st.divider()
    
    st.subheader(f"Applications for: {opp_details[0]}")
    st.write(f"Location: {opp_details[1]} | Date: {opp_details[2]}")
    
    if applications:
        for app in applications:
            app_id, student_name, student_email, status, app_date, student_id = app
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Student:** {student_name}")
                    st.write(f"**Email:** {student_email}")
                    st.write(f"**Applied on:** {app_date}")
                    
                    if status == "accepted":
                        st.success(f"Status: {status.capitalize()}")
                    elif status == "rejected":
                        st.error(f"Status: {status.capitalize()}")
                    else:
                        st.info(f"Status: {status.capitalize()}")
                
                with col2:
                    if status == "pending":
                        if st.button("Accept", key=f"accept_{app_id}", use_container_width=True, type="primary"):
                            c.execute("UPDATE applications SET status = 'accepted' WHERE id = ?", (app_id,))
                            
                            chat_channel = f"chat_{st.session_state.user_id}_{student_id}_{selected_opp_id}"
                            
                            c.execute("""
                            INSERT INTO chats (student_id, org_id, opportunity_id, supabase_channel)
                            VALUES (?, ?, ?, ?)
                            """, (student_id, st.session_state.user_id, selected_opp_id, chat_channel))
                            
                            conn.commit()
                            st.success("Application accepted. A chat channel has been created.")
                            st.rerun()
                        
                        if st.button("Reject", key=f"reject_{app_id}", use_container_width=True):
                            c.execute("UPDATE applications SET status = 'rejected' WHERE id = ?", (app_id,))
                            conn.commit()
                            st.success("Application rejected.")
                            st.rerun()
                    
                    elif status == "accepted":
                        c.execute("""
                        SELECT id FROM chats
                        WHERE student_id = ? AND org_id = ? AND opportunity_id = ?
                        """, (student_id, st.session_state.user_id, selected_opp_id))
                        
                        chat = c.fetchone()
                        
                        if chat and st.button("Open Chat", key=f"chat_{app_id}"):
                            st.session_state.active_chat = chat[0]
                            navigate_to("chat")
                
                st.markdown("---")
    else:
        st.info("No applications found for this opportunity with the selected status.")
    
def chat_page(conn):
    st_autorefresh(interval=5000)
    st.markdown("<h1 style='font-family: Inter;'>Chats</h1>", unsafe_allow_html=True)
    st.divider()
    
    c = conn.cursor()
    
    if st.session_state.user_type == "individual":
        c.execute("""
        SELECT c.id, u.name as org_name, o.title, c.created_at, o.id as opp_id, u.id as org_id
        FROM chats c
        JOIN organisations u ON c.org_id = u.id
        JOIN opportunities o ON c.opportunity_id = o.id
        WHERE c.student_id = ?
        ORDER BY c.created_at DESC
        """, (st.session_state.user_id,))
    else:
        c.execute("""
        SELECT c.id, u.name as student_name, o.title, c.created_at, o.id as opp_id, u.id as student_id
        FROM chats c
        JOIN individuals u ON c.student_id = u.id
        JOIN opportunities o ON c.opportunity_id = o.id
        WHERE c.org_id = ?
        ORDER BY c.created_at DESC
        """, (st.session_state.user_id,))
    
    chats = c.fetchall()
    
    if not chats:
        st.info("No active chats available.")
        return
    
    c1, c2 = st.columns([1, 3], gap="large")
    with c1:
        st.subheader("Your Chats")
        for chat in chats:
            chat_id, other_name, opp_title, chat_date, opp_id, other_id = chat
            if st.button(f"{other_name} - {opp_title}", key=f"chat_btn_{chat_id}", use_container_width=True):
                st.session_state.active_chat = chat_id
                st.rerun()
    
    with c2:
        if st.session_state.active_chat:
            c.execute("""
            SELECT sender_id, content, timestamp FROM messages
            WHERE chat_id = ?
            ORDER BY timestamp ASC
            """, (st.session_state.active_chat,))
            
            messages = c.fetchall()
            st.markdown(f"<h3 style='font-family: Inter;'>Chat with {other_name} - {opp_title}</h3>", unsafe_allow_html=True)
            with st.container(height=400, border=False):
                for msg in messages:
                    sender_id, content, timestamp = msg
                    sender_name = "You" if sender_id == st.session_state.user_id else other_name
                    with st.chat_message(name="ai" if sender_id == st.session_state.user_id else "human"):
                        st.write(f"**{sender_name} ({datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")}):** {content}")
                
            new_message = st.chat_input("Type your message here...")
            if new_message:
                c.execute("""
                INSERT INTO messages (chat_id, sender_id, content)
                VALUES (?, ?, ?)
                """, (st.session_state.active_chat, st.session_state.user_id, new_message))
                conn.commit()
                st.rerun()

def reflections_page(conn):
    st.markdown("<h1 style='font-family: Inter;'>My Reflections</h1>", unsafe_allow_html=True)
    
    c = conn.cursor()
    
    if st.session_state.show_reflection_dialog:
        st.session_state.show_reflection_dialog = False
        st.session_state.reflection_opp_id = None
        st.session_state.reflection_org_id = None
        st.session_state.reflection_title = None
    
    if 'temp_opp_id' in st.session_state:
        opp_id = st.session_state.temp_opp_id
        
        c.execute("""
        SELECT o.title, u.id as org_id
        FROM opportunities o
        JOIN organisations u ON o.org_id = u.id
        WHERE o.id = ?
        """, (opp_id,))
        
        opp = c.fetchone()
        
        if opp:
            st.session_state.reflection_opp_id = opp_id
            st.session_state.reflection_org_id = opp[1]
            st.session_state.reflection_title = opp[0]
            st.session_state.show_reflection_dialog = True
            
            del st.session_state.temp_opp_id
            
            navigate_to("my_applications")
            st.rerun()
        else:
            if 'temp_opp_id' in st.session_state:
                del st.session_state.temp_opp_id
    
    st.subheader("Your Past Reflections")
    
    c.execute("""
    SELECT r.id, o.title, u.name as org_name, r.rating, r.reflection, r.created_at, o.id as opp_id, 
           o.location, o.event_date
    FROM ratings r
    JOIN opportunities o ON r.opportunity_id = o.id
    JOIN organisations u ON r.org_id = u.id
    WHERE r.student_id = ?
    ORDER BY r.created_at DESC
    """, (st.session_state.user_id,))
    
    reflections = c.fetchall()
    
    if reflections:
        st.markdown("""
        <style>
        .reflection-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin: 8px;
            height: 100%;
            background-color: white;
            transition: transform 0.3s;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .reflection-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        }
        .reflection-title {
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 8px;
            color: #2c3e50;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .reflection-org {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-bottom: 5px;
        }
        .reflection-date {
            font-size: 0.85em;
            color: #95a5a6;
            margin-bottom: 10px;
        }
        .reflection-preview {
            font-size: 0.9em;
            color: #34495e;
            margin: 10px 0;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
        }
        .reflection-rating {
            font-size: 1.2em;
            color: #f39c12;
            margin-top: 5px;
        }
        .reflection-divider {
            height: 1px;
            background-color: #ecf0f1;
            margin: 10px 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        num_reflections = len(reflections)
        num_rows = (num_reflections + 2) // 3 
        
        for row_idx in range(num_rows):
            cols = st.columns(3)
            
            for col_idx in range(3):
                ref_idx = row_idx * 3 + col_idx
                
                if ref_idx < num_reflections:
                    ref = reflections[ref_idx]
                    ref_id, title, org_name, rating, reflection_text, created_at, opp_id, location, event_date = ref
                    
                    with cols[col_idx]:
                        with st.container():
                            try:
                                date_obj = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                                formatted_date = date_obj.strftime('%b %d, %Y')
                            except:
                                formatted_date = created_at
                                
                            stars = "★" * rating + "☆" * (5 - rating)
                            
                            preview = reflection_text[:100] + "..." if len(reflection_text) > 100 else reflection_text
                            
                            st.markdown(f"""
                            <div class="reflection-card">
                                <div class="reflection-title">{title}</div>
                                <div class="reflection-org">{org_name}</div>
                                <div class="reflection-date">Reflected on {formatted_date}</div>
                                <div class="reflection-rating">{stars}</div>
                                <div class="reflection-divider"></div>
                                <div class="reflection-preview">{reflection_text}</div>
                            </div>
                            """, unsafe_allow_html=True)

    else:
        st.info("You haven't submitted any reflections yet.")
    
        c.execute("""
        SELECT r.id, o.title, u.name as org_name, r.rating, r.reflection, r.created_at, o.location, o.event_date
        FROM ratings r
        JOIN opportunities o ON r.opportunity_id = o.id
        JOIN organisations u ON r.org_id = u.id
        WHERE r.id = ? AND r.student_id = ?
        """, (ref_id, st.session_state.user_id))
        
        ref_details = c.fetchone()
        
        if ref_details:
            ref_id, title, org_name, rating, reflection, created_at, location, event_date = ref_details
            
            with st.container():
                st.markdown("""
                <style>
                .reflection-detail-dialog {
                    background-color: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0px 0px 15px rgba(0,0,0,0.2);
                    margin: 10px 0;
                    border: 1px solid #ddd;
                }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown(f'<div class="reflection-detail-dialog">', unsafe_allow_html=True)
                st.subheader(f"Reflection: {title}")
                st.write(f"**Organization:** {org_name}")
                st.write(f"**Location:** {location}")
                st.write(f"**Event Date:** {event_date}")
                st.write(f"**Submitted on:** {created_at}")
                
                st.write("**Rating:**")
                st.write("⭐" * rating)
                
                st.write("**Your Reflection:**")
                st.write(reflection)
                
                if st.button("Close"):
                    st.session_state.show_ref_details = False
                    st.session_state.temp_ref_id = None
                    st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    c.execute("""
    SELECT o.id, o.title, u.name as org_name, o.event_date, u.id as org_id
    FROM applications a
    JOIN opportunities o ON a.opportunity_id = o.id
    JOIN organisations u ON o.org_id = u.id
    WHERE a.student_id = ? AND a.status = 'accepted'
    AND o.id NOT IN (
        SELECT opportunity_id FROM ratings WHERE student_id = ?
    )
    ORDER BY o.event_date DESC
    """, (st.session_state.user_id, st.session_state.user_id))
    
    pending_reflections = c.fetchall()
    
    if pending_reflections:
        st.subheader("Opportunities Ready for Reflection:")
        
        num_pending = len(pending_reflections)
        num_rows_pending = (num_pending + 2) // 3
        
        st.markdown("""
        <style>
        .pending-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin: 8px;
            height: 100%;
            background-color: #f0f7ff;
            transition: transform 0.3s;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .pending-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        }
        .pending-title {
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 8px;
            color: #2c3e50;
        }
        .pending-org {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-bottom: 5px;
        }
        .pending-date {
            font-size: 0.85em;
            color: #3498db;
            margin-bottom: 5px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        for row_idx in range(num_rows_pending):
            cols = st.columns(3)
            
            for col_idx in range(3):
                opp_idx = row_idx * 3 + col_idx
                
                if opp_idx < num_pending:
                    opp = pending_reflections[opp_idx]
                    opp_id, title, org_name, event_date, org_id = opp
                    
                    with cols[col_idx]:
                        with st.container():
                            try:
                                date_obj = datetime.strptime(event_date, '%Y-%m-%d')
                                formatted_date = date_obj.strftime('%b %d, %Y')
                            except:
                                formatted_date = event_date
                            
                            st.markdown(f"""
                            <div class="pending-card">
                                <div class="pending-title">{title}</div>
                                <div class="pending-org">{org_name}</div>
                                <div class="pending-date">Event Date: {formatted_date}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("Write Reflection", key=f"reflect_{opp_id}"):
                                st.session_state.show_reflection_dialog = True
                                st.session_state.reflection_opp_id = opp_id
                                st.session_state.reflection_org_id = org_id
                                st.session_state.reflection_title = title
                                navigate_to("my_applications")
                                st.rerun()
    else:
        st.write("You don't have any completed opportunities that need reflections.")

def org_profile(conn):
    st.markdown("<h1 style='font-family: Inter;'>Organisation Profile</h1>", unsafe_allow_html=True)
    
    c = conn.cursor()
    
    c.execute("SELECT name, email, registration_date FROM organisations WHERE id = ?", (st.session_state.user_id,))
    org_info = c.fetchone()
    
    if not org_info:
        st.error("Organization information not found.")
        return
    
    name, email, registration_date = org_info
    
    st.header(name)
    st.write(f"Email: {email}")
    st.write(f"Member since: {registration_date}")

    st.subheader("Statistics")
    
    col1, col2, col3 = st.columns(3)
    total_opportunities = c.execute("SELECT COUNT(*) FROM opportunities WHERE org_id = ?", (st.session_state.user_id,)).fetchone()[0]
    total_applications = c.execute("""
    SELECT COUNT(*) FROM applications a
    JOIN opportunities o ON a.opportunity_id = o.id
    WHERE o.org_id = ?
    """, (st.session_state.user_id,)).fetchone()[0]
    total_ratings = c.execute("""
    SELECT COUNT(*) FROM ratings r
    JOIN opportunities o ON r.opportunity_id = o.id
    WHERE o.org_id = ?
    """, (st.session_state.user_id,)).fetchone()[0]
    avg_rating = c.execute("""
    SELECT AVG(rating) FROM ratings r
    JOIN opportunities o ON r.opportunity_id = o.id
    WHERE o.org_id = ?
    """, (st.session_state.user_id,)).fetchone()[0]

    with col1:
        st.metric("Total Opportunities", total_opportunities)
    with col2:
        st.metric("Total Applications", total_applications)
    with col3:
        st.metric("Total Ratings", total_ratings)
    
    if avg_rating:
        st.metric("Average Rating", round(avg_rating, 2))
    else:
        st.metric("Average Rating", "N/A")

    st.subheader("Recent Ratings")
    c.execute("""
    SELECT r.rating, r.reflection, r.created_at, u.name as student_name, o.title as opp_title
    FROM ratings r
    JOIN individuals u ON r.student_id = u.id
    JOIN opportunities o ON r.opportunity_id = o.id
    WHERE o.org_id = ?
    ORDER BY r.created_at DESC
    LIMIT 5
    """, (st.session_state.user_id,))
    
    recent_ratings = c.fetchall()
    
    if recent_ratings:
        for rating in recent_ratings:
            st.write(f"**{rating[4]}** by {rating[3]}")
            st.write(f"Rating: {'★' * rating[0]}{'☆' * (5 - rating[0])}")
            st.write(f"Reflection: {rating[1]}")
            st.write(f"Submitted on: {rating[2]}")
            st.markdown("---")
    else:
        st.info("No ratings available yet.")

if __name__ == "__main__":
    conn = connect_database()
    st.markdown("""<style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

                * {
                    font-family: 'Inter', sans-serif;
                }
    
                html, body, [class*="st-"] {
                    font-size: 13px !important;
                }
                </style""", unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    .stButton>button:first-child {
        padding: 10px 10px !important;
        transition: all 0.1s ease-in-out;
        border-radius: 10px
    </style>
""", unsafe_allow_html=True)
    
    init_db(conn)
    # conn.cursor().execute("ALTER TABLE users ADD COLUMN last_living_tax TEXT;")
    main(conn)
