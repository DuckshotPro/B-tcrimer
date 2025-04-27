import os
import streamlit as st
import configparser
import datetime
from utils.logging_config import setup_logging, get_logger
from database.operations import initialize_database, perform_database_maintenance
from data_collection.exchange_data import update_exchange_data
from data_collection.news_data import update_news_data
from data_collection.social_data import update_social_data
from pages import dashboard, data_sources, technical_analysis, sentiment, alerts, backtesting, logs

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Initialize session state
if 'initialized' not in st.session_state:
    logger.info("Initializing application session")
    st.session_state.initialized = True
    st.session_state.last_data_refresh = datetime.datetime.min
    st.session_state.config = config
    
    # Initialize database
    initialize_database()
    logger.info("Database initialized")

# Function to refresh data
def refresh_data():
    try:
        logger.info("Starting data refresh")
        current_time = datetime.datetime.now()
        refresh_interval = int(config['DEFAULT']['DataRefreshInterval'])
        
        # Check if refresh is needed
        if (current_time - st.session_state.last_data_refresh).total_seconds() >= refresh_interval:
            with st.spinner('Refreshing data...'):
                if config.getboolean('EXCHANGES', 'Enabled'):
                    update_exchange_data(config)
                
                if config.getboolean('NEWS', 'Enabled'):
                    update_news_data(config)
                
                if config.getboolean('SOCIAL', 'Enabled'):
                    update_social_data(config)
                
                # Perform database maintenance
                perform_database_maintenance()
                
                st.session_state.last_data_refresh = current_time
                logger.info("Data refresh completed")
        else:
            logger.debug("Data refresh skipped - within refresh interval")
    except Exception as e:
        logger.error(f"Error during data refresh: {str(e)}", exc_info=True)
        st.error(f"Error refreshing data: {str(e)}")

# Set page config
st.set_page_config(
    page_title="Cryptocurrency Analysis Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("Crypto Analysis Platform")

# Refresh data button
if st.sidebar.button("Refresh Data"):
    refresh_data()

# Add last refresh time display
if st.session_state.last_data_refresh != datetime.datetime.min:
    st.sidebar.info(f"Last data refresh: {st.session_state.last_data_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

# Navigation
page = st.sidebar.radio(
    "Navigate to",
    ["Dashboard", "Data Sources", "Technical Analysis", "Sentiment Analysis", 
     "Alerts Configuration", "Backtesting", "System Logs"]
)

# Check for automatic data refresh
refresh_data()

# Display the selected page
if page == "Dashboard":
    dashboard.show()
elif page == "Data Sources":
    data_sources.show()
elif page == "Technical Analysis":
    technical_analysis.show()
elif page == "Sentiment Analysis":
    sentiment.show()
elif page == "Alerts Configuration":
    alerts.show()
elif page == "Backtesting":
    backtesting.show()
elif page == "System Logs":
    logs.show()

# Footer
st.sidebar.markdown("---")
st.sidebar.info(
    "Cryptocurrency Analysis Platform\n"
    f"Version 1.0.0\n"
    f"© {datetime.datetime.now().year}"
)
