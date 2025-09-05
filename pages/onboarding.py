import streamlit as st
import configparser
import time
from utils.logging_config import get_logger

logger = get_logger(__name__)

def show_welcome_wizard():
    """Display the welcome wizard for first-time users"""
    
    # Initialize onboarding state
    if 'onboarding_step' not in st.session_state:
        st.session_state.onboarding_step = 1
        st.session_state.onboarding_completed = False
        st.session_state.user_preferences = {
            'experience_level': 'beginner',
            'primary_interest': 'investing',
            'notification_preferences': 'essential',
            'theme': 'dark'
        }
    
    # Custom CSS for onboarding
    st.markdown("""
    <style>
        .onboarding-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 2rem;
            margin: 1rem 0;
            color: white;
            text-align: center;
        }
        .step-indicator {
            display: flex;
            justify-content: center;
            margin-bottom: 2rem;
        }
        .step-circle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 10px;
            font-weight: bold;
        }
        .step-active {
            background-color: #00D1C4;
            color: white;
        }
        .step-completed {
            background-color: #4CAF50;
            color: white;
        }
        .step-inactive {
            background-color: rgba(255,255,255,0.3);
            color: white;
        }
        .welcome-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: linear-gradient(to right, #FFD700, #FFA500);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="welcome-title">Welcome to B-TCRimer! 🚀</h1>', unsafe_allow_html=True)
    
    # Progress indicator
    step_indicators = ""
    for i in range(1, 6):
        if i < st.session_state.onboarding_step:
            class_name = "step-circle step-completed"
            icon = "✓"
        elif i == st.session_state.onboarding_step:
            class_name = "step-circle step-active"
            icon = str(i)
        else:
            class_name = "step-circle step-inactive"
            icon = str(i)
        step_indicators += f'<div class="{class_name}">{icon}</div>'
    
    st.markdown(f'<div class="step-indicator">{step_indicators}</div>', unsafe_allow_html=True)
    
    # Step content
    if st.session_state.onboarding_step == 1:
        show_welcome_step()
    elif st.session_state.onboarding_step == 2:
        show_experience_step()
    elif st.session_state.onboarding_step == 3:
        show_interests_step()
    elif st.session_state.onboarding_step == 4:
        show_setup_step()
    elif st.session_state.onboarding_step == 5:
        show_completion_step()

def show_welcome_step():
    """Step 1: Welcome and overview"""
    st.markdown("""
    <div class="onboarding-container">
        <h2>🎯 Your Ultimate Crypto Analysis Platform</h2>
        <p style="font-size: 1.2rem; margin: 1.5rem 0;">
            B-TCRimer combines real-time market data, advanced technical analysis, 
            and sentiment insights to help you make informed trading decisions.
        </p>
        
        <div style="display: flex; justify-content: space-around; margin: 2rem 0;">
            <div style="text-align: center;">
                <div style="font-size: 2rem;">📊</div>
                <p><strong>Real-Time Data</strong><br/>Live prices from 20+ exchanges</p>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2rem;">🤖</div>
                <p><strong>AI Analysis</strong><br/>Sentiment & technical signals</p>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2rem;">⚡</div>
                <p><strong>Smart Alerts</strong><br/>Never miss opportunities</p>
            </div>
        </div>
        
        <p style="margin-top: 2rem; opacity: 0.9;">
            Let's get you set up in just 2 minutes! ⏱️
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Let's Get Started! 🚀", key="start_onboarding", use_container_width=True):
            st.session_state.onboarding_step = 2
            st.rerun()

def show_experience_step():
    """Step 2: Experience level selection"""
    st.markdown("""
    <div class="onboarding-container">
        <h2>📚 What's Your Experience Level?</h2>
        <p style="font-size: 1.1rem; margin-bottom: 2rem;">
            This helps us customize your dashboard and provide relevant insights.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    experience_options = {
        "beginner": {
            "title": "🌱 New to Crypto",
            "desc": "Just getting started with cryptocurrency trading and analysis"
        },
        "intermediate": {
            "title": "📈 Some Experience", 
            "desc": "Familiar with basic trading concepts and technical analysis"
        },
        "advanced": {
            "title": "🚀 Expert Trader",
            "desc": "Experienced with complex strategies and market analysis"
        }
    }
    
    selected = st.radio(
        "Choose your experience level:",
        options=list(experience_options.keys()),
        format_func=lambda x: f"{experience_options[x]['title']}\n{experience_options[x]['desc']}",
        index=0
    )
    
    st.session_state.user_preferences['experience_level'] = selected
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Back", key="back_to_1"):
            st.session_state.onboarding_step = 1
            st.rerun()
    with col3:
        if st.button("Continue →", key="continue_to_3"):
            st.session_state.onboarding_step = 3
            st.rerun()

def show_interests_step():
    """Step 3: Primary interests selection"""
    st.markdown("""
    <div class="onboarding-container">
        <h2>🎯 What's Your Primary Goal?</h2>
        <p style="font-size: 1.1rem; margin-bottom: 2rem;">
            We'll prioritize features and insights based on your main interest.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    interest_options = {
        "investing": "💎 Long-term Investing - Focus on fundamentals and long-term trends",
        "day_trading": "⚡ Day Trading - Real-time signals and short-term opportunities", 
        "research": "🔬 Market Research - Deep analysis and sentiment tracking",
        "portfolio": "📊 Portfolio Management - Track performance and risk management"
    }
    
    selected = st.radio(
        "What's your primary interest?",
        options=list(interest_options.keys()),
        format_func=lambda x: interest_options[x],
        index=0
    )
    
    st.session_state.user_preferences['primary_interest'] = selected
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Back", key="back_to_2"):
            st.session_state.onboarding_step = 2
            st.rerun()
    with col3:
        if st.button("Continue →", key="continue_to_4"):
            st.session_state.onboarding_step = 4
            st.rerun()

def show_setup_step():
    """Step 4: Quick setup preferences"""
    st.markdown("""
    <div class="onboarding-container">
        <h2>⚙️ Quick Setup</h2>
        <p style="font-size: 1.1rem; margin-bottom: 2rem;">
            Configure your notification and display preferences.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Notification preferences
    st.subheader("📱 Notifications")
    notification_level = st.select_slider(
        "How often would you like to receive alerts?",
        options=["minimal", "essential", "frequent", "all"],
        value="essential",
        format_func=lambda x: {
            "minimal": "🔕 Critical Only",
            "essential": "🔔 Important Updates", 
            "frequent": "📢 Regular Updates",
            "all": "🚨 All Notifications"
        }[x]
    )
    
    # Theme preference
    st.subheader("🎨 Display Theme")
    theme = st.radio(
        "Choose your preferred theme:",
        options=["dark", "light"],
        format_func=lambda x: f"🌙 Dark Mode" if x == "dark" else "☀️ Light Mode",
        horizontal=True
    )
    
    st.session_state.user_preferences['notification_preferences'] = notification_level
    st.session_state.user_preferences['theme'] = theme
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Back", key="back_to_3"):
            st.session_state.onboarding_step = 3
            st.rerun()
    with col3:
        if st.button("Complete Setup →", key="continue_to_5"):
            st.session_state.onboarding_step = 5
            st.rerun()

def show_completion_step():
    """Step 5: Completion and welcome"""
    st.markdown("""
    <div class="onboarding-container">
        <h2>🎉 All Set! Welcome Aboard!</h2>
        <p style="font-size: 1.2rem; margin: 1.5rem 0;">
            Your personalized crypto analysis platform is ready to go!
        </p>
        
        <div style="background: rgba(255,255,255,0.1); border-radius: 10px; padding: 1.5rem; margin: 2rem 0;">
            <h3>🚀 What's Next?</h3>
            <div style="text-align: left; max-width: 400px; margin: 0 auto;">
                <p>✅ Explore the <strong>Dashboard</strong> for live market data</p>
                <p>✅ Check <strong>Technical Analysis</strong> for trading signals</p>
                <p>✅ Visit <strong>Data Sources</strong> to configure your feeds</p>
                <p>✅ Set up <strong>Alerts</strong> for your favorite coins</p>
            </div>
        </div>
        
        <p style="margin-top: 2rem; font-size: 1.1rem;">
            Need help? Look for the <strong>❓ Help</strong> tooltips throughout the platform!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Save preferences
    prefs = st.session_state.user_preferences
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **Your Settings:**
        - Experience: {prefs['experience_level'].title()}
        - Focus: {prefs['primary_interest'].replace('_', ' ').title()}
        - Notifications: {prefs['notification_preferences'].title()}
        - Theme: {prefs['theme'].title()}
        """)
    
    with col2:
        if st.button("🎯 Start Trading!", key="complete_onboarding", use_container_width=True):
            st.session_state.onboarding_completed = True
            st.session_state.show_onboarding = False
            logger.info(f"User completed onboarding with preferences: {prefs}")
            st.success("🚀 Welcome to B-TCRimer! Redirecting to dashboard...")
            time.sleep(2)
            st.rerun()
        
        if st.button("← Back to Settings", key="back_to_4"):
            st.session_state.onboarding_step = 4
            st.rerun()

def show_quick_tour():
    """Show contextual help tour"""
    if st.session_state.get('show_tour', False):
        st.markdown("""
        <div style="position: fixed; top: 20px; right: 20px; z-index: 9999; 
                    background: #FF6B6B; color: white; padding: 1rem; border-radius: 10px; 
                    max-width: 300px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
            <h4 style="margin: 0 0 0.5rem 0;">💡 Quick Tip</h4>
            <p style="margin: 0; font-size: 0.9rem;">
                Welcome to your dashboard! The metrics at the top show your portfolio performance. 
                Click on different tabs to explore analysis tools.
            </p>
            <button onclick="this.parentElement.style.display='none'" 
                    style="background: none; border: none; color: white; float: right; cursor: pointer;">✕</button>
        </div>
        """, unsafe_allow_html=True)

def show():
    """Main onboarding entry point"""
    if st.session_state.get('show_onboarding', True) and not st.session_state.get('onboarding_completed', False):
        show_welcome_wizard()
    else:
        st.session_state.show_onboarding = False
        show_quick_tour()