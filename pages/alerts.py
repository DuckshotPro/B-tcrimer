import streamlit as st
import pandas as pd
import numpy as np
import datetime
import uuid
import os
import configparser

from database.operations import get_db_connection
from data_collection.exchange_data import get_latest_prices
from utils.email_alerts import send_price_alert, send_indicator_alert, send_sentiment_alert
from utils.sms_alerts import send_price_sms_alert, send_indicator_sms_alert, send_sentiment_sms_alert
from utils.logging_config import get_logger

logger = get_logger(__name__)

def show():
    """Display the alerts configuration page"""
    st.title("Alerts Configuration")
    
    try:
        # Get user email for alerts from session state or input
        if 'alert_email' not in st.session_state:
            st.session_state.alert_email = ""
        
        st.sidebar.header("Alert Settings")
        
        # Get configuration
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        # Email settings
        email_enabled = config.getboolean('ALERTS', 'EmailEnabled')
        st.sidebar.subheader("Email Notifications")
        
        if email_enabled:
            alert_email = st.sidebar.text_input("Email for Alerts", 
                                            value=st.session_state.alert_email,
                                            placeholder="Enter your email")
            
            if alert_email != st.session_state.alert_email:
                st.session_state.alert_email = alert_email
        else:
            st.sidebar.warning("Email alerts are disabled in configuration.")
        
        # SMS settings
        sms_enabled = config.getboolean('ALERTS', 'SMSEnabled', fallback=False)
        
        st.sidebar.subheader("SMS Notifications")
        
        # Add alert trigger settings
        st.sidebar.subheader("Alert Trigger Settings")
        
        # Read current trigger settings
        recurring_alerts = config.getboolean('ALERTS', 'RecurringAlerts', fallback=True)
        cooldown_minutes = config.getint('ALERTS', 'CooldownMinutes', fallback=60)
        max_triggers_per_day = config.getint('ALERTS', 'MaxTriggersPerDay', fallback=5)
        
        # UI for trigger settings
        new_recurring = st.sidebar.checkbox("Enable recurring alerts by default", 
                                        value=recurring_alerts,
                                        help="When enabled, alerts can trigger multiple times")
        
        new_cooldown = st.sidebar.number_input("Cooldown period (minutes)", 
                                          min_value=1, max_value=1440, 
                                          value=cooldown_minutes,
                                          help="Minimum time between alert triggers")
        
        new_max_daily = st.sidebar.number_input("Max triggers per day", 
                                           min_value=1, max_value=100, 
                                           value=max_triggers_per_day,
                                           help="Maximum number of times an alert can trigger in a day")
        
        # Save button for alert settings
        if st.sidebar.button("Save Alert Settings"):
            # Update config
            config.set('ALERTS', 'RecurringAlerts', str(new_recurring))
            config.set('ALERTS', 'CooldownMinutes', str(new_cooldown))
            config.set('ALERTS', 'MaxTriggersPerDay', str(new_max_daily))
            
            # Write to file
            with open('config.ini', 'w') as f:
                config.write(f)
            
            st.sidebar.success("Alert settings saved successfully!")
        
        if sms_enabled:
            # Check if Twilio credentials are set
            twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
            twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
            twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
            
            if all([twilio_account_sid, twilio_auth_token, twilio_phone_number]):
                # Get current owner phone from config
                current_phone = config.get('ALERTS', 'OwnerPhoneNumber', fallback='')
                
                # Show phone number input
                phone_number = st.sidebar.text_input(
                    "Your Phone Number (for SMS alerts)",
                    value=current_phone,
                    placeholder="Enter in format: +1234567890"
                )
                
                # Save phone number to config if changed
                if phone_number != current_phone:
                    if not phone_number or phone_number.startswith('+'):
                        config.set('ALERTS', 'OwnerPhoneNumber', phone_number)
                        with open('config.ini', 'w') as f:
                            config.write(f)
                        st.sidebar.success("Phone number saved!")
                    else:
                        st.sidebar.error("Phone number must start with + and country code (e.g., +1 for US)")
            else:
                st.sidebar.warning("Twilio credentials not set. SMS alerts will not work.")
                st.sidebar.info("Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in environment variables.")
                
                # Add button to request Twilio credentials
                if 'request_twilio' not in st.session_state:
                    st.session_state.request_twilio = False
                
                if st.sidebar.button("Set Up Twilio Credentials") or st.session_state.request_twilio:
                    # Set flag to display credentials form
                    st.session_state.request_twilio = True
                    
                    # Display a form to collect Twilio credentials
                    st.sidebar.markdown("### Twilio Credentials")
                    
                    with st.sidebar.form("twilio_credentials_form"):
                        st.write("Enter your Twilio credentials:")
                        account_sid = st.text_input("Account SID", placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
                        auth_token = st.text_input("Auth Token", placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", type="password")
                        phone_number = st.text_input("Twilio Phone Number", placeholder="+12345678900")
                        
                        submitted = st.form_submit_button("Save Credentials")
                        
                        if submitted:
                            if not account_sid or not auth_token or not phone_number:
                                st.error("All fields are required.")
                            else:
                                try:
                                    # Use environment variables
                                    from ask_secrets import ask_secrets
                                    
                                    # This will prompt the user to provide the secrets
                                    ask_secrets(
                                        secret_keys=["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"],
                                        user_message="We need your Twilio credentials to send SMS alerts. Please provide your Twilio credentials to enable SMS notifications."
                                    )
                                    
                                    st.success("Credentials request sent. Please provide the credentials when prompted.")
                                    st.session_state.request_twilio = False
                                except Exception as e:
                                    st.error(f"Failed to save credentials: {str(e)}")
                                    logger.error(f"Failed to save Twilio credentials: {str(e)}", exc_info=True)
        else:
            st.sidebar.info("SMS alerts are disabled. Enable in config.ini to receive text alerts.")
        
        # Create tabs for different alert types
        tabs = st.tabs(["Active Alerts", "Price Alerts", "Technical Indicator Alerts", "Sentiment Alerts"])
        
        # Active alerts tab
        with tabs[0]:
            show_active_alerts()
        
        # Price alerts tab
        with tabs[1]:
            show_price_alerts(st.session_state.alert_email)
        
        # Technical indicator alerts tab
        with tabs[2]:
            show_indicator_alerts(st.session_state.alert_email)
        
        # Sentiment alerts tab
        with tabs[3]:
            show_sentiment_alerts(st.session_state.alert_email)
        
        # Check alerts
        check_all_alerts(st.session_state.alert_email)
    
    except Exception as e:
        logger.error(f"Error displaying alerts page: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")

def show_active_alerts():
    """Display all active alerts"""
    st.header("Active Alerts")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all active alerts
    cursor.execute("""
        SELECT id, symbol, alert_type, condition, value, last_checked, last_triggered, notification_sent, created_at,
               trigger_count, daily_trigger_count, daily_count_reset, recurring
        FROM alerts
        WHERE active = TRUE
        ORDER BY created_at DESC
    """)
    
    alerts = cursor.fetchall()
    conn.close()
    
    if not alerts:
        st.info("No active alerts configured. Use the tabs to create new alerts.")
        return
    
    # Display alerts
    for alert in alerts:
        (alert_id, symbol, alert_type, condition, value, last_checked, last_triggered, 
         notification_sent, created_at, trigger_count, daily_trigger_count, daily_count_reset, recurring) = alert
        
        # Format dates
        if isinstance(created_at, str):
            created_at = datetime.datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        
        if last_checked and isinstance(last_checked, str):
            last_checked = datetime.datetime.strptime(last_checked, '%Y-%m-%d %H:%M:%S')
        
        if last_triggered and isinstance(last_triggered, str):
            last_triggered = datetime.datetime.strptime(last_triggered, '%Y-%m-%d %H:%M:%S')
            
        if daily_count_reset and isinstance(daily_count_reset, str):
            daily_count_reset = datetime.datetime.strptime(daily_count_reset, '%Y-%m-%d %H:%M:%S')
        
        # Alert status
        if notification_sent:
            status = "Triggered"
            status_color = "red"
        elif last_checked:
            status = "Active"
            status_color = "green"
        else:
            status = "Pending"
            status_color = "orange"
        
        # Format alert type for display
        if alert_type == 'price':
            display_type = 'Price'
        elif alert_type.startswith('indicator_'):
            indicator = alert_type.split('_', 1)[1]
            display_type = f'Indicator: {indicator.upper() if indicator in ["rsi", "macd"] else indicator.title()}'
        elif alert_type.startswith('sentiment_'):
            source = alert_type.split('_', 1)[1]
            display_type = f'Sentiment: {source.title()}'
        else:
            display_type = alert_type.title()
        
        # Create alert card with more information
        with st.expander(f"{symbol} - {display_type} {condition} {value}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Type:** {display_type}")
                st.write(f"**Condition:** {condition.title()} {value}")
                st.write(f"**Created:** {created_at.strftime('%Y-%m-%d %H:%M')}")
                
                if last_checked:
                    st.write(f"**Last Checked:** {last_checked.strftime('%Y-%m-%d %H:%M')}")
                
                if last_triggered:
                    st.write(f"**Last Triggered:** {last_triggered.strftime('%Y-%m-%d %H:%M')}")
                
                st.markdown(f"**Status:** <span style='color: {status_color}'>{status}</span>", unsafe_allow_html=True)
            
            with col2:
                # Added new information fields
                st.write(f"**Mode:** {'Recurring' if recurring else 'One-time'}")
                st.write(f"**Total Triggers:** {trigger_count}")
                st.write(f"**Daily Triggers:** {daily_trigger_count}")
                
                # Get config for alert triggers to show limits
                config = configparser.ConfigParser()
                config.read('config.ini')
                cooldown_minutes = config.getint('ALERTS', 'CooldownMinutes', fallback=60)
                max_triggers_per_day = config.getint('ALERTS', 'MaxTriggersPerDay', fallback=5)
                
                # Show cooldown status if alert was triggered
                if last_triggered:
                    cooldown_ends = last_triggered + datetime.timedelta(minutes=cooldown_minutes)
                    now = datetime.datetime.now()
                    if now < cooldown_ends:
                        minutes_left = int((cooldown_ends - now).total_seconds() / 60)
                        st.write(f"**Cooldown:** {minutes_left} min remaining")
                    else:
                        st.write("**Cooldown:** Ready")
                
                # Show daily limit status
                st.write(f"**Daily Limit:** {daily_trigger_count}/{max_triggers_per_day}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Delete button
                if st.button(f"Delete Alert", key=f"delete_{alert_id}"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
                    conn.commit()
                    conn.close()
                    st.success("Alert deleted successfully!")
                    st.rerun()
            
            with col2:
                # Reset button for triggered alerts
                if notification_sent:
                    if st.button(f"Reset Alert", key=f"reset_{alert_id}"):
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE alerts SET triggered = 0, notification_sent = 0 WHERE id = ?", 
                            (alert_id,)
                        )
                        conn.commit()
                        conn.close()
                        st.success("Alert reset successfully!")
                        st.rerun()
            
            with col3:
                # Toggle recurring mode
                current_recurring = bool(recurring)
                new_mode = "One-time" if current_recurring else "Recurring"
                
                if st.button(f"Make {new_mode}", key=f"toggle_{alert_id}"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE alerts SET recurring = ? WHERE id = ?", 
                        (0 if current_recurring else 1, alert_id)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Alert changed to {new_mode} mode!")
                    st.rerun()

def show_price_alerts(email):
    """Configure price-based alerts"""
    st.header("Price Alerts")
    st.write("Create alerts that trigger when a cryptocurrency's price crosses a specific threshold.")
    
    # Get available cryptocurrencies
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT symbol FROM ohlcv_data
        ORDER BY symbol
    """)
    
    available_symbols = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if not available_symbols:
        st.warning("No cryptocurrency data found. Please refresh data first.")
        return
    
    # Create new price alert form
    with st.form("price_alert_form"):
        st.subheader("Create Price Alert")
        
        # Select cryptocurrency
        symbol = st.selectbox("Cryptocurrency", available_symbols)
        
        # Get current price for reference
        latest_prices = get_latest_prices([symbol])
        
        if symbol in latest_prices:
            current_price = latest_prices[symbol]['price']
            st.write(f"Current price: ${current_price:.2f}")
        else:
            current_price = 0
            st.warning("Current price not available.")
        
        # Alert condition
        col1, col2 = st.columns(2)
        
        with col1:
            condition = st.selectbox("Condition", ["above", "below"])
        
        with col2:
            price = st.number_input("Price ($)", value=float(current_price), step=0.01, format="%.2f")
        
        # Email alerts
        receive_email = st.checkbox("Receive email notification", value=email != "")
        
        if receive_email and not email:
            st.warning("Please enter your email in the sidebar to receive notifications.")
        
        # Submit form
        submitted = st.form_submit_button("Create Alert")
        
        if submitted:
            try:
                if price <= 0:
                    st.error("Price must be greater than 0.")
                elif receive_email and not email:
                    st.error("Please enter your email to receive notifications.")
                else:
                    # Save alert to database
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # Get recurring setting
                    recurring = True  # Default to recurring alerts
                    
                    cursor.execute(
                        """
                        INSERT INTO alerts (
                            symbol, alert_type, condition, value, active,
                            triggered, notification_sent, created_at,
                            trigger_count, daily_trigger_count, recurring
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            symbol, 'price', condition, price, 1,
                            0, 0, datetime.datetime.now(),
                            0, 0, int(recurring)
                        )
                    )
                    
                    conn.commit()
                    conn.close()
                    
                    st.success(f"Price alert created for {symbol} {condition} ${price:.2f}")
                    st.rerun()
            except Exception as e:
                logger.error(f"Error creating price alert: {str(e)}", exc_info=True)
                st.error(f"Failed to create alert: {str(e)}")

def show_indicator_alerts(email):
    """Configure technical indicator alerts"""
    st.header("Technical Indicator Alerts")
    st.write("Create alerts that trigger when a technical indicator crosses a threshold.")
    
    # Get available cryptocurrencies
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT symbol FROM technical_indicators
        ORDER BY symbol
    """)
    
    available_symbols = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if not available_symbols:
        st.warning("No technical indicator data found. Please run technical analysis first.")
        return
    
    # Create new indicator alert form
    with st.form("indicator_alert_form"):
        st.subheader("Create Technical Indicator Alert")
        
        # Select cryptocurrency
        symbol = st.selectbox("Cryptocurrency", available_symbols)
        
        # Select indicator
        indicator_options = {
            "RSI": "rsi_14",
            "MACD": "macd",
            "MACD Signal": "macd_signal",
            "MACD Histogram": "macd_histogram"
        }
        
        indicator = st.selectbox("Indicator", list(indicator_options.keys()))
        indicator_key = indicator_options[indicator]
        
        # Get current indicator value for reference
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT {indicator_key} FROM technical_indicators
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (symbol,))
        
        result = cursor.fetchone()
        conn.close()
        
        current_value = result[0] if result else None
        
        if current_value is not None:
            st.write(f"Current {indicator} value: {current_value:.2f}")
        else:
            st.warning(f"Current {indicator} value not available.")
        
        # Alert condition
        col1, col2 = st.columns(2)
        
        with col1:
            condition = st.selectbox("Condition", ["above", "below", "crosses above", "crosses below"])
        
        with col2:
            # Set appropriate default values based on indicator
            default_value = 0
            step = 0.1
            
            if indicator == "RSI":
                default_value = 70 if condition in ["above", "crosses above"] else 30
            
            value = st.number_input(f"{indicator} Value", value=float(default_value), step=step, format="%.2f")
        
        # Email alerts
        receive_email = st.checkbox("Receive email notification", value=email != "")
        
        if receive_email and not email:
            st.warning("Please enter your email in the sidebar to receive notifications.")
        
        # Submit form
        submitted = st.form_submit_button("Create Alert")
        
        if submitted:
            try:
                if receive_email and not email:
                    st.error("Please enter your email to receive notifications.")
                else:
                    # Save alert to database
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    alert_type = f"indicator_{indicator_key}"
                    
                    # Get recurring setting
                    recurring = True  # Default to recurring alerts
                    
                    cursor.execute(
                        """
                        INSERT INTO alerts (
                            symbol, alert_type, condition, value, active,
                            triggered, notification_sent, created_at,
                            trigger_count, daily_trigger_count, recurring
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            symbol, alert_type, condition, value, 1,
                            0, 0, datetime.datetime.now(),
                            0, 0, int(recurring)
                        )
                    )
                    
                    conn.commit()
                    conn.close()
                    
                    st.success(f"Technical indicator alert created for {symbol} {indicator} {condition} {value:.2f}")
                    st.rerun()
            except Exception as e:
                logger.error(f"Error creating indicator alert: {str(e)}", exc_info=True)
                st.error(f"Failed to create alert: {str(e)}")

def show_sentiment_alerts(email):
    """Configure sentiment-based alerts"""
    st.header("Sentiment Alerts")
    st.write("Create alerts that trigger when sentiment for a cryptocurrency changes significantly.")
    
    # Get available cryptocurrencies
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT symbol FROM ohlcv_data
        ORDER BY symbol
    """)
    
    available_symbols = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if not available_symbols:
        st.warning("No cryptocurrency data found. Please refresh data first.")
        return
    
    # Create new sentiment alert form
    with st.form("sentiment_alert_form"):
        st.subheader("Create Sentiment Alert")
        
        # Select cryptocurrency
        symbol = st.selectbox("Cryptocurrency", available_symbols)
        
        # Select sentiment source
        source = st.selectbox("Sentiment Source", ["overall", "news", "social"])
        
        # Alert condition
        col1, col2 = st.columns(2)
        
        with col1:
            condition = st.selectbox("Condition", ["above", "below"])
        
        with col2:
            value = st.slider("Sentiment Score", min_value=-1.0, max_value=1.0, value=0.5 if condition == "above" else -0.5, step=0.1)
        
        # Email alerts
        receive_email = st.checkbox("Receive email notification", value=email != "")
        
        if receive_email and not email:
            st.warning("Please enter your email in the sidebar to receive notifications.")
        
        # Submit form
        submitted = st.form_submit_button("Create Alert")
        
        if submitted:
            try:
                if receive_email and not email:
                    st.error("Please enter your email to receive notifications.")
                else:
                    # Save alert to database
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    alert_type = f"sentiment_{source}"
                    
                    # Get recurring setting
                    recurring = True  # Default to recurring alerts
                    
                    cursor.execute(
                        """
                        INSERT INTO alerts (
                            symbol, alert_type, condition, value, active,
                            triggered, notification_sent, created_at,
                            trigger_count, daily_trigger_count, recurring
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            symbol, alert_type, condition, value, 1,
                            0, 0, datetime.datetime.now(),
                            0, 0, int(recurring)
                        )
                    )
                    
                    conn.commit()
                    conn.close()
                    
                    st.success(f"Sentiment alert created for {symbol} {source} sentiment {condition} {value:.1f}")
                    st.rerun()
            except Exception as e:
                logger.error(f"Error creating sentiment alert: {str(e)}", exc_info=True)
                st.error(f"Failed to create alert: {str(e)}")

def get_recurring_checkbox():
    """Utility function to get a recurring alert checkbox with default from config"""
    config = configparser.ConfigParser()
    config.read('config.ini')
    default_recurring = config.getboolean('ALERTS', 'RecurringAlerts', fallback=True)
    
    # Return the checkbox
    return st.checkbox("Recurring alert", 
                   value=default_recurring,
                   help="When enabled, this alert can trigger multiple times after cooldown periods")


def check_all_alerts(email):
    """Check and process all active alerts"""
    try:
        # Get active alerts
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all active alerts - now all alerts are checked, 
        # even if previously triggered, as we support recurring alerts
        cursor.execute("""
            SELECT id, symbol, alert_type, condition, value
            FROM alerts
            WHERE active = TRUE
        """)
        
        alerts = cursor.fetchall()
        conn.close()
        
        if not alerts:
            return
        
        for alert in alerts:
            alert_id, symbol, alert_type, condition, threshold = alert
            
            # Check alert based on type
            if alert_type == 'price':
                check_price_alert(alert_id, symbol, condition, threshold, email)
            elif alert_type.startswith('indicator_'):
                indicator = alert_type.split('_', 1)[1]
                check_indicator_alert(alert_id, symbol, indicator, condition, threshold, email)
            elif alert_type.startswith('sentiment_'):
                source = alert_type.split('_', 1)[1]
                check_sentiment_alert(alert_id, symbol, source, condition, threshold, email)
    
    except Exception as e:
        logger.error(f"Error checking alerts: {str(e)}", exc_info=True)

def check_price_alert(alert_id, symbol, condition, threshold, email):
    """Check price-based alert"""
    try:
        # Get current price
        latest_prices = get_latest_prices([symbol])
        
        if symbol not in latest_prices:
            logger.warning(f"Cannot check price alert for {symbol}: price not available")
            return
        
        current_price = latest_prices[symbol]['price']
        now = datetime.datetime.now()
        
        # Get configuration for alert triggers
        config = configparser.ConfigParser()
        config.read('config.ini')
        recurring_alerts = config.getboolean('ALERTS', 'RecurringAlerts', fallback=True)
        cooldown_minutes = config.getint('ALERTS', 'CooldownMinutes', fallback=60)
        max_triggers_per_day = config.getint('ALERTS', 'MaxTriggersPerDay', fallback=5)
        sms_enabled = config.getboolean('ALERTS', 'SMSEnabled', fallback=False)
        
        # Update last checked time
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First, get the current alert state to check for cooldown and daily limits
        cursor.execute(
            """
            SELECT triggered, last_triggered, notification_sent, 
                  trigger_count, daily_trigger_count, daily_count_reset, recurring
            FROM alerts WHERE id = ?
            """, 
            (alert_id,)
        )
        
        result = cursor.fetchone()
        if not result:
            logger.warning(f"Alert {alert_id} not found")
            conn.close()
            return
            
        (is_triggered, last_triggered, notification_sent, 
         trigger_count, daily_trigger_count, daily_count_reset, is_recurring) = result
        
        # Update last checked time
        cursor.execute(
            "UPDATE alerts SET last_checked = ? WHERE id = ?",
            (now, alert_id)
        )
        conn.commit()
        
        # Check if this alert is in cooldown period
        in_cooldown = False
        if last_triggered:
            cooldown_ends = last_triggered + datetime.timedelta(minutes=cooldown_minutes)
            if now < cooldown_ends:
                in_cooldown = True
                logger.debug(f"Alert {alert_id} still in cooldown period until {cooldown_ends}")
        
        # Reset daily counter if it's a new day
        today = now.date()
        if not daily_count_reset or daily_count_reset.date() < today:
            daily_trigger_count = 0
            daily_count_reset = now
            cursor.execute(
                "UPDATE alerts SET daily_trigger_count = 0, daily_count_reset = ? WHERE id = ?",
                (now, alert_id)
            )
            conn.commit()
        
        # Check if we've hit the daily limit
        daily_limit_reached = daily_trigger_count >= max_triggers_per_day
        
        # Don't proceed if:
        # 1. Alert is already triggered and not recurring, or
        # 2. In cooldown period, or
        # 3. Daily limit reached
        if (is_triggered and not is_recurring) or in_cooldown or daily_limit_reached:
            conn.close()
            return
        
        # Now check the condition
        triggered = False
        
        if condition == 'above' and current_price > threshold:
            triggered = True
        elif condition == 'below' and current_price < threshold:
            triggered = True
        
        if triggered:
            # Increment counters
            trigger_count += 1
            daily_trigger_count += 1
            
            # Update alert
            cursor.execute(
                """
                UPDATE alerts 
                SET triggered = 1, last_triggered = ?, notification_sent = ?,
                    trigger_count = ?, daily_trigger_count = ?
                WHERE id = ?
                """,
                (
                    now, 
                    1 if (email or sms_enabled) else 0,
                    trigger_count,
                    daily_trigger_count,
                    alert_id
                )
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Price alert triggered for {symbol} {condition} {threshold} (count: {trigger_count})")
            
            # Send email notification if configured
            if email:
                send_price_alert(email, symbol, current_price, condition, threshold)
                
            # Send SMS notification if enabled
            if sms_enabled:
                owner_phone = config.get('ALERTS', 'OwnerPhoneNumber', fallback='')
                if owner_phone:
                    # Send SMS notification to owner
                    send_price_sms_alert(owner_phone, symbol, current_price, condition, threshold)
                    logger.info(f"SMS alert sent to {owner_phone} for {symbol}")
                else:
                    logger.warning("SMS alerts enabled but owner phone number not configured")
        else:
            # If condition no longer met, reset triggered status for recurring alerts
            if is_triggered and is_recurring and not in_cooldown:
                cursor.execute(
                    "UPDATE alerts SET triggered = 0 WHERE id = ?",
                    (alert_id,)
                )
                conn.commit()
                logger.debug(f"Reset triggered status for recurring alert {alert_id}")
            conn.close()
    
    except Exception as e:
        logger.error(f"Error checking price alert: {str(e)}", exc_info=True)

def check_indicator_alert(alert_id, symbol, indicator, condition, threshold, email):
    """Check technical indicator alert"""
    try:
        now = datetime.datetime.now()
        
        # Get configuration for alert triggers
        config = configparser.ConfigParser()
        config.read('config.ini')
        recurring_alerts = config.getboolean('ALERTS', 'RecurringAlerts', fallback=True)
        cooldown_minutes = config.getint('ALERTS', 'CooldownMinutes', fallback=60)
        max_triggers_per_day = config.getint('ALERTS', 'MaxTriggersPerDay', fallback=5)
        sms_enabled = config.getboolean('ALERTS', 'SMSEnabled', fallback=False)
        
        # Get current alert state first
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT triggered, last_triggered, notification_sent, 
                  trigger_count, daily_trigger_count, daily_count_reset, recurring
            FROM alerts WHERE id = ?
            """, 
            (alert_id,)
        )
        
        result = cursor.fetchone()
        if not result:
            logger.warning(f"Alert {alert_id} not found")
            conn.close()
            return
            
        (is_triggered, last_triggered, notification_sent, 
         trigger_count, daily_trigger_count, daily_count_reset, is_recurring) = result
        
        # Check if this alert is in cooldown period
        in_cooldown = False
        if last_triggered:
            cooldown_ends = last_triggered + datetime.timedelta(minutes=cooldown_minutes)
            if now < cooldown_ends:
                in_cooldown = True
                logger.debug(f"Alert {alert_id} still in cooldown period until {cooldown_ends}")
        
        # Reset daily counter if it's a new day
        today = now.date()
        if not daily_count_reset or daily_count_reset.date() < today:
            daily_trigger_count = 0
            daily_count_reset = now
            cursor.execute(
                "UPDATE alerts SET daily_trigger_count = 0, daily_count_reset = ? WHERE id = ?",
                (now, alert_id)
            )
            conn.commit()
        
        # Check if we've hit the daily limit
        daily_limit_reached = daily_trigger_count >= max_triggers_per_day
        
        # Don't proceed if:
        # 1. Alert is already triggered and not recurring, or
        # 2. In cooldown period, or
        # 3. Daily limit reached
        if (is_triggered and not is_recurring) or in_cooldown or daily_limit_reached:
            cursor.execute(
                "UPDATE alerts SET last_checked = ? WHERE id = ?",
                (now, alert_id)
            )
            conn.commit()
            conn.close()
            return
        
        # Get current indicator value based on condition type
        if condition.startswith('crosses'):
            # For crosses conditions, we need current and previous values
            cursor.execute(f"""
                SELECT {indicator}
                FROM technical_indicators
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT 2
            """, (symbol,))
            
            results = cursor.fetchall()
            
            if len(results) < 2:
                cursor.execute(
                    "UPDATE alerts SET last_checked = ? WHERE id = ?",
                    (now, alert_id)
                )
                conn.commit()
                conn.close()
                return
            
            current_value = results[0][0]
            previous_value = results[1][0]
        else:
            # For simple threshold conditions, we only need the current value
            cursor.execute(f"""
                SELECT {indicator}
                FROM technical_indicators
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (symbol,))
            
            result = cursor.fetchone()
            
            if not result:
                cursor.execute(
                    "UPDATE alerts SET last_checked = ? WHERE id = ?",
                    (now, alert_id)
                )
                conn.commit()
                conn.close()
                return
            
            current_value = result[0]
            # Explicitly set previous_value to None for non-crosses conditions
            previous_value = None
        
        # Update last checked time
        cursor.execute(
            "UPDATE alerts SET last_checked = ? WHERE id = ?",
            (now, alert_id)
        )
        
        conn.commit()
        
        # Check alert condition
        triggered = False
        
        if condition.startswith('crosses'):
            # We know previous_value is defined for crosses conditions based on earlier code
            if condition == 'crosses above' and previous_value <= threshold and current_value > threshold:
                triggered = True
            elif condition == 'crosses below' and previous_value >= threshold and current_value < threshold:
                triggered = True
        else:
            # Simple threshold conditions
            if condition == 'above' and current_value > threshold:
                triggered = True
            elif condition == 'below' and current_value < threshold:
                triggered = True
        
        if triggered:
            # Increment counters
            trigger_count += 1
            daily_trigger_count += 1
            
            # Update alert
            cursor.execute(
                """
                UPDATE alerts 
                SET triggered = 1, last_triggered = ?, notification_sent = ?,
                    trigger_count = ?, daily_trigger_count = ?
                WHERE id = ?
                """,
                (
                    now, 
                    1 if (email or sms_enabled) else 0,
                    trigger_count,
                    daily_trigger_count,
                    alert_id
                )
            )
            
            conn.commit()
            conn.close()
            
            # Format indicator name for display
            indicator_name = indicator.upper() if indicator in ['macd', 'rsi'] else ' '.join(part.capitalize() for part in indicator.split('_'))
            
            logger.info(f"Indicator alert triggered for {symbol} {indicator_name} {condition} {threshold} (count: {trigger_count})")
            
            # Send email notification if configured
            if email:
                send_indicator_alert(email, symbol, indicator_name, current_value, condition, threshold)
                
            # Send SMS notification if enabled
            if sms_enabled:
                owner_phone = config.get('ALERTS', 'OwnerPhoneNumber', fallback='')
                if owner_phone:
                    # Send SMS notification to owner
                    send_indicator_sms_alert(owner_phone, symbol, indicator_name, current_value, condition, threshold)
                    logger.info(f"SMS alert sent to {owner_phone} for {symbol} indicator {indicator_name}")
                else:
                    logger.warning("SMS alerts enabled but owner phone number not configured")
        else:
            # If condition no longer met, reset triggered status for recurring alerts
            if is_triggered and is_recurring and not in_cooldown:
                cursor.execute(
                    "UPDATE alerts SET triggered = 0 WHERE id = ?",
                    (alert_id,)
                )
                conn.commit()
                logger.debug(f"Reset triggered status for recurring alert {alert_id}")
            conn.close()
    
    except Exception as e:
        logger.error(f"Error checking indicator alert: {str(e)}", exc_info=True)

def check_sentiment_alert(alert_id, symbol, source, condition, threshold, email):
    """Check sentiment-based alert"""
    try:
        now = datetime.datetime.now()
        
        # Get configuration for alert triggers
        config = configparser.ConfigParser()
        config.read('config.ini')
        recurring_alerts = config.getboolean('ALERTS', 'RecurringAlerts', fallback=True)
        cooldown_minutes = config.getint('ALERTS', 'CooldownMinutes', fallback=60)
        max_triggers_per_day = config.getint('ALERTS', 'MaxTriggersPerDay', fallback=5)
        sms_enabled = config.getboolean('ALERTS', 'SMSEnabled', fallback=False)
        
        # Get current alert state first
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT triggered, last_triggered, notification_sent, 
                  trigger_count, daily_trigger_count, daily_count_reset, recurring
            FROM alerts WHERE id = ?
            """, 
            (alert_id,)
        )
        
        result = cursor.fetchone()
        if not result:
            logger.warning(f"Alert {alert_id} not found")
            conn.close()
            return
            
        (is_triggered, last_triggered, notification_sent, 
         trigger_count, daily_trigger_count, daily_count_reset, is_recurring) = result
        
        # Check if this alert is in cooldown period
        in_cooldown = False
        if last_triggered:
            cooldown_ends = last_triggered + datetime.timedelta(minutes=cooldown_minutes)
            if now < cooldown_ends:
                in_cooldown = True
                logger.debug(f"Alert {alert_id} still in cooldown period until {cooldown_ends}")
        
        # Reset daily counter if it's a new day
        today = now.date()
        if not daily_count_reset or daily_count_reset.date() < today:
            daily_trigger_count = 0
            daily_count_reset = now
            cursor.execute(
                "UPDATE alerts SET daily_trigger_count = 0, daily_count_reset = ? WHERE id = ?",
                (now, alert_id)
            )
            conn.commit()
        
        # Check if we've hit the daily limit
        daily_limit_reached = daily_trigger_count >= max_triggers_per_day
        
        # Don't proceed if:
        # 1. Alert is already triggered and not recurring, or
        # 2. In cooldown period, or
        # 3. Daily limit reached
        if (is_triggered and not is_recurring) or in_cooldown or daily_limit_reached:
            cursor.execute(
                "UPDATE alerts SET last_checked = ? WHERE id = ?",
                (now, alert_id)
            )
            conn.commit()
            conn.close()
            return
        
        # Get sentiment data
        from analysis.sentiment_analysis import get_cryptocurrency_sentiment
        
        sentiment_data = get_cryptocurrency_sentiment(symbol, days_back=1)
        
        # Determine which sentiment value to check
        if source == 'overall':
            current_value = sentiment_data['overall_sentiment']
        elif source == 'news':
            current_value = sentiment_data['avg_news_sentiment']
        elif source == 'social':
            current_value = sentiment_data['avg_social_sentiment']
        else:
            logger.warning(f"Unknown sentiment source: {source}")
            conn.close()
            return
        
        # Update last checked time
        cursor.execute(
            "UPDATE alerts SET last_checked = ? WHERE id = ?",
            (now, alert_id)
        )
        
        conn.commit()
        
        # Check alert condition
        triggered = False
        
        if condition == 'above' and current_value > threshold:
            triggered = True
        elif condition == 'below' and current_value < threshold:
            triggered = True
        
        if triggered:
            # Increment counters
            trigger_count += 1
            daily_trigger_count += 1
            
            # Update alert
            cursor.execute(
                """
                UPDATE alerts 
                SET triggered = 1, last_triggered = ?, notification_sent = ?,
                    trigger_count = ?, daily_trigger_count = ?
                WHERE id = ?
                """,
                (
                    now, 
                    1 if (email or sms_enabled) else 0,
                    trigger_count,
                    daily_trigger_count,
                    alert_id
                )
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Sentiment alert triggered for {symbol} {source} sentiment {condition} {threshold} (count: {trigger_count})")
            
            # Send email notification if configured
            if email:
                send_sentiment_alert(email, symbol, current_value, source)
                
            # Send SMS notification if enabled
            if sms_enabled:
                owner_phone = config.get('ALERTS', 'OwnerPhoneNumber', fallback='')
                if owner_phone:
                    # Send SMS notification to owner
                    send_sentiment_sms_alert(owner_phone, symbol, current_value, source)
                    logger.info(f"SMS alert sent to {owner_phone} for {symbol} sentiment")
                else:
                    logger.warning("SMS alerts enabled but owner phone number not configured")
        else:
            # If condition no longer met, reset triggered status for recurring alerts
            if is_triggered and is_recurring and not in_cooldown:
                cursor.execute(
                    "UPDATE alerts SET triggered = 0 WHERE id = ?",
                    (alert_id,)
                )
                conn.commit()
                logger.debug(f"Reset triggered status for recurring alert {alert_id}")
            conn.close()
    
    except Exception as e:
        logger.error(f"Error checking sentiment alert: {str(e)}", exc_info=True)
