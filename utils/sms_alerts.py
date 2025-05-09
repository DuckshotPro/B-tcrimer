import os
import datetime
import configparser
from twilio.rest import Client
from utils.logging_config import get_logger

logger = get_logger(__name__)

def get_twilio_config():
    """Get Twilio configuration from environment variables"""
    try:
        twilio_config = {
            'account_sid': os.environ.get('TWILIO_ACCOUNT_SID'),
            'auth_token': os.environ.get('TWILIO_AUTH_TOKEN'),
            'phone_number': os.environ.get('TWILIO_PHONE_NUMBER'),
            'enabled': all([
                os.environ.get('TWILIO_ACCOUNT_SID'),
                os.environ.get('TWILIO_AUTH_TOKEN'),
                os.environ.get('TWILIO_PHONE_NUMBER')
            ])
        }
        
        return twilio_config
    except Exception as e:
        logger.error(f"Failed to load Twilio configuration: {str(e)}", exc_info=True)
        return {
            'account_sid': None,
            'auth_token': None,
            'phone_number': None,
            'enabled': False
        }

def send_sms_alert(to_phone_number, message):
    """Send an SMS alert using Twilio"""
    try:
        twilio_config = get_twilio_config()
        
        if not twilio_config['enabled']:
            logger.warning("SMS alerts are disabled due to missing Twilio configuration")
            return False
            
        # Initialize Twilio client
        client = Client(twilio_config['account_sid'], twilio_config['auth_token'])
        
        # Send SMS
        sms = client.messages.create(
            body=message,
            from_=twilio_config['phone_number'],
            to=to_phone_number
        )
        
        logger.info(f"SMS alert sent to {to_phone_number}: {sms.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS alert: {str(e)}", exc_info=True)
        return False

def send_price_sms_alert(to_phone_number, symbol, price, condition, threshold):
    """Send a price alert SMS"""
    try:
        message = f"CRYPTO ALERT: {symbol} price is {condition} ${threshold:.2f}. Current price: ${price:.2f}"
        return send_sms_alert(to_phone_number, message)
    except Exception as e:
        logger.error(f"Failed to send price SMS alert: {str(e)}", exc_info=True)
        return False

def send_indicator_sms_alert(to_phone_number, symbol, indicator, value, condition, threshold):
    """Send a technical indicator alert SMS"""
    try:
        message = f"CRYPTO ALERT: {symbol} {indicator} is {condition} {threshold:.2f}. Current value: {value:.2f}"
        return send_sms_alert(to_phone_number, message)
    except Exception as e:
        logger.error(f"Failed to send indicator SMS alert: {str(e)}", exc_info=True)
        return False

def send_sentiment_sms_alert(to_phone_number, symbol, sentiment_score, source):
    """Send a sentiment alert SMS"""
    try:
        sentiment_label = "positive" if sentiment_score > 0.3 else "negative" if sentiment_score < -0.3 else "neutral"
        message = f"CRYPTO ALERT: {symbol} sentiment is {sentiment_label} ({sentiment_score:.2f}) based on {source}"
        return send_sms_alert(to_phone_number, message)
    except Exception as e:
        logger.error(f"Failed to send sentiment SMS alert: {str(e)}", exc_info=True)
        return False

def send_system_sms_alert(to_phone_number, issue):
    """Send a system alert SMS for errors or important notifications"""
    try:
        message = f"CRYPTO SYSTEM ALERT: {issue}"
        return send_sms_alert(to_phone_number, message)
    except Exception as e:
        logger.error(f"Failed to send system SMS alert: {str(e)}", exc_info=True)
        return False