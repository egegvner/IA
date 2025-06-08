import bcrypt
import re
from datetime import datetime
import streamlit as st

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

def navigate_to(page):
    st.session_state.current_page = page
    for key in list(st.session_state.keys()):
        if key.startswith('temp_'):
            del st.session_state[key]
    st.rerun()

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(provided_password, stored_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

def validate_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

from math import radians, sin, cos, sqrt, atan2

def get_distance_km(lat1, lon1, lat2, lon2):
    """
    Calculates the great-circle distance between two points on the Earth.
    
    Parameters:
        lat1, lon1: Latitude and Longitude of point 1 (float)
        lat2, lon2: Latitude and Longitude of point 2 (float)
        
    Returns:
        Distance in kilometers (float)
    """
    R = 6371.0

    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return round(distance, 2)
