import streamlit as st
from datetime import datetime
from utils import navigate_to
from dialogs import reflection_dialog

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
    
    st.text("")
    st.text("")
    st.text("")

    t1, t2 = st.tabs(["📜 Your Past Reflections", "✅ Opportunities Ready for Reflection"])
    st.markdown('''<style>
                        button[data-baseweb="tab"] {
                        font-size: 24px;
                        margin: 0;
                        width: 100%;
                        }
                        </style>
                ''', unsafe_allow_html=True)
    
    with t1:
        st.text("")
        st.text("")
        st.text("")
        st.markdown("<h3 style='font-family: Inter;'>My Past Reflections</h3>", unsafe_allow_html=True)
        
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
                border: 0px solid #ddd;
                border-radius: 15px;
                padding: 15px;
                margin: 8px;
                background-color: white;
                transition: transform 0.3s;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }

            .reflection-card:hover {
                transform: translateY(-5px);
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
                -webkit-line-clamp: 4;
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

            try:
                c.execute("""
                SELECT r.id, o.title, u.name as org_name, r.rating, r.reflection, r.created_at, o.location, o.event_date
                FROM ratings r
                JOIN opportunities o ON r.opportunity_id = o.id
                JOIN organisations u ON r.org_id = u.id
                WHERE r.id = ? AND r.student_id = ?
                """, (ref_id, st.session_state.user_id))

            except UnboundLocalError as e:
                st.warning("No reflection details available.")
                return
            
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

    with t2:
        pending_reflections = c.execute("""
        SELECT o.id, o.title, u.name as org_name, o.event_date, u.id as org_id
        FROM applications a
        JOIN opportunities o ON a.opportunity_id = o.id
        JOIN organisations u ON o.org_id = u.id
        WHERE a.student_id = ? AND a.status = 'accepted'
        AND o.id NOT IN (
            SELECT opportunity_id FROM ratings WHERE student_id = ?
        )
        ORDER BY o.event_date DESC
        """, (st.session_state.user_id, st.session_state.user_id)).fetchall()
                
        if pending_reflections:
            st.markdown("<h3 style='font-family: Inter;'>Experiences Ready for Reflection</h3>", unsafe_allow_html=True)

            num_pending = len(pending_reflections)
            num_rows_pending = (num_pending + 2) // 3
            
            st.markdown("""
            <style>
            .pending-card {
                border: 0px solid #ddd;
                border-radius: 15px;
                padding: 15px;
                margin: 8px;
                height: 100%;
                background-color: white;
                transition: transform 0.3s;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .pending-card:hover {
                transform: translateY(-5px);
            }
            .pending-title {
                font-weight: bold;
                font-size: 1.2em;
                margin-bottom: 8px;
                color: #2c3e50;
            }
            .pending-org {
                font-size: 0.9em;
                color: #darkgray;
                margin-bottom: 5px;
            }
            .pending-date {
                font-size: 0.85em;
                color: gray;
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
                                
                                if st.button("Write Reflection", key=f"reflect_{opp_id}", use_container_width=True):
                                    st.session_state.show_reflection_dialog = True
                                    st.session_state.reflection_opp_id = opp_id
                                    st.session_state.reflection_org_id = org_id
                                    st.session_state.reflection_title = title
                                    reflection_dialog(conn)
        else:
            st.write("You don't have any completed opportunities that need reflections.")
