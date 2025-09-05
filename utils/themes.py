"""
Professional theming system for B-TCRimer cryptocurrency analysis platform.
Provides dark/light themes with financial-grade styling.
"""

import streamlit as st
from typing import Dict, Any

class Theme:
    """Professional theme configuration for financial applications"""
    
    def __init__(self):
        self.themes = {
            'dark': self._dark_theme(),
            'light': self._light_theme()
        }
    
    def _dark_theme(self) -> Dict[str, Any]:
        """Dark theme optimized for extended trading sessions"""
        return {
            'name': 'dark',
            'display_name': '🌙 Dark Mode',
            'colors': {
                # Primary colors
                'primary': '#00B0F0',
                'secondary': '#00D1C4', 
                'accent': '#FFD700',
                'success': '#10B981',
                'danger': '#EF4444',
                'warning': '#F59E0B',
                'info': '#3B82F6',
                
                # Background colors
                'bg_primary': '#0E1117',
                'bg_secondary': '#262730',
                'bg_tertiary': '#1E1E2E',
                'bg_card': '#1a1a2e',
                'bg_hover': '#2a2a3e',
                
                # Text colors
                'text_primary': '#FAFAFA',
                'text_secondary': '#A0A0A0',
                'text_muted': '#6B7280',
                'text_inverse': '#000000',
                
                # Border colors
                'border_light': 'rgba(255, 255, 255, 0.1)',
                'border_medium': 'rgba(255, 255, 255, 0.2)',
                'border_strong': 'rgba(255, 255, 255, 0.3)',
                
                # Financial colors
                'bull_green': '#10B981',
                'bear_red': '#EF4444',
                'neutral_yellow': '#F59E0B',
                'volume_blue': '#3B82F6'
            },
            'fonts': {
                'primary': '"Inter", "SF Pro Display", "Segoe UI", sans-serif',
                'mono': '"JetBrains Mono", "SF Mono", "Monaco", monospace'
            },
            'shadows': {
                'soft': '0 2px 8px rgba(0, 0, 0, 0.1)',
                'medium': '0 4px 12px rgba(0, 0, 0, 0.15)',
                'strong': '0 8px 25px rgba(0, 0, 0, 0.25)'
            }
        }
    
    def _light_theme(self) -> Dict[str, Any]:
        """Light theme for daytime trading and analysis"""
        return {
            'name': 'light',
            'display_name': '☀️ Light Mode',
            'colors': {
                # Primary colors
                'primary': '#0066CC',
                'secondary': '#00A693',
                'accent': '#FF6B35',
                'success': '#059669',
                'danger': '#DC2626',
                'warning': '#D97706',
                'info': '#2563EB',
                
                # Background colors
                'bg_primary': '#FFFFFF',
                'bg_secondary': '#F8FAFC',
                'bg_tertiary': '#F1F5F9',
                'bg_card': '#FFFFFF',
                'bg_hover': '#F8FAFC',
                
                # Text colors
                'text_primary': '#1F2937',
                'text_secondary': '#4B5563',
                'text_muted': '#9CA3AF',
                'text_inverse': '#FFFFFF',
                
                # Border colors
                'border_light': 'rgba(0, 0, 0, 0.1)',
                'border_medium': 'rgba(0, 0, 0, 0.2)',
                'border_strong': 'rgba(0, 0, 0, 0.3)',
                
                # Financial colors
                'bull_green': '#059669',
                'bear_red': '#DC2626',
                'neutral_yellow': '#D97706',
                'volume_blue': '#2563EB'
            },
            'fonts': {
                'primary': '"Inter", "SF Pro Display", "Segoe UI", sans-serif',
                'mono': '"JetBrains Mono", "SF Mono", "Monaco", monospace'
            },
            'shadows': {
                'soft': '0 2px 8px rgba(0, 0, 0, 0.08)',
                'medium': '0 4px 12px rgba(0, 0, 0, 0.1)',
                'strong': '0 8px 25px rgba(0, 0, 0, 0.15)'
            }
        }

    def get_theme(self, theme_name: str = 'dark') -> Dict[str, Any]:
        """Get theme configuration"""
        return self.themes.get(theme_name, self.themes['dark'])
    
    def apply_theme(self, theme_name: str = None):
        """Apply theme to Streamlit application"""
        if theme_name is None:
            theme_name = st.session_state.get('current_theme', 'dark')
        
        theme = self.get_theme(theme_name)
        colors = theme['colors']
        fonts = theme['fonts']
        shadows = theme['shadows']
        
        # Generate comprehensive CSS
        css = f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');
        
        /* === ROOT VARIABLES === */
        :root {{
            --primary-color: {colors['primary']};
            --secondary-color: {colors['secondary']};
            --accent-color: {colors['accent']};
            --success-color: {colors['success']};
            --danger-color: {colors['danger']};
            --warning-color: {colors['warning']};
            --info-color: {colors['info']};
            
            --bg-primary: {colors['bg_primary']};
            --bg-secondary: {colors['bg_secondary']};
            --bg-tertiary: {colors['bg_tertiary']};
            --bg-card: {colors['bg_card']};
            
            --text-primary: {colors['text_primary']};
            --text-secondary: {colors['text_secondary']};
            --text-muted: {colors['text_muted']};
            
            --border-light: {colors['border_light']};
            --border-medium: {colors['border_medium']};
            
            --bull-green: {colors['bull_green']};
            --bear-red: {colors['bear_red']};
            
            --shadow-soft: {shadows['soft']};
            --shadow-medium: {shadows['medium']};
            --shadow-strong: {shadows['strong']};
            
            --font-primary: {fonts['primary']};
            --font-mono: {fonts['mono']};
        }}
        
        /* === GLOBAL STYLES === */
        .stApp {{
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: var(--font-primary);
        }}
        
        /* === SIDEBAR STYLING === */
        .css-1d391kg, .css-1cypcdb {{
            background-color: var(--bg-secondary) !important;
            border-right: 1px solid var(--border-light);
        }}
        
        .css-1d391kg .css-1544g2n {{
            color: var(--text-primary) !important;
        }}
        
        /* === MAIN CONTENT AREA === */
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }}
        
        /* === ENHANCED CARDS === */
        .financial-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: var(--shadow-soft);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        .financial-card:hover {{
            box-shadow: var(--shadow-medium);
            border-color: var(--border-medium);
            transform: translateY(-2px);
        }}
        
        /* === METRICS STYLING === */
        [data-testid="metric-container"] {{
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: 10px;
            padding: 1rem;
            box-shadow: var(--shadow-soft);
            transition: all 0.3s ease;
        }}
        
        [data-testid="metric-container"]:hover {{
            box-shadow: var(--shadow-medium);
            transform: translateY(-1px);
        }}
        
        [data-testid="metric-container"] > div {{
            gap: 0.25rem;
        }}
        
        [data-testid="metric-container"] [data-testid="metric-label"] {{
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }}
        
        [data-testid="metric-container"] [data-testid="metric-value"] {{
            font-size: 1.875rem;
            font-weight: 700;
            color: var(--text-primary);
            font-family: var(--font-mono);
        }}
        
        [data-testid="metric-container"] [data-testid="metric-delta"] {{
            font-size: 0.875rem;
            font-weight: 600;
        }}
        
        /* === BUTTONS === */
        .stButton > button {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            font-family: var(--font-primary);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: var(--shadow-soft);
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-medium);
            filter: brightness(1.1);
        }}
        
        .stButton > button:active {{
            transform: translateY(0);
        }}
        
        /* === CHARTS & PLOTS === */
        .js-plotly-plot .plotly .main-svg {{
            border-radius: 8px;
            box-shadow: var(--shadow-soft);
        }}
        
        /* === DATAFRAMES === */
        .stDataFrame {{
            border: 1px solid var(--border-light);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: var(--shadow-soft);
        }}
        
        .stDataFrame > div {{
            background-color: var(--bg-card);
        }}
        
        /* === ALERTS & NOTIFICATIONS === */
        .stAlert {{
            border-radius: 8px;
            border: 1px solid var(--border-light);
            box-shadow: var(--shadow-soft);
        }}
        
        .stSuccess {{
            background-color: color-mix(in srgb, var(--success-color) 10%, transparent);
            border-color: var(--success-color);
            color: var(--success-color);
        }}
        
        .stError {{
            background-color: color-mix(in srgb, var(--danger-color) 10%, transparent);
            border-color: var(--danger-color);
            color: var(--danger-color);
        }}
        
        .stWarning {{
            background-color: color-mix(in srgb, var(--warning-color) 10%, transparent);
            border-color: var(--warning-color);
            color: var(--warning-color);
        }}
        
        .stInfo {{
            background-color: color-mix(in srgb, var(--info-color) 10%, transparent);
            border-color: var(--info-color);
            color: var(--info-color);
        }}
        
        /* === TYPOGRAPHY === */
        h1, h2, h3, h4, h5, h6 {{
            font-family: var(--font-primary);
            font-weight: 600;
            color: var(--text-primary);
        }}
        
        .financial-title {{
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
        }}
        
        /* === LOADING ANIMATIONS === */
        .stSpinner > div {{
            border-color: var(--primary-color) transparent transparent transparent;
        }}
        
        /* === RESPONSIVE DESIGN === */
        @media (max-width: 768px) {{
            .main .block-container {{
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1rem;
            }}
            
            .financial-card {{
                padding: 1rem;
                margin-bottom: 1rem;
            }}
            
            [data-testid="metric-container"] [data-testid="metric-value"] {{
                font-size: 1.5rem;
            }}
            
            .financial-title {{
                font-size: 1.5rem;
            }}
        }}
        
        /* === CUSTOM COMPONENTS === */
        .crypto-price-positive {{
            color: var(--bull-green) !important;
            font-weight: 600;
        }}
        
        .crypto-price-negative {{
            color: var(--bear-red) !important;
            font-weight: 600;
        }}
        
        .crypto-volume {{
            color: var(--info-color) !important;
            font-family: var(--font-mono);
        }}
        
        /* === SCROLLBARS === */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: var(--bg-secondary);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--border-medium);
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--primary-color);
        }}
        
        /* === ANIMATIONS === */
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .animate-slide-in {{
            animation: slideIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }}
        
        @keyframes pulse {{
            0%, 100% {{
                opacity: 1;
            }}
            50% {{
                opacity: 0.7;
            }}
        }}
        
        .animate-pulse {{
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }}
        
        /* === THEME TOGGLE === */
        .theme-toggle {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: 50px;
            padding: 0.5rem;
            box-shadow: var(--shadow-medium);
        }}
        
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
        
        # Store current theme
        st.session_state.current_theme = theme_name
    
    def create_theme_selector(self):
        """Create theme selection widget"""
        current_theme = st.session_state.get('current_theme', 'dark')
        
        theme_options = {
            'dark': '🌙 Dark Mode',
            'light': '☀️ Light Mode'
        }
        
        selected_theme = st.selectbox(
            "🎨 Choose Theme",
            options=list(theme_options.keys()),
            format_func=lambda x: theme_options[x],
            index=0 if current_theme == 'dark' else 1,
            key="theme_selector"
        )
        
        if selected_theme != current_theme:
            st.session_state.current_theme = selected_theme
            st.rerun()
        
        return selected_theme

# Create global theme instance
theme_manager = Theme()

def apply_custom_css():
    """Apply additional custom CSS for specific components"""
    st.markdown("""
    <style>
    /* Financial dashboard specific styles */
    .profit-card {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
    }
    
    .loss-card {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 8px 25px rgba(239, 68, 68, 0.3);
    }
    
    .neutral-card {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 8px 25px rgba(245, 158, 11, 0.3);
    }
    
    /* Trading signal indicators */
    .signal-buy {
        background: #10B981;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .signal-sell {
        background: #EF4444;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .signal-hold {
        background: #F59E0B;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

def get_financial_colors():
    """Get standardized financial colors for charts"""
    theme = theme_manager.get_theme(st.session_state.get('current_theme', 'dark'))
    return {
        'bull': theme['colors']['bull_green'],
        'bear': theme['colors']['bear_red'],
        'neutral': theme['colors']['neutral_yellow'],
        'volume': theme['colors']['volume_blue'],
        'primary': theme['colors']['primary'],
        'secondary': theme['colors']['secondary']
    }