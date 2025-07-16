#!/usr/bin/env python3
"""Script to fetch real cryptocurrency data"""
import ccxt
import pandas as pd
import sys
import os
sys.path.append('.')

from database.operations import get_db_connection
from utils.logging_config import get_logger

logger = get_logger(__name__)

def fetch_real_crypto_data():
    """Fetch real cryptocurrency data from Binance"""
    try:
        # Try multiple exchanges until one works
        exchanges_to_try = ['coinbase', 'kraken', 'bitstamp', 'gemini']
        exchange = None
        
        for exchange_id in exchanges_to_try:
            try:
                exchange_class = getattr(ccxt, exchange_id)
                exchange = exchange_class({'enableRateLimit': True})
                exchange.load_markets()  # Test connection
                print(f"Successfully connected to {exchange_id}")
                break
            except Exception as e:
                print(f"Failed to connect to {exchange_id}: {str(e)}")
                continue
        
        if exchange is None:
            raise Exception("Could not connect to any cryptocurrency exchange")
        
        # Get available markets and find common crypto pairs
        markets = exchange.load_markets()
        
        # Define symbols based on what the exchange supports
        base_symbols = ['BTC', 'ETH', 'LTC', 'XRP', 'ADA', 'DOT', 'SOL', 'AVAX']
        quote_currencies = ['USD', 'USDT', 'EUR']
        
        symbols = []
        for base in base_symbols:
            for quote in quote_currencies:
                symbol = f"{base}/{quote}"
                if symbol in markets:
                    symbols.append(symbol)
                    break  # Use first available quote currency
        
        if not symbols:
            # Fallback to any available symbols
            symbols = list(markets.keys())[:10]
        
        print(f"Will fetch data for: {symbols[:8]}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for symbol in symbols:
            try:
                print(f"Fetching data for {symbol}...")
                
                # Fetch OHLCV data (last 30 days)
                ohlcv = exchange.fetch_ohlcv(symbol, '1d', limit=30)
                
                for data_point in ohlcv:
                    timestamp = pd.to_datetime(data_point[0], unit='ms')
                    open_price = data_point[1]
                    high_price = data_point[2]
                    low_price = data_point[3]
                    close_price = data_point[4]
                    volume = data_point[5]
                    
                    # Insert data with proper parameter handling
                    if 'DATABASE_URL' in os.environ:
                        # PostgreSQL
                        query = """
                        INSERT INTO ohlcv_data (symbol, timestamp, open, high, low, close, volume, exchange)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """
                        cursor.execute(query, (symbol, timestamp, open_price, high_price, low_price, close_price, volume, exchange.id))
                    else:
                        # SQLite
                        query = """
                        INSERT OR IGNORE INTO ohlcv_data (symbol, timestamp, open, high, low, close, volume, exchange)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        cursor.execute(query, (symbol, timestamp, open_price, high_price, low_price, close_price, volume, exchange.id))
                
                print(f"✓ Successfully fetched {symbol}")
                
            except Exception as e:
                print(f"✗ Failed to fetch {symbol}: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"\n✓ Successfully fetched real cryptocurrency data!")
        return True
        
    except Exception as e:
        print(f"✗ Data collection failed: {str(e)}")
        return False

if __name__ == "__main__":
    fetch_real_crypto_data()