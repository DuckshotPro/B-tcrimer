import streamlit as st
import pandas as pd
import numpy as np
import datetime
import uuid
import os

from database.operations import get_db_connection
from data_collection.exchange_data import get_latest_prices
from utils.email_alerts import send_price_alert, send_indicator_alert, send_sentiment_alert
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
        alert_email = st.sidebar.text_input("Email for Alerts", 
                                            value=st.session_state.alert_email,
                                            placeholder="Enter your email")
        
        if alert_email != st.session_state.alert_email:
            st.session_state.alert_email = alert_email
        
        # Check if email alerts are enabled in config
        import configparser
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        email_enabled = config.getboolean('ALERTS', 'EmailEnabled')
        
        if not email_enabled:
            st.sidebar.warning("Email alerts are disabled in configuration.")
        
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
        SELECT id, symbol, alert_type, condition, value, last_checked, last_triggered, notification_sent, created_at
        FROM alerts
        WHERE active = 1
        ORDER BY created_at DESC
    """)
    
    alerts = cursor.fetchall()
    conn.close()
    
    if not alerts:
        st.info("No active alerts configured. Use the tabs to create new alerts.")
        return
    
    # Display alerts
    for alert in alerts:
        alert_id, symbol, alert_type, condition, value, last_checked, last_triggered, notification_sent, created_at = alert
        
        # Format dates
        if isinstance(created_at, str):
            created_at = datetime.datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        
        if last_checked and isinstance(last_checked, str):
            last_checked = datetime.datetime.strptime(last_checked, '%Y-%m-%d %H:%M:%S')
        
        if last_triggered and isinstance(last_triggered, str):
            last_triggered = datetime.datetime.strptime(last_triggered, '%Y-%m-%d %H:%M:%S')
        
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
        
        # Create alert card
        with st.expander(f"{symbol} - {alert_type.title()} {condition} {value}"):
            st.write(f"**Type:** {alert_type.title()}")
            st.write(f"**Condition:** {condition.title()} {value}")
            st.write(f"**Created:** {created_at.strftime('%Y-%m-%d %H:%M')}")
            
            if last_checked:
                st.write(f"**Last Checked:** {last_checked.strftime('%Y-%m-%d %H:%M')}")
            
            if last_triggered:
                st.write(f"**Last Triggered:** {last_triggered.strftime('%Y-%m-%d %H:%M')}")
            
            st.markdown(f"**Status:** <span style='color: {status_color}'>{status}</span>", unsafe_allow_html=True)
            
            # Delete button
            if st.button(f"Delete Alert", key=f"delete_{alert_id}"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
                conn.commit()
                conn.close()
                st.success("Alert deleted successfully!")
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
                    
                    cursor.execute(
                        """
                        INSERT INTO alerts (
                            symbol, alert_type, condition, value, active,
                            triggered, notification_sent, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            symbol, 'price', condition, price, 1,
                            0, 0, datetime.datetime.now()
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
                    
                    cursor.execute(
                        """
                        INSERT INTO alerts (
                            symbol, alert_type, condition, value, active,
                            triggered, notification_sent, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            symbol, alert_type, condition, value, 1,
                            0, 0, datetime.datetime.now()
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
                    
                    cursor.execute(
                        """
                        INSERT INTO alerts (
                            symbol, alert_type, condition, value, active,
                            triggered, notification_sent, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            symbol, alert_type, condition, value, 1,
                            0, 0, datetime.datetime.now()
                        )
                    )
                    
                    conn.commit()
                    conn.close()
                    
                    st.success(f"Sentiment alert created for {symbol} {source} sentiment {condition} {value:.1f}")
                    st.rerun()
            except Exception as e:
                logger.error(f"Error creating sentiment alert: {str(e)}", exc_info=True)
                st.error(f"Failed to create alert: {str(e)}")

def check_all_alerts(email):
    """Check and process all active alerts"""
    try:
        # Get active alerts
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, symbol, alert_type, condition, value, notification_sent
            FROM alerts
            WHERE active = 1
        """)
        
        alerts = cursor.fetchall()
        conn.close()
        
        if not alerts:
            return
        
        for alert in alerts:
            alert_id, symbol, alert_type, condition, threshold, notification_sent = alert
            
            # Skip if already notified
            if notification_sent:
                continue
            
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
        
        # Update last checked time
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE alerts SET last_checked = ? WHERE id = ?",
            (datetime.datetime.now(), alert_id)
        )
        
        conn.commit()
        
        # Check alert condition
        triggered = False
        
        if condition == 'above' and current_price > threshold:
            triggered = True
        elif condition == 'below' and current_price < threshold:
            triggered = True
        
        if triggered:
            # Update alert
            cursor.execute(
                """
                UPDATE alerts 
                SET triggered = 1, last_triggered = ?, notification_sent = ?
                WHERE id = ?
                """,
                (
                    datetime.datetime.now(), 
                    1 if email else 0,
                    alert_id
                )
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Price alert triggered for {symbol} {condition} {threshold}")
            
            # Send email notification if configured
            if email:
                send_price_alert(email, symbol, current_price, condition, threshold)
        else:
            conn.close()
    
    except Exception as e:
        logger.error(f"Error checking price alert: {str(e)}", exc_info=True)

def check_indicator_alert(alert_id, symbol, indicator, condition, threshold, email):
    """Check technical indicator alert"""
    try:
        # Get current indicator value
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current and previous values for crosses conditions
        if condition.startswith('crosses'):
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
                    (datetime.datetime.now(), alert_id)
                )
                conn.commit()
                conn.close()
                return
            
            current_value = results[0][0]
            previous_value = results[1][0]
        else:
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
                    (datetime.datetime.now(), alert_id)
                )
                conn.commit()
                conn.close()
                return
            
            current_value = result[0]
        
        # Update last checked time
        cursor.execute(
            "UPDATE alerts SET last_checked = ? WHERE id = ?",
            (datetime.datetime.now(), alert_id)
        )
        
        conn.commit()
        
        # Check alert condition
        triggered = False
        
        if condition == 'above' and current_value > threshold:
            triggered = True
        elif condition == 'below' and current_value < threshold:
            triggered = True
        elif condition == 'crosses above' and previous_value <= threshold and current_value > threshold:
            triggered = True
        elif condition == 'crosses below' and previous_value >= threshold and current_value < threshold:
            triggered = True
        
        if triggered:
            # Update alert
            cursor.execute(
                """
                UPDATE alerts 
                SET triggered = 1, last_triggered = ?, notification_sent = ?
                WHERE id = ?
                """,
                (
                    datetime.datetime.now(), 
                    1 if email else 0,
                    alert_id
                )
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Indicator alert triggered for {symbol} {indicator} {condition} {threshold}")
            
            # Send email notification if configured
            if email:
                # Format indicator name for display
                indicator_name = indicator.upper() if indicator in ['macd', 'rsi'] else ' '.join(part.capitalize() for part in indicator.split('_'))
                send_indicator_alert(email, symbol, indicator_name, current_value, condition, threshold)
        else:
            conn.close()
    
    except Exception as e:
        logger.error(f"Error checking indicator alert: {str(e)}", exc_info=True)

def check_sentiment_alert(alert_id, symbol, source, condition, threshold, email):
    """Check sentiment-based alert"""
    try:
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
            return
        
        # Update last checked time
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE alerts SET last_checked = ? WHERE id = ?",
            (datetime.datetime.now(), alert_id)
        )
        
        conn.commit()
        
        # Check alert condition
        triggered = False
        
        if condition == 'above' and current_value > threshold:
            triggered = True
        elif condition == 'below' and current_value < threshold:
            triggered = True
        
        if triggered:
            # Update alert
            cursor.execute(
                """
                UPDATE alerts 
                SET triggered = 1, last_triggered = ?, notification_sent = ?
                WHERE id = ?
                """,
                (
                    datetime.datetime.now(), 
                    1 if email else 0,
                    alert_id
                )
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Sentiment alert triggered for {symbol} {source} sentiment {condition} {threshold}")
            
            # Send email notification if configured
            if email:
                send_sentiment_alert(email, symbol, current_value, source)
        else:
            conn.close()
    
    except Exception as e:
        logger.error(f"Error checking sentiment alert: {str(e)}", exc_info=True)
