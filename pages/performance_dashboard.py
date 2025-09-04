
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# It's better to have a centralized db connection, but for a modular page, this is straightforward
DATABASE_URL = "sqlite:///./api_keys.db"

def get_db_session():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()

def show():
    st.title("🚀 Performance Dashboard")
    st.markdown("Monitoring key growth and user engagement metrics.")

    try:
        session = get_db_session()
        # Using pandas to read directly from SQL is efficient for analysis
        df = pd.read_sql("SELECT * FROM users", session.bind)
        session.close()
    except Exception as e:
        st.error(f"Failed to connect to the database: {e}")
        st.warning("Please ensure the FastAPI server has been run at least once to create the database.")
        return

    if df.empty:
        st.info("No user data found yet.")
        return

    st.header("Key Metrics")
    col1, col2, col3 = st.columns(3)

    total_users = len(df)
    paid_users = int(df['is_paid_user'].sum())
    total_lead_score = int(df['lead_score'].sum())

    with col1:
        st.metric(label="Total Users", value=total_users)
    
    with col2:
        st.metric(label="Paid Users", value=paid_users)
        if total_users > 0:
            st.markdown(f"**Conversion Rate:** {paid_users/total_users:.2%}")
        
    with col3:
        st.metric(label="Total Lead Score", value=total_lead_score, help="Sum of all user lead scores. Indicates overall engagement.")

    st.header("User Analysis")
    
    st.subheader("Lead Score Distribution")
    st.bar_chart(df['lead_score'].value_counts())
    st.markdown("This chart shows how many users fall into each lead score bucket. A healthy distribution has users moving to higher scores over time.")

    st.subheader("Raw User Data")
    st.dataframe(df)

