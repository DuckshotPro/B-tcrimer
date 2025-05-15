
import streamlit as st
import pandas as pd
import os
import psutil
from sqlalchemy import text
from database.operations import get_db_connection, get_sqlalchemy_engine
from utils.logging_config import get_logger

logger = get_logger(__name__)

def show():
    """Display the debug page with system information and database stats"""
    st.markdown("""
    <h1 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 1.5rem; 
               background: linear-gradient(to right, #00B0F0, #00D1C4); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        System Debug Information
    </h1>
    """, unsafe_allow_html=True)
    
    try:
        # System information
        st.subheader("System Information")
        
        # Create columns for system info
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("Environment Variables")
            env_vars = {key: value for key, value in os.environ.items() 
                        if not key.startswith("AWS") and not "KEY" in key.upper() 
                        and not "SECRET" in key.upper() and not "TOKEN" in key.upper()}
            
            st.dataframe(
                pd.DataFrame(list(env_vars.items()), columns=["Variable", "Value"])
            )
        
        with col2:
            st.info("Database Information")
            try:
                engine = get_sqlalchemy_engine()
                
                # Get database metadata
                with engine.connect() as connection:
                    # Get table counts
                    if 'DATABASE_URL' in os.environ:
                        # PostgreSQL query
                        result = connection.execute(text("""
                            SELECT 
                                tablename as table_name, 
                                (SELECT COUNT(*) FROM information_schema.columns WHERE table_name=t.tablename) as column_count,
                                n_live_tup as row_count
                            FROM pg_stat_user_tables t
                            ORDER BY n_live_tup DESC;
                        """))
                    else:
                        # SQLite query
                        result = connection.execute(text("""
                            SELECT 
                                name as table_name,
                                (SELECT COUNT(*) FROM pragma_table_info(name)) as column_count,
                                (SELECT COUNT(*) FROM main.sqlite_master WHERE type='table') as row_count
                            FROM sqlite_master
                            WHERE type='table' AND name NOT LIKE 'sqlite_%'
                        """))
                    
                    tables_info = [dict(row) for row in result]
                    
                st.dataframe(pd.DataFrame(tables_info))
            except Exception as e:
                st.error(f"Error connecting to database: {str(e)}")
                logger.error(f"Database connection error in debug page: {str(e)}", exc_info=True)
        
        # Database content preview
        st.subheader("Database Content Preview")
        
        # Get list of tables
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if 'DATABASE_URL' in os.environ:
                # PostgreSQL query
                cursor.execute("""
                    SELECT tablename 
                    FROM pg_catalog.pg_tables 
                    WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'
                """)
            else:
                # SQLite query
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                
            tables = cursor.fetchall()
            tables = [row[0] for row in tables] if tables else []
            
            # Create dropdown to select table
            if tables:
                selected_table = st.selectbox("Select a table to preview", tables)
                
                # Display table preview
                if selected_table:
                    cursor.execute(f"SELECT * FROM {selected_table} LIMIT 100")
                    rows = cursor.fetchall()
                    
                    if rows:
                        # Get column names
                        column_names = [desc[0] for desc in cursor.description]
                        
                        # Convert to DataFrame
                        df = pd.DataFrame(rows, columns=column_names)
                        st.dataframe(df)
                    else:
                        st.info(f"Table '{selected_table}' is empty")
            else:
                st.info("No tables found in the database")
            
            conn.close()
        except Exception as e:
            st.error(f"Error previewing database content: {str(e)}")
            logger.error(f"Error in debug page table preview: {str(e)}", exc_info=True)
        
        # Application performance metrics
        st.subheader("Application Performance")
        
        # Create columns for performance data
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("Memory Usage")
            
            try:
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                
                memory_data = {
                    "Metric": ["RSS Memory", "VMS Memory", "Percent Memory"],
                    "Value": [
                        f"{memory_info.rss / (1024 * 1024):.2f} MB",
                        f"{memory_info.vms / (1024 * 1024):.2f} MB",
                        f"{process.memory_percent():.2f}%"
                    ]
                }
                
                st.dataframe(pd.DataFrame(memory_data))
            except Exception as e:
                st.warning(f"Could not get memory usage: {str(e)}")
        
        with col2:
            st.info("Config Settings")
            
            # Show application configuration
            try:
                import configparser
                config = configparser.ConfigParser()
                config.read('config.ini')
                
                config_data = []
                for section in config.sections():
                    for key, value in config[section].items():
                        # Skip sensitive data
                        if "key" in key.lower() or "token" in key.lower() or "secret" in key.lower() or "password" in key.lower():
                            value = "********"
                        
                        config_data.append({"Section": section, "Key": key, "Value": value})
                
                st.dataframe(pd.DataFrame(config_data))
            except Exception as e:
                st.error(f"Error reading configuration: {str(e)}")
        
        # Logs preview
        st.subheader("Recent Logs")
        
        try:
            log_file = "logs/crypto_analysis.log"
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    # Get last 100 lines
                    lines = f.readlines()[-100:]
                    
                    # Display logs with filter option
                    log_filter = st.text_input("Filter logs", "")
                    
                    if log_filter:
                        filtered_lines = [line for line in lines if log_filter.lower() in line.lower()]
                        st.code("".join(filtered_lines))
                    else:
                        st.code("".join(lines))
            else:
                st.warning(f"Log file not found: {log_file}")
        except Exception as e:
            st.error(f"Error reading log file: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading debug page: {str(e)}")
        logger.error(f"Critical error in debug page: {str(e)}", exc_info=True)
