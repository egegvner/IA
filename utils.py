import bcrypt
import re
import streamlit as st
from math import radians, sin, cos, sqrt, atan2
import random
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import sqlite3
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def navigate_to(page: str):
    st.session_state.current_page = page
    for key in list(st.session_state.keys()):
        if key.startswith('temp_'):
            del st.session_state[key]
    st.rerun()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(provided_password: str, stored_password: str) -> bool:
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def get_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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
        
def reverse_geocode_location(lat: float, lon: float) -> str:
    geolocator = Nominatim(user_agent="voluntree_app")
    try:
        loc = geolocator.reverse((lat, lon), language="en", zoom=5, addressdetails=True)
    except GeocoderTimedOut:
        return reverse_geocode_location(lat, lon)
    
    if not loc or not loc.raw.get("address"):
        return "Location unknown"

    addr = loc.raw["address"]
    city     = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("district")
    province = addr.get("state") or addr.get("region")
    country  = addr.get("country")
    
    parts = [part for part in (city, province, country) if part]
    return ", ".join(parts) if parts else "Location unknown"

def get_aes_key() -> bytes:
    key = st.secrets.get("VOLUNTREE_AES_KEY")
    if not key:
        raise ValueError("Encryption key not set in Streamlit secrets (VOLUNTREE_AES_KEY)")
    return base64.urlsafe_b64decode(key)

def encrypt_coordinate(value: float) -> str:
    key = get_aes_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    value_bytes = str(value).encode()
    ct = aesgcm.encrypt(nonce, value_bytes, None)
    return base64.urlsafe_b64encode(nonce + ct).decode()

def decrypt_coordinate(token: str) -> float:
    if token:
        key = get_aes_key()
        aesgcm = AESGCM(key)
        data = base64.urlsafe_b64decode(token)
        nonce, ct = data[:12], data[12:]
        value_bytes = aesgcm.decrypt(nonce, ct, None)
        return float(value_bytes.decode())
    else:
        return "-"
