import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
from datetime import datetime, timedelta
import os

def admin_panel(conn):
    c = conn.cursor()

    if st.session_state.user_email != "egeguvener0808@gmail.com":
        st.error("Access denied.")
        return

    st.markdown("""
        <style>
            .stat {
                text-align: center;
                padding: 1rem;
            }
            .stat .value {
                font-size: 4rem;
                font-weight: bold;
                margin: 0;
                line-height: 1;
            }
            .stat .label {
                font-size: 1.1rem;
                margin: 0;
                color: #555;
            }
            /* Optional: tighten up the columns on smaller screens */
            @media (max-width: 768px) {
                .stColumns > div {width: 50% !important;}
            }
        </style>
    """, unsafe_allow_html=True)

    num_of_pending_orgs = c.execute("SELECT COUNT(*) FROM pending_organisations").fetchone()[0]

    t1, t2, t3, t4 = st.tabs([
        "Analytics",
        f"Pending Organisations ({num_of_pending_orgs})",
        "Databases",
        "Files"
    ])
    st.markdown('''
        <style>
            button[data-baseweb="tab"] {
                font-size: 24px;
                margin: 0;
                width: 100%;
            }
        </style>
            ''''', unsafe_allow_html=True)
    
    with t1:
        st.markdown("<h1 style='font-family: Inter;'>VolunTree</h1>", unsafe_allow_html=True)
        st.text("")
        st.text("")
        st.text("")
        c = conn.cursor()

        queries = [
            ("Organisations",  "SELECT COUNT(*) FROM organisations"),
            ("Users",    "SELECT COUNT(*) FROM users"),
            ("Opportunities",  "SELECT COUNT(*) FROM opportunities"),
            ("Applications",   "SELECT COUNT(*) FROM applications")
        ]
        stats = []
        for label, sql in queries:
            c.execute(sql)
            stats.append((label, c.fetchone()[0]))

        cols = st.columns(len(stats), gap="small")
        for col, (label, value) in zip(cols, stats):
            with col:
                st.markdown(f"""
                    <div class="stat">
                      <p class="value">{value}</p><br>
                      <p class="label">{label}</p>
                    </div>
                """, unsafe_allow_html=True)

        st.text("")
        st.text("")
        st.text("")

        c.execute("""
            SELECT o.id, o.title, u.name AS org_name,
               o.latitude, o.longitude
            FROM opportunities o
            JOIN organisations u ON o.org_id = u.id
            WHERE o.latitude IS NOT NULL AND o.longitude IS NOT NULL
        """)
        opps = c.fetchall()

        data = []
        for opp_id, title, org_name, lat, lon in opps:

            c.execute("""
            SELECT 
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted_count,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_count
            FROM applications
            WHERE opportunity_id = ?
            """, (opp_id,))
            pending_count, accepted_count, rejected_count = c.fetchone()

            c.execute("""
            SELECT AVG(rating) FROM ratings WHERE opportunity_id = ?
            """, (opp_id,))
            avg_rating = c.fetchone()[0]
            avg_rating = round(avg_rating, 2) if avg_rating is not None else "N/A"

            location = c.execute("SELECT location FROM opportunities where id = ?", (opp_id,)).fetchone()[0]
            data.append({
            "opp_id": opp_id,
            "title": title,
            "org_name": org_name,
            "location": location,
            "lat": lat,
            "lon": lon,
            "pending_count": pending_count or 0,
            "accepted_count": accepted_count or 0,
            "rejected_count": rejected_count or 0,
            "avg_rating": avg_rating
            })

        if data:
            df_map = pd.DataFrame(data)
            
            layer = pdk.Layer(
            "ScatterplotLayer",
            df_map,
            get_position=["lon", "lat"],
            get_fill_color="color",
            pickable=True,
            auto_highlight=True,
            radius_scale=20,
            radius_min_pixels=5,
            radius_max_pixels=20,
            id="scatter-layer"
            )

            deck = pdk.Deck(
            map_style="light",
            initial_view_state=pdk.ViewState(
                latitude=df_map["lat"].mean(),
                longitude=df_map["lon"].mean(),
                zoom=10,
                pitch=40,
            ),
            layers=[layer],
            tooltip={
                "html": """
                    <div style="font-family: Inter; font-size:12px; min-width:150px;">
                      <b style="font-size:16px;">{title}</b><hr style="margin:4px 0;">
                        {location}<br>
                        By <b>{org_name}</b><br>
                        <span style="font-size:1em;">
                        <b>{avg_rating}</b> ⭐
                        </span><br>
                    </div>
                """,
                "style": {
                    "backgroundColor": "white",
                    "color": "black",
                    "padding": "15px",
                    "borderRadius": "15px",
                    "minWidth": "200px",
                    "maxWidth": "300px",
                    "width": "auto",
                    "minHeight": "100px",
                    "maxHeight": "150px",
                    "textAlign": "left",
                    "height": "auto",
                    "fontFamily": "Inter, sans-serif",
                    "boxShadow": "0 0 10px rgba(0,0,0,0.2)"
                    }
                }
            )

            st.pydeck_chart(deck, use_container_width=True)
        else:
            for i in range(8):
                st.text("")
            st.info("No opportunities available for mapping.")

        c.execute("""
            SELECT category, COUNT(*) as count
            FROM opportunities
            GROUP BY category
        """)
        category_data = c.fetchall()

        if category_data:
            df = pd.DataFrame(category_data, columns=["Category", "Count"])

            fig = px.pie(
            df,
            names="Category",
            values="Count",
            hole=0.3,
            hover_data=["Count"],
            )

            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category data available for opportunities.")

    with t2:
        st.title("Pending Organisation Requests")
        c = conn.cursor()
        c.execute("SELECT id, name, description, email, request_date FROM pending_organisations")
        pending_orgs = c.fetchall()

        if not pending_orgs:
            st.info("No pending organisation requests.")

        for org in pending_orgs:
            with st.container(border=True):
                org_id, name, description, email, request_date = org
                st.header(name)
                st.write(f"**Description:** {description}")
                st.write(f"**Email:** {email}")
                st.write(f"**Requested on:** {request_date}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Approve", key=f"approve_{org_id}", use_container_width=True, type="primary"):
                        c.execute("""
                            INSERT INTO organisations (name, description, email, password)
                            SELECT name, description, email, password FROM pending_organisations WHERE id = ?
                        """, (org_id,))
                        c.execute("DELETE FROM pending_organisations WHERE id = ?", (org_id,))
                        conn.commit()
                        st.success(f"✅ Approved {name}")
                        st.rerun()
                with col2:
                    if st.button("Reject", key=f"reject_{org_id}", use_container_width=True):
                        c.execute("DELETE FROM pending_organisations WHERE id = ?", (org_id,))
                        conn.commit()
                        st.warning(f"❌ Rejected {name}")
                        st.rerun()

    with t3:
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["Organisations", "Users", "Opportunities", "Applications", "Ratings", "Image BLOB", "Chats", "Chat Messages"])
        with tab1:
            c.execute("SELECT * FROM organisations")
            orgs = c.fetchall()
            orgs_cols = [desc[0] for desc in c.description]
            df_orgs = pd.DataFrame(orgs, columns=orgs_cols)
            edited_orgs = st.data_editor(df_orgs, num_rows="dynamic", use_container_width=True, key="orgs_editor")
            if st.button("Save Changes (Organisations)", key="save_orgs", use_container_width=True):
                for idx, row in edited_orgs.iterrows():
                    c.execute(
                        f"UPDATE organisations SET " +
                        ", ".join([f"{col} = ?" for col in orgs_cols[1:]]) +
                        " WHERE id = ?",
                        [row[col] for col in orgs_cols[1:]] + [row["id"]]
                    )
                conn.commit()
                st.success("Organisations updated.")

        with tab2:
            c.execute("SELECT * FROM users")
            inds = c.fetchall()
            inds_cols = [desc[0] for desc in c.description]
            df_inds = pd.DataFrame(inds, columns=inds_cols)
            edited_inds = st.data_editor(df_inds, num_rows="dynamic", use_container_width=True, key="inds_editor")
            if st.button("Save Changes (Users)", key="save_inds", use_container_width=True):
                for idx, row in edited_inds.iterrows():
                    c.execute(
                        f"UPDATE users SET " +
                        ", ".join([f"{col} = ?" for col in inds_cols[1:]]) +
                        " WHERE id = ?",
                        [row[col] for col in inds_cols[1:]] + [row["id"]]
                    )
                conn.commit()
                st.success("Users updated.")

        with tab3:
            c.execute("SELECT * FROM opportunities")
            opps = c.fetchall()
            opps_cols = [desc[0] for desc in c.description]
            df_opps = pd.DataFrame(opps, columns=opps_cols)
            edited_opps = st.data_editor(df_opps, num_rows="dynamic", use_container_width=True, key="opps_editor")
            if st.button("Save Changes (Opportunities)", key="save_opps", use_container_width=True):
                for idx, row in edited_opps.iterrows():
                    c.execute(
                        f"UPDATE opportunities SET " +
                        ", ".join([f"{col} = ?" for col in opps_cols[1:]]) +
                        " WHERE id = ?",
                        [row[col] for col in opps_cols[1:]] + [row["id"]]
                    )
                conn.commit()
                st.success("Opportunities updated.")

        with tab4:
            c.execute("SELECT * FROM applications")
            apps = c.fetchall()
            apps_cols = [desc[0] for desc in c.description]
            df_apps = pd.DataFrame(apps, columns=apps_cols)
            edited_apps = st.data_editor(df_apps, num_rows="dynamic", use_container_width=True, key="apps_editor")
            if st.button("Save Changes (Applications)", key="save_apps", use_container_width=True):
                for idx, row in edited_apps.iterrows():
                    c.execute(
                        f"UPDATE applications SET " +
                        ", ".join([f"{col} = ?" for col in apps_cols[1:]]) +
                        " WHERE id = ?",
                        [row[col] for col in apps_cols[1:]] + [row["id"]]
                    )
                conn.commit()
                st.success("Applications updated.")

        with tab5:
            c.execute("SELECT * FROM ratings")
            ratings = c.fetchall()
            ratings_cols = [desc[0] for desc in c.description]
            df_ratings = pd.DataFrame(ratings, columns=ratings_cols)
            edited_ratings = st.data_editor(df_ratings, num_rows="dynamic", use_container_width=True, key="ratings_editor")
            if st.button("Save Changes (Ratings)", key="save_ratings", use_container_width=True):
                for idx, row in edited_ratings.iterrows():
                    c.execute(
                        f"UPDATE ratings SET " +
                        ", ".join([f"{col} = ?" for col in ratings_cols[1:]]) +
                        " WHERE id = ?",
                        [row[col] for col in ratings_cols[1:]] + [row["id"]]
                    )
                conn.commit()
                st.success("Ratings updated.")

        with tab6:
            c.execute("SELECT * FROM opportunity_images")
            images = c.fetchall()
            images_cols = [desc[0] for desc in c.description]
            df_images = pd.DataFrame(images, columns=images_cols)
            edited_images = st.data_editor(df_images, num_rows="dynamic", use_container_width=True, key="images_editor")
            if st.button("Save Changes (Images)", key="save_images", use_container_width=True):
                for idx, row in edited_images.iterrows():
                    c.execute(
                        f"UPDATE opportunity_images SET " +
                        ", ".join([f"{col} = ?" for col in images_cols[1:]]) +
                        " WHERE id = ?",
                        [row[col] for col in images_cols[1:]] + [row["id"]]
                    )
                conn.commit()
                st.success("Images updated.")

        with tab7:
            c.execute("SELECT * FROM chats")
            chats = c.fetchall()
            chats_cols = [desc[0] for desc in c.description]
            df_chats = pd.DataFrame(chats, columns=chats_cols)
            edited_chats = st.data_editor(df_chats, num_rows="dynamic", use_container_width=True, key="chats_editor")
            if st.button("Save Changes (Chats)", key="save_chats", use_container_width=True):
                for idx, row in edited_chats.iterrows():
                    c.execute(
                        f"UPDATE chats SET " +
                        ", ".join([f"{col} = ?" for col in chats_cols[1:]]) +
                        " WHERE id = ?",
                        [row[col] for col in chats_cols[1:]] + [row["id"]]
                    )
                conn.commit()
                st.success("Chats updated.")

        with tab8:
            c.execute("SELECT * FROM messages")
            chat_msgs = c.fetchall()
            chat_msgs_cols = [desc[0] for desc in c.description]
            df_chat_msgs = pd.DataFrame(chat_msgs, columns=chat_msgs_cols)
            edited_chat_msgs = st.data_editor(df_chat_msgs, num_rows="dynamic", use_container_width=True, key="chat_msgs_editor")
            if st.button("Save Changes (Chat Messages)", key="save_chat_msgs", use_container_width=True):
                for idx, row in edited_chat_msgs.iterrows():
                    c.execute(
                        f"UPDATE messages SET " +
                        ", ".join([f"{col} = ?" for col in chat_msgs_cols[1:]]) +
                        " WHERE id = ?",
                        [row[col] for col in chat_msgs_cols[1:]] + [row["id"]]
                    )
                conn.commit()
                st.success("Chat Messages updated.")

    with t4:
        def list_files_recursively(directory):
            file_paths = []
            for root, _, files in os.walk(directory):
                for file in files:
                    file_paths.append(os.path.join(root, file))
            return file_paths

        files = list_files_recursively('.')
        
        for file in files:
            st.write(f"File: {file}")
            
            if st.button(f"Download {os.path.basename(file)}", key=file, use_container_width=True):
                with open(file, "rb") as f:
                    file_content = f.read()
                
                st.download_button(
                    label=f"Click to download {os.path.basename(file)}",
                    data=file_content,
                    file_name=os.path.basename(file),
                    mime="application/octet-stream",
                    key=f"download_{file}",
                    use_container_width=True
                )
