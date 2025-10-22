import streamlit as st
import pandas as pd
import io
import base64
import imghdr
from datetime import datetime
from utils import navigate_to, hash_password, validate_email, export_personal_data, export_volunteering_history
from dialogs import map_location_dialog
from streamlit_cookies_controller import CookieController
import time

def detect_image_mime_type(img_bytes):
    try:
        if not img_bytes or len(img_bytes) < 10:
            return None
            
        img_format = imghdr.what(None, h=img_bytes)
        if img_format == 'jpeg':
            return 'image/jpeg'
        elif img_format == 'png':
            return 'image/png'
        elif img_format == 'gif':
            return 'image/gif'
        else:
            return 'image/png'
    except:
        return None

def is_valid_image_data(img_bytes):
    try:
        if not img_bytes:
            return False
        
        if len(img_bytes) < 100:
            return False
            
        if img_bytes.startswith(b'\xff\xd8\xff'):
            return True
        elif img_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            return True
        elif img_bytes.startswith(b'GIF87a') or img_bytes.startswith(b'GIF89a'):
            return True
        else:
            return detect_image_mime_type(img_bytes) is not None
    except:
        return False

def profile_page(conn):
    c = conn.cursor()
    
    try:
        all_users = c.execute("SELECT user_id, profile_picture FROM users WHERE profile_picture IS NOT NULL").fetchall()
        for user_id, profile_picture in all_users:
            if not is_valid_image_data(profile_picture):
                c.execute("UPDATE users SET profile_picture = NULL WHERE user_id = ?", (user_id,))
        conn.commit()
    except Exception as e:
        pass
    
    user_data = c.execute("""
        SELECT name, age, email, latitude, longitude, profile_picture 
        FROM users WHERE user_id = ?
    """, (st.session_state.user_id,)).fetchone()
    
    if not user_data:
        st.error("User not found")
        return
    
    name, age, email, latitude, longitude, profile_picture = user_data
    
    st.markdown("<h1 style='font-family: Inter;'>👤 Profile Settings</h1>", unsafe_allow_html=True)
        
    st.markdown("""
    <style>
    .profile-picture-circle {
        border-radius: 50%;
        object-fit: cover;
        width: 150px;
        height: 150px;
        border: 4px solid #ffffff;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15), 0 0 0 1px rgba(0,0,0,0.05);
        transition: all 0.3s ease-in-out;
        cursor: pointer;
    }
    .profile-picture-circle:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 20px rgba(0,0,0,0.2), 0 0 0 1px rgba(0,0,0,0.1);
        border-color: #f8f9fa;
    }
    .profile-picture-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 15px;
        position: relative;
        padding: 10px;
    }
    .profile-picture-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        border-radius: 50%;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        z-index: -1;
        opacity: 0.8;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if profile_picture and is_valid_image_data(profile_picture):
            try:
                img_base64 = base64.b64encode(profile_picture).decode()
                mime_type = detect_image_mime_type(profile_picture)
                
                if mime_type:
                    st.markdown(f"""
                    <div class="profile-picture-container">
                        <img src="data:{mime_type};base64,{img_base64}" class="profile-picture-circle" alt="Profile Picture">
                    </div>
                    """, unsafe_allow_html=True)
                    st.caption("Current Profile Picture")
                else:
                    st.warning("Invalid image format detected.")
                    if st.button("Remove Invalid Picture", use_container_width=True):
                        c.execute("""
                            UPDATE users SET profile_picture = NULL WHERE user_id = ?
                        """, (st.session_state.user_id,))
                        conn.commit()
                        st.success("Invalid profile picture removed!")
                        st.rerun()
            except Exception as e:
                st.warning("Error displaying profile picture. Please upload a new one.")
                if st.button("Remove Corrupted Picture", use_container_width=True):
                    c.execute("""
                        UPDATE users SET profile_picture = NULL WHERE user_id = ?
                    """, (st.session_state.user_id,))
                    conn.commit()
                    st.success("Corrupted profile picture removed!")
                    st.rerun()
        elif profile_picture:
            st.warning("Invalid profile picture detected. Please upload a new one.")
            if st.button("Remove Invalid Picture", use_container_width=True):
                c.execute("""
                    UPDATE users SET profile_picture = NULL WHERE user_id = ?
                """, (st.session_state.user_id,))
                conn.commit()
                st.success("Invalid profile picture removed!")
                st.rerun()
        else:
            st.image("user.png", width=150, caption="Default Profile Picture")
    
    with col2:
        uploaded_file = st.file_uploader(
            "Upload new profile picture", 
            type=['png', 'jpg', 'jpeg'], 
            help="Upload a profile picture (PNG, JPG, JPEG)"
        )
        
        if uploaded_file is not None:
            if uploaded_file.size > 5 * 1024 * 1024:
                st.error("File size too large. Please upload an image smaller than 5MB.")
                return
            
            if uploaded_file.type not in ['image/png', 'image/jpeg', 'image/jpg']:
                st.error("Please upload a valid image file (PNG, JPG, JPEG)")
                return
            
            img_bytes = uploaded_file.read()
            
            if not is_valid_image_data(img_bytes):
                st.error("Invalid image file detected. Please upload a valid image.")
                return
            
            img_base64 = base64.b64encode(img_bytes).decode()
            mime_type = uploaded_file.type
            
            st.markdown(f"""
            <div class="profile-picture-container">
                <img src="data:{mime_type};base64,{img_base64}" class="profile-picture-circle" alt="Preview">
            </div>
            """, unsafe_allow_html=True)
            st.caption("Preview")
            
            if st.button("Save Profile Picture", type="primary"):
                try:
                    c.execute("""
                        UPDATE users SET profile_picture = ? WHERE user_id = ?
                    """, (img_bytes, st.session_state.user_id))
                    conn.commit()
                    st.success("Profile picture updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating profile picture: {str(e)}")
    
    st.divider()
    
    co1, co2 = st.columns(2, gap="large")
    with co1:
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Name", value=name, disabled=True, help="Name cannot be changed")
        with col2:
            st.text_input("Age", value=age, disabled=True, help="Age cannot be changed")
        
        new_email = st.text_input("Email", value=email, help="You can change your email address")

    with co2:
        
        if latitude and longitude and latitude != "-" and longitude != "-" and latitude is not None and longitude is not None:
            try:
                lat = float(latitude)
                lon = float(longitude)
                
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    try:
                        st.success(f"Your location is **set**")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Change Location", use_container_width=True):
                                map_location_dialog()
                        with col2:
                            if st.button("Remove Location", use_container_width=True):
                                c.execute("""
                                    UPDATE users SET latitude = ?, longitude = ? WHERE user_id = ?
                                """, ("-", "-", st.session_state.user_id,))
                                conn.commit()
                                st.success("Location removed successfully!")
                                st.rerun()

                    except Exception as e:
                        st.warning(f"Error getting location name: {str(e)}")
                        st.write(f"Coordinates: {lat:.6f}, {lon:.6f}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Change Location", use_container_width=True):
                                map_location_dialog()
                        with col2:
                            if st.button("Remove Location", use_container_width=True):
                                c.execute("""
                                    UPDATE users SET latitude = NULL, longitude = NULL WHERE user_id = ?
                                """, (st.session_state.user_id,))
                                conn.commit()
                                st.success("Location removed successfully!")
                                st.rerun()
                else:
                    st.warning("Invalid coordinate values detected. Please update your location.")
                    st.write(f"Coordinates: {latitude}, {longitude}")
                    if st.button("Update Location", use_container_width=True):
                        map_location_dialog()

            except (ValueError, TypeError):
                st.warning("Invalid coordinate format detected. Please update your location.")
                st.write(f"Coordinates: {latitude}, {longitude}")
                if st.button("Update Location", use_container_width=True):
                    map_location_dialog()

        else:
            st.warning("No location set. Add a location to find opportunities near you.")
            if st.button("Add Location", use_container_width=True):
                map_location_dialog()

        st.caption("Please click Update Changes after choosing a location on the map.")

    st.text("")
    st.text("")

    if st.button("Save Changes", type="primary", use_container_width=True):
            if not validate_email(new_email):
                st.error("Please enter a valid email address")
                return
            
            existing_user = c.execute("""
                SELECT user_id FROM users WHERE email = ? AND user_id != ?
            """, (new_email, st.session_state.user_id)).fetchone()
            
            if existing_user:
                st.error("This email is already taken by another user")
                return
            
            try:
                c.execute("""
                    UPDATE users SET email = ? WHERE user_id = ?
                """, (new_email, st.session_state.user_id))
                
                if hasattr(st.session_state, 'picked_lat') and hasattr(st.session_state, 'picked_lon'):
                    if st.session_state.picked_lat and st.session_state.picked_lon:
                        c.execute("""
                            UPDATE users SET latitude = ?, longitude = ? WHERE user_id = ?
                        """, (st.session_state.picked_lat, st.session_state.picked_lon, st.session_state.user_id))
                        st.session_state.picked_lat = None
                        st.session_state.picked_lon = None
                
                conn.commit()
                st.success("Profile updated successfully!")
                
                st.session_state.user_email = new_email
                
                controller = CookieController()
                controller.set("user_email", new_email)
                
                st.rerun()
            except Exception as e:
                st.error(f"Error updating profile: {str(e)}")
                conn.rollback()

    st.divider()
    st.markdown("### 📊 Data Export")
    st.text("")
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        if st.button("Export Personal Data (CSV)", use_container_width=True):
            export_personal_data(conn)
    
    with col2:
        if st.button("Export Volunteering History (CSV)", use_container_width=True):
            export_volunteering_history(conn)

    if st.button("Delete My Account", use_container_width=True):
        st.error("This action is irreversible. All your data will be permanently deleted.")
        time.sleep(1)
        c1, c2 = st.columns(2, gap="large")
        if c1.button("Cancel", use_container_width=True):
            st.rerun()
        if c2.button("Confirm Account Deletion", use_container_width=True, type="primary"):
            with st.spinner("Deleting your account..."):
                try:
                    c.execute("DELETE FROM ratings WHERE user_id = ?", (st.session_state.user_id,))
                    c.execute("DELETE FROM applications WHERE user_id = ?", (st.session_state.user_id,))
                    c.execute("DELETE FROM users WHERE user_id = ?", (st.session_state.user_id,))
                    c.execute("DELETE FROM user_ratings WHERE user_id = ?", (st.session_state.user_id,))
                    c.execute("DELETE FROM messages WHERE sender_id = ?", (st.session_state.user_id,))
                    c.execute("DELETE FROM chats WHERE user_id = ?", (st.session_state.user_id,))
                    conn.commit()
                                    
                    st.session_state.logged_in = False
                    st.session_state.user_id = None
                    st.session_state.user_email = None
                    st.session_state.user_type = None
                    
                    controller = CookieController()
                    controller.delete("user_id")
                    controller.delete("user_email")
                    controller.delete("user_type")
                    time.sleep(4)
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting account: {str(e)}")
