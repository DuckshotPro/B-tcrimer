import os
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser
from utils.logging_config import get_logger

logger = get_logger(__name__)

def get_email_config():
    """Get email configuration from config.ini"""
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        email_config = {
            'enabled': config.getboolean('ALERTS', 'EmailEnabled'),
            'server': config['ALERTS']['EmailServer'],
            'port': int(config['ALERTS']['EmailPort']),
            'from_address': config['ALERTS']['EmailFromAddress'],
            'auth_required': config.getboolean('ALERTS', 'EmailAuthentication')
        }
        
        return email_config
    except Exception as e:
        logger.error(f"Failed to load email configuration: {str(e)}", exc_info=True)
        return {
            'enabled': False,
            'server': '',
            'port': 587,
            'from_address': '',
            'auth_required': False
        }

def send_email_alert(to_address, subject, message, html_message=None):
    """Send an email alert"""
    try:
        email_config = get_email_config()
        
        if not email_config['enabled']:
            logger.warning("Email alerts are disabled in configuration")
            return False
            
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = email_config['from_address']
        msg['To'] = to_address
        
        # Attach text part
        text_part = MIMEText(message, 'plain')
        msg.attach(text_part)
        
        # Attach HTML part if provided
        if html_message:
            html_part = MIMEText(html_message, 'html')
            msg.attach(html_part)
        
        # Connect to server
        server = smtplib.SMTP(email_config['server'], email_config['port'])
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        # Login if authentication required
        if email_config['auth_required']:
            username = os.getenv("EMAIL_USERNAME", "")
            password = os.getenv("EMAIL_PASSWORD", "")
            
            if not username or not password:
                logger.error("Email authentication required but credentials not found in environment variables")
                return False
                
            server.login(username, password)
        
        # Send email
        server.sendmail(email_config['from_address'], to_address, msg.as_string())
        server.quit()
        
        logger.info(f"Email alert sent to {to_address}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email alert: {str(e)}", exc_info=True)
        return False

def send_price_alert(to_address, symbol, price, condition, threshold):
    """Send a price alert email"""
    try:
        subject = f"Crypto Alert: {symbol} price {condition} {threshold}"
        
        message = f"""
Cryptocurrency Price Alert

Symbol: {symbol}
Current Price: ${price:.2f}
Condition: Price is {condition} ${threshold:.2f}
Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated alert from your Cryptocurrency Analysis Platform.
        """
        
        html_message = f"""
<html>
<head></head>
<body>
<h2>Cryptocurrency Price Alert</h2>
<p><b>Symbol:</b> {symbol}</p>
<p><b>Current Price:</b> ${price:.2f}</p>
<p><b>Condition:</b> Price is {condition} ${threshold:.2f}</p>
<p><b>Time:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<hr>
<p><small>This is an automated alert from your Cryptocurrency Analysis Platform.</small></p>
</body>
</html>
        """
        
        return send_email_alert(to_address, subject, message, html_message)
    except Exception as e:
        logger.error(f"Failed to send price alert: {str(e)}", exc_info=True)
        return False

def send_indicator_alert(to_address, symbol, indicator, value, condition, threshold):
    """Send a technical indicator alert email"""
    try:
        subject = f"Crypto Alert: {symbol} {indicator} {condition} {threshold}"
        
        message = f"""
Cryptocurrency Technical Indicator Alert

Symbol: {symbol}
Indicator: {indicator}
Current Value: {value:.2f}
Condition: {indicator} is {condition} {threshold:.2f}
Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated alert from your Cryptocurrency Analysis Platform.
        """
        
        html_message = f"""
<html>
<head></head>
<body>
<h2>Cryptocurrency Technical Indicator Alert</h2>
<p><b>Symbol:</b> {symbol}</p>
<p><b>Indicator:</b> {indicator}</p>
<p><b>Current Value:</b> {value:.2f}</p>
<p><b>Condition:</b> {indicator} is {condition} {threshold:.2f}</p>
<p><b>Time:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<hr>
<p><small>This is an automated alert from your Cryptocurrency Analysis Platform.</small></p>
</body>
</html>
        """
        
        return send_email_alert(to_address, subject, message, html_message)
    except Exception as e:
        logger.error(f"Failed to send indicator alert: {str(e)}", exc_info=True)
        return False

def send_sentiment_alert(to_address, symbol, sentiment_score, source):
    """Send a sentiment alert email"""
    try:
        sentiment_label = "positive" if sentiment_score > 0.3 else "negative" if sentiment_score < -0.3 else "neutral"
        subject = f"Crypto Alert: {symbol} sentiment is {sentiment_label}"
        
        message = f"""
Cryptocurrency Sentiment Alert

Symbol: {symbol}
Sentiment: {sentiment_label.capitalize()} ({sentiment_score:.2f})
Source: {source}
Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated alert from your Cryptocurrency Analysis Platform.
        """
        
        html_message = f"""
<html>
<head></head>
<body>
<h2>Cryptocurrency Sentiment Alert</h2>
<p><b>Symbol:</b> {symbol}</p>
<p><b>Sentiment:</b> {sentiment_label.capitalize()} ({sentiment_score:.2f})</p>
<p><b>Source:</b> {source}</p>
<p><b>Time:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<hr>
<p><small>This is an automated alert from your Cryptocurrency Analysis Platform.</small></p>
</body>
</html>
        """
        
        return send_email_alert(to_address, subject, message, html_message)
    except Exception as e:
        logger.error(f"Failed to send sentiment alert: {str(e)}", exc_info=True)
        return False

def send_system_alert(to_address, issue, details):
    """Send a system alert email for errors or important notifications"""
    try:
        subject = f"Crypto Analysis System Alert: {issue}"
        
        message = f"""
Cryptocurrency Analysis System Alert

Issue: {issue}
Details: {details}
Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated alert from your Cryptocurrency Analysis Platform.
        """
        
        html_message = f"""
<html>
<head></head>
<body>
<h2>Cryptocurrency Analysis System Alert</h2>
<p><b>Issue:</b> {issue}</p>
<p><b>Details:</b> {details}</p>
<p><b>Time:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<hr>
<p><small>This is an automated alert from your Cryptocurrency Analysis Platform.</small></p>
</body>
</html>
        """
        
        return send_email_alert(to_address, subject, message, html_message)
    except Exception as e:
        logger.error(f"Failed to send system alert: {str(e)}", exc_info=True)
        return False
