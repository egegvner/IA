import streamlit as st
from utils import CATEGORY_COLORS
from utils import navigate_to

def browse_opportunities(conn):
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
                                st.rerun()
                                
    else:
        st.info("No opportunities found matching your criteria.")
    
    if 'temp_opp_details' in st.session_state and st.session_state.temp_opp_details and 'temp_opp_id' in st.session_state:
        st.session_state.current_page = "opp_details"
        st.rerun()
