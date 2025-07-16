#!/usr/bin/env python3
"""Collect more comprehensive cryptocurrency data"""
import ccxt
import os
import psycopg2
from datetime import datetime, timedelta
import time

def collect_historical_data():
    """Collect historical data for better charts"""
    try:
        # Connect to exchange
        exchange = ccxt.coinbase({'enableRateLimit': True})
        
        # Connect to database
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cursor = conn.cursor()
        
        symbols = ['BTC/USD', 'ETH/USD', 'LTC/USD', 'XRP/USD']
        
        for symbol in symbols:
            print(f"Collecting historical data for {symbol}...")
            
            # Get daily data for the last 30 days
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, '1d', limit=30)
                
                insert_query = """
                INSERT INTO ohlcv_data (symbol, exchange, timestamp, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, exchange, timestamp) DO NOTHING
                """
                
                for candle in ohlcv:
                    timestamp = datetime.fromtimestamp(candle[0] / 1000)
                    open_price = candle[1]
                    high_price = candle[2]
                    low_price = candle[3]
                    close_price = candle[4]
                    volume = candle[5] or 0
                    
                    cursor.execute(insert_query, (
                        symbol, 'coinbase', timestamp,
                        open_price, high_price, low_price, close_price, volume
                    ))
                
                conn.commit()
                print(f"✓ Added {len(ohlcv)} records for {symbol}")
                
            except Exception as e:
                print(f"✗ Error collecting {symbol}: {e}")
                continue
                
            time.sleep(1)  # Rate limiting
        
        cursor.close()
        conn.close()
        print("✓ Historical data collection complete")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    collect_historical_data()