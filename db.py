import sqlite3
import streamlit as st

@st.cache_resource
def connect_database():
    conn = sqlite3.connect("community_platform_db.db", check_same_thread=False)
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
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        latitude REAL,
        longitude REAL,
        rating REAL DEFAULT 0.0
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
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        event_date TEXT NOT NULL,
        duration TEXT NOT NULL,
        description TEXT NOT NULL,
        requirements TEXT,
        category TEXT,
        min_required_rating REAL NOT NULL,
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

    c.execute('''
        CREATE TABLE IF NOT EXISTS opportunity_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opportunity_id INTEGER NOT NULL,
        image_blob BLOB NOT NULL,
        filename TEXT,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
    );
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS student_ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        org_id INTEGER NOT NULL,
        rating REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES individuals (id),
        FOREIGN KEY (org_id) REFERENCES organisations (id)
    )
    ''')
    
    conn.commit()
