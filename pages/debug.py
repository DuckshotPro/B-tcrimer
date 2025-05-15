import streamlit as st
import pandas as pd
import os
from sqlalchemy import text
from database.operations import get_db_connection, get_sqlalchemy_engine
from utils.logging_config import get_logger

logger = get_logger(__name__)

def show():
    """Display a debug page for testing database connections"""
    st.title("Debug Page")
    
    st.write("This page tests database connectivity and shows if queries are working.")
    
    # Display environment info
    st.subheader("Environment Info")
    if 'DATABASE_URL' in os.environ:
        st.info("PostgreSQL database is configured")
    else:
        st.info("Using SQLite database")
    
    # Connection test
    st.subheader("Database Connection Test")
    try:
        conn = get_db_connection()
        st.success("Database connection successful!")
        conn.close()
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        logger.error(f"Database connection failed: {str(e)}", exc_info=True)
    
    # SQLAlchemy connection test
    st.subheader("SQLAlchemy Engine Test")
    try:
        engine = get_sqlalchemy_engine()
        st.success("SQLAlchemy engine created successfully!")
    except Exception as e:
        st.error(f"SQLAlchemy engine creation failed: {str(e)}")
        logger.error(f"SQLAlchemy engine creation failed: {str(e)}", exc_info=True)
    
    # Simple query test
    st.subheader("Simple Query Test")
    try:
        engine = get_sqlalchemy_engine()
        
        # Create a test table if it doesn't exist
        if 'DATABASE_URL' in os.environ:
            # PostgreSQL
            create_query = """
            CREATE TABLE IF NOT EXISTS debug_test (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                value INTEGER
            )
            """
            with engine.connect() as connection:
                connection.execute(text(create_query))
                connection.commit()
            
            # Insert test data
            insert_query = """
            INSERT INTO debug_test (name, value) 
            VALUES ('test1', 100), ('test2', 200)
            ON CONFLICT (id) DO NOTHING
            """
            with engine.connect() as connection:
                connection.execute(text(insert_query))
                connection.commit()
            
            # Query test data
            query = "SELECT * FROM debug_test"
            df = pd.read_sql_query(query, engine)
            
        else:
            # SQLite
            create_query = """
            CREATE TABLE IF NOT EXISTS debug_test (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
            """
            with engine.connect() as connection:
                connection.execute(text(create_query))
                connection.commit()
            
            # Insert test data
            insert_query = """
            INSERT OR IGNORE INTO debug_test (id, name, value) 
            VALUES (1, 'test1', 100), (2, 'test2', 200)
            """
            with engine.connect() as connection:
                connection.execute(text(insert_query))
                connection.commit()
            
            # Query test data
            query = "SELECT * FROM debug_test"
            df = pd.read_sql_query(query, engine)
        
        # Display results
        st.subheader("Query Results:")
        st.dataframe(df)
        
    except Exception as e:
        st.error(f"Query test failed: {str(e)}")
        logger.error(f"Query test failed: {str(e)}", exc_info=True)