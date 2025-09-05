"""
System status indicator component for B-TCRimer.
Shows real-time system health and alerts in the header.
"""

import streamlit as st
from datetime import datetime
from utils.error_handler import error_handler
from utils.auth import auth_manager

def show_system_status():
    """Display system status indicator at the top of the application"""
    
    # Get system health
    health = error_handler.get_system_health()
    current_user = auth_manager.get_current_user()
    
    # Only show detailed status to admin users
    if current_user and current_user.get('role') in ['admin', 'superadmin']:
        show_detailed_status(health)
    else:
        show_basic_status(health)

def show_basic_status(health):
    """Show basic status for regular users"""
    status = health.get('status', 'unknown')
    
    status_config = {
        'healthy': {
            'color': '#10B981',
            'icon': '🟢',
            'message': 'All systems operational'
        },
        'warning': {
            'color': '#F59E0B',
            'icon': '🟡',
            'message': 'Minor issues detected'
        },
        'critical': {
            'color': '#EF4444',
            'icon': '🔴',
            'message': 'System maintenance in progress'
        }
    }
    
    config = status_config.get(status, status_config['healthy'])
    
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, {config['color']}15 0%, transparent 100%); 
                border-left: 3px solid {config['color']}; 
                padding: 0.5rem 1rem; margin-bottom: 1rem; border-radius: 0 8px 8px 0;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span>{config['icon']}</span>
            <span style="font-size: 0.875rem; color: var(--text-secondary);">{config['message']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_detailed_status(health):
    """Show detailed status for admin users"""
    status = health.get('status', 'unknown')
    
    status_config = {
        'healthy': {'color': '#10B981', 'icon': '🟢'},
        'warning': {'color': '#F59E0B', 'icon': '🟡'},
        'critical': {'color': '#EF4444', 'icon': '🔴'}
    }
    
    config = status_config.get(status, status_config['healthy'])
    
    st.markdown(f"""
    <div style="background: var(--bg-secondary); border: 1px solid var(--border-light); 
                border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span>{config['icon']}</span>
                    <span style="font-weight: 600; color: {config['color']};">
                        System {status.title()}
                    </span>
                </div>
                
                <div style="display: flex; gap: 1.5rem; font-size: 0.875rem; color: var(--text-secondary);">
                    <span>CPU: {health.get('cpu_usage', 0):.1f}%</span>
                    <span>Memory: {health.get('memory_usage', 0):.1f}%</span>
                    <span>Errors (24h): {health.get('errors_24h', 0)}</span>
                </div>
            </div>
            
            <div style="font-size: 0.75rem; color: var(--text-muted);">
                Last check: {health.get('last_check', datetime.now()).strftime('%H:%M:%S')}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_maintenance_banner():
    """Show maintenance mode banner"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); 
                color: white; padding: 1rem; text-align: center; margin-bottom: 2rem;">
        <div style="font-weight: 600; margin-bottom: 0.25rem;">
            🚧 Scheduled Maintenance
        </div>
        <div style="font-size: 0.875rem; opacity: 0.9;">
            Some features may be temporarily unavailable. We'll be back shortly!
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_security_alert(message: str, level: str = "warning"):
    """Show security alert banner"""
    colors = {
        'info': '#3B82F6',
        'warning': '#F59E0B',
        'error': '#EF4444'
    }
    
    icons = {
        'info': 'ℹ️',
        'warning': '⚠️',
        'error': '🚨'
    }
    
    color = colors.get(level, colors['warning'])
    icon = icons.get(level, icons['warning'])
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {color} 0%, {color}CC 100%); 
                color: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.2rem;">{icon}</span>
            <div>
                <div style="font-weight: 600; margin-bottom: 0.25rem;">Security Notice</div>
                <div style="font-size: 0.875rem; opacity: 0.9;">{message}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)