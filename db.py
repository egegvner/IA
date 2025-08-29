import sqlite3
import streamlit as st

@st.cache_resource
def get_db_connection():
    return sqlite3.connect("voluntree.db", check_same_thread = False, uri = True)

def init_db(conn):
    c = conn.cursor()
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY NOT NULL UNIQUE,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        latitude REAL,
        longitude REAL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS organisations (
        id INTEGER PRIMARY KEY,
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
        max_applicants INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (org_id) REFERENCES organisations (id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        opportunity_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
        UNIQUE(user_id, opportunity_id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        org_id INTEGER NOT NULL,
        opportunity_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        reflection TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (org_id) REFERENCES organisations(id),
        FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
        UNIQUE(user_id, opportunity_id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        org_id INTEGER NOT NULL,
        opportunity_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (org_id) REFERENCES organisations(id),
        FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
        UNIQUE(user_id, org_id, opportunity_id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        sender_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chat_id) REFERENCES chats(id),
        FOREIGN KEY (sender_id) REFERENCES users(id)
    )
    ''')

    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_reads (
        chat_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        last_read TIMESTAMP NOT NULL,
        PRIMARY KEY (chat_id, user_id),
        FOREIGN KEY (chat_id) REFERENCES chats(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

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
    CREATE TABLE IF NOT EXISTS user_ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        org_id INTEGER NOT NULL,
        rating REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (org_id) REFERENCES organisations(id)
    )
    ''')
    
    conn.commit()
