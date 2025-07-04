import bcrypt
import re
import streamlit as st
from math import radians, sin, cos, sqrt, atan2
import random
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import sqlite3

CATEGORY_COLORS = {
    "Environment": "#09AD11",
    "Education": "#3AA6FF",
    "Health": "#B50000",
    "Animal Welfare": "#FFAA00",
    "Community Service": "#E456FD",
    "Sports": "#00FFE5",
    "Arts & Culture": "#440FCA",
    "Disaster Relief": "#5C5C5C",
    "Other": "#000000"
}

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

def get_distance_km(lat1: int, lon1: int, lat2: int, lon2: int) -> float:
    R = 6371.0
    
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return round(distance, 2)

def generate_unique_user_id(conn: sqlite3.Connection) -> int:
    while True:
        candidate = random.randint(100000000, 999999999)
        if not conn.cursor().execute("SELECT 1 FROM users WHERE user_id = ?", (candidate,)).fetchone():
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
