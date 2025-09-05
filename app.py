import os
import streamlit as st
import configparser
import datetime
import time
from utils.logging_config import setup_logging, get_logger
from utils.themes import theme_manager, apply_custom_css
from utils.auth import require_authentication, auth_manager
from utils.error_handler import error_handler, safe_execute
from database.operations import initialize_database, perform_database_maintenance
from components.status_indicator import show_system_status
from data_collection.exchange_data import update_exchange_data
from data_collection.news_data import update_news_data
from data_collection.social_data import update_social_data
from pages import dashboard, data_sources, technical_analysis, sentiment, alerts, backtesting, logs, debug, domino_cascade, onboarding, admin

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
                time.sleep(1)
                st.rerun()
        else:
            logger.debug("Data refresh skipped - within refresh interval")
    except Exception as e:
        logger.error(f"Error during data refresh: {str(e)}", exc_info=True)
        st.error(f"Error refreshing data: {str(e)}")

# Set page config
st.set_page_config(
    page_title="B-TCRimer | Professional Crypto Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/DuckshotPro/B-tcrimer',
        'Report a bug': 'https://github.com/DuckshotPro/B-tcrimer/issues',
        'About': "# B-TCRimer\n### Professional Cryptocurrency Analysis Platform\n\nPowered by AI collaboration between Claude Code and Gemini AI."
    }
)

# Apply professional theming system
current_theme = st.session_state.get('current_theme', 'dark')
theme_manager.apply_theme(current_theme)
apply_custom_css()

# Authentication check (will show login if not authenticated)
require_authentication()

# Initialize session state
if 'initialized' not in st.session_state:
    logger.info("Initializing application session")
    st.session_state.initialized = True
    st.session_state.last_data_refresh = datetime.datetime.min
    st.session_state.config = config
    
    # Onboarding state
    st.session_state.show_onboarding = not st.session_state.get('onboarding_completed', False)
    st.session_state.user_preferences = st.session_state.get('user_preferences', {
        'experience_level': 'beginner',
        'primary_interest': 'investing', 
        'notification_preferences': 'essential',
        'theme': 'dark'
    })

    # Try to initialize database, but don't fail if it doesn't work
    try:
        initialize_database()
        logger.info("Database initialized")
        st.session_state.database_available = True
    except Exception as e:
        logger.warning(f"Database initialization failed, continuing without database: {str(e)}")
        st.session_state.database_available = False

# Sidebar header with logo
st.sidebar.markdown("""
<div style="text-align: center; margin-bottom: 20px;">
    <div style="font-size: 2rem; font-weight: 700; 
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                margin-bottom: 5px;">
        B-TCRimer
    </div>
    <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 15px;">
        Professional Crypto Analysis
    </div>
</div>
""", unsafe_allow_html=True)

# User info and logout
if current_user:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 Account")
    
    st.sidebar.markdown(f"""
    <div style="background: var(--bg-secondary); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <div style="color: var(--text-primary); font-weight: 600; margin-bottom: 0.25rem;">
            {current_user['username']}
        </div>
        <div style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.25rem;">
            {current_user['email']}
        </div>
        <div style="color: var(--success-color); font-size: 0.75rem; font-weight: 500;">
            Role: {current_user['role'].title()}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        auth_manager.logout()
        st.rerun()

# Theme selector
st.sidebar.markdown("### ⚙️ Settings")
theme_manager.create_theme_selector()

# Get current user for navigation
current_user = auth_manager.get_current_user()

# Navigation with role-based access
page_icons = {
    "Dashboard": "📊",
    "💰 Profit Center": "💰",
    "🎯 Domino Cascade": "🎯",
    "Technical Analysis": "📈",
    "Sentiment Analysis": "🔍",
    "Alerts Configuration": "⚠️",
    "Backtesting": "⏱️",
    "System Logs": "📝",
    "Debug Page": "🔧",
    "Admin Panel": "🛠️"
}

# Base pages for all users
pages = ["Dashboard", "💰 Profit Center", "🎯 Domino Cascade", "Technical Analysis", "Sentiment Analysis", 
         "Alerts Configuration", "Backtesting", "System Logs", "Debug Page", "Performance Dashboard"]

# Add admin page for admin users
if current_user and current_user.get('role') in ['admin', 'superadmin']:
    pages.append("Admin Panel")

# Check if onboarding should be shown
if st.session_state.get('show_onboarding', True) and not st.session_state.get('onboarding_completed', False):
    onboarding.show()
    st.stop()

# Add help toggle and onboarding reset
help_col1, help_col2 = st.sidebar.columns([1, 1])
with help_col1:
    if st.button("❓ Help", use_container_width=True):
        st.session_state.show_tour = not st.session_state.get('show_tour', False)
        st.rerun()

with help_col2:
    if st.button("🔄 Setup", use_container_width=True, help="Re-run initial setup"):
        st.session_state.show_onboarding = True
        st.session_state.onboarding_completed = False
        st.session_state.onboarding_step = 1
        st.rerun()

st.sidebar.markdown("---")

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
        try:
            refresh_data()
        except Exception as e:
            error_handler.log_error(e)
            error_handler.display_user_friendly_error(e)

with refresh_col2:
    if st.button("🧹 Clean Cache", use_container_width=True):
        st.cache_data.clear()
        st.success("Cache cleared!")
        time.sleep(1)
        st.rerun()

# Add last refresh time display
if st.session_state.last_data_refresh != datetime.datetime.min:
    st.sidebar.info(f"Last data refresh: {st.session_state.last_data_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

# Show system status indicator
show_system_status()

# Store current page for error tracking
st.session_state.current_page = page

# Display the selected page
if page == "Dashboard":
    dashboard.show()
elif page == "💰 Profit Center":
    profit_tracker.show()
elif page == "🎯 Domino Cascade":
    domino_cascade.show()
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
elif page == "Debug Page":
    debug.show()
elif page == "Admin Panel":
    admin.show()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align: center; opacity: 0.7; font-size: 0.8rem;">
    <p>Cryptocurrency Analysis Platform</p>
    <p>Version 1.0.0</p>
    <p>© 2025</p>
</div>
""", unsafe_allow_html=True)� 2025</p>
</div>
""", unsafe_allow_html=True)