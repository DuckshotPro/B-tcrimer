#!/usr/bin/env python3
"""Automated data collection that runs continuously"""
import time
import sys
import os
sys.path.append('.')

import ccxt
import psycopg2
from datetime import datetime
import feedparser
from utils.logging_config import get_logger

logger = get_logger(__name__)

def collect_crypto_data():
    """Collect cryptocurrency price data"""
    try:
        # Connect to Coinbase
        exchange = ccxt.coinbase({'enableRateLimit': True})
        
        # Connect to database
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cursor = conn.cursor()
        
        symbols = ['BTC/USD', 'ETH/USD', 'LTC/USD', 'XRP/USD', 'SOL/USD', 'ADA/USD']
        
        for symbol in symbols:
            try:
                # Fetch current ticker
                ticker = exchange.fetch_ticker(symbol)
                
                # Insert data
                insert_query = """
                INSERT INTO ohlcv_data (symbol, exchange, timestamp, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, exchange, timestamp) DO UPDATE
                SET close = EXCLUDED.close, volume = EXCLUDED.volume
                """
                
                # Ensure we have all required values
                last_price = ticker['last']
                open_price = ticker.get('open') or last_price
                high_price = ticker.get('high') or last_price
                low_price = ticker.get('low') or last_price
                volume = ticker.get('baseVolume') or ticker.get('volume') or 0
                
                cursor.execute(insert_query, (
                    symbol, 'coinbase', datetime.now(),
                    open_price, high_price, low_price, last_price, volume
                ))
                
                logger.info(f"Updated {symbol}: ${ticker['last']}")
                
            except Exception as e:
                logger.error(f"Error collecting {symbol}: {e}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Data collection error: {e}")
        return False

def collect_news_data():
    """Collect cryptocurrency news"""
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cursor = conn.cursor()
        
        feeds = [
            ('https://cointelegraph.com/rss', 'CoinTelegraph'),
            ('https://cryptonews.com/news/feed/', 'CryptoNews'),
            ('https://decrypt.co/feed', 'Decrypt'),
        ]
        
        for feed_url, source in feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:5]:  # Latest 5 articles
                    insert_query = """
                    INSERT INTO news_data (title, link, published_date, source, collected_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (link) DO NOTHING
                    """
                    
                    pub_date = datetime.now()  # Fallback
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])
                    
                    cursor.execute(insert_query, (
                        entry.title, entry.link, pub_date, source, datetime.now()
                    ))
                
                logger.info(f"Updated news from {source}")
                
            except Exception as e:
                logger.error(f"Error collecting news from {source}: {e}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"News collection error: {e}")
        return False

def main():
    """Main data collection loop"""
    logger.info("Starting automated data collection...")
    
    while True:
        try:
            # Collect crypto data
            logger.info("Collecting cryptocurrency data...")
            if collect_crypto_data():
                logger.info("✓ Crypto data collection successful")
            else:
                logger.error("✗ Crypto data collection failed")
            
            # Collect news data every 30 minutes
            if datetime.now().minute % 30 == 0:
                logger.info("Collecting news data...")
                if collect_news_data():
                    logger.info("✓ News data collection successful")
                else:
                    logger.error("✗ News data collection failed")
            
            # Wait 5 minutes before next update
            logger.info("Waiting 5 minutes until next update...")
            time.sleep(300)  # 5 minutes
            
        except KeyboardInterrupt:
            logger.info("Data collection stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(60)  # Wait 1 minute on error

if __name__ == "__main__":
    main()