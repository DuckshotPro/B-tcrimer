import os
import streamlit as st
import configparser
import datetime
import time
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

# Function to refresh data
def refresh_data():
    try:
        logger.info("Starting data refresh")
        current_time = datetime.datetime.now()
        refresh_interval = int(config['DEFAULT']['DataRefreshInterval'])
        
        # Check if refresh is needed
        if (current_time - st.session_state.last_data_refresh).total_seconds() >= refresh_interval:
            with st.spinner('Refreshing cryptocurrency data...'):
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
                st.success("Data refresh completed successfully!")
                time.sleep(1)  # Show success message briefly
                st.rerun()  # Refresh the UI
        else:
            logger.debug("Data refresh skipped - within refresh interval")
    except Exception as e:
        logger.error(f"Error during data refresh: {str(e)}", exc_info=True)
        st.error(f"Error refreshing data: {str(e)}")

# Set page config
st.set_page_config(
    page_title="Crypto Analysis Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for modern UI
st.markdown("""
<style>
    /* Modern card styling */
    div[data-testid="stVerticalBlock"] > div:has(div.stDataFrame) {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 5px;
        font-weight: 500;
    }
    
    /* Header styling */
    h1, h2, h3 {
        font-weight: 600 !important;
    }
    
    /* Sidebar styling */
    [data-testid=stSidebar] {
        background-image: linear-gradient(to bottom, #262730, #1E1E2E);
    }
    
    /* Navigation buttons styling */
    div.row-widget.stRadio > div {
        display: flex;
        flex-direction: column;
        gap: 5px;
    }
    
    div.row-widget.stRadio > div[role="radiogroup"] > label {
        padding: 8px 15px;
        border-radius: 5px;
        background-color: rgba(255, 255, 255, 0.05);
        margin-bottom: 5px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
    
    /* Metrics styling */
    [data-testid="stMetricValue"] {
        font-weight: bold;
    }
    
    /* Success/info message styling */
    div.stSuccess, div.stInfo {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    logger.info("Initializing application session")
    st.session_state.initialized = True
    st.session_state.last_data_refresh = datetime.datetime.min
    st.session_state.config = config
    
    # Initialize database
    initialize_database()
    logger.info("Database initialized")

# Sidebar header with logo
st.sidebar.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 20px;">
    <div style="font-size: 1.8rem; font-weight: 600; background: linear-gradient(to right, #00B0F0, #00D1C4); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Crypto Analysis
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.markdown("### Navigation")

# Navigation
page_icons = {
    "Dashboard": "📊",
    "Data Sources": "📡",
    "Technical Analysis": "📈",
    "Sentiment Analysis": "🔍",
    "Alerts Configuration": "⚠️",
    "Backtesting": "⏱️",
    "System Logs": "📝"
}

pages = ["Dashboard", "Data Sources", "Technical Analysis", "Sentiment Analysis", 
         "Alerts Configuration", "Backtesting", "System Logs"]

# Create navigation buttons
page = st.sidebar.radio(
    "Navigate to",
    pages,
    format_func=lambda x: f"{page_icons[x]} {x}"
)

# Refresh data section
st.sidebar.markdown("### Data Control")
refresh_col1, refresh_col2 = st.sidebar.columns([1, 1])

with refresh_col1:
    if st.button("🔄 Refresh Data", use_container_width=True):
        refresh_data()

with refresh_col2:
    if st.button("🧹 Clean Cache", use_container_width=True):
        st.cache_data.clear()
        st.success("Cache cleared!")
        time.sleep(1)
        st.rerun()

# Add last refresh time display
if st.session_state.last_data_refresh != datetime.datetime.min:
    st.sidebar.info(f"Last data refresh: {st.session_state.last_data_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

# Check for automatic data refresh if more than refresh interval passed
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
st.sidebar.markdown("""
<div style="text-align: center; opacity: 0.7; font-size: 0.8rem;">
    <p>Cryptocurrency Analysis Platform</p>
    <p>Version 1.0.0</p>
    <p>© 2025</p>
</div>
""", unsafe_allow_html=True)
