import argon2
from argon2.low_level import Type
import re
import streamlit as st
from math import radians, sin, cos, sqrt, atan2
import random
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import sqlite3
import os
import base64
import pandas as pd
from datetime import datetime
import time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def navigate_to(page: str):
    st.session_state.current_page = page
    for key in list(st.session_state.keys()):
        if key.startswith('temp_'):
            del st.session_state[key]
    st.rerun()

def hash_password(password: str) -> str:
    ph = argon2.PasswordHasher(
        time_cost=3,
        memory_cost=102400,
        parallelism=4,
        hash_len=32,
        salt_len=16,
        type=Type.ID
    )
    return ph.hash(password)

def check_password(provided_password: str, stored_password: str) -> bool:
    ph = argon2.PasswordHasher(
        time_cost=3,
        memory_cost=102400,
        parallelism=4,
        hash_len=32,
        salt_len=16,
        type=Type.ID
    )
    try:
        ph.verify(stored_password, provided_password)
        return True
    except argon2.exceptions.VerifyMismatchError:
        return False
    except argon2.exceptions.VerificationError:
        return False

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def get_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    if lat1 == "-" or lon1 == "-":
        return "-"
    else:
        R = 6371.0
        
        lat1_rad, lon1_rad = radians(lat1), radians(lon1)
        lat2_rad, lon2_rad = radians(lat2), radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c
        return round(distance, 2)

def generate_unique_id(conn: sqlite3.Connection) -> int:
    while True:
        candidate = random.randint(100000000, 999999999)
        cursor = conn.cursor()
        user_exists = cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (candidate,)).fetchone()
        org_exists = cursor.execute("SELECT 1 FROM organisations WHERE id = ?", (candidate,)).fetchone()
        if not user_exists and not org_exists:
            return candidate

def get_aes_key() -> bytes:
    key = st.secrets.get("VOLUNTREE_AES_KEY")
    if not key:
        raise ValueError("Encryption key not set in Streamlit secrets (VOLUNTREE_AES_KEY)")
    return base64.urlsafe_b64decode(key)

def encrypt_coordinate(value: float) -> str:
    if value:
        key = get_aes_key()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        value_bytes = str(value).encode()
        ct = aesgcm.encrypt(nonce, value_bytes, None)
        return base64.urlsafe_b64encode(nonce + ct).decode()
    else:
        return "-"

def decrypt_coordinate(token) -> float:
    if not token or token == "-":
        return 0.0
    
    if isinstance(token, (int, float)):
        return float(token)
    
    if isinstance(token, str):
        try:
            key = get_aes_key()
            aesgcm = AESGCM(key)
            data = base64.urlsafe_b64decode(token)
            nonce, ct = data[:12], data[12:]
            value_bytes = aesgcm.decrypt(nonce, ct, None)
            return float(value_bytes.decode())
        except Exception as e:
            try:
                return float(token)
            except ValueError:
                return 0.0
    
    return 0.0

def export_personal_data(conn):
    c = conn.cursor()
    
    user_data = c.execute("""
        SELECT name, age, email, latitude, longitude, registration_date
        FROM users WHERE user_id = ?
    """, (st.session_state.user_id,)).fetchone()
    
    if user_data:
        name, age, email, latitude, longitude, registration_date = user_data
        
        data = {
            'Field': ['Name', 'Age', 'Email', 'Latitude', 'Longitude', 'Registration Date'],
            'Value': [name, age, email, latitude or 'Not set', longitude or 'Not set', registration_date]
        }
        
        csv = pd.DataFrame(data).to_csv(index=False)
        
        st.download_button(
            label="Confirm Download",
            data=csv,
            file_name=f"personal_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

        conn.rollback()
        
def export_volunteering_history(conn):
    c = conn.cursor()
    
    applications = c.execute("""
        SELECT 
            o.title,
            o.description,
            o.location,
            o.event_date,
            o.duration,
            o.category,
            o.min_required_rating,
            org.name as organization_name,
            a.status,
            a.application_date,
            r.rating,
            r.reflection,
            r.created_at as reflection_date
        FROM applications a
        JOIN opportunities o ON a.opportunity_id = o.id
        JOIN organisations org ON o.org_id = org.id
        LEFT JOIN ratings r ON a.opportunity_id = r.opportunity_id AND a.user_id = r.user_id
        WHERE a.user_id = ? AND status = 'completed'
        ORDER BY a.application_date DESC
    """, (st.session_state.user_id,)).fetchall()
    
    if applications:
        columns = [
            'Opportunity Title', 'Description', 'Location', 'Event Date', 'Duration',
            'Category', 'Minimum Required Rating', 'Organization', 'Application Status',
            'Application Date', 'Rating Given', 'Reflection', 'Reflection Date'
        ]
        
        csv = pd.DataFrame(applications, columns=columns).to_csv(index=False)
        
        st.download_button(
            label="Confirm Download",
            data=csv,
            file_name=f"volunteering_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No volunteering history found to export.")
