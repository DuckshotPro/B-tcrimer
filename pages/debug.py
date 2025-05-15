import streamlit as st
import pandas as pd
import os
import psutil
from utils.logging_config import get_logger

logger = get_logger(__name__)

def show():
    """Display the debug page with system information and database stats"""
    st.title("System Debug Information")

    try:
        # Basic system information first - with minimal dependencies
        st.subheader("Basic System Status")

        # Process info using psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        st.info(f"Memory Usage: {memory_info.rss / (1024 * 1024):.2f} MB")
        st.info(f"CPU Percent: {process.cpu_percent(interval=0.1)}%")

        # Environment variables (filtered)
        st.subheader("Environment Variables")
        env_vars = {key: value for key, value in os.environ.items() 
                    if not key.startswith("AWS") and not "KEY" in key.upper() 
                    and not "SECRET" in key.upper() and not "TOKEN" in key.upper()
                    and not "PASSWORD" in key.upper() and not "PASS" in key.upper()}

        # Display as simple table
        df = pd.DataFrame(list(env_vars.items()), columns=["Variable", "Value"])
        st.dataframe(df)

        # Check if we can access the database
        st.subheader("Database Connection Test")
        try:
            from database.operations import get_db_connection

            conn = get_db_connection()
            st.success("✅ Database connection successful!")

            # Try a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            st.info(f"Test query result: {result}")

            conn.close()
        except Exception as e:
            st.error(f"❌ Database connection failed: {str(e)}")
            logger.error(f"Database connection error in debug page: {str(e)}", exc_info=True)

    except Exception as e:
        st.error(f"Error in debug page: {str(e)}")
        logger.error(f"General error in debug page: {str(e)}", exc_info=True)