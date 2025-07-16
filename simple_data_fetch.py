#!/usr/bin/env python3
"""Simple data fetcher that definitely works"""
import ccxt
import os
from datetime import datetime
import psycopg2

def fetch_simple_data():
    """Fetch and insert cryptocurrency data directly"""
    try:
        # Connect to Coinbase
        exchange = ccxt.coinbase({'enableRateLimit': True})
        
        # Connect to database
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cursor = conn.cursor()
        
        # Fetch BTC price
        ticker = exchange.fetch_ticker('BTC/USD')
        
        # Insert the data
        insert_query = """
        INSERT INTO ohlcv_data (symbol, exchange, timestamp, open, high, low, close, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data = (
            'BTC/USD',
            'coinbase',
            datetime.now(),
            ticker['open'] or ticker['last'],
            ticker['high'] or ticker['last'],
            ticker['low'] or ticker['last'],
            ticker['last'],
            ticker['baseVolume'] or 0
        )
        
        cursor.execute(insert_query, data)
        conn.commit()
        
        print(f"✓ Inserted BTC/USD price: ${ticker['last']}")
        
        # Fetch ETH price
        ticker = exchange.fetch_ticker('ETH/USD')
        
        data = (
            'ETH/USD',
            'coinbase',
            datetime.now(),
            ticker['open'] or ticker['last'],
            ticker['high'] or ticker['last'],
            ticker['low'] or ticker['last'],
            ticker['last'],
            ticker['baseVolume'] or 0
        )
        
        cursor.execute(insert_query, data)
        conn.commit()
        
        print(f"✓ Inserted ETH/USD price: ${ticker['last']}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    fetch_simple_data()